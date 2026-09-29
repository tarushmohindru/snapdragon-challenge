# ClipTrail v2 deployment outcome and evidence adjudication

Reviewed 22 September 2026. **INCOMPLETE_EVIDENCE; one authorized post-cutoff attempt consumed. Recommendation B: sufficient evidence to continue the application on the proven CPU path, insufficient for a verified NPU claim.** No new experiment, native attempt, runtime change, UI, slides or systems benchmark was performed by this review.

## 1. Reconciliation and provenance

The authoritative latest attempt is the participant-confirmed root archive `smoke-v2-20260921T123814481Z-9573326e.zip`: **183,622 bytes**, SHA-256 **e8aa83c11ef9a96d4c2af205aa2e82197b2499e65af64dbe82ebba27677ef1c4**. The public candidate excludes the ZIP while retaining its [extracted returned evidence and audit](../../experiments/cliptrail_target/v2/review/evidence-audit.json). It is a returned result, distinct from the 315,726,092-byte deployment bundle. Its 21 September 12:38:14.4812721 UTC start is after the original 07:51:35 UTC cutoff and after explicit v2 authorization. The supervisor stopped at 12:39:22.0223171 UTC after **67.5380324 seconds**, without timeout or termination request. Exactly one CPU and one QNN session/run/completed call are recorded; no retries are recorded. The existing authorization is consumed.

The [original deployment outcome](cliptrail-deployment-outcome.md), original cutoff, original ZIP and all ten entries in [the v1 preservation lock](../../experiments/cliptrail_target/v2/v1-preservation-lock.json) remain byte-identical. The original gate expired without returned execution evidence; v2 is not a retrospective v1 success. This separate document updates the deployment outcome without rewriting that historical record. Earlier decision-log entries remain dated history; a new decision supersedes their pending status.

All **18 ZIP members** were read; ZIP CRCs and **17/17 recorded SHA-256 hashes** pass. The hash manifest excludes itself as expected. The returned manifest and authorization match the issued final v2 bytes, including runner source hashes. Reported in-bundle loaded-module hashes and inventory runtime hashes match the manifest. All raw members are preserved in [review/returned](../../experiments/cliptrail_target/v2/review/returned), changing only the Windows directory separator in the extracted inventory path. The original archive is untouched. Hashes establish consistency with the participant-supplied evidence, not independent remote attestation.

The old pending outcome and state are retained in [before-reconciliation](../../experiments/cliptrail_target/v2/review/before-reconciliation). The [current v2 outcome](../../experiments/cliptrail_target/v2/results/smoke-outcome-v2.json) records the reviewed result; the target-produced outcome remains unmodified under `review/returned`. Build/handoff audits are historical preparation records, not current attempt counters.

## 2. What the evidence proves

| Requirement | Adjudication | Evidence and boundary |
| --- | --- | --- |
| Native ARM64 runtime works | **Proven for this smoke workload**, with abnormal shutdown | Native probe: Windows, 64-bit Python, native machine and Python PE `0xaa64`, process machine `0x0`; Python 3.12.10, NumPy 2.5.3, ORT 1.30.0 import and completed inference. Does not establish stable process exit or general application compatibility. |
| ORT QNN provider loads | **Proven** | QNN plugin 2.6.0 imported and registered; provider DLL appears in loaded modules with the issued hash; actual QNN execution follows. Built-in provider enumeration lacking QNN occurred before dynamic registration and is not a failure. |
| Graph executes under QNN | **Proven at the ORT/provider boundary** | `session.run` completed, `[1,512]` output persisted, and ORT recorded a positive-duration QNN kernel event for the same graph. Both fallback mechanisms were disabled in the hash-matched runner. |
| HTP backend present/loaded | **Proven** | Explicit pinned `QnnHtp.dll` path; loaded module hash `2a4406653fd6cf2cbe83d544aa3066776a5d1b99b4cf2d73a446ce841c427e12`; `QnnHtpV81Stub.dll`, `QnnSystem.dll`, `QnnHtpPrepare.dll` and RPC module also loaded. Loading is not a hardware activity trace. |
| QNN partitioning occurred | **Proven** | Framework trace has one QNN subgraph, 414 QNN op mappings, 423/423 supported transformed ONNX nodes and zero unsupported nodes. ORT executed that named subgraph. The original graph has 399 nodes; transformed counts are not original-model node counts. |
| Actual NPU hardware execution | **Strongly supported indirectly; strict requirement NOT satisfied** | HTP target V81, NPU selection, pinned HTP loading, QNN-only recorded compute and valid output form a coherent HTP execution path. None is a recorded positive hardware/device execution event. No such event exists in the supplied files. |
| No ORT CPU compute fallback | **Supported for this recorded run** | ORT profile has one QNN compute event and no CPU compute events; strict settings agree. `CPUExecutionProvider` in the registered/session provider list does not itself show CPU execution. This does not prove that the opaque QNN backend performs no host work. |

