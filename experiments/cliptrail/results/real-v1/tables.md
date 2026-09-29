# Measured ClipTrail retrieval results

Real OpenAI CLIP ViT-B/16, CPU float32, two PyTorch threads. No NPU execution.

24 queries across 6 windows; 11 short-event queries. 16 image encodes + one text encode per independent cold query.

| Method | Recall@1 | Recall@3 | Short R@1 | Short R@3 | Coverage | Median error (s) | p95 error (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| uniform | 70.83% | 79.17% | 54.55% | 54.55% | 83.33% | 0.000 | 25.425 |
| change | 70.83% | 75.00% | 63.64% | 72.73% | 79.17% | 0.000 | 27.475 |
| scene | 83.33% | 87.50% | 72.73% | 81.82% | 91.67% | 0.000 | 18.750 |
| hybrid | 41.67% | 45.83% | 9.09% | 9.09% | 45.83% | 2.500 | 38.087 |
| hierarchical | 45.83% | 54.17% | 9.09% | 18.18% | 54.17% | 1.000 | 38.087 |

## Actual CPU costs

Warm model, recreated index per query. Includes preprocessing and selected-image file reads; excludes source video preparation, initialization and result serialization.

| Method | Image calls | Text calls | Median index (ms) | Median query (ms) | p95 query (ms) | Median total (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| uniform | 384 | 24 | 4181.9 | 24.9 | 29.0 | 4207.0 |
| change | 384 | 24 | 4213.8 | 25.1 | 28.3 | 4240.0 |
| scene | 384 | 24 | 4162.7 | 24.4 | 34.0 | 4189.2 |
| hybrid | 384 | 24 | 4157.8 | 24.4 | 29.9 | 4183.3 |
| hierarchical | 384 | 24 | 2069.4 | 2103.8 | 2170.9 | 4175.4 |

Model initialization plus asset verification: 3440.6 ms. Separate decode/change/JPEG preparation: 23.85 s. Peak process RSS: 841.9 MiB. Preparation is shared offline work, not per-query time; RSS is a process high-water mark.

## Predeclared gate

**kill_adaptive_v1**

- recall1_gain_10pp: FAIL
- recall3_gain_10pp: FAIL
- short_recall3_loss_at_most_5pp: FAIL
- recall3_at_least_80pct: FAIL
- median_localization_regression_at_most_half_second: FAIL
- positive_gain_in_half_windows: FAIL
- neither_source_loses_over_5pp: FAIL

Simple usefulness gate: scene. This does not establish novelty.

## Failure decomposition

| Method | No matching frame sampled | Matching frame sampled but outside top 3 |
| --- | ---: | ---: |
| uniform | 4 | 1 |
| change | 5 | 1 |
| scene | 2 | 1 |
| hybrid | 13 | 0 |
| hierarchical | 11 | 0 |

## Sensitivity to annotation boundaries

| Labels | uniform R@3 | change R@3 | scene R@3 | hybrid R@3 | hierarchical R@3 | Adaptive diagnostic |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| eroded_025s | 79.17% | 29.17% | 83.33% | 37.50% | 50.00% | kill_adaptive_v1 |
| expanded_025s | 79.17% | 79.17% | 87.50% | 45.83% | 54.17% | kill_adaptive_v1 |

The locked primary labels alone determine the official gate. Sensitivity diagnostics retain the original short-event membership.

## Per-window Recall@3

| Window | uniform | change | scene | hybrid | hierarchical |
| --- | ---: | ---: | ---: | ---: | ---: |
| sintel_00 | 100.0% | 25.0% | 100.0% | 75.0% | 75.0% |
| steel_140 | 100.0% | 75.0% | 75.0% | 50.0% | 50.0% |
| steel_20 | 75.0% | 100.0% | 100.0% | 50.0% | 75.0% |
| steel_260 | 75.0% | 75.0% | 100.0% | 25.0% | 25.0% |
| steel_380 | 50.0% | 75.0% | 75.0% | 25.0% | 25.0% |
| steel_500 | 75.0% | 100.0% | 75.0% | 50.0% | 75.0% |

## Cache-demand diagnostic

Unique frames across four queries per window, with perfect reuse. Arithmetic replay only; not measured warm-session speed or a matched-session-budget comparison.

| Method | Unique frames over all windows | Actual cold-run image calls |
| --- | ---: | ---: |
| uniform | 96 | 384 |
| change | 96 | 384 |
| scene | 96 | 384 |
| hybrid | 96 | 384 |
| hierarchical | 207 | 384 |

## Limits

Small convenience corpus: two public films, six windows, one agent annotator, no independent human label audit. Films may overlap CLIP pretraining; results do not generalize to all recordings. Only positive queries; absence/false-positive calibration was not tested. Official CLIP center cropping may remove peripheral content. No QNN, Snapdragon, NPU, energy or production-session claim. Raw vectors, selected timestamps, costs, paired cluster-bootstrap intervals and labels are retained in report.json and embeddings.f32.
