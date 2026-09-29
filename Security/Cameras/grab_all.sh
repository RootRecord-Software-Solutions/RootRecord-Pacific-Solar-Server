#!/usr/bin/env bash
set -euo pipefail
cd "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Security/Cameras"
for ch in 1 2 3 4; do
  python3 grab_frame.py "$ch" || echo "a-eyes: ch${ch} grab failed"
done
