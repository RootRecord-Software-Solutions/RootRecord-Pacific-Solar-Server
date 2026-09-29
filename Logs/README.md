# Logs

Central logging **ownership and path contracts** for Pacific server domains.

This tree is **not** a dump of rotating log files. Large or sensitive logs stay off-git under **Database** (or env overrides).

---

## Status (cutover complete 2026-09-28)

| Item | State |
| --- | --- |
| Domain folders | Ownership + path contracts |
| **Canonical poller log** | `/home/rootrecord/Database/LOGS/Automations/rootserver-poller.log` |
| **Canonical stack-reload log** | `/home/rootrecord/Database/LOGS/Automations/stack-reload.log` |
| Historical residual (G2) | `~/.ollama/skills/logs/store/*.log` — retired defaults; may still exist on disk |

Env overrides: `POLLER_LOG`, `STACK_RELOAD_LOG`.

---

## Code updated (org Pacific)

- `Automations/scripts/poller/poller-watch.py`
- `Automations/scripts/poller/open-poller-window.sh`
- `Automations/scripts/poller/run-poller.sh`
- `Automations/scripts/stack/do-stack-reload.sh`
- `Automations/scripts/stack/schedule-stack-reload.sh`

Detail: [Logs/Automations/README.md](Automations/README.md)

---

## Desk steps (operator)

```bash
mkdir -p /home/rootrecord/Database/LOGS/Automations
# optional migrate existing bytes
cp -an "$HOME/.ollama/skills/logs/store/rootserver-poller.log" \
  /home/rootrecord/Database/LOGS/Automations/ 2>/dev/null || true
cp -an "$HOME/.ollama/skills/logs/store/stack-reload.log" \
  /home/rootrecord/Database/LOGS/Automations/ 2>/dev/null || true
# Align systemd unit StandardOutput/Error if it hardcodes the old skills path
systemctl --user daemon-reload
# pull Pacific + schedule-stack-reload
```

If the unit still appends to the G2 path, either update the unit or set `POLLER_LOG` in the unit `Environment=` to the Database path so poller-watch and the writer match.

---

## Domain subfolders

| Folder | Role |
| --- | --- |
| `Logs/Automations/` | Poller + stack-reload contract |
| `Logs/Energy/` … | Ownership notes until writers assigned |

---

*Cutover documented 2026-09-28 HST — WO-SYS-001 path slice.*
