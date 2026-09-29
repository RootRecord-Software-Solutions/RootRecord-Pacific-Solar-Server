#!/usr/bin/env bash
set -euo pipefail
PORT=8791
if ! ss -ltn 2>/dev/null | grep -q ":${PORT} "; then
  cd "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/A-Eyes/scripts"
  nohup python3 cam_server.py > /tmp/a-eyes-cam-server.log 2>&1 &
  disown
  echo "a-eyes cam server started"
else
  echo "a-eyes cam server already running"
fi
