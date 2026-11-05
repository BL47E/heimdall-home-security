<div align="center">

# 🛡️ Heimdall

### Explainable SSH security monitoring with Linux shell scripts

A college project for Linux & Shell Programming (CSET-213).

**[Runbook](docs/runbook.md)** · **[Milestone plan](docs/college-milestone-plan.md)** · **[Build checklist](checklist.md)** · **[Evaluation requirements](docs/evaluation-alignment.md)** · **[Dashboard decision](docs/adr/0003-shell-monitor-with-local-dashboard.md)**

</div>

## Current status

**CLI version 0.1.0 is implemented and has been deployed and tested on blue.** The current runtime lives in `bin/`, `lib/` and `web/`. [VM verification](docs/verification/2026-11-04-cli-blue.md) records real SSH failures, fourth-failure alerting, review reopening and stop/start persistence. The dashboard passes local browser and HTTP-to-shell checks; its VM deployment and boot/systemd recovery remain separate work. Discord delivery, VirusTotal integration and real blocking remain planned.

The current milestone is a shell-first SSH monitor on Ubuntu ARM64, with shell commands and an owner-requested browser dashboard for status, evidence, review and configuration. [ADR 0003](docs/adr/0003-shell-monitor-with-local-dashboard.md) extends [ADR 0002](docs/adr/0002-shell-first-college-milestone.md): Python's standard library serves HTTP while shell/jq handles SSH rules and state. The broader NAS/router product in [the blueprint](HEIMDALL_BLUEPRINT.md) remains future direction. Faculty acceptance of the expanded dashboard technology remains unconfirmed.

See the [runbook](docs/runbook.md) for local startup, owner-token login, explicit local-IP access, offline sample processing and the uninstalled systemd template. Live records and synthetic sample state must remain separate.

Implemented: password success/failure parsing, per-IP rolling-window alerts, review/reopen history, restart-persistent records and replay deduplication, configurable rule limits/history, text reports, help/version, a labelled synthetic CLI demo and explicit retention cleanup. The browser supports token login, alert investigation, recent events, configuration and monitor controls. Live journal startup/resumption was checked on Ubuntu; the uninstalled service template, daily scheduled retention, TUI and provider integrations remain planned or unverified.

The dashboard separates `/overview`, `/investigations`, `/activity` and `/settings`, with direct links and browser history. Its off-white workspace and black navigation use bundled JetBrains Mono fonts, so the interface loads without external font services.

## What the first version is planned to do

- Watch SSH login records in the background, start at boot and attempt bounded recovery after a crash.
- Raise an explainable alert after **four failures from the same IP in a rolling five-minute window**, across usernames.
- Group a continuous burst until five minutes without another failure. Show the source, timeline, matched rule and recommendations.
- Summarize a successful login with matching preceding failures for the same user and IP when the data supports it.
- Offer direct shell commands and a local browser dashboard for status, alerts, investigation, review, validated configuration and report export. A terminal menu remains a later convenience.
- Preserve local alert history for **60 days** by default, including review history across restarts. Daily cleanup preserves pending delivery and active block records.
- Send optional Discord webhook messages. Queue failed deliveries and send a grouped list when Discord becomes reachable again.
- Optionally enrich eligible public IPs with VirusTotal context. Missing results mean unknown, and zero flags mean no flags found. Local processing works offline.
- Provide a guided demonstration that clearly labels prepared data and simulated actions.

**SSH blocking is the last implementation priority.** It is limited to the test VM and requires a reviewed design plus tested console recovery before activation. The intended block applies only to further SSH connections from the source IP; manual unblock requires confirmation. Reviewing an alert does not unblock it. Internet outages do not trigger quarantine.

## Test environment

One MacBook M4 Air with 16 GB RAM will host two Ubuntu ARM64 virtual machines:

1. **Heimdall VM:** SSH service, shell monitor, terminal management and local records.
2. **Test VM:** controlled SSH attempts over a private virtual network.

Separate outbound connectivity supports Discord and optional VirusTotal. Private VM addresses will not be sent to VirusTotal; the guided reputation demonstration uses labelled simulated results. Choose the VM application, Ubuntu release and actual SSH log input during setup.

## Planned stack

| Area | College milestone |
|---|---|
| Main language | Linux shell scripts |
| Supporting tools | Common Linux commands, curl and jq |
| Management | Shell command interface and local browser dashboard |
| HTTP bridge | Python 3 standard library; no hosted dependencies |
| Normalization helper | Python standard library for canonical IPs and content fingerprints |
| Background operation | Linux service manager |
| Storage | Local files with restricted permissions and safe writes |
| Notifications | Optional Discord webhook |
| Reputation context | Optional VirusTotal API v3 with caching and limits |
| Deployment | Ubuntu ARM64 VMs |

Python is now a prerequisite for the browser bridge, following the owner's scope change. SQLite, Docker Compose and a Python rules engine remain outside this shell-first implementation.

## Start building

Follow [checklist.md](checklist.md) and the [GitHub build backlog](docs/build-backlog.md). Build in this order:

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

[Browser simulation](docs/index.html), [HTML guide](HEIMDALL_BLUEPRINT.html), earlier filled idea documents and the full-marks guide under `docs/` predate the current milestone. They are reference material and may describe broader or older behavior; they do not establish implemented features or replace the supplied rubric. The current plan and evaluation mapping take precedence.

The browser simulation can be opened directly from disk; it does not run the Linux monitor or send real notifications.

## Academic context and authors

- Anirdeep Das — S25CSEU1973
- Harshit Gupta — S25CSEU1971
- Faculty guide: Vimal Kumar
- Course: Linux & Shell Programming (CSET-213)

Use the [glossary](GLOSSARY.md) for project terminology and [AGENTS.md](AGENTS.md) for contribution guidance. Work is tracked in this repository's GitHub Issues.
