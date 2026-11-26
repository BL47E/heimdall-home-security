#!/usr/bin/env python3
"""Read local SSH transport and login observations without changing them."""
import ipaddress
import json
from pathlib import Path
import subprocess


def execute(*args):
    return subprocess.run(args, capture_output=True, text=True, timeout=2, check=True).stdout


def ssh_connections(cli):
    result = {"status": "available", "message": "Established TCP connections to local SSH port 22.", "active": [], "history": []}
    try:
        output = execute("ss", "-H", "-tn", "state", "established", "( sport = :22 )")
        for line in output.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            address = parts[-1].rsplit(":", 1)[0].strip("[]").split("%", 1)[0]
            try:
                address = str(ipaddress.ip_address(address))
            except ValueError:
                continue
            result["active"].append({"address": address})
    except (OSError, subprocess.SubprocessError):
        result["status"] = "unavailable"
        result["message"] = "Current SSH connections unavailable. Linux ss is required."
    try:
        events = json.loads(execute(cli, "events", "--all"))
        if not isinstance(events, list):
            raise ValueError("Invalid SSH event data")
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get("outcome") != "success" or event.get("provenance") != "journal":
                continue
            source, user = event.get("source_ip"), event.get("username")
            if not source:
                continue
            result["history"].append({"address": source, "username": user, "timestamp": event.get("timestamp")})
        result["history"].sort(key=lambda item: item["timestamp"] if isinstance(item["timestamp"], (int, float)) else float("-inf"), reverse=True)
    except (OSError, ValueError, subprocess.SubprocessError):
        result["history_message"] = "Recorded SSH logins unavailable."
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps({"ssh": ssh_connections(str(root / "bin/heimdall"))}))
