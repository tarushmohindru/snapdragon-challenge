# ClipTrail local application architecture — frozen pipeline and demo interface

Frozen 22 September 2026 before application implementation. The source of truth for the measured scene rule and CLIP CPU adapter remains `experiments/cliptrail/benchmark_core.py`, `sampling.py`, and `reference_backend.py`; their frozen bytes are not changed.

## User flow

Local video or folder → decode at 4 Hz → raster-change signal (96×54 bilinear RGB mean absolute difference / 255) → scene boundaries and midpoints → CLIP image embeddings → SQLite index and thumbnails → CLIP text embedding → cosine ranking → timestamped results → open local player at selected timestamp.

The CLI uses separate processes for `index` and `search`; the demo server keeps one backend loaded for its lifetime. Indexing persists normalized float32 `[512]` vectors, image previews, source path/identity, source timestamps, model identity, and the selector version. A prebuilt index never needs image inference during a query. All files and inference stay local. An interrupted index build leaves the previous committed video index intact; a changed source is replaced as one SQLite transaction after successful decoding and embedding. File hashes distinguish changed content. CLI status reports decode/encode progress, per-video completion and failures; a folder continues past an individual bad video and exits nonzero with a summary.

## Preserved and extended behavior

The `scene` selector is called directly from the frozen benchmark code: it ranks change scores, enforces the same three-frame cut spacing, creates boundaries, and selects midpoint candidate frames. Ranking calls the frozen cosine function and sorts by decreasing score, then timestamp. The CPU backend delegates to the frozen `ClipReference.encode_image` and `encode_text` methods. No other selector or alternative model is introduced.

The validated corpus uses preselected 40–60 second windows with a **16-frame budget per window**. The application must handle arbitrary full videos. It divides them into fixed 60-second windows anchored at playback time zero and selects `min(16, candidate count)` frames in each window, including the last partial window. The first sample of each window gets change score zero, as in the frozen corpus. This segmentation rule is an application extension and has no measured retrieval-quality claim. Within a window whose frames match the benchmark preparation, the selector and scoring behavior are identical. Whole-library ranking and quality are not established by the six-window frozen benchmark.

Decode uses PyAV frame presentation times, RGB/Pillow resizing and change calculation from the frozen preparation script. A first pass records sampled timestamps/change without saving every full-resolution frame. A second pass saves only selected frames, preserving actual presentation timestamp for playback and JPEG thumbnails for results. For a source with nonzero stream start PTS, playback time is relative to that start. The app does not rewrite source media.

## Modules and boundaries

| Module | Responsibility |
| --- | --- |
| `cliptrail_app/legacy.py` | Import the frozen benchmark selector, cosine scorer and CPU adapter without editing locked experiment files. |
| `cliptrail_app/video.py` | Local media discovery, 4 Hz candidate decode, fixed-minute windows, selected-frame extraction and timestamps. |
| `cliptrail_app/backends.py` | `EmbeddingBackend` protocol; CPU CLIP implementation. Optional QNN image backend uses the existing extracted image graph and CPU CLIP text tower behind the same protocol. A QNN backend is experimental and has no physical NPU verification claim. |
| `cliptrail_app/store.py` | SQLite schema, transactional per-video replacement, model/version isolation, persistent vectors and thumbnails. |
| `cliptrail_app/search.py` | One text encode per query, vector checks, cosine ranking, stable ties and result projection. |
| `cliptrail_app/playback.py` | Launch an installed local player at the returned timestamp using an argument list. |
| `cliptrail_app/cli.py` | `index`, `search`, `open`, `status`, and `metrics`; progress and errors. |
| `cliptrail_app/web.py` | Loopback-only HTTP server, one lifetime backend, serialized inference, background indexing, status and local media endpoints. Calls the existing index/search/store/playback modules. |
| `cliptrail_app/web_assets/` | Minimal browser selection, progress, library, query, results and timestamped playback. No CDN or remote service. |

One video can be indexed alone or through a folder walk. Search is scoped to the active backend identity so incompatible vectors cannot mix. CPU is the default. The optional QNN backend uses the previously validated image graph and its raw-input preprocessing, with the same CLIP text tower; it must reject fallback and identify its graph in the index. Since the v2 process exited abnormally and hardware profiling evidence is absent, availability of that adapter does not imply production stability or NPU execution.

## Reliability and measurement

Reject nonfinite/wrong-dimension image or text vectors, empty videos, missing source at playback and unsupported video types. A failed reindex never deletes the prior committed rows. SQLite foreign keys and transactions preserve video/frame consistency. Query costs are measured with a prebuilt index, separately from model startup. Per-video index metrics include source duration, selected frame count, elapsed indexing time, bytes of persistent index/preview data per video minute and process peak RSS where available. These are local diagnostic results and cannot establish Snapdragon speed or energy advantage.

The frozen CPU benchmark remains unchanged. An offline application-level replay uses its recorded scene embeddings/queries to verify identical frame selection, ranking, timestamp mapping and R@1/R@3 without rerunning the earlier model experiment.

## Demo application feature freeze — 22 September 2026

The local server accepts one video, a browser-selected folder or a filesystem path, persists the index in the same SQLite store and returns ranked results from the same `search` function. Browser-selected files are copied to a local `uploads/` directory before indexing so the server can reopen them later. The browser seeks its local HTML5 player to the stored timestamp. A native local-player action remains available for codecs the browser cannot decode. The interface shows indexing/search state and distinguishes CPU CLIP from experimental QNN without implying physical NPU execution.

Application validation indexed three videos in one process and reopened the saved index in another. Six searches reused the same loaded CPU model. The first had 45.18 ms query latency; the five later searches had a 27.45 ms median. HTTP integration tests cover local upload, background progress, persisted search, thumbnails, byte-range video transfer and player launch response. Browser pixels/audio could not be observed on the headless host, so visual playback is still a device-specific check. Full measurements are in [`persistent-demo/validation.json`](../../experiments/cliptrail_app/results/persistent-demo/validation.json). Features are frozen at this demo scope; no accounts, cloud, RAG, LLM or additional retrieval modes are planned.
