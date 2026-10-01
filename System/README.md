# System

Host operating-system integration, system sampling, and desk host services.

---

## Status (2026-09-30 02:00 HST)

| Item | State |
| --- | --- |
| Domain folder | **`System/` only** |
| State contract | [CONTRACT.md](CONTRACT.md). Live snapshot is Database `System/status/`, not committed |
| jobs.py | `sys_stats_cycle` → `System/scripts/sys-sample.sh` |
| Sample writes | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/System/` |
| Uptime log | `scripts/uptime_log.py tick\|facts\|recent` (G1 `uptime-log` port, stdlib) → Database `System/uptime/` (events JSONL, KEEP 400; GAP 180 s; boot_id). Job `system_uptime_log` (60 s) **gated OFF** (`RR_UPTIME_LOG=1`). LANDED · PASS one tick 2026-09-29 13:26 HST |
| Host desks | `scripts/host_desks.py net-sample\|net-usage\|security` (G1 `host-metrics` net + security port) → Database `System/network/` (`net-last.json`; `Daily/net-*.jsonl` git-ignored) and `System/security/security-last.json` (counts/booleans only). LANDED · smoke PASS 2026-09-29 14:00 HST (temp root). Sampler job **PROPOSED, not registered** (`system_net_sample`, 300 s, `RR_NET_SAMPLES=1`; block in Library `02-Runtime-Jobs-and-Control/Pending-Job-Registrations-2026-09-29.md`) |
| Host hardware | `scripts/host_hw.py` (G1 `host-metrics` Linux part: temp, per-drive usage, GPU name / busy %, NPU present / busy %; psutil). Prints JSON, on demand, writes nothing. Smoke PASS 2026-09-29 14:35 HST (48 °C, nvme0n1 56.5%, GPU 1%, NPU 0%). Not ported: `reset_series.py` (moves live history files — BLOCKED), Windows PDH counters |
| Worklog | **Reports/** (WO-RPT-001) — no longer System residual |
| Ollama | **Active system service** — `ollama.service`, running as the `ollama` user |
| Ollama model store | **Service-owned**; not `/home/rootrecord/.ollama/models` |
| Ollama logs | **systemd journal**; `Database/Logs/AI/Ollama/` is reserved for deliberate RootRecord AI logs |
| Ollama RootRecord layout | `/home/rootrecord/.ollama/modelfiles` and `logs` point into Database-controlled AI paths; these are organizational symlinks and do not relocate the service model store |
| G2 skills | `/home/rootrecord/.ollama/skills` is not intact at restore commit `1dcee66`. Desk sync has published the identical-file removals. HEAD `87ec9ac` (2026-09-30 01:50 HST) |
| Plumbing / telegram / a-eyes | Live commands are Pacific `System/scripts/plumbing/`, `Communications/telegram/`, and `Security/Cameras/` |

### Naming

Use this folder name only. Do not create a parallel `system` or `system-stats` path for imports. Future Python under System should use package name **`System`** (or local modules under `System/lib` with PYTHONPATH set to `System/`). Full SOP: Library Pacific Domain Import Playbook — standing rules.

---

*Updated 2026-09-30 02:00 HST — skills checkout is past restore commit `1dcee66` (HEAD `87ec9ac`). Plumbing, telegram, and a-eyes run from Pacific paths.*
