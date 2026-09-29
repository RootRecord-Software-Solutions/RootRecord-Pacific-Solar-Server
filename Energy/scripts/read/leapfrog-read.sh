#!/usr/bin/env bash
# Leap-frog: every ~5s call → alternate Delta2 / River2Pro (each pack ~10s)
# Phase 1 import: Pacific Energy/scripts/read (ROOT resolved relative)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# slot = floor(epoch/5); even → delta2, odd → river2pro
slot=$(( $(date +%s) / 5 ))
if (( slot % 2 == 0 )); then
  exec bash "$ROOT/delta2-read.sh"
else
  exec bash "$ROOT/river2pro-read.sh"
fi
