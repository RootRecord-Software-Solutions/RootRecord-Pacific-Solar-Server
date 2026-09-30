#!/usr/bin/env bash
# ==============================================================================
# run-poller.sh — exec rootserver_poller.py with default env
# ------------------------------------------------------------------------------
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -euo pipefail

# ====================================================
# SECTION: PATHS + DEFAULTS
# ====================================================
# This file lives at Automations/scripts/poller/
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$SCRIPTS/../.." && pwd)"

export POLLER_BIND="${POLLER_BIND:-127.0.0.1}"
export POLLER_PORT="${POLLER_PORT:-8799}"
export POLLER_INTERVAL_SEC="${POLLER_INTERVAL_SEC:-5}"
export POLLER_PUBLIC_HOST="${POLLER_PUBLIC_HOST:-rootserver.rootrecord.cloud}"
export POLLER_ENABLE_TUNNEL="${POLLER_ENABLE_TUNNEL:-1}"
export POLLER_LOG="${POLLER_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log}"
export POLLER_TUNNEL_MODE="${POLLER_TUNNEL_MODE:-token}"
export CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-$REPO/Communications/network/cloudflare/bin/cloudflared}"
export CLOUDFLARED_TOKEN_FILE="${CLOUDFLARED_TOKEN_FILE:-$HOME/.cloudflared/rootserver.token}"
# Armed 2026-09-30 after sign-off (WO-MIG-01). No night-mode.json still means not sleeping.
export RR_NIGHT_SLEEP="${RR_NIGHT_SLEEP:-1}"

# ====================================================
# SECTION: EXEC
# ====================================================
exec /usr/bin/python3 "$SCRIPTS/rootserver_poller.py"
