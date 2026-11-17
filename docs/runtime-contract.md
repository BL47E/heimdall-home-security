# Shell monitor and browser dashboard contract

Status: implementation contract selected for the owner's 2026-11-04 request to build the monitor and a local browser dashboard. This records implementation choices, not verified live-VM results. The dashboard extends ADR 0002; unresolved faculty requirements remain open. Integrations and SSH blocking remain planned.

## Components and ownership

- `bin/heimdall`: executable Bash entry point. Target Bash 3.2-compatible syntax for offline development on macOS, and Ubuntu ARM64 for live journal monitoring. Uses `jq` and standard Unix tools. No `eval`, sourced configuration or interpretation of log text as commands.
- `lib/`: shell/jq parsing, rules and storage, plus a small Python standard-library normalization helper for IP validation/canonicalization and content fingerprints. The shell CLI owns every runtime state mutation, including browser configuration and alert reviews.
- `web/server.py`: Python 3 standard-library HTTP bridge. Executes the CLI using argument lists with `shell=False`, timeout and a fixed absolute executable path. Python serves HTTP; SSH interpretation and rule decisions remain in shell/jq.
- `web/static/`: offline HTML, CSS and JavaScript, without CDN dependencies or a build tool. Mobile layout and keyboard access are required.
- `tests/fixtures/`: explicitly synthetic journal JSONL scenarios and provenance notes; never describe them as exported real logs.
- `HEIMDALL_DATA_DIR`: runtime directory, default `${XDG_STATE_HOME:-$HOME/.local/state}/heimdall`. Private directories (0700) and files (0600), excluded from Git. Both components receive the same directory through their environment.

State changes use an operating-system advisory lock through `lib/lock.py` (Python standard-library `fcntl`), a temporary file in the same directory and atomic rename. Transactions wait at most five seconds for their lock. A separate monitor singleton lock rejects duplicate readers; the OS releases these locks after a crash. The journal child closes the singleton descriptor so an orphan cannot retain it. Lock files remain in the private state directory and must not be deleted while software is running. Interrupted writes preserve the prior valid state. Do not overwrite corrupt state.

## CLI interface

All successful commands below return one JSON value on stdout, with diagnostics on stderr. Errors return nonzero. Unknown IDs fail without changing state.

| Command | Result and behavior |
|---|---|
| `heimdall help` / no arguments | Readable command guide; no state creation. |
| `heimdall version` | Version text from `VERSION`; no state creation. |
| `heimdall demo` | Labelled synthetic walkthrough in a newly created separate data directory, retained for inspection. Human-readable output; no live-state mutation or network actions. |
| `heimdall init` | Idempotently create private state and default configuration; return config object. |
| `heimdall status` | Return status object described below, including accurate process liveness. |
| `heimdall alerts` | Return alert array, most recently updated first. |
| `heimdall events` | Return the latest at most 200 events, newest first. |
| `heimdall inspect ID` | Return one complete alert including supporting events and review history. |
| `heimdall review ID` | Mark reviewed, append review history, return updated alert. |
| `heimdall reopen ID` | Mark needs_review, append review history, return updated alert. |
| `heimdall config get` | Return configuration object. |
| `heimdall config history` | Return recorded configuration changes as JSON. |
| `heimdall config set JSON` | Validate a JSON object patch, reject unknown keys, atomically save and return full configuration. No partial update on invalid input. |
| `heimdall ingest FILE` | Read newline-delimited journal JSON from a local file or `-` for stdin. Return counts such as `processed`, `duplicates`, `unsupported`, `malformed`; persist useful evidence. This is offline ingestion, never evidence of a healthy live monitor. |
| `heimdall monitor run` | Foreground live journal consumer for a service manager or standalone use. An installed matching system unit owns this entry point; a managed invocation must belong to that unit's actual process control group. Stdout may be reserved for operational messages; documented exception to JSON command output. |
| `heimdall monitor start` | Use the matching installed system unit when present; otherwise start an independent background journal consumer. Return status; detect duplicates. Never fall back to a detached process after a service control failure. |
| `heimdall monitor stop` | Stop the matching installed system unit when present; otherwise stop only a proven standalone Heimdall monitor process. Return status. No arbitrary PID kills. |
| `heimdall report ID` | Readable text investigation report, documented exception to JSON output. |
| `heimdall cleanup` | Apply retention safely and return removal counts. |

No web endpoint accepts arbitrary shell commands, filesystem paths, journal units or code. CLI ingestion is local-only. If a command cannot be implemented in the first pass, it must fail explicitly and the dashboard must label it unavailable.

### Monitor service ownership

Source implementation selects `HEIMDALL_MONITOR_MANAGER=auto` by default; `standalone` and `systemd` are explicit alternatives. Only the system-scope `heimdall-monitor.service` is supported. Read-only inspection verifies the unit's owner, working directory, exact foreground CLI invocation and `HEIMDALL_DATA_DIR` against the current release and state. An absent unit permits standalone operation in auto mode. A loaded but mismatched, ambiguous or unreadable unit fails closed; choosing standalone does not override a matching installed unit. Fixture status remains usable without querying the live service.

