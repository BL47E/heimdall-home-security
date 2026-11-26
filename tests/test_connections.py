"""Connection observations use local sources and disclose missing data."""
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("connections", ROOT / "lib/connections.py")
connections = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connections)


class ConnectionTests(unittest.TestCase):
    def test_ssh_active_and_recorded_successes(self):
        events = [
            {"outcome": "success", "provenance": "journal", "source_ip": "10.0.0.1", "username": "alice", "timestamp": 123},
            {"outcome": "success", "provenance": "journal", "source_ip": "10.0.0.1", "username": "alice", "timestamp": 100},
            {"outcome": "success", "provenance": "fixture", "source_ip": "10.0.0.2"},
            {"outcome": "failure", "provenance": "journal", "source_ip": "10.0.0.3"},
        ]
        with patch.object(connections, "execute", side_effect=["0 0 10.0.0.9:22 10.0.0.1:49152\n0 0 [::1]:22 [2001:db8::1]:43000\n", json.dumps(events)]):
            result = connections.ssh_connections("heimdall")
        self.assertEqual([x["address"] for x in result["active"]], ["10.0.0.1", "2001:db8::1"])
        self.assertEqual(result["history"], [{"address": "10.0.0.1", "username": "alice", "timestamp": 123}, {"address": "10.0.0.1", "username": "alice", "timestamp": 100}])

    def test_unavailable_sources(self):
        with patch.object(connections, "execute", side_effect=FileNotFoundError()):
            result = connections.ssh_connections("heimdall")
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("history_message", result)

    def test_history_reads_all_retained_events_and_orders_late_records(self):
        events = [{"outcome": "failure", "provenance": "journal"} for _ in range(220)]
        events += [
            {"outcome": "success", "provenance": "journal", "source_ip": "192.0.2.1", "timestamp": 10},
            {"outcome": "success", "provenance": "journal", "source_ip": "192.0.2.2", "timestamp": 20},
        ]
        with patch.object(connections, "execute", side_effect=["", json.dumps(events)]) as execute:
            result = connections.ssh_connections("heimdall")
        execute.assert_any_call("heimdall", "events", "--all")
        self.assertEqual([item["address"] for item in result["history"]], ["192.0.2.2", "192.0.2.1"])

    def test_timeout_is_unavailable(self):
        with patch.object(connections, "execute", side_effect=subprocess.TimeoutExpired("ss", 2)):
            self.assertEqual(connections.ssh_connections("heimdall")["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
