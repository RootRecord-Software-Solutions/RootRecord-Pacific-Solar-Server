#!/usr/bin/env bash
set -euo pipefail
PORT=8791
CAMERA_DIR="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Security/Cameras"
LOG_FILE="/tmp/security-cam-server.log"

if ! ss -ltn 2>/dev/null | grep -q ":${PORT} "; then
  cd "$CAMERA_DIR"
  nohup python3 cam_server.py > "$LOG_FILE" 2>&1 &
  disown
  echo "security cam server started"
else
  echo "security cam server already running"
fi
