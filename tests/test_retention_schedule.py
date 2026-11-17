"""Render manual scheduling templates and exercise cleanup only in disposable state."""
import configparser
import getpass
import grp
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RetentionScheduleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="heimdall-retention-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.data = self.base / "private-state"
        self.tokens = {"OWNER": getpass.getuser(), "GROUP": grp.getgrgid(os.getgid()).gr_name,
                       "REPO_DIR": str(ROOT), "DATA_DIR": str(self.data)}

    def render(self, name):
        text = (ROOT / "deploy" / (name + ".in")).read_text()
        for key, value in self.tokens.items():
            text = text.replace("@" + key + "@", value)
        self.assertIsNone(re.search(r"@[A-Z_]+@", text), "unresolved installation token")
        path = self.base / name
        path.write_text(text)
        unit = configparser.ConfigParser(interpolation=None, strict=True)
        unit.optionxform = str
        unit.read_string(text)
        return path, unit

    def test_cleanup_has_same_identity_and_private_storage_as_monitor(self):
        _, cleanup = self.render("heimdall-cleanup.service")
        _, monitor = self.render("heimdall-monitor.service")
        service = cleanup["Service"]
        for key in ("User", "Group", "WorkingDirectory", "Environment", "ReadWritePaths", "UMask"):
            self.assertEqual(service[key], monitor["Service"][key], key)
        self.assertEqual(service["Type"], "oneshot")
        self.assertEqual(shlex.split(service["ExecStart"]), [str(ROOT / "bin/heimdall"), "cleanup"])
        self.assertEqual(service["NoNewPrivileges"], "true")
        self.assertEqual(service["ProtectSystem"], "strict")
        self.assertNotIn("SupplementaryGroups", service)
        self.assertNotIn("Restart", service)
        self.assertGreater(int(service["TimeoutStartSec"]), 0)
        self.assertLessEqual(int(service["TimeoutStartSec"]), 120)

    def test_timer_runs_daily_with_missed_run_recovery(self):
        _, unit = self.render("heimdall-cleanup.timer")
        timer = unit["Timer"]
        self.assertEqual(timer["OnCalendar"], "daily")
        self.assertEqual(timer["Persistent"], "true")
        self.assertEqual(timer["Unit"], "heimdall-cleanup.service")
        self.assertEqual(unit["Install"]["WantedBy"], "timers.target")
        self.assertIn(timer["RandomizedDelaySec"], ("15m", "900", "900s"))
        self.assertIn(timer["AccuracySec"], ("1m", "60", "60s"))

    def test_rendered_cleanup_only_expires_unneeded_records(self):
        _, unit = self.render("heimdall-cleanup.service")
        service = unit["Service"]
        env = dict(os.environ)
        for assignment in shlex.split(service["Environment"]):
            key, value = assignment.split("=", 1)
            env[key] = value
        init = subprocess.run([str(ROOT / "bin/heimdall"), "init"], env=env, capture_output=True, text=True)
        self.assertEqual(init.returncode, 0, init.stderr)
        state_path = self.data / "state.json"
        state = json.loads(state_path.read_text())
        now = int(time.time())
        old = now - 61 * 86400
        state["events"] = [{"id": "expired", "timestamp": old},
                           {"id": "old-support", "timestamp": old},
                           {"id": "recent", "timestamp": now}]
        state["alerts"] = [{"id": "expired-alert", "last_seen": old, "event_ids": ["expired"]},
                           {"id": "retained-alert", "last_seen": now, "event_ids": ["old-support", "recent"],
                            "review_history": [{"timestamp": old, "status": "reviewed", "reason": "owner"}]}]
        state["sources"] = {"expired-source": {"last": old}, "recent-source": {"last": now}}
        state_path.write_text(json.dumps(state))
        result = subprocess.run(shlex.split(service["ExecStart"]), cwd=service["WorkingDirectory"],
                                env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["events_removed"], 1)
        after = json.loads(state_path.read_text())
        self.assertEqual([e["id"] for e in after["events"]], ["old-support", "recent"])
        self.assertEqual(after["alerts"], state["alerts"][1:])
        self.assertEqual(after["sources"], {"recent-source": {"last": now}})
        self.assertEqual(after["config"], state["config"])
        self.assertEqual(state_path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.data.stat().st_mode & 0o777, 0o700)

    @unittest.skipUnless(shutil.which("systemd-analyze"), "systemd-analyze unavailable; source/render checks only")
    def test_resolved_units_pass_systemd_verification(self):
        paths = [self.render(name)[0] for name in ("heimdall-cleanup.service", "heimdall-cleanup.timer")]
        self.data.mkdir()
        result = subprocess.run(["systemd-analyze", "verify", *map(str, paths)], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
