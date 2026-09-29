#!/usr/bin/env python3
# ==============================================================================
# ai_processing_report.py — AI processing report from run-infer.sh JSONL (stdlib only).
# In : Database/Logs/AI/Inference/inference_current.jsonl + Archive/inference_YYYY-MM-DD.jsonl
# Out: Database/Logs/AI/Reports/ai-processing-report_current.md
#      previous copy -> Logs/AI/Reports/Archive/ai-processing-report_YYYY-MM-DDTHHMM.md (only if changed)
# Window: last RR_AI_REPORT_HOURS hours (default 24). Metadata only — the log never holds prompt text.
# Scheduled by jobs.py id ai_processing_report_hourly, gated OFF unless RR_AI_REPORT=1 at poller start.
# Added 2026-09-29 (g3-voice-ailog).
# ==============================================================================
from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
INF = DB / "Logs" / "AI" / "Inference"
CUR = Path(os.environ.get("RR_INFER_LOG_FILE", str(INF / "inference_current.jsonl")))
OUT_DIR = DB / "Logs" / "AI" / "Reports"
OUT = OUT_DIR / "ai-processing-report_current.md"
GEN_PREFIX = "Generated: "


def load(since: datetime) -> tuple[list[dict], int]:
    files = []
    arch = CUR.parent / "Archive"
    if arch.is_dir():
        d0 = since.date()
        for f in sorted(arch.glob("inference_*.jsonl")):
            try:
                if datetime.strptime(f.stem.split("_", 1)[1], "%Y-%m-%d").date() >= d0:
                    files.append(f)
            except ValueError:
                continue
    if CUR.is_file():
        files.append(CUR)
    rows, bad = [], 0
    for f in files:
        for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
                ts = datetime.fromisoformat(r["ts"])
            except (ValueError, KeyError, TypeError):
                bad += 1
                continue
            if ts >= since:
                r["_ts"] = ts
                rows.append(r)
    rows.sort(key=lambda r: r["_ts"])
    return rows, bad


def pct(vals: list[float], p: float):
    if not vals:
        return None
    s = sorted(vals)
    k = max(0, min(len(s) - 1, math.ceil(p / 100 * len(s)) - 1))
    return s[k]


def fmt(v, unit=""):
    return "n/a" if v is None else f"{v:,}{unit}"


def build(rows: list[dict], bad: int, since: datetime, now: datetime, hours: float) -> str:
    n = len(rows)
    by_route: dict[str, int] = {}
    by_model: dict[str, int] = {}
    for r in rows:
        by_route[r.get("route", "?")] = by_route.get(r.get("route", "?"), 0) + 1
        key = f"{r.get('route', '?')} / {r.get('model', '?')}"
        by_model[key] = by_model.get(key, 0) + 1
    npu = by_route.get("npu-flm", 0)
    lat = [int(r["latency_ms"]) for r in rows if isinstance(r.get("latency_ms"), (int, float))]
    peaks = [int(r["flm_peak_rss_mb"]) for r in rows if isinstance(r.get("flm_peak_rss_mb"), (int, float))]
    avail = [int(r[k]) for r in rows for k in ("mem_avail_mb_before", "mem_avail_mb_after") if isinstance(r.get(k), (int, float))]
    errors = [r for r in rows if r.get("exit_code") not in (0, None)]
    empty = [r for r in rows if r.get("reply_chars") == 0]
    L = [
        "# AI Processing Report",
        "",
        f"{GEN_PREFIX}{now.isoformat(timespec='seconds')}",
        f"Window: {since.isoformat(timespec='minutes')} → {now.isoformat(timespec='minutes')} ({hours:g} h)",
        f"Source: `Logs/AI/Inference/inference_current.jsonl` (+ `Archive/inference_YYYY-MM-DD.jsonl`)",
        "",
        "## Summary",
        "",
        f"- Requests: {n}",
        f"- NPU share (npu-flm): {npu}/{n}" + (f" = {100 * npu / n:.0f}%" if n else ""),
        f"- Fallbacks to Ollama: {sum(1 for r in rows if r.get('fallback') is True)}",
        f"- FLM cold starts: {sum(1 for r in rows if r.get('flm_cold_start') is True)}",
        f"- Errors (exit_code ≠ 0): {len(errors)}; empty replies: {len(empty)}; unparsable lines: {bad}",
        f"- First / last request: {rows[0]['ts'] if rows else 'n/a'} / {rows[-1]['ts'] if rows else 'n/a'}",
        "",
        "## Latency (ms, whole request incl. cold start)",
        "",
        f"- p50 {fmt(pct(lat, 50))} · p95 {fmt(pct(lat, 95))} · max {fmt(max(lat) if lat else None)}",
        "",
        "## Memory",
        "",
        f"- FLM peak RSS (VmHWM, host RAM only; NPU buffers not counted): max {fmt(max(peaks) if peaks else None, ' MB')}",
        f"- Lowest MemAvailable seen before/after a request: {fmt(min(avail) if avail else None, ' MB')}",
        "",
        "## Requests by route",
        "",
        "| Route | Requests |",
        "|---|---|",
    ]
    L += [f"| {k} | {v} |" for k, v in sorted(by_route.items())] or ["| (none) | 0 |"]
    L += ["", "## Requests by route / model", "", "| Route / model | Requests |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(by_model.items())] or ["| (none) | 0 |"]
    if errors:
        L += ["", "## Errors", "", "| ts | caller | route | model | exit_code |", "|---|---|---|---|---|"]
        L += [f"| {r['ts']} | {r.get('caller', '')} | {r.get('route', '')} | {r.get('model', '')} | {r.get('exit_code')} |" for r in errors[-20:]]
    L += ["", "_Metadata only: prompt/reply lengths, never text._", ""]
    return "\n".join(L)


def body(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.startswith(GEN_PREFIX) and not l.startswith("Window: "))


def main() -> int:
    hours = float(os.environ.get("RR_AI_REPORT_HOURS", "24"))
    now = datetime.now().astimezone().replace(microsecond=0)
    since = now - timedelta(hours=hours)
    rows, bad = load(since)
    text = build(rows, bad, since, now, hours)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    archived = ""
    if OUT.is_file():
        old = OUT.read_text(encoding="utf-8", errors="replace")
        if body(old) == body(text):
            print(f"[ok] ai-processing-report unchanged ({len(rows)} requests) — not rewritten")
            return 0
        stamp = datetime.fromtimestamp(OUT.stat().st_mtime).astimezone().strftime("%Y-%m-%dT%H%M")
        dest = OUT_DIR / "Archive" / f"ai-processing-report_{stamp}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        n = 1
        while dest.exists():
            dest = dest.with_name(f"ai-processing-report_{stamp}-{n}.md")
            n += 1
        os.replace(OUT, dest)
        archived = f" archived={dest.name}"
    tmp = OUT.with_suffix(".md.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, OUT)
    print(f"[ok] ai-processing-report written ({len(rows)} requests){archived}: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
