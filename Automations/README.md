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
    rootserver_poller.py    # engine
    jobs.py                 # catalog
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

Some `jobs.py` entries still use absolute `~/.ollama/skills/…` strings for **other** domains (Energy, A-EYES, Github, …). Automations core itself is domain-wired with relative discovery in shell helpers. See Library path inventory.

Boot `self_terminal` still lists skills-prefixed absolute paths for process/watch — operational until those strings are rewritten to the Ecosystem Servers path in a dedicated jobs edit.

---

*Docs-only update 2026-09-28 HST.*
