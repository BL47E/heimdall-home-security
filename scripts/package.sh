#!/bin/bash
# Package allowlisted source and fixtures; never include local records or tokens.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
exec python3 - "$ROOT" "${1:-$ROOT/dist}" <<'PY'
import hashlib
from pathlib import Path
import sys
import tarfile
import tempfile

root, output = map(Path, sys.argv[1:])
version = (root / "VERSION").read_text().strip()
output.mkdir(parents=True, exist_ok=True)
archive = output / ("heimdall-" + version + ".tar.gz")
# Exact release contents. Extra files in source directories may hold private data.
paths = """
VERSION
README.md
scripts/install-cli.sh
docs/runbook.md
docs/runtime-contract.md
bin/heimdall
deploy/heimdall-cleanup.service.in
deploy/heimdall-cleanup.timer.in
deploy/heimdall-discord.service.in
deploy/heimdall-discord.timer.in
deploy/heimdall-monitor.service.in
docs/adr/0001-home-first-local-first.md
docs/adr/0002-shell-first-college-milestone.md
docs/adr/0003-shell-monitor-with-local-dashboard.md
lib/demo.sh
lib/discord.sh
lib/discord_http.py
lib/discord_state.sh
lib/lock.py
lib/monitor.sh
lib/normalize.py
lib/notifications.jq
lib/parse.jq
lib/rules.jq
lib/service.py
lib/tui.py
lib/virustotal.py
tests/fixtures/README.md
tests/fixtures/password-burst.jsonl
tests/fixtures/ubuntu-password-sanitized.jsonl
tests/test_discord.py
tests/test_monitor.py
tests/test_monitor.sh
tests/test_retention_schedule.py
tests/test_service.py
tests/test_tui.py
tests/test_virustotal.py
tests/test_web.py
web/server.py
web/static/app.js
web/static/fonts/JetBrainsMono-Medium.woff2
web/static/fonts/JetBrainsMono-Regular.woff2
web/static/fonts/OFL.txt
web/static/index.html
web/static/style.css
""".split()
with tempfile.TemporaryDirectory(dir=output) as staging:
    staged = Path(staging) / archive.name
    with tarfile.open(staged, "w:gz") as tar:
        for entry in paths:
            file = root / entry
            if not file.is_file() or file.resolve() != root.resolve() / entry:
                raise SystemExit("Missing or linked package input: " + entry)
            tar.add(file, arcname="heimdall-" + version + "/" + entry, recursive=False)
    staged.replace(archive)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
checksum = archive.with_name(archive.name + ".sha256")
checksum.write_text(digest + "  " + archive.name + "\n")
print(archive)
print("SHA256 " + digest)
PY
