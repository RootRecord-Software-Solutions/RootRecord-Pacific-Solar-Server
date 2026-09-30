# Slack

Slack communication integration and future automation hooks. Poller under Pacific Communications. Package name `Slack`. One folder. No lowercase twin.

**Status:** poller landed, not LIVE. Job `communications_slack` is off unless `RR_SLACK=1` at poller start. That flag stays unset. No token means status `not_configured` and no Slack HTTP. A present token still does not call Slack and does not post.

---

## Enablement gate

Before any Slack call on Pacific:

1. Store `SLACK_BOT_TOKEN` in `/home/rootrecord/master/master-key.env` only. Never commit the value.
2. Do not copy a token from archive, mirror, or inventory history.
3. Posts, including `chat.postMessage`, stay off until Alexander signs off.
4. Mark LIVE only after that sign-off. Leaving the job off is the current state.

Draft: `5 - RootRecord-Library/Documentation/06-development/Work-Orders/drafts/Slack_poller_Work_Order_WO-MIG-22-2026-09-29.md`

---

## Layout

| Role | Path |
| --- | --- |
| Code | `Communications/Slack/scripts/poll.py` |
| Allowlist | `Communications/Slack/lib/envload.py` (`SLACK_BOT_TOKEN` only) |
| Database | `2 - RootRecord-Database/Communications/Slack/` |
| Logs | `2 - RootRecord-Database/Logs/Communications/Slack/` |

No `Logs/` directory on the server.

---

*WO-MIG-22 2026-09-30 HST. No secrets in this file.*
