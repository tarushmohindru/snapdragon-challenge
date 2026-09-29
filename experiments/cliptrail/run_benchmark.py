#!/usr/bin/env python3
"""Execute locked real-model ClipTrail falsification. No oracle/mock mode."""
import argparse
import datetime
import json
import resource
import struct
import sys
import time
from pathlib import Path
from benchmark_core import METHODS, boundary_sensitivity, evaluate_query, gate, paired_bootstrap, static_selection, summarize
from freeze_benchmark import safe_frame, verify_lock
from reference_backend import ClipReference, cosine
from sampling import hierarchical, uniform


def run_case(backend, frames, query_text, method, budget, root):
    """No annotations accepted here: selection can inspect only requested scores."""
    if budget > len(frames):
        raise ValueError('Corpus is smaller than requested budget')
    initial_image, initial_text = backend.image_calls, backend.text_calls
    vectors, image_costs, order = {}, {}, []
    began = time.perf_counter()

    def encode(index, stage):
        if index in vectors:
            raise RuntimeError('Repeated image encode within cold query')
        vectors[index], timing = backend.encode_image(safe_frame(root, frames[index]['path']))
        image_costs[index] = {**timing, 'stage': stage}
        order.append(index)

    if method == 'hierarchical':
        index_selection = uniform(len(frames), max(2, budget // 2))[:budget]
    else:
        index_selection = static_selection(method, [f['change'] for f in frames], budget)
    for index in index_selection:
        encode(index, 'index')
    index_end = time.perf_counter()
    text_vector, text_cost = backend.encode_text(query_text)
    scored = set()

    def score(index):
        if index in scored:
            raise RuntimeError('Selector requested the same score twice')
        scored.add(index)
        if index not in vectors:
            encode(index, 'query')
        return cosine(vectors[index], text_vector)

    selected = hierarchical(len(frames), budget, score) if method == 'hierarchical' else index_selection
    if len(selected) != budget or len(set(selected)) != budget or set(selected) != set(vectors):
        raise RuntimeError('Equal-budget/unique-encode invariant failed')
    scores = {i: cosine(vectors[i], text_vector) for i in selected}
    ranked = sorted(selected, key=lambda i: (-scores[i], frames[i]['t_s']))
    end = time.perf_counter()
    calls = (backend.image_calls - initial_image, backend.text_calls - initial_text)
    if calls != (budget, 1):
        raise RuntimeError(f'Actual encoder calls {calls} differ from expected {(budget, 1)}')
    row = {
        'method': method, 'selected_indices': selected, 'encode_order': order,
        'selected_times_s': [frames[i]['t_s'] for i in selected],
        'ranked_indices': ranked, 'ranked_times_s': [frames[i]['t_s'] for i in ranked],
        'scores': {str(i): scores[i] for i in selected},
        'cost': {'image_calls': calls[0], 'text_calls': calls[1],
                 'index_image_calls': len(index_selection), 'query_image_calls': budget - len(index_selection),
                 'index_ms': (index_end - began) * 1000,
                 'query_ms': (end - index_end) * 1000, 'total_ms': (end - began) * 1000,
                 'images': image_costs, 'text': text_cost},
    }
    return row, vectors, text_vector


def cache_diagnostic(rows):
    result = []
    for clip in sorted({r['clip_id'] for r in rows}):
        for method in METHODS:
            subset = [r for r in rows if r['clip_id'] == clip and r['method'] == method]
            indices = set().union(*(set(r['selected_indices']) for r in subset))
            result.append({'clip_id': clip, 'method': method, 'queries': len(subset),
                           'unique_images_if_cached': len(indices),
                           'actual_cold_image_calls': sum(r['cost']['image_calls'] for r in subset)})
    return {'provenance': 'ARITHMETIC replay, not warm-session timing or matched-session quality',
            'rows': result}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--model-dir', type=Path, default=Path(__file__).parent / 'assets/model')
    p.add_argument('--provisioning', type=Path, default=Path(__file__).parent / 'results/provisioning.json')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--threads', type=int, default=2)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Output exists; preserve previous evidence and choose another directory')
    a.output.mkdir(parents=True)
    report = {'schema': 2, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'initializing', 'inference_performed': False, 'valid_benchmark': False,
              'npu_verified': False, 'rows': []}
    backend = None

    def save():
        temp = a.output / 'report.json.tmp'
        temp.write_text(json.dumps(report, indent=2, allow_nan=False))
        temp.replace(a.output / 'report.json')

    save()
    try:
        manifest, lock = verify_lock(a.manifest)
        report.update(lock=lock, common_preparation=[{
            'clip_id': c['id'], 'decoded_frames': c['decoded_frames'],
            'decode_change_jpeg_ms': c['preparation_ms'],
        } for c in manifest['clips']])
        backend = ClipReference(a.model_dir, a.provisioning, a.threads)
        backend.warmup(safe_frame(a.manifest.parent, manifest['clips'][0]['frames'][0]['path']))
        report.update(model=backend.metadata, status='running')
        save()
        sequence_number = 0
        with (a.output / 'embeddings.f32').open('wb') as embeddings:
            for clip in manifest['clips']:
                for query in clip['queries']:
                    shift = sequence_number % len(METHODS)
                    ordered = METHODS[shift:] + METHODS[:shift]
                    sequence_number += 1
                    for method in ordered:
                        row, vectors, text_vector = run_case(
                            backend, clip['frames'], query['text'], method, lock['budget'], a.manifest.parent)
                        row.update(clip_id=clip['id'], source_id=clip['source_id'], query_id=query['id'],
                                   query=query['text'], intervals_s=query['intervals_s'])
                        row['metrics'] = evaluate_query(row['ranked_times_s'], row['selected_times_s'], query['intervals_s'])
                        row['embedding_file'] = 'embeddings.f32'
                        row['text_embedding_byte_offset'] = embeddings.tell()
                        embeddings.write(struct.pack('<512f', *text_vector))
                        row['image_embedding_byte_offsets'] = {}
                        for index in row['encode_order']:
                            row['image_embedding_byte_offsets'][str(index)] = embeddings.tell()
                            embeddings.write(struct.pack('<512f', *vectors[index]))
                        embeddings.flush()
                        report['rows'].append(row)
                        report['inference_performed'] = True
                        save()
                        print(f'{clip["id"]}/{query["id"]} {method}: R1={row["metrics"]["recall_at_1"]} '
                              f'R3={row["metrics"]["recall_at_3"]} image_calls={row["cost"]["image_calls"]}', flush=True)
        report['summary'] = summarize(report['rows'])
        report['gate'] = gate(report['summary'])
        report['paired_comparisons'] = paired_bootstrap(report['rows'])
        report['boundary_sensitivity'] = boundary_sensitivity(report['rows'])
        report['cache_demand_diagnostic'] = cache_diagnostic(report['rows'])
        report.update(status='completed', valid_benchmark=True,
                      provenance='MEASURED real OpenAI CLIP CPU embeddings; no Snapdragon inference')
    except Exception as exc:
        report.update(status='blocked_or_failed', error=f'{type(exc).__name__}: {exc}',
                      gate={'adaptive_verdict': 'not_evaluated'})
    report['peak_process_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    report['memory_note'] = 'Process high-water RSS; not per-model incremental memory or NPU memory'
    if backend is not None:
        report['actual_calls_excluding_warmup'] = {'image': backend.image_calls, 'text': backend.text_calls}
        report['inference_performed'] = bool(report['inference_performed'] or backend.image_calls or backend.text_calls)
    save()
    print(json.dumps({k: v for k, v in report.items() if k in ('status', 'error', 'gate', 'actual_calls_excluding_warmup')}, indent=2))
    return 0 if report['valid_benchmark'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
