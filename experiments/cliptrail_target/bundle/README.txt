ClipTrail: one-image Snapdragon HTP verification bundle v1

Run on the friend's Snapdragon Windows HP PC, from an extracted local folder.
Do not run inside the ZIP or through WSL. No Python/pip/SDK installation needed.

1. Extract ClipTrail-HTP-smoke-v1.zip (about 640 MB free extracted space required;
   allow 2 GB free for extraction/logs and compilation). Keep every file together.
2. Open PowerShell in that folder. Copy this command as ONE line:

   powershell.exe -NoProfile -File .\run_smoke.ps1

3. Wait for completion (up to ten minutes). Return the printed
   evidence\smoke-<UTC timestamp>.zip, including failed runs.

The runner collects hardware/runtime inventory, validates all bundle hashes,
runs the fixed image once with CPU and once with strict QNN HTP, and saves the
raw embeddings and execution traces. It does not index videos, access private
images, capture the screen, install software, change execution policy, or make
application network requests. ORT telemetry is disabled via its API after import;
we have not measured operating-system/vendor network activity.

Required target environment
- Actual Snapdragon Windows ARM64. x64 Python emulation is rejected.
- OEM Qualcomm NPU/Hexagon driver and its RPC components (libcdsprpc.dll).
- Native Visual C++ runtime: msvcp140.dll and msvcp140_1.dll in System32.
  The runner reports loader errors. It does NOT install/update drivers or runtimes.
- Ordinary local write permission; no administrator launch required.
- Gate deadline: 2026-09-21 07:51:35 UTC. After this the runner stops without
  inference. The participant must decide the next step; do not change the deadline.

Private pinned dependencies
- CPython 3.12.10 Windows ARM64 embedded distribution (includes VC runtime helpers).
- onnxruntime 1.30.0 Windows ARM64 cp312, NumPy 2.5.3 Windows ARM64 cp312.
- onnxruntime-qnn 2.6.0 Windows ARM64 cp312; QAIRT build 2.50.40 in its wheel.
- Transitive Python dependencies and original license files are bundled.
- Exact wheels, source URLs, versions and SHA-256 values: bundle-manifest.json.
- This is the QNN 2.x plugin API: core ORT plus QNN plugin is intentional.
  The vendor tested QNN 2.6 with ORT 1.27; our 1.30 combination is unverified on
  target until this run. Docs state ORT >=1.24.1; wheel requires >=1.24.2.

Model / fixed input
- Qualcomm AI Hub OpenAI CLIP ViT-B/16 release v0.62.2 float ONNX image branch.
- We pruned the text branch without changing image weights. 399 image nodes.
- Input: float32 [1,3,224,224] RGB [0,1]; normalization is inside the model.
- Output: normalized float32 [1,512] image_features.
- HTP request: FP16 execution of floating graph, balanced performance mode.
  Requested precision is not proof of actual per-operator arithmetic precision.
- First frame selected by the frozen scene control: sintel_00 frame 9, 2.25 s.
  input/reference.json records source/model hashes and preprocessing provenance.
- Only precomputed tensors are used on target; video decoding is a later gate.

What constitutes evidence
- Native ARM64 and pinned runtime identities; exact input/model checksums.
- QNN NPU device, pinned QnnHtp.dll requested AND actually loaded.
- CPU fallback disabled, ORT executed-QNN-node profile and no CPU compute events.
- QNN detailed CSV with positive device execution events, plus operator mapping,
  raw logs and module hashes. Registration/model loading alone cannot pass.
- Compare returned vector to the frozen PyTorch CPU embedding:
  cosine >=0.999 AND max absolute difference <=0.02 AND norm in [0.98,1.02].
  Same-graph target CPU: cosine >=0.99999, maximum error <=0.001.
- Even EVIDENCE_COMPLETE_REVIEW_REQUIRED leaves npu_verified=false until raw
  evidence is reviewed. INCOMPLETE_EVIDENCE requires inspection, not a success claim.
- Reported one-call timings include profiling/cold effects, not benchmark results.

If something fails
- Return the evidence ZIP. Native errors/timeout/failed stage are useful evidence.
- If PowerShell policy prevents launching, return the exact message and stop.
  Do not bypass a managed policy or change machine settings for this script.
- Missing Visual C++ runtime: report before modifying the PC. Official guidance:
  https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist
- Missing/old NPU driver: report HP model, chip and inventory; use OEM-supported
  driver guidance only after identifying the actual mismatch. No generic driver swap.
- Do not enable CPU fallback, change provider/precision, or omit failing files.

Attribution and licenses
- OpenAI CLIP: MIT; see CLIP_LICENSE.txt.
- Sintel frame: (c) Blender Foundation / Sintel team, CC BY 3.0;
  https://durian.blender.org/ and https://creativecommons.org/licenses/by/3.0/.
  Frame extracted/resized from the public Sintel trailer for this diagnostic.
- Runtime licenses remain beside their packages under runtime/Lib/site-packages;
  CPython license is runtime/LICENSE.txt. Qualcomm's binary AI Stack terms are
  runtime/Lib/site-packages/onnxruntime_qnn/Qualcomm_LICENSE.pdf. These binaries
  are incorporated only for this ClipTrail application/benchmark, not relicensed
  as MIT or redistributed as a standalone SDK.
