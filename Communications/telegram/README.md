# telegram

Telegram communication integration, alerts, and council-relay services.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Folder in this repo | **Shell only** |
| Live relay today | Legacy `~/.ollama/skills/coms/telegram/` |
| Standing rule | **One** getUpdates owner (council-relay) |

---

## jobs.py references (residual)

| Job id | Legacy path |
| --- | --- |
| `council_relay` | `…/skills/coms/telegram/scripts/ensure-relay.sh` |
| cwd | `…/skills/coms/telegram` |

Do not run a second Telegram poller against the same bot token.

---

## Expected layout after import (docs only)

```text
Communications/telegram/
  README.md
  scripts/
    ensure-relay.sh
    council-relay.py   # if packaged here
```

Secrets / bot tokens stay local.

---

*Docs-only update 2026-09-28 HST.*
