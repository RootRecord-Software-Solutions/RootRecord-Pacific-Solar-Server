# Security

Security subsystem ownership: cameras (A-EYES), access surfaces, and related desk security tooling.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Shell only** |
| A-EYES runtime today | Legacy `~/.ollama/skills/a-eyes/` |
| Frame / video data | `/home/rootrecord/Database/A-EYES/` (never commit) |
| Live UI | `127.0.0.1:8791` → `https://rootserver.rootrecord.cloud/aeyes` |

---

## jobs.py references (residual)

| Job id | Legacy path |
| --- | --- |
| `a_eyes_cam_server` | `…/skills/a-eyes/scripts/ensure_cam_server.sh` |
| `a_eyes_timelapse_catchup` | `…/skills/a-eyes/scripts/timelapse_catchup.sh` |
| `a_eyes_frame_grab` | `…/skills/a-eyes/scripts/grab_all.sh` |
| `a_eyes_timelapse_hourly_compile` | `…/skills/a-eyes/scripts/timelapse_hourly.sh` |
| `a_eyes_timelapse_daily_render` | `…/skills/a-eyes/scripts/timelapse_daily.sh` |

Full inventory: Library `Documentation/00-architecture/Pacific-Jobs-Path-Inventory-2026-09-28.md`.  
Optimization work order: Library WO-AEYES.

---

## Expected layout after import (docs only)

```text
Security/
  README.md
  a-eyes/          # or Security/scripts/ — operator choice at import
    scripts/
    store/         # CONNECTION.json stays local / gitignored
```

Never commit RTSP passwords or public UI passwords.

---

*Docs-only update 2026-09-28 HST.*
