# Verification records

Each file is a dated observation. Its statements about what was still planned apply to that checkpoint, not automatically to today's source or deployment. Preserve those original results and limitations; use the [current implementation status](../status.md) and [runbook](../runbook.md) when resuming.

| Record | What it establishes |
| --- | --- |
| [November 25 service switch](2026-11-25-service-switch.md) | All installed units and the launcher switched from the `vt` preview release to `0.1.0-342daa1`; control identity verified, state preserved. Explains the designed release-identity check. |
| [November 25 release](2026-11-25-release-verification.md) | Updated CLI (`342daa1`: VirusTotal, terminal app, monitor-start fix) deployed as a fresh release on blue; all 82 tests pass on the VM. The service and launcher still run the older release. |
| [November 17 Discord](2026-11-17-discord.md) | Current real delivery, controlled sender-only failure/recovery and automatic timer delivery. Latest recorded state: 136 events, three alerts, four notices delivered in three messages. |
| [November 17 deployment](2026-11-17-deployment.md) | Source `ecaec12` deployed; service-aware CLI/API control checks, preserved state and enabled daily cleanup. Discord was not yet enabled at this earlier point that day. |
| [November 17 source](2026-11-17-source.md) | Queue concurrency fix, packaging and all 66 tests passing on Ubuntu; distinct from live external-provider evidence. |
| [November 7 service](2026-11-07-systemd.md) | Actual boot startup, bounded crash recovery and retry limiting for the earlier release. Later service-aware controls supersede its operating advice. |
| [November 7 red/blue](2026-11-07-red-blue-recovery.md) | Real threshold/reopening input and manual console recovery. |
| [November 7 source](2026-11-07-swarm-source.md) | Local fake-manager and cleanup-template tests before later deployment. |
| [November 5 dashboard](2026-11-05-dashboard.md) | Authenticated dashboard/browser behavior, including labelled synthetic scenarios and stated limits. |
| [November 4 CLI](2026-11-04-cli-blue.md) | Packaged CLI on blue, real threshold/reopening alerts and cursor/restart persistence. |

Synthetic, sanitized-export and live-journal evidence are different: see the [fixture provenance](../../tests/fixtures/README.md). Credentials, raw private state, provider URLs and original private VM evidence are excluded from repository records. Passing tests or a running process alone does not prove uninterrupted monitoring or remote message acceptance.
