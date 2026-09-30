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
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import math  # info: import math
import os  # info: import os
import sys  # info: import sys
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
INF = DB / "Logs" / "AI" / "Inference"  # info: set INF
CUR = Path(os.environ.get("RR_INFER_LOG_FILE", str(INF / "inference_current.jsonl")))  # info: set CUR
OUT_DIR = Path(os.environ.get("RR_AI_REPORT_OUT", str(DB.parent / "test-reports" / "AI-Processing")))  # info: set OUT_DIR
OUT = OUT_DIR / "ai-processing-report_current.md"  # info: set OUT
USAGE_SUMMARY = DB / "Reports" / "AI-Usage" / "last-summary.json"  # info: set USAGE_SUMMARY
GEN_PREFIX = "Generated: "  # info: set GEN_PREFIX


# ====================================================
# SECTION: function load
# What it does: load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load(since: datetime) -> tuple[list[dict], int]:  # info: def load
    files = []  # info: set files
    arch = CUR.parent / "Archive"  # info: set arch
    if arch.is_dir():  # info: if arch . is_dir ( ) :
        d0 = since.date()  # info: set d0
        for f in sorted(arch.glob("inference_*.jsonl")):  # info: for f in sorted ( arch . glob
            try:  # info: try :
                if datetime.strptime(f.stem.split("_", 1)[1], "%Y-%m-%d").date() >= d0:  # info: if datetime . strptime ( f . stem
                    files.append(f)  # info: files . append ( f )
            except ValueError:  # info: except ValueError :
                continue  # info: continue
    if CUR.is_file():  # info: if CUR . is_file ( ) :
        files.append(CUR)  # info: files . append ( CUR )
    rows, bad = [], 0  # info: rows , bad = [ ] , 0
    for f in files:  # info: for f in files :
        for ln in f.read_text(encoding="utf-8", errors="replace").splitlines():  # info: for ln in f . read_text ( encoding
            if not ln.strip():  # info: if not ln . strip ( ) :
                continue  # info: continue
            try:  # info: try :
                r = json.loads(ln)  # info: set r
                ts = datetime.fromisoformat(r["ts"])  # info: set ts
            except (ValueError, KeyError, TypeError):  # info: except ( ValueError , KeyError , TypeError )
                bad += 1  # info: set bad
                continue  # info: continue
            if ts >= since:  # info: if ts >= since :
                r["_ts"] = ts  # info: r [ "_ts" ] = ts
                rows.append(r)  # info: rows . append ( r )
    rows.sort(key=lambda r: r["_ts"])  # info: rows . sort ( key = lambda r
    return rows, bad  # info: return rows , bad


# ====================================================
# SECTION: function pct
# What it does: pct.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pct(vals: list[float], p: float):  # info: def pct
    if not vals:  # info: if not vals :
        return None  # info: return None
    s = sorted(vals)  # info: set s
    k = max(0, min(len(s) - 1, math.ceil(p / 100 * len(s)) - 1))  # info: set k
    return s[k]  # info: return s [ k ]


# ====================================================
# SECTION: function fmt
# What it does: fmt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fmt(v, unit=""):  # info: def fmt
    return "n/a" if v is None else f"{v:,}{unit}"  # info: return "n/a" if v is None else f"


