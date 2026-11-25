"""Heimdall's local terminal application.

The shell CLI owns every state change; this panel only calls it and renders
results. Opening the panel never modifies accounts, groups, network, firewall
or services. Leaving the application requires the typed /exit command, so a
stray key cannot end a session.
"""

from dataclasses import dataclass
import getpass
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from typing import Callable
import warnings

try:
    import curses
except ImportError:
    curses = None


PAGES = ("Overview", "Setup", "Providers", "Demo")
ONBOARDING_STEPS = ("Welcome", "Prerequisites", "Local state", "Finish")
ENTER = (10, 13)
MIN_ROWS, MIN_COLS = 14, 48
RECORD_NAME = "tui.json"

WELCOME = """Heimdall watches this machine's SSH journal and records explainable local alerts.

The panel reads and controls Heimdall through its existing commands only. Opening it changes no accounts, groups, network, firewall or services, and nothing is sent anywhere.

Setup checks the runtime, SSH journal access and private local state. Finish in local mode for live monitoring, or offline mode to explore the labelled demo first."""

COMMAND_HELP = """/overview  /setup  /providers  /demo    Open a page
/rules    View or edit rule settings
/refresh    Reload monitor status and lists
/config {"threshold":5}    Apply a validated settings patch (asks first)
/help    Show this list
/exit    Leave Heimdall

Anything else is unknown. Leaving normally requires the exact command /exit; Ctrl+C also interrupts the process and restores the terminal."""

RULE_FIELDS = (
    ("threshold", "Failure threshold"),
    ("window_seconds", "Window (seconds)"),
    ("retention_days", "Retention (days)"),
)


@dataclass(frozen=True)
class Item:
    title: str
    detail: str
    action: Callable


def run(*command, secret=None, timeout=10):
    # A child CLI cannot read navigation keys or print directly into the panel.
    return subprocess.run(
        command, stdin=subprocess.DEVNULL if secret is None else None,
        input=secret, capture_output=True, text=True, errors="replace",
        timeout=timeout,
    )


def journal_access():
    if not shutil.which("journalctl"):
        return "Unavailable", "Live SSH monitoring needs the system journal on Ubuntu."
    try:
        check = run("journalctl", "-u", "ssh", "-n", "1", "--no-pager", "-o", "json")
        if check.returncode == 0 and check.stdout.strip():
            record = json.loads(check.stdout)
            if isinstance(record, dict) and record.get("__CURSOR"):
                return "Readable", "This login can read an SSH journal record."
        detail = check.stderr.lower()
        if any(hint in detail for hint in ("permission", "access", "not seeing messages")):
            return "Access needed", "Ask the system administrator to review journal access for this login."
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return "Check failed", "Run the journal check in the Permissions guide from the Linux terminal."
    return "Unverified", "The journal returned no readable SSH records. Check the SSH service and its logs."


def load_record(data):
    """Return the saved onboarding record, or None when setup has not completed."""
    try:
        record = json.loads((Path(data) / RECORD_NAME).read_text())
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) and record.get("onboarded") is True else None


def save_record(data, mode):
    """Persist onboarding completion atomically in the private state directory."""
    data = Path(data)
    if data.is_symlink():
        raise ValueError("State directory must not be a symbolic link")
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(data, 0o700)
    payload = json.dumps(
        {"onboarded": True, "mode": mode, "completed_at": int(time.time())}, indent=2
    ) + "\n"
    handle, temporary = tempfile.mkstemp(dir=data, prefix=".tui.")
    try:
        with os.fdopen(handle, "w") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, data / RECORD_NAME)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