Service operations use bounded, noninteractive `systemctl --system --no-ask-password` calls. They never invoke sudo, save passwords, install authorization policy or request an arbitrary unit. Existing system authorization determines whether control succeeds. If authorization is unavailable, exit 77 with a service-control diagnostic and a manual administrator command; the browser returns an actionable 503 response. No direct process control follows a service failure.

Status adds `monitor.manager` and `monitor.service` metadata. A system unit reported active is insufficient for available coverage: the saved PID must still be alive, match the CLI process and equal the unit's MainPID, and live journal coverage must have been established. Inactive, failed, mismatched or unreadable service state cannot report healthy monitoring. A known unit-owned PID's Linux control-group membership prevents standalone fallback if service inspection disappears. This local source integration requires separate deployment verification on blue; the earlier service evidence tested the installed unit with the previous process-only CLI.

## Configuration

```json
{"threshold":4,"window_seconds":300,"retention_days":60}
```

Only those three integer fields are editable in the first dashboard. Bounds: threshold 2–100, window_seconds 30–3600, retention_days 1–365. Reject booleans, fractions, null and numeric strings. The live source is fixed to `journalctl -u ssh` JSON. Configuration changes affect subsequently processed events and are recorded; old alerts preserve the rule settings that produced them. Config changes must not reset review history or discard events. The monitor re-reads config between events. No provider secrets are part of this configuration.

## Event contract and detection

Accept journal JSON records with `MESSAGE`, `__CURSOR`, `__REALTIME_TIMESTAMP` (microseconds since epoch). Preserve the original timestamp string and cursor; expose normalized `timestamp` as Unix seconds (number or null). A cursor is the durable source identity when present. An offline record without a cursor may use an explicitly labelled content fingerprint for deduplication, never a claimed journal identity. Preserve event provenance (`journal` or `fixture`) and raw authentication message locally. Avoid collecting unrelated message bodies indefinitely.

Recognize only explicit `Accepted password for USER from IP port PORT ssh2`, `Failed password for USER from IP port PORT ssh2`, and `Failed password for invalid user USER from IP port PORT ssh2`. Supporting PAM, invalid-user and closure lines do not add authentication attempts. Malformed/unsupported input never invents an outcome. Keep useful available evidence and availability notes. Known valid time/source/failure may count without username; unknown sources are never merged. Validate IPv4/IPv6 before grouping and canonicalize equivalent addresses where supported; explicitly state any unsupported address forms.

Event fields exposed to the browser:

```json
{"id":"stable-reference","cursor":null,"timestamp":1793447945,"timestamp_us":"1793447945000000","source_ip":"10.37.129.4","username":"testuser","outcome":"failure","invalid_user":null,"message":"Failed password ...","notes":[],"provenance":"fixture","preceding_failures":null}
```

Failure rule: qualifying events for one IP at times `t-window_seconds <= event.time <= t` count across usernames. Four qualify by default. Keep one burst until a gap of at least window_seconds since its last failure, then create a later alert only when the new burst reaches threshold. At the exact quiet-time boundary the previous burst is closed; the rolling count must not drag the preceding burst's boundary event into the new burst. Explain this distinction in tests/docs. An alert contains its own threshold/window settings, source, count, event IDs and explanation. New failures in an active reviewed alert reopen it and append a history record. Successful logins may summarize prior failures for the same IP/user within the window; missing matching evidence yields unknown. Success alone never blocks or proves compromise.

Order and replay: persist cursor-based deduplication with state so restart cannot recount events. The initial live start begins at the current journal position (`--since now` or equivalent) rather than silently alerting on historical attacks; later starts resume after the saved cursor. A lost cursor/read failure must be visible, not silently reported as uninterrupted coverage. Late older records remain evidence but do not move a source's active clock backwards or create new current alerts; document their exclusion from real-time rules. Fixture replay uses the same detector but labels simulated input and coverage. Retention defaults to 60 days and preserves evidence needed by retained alerts; provider pending/block exemptions remain design obligations before those features exist.

## Alert and status responses

```json
{"id":"alert-reference","source_ip":"10.37.129.4","severity":"MEDIUM","review_status":"needs_review","first_seen":1793447700,"last_seen":1793447945,"failure_count":4,"rule":{"id":"ssh-password-burst","version":1,"threshold":4,"window_seconds":300},"explanation":"Four failed password attempts from this source within five minutes.","recommendation":"Review the account and the supporting SSH records.","event_ids":[],"events":[],"review_history":[],"provenance":"fixture"}
```

`events` may be omitted in list responses but must be present on inspect. `review_history` records timestamp, resulting review status and reason (`owner` or `new_failure`).

