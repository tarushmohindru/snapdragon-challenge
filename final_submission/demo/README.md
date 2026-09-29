# ClipTrail demo handoff

Record the working CPU application with a **persisted local index**. Do not describe the prebuilt index as live indexing. Keep the CPU backend badge visible. The canonical search is:

> A red-haired woman surrounded by burning rubble.

With the preserved three-video demo index and its matching source library, the expected top result is `sintel_trailer-480p.mp4` at approximately **23.25 s**. Confirm it again in preflight; a newly rebuilt index may differ if assets or versions change.

From the repository root, launch with:

```bash
bash final_submission/demo/launch-demo.sh
```

The helper uses the preserved local index when present and its source paths exist. Otherwise it uses `.cliptrail/demo.sqlite3`; if no local index exists, run the reset helper to prepare one. The reset helper downloads/provisions public assets if necessary and runs the existing application indexer. This is **demo setup**, not a rerun of the frozen retrieval benchmark. On a public clone:

```bash
bash experiments/cliptrail/provision_reference.sh
bash final_submission/demo/reset-demo.sh
bash final_submission/demo/launch-demo.sh
```

The setup requires an internet connection to provision dependencies and source assets. Once those assets are present, indexing, search, and playback are local. The app serves on `http://127.0.0.1:8765/` (loopback only). Chrome or Edge are reasonable first browsers; test codec playback on the actual recording machine. Use **Open in local player** with `mpv`, `ffplay`, or `vlc` if the browser cannot play the source. See [preflight](preflight-checklist.md) and [fallback](fallback-plan.md).

For the live indexing option, choose a short, not-yet-indexed local video and accurately describe that segment as live. It is optional; the primary demo should stay under 90 seconds.
