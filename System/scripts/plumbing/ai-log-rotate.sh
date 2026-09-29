#!/usr/bin/env bash
# ==============================================================================
# ai-log-rotate.sh — daily rotation of the AI inference JSONL (`_current` convention).
#   Logs/AI/Inference/inference_current.jsonl  (live, appended by run-infer.sh)
#   Logs/AI/Inference/Archive/inference_YYYY-MM-DD.jsonl  (one file per HST day)
# Lines dated before today (by their "ts" field) move to that day's archive; today's
# lines stay live. Same flock as run-infer.sh's append (inference_current.lock).
# Called by the gated ai_processing_report job (RR_AI_REPORT=1) before the report.
# Safe to run any time; stdlib only; never touches line content. Added 2026-09-29.
# ==============================================================================
set -u
DB="${RR_DATABASE_ROOT:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database}"
CUR="${RR_INFER_LOG_FILE:-$DB/Logs/AI/Inference/inference_current.jsonl}"
exec nice -n 10 python3 - "$CUR" <<'PY'
import fcntl, os, sys
from datetime import datetime
cur = sys.argv[1]
if not os.path.isfile(cur) or os.path.getsize(cur) == 0:
    print("[ok] ai-log-rotate: nothing to rotate"); sys.exit(0)
arch = os.path.join(os.path.dirname(cur), "Archive")
today = datetime.now().astimezone().strftime("%Y-%m-%d")
lock = cur[: -len(".jsonl")] + ".lock" if cur.endswith(".jsonl") else cur + ".lock"
with open(lock, "a") as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    with open(cur, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    keep, move = [], {}
    for ln in lines:
        day = ln[7:17] if ln.startswith('{"ts":"') else ""
        if len(day) == 10 and day[4] == "-" and day < today:
            move.setdefault(day, []).append(ln)
        else:
            keep.append(ln)
    if move:
        os.makedirs(arch, exist_ok=True)
        for day, rows in sorted(move.items()):
            with open(os.path.join(arch, f"inference_{day}.jsonl"), "a", encoding="utf-8") as out:
                out.writelines(rows)
        tmp = cur + ".tmp"
        with open(tmp, "w", encoding="utf-8") as out:
            out.writelines(keep)
        os.replace(tmp, cur)
    print(f"[ok] ai-log-rotate: moved={sum(len(v) for v in move.values())} kept={len(keep)} days={sorted(move)}")
PY
