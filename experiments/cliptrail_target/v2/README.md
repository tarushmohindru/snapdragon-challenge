# ClipTrail smoke v2: attempt consumed; INCOMPLETE_EVIDENCE

**Current status, reconciled 22 September 2026:** the participant returned the root `smoke-v2-20260921T123814481Z-9573326e.zip`. One authorized post-cutoff attempt completed CPU/QNN inference and passed parity, but did not emit hardware profiling evidence and exited with `C0000005` after persisting results. **Do not follow the historical launch command below again.** The attempt is consumed; no retry is authorized. See the [current deployment adjudication](../../../project/planning/cliptrail-deployment-outcome-v2.md), [raw artifacts](review/returned/) and [integrity audit](review/evidence-audit.json). Recommendation B; NPU verification remains false. Build/handoff audits below describe preparation, not the current attempt count.

The participant authorized this extension on **21 September 2026**, after the original deployment cutoff. Scope is exactly **one native smoke attempt**, capped at **600 wall seconds**, with **no automatic retries**. Success or failure ends execution and requires review. There is no authorization to start the three-control systems benchmark from this run.

Historical handoff preparation (superseded by the returned result below): the final bundle was ready before the single attempt. Final ZIP: **315,726,092 bytes**, SHA-256 `170a99c641c585445198963845a2dfe443354cdbdbdeccc5928bd9bac353b6f9`. All 3,142 model/runtime/input files match v1, all 3,152 payload files pass archive checks, and historical v1 hashes remain unchanged. Only the final `ClipTrail-HTP-smoke-v2.zip` is for the target. An unissued `-preflight` packaging draft is archived; the final launcher additionally drains redirected output after the child has exited before hashing logs. Neither build ran inference or consumed a target attempt.

## Historical operator handoff — do not execute again

Use `../artifacts/ClipTrail-HTP-smoke-v2.zip`. Extract into a **new local folder** on the identified **ASUS Zenbook A14 UX3407NA / Snapdragon X2 Elite X2E88100**. Open Windows PowerShell there and run this single line once:

```powershell
powershell.exe -NoProfile -File .\run_smoke.ps1
```

Return the printed `evidence\smoke-v2-<timestamp>-<id>.zip` regardless of result. If launch or compression fails, return the exact error/evidence folder. Stop after that invocation. Do not rerun, remove markers, change model/runtime files, update drivers or install another version.

