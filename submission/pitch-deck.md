# ClipTrail pitch deck content

## Slide 1 — Find the moment. Keep the video local.

**ClipTrail**

Private, scene-aware search for local video

Describe a scene → see ranked moments → play the source at the timestamp

**Speaker note:** Video filenames cannot tell us what happens inside a recording. ClipTrail lets people search the contents of private videos without uploading them.

## Slide 2 — The problem is inside the file

- Personal and work video libraries are hard to search.
- Exact timestamps are buried behind manual scrubbing.
- Cloud indexing adds upload time, recurring storage, and privacy exposure.
- Embedding every frame wastes compute and storage.

**Speaker note:** The user needs a moment, not another file list. The product should understand visual content while keeping the source under local control.

## Slide 3 — A local semantic index of scenes

1. Select a video or folder.
2. Sample locally at 4 Hz and detect visual transitions.
3. Choose representative scene midpoints.
4. Store CLIP image embeddings, thumbnails, and timestamps in SQLite.
5. Search with natural language and play the ranked moment.

**On-slide line:** No cloud, account, RAG pipeline, or LLM.

## Slide 4 — Built for repeat use

- Persistent index: videos are not re-embedded for every search.
- Lifetime model: repeat queries avoid model startup.
- Sparse index: 48 representative frames for 2.279 video minutes in the recorded demo library.
- Transactional replacement: a failed reindex preserves the previous usable index.
- Browser and CLI share one retrieval implementation.

**Speaker note:** The product path is deliberately small. It turns measured retrieval code into a durable local tool rather than a one-off notebook.

## Slide 5 — Measured product behavior

**Recorded CPU host: AMD Ryzen 5 5600H, WSL2/Linux**

| Metric | Result |
| --- | ---: |
| Warm query latency | **27.45 ms median** across five repeat queries |
| Indexing | **6.80 s per video minute** after model load |
| Persistent payload | **250 KB per video minute** for vectors + JPEGs |
| Frozen scene retrieval | **87.50% Recall@3** |

**Scope line:** Quality uses 24 positive queries across six windows from two public films. Performance is CPU-only on the recorded host.

## Slide 6 — Snapdragon path, stated precisely

**Observed on an ASUS Snapdragon X2 Elite**

- Native ARM64 runtime completed the fixed graph.
- ONNX Runtime QNN provider loaded.
- Pinned HTP backend libraries loaded.
- One QNN partition executed at the provider boundary.
- QNN/CPU embedding cosine: **0.999982834**.

**Boundary:** Hardware device events were not captured. Physical NPU execution, speedup, energy savings, HP deployment, and full target-app performance remain unverified.

**Speaker note:** The architecture is ready for a QNN image backend, and the fixed graph passed provider-level compatibility and parity. We stop the claim exactly where the evidence stops.

## Slide 7 — Why ClipTrail is worth advancing

- A working local product with a clear 60–90 second demo.
- Immediate user value: search private video by meaning and jump to the moment.
- Efficient product shape: scene-aware sampling, persistent embeddings, fast warm retrieval.
- A clean CPU/QNN backend boundary for future Windows ARM64 work.
- Reproducible benchmarks and preservation of both successful and negative evidence.

**Closing line:** ClipTrail makes private video searchable today, with an evidence-backed path toward Snapdragon optimization tomorrow.
