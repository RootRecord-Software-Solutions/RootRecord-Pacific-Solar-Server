#!/usr/bin/env bash
# Migrated from legacy plumbing/scripts/ollama-warmup.sh; G3 System path only.
# Local service warmup; no internet required.
set -euo pipefail
if curl -sf -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "[ok] ollama up"
  exit 0
fi
echo "[wait] ollama not up; sleeping 60s before another start"
sleep 60
if curl -sf -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "[ok] ollama up"
  exit 0
fi
if command -v ollama >/dev/null 2>&1; then
  nohup ollama serve >>/tmp/ollama-serve.log 2>&1 &
  sleep 2
fi
if curl -sf -m 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "[ok] ollama up"
  exit 0
fi
echo "[warn] ollama not ready"
exit 0
