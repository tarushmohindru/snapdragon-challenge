ClipTrail v2: ONE authorized native smoke attempt on the ASUS X2 Elite

This is the participant's explicit extension after the v1 deployment cutoff.
The original v1 bundle, deadline, hashes and failed-to-verify outcome are preserved.
This v2 bundle uses exactly the same model, runtime, precision and prepared input.

On ASUS Zenbook A14 UX3407NA, Snapdragon X2 Elite X2E88100:
1. Extract ClipTrail-HTP-smoke-v2.zip into a NEW local folder, separate from v1.
2. Open Windows PowerShell in that folder and run this ONE line ONCE:

   powershell.exe -NoProfile -File .\run_smoke.ps1

3. Wait up to ten minutes for the attempt, then allow evidence packaging to finish.
4. Return the printed evidence\smoke-v2-<timestamp>-<id>.zip regardless of outcome.
   If no ZIP is produced, return the evidence folder or exact console error.
   STOP after this run. Do not retry, change files, delete attempt markers,
   install dependencies, update drivers or run a benchmark.

What runs
- Hardware/Windows/driver inventory, then the private native ARM64 Python.
- Bundle hashes, native architecture and existing platform dependency checks.
- One same-graph CPU reference call and one QNN HTP call on the fixed scene tensor.
  These are two planned checks within ONE attempt; no warm-ups or inference retries.
- QNN registration/device selection, strict CPU-fallback-disabled graph creation,
  raw embedding output, frozen-reference parity and detailed execution profiles.
- Python wrapper retries are disabled before both session constructors as well as
  for run(). A failed initialization is reported immediately without a fallback run.

Enforcement
- The 600-second budget starts when the supervisor starts and includes inventory,
  validation, CPU and QNN work. A watchdog requests termination of the attempt's
  PowerShell/Python process tree at the limit. Termination time/status is recorded;
  OS termination overhead can take additional seconds. There is no automatic retry.
- This creates small persistent attempt markers in this extraction and under:
  %LOCALAPPDATA%\ClipTrail\cliptrail-htp-v2-asus-x2e88100-one-attempt\
  A second launch under the same Windows account is refused, including from a new
  extraction. Markers remain even after failure. This is an accidental-rerun guard,
  not tamper-proof enforcement across accounts or machines.
- Direct Python launch requires the supervisor ticket and consumes an additional
  atomic native-start marker. Do not run the helper scripts directly.
- The ten-minute limit does not cover ZIP compression AFTER the compute attempt
  ends; that step runs no inference. No calendar deadline is silently substituted
  for the original v1 cutoff: this extension is bounded by one attempt and duration.

Evidence returned
- smoke-outcome-v2.json: supervisor timestamps, timeout, return/exception status,
  observed runtime and stage summary; npu_verified stays false pending review.
- smoke.json, stages.jsonl, native-child.json: native progress and exact failure stage.
- python.stdout.log / python.stderr.log: unbuffered native logs and fault-handler output.
- attempt.stdout.log / attempt.stderr.log / supervisor.log: inventory/helper/launch logs.
- Original inventory, DLL/runtime identities, providers/options, ORT placement profile,
  QNN detailed CSV/log and operator trace when produced.
- cpu_embedding.npy and qnn_embedding.npy when produced, with SHA-256 hashes.
- evidence-hashes-v2.json covers the returned files after writers have stopped.

Proof rules (unchanged)
Registration, installed drivers and successful model loading do not prove NPU use.
Require pinned QnnHtp.dll actually loaded, successful inference with fallback disabled,
actual QNN compute placement and positive backend hardware execution events, no CPU
compute partitions, and finite [1,512] output. Compare with frozen CPU embedding:
cosine >=0.999, max absolute error <=0.02, norm in [0.98,1.02]. Same-graph CPU limits:
cosine >=0.99999 and max absolute error <=0.001. Unknown profile schemas stay incomplete.
Even an automated EVIDENCE_COMPLETE_REVIEW_REQUIRED result needs raw-evidence review.

Pinned assets (all unchanged from v1)
CLIP ViT-B/16 image branch: Qualcomm release 0.62.2 float ONNX, 399 nodes.
Graph SHA-256: 110bb22c56b7232c5236c7fb68d5e5101f8ff70720adbdd86730e78247af4631
Scene: sintel_00, frame 9, timestamp 2.25 s; RGB float32 [1,3,224,224], [0,1].
Requested backend/precision: QnnHtp.dll, enable_htp_fp16_precision=1, balanced mode.
Private runtime: Python 3.12.10, ORT 1.30.0, QNN plugin 2.6.0 / QAIRT 2.50.40,
NumPy 2.5.3. No downloads or global installs. Existing MSVC/NPU/RPC dependencies
are checked as found; missing or incompatible components cause a recorded stop.

Model/image/runtime attribution and licences
OpenAI CLIP: MIT, CLIP_LICENSE.txt. Sintel frame: Blender Foundation / Sintel team,
CC BY 3.0, https://durian.blender.org/ and https://creativecommons.org/licenses/by/3.0/.
CPython: runtime/LICENSE.txt. Package licences remain under runtime/Lib/site-packages.
Qualcomm binary terms: onnxruntime_qnn/Qualcomm_LICENSE.pdf; binaries are incorporated
in this diagnostic application, not relicensed or offered as a standalone SDK.

This runner changes no installed software, drivers, execution policy or model assets.
It creates evidence and attempt markers. Native diagnostics can contain local paths.
It makes no application network requests; vendor/OS traffic has not been measured.
ASUS results are not HP deployment evidence. No energy/performance benchmark claim.
