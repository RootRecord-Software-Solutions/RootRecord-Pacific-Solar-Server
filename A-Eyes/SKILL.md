---
name: a-eyes
description: Camera views only. Local server serves live stills from the DVR channels; grab_frame.py writes them to the Database. Use for cam stills, current.jpg, health check, public /aeyes live page.
---

# a-eyes

Cameras only — live stills, local server, optional public web UI.

## INFO — MUST HAVE

- Never invent a frame. No stream means an error response, not a fake image.
- Real DVR credentials go in `store/CONNECTION.json` (never in git).
- Public web password: `AEYES_PUBLIC_PASSWORD` in `/home/rootrecord/master/master-key.env`.
- Frames are written ONLY to `/home/rootrecord/Database/A-EYES/frames/`.
- `cam_server.py` binds `127.0.0.1:8791`. Public path is
  `https://rootserver.rootrecord.cloud/aeyes` via poller reverse-proxy.

## Live web UI

- URL: `https://rootserver.rootrecord.cloud/aeyes`
- Single password from `AEYES_PUBLIC_PASSWORD` (master-key.env)
- Channels 1–4, live JPEG refresh (~2s), not archived stills
- Install / wire proxy: `bash a-eyes/scripts/install_aeyes_web.sh`

## Timelapse

Window **05:00–19:00 HST** (14 hours), MP4 only → `final_output/master_stitched_timelapse.mp4`.
Daily stitch at **19:01**. Crop is applied at grab time (right edge pct + 20px).

## Run

```bash
python3 scripts/cam_server.py
# or
bash scripts/ensure_cam_server.sh
```
