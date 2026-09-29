# Likely judge Q&A

## Product and user value

### 1. What problem does ClipTrail solve?

It finds visual moments inside local video files using natural language. Users get ranked thumbnails and timestamps and can play the original video at the selected moment without uploading it.

### 2. Who is it for?

People and teams with private, poorly labeled video libraries: creators, researchers, educators, families, and professionals reviewing local footage. The current prototype is a general local search tool rather than a vertical-specific workflow.

### 3. Why not use filenames, transcripts, or tags?

Filenames and manual tags are incomplete, while transcripts miss visual events and videos without speech. ClipTrail searches visual content. Transcripts could be complementary in future work, but they are outside this feature-frozen submission.

### 4. What is the key product differentiator?

The combination of local-only processing, scene-aware sparse indexing, persistent search, and direct timestamped playback. The user gets semantic retrieval without sending source media to a cloud index.

### 5. Does the application require an internet connection?

Provisioning downloads the model and dependencies. After those assets exist locally, application indexing, persistence, querying, and playback use no cloud service or remote model API.

### 6. What data leaves the computer?

The application is designed so videos, thumbnails, embeddings, queries, and results remain local. The server binds to loopback. The submission does not claim a formal network-isolation certification.

## Technical design

### 7. How does scene selection work?

ClipTrail samples at 4 Hz, computes mean RGB raster change on 96×54 frames, enforces a three-sample separation between cuts, forms scene spans, and chooses span midpoints. It stores up to 16 selected frames per fixed 60-second window.

### 8. Why scene midpoints?

They avoid transition frames and represent the stable visual content inside a scene. On the frozen small corpus, scene selection performed better than equal-budget uniform, change-only, corrected hybrid, and hierarchical alternatives.

### 9. Why not embed every frame?

Embedding every frame increases indexing time and storage with many near-duplicates. Sparse representatives make a local persistent index practical. The tradeoff is that very brief or visually subtle events can be missed.

### 10. What model is used?

OpenAI CLIP ViT-B/16 through a pinned Transformers/PyTorch CPU reference implementation. Image and text vectors are normalized 512-dimensional embeddings ranked with cosine similarity.

### 11. Is an LLM or RAG system involved?

No. CLIP maps text and images into a shared embedding space. Search is direct cosine ranking over stored vectors.

### 12. Why SQLite?

It is local, durable, portable, transactional, and sufficient for the current scale. It stores video identity, model/sampler identity, timestamps, normalized vectors, thumbnails, and indexing metrics in one file.

### 13. What happens when a source video changes?

The source hash changes. ClipTrail builds the replacement and commits it transactionally, so a failed rebuild does not erase the previous usable index.

### 14. Can CPU and QNN embeddings mix?

No. Every stored video index has a backend identity. Search reads only rows matching the active backend, preventing accidental comparison across incompatible model or graph identities.

### 15. How does playback work?

The result stores the original presentation timestamp. The browser requests the local source with HTTP byte ranges and seeks to that timestamp. A native-player path is available when the browser does not support the codec.

## Evidence and performance

### 16. How good is retrieval?

Scene indexing reached 83.33% Recall@1 and 87.50% Recall@3 on 24 positive queries across six windows from two public films. Short-event Recall@3 was 81.82% on 11 queries. This is a small frozen benchmark, not a general accuracy claim.

### 17. What does Recall@3 mean here?

A query counts as successful when at least one of the top three selected timestamps falls inside a predeclared matching interval for that query.

### 18. How fast is search?

With one loaded CPU model and a prebuilt 48-frame index, five repeated searches had 27.45 ms median latency and 34.70 ms maximum on the recorded AMD Ryzen 5 5600H WSL2/Linux host. Model startup and indexing are separate.

### 19. How fast is indexing?

The three-video validation indexed 2.279 video minutes in 15.49 seconds after model load, or 6.80 seconds per video minute, on the same CPU host. This is one run, not a cross-device distribution.

### 20. How large is the index?

The same run stored 570,215 logical bytes of normalized vectors and JPEG thumbnails, about 250,186 bytes per video minute. The closed SQLite file was 638,976 bytes. Source media, uploaded local copies, caches, and database page overhead are separate.

### 21. How much memory does it use?

Whole-process RSS was 757.6 MB after multi-video indexing and 913.6 MB after repeated queries in the recorded run. CLIP/PyTorch dominates memory; memory optimization remains future engineering.

### 22. How reproducible are the results?

The repository retains frozen annotations, corpus manifests and hashes, exact model revision and dependency versions, raw embeddings, per-query reports, audit scripts, application measurements, tests, and target logs. Generated weights and media are downloaded rather than committed.

### 23. What are the largest benchmark limitations?

Only two source films, 24 positive queries, one annotator, no absence-query calibration, and possible CLIP pretraining overlap. The application’s full-video windowing was not evaluated as a separate quality benchmark.

## Snapdragon and QNN

### 24. Does ClipTrail run on the Snapdragon NPU?

The strict answer is that physical NPU execution was not verified. A fixed CLIP image graph completed native ARM64 ONNX Runtime QNN inference on an ASUS Snapdragon X2 Elite with the pinned HTP backend loaded and one QNN partition. The required positive hardware event or attributable HTP cycles were missing.

### 25. What exactly did the target smoke prove?

It proved native ARM64 runtime operation for the fixed workload, QNN provider loading, HTP library loading, provider-level graph execution with fallback controls disabled, QNN partition mapping, and output parity with CPU.

### 26. How close was QNN output to CPU?

The QNN embedding versus the frozen CPU reference had cosine similarity 0.999982834 and maximum absolute difference 0.001173690 for one fixed image.

### 27. Why do you not claim acceleration?

There is no comparable end-to-end CPU/QNN benchmark under matched conditions and no captured device-level execution evidence. One host-observed provider duration cannot establish NPU speed, throughput, or energy benefit.

### 28. What happened after the QNN run?

The output, placement trace, parity result, and final evidence state were persisted. The native process then exited with `C0000005`. The root cause is unknown, so the QNN backend is experimental and not presented as production-stable.

### 29. Was the application deployed on the target?

No. The target attempt exercised the fixed image graph, not the full ClipTrail application. No HP-device deployment was performed; the observed target was an ASUS Snapdragon X2 Elite system.

### 30. Why include the QNN backend at all?

It keeps application logic independent of the image inference runtime and demonstrates a concrete Windows ARM64/QNN compatibility path. It is valuable architectural work as long as its unverified hardware and stability boundaries remain explicit.

## Delivery and next steps

### 31. What would you improve next?

After submission, the highest-value product work would be broader independently labeled evaluation, larger-library scaling, memory reduction, and target application validation. A device-level QNN profile would be needed before any physical NPU or acceleration claim.

### 32. Why should this project advance despite incomplete NPU proof?

ClipTrail is already a usable local product with measured retrieval, persistent indexing, fast warm search, and a clean demo. The Snapdragon path has meaningful provider-level evidence, and the project reports the missing proof rather than converting it into a marketing claim.
