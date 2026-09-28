#!/usr/bin/env bash
# ==============================================================================
# open-poller-window.sh — open colored live poller status window
# ------------------------------------------------------------------------------
# Ctrl-C or close window must stop the whole stack (handled in poller-watch.py).
# Used by: rootserver-poller window, do-stack-reload after start.
# Layout style (standing): keep SECTION banners.
# ==============================================================================
set -euo pipefail

# ====================================================
# SECTION: PATHS
# ====================================================
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WATCH="$ROOT/scripts/poller-watch.py"
UNIT="rr-rootserver-poller.service"
TITLE="RootRecord poller — rootserver"
export POLLER_LOG="${POLLER_LOG:-$HOME/.ollama/skills/logs/store/rootserver-poller.log}"
mkdir -p "$(dirname "$POLLER_LOG")"
touch "$POLLER_LOG"

# ====================================================
# SECTION: START POLLER STACK
# ====================================================
echo "[open] starting ${UNIT:-rr-rootserver-poller.service}…"
systemctl --user start "${UNIT:-rr-rootserver-poller.service}"

# ====================================================
# SECTION: OPEN TERMINAL
# ====================================================
if command -v gnome-terminal >/dev/null 2>&1; then
  exec gnome-terminal --title="$TITLE" --geometry=100x36 -- \
    bash -lc "exec /usr/bin/python3 '$WATCH'"
fi
exec x-terminal-emulator -T "$TITLE" -e /usr/bin/python3 "$WATCH"
