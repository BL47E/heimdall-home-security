"""Pseudo-terminal checks for the Heimdall terminal application.

Every session runs the real `bin/heimdall tui` against disposable state
directories. No live VM state, credentials or network is involved.
"""

import fcntl
import importlib.util
import json
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import tempfile
import termios
import threading
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("tui", ROOT / "lib/tui.py")
tui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tui)

DOWN, UP, ESC, ENTER_KEY = "\x1b[B", "\x1b[A", "\x1b", "\r"


class Screen:
    """A minimal terminal that reconstructs what the application actually shows.

    Old ncurses carves updates into cursor-hopped fragments, so concatenated
    output cannot be searched for text. This model replays cursor addressing,
    line clears and printed cells, and exposes the visible screen as text.
    """

    def __init__(self):
        self.cells = {}
        self.row = 0
        self.col = 0

    def feed(self, data):
        index = 0
        size = len(data)
        while index < size:
            byte = data[index]
            if byte == 0x1B and index + 1 < size and data[index + 1] == ord("["):
                index += 2
                params = bytearray()
                while index < size and (0x30 <= data[index] <= 0x3F):
                    params.append(data[index])
                    index += 1
                while index < size and (0x20 <= data[index] <= 0x2F):
                    index += 1
                if index >= size:
                    return
                final = chr(data[index])
                index += 1
                self.control(params.decode("ascii"), final)
            elif byte == 0x1B and index + 1 < size and data[index + 1] == ord("]"):
                end = data.find(b"\x07", index)
                alt = data.find(b"\x1b\\", index)
                if end == -1 and alt == -1:
                    return
                index = (min(x for x in (end, alt) if x != -1) + (1 if end != -1 and (alt == -1 or end < alt) else 2))
            elif byte == 0x1B and index + 2 < size and data[index + 1] in (ord("("), ord(")")):
                index += 3
            elif byte == 0x1B:
                index += 1
            elif byte == 0x0D:
                self.col = 0
                index += 1
            elif byte == 0x0A:
                self.row += 1
                index += 1
            elif byte >= 0x20:
                self.cells[(self.row, self.col)] = chr(byte)
                self.col += 1
                index += 1
            else:
                index += 1

    def control(self, params, final):
        numbers = [int(part) if part else 0 for part in params.lstrip("?").split(";")]
        def arg(position, default):
            return numbers[position] if position < len(numbers) and numbers[position] else default
        if final == "H" or final == "f":
            self.row, self.col = max(0, arg(0, 1) - 1), max(0, arg(1, 1) - 1)
        elif final == "G":
            self.col = max(0, arg(0, 1) - 1)
        elif final == "K":
            for column in range(self.col, 200):
                self.cells.pop((self.row, column), None)
        elif final == "J":
            mode = numbers[0] if numbers else 0
            if mode == 2:
                self.cells.clear()
            else:
                for (row, column) in list(self.cells):
                    if row > self.row or (row == self.row and column >= self.col):
                        del self.cells[(row, column)]
        elif final in "XP":
            for column in range(self.col, self.col + arg(0, 1)):
                self.cells.pop((self.row, column), None)

    def text(self, rows=40, columns=200):
        lines = []
        for row in range(rows):
            line = "".join(self.cells.get((row, column), " ") for column in range(columns))
            lines.append(line.rstrip())
        return "\n".join(lines)


