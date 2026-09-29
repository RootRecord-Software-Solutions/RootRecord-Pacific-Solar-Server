# discord

Discord communication integration shell under Pacific Communications.

**Status:** shell only — not LIVE. Enablement is gated by Library work order **WO-COM-002**.

---

## Migration / enablement gate (required)

Before any Discord bot is brought online on Pacific:

1. **Issue a new bot token** from the Discord Developer Portal for the target application (Reset Token / generate).
2. **Store the token only on the host** — env file or secret path that is gitignored. Never commit tokens, transcript dumps, or agent logs that may contain them.
3. **Do not copy tokens from archive, mirror, or inventory history.** Those paths are non-authoritative for credentials.
4. Wire runtime config to the local secret; smoke-test login/ready offline from production traffic if possible.
5. Mark LIVE only after smoke test. Leaving the bot offline until the gate is complete is acceptable.

Canonical process: [WO-COM-002 — Discord Bot Credential Rotation](https://github.com/RootRecord-Software-Solutions/RootRecord-Library/blob/main/Documentation/06-development/Work-Orders/WO-COM-002-Discord-Bot-Credential-Rotation.md)

Related surface policy: [WO-COM-001 — Communications Surface](https://github.com/RootRecord-Software-Solutions/RootRecord-Library/blob/main/Documentation/06-development/Work-Orders/WO-COM-001-Communications-Surface.md)

---

## Layout (future)

```text
Communications/discord/
  README.md          ← this file
  (scripts / config — secrets stay off-repo)
```

---

*Docs-only 2026-09-28 HST. No secrets in this file.*
