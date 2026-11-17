# Heimdall college milestone

Status: agreed planning direction, 2026-11-01, extended by the owner's 2026-11-04 request for a local browser dashboard. Status reconciled November 17: the SSH monitor/dashboard, service controls, daily cleanup and optional real Discord delivery are implemented and deployed. The feature list below remains the full target, including unfinished optional work; see [implementation status](status.md) for the code/test/evidence mapping. The earlier browser prototype is simulated. See [ADR 0003](adr/0003-shell-monitor-with-local-dashboard.md) for the dashboard amendment to [ADR 0002](adr/0002-shell-first-college-milestone.md), [the runbook](runbook.md) for setup, and [the blueprint](../HEIMDALL_BLUEPRINT.md) for the broader product.

## Current delivery checkpoint

[November 17 Discord verification](verification/2026-11-17-discord.md) records four notices delivered in three messages, including real threshold/reopening alerts, grouped recovery after an injected sender-only failure, and timer-driven delivery. This is not evidence of a genuine Discord outage. The [deployment record](verification/2026-11-17-deployment.md) covers service-aware controls and retention; [earlier service evidence](verification/2026-11-07-systemd.md) covers real boot/crash tests. The dashboard still starts manually, and existing Ubuntu policy requires administrator console commands for monitor start/stop. VirusTotal, terminal menu, enforcement and the final academic submission remain unfinished.

## Goal and constraints

Deliver an explainable, live SSH security demonstration for a first Linux and shell programming project. Two students are involved, with the owner doing most development. Plan for ten working days from the agreed project start; the exact submission date is unconfirmed.

The owner supplied the 30-mark evaluation rubric and idea template on 2026-11-01. See [evaluation alignment](evaluation-alignment.md) for all ten sub-criteria, the evidence plan and the proposal's required sections and formatting. The rubric gives 6 marks each to analysis, design, implementation, the report and communication. The idea template allows at most three realistic quantified objectives and requires a Gantt chart. Whether it also governs the final report, any separate feature requirements, exact deadline and presentation duration remain pending. The existing repository evaluation guide is supplementary material.

## Environment and architecture

- MacBook M4 Air, 16 GB RAM, hosting two Ubuntu ARM64 VMs.
- Heimdall VM: SSH service, shell-based monitor, local records, command interface and local browser dashboard. A TUI remains optional later work.
- Test VM: controlled SSH attempts against the Heimdall VM over a private virtual network.
- Shared adapters provide outbound routes; real Discord delivery from blue was verified. Host-Only adapters carry controlled SSH tests. Separate standalone reachability evidence for red remains open.
- Shell is the main implementation language; jq handles JSON records and Python 3's standard library provides the HTTP bridge. This owner-requested addition is not evidence of faculty approval of permitted technologies. Parallels Desktop is selected; blue's observed SSH banner reports Ubuntu 26.04.1 LTS and the live source is `journalctl -u ssh` JSON. Record/recheck versions when resuming.
- Local files store state and history. Use restricted permissions, atomic updates and locking where needed; keep secrets out of reports and source control.
- A Linux service manager is the intended boot/startup path, with duplicate prevention and bounded crash restarts. The repository includes a service template; a resolved instance was installed on blue and verified for boot startup, automatic crash recovery and bounded retries on 2026-11-07 ([evidence](verification/2026-11-07-systemd.md)). The dashboard remains manually started. Service-aware controls and daily cleanup were deployed and verified on November 17 ([evidence](verification/2026-11-17-deployment.md)); existing Ubuntu policy requires administrator console commands for start/stop. Closing the browser does not stop an independently running monitor.
- The dashboard defaults to loopback; binding a specific trusted local IP requires an explicit launch option. Owner-token login and protected mutations govern review, configuration and monitor start/stop. No automatic firewall, adapter or router changes accompany dashboard access.
- Local monitoring remains useful offline. There is no outage-triggered quarantine mode.

## Detection and investigation

- Read one documented Ubuntu SSH log source; discover and test its actual format before writing the parser.
- Raise an alert at four failures from the same source IP in a rolling five-minute window, across usernames. This is a configurable heuristic, not proof of compromise.
- Show missing source addresses as unknown; do not group all unknown sources into a single source-based alert.
- Keep a continuous burst in one alert until five minutes pass without another failure from that IP. A later burst creates a new alert.
- Explain the rule, source, timestamps, failure count, evidence timeline, severity and recommended manual next step.
- Show whether an address is private/local or public without implying that either category establishes safety.
- If a successful login occurs before the blocking threshold, record the number of preceding failures for the same username and IP within five minutes. Missing matching fields produce an unknown count. Do not block solely because of that success.
- Keep local alert history, allow inspection and report export, and display monitoring and provider health clearly. Missing or unreadable logs must not be reported as healthy monitoring.
- Alerts begin as Needs review. Owners can mark them Reviewed or return them to Needs review. Preserve review history.
- New failures after review reopen an active alert as Needs review and generate a Discord update on that transition, rather than on every subsequent failure.

## VirusTotal context

Optional and disabled until configured. Look up eligible, non-sensitive public IPs after an alert; never submit private addresses or full logs. Cache results and respect account quotas and rate limits. A timeout, missing key or exhausted quota means unknown reputation, not zero flags.

| Vendors flagging the IP | Reputation label |
|---:|---|
| 0 | No flags found |
| 1–3 | Low concern |
| 4–6 | Medium concern |
| 7–9 | High concern |
| 10 or more | Very high concern |
| Lookup unavailable | Unknown |

