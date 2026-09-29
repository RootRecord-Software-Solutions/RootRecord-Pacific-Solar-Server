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
# Config: config/{voices,relay,bots}.conf
# DESK_LIVE_FILE → Database/intake/desk-live.txt (measured or No data)
# Bak: /home/rootrecord/Database/GITHUB/
# Style bar: automations/scripts/jobs.py
# Walls: billing → Carly · AWS → US-MAINLAND · public wording → Ava
# ==============================================================================

# telegram

| | |
|--|--|
| Config | `config/voices.conf` · `config/relay.conf` |
| Ask | `scripts/ask-voice.sh <voice> '…'` |
| Post | `scripts/post-voice.sh <voice> '…'` |
| Poll | `scripts/council-relay.py` (**one** process) |
| Status | `scripts/status.sh` |
| Infer | `plumbing/scripts/run-infer.sh` (via relay) |

Set `COUNCIL_CHAT_ID` before live poll. Stop legacy `apps.council` first.
`DESK_LIVE_FILE` must point at the measured desk file (or leave empty = No data).

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
