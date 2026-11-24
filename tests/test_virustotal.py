"""Verify IP disclosure gates and lookup semantics without contacting VirusTotal."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('virustotal', ROOT / 'lib/virustotal.py')
vt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vt)


class VirusTotalTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.data = Path(directory.name)

    def cli(self, *args, input=None, success=True):
        result = subprocess.run([str(ROOT / 'bin/heimdall'), *args],
                                input=input, text=True, capture_output=True, timeout=10,
                                env={**os.environ, 'HEIMDALL_DATA_DIR': str(self.data)})
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result.stdout

    def test_private_and_special_addresses_never_reach_transport(self):
        self.cli('virustotal', 'configure', input='test-key\n')
        self.assertEqual((self.data / 'virustotal-key').stat().st_mode & 0o777, 0o600)
        with patch.object(vt, 'fetch') as fetch:
            for ip in ('10.37.129.4', '100.64.0.1', '127.0.0.1', '192.0.0.9', '192.0.2.1',
                       '224.0.0.1', '::1', 'fc00::1', 'fe80::1%en0', '::ffff:8.8.8.8',
                       '2001:db8::1', '2002::1', '3fff::1', 'ff02::1', 'invalid'):
                with self.subTest(ip=ip):
                    self.assertIsNone(vt.lookup(self.data, ip)['flags'])
            fetch.assert_not_called()
        self.assertEqual(vt.eligible_ip('2606:4700:4700:0::1111'), '2606:4700:4700::1111')

    def test_cache_expiry_and_local_quota(self):
        vt.write_private(self.data / 'virustotal-key', 'test-key')
        with patch.object(vt.time, 'time', return_value=200000) as clock, \
             patch.object(vt, 'fetch', return_value=(0, None, 0)) as fetch:
            first = vt.lookup(self.data, '8.8.8.8')
            self.assertEqual(first['label'], 'No flags found')
            clock.return_value += 30
            cached = vt.lookup(self.data, '8.8.8.8')
            self.assertTrue(cached['from_cache'])
            self.assertEqual(cached['checked_at'], first['checked_at'])
            for ip in ('8.8.4.4', '1.0.0.1', '1.1.1.1'):
                vt.lookup(self.data, ip)
            self.assertIsNone(vt.lookup(self.data, '9.9.9.9')['flags'])
            self.assertEqual(fetch.call_count, 4)
            path = self.data / 'virustotal-cache.json'
            store = json.loads(path.read_text())
            store['requests'] = [clock.return_value - 90] * 500
            vt.write_private(path, json.dumps(store))
            self.assertIn('limit', vt.lookup(self.data, '9.9.9.9')['reason'])
            self.assertEqual(fetch.call_count, 4)
            clock.return_value += vt.DAY
            self.assertFalse(vt.lookup(self.data, '8.8.8.8')['from_cache'])
            self.assertEqual(fetch.call_count, 5)

    def test_provider_cooldown_survives_second_lookup(self):
        vt.write_private(self.data / 'virustotal-key', 'test-key')
        with patch.object(vt.time, 'time', return_value=200000) as clock, \
             patch.object(vt, 'fetch', return_value=(None, 'Provider quota reached', 200120)) as fetch:
            self.assertEqual(vt.lookup(self.data, '8.8.8.8')['reason'], 'Provider quota reached')
            clock.return_value = 200119
            self.assertIn('cooldown', vt.lookup(self.data, '1.1.1.1')['reason'])
            self.assertEqual(fetch.call_count, 1)
            clock.return_value = 200120
            vt.lookup(self.data, '1.1.1.1')
            self.assertEqual(fetch.call_count, 2)

    def test_transport_sends_only_ip_and_reads_vendor_counts(self):
        with patch.object(vt, 'HTTPSConnection') as connect:
            response = MagicMock(status=200)
            connect.return_value.getresponse.return_value.__enter__.return_value = response
            stats = {'malicious': 7, 'suspicious': 3}
            report = {'data': {'type': 'ip_address', 'id': '8.8.8.8',
                               'attributes': {'last_analysis_stats': stats}}}
            response.read.return_value = json.dumps(report).encode()
            self.assertEqual(vt.fetch('8.8.8.8', 'test-key'), (10, None, 0))
            connect.assert_called_once_with('www.virustotal.com', timeout=3)
            connect.return_value.request.assert_called_once_with(
                'GET', '/api/v3/ip_addresses/8.8.8.8',
                headers={'Accept': 'application/json', 'x-apikey': 'test-key'})
            del stats['suspicious']
            response.read.return_value = json.dumps(report).encode()
            self.assertIsNone(vt.fetch('8.8.8.8', 'test-key')[0])
            response.status = 302
            self.assertIsNone(vt.fetch('8.8.8.8', 'test-key')[0])
            connect.return_value.getresponse.side_effect = TimeoutError('injected timeout')
            self.assertIsNone(vt.fetch('8.8.8.8', 'test-key')[0])

    def test_cli_scope_and_persistence(self):
        self.assertEqual(json.loads(self.cli('status'))['providers']['virustotal'], 'disabled')
        self.cli('virustotal', 'configure', input='private-test-key\n')
        status = self.cli('virustotal', 'status')
        self.assertNotIn('private-test-key', status)
        self.assertEqual(json.loads(status)['provider_state'], 'configured')
        self.cli('ingest', str(ROOT / 'tests/fixtures/password-burst.jsonl'))
        alert_id = json.loads(self.cli('alerts'))[0]['id']
        self.cli('virustotal', 'lookup', alert_id, success=False)
        for count, label in [(0, 'No flags found'), (1, 'Low concern'), (4, 'Medium concern'),
                             (7, 'High concern'), (10, 'Very high concern')]:
            alert = json.loads(self.cli('virustotal', 'simulate', alert_id, str(count)))
            self.assertEqual(alert['reputation']['label'], label)
            self.assertEqual(alert['severity'], 'HIGH' if count == 10 else 'MEDIUM')
        alert = json.loads(self.cli('review', alert_id))
        self.assertEqual(alert['severity'], 'HIGH')
        self.assertEqual(alert['reputation']['provenance'], 'simulated')
        self.assertIn('Very high concern (simulated)', self.cli('report', alert_id))
        self.assertFalse((self.data / 'virustotal-cache.json').exists())

        # Treat the disposable alert as a journal alert to exercise the other gate.
        path = self.data / 'state.json'
        state = json.loads(path.read_text())
        state['mode'] = 'live'
        state['alerts'][0]['provenance'] = 'journal'
        path.write_text(json.dumps(state))
        self.cli('virustotal', 'simulate', alert_id, '10', success=False)
        result = json.loads(self.cli('virustotal', 'lookup', alert_id))
        self.assertEqual(result['reputation']['label'], 'Unknown')
        self.assertEqual(result['severity'], 'MEDIUM')
        self.assertIn('not eligible', result['reputation']['reason'])
        self.assertFalse((self.data / 'virustotal-cache.json').exists())
        self.cli('virustotal', 'disable')
        self.assertFalse((self.data / 'virustotal-key').exists())
