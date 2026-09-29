#!/usr/bin/env bash
# Migrated from legacy plumbing/scripts/flm-warmup.sh; G3 System path only.
set -euo pipefail
# NO RESIDENT MODEL (Alexander 03:12 HST 2026-09-29): `flm serve llama3.2:3b` maps ~10 GB (9.6 GB shmem) and
# OOM-killed the whole poller unit at every start (restart loop 03:10-03:13). Warmup is now OPT-IN only:
# FLM_WARMUP_RESIDENT=1 bash flm-warmup.sh. Default = skip; inference loads on demand (run-infer.sh).
if [[ "${FLM_WARMUP_RESIDENT:-0}" != "1" ]]; then
  echo "[skip] FLM warmup disabled (no resident model; set FLM_WARMUP_RESIDENT=1 to opt in)"
  exit 0
fi
PORT=52625
FLM_MODEL="${FLM_MODEL:-llama3.2:3b}"
# Log holds full request bodies (prompts): git-ignored Logs/AI/FLM/ (2026-09-29; was tracked GITHUB/logs/flm.log).
LOG="${FLM_LOG:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/AI/FLM/flm.log}"
mkdir -p "$(dirname "$LOG")"
FLM_BIN=""
for c in "$HOME/.local/bin/flm" /usr/local/bin/flm flm; do
  if command -v "$c" >/dev/null 2>&1 || [[ -x "$c" ]]; then
    FLM_BIN=$(command -v "$c" 2>/dev/null || echo "$c")
    break
  fi
done
if [[ -z "$FLM_BIN" || ! -x "$FLM_BIN" ]]; then
  echo "[skip] FLM binary not found (NPU path optional; Ollama remains fallback)"
  exit 0
fi
if curl -sf -m 1 "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1; then
  echo "[ok] FLM already up"
  exit 0
fi
pkill -f "flm serve" 2>/dev/null || true
sleep 1
nohup "$FLM_BIN" serve "$FLM_MODEL" --pmode "${FLM_PMODE:-balanced}" --host 127.0.0.1 --port "$PORT" >>"$LOG" 2>&1 &
echo "[ok] FLM starting pid=$! → $LOG"
for i in 1 2 3 4 5 6 7 8 9 10; do
  sleep 2
  if curl -sf -m 1 "http://127.0.0.1:$PORT/v1/models" >/dev/null 2>&1; then
    echo "[ok] FLM ready"
    exit 0
  fi
done
echo "[warn] FLM not ready yet — check $LOG"
exit 0
