# Optional Discord delivery

Status: implementation design for the existing college milestone, prepared 2026-11-07. The design is now implemented in local source and covered by fake-endpoint tests; see [source verification](verification/2026-11-17-source.md). It does not establish live-tested Discord delivery. It follows the [milestone plan](college-milestone-plan.md) and [runtime contract](runtime-contract.md). No real provider is enabled by this design.

## Purpose and boundary

Local SSH parsing, alerts and review remain useful without internet access or credentials. A configured channel webhook adds concise notifications. Provider failure must not delay or terminate journal processing. Shell/jq owns alert decisions and durable delivery transitions; a narrow standard-library HTTP helper may perform transport and response validation. No new hosted dependency or required bot is needed.

Do not configure a real destination or transmit live evidence until the owner supplies and authorizes that destination. Routine source tests use a fake HTTP endpoint on loopback with explicitly labelled synthetic records. A successful fake endpoint test establishes local behavior, not delivery to Discord.

## Durable work

Enqueue one notification when an eligible alert is created and one when new failures reopen an active Reviewed alert. Do not enqueue another notification for each following failure. Manual reopen is a review operation, not new SSH activity. Preserve the alert transition and notification enqueue atomically, under the existing application transaction lock.

Disabled or unconfigured delivery makes no external requests. Define enabling as applying to subsequent alert transitions; do not silently send historical findings when a secret is first configured. Provider status must distinguish disabled, configured/pending, delivery error, rate limited and accepted delivery where supported. Never describe internet reachability as provider health.

Queue records need stable local IDs, alert references, transition reason, creation time, pending/accepted state, attempts and next-eligible-at time. Store only safe diagnostic categories, not response bodies or URLs. Retain pending delivery across process restarts. Retention must preserve the related alert and supporting events while a notification remains pending, even beyond the configured history period. This does not establish a block-state schema: real enforcement is unimplemented and remains behind its separate gate.

## Transport and retries

The official [Execute Webhook documentation](https://github.com/discord/discord-api-docs/blob/main/developers/resources/webhook.mdx#execute-webhook) documents `wait=true` for server confirmation and a created-message response; use this instead of assuming a fire-and-forget response proves delivery. Keep content within 2,000 characters and disable automatic mentions through `allowed_mentions`. Use [Discord's rate-limit guidance](https://github.com/discord/discord-api-docs/blob/main/developers/topics/rate-limits.mdx) for dynamic retry timing: `Retry-After`/`retry_after` are seconds; a missing webhook (404) should not be repeatedly retried.

Use bounded connection/request timeouts, exponential retry backoff and durable retry timing. Honor provider rate-limit delays, including a successful response that exhausts the current bucket. Invalid credentials or a deleted destination require owner correction; keep the local pending evidence intact. Validate destination URLs and do not follow redirects carrying a webhook secret. Never print credentials in commands, logs, reports, HTTP responses or the interface. Production destinations are approved Discord HTTPS webhook URLs; an explicitly separate loopback test path must not silently expand production URL acceptance.

Snapshot a bounded group of pending notifications under a delivery singleton lock, release the state transaction lock during HTTP, then mark only the exact accepted group delivered in another state transaction. Preserve notifications appended while an HTTP request is in flight. Multiple workers or timer invocations must not concurrently send the same queue entry. If a request was accepted remotely but its response or local acknowledgement was lost, retain an honest ambiguous outcome and retry according to policy; duplicate delivery is possible.

After an outage, format pending findings together as a list and split only to meet message limits. Include timestamp, source, failure count, severity, rule explanation, reputation availability and actual action state. Do not include raw SSH messages, usernames, webhook credentials or claims of active blocking. Synthetic provenance must remain visible. One recovery message is preferable to one HTTP request per alert when the list fits.

## Required checks

- Unconfigured operation: no network request, normal local ingestion and truthful provider status.
- New alert/review-reopen transitions enqueue exactly once; duplicate ingestion and continuing failures do not duplicate work.
- HTTP rejection, timeout and process restart retain pending work and do not stop monitoring.
- Recovery groups pending findings and splits overlength content without dropping references.
- Acceptance marks only the transmitted snapshot; concurrent enqueue remains pending.
- Rate-limit timing survives restart; disabled/revoked credentials do not generate tight retry loops.
- Lost acknowledgements retain ambiguity without promising exactly-once delivery.
- Cleanup preserves pending alert/evidence references; delivered history can expire normally.
- Secret files are private, production URL restrictions hold, redirects are rejected and no secret appears in outputs or evidence.

Scheduled delivery, provider UI and report context must be marked implemented only when their integration checks pass. A later owner-authorized live test remains separate from this fake-endpoint implementation stage.
