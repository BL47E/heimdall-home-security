"""HTTP integration checks against the actual shell CLI and disposable state."""
import http.client
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('webserver', ROOT / 'web/server.py')
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)


class WebTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / 'data'
        self.server = web.Server(('127.0.0.1', 0), ROOT / 'bin/heimdall', self.data)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host = '127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=15)
        connection.request(method, path, body, {'Host': self.host, **(headers or {})})
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def login(self):
        status, headers, body = self.request('POST', '/api/login', json.dumps({'token': self.server.token}),
                                             {'Origin': 'http://' + self.host, 'Content-Type': 'application/json'})
        self.assertEqual(status, 200)
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Strict', headers['Set-Cookie'])
        cookie = headers['Set-Cookie'].split(';')[0]
        csrf = json.loads(body)['csrf']
        return {'Cookie': cookie, 'Origin': 'http://' + self.host, 'Content-Type': 'application/json', 'X-CSRF-Token': csrf}

    def ingest(self):
        result = subprocess.run([str(ROOT / 'bin/heimdall'), 'ingest', str(ROOT / 'tests/fixtures/password-burst.jsonl')],
                                env={**os.environ, 'HEIMDALL_DATA_DIR': str(self.data)}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_real_cli_status_config_and_persistence(self):
        headers = self.login()
        self.assertEqual(self.request('GET', '/api/status')[0], 401)
        status, _, body = self.request('GET', '/api/status', headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['monitor']['coverage'], 'unavailable')
        status, _, body = self.request('POST', '/api/config', '{"threshold":5}', headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['threshold'], 5)
        self.assertEqual(json.loads((self.data / 'state.json').read_text())['config']['threshold'], 5)
        self.assertEqual(self.request('GET', '/api/config', headers=headers)[0], 200)
        self.assertEqual(self.data.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.data / 'web-token').stat().st_mode & 0o777, 0o600)

    def test_real_alert_review_reopen_and_report(self):
        self.ingest()
        headers = self.login()
        status, _, body = self.request('GET', '/api/alerts', headers=headers)
        self.assertEqual(status, 200)
        alerts = json.loads(body)
        self.assertEqual(len(alerts), 1)
        alert_id = alerts[0]['id']
        status, _, body = self.request('GET', '/api/alerts/' + alert_id, headers=headers)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(json.loads(body)['events']), 4)
        for action, expected in [('review', 'reviewed'), ('reopen', 'needs_review')]:
            status, _, body = self.request('POST', f'/api/alerts/{alert_id}/{action}', '{}', headers)
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)['review_status'], expected)
        status, response_headers, body = self.request('GET', f'/api/alerts/{alert_id}/report', headers=headers)
        self.assertEqual(status, 200)
        self.assertIn('attachment', response_headers['Content-Disposition'])
        self.assertIn(b'Heimdall investigation', body)
        self.assertIn(b'fixture', body)
        status, _, body = self.request('GET', '/api/events', headers=headers)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(json.loads(body)), 4)

    def test_host_origin_csrf_and_static_path_guards(self):
        headers = self.login()
        self.assertEqual(self.request('GET', '/', headers={'Host': 'evil.example'})[0], 400)
        self.assertEqual(self.request('POST', '/api/config', '{}', {**headers, 'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.request('POST', '/api/config', '{}', {**headers, 'X-CSRF-Token': 'wrong'})[0], 403)
        self.assertEqual(self.request('POST', '/api/config', '{}', {**headers, 'X-CSRF-Token': chr(233)})[0], 403)
        for path in ['/../bin/heimdall', '/%2e%2e/bin/heimdall', '//etc/passwd', '/api/status?token=x']:
            self.assertEqual(self.request('GET', path, headers=headers)[0], 404, path)
        status, response_headers, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn('frame-ancestors', response_headers['Content-Security-Policy'])
        self.assertNotIn(self.server.token.encode(), body)

    def test_page_routes_and_guards(self):
        pages = ['/', '/overview', '/investigations', '/activity', '/settings']
        shell = None
        for path in pages:
            with self.subTest(path=path):
                status, headers, body = self.request('GET', path)
                self.assertEqual(status, 200)
                self.assertEqual(headers['Content-Type'], 'text/html; charset=utf-8')
                self.assertEqual(headers['Cache-Control'], 'no-store, private')
                self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
                self.assertEqual(headers['X-Frame-Options'], 'DENY')
                self.assertEqual(headers['Referrer-Policy'], 'no-referrer')
                self.assertIn('frame-ancestors', headers['Content-Security-Policy'])
                self.assertIn(b'<html', body.lower())
                self.assertNotIn(self.server.token.encode(), body)
                if shell is None: shell = body
                self.assertEqual(body, shell)
                self.assertEqual(self.request('GET', path, headers={'Host': 'evil.example'})[0], 400)
        headers = self.login()
        for path in ['/missing', '/overview/', '/Overview', '/overview?x=1', '/overview#ignored', '/%6fverview',
                     '//overview', '/activity//', '/static/index.html', '/web-token', '/state.json',
                     '/fonts/unknown.woff2', '/fonts/JetBrainsMono-Regular.woff2#ignored',
                     'http://elsewhere.example/overview']:
            with self.subTest(path=path):
                self.assertEqual(self.request('GET', path, headers=headers)[0], 404)
        for path in pages:
            self.assertEqual(self.request('POST', path, '{}', headers)[0], 404, path)

    def test_evidence_endpoints_require_session(self):
        for path in ['/api/status', '/api/alerts', '/api/events', '/api/config',
                     '/api/alerts/example', '/api/alerts/example/report']:
            with self.subTest(path=path):
                self.assertEqual(self.request('GET', path)[0], 401)

    def test_allowlisted_fonts(self):
        for weight in ['Regular', 'Medium']:
            path = f'/fonts/JetBrainsMono-{weight}.woff2'
            with self.subTest(path=path):
                status, headers, body = self.request('GET', path)
                self.assertEqual(status, 200)
                self.assertEqual(headers['Content-Type'], 'font/woff2')
                self.assertEqual(headers['Cache-Control'], 'no-store, private')
                self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
                self.assertTrue(body.startswith(b'wOF2'))
                self.assertNotIn(self.server.token.encode(), body)

    def test_configuration_rejection_does_not_mutate_state(self):
        headers = self.login()
        before = (self.data / 'state.json').read_bytes()
        for patch in [{'threshold': True}, {'threshold': 4.5}, {'threshold': '4'}, {'threshold': 1},
                      {'window_seconds': 0}, {'retention_days': 366}, {'shell': 'echo bad'}, {}]:
            self.assertEqual(self.request('POST', '/api/config', json.dumps(patch), headers)[0], 400, patch)
        self.assertEqual(self.request('POST', '/api/config', ' ' * 16385, headers)[0], 400)
        self.assertEqual(self.request('POST', '/api/config', '{broken', headers)[0], 400)
        self.assertEqual(self.request('POST', '/api/config', '{}', {**headers, 'Content-Type': 'text/plain'})[0], 400)
        self.assertEqual((self.data / 'state.json').read_bytes(), before)

    def test_login_limit_logout_and_expiry(self):
        headers = self.login()
        self.assertTrue(json.loads(self.request('GET', '/api/session', headers=headers)[2])['authenticated'])
        self.assertEqual(self.request('POST', '/api/logout', '{}', headers)[0], 200)
        self.assertEqual(self.request('GET', '/api/config', headers=headers)[0], 401)
        headers = self.login()
        session_id = headers['Cookie'].split('=', 1)[1]
        self.server.sessions[session_id]['expires'] = 0
        self.assertEqual(self.request('GET', '/api/config', headers=headers)[0], 401)
        for index in range(6):
            status = self.request('POST', '/api/login', '{"token":"wrong"}',
                                  {'Origin': 'http://' + self.host, 'Content-Type': 'application/json'})[0]
            self.assertEqual(status, 401 if index < 5 else 429)

    def test_cli_failure_is_visible_not_empty_success(self):
        headers = self.login()
        (self.data / 'state.json').write_text('{broken')
        status, _, body = self.request('GET', '/api/alerts', headers=headers)
        self.assertEqual(status, 503)
        self.assertIn('error', json.loads(body))
        self.assertEqual((self.data / 'state.json').read_text(), '{broken')


if __name__ == '__main__':
    unittest.main()
