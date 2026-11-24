# Heimdall build checklist

Current scope: [college milestone](docs/college-milestone-plan.md), [ADR 0002](docs/adr/0002-shell-first-college-milestone.md), the owner's [dashboard extension in ADR 0003](docs/adr/0003-shell-monitor-with-local-dashboard.md) and [evaluation alignment](docs/evaluation-alignment.md). The broader blueprint remains future scope where the milestone overrides it.

Status: CLI and dashboard 0.1.0 are deployed on blue. Live status, preserved alert history, owner authentication and Host-Only access were verified on 2026-11-05; see [the diary](diary.md) and [earlier CLI verification](docs/verification/2026-11-04-cli-blue.md). Real red-to-blue threshold alerting, review reopening and manual console recovery after a monitor crash were verified on 2026-11-07 ([evidence](docs/verification/2026-11-07-red-blue-recovery.md)). Boot startup and bounded automatic systemd crash recovery were verified on blue ([service evidence](docs/verification/2026-11-07-systemd.md)). GitHub Issues are the implementation tracker; see the [build backlog](docs/build-backlog.md). Track actual contribution by both students.

Latest recorded checkpoint, November 17 after Discord testing: 136 events, three alerts, four delivered notices in three Discord messages and zero pending notices. Monitoring stayed healthy. See [current status](docs/status.md) and [Discord evidence](docs/verification/2026-11-17-discord.md).

Progress reconciled on 2026-11-17 against the [source checkpoint](docs/verification/2026-11-17-source.md), [live deployment evidence](docs/verification/2026-11-17-deployment.md) and [Discord verification](docs/verification/2026-11-17-discord.md). Planning checkboxes record agreed choices; implementation checkboxes identify their evidence. GitHub decision tickets remain open until owner answers resolve them.

## Resume the lab

Lab identity after the owner's laptop reset (observed over SSH on November 25): the VMs are now UbuntuBlue (hostname `blueblue`, user `blazeblue`) and UbuntuRed (hostname `blazered`, user `blazered`). Blue is at `10.211.55.9` (Shared) and `10.37.129.8` (Host-Only); red at `10.211.55.10` (Shared) and `10.37.129.9` (Host-Only). The pre-reset addresses in older diary/evidence records no longer respond; historical entries keep their original values.
- Blue's Heimdall survived the account rename: releases `0.1.0-ecaec12`, `0.1.0-vt` and the November 25 `0.1.0-342daa1` (updated CLI: VirusTotal, terminal app, monitor-start fix; all 82 tests pass on the VM) exist under `/home/blazeblue/heimdall`. `heimdall-monitor.service` is enabled and active on the older `0.1.0-ecaec12` release, and the cleanup and Discord sender timers are active. `heimdall status` from the installed launcher reported the monitor running from `journalctl -u ssh` with no last error. Switching the service/launcher to the new release awaits an owner decision and an administrator console step.
- Service-aware CLI/browser controls are deployed. Existing Ubuntu policy denies unprivileged start/stop: the interface shows administrator console instructions and never starts a separate reader. Use `sudo systemctl start|stop|restart heimdall-monitor` in blue's terminal.
- The daily cleanup timer is installed, has triggered, and the cleanup service completed successfully. State is backed up privately on blue. Blocking remains unimplemented and its recovery gate remains open.
- Per the owner's request on November 25, both VMs disable idle screen locking (`idle-delay 0`) and idle suspend; the screen asks for a password only at explicit logout/login or a manual lock.

## Panel design and repository cleanup — completed locally and saved

