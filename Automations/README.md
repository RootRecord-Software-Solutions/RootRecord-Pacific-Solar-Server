# Automations

RootRecord automation orchestration: poller engine, job catalog, stack lifecycle, and operational scripts.

---

## Status (2026-09-28 ~16:56 HST)

| Item | State |
| --- | --- |
| Domain | **Live / authoritative** for poller core |
| Desk path | `…/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/` |
| systemd | `rr-rootserver-poller.service` — ExecStart on Pacific (quoted) |
| Log | `/home/rootrecord/Database/Logs/Automations/automations_current.log` |
| Energy / System jobs | **LIVE** on Pacific |

**Policy:** No old desk as poller host. Domain folders use the **existing capitalized names only** — never add a parallel lowercase dir/symlink for Python package convenience. See Library playbook standing rules.

---

## Layout

```text
Automations/scripts/
  rootserver_poller.py
  jobs.py
  poller/   # run-poller, open-poller-window, poller-watch, internet_gate
  stack/    # stop, do-reload, schedule-reload
```

---

## systemd + deploy

```text
ExecStart=/bin/bash "…/Automations/scripts/poller/run-poller.sh"
push → pull → schedule-stack-reload / systemctl --user restart rr-rootserver-poller
```

Quote every Pacific path that contains spaces (`1 - Servers`).

---

## Domain naming (standing)

| Rule | Detail |
| --- | --- |
| One folder per domain | `Energy/`, `System/`, `Weather/`, … as already created |
| Python package | Matches folder name (`import Energy…`) |
| No dual names | Do not add `energy` → `Energy` (or similar) symlinks |
| G2 import | Rewrite `import oldskillname` to the Pacific domain name |

Full SOP: Library `Documentation/00-architecture/Pacific-Domain-Import-Playbook-2026-09-28.md`.

---

## On Pacific (done)

| Piece | Notes |
| --- | --- |
| self_terminal, tunnel, network_globe | Pacific |
| ecoflow_read_* | `Energy/` only |
| sys_stats_cycle | `System/scripts/sys-sample.sh` |
| systemd + open-poller-window | Pacific |

## Residual G2

| Job | Target |
| --- | --- |
| worklog_scan | reports → System/ or Reports/ |
| github_* | Github/ or Communications/github |
| ollama / flm warmup | System/plumbing or Plumbing/ |
| council_relay | Communications/telegram |
| a_eyes_* | domain under Pacific |
| weather_poller | Weather/ (disabled until present) |
| energy actions | Energy/scripts/actions (Phase 2) |

---

*Updated 2026-09-28 HST — naming SOP.*
