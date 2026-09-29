# ClipTrail real-model kill gate — protocol v2

Predeclared: 2026-09-20, before any real model inference. Supersedes the archived v1 Hit@5 proposal. **Status: assets/annotations pending; no real retrieval results.** Deadline: 30 September. This is a falsification test, not an application build.

## Claim under test

At a fixed total image-encoder budget, half-uniform indexing followed by query-conditioned interval bisection improves retrieval of visible events over straightforward sampling. The existing `sampling.py::hierarchical` is frozen: prioritize the interval with the strongest observed endpoint score, break ties by width then earlier position, encode its midpoint, repeat. No dense embedding access, learned scheduler, or revised algorithm after seeing results.

The previous oracle result (hierarchical 2/4 constructed cases, change 3/4) is **negative mechanistic evidence**, not measured CLIP accuracy. Local inference and a useful search interface alone are established prior art. Snapdragon acceleration is a separate gate and cannot rescue missing retrieval evidence here.

## Real reference runtime

Official `openai/clip-vit-base-patch16` checkpoint, pinned to the actual downloaded revision and SHA-256 hashes. Transformers CLIPModel on CPU, float32, eval/inference mode, one image per encode, official image processor and tokenizer; normalized 512D embeddings, cosine similarity. No prompt ensemble or query reformulation. Exact natural-language query is the text input. Offline loading; no remote code. Record processor/config/runtime versions, thread count, initialization, warm-up, preprocessing, inference, peak process RSS. This validates the algorithm only, not Windows/QNN/NPU execution.

## Corpus and independent annotation

Minimum **six 40–90 s windows, two source videos, 24 queries, eight short-event queries**. Start with locally downloaded Blender Sintel trailer and Tears of Steel; inspect actual assets before choosing windows. Do not invent timestamps. Preserve source URLs, attribution, original video hashes, selected offsets and selection rationale. Two films are a narrow convenience corpus, not representative proof for all personal/screen recordings.

Use a 4 Hz candidate grid (0.25 s); frame timestamps are actual decoded presentation timestamps. An event must last at least 0.5 s and intersect the grid. Short means **every relevant interval is ≤2.0 s**; report mixed-duration queries separately. Include cuts, motion, long states, brief states, repeated objects and visually similar distractors. Do not construct sequences around the sampler's anchors. At least four natural-language visual-state queries per window, without template prompt engineering. No subtitle/transcript, small-text, invisible intent or action-order claims.

Annotate **all matching intervals**, not just the intended first occurrence. Record half-open intervals [start,end), plain-language rationale and confounders. Inspect raw/contact-sheet frames and boundary frames before any model result. One annotator, no human reliability estimate; boundary uncertainty ≤0.25 s where possible. Freeze the final manifest, this protocol and implementation hashes before inference with `freeze_benchmark.py`; changes invalidate the lock and require a documented new experiment. No tuning/holding out frame-level pseudo-splits: all cases form one small falsification set, with per-source/per-window results.

## Matched-budget methods

Primary **B=16 image encodes + 1 text encode per independent cold query**, on exactly the same candidate frames. Run all methods separately with no cross-method embedding cache. Image encoding at query time is charged, including refinement. No early stopping that leaves a weaker baseline under budget.

| Method | Selection | Main vulnerability |
| --- | --- | --- |
| uniform | existing evenly spaced timestamps, endpoints included | short events between samples |
| change | existing top raster-change scores with >2-grid-index suppression | camera motion/fades consume samples |
| scene | top B−1 suppressed raster-change cut candidates, midpoint per resulting segment | inferred cuts are imperfect |
| hybrid | B/2 uniform + strongest distinct change samples | splits budget between two imperfect heuristics |
| hierarchical | unchanged half-uniform + score-guided interval bisection | no anchor hint / semantic distractors |

Cheap change signal: mean absolute RGB difference between consecutive 96×54 thumbnails, normalized to [0,1]. Scene boundaries use ≥3-grid-index separation. These are fixed, untrained baselines; no threshold sweep. Frames decoded for the change pass count as CPU work; reducing CLIP calls does not remove video decoding.

All methods must encode exactly min(B,N) distinct images. Hierarchical uses only scores requested via its encoder callback. Labels are evaluator-only. Top-3 refers to three frames ordered by cosine (ties earlier first), **without label-based suppression**. Also report coverage of any sampled matching frame to separate sampling failures from ranking failures. Adjacent duplicates may hurt all methods; no post-hoc reranker.

