# Running Heimdall

Current operating checkpoint: [November 17 status](status.md), [deployment](verification/2026-11-17-deployment.md) and [Discord](verification/2026-11-17-discord.md). Monitor, cleanup and sender are enabled on blue; the dashboard starts manually. Dated records are not a fresh health probe.

This runbook covers the shell monitor and owner-requested local browser dashboard described in [ADR 0003](adr/0003-shell-monitor-with-local-dashboard.md). The first CLI is implemented and [tested on blue](verification/2026-11-04-cli-blue.md), including real fourth-failure alerts and restart persistence. The dashboard was verified on blue over loopback and from the Mac over Host-Only. [Deployment evidence](../diary.md#2026-11-05--dashboard-deployed-and-verified-on-blue) Commands and schemas follow [the runtime contract](runtime-contract.md); boot startup and bounded systemd recovery were verified on blue on 2026-11-07 ([evidence](verification/2026-11-07-systemd.md)); faculty acceptance of the dashboard remains open.

## What runs where

Run the live monitor on **blue**, the Ubuntu VM receiving SSH attempts. Red is the controlled test source. A browser connects to the HTTP bridge on blue; the bridge asks the shell CLI to read alerts, update review status, control the monitor or save validated settings. Closing the browser does not stop the monitor. Shell/jq interprets SSH messages and maintains rules and alert state; Python handles HTTP and validates canonical IP addresses/content fingerprints through a small normalization helper.

Local records default to `~/.local/state/heimdall` for the account running the software. Directories are private and files contain the SSH evidence and owner token. Use the same account and `HEIMDALL_DATA_DIR` for CLI, monitor and web server. Do not run the web server as root.

## Ubuntu prerequisites

Open a terminal on blue. From a checkout of this repository, install the supporting tools if they are absent:

```sh
sudo apt update
sudo apt install jq python3 openssh-server
bash --version
jq --version
python3 --version
journalctl -u ssh -n 5 --no-pager -o json
```

The first two commands contact Ubuntu's package repositories and need administrator permission. The final command reads five records from the SSH service's system journal. Confirm that it shows SSH records and no access warning. Successful execution with empty output alone does not prove access to the system journal. This installation's SSH unit is `ssh`; unsupported authentication methods and unrelated services are outside initial coverage.

If the owner account cannot read SSH's system journal, an administrator must review whether to grant that account `systemd-journal` membership. That group grants access to more than SSH records. After an approved group change, sign out and back in and repeat the read check. Do not solve journal permissions by running the browser server as root.

## Local CLI and live monitoring

The current application version is `0.1.0`. From its release directory, `./bin/heimdall help` lists the commands, `./bin/heimdall version` prints the version, and `./bin/heimdall demo` runs a labelled synthetic walkthrough without changing live state. The CLI prints JSON for machine-readable operations; pipe a result to `jq` when inspecting it. `config history` shows saved configuration changes.

For the verified installation on blue, use `~/heimdall/heimdall help` or `~/heimdall/heimdall status` from any directory. This launcher now points to `/home/bl47eheim/heimdall/releases/0.1.0-ecaec12/heimdall-0.1.0`, deployed and verified on November 17 ([evidence](verification/2026-11-17-deployment.md)). After the November 25 lab rename the account is `blazeblue`, so that release tree now lives under `/home/blazeblue/heimdall`; a newer `0.1.0-vt` release was also observed there. The latest previous launcher is saved privately under `~/heimdall/evidence/2026-11-17/attempt2/heimdall-launcher.before`; the older `heimdall.before-dashboard` checkpoint is historical. The monitor is now managed by the enabled `heimdall-monitor.service` on blue. Check `systemctl status heimdall-monitor --no-pager` and `~/heimdall/heimdall status` after boot. Use `sudo systemctl start|stop|restart heimdall-monitor` to manage this installed service; the vertical bars mean choose one action. Browser/CLI controls now validate and address the fixed systemd unit. Existing Ubuntu authorization denies unprivileged start/stop, returning an administrator instruction instead of starting a separate process. Use the console systemctl commands for actual lifecycle changes on blue.

For a new standalone setup with no installed monitor service, enter its release directory and run these commands. On blue's existing service-managed installation, use the administrator systemctl commands above instead of standalone startup:

```sh
./bin/heimdall init
./bin/heimdall status
./bin/heimdall monitor start
./bin/heimdall status
```

`init` prepares private state with defaults. With no installed service, `start` starts a background reader of `journalctl -u ssh`; `status` reports whether that reader is alive and whether journal coverage is available. A running browser is not evidence that monitoring is healthy. Initial monitoring starts at the current journal position; subsequent starts use the saved cursor, a journal record reference that prevents replay from being counted twice. Cursor loss, unreadable logs or a terminated reader must remain visible in status.

Inspect findings through the same commands used by the dashboard:

```sh
./bin/heimdall alerts
./bin/heimdall events
./bin/heimdall config get
./bin/heimdall config set '{"threshold":4,"window_seconds":300,"retention_days":60}'
```

To inspect, review or export an alert, replace `ALERT_ID` with an ID returned by `alerts`:

```sh
./bin/heimdall inspect ALERT_ID
./bin/heimdall review ALERT_ID
./bin/heimdall reopen ALERT_ID
./bin/heimdall report ALERT_ID
```

An alert's review status records the owner's investigation progress. New failures reopen a reviewed alert while its burst remains active. Review commands do not change SSH access. Configuration accepts only bounded integers: threshold 2–100, window 30–3600 seconds and retention 1–365 days. Changes apply to later events; existing findings retain their rule settings.

On a standalone installation, stop the background reader with `./bin/heimdall monitor stop`. With a matching installed unit, start/stop addresses systemd and may require administrator console action. Foreground `./bin/heimdall monitor run` is owned by that service and cannot be used to bypass it.

Transaction and monitor locks use an operating-system advisory lock through a small Python standard-library helper. A process crash releases its lock automatically; the next monitor owns and cleans only its known scratch files. Keep `.transaction.lock` and `.monitor.lock` in place while any Heimdall process runs. Never remove locks to bypass an active writer. Mock crash/restart tests establish local behavior. Real blue service crash recovery, retry limiting and boot startup are recorded in [service evidence](verification/2026-11-07-systemd.md).

## Terminal panel and onboarding

Run `./bin/heimdall` with no arguments in an interactive terminal to open the Heimdall terminal app; `./bin/heimdall tui` is the explicit form. Noninteractive invocations (scripts, pipes) still print plain help. On Blue, the installed launcher opens the app once a release containing it is installed. Use a regular login and a terminal with Python curses support and at least 48 columns by 14 rows. The palette uses a genuine black background with light text and one cyan accent; the first line always shows monitor state, coverage and alert counts.

The first launch in each state directory opens guided onboarding: a welcome, a prerequisites and SSH journal check, and local state preparation. An existing state directory — such as Blue's — is adopted unchanged; nothing is reset and no history, reviews or provider configuration are touched. Finish in **local mode** for live SSH monitoring or **offline mode** to start with the labelled demo. Completion is saved explicitly in a private `tui.json` record; later launches open the regular workspace, and Setup remains available for rechecks. Opening the panel never modifies accounts, groups, network, firewall or services.

- **Overview** is the working home: monitor status and start/stop, each alert with its investigation and review/reopen, recent events, rule settings and provider summary, plus access to Setup and Demo.
- Press **1–4** or **Tab** to switch pages, **Up/Down** to select, **Enter** to open, **r** to refresh. In detail panels, **Up/Down** scrolls, **Esc** returns, and **y** confirms or reviews where a footer says so.
- Type **/** to open the persistent command bar. Commands: `/overview`, `/setup`, `/providers`, `/demo`, `/refresh`, `/config {"threshold":5}` (confirmed before applying), `/help`.
- Leaving during normal use requires the exact command **`/exit`**. Neither **q** nor **Esc** exits; Esc cancels the command bar, returns from details or steps back in onboarding. Ctrl+C also interrupts the process and restores the terminal.
- In **Setup**, check the required tools and initialize local state. Open **SSH journal** for the read-access check and the administrator's permission review steps. **Providers** accepts optional Discord and VirusTotal credentials through hidden input; saving a Discord webhook and enabling delivery are separate actions. **Demo** runs the synthetic walkthrough in separate state.

The panel shows installer and permission commands for review in the VM console. Run approved administrator commands there, then return to Setup and press **r** to check access again.

## Packaging a build for the VM

On the development Mac, run `./scripts/package.sh` from the repository. It writes `dist/heimdall-0.1.0.tar.gz` and a SHA-256 checksum file. Only the allowlisted application, tests, synthetic fixtures and selected documentation are packaged; local evidence, tokens and caches are excluded. Transfer both files to blue using verified SSH, check `sha256sum -c heimdall-0.1.0.tar.gz.sha256` there, then extract into a fresh release directory under `~/heimdall/releases`. Keep an earlier release and live state intact when updating. Start the new build using its own `bin/heimdall` path; no system-wide installation or PATH edit is required.

Retention cleanup runs explicitly with `./bin/heimdall cleanup`. It uses the configured retention period. The daily cleanup timer is installed and enabled on blue. It uses the same owner, release and state directory as the monitor; the monitor service itself does not schedule cleanup.

### Optional daily retention schedule

`deploy/heimdall-cleanup.service.in` and `deploy/heimdall-cleanup.timer.in` are manual templates. Resolve the service's owner, group, absolute release directory and private state directory to the same values as the monitor. The cleanup command needs no journal group and runs as that owner with writes limited to the state directory. It does not start, stop or restart monitoring.

The timer runs daily with up to fifteen minutes of randomized delay. `Persistent=true` requests one catch-up run after downtime, rather than one run for every missed day. Review the resolved units and run `systemd-analyze verify` on Ubuntu before installation. After explicit owner approval, install only those reviewed units, reload systemd and enable `heimdall-cleanup.timer`; inspect `systemctl list-timers heimdall-cleanup.timer` and the cleanup service journal to verify actual execution. The reviewed schedule was activated on blue on November 17, with a timer trigger and successful cleanup recorded in [deployment evidence](verification/2026-11-17-deployment.md). This section explains the setup; do not reinstall it when simply resuming the lab.

Local rendered-unit tests verify the command against disposable state, including preservation of supporting evidence and review history for retained alerts. Local pending-notification retention is implemented and covered by synthetic delivery tests; active block retention remains a future enforcement obligation because blocks are not implemented.

## Browser login on blue

Run this in a second terminal in the repository, with the same account and state directory:

```sh
python3 web/server.py --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765` in blue's browser. The server creates a private `web-token` file and prints its location. Read that file in blue's terminal, paste its token into the dashboard's owner login, and leave the token out of screenshots, Git and shared messages. The browser receives a session cookie; the owner token is never placed in a URL. This token is separate from the Ubuntu password.

Overview, Investigations, Activity and Settings have distinct URLs (`/overview`, `/investigations`, `/activity` and `/settings`). You can open or reload one directly and use the browser's Back and Forward controls. If sign-in is needed, the requested page remains selected after login. The page shell is public; evidence still requires the owner session.

Settings warns before you leave with unsaved edits. The interface uses locally bundled JetBrains Mono, with a system monospace fallback; it needs no external font connection. Sign-out and expired sessions clear the displayed records, and a page restored with Back or Forward checks its session before showing them again.

The dashboard exposes monitoring status, alert evidence, review/reopen, recent events, report downloads and configuration. Start/stop controls operate the monitor, not Ubuntu's SSH service. Discord, reputation enrichment and blocking must show their actual implementation state and must not be presented as active protection.

## Browser access from the trusted local network

Loopback (`127.0.0.1`) accepts only browsers on blue. To use a browser on the Mac or another device on a reachable trusted lab network, identify blue's actual address first:

```sh
ip -br address
```

For Mac-to-blue access, use the current Host-Only address when available: after the owner's laptop reset this is `10.37.129.8` (observed November 25), so the dashboard URL is `http://10.37.129.8:8765/overview`. Earlier verified addresses in the diary are historical. After booting blue, start the dashboard manually from the deployed release directory using the command below. Stop the loopback server with Ctrl+C, then bind to the chosen address explicitly; replace `BLUE_LOCAL_IP` with that address:

```sh
python3 web/server.py --host BLUE_LOCAL_IP --port 8765
```

Open `http://BLUE_LOCAL_IP:8765` from a browser that can reach it, then use the same owner-token login. Prefer a specific address to `0.0.0.0`, which listens on every adapter. Parallels Host-Only is ordinarily reachable from the Mac and guests on that network, not directly from a phone. T3 Connect screenshots show the Mac's work; they do not automatically make the VM's dashboard reachable from the phone.

This is plain HTTP for a trusted lab. Do not enter tokens on an untrusted network or configure router port forwarding. Remote access and TLS termination require a separate reviewed setup. Do not change the Mac firewall, VM firewall, adapter topology or router automatically to make the page reachable.

## Offline synthetic demonstration on macOS or Ubuntu

Offline ingestion is useful when no VM, journal access or provider credentials are available. It does not monitor the host's real SSH service. On macOS, install jq through your usual package manager if needed; the scripts target the supplied Bash 3.2 and use no hosted JavaScript or Python packages.

Keep sample state separate from live evidence. From the repository:

```sh
export HEIMDALL_DATA_DIR="$(mktemp -d "${TMPDIR:-/tmp}/heimdall-demo.XXXXXX")"
./bin/heimdall init
./bin/heimdall ingest tests/fixtures/password-burst.jsonl
./bin/heimdall alerts
python3 web/server.py --host 127.0.0.1 --port 8765
```

The fixture is synthetic, not an export of blue's journal. Its provenance notes live in `tests/fixtures/README.md`; sample state is labelled in the dashboard. Stop the HTTP server with Ctrl+C. Remove the temporary directory only after confirming it contains solely this disposable demo's state; keep live records and tokens private.

## Optional manual systemd setup

The current source includes service-aware monitor controls with automatic detection of the fixed `heimdall-monitor.service`. These changes are deployed on blue and have local fake-manager, CLI/HTTP and real service checks. They verify the installed unit's release, state directory and owner, then request noninteractive service control. Without an existing authorization policy, the command fails with a manual `sudo systemctl` instruction. It never stores a sudo password or falls back to an unsupervised monitor. Use the explicit administrator console systemctl commands above on blue; service-aware controls do not add a privilege policy.

`deploy/heimdall-monitor.service.in` is a template requiring per-host review. A resolved instance is installed and enabled on blue, with boot/crash/retry-limit checks recorded in [service evidence](verification/2026-11-07-systemd.md). systemd is Ubuntu's service manager: it can start the monitor at boot and attempt a limited number of restarts after failure. It does not run the dashboard or enable blocking.

Before installing, choose the owner account, absolute repository path and private absolute state directory. Replace every `@...@` placeholder, inspect the resulting file and verify its commands manually under that account. The template grants the service journal-read access using `SupplementaryGroups=systemd-journal`; an administrator should review that broader read access. The state directory must already exist and belong to the selected user.

Only after manual review, place the completed unit at `/etc/systemd/system/heimdall-monitor.service`, run `sudo systemctl daemon-reload`, and choose whether to start it with `sudo systemctl start heimdall-monitor`. Enable boot startup separately with `sudo systemctl enable heimdall-monitor` when ready. Do not run a separate CLI-started monitor alongside the service. Check both `systemctl status heimdall-monitor` and `./bin/heimdall status` under the configured account/state path. A daemon restart is not evidence of complete journal coverage.

To undo the service setup, stop and disable that unit, remove only its reviewed unit file, and reload systemd. Keep the state directory until the owner decides how to archive its records. The resolved blue unit was first installed with owner authorization on November 7 and updated for the new release on November 17; this section is not an instruction to reinstall it. Blue uses its existing owner journal permissions without the template’s additional systemd-journal group.

## Verification and remaining evidence

Record exact checks and outcomes with the implementation issue. At minimum, verify three versus four failures, window expiry, separate IPs, malformed fields, duplicate replay, review/reopen, persistent restart state, invalid configuration and unauthorized browser requests. Completed live journal, cursor, service and red-to-blue results are linked in the [verification index](verification/README.md). Remaining work includes additional real expired-window/concurrent-source/success-correlation scenarios, sender-timer reboot startup and later unattended cleanup/catch-up; those cases are not established by the completed tests. Faculty questions about permitted tools, final report, deadline and presentation remain open.

## November 17 deployment recovery

Blue's private backups are under `~/heimdall/evidence/2026-11-17/` and `attempt2/`: previous unit and launcher, plus `state-before.json` and a full private state archive. Keep them private because the archive includes authentication material. The old release remains in the `releases/0.1.0.lzc7GK/heimdall-0.1.0` directory, which moved to `/home/blazeblue/heimdall` with the November 25 account rename. The current release is identified by its source commit and archive checksum in the deployment evidence, even though both releases report application version 0.1.0.

To stop daily scheduling without deleting history, run `sudo systemctl disable --now heimdall-cleanup.timer` in blue's terminal. `systemctl list-timers heimdall-cleanup.timer --no-pager` shows its next trigger. `systemctl show heimdall-cleanup.service -p Result -p ExecMainStatus` shows the latest cleanup result. The current service runs daily with up to fifteen minutes of randomized delay and one catch-up after downtime; active-block retention remains future work.

A rollback must restore the old monitor unit and matching launcher together, reload systemd and start the monitor; stop the newer dashboard before launching the older one. Do not restore an old state archive during a routine code rollback, because doing so would discard newer observations. Preserve state and inspect compatibility first.

## Discord on blue

The owner-approved Heimdall webhook posts summaries to Blaze's TEST → #general. [Live verification](verification/2026-11-17-discord.md) covers threshold/reopening alerts, a controlled sender-only transport failure, grouped recovery and timer-driven delivery. Usernames, raw SSH messages and credentials are excluded from notification text. This deliberately shares summary metadata, including the lab source IP, with Discord.

In blue's terminal, `~/heimdall/heimdall discord status` shows configuration, pending/delivered notice counts, retry timing and the latest result. Counts refer to notices; several notices may share one grouped message. `discord flush` attempts eligible work immediately, respecting saved backoff. A delivery error does not stop monitoring. An ambiguous result means remote acceptance was not established; a retry can duplicate delivery.

The enabled `heimdall-discord.timer` invokes the unprivileged fixed sender service on boot and every fifteen seconds after the previous invocation finishes. Inspect `systemctl list-timers heimdall-discord.timer --no-pager` and `systemctl show heimdall-discord.service -p Result -p ExecMainStatus`. It needs no running browser. Startup after a fresh reboot remains a separate observation to capture.

To stop external delivery, run `~/heimdall/heimdall discord disable`; local monitoring and pending evidence remain. To stop scheduled checks too, run `sudo systemctl disable --now heimdall-discord.timer`. Re-enable only for the approved destination with `~/heimdall/heimdall discord enable` and `sudo systemctl enable --now heimdall-discord.timer`. Disabling does not erase pending notices or the private credential.

For an owner-approved replacement destination, use hidden input in blue's terminal, keeping the URL out of shell history and chat:

```sh
python3 - <<'PYTHON'
import getpass
import os
import subprocess
subprocess.run(
    [os.path.expanduser("~/heimdall/heimdall"), "discord", "configure"],
    input=getpass.getpass("Discord webhook URL (hidden): ") + "\n",
    text=True, check=True,
)
PYTHON
```

Configuration starts disabled; inspect status and explicitly enable after checking the destination. The private `~/.local/state/heimdall/discord-webhook` file must remain mode 0600 and must not enter Git, reports or screenshots. Correct a deleted/rejected destination through configuration; repeatedly flushing it will not repair its credentials. A timer exit status of zero alone does not prove delivery—also inspect provider status and pending work.

## VirusTotal IP reputation

From the repository root, run `./bin/heimdall demo` to see a labelled, simulated result on the private lab IP. The demo uses a separate state directory and works without an account or internet connection.

For a live lookup, use the checkout or release containing VirusTotal support. In its repository or release directory, run the following from your terminal to save your key through a hidden prompt. A configured key enables manual lookups for that state directory. [VirusTotal authentication](https://docs.virustotal.com/reference/authentication)

```sh
python3 - <<'PYTHON'
import getpass
import subprocess
subprocess.run(
    ["./bin/heimdall", "virustotal", "configure"],
    input=getpass.getpass("VirusTotal API key (hidden): ") + "\n",
    text=True, check=True,
)
PYTHON
```

Run `./bin/heimdall alerts` to find the alert ID and review its source IP. For a public IP you are authorized to share, run `./bin/heimdall virustotal lookup ALERT_ID`, replacing `ALERT_ID` with the saved alert's ID. VirusTotal may add a queried IP to its dataset. Choose only non-sensitive indicators. Heimdall sends the selected IP with the API key in the authentication header. [IP report and data sharing](https://docs.virustotal.com/reference/ip-info)

The result appears in Investigations and `./bin/heimdall report ALERT_ID`. The reputation label uses the sum of malicious and suspicious vendor results. Ten or more flags raise the alert severity to High. An unavailable lookup appears as Unknown. Successful lookups are reused for 24 hours. Heimdall limits its requests to four per minute and 500 per rolling day per state directory. VirusTotal applies account limits across clients. [Public API quotas](https://docs.virustotal.com/reference/public-vs-premium-api)

`./bin/heimdall virustotal status` checks local key setup. `./bin/heimdall virustotal disable` removes the private key and preserves alert evidence. The credential is stored as `virustotal-key` in the private Heimdall state directory with mode 0600.