The launcher creates evidence plus small attempt markers in the extraction and `%LOCALAPPDATA%\ClipTrail\cliptrail-htp-v2-asus-x2e88100-one-attempt\`. Atomic creation blocks repeat launches under the same account, including a second extraction. The Python runner requires the issued ticket and a second atomic native-start marker. These are operational guards against accidental reruns, not tamper-proof cross-account enforcement. No system setting is changed.

## Unchanged experiment

All `model/`, `input/` and `runtime/` payload hashes and all model/runtime manifest fields must equal v1. This includes graph, weights, prepared tensor, frozen CPU reference, package versions, runtime binaries and embedded Python path configuration. No reprovisioning, new calibration, conversion, driver update, precision change or preprocessing change occurs.

The attempt preserves v1's two planned checks: one target CPU call for same-graph parity and one QNN call on the same fixed scene. There are no warm-ups, repeats or performance benchmarks. Provider options and ORT thread configuration match v1. Requested HTP FP16 remains a requested arithmetic mode until actual evidence can be reviewed.

The only changed v1 payload files are the launcher, Python diagnostic runner and operator README. V2 adds authorization, an attempt-policy module and the child PowerShell helper; it removes obsolete inventory-only instructions. The builder reports the exact diff. No existing v1 file is rewritten.

One justified control change is `enable_fallback=False` in both ORT constructors, using the already bundled ORT 1.30 API. Its Python wrapper otherwise permits constructor-time fallback before `disable_fallback()` can be called. The engine also retains `session.disable_cpu_ep_fallback=1`. This implements the authorized no-retry/no-silent-fallback rule without changing the runtime package. A host test exercises the real wrapper's failure branch with session creation mocked; it runs no model.

## Timing and failure capture

The supervisor's monotonic stopwatch includes inventory, hashes, Python imports, graph initialization, CPU and QNN calls. At 600 seconds it requests termination of only its attempt process tree and records actual timing/termination status. OS termination overhead may add seconds; no further inference call is launched. ZIP packaging after compute termination is not part of inference and may finish afterward. The participant authorized an attempt-count/duration extension, not a replacement calendar deadline for v1.

`run_smoke.py` checkpoints state before risky operations and writes unbuffered stdout/stderr with Python's fault handler enabled. The helper/supervisor also record native launch and signed/hex return codes, allowing a missing DLL or native crash to be distinguished from a Python exception. Timeout/crash can leave partial native profiles; incomplete evidence cannot pass.

Artifacts include:

- `smoke-outcome-v2.json`: supervisor result, timeout, return codes, observed runtime, parity and evidence-check summary.
- `smoke.json`, `stages.jsonl`, `native-child.json`: detailed stage/call accounting and exact failed stage when available.
- `python.stdout.log`, `python.stderr.log`, `attempt.stdout.log`, `attempt.stderr.log`, `supervisor.log`: process diagnostics; `termination.log` if needed.
- Raw inventory, bundle/authorization identities, loaded DLLs, provider/device information, ORT profile, QNN CSV/log and operator trace when produced.
- CPU/QNN embedding `.npy` files and hashes when produced; full evidence hashes after writers stop.

Profiled/cold single-call timings are diagnostic durations, not benchmark results. No utilization, energy, HP compatibility or per-operator precision claim follows from a successful import or driver entry.

## Review six questions, then stop

1. Did native ARM64 Python initialize, and which exact runtime imports completed?
2. Did ORT register/load the QNN plugin? Preserve registration errors; registration alone is insufficient.
3. Did the exact prepared graph load and execute? Distinguish session creation attempts, run attempts and completed calls.
4. Is the pinned HTP backend actually loaded, with real QNN compute partition evidence and positive device execution events, without CPU compute fallback?
5. Was a finite normalized `[1,512]` embedding produced? Preserve any invalid output too.
6. What are cosine similarity and maximum absolute difference versus frozen CPU, at unchanged v1 tolerances?

The frozen `evidence_rules.py` is reused byte-for-byte. `npu_verified` stays false in automated records pending raw-evidence review. A complete record still needs inspection of actual backend/placement/hardware events. Driver presence, package metadata, model loading and provider registration never establish NPU execution on their own.

After success, report status, proof, parity, observed runtime, warnings and any partitions, and stop. After failure, report the exact failing stage/error and smallest required intervention, and stop. No intervention or second attempt is automatically authorized.

## Reproduction and preservation

`authorization-v2.json` records scope and target. `v1-preservation-lock.json` freezes original ZIP, manifest, gate, hashes and historical outcome. `build_bundle.py` copies v1's archived payload, overlays only v2 control files, verifies each new archive member and rechecks the v1 lock. It performs no download or model inference. It refuses to overwrite an existing v2 ZIP.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cliptrail-target-tools/bin/python -m unittest discover -s experiments/cliptrail_target/v2 -p test_v2_policy.py -v
PYTHONDONTWRITEBYTECODE=1 .venv-cliptrail-target-tools/bin/python experiments/cliptrail_target/v2/build_bundle.py
```

Host tests exercise the attempt policy, concurrent/repeated ticket rejection, target identity, exact 600-second bound, disabled ORT wrapper retry, and unchanged provider/precision/thread settings. PowerShell process supervision and Windows-native execution cannot be tested on this Linux host; that limitation is recorded rather than consuming an extra target attempt. The test's ORT import emitted a telemetry-ID persistence warning, preserved in `results/host-tests-v2.txt`; no host model inference or target attempt occurred.

`results/smoke-outcome-v2.json` now records **INCOMPLETE_EVIDENCE**, one native attempt observed and consumed. Its earlier pending bytes are in `review/before-reconciliation/`. The target-produced outcome and all raw files are preserved under `review/returned/`, and the original result ZIP remains at the project root. The historical v1 cutoff and outcome remain unchanged.
