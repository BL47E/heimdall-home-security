# Live red-to-blue alerting and manual console recovery

Subsequent checkpoint: the owner provided administrator authentication and the prepared service was installed and verified for automatic crash recovery, bounded retries and startup after reboot. See [service verification](2026-11-07-systemd.md). The preparation notes below preserve the earlier checkpoint.

Observed on 2026-11-07, approximately 21:36–21:40 IST. These are real Ubuntu SSH records and deployed Heimdall results, not synthetic fixtures. Commands were entered through the Parallels VM consoles; the Mac had no loaded SSH identity. No runtime source was changed.

## Environment and initial state

- Parallels reported `UbuntuServMain` (blue) and `UbuntuServTest` (red) running. Guest tools remain uninstalled.
- Blue: `10.37.129.3`; red: `10.37.129.4`. Red's `ip route get 10.37.129.3` selected `enp0s6` with source `10.37.129.4`.
- Red's existing known-hosts file contained blue's host keys. Every test used `StrictHostKeyChecking=yes`; no host-key warning was bypassed.
- Blue's owner account is `bl47eheim`, red's is `blazetest`.
- Blue's launcher points to `/home/bl47eheim/heimdall/releases/0.1.0.lzc7GK/heimdall-0.1.0/bin/heimdall` (version 0.1.0).
- Initial status: stopped, coverage unavailable, 44 stored events, one existing Mac-source alert. Configuration: threshold 4, window 300 seconds, retention 60 days.
- Manual monitor startup resumed the journal and reached 48 events with available coverage. Its observed PID was 3903.

## Checks and observed results

| Check | Result |
|---|---|
| Three red-to-blue failed password attempts | Exactly three recognized failures for `heimdall_probe_invalid` from red; no red-source alert. Existing Mac-source alert remained unchanged. |
| Fourth failure within five minutes | New alert `ssh-a934b6b69ec0b8ab5a6bec2c`, source `10.37.129.4`, count 4, severity `MEDIUM`, status `needs_review`. Total events 68, alerts 2. |
| Review, then fifth failure | Same alert reached count 5 and reopened as `needs_review`. History retained the owner review and `new_failure` reopening. |
| Report export | CLI report command completed and saved a local text report. Report contents were not separately reviewed in this session. |
| Forced monitor crash | Verified PID 3903's command was the deployed `heimdall monitor run`, then sent SIGKILL to that PID only. Status reported `error`, null PID, unavailable coverage, and `Monitor process exited; coverage unavailable`. |
| Recovery from blue's console | Manual `monitor start` produced PID 5233 with available coverage and no last error. Before/after counts stayed at 73 events and 2 alerts; the red alert remained at 5 failures. No lock files were removed. |
| Dashboard restart and live HTTP | Started the deployed server manually on `10.37.129.3:8765`. Mac GET `/overview` returned HTTP 200. On blue, authenticated HTTP login and GET `/api/status` and `/api/alerts` succeeded; the returned monitor PID, coverage and both alert counts agreed with the CLI. Token and cookie values were not printed or saved in the evidence result. |

The controlled attempts targeted a deliberately nonexistent username on the owned blue VM. Red used one password prompt per connection, password-only authentication, and `/bin/echo` as an askpass helper to supply a deliberately invalid response without collecting a real password. Supporting PAM/closure messages were not counted as additional password failures. Recorded first three event timestamps were `1794067710.449572`, `1794067714.106175`, and `1794067716.933075` (Unix seconds).

One initial read-only jq inspection had a quoting error; it was corrected with a single-quoted filter before confirming the three-event result. This did not modify application state.

## Private evidence on blue

Evidence was created with umask 077 under `/home/bl47eheim/heimdall/evidence/2026-11-07/`: `baseline.json`, `three-alerts.json`, `three-events.json`, `four-alerts.json`, `reviewed.json`, `reopened.json`, `report.txt`, `pre-crash.json`, `crashed.json`, `restarted.json`, `http-live.json`, `final-status.json`, and the staged service file. The directory also holds the dashboard operational log. Raw private evidence was not copied into Git. This document is the sanitized observation record; it is not a byte-for-byte journal export.

## Boot-service preparation and remaining gate

Resolved the deployed service template's placeholders for blue's actual account, release path and private state directory, saving `heimdall-monitor.service` in the evidence directory. The state directory belongs to `bl47eheim` with mode 700. `systemd-analyze verify` returned exit 0. `systemctl is-enabled heimdall-monitor.service` returned `not-found`: the unit is not installed.

Removed `SupplementaryGroups=systemd-journal` from this staged instance because the owner account already has journal access through its existing `adm` membership; no additional group access is needed. The repository's general template remains unchanged. The staged unit runs as the owner, restricts writes to the state directory, uses a private temporary directory, restarts on failure after five seconds and limits starts to three in sixty seconds. Validation establishes syntax and referenced-command validity, not successful sandboxed runtime or boot operation.

`sudo -n true` returned 1, so administrator authentication is required before installation. Installation, service startup, automatic crash restart, restart-limit behavior and a real reboot check remain unperformed. Stop the manually started monitor before starting the service. Review dashboard start/stop semantics under systemd before claiming those controls reliably stop a service-managed monitor.

Manual console recovery of the monitor is verified. Recovery from an SSH source block, a fresh console login and reboot recovery are not established. No firewall, SSH access, adapter, account-membership or boot-service changes were made. Discord, VirusTotal and enforcement remain planned. The monitor and dashboard were left running manually.

The owner supplied running VMs and authorized this work package; the assistant executed the checks and recorded observations. This does not establish either student's individual academic contribution.
