# Heimdall build checklist

Current scope: [college milestone](docs/college-milestone-plan.md), [ADR 0002](docs/adr/0002-shell-first-college-milestone.md), the owner's [dashboard extension in ADR 0003](docs/adr/0003-shell-monitor-with-local-dashboard.md) and [evaluation alignment](docs/evaluation-alignment.md). The broader blueprint remains future scope where the milestone overrides it.

Use the [status matrix](docs/status.md) for current implementation and dated evidence, and the [build backlog](docs/build-backlog.md) for GitHub Issues. Completed checkboxes record acceptance; open decision tickets remain open until the owner answers them.

## Home deployment follow-up

- [ ] Add [private Tailscale access to the Heimdall dashboard on a Linux NAS](https://github.com/BL47E/heimdall-home-security/issues/16). Verify remote browser access and Heimdall login after restart, plus local monitoring and TUI access when Tailscale is disconnected.

## Resume the lab

Lab identity after the owner's laptop reset (observed over SSH on November 25): the VMs are now UbuntuBlue (hostname `blueblue`, user `blazeblue`) and UbuntuRed (hostname `blazered`, user `blazered`). Blue is at `10.211.55.9` (Shared) and `10.37.129.8` (Host-Only); red at `10.211.55.10` (Shared) and `10.37.129.9` (Host-Only). The pre-reset addresses in older diary/evidence records no longer respond; historical entries keep their original values.
- The deployed release and services are described in [current status](docs/status.md); use the [runbook](docs/runbook.md) for service controls and recovery. Blocking remains unimplemented and its recovery gate remains open.
- Per the owner's request on November 25, both VMs disable idle screen locking (`idle-delay 0`) and idle suspend; the screen asks for a password only at explicit logout/login or a manual lock.

## Panel design and repository cleanup — completed locally and saved

- [x] Create the [control panel design guide](docs/control-panel-design.md), archive and deduplicate historical artifacts, and verify formatting, documentation links and packaging. The [archive record](docs/archive/README.md) preserves the deduplication evidence; [issue 14](https://github.com/BL47E/heimdall-home-security/issues/14) is closed.
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

- [x] Record the scope change in ADR 0003 and verify authentication, routes, security checks and live operations; [dashboard evidence](docs/verification/2026-11-05-dashboard.md) distinguishes synthetic and live scenarios. Faculty tool acceptance remains open.

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
- [x] Install and verify daily cleanup, including a timer trigger and successful service execution; synthetic tests cover expiration and pending deliveries.
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
