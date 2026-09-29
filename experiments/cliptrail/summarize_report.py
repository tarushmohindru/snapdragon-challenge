#!/usr/bin/env python3
"""Render measured tables from a completed report; no inference or tuning."""
import argparse
import json
from pathlib import Path
from benchmark_core import METHODS


def main():
    p = argparse.ArgumentParser()
    p.add_argument('report', type=Path)
    a = p.parse_args()
    r = json.loads(a.report.read_text())
    if r['status'] != 'completed' or not r['valid_benchmark']:
        raise ValueError('Benchmark not completed')
    overall = r['summary']['overall']
    lines = ['# Measured ClipTrail retrieval results', '',
             'Real OpenAI CLIP ViT-B/16, CPU float32, two PyTorch threads. No NPU execution.', '',
             f'{r["lock"]["counts"]["queries"]} queries across {r["lock"]["counts"]["clips"]} windows; '
             f'{r["lock"]["counts"]["short_queries"]} short-event queries. '
             f'{r["lock"]["budget"]} image encodes + one text encode per independent cold query.', '',
             '| Method | Recall@1 | Recall@3 | Short R@1 | Short R@3 | Coverage | Median error (s) | p95 error (s) |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for m in METHODS:
        v = overall[m]
        values = [v[k] * 100 for k in ('recall_at_1', 'recall_at_3', 'short_recall_at_1', 'short_recall_at_3', 'coverage')]
        lines.append(f'| {m} | ' + ' | '.join(f'{v:.2f}%' for v in values)
                     + f' | {v["localization_error_s_median"]:.3f} | {v["localization_error_s_p95"]:.3f} |')
    lines += ['', '## Actual CPU costs', '',
              'Warm model, recreated index per query. Includes preprocessing and selected-image file reads; excludes source video preparation, initialization and result serialization.', '',
              '| Method | Image calls | Text calls | Median index (ms) | Median query (ms) | p95 query (ms) | Median total (ms) |',
              '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for m in METHODS:
        v = overall[m]
        lines.append(f'| {m} | {v["image_calls_total"]} | {v["text_calls_total"]} | '
                     f'{v["index_ms_median"]:.1f} | {v["query_ms_median"]:.1f} | '
                     f'{v["query_ms_p95"]:.1f} | {v["total_ms_median"]:.1f} |')
    prep = sum(c['decode_change_jpeg_ms'] for c in r['common_preparation'])
    lines += ['', f'Model initialization plus asset verification: {r["model"]["init_and_verification_ms"]:.1f} ms. '
              f'Separate decode/change/JPEG preparation: {prep/1000:.2f} s. '
              f'Peak process RSS: {r["peak_process_rss_bytes"]/(1024**2):.1f} MiB. '
              'Preparation is shared offline work, not per-query time; RSS is a process high-water mark.', '',
              '## Predeclared gate', '', f'**{r["gate"]["adaptive_verdict"]}**', '']
    for check, passed in r['gate']['checks'].items():
        lines.append(f'- {check}: {"PASS" if passed else "FAIL"}')
    lines += ['', 'Simple usefulness gate: ' + (', '.join(r['gate']['simple_usefulness_gate_passes']) or 'no baseline passes all conditions')
              + '. This does not establish novelty.', '', '## Failure decomposition', '',
              '| Method | No matching frame sampled | Matching frame sampled but outside top 3 |',
              '| --- | ---: | ---: |']
    for m in METHODS:
        rows = [row for row in r['rows'] if row['method'] == m]
        sampling = sum(not row['metrics']['coverage'] for row in rows)
        ranking = sum(row['metrics']['coverage'] and not row['metrics']['recall_at_3'] for row in rows)
        lines.append(f'| {m} | {sampling} | {ranking} |')
    lines += ['', '## Sensitivity to annotation boundaries', '',
              '| Labels | uniform R@3 | change R@3 | scene R@3 | hybrid R@3 | hierarchical R@3 | Adaptive diagnostic |',
              '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for name, item in r['boundary_sensitivity'].items():
        lines.append('| ' + name + ' | ' + ' | '.join(f'{item["summary"]["overall"][m]["recall_at_3"]*100:.2f}%' for m in METHODS)
                     + f' | {item["gate_diagnostic"]["adaptive_verdict"]} |')
    lines += ['', 'The locked primary labels alone determine the official gate. Sensitivity diagnostics retain the original short-event membership.', '',
              '## Per-window Recall@3', '',
              '| Window | uniform | change | scene | hybrid | hierarchical |',
              '| --- | ---: | ---: | ---: | ---: | ---: |']
    for clip, methods in r['summary']['clip_id'].items():
        lines.append('| ' + clip + ' | ' + ' | '.join(f'{methods[m]["recall_at_3"]*100:.1f}%' for m in METHODS) + ' |')
    lines += ['', '## Cache-demand diagnostic', '',
              'Unique frames across four queries per window, with perfect reuse. Arithmetic replay only; not measured warm-session speed or a matched-session-budget comparison.', '',
              '| Method | Unique frames over all windows | Actual cold-run image calls |',
              '| --- | ---: | ---: |']
    for m in METHODS:
        rows = [x for x in r['cache_demand_diagnostic']['rows'] if x['method'] == m]
        lines.append(f'| {m} | {sum(x["unique_images_if_cached"] for x in rows)} | {sum(x["actual_cold_image_calls"] for x in rows)} |')
    lines += ['', '## Limits', '',
              'Small convenience corpus: two public films, six windows, one agent annotator, no independent human label audit. '
              'Films may overlap CLIP pretraining; results do not generalize to all recordings. '
              'Only positive queries; absence/false-positive calibration was not tested. '
              'Official CLIP center cropping may remove peripheral content. '
              'No QNN, Snapdragon, NPU, energy or production-session claim. '
              'Raw vectors, selected timestamps, costs, paired cluster-bootstrap intervals and labels are retained in report.json and embeddings.f32.', '']
    output = a.report.parent / 'tables.md'
    if output.exists():
        raise ValueError('Rendered tables already exist; preserve existing artifact')
    output.write_text('\n'.join(lines))
    print(output)


if __name__ == '__main__':
    main()
