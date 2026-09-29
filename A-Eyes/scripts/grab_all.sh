#!/usr/bin/env bash
set -euo pipefail
cd ~/.ollama/skills/a-eyes/scripts
for ch in 1 2 3 4; do
  python3 grab_frame.py "$ch" || echo "a-eyes: ch${ch} grab failed"
done
