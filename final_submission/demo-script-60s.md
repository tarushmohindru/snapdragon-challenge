# ClipTrail demo narration — approximately 60 seconds

**0:00–0:10** — “Finding one visual moment inside a video usually means scrubbing by hand or uploading it. ClipTrail searches local videos without sending them to a cloud index.”

**0:10–0:22** — “This folder was indexed earlier. ClipTrail stored representative scene embeddings, thumbnails, and timestamps in SQLite. The CPU model stays loaded, so I can search the saved index repeatedly.”

**0:22–0:40** — Search **A red-haired woman surrounded by burning rubble.** “The top result is *Sintel* near 23.25 seconds. I can see its thumbnail and score, then click to play the original video at that moment.”

**0:40–0:51** — “In one recorded CPU run, five warm searches had a 27.45 millisecond median; the logical vectors and thumbnails used about 250 kilobytes per video minute. These are single-host results.”

**0:51–1:00** — “A fixed image graph also ran through ONNX Runtime QNN on Snapdragon, with HTP loading and partitioning observed. Physical NPU execution remains unverified. The working product is private video search today.”
