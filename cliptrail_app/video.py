"""Local 4 Hz video decode and frozen scene-midpoint selection."""
from dataclasses import dataclass
import math
from pathlib import Path

from .legacy import scene_indices

VIDEO_EXTENSIONS = frozenset({'.mp4', '.mov', '.mkv', '.m4v', '.avi', '.webm'})
WINDOW_SECONDS = 60
GRID_HZ = 4
SCENE_BUDGET = 16


@dataclass(frozen=True)
class Candidate:
    pts: int
    t_s: float
    change: float
    window: int


def discover(path):
    source = Path(path).expanduser().resolve()
    if source.is_file():
        if source.suffix.casefold() not in VIDEO_EXTENSIONS:
            raise ValueError(f'Unsupported video extension: {source.suffix}')
        return [source]
    if not source.is_dir():
        raise FileNotFoundError(source)
    videos = sorted(p for p in source.rglob('*') if p.is_file() and p.suffix.casefold() in VIDEO_EXTENSIONS)
    if not videos:
        raise ValueError(f'No supported videos in {source}')
    return videos


def select_candidates(candidates):
    """Run the measured scene selector independently in each minute window."""
    if not candidates:
        raise ValueError('No sampled frames to index')
    by_window = {}
    for candidate in candidates:
        by_window.setdefault(candidate.window, []).append(candidate)
    selected = []
    for window in sorted(by_window):
        frames = by_window[window]
        selected.extend(frames[i] for i in scene_indices([f.change for f in frames], SCENE_BUDGET))
    return sorted(selected, key=lambda f: (f.t_s, f.pts))


def scan(path, progress=None):
    """First pass: exact benchmark-style 4 Hz sample and 96x54 RGB change."""
    import av
    import numpy as np
    from PIL import Image

    candidates = []
    decoded = 0
    previous = None
    previous_window = None
    next_tick = 0.0
    last_time = 0.0
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        origin = float(stream.start_time * stream.time_base) if stream.start_time is not None else None
        metadata_duration = float(container.duration / av.time_base) if container.duration is not None else None
        for frame in container.decode(stream):
            decoded += 1
            if frame.pts is None:
                raise ValueError(f'Missing presentation timestamp in {path}')
            stamp = float(frame.pts * frame.time_base)
            if origin is None:
                origin = stamp
            t_s = stamp - origin
            if t_s < -1e-8:
                continue
            last_time = max(last_time, t_s)
            if t_s + 1e-8 < next_tick:
                continue
            window = int(t_s // WINDOW_SECONDS)
            if window != previous_window:
                previous = None
                previous_window = window
            rgb = frame.to_image().convert('RGB')
            thumb = np.asarray(rgb.resize((96, 54), Image.Resampling.BILINEAR), dtype=np.float32)
            change = 0.0 if previous is None else float(np.abs(thumb - previous).mean() / 255.0)
            previous = thumb
            candidates.append(Candidate(int(frame.pts), t_s, change, window))
            next_tick = (math.floor(t_s * GRID_HZ + 1e-8) + 1) / GRID_HZ
            if progress and len(candidates) % 16 == 0:
                progress('decode', len(candidates), t_s, metadata_duration)
    if not candidates:
        raise ValueError(f'No decodable video frames in {path}')
    # Container duration may include non-video streams; retain the observed video end.
    duration = max(last_time, candidates[-1].t_s) + 1 / GRID_HZ
    if progress:
        progress('decode', len(candidates), duration, metadata_duration)
    return candidates, duration, decoded


def extract_selected(path, selected, output, progress=None):
    """Second pass: write only selected source frames at their actual PTS."""
    import av

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    needed = {c.pts: (i, c) for i, c in enumerate(selected)}
    saved = {}
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        for frame in container.decode(stream):
            if frame.pts not in needed:
                continue
            i, candidate = needed[frame.pts]
            image_path = output / f'{i:06d}.jpg'
            # Match frozen preparation: RGB JPEG quality 95, no chroma subsampling.
            frame.to_image().convert('RGB').save(image_path, quality=95, subsampling=0)
            saved[i] = (candidate, image_path)
            if progress:
                progress('extract', len(saved), len(selected), None)
            if len(saved) == len(selected):
                break
    if len(saved) != len(selected):
        raise RuntimeError(f'Only extracted {len(saved)}/{len(selected)} selected frames from {path}')
    return [saved[i] for i in range(len(selected))]
