# Implementation status

The latest recorded VM checkpoint is November 17, with a fresh SSH observation on November 25 after the owner's laptop reset (renamed VMs and accounts; see the checklist's resume section for current names and addresses). Application version is `0.1.0`. At the November 17 checkpoint, blue ran runtime source commit `ecaec12`; the account was later renamed, moving the release tree to `/home/blazeblue/heimdall`. Source-only work is identified below.

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
| Optional VirusTotal IP reputation | `bin/heimdall`, `lib/virustotal.py`, `lib/demo.sh`; `tests/test_virustotal.py`, HTTP tests | Manual lookup, labelled simulation, report and dashboard context are implemented in source. Tests use a mocked HTTPS response. A real provider lookup and deployment on blue remain unverified. |

The deployed package passed all 66 Python tests on Ubuntu, plus shell/configuration checks and 19 monitor scenarios. During this documentation/PR audit, the Mac suite was rerun: 66 tests in 53.490 seconds, 65 passed and one Ubuntu-only unit-parser check skipped because systemd-analyze is absent. [Source evidence](verification/2026-11-17-source.md) records the checksum and the concurrency fix. Fake endpoint tests cover rate limits, ambiguous acceptance, chunking and concurrent enqueue; live Discord recovery used a controlled sender-only socket failure, not a genuine provider or VM-network outage.

Latest recorded VM state after Discord testing (November 17): blue `10.37.129.3`, red `10.37.129.4`; monitor PID 21431, running with available coverage; 136 stored events, three alerts. Monitor, daily cleanup and Discord sender timers were enabled. The HTTP dashboard was manually running at `http://10.37.129.3:8765`. These counts are dated observations from before the reset.

November 25 SSH observation after the reset: blue (user `blazeblue`, Host-Only `10.37.129.8`) has releases `0.1.0-ecaec12`, `0.1.0-vt` and `0.1.0-342daa1`. The updated CLI release passed all 82 tests on the VM ([release evidence](verification/2026-11-25-release-verification.md)); after the owner-requested switch the monitor/cleanup/Discord units and launcher run `0.1.0-342daa1` with the control identity verified and live state preserved ([switch evidence](verification/2026-11-25-service-switch.md)). The monitor is enabled, active and reading `journalctl -u ssh` with available coverage; the cleanup and Discord timers are active; latest observed counts were 59 events and zero alerts. Red (user `blazered`, Host-Only `10.37.129.9`) has no Heimdall deployment, as intended for the test source. The dashboard was not rechecked from the Mac this session.

## Simulated and planned

- Synthetic CLI/demo records are kept separate from live state. The archived browser simulation does not run the monitor or providers.
- The guided VirusTotal simulation uses a prepared vendor count in separate fixture state.
- SSH blocking remains last priority, with separate design review, explicit approval and tested console recovery before activation. No firewall enforcement is active.
- The terminal app is implemented in source: bare `heimdall` in an interactive terminal runs first-use onboarding (completion persisted per state directory, existing state adopted unchanged) and then an Overview workspace with monitor control, investigations and review/reopen, recent events, rules, providers and the demo. Leaving requires the exact `/exit` command. Deployment on blue remains pending; its pseudo-terminal tests run on macOS and Ubuntu. Discord browser configuration controls remain planned.
- NAS/router syslog intake, SQLite and Compose belong to the broader future blueprint, not this college runtime.

## Remaining work

1. Capture the additional live detection scenarios above; observe Discord timer startup after a new reboot and a later unattended cleanup/catch-up run.
2. Resolve configuration-policy consistency and owner decisions on event format, rolling-window/replay semantics and durable recovery. Implementation choices do not close the discussion tickets.
3. Agree and implement CI gates and manual deployment evidence. CI means automated repository checks; no GitHub Actions workflow is implemented.
4. Rehearse the complete final demonstration with the labelled VirusTotal example. Verify a live public-IP lookup separately if needed. Action outcomes in reports remain tied to future enforcement.
5. Prepare the proposal/report, Gantt chart and presentation; record both students' real contributions. Faculty tool acceptance, final format, title-page dates, deadline and presentation duration remain unconfirmed.

Use the [checklist](../checklist.md) for acceptance gates, [backlog](build-backlog.md) for issue links, [runbook](runbook.md) for operating commands and [evaluation alignment](evaluation-alignment.md) for supplied academic requirements. The [verification index](verification/README.md) separates current evidence from earlier checkpoints.
