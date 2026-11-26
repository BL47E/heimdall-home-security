import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DashboardStartTests(unittest.TestCase):
    def test_fallback_and_automatic_rebind(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            address = root / 'address'
            calls = root / 'calls'
            address.write_text('')
            tailscale = root / 'tailscale'
            tailscale.write_text('#!/bin/sh\ncat "$TEST_ADDRESS"\n')
            tailscale.chmod(0o755)
            cli = root / 'heimdall'
            cli.write_text('#!/bin/sh\necho "$*" >> "$TEST_CALLS"\nexec sleep 30\n')
            cli.chmod(0o755)
            env = dict(os.environ, PATH=directory + ':' + os.environ['PATH'],
                       TEST_ADDRESS=str(address), TEST_CALLS=str(calls))
            process = subprocess.Popen(
                ['python3', str(ROOT / 'lib/dashboard_supervisor.py'), str(cli)],
                env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

            def wait_for(expected):
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if calls.exists() and expected in calls.read_text().splitlines():
                        return
                    self.assertIsNone(process.poll(), 'dashboard supervisor exited')
                    time.sleep(0.05)
                self.fail(f'dashboard did not start on {expected}')

            try:
                wait_for('dashboard --host 127.0.0.1 --port 8765')
                address.write_text('100.100.1.2')
                wait_for('dashboard --host 100.100.1.2 --port 8765')
                address.write_text('100.100.1.3')
                wait_for('dashboard --host 100.100.1.3 --port 8765')
                address.write_text('invalid')
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if calls.read_text().splitlines().count('dashboard --host 127.0.0.1 --port 8765') == 2:
                        break
                    time.sleep(0.05)
                else:
                    self.fail('dashboard did not fall back to localhost')
            finally:
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=8)


if __name__ == '__main__':
    unittest.main()
