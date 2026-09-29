# ClipTrail real-model gate outcome — 20 September 2026

**Reject the current adaptive/hierarchical formulation. Promote BenchProof to the next bounded feasibility experiment. Retain scene-indexed ClipTrail as a working reuse fallback, not the selected competition project.**

The real CPU experiment passed execution/provenance checks and failed all seven adaptive quality checks. This is a negative result from actual OpenAI CLIP ViT-B/16 embeddings, not the older score oracle and not a missing-QNN failure.

## Measured evidence

Six fixed windows, 348 seconds total, 24 natural-language queries (11 short), 1,392 candidate frames. All required comparisons use 16 image encodes + one text encode per query. The CPU reference is torch 2.8.0+cpu / Transformers 4.57.1 on an AMD Ryzen 5 5600H host with two PyTorch threads.

| Method | Recall@1 | Recall@3 | Short-event R@3 | Median / p95 localization error |
| --- | ---: | ---: | ---: | ---: |
| Uniform | 17/24 (70.83%) | 19/24 (79.17%) | 6/11 (54.55%) | 0 / 25.425 s |
| Change maxima | 17/24 (70.83%) | 18/24 (75.00%) | 8/11 (72.73%) | 0 / 27.475 s |
| Scene midpoints | 20/24 (83.33%) | 21/24 (87.50%) | 9/11 (81.82%) | 0 / 18.750 s |
| Existing hierarchical | 11/24 (45.83%) | 13/24 (54.17%) | 2/11 (18.18%) | 1 / 38.087 s |

Hierarchical loses **37.5 pp Recall@1 and 33.33 pp Recall@3** to scene midpoints, with a **63.64 pp short-event deficit**. Its 11 Recall@3 failures all have zero sampled target coverage: reranking the same selected frames cannot repair them. It beats uniform on **zero** Recall@3 queries (ties 18, loses six). Against scene sampling, it wins two queries and loses ten. The clip-cluster bootstrap interval for its Recall@3 difference versus scene is −54.17 to −16.67 pp; the small two-source corpus limits statistical generalization.

Eroding every annotated interval by 0.25 s yields scene 83.33% versus hierarchical 50% Recall@3. Expanding intervals yields 87.5% versus 54.17%. The decision therefore does not hinge on exact cut boundaries.

Median encoding-index / online-query costs: scene **4,162.7 / 24.4 ms**, hierarchical **2,069.4 / 2,103.8 ms**. Cold totals are approximately 4.2 s for both. Hierarchical moves work into the query without an overall cost advantage. Common video decode/change/JPEG preparation is separate (23.85 s for all six windows), as are initialization (3,440.6 ms in this run) and process high-water RSS (841.9 MiB). These are reference-host measurements, not NPU or production indexing numbers.

For four queries per window, cache-demand replay requires 207 unique hierarchical image encodes versus 96 for each fixed index. That is an arithmetic diagnostic, not measured warm-session performance; no amortized benefit is claimed.

## Interpretation

The coarse anchors provide insufficient semantic coverage. Highest observed endpoint similarity is not a reliable upper bound on the contents of an unsampled interval. The algorithm spends its refinement budget around already attractive anchors while missing brief or unrelated states. This agrees with the prior no-hint oracle counterexample. Real CLIP ranking is usable: scene midpoints pass the predeclared usefulness gate. The proposed adaptive contribution is the failed component.

Simple scene indexing is a defensible local retrieval prototype, but the repository already records scene-to-CLIP search prior art [S25] and sparse-sampling prior art [S26]. We have no measured QNN integration, quantization benefit, energy reduction or distinctive deployment improvement to replace the failed contribution. Under the user's engineering/innovation bar, simply packaging that baseline is not yet competition-worthy. BenchProof is promoted **for investigation**, not asserted to work; PatchCore prior art and its own feature-export/robustness gates remain.

## Control defect and correction

Review discovered that the supplemental v1 hybrid accidentally used `changed(changes, N)`, whose sorted return value contains every timestamp. Thus it selected early chronological frames rather than the intended strongest distinct changes. The required uniform/change/scene/hierarchical methods are unaffected. Preserve the original report and protocol lock; do not cite the buggy hybrid's 45.83% Recall@3 as a valid hybrid baseline.

`correct_hybrid.py` explicitly registers and reruns only that control with half uniform plus descending change priority, skipping duplicates. Its separate amended report reuses the original required-method outputs, records the post-run correction and retains all raw embeddings/costs. The strongest required baseline already defeats every adaptive quality gate irrespective of this correction. Regression tests check late change peaks, not just budget cardinality.

The correction completed: hybrid Recall@1 **66.67%**, Recall@3 **75%**, short Recall@3 **54.55%**. The amended audit passes all 120 cases and 2,040 raw vector records, including selector replay. Only scene midpoints pass the simple usefulness gate. There are 15 passing correctness tests. The complete primary-plus-correction workload used 2,304 image and 144 text encodes, excluding warm-ups and the separate smoke proof.

## Scope and artifacts

This is within-window retrieval on two public films, not whole-library search, personal-video validation or a product/user study. Labels were agent-annotated before benchmark scores, with no independent human review; fades, morphs and framing are confounders. CLIP's center crop can remove peripheral content. No absent-event calibration, NPU execution, power or Windows deployment result is claimed.

- Frozen protocol: `cliptrail-mve-protocol.md` (kept byte-identical for audit).
- Data: `experiments/cliptrail/datasets/annotations-v1.json`, `real-v1/manifest.json`, `manifest.lock.json`.
- Original evidence: `experiments/cliptrail/results/real-v1/report.json`, raw `embeddings.f32`, `audit.json`, `tables.md`.
- Corrected supplemental control: `experiments/cliptrail/results/real-v1-amended/`.
- Fresh source-video decoding reproduced all 1,392 frame hashes: `results/real-v1/corpus-reproduction.json`.
- Real CPU smoke: `results/clip-cpu-real-smoke.json`; installed package freeze and source hashes retained.

Do not retune the hierarchical strategy against these labels. No UI, ShareGuard work or submission materials were produced in this stage.
