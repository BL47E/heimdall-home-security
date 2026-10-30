# Heimdall

**A clear, local security overview for a home server or NAS, without running a full SOC stack.**

Heimdall is a planned, lightweight home security assistant. It will collect security events from a NAS, router, and selected services, explain which events deserve attention, and keep a local history of what happened. Its first release is intended for people who want actionable context without managing a full security operations platform.

## Why Heimdall

NAS products already provide useful security checks for their own systems. Heimdall is designed to add a small cross-device view: receive events over syslog, group related activity, explain the matching rule and severity, and optionally enrich selected indicators. Local rules and history should work without internet access. External lookups will be opt-in.

Heimdall complements tools such as Synology Security Advisor, TrueNAS auditing, and CrowdSec. It is not intended to replace endpoint detection, a SIEM, an IDS, or the NAS vendor's security controls.

## Version one

The initial scope is deliberately small:

- Receive syslog events from a home NAS or router.
- Detect a few understandable patterns, beginning with repeated failed logins and suspicious activity around authentication.
- Group repeated events, explain why an alert was raised, and assign a transparent severity.
- Keep alerts and an enrichment cache in a local SQLite database.
- Send optional notifications through a configurable provider.
- Run in mock/offline mode without API keys or internet access.
- Recommend next steps; require the owner to approve changes to devices or network controls.

The first release will not automatically block addresses, delete files, or change NAS configuration.

## Planned stack

- Python application, with Bash limited to a small launcher or setup helper.
- Docker Compose deployment, packaged for the target CPU architectures.
- SQLite for local alert history, deduplication, and enrichment cache.
- Syslog as the first input path; additional source adapters can follow.
- A small server-rendered web interface and API.
- Optional notification and threat-intelligence providers behind replaceable interfaces.

These are design choices, not implemented components yet.

## Project status

This repository currently contains the product blueprint, interactive documentation, proposal material, and evaluation guide. The interactive console and IOC defanger are browser simulations. Heimdall does not yet receive live logs, query threat-intelligence services, persist alerts, or send notifications.

## Start here

- [Product and technical blueprint](HEIMDALL_BLUEPRINT.md)
- [Interactive project guide](docs/index.html)
- [Evaluation guide](docs/Heimdall_Rubric_Full_Marks_Guide.html)
- [Architecture decision record](docs/adr/0001-home-first-local-first.md)
- [Glossary](GLOSSARY.md)

Open `docs/index.html` directly in a browser to explore the simulated workflow. It does not need a server.

## Roadmap

1. Define the alert contract, supported syslog format, and safe configuration defaults.
2. Implement syslog ingestion, normalization, and a small set of local rules.
3. Add event grouping, explainable severity, SQLite history, and offline demonstrations.
4. Add notifications and optional, rate-limited indicator enrichment.
5. Package a low-maintenance Docker Compose install and document supported NAS targets.

See the [full blueprint](HEIMDALL_BLUEPRINT.md) for boundaries, architecture, and acceptance criteria.
