# Brief Project Description

## ClipTrail — Private, Scene-Aware Search for Local Video

Video libraries are full of useful moments that filenames cannot describe. Finding one scene often means scrubbing through several recordings or uploading private media to a cloud service.

ClipTrail is a fully local semantic video search application. A user selects a video or folder, waits while ClipTrail builds a persistent scene index, and then searches with ordinary language. Results show a representative frame, filename, timestamp, and similarity score. Selecting a result opens the source video at that moment.

ClipTrail keeps the index compact by sampling video at 4 Hz, detecting visual transitions, and embedding representative scene midpoints instead of every frame. It stores normalized CLIP image vectors, thumbnails, timestamps, source hashes, and backend identity in SQLite. The model remains loaded for the lifetime of the application, so repeated searches only encode the query text and rank saved image vectors. All processing, storage, search, and playback stay on the user's computer.

The working application uses OpenAI CLIP ViT-B/16 on CPU. In a recorded three-video run covering 2.279 video minutes, it indexed 48 scene frames in 15.49 seconds after model load and stored 570,215 logical bytes of vectors and thumbnails. Five repeated warm queries had 27.45 ms median latency. These are CPU measurements from an AMD Ryzen 5 5600H WSL2/Linux host.

The scene selector was chosen through a frozen benchmark containing 24 positive queries across six windows from two public films. Scene midpoint indexing reached 83.33% Recall@1, 87.50% Recall@3, and 81.82% short-event Recall@3. This small-corpus result does not establish quality for arbitrary personal videos, absence queries, or whole libraries.

ClipTrail also preserves a clean inference-backend boundary for Windows ARM64/QNN. On an ASUS Snapdragon X2 Elite, the fixed CLIP image graph completed native ARM64 ONNX Runtime QNN inference with the pinned HTP backend loaded, one QNN partition, and output matching the CPU reference. The required hardware profiling events were not captured, so physical NPU execution remains unverified. ClipTrail makes no claim of NPU acceleration, energy savings, HP-device deployment, or target application performance.

The project combines a usable private-search product with reproducible evidence: frozen labels, raw vectors, source and model hashes, transactional persistence tests, target logs, and preserved negative results. Its strongest contribution is practical local video retrieval with unusually explicit proof boundaries.