class Panel:
    def __init__(self, screen, cli, data):
        self.screen, self.cli, self.data = screen, cli, Path(data)
        self.record = load_record(self.data)
        self.onboarding = 0 if self.record is None else None
        self.page, self.cursor, self.offset = 0, 0, 0
        self.dialog = None
        self.dialog_keys = {}
        self.dialog_hint = ""
        self.scroll = 0
        self.status = {}
        self.status_error = ""
        self.ready = False
        self.alerts = []
        self.alerts_error = ""
        self.journal = ("Unchecked", "")
        self.command_text = ""
        self.command_mode = False
        self.rule_field = None
        self.message = ""
        self.heading = curses.A_BOLD
        self.muted = curses.A_DIM
        self.accent = 0
        self.normal = 0
        self.selected = curses.A_REVERSE | curses.A_BOLD
        if curses.has_colors() and curses.COLOR_PAIRS >= 3:
            try:
                curses.use_default_colors()
            except curses.error:
                pass
            # Heimdall's identity: genuine black background, light primary text,
            # quiet gray secondary tone and a single cyan accent.
            if curses.can_change_color():
                try:
                    curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
                except curses.error:
                    pass
            for pair, foreground, background in (
                (1, curses.COLOR_WHITE, curses.COLOR_BLACK),
                (2, curses.COLOR_CYAN, curses.COLOR_BLACK),
                (3, curses.COLOR_BLACK, curses.COLOR_WHITE),
            ):
                curses.init_pair(pair, foreground, background)
            self.normal = curses.color_pair(1)
            self.heading = curses.A_BOLD | self.normal
            self.accent = curses.color_pair(2)
            if curses.COLORS >= 256 and curses.COLOR_PAIRS >= 4:
                curses.init_pair(4, 242, curses.COLOR_BLACK)
                self.muted = curses.color_pair(4)
            else:
                self.muted = self.normal | curses.A_DIM
            self.selected = curses.color_pair(3) | curses.A_BOLD
        screen.bkgd(" ", self.normal)

    # -- data access ---------------------------------------------------------

    def command(self, *args, raw=False, secret=None, timeout=10):
        result = run(self.cli, *args, secret=secret, timeout=timeout)
        if result.returncode:
            error = result.stderr.strip() if secret is None else "Heimdall rejected the credential."
            raise ValueError(error or f"Heimdall exited with status {result.returncode}.")
        return result.stdout if raw else json.loads(result.stdout)

    def refresh(self):
        self.ready = (self.data / "state.json").is_file()
        self.status, self.status_error = {}, ""
        self.alerts, self.alerts_error = [], ""
        if self.ready or self.data.is_symlink():
            try:
                self.status = self.command("status")
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                self.status_error = str(error)
        if self.page == 1 or self.onboarding == 1:
            self.journal = journal_access()
        if self.page == 0 and self.status:
            try:
                self.alerts = self.command("alerts")
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                self.alerts_error = str(error)

    # -- dialogs -------------------------------------------------------------

    def show(self, title, content, keys=None, hint=""):
        self.dialog = (title, content)
        self.dialog_keys = dict(keys or {})
        self.dialog_hint = hint
        self.scroll = 0

    def confirm(self, title, body, action):
        def run_confirmed():
            action()
            self.refresh()
        self.show(title, body + "\n\nPress y to confirm or Esc to go back.",
                  {ord("y"): run_confirmed}, "y confirm")

    def permissions(self):
        self.show("Review journal permissions", """On the monitored Linux system, run this as the account that will use Heimdall.

journalctl -u ssh -n 1 --no-pager -o json

A record confirms read access. An empty result can also mean that the SSH service has written no records. Check the service and its logs before changing permissions.

If access is denied, ask the system administrator to review systemd-journal membership for your account. This group can read system logs beyond SSH. If approved, run the command below on that system, then sign out and sign back in.

sudo usermod -aG systemd-journal "$USER"

Press r in Setup after signing back in. Use your regular login for Heimdall.""")

    # -- actions -------------------------------------------------------------

    def credential(self, provider):
        if not self.status:
            self.show("Set up local state", "Initialize private local state before saving a credential.")
            return
        # Pause curses while getpass uses the real terminal with echo disabled.
        curses.def_prog_mode()
        curses.endwin()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", getpass.GetPassWarning)
                print(f"\n{provider} setup. Press Enter to cancel.", flush=True)
                if provider == "Discord":
                    print("Use a webhook for a channel you control and approve.", flush=True)
                value = getpass.getpass("Discord webhook URL: " if provider == "Discord" else "VirusTotal API key: ")
            if value:
                self.command(provider.lower(), "configure", secret=value + "\n")
                self.refresh()
                self.show(provider, "Credential saved in private local state."
                          + (" Open Enable Discord delivery when the channel is ready."
                             if provider == "Discord" else " Use the CLI to request a lookup for an eligible public IP."))
        except (getpass.GetPassWarning, EOFError, KeyboardInterrupt):
            self.show(provider, "Setup canceled. Enter credentials in a terminal that supports hidden input.")
        finally:
            curses.reset_prog_mode()
            self.screen.clear()
            try:
                curses.curs_set(0)
            except curses.error:
                pass

    def set_monitor(self, action):
        result = self.command("monitor", action)["monitor"]
        self.show("Monitor status", f"State  {result['state']}\nCoverage  {result['coverage']}"
                  + (f"\n\n{result['last_error']}" if result.get("last_error") else ""))

    def start_monitor(self):
        if not self.status:
            self.show("Before starting", "Initialize private local state first.")
        elif self.status.get("mode") == "fixture":
            self.show("Sample data", "Use a separate live state directory to start SSH monitoring.")
        elif self.status["monitor"]["state"] == "running":
            self.show("Monitor already running", "Open the monitor status for the current journal coverage.")
        elif self.journal[0] != "Readable" and journal_access()[0] != "Readable":
            self.show("Before starting", "Verify SSH journal access in Setup and refresh with r.")
        else:
            self.set_monitor("start")

    def stop_monitor(self):
        self.confirm("Stop monitor", "New SSH activity may go unmonitored while the reader is stopped.",
                     lambda: self.set_monitor("stop"))

    def monitor_detail(self):
        monitor = self.status.get("monitor", {})
        text = (f"State  {monitor.get('state', 'unverified')}"
                f"\nCoverage  {monitor.get('coverage', 'unverified')}"
                f"\nManager  {monitor.get('manager', 'unverified')}")
        if monitor.get("last_error"):
            text += "\n\n" + monitor["last_error"]
        if monitor.get("manager") == "systemd":
            text += ("\n\nThe Linux service manager owns the SSH reader. If regular controls are denied, "
                     "an administrator can use these commands on the monitored system:\n\n"
                     "sudo systemctl start heimdall-monitor.service\n"
                     "sudo systemctl stop heimdall-monitor.service")
        else:
            text += "\n\nFor boot startup, follow the reviewed systemd setup in docs/runbook.md."
        text += "\n\nStart or stop from the Overview page. Local policy may require an administrator."
        self.show("Monitor status", text)

    def open_investigation(self, alert):
        report = self.command("report", alert["id"], raw=True)
        self.show("Investigation  ·  " + alert["id"], report,
                  {ord("y"): lambda: self.confirm_review(alert)}, "y review/reopen")

    def confirm_review(self, alert):
        if alert.get("review_status") == "reviewed":
            self.confirm("Reopen alert", "Return this alert to needs-review so new failures reopen it.",
                         lambda: self.apply_review(alert, "reopen"))
        else:
            self.confirm("Mark reviewed", "Record that the owner reviewed this investigation.",
                         lambda: self.apply_review(alert, "review"))

    def apply_review(self, alert, verb):
        self.command(verb, alert["id"])
        status = "needs review" if verb == "reopen" else "reviewed"
        self.show("Review updated", f"Alert {alert['id']} is now {status}. The change is recorded in its history.")

    def open_events(self):
        events = self.command("events")
        lines = ["Latest observations, newest first.", ""]
        for event in events[:12]:
            when = event.get("timestamp") or "unknown time"
            who = event.get("username") or "unknown user"
            note = (event.get("message") or "")[:70]
            lines.append(f"{when}  {who}  {note}")
        if len(events) > 12:
            lines.append(f"... {len(events) - 12} older records retained.")
        elif not events:
            lines.append("No observations yet. The monitor records them as SSH activity arrives.")
        self.show("Recent events", "\n".join(lines))

    def open_rules(self):
        if not self.status:
            self.show("Rule settings", self.status_error or "Initialize private local state in Setup first.")
            return
        config = self.status.get("config", {}) or {}
        history = self.command("config", "history")
        changes = (f"{len(history)} recorded change(s), latest: {json.dumps(history[-1]['patch'])}."
                    if history else "No configuration changes recorded.")
        values = "\n".join(
            f"{index}. {label}  {config.get(field, 'unset')}"
            for index, (field, label) in enumerate(RULE_FIELDS, 1)
        )
        keys = {
            ord(str(index)): lambda field=field, label=label: self.edit_rule(field, label)
            for index, (field, label) in enumerate(RULE_FIELDS, 1)
        }
        self.show("Rule settings", f"{values}\n\n{changes}", keys, "1–3 edit")

    def edit_rule(self, field, label):
        self.rule_field = (field, label)
        self.command_mode, self.command_text = True, ""
        self.show(f"Edit {label.lower()}", "Enter a whole number, then press Enter to review.")

    def review_rule_edit(self, text):
        field, label = self.rule_field
        if not text:
            self.rule_field = None
            self.open_rules()
            return
        if not text.isdecimal() or len(text) > 10:
            self.edit_rule(field, label)
            self.show(f"Edit {label.lower()}", "Enter a whole number using digits 0–9.")
            return
        self.rule_field = None
        value = int(text)
        patch = json.dumps({field: value})
        self.confirm("Apply configuration change", f"Set {label.lower()} to {value}.",
                     lambda: self.apply_config(patch))

    def apply_config(self, patch):
        self.command("config", "set", patch)
        self.message = "Configuration applied."

    def initialize_state(self):
        self.command("init")
        self.message = "Local state initialized with default settings."

    # -- onboarding ----------------------------------------------------------

    def advance_onboarding(self):
        self.onboarding = min(self.onboarding + 1, len(ONBOARDING_STEPS) - 1)
        self.cursor, self.offset = 0, 0

    def step_back(self):
        if self.onboarding:
            self.onboarding -= 1
            self.cursor, self.offset = 0, 0
        else:
            self.message = "Enter continues onboarding; /exit leaves."

    def review_setup_again(self):
        self.onboarding = 1
        self.cursor, self.offset = 0, 0

    def finish_onboarding(self, mode):
        save_record(self.data, mode)
        self.record = load_record(self.data)
        self.onboarding = None
        self.navigate(0)
        self.message = f"Onboarding saved ({mode} mode). Welcome to Heimdall."

    def onboarding_items(self):
        step = self.onboarding
        if step == 0:
            return [
                Item("Begin setup", "Check requirements, prepare state and choose a working mode.",
                     self.advance_onboarding),
                Item("About Heimdall", "What this application watches and what it never touches.",
                     lambda: self.show("Welcome", WELCOME)),
            ]
        if step == 1:
            missing = [name for name in ("bash", "jq", "python3") if not shutil.which(name)]
            details = "Missing  " + ", ".join(missing) if missing else "Bash, jq, and Python 3 available"
            return [
                Item("Runtime  /  " + ("Missing tools" if missing else "Ready"), details,
                     lambda: self.show("Runtime requirements",
                                       details + "\n\nOn Ubuntu, the administrator can install prerequisites with:\n\n"
                                       "sudo apt install bash jq python3 openssh-server\n\n"
                                       "The offline demo needs Bash, jq and Python 3. Live monitoring also needs an SSH journal.")),
                Item(f"SSH journal  /  {self.journal[0]}", self.journal[1], self.permissions),
                Item("Continue to local state", "Adopt existing records or initialize private state.",
                     self.advance_onboarding),
            ]
        if step == 2:
            if self.ready:
                counts = self.status.get("counts", {}) or {}
                return [
                    Item("Local state  /  Existing", f"{counts.get('events', 0)} events    "
                           f"{counts.get('alerts', 0)} alerts — adopted unchanged",
                         lambda: self.show("Existing local state",
                                           f"Heimdall will adopt the existing records in {self.data} without resetting anything. "
                                           "No history, reviews or provider configuration are touched.")),
                    Item("Continue to finish", "Choose how this installation will be used.",
                         self.advance_onboarding),
                ]
            return [
                Item("Local state  /  Pending", str(self.data),
                     lambda: self.show("Local state",
                                       f"Heimdall keeps private records in {self.data}. "
                                       "Initialize creates it with default settings; nothing is created until you confirm.")),
                Item("Initialize local state", "Create private state with default settings.",
                     lambda: self.confirm("Initialize local state",
                                          f"Prepare {self.data} with Heimdall's default settings.",
                                          self.initialize_state)),
                Item("Continue without initializing", "Finish offline; initialize later from Setup.",
                     self.advance_onboarding),
            ]
        return [
            Item("Finish in local mode", "Save setup and open the workspace for live SSH monitoring.",
                 lambda: self.finish_onboarding("local")),
            Item("Finish in offline mode", "Save setup for the labelled demo and offline use.",
                 lambda: self.finish_onboarding("offline")),
            Item("Review setup again", "Recheck requirements and local state.", self.review_setup_again),
        ]

    # -- pages ---------------------------------------------------------------

    def navigate(self, page):
        self.page, self.cursor, self.offset = page, 0, 0
        self.dialog, self.dialog_keys, self.dialog_hint = None, {}, ""
        self.refresh()

    def overview_items(self):
        monitor = self.status.get("monitor", {})
        counts = self.status.get("counts", {}) or {}
        state = monitor.get("state", "unverified")
        items = [
            Item(f"Monitor  /  {state}",
                 f"Coverage {monitor.get('coverage', 'unverified')}    "
                 f"Manager {monitor.get('manager', 'unverified')}",
                 self.monitor_detail),
            Item("Stop monitor" if state == "running" else "Start monitor",
                 "Pause collection until restart." if state == "running"
                 else "Begin reading SSH activity through the monitor command.",
                 self.stop_monitor if state == "running" else self.start_monitor),
            Item(f"Rules  /  {(self.status.get('config') or {}).get('threshold', '?')} failures in "
                 f"{(self.status.get('config') or {}).get('window_seconds', '?')}s",
                 "Edit threshold, window and retention.", self.open_rules),
        ]
        if self.alerts:
            items += [
                Item(f"{alert.get('source_ip') or 'Unknown source'}  /  {alert['severity'].title()}",
                     f"{alert['failure_count']} failures    {alert['review_status'].replace('_', ' ')}",
                     lambda alert=alert: self.open_investigation(alert))
                for alert in self.alerts
            ]
        else:
            message = self.alerts_error or "Heimdall lists findings here when a rule matches."
            items.append(Item("No alerts", message, lambda: self.show("Alerts", message)))
        items += [
            Item(f"Recent events  /  {counts.get('events', 0)} stored",
                 "Latest SSH observations and their outcomes.", self.open_events),
            Item("Providers  /  Discord " + (self.status.get("providers", {}) or {}).get("discord", "unconfigured").replace("_", " ")
                 + " · VirusTotal " + (self.status.get("providers", {}) or {}).get("virustotal", "unconfigured").replace("_", " "),
                 "Optional delivery and reputation. Enter opens configuration.", lambda: self.navigate(2)),
            Item("Setup", "Runtime, permissions and local state.", lambda: self.navigate(1)),
            Item("Demo", "Labelled synthetic walkthrough in separate state.", lambda: self.navigate(3)),
        ]
        return items

    def setup_items(self):
        missing = [name for name in ("bash", "jq", "python3") if not shutil.which(name)]
        details = "Missing  " + ", ".join(missing) if missing else "Bash, jq, and Python 3 available"
        state_label = "Ready" if self.status else "Needs attention" if self.status_error else "Pending"
        return [
            Item("Runtime  /  " + ("Missing tools" if missing else "Ready"), details,
                 lambda: self.show("Runtime requirements",
                                   details + "\n\nOn Ubuntu, the administrator can install prerequisites with:\n\n"
                                   "sudo apt install bash jq python3 openssh-server\n\n"
                                   "The offline demo needs Bash, jq and Python 3. Live monitoring also needs an SSH journal.")),
            Item(f"Local state  /  {state_label}", str(self.data),
                 lambda: self.show("Local state", f"Private storage is ready in {self.data}.")
                 if self.status else self.confirm(
                     "Initialize local state", f"Prepare {self.data} with Heimdall's default settings.",
                     self.initialize_state)),
            Item(f"SSH journal  /  {self.journal[0]}", self.journal[1], self.permissions),
            Item("Optional integrations", "Set up Discord or VirusTotal when you have credentials.",
                 lambda: self.navigate(2)),
            Item("Overview", "Back to the workspace.", lambda: self.navigate(0)),
        ]

    def provider_items(self):
        providers = self.status.get("providers", {})
        discord = self.status.get("discord", {})
        discord_state = (providers.get("discord", "unconfigured") or "unconfigured").replace("_", " ")
        vt_state = (providers.get("virustotal", "unconfigured") or "unconfigured").replace("_", " ")
        options = [Item(f"Discord  /  {discord_state}",
                        f"{discord.get('pending', 0)} queued    {discord.get('delivered', 0)} delivered",
                        lambda: self.show("Discord delivery",
                                          "Discord receives summaries of new Heimdall alerts when delivery is enabled. "
                                          "Use an approved destination. On a service-managed installation, the Discord "
                                          "sender timer is set up separately in docs/runbook.md.")),
                   Item("Save Discord webhook", "Enter the webhook URL through a hidden prompt.",
                        lambda: self.credential("Discord"))]
        if discord.get("configured"):
            if discord.get("enabled"):
                options.append(Item("Disable Discord delivery", "Pause sending and retain queued notices.",
                                    lambda: self.confirm("Disable Discord delivery",
                                                         "Queued notices are retained and delivery pauses.",
                                                         lambda: self.command("discord", "disable"))))
            else:
                options.append(Item("Enable Discord delivery", "Authorize sending summaries to the configured channel.",
                                    lambda: self.confirm(
                                        "Enable Discord delivery",
                                        "Confirm that you approve this channel receiving SSH alert summaries, including source IPs.",
                                        lambda: self.command("discord", "enable"))))
        options += [
            Item(f"VirusTotal  /  {vt_state}", "Save an API key for optional manual public-IP lookups.",
                 lambda: self.credential("VirusTotal")),
            Item("Overview", "Back to the workspace.", lambda: self.navigate(0)),
        ]
        return options

    def demo_items(self):
        return [
            Item("Run offline demo", "Walk through detection, review, reopening and simulated reputation.",
                 lambda: self.show("Synthetic demonstration", self.command("demo", raw=True, timeout=45))),
            Item("Overview", "Back to the workspace.", lambda: self.navigate(0)),
        ]

    def items(self):
        if self.onboarding is not None:
            return self.onboarding_items()
        return (self.overview_items, self.setup_items,
                self.provider_items, self.demo_items)[self.page]()

    # -- commands ------------------------------------------------------------

    def run_command(self, text):
        """Run one bar command. Returns False only for the exact /exit."""
        if text == "exit":
            return False
        command = "/" + text.strip().lstrip("/")
        if command == "/help":
            self.show("Commands", COMMAND_HELP)
            return True
        if command == "/refresh":
            self.refresh()
            self.message = "Refreshed."
            return True
        if (command not in ("/overview", "/setup", "/providers", "/demo", "/rules", "/config")
                and not command.startswith("/config ")):
            self.message = f"Unknown command {command.split()[0]} — /help lists commands."
            return True
        if self.onboarding is not None:
            self.message = "Onboarding is open — Enter continues, /exit leaves."
            return True
        if command == "/overview":
            self.navigate(0)
        elif command == "/setup":
            self.navigate(1)
        elif command == "/providers":
            self.navigate(2)
        elif command == "/demo":
            self.navigate(3)
        elif command == "/rules":
            self.open_rules()
        else:
            patch = command[len("/config"):].strip()
            try:
                json.loads(patch)
            except ValueError:
                self.message = 'Usage: /config {"threshold":5}'
            else:
                self.confirm("Apply configuration change",
                             f"Set {patch} in local rule settings.", lambda: self.apply_config(patch))
        return True

    # -- rendering ------------------------------------------------------------

    def write(self, row, col, value, limit, attrs=None):
        if limit <= 0:
            return
        # SSH evidence may contain control characters or terminal escape sequences.
        safe = "".join(char if char.isprintable() else " " for char in str(value))
        try:
            self.screen.addnstr(row, col, safe, limit, self.normal if attrs is None else attrs)
        except curses.error:
            pass

    def status_right(self):
        if not self.status:
            return "state pending"
        monitor = self.status.get("monitor", {})
        counts = self.status.get("counts", {}) or {}
        alerts = counts.get("alerts", 0)
        text = f"{monitor.get('state', 'unverified')} · {monitor.get('coverage', 'unverified')} · {alerts} alert"
        if alerts != 1:
            text += "s"
        needs = counts.get("needs_review", 0)
        if needs:
            text += f" ({needs} to review)"
        if self.status.get("mode") == "fixture":
            text += " · samples"
        return text

    def draw_command_bar(self, rows, cols):
        if self.command_mode:
            prefix = "> " if self.rule_field else "/"
            self.write(rows - 1, 2, prefix + self.command_text, cols - 3)
        else:
            text = self.message or "/ commands    /exit leaves"
            self.write(rows - 1, 2, text, cols - 3,
                       self.accent if self.message else self.muted)

    def place_cursor(self, rows, cols):
        # Runs last so list rendering cannot move the typing cursor away.
        try:
            if self.command_mode:
                prefix_width = 2 if self.rule_field else 1
                self.screen.move(rows - 1, min(2 + prefix_width + len(self.command_text), cols - 2))
                curses.curs_set(1)
            else:
                curses.curs_set(0)
        except curses.error:
            pass

    def draw_context_line(self, rows, cols):
        if self.dialog:
            hint = "↑↓ scroll    Esc back"
            if self.dialog_hint:
                hint += "    " + self.dialog_hint
        elif self.onboarding is not None:
            hint = "↑↓ move  Enter open  Esc back    / commands"
        else:
            hint = "↑↓ move  Enter open  Tab page  r refresh"
        self.write(rows - 2, 2, hint, cols - 3, self.muted)

    def render(self, items):
        screen = self.screen
        screen.erase()
        rows, cols = screen.getmaxyx()
        if rows < MIN_ROWS or cols < MIN_COLS:
            self.write(0, 0, "Resize to 48 × 14. /exit leaves", cols - 1)
            if rows >= 2:
                self.draw_command_bar(rows, cols)
            self.place_cursor(rows, cols)
            return
        label = (f"{ONBOARDING_STEPS[self.onboarding]}  ({self.onboarding + 1}/{len(ONBOARDING_STEPS)})"
                 if self.onboarding is not None else PAGES[self.page])
        self.write(0, 2, "▥ HEIMDALL", cols - 3, self.heading)
        self.write(0, 14, "·  " + label, cols - 17, self.accent)
        right = self.status_right()
        if cols >= 68:
            self.write(0, cols - 2 - len(right), right, len(right), self.accent)
        self.write(1, 2, "─" * (cols - 4), cols - 3, self.muted)
        self.write(rows - 3, 2, "─" * (cols - 4), cols - 3, self.muted)
        self.draw_context_line(rows, cols)
        self.draw_command_bar(rows, cols)

        if self.dialog:
            title, detail = self.dialog
            self.write(3, 2, title, cols - 4, self.heading)
            wrapped = [line for paragraph in detail.split("\n")
                       for line in (textwrap.wrap(paragraph, min(cols - 5, 88)) or [""])]
            height = rows - 9
            self.scroll = min(self.scroll, max(0, len(wrapped) - height))
            for line_index, line in enumerate(wrapped[self.scroll:self.scroll + height], 5):
                self.write(line_index, 2, line, cols - 3)
            self.place_cursor(rows, cols)
            return

        wide = cols >= 76
        if self.onboarding is not None:
            left, content_top = 2, 6
            if self.onboarding == 0:
                # A quiet dotted wordmark opens the guided welcome.
                content_top = 8
                self.write(4, 4, "· ˖ · ˙ ·  ˖ · ˖  · ˙ · ˖ ·", cols - 6, self.accent)
                self.write(5, 4, "ᚼ   H E I M D A L L   ᚼ", cols - 6, self.heading)
        elif wide:
            left, content_top = 21, 6
            for index, name in enumerate(PAGES):
                active = index == self.page
                self.write(4 + index, 2, f"{index + 1} {name}".ljust(15), 15,
                           self.selected if active else self.normal)
        else:
            left, content_top = 2, 7
            tabs = [f"{index + 1} {name}" for index, name in enumerate(PAGES)]
            self.write(4, 2, "  ".join(tabs), cols - 3)
            offset = sum(len(tab) + 2 for tab in tabs[:self.page])
            self.write(4, 2 + offset, tabs[self.page], len(tabs[self.page]), self.selected)
        if self.onboarding != 0:
            title = (f"Onboarding — {ONBOARDING_STEPS[self.onboarding]}" if self.onboarding is not None
                     else PAGES[self.page])
            self.write(content_top - 2, left, title, cols - left - 2, self.heading)
        if self.status_error:
            self.write(content_top - 1, left, self.status_error, cols - left - 2, self.accent)
        visible = max(1, (rows - 4 - content_top) // 2)
        self.cursor = min(self.cursor, len(items) - 1)
        self.offset = min(max(self.offset, self.cursor - visible + 1), self.cursor)
        for index in range(self.offset, min(len(items), self.offset + visible)):
            item = items[index]
            row = content_top + 2 * (index - self.offset)
            width = cols - left - 3
            selected = index == self.cursor
            self.write(row, left, ("› " + item.title).ljust(width) if selected else "  " + item.title,
                       width, self.selected if selected else self.normal)
            self.write(row + 1, left + 2, item.detail, width - 2, self.muted)
        self.place_cursor(rows, cols)

    # -- input ---------------------------------------------------------------

    def handle_command_key(self, key):
        """Handle one keystroke while the command bar has focus. Returns False to exit."""
        if key == 27:
            self.command_mode, self.command_text = False, ""
            if self.rule_field:
                self.review_rule_edit("")
        elif key in ENTER + (curses.KEY_ENTER,):
            self.command_mode = False
            text, self.command_text = self.command_text, ""
            if self.rule_field:
                self.review_rule_edit(text)
                return True
            return self.run_command(text)
        elif key in (8, 127, curses.KEY_BACKSPACE):
            self.command_text = self.command_text[:-1]
        elif 32 <= key <= 126:
            self.command_text += chr(key)
        return True

    def get_key(self):
        """Read one key, reassembling arrow sequences where ncurses splits them.

        macOS's bundled ncurses can deliver "\x1b[B" byte-by-byte even with
        keypad enabled; on Ubuntu ncurses returns KEY_DOWN directly and this
        helper never sees a split sequence.
        """
        key = self.screen.getch()
        if key != 27:
            return key
        self.screen.nodelay(True)
        try:
            following = []
            while len(following) < 2:
                nxt = self.screen.getch()
                if nxt == -1:
                    break
                following.append(nxt)
        finally:
            self.screen.nodelay(False)
        arrows = {(91, 65): curses.KEY_UP, (91, 66): curses.KEY_DOWN,
                  (91, 67): curses.KEY_RIGHT, (91, 68): curses.KEY_LEFT}
        if len(following) == 2 and tuple(following) in arrows:
            return arrows[tuple(following)]
        for leftover in reversed(following):
            curses.ungetch(leftover)
        return 27

    def loop(self):
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        self.refresh()
        while True:
            items = self.items()
            self.render(items)
            key = self.get_key()
            if key == -1:
                # A read error or interrupted read; pause instead of spinning.
                curses.napms(50)
                continue
            if key == curses.KEY_RESIZE:
                continue
            try:
                if self.command_mode:
                    if not self.handle_command_key(key):
                        return
                elif key == ord("/"):
                    self.command_mode, self.command_text = True, ""
                elif self.dialog:
                    if key in self.dialog_keys:
                        action = self.dialog_keys[key]
                        self.dialog, self.dialog_keys, self.dialog_hint = None, {}, ""
                        action()
                    elif key == 27:
                        self.dialog, self.dialog_keys, self.dialog_hint = None, {}, ""
                    elif key in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_PPAGE, curses.KEY_NPAGE):
                        delta = {curses.KEY_UP: -1, curses.KEY_DOWN: 1,
                                 curses.KEY_PPAGE: -10, curses.KEY_NPAGE: 10}
                        self.scroll = max(0, self.scroll + delta[key])
                elif key == 27:
                    if self.onboarding is not None:
                        self.step_back()
                    else:
                        self.message = ""
                elif key == ord("r"):
                    self.refresh()
                elif self.onboarding is None and key in (9, curses.KEY_RIGHT, curses.KEY_LEFT, curses.KEY_BTAB):
                    change = -1 if key in (curses.KEY_LEFT, curses.KEY_BTAB) else 1
                    self.navigate((self.page + change) % len(PAGES))
                elif self.onboarding is None and ord("1") <= key <= ord("4"):
                    self.navigate(key - ord("1"))
                elif key in (curses.KEY_UP, curses.KEY_DOWN):
                    self.cursor = max(0, min(len(items) - 1, self.cursor + (1 if key == curses.KEY_DOWN else -1)))
                elif key in ENTER + (curses.KEY_ENTER,) and all(
                    size >= minimum for size, minimum in zip(self.screen.getmaxyx(), (MIN_ROWS, MIN_COLS))
                ):
                    items[self.cursor].action()
                    if not self.dialog:
                        self.refresh()
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                self.show("Action could not complete", str(error))


def main():
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Heimdall's terminal app needs an interactive terminal. "
              "Run heimdall --console in a terminal.", file=sys.stderr)
        return 1
    if curses is None or os.environ.get("TERM") in (None, "", "dumb"):
        print("Heimdall's terminal app needs Python curses and a supported TERM.", file=sys.stderr)
        return 1
    if len(sys.argv) != 3:
        print("Internal error: the launcher must pass the CLI and state directory.", file=sys.stderr)
        return 2
    # Recognize the Escape key promptly instead of pausing on partial sequences.
    os.environ.setdefault("ESCDELAY", "25")
    cli, data = sys.argv[1], sys.argv[2]
    try:
        curses.wrapper(lambda screen: Panel(screen, cli, Path(data)).loop())
    except KeyboardInterrupt:
        return 130
    except curses.error:
        print("The terminal could not start Heimdall's panel. Check TERM and try again.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
