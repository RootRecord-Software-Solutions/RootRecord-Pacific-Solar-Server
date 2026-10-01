---
name: telegram
description: >-
  Telegram helpers + council relay to Ollama/FLM ava/bruce/carly. Single-flight
  plumbing. Exactly one getUpdates owner. Tokens in secrets — never print.
---

# ==============================================================================
# # INFO — MUST HAVE (operators / future agents)
# ------------------------------------------------------------------------------
# What: one council-relay (getUpdates) + per-voice post; mediate = Bruce
# Config: config/voices.conf, config/relay.conf
# Council default: llama3.2:3b on the NPU via ensure-relay.sh. RR_NPU_ONLY=1. Context 4096.
# Ava's Telegram lane: gemma3:4b (voices.conf flm_model). Bruce and Carly stay on the default.
# Inference binary: System/scripts/plumbing/run-infer.sh
# Persona packs are Library Agent Context, not this folder.
# ==============================================================================

# telegram

| | |
|--|--|
| Config | `config/voices.conf` · `config/relay.conf` |
| Poll | `scripts/council-relay.py` (**one** process), started by `scripts/ensure-relay.sh` |
| Desk lines | `scripts/desk-live.py` |
| Held messages | `scripts/relay-inbox-replay.py` (read-only unless `--send` and `RR_RELAY_REPLIES=1`) |
| Infer | `System/scripts/plumbing/run-infer.sh` (via relay) |

Set `COUNCIL_CHAT_ID` before live poll. Stop legacy `apps.council` first.
The original council chat is `COUNCIL_CHAT_ID`. `COUNCIL_REPLIES=1` answers that chat. The sandbox (`SANDBOX_CHAT_ID`, https://t.me/c/4406495175/2) answers only when `SANDBOX_REPLIES=1`. Reports and statuses use `RR_TELEGRAM_DEST=council` for the original chat.
`DESK_LIVE_FILE` is refreshed before each reply. A power question cites those lines. A scope question cites the state slice. Private DMs stay off until `RR_RELAY_REPLIES=1`.

# ------------------------------------------------------------------------------
# SECTION: HOW TO ADD A VOICE
# ------------------------------------------------------------------------------
# 1) Add a row in voices.conf (enabled, @user, token_env, model, fallback).
# 2) Ensure Modelfile lane exists (e.g. carly-telegram) — Carly seals persona diffs.
# 3) Token lives in secrets.env only — never paste into staging or git.
# 4) Restart / ensure-relay once — still **one** getUpdates (POLL_VOICE=ava).

# ------------------------------------------------------------------------------
# SECTION: ONE getUpdates OWNER
# ------------------------------------------------------------------------------
# Only council-relay.py long-polls (POLL_VOICE token). Other bots post only.
# Dual poller → Telegram 409. Soft-park any second relay before start.
