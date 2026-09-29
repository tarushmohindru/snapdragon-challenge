# Real temporal retrieval corpus v1

`windows-v1.json` selects 348 seconds of real public footage: the first 48 seconds of the Sintel trailer and five 60-second Tears of Steel windows starting at 20, 140, 260, 380 and 500 seconds. These fixed chronological offsets were selected before CLIP benchmark results. Windows do not overlap. Source URLs, attribution and hashes are retained.

`annotations-v1.json` contains 24 natural-language queries with all visually identified matching intervals. Eleven queries have only short (≤2 s) occurrences. All intervals are half-open, measured relative to their window. `real-v1/manifest.json` adds 1,392 candidate-frame timestamps, image hashes and raster-change scores; `manifest.lock.json` binds data, code and protocol before inference.

Annotations came from agent visual inspection of full-window 1 Hz overviews, 4 Hz contact sheets for transient/repeated shots, and boundary montages. No tested CLIP similarities were used to select labels or queries. They are not independent human annotations. Uncertainty includes fades, morphing objects, partial views and approximately 0.25-second boundary precision. The protocol predeclares ±0.25-second boundary diagnostics. The CPU smoke test used excluded film times 100 and 110 seconds and a generic query.

The task is **temporal retrieval within a known 48–60 second window**, not searching the entire two-film library. This small test can falsify an advantage of the sampler; it cannot establish product quality for hours-long recordings. Two related cinematic sources, repeated actors and possible CLIP pretraining overlap limit generalization. The dataset has positive queries only, so an absent-event detector or calibrated confidence is not being evaluated.

Original videos, contact sheets and decoded frames are local evaluation assets excluded from Git. The manifest and preparation script permit reproducible regeneration. See the experiment README for commands. Do not overwrite v1 labels after inspecting results; record any discovered annotation defect separately and preserve the locked primary result.
