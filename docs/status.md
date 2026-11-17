# Implementation status — November 17, 2026

This is the current milestone checkpoint, based on recorded evidence rather than a fresh VM probe. Application version is `0.1.0`; blue runs runtime source commit `ecaec12` at `/home/bl47eheim/heimdall/releases/0.1.0-ecaec12/heimdall-0.1.0`. Later repository commits update documentation and ignore rules. A Git push, a merge into `main`, and a VM deployment are separate operations; merging documentation does not deploy software.

## Implemented and verified

| Capability | Code and tests | Evidence and limits |
| --- | --- | --- |
| Password-result parsing and four failures per IP in 300 seconds | `lib/parse.jq`, `lib/normalize.py`, `lib/rules.jq`; `tests/test_monitor.py` | [CLI verification](verification/2026-11-04-cli-blue.md), [red-to-blue checks](verification/2026-11-07-red-blue-recovery.md) and [Discord threshold test](verification/2026-11-17-discord.md). Only explicit password results count; supporting messages remain evidence. |
| Rolling windows, source separation, missing fields, replay and success correlation | Same parser/rules and monitor scenario tests | Synthetic boundary/multiple-IP tests and sanitized real exports pass. Additional real expired-window, concurrent-source and success-correlation demonstrations remain open. |
| Persistent alerts, review/reopen history, configuration, text reports and isolated demo | `bin/heimdall`, `lib/lock.py`, `lib/demo.sh`; monitor and HTTP tests | [CLI evidence](verification/2026-11-04-cli-blue.md) and [latest deployment](verification/2026-11-17-deployment.md). Local file storage, not SQLite. |
| Authenticated local dashboard | `web/server.py`, `web/static/`; `tests/test_web.py` | [Dashboard checks](verification/2026-11-05-dashboard.md) and latest deployment. Four routes, private evidence, review, reports and settings; startup remains manual. |
| Background service and service-aware controls | `lib/monitor.sh`, `lib/service.py`, monitor unit; `tests/test_service.py`, HTTP tests | [November 7 boot/crash checks](verification/2026-11-07-systemd.md); [November 17 control checks](verification/2026-11-17-deployment.md). Existing Ubuntu policy denies unprivileged start/stop; the CLI/API show administrator commands without a process fallback. |
| Daily 60-day retention | CLI cleanup, `lib/notifications.jq`, cleanup service/timer; retention and Discord tests | Daily timer installed/enabled, trigger and successful cleanup observed. Pending notices preserve alert evidence. Expiration cases use disposable synthetic state; active blocks do not exist. |
| Optional Discord queue and real delivery | `lib/discord.sh`, `lib/discord_state.sh`, `lib/discord_http.py`, `lib/notifications.jq`; `tests/test_discord.py` | [Live Discord verification](verification/2026-11-17-discord.md): owner-approved test destination, first alert, review-reopening updates, grouped recovery and automatic sender. Four notices in three messages, zero pending at checkpoint. |

The deployed package passed all 66 Python tests on Ubuntu, plus shell/configuration checks and 19 monitor scenarios. During this documentation/PR audit, the Mac suite was rerun: 66 tests in 53.490 seconds, 65 passed and one Ubuntu-only unit-parser check skipped because systemd-analyze is absent. [Source evidence](verification/2026-11-17-source.md) records the checksum and the concurrency fix. Fake endpoint tests cover rate limits, ambiguous acceptance, chunking and concurrent enqueue; live Discord recovery used a controlled sender-only socket failure, not a genuine provider or VM-network outage.

Latest recorded VM state after Discord testing: blue `10.37.129.3`, red `10.37.129.4`; monitor PID 21431, running with available coverage; 136 stored events, three alerts. Monitor, daily cleanup and Discord sender timers were enabled. The HTTP dashboard was manually running at `http://10.37.129.3:8765`. Recheck addresses and health when resuming; these counts are dated observations.

## Simulated and planned

- Synthetic CLI/demo records are kept separate from live state. The archived browser simulation does not run the monitor or providers.
- VirusTotal integration and its guided simulated adapter are still planned. No reputation implementation or real blocking is established by existing sample artwork or text.
- SSH blocking remains last priority, with separate design review, explicit approval and tested console recovery before activation. No firewall enforcement is active.
- A terminal menu is optional later work. Discord browser configuration controls and provider-specific report details are not implemented.
- NAS/router syslog intake, SQLite and Compose belong to the broader future blueprint, not this college runtime.

## Remaining work

1. Capture the additional live detection scenarios above; observe Discord timer startup after a new reboot and a later unattended cleanup/catch-up run.
2. Resolve configuration-policy consistency and owner decisions on event format, rolling-window/replay semantics and durable recovery. Implementation choices do not close the discussion tickets.
3. Agree and implement CI gates and manual deployment evidence. CI means automated repository checks; no GitHub Actions workflow is implemented.
4. Decide whether optional VirusTotal work fits the milestone, extend provider/action reports when applicable, and rehearse the complete final demonstration.
5. Prepare the proposal/report, Gantt chart and presentation; record both students' real contributions. Faculty tool acceptance, final format, title-page dates, deadline and presentation duration remain unconfirmed.

Use the [checklist](../checklist.md) for acceptance gates, [backlog](build-backlog.md) for issue links, [runbook](runbook.md) for operating commands and [evaluation alignment](evaluation-alignment.md) for supplied academic requirements. The [verification index](verification/README.md) separates current evidence from earlier checkpoints.
