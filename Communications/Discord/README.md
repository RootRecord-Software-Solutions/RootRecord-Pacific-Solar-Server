# Discord

Discord poller under Pacific Communications. Package name `Discord`. One folder. No lowercase twin.

**Status:** poller landed, not LIVE. Job `discord_poller` is `enabled: False`. `RR_DISCORD_POLLER`, `RR_DISCORD_POST`, and `RR_DISCORD_REVIEW_PIPELINE` stay unset. No token means no Discord HTTP.

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
| REST send | `Communications/Discord/lib/api.py` (`post_message`, gate `RR_DISCORD_POST`) |
| Review pipeline | `Communications/Discord/scripts/review.py` (gate `RR_DISCORD_REVIEW_PIPELINE`) |
| Allowlist | `Communications/Discord/lib/envload.py` (`DISCORD_BOT_TOKEN` only) |
| Channels | `Communications/Discord/config/channels.json` |
| Persona loader | `Communications/CouncilPersona/scripts/personas.py` reads Library `Agent Context/` |
| Inference | `System/scripts/plumbing/run-infer.sh` |
| Database | `2 - RootRecord-Database/Communications/Discord/` |
| Logs | `2 - RootRecord-Database/Logs/Communications/Discord/` |

No `Logs/` directory on the server.

---

## Ava-led review pipeline

Discord uses Ava as the public-facing agent. Bruce and Carly review inside the process. Ava writes the final public response. The Discord user sees that one reply.

```text
Discord user
    → Ava draft
    → Bruce review
    → Carly review
    → Ava final
    → Discord user
```

Telegram stays the council. This pipeline does not read or change `PIPELINE_ORDER`, `PIPELINE_TRIGGERS`, or `DEFAULT_SINGLE_VOICE`.

The gate is `RR_DISCORD_REVIEW_PIPELINE=1`. Unset means the poller only fetches, as before. A message runs the pipeline when the gate is on and the message names Ava (the word Ava, or a mention whose username is Ava). Other channel traffic is left alone. The poller has no separate auto-reply rule.

Bruce and Carly return `APPROVE` or `CHANGES`. Their notes are not posted. There is no debug mode that posts the chain.

Posting the final text still requires `RR_DISCORD_POST=1`. With only the review gate on, the pipeline can run and `post_message` still returns without HTTP.

Identity comes from Library `Agent Context/{Ava,Bruce,Carly}-Agent-Context/` through `CouncilPersona/scripts/personas.py`, passed as `RR_PERSONA_SYSTEM`. This folder does not keep a persona copy.

Inference is `run-infer.sh` with `RR_NPU_ONLY=1`, `RR_NPU_PERSONA=1`, and `FLM_MODEL=llama3.2:3b`. That is the same single-flight path the council uses. Reviewer prompts ask for a short review, not a second full answer.

If Bruce or Carly cannot review, that hop is logged `unavailable` and is not treated as `APPROVE`. Ava still finishes from the draft. If Ava cannot draft, nothing is posted. If Ava's final pass fails, the draft is the public text. Internal failure text is not sent to the channel.

Stage lines go to the existing Discord `poll.log`: request received, Ava draft, Bruce review, Carly review, Ava final, Discord send. The lines do not include the user message, the draft, or the reviews.

Handled message ids are stored in `Communications/Discord/review-seen.json` under the database root. The file stores ids only. A failed draft is not marked seen, so a later poll can retry. A finished reply is marked seen even when the post gate skips HTTP, so the same message is not inferred again.

The scheduled job stays `enabled: False`. Its timeout is 900 seconds so four sequential turns fit if the job is enabled later. Do not enable it, and do not set the two Discord gates, until a manual test is signed off. A manual test is one `python3 poll.py` with both gates set in that process only. Do not restart Telegram.

Offline check:

```text
python3 Communications/Discord/tests/test_review.py
```

---

*WO-MIG-21 2026-09-30 HST. Review pipeline 2026-09-30 HST. No secrets in this file.*
