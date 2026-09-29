# System

Host operating-system integration, system sampling, and desk host services.

---

## Status (2026-09-29 HST)

| Item | State |
| --- | --- |
| Domain folder | **`System/` only** |
| jobs.py | `sys_stats_cycle` → `System/scripts/sys-sample.sh` |
| Sample writes | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/System/` |
| Uptime log | `scripts/uptime_log.py tick\|facts\|recent` (G1 `uptime-log` port, stdlib) → Database `System/uptime/` (events JSONL, KEEP 400; GAP 180 s; boot_id). Job `system_uptime_log` (60 s) **gated OFF** (`RR_UPTIME_LOG=1`). LANDED · PASS one tick 2026-09-29 13:26 HST |
| Worklog | **Reports/** (WO-RPT-001) — no longer System residual |
| Ollama | **Active system service** — `ollama.service`, running as the `ollama` user |
| Ollama model store | **Service-owned**; not `/home/rootrecord/.ollama/models` |
| Ollama logs | **systemd journal**; `Database/Logs/AI/Ollama/` is reserved for deliberate RootRecord AI logs |
| Ollama RootRecord layout | `/home/rootrecord/.ollama/modelfiles` and `logs` point into Database-controlled AI paths; these are organizational symlinks and do not relocate the service model store |
| G2 skills | `/home/rootrecord/.ollama/skills` remains intact at restore commit `1dcee66` |
| Plumbing / telegram / a-eyes | Still G2 until imported |

### Naming

Use this folder name only. Do not create a parallel `system` or `system-stats` path for imports. Future Python under System should use package name **`System`** (or local modules under `System/lib` with PYTHONPATH set to `System/`). Full SOP: Library Pacific Domain Import Playbook — standing rules.

---

*Updated 2026-09-29 HST — Ollama service/storage boundary documented.*
