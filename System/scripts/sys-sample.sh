#!/usr/bin/env bash
# System/scripts/sys-sample.sh — host CPU/load/mem sample (Pacific)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/lib${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$ROOT/lib/sample.py"
