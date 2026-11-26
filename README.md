<div align="center">

# 🛡️ Heimdall

### Explainable SSH security monitoring with Linux shell scripts

A college project for Linux & Shell Programming (CSET-213).

**[Status](docs/status.md)** · **[Runbook](docs/runbook.md)** · **[Milestone plan](docs/college-milestone-plan.md)** · **[Build checklist](checklist.md)** · **[Evaluation requirements](docs/evaluation-alignment.md)** · **[Dashboard decision](docs/adr/0003-shell-monitor-with-local-dashboard.md)**

</div>

## What Heimdall does

Heimdall reads supported SSH password events from the Ubuntu system journal and groups repeated failures into explainable local alerts. By default, four failures from one IP within five minutes trigger an alert. The owner can investigate evidence, record a review, and export a text report through the terminal or authenticated local dashboard.

- **Implemented:** local SSH monitoring, persistent investigations, terminal and browser interfaces, service controls, scheduled retention, and optional Discord notifications.
- **Simulated:** the isolated demo and VirusTotal example use labelled sample data. Manual VirusTotal lookups are implemented, but a live lookup has not been verified on the lab installation.
- **Planned:** SSH blocking, general Linux deployment and private remote dashboard access. Blocking requires a reviewed design and tested console recovery.

The latest recorded lab deployment is from November 25. See [implementation status](docs/status.md) for evidence and limitations.

## Try the offline demo

From the repository directory, with Bash, `jq` and Python 3 installed, run:

```sh
./bin/heimdall demo
```

The demo uses separate synthetic state and needs no credentials or internet connection. For live Ubuntu monitoring, installation, dashboard login and service management, follow the [runbook](docs/runbook.md).

## Checks and deployment

Run the local checks from the repository root:

```sh
bash tests/test_monitor.sh
python3 -m unittest discover -s tests
```

GitHub Actions is enabled for the repository, but no CI workflow is configured yet. CI gates and evidence for manual deployment are being decided in [issue #12](https://github.com/BL47E/heimdall-home-security/issues/12). The [runbook](docs/runbook.md#packaging-a-build-for-the-vm) describes packaging and manual deployment.

## Home deployment target

Heimdall is intended to run as a background service on a Linux system, with monitoring and records kept on that system. For quick setup or settings changes, open the terminal user interface (TUI) directly on the Linux system with `heimdall`. For access away from home, the owner will configure Tailscale on that system and open the same dashboard in a browser from an authorized phone or laptop. This [private remote access](https://github.com/BL47E/heimdall-home-security/issues/16) is planned; see the [proposed home deployment design](docs/home-deployment-design.md).

The Ubuntu VMs are the current development and test environment. See the [blueprint](HEIMDALL_BLUEPRINT.md) for the home deployment direction.

## Current status

The shell monitor, dashboard, terminal app, service controls, daily cleanup and Discord delivery are deployed on blue. The November 25 release passed 82 tests on Ubuntu and the service switch preserved live state. The dashboard starts manually; unprivileged start/stop requests require administrator commands. VirusTotal supports manual lookups and labelled simulation; a live lookup remains unverified. SSH blocking is planned behind a separate design and recovery gate.

See the [status matrix](docs/status.md) for implementation and evidence, the [runbook](docs/runbook.md) for operation, and the [verification index](docs/verification/README.md) for dated results. Faculty acceptance of the Python dashboard bridge remains unconfirmed. The earlier browser simulation is not the Linux monitor.

## Terminal onboarding

From a retained release directory on Linux, run `bash scripts/install-cli.sh` once to make `heimdall` available by name for your Bash account. Open a new terminal and run `heimdall --help` for the command list or `heimdall --console` to open the keyboard-driven terminal app.

First launch checks prerequisites and SSH journal access, guides you through local state setup, and saves completion when you confirm. It adopts existing records unchanged. Later launches open Overview, where you can check the monitor, review alerts and open **Rules** to edit the failure threshold, time window or retention. Type `/exit` to leave. [Terminal panel controls](docs/runbook.md#terminal-panel-and-onboarding)

## Milestone behavior and remaining targets

Heimdall watches SSH login records, explains a configurable alert when four failures from one IP occur within five minutes, and retains local investigation history. Optional Discord delivery and VirusTotal reputation add context without making local monitoring depend on internet access. The guided demo labels synthetic data and actions.

The [milestone plan](docs/college-milestone-plan.md) defines behavior and safety boundaries; the [checklist](checklist.md) tracks acceptance and remaining work. The broader home-system design in the [blueprint](HEIMDALL_BLUEPRINT.md) remains planned.

## Test environment

One MacBook M4 Air with 16 GB RAM hosts two Ubuntu ARM64 virtual machines in Parallels Desktop:

1. **Heimdall VM:** SSH service, shell monitor, terminal management and local records.
2. **Test VM:** controlled SSH attempts over a private virtual network.

Separate outbound connectivity supports Discord and optional VirusTotal. Private VM addresses will not be sent to VirusTotal; the guided reputation demonstration uses labelled simulated results. Blue's observed SSH banner reports Ubuntu 26.04.1 LTS; the live input is `journalctl -u ssh` JSON. See the dated lab evidence and recheck the environment when resuming.

## Continue the milestone

The milestone uses shell scripts, jq, local files and the Python standard library on Ubuntu ARM64. The [backlog](docs/build-backlog.md) links GitHub Issues; the [checklist](checklist.md) tracks verification, academic work and open decisions. Ten working days is a planning target, not a confirmed submission date.

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
