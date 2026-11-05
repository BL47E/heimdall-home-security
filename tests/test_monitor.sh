#!/bin/bash
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
HEIMDALL_DATA_DIR=$(mktemp -d)
trap 'rm -rf "$HEIMDALL_DATA_DIR"' EXIT
export HEIMDALL_DATA_DIR
CLI=$ROOT/bin/heimdall
fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}
"$CLI" init | jq -e '.threshold == 4 and .window_seconds == 300 and .retention_days == 60' >/dev/null || fail defaults
"$CLI" config set '{"threshold":2,"window_seconds":3600}' | jq -e '.threshold == 2 and .window_seconds == 3600' >/dev/null || fail config
for p in '{"threshold":1}' '{"threshold":2.5}' '{"threshold":true}' '{"threshold":"4"}' '{"unknown":1}' '{"retention_days":366}'; do
  if "$CLI" config set "$p" >/dev/null 2>&1; then fail "accepted $p"; fi
done
"$CLI" config get | jq -e '.threshold == 2 and .window_seconds == 3600' >/dev/null || fail 'invalid patch changed state'
"$CLI" status | jq -e '.monitor.coverage == "unavailable" and .providers.discord == "not_implemented"' >/dev/null || fail status
python3 "$ROOT/tests/test_monitor.py"
printf '%s\n' 'PASS: shell state/configuration and monitor scenario tests'
