#!/bin/bash
# Supervise the dashboard on the current Tailscale address or loopback.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
exec python3 "$ROOT/lib/dashboard_supervisor.py" "$ROOT/bin/heimdall"
