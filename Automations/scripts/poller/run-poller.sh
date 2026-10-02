#!/usr/bin/env bash
# ==============================================================================
# run-poller.sh — exec rootserver_poller.py with default env
# ------------------------------------------------------------------------------
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -euo pipefail  # info: set

# ====================================================
# SECTION: PATHS + DEFAULTS
# ====================================================
# This file lives at Automations/scripts/poller/
HERE="$(cd "$(dirname "$0")" && pwd)"  # info: set HERE
SCRIPTS="$(cd "$HERE/.." && pwd)"  # info: set SCRIPTS
REPO="$(cd "$SCRIPTS/../.." && pwd)"  # info: set REPO

export POLLER_BIND="${POLLER_BIND:-127.0.0.1}"  # info: export
export POLLER_PORT="${POLLER_PORT:-8799}"  # info: export
export POLLER_INTERVAL_SEC="${POLLER_INTERVAL_SEC:-5}"  # info: export
export POLLER_PUBLIC_HOST="${POLLER_PUBLIC_HOST:-rootserver.rootrecord.cloud}"  # info: export
export POLLER_ENABLE_TUNNEL="${POLLER_ENABLE_TUNNEL:-1}"  # info: export
export POLLER_LOG="${POLLER_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log}"  # info: export
export POLLER_TUNNEL_MODE="${POLLER_TUNNEL_MODE:-token}"  # info: export
export CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-$REPO/Communications/network/cloudflare/bin/cloudflared}"  # info: export
export CLOUDFLARED_TOKEN_FILE="${CLOUDFLARED_TOKEN_FILE:-$HOME/.cloudflared/rootserver.token}"  # info: export
# Armed 2026-09-30 after sign-off (WO-MIG-01). No night-mode.json still means not sleeping.
export RR_NIGHT_SLEEP="${RR_NIGHT_SLEEP:-1}"  # info: export
# Voice notes Alexander asked for on 2026-09-30. Original council chat as of 2026-09-30 evening. Takes effect at the next poller start.
export RR_VOICE_DELIVER="${RR_VOICE_DELIVER:-1}"  # info: export
export RR_TELEGRAM_DEST="${RR_TELEGRAM_DEST:-council}"  # info: export
export RR_VOICE_NWS="${RR_VOICE_NWS:-1}"  # info: export
export RR_VOICE_KILAUEA="${RR_VOICE_KILAUEA:-1}"  # info: export
export RR_VOICE_KILAUEA_IMAGE="${RR_VOICE_KILAUEA_IMAGE:-1}"  # info: export — overnight soak image check
export RR_VOICE_SECURITY="${RR_VOICE_SECURITY:-1}"  # info: export
export RR_VOICE_BANDWIDTH="${RR_VOICE_BANDWIDTH:-1}"  # info: export
export RR_VOICE_SYSTEM_PERF="${RR_VOICE_SYSTEM_PERF:-1}"  # info: export
export RR_VOICE_REMAINING="${RR_VOICE_REMAINING:-1}"  # info: export
export RR_VOICE_QUAKE="${RR_VOICE_QUAKE:-1}"  # info: export
export RR_VOICE_SOLAR="${RR_VOICE_SOLAR:-1}"  # info: export
export RR_VOICE_ROLLUPS="${RR_VOICE_ROLLUPS:-1}"  # info: export
export RR_VOICE_LATE_FINAL="${RR_VOICE_LATE_FINAL:-1}"  # info: export
export RR_VOICE_HURRICANE="${RR_VOICE_HURRICANE:-1}"  # info: export
export RR_VOICE_CURRENT="${RR_VOICE_CURRENT:-1}"  # info: export
export RR_RADIO_RSS="${RR_RADIO_RSS:-1}"  # info: export
export RR_RADIO_NEWS="${RR_RADIO_NEWS:-1}"  # info: export
export RR_GEOLOGY="${RR_GEOLOGY:-1}"  # info: export
export RR_MOON="${RR_MOON:-1}"  # info: export
export RR_SUN_TIMES="${RR_SUN_TIMES:-1}"  # info: export
export RR_NET_SAMPLES="${RR_NET_SAMPLES:-1}"  # info: export
export RR_UPTIME_LOG="${RR_UPTIME_LOG:-1}"  # info: export

# ====================================================
# SECTION: EXEC
# ====================================================
exec /usr/bin/python3 "$SCRIPTS/rootserver_poller.py"  # info: exec
