# ClipTrail real-model falsification

**Outcome: reject the current adaptive strategy.** Scene-midpoint Recall@3 is 87.5%, hierarchical 54.17%; short-event Recall@3 is 81.82% versus 18.18%. Scene indexing remains a useful fallback. BenchProof is the next feasibility candidate. See the [decision](../../project/planning/cliptrail-mve-outcome.md) and [canonical amended tables](results/real-v1-amended/tables.md).

The original supplemental hybrid had a priority-order bug. Its corrected control was rerun separately and reaches 75% Recall@3. The required uniform/change/scene/hierarchical results are unchanged. The original report and immutable protocol remain available for audit; use the amended report for the full five-method comparison.

OpenAI CLIP ViT-B/16 now runs locally through Transformers/PyTorch CPU. This experiment tests the existing hierarchical sampler against uniform, raster-change, scene-midpoint and uniform/change hybrid sampling. No UI or Snapdragon performance claim is included.

The [protocol](../../project/planning/cliptrail-mve-protocol.md) predeclares survival/kill thresholds. The [frozen corpus](datasets/real-v1/manifest.json) has six nonoverlapping windows, 24 natural-language queries, 11 short-event queries and 1,392 frames at 4 Hz. Each method receives **16 image encodes and one text encode per cold query**, including refinement. Query-level Recall@1/3, timestamp error, short-event recall, coverage and actual stage costs are recorded.

The [real report](results/real-v1/report.json) records run status and individual results; a verdict exists only after successful completion. The prior [oracle diagnostic](results/sampling-oracle.json) remains negative evidence: hierarchical 2/4 versus change 3/4. It is not CLIP accuracy.

## Environment and model proof

From a network-capable WSL/Linux terminal at repository root:

```bash
bash experiments/cliptrail/provision_reference.sh
```

No global installs or QNN dependency. This creates `.venv-cliptrail`, fetches the official Hugging Face revision `57c216476eefef5ab752ec549e440a49ae4ae5f3`, and downloads the public source videos. About 2 GB is used by the environment and source assets, plus decoded frames. Actual files and hashes are in [provisioning.json](results/provisioning.json); exact installed versions in [reference-freeze.txt](results/reference-freeze.txt). Downloads are separate from inference; the adapter loads local assets only.

[clip-cpu-real-smoke.json](results/clip-cpu-real-smoke.json) contains actual 512D image/text vectors from **excluded** Tears of Steel times 100 s and 110 s. These images were not benchmark examples and the smoke query was not used to select annotations. `run_clip_legacy.py` preserves the earlier upstream-CLIP adapter attempt; current scripts use Transformers.

## Reproduce the frozen benchmark

The original videos and decoded images are excluded from Git. Download with the provisioner, then regenerate pixels without relabeling:

```bash
.venv-cliptrail/bin/python experiments/cliptrail/prepare_corpus.py \
  --spec experiments/cliptrail/datasets/windows-v1.json \
  --output experiments/cliptrail/datasets/replay-v1
cp experiments/cliptrail/datasets/real-v1/manifest.json \
  experiments/cliptrail/datasets/replay-v1/manifest.json
cp experiments/cliptrail/datasets/real-v1/manifest.lock.json \
  experiments/cliptrail/datasets/replay-v1/manifest.lock.json
.venv-cliptrail/bin/python experiments/cliptrail/run_benchmark.py \
  --manifest experiments/cliptrail/datasets/replay-v1/manifest.json \
  --output experiments/cliptrail/results/replay-v1 --threads 2
.venv-cliptrail/bin/python experiments/cliptrail/audit_results.py \
  --manifest experiments/cliptrail/datasets/replay-v1/manifest.json \
  --report experiments/cliptrail/results/replay-v1/report.json
```

Output directories must be new, so reruns cannot silently overwrite evidence. The runner verifies every frame hash and the frozen manifest/protocol/code before loading the model. Regenerated pixels must match the pinned decoder/Pillow output; a hash mismatch is an invalid reproduction, not a model failure. On the original corpus, use `datasets/real-v1/manifest.json` and a new results directory.

Those commands reproduce frozen v1, including its documented supplemental-control defect. Apply the explicit correction afterward:

```bash
.venv-cliptrail/bin/python experiments/cliptrail/correct_hybrid.py \
  --manifest experiments/cliptrail/datasets/replay-v1/manifest.json \
  --original experiments/cliptrail/results/replay-v1/report.json \
  --output experiments/cliptrail/results/replay-v1-amended
.venv-cliptrail/bin/python experiments/cliptrail/audit_results.py \
  --manifest experiments/cliptrail/datasets/replay-v1/manifest.json \
  --report experiments/cliptrail/results/replay-v1-amended/report.json \
  --original experiments/cliptrail/results/replay-v1/report.json
.venv-cliptrail/bin/python experiments/cliptrail/summarize_report.py \
  experiments/cliptrail/results/replay-v1-amended/report.json
```

The amendment encodes only the corrected hybrid control, copies the unaffected measured rows/vectors explicitly, records its own script hash before execution and preserves the original report. Total recorded experimental work is 2,304 image and 144 text encodes across primary plus correction, excluding warm-ups and the separate smoke proof. The canonical comparison itself contains equal 384 image and 24 text encodes per method. `results/real-v1/corpus-reproduction.json` confirms independent source decoding matched all 1,392 original frame hashes.

`embeddings.f32` stores the actual normalized vectors as little-endian float32, 512 values per record; each result records offsets. The audit recomputes scores/rankings/metrics from these vectors, verifies distinct offsets and actual calls, and checks repeated-frame consistency. Cost records exclude serialization, common decode preparation and model initialization; those are reported separately. Peak RSS is whole-process high-water memory.

## Annotating a new corpus

`prepare_corpus.py` emits a draft manifest and 4 Hz contact sheets. Fill queries as in [annotations-v1.json](datasets/annotations-v1.json), review **all matching intervals**, then freeze with `freeze_benchmark.py`. Each query has text, intervals, rationale and confounders. Validation requires six windows, two distinct videos, 24 queries and eight short-event queries. The checked-in v1 annotations were produced by agent visual inspection before benchmark CLIP output, not independent human raters.

The two source films are a convenience corpus with animation, compositing, camera motion, repeated characters and short cuts. They are not a representative test of screen recordings, lecture content or personal videos. Positive-only queries do not measure false positive/absence calibration. CLIP may have seen related public imagery in pretraining. No model fine-tuning, query rewriting or test-set parameter tuning was used.

## Correctness checks

```bash
.venv-cliptrail/bin/python -m unittest discover \
  -s experiments/cliptrail -p 'test_*.py' -v
```

Tests check budgets, evaluator boundaries, inclusion of misses in localization, repeated occurrences and annotation validation. Test doubles are isolated to unit tests; the benchmark has no mock or oracle mode. An environment/data failure exits nonzero and produces no model verdict.

## Interpreting the comparison

Cold-query inference budgets are matched. The cache-demand diagnostic only counts the unique frames a session could reuse; it is **not** measured warm-session performance or an equal-session-budget quality comparison. Uniform/scene indexes can reuse all 16 embeddings across queries, whereas hierarchical refinement may add new embeddings. A later amortized-efficiency claim would need expanded baseline indexes at that same cumulative budget.

CPU results do not establish Windows ARM64 compatibility, QNN execution, NPU utilization, power savings or target latency. See the current [benchmark and target evidence summary](../../docs/evidence.md). The failed adaptive gate is retained as negative evidence; it is not presented as product innovation.
