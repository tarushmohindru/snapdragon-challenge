# Demo fallback plan

1. **Browser codec failure:** use the result card's **Open in local player** action. Test `mpv`, `ffplay`, or `vlc` before recording. Explain that the stored timestamp opens the original source locally.
2. **Live indexing runs long:** omit it. Show the existing library and say clearly that it is a persisted, previously built local index.
3. **Query result differs:** stop the take. Verify the chosen database, source hashes, backend badge, and query spelling. Do not stage or edit a fake result. Use the preserved demo index if available.
4. **Server or browser does not open:** the helper prints the local URL. Open `http://127.0.0.1:8765/` manually; restart after closing any process already using port 8765.
5. **Playback cannot be visually demonstrated:** show the ranked result and the tested native-player route, and state the limitation honestly. Do not claim that the recording showed playback.