Keep reputation labels separate from SSH alert severity. The agreed starting severity is Medium for a qualifying failure burst and High with ten or more vendor flags. Always show the supporting facts and lookup time; neither vendor count nor severity is a probability of compromise.

The private VM source addresses are ineligible for external lookup. Demonstrate reputation bands using clearly labelled simulated results. Any separate live lookup must use an eligible public indicator with awareness that the query shares it with the provider.

## Discord delivery

- Use a channel webhook, not a required bot implementation.
- Send live alerts promptly, including the time, source, failure count, severity, rule explanation, reputation availability and actual block outcome where applicable. Keep detailed evidence locally.
- Save notification state across restarts. Retry delivery when Discord becomes reachable; internet connectivity alone does not establish Discord availability.
- After an outage, send pending alerts together as a list, splitting only for message limits. Mark only accepted messages as delivered.
- Delivery is best effort, with backoff and provider rate limits; exact same-second delivery cannot be guaranteed. Handle ambiguous delivery outcomes without promising duplicate-free delivery.

## SSH response: last implementation priority

The owner supports automatic SSH source blocking in the isolated VM. The detailed design must be reviewed and recovery tested before enabling automatic network changes. This is a scoped exception to the broader product's recommendation-only first release, not permission to change the Mac or arbitrary devices.

- On four failures from an IP in five minutes, block further SSH connection attempts from that IP only. Account lockout and general outbound shutdown are excluded.
- Preserve blocks across reboot until explicit manual unblock.
- Show and confirm the IP and related alert before unblocking. Verify and record success or failure.
- A review-status change never unblocks a source.
- After unblock, count only new failures toward another block; preserve earlier evidence.
- Record block/unblock time, source, result and related alert. A failed block produces an urgent local and Discord warning, pending delivery if offline.
- Recover through the VM console. Define and test firewall ownership, privilege separation, startup restoration and IPv4/IPv6 handling before activation.
- The guided demo simulates the action and labels it. A deliberate, separate live test uses the second VM after design review and recovery testing.
- Blocking may prevent later failures from reaching SSH logs; do not claim that the SSH monitor sees attempts dropped by the firewall.

## Management and retention

The browser dashboard and commands share the same application operations. Current implementation interface and schemas are specified in [the runtime contract](runtime-contract.md); the earlier TUI-oriented command sketch below remains a proposal for convenience commands, not evidence each command exists:

```text
heimdall                     Open terminal menu
heimdall monitor start       Start background monitoring
heimdall monitor stop        Stop monitoring
heimdall status              Show service, log and provider health
heimdall alerts              List alerts
heimdall inspect ID          Display evidence and history
heimdall review ID           Mark reviewed
heimdall reopen ID           Return to Needs review
heimdall report ID           Export a readable investigation report
heimdall demo                Run guided, labelled demonstration
heimdall help                Explain available commands
```

Add block-list and unblock commands only alongside the reviewed response implementation. Confirm names during implementation rather than treating this example as an installed interface.

Keep alerts for 60 days by default, configurable. Run cleanup daily. Preserve pending notifications and active block records beyond this period until resolved. Keep supporting records needed to interpret retained alerts. Never delete active enforcement state as routine history cleanup.

## Ten-day sequence

1. Day 1: establish both VMs, private networking, SSH and representative logs; record setup.
2. Days 2–3: parser, sample fixtures, rolling-window rule, live monitoring and explanations.
3. Days 4–5: local history, review states, commands, browser dashboard and background service lifecycle.
4. Day 6: Discord alerts, outage queue and grouped recovery delivery.
5. Day 7: optional VirusTotal context and investigation reports.
6. Day 8: guided demo, health visibility and end-to-end checks. If core features are reliable, review the SSH response design and test console recovery before implementation.
7. Day 9: bounded live blocking work only if recovery checks pass; otherwise polish the simulated response and document the limitation.
8. Day 10: rehearse, verify restart/outage behavior, finish the report and presentation, and freeze features.

This is a target sequence, not a guarantee of feature completion. Prioritize live detection and explanation, then TUI/history/Discord, then enrichment/reports, and real blocking last. Reserve rehearsal time even if blocking remains simulated. Draft the academic report, capture test evidence and record each student's actual contributions throughout development; Day 10 is for final checks and rehearsal, not the first report draft. Keep the final design aligned with the delivered modules.

## Demonstration evidence

- Three failures do not trigger the four-failure alert; the fourth within five minutes does. Failures outside the rolling window do not incorrectly contribute.
- Different source IPs remain separate, unknown sources are not merged, and user-controlled log text is handled as data.
- Grouping, review transitions and successful-login summaries match the agreed behavior.
- Restart retains records and pending notifications; status exposes monitor failure and service restart behavior.
- A Discord outage preserves alerts and recovery sends a grouped list with honest delivery status.
- VirusTotal unavailable means unknown; simulated scores and sample data are labelled throughout.
- If live blocking is implemented, demonstrate only SSH restriction, successful console recovery and truthful action reporting on both success and failure.

## Open prerequisites

- Final-report template applicability, any separate course requirements, exact submission date, presentation duration and title-page dates; the marking rubric and idea template have been received and mapped.
- Additional live expired-window, concurrent-source and success-correlation evidence; Discord timer startup after a fresh reboot and later unattended cleanup/catch-up evidence. The VM platform, blue version and exported SSH examples are already recorded.
- Optional VirusTotal credentials if that provider is implemented. Discord is already privately configured for the owner-approved test destination; its credential must stay out of documents and Git.
- Detailed SSH response design review and recovery evidence before automatic enforcement.
