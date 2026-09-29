#!/usr/bin/env python3
"""Verify recorded results against frozen labels, raw vectors and actual calls."""
import argparse
import json
import math
import struct
from pathlib import Path
from benchmark_core import METHODS, evaluate_query, gate, static_selection, summarize
from freeze_benchmark import verify_lock
from reference_backend import cosine, sha256
from sampling import hierarchical


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--original', type=Path)
    a = p.parse_args()
    data, lock = verify_lock(a.manifest)
    report = json.loads(a.report.read_text())
    if report.get('status') != 'completed' or not report.get('valid_benchmark'):
        raise ValueError('No completed real-model benchmark to audit')
    if not report.get('inference_performed') or report['npu_verified']:
        raise ValueError('Unexpected CPU inference provenance')
    if 'correction' in report:
        if not a.original or sha256(a.original) != report['correction']['original_report_sha256']:
            raise ValueError('Supply --original matching the preserved original report')
        if sha256(Path(__file__).parent / 'correct_hybrid.py') != report['correction']['script_sha256']:
            raise ValueError('Hybrid correction implementation changed after registration')
    expected_queries = {(c['id'], q['id']): (c, q) for c in data['clips'] for q in c['queries']}
    expected_keys = {(m, c, q) for m in METHODS for c, q in expected_queries}
    keys, offsets = set(), []
    previous_vectors = {}
    actual_image_calls = actual_text_calls = 0
    with (a.report.parent / 'embeddings.f32').open('rb') as vectors:
        def read_vector(offset):
            offsets.append(offset)
            vectors.seek(offset)
            raw = vectors.read(512 * 4)
            if len(raw) != 512 * 4:
                raise ValueError('Truncated embedding file')
            vector = struct.unpack('<512f', raw)
            if not all(math.isfinite(x) for x in vector) or abs(sum(x*x for x in vector) - 1) > 1e-5:
                raise ValueError('Embedding is not finite/unit normalized')
            return vector
        for row in report['rows']:
            key = row['method'], row['clip_id'], row['query_id']
            if key in keys or key not in expected_keys:
                raise ValueError('Duplicate/unexpected result')
            keys.add(key)
            clip, query = expected_queries[key[1:]]
            if row['query'] != query['text'] or row['intervals_s'] != query['intervals_s']:
                raise ValueError('Query or labels differ from pre-registration')
            times = {i: f['t_s'] for i, f in enumerate(clip['frames'])}
            selected = row['selected_indices']
            if len(selected) != lock['budget'] or len(set(selected)) != lock['budget']:
                raise ValueError('Image budget mismatch')
            if row['cost']['image_calls'] != lock['budget'] or row['cost']['text_calls'] != 1:
                raise ValueError('Encoder-call mismatch')
            actual_image_calls += row['cost']['image_calls']
            actual_text_calls += row['cost']['text_calls']
            text = read_vector(row['text_embedding_byte_offset'])
            scores = {}
            for i in selected:
                vector = read_vector(row['image_embedding_byte_offsets'][str(i)])
                scores[i] = cosine(vector, text)
                if abs(scores[i] - row['scores'][str(i)]) > 2e-6:
                    raise ValueError('Stored cosine does not match actual raw vectors')
                image_key = row['clip_id'], i
                if image_key in previous_vectors:
                    if max(abs(x-y) for x,y in zip(vector, previous_vectors[image_key])) > 1e-5:
                        raise ValueError('Repeated frame embedding unexpectedly changed')
                else:
                    previous_vectors[image_key] = vector
            ranking = sorted(selected, key=lambda i: (-scores[i], times[i]))
            if row['method'] == 'hierarchical':
                replay = hierarchical(len(clip['frames']), lock['budget'], lambda i: scores[i])
            elif row['method'] == 'hybrid' and 'correction' in report:
                from correct_hybrid import corrected_selection
                replay = corrected_selection('hybrid', [f['change'] for f in clip['frames']], lock['budget'])
            else:
                replay = static_selection(row['method'], [f['change'] for f in clip['frames']], lock['budget'])
            if set(replay) != set(selected):
                raise ValueError('Selector replay differs from actual encoded frames')
            ranked_times = [times[i] for i in ranking]
            selected_times = [times[i] for i in selected]
            if row['ranked_indices'] != ranking or row['ranked_times_s'] != ranked_times or row['selected_times_s'] != selected_times:
                raise ValueError('Incorrect ranking or timestamps')
            if row['metrics'] != evaluate_query(ranked_times, selected_times, query['intervals_s']):
                raise ValueError('Incorrect evaluation metrics')
            image_index_ms = sum(t['total_ms'] for t in row['cost']['images'].values() if t['stage'] == 'index')
            image_query_ms = sum(t['total_ms'] for t in row['cost']['images'].values() if t['stage'] == 'query')
            if row['cost']['index_ms'] + .1 < image_index_ms or row['cost']['query_ms'] + .1 < image_query_ms + row['cost']['text']['total_ms']:
                raise ValueError('Encoder work omitted from measured stage cost')
    if keys != expected_keys:
        raise ValueError('Missing query/method cases')
    if sorted(offsets) != list(range(0, len(offsets)*512*4, 512*4)):
        raise ValueError('Embedding records reused or missing')
    if (a.report.parent / 'embeddings.f32').stat().st_size != len(offsets)*512*4:
        raise ValueError('Unexpected embedding payload size')
    calls = {'image': actual_image_calls, 'text': actual_text_calls}
    if report['actual_calls_excluding_warmup'] != calls:
        raise ValueError('Reported runtime call total does not match rows')
    if report['summary'] != summarize(report['rows']) or report['gate'] != gate(report['summary']):
        raise ValueError('Summary/gate cannot be reproduced from raw rows')
    audit = {
        'status': 'passed', 'provenance': 'MEASURED artifact consistency checks, not independent annotation validation',
        'rows_checked': len(keys), 'vectors_checked': len(offsets), 'unique_images_checked': len(previous_vectors),
        'actual_calls_excluding_warmup': calls, 'manifest_sha256': sha256(a.manifest),
        'report_sha256': sha256(a.report), 'embeddings_sha256': sha256(a.report.parent / 'embeddings.f32'),
        'checks': ['frozen corpus/protocol/code', 'query and interval equality', 'exact inference budgets',
                   'unit vector norms', 'raw vector cosine/ranking', 'repeat image consistency',
                   'no embedding-offset reuse', 'metric and gate recomputation', 'stage timing covers encodes'],
    }
    output = a.report.parent / 'audit.json'
    if output.exists():
        raise ValueError('Audit exists; preserve original evidence')
    output.write_text(json.dumps(audit, indent=2))
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
