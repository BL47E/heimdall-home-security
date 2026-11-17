<div align="center">

# 🛡️ Heimdall

### Explainable SSH security monitoring with Linux shell scripts

A college project for Linux & Shell Programming (CSET-213).

**[Status](docs/status.md)** · **[Runbook](docs/runbook.md)** · **[Milestone plan](docs/college-milestone-plan.md)** · **[Build checklist](checklist.md)** · **[Evaluation requirements](docs/evaluation-alignment.md)** · **[Dashboard decision](docs/adr/0003-shell-monitor-with-local-dashboard.md)**

</div>

## Current status

**Heimdall CLI and dashboard are deployed on blue.** The November 17 update deploys source commit `ecaec12` into a fresh release, with service-aware controls and enabled daily cleanup. All 66 packaged Python tests passed on Ubuntu, plus the shell checks. Live CLI/API checks verified service identity, truthful stopped/running status, denied unprivileged control without a fallback, preserved records and successful cleanup. [Latest deployment evidence](docs/verification/2026-11-17-deployment.md)

The monitor is enabled at boot; earlier real reboot/crash checks are recorded in [service evidence](docs/verification/2026-11-07-systemd.md). The dashboard still starts manually. Start/stop requests from the unprivileged CLI/dashboard require administrator console commands on this installation; no broader control permissions were added. Discord is connected to the owner-approved test server: real threshold/reopening messages, controlled sender-failure recovery and automatic scheduled delivery were verified on November 17. [Discord evidence](docs/verification/2026-11-17-discord.md) VirusTotal and blocking remain planned.

The current milestone is a shell-first SSH monitor on Ubuntu ARM64, with shell commands and an owner-requested browser dashboard for status, evidence, review and configuration. [ADR 0003](docs/adr/0003-shell-monitor-with-local-dashboard.md) extends [ADR 0002](docs/adr/0002-shell-first-college-milestone.md): Python's standard library serves HTTP while shell/jq handles SSH rules and state. The broader NAS/router product in [the blueprint](HEIMDALL_BLUEPRINT.md) remains future direction. Faculty acceptance of the expanded dashboard technology remains unconfirmed.

See the [runbook](docs/runbook.md) for local startup, owner-token login, explicit local-IP access, offline sample processing and the systemd template and blue service instructions. Live records and synthetic sample state must remain separate.

Implemented: password success/failure parsing, per-IP rolling-window alerts, review/reopen history, restart-persistent records and replay deduplication, configurable rule limits/history, text reports, help/version, a labelled synthetic CLI demo and explicit retention cleanup. The browser supports token login, alert investigation, recent events, configuration and monitor controls. Live journal startup/resumption was checked on Ubuntu; boot startup and bounded crash recovery are verified on blue. Service-aware controls and daily cleanup are deployed and verified on blue. Discord queue/transport tests use a fake endpoint, with separate real delivery and scheduled-sender evidence on blue. TUI, VirusTotal and blocking remain planned.

The dashboard separates `/overview`, `/investigations`, `/activity` and `/settings`, with direct links and browser history. Its off-white workspace and black navigation use bundled JetBrains Mono fonts, so the interface loads without external font services.

Future panel changes follow the [control panel design guide](docs/control-panel-design.md), including the owner's preference for dark dotted graphics, terminal art and animation.

## Milestone behavior and remaining targets

- Watch SSH login records in the background, start at boot and attempt bounded recovery after a crash.
- Raise an explainable alert after **four failures from the same IP in a rolling five-minute window**, across usernames.
- Group a continuous burst until five minutes without another failure. Show the source, timeline, matched rule and recommendations.
- Summarize a successful login with matching preceding failures for the same user and IP when the data supports it.
- Offer direct shell commands and a local browser dashboard for status, alerts, investigation, review, validated configuration and report export. A terminal menu remains a later convenience.
- Preserve local alert history for **60 days** by default, including review history across restarts. Daily cleanup preserves pending delivery and required supporting evidence. Active-block retention is a future requirement because blocking is not implemented.
- Send optional Discord webhook messages. Queue failed deliveries and send a grouped list when Discord becomes reachable again.
- Optionally enrich eligible public IPs with VirusTotal context. Missing results mean unknown, and zero flags mean no flags found. Local processing works offline.
- Provide a guided demonstration that clearly labels prepared data and simulated actions.

