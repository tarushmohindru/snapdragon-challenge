#!/usr/bin/env python3
"""Post-run correction of the supplemental hybrid control, not adaptive tuning.

v1 mistakenly iterated changed(changes, N), which sorts its output by timestamp
and returns all frames. Correct the preregistered 'strongest distinct changes'
definition: half uniform, then descending pixel change, skipping duplicates.
Required baselines/hierarchical/data/thresholds stay byte-for-byte unchanged.
"""
import argparse
import copy
import datetime
import json
import resource
import struct
from pathlib import Path
import run_benchmark
from benchmark_core import boundary_sensitivity, evaluate_query, gate, paired_bootstrap, summarize
from freeze_benchmark import safe_frame, verify_lock
from reference_backend import ClipReference, sha256
from sampling import uniform


def corrected_selection(method, changes, budget):
    if method != 'hybrid':
        raise ValueError('Correction is restricted to supplemental hybrid baseline')
    selected = uniform(len(changes), max(1, budget // 2))
    for i in sorted(range(len(changes)), key=lambda i: (-changes[i], i)):
        if len(selected) == min(budget, len(changes)):
            break
        if i not in selected:
            selected.append(i)
    return sorted(selected)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--original', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Correction output exists; preserve it')
    data, lock = verify_lock(a.manifest)
    original = json.loads(a.original.read_text())
    if original['status'] != 'completed':
        raise ValueError('Original run must be complete')
    a.output.mkdir(parents=True)
    correction = {'reason': __doc__, 'frozen_before_correction_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'script_sha256': sha256(__file__), 'original_report_sha256': sha256(a.original),
                  'reused_methods': ['uniform', 'change', 'scene', 'hierarchical'],
                  'rerun_method': 'hybrid', 'annotations_or_thresholds_changed': False}
    (a.output / 'correction-registration.json').write_text(json.dumps(correction, indent=2))
    root = Path(__file__).resolve().parent
    backend = ClipReference(root / 'assets/model', root / 'results/provisioning.json', 2)
    backend.warmup(safe_frame(a.manifest.parent, data['clips'][0]['frames'][0]['path']))
    # Explicit dependency replacement in this correction process only.
    run_benchmark.static_selection = corrected_selection
    report = copy.deepcopy(original)
    report.update(status='running_correction', valid_benchmark=False, rows=[], correction=correction,
                  correction_model=backend.metadata)
    new_vectors = []
    for clip in data['clips']:
        for query in clip['queries']:
            row, vectors, text = run_benchmark.run_case(backend, clip['frames'], query['text'], 'hybrid', 16, a.manifest.parent)
            row.update(clip_id=clip['id'], source_id=clip['source_id'], query_id=query['id'],
                       query=query['text'], intervals_s=query['intervals_s'])
            row['metrics'] = evaluate_query(row['ranked_times_s'], row['selected_times_s'], query['intervals_s'])
            new_vectors.append((row, vectors, text))
            print(f'Corrected hybrid: {query["id"]} R3={row["metrics"]["recall_at_3"]}', flush=True)
    with (a.output / 'embeddings.f32').open('wb') as destination:
        def store(row, vectors, text):
            row = copy.deepcopy(row)
            row['embedding_file'] = 'embeddings.f32'
            row['text_embedding_byte_offset'] = destination.tell()
            destination.write(struct.pack('<512f', *text))
            row['image_embedding_byte_offsets'] = {}
            for i in row['encode_order']:
                row['image_embedding_byte_offsets'][str(i)] = destination.tell()
                destination.write(struct.pack('<512f', *vectors[i]))
            report['rows'].append(row)
        with (a.original.parent / 'embeddings.f32').open('rb') as source:
            def read(offset):
                source.seek(offset)
                return struct.unpack('<512f', source.read(512*4))
            for row in original['rows']:
                if row['method'] != 'hybrid':
                    store(row, {i: read(row['image_embedding_byte_offsets'][str(i)]) for i in row['selected_indices']},
                          read(row['text_embedding_byte_offset']))
        for row, vectors, text in new_vectors:
            store(row, vectors, text)
    report['summary'] = summarize(report['rows'])
    report['gate'] = gate(report['summary'])
    report['paired_comparisons'] = paired_bootstrap(report['rows'])
    report['boundary_sensitivity'] = boundary_sensitivity(report['rows'])
    report['cache_demand_diagnostic'] = run_benchmark.cache_diagnostic(report['rows'])
    report['correction_actual_calls_excluding_warmup'] = {'image': backend.image_calls, 'text': backend.text_calls}
    report['whole_experiment_calls_excluding_warmups'] = {'image': 1920 + backend.image_calls, 'text': 120 + backend.text_calls}
    report['correction_peak_process_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    report['memory_note'] += '; original-run high-water retained, correction process reported separately'
    report.update(status='completed', valid_benchmark=True,
                  provenance='MEASURED original required comparisons, supplemental hybrid rerun after implementation bug fix; no NPU')
    (a.output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    print(json.dumps(report['gate'], indent=2))


if __name__ == '__main__':
    main()
