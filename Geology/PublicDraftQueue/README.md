# PublicDraftQueue

Queues a Kīlauea public draft from Database `Geology/Volcanoes/Hawaii/kilauea_current.json` when the HVO notice id or alert level changes.

No HTTP. No Grok. No Discord, Slack, or Telegram send. Council publishes a queued file later.

```text
python3 scripts/queue_draft.py
```

| Result | What it writes |
| --- | --- |
| `no-notice` | Log line only. Does not overwrite `publish-last.json`. |
| `seed` | `publish-last.json`. No queue file. |
| `unchanged` | Refreshes `publish-last.json`. No queue file. |
| `queued` | One `queue/YYYY-MM-DDTHHMMSS-kilauea-cron.md` (1900 characters max) and `publish-last.json`. |

Data: `2 - RootRecord-Database/Geology/PublicDraftQueue/`. Logs: `2 - RootRecord-Database/Logs/Geology/PublicDraftQueue/`.

Job `geology_kilauea_public_draft` in `Automations/scripts/jobs.py` stays off unless `RR_KILAUEA_DRAFT=1` at poller start. That variable stays unset.
