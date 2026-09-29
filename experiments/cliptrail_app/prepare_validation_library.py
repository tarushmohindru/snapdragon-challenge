"""Create local application-validation videos; no benchmark labels or model runs."""
import hashlib
import json
import math
from pathlib import Path
import shutil

import av
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'experiments/cliptrail/assets/videos'
DEST = ROOT / 'experiments/cliptrail_app/validation_library'
SAMPLES = [('steel_early.mov', 20.0, 42.0), ('steel_late.mov', 300.0, 42.0)]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def make_excerpt(source, destination, start, duration):
    with av.open(str(source)) as original, av.open(str(destination), mode='w') as output:
        inbound = original.streams.video[0]
        outbound = output.add_stream('mpeg4', rate=12)
        outbound.width = 640
        outbound.height = 268
        outbound.pix_fmt = 'yuv420p'
        original.seek(int(start * av.time_base), backward=True)
        next_tick = start
        count = 0
        for frame in original.decode(inbound):
            if frame.pts is None:
                continue
            t = float(frame.pts * frame.time_base)
            if t >= start + duration:
                break
            if t + 1e-8 < next_tick:
                continue
            image = frame.to_image().convert('RGB').resize((640, 268), Image.Resampling.BICUBIC)
            encoded = av.VideoFrame.from_image(image)
            encoded.pts = count
            for packet in outbound.encode(encoded):
                output.mux(packet)
            count += 1
            next_tick = start + (math.floor((t - start) * 12 + 1e-8) + 1) / 12
        for packet in outbound.encode(None):
            output.mux(packet)
    if count < duration * 10:
        raise RuntimeError(f'Incomplete app-validation excerpt: {destination}')
    return count


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    trailer = SOURCE / 'sintel_trailer-480p.mp4'
    original = SOURCE / 'tears_of_steel_720p.mov'
    manifest_path = DEST / 'manifest.json'
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text())
        if all(sha(DEST / item['name']) == item['sha256'] for item in existing['videos']):
            print(json.dumps({'status': 'existing_library_verified', 'manifest': str(manifest_path)}))
            return
        raise ValueError('Existing validation library changed; preserve it')
    shutil.copyfile(trailer, DEST / trailer.name)
    videos = [{'name': trailer.name, 'source': str(trailer), 'kind': 'complete source',
               'sha256': sha(DEST / trailer.name), 'bytes': (DEST / trailer.name).stat().st_size}]
    for name, start, duration in SAMPLES:
        count = make_excerpt(original, DEST / name, start, duration)
        videos.append({'name': name, 'source': str(original), 'kind': 'local application test excerpt',
                       'source_start_s': start, 'duration_s': duration, 'frames_encoded': count,
                       'sha256': sha(DEST / name), 'bytes': (DEST / name).stat().st_size})
    manifest = {'schema': 1, 'purpose': 'Application validation only; not the frozen retrieval benchmark',
                'original_tears_sha256': sha(original), 'videos': videos,
                'model_inference_performed': False}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'status': 'created', 'manifest': str(manifest_path), 'videos': videos}, indent=2))


if __name__ == '__main__':
    main()