```json
{"monitor":{"state":"stopped","pid":null,"source":"journalctl -u ssh","last_event_at":null,"last_error":null,"coverage":"unavailable"},"counts":{"events":0,"alerts":0,"needs_review":0},"providers":{"discord":"disabled","virustotal":"not_implemented"},"mode":"live","config":{"threshold":4,"window_seconds":300,"retention_days":60}}
```

State values: `running`, `stopped`, `error`; coverage `available` only after a live journal read is proven and consumer is alive, otherwise `unavailable`. Mode `fixture` means offline samples, never live healthy monitoring. Preserve last errors and report permission/read/child-process failure. Quiet logs alone do not imply failure. Do not claim integrations work.

## Browser API

The server CLI is `python3 web/server.py --host 127.0.0.1 --port 8765`; `--host LOCAL_IP` explicitly enables trusted local-network access. It initializes shell state. It creates/loads a random owner token in a private `web-token` file inside the state directory and prints the path, never the value in request logs or URLs. The owner reads that file locally to sign in. HTTP is for a trusted local lab only; remote/untrusted exposure requires TLS/reverse-proxy design.

| Endpoint | Result |
|---|---|
| `GET /`, `/overview`, `/investigations`, `/activity`, `/settings` and fixed static assets | Implemented public application shell/static files only; no private state embedded. Each page URL can be loaded or reloaded directly. |
| `POST /api/login` with `{"token":"..."}` | Constant-time token comparison, bounded attempts; establish random HttpOnly SameSite=Strict session cookie and return CSRF token. |
| `POST /api/logout` | Expire session. |
| `GET /api/session` | Authentication state and CSRF token for authenticated session; never owner token. |
| `GET /api/status` | CLI status object. |
| `GET /api/alerts` | CLI alert array. |
| `GET /api/events` | CLI event array. |
| `GET /api/alerts/ID` | CLI inspect object. |
| `GET /api/alerts/ID/report` | Text report download. |
| `GET /api/config` | Configuration. |
| `POST /api/config` | Configuration patch; full validated config response. |
| `POST /api/alerts/ID/review` | Updated alert. |
| `POST /api/alerts/ID/reopen` | Updated alert. |
| `POST /api/monitor/start` | Status. |
| `POST /api/monitor/stop` | Status. |

Except login/session discovery/static assets, require authenticated session. Every mutation including logout requires session CSRF header `X-CSRF-Token`; login requires same-origin checks. Validate Host and Origin against the configured listener, reject cross-origin writes, do not enable CORS. Enforce `application/json`, 16 KiB maximum body, subprocess timeouts, URL/ID validation and fixed static-path allowlist. Report errors as `{"error":"Useful message"}` with appropriate HTTP status. Never use log messages as HTML: render text with `textContent`. Add no-cache/private responses, CSP, frame protection and referrer policy.

Page navigation uses distinct URLs; signing in preserves the requested page. Direct loading the public shell does not grant access to evidence or other protected API responses.

The dashboard presents honest status, alert list and evidence, recent events, review/reopen, configuration form, monitor start/stop and readable report downloads. Use a simple polling refresh with visible stale/error state. Describe disabled integrations as planned. Do not offer firewall manipulation, arbitrary script editing or faux working controls.

Page navigation uses real links: `/` and `/overview` select Overview, `/investigations` selects alert review, `/activity` selects recent events and `/settings` selects configuration. Exactly one page is visible after authentication. Direct loads and browser Back/Forward retain the intended route; unsaved configuration edits trigger the browser's leave-page warning. Authentication loss clears private page content, and restored browser-history pages revalidate their session before showing records. Refresh responses from an earlier session cannot repopulate private content after sign-out.

JetBrains Mono Regular and Medium load from the exact public asset URLs `/fonts/JetBrainsMono-Regular.woff2` and `/fonts/JetBrainsMono-Medium.woff2`, served as `font/woff2`; no external font service is required. Their SIL Open Font License is retained in `web/static/fonts/OFL.txt`. Unknown routes and assets, encoded paths, query strings, fragments and non-origin-form request targets are rejected rather than falling through to a general filesystem server.

## Local delivery extension — November 17 source checkpoint

`discord configure` reads an approved HTTPS Discord webhook from stdin and saves it privately; `configure-test` accepts only explicit loopback test destinations. `enable`, `disable`, `status` and `flush` manage optional delivery. It starts disabled and does not enqueue old alerts retroactively. Created alerts and new failures reopening reviewed alerts enqueue atomically. One flush handles only its initial bounded snapshot; later findings remain pending. Pending notices and their alert evidence survive cleanup. Fake-endpoint tests establish retries, rate limits, grouped messages and ambiguous outcomes; actual Discord delivery remains unverified. See [delivery design](discord-delivery-design.md).

Live monitor status includes its selected manager and fixed service metadata. CLI start/stop requests use noninteractive systemctl only after owner/release/state/command identity checks; unavailable authorization returns exit 77 and browser HTTP 503 with console instructions. No privilege policy or sudo credential is added. Fixtures remain independent of installed services.
