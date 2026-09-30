# ==============================================================================
# FILE: Energy/scripts/actions/river2pro-ac-always-on-off.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Migrated from legacy energy/scripts/actions/river2pro-ac-always-on-off.sh; G3 Pacific path only.
# Atomic BLE action; honest WAITING/FAIL semantics remain in action_runner.py.
set -euo pipefail  # info: set
ROOT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy"  # info: set ROOT
exec "$ROOT/lib/py" "$ROOT/lib/action_runner.py" \
  --device "river2pro" \
  --method "enable_ac_always_on" \
  --want "off" \
  --label "River2Pro AC always-on OFF"  # info: --label
