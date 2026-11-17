# Swarm source verification

This record covers local source work after the November 7 live VM checks. It does not establish that these source changes are deployed on blue. The already installed monitor service and its real boot/crash checks are documented separately in [service verification](2026-11-07-systemd.md).

## Stage 1 — Service-aware monitor control

Implemented a fixed system-unit boundary in `lib/service.py`, called by the shell lifecycle and status operations. The helper only normalizes systemctl metadata and invokes the fixed unit; shell/jq remains responsible for SSH parsing, alert rules and saved state. Auto mode detects `heimdall-monitor.service` and verifies the configured owner, release, state path and exact foreground command before control. It refuses mismatch, ambiguity, failed inspection and manual foreground/standalone bypass. A managed foreground invocation must belong to the actual Linux control group for this unit; environment markers do not grant that permission.

The browser still uses the CLI. A fixed service-control failure marker and exit 77 produce an actionable HTTP 503 response; arbitrary command stderr is not exposed. The implementation does not add sudo, authorization policy, a privileged web server, an installer or an automatic VM change. On an ordinary unprivileged deployment, service control can still require an administrator's console command. Fixture status and standalone operation without an installed unit remain available offline.

Worker runtime changes were inspected and integrated with independent fake-manager tests and the handler's narrow HTTP error mapping. Tests cover fixed noninteractive dispatch, denied authorization without process fallback, mismatched identity, ambiguous and user-controlled property text, bounded timeout, inactive/failed service health, saved process safety, auto selection, fixture independence and foreground bypass with a spoofed environment marker. The existing mock-journal tests now hide real host units so tests cannot control an installed service.

Handler verification passed:

- `python3 -m unittest discover -s tests -v`: **42 tests**, 19.195 seconds.
- `bash tests/test_monitor.sh`: shell configuration checks and its 19 monitor scenarios passed.
- Bash syntax for CLI/monitor, Python compilation for service helper/HTTP bridge and `git diff --check` passed.

These fake-manager and HTTP checks do not establish real systemd control authorization or real cgroup startup with the new helper. Deployment and live service-aware control checks on blue remain open. The installed older release still requires explicit systemctl lifecycle management.

The user requested two workers plus a dedicated handler. Runtime and test workers contributed separate changes; the handler reviewed their artifacts, added the HTTP mapping and maintained the shared contract/runbook/checklist. These are agent contributions, not evidence of either student's academic contribution. Existing local work and earlier verification records were preserved. No commit, push, external notification or VM deployment accompanies this source checkpoint.

## Stage 2 — Optional daily cleanup templates

Added `deploy/heimdall-cleanup.service.in` and `deploy/heimdall-cleanup.timer.in`. The fixed oneshot command invokes the shell cleanup operation as the same owner, release and state directory as the monitor. No journal group, monitor lifecycle action or automatic installation is included. Daily scheduling uses `Persistent=true`, up to fifteen minutes of randomized delay and one-minute accuracy. A missed schedule catches up once, rather than replaying every missed day.

The independent rendered-template tests execute the actual cleanup command against disposable state and check expiration, retention of old supporting evidence for retained alerts, review history, unchanged configuration and private file permissions. Handler verification: **3 tests passed, 1 skipped** because `systemd-analyze` is unavailable on this Mac. The skipped test is the real Ubuntu unit-parser check; fake execution is not evidence that the timer is installed or firing. `git diff --check` passed. A temporary package included the new deploy templates; the existing `dist/` release was left untouched.

No daily cleanup was activated on blue. Preservation of pending notification references is coupled to the next delivery-state implementation, and real block-state retention remains planned with enforcement.
