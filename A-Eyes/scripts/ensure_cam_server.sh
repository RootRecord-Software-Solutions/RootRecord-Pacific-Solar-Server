#!/usr/bin/env bash
set -euo pipefail
PORT=8791
if ! ss -ltn 2>/dev/null | grep -q ":${PORT} "; then
  cd ~/.ollama/skills/a-eyes/scripts
  nohup python3 cam_server.py > /tmp/a-eyes-cam-server.log 2>&1 &
  disown
  echo "a-eyes cam server started"
else
  echo "a-eyes cam server already running"
fi
