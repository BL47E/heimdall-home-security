# Service controls and daily cleanup deployment

Verified November 17, 2026, IST. The owner requested checking/saving local work and deploying service-aware controls plus daily cleanup using the running VMs. Computer Use operated the Parallels consoles; the owner unlocked the consoles and supplied administrator authentication at blue's normal password prompt. No credential is included in this record.

## Release and preflight

- Source checkpoint: `ecaec12`, branch `codex/service-cleanup-deployment`; application version remains `0.1.0`.
- Archive SHA-256: `aec7a7b210187426278dc460008fbca64a270c83a74c3824867f3df327310c9e`, verified on blue before extraction.
- New release: `/home/bl47eheim/heimdall/releases/0.1.0-ecaec12/heimdall-0.1.0`.
- Preserved old release: `/home/bl47eheim/heimdall/releases/0.1.0.lzc7GK/heimdall-0.1.0`.
- Same existing user/group `bl47eheim`, state directory `/home/bl47eheim/.local/state/heimdall`, and launcher `~/heimdall/heimdall`.
- On blue: all 66 Python tests passed in 34.232 seconds with no skips; shell/configuration checks and 19 monitor scenarios passed in 4.675 seconds. `systemd-analyze verify` accepted the resolved monitor, cleanup service and cleanup timer units.

Temporary transfer used Python standard-library HTTP on the existing Host-Only network between Mac `10.37.129.2` and blue `10.37.129.3`; no packages, SSH access credentials, firewall rules or adapters were added. The archive excluded private state, tokens, credentials and caches. Tests used isolated synthetic state and fake providers/managers, not blue's live records. Source verification is [recorded separately](2026-11-17-source.md).

## Installed and preserved

Installed root-owned mode-644 monitor/cleanup units under `/etc/systemd/system/`, with the reviewed owner/release/state values. Preserved blue's existing journal-read permissions without adding the template's supplementary group. Retained bounded monitor restarts and the existing sandbox settings. Updated the owner launcher to match the new monitor unit. The separate dashboard runs unprivileged on `10.37.129.3:8765`; its startup remains manual.

Stopped writers and saved private state backups plus the previous unit/launcher under `~/heimdall/evidence/2026-11-17/` and `attempt2/`. Compared every prior stored event and both alert objects—including review history—after the update and cleanup. All 93 baseline events, both alerts and configuration were preserved. File mode remained 0600. No lock files were deleted.

The first verification attempt expected exit 77 for a duplicate foreground reader while the monitor lock was already held. The actual correct result was exit 1 with `operation is already active; lock wait expired`. That overly strict harness assertion triggered restoration of the previous monitor unit/launcher. Corrected the harness to accept the documented lock refusal and repeated deployment, preserving the first backup and recording a separate second attempt. No runtime code change was needed for this verification correction.

## Live control checks

The new monitor identified the real fixed unit and actual matching process, with running/available coverage. CLI `monitor stop` and `monitor start` returned exit 77 under existing Ubuntu authorization. Authenticated HTTP requests to both lifecycle endpoints returned HTTP 503 with the administrator's console command. Neither denied request changed the supervised PID or launched a fallback. Unauthorized status returned HTTP 401; login/status/logout succeeded without exporting the owner token.

A forced standalone selection was refused. While the service was running, duplicate foreground startup was prevented by its lock. After an administrator stopped the new unit, CLI status showed stopped/unavailable; direct foreground startup was then refused by the service/cgroup guard with exit 77, and unprivileged start remained denied without a fallback. Administrator start restored running/available coverage, PID 21431 at that checkpoint. The monitor remains enabled at boot. Real reboot/crash/retry-limit verification from November 7 remains [historical evidence](2026-11-07-systemd.md); those destructive scenarios were not repeated for this update.

These controls are service-aware, but this installation does **not** grant one-click browser start/stop. Use `sudo systemctl start|stop|restart heimdall-monitor` in blue's console. No authorization policy, stored sudo credential or privileged dashboard was introduced.

## Daily cleanup

Enabled `heimdall-cleanup.timer` with `OnCalendar=daily`, `Persistent=true`, fifteen-minute randomized delay and one-minute accuracy. The timer recorded an actual trigger at **15:36:17 IST**, and the cleanup service completed successfully; an explicit repeat service invocation also completed with `Result=success`, `ExecMainStatus=0`, at **15:38:07 IST**. The observed next trigger was **November 18 at 00:05:11 IST**. No accelerated schedule or temporary timer override was installed.

The cleanup service runs the new release's CLI as the same owner with writes restricted to the live state directory. It does not control the monitor. Synthetic tests establish expiration of eligible old records and preservation of retained-alert evidence, review history and pending notification references. Live history was younger than the 60-day default and remained intact. Active-block retention cannot be established because enforcement state is unimplemented. A later unattended midnight trigger or reboot catch-up was not observed in this session.

## Fresh input and remaining boundaries

A controlled test from red (`VirtualTest`, Host-Only `10.37.129.4`) checked blue's ED25519 host key against its console fingerprint, kept strict host checking enabled, and sent one deliberately invalid password for `heimdall_deploy_probe`. SSH returned the expected permission denial. Blue ingested exactly one matching journal-provenance password failure (`invalid_user=true`, source `10.37.129.4`, timestamp `1794910283.569157`). Final state had 99 total stored events, two unchanged alerts/review histories and healthy systemd coverage under PID 21431. The extra stored records include supporting SSH messages; they do not represent six failed authentications. All 93 baseline events remained unchanged. This is a fresh ingestion smoke check, not another four-failure threshold or concurrent-window demonstration.

Discord remains disabled, unconfigured, with no pending messages or credential file. No real Discord destination, delivery timer, VirusTotal provider or SSH blocking was activated. Student contributions and faculty questions remain unresolved. Git checkpoints are local; no push, issue comment or other external message accompanies this work.

Private VM evidence: `~/heimdall/staging-20261117/{tests.log,shell-tests.log,unit-verify.log}`; `~/heimdall-deployment-20261117.log`; `~/heimdall-deployment-20261117-attempt2.log`; and `~/heimdall/evidence/2026-11-17/attempt2/{state-before.json,state-before.tar.gz,heimdall-monitor.service.before,heimdall-launcher.before,lifecycle-check.txt,final-observation.txt}`. The state archive includes authentication material and must remain private. The temporary Mac transfer server was stopped after collecting verification; the dashboard remained reachable from the Mac (HTTP 200), while unauthenticated evidence stayed protected (HTTP 401).
