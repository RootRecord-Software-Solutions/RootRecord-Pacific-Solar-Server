# Logs / Automations

## Canonical paths (cutover 2026-09-28)

| Stream | Path |
|--------|------|
| Poller live log | `/home/rootrecord/Database/LOGS/Automations/rootserver-poller.log` |
| Stack reload log | `/home/rootrecord/Database/LOGS/Automations/stack-reload.log` |

Env overrides: `POLLER_LOG`, `STACK_RELOAD_LOG`.

## Code that sets defaults

- `Automations/scripts/poller/poller-watch.py`
- `Automations/scripts/poller/open-poller-window.sh`
- `Automations/scripts/poller/run-poller.sh`
- `Automations/scripts/stack/do-stack-reload.sh`
- `Automations/scripts/stack/schedule-stack-reload.sh`

## Operator notes

1. Ensure `rr-rootserver-poller.service` writes to the same poller log path (or journal only).
2. One-time copy from G2 residual if desired:
   `cp -an ~/.ollama/skills/logs/store/rootserver-poller.log /home/rootrecord/Database/LOGS/Automations/`
3. Bytes live under **Database**, not this git folder.
