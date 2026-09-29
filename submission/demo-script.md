# ClipTrail demo script

The actual 88-second Hyperframes recording is complete. Its exact spoken transcript, shot timeline, credits, and provenance are in `final_submission/demo/`; the MP4 is `final_submission/ClipTrail-Demo.mp4`. The timings below are the pre-recording plan.

Target length: **75–90 seconds**. Use the persistent CPU application and a preindexed folder. Keep the backend badge visible. Do not show an “NPU accelerated” label.

## Before recording

- Start the application with `.venv-cliptrail/bin/python -m cliptrail_app serve`.
- Confirm the badge reads **CPU CLIP backend** and the three-video library is present.
- Confirm the *Sintel* source plays in the recording browser.
- Put the demo window at a readable zoom and hide unrelated desktop content.
- Keep a second, not-yet-indexed short video ready if live indexing will be shown.
- Close network-dependent applications. ClipTrail itself should need no network after provisioning.

## Script

### 0:00–0:12 — Problem and product

**Screen:** ClipTrail home, indexed library visible.

**Say:** “Video filenames tell me almost nothing about the moments inside them. ClipTrail creates a private semantic index on this computer, then lets me find a moment with a sentence.”

### 0:12–0:27 — Local persistent library

**Screen:** Point to the CPU backend badge, indexed-video list, scene counts, and local-index status.

**Say:** “I can select one video or a folder. ClipTrail samples scenes, embeds representative frames, and saves the vectors, thumbnails, and timestamps in SQLite. The model stays loaded, and these videos do not need to be re-embedded for every query.”

Optional live action: add the prepared short video and briefly show decode, extract, and embed progress. Skip this if it makes the demo exceed 90 seconds.

### 0:27–0:48 — Natural-language retrieval

**Screen:** Search for `A red-haired woman surrounded by burning rubble.`

**Say:** “I’ll describe a visual moment rather than a filename. The warm search ranks the saved scene vectors locally.”

**Screen:** Results appear. Point to thumbnail, filename, 23.25-second timestamp, score, and displayed query latency.

**Say:** “The first result is the matching scene in *Sintel* at 23.25 seconds.”

### 0:48–1:02 — Playback

**Screen:** Select the first result. Let playback begin around the returned moment.

**Say:** “Selecting the result opens the original source at the stored timestamp. The source video, index, query, and playback all stay on this computer.”

### 1:02–1:18 — Why sparse indexing matters

**Screen:** Return to the library and results.

**Say:** “Instead of embedding every frame, ClipTrail uses scene midpoints. In the recorded three-video run, it indexed 48 frames across 2.279 video minutes, used about 570 kilobytes for vectors and thumbnails, and repeated searches had 27.45 millisecond median latency on the recorded CPU host.”

### 1:18–1:28 — Snapdragon boundary and close

**Screen:** Show a small architecture/evidence slide or remain on the CPU badge.

**Say:** “The same application boundary supports an experimental Windows ARM64 QNN image backend. We observed native QNN graph execution, HTP loading, partitioning, and embedding parity on Snapdragon. Hardware profiling was incomplete, so we do not claim verified NPU acceleration. ClipTrail is useful now as private local search, with a precise path for future Snapdragon optimization.”

## Capture fallback

If live playback fails because of browser codec support, use **Open in local player**. If a new indexing run is too slow for the recording, show the already indexed library and clearly call it a persisted index. Do not use prerecorded output while describing it as a live run.
