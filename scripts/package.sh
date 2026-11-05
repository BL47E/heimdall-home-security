#!/bin/bash
# Package allowlisted source and fixtures; never include local records or tokens.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
exec python3 - "$ROOT" "${1:-$ROOT/dist}" <<'PY'
import hashlib
from pathlib import Path
import sys
import tarfile

root, output = map(Path, sys.argv[1:])
version = (root / "VERSION").read_text().strip()
output.mkdir(parents=True, exist_ok=True)
archive = output / ("heimdall-" + version + ".tar.gz")
paths = [
    "VERSION",
    "README.md",
    "bin",
    "lib",
    "web",
    "tests",
    "deploy",
    "docs/runbook.md",
    "docs/runtime-contract.md",
    "docs/adr",
]
with tarfile.open(archive, "w:gz") as tar:
    for entry in paths:
        candidate = root / entry
        files = sorted(candidate.rglob("*")) if candidate.is_dir() else [candidate]
        for file in files:
            if "__pycache__" in file.parts or file.suffix in (".pyc", ".pyo"):
                continue
            if file.is_symlink():
                raise SystemExit("Refusing to package a symlink: " + str(file))
            if file.is_file():
                tar.add(
                    file,
                    arcname="heimdall-" + version + "/" + str(file.relative_to(root)),
                    recursive=False,
                )
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
checksum = archive.with_name(archive.name + ".sha256")
checksum.write_text(digest + "  " + archive.name + "\n")
print(archive)
print("SHA256 " + digest)
PY
