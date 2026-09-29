# Final narration — ClipTrail

**0:00–0:10**
A filename tells you almost nothing about the moments inside a video. Finding one scene usually means scrubbing by hand.

**0:10–0:23**
These three videos were indexed earlier, on this computer. ClipTrail chooses representative scene frames and saves their CLIP vectors, thumbnails, and timestamps in SQLite.

**0:23–0:43**
Now I can describe what I remember: a red-haired woman surrounded by burning rubble. ClipTrail searches the saved index locally. The real top result is Sintel at 23.25 seconds, with a thumbnail and similarity score.

**0:43–0:56**
Clicking the result opens the original video at that saved moment. The matching scene is right there, and the video never leaves this computer.

**0:56–1:06**
The index is sparse and persistent. Repeat searches encode just the text query and rank saved image vectors, without processing the videos again.

**1:06–1:16**
Recorded CPU result: 27.45 milliseconds median warm search; about 250 kilobytes of index payload per video minute.

**1:16–1:28**
The experimental Windows ARM64 QNN image path showed provider-level execution and parity on Snapdragon. Physical NPU execution remains unverified.
