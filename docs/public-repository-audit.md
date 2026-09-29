# Public repository audit

Audited 23 September 2026 and refreshed 29 September 2026 for competition publication. ClipTrail is the product; older selection work is retained only as engineering history. This audit covers the public candidate in the writable alternate Git metadata directory `.publication.git` because the supplied `.git` directory is empty and read-only.

## Publication result

The staged candidate contains the application source and tests, canonical documentation, MIT license, frozen retrieval reports/manifests/raw vectors, compact application measurements, extracted target evidence, final exports, and submission handoff. The `.gitignore` excludes virtual environments, caches, model weights, source videos, native QNN/runtime packages, generated databases, archives, assembled bundles, rejected-branch bulk data, and the alternate Git metadata itself. The locally retained Qualcomm license PDF is also excluded; `THIRD_PARTY_NOTICES.md` describes that upstream boundary.

The original 23 September committed inventory contained **210 files / 16,460,887 bytes**. The 29 September final handoff contains **220 tracked files** after adding documentation, a demo poster, and video provenance; the MP4 remains Git-ignored as a separate upload artifact. `submission/tools/audit_public.py` validated **63 JSON files** and **85 local Markdown links**, with no broken link, secret-pattern hit, or tracked file over 5 MB. No source video, model weights, runtime binary, database, environment file, generated archive, temporary render frames, or local Hyperframes project belongs in the public candidate. Sixteen preserved raw evidence files contain recorded absolute local paths as provenance; they were not edited because the frozen records must remain exact. User-facing Markdown, exported files, and the demo capture contain no personal absolute path.

The seven-slide pitch PDF and one-page brief PDF were rendered and visually checked; the DOCX and PPTX are valid ZIP packages. The PPTX has seven slides and seven speaker-note parts. The DOCX carries the approved brief content. The 88-second demo has been recorded from the real persisted CPU application with the canonical Sintel result and browser playback. Native Microsoft Office rendering and the participant's final video viewing remain personal visual checks.

## Preservation and evidence

The original expired v1 gate, its outcome, and the ten files named in `experiments/cliptrail_target/v2/v1-preservation-lock.json` remain historical facts and unchanged. The one authorized post-cutoff v2 attempt remains the latest target evidence. Its returned logs, partition trace, embeddings, and adjudication remain available without revising frozen evidence. The target path supports native ARM64/ORT QNN graph execution, HTP loading, partitioning, and embedding parity; physical NPU device execution is unverified.

The public candidate includes the original and amended retrieval reports, including the corrected supplemental control and rejected adaptive result. Downloaded media and weights are reconstructed locally from provisioning instructions; they are not committed. All six application tests passed in the available environment. The loopback test required a socket-permitting execution context; its first run in the default sandbox failed at socket creation, then all six passed without source changes.

## Documentation and claim checks

The root README is the public entry point. `docs/architecture.md` is the canonical architecture source, with a presentation rendering in `final_submission/assets/architecture.png`. `docs/evidence.md` separates small-corpus quality, one-host CPU application measurements, and Snapdragon/QNN provider-level observations. `final_submission/claims-audit.md` reviews each public claim, including speaker notes and exports. Rejected ShareGuard, BenchProof, and adaptive ClipTrail work appears only in engineering history or explicit evaluation context, not the product pitch.

The final visual includes one saved *Sintel* result frame with Blender Foundation / *Sintel* CC BY 3.0 credit. It is labeled a saved result frame, not an application screenshot. The brief and deck share the primary title, tagline, CPU measurement scope, and unverified physical NPU boundary.

## Publication commands and remaining actions

The empty supplied `.git` cannot be written in this workspace, so use the local history already prepared in `.publication.git`. From the repository root, after creating an empty public GitHub repository, set its real URL and push:

The participant explicitly chose to keep the globally configured Gmail commit author address for public display. No author-identity decision remains open.

```bash
REPO_URL='<YOUR REAL GITHUB REPOSITORY URL>'
GIT_DIR=.publication.git GIT_WORK_TREE=. git remote add origin "$REPO_URL"
GIT_DIR=.publication.git GIT_WORK_TREE=. git push -u origin main
```

If `origin` has already been added, use `git remote set-url origin "$REPO_URL"` with the same `GIT_DIR`/`GIT_WORK_TREE` prefix. The participant must verify public visibility in a signed-out browser and put the real URL into the portal. No GitHub URL or portal completion is claimed here.

Participant-owned review remains: inspect DOCX/PPTX/PDF/video rendering on the presentation machine, create and verify the public GitHub repository, choose optional video hosting, inspect authenticated portal fields, and complete upload/submission. The project code is under the participant-selected MIT license; third-party model, media, library, music, and runtime terms remain separate. See `final_submission/participant-handoff.md` for exact commands and steps.
