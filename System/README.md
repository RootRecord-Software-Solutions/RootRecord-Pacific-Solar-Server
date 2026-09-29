# System

Host operating-system integration, system sampling, and desk host services.

---

## Status (2026-09-28 ~16:49 HST) — Phase 1 LIVE

| Item | State |
| --- | --- |
| Domain folder | **`System/` only** |
| jobs.py | `sys_stats_cycle` → `System/scripts/sys-sample.sh` |
| Sample writes | `/home/rootrecord/Database/SYSTEM/` |
| Plumbing / worklog | Still G2 until imported |

### Naming

Use this folder name only. Do not create a parallel `system` or `system-stats` path for imports. Future Python under System should use package name **`System`** (or local modules under `System/lib` with PYTHONPATH set to `System/`). Full SOP: Library Pacific Domain Import Playbook — standing rules.

---

*Phase 1 LIVE 2026-09-28 HST.*
