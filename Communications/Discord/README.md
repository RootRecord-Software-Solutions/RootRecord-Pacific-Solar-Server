# Discord

Discord poller under Pacific Communications. Package name `Discord`. One folder. No lowercase twin.

**Status:** chat poller is not LIVE. Job `discord_poller` is `enabled: False`. `RR_DISCORD_POLLER`, `RR_DISCORD_REVIEW_PIPELINE`, and `RR_GLOBAL_UPDATER` stay unset. Job `discord_report_relay` posts the measured report (title, measured lines, and `https://www.rootrecord.cloud/reports/<slug>`) when that file changes. Spoken transcripts and persona names stay off the post. Before it posts, `scripts/report_relay.py` runs `Website/scripts/publish_report_pages.py`. `discord_report_8h` and `discord_report_24h` use the same measured text. `discord_report_8h` posts at 00:00, 08:00, and 16:00 HST. `discord_report_24h` posts at 12:00 HST. Each job sets `RR_DISCORD_POST=1` only for itself.

---

## Migration / enablement gate (required)

Before any Discord bot is brought online on Pacific:

1. Issue a new bot token from the Discord Developer Portal for the target application (Reset Token / generate).
2. Store it as `DISCORD_BOT_TOKEN` in `/home/rootrecord/master/master-key.env` only. Never commit the value.
3. Do not copy tokens from archive, mirror, or inventory history. Do not fall through `AVA_DISCORD_BOT_TOKEN`, `SEXI_DISCORD_BOT_TOKEN`, or `DISCORD_ROOTMC_BOT_TOKEN`.
4. `config/channels.json` lists only `#help-desk` (`1555097963049521192`). The poller does not fetch other channels.
5. Chat replies stay off unless `RR_DISCORD_POST=1` is set for that process. The report relay job sets the gate for itself. Mark the chat poller LIVE only after a smoke test Alexander signs off.

Canonical process: [WO-COM-002 — Discord Bot Credential Rotation](https://github.com/RootRecord-Software-Solutions/RootRecord-Library/blob/main/Documentation/06-Development/Work-Orders/WO-COM-002-Discord-Bot-Credential-Rotation.md)

Draft: `5 - RootRecord-Library/Documentation/06-Development/Work-Orders/drafts/Discord_poller_Work_Order_WO-MIG-21-2026-09-29.md`

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
| Global Updater | `Communications/Discord/scripts/global_updater.py` (gate `RR_GLOBAL_UPDATER`) |
| Guild allowlist | `Communications/Discord/config/guilds.json` (`1497039564345442406`, RootRecord Software Solutions) |
| Channel map | `Communications/Discord/config/channel-map.json` (full layout, including Reports) |
| Report routes | `Communications/Discord/config/report-channels.json` (one channel id per automated report) |
| Report relay | `Communications/Discord/scripts/report_relay.py` (job `discord_report_relay`) |
| Application label | `Communications/Discord/config/global-updater.json` (name and application id; not a token, not a bot user id) |
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
python3 Communications/Discord/tests/test_global_updater.py
```

---

## Root Record Global Updater

This Discord application is **Root Record Global Updater** (application id `1500289560343740566`). The professional guild allowlist is `1497039564345442406`. It is the professional RootRecord help desk: factual data, measured observations, operational information, and documentation answers.

It is not Ava Ivy. Ava Ivy remains the Minecraft / RootMC personality. This folder does not use `AVA_DISCORD_BOT_TOKEN`. The professional token name stays `DISCORD_BOT_TOKEN`.

Canonical identity:

```text
5 - RootRecord-Library/Agent Context/Global-Updater-Agent-Context/
```

`scripts/global_updater.py` loads that pack through `CouncilPersona/scripts/personas.py` and passes it as `RR_PERSONA_SYSTEM`. The turn wrapper in `lib/updater.py` is not a second persona. When a model reply claims to be Ava, Bruce, or Carly, the public text is replaced with the Public introduction section of `IDENTITY.md`.

The gate is `RR_GLOBAL_UPDATER=1`. Unset means the poller does not run this path. A message is answered only when all of these are true:

- the gate is on
- the channel id is in `config/channels.json`
- the guild id is in `config/guilds.json`
- the message names Root Record Global Updater, or a mention username matches that name
- the author is not a bot

The professional guild is `1497039564345442406`. Direct messages have no guild id, so they are ignored. The bot user id is `1500289560343740566`. A mention of that id, or of the name Root Record Global Updater, is the trigger, and only in `#help-desk`. `config/channel-map.json` is the full professional layout. `RR_GLOBAL_UPDATER` stays unset, so the poller does not reply in chat. Report posts use `config/report-channels.json` and do not use this mention path.

The reply is one `run-infer.sh` call for the voice `global-updater`, on the existing NPU single-flight path (`RR_NPU_ONLY=1`, `llama3.2:3b`). It does not call Ava, Bruce, or Carly. Host figures come from the recorded file `2 - RootRecord-Database/System/last/host-last.json`. Discord does not sample the host. A missing or old sample is unavailable. A sample older than 15 minutes and no older than 6 hours is reported as stale. A host sample is not a service-status claim.

A chat reply still requires `RR_DISCORD_POST=1` on the poller. Do not set `RR_GLOBAL_UPDATER`, and do not enable `discord_poller`, until a manual chat test is signed off.

```text
Ava Ivy
→ Minecraft / RootMC
→ personality-driven gamer/community agent

Global Updater
→ professional RootRecord Discord
→ factual operational/data/help-desk agent
```

The Ava review pipeline above is unchanged and stays off. A Global Updater reply is not fed through that pipeline.

---

*WO-MIG-21 2026-09-30 HST. Review pipeline 2026-09-30 HST. Global Updater persona 2026-09-30 HST. No secrets in this file.*
