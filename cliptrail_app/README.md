# ClipTrail local application

The demo application keeps one CLIP backend loaded while you **select a video or folder → index it into SQLite → search in natural language → play a timestamped result**. CPU CLIP ViT-B/16 is the default and uses the existing measured `ClipReference` inference code and frozen scene selector. Videos, embeddings, previews and queries remain on the local machine. See the [application architecture](../project/docs/cliptrail-application-architecture.md).

Start the local interface from the workspace root:

```bash
.venv-cliptrail/bin/python -m cliptrail_app serve
```

It opens `http://127.0.0.1:8765/`. Use `serve --no-browser` to print the URL without launching a browser, `serve --port N` to choose a port, or place `--db /path/to/index.sqlite3` before `serve` to use another persistent index. The server binds to loopback only. The browser can choose a video or a folder, or enter an existing path on the same machine. Browser-selected media are copied into the index directory's `uploads/` folder before indexing; original files are not modified. The page shows backend, indexing/search status, progress, indexed videos, result thumbnails, timestamps and scores. Clicking a result seeks an HTML5 video player to that stored timestamp; **Open in local player** is available when a browser cannot decode a source. Browser codec support varies, especially for `.mov`. A local access token guards the API; the server serves the source video from the local filesystem to the local browser for playback. Stop the server with Ctrl+C.

The backend loads once when the server starts. Searches reuse it and the saved image vectors; each search computes only a text embedding. The UI labels the default as CPU CLIP and the optional `serve --backend qnn` as experimental QNN with hardware execution unverified. QNN application operation has not been validated on target; no physical NPU acceleration claim is made.

## Command-line flow

Run from the workspace root with the existing `.venv-cliptrail` environment:

```bash
.venv-cliptrail/bin/python -m cliptrail_app index /path/to/video.mp4
.venv-cliptrail/bin/python -m cliptrail_app index /path/to/video-folder
.venv-cliptrail/bin/python -m cliptrail_app search 'a red-haired woman surrounded by burning rubble'
.venv-cliptrail/bin/python -m cliptrail_app open 7
.venv-cliptrail/bin/python -m cliptrail_app status
.venv-cliptrail/bin/python -m cliptrail_app metrics
```

`--db /path/to/index.sqlite3` goes before the subcommand. By default, the index is `.cliptrail/index.sqlite3` under the working directory. Folder indexing is recursive for `.mp4`, `.mov`, `.mkv`, `.m4v`, `.avi` and `.webm`. `index` shows decode/extract/embed progress and skips a video when its content hash, sampler and model identity already match. `--force` rebuilds it. A failed video is reported and other folder members continue; the command exits nonzero if any failed. Replacing a video's stored frames is transactional.

`search` returns filename, playback timestamp, cosine score, result ID and JPEG preview path. Use `--json` for machine-readable output, `--limit N` to change result count, or `--open 1` to open the first returned result. `open RESULT_ID` works in a later process because IDs and timestamps are stored in SQLite.

Playback prefers an installed `mpv`, `ffplay` or `vlc`. `--player NAME_OR_PATH` selects one explicitly. With no installed player, `open` generates a local HTML viewer with an HTML5 video element and seeks to the saved timestamp; `--player browser` forces this mode. The viewer path/URL is printed. Browser codec support varies, especially for `.mov`; use a native player if the browser cannot decode a source. The system opener returning success does not independently prove that a visible browser played it. No network service is started.

CPU model startup/asset verification happens once per CLI `index` or `search` process, but only once for the lifetime of `serve`. A prebuilt-index query performs one CLIP text encode and reads stored image vectors; it does not re-embed video frames. Query latency printed by `search` excludes model startup, while an external wall-clock run includes it. `metrics` reports per-video indexing time and logical embedding/thumbnail bytes per video minute plus the current SQLite disk footprint. Model startup, cache files and SQLite page overhead are separate costs.

The optional `--backend qnn` adapter has the same application interface. It uses the pinned extracted image graph with strict CPU fallback disabling and the CPU CLIP text tower in one native Windows ARM64 Python environment. That environment must provide the issued QNN runtime **and** PyTorch/Transformers. The application QNN adapter has not been run on target. The earlier target smoke proved QNN inference and parity but did not capture direct hardware device events, and its process crashed after persisting output. **No verified NPU execution, speed or energy claim follows from this option.** Backend identities keep CPU and QNN indexes separate.

## Verified first flow

The [saved local run](../experiments/cliptrail_app/results/first-flow/measurement.json) indexed the complete 52.42-second Sintel trailer into 16 scene frames. A CLIP query for the frozen red-haired-woman phrase ranked a frame at **23.25 s** first, inside its annotated **22–24 s** interval, with a persisted thumbnail and generated local playback viewer. This is one app smoke, not a new retrieval benchmark. The [application tests](tests/test_application.py) replay all 24 frozen scene queries from recorded vectors and reproduce 20/24 Recall@1, 21/24 Recall@3 and 9/11 short-event Recall@3 without rerunning inference.

## Persistent demo validation

The [three-video validation](../experiments/cliptrail_app/results/persistent-demo/validation.json) indexed a small folder containing the complete Sintel trailer and two 42-second Tears of Steel excerpts on this Linux CPU host. One loaded model indexed **48 scene frames** across **2.279 video minutes** in **15.49 s** (**6.80 s per video minute**, excluding 5.10 s model startup). Logical vectors and JPEGs grew by **570,215 bytes** (**250,186 bytes per video minute**); the closed SQLite file is **638,976 bytes**. These index-storage figures exclude source media and browser-selected local copies. The five repeated warm queries had **27.45 ms median** latency, with **34.70 ms maximum**. RSS reached **757.6 MB** after multi-video indexing and **913.6 MB** after queries. A fresh CLI process read all three videos and reproduced the top 23.25-second result from the saved index. These are one-host diagnostics, not a broad performance distribution or Snapdragon result. The two excerpts come from one film and do not establish broad-media retrieval quality.

The [HTTP integration test](tests/test_web.py) covers selection upload, background indexing/status, search, thumbnail delivery, byte-range video responses, local-player open and index reuse after restart. A [real-model HTTP smoke](../experiments/cliptrail_app/results/persistent-demo/real-http-smoke.json) retrieved the saved 23.25-second top result and delivered its JPEG and a byte range from the original video. These verify the source and timestamp reach playback endpoints; visible browser playback remains unconfirmed in this headless workspace. Frozen retrieval replay remains unchanged at **20/24 R@1, 21/24 R@3, 9/11 short R@3**.

```bash
PYTHONDONTWRITEBYTECODE=1 .venv-cliptrail/bin/python -m unittest discover -s cliptrail_app/tests -p 'test_*.py' -v
```
