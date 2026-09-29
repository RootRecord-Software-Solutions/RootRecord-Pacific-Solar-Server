# Logs

Central logging **ownership and path contracts** for Pacific server domains.

This tree is **not** a dump of rotating log files. Large or sensitive logs stay off-git under Database (or env overrides).

---

## Baseline (pre-cutover, observed 2026-09-28)

| Item | State |
| --- | --- |
| Domain folders | Ownership markers only |
| Poller log (live) | `~/.ollama/skills/logs/store/rootserver-poller.log` |
| Stack reload log | `~/.ollama/skills/logs/store/stack-reload.log` |
| Policy | Prefer Database / desk stores — not this git tree |

---

## Target after cutover (WO-SYS-001 / log storage upgrade)

| Stream | Path |
| --- | --- |
| Poller live log | `/home/rootrecord/Database/LOGS/Automations/rootserver-poller.log` |
| Stack reload log | `/home/rootrecord/Database/LOGS/Automations/stack-reload.log` |

Env overrides: `POLLER_LOG`, `STACK_RELOAD_LOG`.

Code defaults in `Automations/scripts/poller/*` and `stack/*` will be updated in the same session; systemd unit must match or the status window will be empty.

---

*Baseline recorded 2026-09-28 HST — cutover next.*
