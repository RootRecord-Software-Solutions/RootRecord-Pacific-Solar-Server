# ==============================================================================
# FILE: Energy/scripts/read/leapfrog-read.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Leap-frog: every ~5s call → alternate Delta2 / River2Pro (each pack ~10s)
# Phase 1 import: Pacific Energy/scripts/read (ROOT resolved relative)
set -euo pipefail  # info: set
ROOT="$(cd "$(dirname "$0")" && pwd)"  # info: set ROOT
# slot = floor(epoch/5); even → delta2, odd → river2pro
slot=$(( $(date +%s) / 5 ))  # info: set slot
if (( slot % 2 == 0 )); then  # info: if
  exec bash "$ROOT/delta2-read.sh"  # info: exec
else  # info: else
  exec bash "$ROOT/river2pro-read.sh"  # info: exec
fi  # info: fi
