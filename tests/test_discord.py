"""Synthetic Discord delivery checks using only an explicitly configured loopback server."""
import http.server
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin/heimdall"


class FakeDiscord(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), FakeWebhook)
        self.requests = []
        self.response_status = 200
        self.response_body = {"id": "123456789012345678"}
        self.response_headers = {}
        self.responses = []
        self.entered = threading.Event()
        self.release = None


class FakeWebhook(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        self.server.requests.append((self.path, json.loads(body)))
        self.server.entered.set()
        if self.server.release is not None:
            self.server.release.wait(8)
        status, response = (self.server.responses.pop(0) if self.server.responses else
                            (self.server.response_status, self.server.response_body))
        self.send_response(status)
        for key, value in self.server.response_headers.items():
            self.send_header(key, value)
        self.end_headers()
        response = json.dumps(response).encode() if isinstance(response, (dict, list)) else response
        try:
            self.wfile.write(response)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *_):
        pass


class DiscordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="heimdall-discord-")
        self.addCleanup(self.tmp.cleanup)
        self.data = Path(self.tmp.name) / "state"
        self.env = dict(os.environ, HEIMDALL_DATA_DIR=str(self.data))
        self.http = FakeDiscord()
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_http)
        self.url = f"http://127.0.0.1:{self.http.server_port}/api/webhooks/123/test-secret"
        self.cli("init")

    def close_http(self):
        if self.http.release:
            self.http.release.set()
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=5)

    def cli(self, *args, data=None, ok=True):
        result = subprocess.run([str(CLI), *args], env=self.env, input=data,
                                text=True, capture_output=True, timeout=20)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def state(self):
        return json.loads((self.data / "state.json").read_text())

    def save_state(self, state):
        (self.data / "state.json").write_text(json.dumps(state))

    def configure(self):
        output = self.cli("discord", "configure-test", data=self.url + "\n")
        self.assertNotIn("test-secret", json.dumps(output))
        self.cli("discord", "enable")

    def burst(self, index=0, count=4, start=None):
        now = int(time.time()) if start is None else start
        records = [{"__CURSOR": f"synthetic-discord:{index}:{i}",
                    "__REALTIME_TIMESTAMP": str((now + i) * 1000000),
                    "MESSAGE": f"Failed password for secret-user from 192.0.2.{index + 1} port 4321 ssh2"}
                   for i in range(count)]
        return self.cli("ingest", "-", data="".join(json.dumps(r) + "\n" for r in records))

    def pending(self):
        return [n for n in self.state().get("notifications", []) if n["status"] == "pending"]

    def make_due(self):
        # Test setup advances persisted retry eligibility without sleeping/backoff bypass in production.
        state = self.state()
        for item in state.get("notifications", []):
            item["next_attempt_at"] = 0
        state["discord"]["retry_after"] = 0
        self.save_state(state)

    def test_disabled_has_no_requests_or_retroactive_queue(self):
        self.burst()
        self.assertEqual(self.state().get("notifications", []), [])
        self.cli("discord", "flush")
        self.assertEqual(self.http.requests, [])
        self.configure()
        self.assertEqual(self.pending(), [])
        self.cli("discord", "disable")
        self.burst(1)
        self.cli("discord", "flush")
        self.assertEqual(self.http.requests, [])
        self.assertEqual(self.pending(), [])

    def test_transition_queue_replay_and_manual_reopen(self):
        self.configure()
        start = int(time.time())
        self.burst(start=start)
        self.assertEqual(len(self.pending()), 1)
        alert_id = self.state()["alerts"][0]["id"]
        self.burst(start=start)
        self.assertEqual(len(self.pending()), 1)
        self.cli("review", alert_id)
        self.cli("reopen", alert_id)
        self.assertEqual(len(self.pending()), 1)
        self.cli("review", alert_id)
        self.burst(count=6, start=start)
        self.assertEqual([n["reason"] for n in self.pending()], ["created", "reopened"])

    def test_recovery_groups_findings_and_disables_mentions(self):
        self.configure()
        self.burst(0)
        self.burst(1)
        self.cli("discord", "flush")
        self.assertEqual(len(self.http.requests), 1)
        path, payload = self.http.requests[0]
        self.assertIn("wait=true", path)
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        self.assertLessEqual(len(payload["content"]), 2000)
        for ip in ("192.0.2.1", "192.0.2.2"):
            self.assertIn(ip, payload["content"])
        self.assertNotIn("secret-user", payload["content"])
        self.assertNotIn("Failed password for", payload["content"])
        self.assertIn("synthetic", payload["content"].lower())
        self.assertEqual(self.pending(), [])
        self.assertTrue(all(n["delivered_at"] is not None for n in self.state()["notifications"]))

    def test_pending_retains_expired_alert_and_supporting_evidence(self):
        self.configure()
        self.burst(start=int(time.time()) - 61 * 86400)
        before = self.state()
        self.cli("cleanup")
        after = self.state()
        self.assertEqual(after["alerts"], before["alerts"])
        self.assertEqual(after["events"], before["events"])
        self.cli("discord", "flush")
        self.cli("cleanup")
        self.assertEqual(self.state()["alerts"], [])
        self.assertEqual(self.state()["events"], [])

    def test_ambiguous_response_retains_queue_across_processes(self):
        self.configure()
        self.burst()
        for status, body in ((204, b""), (200, b"not-json"), (200, {"id": "not-numeric"})):
            with self.subTest(status=status, body=body):
                self.make_due()
                self.http.response_status, self.http.response_body = status, body
                self.cli("discord", "flush")
                self.assertEqual(len(self.pending()), 1)
                self.assertTrue(self.pending()[0]["ambiguous"])
                self.assertGreater(self.pending()[0]["next_attempt_at"], time.time() - 1)
                self.cli("discord", "status")
                self.assertEqual(len(self.pending()), 1)

    def test_server_error_then_recovery(self):
        self.configure()
        self.burst()
        self.http.response_status = 500
        self.cli("discord", "flush")
        self.assertEqual(len(self.pending()), 1)
        self.assertGreater(self.pending()[0]["attempts"], 0)
        self.cli("discord", "flush")
        self.assertEqual(len(self.http.requests), 1, "retry delay ignored")
        self.make_due()
        self.http.response_status = 200
        self.cli("discord", "flush")
        self.assertEqual(self.pending(), [])

    def test_rate_limit_persists_retry_timing(self):
        self.configure()
        self.burst()
        self.http.response_status = 429
        self.http.response_headers = {"Retry-After": "12"}
        self.http.response_body = {"retry_after": 15.5}
        before = time.time()
        self.cli("discord", "flush")
        self.assertEqual(len(self.pending()), 1)
        self.assertGreaterEqual(self.pending()[0]["next_attempt_at"], before + 12)
        self.cli("discord", "flush")
        self.assertEqual(len(self.http.requests), 1)

    def test_invalid_destination_pauses_retries(self):
        self.configure()
        self.burst()
        for status in (401, 403, 404):
            with self.subTest(status=status):
                self.configure()  # Owner correction resumes retained pending work.
                self.make_due()
                self.http.response_status = status
                self.cli("discord", "flush")
                count = len(self.http.requests)
                self.assertEqual(len(self.pending()), 1)
                self.assertTrue(self.state()["discord"]["blocked"])
                self.cli("discord", "enable", ok=False)
                self.cli("discord", "flush")
                self.assertEqual(len(self.http.requests), count)

    def test_redirect_does_not_follow_or_disclose_secret(self):
        self.configure()
        self.burst()
        self.http.response_status = 302
        self.http.response_headers = {"Location": self.url + "/redirected"}
        self.cli("discord", "flush")
        self.assertEqual(len(self.http.requests), 1)
        self.assertEqual(len(self.pending()), 1)
        self.assertNotIn("test-secret", json.dumps(self.state()))
        self.assertNotIn("test-secret", json.dumps(self.cli("discord", "status")))
        secret = self.data / "discord-webhook"
        self.assertEqual(secret.stat().st_mode & 0o777, 0o600)

    def test_production_and_test_url_boundaries(self):
        for url in (self.url, "https://evil.example/api/webhooks/123/secret", "https://discord.com.evil.example/api/webhooks/123/secret",
                    "https://discord.com/api/webhooks/123/secret?wait=true", "https://user:pass@discord.com/api/webhooks/123/secret"):
            with self.subTest(url=url):
                result = self.cli("discord", "configure", data=url + "\n", ok=False)
                self.assertNotIn(url, result.stderr)
        self.cli("discord", "configure-test", data="http://example.com/api/webhooks/123/secret\n", ok=False)
        self.assertEqual(self.http.requests, [])

    def test_concurrent_enqueue_during_delivery_remains_pending(self):
        self.configure()
        self.burst(0)
        self.http.release = threading.Event()
        process = subprocess.Popen([str(CLI), "discord", "flush"], env=self.env,
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertTrue(self.http.entered.wait(5))
            self.burst(1)
            self.http.release.set()
            out, err = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, err)
            self.assertEqual(len(self.pending()), 1)
            self.assertEqual(self.pending()[0]["alert_id"], self.state()["alerts"][1]["id"])
            self.assertEqual(len(self.http.requests), 1)
        finally:
            self.http.release.set()
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_concurrent_flush_cannot_send_same_snapshot_twice(self):
        self.configure()
        self.burst()
        self.http.release = threading.Event()
        process = subprocess.Popen([str(CLI), "discord", "flush"], env=self.env,
                                   text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertTrue(self.http.entered.wait(5))
            self.cli("discord", "flush", ok=False)
            self.assertEqual(len(self.http.requests), 1)
            self.http.release.set()
            _, err = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, err)
            self.assertEqual(self.pending(), [])
        finally:
            self.http.release.set()
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_timeout_keeps_pending_and_durable_ambiguity(self):
        self.configure()
        self.burst()
        self.http.release = threading.Event()
        try:
            self.cli("discord", "flush")
            self.assertEqual(len(self.pending()), 1)
            self.assertTrue(self.pending()[0]["ambiguous"])
            self.assertGreater(self.pending()[0]["next_attempt_at"], time.time())
            self.cli("discord", "status")
            self.assertEqual(len(self.pending()), 1)
        finally:
            self.http.release.set()

    def test_success_exhausted_bucket_delays_later_work(self):
        self.configure()
        self.burst(0)
        self.http.response_headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset-After": "20"}
        before = time.time()
        self.cli("discord", "flush")
        self.assertEqual(self.pending(), [])
        self.assertGreaterEqual(self.state()["discord"]["retry_after"], before + 19)
        self.burst(1)
        self.cli("discord", "flush")
        self.assertEqual(len(self.http.requests), 1)
        self.assertEqual(len(self.pending()), 1)

    def test_nonfinite_rate_limit_is_safe_and_pending(self):
        self.configure()
        self.burst()
        self.http.response_status = 429
        self.http.response_headers = {"Retry-After": "Infinity"}
        self.http.response_body = {"retry_after": "NaN"}
        self.cli("discord", "flush")
        self.assertEqual(len(self.pending()), 1)
        self.assertLess(self.pending()[0]["next_attempt_at"], time.time() + 86401)
        self.assertGreater(self.pending()[0]["next_attempt_at"], time.time())

    def test_fixture_switch_to_production_never_attempts_transport(self):
        self.configure()
        self.burst()
        self.cli("discord", "configure", data="https://discord.com/api/webhooks/123/fake-secret\n")
        self.cli("discord", "enable")
        # Safety guard: all connections are blocked in child Python processes.
        # A marker records even an attempted network operation; no real provider is contacted.
        guard = Path(self.tmp.name) / "transport-guard"
        guard.mkdir()
        marker = guard / "network-attempted"
        (guard / "sitecustomize.py").write_text(
            "import socket\nfrom pathlib import Path\n"
            "def blocked(*a, **kw):\n"
            "    Path(" + repr(str(marker)) + ").touch()\n"
            "    raise OSError('test disallows all network transport')\n"
            "socket.socket.connect = blocked\n"
            "socket.create_connection = blocked\n")
        self.env["PYTHONPATH"] = str(guard)
        self.cli("discord", "flush")
        self.assertFalse(marker.exists(), "fixture destination mismatch attempted transport")
        self.assertEqual(len(self.pending()), 1)
        self.assertEqual(self.http.requests, [])
        self.burst(1)
        self.assertEqual(len(self.pending()), 1, "production fixture transition was enqueued")

    def test_invalid_reconfiguration_disables_existing_destination(self):
        self.configure()
        self.burst()
        self.cli("discord", "configure-test", data="http://evil.example/webhook\n", ok=False)
        self.assertFalse(self.state()["discord"]["enabled"])
        self.cli("discord", "flush")
        self.assertEqual(self.http.requests, [])
        self.assertEqual(len(self.pending()), 1)

    def test_unsafe_credential_files_never_send(self):
        self.configure()
        self.burst()
        credential = self.data / "discord-webhook"
        for kind in ("world-readable", "symlink"):
            with self.subTest(kind=kind):
                self.configure()
                if kind == "world-readable":
                    credential.chmod(0o644)
                else:
                    target = Path(self.tmp.name) / "credential-target"
                    target.write_text(self.url + "\n")
                    target.chmod(0o600)
                    credential.unlink()
                    credential.symlink_to(target)
                self.cli("discord", "flush")
                self.assertEqual(self.http.requests, [])
                self.assertEqual(len(self.pending()), 1)
                credential.unlink()

    def test_partial_chunk_acceptance_keeps_only_unsent_work_pending(self):
        self.configure()
        self.burst()
        state = self.state()
        alert, notification = state["alerts"][0], state["notifications"][0]
        state["alerts"], state["notifications"] = [], []
        for index in range(24):
            aid = "partial-alert-" + str(index)
            state["alerts"].append(dict(alert, id=aid, source_ip=f"198.51.100.{index + 1}"))
            state["notifications"].append(dict(notification, id="partial-notification-" + str(index), alert_id=aid))
        self.save_state(state)
        self.http.responses = [(200, {"id": "123456789012345678"}), (500, b"server failed")]
        self.cli("discord", "flush")
        self.assertEqual(len(self.http.requests), 2)
        after = self.state()
        pending = self.pending()
        delivered = [n for n in after["notifications"] if n["status"] == "delivered"]
        self.assertGreater(len(delivered), 0)
        self.assertGreater(len(pending), 0)
        self.assertEqual(len(delivered) + len(pending), 24)
        first_content = self.http.requests[0][1]["content"]
        self.assertTrue(all(("- " + n["alert_id"] + " [") in first_content for n in delivered))
        self.assertTrue(all(("- " + n["alert_id"] + " [") not in first_content for n in pending))

    def test_chunking_preserves_all_findings(self):
        self.configure()
        # Synthetic queue setup: enough individually distinct alerts to exceed one Discord message.
        self.burst()
        state = self.state()
        alert = state["alerts"][0]
        notification = state["notifications"][0]
        state["alerts"] = []
        state["notifications"] = []
        for index in range(24):
            aid = "synthetic-chunk-alert-" + str(index)
            state["alerts"].append(dict(alert, id=aid, source_ip=f"198.51.100.{index + 1}"))
            state["notifications"].append(dict(notification, id="synthetic-notification-" + str(index), alert_id=aid))
        self.save_state(state)
        self.cli("discord", "flush")
        self.assertGreater(len(self.http.requests), 1)
        combined = "\n".join(payload["content"] for _, payload in self.http.requests)
        for index in range(24):
            self.assertIn(f"198.51.100.{index + 1}", combined)
        self.assertTrue(all(len(payload["content"]) <= 2000 for _, payload in self.http.requests))
        self.assertEqual(self.pending(), [])


if __name__ == "__main__":
    unittest.main()
