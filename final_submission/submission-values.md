# Copy-paste submission values

**Prepared locally; no portal submission has occurred.** Use only fields the authenticated form actually shows. The signed-in form controls any limits and accepted formats.

**Project Title**
ClipTrail — Private, Scene-Aware Search for Local Video

**Tagline**
Describe a scene. Jump to the moment. Keep every video local.

**Brief one-line summary**
ClipTrail is a fully local application that indexes representative video scenes and lets users find and play visual moments with natural-language search.

**Short description**
Select a local video or folder, build a persistent scene index, describe a visual moment, and open the ranked source video at its timestamp. ClipTrail stores CLIP embeddings, thumbnails, and metadata in SQLite and keeps the CPU model loaded for repeated searches. No video or query needs to leave the computer.

**Longer project description**
ClipTrail turns local video libraries into searchable visual moments. It decodes each video, detects visual changes, selects representative scene midpoints, and stores normalized CLIP image vectors, thumbnails, filenames, and timestamps in SQLite. A natural-language query becomes a CLIP text vector; cosine ranking returns playable results with a thumbnail and score. The working CPU application supports single videos and folders, visible indexing progress, persistent reuse after restart, and browser or native-player playback. The frozen small benchmark reached 87.50% Recall@3 on 24 positive queries from two public films. In one recorded three-video CPU run, five warm repeat queries had 27.45 ms median latency, indexing took 6.80 s per video minute after model load, and logical vectors plus thumbnails used about 250 KB per video minute. An experimental Windows ARM64/QNN image backend has provider-level graph evidence on Snapdragon, while physical NPU execution remains unverified.

**GitHub Repository Link**
PENDING — paste the real public repository URL only after the push and signed-out verification.

**Brief Project Description file**
`ClipTrail-Brief-Project-Description.pdf` (recommended; DOCX backup also ready)

**Short Pitch Presentation in PDF**
`ClipTrail-Pitch.pdf`

**Short Pitch Presentation in PPT**
`ClipTrail-Pitch.pptx` (confirm the live validator accepts PPTX; convert to legacy PPT only if required)

**Demo Video — OPTIONAL SUPPORTING MATERIAL unless the live portal makes it required**
`ClipTrail-Demo.mp4`, 88.000 seconds. Public link: PENDING participant hosting and signed-out verification. Do not paste a placeholder URL.

**Technology summary**
Python, PyAV, OpenAI CLIP ViT-B/16 via PyTorch/Transformers, SQLite, local loopback browser interface, and an isolated experimental Windows ARM64 ONNX Runtime QNN image backend. The verified application backend is CPU CLIP.

**Snapdragon/QNN statement**
On an ASUS Snapdragon X2 Elite, one fixed CLIP image graph completed native ARM64 ONNX Runtime QNN provider-level execution. The pinned HTP backend loaded, one QNN partition was reported, and the embedding matched the CPU reference (cosine 0.999982834). Required hardware profiler events were not captured, so physical NPU execution, speedup, energy benefit, full application target deployment, and HP-device performance remain unverified.

**Key measured results**
Frozen small corpus: 83.33% Recall@1, 87.50% Recall@3, 81.82% short-event Recall@3; 24 positive queries, six windows, two films. Recorded AMD Ryzen 5 5600H WSL2/Linux CPU application: 27.45 ms median warm query across five post-first searches; 6.80 s indexing per video minute after model load; 250,186 logical bytes of vectors and thumbnails per video minute across three files totaling 2.279 minutes.

**Known limitations**
The retrieval corpus is small, positive-query-only, and labeled by one annotator. Full-video windowing and broad personal libraries have not been quality-tested. Browser playback depends on codec support. The QNN backend is experimental; physical NPU execution, target application operation, acceleration, energy savings, and production stability have not been established.

**Likely attribution text**
ClipTrail original code: MIT License, copyright 2026 ClipTrail contributors. OpenAI CLIP model terms, Python package terms, Blender Foundation *Sintel*/*Tears of Steel* media attribution (CC BY 3.0), and Qualcomm/ONNX Runtime QNN terms remain separate; see `THIRD_PARTY_NOTICES.md`. The pitch uses one saved *Sintel* result frame credited to Blender Foundation / *Sintel* (CC BY 3.0).

Portal fields vary; use only fields actually requested. Verify live competition rules before submission.