### Complete returned-artifact classification

Paths below are relative to `experiments/cliptrail_target/v2/review/returned/`.

| Artifact | Classification and interpretation |
| --- | --- |
| `inventory-20260921T123815018Z/inventory.json` | Hardware/runtime presence and target identity: ASUS UX3407NA, X2E88100, Windows ARM64 28000.2956, driver and runtime file inventory. No hardware execution proof. Its `inference_performed=false` describes the inventory stage only. |
| `attempt-ticket.json` | Identifies the authorized attempt, extraction, start and manifest. Matches the native claim token. No execution proof alone. |
| `authorization-v2.json` | Scope: one post-cutoff attempt, 600 seconds, no retries. No execution proof. |
| `bundle-manifest-v2.json` | Exact issued runtime/model/input/control identities. No execution proof by itself. |
| `native-child.json` | Native process launched and exited with `C0000005`; corroborates lifecycle, not NPU execution. |
| `smoke.json` | Runtime/native probes, provider registration, one completed QNN call, loaded HTP modules, hashes, parity and placement. Proves the respective host/runtime/provider milestones when cross-checked against raw vectors and ORT trace; explicitly reports missing hardware profile. |
| `smoke-outcome-v2.json` | Supervisor summary: incomplete evidence, 67.538 seconds, no timeout, crash status, passing parity. Derived aggregation, not a second independent hardware observation. |
| `cpu_embedding.npy` | Finite normalized same-graph target CPU output matching frozen reference. No NPU proof. |
| `qnn_embedding.npy` | Finite normalized provider output; paired with run record and ORT trace proves useful QNN inference output. Numeric similarity alone cannot identify a device. |
| `ort-profile_2026-09-21_18-09-07_915.json` | Five events: model loading, session initialization, one QNN kernel, executor and model run. QNN kernel duration 511,435 microseconds. Proves ORT dispatch/completion and placement; this is a host duration, not hardware cycles or device timing. Thread-pool statistics are not NPU telemetry. |
| `qnn_op_trace.json` | Entire structure inspected: backend/model/SoC metadata, mappings, summary, unsupported-node list. HTP V81 compilation and partition mapping; **no execution event, timestamp or cycle measurement**. Despite its name, it is a framework mapping trace, not the missing hardware profile. |
| `stages.jsonl` | Seventeen persisted checkpoints through `finished`, with CPU/QNN call counters. Proves execution ordering and completed evidence persistence; no hardware event. |
| `python.stdout.log` | Same checkpoints plus final incomplete-evidence JSON. Corroborates completion and missing hardware evidence. |
| `python.stderr.log` | Three profiling-suppression messages followed by fatal access violation. Mixed UTF-16LE native text and UTF-8 Python fault-handler text; [decoded view](../../experiments/cliptrail_target/v2/review/python.stderr.decoded.txt) preserves both. Not evidence that hardware execution failed. |
| `attempt.stdout.log` | Inventory completion message only. Its no-inference statement is scoped to inventory, not the later smoke. |
| `attempt.stderr.log` | Empty; no positive or negative hardware conclusion. Native failure is in Python stderr and child return code. |
| `supervisor.log` | Attempt claimed and stopped; no automatic retry. No hardware proof. |
| `evidence-hashes-v2.json` | Validates 17 other members after process writers stopped. Integrity/consistency only. |

### Recomputed output parity and timing limits

Recomputed directly from preserved `.npy` files and the hash-matched frozen reference, with no model execution:

| Comparison | Cosine | Maximum absolute difference | Result |
| --- | ---: | ---: | --- |
| Target CPU vs frozen | 1.000000 | 0.000000510132 | Pass |
| QNN vs frozen | 0.999982834 | 0.001173689961 | Pass |
| QNN vs target CPU | 0.999982834 | 0.001173630357 | Pass |

QNN output is finite `[1,512]`, norm approximately 1.000092. Tiny host/target floating reduction differences do not affect any threshold. This is one fixed image, not target retrieval-quality validation across the corpus. Requested HTP FP16 is not per-operator precision evidence.

Recorded CPU call: **89.0111 ms**; profiled QNN call: **511.7389 ms**; QNN session initialization: **7011.7002 ms**. These single-call diagnostics neither show a speedup nor establish a representative slowdown. They include different profiling conditions and cannot support latency, throughput, energy or foreground-interference claims. No HP compatibility is established.

## 3. Profiling failure and crash

### Verified facts

