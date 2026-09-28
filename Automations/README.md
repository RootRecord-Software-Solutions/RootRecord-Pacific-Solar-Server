# Automations

RootRecord automation orchestration: poller engine, job catalog, stack lifecycle, and operational scripts.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain in this repo | **Live / authoritative** for poller core |
| Desk path | `…/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/` |
| systemd | `rr-rootserver-poller.service` |
| Public | `https://rootserver.rootrecord.cloud/` |
| Local HTTP | `http://127.0.0.1:8799/` |

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

## Deploy standing rule

```text
push → github_sync_all merge → schedule-stack-reload
```

Ctrl-C in the poller window / stack stop kills **entire** stack (poller + cloudflared + unit).

---

## Residual note

Some `jobs.py` entries still use absolute `~/.ollama/skills/…` strings for **other** domains. Automations core uses relative discovery in shell helpers.

Boot `self_terminal` still lists skills-prefixed absolute paths for process/watch until a dedicated jobs rewrite to Ecosystem paths.

---

## G1 (Old) — do not replace this engine blindly

| G1 packet | Guidance |
| --- | --- |
| `scheduler-clock` | Likely **retired** by G3 poller |
| `hybrid-night-poller` | Likely **retired** — design review before any merge |
| `heartbeat` | G3 has builtin heartbeat |
| `net-gate` | Compare to `internet_gate.py` only |

G3 Automations is the modern scheduler. G1 schedulers are forensic unless a unique feature is proven missing.

---

*Docs-only 2026-09-28 HST.*
