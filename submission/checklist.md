# Final submission checklist

Updated 29 September 2026. Application features are frozen. Checkmarks below indicate evidence present in this workspace, not completion of external portal actions.

## Product and claims

- [x] Primary title selected: **ClipTrail — Private, Scene-Aware Search for Local Video**.
- [x] Product narrative centers on the working local application.
- [x] CPU is identified as the verified application backend.
- [x] Frozen scene quality is scoped to 24 positive queries, six windows, and two public films.
- [x] Application performance is identified as CPU-only on the recorded AMD Ryzen 5 5600H WSL2/Linux host.
- [x] Snapdragon language is limited to native ARM64/QNN execution, HTP loading, partitioning, and embedding parity.
- [x] Physical NPU execution, speedup, energy advantage, HP deployment, target app deployment, and production stability are explicitly unverified.
- [x] The post-inference `C0000005` is reported as an unknown-root-cause target limitation.

## Repository

- [x] Root README presents the product, quick start, architecture, evidence, and limits.
- [x] One canonical architecture diagram exists in `docs/architecture.md`.
- [x] Benchmark/evidence summary links to raw reports and adjudication.
- [x] Virtual environments, caches, weights, videos, runtime binaries, bundles, databases, and rejected-branch bulk data are excluded by `.gitignore`.
- [x] Generated Python caches and stray Windows metadata were removed from the public source tree.
- [x] Compact returned target evidence and negative-result adjudication remain available.
- [x] Third-party model, dependency, media, and QNN boundaries are summarized in `THIRD_PARTY_NOTICES.md`.
- [x] V1 preservation-lock hashes still pass after repository cleanup.
- [x] Public-candidate secret scan found no credential or private-key material.
- [x] No source file larger than 5 MB remains in the public candidate set.
- [x] Prepare writable alternate Git metadata (`.publication.git`) because the provided `.git` is read-only; stage and audit the public candidate, then commit it locally.
- [ ] Set repository visibility to public and record the final URL.
- [x] Participant selected MIT; root `LICENSE` added for original project code. Upstream model, media, and runtime terms remain separate.

## Validation

- [x] Six ClipTrail application tests pass, including loopback upload, progress, search, persistence, thumbnails, byte ranges, and playback routing.
- [x] SQLite persistence reopens with three videos and 48 frames.
- [x] Real-model HTTP smoke returns the saved 23.25-second result and media bytes.
- [x] Frozen offline replay reproduces 20/24 Recall@1, 21/24 Recall@3, and 9/11 short Recall@3.
- [x] Recorded benchmark and application metrics are preserved without rerunning prior experiments.
- [x] Capture and review the final 88-second demo from the persistent CPU browser application. The canonical result and actual browser playback are visible; final participant viewing remains open.
- [x] Confirm the capture browser decoded and played the source clip at the saved moment.

## Submission materials

- [x] Final positioning and title candidates completed.
- [x] Brief Project Description completed.
- [x] Seven-slide pitch content completed.
- [x] 75–90 second demo script completed.
- [x] Judge Q&A completed with 32 evidence-backed answers.
- [x] Unsupported accelerator and deployment language removed from canonical materials.
- [x] Export the seven-slide pitch as PDF/PPTX from the approved narrative; inspect rendered PDF pages.
- [x] Export the brief as DOCX/PDF and inspect the rendered PDF page.
- [ ] Verify any portal-specific template, page/word limit, or file-format requirement against the live rules.
- [ ] Add the real repository URL and any optional/required video link to the live submission fields after signed-out verification.
- [ ] Verify competition eligibility, naming, file-size limits, required licenses/attributions, and exact portal closing time against the live rules.
- [ ] Open every exported file on a second machine and check fonts, video links, diagrams, and accessibility.
- [ ] Submit before the confirmed deadline and preserve the final submitted files and confirmation receipt.

## Final human read-through

- [ ] Read the README, brief, deck, and demo narration aloud as one story.
- [ ] Confirm every displayed number appears in `docs/evidence.md` and a linked raw artifact.
- [ ] Confirm no slide or narration says “NPU accelerated,” “NPU-powered,” or implies measured Snapdragon advantage.
- [ ] Confirm rejected concepts appear only in engineering history or a direct judge answer.
- [ ] Confirm no local absolute path, personal file, or unrelated desktop content appears in screenshots or recordings.
