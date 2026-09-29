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
# This file lives at Automations/scripts/poller/
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$SCRIPTS/../.." && pwd)"
WATCH="$HERE/poller-watch.py"
UNIT="rr-rootserver-poller.service"
TITLE="RootRecord poller — rootserver"
# Canonical: RootRecord-Database repo → desk /home/rootrecord/Database/
# Override with POLLER_LOG.
export POLLER_LOG="${POLLER_LOG:-/home/rootrecord/Database/Logs/Automations/automations_current.log}"
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
