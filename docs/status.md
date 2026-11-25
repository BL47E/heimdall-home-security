# Implementation status

The latest recorded VM checkpoint is November 25, after the owner’s laptop reset and the service switch to release `0.1.0-342daa1`. Application version is `0.1.0`; see the [lab resume notes](../checklist.md#resume-the-lab) for current names and addresses. Earlier checkpoints and their limitations remain linked below.

## Implemented and verified

| Capability | Code and tests | Evidence and limits |
| --- | --- | --- |
| Password-result parsing and four failures per IP in 300 seconds | `lib/parse.jq`, `lib/normalize.py`, `lib/rules.jq`; `tests/test_monitor.py` | [CLI verification](verification/2026-11-04-cli-blue.md), [red-to-blue checks](verification/2026-11-07-red-blue-recovery.md) and [Discord threshold test](verification/2026-11-17-discord.md). Only explicit password results count; supporting messages remain evidence. |
| Rolling windows, source separation, missing fields, replay and success correlation | Same parser/rules and monitor scenario tests | Synthetic boundary/multiple-IP tests and sanitized real exports pass. Additional real expired-window, concurrent-source and success-correlation demonstrations remain open. |
| Persistent alerts, review/reopen history, configuration, text reports and isolated demo | `bin/heimdall`, `lib/lock.py`, `lib/demo.sh`; monitor and HTTP tests | [CLI evidence](verification/2026-11-04-cli-blue.md) and [November 17 deployment](verification/2026-11-17-deployment.md). Local file storage, not SQLite. |
| Authenticated local dashboard | `web/server.py`, `web/static/`; `tests/test_web.py` | [Dashboard checks](verification/2026-11-05-dashboard.md) and [November 17 HTTP checks](verification/2026-11-17-deployment.md). Four routes, private evidence, review, reports and settings; startup remains manual. |
| Local terminal app | `bin/heimdall`, `lib/tui.py`; `tests/test_tui.py` | Blue's console demonstration verified first-use onboarding, adoption of existing state and live monitor status. The guided Rules editor is verified locally with temporary state. [Lab diary](../diary.md) |
| Background service and service-aware controls | `lib/monitor.sh`, `lib/service.py`, monitor unit; `tests/test_service.py`, HTTP tests | [November 7 boot/crash checks](verification/2026-11-07-systemd.md); [November 17 control checks](verification/2026-11-17-deployment.md). Existing Ubuntu policy denies unprivileged start/stop; the CLI/API show administrator commands without a process fallback. |
| Daily 60-day retention | CLI cleanup, `lib/notifications.jq`, cleanup service/timer; retention and Discord tests | Daily timer installed/enabled, trigger and successful cleanup observed. Pending notices preserve alert evidence. Expiration cases use disposable synthetic state; active blocks do not exist. |
| Optional Discord queue and real delivery | `lib/discord.sh`, `lib/discord_state.sh`, `lib/discord_http.py`, `lib/notifications.jq`; `tests/test_discord.py` | [Live Discord verification](verification/2026-11-17-discord.md): owner-approved test destination, first alert, review-reopening updates, grouped recovery and automatic sender. Four notices in three messages, zero pending at checkpoint. |
| Optional VirusTotal IP reputation | `bin/heimdall`, `lib/virustotal.py`, `lib/demo.sh`; `tests/test_virustotal.py`, HTTP tests | Manual lookup, labelled simulation, report and dashboard context are implemented in source. Tests use a mocked HTTPS response. The release containing it is deployed on blue; a real provider lookup remains unverified. |

Blue passed 82 packaged tests on November 25. The monitor, cleanup and Discord units and the launcher were switched to release `0.1.0-342daa1`. The live terminal demonstration subsequently showed the monitor running with 80 stored events and zero alerts. A fresh browser check from the Mac remains open. [Release checks](verification/2026-11-25-release-verification.md) · [Service switch](verification/2026-11-25-service-switch.md) · [Console demonstration](../diary.md)

## Simulated and planned

- Synthetic CLI/demo records are kept separate from live state. The archived browser simulation does not run the monitor or providers.
- The guided VirusTotal simulation uses a prepared vendor count in separate fixture state.
- SSH blocking remains last priority, with separate design review, explicit approval and tested console recovery before activation. No firewall enforcement is active.
- Discord browser configuration controls remain planned.
- NAS/router syslog intake, SQLite and Compose belong to the broader future blueprint, not this college runtime.

## Remaining work

1. Capture the additional live detection scenarios above; observe Discord timer startup after a new reboot and a later unattended cleanup/catch-up run.
2. Resolve configuration-policy consistency and owner decisions on event format, rolling-window/replay semantics and durable recovery. Implementation choices do not close the discussion tickets.
3. Agree and implement CI gates and manual deployment evidence. CI means automated repository checks; no GitHub Actions workflow is implemented.
4. Rehearse the complete final demonstration with the labelled VirusTotal example. Verify a live public-IP lookup separately if needed. Action outcomes in reports remain tied to future enforcement.
5. Prepare the proposal/report, Gantt chart and presentation; record both students' real contributions. Faculty tool acceptance, final format, title-page dates, deadline and presentation duration remain unconfirmed.

Use the [checklist](../checklist.md) for acceptance gates, [backlog](build-backlog.md) for issue links, [runbook](runbook.md) for operating commands and [evaluation alignment](evaluation-alignment.md) for supplied academic requirements. The [verification index](verification/README.md) separates current evidence from earlier checkpoints.
