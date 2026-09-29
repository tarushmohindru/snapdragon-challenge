# Benchmark and evidence summary

This document separates product behavior, retrieval quality, host performance, and Snapdragon/QNN compatibility. Results from one category do not imply results in another.

## What is established

| Area | Result | Scope |
| --- | --- | --- |
| End-to-end product | Video/folder indexing, persistent SQLite storage, text search, ranked thumbnails/timestamps/scores, and timestamped playback routes work | Local CPU application and automated tests |
| Retrieval quality | Scene selection: **83.33% Recall@1**, **87.50% Recall@3**, **81.82% short-event Recall@3** | 24 positive queries, 11 short-event queries, six windows from two public films |
| Warm search | **27.45 ms median**, **34.70 ms maximum** across five post-first searches | Prebuilt 48-frame index, one loaded CPU model, recorded Linux host |
| Multi-video indexing | **15.49 s** for 2.279 video minutes; **6.80 s per video minute** | Three video files on the recorded CPU host; model startup excluded |
| Persistent index | **570,215 logical bytes**, **250,186 bytes per video minute**; closed SQLite file **638,976 bytes** | 48 normalized vectors plus JPEG thumbnails and metadata; source media excluded |
| Process memory | **757.6 MB RSS after indexing**, **913.6 MB after queries** | Whole process on the recorded CPU host |
| Snapdragon compatibility | Native ARM64 runtime, ORT QNN provider, pinned HTP backend loading, QNN partitioning/execution, and embedding parity observed | One fixed image-graph smoke on an ASUS Snapdragon X2 Elite |
| Physical NPU execution | **Not verified** | Required hardware device events/cycles were absent |

## Frozen retrieval benchmark

The frozen benchmark uses OpenAI CLIP ViT-B/16 in float32 on CPU, two inference threads, 16 selected image frames per query, and one text encoding per query. It contains 24 prewritten positive queries across six 40–60 second windows from *Sintel* and *Tears of Steel*. Eleven queries target short events.

| Selector | Recall@1 | Recall@3 | Short R@3 | Coverage |
| --- | ---: | ---: | ---: | ---: |
| Uniform | 70.83% | 79.17% | 54.55% | 83.33% |
| Raster change | 70.83% | 75.00% | 72.73% | 79.17% |
| **Scene midpoint** | **83.33%** | **87.50%** | **81.82%** | **91.67%** |
| Corrected uniform/change hybrid | 66.67% | 75.00% | 54.55% | 75.00% |
| Hierarchical adaptive | 45.83% | 54.17% | 18.18% | 54.17% |

The application uses the scene midpoint selector because it performed best in this comparison. The adaptive method failed its predeclared gate and was not carried into the product. Raw vectors, labels, hashes, selected timestamps, per-query results, and the correction to the supplemental hybrid are preserved under `experiments/cliptrail/`.

### Quality limits

- The corpus is small and consists of two public films; it is not representative of personal video libraries.
- One agent created the labels; there was no independent rater audit.
- Queries are positive-only, so absence detection and false-positive calibration were not tested.
- The films may overlap CLIP pretraining.
- Full-video 60-second windowing is an application extension outside this quality measurement.
- These CPU quality results are not a target-device or QNN retrieval evaluation.

## Persistent application measurements

Host: x86_64 WSL2/Linux on an AMD Ryzen 5 5600H. Backend: official CLIP ViT-B/16 through PyTorch/Transformers CPU. Validation library: the complete 52.42-second *Sintel* trailer and two 42.17-second *Tears of Steel* excerpts. The two excerpts are separate files from one film, so this remains a two-film sample.

| Measurement | Recorded value |
| --- | ---: |
| Model load | 5.10 s |
| Index wall time after load | 15.49 s |
| Indexed duration | 2.279 video minutes |
| Throughput | 8.83 video minutes per wall minute |
| Selected scene frames | 48 |
| First query after load | 45.18 ms |
| Later warm queries | 27.45 ms median; 34.70 ms max; n=5 |
| Logical vectors + thumbnails | 570,215 bytes |
| Logical storage rate | 250,186 bytes/video minute |
| Closed SQLite file | 638,976 bytes |
| RSS after multi-video index | 757.6 MB |
| Peak RSS after queries | 913.6 MB |

Index time includes hashing, two-pass decode, image embeddings, and SQLite writes. It excludes model initialization. Logical storage excludes source media, browser-upload copies, SQLite page overhead, and caches. Measurements are single-host diagnostics rather than distributions. A fresh process reopened all three videos and 48 frames and reproduced the top *Sintel* result at 23.25 seconds. A real-model loopback smoke returned the same result, delivered its JPEG, and served a 1,024-byte source-video range.

## Snapdragon/QNN evidence

One explicitly authorized post-cutoff smoke ran on an ASUS Zenbook A14 UX3407NA with Snapdragon X2 Elite X2E88100 and Windows ARM64. The returned evidence supports these statements:

- Native ARM64 Python and ONNX Runtime imported and completed the fixed workload.
- The ORT QNN provider registered and loaded its issued provider library.
- The pinned `QnnHtp.dll` and related HTP libraries were present and loaded.
- Framework mapping reported one QNN subgraph, 423 supported transformed nodes, and no unsupported transformed nodes.
- ORT recorded one completed QNN execution-provider kernel for the graph with CPU fallback controls disabled.
- The QNN image embedding matched the frozen CPU reference: cosine **0.999982834**, maximum absolute difference **0.001173690**.

The returned evidence does **not** contain a positive device execution event, attributable HTP cycles, QNN profile CSV/log, or ETL hardware event export. Physical NPU hardware execution therefore remains unverified. The process also exited with `C0000005` after results and evidence had been persisted; its root cause is unknown. The recorded CPU and QNN call timings used different profiling conditions and do not establish a speed comparison.

No NPU speedup, energy advantage, HP-device deployment, full application target run, production stability, or target retrieval-quality result is claimed.

## Reproducibility map

| Evidence | Canonical files |
| --- | --- |
| Frozen retrieval report | `experiments/cliptrail/results/real-v1-amended/report.json` and `tables.md` |
| Frozen labels and corpus specification | `experiments/cliptrail/datasets/annotations-v1.json`, `windows-v1.json`, and `real-v1/manifest.json` |
| Application measurement | `experiments/cliptrail_app/results/persistent-demo/validation.json` |
| Restart and real HTTP checks | `status-after-restart.json`, `search-after-restart.json`, and `real-http-smoke.json` in the same result directory |
| Target evidence audit | `experiments/cliptrail_target/v2/review/evidence-audit.json` |
| Full target adjudication | `project/planning/cliptrail-deployment-outcome-v2.md` |
| Historical v1 preservation lock | `experiments/cliptrail_target/v2/v1-preservation-lock.json` |

The public repository excludes downloaded model weights, source videos, native runtime packages, generated databases, and deployment bundles. Provisioning scripts and hashes describe how those local assets were obtained.
