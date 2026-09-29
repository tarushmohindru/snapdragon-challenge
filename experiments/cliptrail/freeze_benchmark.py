#!/usr/bin/env python3
"""Validate annotations and lock protocol/code/data before CLIP sees queries."""
import argparse
import datetime
import json
import math
from pathlib import Path
from reference_backend import sha256

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT.parents[1] / 'project/planning/cliptrail-mve-protocol.md'
CODE = ('sampling.py', 'benchmark_core.py', 'reference_backend.py',
        'run_benchmark.py', 'freeze_benchmark.py', 'prepare_corpus.py')


def safe_frame(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Frame path escapes corpus directory')
    return path


def validate(manifest, root, verify_images=True):
    if manifest.get('schema') != 2 or manifest.get('grid_hz') != 4:
        raise ValueError('Expected protocol-v2 corpus with 4 Hz candidate grid')
    if not manifest.get('annotator') or manifest.get('annotations_before_model_results') is not True:
        raise ValueError('Record annotator and pre-inference annotation declaration')
    if manifest.get('all_matching_occurrences_reviewed') is not True:
        raise ValueError('Review all matching occurrences, not just one selected target')
    clips = manifest['clips']
    if len(clips) < 6 or len({c['source_id'] for c in clips}) < 2:
        raise ValueError('Require >=6 windows from >=2 sources')
    counts = {'clips': len(clips), 'queries': 0, 'short_queries': 0, 'candidate_frames': 0}
    seen_clips, seen_queries = set(), set()
    source_hashes, source_windows = {}, {}
    for c in clips:
        if c['id'] in seen_clips:
            raise ValueError('Duplicate clip')
        seen_clips.add(c['id'])
        duration = c['duration_s']
        if not 40 <= duration <= 90 or not c.get('selection_reason'):
            raise ValueError('Missing window rationale or invalid duration')
        if not c.get('source_url') or not c.get('attribution') or not c.get('video_sha256'):
            raise ValueError('Missing public-source provenance/attribution')
        source = c['source_id']
        previous_hash = source_hashes.setdefault(source, c['video_sha256'])
        if previous_hash != c['video_sha256']:
            raise ValueError('One source ID refers to different source files')
        start = c['start_s']
        if not math.isfinite(start) or start < 0:
            raise ValueError('Invalid source window offset')
        for a, b in source_windows.setdefault(source, []):
            if start < b and start + duration > a:
                raise ValueError('Overlapping windows create duplicate temporal evidence')
        source_windows[source].append((start, start + duration))
        frames = c['frames']
        times = [f['t_s'] for f in frames]
        if len(times) < duration * 3.8 or any(not math.isfinite(t) or not 0 <= t < duration for t in times):
            raise ValueError('Incomplete or invalid candidate grid')
        if any(b <= a or b - a > .5 for a, b in zip(times, times[1:])):
            raise ValueError('Candidate timestamps must increase without large holes')
        if times[0] > .1 or duration - times[-1] > .5:
            raise ValueError('Candidate grid does not cover entire window')
        if len({f['path'] for f in frames}) != len(frames):
            raise ValueError('Repeated candidate image path')
        for f in frames:
            if not math.isfinite(f['change']) or not 0 <= f['change'] <= 1:
                raise ValueError('Invalid raster-change score')
            path = safe_frame(root, f['path'])
            if verify_images and sha256(path) != f['sha256']:
                raise ValueError(f'Changed candidate image: {path}')
        if len(c['queries']) < 4:
            raise ValueError('At least four queries per window required')
        seen_text = set()
        for q in c['queries']:
            if q['text'].strip().lower() in seen_text:
                raise ValueError('Duplicate query in one window')
            seen_text.add(q['text'].strip().lower())
            if q['id'] in seen_queries:
                raise ValueError('Query IDs must be globally unique')
            seen_queries.add(q['id'])
            if not q['text'].strip() or not q.get('rationale') or not q.get('confounders'):
                raise ValueError('Query needs natural language, rationale and confounders')
            intervals = q['intervals_s']
            if not intervals:
                raise ValueError('No empty-answer queries in this positive retrieval gate')
            for i, (a, b) in enumerate(intervals):
                if not 0 <= a < b <= duration or b - a < .5 - 1e-9:
                    raise ValueError('Intervals must last >=0.5 s and lie within clip')
                if i and a < intervals[i-1][1]:
                    raise ValueError('Intervals must be sorted and nonoverlapping')
                if not any(a <= t < b for t in times):
                    raise ValueError('Annotated event has no candidate frame')
            counts['queries'] += 1
            counts['short_queries'] += int(all(b - a <= 2 + 1e-9 for a, b in intervals))
        counts['candidate_frames'] += len(frames)
    if len(set(source_hashes.values())) < 2:
        raise ValueError('Require two different source video files')
    if counts['queries'] < 24 or counts['short_queries'] < 8:
        raise ValueError('Require >=24 queries and >=8 short-event queries')
    return counts


def current_fingerprint(manifest):
    return {'manifest_sha256': sha256(manifest), 'protocol_sha256': sha256(PROTOCOL),
            'code_sha256': {name: sha256(ROOT / name) for name in CODE}}


def verify_lock(manifest):
    lock_path = manifest.with_suffix('.lock.json')
    lock = json.loads(lock_path.read_text())
    if lock['fingerprint'] != current_fingerprint(manifest):
        raise ValueError('Data/protocol/code changed after freeze; document a new version')
    data = json.loads(manifest.read_text())
    counts = validate(data, manifest.parent)
    if counts != lock['counts']:
        raise ValueError('Frozen corpus counts do not match')
    return data, lock


def main():
    p = argparse.ArgumentParser()
    p.add_argument('manifest', type=Path)
    a = p.parse_args()
    output = a.manifest.with_suffix('.lock.json')
    if output.exists():
        raise ValueError('Lock already exists; do not overwrite pre-registration')
    data = json.loads(a.manifest.read_text())
    counts = validate(data, a.manifest.parent)
    lock = {'frozen_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'counts': counts, 'fingerprint': current_fingerprint(a.manifest),
            'budget': 16, 'embeddings_seen_before_annotations': False}
    output.write_text(json.dumps(lock, indent=2))
    print(json.dumps({'lock': str(output), **counts}, indent=2))


if __name__ == '__main__':
    main()
