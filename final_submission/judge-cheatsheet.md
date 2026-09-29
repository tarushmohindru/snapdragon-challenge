# ClipTrail judge cheatsheet

Use [the full Q&A](../submission/judge-qa.md) for detail. State measured scope with every number.

| Likely question | Immediate answer |
| --- | --- |
| What problem does ClipTrail solve? | It finds visual moments inside local videos using natural language and opens the original source at the ranked timestamp. |
| Why avoid cloud search? | Videos, thumbnails, embeddings, and queries stay on the user's computer; no upload or cloud index is required after local provisioning. |
| Why scene midpoints? | A midpoint represents stable content within a detected scene. It performed best among the equal-budget selectors on the frozen small benchmark. |
| Why not every frame? | Adjacent frames are often redundant; sparse representatives reduce indexing and storage. Brief or subtle events can still be missed. |
| How good is retrieval? | 83.33% Recall@1, 87.50% Recall@3, and 81.82% short-event Recall@3 on 24 positive queries, six windows, two public films. No broad-library claim. |
| How fast is search? | Five post-first warm CPU searches over a prebuilt 48-frame index had 27.45 ms median latency on an AMD Ryzen 5 5600H WSL2/Linux host. |
| How fast is indexing? | One three-video CPU run indexed 2.279 video minutes in 15.49 s after model load: 6.80 s per video minute. |
| How large is the index? | 570,215 logical bytes for vectors and JPEG thumbnails, about 250 KB per video minute; the closed SQLite file was 638,976 bytes. Media is excluded. |
| What was observed on Snapdragon? | A fixed image graph completed native ARM64 ONNX Runtime QNN provider execution; pinned HTP libraries loaded, one QNN partition mapped, and output matched CPU (cosine 0.999982834). |
| Does it run on the NPU? | Physical NPU execution was **not verified**: the required positive device event or attributable HTP cycles were missing. |
| Why no acceleration claim? | There is no verified device-level hardware event and no matched CPU/QNN end-to-end speed or energy comparison. |
| Biggest limits and next step? | Quality uses two films and positive queries; browser codec support varies; the QNN path is experimental. Next: broader independent evaluation and device-level target evidence before hardware claims. |
