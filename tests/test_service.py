"""Process-boundary service-manager tests; no real systemd or privileges required."""
import getpass
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin/heimdall"
UNIT = "heimdall-monitor.service"

FAKE_MANAGER = '''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
base = Path(os.environ["FAKE_MANAGER_DIR"])
args = sys.argv[1:]
with (base / "calls").open("a") as out:
    out.write(json.dumps(args) + "\\n")
if "show" in args:
    if (base / "hang").exists(): time.sleep(30)
    if (base / "slow").exists(): time.sleep(1.2)
    print((base / "properties").read_text(), end="")
    sys.exit(0)
if "start" in args or "stop" in args:
    if (base / "deny").exists():
        print("Access denied: interactive authentication required", file=sys.stderr)
        sys.exit(1)
    text = (base / "properties").read_text()
    if "start" in args:
        text = text.replace("ActiveState=inactive", "ActiveState=active").replace("SubState=dead", "SubState=running")
    else:
        text = text.replace("ActiveState=active", "ActiveState=inactive").replace("SubState=running", "SubState=dead").replace("MainPID=12345", "MainPID=0")
    (base / "properties").write_text(text)
    sys.exit(0)
print("Unexpected manager operation", file=sys.stderr)
sys.exit(2)
'''


class ServiceManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="heimdall-service-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.data = self.base / "state"
        mock = self.base / "mock"
        mock.mkdir()
        manager = mock / "systemctl"
        manager.write_text(FAKE_MANAGER)
        manager.chmod(0o700)
        # Detached fallback is observable and cannot accidentally start a monitor.
        for name in ("nohup", "sudo", "journalctl"):
            script = mock / name
            script.write_text('#!/bin/sh\nprintf "%s\\n" "$0" >> "$FAKE_MANAGER_DIR/forbidden"\nexit 99\n')
            script.chmod(0o700)
        self.env = dict(os.environ, HEIMDALL_DATA_DIR=str(self.data),
                        HEIMDALL_MONITOR_MANAGER="systemd",
                        FAKE_MANAGER_DIR=str(self.base),
                        PATH=str(mock) + ":" + os.environ["PATH"])
        self.properties = {
            "LoadState": "loaded", "ActiveState": "inactive", "SubState": "dead",
            "MainPID": "0", "Result": "success", "NRestarts": "0",
            "WorkingDirectory": str(ROOT), "Environment": "HEIMDALL_DATA_DIR=" + str(self.data),
            "ExecStart": "{ path=" + str(CLI) + " ; argv[]=" + str(CLI) + " monitor run ; ignore_errors=no ; start_time=[n/a] ; stop_time=[n/a] ; pid=0 ; code=(null) ; status=0/0 }",
            "User": getpass.getuser(),
        }
        self.write_properties()

    def write_properties(self, extra=""):
        (self.base / "properties").write_text("".join(f"{k}={v}\n" for k, v in self.properties.items()) + extra)

    def cli(self, *args, ok=True, data=None):
        result = subprocess.run([str(CLI), *args], env=self.env, input=data, capture_output=True, text=True, timeout=15)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def calls(self):
        path = self.base / "calls"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def assert_no_fallback(self):
        self.assertFalse((self.base / "forbidden").exists(), "managed instance fell back to a detached process or sudo")

    def test_start_and_stop_use_fixed_noninteractive_unit(self):
        self.cli("monitor", "start")
        self.cli("monitor", "stop")
        mutations = [args for args in self.calls() if "start" in args or "stop" in args]
        self.assertEqual(len(mutations), 2)
        for args, action in zip(mutations, ("start", "stop")):
            self.assertIn("--no-ask-password", args)
            self.assertEqual(args[-2:], [action, UNIT])
        self.assert_no_fallback()

    def test_inactive_and_failed_unit_are_never_healthy(self):
        for active, sub, result in (("inactive", "dead", "success"), ("failed", "failed", "start-limit-hit")):
            with self.subTest(active=active):
                self.properties.update(ActiveState=active, SubState=sub, Result=result)
                self.write_properties()
                monitor = self.cli("status")["monitor"]
                self.assertEqual(monitor["manager"], "systemd")
                self.assertEqual(monitor["coverage"], "unavailable")
                self.assertNotEqual(monitor["state"], "running")

    def test_auto_detects_installed_manager(self):
        self.env.pop("HEIMDALL_MONITOR_MANAGER")
        self.assertEqual(self.cli("status")["monitor"]["manager"], "systemd")
        self.cli("monitor", "start")
        self.assertTrue(any("start" in args for args in self.calls()))
        self.assert_no_fallback()

    def test_installed_unit_refuses_manual_foreground_reader(self):
        self.env["INVOCATION_ID"] = "spoofed-service-marker"
        self.cli("monitor", "run", ok=False)
        self.assert_no_fallback()
        self.assertFalse(any("start" in args or "stop" in args for args in self.calls()))

    def test_auto_absent_unit_keeps_offline_state_useful(self):
        self.env.pop("HEIMDALL_MONITOR_MANAGER")
        self.properties["LoadState"] = "not-found"
        self.write_properties()
        self.assertEqual(self.cli("status")["monitor"]["manager"], "standalone")
        self.cli("ingest", "-", data="")
        self.assertEqual(self.cli("status")["mode"], "fixture")
        self.assert_no_fallback()

    def test_standalone_selection_cannot_bypass_installed_unit(self):
        self.env["HEIMDALL_MONITOR_MANAGER"] = "standalone"
        self.cli("monitor", "start", ok=False)
        self.cli("monitor", "stop", ok=False)
        self.assertFalse(any("start" in a or "stop" in a for a in self.calls()))
        self.assert_no_fallback()

    def test_service_stop_does_not_signal_recorded_process(self):
        sentinel = subprocess.Popen(["sleep", "30"])
        try:
            self.cli("init")
            path = self.data / "state.json"
            state = json.loads(path.read_text())
            state["monitor"].update(pid=sentinel.pid, state="running", coverage="available")
            path.write_text(json.dumps(state))
            self.properties.update(ActiveState="active", SubState="running", MainPID="12345")
            self.write_properties()
            monitor = self.cli("status")["monitor"]
            self.assertEqual(monitor["coverage"], "unavailable")
            self.cli("monitor", "stop")
            self.assertIsNone(sentinel.poll(), "service stop directly signalled a saved PID")
            self.assertTrue(any("stop" in args for args in self.calls()))
        finally:
            sentinel.terminate()
            sentinel.wait(timeout=5)

    def test_offline_fixture_status_does_not_depend_on_service(self):
        self.cli("ingest", "-", data="")
        monitor = self.cli("status")["monitor"]
        self.assertEqual(monitor["coverage"], "unavailable")
        self.assertNotEqual(monitor["state"], "running")

    def test_permission_denial_never_falls_back(self):
        (self.base / "deny").touch()
        for action in ("start", "stop"):
            failure = self.cli("monitor", action, ok=False)
            self.assertIn("systemctl", failure.stderr)
        self.assert_no_fallback()

    def test_wrong_identity_is_rejected_without_mutation(self):
        for key, value in (("WorkingDirectory", "/other/release"), ("Environment", "HEIMDALL_DATA_DIR=/other/state"), ("User", "another-owner"), ("ExecStart", "/bin/echo monitor run")):
            original = self.properties[key]
            with self.subTest(key=key):
                self.properties[key] = value
                self.write_properties()
                self.cli("monitor", "start", ok=False)
                self.cli("monitor", "stop", ok=False)
            self.properties[key] = original
        self.assertFalse(any("start" in a or "stop" in a for a in self.calls()))
        self.assert_no_fallback()

    def test_ambiguous_properties_are_rejected(self):
        self.write_properties("Environment=HEIMDALL_DATA_DIR=" + str(self.data) + "\n")
        self.cli("monitor", "start", ok=False)
        self.assertFalse(any("start" in a for a in self.calls()))
        self.assert_no_fallback()

    def test_slow_manager_status_is_still_available(self):
        (self.base / "slow").touch()
        self.assertEqual(self.cli("status")["monitor"]["manager"], "systemd")
        self.assert_no_fallback()

    def test_manager_timeout_is_bounded_and_never_falls_back(self):
        (self.base / "hang").touch()
        self.cli("monitor", "start", ok=False)
        self.assert_no_fallback()

    def test_untrusted_property_text_is_never_executed(self):
        marker = self.base / "injected"
        self.properties["ExecStart"] = "$(touch " + str(marker) + ")"
        self.write_properties()
        self.cli("monitor", "start", ok=False)
        self.assertFalse(marker.exists())
        self.assert_no_fallback()


if __name__ == "__main__":
    unittest.main()
