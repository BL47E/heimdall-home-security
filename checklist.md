# Heimdall build checklist

Current scope: [college milestone](docs/college-milestone-plan.md), [ADR 0002](docs/adr/0002-shell-first-college-milestone.md) and [evaluation alignment](docs/evaluation-alignment.md). The broader blueprint remains future scope where the milestone overrides it.

Status: documentation and browser simulation exist; all runtime modules below are planned. GitHub Issues are the implementation tracker; see the [build backlog](docs/build-backlog.md) for the initial work packages. Check an item only after recording its implementation and verification evidence in the corresponding issue. Track actual contribution by both students.

## Ready to start

- [x] Record shell-first scope, priorities, detection rules, notification behavior and response limits.
- [x] Map the supplied rubric and idea template; retain the originals under `docs/reference/`.
- [x] Keep faculty questions open: final report format, title-page dates, deadline, presentation duration and any separate constraints.
- [ ] Agree meaningful ownership with the teammate and record actual contributions throughout the project.

## 1. Ubuntu lab and log contract — Day 1

- [ ] Set up two Ubuntu ARM64 VMs with console recovery and a private test network.
- [ ] Verify controlled SSH access and separate outbound access where configured.
- [ ] Capture sanitized examples of failed and successful SSH login records and identify the actual source, timestamp format and read permissions.
- [ ] Document dependencies, setup and teardown. Capture three-failure, fourth-failure, expired-window, multiple-IP, missing-field and malformed examples.

Acceptance: representative real logs and repeatable offline samples are available; tests remain on the VM network. Record chosen versions and environment rather than guessing log paths.

## 2. Parsing and detection — Days 2–3

- [ ] Parse the supported log source into a stable event contract. Treat log text as data and handle missing fields visibly.
- [ ] Implement four failures per IP in a rolling five-minute window, across usernames; keep unknown sources separate.
- [ ] Group bursts until five quiet minutes and explain counts, timeline, severity and matched rule.
- [ ] Summarize successes against matching IP/user failures and preserve unknown counts when evidence is incomplete.
- [ ] Verify boundary cases, malformed input and local operation without credentials or internet.

Acceptance: three failures do not alert, the fourth within the window does, expired events do not count, and different IPs remain separate. Decide exact timestamp boundary/replay handling in the implementation issue.

## 3. Local investigations and management — Days 4–5

- [ ] Implement restricted local storage, safe updates, locking and restart recovery.
- [ ] Add alert listing, inspection, review/reopen, review history and simple readable report output.
- [ ] Reopen a reviewed active alert on new failures; a later burst becomes a new alert.
- [ ] Add the shared CLI/TUI operations and honest monitoring/provider status.
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

- [ ] Add the guided demonstration with explicit simulation labels and deterministic sample scenarios.
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
