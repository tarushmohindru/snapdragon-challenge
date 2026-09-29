# Demo assets and provenance

The **final deliverable** is `../ClipTrail-Demo.mp4` (88.000 seconds). Its poster is
`../ClipTrail-Demo-Poster.jpg`. The full local Hyperframes project and intermediate
capture are preserved in `brag-output-2026-09-29-121741/` at the repository root;
that working directory is intentionally excluded from the public Git tree. The
rendered MP4 and poster are the files to use for publication.

- `capture.mp4` — real screen capture of the running persistent ClipTrail browser app, including typing, search, result selection, and playing source media. Located in the local Hyperframes working directory.
- `live-library.png`, `live-results.png`, `live-playback.png` — real browser stills used for readable holds.
- `composition/index.html` — Hyperframes composition with restrained title, architecture, metric, attribution, and QNN boundary overlays.
- `composition/assets/voice/01.wav` through `07.wav` — narration generated locally with Hyperframes Kokoro.
- `composition/assets/music/happy-beats-business-moves-vol-12-by-ende-dot-app.mp3` — bundled brag music bed, mixed quietly under the narration.
- `composition/snapshots/` — visual review frames.

Source video in the capture: Blender Foundation, *Sintel*, CC BY 3.0. The three-video SQLite index is the preserved real validation index. The canonical query returned the real top row `sintel_trailer-480p.mp4` at 23.25 s with similarity 0.3574781888. Browser playback was observed at time greater than 23.2 s, ready state 4, unpaused, and with no media error.

## Deviations from the requested outline

- The architecture callout starts at 0:56 and the two CPU metrics appear at 1:06, giving the QNN boundary a full 12 seconds at the end.
- Only two CPU metrics are displayed; the small retrieval benchmark is omitted to keep the product flow clear.
- No face-cam or live indexing appears. The library is explicitly labeled as previously indexed.
