"""Single-process localhost demo UI over the existing ClipTrail application modules."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path, PurePosixPath
import secrets
import threading
from urllib.parse import quote, unquote, urlsplit
import webbrowser

from .backends import make_backend
from .indexer import index_video
from .playback import open_result, playback_source
from .search import search
from .store import IndexStore
from .video import VIDEO_EXTENSIONS, discover

ASSETS = Path(__file__).resolve().parent / 'web_assets'
MAX_UPLOAD_BYTES = 4 * 1024**3
MAX_JSON_BYTES = 64 * 1024


class AppRuntime:
    """One backend for the full server lifetime; database connections are thread-local."""

    def __init__(self, db_path, backend_name='cpu', backend_factory=make_backend):
        self.db_path = Path(db_path).expanduser().resolve()
        with IndexStore(self.db_path):
            pass
        self.backend_name = backend_name
        self.backend = backend_factory(backend_name)
        self.token = secrets.token_urlsafe(24)
        self.lock = threading.Lock()
        self.inference_lock = threading.Lock()
        self.state = {'phase': 'ready', 'message': 'Ready', 'completed': 0,
                      'total': 0, 'current': None, 'stage': None,
                      'progress_count': 0, 'progress_total': None,
                      'indexed': [], 'errors': [], 'last_query_ms': None}
        self.worker = None

    def _update(self, **items):
        with self.lock:
            self.state.update(items)

    def snapshot(self):
        with self.lock:
            state = dict(self.state)
            state['indexed'] = list(self.state['indexed'])
            state['errors'] = list(self.state['errors'])
        with IndexStore(self.db_path) as store:
            videos = [v for v in store.videos() if v['backend_identity'] == self.backend.identity]
            disk_bytes = store.disk_bytes()
        return {'state': state, 'videos': videos, 'index_disk_bytes': disk_bytes,
                'backend': self.backend_name, 'backend_label': self.backend.label,
                'backend_identity': self.backend.identity, 'npu_verified': False}

    def start_index(self, paths):
        found = []
        for path in paths:
            found.extend(discover(path))
        unique = list(dict.fromkeys(found))
        if not unique:
            raise ValueError('No videos selected')
        with self.lock:
            if self.state['phase'] != 'ready':
                raise RuntimeError('Finish the current indexing or search operation first')
            self.state.update(phase='indexing', message='Preparing video index',
                              completed=0, total=len(unique), current=None,
                              stage='preparing', progress_count=0,
                              progress_total=None, indexed=[], errors=[])
        self.worker = threading.Thread(target=self._index_all, args=(unique,), daemon=True)
        self.worker.start()
        return {'accepted': len(unique)}

    def _index_all(self, videos):
        indexed, errors = [], []
        for number, path in enumerate(videos, 1):
            self._update(current=path.name, message=f'Indexing {path.name}',
                         stage='hash', progress_count=0, progress_total=None)

            def progress(stage, count, value, duration):
                self._update(stage=stage, progress_count=count,
                             progress_total=value if stage in {'extract', 'embed'} else None,
                             message=(f'{stage.title()} {path.name}: {count}' +
                                      (f' / {value}' if stage in {'extract', 'embed'} else
                                       f' frames, {value:.1f}s' if stage == 'decode' else '')))

            try:
                with self.inference_lock, IndexStore(self.db_path) as store:
                    indexed.append(index_video(store, self.backend, path, progress))
            except Exception as exc:
                errors.append({'filename': path.name, 'error': f'{type(exc).__name__}: {exc}'})
            self._update(completed=number, indexed=list(indexed), errors=list(errors))
        self._update(phase='ready', current=None, stage='complete',
                     message=(f'Indexed {len(indexed)} / {len(videos)} videos' if not errors
                              else f'Completed with {len(errors)} error(s)'))

    def query(self, text, limit=8):
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Enter a natural-language query')
        if not isinstance(limit, int) or not 1 <= limit <= 50:
            raise ValueError('Result limit must be from 1 to 50')
        with self.lock:
            if self.state['phase'] != 'ready':
                raise RuntimeError('Finish the current operation before searching')
            self.state.update(phase='searching', message='Searching local index')
        try:
            with self.inference_lock, IndexStore(self.db_path) as store:
                results, timing = search(store, self.backend, text, limit,
                                         materialize_thumbnails=False)
            for result in results:
                result['thumbnail_url'] = f'/api/thumbnail/{result["result_id"]}?token={quote(self.token)}'
            return {'results': results, 'timing': timing, 'npu_verified': False}
        finally:
            self._update(phase='ready', message='Ready',
                         last_query_ms=timing['query_ms'] if 'timing' in locals() else None)

    def upload_path(self, relative):
        relative = unquote(relative)
        parts = PurePosixPath(relative).parts
        if not parts or any(p in {'', '.', '..'} for p in parts) or relative.startswith('/') or any(
                c in relative for c in ('\\', ':', '\x00')):
            raise ValueError('Unsafe upload filename')
        if Path(parts[-1]).suffix.casefold() not in VIDEO_EXTENSIONS:
            raise ValueError('Unsupported video extension')
        root = self.db_path.parent / 'uploads'
        output = root.joinpath(*parts)
        if not output.resolve().is_relative_to(root.resolve()):
            raise ValueError('Unsafe upload path')
        output.parent.mkdir(parents=True, exist_ok=True)
        return output


def parse_range(value, size):
    if not value:
        return 0, size - 1, False
    if not value.startswith('bytes=') or ',' in value:
        raise ValueError('Unsupported byte range')
    first, sep, last = value[6:].partition('-')
    if not sep:
        raise ValueError('Invalid byte range')
    if first:
        start = int(first)
        end = min(size - 1, int(last)) if last else size - 1
    else:
        if not last or int(last) <= 0:
            raise ValueError('Invalid suffix range')
        start, end = max(0, size - int(last)), size - 1
    if start < 0 or start >= size or end < start:
        raise ValueError('Range is outside video')
    return start, end, True


def make_handler(runtime):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'ClipTrailLocal/1'

        def _send(self, code, data, content_type, *, headers=None, head=False):
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            if not head:
                self.wfile.write(data)

        def _json(self, code, value):
            self._send(code, json.dumps(value, allow_nan=False).encode(), 'application/json; charset=utf-8')

        def _error(self, code, error):
            self._json(code, {'error': str(error)})

        def _authorized(self, media=False):
            path = urlsplit(self.path)
            if media:
                from urllib.parse import parse_qs
                return parse_qs(path.query).get('token') == [runtime.token]
            return self.headers.get('X-ClipTrail-Token') == runtime.token

        def _read_json(self):
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_JSON_BYTES:
                raise ValueError('Invalid JSON request size')
            value = json.loads(self.rfile.read(size))
            if not isinstance(value, dict):
                raise ValueError('Expected a JSON object')
            return value

        def _media(self, head=False):
            if not self._authorized(media=True):
                self._error(403, 'Forbidden')
                return
            path = urlsplit(self.path).path
            kind, _, raw_id = path.removeprefix('/api/').partition('/')
            try:
                result_id = int(raw_id)
                with IndexStore(runtime.db_path) as store:
                    if kind == 'thumbnail':
                        row = store.result(result_id)
                        if row is None:
                            raise KeyError('Unknown result')
                        self._send(200, row['thumbnail'], 'image/jpeg', head=head)
                        return
                    row, video = playback_source(store, result_id)
                size = video.stat().st_size
                start, end, partial = parse_range(self.headers.get('Range'), size)
                length = end - start + 1
                self.send_response(206 if partial else 200)
                self.send_header('Content-Type', mimetypes.guess_type(video.name)[0] or 'application/octet-stream')
                self.send_header('Content-Length', str(length))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                if partial:
                    self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
                self.end_headers()
                if head:
                    return
                with video.open('rb') as source:
                    source.seek(start)
                    remaining = length
                    while remaining:
                        block = source.read(min(1024 * 1024, remaining))
                        if not block:
                            break
                        self.wfile.write(block)
                        remaining -= len(block)
            except (KeyError, FileNotFoundError, ValueError) as exc:
                self._error(404 if isinstance(exc, (KeyError, FileNotFoundError)) else 416, exc)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_HEAD(self):
            path = urlsplit(self.path).path
            if path.startswith('/api/video/') or path.startswith('/api/thumbnail/'):
                return self._media(head=True)
            self._error(404, 'Not found')

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/':
                page = (ASSETS / 'index.html').read_text().replace('__TOKEN__', runtime.token)
                return self._send(200, page.encode(), 'text/html; charset=utf-8',
                                  headers={'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; media-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'"})
            if path in {'/app.js', '/style.css'}:
                content_type = 'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8'
                return self._send(200, (ASSETS / path[1:]).read_bytes(), content_type)
            if path.startswith('/api/video/') or path.startswith('/api/thumbnail/'):
                return self._media()
            if path == '/api/status':
                if not self._authorized():
                    return self._error(403, 'Forbidden')
                return self._json(200, runtime.snapshot())
            self._error(404, 'Not found')

        def do_PUT(self):
            if not self._authorized():
                return self._error(403, 'Forbidden')
            path = urlsplit(self.path).path
            if not path.startswith('/api/upload/'):
                return self._error(404, 'Not found')
            try:
                with runtime.lock:
                    if runtime.state['phase'] != 'ready':
                        raise RuntimeError('Finish the current operation before adding files')
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= MAX_UPLOAD_BYTES:
                    raise ValueError('Invalid upload size')
                output = runtime.upload_path(path.removeprefix('/api/upload/'))
                temp = output.with_name(output.name + '.uploading')
                try:
                    with temp.open('wb') as handle:
                        remaining = size
                        while remaining:
                            block = self.rfile.read(min(1024 * 1024, remaining))
                            if not block:
                                raise ValueError('Incomplete upload')
                            handle.write(block)
                            remaining -= len(block)
                    temp.replace(output)
                finally:
                    temp.unlink(missing_ok=True)
                return self._json(200, {'path': str(output), 'bytes': size})
            except (ValueError, OSError, RuntimeError) as exc:
                return self._error(409 if isinstance(exc, RuntimeError) else 400, exc)

        def do_POST(self):
            if not self._authorized():
                return self._error(403, 'Forbidden')
            path = urlsplit(self.path).path
            try:
                payload = self._read_json()
                if path == '/api/index':
                    paths = payload.get('paths')
                    if not isinstance(paths, list) or not paths or len(paths) > 100 or not all(
                            isinstance(p, str) and p for p in paths):
                        raise ValueError('Choose a video or folder')
                    return self._json(202, runtime.start_index(paths))
                if path == '/api/search':
                    return self._json(200, runtime.query(payload.get('text'), payload.get('limit', 8)))
                if path == '/api/open':
                    with IndexStore(runtime.db_path) as store:
                        return self._json(200, open_result(store, int(payload['result_id']), payload.get('player')))
                return self._error(404, 'Not found')
            except (ValueError, KeyError, RuntimeError, FileNotFoundError, TypeError) as exc:
                return self._error(409 if isinstance(exc, RuntimeError) else 400, exc)

        def log_message(self, format, *args):
            message = (format % args).replace(runtime.token, '[local token]')
            print(f'ClipTrail local: {self.address_string()} ' + message, flush=True)

    return Handler


def run_server(db_path, backend='cpu', port=8765, open_browser=True, backend_factory=make_backend):
    runtime = AppRuntime(db_path, backend, backend_factory)
    server = ThreadingHTTPServer(('127.0.0.1', port), make_handler(runtime))
    server.daemon_threads = True
    url = f'http://127.0.0.1:{server.server_port}/'
    print(f'ClipTrail local application: {url} ({runtime.backend.label})', flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    finally:
        server.server_close()
