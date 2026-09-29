"""Measure the persistent CPU app on a small local three-video library."""
import datetime
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import time

from cliptrail_app.playback import playback_source
from cliptrail_app.store import IndexStore
from cliptrail_app.web import AppRuntime

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / 'experiments/cliptrail_app/validation_library'
OUTPUT = ROOT / 'experiments/cliptrail_app/results/persistent-demo'
DB = OUTPUT / 'index.sqlite3'
REPORT = OUTPUT / 'validation.json'
QUERIES = [
    'A red-haired woman surrounded by burning rubble.',
    'An older man with a gray beard and a headband indoors.',
    'A narrow stone alley viewed from above.',
    'A person standing in a futuristic building.',
    'A robot moving through a city.',
    'Golden sand dunes stretching into the distance.',
]


def rss_bytes():
    with open('/proc/self/status') as handle:
        for line in handle:
            if line.startswith('VmRSS:'):
                return int(line.split()[1]) * 1024
    return None


def main():
    if REPORT.exists() or DB.exists():
        raise ValueError('Validation output exists; preserve original measurements')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((LIBRARY / 'manifest.json').read_text())
    print('Loading one persistent CPU CLIP backend', flush=True)
    app_started = time.perf_counter()
    app = AppRuntime(DB, 'cpu')
    loaded_s = time.perf_counter() - app_started
    print('Indexing local three-video folder', flush=True)
    began = time.perf_counter()
    app.start_index([str(LIBRARY)])
    last_line = None
    while app.worker.is_alive():
        app.worker.join(.5)
        state = app.snapshot()['state']
        line = (state['completed'], state['current'], state['stage'], state['progress_count'])
        if line != last_line:
            print(json.dumps({'completed': line[0], 'current': line[1],
                              'stage': line[2], 'count': line[3]}), flush=True)
            last_line = line
    index_wall_s = time.perf_counter() - began
    snapshot = app.snapshot()
    if snapshot['state']['errors'] or len(snapshot['videos']) != 3:
        raise RuntimeError(f"Incomplete multi-video index: {snapshot['state']}")
    rss_after_index = rss_bytes()
    peak_after_index = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    print('Running six queries with the same loaded model', flush=True)
    query_records = []
    for text in QUERIES:
        result = app.query(text, 5)
        if not result['results']:
            raise RuntimeError(f'No results for {text}')
        top = result['results'][0]
        with IndexStore(DB) as store:
            row, video = playback_source(store, top['result_id'])
            if abs(row['timestamp_s'] - top['timestamp_s']) > 1e-9:
                raise RuntimeError('Stored playback timestamp differs from search result')
        query_records.append({'query': text, 'query_ms': result['timing']['query_ms'],
                              'text_encode_ms': result['timing']['text_encode_ms'],
                              'top_result_id': top['result_id'], 'top_filename': top['filename'],
                              'top_timestamp_s': top['timestamp_s'],
                              'top_similarity': top['similarity'],
                              'playback_source_exists': video.is_file()})
        print(json.dumps(query_records[-1]), flush=True)
    video_seconds = sum(v['duration_s'] for v in snapshot['videos'])
    logical_bytes = sum(v['logical_storage_bytes'] for v in snapshot['videos'])
    record = {
        'measured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'Local persistent CPU application on 3 videos from two public Blender films; no frozen benchmark rerun or target NPU run',
        'platform': platform.platform(), 'backend': snapshot['backend_label'],
        'model_load_s': loaded_s, 'source_manifest': str(LIBRARY / 'manifest.json'),
        'source_names': [v['name'] for v in manifest['videos']],
        'index_wall_s': index_wall_s, 'video_seconds': video_seconds,
        'video_minutes': video_seconds / 60,
        'throughput_video_minutes_per_wall_minute': (video_seconds / 60) / (index_wall_s / 60),
        'index_s_per_video_minute': index_wall_s / (video_seconds / 60),
        'indexed_videos': snapshot['videos'],
        'selected_frames_total': sum(v['selected_frames'] for v in snapshot['videos']),
        'logical_storage_bytes_total': logical_bytes,
        'logical_storage_bytes_per_video_minute': logical_bytes / (video_seconds / 60),
        'sqlite_disk_bytes_during_runtime': snapshot['index_disk_bytes'],
        'rss_after_multi_video_index_bytes': rss_after_index,
        'peak_rss_through_multi_video_index_bytes': peak_after_index,
        'query_records': query_records,
        'warm_query_latency_ms': [v['query_ms'] for v in query_records[1:]],
        'warm_query_median_ms': statistics.median(v['query_ms'] for v in query_records[1:]),
        'warm_query_max_ms': max(v['query_ms'] for v in query_records[1:]),
        'peak_rss_after_queries_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        'runtime_status_after_queries': app.snapshot()['state'],
        'npu_verified': False, 'target_run_performed': False,
        'notes': ['Index wall time excludes backend startup and includes hashing, two-pass decode, image encodes and SQLite writes.',
                  'Warm query sample excludes the first query after model load; all six use one backend instance and a prebuilt index.',
                  'Current/peak RSS are whole process; SQLite disk size includes WAL while server is running.',
                  'Two Tears clips are locally re-encoded excerpts for application validation, not independent source domains.']
    }
    REPORT.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'report': str(REPORT), 'status': 'complete'}), flush=True)


if __name__ == '__main__':
    main()
