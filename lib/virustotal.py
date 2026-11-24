#!/usr/bin/env python3
"""Local VirusTotal credentials, bounded lookup cache, and IP-only HTTPS transport."""
from email.utils import parsedate_to_datetime
from http.client import HTTPException, HTTPSConnection
import ipaddress
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import tempfile
import time

DAY = 86400
TIMEOUT = 3
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
GLOBAL_IPV6 = ipaddress.ip_network('2000::/3')
SPECIAL_IPV4 = tuple(map(ipaddress.ip_network, ('192.0.0.0/24', '192.88.99.0/24')))
SPECIAL_IPV6 = tuple(map(ipaddress.ip_network, ('2001::/23', '2002::/16', '3fff::/20')))


def eligible_ip(value):
    if not isinstance(value, str) or '%' in value:
        return None
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return None
    if not address.is_global or address.is_multicast or address.is_reserved:
        return None
    if address.version == 6:
        if address not in GLOBAL_IPV6 or any(address in network for network in SPECIAL_IPV6):
            return None
    elif any(address in network for network in SPECIAL_IPV4):
        return None
    return str(address)


def write_private(path, value):
    fd, name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(value + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def read_private(path, limit):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, encoding='utf-8') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.geteuid():
            raise ValueError('Invalid private file')
        value = stream.read(limit + 1)
        if len(value) > limit:
            raise ValueError('Private file exceeds limit')
        return value


def validate_key(value):
    key = value.removesuffix('\n').removesuffix('\r')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,256}', key):
        raise ValueError('Expected one API key')
    return key


def provider_status(path):
    try:
        validate_key(read_private(path, 258))
    except FileNotFoundError:
        return 'disabled'
    except (OSError, ValueError):
        return 'needs_configuration'
    return 'configured'


def reputation(now, flags=None, reason=None, provenance='live', from_cache=False):
    if flags is None:
        label = 'Unknown'
    else:
        label = next(label for minimum, label in (
            (10, 'Very high concern'), (7, 'High concern'), (4, 'Medium concern'),
            (1, 'Low concern'), (0, 'No flags found'),
        ) if flags >= minimum)
    return {'label': label, 'flags': flags, 'checked_at': now, 'provenance': provenance,
            'reason': reason, 'from_cache': from_cache}


def retry_deadline(value, now):
    if value:
        try:
            if re.fullmatch(r'[0-9]{1,20}', value):
                return now + int(value)
            return int(parsedate_to_datetime(value).timestamp())
        except (ValueError, TypeError, OverflowError):
            pass
    return now + DAY


def fetch(address, key):
    def expire(signum, frame):
        raise TimeoutError('VirusTotal lookup deadline exceeded')

    connection = HTTPSConnection('www.virustotal.com', timeout=TIMEOUT)
    previous_handler = signal.signal(signal.SIGALRM, expire)
    signal.setitimer(signal.ITIMER_REAL, TIMEOUT)
    try:
        connection.request('GET', '/api/v3/ip_addresses/' + address,
                           headers={'Accept': 'application/json', 'x-apikey': key})
        with connection.getresponse() as response:
            if response.status == 429:
                return None, 'VirusTotal rate limit or quota reached', retry_deadline(
                    response.getheader('Retry-After'), int(time.time()))
            if response.status in (401, 403):
                return None, 'VirusTotal rejected the configured key or access', 0
            if response.status == 404:
                return None, 'VirusTotal has no IP report', 0
            if response.status != 200:
                return None, 'VirusTotal lookup unavailable', 0
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError('Response exceeds limit')
        report = json.loads(raw)['data']
        if report['type'] != 'ip_address' or ipaddress.ip_address(report['id']) != ipaddress.ip_address(address):
            raise ValueError('Unexpected IP report')
        stats = report['attributes']['last_analysis_stats']
        counts = [stats[name] for name in ('malicious', 'suspicious')]
        if not all(type(count) is int and 0 <= count <= 10000 for count in counts):
            raise ValueError('Invalid vendor counts')
        return sum(counts), None, 0
    except (OSError, HTTPException):
        return None, 'VirusTotal lookup unavailable', 0
    except (KeyError, TypeError, ValueError, RecursionError):
        return None, 'VirusTotal returned no usable vendor counts', 0
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        connection.close()


def lookup(data, value):
    now = int(time.time())
    address = eligible_ip(value)
    if address is None:
        return reputation(now, reason='Source IP is not eligible for external lookup')
    try:
        key = validate_key(read_private(data / 'virustotal-key', 258))
    except (OSError, ValueError):
        return reputation(now, reason='VirusTotal API key is unavailable')

    path = data / 'virustotal-cache.json'
    try:
        store = json.loads(read_private(path, 128 * 1024))
    except FileNotFoundError:
        store = {'cache': {}, 'requests': [], 'retry_at': 0}
    requests = [at for at in store['requests'] if at > now - DAY]
    cache = {ip: entry for ip, entry in store['cache'].items()
             if 0 <= now - entry['checked_at'] < DAY}
    if address in cache:
        entry = cache[address]
        return reputation(entry['checked_at'], entry['flags'], from_cache=True)
    if store['retry_at'] > now:
        return reputation(now, reason='VirusTotal is in provider rate-limit cooldown')
    if len(requests) >= 500 or sum(at > now - 60 for at in requests) >= 4:
        return reputation(now, reason='Local VirusTotal request limit reached')

    # Persist the quota reservation before sending, even if the process stops.
    store.update(requests=requests + [now], cache=cache)
    write_private(path, json.dumps(store))
    flags, reason, retry_at = fetch(address, key)
    checked_at = int(time.time())
    if retry_at > 0:
        store['retry_at'] = max(checked_at + 60, retry_at)
    if flags is not None:
        cache[address] = {'checked_at': checked_at, 'flags': flags}
        if len(cache) > 256:
            del cache[min(cache, key=lambda ip: cache[ip]['checked_at'])]
    if retry_at > 0 or flags is not None:
        write_private(path, json.dumps(store))
    return reputation(checked_at, flags, reason)


def main(data, action, *args):
    key_path = data / 'virustotal-key'
    if action == 'status':
        return provider_status(key_path)
    if action == 'configure':
        write_private(key_path, validate_key(sys.stdin.read(259)))
        return {'provider_state': 'configured'}
    if action == 'disable':
        key_path.unlink(missing_ok=True)
        return {'provider_state': 'disabled'}

    target = json.load(sys.stdin)
    if action == 'simulate':
        if target['mode'] != 'fixture' or target['provenance'] != 'fixture':
            raise ValueError('Simulation requires fixture state')
        if not re.fullmatch(r'[0-9]{1,4}', args[0]):
            raise ValueError('Simulation requires an integer from 0 to 9999')
        result = reputation(int(time.time()), int(args[0]), provenance='simulated')
    elif action == 'lookup' and target['mode'] == 'live' and target['provenance'] == 'journal':
        result = lookup(data, target['source_ip'])
    else:
        raise ValueError('Live lookups require a journal alert')
    return {'target': target, 'reputation': result}


if __name__ == '__main__':
    try:
        print(json.dumps(main(Path(sys.argv[1]), *sys.argv[2:])))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError):
        sys.exit('VirusTotal operation refused. Check the command, alert provenance, private key or local cache.')
