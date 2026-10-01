# telegram

Telegram communication integration, alerts, and council-relay services.

---

## Status (2026-09-30 02:00 HST)

| Item | State |
| --- | --- |
| Folder in this repo | Live relay scripts under `Communications/telegram/` |
| Live relay today | Poller boot job `council_relay` runs `ensure-relay.sh`. Original council replies are on (`COUNCIL_REPLIES=1`). Sandbox replies are off. Private DMs stay off (`RR_RELAY_REPLIES` default 0). Reports use `RR_TELEGRAM_DEST=council`. Inference is NPU `llama3.2:3b`, on demand, context 4096. |
| Sandbox | `SANDBOX_CHAT_ID=-1004406495175` ([t.me/c/4406495175/2](https://t.me/c/4406495175/2)). `SANDBOX_REPLIES=0` does not answer that chat. |
| Standing rule | **One** getUpdates owner (council-relay) |
| Contract | [CONTRACT.md](CONTRACT.md) |

---

## jobs.py

`council_relay` runs Pacific `Communications/telegram/scripts/ensure-relay.sh` (cwd `Communications/telegram`). Original council replies are on. Sandbox replies are off. Private DMs stay off (`RR_RELAY_REPLIES` default 0). Council inference is NPU `llama3.2:3b`, on demand, context 4096.

Do not run a second Telegram poller against the same bot token.

---

## Layout

```text
Communications/telegram/
  README.md
  scripts/
    ensure-relay.sh
    council-relay.py
```

Secrets / bot tokens stay local.

---

*Updated 2026-09-30 afternoon — sandbox replies on. Live council and private DMs stay off. Council inference is NPU llama3.2:3b, on demand.*

---

## Quiet-mode inbox + replay (2026-09-29 ~04:05 HST, approved: Library 08-ideas relay-quiet-mode-message-hold)

- With `RR_RELAY_REPLIES=0` (default), `scripts/council-relay.py` appends each consumed message (ts, chat id, from, persona target, message_id, text) to the git-ignored `2 - RootRecord-Database/Logs/Communications/Relay-Inbox/relay-inbox_current.jsonl`, cut hourly into `Archive/YYYY-MM-DD/`. Takes effect at the next relay start.
- `scripts/relay-inbox-replay.py` lists held messages (default, read-only). It answers them only with `--send` **and** `RR_RELAY_REPLIES=1` (sign-off needed), and records each in `Relay-Inbox/replayed.jsonl`.
- Mid-session recovery: `Automations/scripts/supervise-services.sh` (job `service_supervisor`, every 300 s from the next poller start) re-runs `scripts/ensure-relay.sh` if the relay is dead (max 3 per 30 min, then BLOCKED).
