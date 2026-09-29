# a-eyes — how the cameras work

## Hardware
- Night Owl DVR on the LAN, 4 channels (ch1–ch4).
- Connect over RTSP using `store/CONNECTION.json` (IP + RTSP user/password).

## Scripts
- `scripts/grab_frame.py` — pulls one JPEG per channel via ffmpeg/RTSP and
  writes it straight to `/home/rootrecord/Database/A-EYES/frames/`. That's
  the only thing it does — no serving, no power control, no mirroring.
- `scripts/cam_server.py` — the one local server that hosts the camera
  views. Binds `127.0.0.1:8791`. Calls `grab_frame.grab_jpeg()` on request
  and returns the JPEG. If another server is found running the old routes
  somewhere else, it's leftover and should be stopped/removed.

## Storage
- Single source of truth: `/home/rootrecord/Database/A-EYES/frames/`
- No local `store/frames/` — that mirror was removed.

## Watermark crop
- `store/CONNECTION.json` → `capture.crop_right_pct` (default `0.08`) cuts that
  fraction off the RIGHT edge of every frame in the same ffmpeg pass that grabs
  it — no second read, no second file, no post-processing step. Left side
  (where the Night Owl timestamp OSD sits) and full height are untouched.
- Override per-run without editing the config: `AEYES_CROP_RIGHT_PCT=0.06 python3 scripts/grab_frame.py 1`.
  Grab one frame, look at it, nudge the number up/down until the watermark is
  just gone and re-check that the timestamp text is still intact, then set
  the final value in `capture.crop_right_pct`.
- `0.08` is a starting guess, not a measurement — tune it against a real frame.

## No-overlap guarantee
- `frames/` is touched from three independent places: the scheduled grab
  (`grab_all.sh` via the poller), `cam_server.py`'s on-demand `/current.jpg`
  (a separate always-on process, NOT covered by the poller's own
  single-threaded serialization), and the hourly compile's read/archive step.
  All three now go through one cross-process `flock` (`grab_frame.frames_lock`,
  lock file `/tmp/a-eyes-frames.lock`) so none of them can ever run at the
  same instant.
- Grabs (scheduled or on-demand) take the lock **non-blocking**: if it's busy,
  that one frame is skipped (logged, exit 0, not treated as a failure) rather
  than queued or retried. Frames are the lowest-priority thing here — with a
  grab roughly every ~1s of wall time, skipping one is a non-event.
- The hourly compile takes the lock **blocking, up to 30s** for its two short
  read/archive windows only — never for the multi-second ffmpeg encode in
  between, so it doesn't starve grabs while it's rendering. If the lock is
  still busy after 30s it defers cleanly and the next catch-up run finishes
  the job (retired frames sweep on every subsequent hourly/catchup pass).

## Rules
- Never invent a frame or caption — no stream means an error, not a fake image.
- Secrets only in `store/CONNECTION.json` (or a secrets file you add) — never in git.
