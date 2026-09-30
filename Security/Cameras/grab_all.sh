# ==============================================================================
# FILE: Security/Cameras/grab_all.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
set -euo pipefail  # info: set
cd "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Security/Cameras"  # info: cd
for ch in 1 2 3 4; do  # info: for
  python3 grab_frame.py "$ch" || echo "a-eyes: ch${ch} grab failed"  # info: python3
done  # info: done