- [x] Create [the control panel design guide](docs/control-panel-design.md), link it from `AGENTS.md`/README and retain the owner's reference image. Use black/off-white, local JetBrains Mono, separate pages, and the stated preference for dark dotted graphics, TUI art and animations.
- [x] Archive historical guides/proposal artifacts in [docs/archive](docs/archive/README.md); preserve faculty originals, current plans, ADRs and evidence.
- [x] Verify duplicate hashes before removing two identical template copies and the near-identical second HTML simulation; retain a small documentation index and repair links.
- [x] Format runtime source and relevant tests without a behavior/design refactor or new runtime dependencies; preserve syntax structure, CSS order, HTML/art and source permissions.
- [x] Pass all 28 runtime tests, verify the 82 then-current local documentation links and build a package in temporary output; preserve the earlier deployed release archive/checksum. [Issue 14](https://github.com/BL47E/heimdall-home-security/issues/14) is closed.
- [ ] Address configuration-policy consistency as a separate follow-up; browser session structure and ingestion optimization remain additional survey candidates, not completed refactors.

## Ready to start

- [x] Record shell-first scope, priorities, detection rules, notification behavior and response limits.
- [x] Map the supplied rubric and idea template; retain the originals under `docs/reference/`.
- [x] Keep faculty questions open: final report format, title-page dates, deadline, presentation duration and any separate constraints.
- [ ] Agree meaningful ownership with the teammate and record actual contributions throughout the project.

## Workflow and SSH contract planning

- [x] Create the [Wayfinder decision map](https://github.com/BL47E/heimdall-home-security/issues/8), four native child tickets and dependencies; keep implementation issues separate.
- [x] Record the owner's beginner learning preference in `AGENTS.md`.
- [x] Agree the initial source and authentication scope: blue's SSH journal and explicit password successes/failures; supporting messages do not add attempts.
- [x] Agree Event facts, restricted local original-message evidence and short information-availability notes; preserve incomplete evidence without inventing missing facts.
- [x] Inspect journal cursor identity and microsecond timestamp fields on blue; export structured sanitized accepted/invalid-user/existing-account password samples with provenance.
- [ ] Finalize [the SSH log and event contract](https://github.com/BL47E/heimdall-home-security/issues/9) discussion; the factual inspections do not automatically resolve owner decision tickets.
- [ ] Resolve the dependent time-window/replay and durable-state decisions.
- [ ] Agree CI gates and manual deployment evidence, then implement and verify the selected checks. CI workflows are not implemented.

## Owner-requested browser dashboard — 2026-11-04

- [x] Record the owner's shell-monitor plus local-dashboard scope change in ADR 0003; faculty tool acceptance remains open.
- [x] Verify the Python standard-library HTTP bridge uses the shell commands for every state mutation (local HTTP integration tests).
- [x] Verify owner-token login, session handling, CSRF/origin/host checks and private token storage (local HTTP integration tests).
- [x] Verify distinct Overview/Investigations/Activity/Settings routes, owner login destination, local JetBrains Mono loading, review/reopen/report actions, saved settings and dirty-edit warnings with local synthetic state; see [dashboard verification](docs/verification/2026-11-05-dashboard.md).
- [x] Verify sign-out and browser-history restoration clear private records, including a delayed alert response arriving after logout (local browser check).
- [x] Preserve the approved panel appearance during source formatting using syntax/HTML/CSS comparisons; no new visual browser test was performed for the cleanup.
- [x] Verify live monitor start/stop, status and retained alert history in the deployed blue dashboard over authenticated HTTP.
- [x] Verify loopback default and explicit Host-Only access on blue at `10.37.129.3:8765`; see [the diary](diary.md).
- [x] Record which scenarios use synthetic data and which were verified against real Ubuntu SSH records; current runtime tests use synthetic/fake-journal input, not live Ubuntu evidence.

## 1. Ubuntu lab and log contract — Day 1

- [x] Set up two Ubuntu ARM64 VMs with Host-Only test adapters and separate Shared adapters; record observed environment and addresses in the diary.
- [x] Demonstrate manual monitor recovery through the VM console after a forced crash, preserving counts and available coverage ([2026-11-07 evidence](docs/verification/2026-11-07-red-blue-recovery.md)). Shared networking is not full isolation from the host or LAN.
- [ ] Verify fresh console login and recovery for the reviewed SSH-block scenario before enabling any real block.
- [x] Verify controlled red-to-blue SSH access over Host-Only, including host-key checking and source/destination addresses.
- [x] Record separate outbound routes through the Shared adapters.
- [ ] Verify and record separate outbound connectivity where configured.
- [x] Inspect real successful and invalid-user failed-password records; identify `journalctl -u ssh`, observed `sshd-session` messages, displayed timestamps/time zone and non-root read access in the tested account.
- [x] Export structured sanitized successful, invalid-user and existing-account wrong-password samples; fixture documentation records omitted fields and pseudonymized cursors.
- [x] Document dependencies, startup/shutdown, packaging and optional manual service setup/removal in the runbook; a resolved service instance is now installed and verified on blue.
- [x] Capture synthetic boundary/multiple-IP/missing-field/malformed scenarios and real Mac-to-blue three/four-failure evidence.
- [x] Capture real red-to-blue three/four-failure alerting, review/fifth-failure reopening, separate retained Mac-source alert and manual crash-recovery evidence ([2026-11-07](docs/verification/2026-11-07-red-blue-recovery.md)).
- [ ] Capture additional real expired-window and concurrent multiple-IP scenarios required for the final demonstration; retained alerts from separate sessions do not establish concurrent-window behavior.

Acceptance: representative real logs and repeatable offline samples are available; tests remain on the VM network. Record chosen versions and environment rather than guessing log paths.

## 2. Parsing and detection — Days 2–3

- [x] Implement supported password-result parsing and visible missing-field handling; synthetic scenarios and sanitized real Ubuntu exports pass. Final owner sign-off of the event contract remains open in issue 9 above.
- [x] Implement four failures per IP in a rolling five-minute window, across usernames; keep unknown sources separate (synthetic tests).
- [x] Group bursts until five quiet minutes and explain counts, timeline, severity and matched rule (synthetic tests).
- [x] Summarize successes against matching IP/user failures and preserve unknown counts when evidence is incomplete (synthetic implementation; live coverage remains to verify).
- [x] Verify boundary cases, malformed input and local operation without credentials or internet (local scenario tests).

Acceptance: three failures do not alert, the fourth within the window does, expired events do not count, and different IPs remain separate. Decide exact timestamp boundary/replay handling in the implementation issue.

## 3. Local investigations and management — Days 4–5

- [x] Implement restricted local storage, atomic updates and OS advisory locking; Ubuntu tests exercise crash recovery, and live stop/start preserves journal state. Boot recovery is recorded in the service checks below.
- [x] Add alert listing, inspection, review/reopen, review history and simple readable report output (local CLI/HTTP tests).
- [x] Reopen a reviewed active alert on new failures; a later burst becomes a new alert (synthetic tests).
- [x] Add shared CLI/browser operations and honest monitoring/provider status (real HTTP-to-CLI tests); the terminal app (bare `heimdall`, onboarding, Overview workspace, exact `/exit`) is implemented in source with pseudo-terminal tests.
- [x] Implement manual monitor start/stop, singleton prevention, cursor resume and readable failure state; verify live stop/start on blue and fake-journal crash scenarios locally.
- [x] Provide a manual systemd template with bounded restart settings and runbook instructions; the resolved blue instance is now installed and boot-tested.
- [x] Install and verify the reviewed systemd setup on blue, including boot startup and bounded recovery after a crash ([2026-11-07 service evidence](docs/verification/2026-11-07-systemd.md)).
- [x] Align source CLI/browser monitor controls with the fixed systemd unit, identity checks and noninteractive authorization failure handling (local fake-manager/HTTP checks and November 17 live deployment checks).
- [x] Deploy and verify service-aware CLI/browser controls on blue, including real authorization denial without fallback and administrator stop/start with truthful status ([evidence](docs/verification/2026-11-17-deployment.md)).
- [x] Implement explicit retention cleanup using configured days and preserving evidence referenced by retained alerts; default 60 days. Local cleanup now preserves pending Discord notifications and their evidence; active blocks remain unimplemented.
- [x] Provide daily cleanup service/timer templates, pass Ubuntu unit verification and install/enable them on blue; verify a timer trigger and successful service execution.
- [x] Implement and activate daily 60-day retention, preserving pending notifications and required supporting evidence; synthetic tests cover expired records and pending deliveries.
- [ ] Preserve active block records when enforcement state is designed and implemented; no blocks exist yet.

Acceptance: background monitoring survives closing the launching terminal or browser; local records survive restart, and future delivery state must also survive. Review changes do not change firewall state. A stopped or failing monitor is never shown as healthy.

## 4. Discord delivery — Day 6

Local queue, transport and fake-endpoint tests are implemented and checked in the [November 17 source checkpoint](docs/verification/2026-11-17-source.md). Real delivery to the owner-approved test server, controlled sender-only failure/recovery, queue persistence across fresh sender processes and scheduled delivery passed on November 17 ([evidence](docs/verification/2026-11-17-discord.md)). The injected failure was not a real Discord or VM network outage.

- [x] Configure the optional webhook securely; exclude secrets from source, logs, reports and the interface.
- [x] Send informative live alerts and notifications when new activity reopens a reviewed alert.
- [x] Persist failed deliveries; retry promptly when Discord is reachable using timeouts/backoff and provider rate limits.
- [x] Send outage backlog as a list, splitting only where necessary; mark accepted messages delivered.
- [x] Verify offline operation, recovery, restart and ambiguous delivery outcomes with a fake endpoint before a configured live test.

Acceptance: provider failure does not lose alerts or stop local monitoring; the backlog is grouped and delivery status is truthful.

- [ ] Observe sender-timer startup after a new VM reboot; source scheduling is installed/enabled, but that reboot check was not repeated.

## 5. Reputation and reports — Day 7

- [x] Add manual VirusTotal lookup for eligible public IPs, offline simulation, caching, quotas, timeouts and unknown-state handling.
- [x] Implement the agreed vendor-count labels and separate SSH alert severity.
- [x] Reject private and special-use addresses, send only the explicitly selected IP, and label mock responses.
- [x] Implement local text report export with evidence, rule explanation, review history and live/sample provenance (CLI and HTTP checks).
- [x] Show VirusTotal reputation and supporting facts in investigations and text reports.
- [ ] Verify an authorized public-IP lookup against VirusTotal on the lab installation if needed. Action outcomes remain planned with enforcement.

Acceptance: zero flags is no flags found, lookup failure is unknown, and private VM traffic never causes an external lookup. Reports contain no secrets.

## 6. Demonstration and response gate — Days 8–9

- [x] Add `heimdall demo` with explicit synthetic labels and deterministic rule/review/success scenarios in separate state; tested on blue. Provider/outage rehearsal remains open.
- [ ] Rehearse end-to-end alert investigation, restart and notification-outage recovery.
- [ ] Review the SSH-only response design, privilege boundary, firewall ownership, IPv4/IPv6 behavior and startup restoration before activation.
- [ ] Test recovery through the VM console before enabling a real block.
- [ ] If feasible after the gate: persist blocks, require confirmed manual unblock, count only new failures after unblock, audit outcomes and urgently report failed blocks.
- [ ] Run a separate deliberate live-block test from the second VM; otherwise keep this feature simulated and document its status.

Acceptance: the core demo works before enforcement work starts. No Mac firewall changes or general outbound quarantine. Do not claim the SSH parser sees connections already dropped by the firewall.

## 7. Evaluation and handoff — Throughout; finalize Day 10

- [ ] Draft the proposal with the idea template's section limits and at most three quantified objectives.
- [ ] Produce the required Gantt chart once preparing the proposal; use relative days until calendar dates are confirmed.
- [ ] Document the problem, existing-tool comparison and feasibility with verifiable sources.
- [ ] Keep objectives, algorithms, implemented modules and evidence aligned; distinguish simulated and planned work.
- [x] Record current CLI/VM and local dashboard inputs, expected/actual outcomes and limitations under `docs/verification/`, the diary and issue evidence.
- [ ] Capture the remaining live rule scenarios, sender-timer reboot startup, later unattended retention/catch-up and final-demo evidence; preserve already completed boot/crash and Discord results.
- [ ] Record both students' meaningful contributions and rehearse each person's explanation.
- [ ] Apply the confirmed report format when received. Leave faculty questions open until answered.
- [ ] Freeze features, check secrets are excluded and rehearse the final presentation.

Acceptance: submission claims match delivered behavior, evidence is reproducible, and the two students can explain their contributions and the full pipeline.
