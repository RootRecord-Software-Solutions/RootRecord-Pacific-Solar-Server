# System

Host operating-system integration, system sampling, and desk host services.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder | **Shell only** |
| G2 residual | `~/.ollama/skills/system-stats/` → `sys_stats_cycle` |
| G1 cousins | `host-metrics`, `system-perf`, `uptime-log`, `log-cleanup` |
| Sample writes | `/home/rootrecord/Database/SYSTEM/` |

**Import order:** G2 system-stats first; then diff G1 host-metrics / system-perf.

**Plumbing decision:** G2 `plumbing/` (ollama/flm) and G1 `ollama-*` may land under `System/scripts/plumbing/` or a future `Plumbing/` domain — operator chooses at import.

---

## jobs.py (residual G2)

| Job id | Path |
| --- | --- |
| `sys_stats_cycle` | `…/skills/system-stats/scripts/sys-sample.sh` |
| `ollama_warmup` / `flm_npu_warmup` | `…/skills/plumbing/scripts/*` (no System folder yet) |

---

## Expected layout after import

```text
System/
  README.md
  scripts/
    sys-sample.sh
    # optional: plumbing/
```

---

*Docs-only 2026-09-28 HST.*
