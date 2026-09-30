# Discord

Discord poller under Pacific Communications. Package name `Discord`. One folder. No lowercase twin.

**Status:** poller landed, not LIVE. Job `discord_poller` is `enabled: False`. `RR_DISCORD_POLLER` and `RR_DISCORD_POST` stay unset. No token means no Discord HTTP.

---

## Migration / enablement gate (required)

Before any Discord bot is brought online on Pacific:

1. Issue a new bot token from the Discord Developer Portal for the target application (Reset Token / generate).
2. Store it as `DISCORD_BOT_TOKEN` in `/home/rootrecord/master/master-key.env` only. Never commit the value.
3. Do not copy tokens from archive, mirror, or inventory history. Do not fall through `AVA_DISCORD_BOT_TOKEN`, `SEXI_DISCORD_BOT_TOKEN`, or `DISCORD_ROOTMC_BOT_TOKEN`.
4. `config/channels.json` stays `[]` until a channel id is accepted. An empty list does not call Discord, even after the token is present.
5. Posts stay off unless `RR_DISCORD_POST=1`. That gate is unset. Mark LIVE only after a smoke test Alexander signs off.

Canonical process: [WO-COM-002 — Discord Bot Credential Rotation](https://github.com/RootRecord-Software-Solutions/RootRecord-Library/blob/main/Documentation/06-development/Work-Orders/WO-COM-002-Discord-Bot-Credential-Rotation.md)

Draft: `5 - RootRecord-Library/Documentation/06-development/Work-Orders/drafts/Discord_poller_Work_Order_WO-MIG-21-2026-09-29.md`

---

## Layout

| Role | Path |
| --- | --- |
| Code | `Communications/Discord/scripts/poll.py` |
| Allowlist | `Communications/Discord/lib/envload.py` (`DISCORD_BOT_TOKEN` only) |
| Channels | `Communications/Discord/config/channels.json` |
| Database | `2 - RootRecord-Database/Communications/Discord/` |
| Logs | `2 - RootRecord-Database/Logs/Communications/Discord/` |

No `Logs/` directory on the server.

---

*WO-MIG-21 2026-09-30 HST. No secrets in this file.*
