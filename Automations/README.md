# Automations

RootRecord automation orchestration: poller engine, job catalog, stack lifecycle, and operational scripts.

---

## Status (2026-09-28 ~16:25 HST)

| Item | State |
| --- | --- |
| Domain in this repo | **Live / authoritative** for poller core |
| Desk path | `/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/` |
| systemd unit | `rr-rootserver-poller.service` — **ExecStart on Pacific** (not G2 skills) |
| ExecStart | `/bin/bash "…/Automations/scripts/poller/run-poller.sh"` (quoted — path has spaces) |
| Public | `https://rootserver.rootrecord.cloud/` |
| Local HTTP | `http://127.0.0.1:8799/` |
| Log | `/home/rootrecord/Database/Logs/Automations/automations_current.log` |

**Policy:** Do not run the old desk (`~/.ollama/skills`) as the poller host. Migrate residual job commands domain-by-domain into this tree until the job catalog has zero skills paths.

---

## Layout

```text
Automations/
  README.md
  scripts/
    rootserver_poller.py
    jobs.py
    poller/
      internet_gate.py
      run-poller.sh
      open-poller-window.sh
      poller-watch.py
    stack/
      stop-poller-stack.sh
      do-stack-reload.sh
      schedule-stack-reload.sh
```

---

## systemd (standing)

Unit file: `~/.config/systemd/user/rr-rootserver-poller.service`

- `WorkingDirectory` = Pacific repo root (path with spaces OK as a single value)
- `ExecStart=/bin/bash "/…/Automations/scripts/poller/run-poller.sh"` — **required** quoting
- Drop-in `logging.conf` → append to Database Automations log (same path as `POLLER_LOG`)
- Never point `ExecStart` at `~/.ollama/skills/…`

---

## Deploy standing rule

```text
push → github_sync_all merge → schedule-stack-reload
```

Ctrl-C in the poller window / stack stop kills **entire** stack (poller + cloudflared + unit).

Paths under Pacific that contain spaces must be **double-quoted** in every `jobs.py` command string.

---

## Residual G2 job map (clear these next)

| Job id | Still on `~/.ollama/skills` | Target domain |
| --- | --- | --- |
| github_setup_remotes / github_sync_all | `github/` | Communications/github or Github/ |
| ollama_warmup / flm_npu_warmup | `plumbing/` | System/ or Plumbing/ |
| council_relay | `coms/telegram/` | Communications/telegram |
| a_eyes_* | `a-eyes/` | A-Eyes/ (or cameras domain) |
| sys_stats_cycle | `system-stats/` | System/ |
| worklog_scan | `reports/` | System/ or Reports/ |
| weather_poller | `Weather/` (missing; **disabled**) | Weather/ |
| energy actions | `energy/scripts/actions` | Energy/scripts/actions (Phase 2) |

Already on Pacific: self_terminal, cloudflare_tunnel, network_globe_hawaii, ecoflow_read_* commands (scripts path). EcoFlow **runtime modules** (`read_runner.py` etc.) still being filled from G2 energy lib.

---

## G1 (Old) — do not replace this engine blindly

| G1 packet | Guidance |
| --- | --- |
| `scheduler-clock` | **Retired** by G3 poller |
| `hybrid-night-poller` | **Retired** unless unique feature proven |
| `heartbeat` | G3 builtin |
| `net-gate` | Compare to `internet_gate.py` only |

---

*Updated 2026-09-28 HST after systemd cutover to Pacific.*
