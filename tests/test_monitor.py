import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

CLI = Path(__file__).resolve().parents[1] / "bin/heimdall"


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        # Tests must never discover/control a real installed host service.
        manager_bin = Path(self.directory.name) / "isolated-manager"
        manager_bin.mkdir()
        manager = manager_bin / "systemctl"
        manager.write_text("#!/bin/sh\nprintf '%s\\n' 'LoadState=not-found'\n")
        manager.chmod(0o700)
        self.env = dict(
            os.environ, HEIMDALL_DATA_DIR=self.directory.name,
            HEIMDALL_MONITOR_MANAGER="auto",
            PATH=str(manager_bin) + ":" + os.environ["PATH"],
        )

    def cli(self, *args, data=None, ok=True):
        p = subprocess.run(
            [str(CLI), *args], input=data, text=True, capture_output=True, env=self.env
        )
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
            return json.loads(p.stdout)
        self.assertNotEqual(p.returncode, 0, p.stdout)

    def event(self, i, t, ip="10.37.129.4", user="alice", verb="Failed"):
        return {
            "__CURSOR": f"synthetic:{i}",
            "__REALTIME_TIMESTAMP": str(int(t * 1000000)),
            "MESSAGE": f"{verb} password for {user} from {ip} port 4321 ssh2",
        }

    def ingest(self, *records):
        return self.cli(
            "ingest", "-", data="".join(json.dumps(r) + "\n" for r in records)
        )

    def test_threshold_replay_review_and_success(self):
        events = [self.event(i, 1000 + i * 30, user=f"user{i}") for i in range(4)]
        self.ingest(*events[:3])
        self.assertEqual(self.cli("alerts"), [])
        self.ingest(events[3])
        alert = self.cli("alerts")[0]
        self.assertEqual(alert["failure_count"], 4)
        self.assertEqual(self.ingest(*events)["duplicates"], 4)
        self.cli("review", alert["id"])
        self.ingest(self.event(4, 1140))
        record = self.cli("inspect", alert["id"])
        self.assertEqual(record["review_status"], "needs_review")
        self.assertEqual(record["review_history"][-1]["reason"], "new_failure")
        self.assertEqual(len(record["events"]), 5)
        self.ingest(self.event(5, 1150, verb="Accepted"))
        self.assertEqual(self.cli("events")[0]["preceding_failures"], 1)

    def test_expiry_and_separate_ips(self):
        self.ingest(*[self.event(i, 1000 + i * 110) for i in range(4)])
        self.assertEqual(self.cli("alerts"), [])
        self.ingest(*[self.event(10 + i, 1400 + i, ip="10.37.129.5") for i in range(3)])
        self.assertEqual(self.cli("alerts"), [])
        self.ingest(self.event(20, 1404, ip="10.37.129.5"))
        self.assertEqual(self.cli("alerts")[0]["source_ip"], "10.37.129.5")

    def test_quiet_boundary_and_late(self):
        self.ingest(*[self.event(i, 1000 + i) for i in range(4)])
        self.ingest(self.event(9, 900))
        self.assertEqual(self.cli("alerts")[0]["failure_count"], 4)
        self.ingest(*[self.event(10 + i, 1303 + i) for i in range(4)])
        self.assertEqual(len(self.cli("alerts")), 2)

    def test_late_failure_remains_evidence_without_counting_in_later_rules(self):
        self.ingest(self.event(1, 1000), self.event(2, 1020), self.event(3, 1010))
        self.assertIn("Late record", self.cli("events")[0]["notes"][-1])
        self.ingest(self.event(4, 1030))
        self.assertEqual(self.cli("alerts"), [])
        self.ingest(self.event(5, 1035, verb="Accepted"))
        self.assertEqual(self.cli("events")[0]["preceding_failures"], 3)
        self.ingest(self.event(6, 1040))
        alert = self.cli("inspect", self.cli("alerts")[0]["id"])
        self.assertEqual([event["cursor"] for event in alert["events"]],
                         ["synthetic:1", "synthetic:2", "synthetic:4", "synthetic:6"])

    def test_inclusive_rolling_boundary(self):
        self.ingest(*[self.event(i, 1000 + i * 100) for i in range(4)])
        self.assertEqual(self.cli("alerts")[0]["failure_count"], 4)

    def test_invalid_user_and_fingerprint_replay(self):
        e = self.event(1, 1000, user="invalid user visitor")
        del e["__CURSOR"]
        self.ingest(e)
        self.assertTrue(self.cli("events")[0]["invalid_user"])
        self.assertEqual(self.ingest(e)["duplicates"], 1)

    def test_journal_ingestion_requires_an_active_monitor(self):
        self.cli("init")
        self.cli("_journal_ingest", "-", data=json.dumps(self.event(1, 1000)), ok=False)
        self.assertEqual(self.cli("events"), [])

    def test_fixture_ingestion_cannot_replace_live_state_with_a_saved_cursor(self):
        self.cli("init")
        state = Path(self.directory.name) / "state.json"
        value = json.loads(state.read_text())
        value["cursor"] = "saved-after-pruning-events"
        state.write_text(json.dumps(value))
        self.cli("ingest", "-", data=json.dumps(self.event(1, 1000)), ok=False)
        self.assertEqual(json.loads(state.read_text()), value)

    def test_non_record_journal_probe_leaves_coverage_unavailable(self):
        mock = Path(self.directory.name) / "mock"
        mock.mkdir()
        journal = mock / "journalctl"
        journal.write_text("#!/bin/sh\nprintf '%s\\n' 'No usable records'\n")
        journal.chmod(0o700)
        self.env["PATH"] = str(mock) + ":" + self.env["PATH"]

        self.cli("monitor", "run", ok=False)
        status = self.cli("status")["monitor"]
        self.assertEqual(status["state"], "error")
        self.assertEqual(status["coverage"], "unavailable")
        self.assertIn("SSH journal unavailable", status["last_error"])

    def test_lost_journal_cursor_fails_closed(self):
        self.cli("init")
        state = Path(self.directory.name) / "state.json"
        value = json.loads(state.read_text())
        value["cursor"] = "lost-reference"
        state.write_text(json.dumps(value))
        mock = Path(self.directory.name) / "mock"
        mock.mkdir()
        journal = mock / "journalctl"
        journal.write_text(
            "#!/bin/bash\nprintf '%s\\n' '" + json.dumps(self.event(1, 1000)) + "'\n"
        )
        journal.chmod(0o700)
        self.env["PATH"] = str(mock) + ":" + self.env["PATH"]
        self.cli("monitor", "run", ok=False)
        status = self.cli("status")["monitor"]
        self.assertEqual(status["state"], "error")
        self.assertEqual(status["coverage"], "unavailable")
        self.assertIn("cursor", status["last_error"])

    def test_missing_invalid_unsupported_and_injection(self):
        bad = self.event(1, 1000, ip="999.999.1.1")
        missing = self.event(2, 1001)
        del missing["__REALTIME_TIMESTAMP"]
        supporting = self.event(3, 1002)
        supporting["MESSAGE"] = (
            "pam_unix authentication failure $(touch /tmp/heimdall-must-not-run)"
        )
        result = self.ingest(bad, missing, supporting)
        self.assertEqual(result["unsupported"], 1)
        self.assertEqual(self.cli("alerts"), [])
        self.assertEqual(self.cli("events")[-1]["source_ip"], None)
        self.assertEqual(self.cli("ingest", "-", data="bad json\n42\n")["malformed"], 2)

    def test_ipv6_and_missing_username(self):
        self.ingest(
            *[
                self.event(
                    i,
                    1000 + i,
                    ip=("2001:db8::1" if i % 2 else "2001:0db8:0:0:0:0:0:1"),
                    user="",
                )
                for i in range(4)
            ]
        )
        self.assertEqual(self.cli("alerts")[0]["source_ip"], "2001:db8::1")
        self.assertEqual(self.cli("alerts")[0]["failure_count"], 4)

    def test_config_retention_and_permissions(self):
        self.cli("config", "set", '{"threshold":2}')
        self.ingest(self.event(1, 1000), self.event(2, 1001))
        self.assertEqual(len(self.cli("alerts")), 1)
        path = Path(self.directory.name) / "state.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(len(json.loads(path.read_text())["config_history"]), 1)
        self.cli("cleanup")
        self.assertEqual(self.cli("alerts"), [])
        self.assertEqual(self.cli("events"), [])

    def test_corrupt_state_preserved(self):
        self.cli("init")
        path = Path(self.directory.name) / "state.json"
        path.write_text("{broken")
        self.cli("init", ok=False)
        self.assertEqual(path.read_text(), "{broken")

    def test_retention_preserves_untimed_evidence(self):
        event = self.event(1, 1000)
        del event["__REALTIME_TIMESTAMP"]
        self.ingest(event)
        self.cli("cleanup")
        self.assertEqual(len(self.cli("events")), 1)
        self.assertIsNone(self.cli("events")[0]["timestamp"])

    def test_mock_journal_lifecycle_and_resume(self):
        mock = Path(self.directory.name) / "mock"
        mock.mkdir()
        journal = mock / "journalctl"
        record = json.dumps(self.event(1, 1000))
        journal.write_text(
            '#!/bin/bash\ncase " $* " in\n*" --follow "*) printf \'%s\\n\' \''
            + record
            + "'; sleep 20 ;;\n*) printf '%s\\n' '"
            + record
            + "' ;;\nesac\n"
        )
        journal.chmod(0o700)
        self.env["PATH"] = str(mock) + ":" + self.env["PATH"]
        try:
            self.cli("monitor", "start")
            import time

            for _ in range(50):
                if self.cli("events"):
                    break
                time.sleep(0.02)
            self.assertEqual(len(self.cli("events")), 1)
            self.assertEqual(self.cli("status")["monitor"]["coverage"], "available")
            self.cli("ingest", "-", data="{}\n", ok=False)
            self.cli("monitor", "start")
            self.assertEqual(len(self.cli("events")), 1)
            self.cli("monitor", "stop")
            self.assertEqual(self.cli("status")["monitor"]["state"], "stopped")
            self.cli("monitor", "start")
            self.assertEqual(len(self.cli("events")), 1)
        finally:
            self.cli("monitor", "stop")

    def test_live_unavailable(self):
        self.assertEqual(self.cli("status")["monitor"]["coverage"], "unavailable")
        if subprocess.run(["which", "journalctl"], capture_output=True).returncode:
            self.cli("monitor", "run", ok=False)
            status = self.cli("status")["monitor"]
            self.assertEqual(status["coverage"], "unavailable")
            self.assertIn("journal", status["last_error"].lower())

    def test_help_and_version_do_not_create_state(self):
        p = subprocess.run(
            [str(CLI), "help"], env=self.env, text=True, capture_output=True
        )
        self.assertEqual(p.returncode, 0)
        self.assertIn("monitor start|stop|run", p.stdout)
        self.assertFalse((Path(self.directory.name) / "state.json").exists())
        p = subprocess.run(
            [str(CLI), "version"], env=self.env, text=True, capture_output=True
        )
        self.assertEqual(p.stdout.strip(), "0.1.0")

    def test_sanitized_ubuntu_export(self):
        sample = CLI.parent.parent / "tests/fixtures/ubuntu-password-sanitized.jsonl"
        result = self.cli("ingest", str(sample))
        self.assertEqual(result["processed"], 3)
        self.assertEqual(result["unsupported"], 0)
        events = self.cli("events")
        self.assertEqual(sum(e["outcome"] == "failure" for e in events), 2)
        self.assertEqual(sum(e["outcome"] == "success" for e in events), 1)
        self.assertEqual(sum(e["invalid_user"] is True for e in events), 1)
        self.assertTrue(all(e["provenance"] == "fixture" for e in events))

    def test_config_history_and_concurrent_changes(self):
        self.cli("init")
        patches = ['{"threshold":5}', '{"window_seconds":400}', '{"retention_days":50}']
        processes = [
            subprocess.Popen(
                [str(CLI), "config", "set", p],
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for p in patches
        ]
        for process in processes:
            out, err = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, err)
        self.assertEqual(
            self.cli("config", "get"),
            {"threshold": 5, "window_seconds": 400, "retention_days": 50},
        )
        self.assertEqual(len(self.cli("config", "history")), 3)

    def test_demo_leaves_live_state_unchanged(self):
        self.cli("init")
        state = Path(self.directory.name) / "state.json"
        before = state.read_bytes()
        p = subprocess.run(
            [str(CLI), "demo"], env=self.env, text=True, capture_output=True, timeout=15
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("After three failures: 0 alerts", p.stdout)
        self.assertIn("After the fourth: 1 alert", p.stdout)
        self.assertIn("needs_review", p.stdout)
        self.assertEqual(before, state.read_bytes())

    def test_crash_releases_transaction_lock(self):
        import time

        helper = CLI.parent.parent / "lib/lock.py"
        lock = Path(self.directory.name) / ".transaction.lock"
        process = subprocess.Popen(
            [
                "python3",
                str(helper),
                str(lock),
                "TEST_LOCK_PID",
                "5",
                "/bin/sleep",
                "30",
            ]
        )
        try:
            for _ in range(100):
                if lock.exists():
                    break
                time.sleep(0.01)
            process.kill()
            process.wait(timeout=5)
            self.assertEqual(self.cli("init")["threshold"], 4)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_crashed_monitor_can_restart(self):
        import time

        mock = Path(self.directory.name) / "mock"
        mock.mkdir()
        journal = mock / "journalctl"
        record = json.dumps(self.event(1, 1000))
        journal.write_text(
            "#!/usr/bin/env python3\nimport sys,time\nprint("
            + repr(record)
            + ',flush=True)\nif "--follow" in sys.argv: time.sleep(30)\n'
        )
        journal.chmod(0o700)
        self.env["PATH"] = str(mock) + ":" + self.env["PATH"]
        process = subprocess.Popen(
            [str(CLI), "monitor", "run"],
            env=self.env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(100):
                if self.cli("events"):
                    break
                time.sleep(0.02)
            process.kill()
            process.wait(timeout=5)
            self.assertEqual(self.cli("status")["monitor"]["coverage"], "unavailable")
            self.cli("monitor", "start")
            self.assertEqual(self.cli("status")["monitor"]["coverage"], "available")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            self.cli("monitor", "stop")


if __name__ == "__main__":
    unittest.main()
