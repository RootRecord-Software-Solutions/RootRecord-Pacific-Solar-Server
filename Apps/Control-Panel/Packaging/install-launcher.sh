# ==============================================================================
# FILE: Apps/Control-Panel/Packaging/install-launcher.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# install-launcher.sh — copy the Root Monitor + "Poller Dashboard (terminal)" launchers into ~/.local/share/applications (added 2026-09-29).
# User-level only (no sudo). Does NOT install/enable the systemd unit and does NOT start conky.
# Installs the conky config to ~/.config/conky/ only if conky is already installed.
set -euo pipefail  # info: set
HERE="$(cd "$(dirname "$0")" && pwd)"  # info: set HERE
APPS="$HOME/.local/share/applications"  # info: set APPS
mkdir -p "$APPS"  # info: mkdir
install -m 0644 "$HERE/rootrecord-control-panel.desktop" "$APPS/rootrecord-control-panel.desktop"  # info: install
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true  # info: command
echo "[ok] launcher -> $APPS/rootrecord-control-panel.desktop (Name=Root Monitor)"  # info: echo
install -m 0644 "$HERE/poller-dashboard-terminal.desktop" "$APPS/rootrecord-poller-dashboard-terminal.desktop"  # info: install
echo "[ok] launcher -> $APPS/rootrecord-poller-dashboard-terminal.desktop (Name=Poller Dashboard (terminal))"  # info: echo
if command -v conky >/dev/null 2>&1; then  # info: if
  mkdir -p "$HOME/.config/conky"  # info: mkdir
  install -m 0644 "$HERE/../Conky/rootrecord.conkyrc" "$HOME/.config/conky/rootrecord.conkyrc"  # info: install
  echo "[ok] conky config -> ~/.config/conky/rootrecord.conkyrc (not started)"  # info: echo
else  # info: else
  echo "[skip] conky not installed — config left in repo (sign-off: sudo apt install conky-all)"  # info: echo
fi  # info: fi
echo "[info] systemd --user unit NOT installed/enabled (sign-off item)"  # info: echo
echo "[info] default-viewer swap NOT applied (sign-off item: Packaging/swap-default-viewer.sh apply)"  # info: echo
