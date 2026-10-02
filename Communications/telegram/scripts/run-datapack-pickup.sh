#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${RR_DATAPACK_PYTHON:-python3}"
exec "$PY" "$ROOT/scripts/datapack-pickup.py" "$@"
