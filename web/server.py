#!/usr/bin/env python3
"""Local-only HTTP bridge to the Heimdall shell interface."""
import argparse
import hmac
from ipaddress import IPv4Address
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
from threading import Lock
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
CONFIG_BOUNDS = json.loads((ROOT.parent / "lib" / "config-policy.json").read_text())
ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
LIMIT = 16384
SESSION_SECONDS = 8 * 60 * 60
MAX_SESSIONS = 128


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        # Avoid reverse DNS lookup; listener addresses are explicitly configured.
        from socketserver import TCPServer

        TCPServer.server_bind(self)
        self.server_name, self.server_port = self.server_address[:2]

    def __init__(self, address, cli, data):
        host, port = address
        ip = IPv4Address("127.0.0.1" if host == "localhost" else host)
        if ip.is_unspecified or ip.is_multicast or ip == IPv4Address("255.255.255.255"):
            raise ValueError("Use a specific local IPv4 address for --host")
        address = (str(ip), port)
        self.cli, self.data = str(Path(cli).resolve()), Path(data)
        if self.data.is_symlink():
            raise ValueError("State directory must not be a symbolic link")
        super().__init__(address, Handler)
        self.data.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.data, 0o700)
        token_file = self.data / "web-token"
        try:
            fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(secrets.token_urlsafe(32))
        except FileExistsError:
            pass
        if token_file.is_symlink() or not token_file.is_file():
            raise ValueError("Invalid token file")
        os.chmod(token_file, 0o600)
        self.token = token_file.read_text().strip()
        if not self.token:
            raise ValueError("Empty token file")
        self.sessions, self.attempts = {}, {}
        self.auth_lock = Lock()
        self.allowed = {f"{address[0]}:{self.server_port}"}
        if address[0] == "127.0.0.1":
            self.allowed.add(f"localhost:{self.server_port}")
        try:
            self.call(["init"])
        except ValueError:
            pass  # The UI reports an unavailable CLI on requests.

    def call(self, args, report=False):
        env = os.environ.copy()
        env["HEIMDALL_DATA_DIR"] = str(self.data)
        try:
            p = subprocess.run(
                [self.cli, *args],
                shell=False,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if p.returncode:
                if (
                    p.returncode == 77
                    and args in (["monitor", "start"], ["monitor", "stop"])
                    and p.stderr.startswith("HEIMDALL_SERVICE_CONTROL:")
                ):
                    raise ValueError(
                        "Monitor service control failed. Check the monitor status and "
                        "the unit's configured owner, release and state paths. An "
                        "administrator may need to run: sudo systemctl "
                        + args[1]
                        + " heimdall-monitor.service"
                    )
                raise ValueError(
                    "Heimdall command failed. Check the local CLI and state."
                )
            return p.stdout if report else json.loads(p.stdout)
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            raise ValueError("Heimdall CLI is unavailable or returned invalid output.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, status, data, kind="application/json; charset=utf-8", extra=None):
        if kind.startswith("application/json"):
            data = json.dumps(data).encode()
        elif isinstance(data, str):
            data = data.encode()
        self.send_response(status)
        for k, v in {
            "Content-Type": kind,
            "Content-Length": str(len(data)),
            "Cache-Control": "no-store, private",
            "Content-Security-Policy": "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            **(extra or {}),
        }.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def fail(self, status, message):
        self.reply(status, {"error": message})

    def host_ok(self):
        return self.headers.get("Host", "").lower() in self.server.allowed

    def origin_ok(self):
        origin = self.headers.get("Origin")
        return bool(
            origin
            and origin.lower() == "http://" + self.headers.get("Host", "").lower()
        )

    def session(self):
        from http.cookies import SimpleCookie, CookieError

        try:
            c = SimpleCookie()
            c.load(self.headers.get("Cookie", ""))
            key = c["session"].value if "session" in c else ""
            with self.server.auth_lock:
                value = self.server.sessions.get(key)
                if value and value["expires"] > time.monotonic():
                    return value["csrf"], key
                self.server.sessions.pop(key, None)
            return None, ""
        except CookieError:
            return None, ""

    def body(self):
        if (
            self.headers.get("Content-Type", "").split(";")[0].strip().lower()
            != "application/json"
        ):
            raise ValueError("Expected application/json.")
        n = self.headers.get("Content-Length", "")
        if not n.isdigit() or int(n) > LIMIT:
            raise ValueError("Invalid or oversized request body.")
        self.connection.settimeout(5)
        try:
            obj = json.loads(self.rfile.read(int(n)))
        except (ValueError, TimeoutError, RecursionError):
            raise ValueError("Invalid JSON body.")
        if not isinstance(obj, dict):
            raise ValueError("Expected a JSON object.")
        return obj

    def do_GET(self):
        self.dispatch(False)

    def do_POST(self):
        self.dispatch(True)

    def dispatch(self, post):
        if not self.host_ok():
            return self.fail(400, "Invalid Host.")
        # BaseHTTPRequestHandler normalizes leading double slashes in self.path.
        target = self.requestline.split()[1]
        if not target.startswith("/") or any(
            marker in target for marker in ("?", "#", "%", "//")
        ):
            return self.fail(404, "Not found.")
        path = target
        pages = ("/", "/overview", "/investigations", "/activity", "/settings")
        assets = {
            "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/style.css": ("style.css", "text/css; charset=utf-8"),
            "/fonts/JetBrainsMono-Regular.woff2": (
                "fonts/JetBrainsMono-Regular.woff2",
                "font/woff2",
            ),
            "/fonts/JetBrainsMono-Medium.woff2": (
                "fonts/JetBrainsMono-Medium.woff2",
                "font/woff2",
            ),
        }
        if not post and (path in pages or path in assets):
            name, kind = (
                ("index.html", "text/html; charset=utf-8")
                if path in pages
                else assets[path]
            )
            return self.reply(200, (ROOT / "static" / name).read_bytes(), kind)
        session, key = self.session()
        if post and not self.origin_ok():
            return self.fail(403, "Invalid Origin.")
        if path == "/api/session" and not post:
            return self.reply(
                200,
                {
                    "authenticated": bool(session),
                    **({"csrf": session} if session else {}),
                },
            )
        if path == "/api/login" and post:
            try:
                body = self.body()
            except ValueError as e:
                return self.fail(400, str(e))
            with self.server.auth_lock:
                status, value = self.login(body.get("token"))
            if status != 200:
                return self.fail(status, value)
            key, csrf = value
            return self.reply(
                200,
                {"csrf": csrf},
                extra={
                    "Set-Cookie": f"session={key}; Max-Age={SESSION_SECONDS}; HttpOnly; SameSite=Strict; Path=/"
                },
            )
        if not session:
            return self.fail(401, "Sign in required.")
        if post and not hmac.compare_digest(
            self.headers.get("X-CSRF-Token", "").encode(), session.encode()
        ):
            return self.fail(403, "Invalid CSRF token.")
        if post and path != "/api/config":
            try:
                self.body()
            except ValueError as e:
                return self.fail(400, str(e))
        if post and path == "/api/logout":
            with self.server.auth_lock:
                self.server.sessions.pop(key, None)
            return self.reply(
                200,
                {"ok": True},
                extra={
                    "Set-Cookie": "session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/"
                },
            )
        args = None
        report = False
        if not post:
            args = {
                "/api/status": ["status"],
                "/api/alerts": ["alerts"],
                "/api/events": ["events"],
                "/api/config": ["config", "get"],
            }.get(path)
        match = re.fullmatch(r"/api/alerts/([^/]+)(?:/(report|review|reopen))?", path)
        if match and ID.fullmatch(match[1]):
            action = match[2]
            if not post and action in (None, "report"):
                args = [action or "inspect", match[1]]
                report = action == "report"
            elif post and action in ("review", "reopen"):
                args = [action, match[1]]
        if post and path in ("/api/monitor/start", "/api/monitor/stop"):
            args = ["monitor", path.rsplit("/", 1)[1]]
        if post and path == "/api/config":
            try:
                body = self.body()
                if not body or any(
                    k not in CONFIG_BOUNDS
                    or type(v) is not int
                    or not CONFIG_BOUNDS[k][0] <= v <= CONFIG_BOUNDS[k][1]
                    for k, v in body.items()
                ):
                    raise ValueError("Invalid configuration values.")
                args = ["config", "set", json.dumps(body, separators=(",", ":"))]
            except ValueError as e:
                return self.fail(400, str(e))
        if args is None:
            return self.fail(404, "Not found.")
        try:
            result = self.server.call(args, report)
        except ValueError as e:
            return self.fail(503, str(e))
        return self.reply(
            200,
            result,
            (
                "text/plain; charset=utf-8"
                if report
                else "application/json; charset=utf-8"
            ),
            (
                {"Content-Disposition": 'attachment; filename="heimdall-report.txt"'}
                if report
                else None
            ),
        )

    def login(self, token):
        addr = self.client_address[0]
        now = time.monotonic()
        attempts = [t for t in self.server.attempts.get(addr, []) if now - t < 60]
        if len(attempts) >= 5:
            return 429, "Too many attempts. Try again later."
        try:
            valid = isinstance(token, str) and hmac.compare_digest(
                token.encode(), self.server.token.encode()
            )
        except UnicodeEncodeError:
            valid = False
        if not valid:
            attempts.append(now)
            self.server.attempts[addr] = attempts
            return 401, "Invalid token."
        self.server.attempts.pop(addr, None)
        key, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        if len(self.server.sessions) >= MAX_SESSIONS:
            oldest = min(self.server.sessions, key=lambda sid: self.server.sessions[sid]["expires"])
            self.server.sessions.pop(oldest)
        self.server.sessions[key] = {"csrf": csrf, "expires": now + SESSION_SECONDS}
        return 200, (key, csrf)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--cli", default=str(ROOT.parent / "bin" / "heimdall"))
    a = p.parse_args()
    state_home = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    data = os.environ.get("HEIMDALL_DATA_DIR") or state_home / "heimdall"
    try:
        server = Server((a.host, a.port), a.cli, data)
    except (ValueError, OSError) as e:
        p.error(str(e))
    print("Owner token file:", server.data / "web-token", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
