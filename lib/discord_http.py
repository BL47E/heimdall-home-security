#!/usr/bin/env python3
"""Narrow optional webhook transport. Never persist response text or expose URLs."""
from decimal import Decimal, InvalidOperation
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import signal
import socket
import time
import stat
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 3
LIMIT = 2000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_url(value, kind):
    if not value or len(value) > 2048 or any(ord(c) <= 32 or ord(c) >= 127 for c in value):
        raise ValueError('Invalid destination')
    url = urllib.parse.urlsplit(value)
    if url.username or url.password or url.query or url.fragment:
        raise ValueError('Invalid destination')
    if kind == 'production':
        if not re.fullmatch(r'https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+', value):
            raise ValueError('Invalid production destination')
    elif kind == 'loopback_test':
        if url.scheme != 'http' or url.hostname not in ('127.0.0.1', '::1') or not url.port or not url.path.startswith('/'):
            raise ValueError('Invalid test destination')
        if not ipaddress.ip_address(url.hostname).is_loopback:
            raise ValueError('Invalid test destination')
    else:
        raise ValueError('Unknown destination kind')
    return value


def configure(data, action):
    kind = 'production' if action == 'configure' else 'loopback_test'
    value = sys.stdin.read(4097)
    # Accept a single line pasted through stdin, never shell arguments.
    value = value.removesuffix('\n').removesuffix('\r')
    validate_url(value, kind)
    destination = data / 'discord-webhook'
    if destination.is_symlink():
        raise ValueError('Credential must not be a symbolic link')
    fd, name = tempfile.mkstemp(prefix='.discord-webhook.', dir=data)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(value + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, destination)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return {'configured': True, 'destination_kind': kind}


def credential(data, kind):
    fd = os.open(data / 'discord-webhook', os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.geteuid():
            raise ValueError('Credential permissions invalid')
        value = stream.read(4097).removesuffix('\n')
    return validate_url(value, kind)


def clean(value, maximum):
    # Prevent markdown/mention-like evidence from posing as interface text.
    text = re.sub(r'[\x00-\x1f\x7f`*_~|<>@\\]', ' ', str(value if value is not None else 'unknown'))
    return re.sub(r'\s+', ' ', text).strip()[:maximum]


def build_message(items):
    header = 'Heimdall SSH findings (grouped local notifications)\n'
    footer = '\nReview local evidence. SSH blocking: not implemented.'
    content = header
    ids = []
    for item in items:
        alert = item.get('alert', {})
        provenance = 'synthetic fixture' if alert.get('provenance') == 'fixture' else clean(alert.get('provenance'), 24)
        reputation = alert.get('reputation') or {}
        reputation_label = clean(reputation.get('label', 'Unknown'), 24)
        if reputation.get('provenance') == 'simulated':
            reputation_label += ' (simulated)'
        line = (f"- {clean(alert.get('id'), 64)} [{provenance}; {clean(item.get('reason'), 16)}] "
                f"time={clean(item.get('created_at'), 24)} source={clean(alert.get('source_ip'), 48)} "
                f"failures={clean(alert.get('failure_count'), 12)} severity={clean(alert.get('severity'), 16)}: "
                f"{clean(alert.get('explanation'), 320)} VirusTotal: {reputation_label}.\n")
        if len(content + line + footer) > LIMIT:
            break
        content += line
        ids.append(item['id'])
    return ids, {'content': content + footer, 'allowed_mentions': {'parse': []}}


def delay_number(value):
    if isinstance(value, bool):
        return None
    try:
        precise = Decimal(str(value))
        if not precise.is_finite() or precise < 0:
            return None
        if precise > Decimal(str(sys.float_info.max)):
            raise OverflowError('Retry delay cannot be represented safely')
        number = float(precise)
    except (ValueError, TypeError, InvalidOperation):
        return None
    return number if math.isfinite(number) else None


def response_delay(headers, body, rate_limited=False):
    values = []
    if rate_limited:
        for candidate in (headers.get('Retry-After'), body.get('retry_after') if isinstance(body, dict) else None):
            delay = delay_number(candidate)
            if delay is not None:
                values.append(delay)
    if headers.get('X-RateLimit-Remaining') == '0':
        delay = delay_number(headers.get('X-RateLimit-Reset-After'))
        if delay is None:
            reset = delay_number(headers.get('X-RateLimit-Reset'))
            delay = max(0, reset - time.time()) if reset is not None else 30
        values.append(delay)
    return max(values, default=0)


def send(data, snapshot):
    ids, payload = build_message(snapshot.get('items', []))
    result = {'ids': ids, 'outcome': 'temporary_error', 'delay_seconds': 30, 'ambiguous': False}
    attempts = max((int(item.get('attempts', 0)) for item in snapshot.get('items', []) if item.get('id') in ids), default=0)
    result['delay_seconds'] = min(3600, 30 * 2 ** min(max(attempts, 0), 7))
    if not ids:
        return result
    if not snapshot.get('enabled') or not snapshot.get('configured') or snapshot.get('blocked'):
        result['ids'] = []
        return result
    kind = snapshot.get('destination_kind')
    if kind == 'production' and snapshot.get('mode') == 'fixture':
        raise ValueError('Synthetic state cannot transmit to Discord; use an explicit loopback test destination')
    try:
        destination = credential(data, kind)
    except (OSError, ValueError):
        result.update(outcome='permanent_error')
        return result
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(destination + '?wait=true', data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json', 'User-Agent': 'Heimdall-local/0.1'}, method='POST')
    def deadline_expired(signum, frame):
        raise TimeoutError('Webhook request deadline exceeded')
    previous_handler = signal.signal(signal.SIGALRM, deadline_expired)
    signal.setitimer(signal.ITIMER_REAL, TIMEOUT)
    try:
        try:
            response = opener.open(request, timeout=TIMEOUT)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            status = response.code
            raw = response.read(65537)
            try:
                body = json.loads(raw, parse_float=Decimal) if len(raw) <= 65536 else None
            except (ValueError, UnicodeError):
                body = None
            delay = response_delay(response.headers, body, status == 429)
        if status == 200 and isinstance(body, dict) and isinstance(body.get('id'), str) and re.fullmatch(r'[0-9]+', body['id']):
            result.update(outcome='accepted', delay_seconds=delay)
        elif status == 429:
            result.update(outcome='rate_limited', delay_seconds=max(delay, result['delay_seconds']))
        elif status in (401, 403, 404) or 300 <= status < 400 or (400 <= status < 500):
            result.update(outcome='permanent_error')
        elif 200 <= status < 300:
            result.update(outcome='ambiguous', ambiguous=True)
        elif status >= 500:
            result.update(outcome='temporary_error')
        else:
            result.update(outcome='ambiguous', ambiguous=True)
    except OverflowError:
        # A valid but unrepresentable retry delay requires owner inspection,
        # never a shortened delay followed by an early retry.
        result.update(outcome='permanent_error', delay_seconds=0, ambiguous=True)
    except (urllib.error.URLError, OSError, socket.timeout, TimeoutError, http.client.HTTPException):
        result.update(outcome='ambiguous', ambiguous=True)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
    return result


def main():
    try:
        data = Path(sys.argv[1])
        action = sys.argv[2]
        if action in ('configure', 'configure-test'):
            result = configure(data, action)
        elif action == 'send':
            result = send(data, json.load(sys.stdin))
        else:
            raise ValueError('Unknown transport operation')
        print(json.dumps(result, allow_nan=False))
        return 0
    except Exception:
        # Exceptions may contain credential URLs, request bodies or headers.
        print('Discord operation refused; check destination, private credential file and local state.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
