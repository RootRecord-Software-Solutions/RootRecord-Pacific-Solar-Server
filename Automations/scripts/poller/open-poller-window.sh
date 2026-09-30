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
set -euo pipefail  # info: set

# ====================================================
# SECTION: PATHS
# ====================================================
HERE="$(cd "$(dirname "$0")" && pwd)"  # info: set HERE
SCRIPTS="$(cd "$HERE/.." && pwd)"  # info: set SCRIPTS
REPO="$(cd "$SCRIPTS/../.." && pwd)"  # info: set REPO
WATCH="$HERE/${POLLER_VIEWER:-poller-dashboard.py}"  # info: set WATCH
UNIT="rr-rootserver-poller.service"  # info: set UNIT
TITLE="RootRecord poller — rootserver"  # info: set TITLE
# Cols x Rows + X + Y  (pixels for +X+Y under X11; Wayland may approximate)
GEOMETRY="${POLLER_WINDOW_GEOMETRY:-100x36+480+160}"  # info: set GEOMETRY
export POLLER_LOG="${POLLER_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/automations_current.log}"  # info: export
mkdir -p "$(dirname "$POLLER_LOG")"  # info: mkdir
touch "$POLLER_LOG"  # info: touch

# ====================================================
# SECTION: START POLLER STACK
# ====================================================
echo "[open] starting ${UNIT}…"  # info: echo
systemctl --user start "${UNIT}"  # info: systemctl

# Avoid stacking duplicate viewers: keep the one that is already open.
if pgrep -f "^[^ ]*python3 .*$(basename "$WATCH" | sed 's/\./\\./g')" >/dev/null 2>&1; then  # info: if
  echo "[open] viewer already open ($(basename "$WATCH")) — leaving it"  # info: echo
  exit 0  # info: exit
fi  # info: fi
# ====================================================
# SECTION: OPEN TERMINAL (detached; do not exec)
# ====================================================
# gnome-terminal often hands off to an existing server and exits the client.
# Launch detached so reload scripts are not tied to that client lifetime.
if command -v gnome-terminal >/dev/null 2>&1; then  # info: if
  echo "[open] gnome-terminal geometry=${GEOMETRY}"  # info: echo
  nohup gnome-terminal --disable-factory --title="$TITLE" --geometry="$GEOMETRY" -- \
    bash -lc "/usr/bin/python3 '$WATCH'; rc=\$?; echo; echo \"poller-watch exited (code=\$rc) — terminal left open for inspection.\"; exec bash -i" >/dev/null 2>&1 &  # info: bash
  sleep 0.5  # info: sleep
  exit 0  # info: exit
fi  # info: fi

# Ptyxis (Ubuntu default; gnome-terminal is not installed on the desk). The client
# hands the window to the running ptyxis service and exits, so the window does
# not depend on the launcher's (e.g. do-stack-reload's transient unit) lifetime.
if command -v ptyxis >/dev/null 2>&1; then  # info: if
  echo "[open] ptyxis new window"  # info: echo
  nohup ptyxis --new-window -T "$TITLE" -x "/usr/bin/python3 '$WATCH'" >/dev/null 2>&1 &  # info: nohup
  sleep 0.5  # info: sleep
  exit 0  # info: exit
fi  # info: fi

if command -v x-terminal-emulator >/dev/null 2>&1; then  # info: if
  nohup x-terminal-emulator -T "$TITLE" -e /usr/bin/python3 "$WATCH" >/dev/null 2>&1 &  # info: nohup
  exit 0  # info: exit
fi  # info: fi

echo "[open] no terminal emulator found" >&2  # info: echo
exit 1  # info: exit
