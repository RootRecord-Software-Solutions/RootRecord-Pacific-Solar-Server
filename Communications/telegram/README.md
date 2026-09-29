# telegram

Telegram communication integration, alerts, and council-relay services.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Folder in this repo | **Shell only** |
| Live relay today | Pacific `Communications/telegram/` (poller boot job `council_relay`); G2 copy kept dormant |
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

---

## Quiet-mode inbox + replay (2026-09-29 ~04:05 HST, approved: Library 08-ideas relay-quiet-mode-message-hold)

- With `RR_RELAY_REPLIES=0` (default), `scripts/council-relay.py` appends each consumed message (ts, chat id, from, persona target, message_id, text) to the git-ignored `2 - RootRecord-Database/Logs/Communications/Relay-Inbox/relay-inbox_current.jsonl`, cut hourly into `Archive/YYYY-MM-DD/`. Takes effect at the next relay start.
- `scripts/relay-inbox-replay.py` lists held messages (default, read-only). It answers them only with `--send` **and** `RR_RELAY_REPLIES=1` (sign-off needed), and records each in `Relay-Inbox/replayed.jsonl`.
- Mid-session recovery: `Automations/scripts/supervise-services.sh` (job `service_supervisor`, every 300 s from the next poller start) re-runs `scripts/ensure-relay.sh` if the relay is dead (max 3 per 30 min, then BLOCKED).
