# Automations

RootRecord automation orchestration: poller engine, job catalog, stack lifecycle, and operational scripts.

---

## Status (2026-09-29 HST)

| Item | State |
| --- | --- |
| Domain | **Live / authoritative** for poller core |
| Desk path | `…/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/` |
| systemd | `rr-rootserver-poller.service` — ExecStart on Pacific (quoted) |
| **Log authority** | **`/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/` only** — not a Pacific domain folder |
| Canonical poller log | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log` (git-ignored; hourly `Archive/` is synced) |
| Energy / System | LIVE on Pacific |
| Weather | **PASS** — `weather_poller` enabled; run + reports verified 2026-09-29 01:50/01:59 HST |
| Ollama | **System service** — separate service-owned model store; operational logs are in journald |

**Policy:** No old desk as poller host. Domain folders use existing capitalized names only. **Do not recreate `Logs/` under Pacific** — persistent logs belong to `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/`. GitHub sync flags and backups stay under `2 - RootRecord-Database/Github`. Mirror worktrees stay in `Github-worktrees/` at the ecosystem root. Nothing writes to `/home/rootrecord/Database`.

---

## Layout

```text
Automations/scripts/
  rootserver_poller.py
  jobs.py
  poller/   # run-poller, open-poller-window, poller-watch, internet_gate
  stack/    # stop, do-reload, schedule-reload
```

Pacific domain shells (code): Automations, Communications, Energy, System, Weather, Geology, Github, Security, …

**Not a Pacific domain:** `Logs/` — removed; use Database.

---

## systemd + deploy

```text
ExecStart=/bin/bash "…/Automations/scripts/poller/run-poller.sh"
POLLER_LOG="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log"
push → pull → schedule-stack-reload / systemctl --user restart rr-rootserver-poller
```

Quote every Pacific path that contains spaces (`1 - Servers`).

---

## Domain naming (standing)

| Rule | Detail |
| --- | --- |
| One folder per **code** domain | `Energy/`, `System/`, `Geology/`, … |
| Logs | Database only — never a second log tree on Pacific |
| Python package | Matches folder name |
| No dual names | No lowercase symlink siblings |

Full SOP: Library `Pacific-Domain-Import-Playbook-2026-09-28.md`.

---

## On Pacific (done)

| Piece | Notes |
| --- | --- |
| self_terminal, tunnel, network_globe | Pacific |
| ecoflow_read_* | `Energy/` |
| sys_stats_cycle | `System/` |
| systemd + open-poller-window | Pacific |
| weather_poller | Pacific Weather scheduler; current statewide/county reports verified |

## Residual G2

worklog · github_* · plumbing · telegram · a_eyes_* · energy actions

---

*Updated 2026-09-29 HST — Weather PASS; Database log authority preserved.*
