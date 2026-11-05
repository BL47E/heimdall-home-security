#!/usr/bin/env python3
"""Validate addresses and attach deterministic local IDs; rules live in rules.jq."""
import hashlib
import ipaddress
import json
import sys

for line in sys.stdin:
    event = json.loads(line)
    address = event.get("source_ip")
    try:
        if not address or "%" in address:
            raise ValueError()
        event["source_ip"] = str(ipaddress.ip_address(address))
    except ValueError:
        event["source_ip"] = None
        if address:
            event["notes"].append(
                "Source address could not be interpreted; excluded from the source rule"
            )
    cursor = event.get("cursor")
    event["id"] = hashlib.sha256(
        ("cursor:" + cursor if cursor else "fingerprint:" + line.strip()).encode()
    ).hexdigest()
    if not cursor:
        event["notes"].append(
            "Journal identity unavailable; using a local content fingerprint"
        )
    print(json.dumps(event, separators=(",", ":")))
