# Automations

RootRecord automation orchestration: poller engine, job catalog, stack lifecycle, and operational scripts.

---

## Status (2026-09-28 ~16:40 HST)

| Item | State |
| --- | --- |
| Domain in this repo | **Live / authoritative** for poller core |
| Desk path | `/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/` |
| systemd unit | `rr-rootserver-poller.service` — **ExecStart on Pacific** |
| ExecStart | `/bin/bash "…/Automations/scripts/poller/run-poller.sh"` (quoted — path has spaces) |
| Public | `https://rootserver.rootrecord.cloud/` |
| Local HTTP | `http://127.0.0.1:8799/` |
| Log | `/home/rootrecord/Database/Logs/Automations/automations_current.log` |
| Energy jobs | **LIVE** — SUMMARY delta2 / river2pro alternating on Pacific |

**Policy:** Do not run the old desk (`~/.ollama/skills`) as the poller host. Migrate residual job commands domain-by-domain until `jobs.py` has zero skills paths.

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

Unit: `~/.config/systemd/user/rr-rootserver-poller.service`

- `WorkingDirectory` = Pacific repo root
- `ExecStart=/bin/bash "/…/Automations/scripts/poller/run-poller.sh"` — **required** quoting
- Drop-in `logging.conf` → Database Automations log (same as `POLLER_LOG`)
- Never point `ExecStart` at `~/.ollama/skills/…`

Open-window wrapper (any desk shortcut):

```bash
#!/usr/bin/env bash
exec /bin/bash "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/scripts/poller/open-poller-window.sh"
```

---

## Deploy standing rule

```text
push → github_sync_all merge → schedule-stack-reload
```

Ctrl-C in the poller window / stack stop kills **entire** stack (poller + cloudflared + unit).

Pacific paths with spaces must be **double-quoted** in every `jobs.py` command string.

---

## On Pacific (done)

| Job / piece | Notes |
| --- | --- |
| self_terminal | process + watch on Pacific |
| cloudflare_tunnel | Pacific cloudflared bin |
| network_globe_hawaii | quoted Pacific script |
| ecoflow_read_boot / cycle | Pacific Energy/scripts/read; lib + `energy`→`Energy` symlink |
| systemd + open-poller-window | Pacific only |

---

## Residual G2 (clear next)

| Job id | Still on `~/.ollama/skills` | Target |
| --- | --- | --- |
| sys_stats_cycle | `system-stats/` | **System/** (next) |
| worklog_scan | `reports/` | System/ or Reports/ |
| github_setup_remotes / github_sync_all | `github/` | Github/ or Communications/github |
| ollama_warmup / flm_npu_warmup | `plumbing/` | System/ or Plumbing/ |
| council_relay | `coms/telegram/` | Communications/telegram |
| a_eyes_* | `a-eyes/` | A-Eyes/ |
| weather_poller | missing; **disabled** | Weather/ |
| energy actions | `energy/scripts/actions` | Energy/scripts/actions (Phase 2) |

---

## Energy package note

```bash
cd "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"
ln -sfn Energy energy   # required: import energy.*
```

`Energy/lib/py` sets `PYTHONPATH` = vendor + Pacific root.

---

*Updated 2026-09-28 ~16:40 HST — Energy Phase 1 LIVE.*
