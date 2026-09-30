# ==============================================================================
# FILE: Apps/Control-Panel/Packaging/open-root-monitor.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Open Root Monitor (GTK). Does not start the poller, the relay, or the cameras.
# If a window is already open this script does nothing.
set -euo pipefail  # info: set
HERE="$(cd "$(dirname "$0")" && pwd)"  # info: set HERE
PANEL="$(cd "$HERE/.." && pwd)/rr_control_panel.py"  # info: set PANEL
if pgrep -f "python3 .*rr_control_panel\\.py" >/dev/null 2>&1; then  # info: if
  echo "[open] Root Monitor already open — leaving it"  # info: echo
  exit 0  # info: exit
fi  # info: fi
if [[ -z "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then  # info: if
  echo "[open] no graphical session — Root Monitor not started" >&2  # info: echo
  exit 1  # info: exit
fi  # info: fi
echo "[open] Root Monitor"  # info: echo
nohup /usr/bin/python3 "$PANEL" >/dev/null 2>&1 &  # info: nohup
exit 0  # info: exit
