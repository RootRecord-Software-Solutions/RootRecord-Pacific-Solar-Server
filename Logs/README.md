# Logs

Central logging ownership notes for Pacific server domains.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder | Shell / ownership marker |
| Poller log (observed) | `~/.ollama/skills/logs/store/rootserver-poller.log` |
| Generated operational logs | Prefer Database / desk log stores — not this git tree |

This folder is for **ownership and policy**, not a dump of rotating log files. Large or sensitive logs stay off-git.

---

## Future optional layout

```text
Logs/
  README.md
  # optional: logrotate configs, path contracts per domain
```

Moving the poller log path into a Logs/Automations contract is optional and should not break the live unit until coordinated.

---

*Docs-only update 2026-09-28 HST.*