## Measurements

For query q with relevant interval union Gq and ranked timestamps t1…tk:

- **Recall@k** = mean_q 1[there exists j≤k with tj ∈ Gq], k=1,3. This is query-level temporal success, not the fraction of all repeated events recovered.
- **Localization error** = min_[a,b)∈Gq max(a−t1, 0, t1−b), seconds. A timestamp exactly at b is a retrieval miss but zero distance to the interval boundary. Report median/p95 over **all queries**, including failures. Also report midpoint distance separately; do not substitute it for the primary metric.
- **Short-event Recall@1/3**, coverage, per-source/per-clip metrics and individual failures.
- Per query: actual image/text encoder calls, selected timestamps/scores, ranking, image preprocessing/forward time, text preprocessing/forward time, index time, online query time, total warm-model time. Model initialization/warm-up and common video decode/change preparation are reported separately. No simulated latency. Peak process RSS is process high-water mark, not NPU/model-only memory.
- Cold comparison recreates each index per query to make budget accounting and timing explicit. Query-time encodes count toward B. Report median/p95 costs; rotate method execution order deterministically to reduce order bias. Single-host CPU times are descriptive, not battery/NPU/production claims.
- Multi-query **cache-demand diagnostic**: number of unique frame encodes per method/window across its fixed query set, assuming reuse. This is arithmetic replay, not measured warm-session latency or an equal-session-budget quality comparison. Never claim an amortized advantage from cold-query results. Expanded uniform/change baselines are required before any later session-level efficiency claim.

## Predeclared decisions (no rescue by an optional metric)

Adaptive v1 **survives provisionally only if all hold**:

1. Hierarchical Recall@1 **and** Recall@3 each exceed the best corresponding score among uniform/change/scene/hybrid by **≥10 percentage points**.
2. Hierarchical short-event Recall@3 is no more than **5 pp below** the strongest baseline on short events; overall Recall@3 **≥80%**.
3. Its median localization error is no more than **0.5 s worse** than the best baseline; Recall@3 improvement is positive in at least half of windows and neither source loses more than 5 pp relative to its strongest baseline.
4. Exact budget/label isolation/provenance checks pass. No hidden dense inference or synthetic embeddings.

Failure of any quality condition **kills this adaptive formulation for the competition deadline**. It does not prove every adaptive retrieval algorithm fails. Do not modify it and repeatedly test against the same labels. Missing dependencies/assets, invalid annotations, or execution errors are **blocked/invalid experiments**, never negative model results.

A simpler formulation clears a **usefulness gate** only if one fixed baseline achieves Recall@1 ≥60%, Recall@3 ≥80%, short-event Recall@3 ≥60%, median localization error ≤1 s, and each source Recall@3 ≥60%. This is insufficient by itself for competition-worthy novelty. If adaptive fails, inspect whether there is already measured distinctive systems/deployment work. With none, do not market ordinary CLIP search as the contribution: promote BenchProof to its own bounded real-feature kill gate, retaining simple ClipTrail only as reuse fallback. A later genuine deployment contribution may warrant reconsideration; vendor numbers do not.

Report paired deltas, integer wins/losses and a deterministic 2,000-resample **clip-cluster bootstrap** interval for Recall@1/3 deltas. With six windows/two sources, uncertainty is substantial; intervals excluding zero are not required for this small engineering gate and a pass is provisional, not publication-grade evidence.

Predeclared annotation sensitivity: recompute metrics after expanding and eroding each interval by 0.25 s at both ends; retain the original short-event membership. Report both, with no new embeddings or label edits. These diagnostics cannot replace the primary gate. Annotations are produced by the agent's visual inspection, not independent human raters; this limits any positive generalization claim. Runtime smoke inference on excluded footage is allowed before annotation, but no benchmark frame/query scores may be inspected before freeze.

## Snapdragon gate, explicitly separate

Existing evidence: AI Hub combined CLIP graph, released float/w8a16 ONNX asset metadata and vendor X Elite profiles. Neither downloaded target assets nor actual NPU execution are proven. CPU results will not be relabeled as QNN. Later: fetch exact asset, verify input preprocessing/tokens, compare embeddings, run native ARM64 ORT/QNN, inspect HTP execution and measure application costs. This stage is not a prerequisite for CPU inference.
