"""Local HTTP application flow with an actual loopback server and fixture media."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from cliptrail_app.web import AppRuntime, ThreadingHTTPServer, make_handler
from test_application import SimpleBackend, write_video


class WebApplicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original = self.root / 'original.mp4'
        write_video(self.original)
        self.created = []

        def factory(name):
            self.created.append(name)
            return SimpleBackend()

        self.runtime = AppRuntime(self.root / 'index.sqlite3', 'cpu', factory)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.runtime))
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        if self.runtime.worker:
            self.runtime.worker.join(5)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        self.tmp.cleanup()

    def request(self, path, method='GET', data=None, token=True, extra=None):
        headers = {'X-ClipTrail-Token': self.runtime.token} if token else {}
        if extra: headers.update(extra)
        req = Request(self.base + path, data=data, headers=headers, method=method)
        with urlopen(req, timeout=8) as response:
            return response.status, dict(response.headers), response.read()

    def post(self, path, data):
        return json.loads(self.request(path, 'POST', json.dumps(data).encode(),
                                       extra={'Content-Type': 'application/json'})[2])

    def test_upload_index_search_playback_and_restart(self):
        status, _, page = self.request('/', token=False)
        self.assertEqual(status, 200)
        self.assertIn(self.runtime.token.encode(), page)
        with self.assertRaises(HTTPError) as forbidden:
            self.request('/api/status', token=False)
        self.assertEqual(forbidden.exception.code, 403)
        body = self.original.read_bytes()
        uploaded = json.loads(self.request('/api/upload/demo/video.mp4', 'PUT', body)[2])
        self.assertEqual(Path(uploaded['path']).read_bytes(), body)
        with self.assertRaises(HTTPError) as traversal:
            self.request('/api/upload/%2e%2e/escape.mp4', 'PUT', body)
        self.assertEqual(traversal.exception.code, 400)
        entered, release = threading.Event(), threading.Event()
        original_encode = self.runtime.backend.encode_image

        def gated_encode(path):
            entered.set()
            if not release.wait(5):
                raise TimeoutError('Test indexing gate timed out')
            return original_encode(path)

        with mock.patch.object(self.runtime.backend, 'encode_image', side_effect=gated_encode):
            self.assertEqual(self.post('/api/index', {'paths': [uploaded['path']]}), {'accepted': 1})
            self.assertTrue(entered.wait(5))
            active = json.loads(self.request('/api/status')[2])
            self.assertEqual(active['state']['phase'], 'indexing')
            self.assertEqual(active['state']['stage'], 'extract')
            with self.assertRaises(HTTPError) as busy:
                self.post('/api/search', {'text': 'red'})
            self.assertEqual(busy.exception.code, 409)
            release.set()
            self.runtime.worker.join(8)
        current = json.loads(self.request('/api/status')[2])
        self.assertEqual(current['state']['phase'], 'ready')
        self.assertEqual(current['state']['completed'], 1)
        self.assertEqual(current['backend_label'], SimpleBackend.label)
        self.assertFalse(current['npu_verified'])
        self.assertEqual(current['videos'][0]['selected_frames'], 16)
        first = self.post('/api/search', {'text': 'red', 'limit': 3})
        second = self.post('/api/search', {'text': 'blue', 'limit': 3})
        self.assertEqual(self.created, ['cpu'])
        self.assertEqual(first['results'][0]['filename'], 'video.mp4')
        self.assertTrue(first['results'][0]['thumbnail_url'].startswith('/api/thumbnail/'))
        self.assertGreater(second['timing']['query_ms'], 0)
        result_id = first['results'][0]['result_id']
        status, headers, thumbnail = self.request(first['results'][0]['thumbnail_url'], token=False)
        self.assertEqual((status, headers['Content-Type']), (200, 'image/jpeg'))
        self.assertTrue(thumbnail.startswith(b'\xff\xd8'))
        video_path = f'/api/video/{result_id}?token={self.runtime.token}'
        status, headers, sample = self.request(video_path, token=False,
                                                extra={'Range': 'bytes=0-31'})
        self.assertEqual(status, 206)
        self.assertEqual(headers['Content-Range'], f'bytes 0-31/{len(body)}')
        self.assertEqual(sample, body[:32])
        with self.assertRaises(HTTPError) as invalid_range:
            self.request(video_path, token=False, extra={'Range': 'bytes=999999999-'})
        self.assertEqual(invalid_range.exception.code, 416)
        with mock.patch('cliptrail_app.playback.webbrowser.open', return_value=False):
            opened = self.post('/api/open', {'result_id': result_id, 'player': 'browser'})
        self.assertEqual(opened['timestamp_s'], first['results'][0]['timestamp_s'])
        self.assertIn('video.currentTime=', Path(opened['viewer']).read_text())
        restarted = AppRuntime(self.root / 'index.sqlite3', 'cpu', lambda _: SimpleBackend())
        self.assertEqual(len(restarted.snapshot()['videos']), 1)
        self.assertEqual(restarted.query('red', 3)['results'][0]['result_id'], result_id)
