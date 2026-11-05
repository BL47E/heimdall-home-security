# Heimdall build checklist

Current scope: [college milestone](docs/college-milestone-plan.md), [ADR 0002](docs/adr/0002-shell-first-college-milestone.md), the owner's [dashboard extension in ADR 0003](docs/adr/0003-shell-monitor-with-local-dashboard.md) and [evaluation alignment](docs/evaluation-alignment.md). The broader blueprint remains future scope where the milestone overrides it.

Status: CLI 0.1.0 passes local tests and has been deployed and checked against real SSH records on blue; see [VM verification](docs/verification/2026-11-04-cli-blue.md). The browser has local and HTTP-to-shell checks. Items requiring boot/service recovery or browser VM deployment remain open. GitHub Issues are the implementation tracker; see the [build backlog](docs/build-backlog.md). Track actual contribution by both students.

Progress reconciled on 2026-11-04 against [the diary](diary.md), [lab verification evidence](https://github.com/BL47E/heimdall-home-security/issues/1#issuecomment-6632267553) and the [SSH contract discussion](https://github.com/BL47E/heimdall-home-security/issues/9). Checked planning items below record agreed choices, not working runtime behavior. Earlier lab observations do not establish the VMs' current power state or addresses.

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
- [ ] Verify live monitor controls and status in the deployed blue dashboard; browser layout checks do not establish live Ubuntu coverage.
- [ ] Verify loopback default and explicit trusted-local-IP access on blue; record actual reachable address without changing network controls automatically.
- [x] Record which scenarios use synthetic data and which were verified against real Ubuntu SSH records; current runtime tests use synthetic/fake-journal input, not live Ubuntu evidence.

## 1. Ubuntu lab and log contract — Day 1

- [x] Set up two Ubuntu ARM64 VMs with Host-Only test adapters and separate Shared adapters; record observed environment and addresses in the diary.
- [ ] Demonstrate and record recovery through the VM console. Shared networking is not full isolation from the host or LAN.
- [x] Verify controlled red-to-blue SSH access over Host-Only, including host-key checking and source/destination addresses.
- [x] Record separate outbound routes through the Shared adapters.
- [ ] Verify and record separate outbound connectivity where configured.
- [x] Inspect real successful and invalid-user failed-password records; identify `journalctl -u ssh`, observed `sshd-session` messages, displayed timestamps/time zone and non-root read access in the tested account.
- [x] Export structured sanitized successful, invalid-user and existing-account wrong-password samples; fixture documentation records omitted fields and pseudonymized cursors.
- [ ] Document dependencies, setup and teardown. Capture three-failure, fourth-failure, expired-window, multiple-IP, missing-field and malformed examples.

Acceptance: representative real logs and repeatable offline samples are available; tests remain on the VM network. Record chosen versions and environment rather than guessing log paths.

## 2. Parsing and detection — Days 2–3

- [ ] Parse the supported log source into a stable event contract. Treat log text as data and handle missing fields visibly.
- [x] Implement four failures per IP in a rolling five-minute window, across usernames; keep unknown sources separate (synthetic tests).
- [x] Group bursts until five quiet minutes and explain counts, timeline, severity and matched rule (synthetic tests).
- [x] Summarize successes against matching IP/user failures and preserve unknown counts when evidence is incomplete (synthetic implementation; live coverage remains to verify).
- [x] Verify boundary cases, malformed input and local operation without credentials or internet (local scenario tests).

Acceptance: three failures do not alert, the fourth within the window does, expired events do not count, and different IPs remain separate. Decide exact timestamp boundary/replay handling in the implementation issue.

## 3. Local investigations and management — Days 4–5

- [x] Implement restricted local storage, atomic updates and OS advisory locking; Ubuntu tests exercise crash recovery, and live stop/start preserves journal state. Boot recovery remains below.
- [x] Add alert listing, inspection, review/reopen, review history and simple readable report output (local CLI/HTTP tests).
- [x] Reopen a reviewed active alert on new failures; a later burst becomes a new alert (synthetic tests).
- [ ] Add shared CLI/browser operations and honest monitoring/provider status; TUI remains later convenience work.
- [ ] Add service startup, shutdown, duplicate prevention, bounded crash restart and readable failure state.
- [ ] Implement daily 60-day retention while preserving pending notifications, active blocks and required supporting evidence.

Acceptance: background monitoring survives closing the TUI; records and delivery state survive restart; review changes do not change firewall state. A stopped or failing monitor is never shown as healthy.

## 4. Discord delivery — Day 6

- [ ] Configure the optional webhook securely; exclude secrets from source, logs, reports and the interface.
- [ ] Send informative live alerts and notifications when new activity reopens a reviewed alert.
- [ ] Persist failed deliveries; retry promptly when Discord is reachable using timeouts/backoff and provider rate limits.
- [ ] Send outage backlog as a list, splitting only where necessary; mark accepted messages delivered.
- [ ] Verify offline operation, recovery, restart and ambiguous delivery outcomes with a fake endpoint before a configured live test.

Acceptance: provider failure does not lose alerts or stop local monitoring; the backlog is grouped and delivery status is truthful.

## 5. Reputation and reports — Day 7

- [ ] Add optional public-IP eligibility, simulated VirusTotal adapter, caching, quotas, timeouts and unknown-state handling.
- [ ] Implement the agreed vendor-count labels and separate SSH alert severity.
- [ ] Never submit private/sensitive indicators or raw logs. Clearly label mock responses.
- [ ] Finish report export with evidence, review history, provider provenance and action outcomes when present.

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
- [ ] Record test inputs, expected/actual outcomes, screenshots or terminal transcripts and limitations.
- [ ] Record both students' meaningful contributions and rehearse each person's explanation.
- [ ] Apply the confirmed report format when received. Leave faculty questions open until answered.
- [ ] Freeze features, check secrets are excluded and rehearse the final presentation.

Acceptance: submission claims match delivered behavior, evidence is reproducible, and the two students can explain their contributions and the full pipeline.
