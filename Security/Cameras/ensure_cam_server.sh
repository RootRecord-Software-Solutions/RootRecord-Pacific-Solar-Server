# ==============================================================================
# FILE: Security/Cameras/ensure_cam_server.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
set -euo pipefail  # info: set
PORT=8791  # info: set PORT
CAMERA_DIR="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Security/Cameras"  # info: set CAMERA_DIR
LOG_FILE="/tmp/security-cam-server.log"  # info: set LOG_FILE

if ! ss -ltn 2>/dev/null | grep -q ":${PORT} "; then  # info: if
  cd "$CAMERA_DIR"  # info: cd
  nohup python3 cam_server.py > "$LOG_FILE" 2>&1 &  # info: nohup
  disown  # info: disown
  echo "security cam server started"  # info: echo
else  # info: else
  echo "security cam server already running"  # info: echo
fi  # info: fi
