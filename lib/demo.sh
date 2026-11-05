#!/bin/bash
# Synthetic examples never touch the owner's live data directory.
set -eu
umask 077
ROOT=$(cd "$(dirname "$0")/.." && pwd)
HEIMDALL_DATA_DIR=$(mktemp -d "${TMPDIR:-/tmp}/heimdall-demo.XXXXXXXX")
export HEIMDALL_DATA_DIR
CLI=$ROOT/bin/heimdall
printf '%s\n' 'Heimdall synthetic demonstration — no SSH connections or blocks are performed.'
printf 'Separate demonstration state: %s\n\n' "$HEIMDALL_DATA_DIR"
head -n 3 "$ROOT/tests/fixtures/password-burst.jsonl" | "$CLI" ingest - >/dev/null
printf 'After three failures: %s alerts (expected 0).\n' "$("$CLI" alerts | jq length)"
sed -n '4p' "$ROOT/tests/fixtures/password-burst.jsonl" | "$CLI" ingest - >/dev/null
printf 'After the fourth: %s alert (expected 1).\n' "$("$CLI" alerts | jq length)"
id=$("$CLI" alerts | jq -r '.[0].id')
"$CLI" review "$id" >/dev/null
printf '%s\n' 'Owner review recorded. No access restrictions were changed.'
sed -n '5p' "$ROOT/tests/fixtures/password-burst.jsonl" | "$CLI" ingest - >/dev/null
printf 'Following successful login: %s preceding matching failures in these samples.\n' "$("$CLI" events | jq '.[0].preceding_failures')"
head -n 1 "$ROOT/tests/fixtures/password-burst.jsonl" | jq -c '.__CURSOR="synthetic:demo:6" | .__REALTIME_TIMESTAMP="1793790120000000"' | "$CLI" ingest - >/dev/null
printf 'New failure reopens the active alert: %s.\n' "$("$CLI" inspect "$id" | jq -r '.review_status')"
"$CLI" report "$id"
printf '\nSynthetic data is retained only in %s\n' "$HEIMDALL_DATA_DIR"