# ====================================================
# SECTION: function grok_spend_lines
# What it does: xAI rows from the local ledger summary. No network. Missing or empty -> no ledger rows.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def grok_spend_lines() -> list[str]:  # info: def grok_spend_lines
    """xAI rows from the local ledger summary. No network. Missing or empty -> no ledger rows."""  # info: """xAI rows from the local ledger summary. No network. Missing or empty -> no ledger rows."""
    lines = ["", "## Grok spend", ""]
    if not USAGE_SUMMARY.is_file():  # info: if not USAGE_SUMMARY . is_file ( ) :
        lines.append("- no ledger rows")  # info: lines . append ( "- no ledger rows" )
        return lines  # info: return lines
    try:  # info: try :
        data = json.loads(USAGE_SUMMARY.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        lines.append("- no ledger rows")  # info: lines . append ( "- no ledger rows" )
        return lines  # info: return lines
    detail = [d for d in (data.get("detail") or []) if str(d.get("provider", "")).lower() == "xai"]  # info: set detail
    if not detail:  # info: if not detail :
        lines.append("- no ledger rows")  # info: lines . append ( "- no ledger rows" )
        return lines  # info: return lines
    calls = sum(int(d.get("calls") or 0) for d in detail)  # info: set calls
    tokens = sum(int(d.get("total_tokens") or 0) for d in detail)  # info: set tokens
    cost = sum(float(d.get("cost_usd") or 0) for d in detail)  # info: set cost
    lines.append(f"- xAI calls: {calls}")  # info: lines . append ( f" - xAI calls: { calls
    lines.append(f"- Tokens: {tokens:,}")  # info: lines . append ( f" - Tokens: { tokens
    lines.append(f"- Estimated USD: {cost:.2f}")  # info: lines . append ( f" - Estimated USD: { cost
    return lines  # info: return lines


# ====================================================
# SECTION: function build
# What it does: build.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build(rows: list[dict], bad: int, since: datetime, now: datetime, hours: float) -> str:  # info: def build
    n = len(rows)  # info: set n
    by_route: dict[str, int] = {}  # info: set by_route
    by_model: dict[str, int] = {}  # info: set by_model
    for r in rows:  # info: for r in rows :
        by_route[r.get("route", "?")] = by_route.get(r.get("route", "?"), 0) + 1  # info: by_route [ r . get ( "route" ,
        key = f"{r.get('route', '?')} / {r.get('model', '?')}"  # info: set key
        by_model[key] = by_model.get(key, 0) + 1  # info: by_model [ key ] = by_model . get
    npu = by_route.get("npu-flm", 0)  # info: set npu
    lat = [int(r["latency_ms"]) for r in rows if isinstance(r.get("latency_ms"), (int, float))]  # info: set lat
    peaks = [int(r["flm_peak_rss_mb"]) for r in rows if isinstance(r.get("flm_peak_rss_mb"), (int, float))]  # info: set peaks
    avail = [int(r[k]) for r in rows for k in ("mem_avail_mb_before", "mem_avail_mb_after") if isinstance(r.get(k), (int, float))]  # info: set avail
    errors = [r for r in rows if r.get("exit_code") not in (0, None)]  # info: set errors
    empty = [r for r in rows if r.get("reply_chars") == 0]  # info: set empty
    L = [  # info: set L
        "# AI Processing Report",
        "",  # info: "" ,
        f"{GEN_PREFIX}{now.isoformat(timespec='seconds')}",  # info: f" { GEN_PREFIX } { now . isoformat
        f"Window: {since.isoformat(timespec='minutes')} → {now.isoformat(timespec='minutes')} ({hours:g} h)",  # info: f" Window: { since . isoformat ( timespec
        f"Source: `Logs/AI/Inference/inference_current.jsonl` (+ `Archive/inference_YYYY-MM-DD.jsonl`)",  # info: f" Source: `Logs/AI/Inference/inference_current.jsonl` (+ `Archive/inference_YYYY-MM-DD.jsonl`) " ,
        "",  # info: "" ,
        "## Summary",
        "",  # info: "" ,
        f"- Requests: {n}",  # info: f" - Requests: { n } " ,
        f"- NPU share (npu-flm): {npu}/{n}" + (f" = {100 * npu / n:.0f}%" if n else ""),  # info: f" - NPU share (npu-flm): { npu } / { n
        f"- Fallbacks to Ollama: {sum(1 for r in rows if r.get('fallback') is True)}",  # info: f" - Fallbacks to Ollama: { sum ( 1 for r
        f"- FLM cold starts: {sum(1 for r in rows if r.get('flm_cold_start') is True)}",  # info: f" - FLM cold starts: { sum ( 1 for r
        f"- Errors (exit_code ≠ 0): {len(errors)}; empty replies: {len(empty)}; unparsable lines: {bad}",  # info: f" - Errors (exit_code ≠ 0): { len ( errors ) }
        f"- First / last request: {rows[0]['ts'] if rows else 'n/a'} / {rows[-1]['ts'] if rows else 'n/a'}",  # info: f" - First / last request: { rows [ 0 ] [
        "",  # info: "" ,
        "## Latency (ms, whole request incl. cold start)",
        "",  # info: "" ,
        f"- p50 {fmt(pct(lat, 50))} · p95 {fmt(pct(lat, 95))} · max {fmt(max(lat) if lat else None)}",  # info: f" - p50 { fmt ( pct ( lat
        "",  # info: "" ,
        "## Memory",
        "",  # info: "" ,
        f"- FLM peak RSS (VmHWM, host RAM only; NPU buffers not counted): max {fmt(max(peaks) if peaks else None, ' MB')}",  # info: f" - FLM peak RSS (VmHWM, host RAM only; NPU buffers not counted): max { fmt ( max ( peaks
        f"- Lowest MemAvailable seen before/after a request: {fmt(min(avail) if avail else None, ' MB')}",  # info: f" - Lowest MemAvailable seen before/after a request: { fmt ( min ( avail
        "",  # info: "" ,
        "## Requests by route",
        "",  # info: "" ,
        "| Route | Requests |",  # info: "| Route | Requests |" ,
        "|---|---|",  # info: "|---|---|" ,
    ]  # info: ]
    L += [f"| {k} | {v} |" for k, v in sorted(by_route.items())] or ["| (none) | 0 |"]  # info: set L
    L += ["", "## Requests by route / model", "", "| Route / model | Requests |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(by_model.items())] or ["| (none) | 0 |"]  # info: set L
    if errors:  # info: if errors :
        L += ["", "## Errors", "", "| ts | caller | route | model | exit_code |", "|---|---|---|---|---|"]
        L += [f"| {r['ts']} | {r.get('caller', '')} | {r.get('route', '')} | {r.get('model', '')} | {r.get('exit_code')} |" for r in errors[-20:]]  # info: set L
    L += grok_spend_lines()  # info: set L
    L += ["", "_Metadata only: prompt/reply lengths, never text._", ""]  # info: set L
    return "\n".join(L)  # info: return "\n" . join ( L )


# ====================================================
# SECTION: function body
# What it does: body.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def body(text: str) -> str:  # info: def body
    return "\n".join(l for l in text.splitlines() if not l.startswith(GEN_PREFIX) and not l.startswith("Window: "))  # info: return "\n" . join ( l for l


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    hours = float(os.environ.get("RR_AI_REPORT_HOURS", "24"))  # info: set hours
    now = datetime.now().astimezone().replace(microsecond=0)  # info: set now
    since = now - timedelta(hours=hours)  # info: set since
    rows, bad = load(since)  # info: rows , bad = load ( since )
    text = build(rows, bad, since, now, hours)  # info: set text
    OUT_DIR.mkdir(parents=True, exist_ok=True)  # info: OUT_DIR . mkdir ( parents = True ,
    archived = ""  # info: set archived
    if OUT.is_file():  # info: if OUT . is_file ( ) :
        old = OUT.read_text(encoding="utf-8", errors="replace")  # info: set old
        if body(old) == body(text):  # info: if body ( old ) == body (
            print(f"[ok] ai-processing-report unchanged ({len(rows)} requests) — not rewritten")  # info: call print
            return 0  # info: return 0
        stamp = datetime.fromtimestamp(OUT.stat().st_mtime).astimezone().strftime("%Y-%m-%dT%H%M")  # info: set stamp
        dest = OUT_DIR / "Archive" / f"ai-processing-report_{stamp}.md"  # info: set dest
        dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents =
        n = 1  # info: set n
        while dest.exists():  # info: while dest . exists ( ) :
            dest = dest.with_name(f"ai-processing-report_{stamp}-{n}.md")  # info: set dest
            n += 1  # info: set n
        os.replace(OUT, dest)  # info: os . replace ( OUT , dest )
        archived = f" archived={dest.name}"  # info: set archived
    tmp = OUT.with_suffix(".md.tmp")  # info: set tmp
    tmp.write_text(text, encoding="utf-8")  # info: tmp . write_text ( text , encoding =
    os.replace(tmp, OUT)  # info: os . replace ( tmp , OUT )
    print(f"[ok] ai-processing-report written ({len(rows)} requests){archived}: {OUT}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
