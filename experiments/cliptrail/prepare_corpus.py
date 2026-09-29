#!/usr/bin/env python3
"""Decode chosen real-video windows; produce annotation contact sheets, no ML.

Spec: {"clips": [{"id":..., "source_id":..., "video": absolute_or_relative_path,
                  "start_s":..., "duration_s":..., "selection_reason":...}]}
Relative video paths are resolved against the spec file. Choose windows before
model inference; inspect sheets and annotate all matching event occurrences.
"""
import argparse
import json
import math
import time
from pathlib import Path
from reference_backend import sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--spec', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    import av
    import numpy as np
    from PIL import Image, ImageDraw
    if a.output.exists():
        raise ValueError('Output exists; use a new corpus directory to preserve prior artifacts')
    spec = json.loads(a.spec.read_text())
    a.output.mkdir(parents=True)
    manifest = {'schema': 2, 'status': 'unannotated', 'grid_hz': 4,
                'spec_sha256': sha256(a.spec), 'clips': [],
                'preparation': {'av': av.__version__, 'numpy': np.__version__}}
    for clip in spec['clips']:
        name = clip['id']
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in name):
            raise ValueError('Clip IDs must contain lowercase letters, digits, _ or -')
        if name in {c['id'] for c in manifest['clips']}:
            raise ValueError('Duplicate clip ID')
        video = (a.spec.resolve().parent / clip['video']).resolve()
        start, duration = float(clip['start_s']), float(clip['duration_s'])
        if not 40 <= duration <= 90 or start < 0 or not clip['selection_reason']:
            raise ValueError('Require 40–90 s window, nonnegative start and selection rationale')
        row = {**clip, 'video': str(video), 'video_sha256': sha256(video), 'frames': []}
        directory = a.output / 'frames' / name
        directory.mkdir(parents=True)
        tick, previous, decoded = start, None, 0
        began = time.perf_counter()
        with av.open(str(video)) as container:
            stream = container.streams.video[0]
            container.seek(int(start * av.time_base), backward=True)
            for frame in container.decode(stream):
                decoded += 1
                if frame.pts is None:
                    raise ValueError('Missing presentation timestamp')
                stamp = float(frame.pts * frame.time_base)
                if stamp >= start + duration:
                    break
                if stamp + 1e-8 < tick:
                    continue
                rgb = frame.to_image().convert('RGB')
                thumb = np.asarray(rgb.resize((96, 54), Image.Resampling.BILINEAR), dtype=np.float32)
                change = 0.0 if previous is None else float(np.abs(thumb - previous).mean() / 255.0)
                previous = thumb
                path = directory / f'{len(row["frames"]):05d}.jpg'
                rgb.save(path, quality=95, subsampling=0)
                row['frames'].append({'t_s': stamp - start, 'source_t_s': stamp,
                                      'path': str(path.relative_to(a.output)),
                                      'sha256': sha256(path), 'change': change})
                tick = start + (math.floor((stamp - start) * 4 + 1e-8) + 1) / 4
        row['preparation_ms'] = (time.perf_counter() - began) * 1000
        row['decoded_frames'] = decoded
        if len(row['frames']) < duration * 3.8:
            raise ValueError(f'{name}: incomplete window or unexpectedly sparse video')
        sheetdir = a.output / 'contact_sheets'
        sheetdir.mkdir(exist_ok=True)
        for offset in range(0, len(row['frames']), 32):
            sheet = Image.new('RGB', (4 * 320, 8 * 200), '#202020')
            draw = ImageDraw.Draw(sheet)
            for pos, item in enumerate(row['frames'][offset:offset + 32]):
                x, y = (pos % 4) * 320, (pos // 4) * 200
                with Image.open(a.output / item['path']) as image:
                    image.thumbnail((316, 174))
                    sheet.paste(image, (x, y))
                draw.text((x + 2, y + 178), f'{name}  t={item["t_s"]:.3f}s  frame={offset+pos}', fill='white')
            sheet.save(sheetdir / f'{name}_{offset:05d}.jpg', quality=90)
        row['queries'] = []
        manifest['clips'].append(row)
        (a.output / 'manifest.draft.json').write_text(json.dumps(manifest, indent=2))
        print(f'{name}: {len(row["frames"])} candidate frames; no CLIP inference', flush=True)
    print(f'Annotate {a.output / "manifest.draft.json"}, save as manifest.json, then freeze.')


if __name__ == '__main__':
    main()
