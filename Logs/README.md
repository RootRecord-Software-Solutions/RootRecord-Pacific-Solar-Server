# Logs (Pacific — ownership only)

**Authority for log bytes:** [`RootRecord-Database`](https://github.com/RootRecord-Software-Solutions/RootRecord-Database)  
Desk root: `/home/rootrecord/Database/`

This Pacific `Logs/` tree is **path contracts + domain markers**, not the live log files.

---

## Canonical paths (aligned 2026-09-28)

| Stream | Path (desk = Database repo) |
| --- | --- |
| Poller / automations | `/home/rootrecord/Database/Logs/Automations/automations_current.log` |
| Stack reload | `/home/rootrecord/Database/Logs/Automations/stack_reload_current.log` |

Env overrides: `POLLER_LOG`, `STACK_RELOAD_LOG`.

Archive rotation policy lives in Database: `Logs/*/Archive/README.md`.

---

## Code (this repo)

Defaults updated in:

- `Automations/scripts/poller/poller-watch.py`
- `Automations/scripts/poller/open-poller-window.sh`
- `Automations/scripts/poller/run-poller.sh`
- `Automations/scripts/stack/do-stack-reload.sh`
- `Automations/scripts/stack/schedule-stack-reload.sh`

---

## Operator

1. Confirm desk tree matches Database repo (`Logs/Automations/automations_current.log` already holds live poller history).
2. Align `rr-rootserver-poller.service` writer with the same path (or `Environment=POLLER_LOG=...`).
3. `git pull` Pacific + stack reload; banner `log` line should show `…/automations_current.log`.

Historical residual: `~/.ollama/skills/logs/store/` — do not use as default.

---

*Aligned to RootRecord-Database 2026-09-28 HST.*
