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

# ====================================================
# SECTION: EXEC
# ====================================================
exec /usr/bin/python3 "$SCRIPTS/rootserver_poller.py"  # info: exec
