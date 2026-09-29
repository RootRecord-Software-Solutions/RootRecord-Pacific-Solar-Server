# System

Host operating-system integration, system sampling, and desk host services.

---

## Status (2026-09-28 ~16:49 HST) — Phase 1 LIVE

| Item | State |
| --- | --- |
| Domain | **LIVE** on Pacific |
| jobs.py | `sys_stats_cycle` → `System/scripts/sys-sample.sh` (quoted) |
| Evidence | `SYSTEM cpu=… OK wrote …/Database/SYSTEM/samples/sys-20260928-164937.json` |
| Sample writes | `/home/rootrecord/Database/SYSTEM/` |
| Plumbing (ollama/flm) | Still G2 |
| worklog | Still G2 reports/ |

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/System/
```

### Layout on desk

```text
System/
  README.md
  scripts/sys-sample.sh
  lib/{sample.py,paths.py,status_json.py}
  db/{store.py,schema.sql,aggregate.py,…}
```

### Policy

No old desk for sys-stats. G2 `system-stats` is archive-only for this job.

---

*Phase 1 LIVE 2026-09-28 HST.*
