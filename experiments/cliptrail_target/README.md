# ClipTrail: one native HTP embedding gate

**21 September update: the original deployment gate expired at 07:51:35 UTC without returned HTP execution evidence. Do not start another v1 run or change its cutoff.** The participant relayed an ASUS X2 Elite inventory and confirmed provisioning; neither is an inference result. See [gate outcome](../../project/planning/cliptrail-deployment-outcome.md). Instructions below preserve the original experiment; a new attempt needs a separately authorized bound/version.

This directory preserves the deterministic Windows ARM64/QNN deployment experiment and its [final v2 evidence adjudication](../../project/planning/cliptrail-deployment-outcome-v2.md). Scene selection, retrieval code, annotations, and prior negative experiments remain frozen. The returned attempt established native ARM64 QNN graph execution, HTP loading, partitioning, and embedding parity, while physical NPU hardware execution remained unverified. No acceleration, energy, HP deployment, or full target-application result follows.

The deployment interval is **20 September 2026 07:51:35 UTC → 21 September 2026 07:51:35 UTC**. `deployment-gate.json` records the absolute deadline. Waiting for hardware does not extend it. If no verified inference is obtained, stop debugging and record the exact blocker before deciding how to package CPU ClipTrail.

## Target operator

Transfer `artifacts/ClipTrail-HTP-smoke-v1.zip` to the friend's HP PC and extract to a local folder. Open PowerShell there and run this single line:

```powershell
powershell.exe -NoProfile -File .\run_smoke.ps1
```

Return the printed `evidence\smoke-<timestamp>.zip`, including failed runs. Inventory is incorporated; no separate inventory run is needed if using this complete bundle. See [target README](bundle/README.txt). No cloud account, pip, PyTorch, model download or QAIRT SDK installation is needed on target. Native Windows ARM64, the OEM NPU/RPC driver and native Visual C++ runtime are still prerequisites. The runner does not install them or change policy. PowerShell/Windows portions remain unexecuted here.

## Fixed model and input

