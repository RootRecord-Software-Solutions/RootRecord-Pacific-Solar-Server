# ==============================================================================
# FILE: Apps/Control-Panel/Packaging/swap-default-viewer.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# swap-default-viewer.sh — make Root Monitor the default viewer at login, reversibly (added 2026-09-29).
# SIGN-OFF ITEM: nothing runs this automatically; Alexander runs it himself.
#
#   swap-default-viewer.sh status   show which viewer autostarts (read-only)
#   swap-default-viewer.sh apply    Root Monitor autostarts instead of the terminal poller dashboard
#   swap-default-viewer.sh revert   put everything back exactly as it was (byte-identical restore, sha256-checked)
#
# What apply does (user-level only, no sudo, nothing restarted):
#   1. moves ~/.config/autostart/rootrecord-poller-watch.desktop (unchanged bytes) into
#      ~/.config/autostart/.root-monitor-swap/ and records its sha256
#   2. installs Packaging/root-monitor-autostart.desktop as ~/.config/autostart/root-monitor.desktop
# It does NOT edit open-poller-window.sh, poller-dashboard.py, the Desktop launcher or the poller unit.
# The poller keeps starting at login on its own (rr-rootserver-poller.service is enabled via default.target;
# the old autostart's `systemctl --user start` was a no-op for it).
# Note: do-stack-reload.sh still opens the terminal dashboard after a stack reload (OPEN_POLLER_WINDOW=1 default);
# that is unchanged by design. The terminal dashboard stays installed: app menu "Poller Dashboard (terminal)".
set -euo pipefail  # info: set
HERE="$(cd "$(dirname "$0")" && pwd)"  # info: set HERE
AS="$HOME/.config/autostart"  # info: set AS
OLD="$AS/rootrecord-poller-watch.desktop"  # info: set OLD
NEW="$AS/root-monitor.desktop"  # info: set NEW
KEEP="$AS/.root-monitor-swap"  # info: set KEEP
cmd="${1:-status}"  # info: set cmd
case "$cmd" in  # info: case
  status)  # info: status
    [ -f "$OLD" ] && echo "terminal poller dashboard autostart: PRESENT ($OLD)" || echo "terminal poller dashboard autostart: not present"  # info: command
    [ -f "$NEW" ] && echo "Root Monitor autostart: PRESENT ($NEW)" || echo "Root Monitor autostart: not present"  # info: command
    [ -f "$KEEP/rootrecord-poller-watch.desktop" ] && echo "saved original: $KEEP/rootrecord-poller-watch.desktop (sha256 $(cut -d' ' -f1 "$KEEP/sha256"))" || true  # info: command
    ;;  # info: command
  apply)  # info: apply
    [ -f "$NEW" ] && [ ! -f "$OLD" ] && { echo "already applied"; exit 0; }  # info: command
    [ -f "$OLD" ] || { echo "refusing: $OLD not found (nothing to swap)"; exit 1; }  # info: command
    [ -e "$KEEP/rootrecord-poller-watch.desktop" ] && { echo "refusing: a saved original already exists in $KEEP — run revert first"; exit 1; }  # info: command
    mkdir -p "$KEEP"  # info: mkdir
    sha256sum "$OLD" > "$KEEP/sha256"  # info: sha256sum
    mv "$OLD" "$KEEP/rootrecord-poller-watch.desktop"  # info: mv
    install -m 0644 "$HERE/root-monitor-autostart.desktop" "$NEW"  # info: install
    echo "[ok] applied: Root Monitor autostarts at next login; terminal dashboard autostart saved in $KEEP"  # info: echo
    echo "     revert any time: $0 revert"  # info: echo
    ;;  # info: command
  revert)  # info: revert
    [ -f "$KEEP/rootrecord-poller-watch.desktop" ] || { echo "nothing to revert (no saved original)"; exit 0; }  # info: command
    want="$(cut -d' ' -f1 "$KEEP/sha256")"  # info: set want
    have="$(sha256sum "$KEEP/rootrecord-poller-watch.desktop" | cut -d' ' -f1)"  # info: set have
    [ "$want" = "$have" ] || { echo "refusing: saved original changed (sha mismatch) — restore by hand from $KEEP"; exit 1; }  # info: command
    [ -e "$OLD" ] && { echo "refusing: $OLD exists again — compare by hand"; exit 1; }  # info: command
    mv "$KEEP/rootrecord-poller-watch.desktop" "$OLD"  # info: mv
    rm -f "$NEW" "$KEEP/sha256"  # info: rm
    rmdir "$KEEP" 2>/dev/null || true  # info: rmdir
    echo "[ok] reverted: terminal poller dashboard autostarts again (byte-identical, sha256 $want)"  # info: echo
    ;;  # info: command
  *) echo "usage: $0 status|apply|revert"; exit 2 ;;  # info: command
esac  # info: esac
