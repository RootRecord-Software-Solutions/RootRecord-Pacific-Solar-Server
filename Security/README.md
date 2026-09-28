# Security

Security subsystem ownership: cameras (A-EYES), access surfaces, and related desk security tooling.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Shell only** |
| A-EYES runtime today (**G2**) | `~/.ollama/skills/a-eyes/` |
| A-EYES in G1 Old | **Not present** as top-level — evolved later |
| Frame / video data | `/home/rootrecord/Database/A-EYES/` (never commit) |
| Live UI | `127.0.0.1:8791` → `https://rootserver.rootrecord.cloud/aeyes` |

**Import order:** G2 `a-eyes/` first. Optional G1 recovery: `panels-cam/`, `kilauea/kilauea-cams` (diff only).

---

## jobs.py references (residual G2)

| Job id | Legacy path |
| --- | --- |
| `a_eyes_cam_server` | `…/skills/a-eyes/scripts/ensure_cam_server.sh` |
| `a_eyes_timelapse_catchup` | `…/skills/a-eyes/scripts/timelapse_catchup.sh` |
| `a_eyes_frame_grab` | `…/skills/a-eyes/scripts/grab_all.sh` |
| `a_eyes_timelapse_hourly_compile` | `…/skills/a-eyes/scripts/timelapse_hourly.sh` |
| `a_eyes_timelapse_daily_render` | `…/skills/a-eyes/scripts/timelapse_daily.sh` |

Library: path inventory, WO-AEYES, Old inventory map.

---

## Expected layout after G2 import

```text
Security/
  README.md
  a-eyes/
    scripts/
    store/         # CONNECTION.json local / gitignored
```

Never commit RTSP passwords or public UI passwords.

---

*Docs-only 2026-09-28 HST.*
