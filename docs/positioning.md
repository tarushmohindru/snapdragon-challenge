# ClipTrail positioning and title

## Recommended title

**ClipTrail — Private, Scene-Aware Search for Local Video**

This title names the product, explains the differentiator, and avoids implying measured NPU acceleration.

## One-line position

ClipTrail turns a natural-language description into a ranked, playable moment from videos indexed entirely on the user's computer.

## Short position

Private video libraries are difficult to search because filenames and folders say little about what happens inside a recording. ClipTrail samples video locally, selects representative scene midpoints, embeds those frames with CLIP, and saves a compact semantic index. After indexing, users can search with phrases such as “a red-haired woman surrounded by burning rubble” and jump directly to the matching moment. The working application uses a verified CPU backend; an experimental Windows ARM64/QNN image backend preserves the same application interface.

## Value pillars

- **Private by construction:** media, embeddings, thumbnails, queries, and playback remain local.
- **Search moments, not files:** results include a representative frame, filename, timestamp, similarity score, and direct playback.
- **Sparse persistent indexing:** scene-aware selection stores a small number of representative frames instead of embedding every frame or reprocessing videos for each query.
- **Fast repeat search:** the persistent application keeps CLIP loaded and searches prebuilt image vectors with one text encoding.
- **Portable inference boundary:** CPU CLIP and the experimental QNN image path implement the same backend contract.
- **Auditable claims:** frozen labels, raw vectors, manifests, hashes, tests, negative outcomes, and target evidence are retained with explicit limits.

## Title candidates

1. **ClipTrail — Private, Scene-Aware Search for Local Video** *(recommended)*
2. **ClipTrail — Find the Moment. Keep the Video Local.**
3. **ClipTrail — Natural-Language Search for Your Video Library**
4. **ClipTrail Local — Semantic Video Search Without the Cloud**
5. **ClipTrail — Sparse Semantic Indexing for Private Video**

## Submission tagline

**Describe a scene. Jump to the moment. Keep every video local.**

## Claim language

Use “Windows ARM64/QNN-compatible experimental backend” or “QNN graph execution observed on Snapdragon.” Do not use “NPU accelerated,” “runs on the NPU,” “faster on Snapdragon,” “energy efficient,” or “deployed on HP hardware.” Direct physical NPU execution, acceleration, energy benefit, and HP deployment were not measured.
