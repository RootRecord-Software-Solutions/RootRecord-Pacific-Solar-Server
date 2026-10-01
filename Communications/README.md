# Communications

How the Pacific server reaches something outside itself, or exposes a communication-facing interface.

Messaging, the live Cloudflare tunnel, the Hawaii network-globe collector, and chat-facing adapters live here. Domain processing, agent identity, local models, and the public website do not.

---

## Owns

| Path | Role | State |
| --- | --- | --- |
| `network/cloudflare/` | Live `cloudflared` for `rootserver.rootrecord.cloud` → `127.0.0.1:8799`. Binary is untracked. Token file `~/.cloudflared/rootserver.token`. | **Live.** Job `cloudflare_tunnel`. |
| `network/local-data-globe/` | Hawaii SSH collector. Live records go to AWS, or to Telegram when SSH is down. Not a chart library. | **Live.** Job `network_globe_hawaii`. |
| `telegram/` | One `getUpdates` owner (`council-relay.py` via `ensure-relay.sh`). Contract: `telegram/CONTRACT.md`. | **Live.** Sandbox replies on. Live council and private DMs stay off (`RR_RELAY_REPLIES` default 0). Inference is NPU `llama3.2:3b` on demand, in `System/scripts/plumbing/`, not here. |
| `Discord/` | Poller. Token `DISCORD_BOT_TOKEN` only, local. | **Off.** Job `discord_poller` enabled false. No post. |
| `Slack/` | Poller. Token `SLACK_BOT_TOKEN` only, local. | **Off** unless `RR_SLACK=1`. No post. |
| `email/` | Empty shell. | **Unused.** |
| `github/` | Empty shells for API, messaging, notifications, webhooks. | **Unused.** Git catalog sync is `Github/`, not here. |
| `Inbox/` | Reads the quiet-mode relay hold. Does not poll Telegram. | **Off.** Jobs `inbox_drain`, `overnight_relay`. |
| `CouncilHealth/` | Relay process, Telegram `getMe`, and 409 tail. Report only. | **Off** unless `RR_COUNCIL_HEALTH=1`. Default command is `--no-alert --no-probe`. |
| `CouncilQuake/` | Telegram text from existing Geology last files. Does not fetch USGS. | **Off** unless `RR_COUNCIL_QUAKE=1`. Send stays off. |
| `BruceStats/` | Telegram text from existing host and EcoFlow last files. Does not sample the host. | **Off** unless `RR_BRUCE_STATS=1`. Send stays off. |
| `PublicHealth/` | HTTP probes of the public radio origin and `127.0.0.1:8787`, plus an optional Telegram line. Does not start port 8787. | **Off** unless `RR_PUBLIC_HEALTH=1`. Send stays off. |
| `live-wx/` | Chat lines from NWS and the weather poller's hurricane files. | **On demand.** No job. Not wired to the relay. |
| `web-facts/` | Allowlisted HTTPS GET for chat. | **On demand.** No job. Not wired to the relay. |
| `CouncilPersona/` | Chat system text for voices `ava`, `bruce`, `carly`. Loaded by the relay as `RR_PERSONA_SYSTEM`. | **Loader.** Does not poll or send. |

## Does not own

| Concern | Where it lives |
| --- | --- |
| Agent identity | Library `Agent Context/{Ava,Bruce,Carly}-Agent-Context/` |
| Telegram chat prompts | `CouncilPersona/prompts/` (rendering of those packs, not a second identity) |
| Telegram Modelfiles | Database `AI/Ollama/Modelfiles/Production/` |
| Local inference | `System/scripts/plumbing/` (`run-infer.sh`) |
| Earthquake and volcano collection | `Geology/` |
| Weather collection and reports | `Weather/` |
| Public Vercel app, route manifest, undeployed site worker | `Website/`, `Website/Site/`, `Website/Cloudflare-Workers/` |
| Meta AI chat client | Still `Communications/MetaAI/` until an owner is chosen. No job. Do not send. |

`network/cloudflare/` is the live tunnel binary and config. `Website/Cloudflare-Workers/` is a separate, undeployed worker in front of the Vercel origin. They are not the same system.

## Contracts

- Relay: `telegram/CONTRACT.md`
- Relay settings: `telegram/config/relay.conf`, `telegram/config/voices.conf`
- Discord channels: `Discord/config/channels.json` (empty)

Identity packs are not a Communications contract. `CouncilPersona/` is only the chat rendering the relay loads.

---

*Boundary set 2026-09-30. No jobs were enabled or disabled.*
