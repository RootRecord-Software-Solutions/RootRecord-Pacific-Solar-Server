#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/rootrecord/.ollama/skills/system-stats"
export PYTHONPATH="$ROOT/lib${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$ROOT/lib/sample.py"
