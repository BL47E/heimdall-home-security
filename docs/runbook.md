# Running Heimdall

This runbook covers the shell monitor and owner-requested local browser dashboard described in [ADR 0003](adr/0003-shell-monitor-with-local-dashboard.md). The first CLI is implemented and [tested on blue](verification/2026-11-04-cli-blue.md), including real fourth-failure alerts and restart persistence. The browser has local and HTTP-to-shell checks. Commands and schemas follow [the runtime contract](runtime-contract.md); boot/systemd recovery and faculty acceptance of the dashboard remain open.

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

For the verified installation on blue, use `~/heimdall/heimdall help` or `~/heimdall/heimdall status` from any directory. This launcher points to the release recorded in [VM verification](verification/2026-11-04-cli-blue.md). The monitor was manually started and checked from the VM console after the deployment SSH connection closed; boot startup is still a separate step.

In blue's terminal, enter the repository directory before running these commands:

```sh
./bin/heimdall init
./bin/heimdall status
./bin/heimdall monitor start
./bin/heimdall status
```

`init` prepares private state with defaults. `start` starts a background reader of `journalctl -u ssh`; `status` reports whether that reader is alive and whether journal coverage is available. A running browser is not evidence that monitoring is healthy. Initial monitoring starts at the current journal position; subsequent starts use the saved cursor, a journal record reference that prevents replay from being counted twice. Cursor loss, unreadable logs or a terminated reader must remain visible in status.

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

Stop the background reader with `./bin/heimdall monitor stop`. Foreground operation for a service manager is `./bin/heimdall monitor run`.

Transaction and monitor locks use an operating-system advisory lock through a small Python standard-library helper. A process crash releases its lock automatically; the next monitor owns and cleans only its known scratch files. Keep `.transaction.lock` and `.monitor.lock` in place while any Heimdall process runs. Never remove locks to bypass an active writer. Mock crash/restart tests establish local recovery behavior; boot and systemd recovery still need Ubuntu evidence.

## Packaging a build for the VM

On the development Mac, run `./scripts/package.sh` from the repository. It writes `dist/heimdall-0.1.0.tar.gz` and a SHA-256 checksum file. Only the allowlisted application, tests, synthetic fixtures and selected documentation are packaged; local evidence, tokens and caches are excluded. Transfer both files to blue using verified SSH, check `sha256sum -c heimdall-0.1.0.tar.gz.sha256` there, then extract into a fresh release directory under `~/heimdall/releases`. Keep an earlier release and live state intact when updating. Start the new build using its own `bin/heimdall` path; no system-wide installation or PATH edit is required.

Retention cleanup is currently explicit: `./bin/heimdall cleanup`. It uses the configured retention period; daily scheduling remains planned. Do not claim the uninstalled monitor service template schedules cleanup.

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

For Mac-to-blue access, use the current Host-Only address when available. Historical addresses in the diary may have changed. Stop the loopback server with Ctrl+C, then bind to the chosen address explicitly; replace `BLUE_LOCAL_IP` with that address:

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

`deploy/heimdall-monitor.service.in` is an **uninstalled template**, not an active service. systemd is Ubuntu's service manager: it can start the monitor at boot and attempt a limited number of restarts after failure. It does not run the dashboard or enable blocking.

Before installing, choose the owner account, absolute repository path and private absolute state directory. Replace every `@...@` placeholder, inspect the resulting file and verify its commands manually under that account. The template grants the service journal-read access using `SupplementaryGroups=systemd-journal`; an administrator should review that broader read access. The state directory must already exist and belong to the selected user.

Only after manual review, place the completed unit at `/etc/systemd/system/heimdall-monitor.service`, run `sudo systemctl daemon-reload`, and choose whether to start it with `sudo systemctl start heimdall-monitor`. Enable boot startup separately with `sudo systemctl enable heimdall-monitor` when ready. Do not run a separate CLI-started monitor alongside the service. Check both `systemctl status heimdall-monitor` and `./bin/heimdall status` under the configured account/state path. A daemon restart is not evidence of complete journal coverage.

To undo the service setup, stop and disable that unit, remove only its reviewed unit file, and reload systemd. Keep the state directory until the owner decides how to archive its records. No setup command in this section has been executed automatically.

## Verification and remaining evidence

Record exact checks and outcomes with the implementation issue. At minimum, verify three versus four failures, window expiry, separate IPs, malformed fields, duplicate replay, review/reopen, persistent restart state, invalid configuration and unauthorized browser requests. Real blue-VM journal parsing, access denial, cursor resumption, boot/crash recovery and controlled red-to-blue tests require separate live evidence. Faculty questions about permitted tools, final report, deadline and presentation remain open.
