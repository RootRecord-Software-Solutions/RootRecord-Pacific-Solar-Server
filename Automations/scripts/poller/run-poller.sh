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
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export POLLER_BIND="${POLLER_BIND:-127.0.0.1}"
export POLLER_PORT="${POLLER_PORT:-8799}"
export POLLER_INTERVAL_SEC="${POLLER_INTERVAL_SEC:-5}"
export POLLER_PUBLIC_HOST="${POLLER_PUBLIC_HOST:-rootserver.rootrecord.cloud}"
export POLLER_ENABLE_TUNNEL="${POLLER_ENABLE_TUNNEL:-1}"
export POLLER_TUNNEL_MODE="${POLLER_TUNNEL_MODE:-token}"
export CLOUDFLARED_BIN="${CLOUDFLARED_BIN:-$ROOT/bin/cloudflared}"
export CLOUDFLARED_TOKEN_FILE="${CLOUDFLARED_TOKEN_FILE:-$HOME/.cloudflared/rootserver.token}"

# ====================================================
# SECTION: EXEC
# ====================================================
exec /usr/bin/python3 "$ROOT/scripts/rootserver_poller.py"
