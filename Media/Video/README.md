# Media / Video

Pacific video helpers. Output bytes go to Database `Media/Video/` (`*.mp4` is git-ignored there).

| Script | What | Schedule | State |
| --- | --- | --- | --- |
| `scripts/mp4_converter.py` | Still image + MP3/WAV → MP4 (G1 `mp4-converter` port: libx264 stillimage, AAC 192k, `-shortest`, faststart; nice 10, 180 s timeout) | On demand only (no `jobs.py` entry) | LANDED · PASS (2 s synthetic test, 2026-09-29 13:29 HST) |

```bash
python3 scripts/mp4_converter.py --audio "<file.wav|mp3>" --thumb "<still.jpg>" [--out "<file.mp4>"] [--current "<copy.mp4>"]
```

- Default still: `--thumb` or env `RR_BROADCAST_THUMB` (G1 used the Ava-Core daily broadcast thumbnail; no G3 equivalent yet).
- No upload, broadcast or playback. G1 source: `Solar-Pacific-RootRecord-Server-Old/mp4-converter/` (KEPT, not retired).

*Added 2026-09-29 (migration pass, Library `Documentation/00-architecture/Old-Repo-Migration-Matrix.md`).*
