#!/usr/bin/env bash
# install-launcher.sh — copy the Root Monitor + "Poller Dashboard (terminal)" launchers into ~/.local/share/applications (added 2026-09-29).
# User-level only (no sudo). Does NOT install/enable the systemd unit and does NOT start conky.
# Installs the conky config to ~/.config/conky/ only if conky is already installed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APPS="$HOME/.local/share/applications"
mkdir -p "$APPS"
install -m 0644 "$HERE/rootrecord-control-panel.desktop" "$APPS/rootrecord-control-panel.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true
echo "[ok] launcher -> $APPS/rootrecord-control-panel.desktop (Name=Root Monitor)"
install -m 0644 "$HERE/poller-dashboard-terminal.desktop" "$APPS/rootrecord-poller-dashboard-terminal.desktop"
echo "[ok] launcher -> $APPS/rootrecord-poller-dashboard-terminal.desktop (Name=Poller Dashboard (terminal))"
if command -v conky >/dev/null 2>&1; then
  mkdir -p "$HOME/.config/conky"
  install -m 0644 "$HERE/../Conky/rootrecord.conkyrc" "$HOME/.config/conky/rootrecord.conkyrc"
  echo "[ok] conky config -> ~/.config/conky/rootrecord.conkyrc (not started)"
else
  echo "[skip] conky not installed — config left in repo (sign-off: sudo apt install conky-all)"
fi
echo "[info] systemd --user unit NOT installed/enabled (sign-off item)"
echo "[info] default-viewer swap NOT applied (sign-off item: Packaging/swap-default-viewer.sh apply)"
