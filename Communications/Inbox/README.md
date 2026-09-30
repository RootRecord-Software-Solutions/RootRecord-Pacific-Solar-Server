# Inbox

Local reader of the quiet-mode relay hold. No second Telegram poller. No Discord or Slack post. No Cloudflare D1 call. D1 sync has no Folder, so the old edge delete stays paused.

| Place | Path |
| --- | --- |
| Code | `1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/Inbox/scripts` |
| Database | `2 - RootRecord-Database/Communications/Inbox/` |
| Logs | `2 - RootRecord-Database/Logs/Communications/Inbox/` |

The hold itself stays at `2 - RootRecord-Database/Logs/Communications/Relay-Inbox/`, written by `Communications/telegram/scripts/council-relay.py`. This package only reads that JSONL.

`inbox.py subscribe` records private `/subscribe` and `/unsubscribe` into `subscribers.json`. `drain` copies held rows into `feedback.jsonl` and `drain-ledger.jsonl` and leaves the hold files in place. `overnight` writes `overnight-last.txt` (solar line only when `--solar-line` is passed). `feedback --note` appends `reply-feedback.jsonl`.

Jobs `inbox_drain` (`RR_INBOX_DRAIN`) and `overnight_relay` (`RR_OVERNIGHT_RELAY`, 22:20 HST) are gated off. Sends stay off (`RR_RELAY_REPLIES` stays unset).

*WO-MIG-31, 2026-09-30 HST.*
