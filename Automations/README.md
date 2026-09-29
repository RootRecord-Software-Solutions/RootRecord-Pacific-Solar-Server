# Automations

RootRecord automation orchestration: poller engine, job catalog, stack lifecycle, and operational scripts.

---

## Status (2026-09-28 ~17:01 HST)

| Item | State |
| --- | --- |
| Domain | **Live / authoritative** for poller core |
| Desk path | `…/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/` |
| systemd | `rr-rootserver-poller.service` — ExecStart on Pacific (quoted) |
| **Log authority** | **`/home/rootrecord/Database/Logs/` only** — not a Pacific domain folder |
| Canonical poller log | `/home/rootrecord/Database/Logs/Automations/automations_current.log` |
| Energy / System | LIVE on Pacific |

**Policy:** No old desk as poller host. Domain folders use existing capitalized names only. **Do not recreate `Logs/` under Pacific** — persistent logs belong to the Database tree (RootRecord-Database / desk `/home/rootrecord/Database`).

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
POLLER_LOG=/home/rootrecord/Database/Logs/Automations/automations_current.log
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

## Residual G2

worklog · github_* · plumbing · telegram · a_eyes_* · weather (disabled) · energy actions

---

*Updated 2026-09-28 HST — Pacific Logs/ removed; Database log authority.*