Both requested and effective QNN options contain `profiling_level=detailed`, an absolute `profiling_file_path` ending in `qnn-profile.csv`, and `enable_framework_op_trace=1`. ORT profiling was separately enabled and emitted its JSON. Thus this was not an omitted profiling option or a failure to enable ORT profiling.

The expected primary output was **`qnn-profile.csv`**: QNN backend profiling events including positive device execution time/cycles. The pinned v2.6 documentation also describes the companion **`qnn-profile_qnn.log`** for recent QAIRT builds. Neither is in the archive or its hash manifest; no ETL, decoded ETW hardware event export, crash dump or exception JSON was returned. Framework tracing emits the mapping JSON separately and cannot replace the hardware profile. See [release documentation](https://github.com/onnxruntime/onnxruntime-qnn/blob/v2.6.0/docs/execution_providers/QNN-ExecutionProvider.md#qnn-ep-profiling).

The native log states three times: “ETW enabled previously, but disabled now. Can't do the switch! Won't output any profiling.” The errors are timestamped 18:09:08.530, 18:09:13.358 and 18:09:15.350 in the native log's unzoned clock. Their approximately +05:30 offset relative to UTC stage records is consistent with local time; that offset is inferred, not supplied by those log lines. The first two align with QNN initialization and the third with inference. UTC checkpoints remain the authoritative cross-process timeline.

The v2.6 release source's `ExtractBackendProfilingInfo` logs that exact message and returns before retrieving or serializing profile events when saved ETW state is non-invalid but current profiling ETW is unavailable. The issued runner then calls `end_profiling`, deletes the session and runs garbage collection, checks the CSV, records it absent, unregisters the provider, closes DLL search handles, and persists `finished`. Missing CSV evidence therefore predates the terminal crash; a shutdown-only flush explanation does not fit the complete record. See [release backend source](https://github.com/onnxruntime/onnxruntime-qnn/blob/v2.6.0/onnxruntime/core/providers/qnn/builder/qnn_backend_manager.cc#L2502).

| UTC checkpoint | Observed event |
| --- | --- |
| 12:39:07.912177 | QNN session creation begins |
| 12:39:14.925981 | QNN inference begins |
| 12:39:15.462715 | Embedding already saved; validation begins; completed QNN count is one |
| 12:39:15.465750 | Execution evidence collection begins |
| 12:39:15.850884 | `finished` persisted; output hashes, placement, absent hardware profile and incomplete status recorded |
| By 12:39:21.9920603 | Native child observed exited with signed code -1073741819 / `C0000005` |
| 12:39:22.0223171 onward | Supervisor completes outcome; then hashes and packages evidence |

The exact crash timestamp is absent. The fault handler identifies only module-level line 207, `raise SystemExit(main())`, without a native stack. The final stdout JSON and all returned vectors/traces are intact. A fatal exception superseded the runner's intended exit code 3; the supervisor's status follows `smoke.json` while separately retaining the native crash code. Both must be reported.

### Strongest plausible interpretation

**Profiling:** an ETW state/level mismatch suppressed extraction during initialization and inference. It is not established that an operator actually disabled tracing. In the release provider source, initialization accepts a nonzero ETW level with the profiling keyword, whereas extraction requires level at least 5. Levels 1–4 can therefore trigger this message without a real on/off transition. Actual ETW state/level/session owner was not captured. The DLL telemetry provider has separate state from ORT's telemetry API; simply removing `disable_telemetry_events()` is not an evidenced fix. See [provider initialization](https://github.com/onnxruntime/onnxruntime-qnn/blob/v2.6.0/onnxruntime/core/providers/qnn/qnn_execution_provider.cc#L737) and [telemetry implementation](https://github.com/onnxruntime/onnxruntime-qnn/blob/v2.6.0/onnxruntime/core/providers/qnn/qnn_telemetry.cc).

**Crash:** a post-result lifetime/teardown failure is the strongest interpretation. Explicit session deletion and provider unregistration returned before the final checkpoint. Later boundaries include destruction of local session options and EP-device wrappers when `main()` returns, interpreter/module finalization, and native DLL/static-object teardown. The source keeps `qopts`, `devices` and `selected` alive across explicit provider unregistration, which is a concrete lifetime boundary worth inspecting if debugging is later authorized. No evidence identifies any of these as the faulting object or library. The profiler error and crash may be separate issues; temporal proximity does not prove causation.

### Unknowns and excluded explanations

- Whether QNN accumulated hardware events internally before extraction was suppressed; no recoverable event buffer is included.
- Which ETW session, level, keyword or state change produced the mismatch; no ETW controller state was recorded.
- Whether any profile exists elsewhere on the target. The archive exhaustively covers the supplied evidence, not the target filesystem. It contains no alternative event stream to salvage offline.
- The faulting native module/address, exception parameters, asynchronous callbacks and actual object-destruction order. No dump/native stack exists.
- Exact correspondence between the released source and compiled plugin beyond version and matching error location/text. [Source snapshots and provenance](../../experiments/cliptrail_target/v2/review/sources/provenance.json) are interpretation aids, not a binary reproducibility proof. The web text renderer removes some blank lines; saved GitHub file content retains source line numbering.

Adjudication of the four profiling possibilities: **requested/enabled in configuration; failed to emit because extraction was explicitly suppressed; not demonstrated to be a mere flush failure; not supported as evidence lost only in shutdown.** Internal profiling activation and earlier/later emissions outside supplied files remain unknown. No claim that the model failed or that the hardware did not run follows.

## 4. Go/no-go decision

**Choose B now.** Continue to regard the existing CPU scene retrieval as an application foundation. This review does not authorize UI or other development in this turn. Keep NPU verification false and the strict HTP/systems gate closed. The compatibility, QNN execution, backend, placement and parity subrequirements are satisfied; positive device execution evidence is the single missing HTP proof item. Stable shutdown is a separate deployment issue.

Permissible factual statement: **“On an ASUS Snapdragon X2 Elite, the fixed CLIP image graph completed one ONNX Runtime QNN inference with the pinned HTP backend loaded and output matching CPU. Direct NPU hardware profiling verification remains incomplete; the process subsequently exited with an access violation.”** Do not shorten this to verified NPU acceleration, NPU-only work, a speed/energy advantage, production readiness, full-corpus target quality or HP deployment.

- **A:** No for a claim of verified NPU hardware execution/acceleration. The narrower platform/provider statement above is supported, but it does not close the original requirement.
- **B:** Yes as current disposition, using the proven CPU application path and treating QNN integration as experimental.
- **C:** Technically justified **only if the participant later chooses to reopen the NPU claim**. Not authorized, prepared or launched by this review. The record narrows the problem enough to avoid a model/runtime/version sweep.
- **D:** The appropriate fallback if no further target access is chosen: stop target work and describe Snapdragon NPU optimization as intended/unverified, retaining the successful provider-level smoke result and crash honestly. This does not reject scene-indexed ClipTrail.

### Conditional single-purpose follow-up specification (no execution)

**Only missing hardware evidence to collect:** a preserved positive **backend `EXECUTE DEVICE` event or equivalent attributable HTP hardware cycles**, associated with the same graph's single QNN call, together with its ORT placement/output identities. A host `EXECUTE` duration, mapping JSON, utilization screenshot or backend-loading log alone will not satisfy it.

**Smallest proposed intervention:** control the profiling sink in the launcher, without changing model, tensor, preprocessing, precision, runtime or driver. Start one local ETW capture for the plugin's `Microsoft.ML.ONNXRuntime` provider before Python/provider initialization, enable profiling keyword **0x100** at **level 5**, and keep that session active through process exit. Stop/flush and preserve its ETL from the supervisor after the child exits, including on crash. The release source defines provider GUID **3a26b1ff-7484-7484-7484-15261f42614d** and basic profiling at level 5; this offers a targeted route around the recorded mismatch and a sink outside Python shutdown. Existing detailed CSV options may remain; acceptance depends on decoded device events, not the file extension. See [telemetry provider](https://github.com/onnxruntime/onnxruntime-qnn/blob/v2.6.0/onnxruntime/core/providers/qnn/qnn_telemetry.cc#L58) and [profiling keyword](https://github.com/onnxruntime/onnxruntime-qnn/blob/v2.6.0/onnxruntime/core/providers/qnn/qnn_telemetry.h#L112).

This is a source-supported proposal, **not a tested fix**. Controller availability/permissions, ETL decoding with provider metadata, event loss and interaction with other trace sessions would need review before issuing a new bundle. Do not stop unrelated tracing sessions, clear v2 markers, disable all telemetry blindly, patch the binary or substitute another runtime. Any future run needs a separate authorization/attempt identity and the same one-call/no-retry bound. A positive device event would satisfy the missing execution item but would not repair the crash or prove performance. No broad crash investigation is bundled into this proposal.

## Validation performed in this adjudication

[Read-only audit script](../../experiments/cliptrail_target/v2/review/audit_returned.py) and [saved audit](../../experiments/cliptrail_target/v2/review/evidence-audit.json) verify archive coverage, hashes, identities, stage/call accounting, raw-vector parity, raw ORT placement, framework-to-ORT graph-name agreement and historical v1 preservation. No inference library is initialized by this script; NumPy is used only to read and compare existing arrays. Prior host test results remain prior results; no prior experiment was rerun. Final reconciliation validation also checks extracted bytes, current outcome links and historical preservation.
