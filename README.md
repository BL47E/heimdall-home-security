<div align="center">

# 🛡️ Heimdall

### Explainable SSH security monitoring with Linux shell scripts

A college project for Linux & Shell Programming (CSET-213).

**[Milestone plan](docs/college-milestone-plan.md)** · **[Build checklist](checklist.md)** · **[Evaluation requirements](docs/evaluation-alignment.md)** · **[Architecture decision](docs/adr/0002-shell-first-college-milestone.md)**

</div>

## Current status

**Planning complete enough to begin development; the live software is not implemented yet.** This repository contains the agreed plan, architecture decisions, supplied academic documents and earlier browser simulations. There is no installed `heimdall` command or working monitoring service yet.

The current milestone is a shell-first, terminal-based SSH monitor on Ubuntu ARM64. The broader NAS/router product in [the blueprint](HEIMDALL_BLUEPRINT.md) remains future direction. [ADR 0002](docs/adr/0002-shell-first-college-milestone.md) records this scope decision.

## What the first version is planned to do

- Watch SSH login records in the background, start at boot and attempt bounded recovery after a crash.
- Raise an explainable alert after **four failures from the same IP in a rolling five-minute window**, across usernames.
- Group a continuous burst until five minutes without another failure. Show the source, timeline, matched rule and recommendations.
- Summarize a successful login with matching preceding failures for the same user and IP when the data supports it.
- Offer a terminal menu and direct commands for status, alerts, investigation, review and report export.
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
| Management | Terminal menu and command interface |
| Background operation | Linux service manager |
| Storage | Local files with restricted permissions and safe writes |
| Notifications | Optional Discord webhook |
| Reputation context | Optional VirusTotal API v3 with caching and limits |
| Deployment | Ubuntu ARM64 VMs |

Python, SQLite, a web dashboard and Docker Compose belong to the broader future architecture, not prerequisites for this milestone.

## Start building

Follow [checklist.md](checklist.md) and the [GitHub build backlog](docs/build-backlog.md). Build in this order:

1. VM setup, representative SSH logs and sample fixtures.
2. Live parsing, rolling-window detection and explanations.
3. Persistent investigations, CLI, TUI and background service.
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