| Item | Identity / evidence |
| --- | --- |
| CPU reference | OpenAI CLIP ViT-B/16, revision `57c216476eefef5ab752ec549e440a49ae4ae5f3`, existing frozen Transformers/PyTorch runtime |
| Scene | `sintel_00`, frame 9, 2.25 s; first selected frame in first scene-control row, no score-based choice |
| Qualcomm release | `openai_clip` v0.62.2 float ONNX, [official asset](https://qaihub-public-assets.s3.us-west-2.amazonaws.com/qai-hub-models/models/openai_clip/releases/v0.62.2/openai_clip-onnx-float.zip) |
| Export | `onnx.utils.Extractor` removes text branch, embeds image weights; ONNX checker passes; 399 nodes; 345,929,335 bytes |
| Graph SHA-256 | `110bb22c56b7232c5236c7fb68d5e5101f8ff70720adbdd86730e78247af4631` |
| Interface | RGB float32 `[1,3,224,224]` in `[0,1]` → normalized `[1,512]`; graph performs CLIP normalization |
| Native packages | Python 3.12.10 cp312; ORT 1.30.0; QNN plugin 2.6.0 / QAIRT 2.50.40; NumPy 2.5.3 |
| Requested HTP precision | FP16 execution of float graph; no claim about exact per-operator arithmetic before traces |

The modified image graph is **not** assumed to inherit the vendor's compiled compatibility. Compilation/finalization happens on the native device. No target-specific context binary or AI Hub job result has been generated. Static shape and documented FP16/operator support are a plausible path, not execution proof.

Measured reference checks in [graph-preparation.json](results/graph-preparation.json): original CPU embedding replay has maximum difference **0.0**; released/pruned image outputs have cosine **0.9999999404**, maximum difference **3.0361e-7** versus frozen reference; pruned versus combined image output difference **0.0**. The two recorded CPU call times are single cold/profile-preparation calls, not a performance comparison.

## Proof chain and predeclared smoke tolerances

1. Capture exact HP/chip/core/RAM/Windows/build/driver/power/runtime inventory. No serial number, hostname, private files, screen, camera or audio collection. Native logs can contain extraction paths; inspect before making public.
2. Verify Python PE architecture and `IsWow64Process2`, every manifest hash, all package versions and pinned DLL paths. Probe native MSVC/RPC dependencies. The two MSVC imports are independently visible in the official wheel import tables (`results/pe-imports.json`).
3. Execute same-graph CPU reference once. Require cosine ≥0.99999, max absolute difference ≤0.001, norm in [0.98,1.02].
4. Register QNN **plugin** through ORT 1.30 device API, select its NPU device and explicitly request the pinned `QnnHtp.dll`. Disable CPU fallback at session creation and in the Python wrapper.
5. Execute once. Require finite `[1,512]`, cosine ≥0.999, max absolute difference ≤0.02 and norm in [0.98,1.02]. These thresholds precede all target output. w8a16 would require a separate, versioned artifact and its already declared tolerances (≥0.99 cosine, ≤0.05 max error); it is not packaged or automatically tried.
6. Save raw vector, detailed QNN CSV/log, ORT executed-node profile, framework operator mapping, loader identities and errors. Strict placement requires actual QNN compute events and no CPU compute events. Positive hardware execution events are also required. Loading/registering a provider is insufficient.
7. Review returned raw evidence against the local manifest/reference before marking HTP verified. `npu_verified=false` even when automated checks are complete. Unknown profile schema fails closed for manual inspection. A smoke pass would prove one image/graph only, not all-image quality, speed, utilization, energy or scheduler benefit.

The ten-minute launcher preserves incomplete runs and timeout status. Every attempt has its own timestamped evidence directory; no fallback to CPU or overwrite of an earlier target run. Successful NPU execution with missing proof remains **incomplete evidence**.

## Dependency reproducibility

`results/provisioning.json` is the lock for official URLs and SHA-256 values of model, Python and every wheel. `tooling-freeze.txt` pins the separate x86 development environment. `bundle-manifest.json` pins the finished files. The initial `provision_dev.sh` discovered current packages; **do not rerun its floating resolution to reproduce v1**. Use `restore_assets.py` to restore the locked downloads in an asset-missing checkout. The existing `.venv-cliptrail` was not modified.

The normal preparation commands (from repository root, using existing provisioned environments) are:

```bash
.venv-cliptrail/bin/python experiments/cliptrail_target/prepare_reference.py
.venv-cliptrail-target-tools/bin/python experiments/cliptrail_target/prepare_graph.py
.venv-cliptrail-target-tools/bin/python -m unittest discover -s experiments/cliptrail_target -p test_evidence.py -v
.venv-cliptrail-target-tools/bin/python experiments/cliptrail_target/assemble_bundle.py
```

Existing reference/graph records are verified and preserved. The assembler refuses an existing runtime/staging directory or ZIP. Rebuild in a separate working copy, preserving recorded inputs and results. Native wheels are unpacked according to their wheel schemes into a private embedded Python directory; no target installation occurs. `._pth` limits imports to embedded standard library, private site-packages and bundle scripts. Scripts/headers from wheel data are unnecessary for this diagnostic; data files and original licenses are retained.

The first assembly stopped on SymPy's manual-page wheel data scheme; raw error is retained as `results/bundle-assembly-attempt1.txt`. Its incomplete stage was isolated. The assembler now maps `.data/data` to the private runtime prefix; a regression test covers it. This was a packaging defect, not a target/QNN failure.

Official QNN 2.6 docs recommend/test ORT 1.27.0 and state ≥1.24.1 compatibility; wheel metadata requires ≥1.24.2. Our exact 1.30.0 combination is downloaded/pinned and still **UNKNOWN** on target. Older monolithic-QNN package guidance does not apply to this plugin. Full runtime licences remain included; Qualcomm binary AI Stack licence is distinct from the MIT plugin source. Libraries are incorporated in this diagnostic application, not distributed as a standalone SDK. No public release has occurred.

## After hardware proof

Freeze actual model/precision/runtime, all selected timestamps, query vectors, foreground calibration and systems-run code. Then run exactly the three existing controls with capacity two, randomized order, one excluded warm-up and five runs/control under idle and loaded conditions. Require ≥25% foreground p95 improvement versus synchronous QNN, within 20% of idle, ≥90% throughput, ≤2 percentage-point R@3 loss. If synchronous QNN inflation is <20%, the hypothesized interference problem is absent. No threshold tuning or new scheduler search on the results.

The feature-frozen application and submission now use the CPU path while preserving this target record. See the current [benchmark and target evidence summary](../../docs/evidence.md) and [full v2 adjudication](../../project/planning/cliptrail-deployment-outcome-v2.md).
