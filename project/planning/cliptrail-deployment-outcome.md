# ClipTrail deployment gate: expired without execution proof

Recorded 21 September 2026. **Gate not met: target execution remains unverified.** This is an evidence/access outcome, not an observed QNN compatibility failure or a rejection of scene-indexed ClipTrail.

## Deadline and exact stopping point

The agreed deployment interval was **20 September 07:51:35 UTC through 21 September 07:51:35 UTC**. At the resume check on 21 September 09:53:05 UTC, only inventory and provisioning confirmations had been returned. The inventory was collected at a target-reported **20 September 12:19:03 UTC**, within the original interval, but it explicitly records no inference. Its collection time does not extend the gate.

**Exact blocker:** no returned execution of the one-image native ARM64 smoke runner, no target embedding, and no ORT/QNN execution or partition trace. There is no observed native import, model compilation or HTP error to diagnose. The agent has no direct access to this PC. A driver entry alone cannot establish that the bundled runtime loads or the graph executes on HTP. Actual unreported attempts, if any, are unknown.

Stop deployment debugging now under the participant's instruction: “If target deployment cannot be made functional within the one-day deployment gate, stop debugging indefinitely and report the exact blocker. We will then decide how to package the working scene-indexed CPU ClipTrail honestly for submission.” No new inference request, version sweep, driver change, scheduler work, UI or submission preparation follows automatically. The original smoke bundle's deadline and hashes are unchanged; it refuses inference after its cutoff.

## Available device, from the relayed inventory

| Field | Reported value |
| --- | --- |
| Manufacturer/model | **ASUS Zenbook A14 UX3407NA** |
| CPU | Snapdragon X2 Elite **X2E88100**, 18 cores / 18 logical processors |
| RAM | 16,784,158,720 bytes (about 15.63 GiB visible; 16 GB class) |
| OS | Windows 11 Home Single Language, ARM64, 26H1, **28000.2956** |
| NPU driver | Hexagon NPU **30.0.220.11010**, `oem122.inf` |
| FastRPC driver | **685.13804.20.0**, `oem39.inf` |
| Compute DSP driver | **685.13804.70.0**, `oem9.inf` |
| GPU | Adreno X2-90, driver **32.0.149.0** |
| Shell | PowerShell **5.1.28000.2952**, reports ARM64 |
| Power scheme | Balanced; AC state and power-mode slider were not collected |
| Python discovery | Path named `Python312-arm64`; exact executable version/PE architecture not probed |
| Private runtime scan | Empty in the inventory-only bundle; does not establish that global ORT/QNN is absent |
| Execution | `inference_performed=false`, `npu_verified=false`, inventory `errors=[]` |

Provenance: [selected inventory fields](../../experiments/cliptrail_target/results/inventory-user-extract-20260921.json), transcribed from the participant's pasted JSON. This is explicitly a partial extract, not an attached native file or a claimed checksum of the original inventory. Peripheral driver rows unrelated to this gate are omitted. No official product specification cross-check was conducted after the cutoff.

The available test device is **ASUS, not HP**. A future successful run would establish behavior on this identified ASUS X2 Elite configuration only. HP deployment, including any other Snapdragon generation, remains unverified. The challenge's supplied “designed/developed/intended to be optimized for HP” wording does not by itself establish that development on ASUS is disallowed; no new eligibility claim is made either way.

## What the project actually has

- Working CPU CLIP scene retrieval on the frozen small corpus: Recall@1 83.33%, Recall@3 87.5%, short-event Recall@3 81.82%.
- CPU equivalence of the extracted Qualcomm CLIP image graph on one predetermined frame: cosine 0.9999999404, max error 3.0361e-7.
- Pinned private ARM64 runtime and diagnostic bundle, 13 host tests, static PE/hash checks. Native inventory collection is now user-confirmed; native Python/ORT/QNN execution is not.
- Provisioning confirmation consistent with the existing successful download records. No new download or compilation is necessary to explain that output.
- No target embedding, HTP partition/execution proof, full-corpus target parity, scheduler measurements, foreground-load calibration or energy measurements.

All existing raw CPU results, negative experiments, packaging-attempt logs, locks and ZIPs remain preserved. No systems thresholds changed. The three-control benchmark remains unexecuted and its final workload/calibration are not frozen.

## Decision pending

Scene-indexed ClipTrail remains the project. The default consequence of the expired gate is to discuss packaging its measured CPU implementation with Snapdragon acceleration clearly marked unverified. This outcome document is an engineering record, not a submission claim or polished presentation.

If the participant elects to reopen hardware work now that the device is identified, the smallest concrete next scope is **one run of the already prepared graph/runtime diagnostic, with its existing ten-minute timeout and no automatic retries**, followed by raw-evidence review. That requires an explicit new bound and a separately versioned manifest/bundle; never edit the frozen v1 deadline or infer authorization from the delayed inventory reply. No such extension or new run is authorized yet.
