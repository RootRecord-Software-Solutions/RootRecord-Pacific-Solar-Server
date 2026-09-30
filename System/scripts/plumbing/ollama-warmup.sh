# ==============================================================================
# FILE: System/scripts/plumbing/ollama-warmup.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
# Migrated from legacy plumbing/scripts/ollama-warmup.sh; G3 System path only.
# Local service warmup; no internet required.
set -euo pipefail  # info: set
if curl -sf -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then  # info: if
  echo "[ok] ollama up"  # info: echo
  exit 0  # info: exit
fi  # info: fi
echo "[wait] ollama not up; sleeping 60s before another start"  # info: echo
sleep 60  # info: sleep
if curl -sf -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then  # info: if
  echo "[ok] ollama up"  # info: echo
  exit 0  # info: exit
fi  # info: fi
if command -v ollama >/dev/null 2>&1; then  # info: if
  nohup ollama serve >>/tmp/ollama-serve.log 2>&1 &  # info: nohup
  sleep 2  # info: sleep
fi  # info: fi
if curl -sf -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then  # info: if
  echo "[ok] ollama up"  # info: echo
  exit 0  # info: exit
fi  # info: fi
echo "[warn] ollama not ready"  # info: echo
exit 0  # info: exit