class Session:
    """A Heimdall terminal application running on a private pseudo-terminal.

    A reader thread drains the terminal continuously: the pty's small output
    buffer would otherwise block the application's own writes mid-session.
    """

    def __init__(self, data, rows=24, cols=80):
        self.data = Path(data)
        self.rows, self.cols = rows, cols
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        environment = dict(os.environ, HEIMDALL_DATA_DIR=str(self.data), TERM="xterm-256color")
        self.process = subprocess.Popen(
            [str(ROOT / "bin/heimdall"), "tui"],
            stdin=slave, stdout=slave, stderr=slave, env=environment, close_fds=True,
        )
        os.close(slave)
        self.screen = Screen()
        self.lock = threading.Lock()
        self.stopped = threading.Event()
        self.reader = threading.Thread(target=self._drain, daemon=True)
        self.reader.start()

    def _drain(self):
        while not self.stopped.is_set():
            ready, _, _ = select.select([self.master], [], [], 0.2)
            if not ready:
                continue
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                return
            if not chunk:
                return
            with self.lock:
                self.screen.feed(chunk)

    def text(self):
        with self.lock:
            return self.screen.text(rows=self.rows + 4, columns=self.cols)

    def send(self, keys):
        os.write(self.master, keys.encode())

    def expect(self, pattern, timeout=15):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if pattern in self.text():
                return
            if self.process.poll() is not None and not self.reader.is_alive():
                break
            time.sleep(0.1)
        if pattern not in self.text():
            raise AssertionError(
                f"Timed out waiting for {pattern!r}.\n--- screen ---\n{self.text()}"
            )

    def alive(self):
        return self.process.poll() is None

    def quit(self):
        self.send("/exit\r")
        return self.process.wait(timeout=15)

    def close(self):
        self.stopped.set()
        self.reader.join(timeout=2)
        if self.alive():
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # ncurses can swallow SIGTERM while blocked in getch; SIGKILL cannot.
                self.process.kill()
            self.process.wait(timeout=10)
        try:
            os.close(self.master)
        except OSError:
            pass


class TerminalAppTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "data"

    def tearDown(self):
        self.tmp.cleanup()

    def launch(self, rows=24, cols=80):
        session = Session(self.data, rows, cols)
        self.addCleanup(session.close)
        session.expect("HEIMDALL")
        return session

    def complete_onboarding(self, session, initialize=True):
        session.expect("Welcome")
        session.send(ENTER_KEY)
        session.expect("Prerequisites")
        session.send(DOWN + DOWN + ENTER_KEY)
        session.expect("Local state")
        if initialize and not (self.data / "state.json").is_file():
            session.send(DOWN + ENTER_KEY)
            session.expect("Initialize local state")
            session.send("y")
            session.expect("Local state initialized")
            session.send(DOWN + ENTER_KEY)
        else:
            session.send(DOWN + DOWN + ENTER_KEY)
        session.expect("Finish in local mode")
        session.send(ENTER_KEY)
        session.expect("Overview")
        session.expect("Onboarding saved")

    def test_first_run_opens_onboarding_and_requires_exact_exit(self):
        session = self.launch()
        session.expect("Begin setup")
        # q and Escape must not exit the application.
        session.send("q")
        time.sleep(0.4)
        self.assertTrue(session.alive())
        session.send(ESC)
        time.sleep(0.4)
        self.assertTrue(session.alive())
        # A partial command is not the exact /exit.
        session.send("/exi" + ENTER_KEY)
        session.expect("Unknown command /exi")
        self.assertTrue(session.alive())
        session.send("/exit" + ENTER_KEY)
        self.assertEqual(session.process.wait(timeout=15), 0)
        # Opening and leaving the panel without finishing setup changed nothing.
        self.assertFalse(self.data.exists())

    def test_completed_onboarding_is_saved_and_reused(self):
        session = self.launch()
        self.complete_onboarding(session)
        self.assertTrue((self.data / "state.json").is_file())
        record = json.loads((self.data / "tui.json").read_text())
        self.assertTrue(record["onboarded"])
        self.assertEqual(record["mode"], "local")
        self.assertEqual(session.quit(), 0)

        second = self.launch()
        second.expect("Monitor")
        self.assertNotIn("Onboarding —", second.text())
        self.assertEqual(second.quit(), 0)

    def test_canceled_onboarding_leaves_no_completion_record(self):
        session = self.launch()
        session.send(ENTER_KEY)
        session.expect("Prerequisites")
        session.send(ESC)
        session.expect("Welcome")
        session.send("/exit" + ENTER_KEY)
        self.assertEqual(session.process.wait(timeout=15), 0)
        self.assertFalse((self.data / "tui.json").exists())

    def test_existing_state_is_adopted_without_reset(self):
        subprocess.run(
            [str(ROOT / "bin/heimdall"), "ingest", str(ROOT / "tests/fixtures/password-burst.jsonl")],
            env={**os.environ, "HEIMDALL_DATA_DIR": str(self.data)},
            capture_output=True, check=True,
        )
        before = json.loads((self.data / "state.json").read_text())
        self.assertEqual(len(before["alerts"]), 1)

        session = self.launch()
        session.expect("Begin setup")
        session.send(ENTER_KEY)
        session.expect("Prerequisites")
        session.send(DOWN + DOWN + ENTER_KEY)
        session.expect("adopted unchanged")
        session.send(DOWN + ENTER_KEY)
        session.expect("Finish in local mode")
        session.send(DOWN + ENTER_KEY)
        session.expect("Onboarding saved (offline mode)")
        session.expect("10.37.129.4")

        # Normal in-app use: q and Escape stay inside the application.
        session.send("q" + ESC)
        time.sleep(0.4)
        self.assertTrue(session.alive())
        self.assertEqual(session.quit(), 0)

        after = json.loads((self.data / "state.json").read_text())
        self.assertEqual(len(after["alerts"]), 1)
        self.assertEqual(after["alerts"][0]["id"], before["alerts"][0]["id"])

    def test_offline_completion_without_journal_or_state(self):
        # The development Mac has no journalctl; onboarding still completes offline.
        session = self.launch()
        session.expect("Begin setup")
        session.send(ENTER_KEY)
        session.expect("Prerequisites")
        session.expect("SSH journal")
        session.send(DOWN + DOWN + ENTER_KEY)
        session.expect("Continue without initializing")
        session.send(DOWN + DOWN + ENTER_KEY)
        session.expect("Finish in offline mode")
        session.send(DOWN + ENTER_KEY)
        session.expect("Onboarding saved (offline mode)")
        record = json.loads((self.data / "tui.json").read_text())
        self.assertEqual(record["mode"], "offline")
        self.assertEqual(session.quit(), 0)

    def test_command_bar_navigation_and_config(self):
        session = self.launch()
        self.complete_onboarding(session)
        session.send("/setup" + ENTER_KEY)
        session.expect("Runtime")
        session.send("/providers" + ENTER_KEY)
        session.expect("Discord")
        session.send("/help" + ENTER_KEY)
        session.expect("/overview")
        session.send(ESC)
        session.send("/config {\"threshold\":5}" + ENTER_KEY)
        session.expect("Apply configuration change")
        session.send("y")
        session.expect("Configuration applied")
        config = json.loads((self.data / "state.json").read_text())["config"]
        self.assertEqual(config["threshold"], 5)
        self.assertEqual(session.quit(), 0)

    def test_narrow_screen_shows_guidance_and_stays_controllable(self):
        session = Session(self.data, rows=20, cols=40)
        self.addCleanup(session.close)
        session.expect("Resize to 48")
        session.send("/exit" + ENTER_KEY)
        self.assertEqual(session.process.wait(timeout=15), 0)


class RecordTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "data"

    def tearDown(self):
        self.tmp.cleanup()

    def test_record_roundtrip_is_private_and_atomic(self):
        self.assertIsNone(tui.load_record(self.data))
        tui.save_record(self.data, "local")
        record = tui.load_record(self.data)
        self.assertEqual(record["mode"], "local")
        self.assertEqual(record["onboarded"], True)
        self.assertEqual((self.data / "tui.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.data.stat().st_mode & 0o777, 0o700)

    def test_corrupt_record_is_treated_as_unfinished(self):
        self.data.mkdir(parents=True)
        (self.data / "tui.json").write_text("{not json")
        self.assertIsNone(tui.load_record(self.data))
        (self.data / "tui.json").write_text('{"onboarded": false}')
        self.assertIsNone(tui.load_record(self.data))


class LauncherTest(unittest.TestCase):
    def test_noninteractive_default_remains_help(self):
        result = subprocess.run(
            [str(ROOT / "bin/heimdall")], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: ./bin/heimdall [COMMAND]", result.stdout)

    def test_noninteractive_tui_refuses_with_guidance(self):
        result = subprocess.run(
            [str(ROOT / "bin/heimdall"), "tui"], capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("needs an interactive terminal", result.stderr)


if __name__ == "__main__":
    unittest.main()
