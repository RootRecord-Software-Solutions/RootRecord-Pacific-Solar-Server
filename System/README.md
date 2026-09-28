# System

Host operating-system integration, system sampling, and desk host services.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Shell only** |
| sys-sample runtime today | Legacy `~/.ollama/skills/system-stats/` |
| Sample writes | `/home/rootrecord/Database/SYSTEM/` (never commit bulk samples) |

---

## jobs.py references (residual)

| Job id | Legacy path |
| --- | --- |
| `sys_stats_cycle` | `…/skills/system-stats/scripts/sys-sample.sh` (every 5s) |

Observed healthy in poller window 2026-09-28 (SYSTEM lines + JSON under Database/SYSTEM).

---

## Expected layout after import (docs only)

```text
System/
  README.md
  scripts/
    sys-sample.sh
  # optional: other host helpers
```

---

*Docs-only update 2026-09-28 HST.*
