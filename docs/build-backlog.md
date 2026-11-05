# Build backlog

GitHub Issues are the implementation tracker. This index links the initial work packages; issue comments hold current ownership, status and verification evidence. Ready-for-human items cover lab/team work; dependent implementation packages begin as needs-triage until their inputs are settled.

The owner-requested shell monitor and browser dashboard extension is tracked in [implementation issue 13](https://github.com/BL47E/heimdall-home-security/issues/13). Its [local verification checkpoint](https://github.com/BL47E/heimdall-home-security/issues/13#issuecomment-6633729764) covers synthetic monitor tests and actual HTTP-to-shell integration; live Ubuntu/service evidence remains outstanding.

Design decisions are tracked separately in [Chart the shell-first college milestone and CI decisions](https://github.com/BL47E/heimdall-home-security/issues/8). Query its native child issues for open decisions; see [Wayfinding operations](agents/issue-tracker.md#wayfinding-operations). The [development diary](../diary.md) records dated observations and the [checklist](../checklist.md) distinguishes completed preparation from planned runtime behavior.

- [Prepare the two-VM Ubuntu ARM64 lab and capture SSH log fixtures](https://github.com/BL47E/heimdall-home-security/issues/1) — Day 1.
- [Implement shell SSH parsing and rolling-window alerts](https://github.com/BL47E/heimdall-home-security/issues/2) — Days 2–3.
- [Add persistent investigations, CLI/TUI and background service management](https://github.com/BL47E/heimdall-home-security/issues/3) — Days 4–5.
- [Add Discord webhook alerts and grouped outage recovery](https://github.com/BL47E/heimdall-home-security/issues/4) — Day 6.
- [Add optional VirusTotal reputation context and investigation exports](https://github.com/BL47E/heimdall-home-security/issues/5) — Day 7.
- [Build the guided demonstration and review optional SSH enforcement](https://github.com/BL47E/heimdall-home-security/issues/6) — Days 8–9.
- [Prepare rubric evidence, proposal and presentation with both team members](https://github.com/BL47E/heimdall-home-security/issues/7) — Throughout; finalize Day 10.

See [the checklist](../checklist.md) for the ordered acceptance gates and [the milestone plan](college-milestone-plan.md) for scope. Keep real blocking last and preserve final-day rehearsal.
