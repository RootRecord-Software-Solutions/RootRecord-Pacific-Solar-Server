# ==============================================================================
# FILE: Products/scripts/Companions/dev-desk/bin/start-dev-desk.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
echo "target is not on this desk" >&2; exit 1  # info: echo
exec /home/rootrecord/.ollama/skills/companions/scripts/start-dev-desk.sh "$@"  # info: exec