**SSH blocking is the last implementation priority.** It is limited to the test VM and requires a reviewed design plus tested console recovery before activation. The intended block applies only to further SSH connections from the source IP; manual unblock requires confirmation. Reviewing an alert does not unblock it. Internet outages do not trigger quarantine.

## Test environment

One MacBook M4 Air with 16 GB RAM hosts two Ubuntu ARM64 virtual machines in Parallels Desktop:

1. **Heimdall VM:** SSH service, shell monitor, terminal management and local records.
2. **Test VM:** controlled SSH attempts over a private virtual network.

Separate outbound connectivity supports Discord and optional VirusTotal. Private VM addresses will not be sent to VirusTotal; the guided reputation demonstration uses labelled simulated results. Blue's observed SSH banner reports Ubuntu 26.04.1 LTS; the live input is `journalctl -u ssh` JSON. See the dated lab evidence and recheck the environment when resuming.

## College milestone stack

| Area | College milestone |
|---|---|
| Main language | Linux shell scripts |
| Supporting tools | Common Linux commands and jq; Python standard-library HTTPS transport |
| Management | Shell command interface and local browser dashboard |
| HTTP bridge | Python 3 standard library; no hosted dependencies |
| Normalization helper | Python standard library for canonical IPs and content fingerprints |
| Background operation | Linux service manager |
| Storage | Local files with restricted permissions and safe writes |
| Notifications | Optional Discord webhook |
| Reputation context | Optional VirusTotal API v3 with caching and limits |
| Deployment | Ubuntu ARM64 VMs |

Python is now a prerequisite for the browser bridge, following the owner's scope change. SQLite, Docker Compose and a Python rules engine remain outside this shell-first implementation.

## Continue the milestone

The core monitor/dashboard, services, retention and Discord are delivered. Use the [current status](docs/status.md), [checklist](checklist.md) and [GitHub backlog](docs/build-backlog.md) for remaining live evidence, open decisions and academic work. The original build sequence was:

1. VM setup, representative SSH logs and sample fixtures.
2. Live parsing, rolling-window detection and explanations.
3. Persistent investigations, CLI, browser dashboard and background service.
4. Discord delivery and outage recovery.
5. Optional VirusTotal context and readable reports.
6. Guided demo, evidence and rehearsal; real blocking only after its design and recovery gates pass.

The target is ten working days from project start, not a confirmed submission date. Collect report and test evidence throughout development. Reconcile the deadline, final-report format and title-page dates with the professor when available.

## Academic documents

- [Supplied 30-mark rubric](docs/reference/evaluation-rubric.docx)
- [Supplied idea template](docs/reference/idea-template.docx)
- [Criteria, formatting and evidence mapping](docs/evaluation-alignment.md)

The idea template allows at most three realistic quantified objectives and requires a Gantt chart. The rubric awards 6 marks each for analysis, design, implementation, report and communication. Keep the final design consistent with working modules and record both students' actual contributions.

Whether the idea template also governs the final report, the submission date, presentation duration and correct title-page dates remain open for faculty confirmation.

## Earlier reference artifacts

[Historical references](docs/archive/README.md) include the earlier browser simulation, proposal artifacts and supplementary rubric guide. They predate the current milestone and may describe broader or older behavior; they do not establish implemented features or replace the supplied rubric. The current plan and evaluation mapping take precedence. The [documentation index](docs/index.html) links current documents and the archive.

The browser simulation can be opened directly from disk; it does not run the Linux monitor or send real notifications.

## Academic context and authors

- Anirdeep Das — S25CSEU1973
- Harshit Gupta — S25CSEU1971
- Faculty guide: Vimal Kumar
- Course: Linux & Shell Programming (CSET-213)

Use the [glossary](GLOSSARY.md) for project terminology and [AGENTS.md](AGENTS.md) for contribution guidance. Work is tracked in this repository's GitHub Issues.
