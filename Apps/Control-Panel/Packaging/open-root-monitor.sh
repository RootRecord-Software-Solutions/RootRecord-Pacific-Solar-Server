#!/usr/bin/env bash
# Open Root Monitor (GTK). Does not start the poller, the relay, or the cameras.
# If a window is already open this script does nothing.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PANEL="$(cd "$HERE/.." && pwd)/rr_control_panel.py"
if pgrep -f "python3 .*rr_control_panel\\.py" >/dev/null 2>&1; then
  echo "[open] Root Monitor already open — leaving it"
  exit 0
fi
if [[ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
  echo "[open] no graphical session — Root Monitor not started" >&2
  exit 1
fi
echo "[open] Root Monitor"
nohup /usr/bin/python3 "$PANEL" >/dev/null 2>&1 &
exit 0
