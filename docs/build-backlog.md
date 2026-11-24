# Build backlog

GitHub Issues are the implementation tracker. This index links the initial work packages; issue comments hold current ownership, status and verification evidence. Ready-for-human items cover lab/team work; dependent implementation packages begin as needs-triage until their inputs are settled.

## November 17 delivery checkpoint

The shell monitor/dashboard, service-aware controls, daily cleanup and real scheduled Discord delivery are implemented and deployed. Use the [status matrix](status.md) for code/test/evidence mapping and the [verification index](verification/README.md) for dated results. GitHub issues remain open until their full acceptance scope and owner decisions are reconciled; an open issue does not by itself mean every component is unimplemented.

| Work package | Delivered evidence | Still open |
| --- | --- | --- |
| Lab and fixtures (#1) | Two ARM64 VMs, SSH journal/exported examples and controlled red-to-blue input | Additional live window/concurrent-source/success scenarios and separate red outbound reachability evidence |
| Parser/rules (#2) | Shell/jq rules, synthetic boundary tests and real threshold/reopening checks | Owner sign-off of event/time/replay contracts and remaining live scenarios |
| History/service/dashboard (#3, #13) | Durable history, reports, authenticated panel, real boot/crash recovery, service controls and daily cleanup | Terminal panel deployment, configuration-policy follow-up, later unattended retention evidence; browser lifecycle still requires administrator commands on blue |
| Discord (#4) | [Real delivery, controlled failure recovery and scheduled sender](verification/2026-11-17-discord.md) | Observe sender-timer startup after a new reboot; full final-demo rehearsal |
| Reputation/reports (#5) | Manual VirusTotal lookup and offline simulation in source, with reputation in investigations and text reports | Live provider check and lab deployment if needed. Action report details depend on enforcement. |
| Guided demo/response (#6) | Isolated labelled CLI demo | Full rehearsal; optional blocking design/approval/console-recovery gates |
| College deliverables (#7) | Rubric/template mapping and dated evidence | Proposal/report, Gantt chart, balanced student contribution records, presentation and faculty answers |

The owner-requested shell monitor/dashboard extension is tracked in [issue 13](https://github.com/BL47E/heimdall-home-security/issues/13). Earlier issue comments are historical checkpoints; the linked evidence and checklist describe subsequent work.

Design decisions are tracked separately in [Chart the shell-first college milestone and CI decisions](https://github.com/BL47E/heimdall-home-security/issues/8). Query its native child issues for open decisions; see [Wayfinding operations](agents/issue-tracker.md#wayfinding-operations). The [development diary](../diary.md) records dated observations and the [checklist](../checklist.md) distinguishes completed preparation from planned runtime behavior.

- [Prepare the two-VM Ubuntu ARM64 lab and capture SSH log fixtures](https://github.com/BL47E/heimdall-home-security/issues/1) — Day 1.
- [Implement shell SSH parsing and rolling-window alerts](https://github.com/BL47E/heimdall-home-security/issues/2) — Days 2–3.
- [Add persistent investigations, CLI/TUI and background service management](https://github.com/BL47E/heimdall-home-security/issues/3) — Days 4–5.
- [Add Discord webhook alerts and grouped outage recovery](https://github.com/BL47E/heimdall-home-security/issues/4) — Day 6.
- [Add optional VirusTotal reputation context and investigation exports](https://github.com/BL47E/heimdall-home-security/issues/5) — Day 7.
- [Build the guided demonstration and review optional SSH enforcement](https://github.com/BL47E/heimdall-home-security/issues/6) — Days 8–9.
- [Prepare rubric evidence, proposal and presentation with both team members](https://github.com/BL47E/heimdall-home-security/issues/7) — Throughout; finalize Day 10.

See [the checklist](../checklist.md) for the ordered acceptance gates and [the milestone plan](college-milestone-plan.md) for scope. Keep real blocking last and preserve final-day rehearsal.
