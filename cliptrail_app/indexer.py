"""Index one local video with atomic persistence."""
import datetime
import io
from pathlib import Path
import tempfile
import time

from PIL import Image

from .backends import normalized_vector
from .legacy import sha256
from .video import extract_selected, scan, select_candidates


def index_video(store, backend, source, progress=None, force=False):
    source = Path(source).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    started = time.perf_counter()
    before = source.stat()
    digest = sha256(source)
    hashed = source.stat()
    if (before.st_size, before.st_mtime_ns) != (hashed.st_size, hashed.st_mtime_ns):
        raise RuntimeError(f'Source video changed while hashing: {source}')
    if not force and store.current(source, backend.identity, digest):
        if progress:
            progress('cached', 0, 0, None)
        return {'path': str(source), 'filename': source.name, 'status': 'cached',
                'source_sha256': digest}
    candidates, duration, decoded = scan(source, progress)
    selected = select_candidates(candidates)
    persisted = []
    with tempfile.TemporaryDirectory(prefix='cliptrail-frames-') as temporary:
        for ordinal, (candidate, path) in enumerate(
                extract_selected(source, selected, temporary, progress), start=1):
            vector = normalized_vector(backend.encode_image(path))
            with Image.open(path) as image:
                preview = image.convert('RGB')
                preview.thumbnail((320, 180), Image.Resampling.BICUBIC)
                buffer = io.BytesIO()
                preview.save(buffer, 'JPEG', quality=85)
            persisted.append((candidate.t_s, candidate.pts, vector, buffer.getvalue()))
            if progress:
                progress('embed', ordinal, len(selected), None)
    elapsed = time.perf_counter() - started
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f'Source video changed during indexing: {source}')
    video_id, logical_bytes = store.replace_video(
        path=source, source_sha256=digest, source_bytes=after.st_size,
        backend_identity=backend.identity, duration_s=duration,
        decoded_frames=decoded, candidate_frames=len(candidates),
        index_elapsed_s=elapsed, frames=persisted,
        indexed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    return {'video_id': video_id, 'path': str(source), 'filename': source.name,
            'status': 'indexed', 'source_sha256': digest, 'duration_s': duration,
            'decoded_frames': decoded, 'candidate_frames': len(candidates),
            'selected_frames': len(selected), 'index_elapsed_s': elapsed,
            'index_s_per_video_min': elapsed / (duration / 60),
            'logical_storage_bytes': logical_bytes,
            'logical_bytes_per_video_min': logical_bytes / (duration / 60)}
