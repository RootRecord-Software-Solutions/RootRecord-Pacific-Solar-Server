#!/usr/bin/env bash
# ==============================================================================
# open-poller-window.sh — open colored live poller status window
# ------------------------------------------------------------------------------
# Opens ONE read-only poller-dashboard.py window (2026-09-29 WO-SRV viewer fix).
# Closing it / Ctrl-C exits the viewer only; the poller keeps running.
# If a dashboard is already open this script does nothing (no duplicate/flashing windows).
# POLLER_VIEWER=poller-watch.py selects Bruce's scrolling log view instead.
# Used by: operator manual open, do-stack-reload after start.
#
# Position: POLLER_WINDOW_GEOMETRY (default 100x36+480+160) keeps the window
# near the center desktop spot operators use. Override if your layout differs:
#   POLLER_WINDOW_GEOMETRY=100x36+200+100 bash open-poller-window.sh
# ==============================================================================
set -euo pipefail

# ====================================================
# SECTION: PATHS
# ====================================================
HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPTS="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$SCRIPTS/../.." && pwd)"
WATCH="$HERE/${POLLER_VIEWER:-poller-dashboard.py}"
UNIT="rr-rootserver-poller.service"
TITLE="RootRecord poller — rootserver"
# Cols x Rows + X + Y  (pixels for +X+Y under X11; Wayland may approximate)
GEOMETRY="${POLLER_WINDOW_GEOMETRY:-100x36+480+160}"
export POLLER_LOG="${POLLER_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log}"
mkdir -p "$(dirname "$POLLER_LOG")"
touch "$POLLER_LOG"

# ====================================================
# SECTION: START POLLER STACK
# ====================================================
echo "[open] starting ${UNIT}…"
systemctl --user start "${UNIT}"

# Avoid stacking duplicate viewers: keep the one that is already open.
if pgrep -f "$(basename "$WATCH" | sed 's/\./\\./g')" >/dev/null 2>&1; then
  echo "[open] viewer already open ($(basename "$WATCH")) — leaving it"
  exit 0
fi
# ====================================================
# SECTION: OPEN TERMINAL (detached; do not exec)
# ====================================================
# gnome-terminal often hands off to an existing server and exits the client.
# Launch detached so reload scripts are not tied to that client lifetime.
if command -v gnome-terminal >/dev/null 2>&1; then
  echo "[open] gnome-terminal geometry=${GEOMETRY}"
  nohup gnome-terminal --disable-factory --title="$TITLE" --geometry="$GEOMETRY" -- \
    bash -lc "/usr/bin/python3 '$WATCH'; rc=\$?; echo; echo \"poller-watch exited (code=\$rc) — terminal left open for inspection.\"; exec bash -i" >/dev/null 2>&1 &
  sleep 0.5
  exit 0
fi

# Ptyxis (Ubuntu default; gnome-terminal is not installed on the desk). The client
# hands the window to the running ptyxis service and exits, so the window does
# not depend on the launcher's (e.g. do-stack-reload's transient unit) lifetime.
if command -v ptyxis >/dev/null 2>&1; then
  echo "[open] ptyxis new window"
  nohup ptyxis --new-window -T "$TITLE" -x "/usr/bin/python3 '$WATCH'" >/dev/null 2>&1 &
  sleep 0.5
  exit 0
fi

if command -v x-terminal-emulator >/dev/null 2>&1; then
  nohup x-terminal-emulator -T "$TITLE" -e /usr/bin/python3 "$WATCH" >/dev/null 2>&1 &
  exit 0
fi

echo "[open] no terminal emulator found" >&2
exit 1
