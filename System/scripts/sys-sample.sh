# ==============================================================================
# FILE: System/scripts/sys-sample.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# System/scripts/sys-sample.sh — host CPU/load/mem sample (Pacific)
set -euo pipefail  # info: set
ROOT="$(cd "$(dirname "$0")/.." && pwd)"  # info: set ROOT
export PYTHONPATH="$ROOT/lib${PYTHONPATH:+:$PYTHONPATH}"  # info: export
exec python3 "$ROOT/lib/sample.py"  # info: exec
