# ClipTrail demo narration — 75–90 seconds

This is the prepared recording script. The exact narration in the finished 88-second MP4 is in `demo/final-narration.md`.

**0:00–0:12 · Library** — “A video filename tells me very little about the moments inside it. ClipTrail makes those moments searchable on this computer, without uploading the video.”

**0:12–0:27 · Persistent index** — “I selected a local folder earlier. ClipTrail sampled visual scenes, embedded representative frames, and saved their vectors, thumbnails, and timestamps in SQLite. This is a persisted index; the CPU model stays loaded for repeated searches.”

**0:27–0:48 · Search** — Type **A red-haired woman surrounded by burning rubble.** “I can describe a scene instead of remembering a filename. ClipTrail ranks the stored frames locally. The top result is *Sintel* at about 23.25 seconds, with its thumbnail, score, and timestamp.”

**0:48–1:02 · Playback** — Click the result. “The selected result opens the original source around that saved moment. The video, query, index, and playback remain local.”

**1:02–1:18 · Efficiency** — “Scene midpoint indexing avoids embedding every frame. In the recorded three-video CPU run, 48 frames represented 2.279 minutes, with about 250 kilobytes of vectors and thumbnails per video minute. Five warm repeat queries had a 27.45 millisecond median on the recorded host.”

**1:18–1:28 · Boundary and close** — “An experimental Windows ARM64 QNN image path completed a fixed graph on Snapdragon with HTP loading, partitioning, and output parity. Physical NPU execution was not verified, so I make no acceleration claim. ClipTrail is useful now as private local video search.”

Use the native-player fallback if browser codec playback fails. Keep the backend badge visible. The indexing shown here is precomputed unless a separate live index is explicitly demonstrated.
