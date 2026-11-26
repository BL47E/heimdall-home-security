import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest

CLI = Path(__file__).resolve().parents[1] / 'bin/heimdall'


class PauseTests(unittest.TestCase):
    def test_pause_skips_events_and_keeps_process_alive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = root / 'systemctl'
            manager.write_text("#!/bin/sh\necho LoadState=not-found\n")
            manager.chmod(0o700)
            records = root / 'records'
            records.touch()
            journal = root / 'journalctl'
            journal.write_text('''#!/usr/bin/env python3
import json, os, sys, time
if '--follow' not in sys.argv:
    cursor = next((arg.split('=', 1)[1] for arg in sys.argv if arg.startswith('--cursor=')), 'probe')
    print(json.dumps({'__CURSOR':cursor,'__REALTIME_TIMESTAMP':str(time.time_ns()//1000),'MESSAGE':'probe'}), flush=True)
else:
    with open(os.environ['TEST_RECORDS']) as source:
        while True:
            line = source.readline()
            if line: print(line, end='', flush=True)
            else: time.sleep(.02)
''')
            journal.chmod(0o700)
            env = dict(os.environ, PATH=directory + ':' + os.environ['PATH'],
                       HEIMDALL_DATA_DIR=str(root / 'state'), TEST_RECORDS=str(records))
            def cli(*args):
                result = subprocess.run([str(CLI), *args], env=env, text=True,
                                        capture_output=True, timeout=10, check=True)
                return json.loads(result.stdout)
            def send(cursor, timestamp=None):
                event = {'__CURSOR': cursor, '__REALTIME_TIMESTAMP': str(timestamp or time.time_ns() // 1000),
                         'MESSAGE': 'Failed password for alice from 10.0.0.1 port 22 ssh2'}
                with records.open('a') as stream:
                    stream.write(json.dumps(event) + '\n')
                for _ in range(100):
                    state = json.loads((root / 'state/state.json').read_text())
                    if state.get('cursor') == cursor:
                        return
                    time.sleep(.05)
                self.fail('journal event was not consumed')
            process = subprocess.Popen([str(CLI), 'monitor', 'run'], env=env,
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for _ in range(100):
                    if (root / 'state/state.json').exists() and cli('status')['monitor']['coverage'] == 'available':
                        break
                    time.sleep(.05)
                send('before')
                self.assertEqual(len(cli('events')), 1)
                paused = cli('monitor', 'stop')['monitor']
                self.assertEqual(paused['state'], 'paused')
                self.assertIsNone(process.poll())
                send('during')
                self.assertEqual(len(cli('events')), 1)
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=10)
                process = subprocess.Popen([str(CLI), 'monitor', 'run'], env=env,
                                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for _ in range(100):
                    if cli('status')['monitor']['state'] == 'paused':
                        break
                    time.sleep(.05)
                self.assertEqual(cli('status')['monitor']['state'], 'paused')
                send('during-restart')
                paused_timestamp = time.time_ns() // 1000
                self.assertEqual(len(cli('events')), 1)
                self.assertEqual(cli('monitor', 'start')['monitor']['state'], 'running')
                send('buffered-during-pause', paused_timestamp)
                self.assertEqual(len(cli('events')), 1)
                send('after')
                self.assertEqual(len(cli('events')), 2)
                self.assertEqual(cli('alerts'), [])
            finally:
                if process.poll() is None:
                    process.send_signal(signal.SIGTERM)
                    process.wait(timeout=10)


if __name__ == '__main__':
    unittest.main()
