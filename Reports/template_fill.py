#!/usr/bin/env python3
# ==============================================================================
# # INFO — template_fill.py: fill the Library operations templates from measured desk data (stdlib)
# ------------------------------------------------------------------------------
# Usage: template_fill.py [--all | --template worklog|checkpoint|event|workorder] [--date YYYY-MM-DD]
#                         [--draft none|model|auto] [--model-templates worklog,workorder] [--dry-run]
# Templates (read-only): Library Documentation/01-Operations/Templates/TEMPLATE *.md — same headings,
#   tables, field order, date formats (YYYY-MM-DD, HH:MM HST, HH_MM in filenames) and status vocabulary.
# Sources: Library 07-Testing index, 08-Ideas index, Work-Orders, operator worklogs of the day (sign-off list);
#   Database Logs/AI/Inference JSONL, Logs/Automations poller log (+ hourly Archive), System/last host sample,
#   Energy/soc, Energy/layers/periods.json, Media/Images, Weather reports, Worklog; read-only systemctl --user is-active / process checks.
# Free text ONLY (purpose, status line, next step, principle, scope, intent) is drafted by a specialist via
#   System/scripts/plumbing/run-infer.sh (TARGET rr-exec: NPU on demand, Ollama fallback keep_alive 0) with a
#   strict "use only the facts given" prompt. Drafts with unsupported numbers / bad shape -> deterministic text.
# Out: Database Reports/Generated/<Template-Name>_current.md (previous copy -> Archive/<name>_YYYY-MM-DDTHHMM.md
#   if changed) + template-fill-validation_current.json. NEVER writes into the Library (guarded).
# Validator: Reports/template_validate.py — structural mismatch => output rejected (<name>_rejected.md).
# Job: jobs.py id template_reports_daily, OFF unless RR_TEMPLATE_REPORTS=1 at poller start.
# HOW TO ADD a template: add a render_<key>() + TEMPLATES row (file, output name, vocab rules, free-text keys).
# Created 2026-09-29 HST (g3-template-reports). Bak snapshots: 2 - RootRecord-Database/Archive/Github-desk-backups/
# ==============================================================================
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import os  # info: import os
import re  # info: import re
import shutil  # info: import shutil
import socket  # info: import socket
import statistics  # info: import statistics
import subprocess  # info: import subprocess
import sys  # info: import sys
import tempfile  # info: import tempfile
import urllib.request  # info: import urllib . request
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parent  # info: set PACIFIC
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
import template_validate as tv  # noqa: E402

ECO = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ECO
DB = Path(os.environ.get("RR_DATABASE_ROOT", str(ECO / "2 - RootRecord-Database")))  # info: set DB
LIB = Path(os.environ.get("RR_LIBRARY_ROOT", str(ECO / "5 - RootRecord-Library")))  # info: set LIB
DOCS = LIB / "Documentation"  # info: set DOCS
TPL_DIR = DOCS / "01-Operations" / "Templates"  # info: set TPL_DIR
OUT_DIR = Path(os.environ.get("RR_TEMPLATE_OUT", str(ECO / "test-reports" / "Templates")))  # info: set OUT_DIR
RUN_INFER = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"  # info: set RUN_INFER
SF = PACIFIC / "System" / "scripts" / "plumbing" / "single-flight.sh"  # info: set SF
POLLER_LOG = DB / "Logs" / "Automations" / "automations_current.log"  # info: set POLLER_LOG
INFER_LOG = DB / "Logs" / "AI" / "Inference" / "inference_current.jsonl"  # info: set INFER_LOG
SPECIALIST = os.environ.get("RR_TEMPLATE_SPECIALIST", "rr-exec")  # info: set SPECIALIST
MIN_MEM_MB_FOR_MODEL = 3072  # info: set MIN_MEM_MB_FOR_MODEL


# ------------------------------------------------------------------ helpers
# ====================================================
# SECTION: function now
# What it does: now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> datetime:  # info: def now
    return datetime.now().astimezone()  # info: return datetime . now ( ) . astimezone


# ====================================================
# SECTION: function hm
# What it does: hm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hm(dt: datetime) -> str:  # info: def hm
    return dt.astimezone().strftime("%H:%M")  # info: return dt . astimezone ( ) . strftime


# ====================================================
# SECTION: function read
# What it does: read.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read(p: Path) -> str:  # info: def read
    try:  # info: try :
        return p.read_text(encoding="utf-8", errors="replace")  # info: return p . read_text ( encoding = "utf-8"
    except OSError:  # info: except OSError :
        return ""  # info: return ""


# ====================================================
# SECTION: function cell
# What it does: cell.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cell(s: str, n: int = 110) -> str:  # info: def cell
    s = re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()  # info: set s
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)  # drop md links inside cells
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"  # info: return s if len ( s ) <=


# ====================================================
# SECTION: function mem_avail_mb
# What it does: mem avail mb.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mem_avail_mb() -> int:  # info: def mem_avail_mb
    for ln in read(Path("/proc/meminfo")).splitlines():  # info: for ln in read ( Path ( "/proc/meminfo"
        if ln.startswith("MemAvailable:"):  # info: if ln . startswith ( "MemAvailable:" ) :
            return int(ln.split()[1]) // 1024  # info: return int ( ln . split ( )
    return 0  # info: return 0


# ====================================================
# SECTION: function is_active
# What it does: is active.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_active(unit: str) -> str:  # info: def is_active
    try:  # info: try :
        r = subprocess.run(["systemctl", "--user", "is-active", unit], capture_output=True, text=True, timeout=3)  # info: set r
        return r.stdout.strip() or "unknown"  # info: return r . stdout . strip ( )
    except Exception:  # info: except Exception :
        return "unknown"  # info: return "unknown"


# ====================================================
# SECTION: function procs_matching
# What it does: procs matching.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def procs_matching(pred) -> int:  # info: def procs_matching
    n = 0  # info: set n
    for d in Path("/proc").iterdir():  # info: for d in Path ( "/proc" ) .
        if not d.name.isdigit():  # info: if not d . name . isdigit (
            continue  # info: continue
        try:  # info: try :
            cmd = (d / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")  # info: set cmd
        except OSError:  # info: except OSError :
            continue  # info: continue
        if pred(cmd):  # info: if pred ( cmd ) :
            n += 1  # info: set n
    return n  # info: return n


# ====================================================
# SECTION: function procs_by_comm
# What it does: procs by comm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def procs_by_comm(name: str) -> int:  # info: def procs_by_comm
    n = 0  # info: set n
    for d in Path("/proc").iterdir():  # info: for d in Path ( "/proc" ) .
        if d.name.isdigit():  # info: if d . name . isdigit ( )
            try:  # info: try :
                n += (d / "comm").read_text().strip() == name  # info: set n
            except OSError:  # info: except OSError :
                pass  # info: pass
    return n  # info: return n


# ====================================================
# SECTION: function port_open
# What it does: port open.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def port_open(port: int) -> bool:  # info: def port_open
    try:  # info: try :
        with socket.create_connection(("127.0.0.1", port), timeout=1):  # info: with socket . create_connection ( ( "127.0.0.1" ,
            return True  # info: return True
    except OSError:  # info: except OSError :
        return False  # info: return False


# ====================================================
# SECTION: function age_min
# What it does: age min.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def age_min(dt: datetime | None, ref: datetime) -> float | None:  # info: def age_min
    return None if dt is None else (ref - dt).total_seconds() / 60  # info: return None if dt is None else (


# ====================================================
# SECTION: function newest_mtime
# What it does: newest mtime.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def newest_mtime(root: Path, pattern: str = "*", max_files: int = 200000) -> datetime | None:  # info: def newest_mtime
    best = None  # info: set best
    try:  # info: try :
        for i, e in enumerate(os.scandir(root)):  # info: for i , e in enumerate ( os
            if i > max_files:  # info: if i > max_files :
                break  # info: break
            if e.is_file() and Path(e.name).match(pattern):  # info: if e . is_file ( ) and Path
                m = e.stat().st_mtime  # info: set m
                best = m if best is None or m > best else best  # info: set best
    except OSError:  # info: except OSError :
        return None  # info: return None
    return datetime.fromtimestamp(best).astimezone() if best else None  # info: return datetime . fromtimestamp ( best ) .


# ------------------------------------------------------------------ sources
# ====================================================
# SECTION: class Facts
# What it does: Everything a report may state. corpus = every source string used (for the number check).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Facts:  # info: class Facts
    """Everything a report may state. corpus = every source string used (for the number check)."""  # info: """Everything a report may state. corpus = every source string used (for the number check)."""

    def __init__(self, day: str):  # info: def __init__
        self.day, self.t = day, now()  # info: self . day , self . t =
        self.corpus: list[str] = [day, hm(self.t), self.t.strftime("%H_%M")]  # info: self . corpus : list [ str ]

    def add(self, *s):  # info: def add
        self.corpus.extend(str(x) for x in s)  # info: self . corpus . extend ( str (


# ====================================================
# SECTION: function testing_records
# What it does: testing records.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def testing_records(f: Facts) -> list[dict]:  # info: def testing_records
    rows = []  # info: set rows
    for ln in read(DOCS / "07-Testing" / "README.md").splitlines():  # info: for ln in read ( DOCS / "07-Testing"
        m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s+(~?\d{2}:\d{2})\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(.+?)\s*\|\s*$", ln)  # info: set m
        if m and m.group(1) == f.day:  # info: if m and m . group ( 1
            rows.append({"time": m.group(2), "title": m.group(3), "file": m.group(4), "state": m.group(5)})  # info: rows . append ( { "time" : m
            f.add(ln)  # info: f . add ( ln )
    rows.sort(key=lambda r: r["time"].lstrip("~"))  # info: rows . sort ( key = lambda r
    return rows  # info: return rows


# ====================================================
# SECTION: function ideas
# What it does: ideas.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ideas(f: Facts) -> list[dict]:  # info: def ideas
    rows = []  # info: set rows
    for ln in read(DOCS / "08-Ideas" / "README.md").splitlines():  # info: for ln in read ( DOCS / "08-Ideas"
        m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\[([^\]]+)\]\([^)]+\)\s*\|\s*(.+?)\s*\|", ln)  # info: set m
        if m:  # info: if m :
            rows.append({"date": m.group(1), "title": m.group(2), "state": m.group(3)})  # info: rows . append ( { "date" : m
            f.add(ln)  # info: f . add ( ln )
    return rows  # info: return rows


# ====================================================
# SECTION: function signoff_items
# What it does: signoff items.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def signoff_items(f: Facts) -> list[str]:  # info: def signoff_items
    items = []  # info: set items
    logs = sorted((DOCS / "01-Operations" / "0 - Human Operator Work Logs").glob(f"{f.day} *.md"))  # info: set logs
    for p in logs:  # info: for p in logs :
        txt = read(p)  # info: set txt
        m = re.search(r"^## Needs Alexander sign-off\s*$(.*?)(?=^## |\Z)", txt, re.M | re.S)
        if not m:  # info: if not m :
            continue  # info: continue
        for ln in m.group(1).splitlines():  # info: for ln in m . group ( 1
            mm = re.match(r"^- \[ \] (.+)$", ln.strip())  # info: set mm
            if mm:  # info: if mm :
                t = mm.group(1)  # info: set t
                b = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", t)  # info: set b
                if b and b.group(1).endswith(":"):  # "**Hardware tests:** Energy arm/disarm ..." -> keep the first clause
                    items.append(cell(b.group(1) + " " + re.split(r"(?<=[.;(])\s", b.group(2))[0].rstrip(".;("), 100))  # info: items . append ( cell ( b .
                else:  # info: else :
                    items.append(cell(b.group(1).rstrip(".") if b else t, 100))  # info: items . append ( cell ( b .
                f.add(ln)  # info: f . add ( ln )
    seen, out = set(), []  # info: seen , out = set ( ) ,
    for i in items:  # info: for i in items :
        if i not in seen:  # info: if i not in seen :
            seen.add(i)  # info: seen . add ( i )
            out.append(i)  # info: out . append ( i )
    return out  # info: return out


# ====================================================
# SECTION: function work_orders
# What it does: work orders.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def work_orders(f: Facts) -> list[dict]:  # info: def work_orders
    rows = []  # info: set rows
    for p in sorted((DOCS / "06-Development" / "Work-Orders").glob("*.md")):  # info: for p in sorted ( ( DOCS /
        if p.name == "README.md":  # info: if p . name == "README.md" :
            continue  # info: continue
        txt = read(p)  # info: set txt
        st = re.search(r"^\|\s*\*\*Status\*\*\s*\|\s*(.+?)\s*\|", txt, re.M)  # info: set st
        rows.append({"file": p.stem, "status": cell((st.group(1) if st else "not recorded").replace("**", ""), 80)})  # info: rows . append ( { "file" : p
        f.add(p.stem, st.group(0) if st else "")  # info: f . add ( p . stem ,
    return rows  # info: return rows


# ====================================================
# SECTION: function inference
# What it does: inference.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def inference(f: Facts) -> dict:  # info: def inference
    files = [DB / "Logs" / "AI" / "Inference" / "Archive" / f"inference_{f.day}.jsonl", INFER_LOG]  # info: set files
    rows = []  # info: set rows
    for p in files:  # info: for p in files :
        for ln in read(p).splitlines():  # info: for ln in read ( p ) .
            try:  # info: try :
                r = json.loads(ln)  # info: set r
                ts = datetime.fromisoformat(r["ts"])  # info: set ts
            except Exception:  # info: except Exception :
                continue  # info: continue
            if ts.astimezone().strftime("%Y-%m-%d") == f.day:  # info: if ts . astimezone ( ) . strftime
                r["_ts"] = ts  # info: r [ "_ts" ] = ts
                rows.append(r)  # info: rows . append ( r )
                f.add(ln)  # info: f . add ( ln )
    rows.sort(key=lambda r: r["_ts"])  # info: rows . sort ( key = lambda r
    lat = [r.get("latency_ms", 0) for r in rows]  # info: set lat
    s = {"rows": rows, "n": len(rows), "fallbacks": sum(1 for r in rows if r.get("fallback")),  # info: set s
         "nonzero": sum(1 for r in rows if r.get("exit_code")), "p50": int(statistics.median(lat)) if lat else None,  # info: "nonzero" : sum ( 1 for r in
         "max": max(lat) if lat else None,  # info: "max" : max ( lat ) if lat
         "min_mem": min((r.get("mem_avail_mb_after") for r in rows if r.get("mem_avail_mb_after")), default=None),  # info: "min_mem" : min ( ( r . get
         "routes": sorted({r.get("route", "?") for r in rows})}  # info: "routes" : sorted ( { r . get
    f.add(s["n"], s["fallbacks"], s["nonzero"], s["p50"], s["max"], s["min_mem"])  # info: f . add ( s [ "n" ]
    return s  # info: return s


# ====================================================
# SECTION: function poller
# What it does: poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poller(f: Facts) -> dict:  # info: def poller
    lines = []  # info: set lines
    arch = sorted((DB / "Logs" / "Automations" / "Archive").glob(f"automations_{f.day}_*.log"))  # info: set arch
    for p in arch + [POLLER_LOG]:  # info: for p in arch + [ POLLER_LOG ]
        lines += [ln for ln in read(p).splitlines() if ln.startswith(f.day)]  # info: set lines
    fails = []  # info: set fails
    for ln in lines:  # info: for ln in lines :
        m = re.match(r"^(\S+?)job:(\S+) FAIL(.*)$", ln)  # info: set m
        if m:  # info: if m :
            fails.append({"time": m.group(1)[11:16], "job": m.group(2), "detail": m.group(3).strip()})  # info: fails . append ( { "time" : m
            f.add(ln)  # info: f . add ( ln )
    runs = sum(1 for ln in lines if re.search(r"job:\S+ RUN ", ln))  # info: set runs
    tunnel = [ln for ln in lines if ln[25:].startswith("tunnel ")]  # info: set tunnel
    gh = [ln for ln in lines if "job:github_sync_all" in ln]  # info: set gh
    gh_last = gh[-1] if gh else ""  # info: set gh_last
    gh_bad = any(re.search(r"FAIL|error|fatal|rejected", ln, re.I) for ln in gh[-12:])  # info: set gh_bad
    s = {"lines": len(lines), "runs": runs, "fails": fails, "gh_last_time": gh_last[11:16] if gh_last else None, "gh_bad": gh_bad,  # info: set s
         "last_time": lines[-1][11:16] if lines else None, "tunnel": tunnel}  # info: "last_time" : lines [ - 1 ] [
    f.add(s["lines"], s["runs"], s["gh_last_time"], s["last_time"])  # info: f . add ( s [ "lines" ]
    return s  # info: return s


# ====================================================
# SECTION: function host
# What it does: host.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host(f: Facts) -> dict:  # info: def host
    try:  # info: try :
        d = json.loads(read(DB / "System" / "last" / "host_current.json"))  # info: set d
        fl = d.get("fields", {})  # info: set fl
        obs = d.get("observed_at") or d.get("generated_at")  # info: set obs
        at = datetime.fromisoformat(obs.replace("Z", "+00:00")).astimezone() if obs else None  # info: set at
        s = {"at": at, "load1": fl.get("load1", {}).get("value"), "cpu": fl.get("cpu_percent", {}).get("value"),  # info: set s
             "mem_avail_mb": int(fl["mem_available_bytes"]["value"] / 1048576) if "mem_available_bytes" in fl else None}  # info: "mem_avail_mb" : int ( fl [ "mem_available_bytes" ]
    except Exception:  # info: except Exception :
        s = {"at": None, "load1": None, "cpu": None, "mem_avail_mb": None}  # info: set s
    if s["at"] is None:  # fall back to file mtime
        s["at"] = newest_mtime(DB / "System" / "last", "*.json")  # info: s [ "at" ] = newest_mtime ( DB
    f.add(s["load1"], s["cpu"], s["mem_avail_mb"], hm(s["at"]) if s["at"] else "")  # info: f . add ( s [ "load1" ]
    return s  # info: return s


# ====================================================
# SECTION: function energy
# What it does: energy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def energy(f: Facts) -> list[dict]:  # info: def energy
    out = []  # info: set out
    for p in sorted((DB / "Energy" / "soc").glob("*-last.json")):  # info: for p in sorted ( ( DB /
        try:  # info: try :
            d = json.loads(read(p))  # info: set d
            out.append({"pack": p.name.replace("-last.json", ""), "soc": d.get("soc"), "at": datetime.fromisoformat(d["at"]), "source": d.get("source")})  # info: out . append ( { "pack" : p
            f.add(read(p), hm(datetime.fromisoformat(d["at"])))  # info: f . add ( read ( p )
        except Exception:  # info: except Exception :
            continue  # info: continue
    return out  # info: return out


# ====================================================
# SECTION: function energy_periods
# What it does: Quote the hour, day, week, and month lines from Energy/layers/periods.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def energy_periods(f: Facts) -> list[str]:  # info: def energy_periods
    if str(PACIFIC) not in sys.path:  # info: if str ( PACIFIC ) not in sys . path
        sys.path.insert(0, str(PACIFIC))  # info: sys . path . insert ( 0 , str ( PACIFIC ) )
    from Energy.db.report_json import REPORT_JSON, period_lines  # info: from Energy . db . report_json import REPORT_JSON
    try:  # info: try
        doc = json.loads(REPORT_JSON.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return []  # info: return [ ]
    lines = period_lines(doc)  # info: set lines
    f.add(*lines)  # info: f . add the period lines
    return lines  # info: return lines


# ====================================================
# SECTION: function state_by_age
# What it does: state by age.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def state_by_age(age: float | None, ok_min: float, degraded_min: float) -> str:  # info: def state_by_age
    if age is None:  # info: if age is None :
        return "down"  # info: return "down"
    return "ok" if age <= ok_min else ("degraded" if age <= degraded_min else "down")  # info: return "ok" if age <= ok_min else (


# ====================================================
# SECTION: function subsystems
# What it does: subsystems.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def subsystems(f: Facts, h: dict, en: list, pl: dict) -> list[tuple[str, str, str]]:  # info: def subsystems
    t = f.t  # info: set t
    rows = []  # info: set rows
    a = age_min(h["at"], t)  # info: set a
    rows.append(("System / telemetry", state_by_age(a, 15, 360), f"`System/last/host_current.json` sample {hm(h['at'])} HST" if h["at"] else "no sample found"))  # info: rows . append ( ( "System / telemetry" , state_by_age
    wl = newest_mtime(DB / "Worklog", "worklog_current.md")  # info: set wl
    rows.append(("Worklog scan", state_by_age(age_min(wl, t), 30, 360), f"`Worklog/worklog_current.md` updated {hm(wl)} HST" if wl else "no worklog file"))  # info: rows . append ( ( "Worklog scan" , state_by_age
    try:  # info: try :
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=2) as r:  # info: with urllib . request . urlopen ( "http://127.0.0.1:11434/api/ps"
            loaded = len(json.loads(r.read().decode()).get("models", []))  # info: set loaded
        oll = ("ok", f"`ollama.service` API up; {loaded} model(s) resident")  # info: set oll
    except Exception:  # info: except Exception :
        oll = ("down", "API not reachable on 127.0.0.1:11434")  # info: set oll
    rows.append(("Ollama",) + oll)  # info: rows . append ( ( "Ollama" , )
    ea = [age_min(e["at"], t) for e in en]  # info: set ea
    rows.append(("EcoFlow BLE", state_by_age(min(ea) if ea else None, 15, 360),  # info: rows . append ( ( "EcoFlow BLE" , state_by_age
                 "; ".join(f"{e['pack']} read {hm(e['at'])} HST ({e['source']})" for e in en) or "no SOC file"))  # info: "; " . join ( f" { e [
    im = newest_mtime(DB / "Media" / "Images", "*.jpg")  # info: set im
    rows.append(("A-EYES", state_by_age(age_min(im, t), 30, 360), f"newest still in `Media/Images/` {hm(im)} HST" if im else "no still found"))  # info: rows . append ( ( "A-EYES" , state_by_age
    wr = newest_mtime(DB / "Weather" / "Hawai'i" / "reports" / "1 County Processing", "*_current.md")  # info: set wr
    rows.append(("Weather", state_by_age(age_min(wr, t), 180, 720), f"county reports updated {hm(wr)} HST" if wr else "no county report found"))  # info: rows . append ( ( "Weather" , state_by_age
    gh = "degraded" if pl["gh_bad"] else ("ok" if pl["gh_last_time"] else "down")  # info: set gh
    rows.append(("GitHub sync", gh, f"last `github_sync_all` line {pl['gh_last_time']} HST" if pl["gh_last_time"] else "no github_sync_all line today"))  # info: rows . append ( ( "GitHub sync" , gh
    cf = procs_by_comm("cloudflared")  # info: set cf
    tun = [ln for ln in pl.get("tunnel", []) if "connected" in ln or "timeout" in ln]  # info: set tun
    last = tun[-1] if tun else ""  # info: set last
    cf_state = "down" if not cf else ("degraded" if "timeout" in last else "ok")  # info: set cf_state
    rows.append(("Cloudflare tunnel", cf_state, f"{cf} cloudflared process(es)" + (f"; last tunnel line {last[11:16]} HST: {last[25:].strip()}" if last else "")))  # info: rows . append ( ( "Cloudflare tunnel" , cf_state
    for r in rows:  # info: for r in rows :
        f.add(r[2])  # info: f . add ( r [ 2 ]
    return rows  # info: return rows


# ------------------------------------------------------------------ free text (specialist)
# ====================================================
# SECTION: function draft
# What it does: keys: {KEY: instruction}. Returns {KEY: text}; falls back to '' (caller substitutes deterministic text).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def draft(keys: dict[str, str], facts_lines: list[str], mode: str, f: Facts, log: dict, checks: dict | None = None) -> dict[str, str]:  # info: def draft
    """keys: {KEY: instruction}. Returns {KEY: text}; falls back to '' (caller substitutes deterministic text)."""  # info: """keys: {KEY: instruction}. Returns {KEY: text}; falls back to '' (caller substitutes deterministic text)."""
    out = {k: "" for k in keys}  # info: set out
    log.update({"draft_mode": mode, "model_called": False})  # info: log . update ( { "draft_mode" : mode
    if mode == "none":  # info: if mode == "none" :
        return out  # info: return out
    mem = mem_avail_mb()  # info: set mem
    try:  # info: try :
        idle = subprocess.run([str(SF), "status"], capture_output=True, text=True, timeout=5).stdout.startswith("IDLE")  # info: set idle
    except Exception:  # info: except Exception :
        idle = False  # info: set idle
    log.update({"mem_avail_mb_before": mem, "lock_idle": idle})  # info: log . update ( { "mem_avail_mb_before" : mem
    if mem < MIN_MEM_MB_FOR_MODEL or not idle:  # info: if mem < MIN_MEM_MB_FOR_MODEL or not idle :
        log["skip_reason"] = "low memory" if mem < MIN_MEM_MB_FOR_MODEL else "single-flight busy"  # info: log [ "skip_reason" ] = "low memory" if mem
        return out  # info: return out
    facts = "\n".join("- " + cell(x, 200) for x in facts_lines[:30])  # info: set facts
    prompt = ("Use ONLY the facts below. Do not add any number, name, path, date or claim that is not in the facts. "  # info: set prompt
              "If the facts do not support a field, write: No data.\n"  # info: "If the facts do not support a field, write: No data.\n"
              "Reply with exactly these lines and nothing else:\n"  # info: "Reply with exactly these lines and nothing else:\n"
              + "\n".join(f"{k}: <{v}>" for k, v in keys.items()) + "\n\nFACTS:\n" + facts)  # info: + "\n" . join ( f" { k
    env = {k: v for k, v in os.environ.items() if k != "DESK_LIVE_FILE"}  # info: set env
    env["RR_CALLER"] = "template_fill"  # info: env [ "RR_CALLER" ] = "template_fill"
    desk = None  # info: set desk
    if os.environ.get("RR_TEMPLATE_SPECIALIST_HOOK", "1") == "1":  # explicit specialist via the run-infer.sh hook (FLM gets its SYSTEM)
        env.update({"RR_SPECIALIST_ROUTING": "1", "RR_SPECIALIST": SPECIALIST})  # info: env . update ( { "RR_SPECIALIST_ROUTING" : "1"
        # v3 (2026-09-29): the same facts as a temporary desk file, so the specialist's DATA GATE sees measured lines
        # ("[desk: measured — cite only these lines]") instead of answering "No data". Deleted right after the call.
        fd, desk = tempfile.mkstemp(prefix="rr-template-desk-", suffix=".txt", dir=os.environ.get("XDG_RUNTIME_DIR") or None)  # info: fd , desk = tempfile . mkstemp (
        with os.fdopen(fd, "w", encoding="utf-8") as fh:  # info: with os . fdopen ( fd , "w"
            fh.write("".join("- " + cell(x, 200) + "\n" for x in facts_lines[:30]))  # info: fh . write ( "" . join (
        env["DESK_LIVE_FILE"] = desk  # info: env [ "DESK_LIVE_FILE" ] = desk
        prompt = (prompt.split("\n\nFACTS:\n")[0] + "\n\nFACTS: the measured desk lines above.\n"  # info: set prompt
                  "Do not repeat any rules or headers. Answer now with only the " + " and ".join(f"{k}:" for k in keys) + " lines.")  # info: "Do not repeat any rules or headers. Answer now with only the " + " and " . join ( f" {
        log["desk_file_lines"] = min(len(facts_lines), 30)  # info: log [ "desk_file_lines" ] = min ( len
    t0 = now()  # info: set t0
    try:  # info: try :
        r = subprocess.run(["nice", "-n", "10", str(RUN_INFER), SPECIALIST, prompt], capture_output=True, text=True, timeout=180, env=env)  # info: set r
        reply = "\n".join(ln for ln in r.stdout.splitlines() if not re.match(r"^\[(ok|warn|busy|fail)\]", ln))  # info: set reply
        log.update({"model_called": True, "rc": r.returncode, "latency_ms": int((now() - t0).total_seconds() * 1000),  # info: log . update ( { "model_called" : True
                    "reply_chars": len(reply), "mem_avail_mb_after": mem_avail_mb(),  # info: "reply_chars" : len ( reply ) , "mem_avail_mb_after"
                    "backend": "npu-flm" if "FLM/NPU" in r.stderr else ("ollama" if "Ollama" in r.stderr else "unknown")})  # info: "backend" : "npu-flm" if "FLM/NPU" in r .
    except Exception as e:  # info: except Exception as e :
        log.update({"model_called": True, "error": type(e).__name__})  # info: log . update ( { "model_called" : True
        return out  # info: return out
    finally:  # info: finally :
        if desk:  # info: if desk :
            try:  # info: try :
                os.unlink(desk)  # info: os . unlink ( desk )
            except OSError:  # info: except OSError :
                pass  # info: pass
    allowed = tv.corpus_numbers("\n".join(facts_lines) + "\n" + f.day)  # info: set allowed
    accepted = {}  # info: set accepted
    for k in keys:  # info: for k in keys :
        m = re.search(rf"^[\s>*#\-\d.)]*\**{k}\**\s*\**\s*[:\-—]\s*\**\s*(.*?)\s*$(?:\n\s*([^\n:]+?)\s*$)?", reply, re.M | re.I)
        v = ((m.group(1) or (m.group(2) or "")) if m else "").strip().strip("<>*\"").strip()  # info: set v
        failed_check = False  # info: set failed_check
        if v and checks and k in checks:  # info: if v and checks and k in checks
            v2 = checks[k](v) or ""  # info: set v2
            failed_check, v = (not v2), v2  # info: failed_check , v = ( not v2 )
        bad = [t for t in tv.number_tokens(v) if not tv.number_ok(t, allowed)]  # info: set bad
        if v and len(v) <= 300 and "{{" not in v and not bad and not re.fullmatch(r"(?i)no data\.?", v):  # info: if v and len ( v ) <=
            out[k] = v.rstrip()  # info: out [ k ] = v . rstrip
            accepted[k] = "model"  # info: accepted [ k ] = "model"
        else:  # info: else :
            accepted[k] = "fallback" + (f" (unsupported numbers {bad})" if bad else (" (failed field check)" if failed_check else (" (missing)" if not v else " (rejected)")))  # info: accepted [ k ] = "fallback" + (
    log["fields"] = accepted  # info: log [ "fields" ] = accepted
    log["reply_preview"] = cell(reply, 300)  # info: log [ "reply_preview" ] = cell ( reply
    if reply.strip() == "No live desk data attached.":  # run-infer.sh sanitize() replaced a reply that echoed DESK_LIVE:/rules
        log["sanitized_by_run_infer"] = True  # info: log [ "sanitized_by_run_infer" ] = True
    return out  # info: return out


# ------------------------------------------------------------------ template helpers
# ====================================================
# SECTION: function tpl
# What it does: tpl.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tpl(name: str) -> str:  # info: def tpl
    return read(TPL_DIR / name)  # info: return read ( TPL_DIR / name )


# ====================================================
# SECTION: function section_verbatim
# What it does: Copy a template section (from heading to the next '---' or EOF) verbatim with placeholder subs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def section_verbatim(t: str, heading: str, subs: dict[str, str]) -> str:  # info: def section_verbatim
    """Copy a template section (from heading to the next '---' or EOF) verbatim with placeholder subs."""  # info: """Copy a template section (from heading to the next '---' or EOF) verbatim with placeholder subs."""
    i = t.index(heading)  # info: set i
    j = t.find("\n---\n", i)  # info: set j
    body = t[i:] if j < 0 else t[i:j]  # info: set body
    for k, v in subs.items():  # info: for k , v in subs . items
        body = body.replace(k, v)  # info: set body
    return body.rstrip("\n")  # info: return body . rstrip ( "\n" )


# ------------------------------------------------------------------ renderers
# ====================================================
# SECTION: function render_worklog
# What it does: render worklog.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_worklog(f: Facts, mode: str, log: dict) -> str:  # info: def render_worklog
    t = tpl("TEMPLATE System Operator Worklog — Session.md")  # info: set t
    tr, inf, pl, so = testing_records(f), inference(f), poller(f), signoff_items(f)  # info: tr , inf , pl , so =
    ev = [(r["time"], f"Testing record: {cell(r['title'], 80)} — {cell(r['state'], 60)}") for r in tr]  # info: set ev
    ev += [(x["time"], f"Poller job `{x['job']}` FAIL {x['detail']}".strip()) for x in pl["fails"]]  # info: set ev
    for r in inf["rows"]:  # info: for r in inf [ "rows" ] :
        if r.get("exit_code") or r.get("fallback"):  # info: if r . get ( "exit_code" ) or
            ev.append((hm(r["_ts"]), f"Inference {r.get('route')} `{r.get('model')}` rc {r.get('exit_code')}, fallback {str(r.get('fallback')).lower()}"))  # info: ev . append ( ( hm ( r
    ev.sort(key=lambda e: e[0].lstrip("~"))  # info: ev . sort ( key = lambda e
    live = f.day == f.t.strftime("%Y-%m-%d")  # info: set live
    w0 = ev[0][0].lstrip("~") if ev else hm(f.t)  # info: set w0
    w1 = hm(f.t) if live else (ev[-1][0].lstrip("~") if ev else hm(f.t))  # info: set w1
    facts = [f"date {f.day}", f"{len(tr)} testing records today", f"{sum(1 for r in tr if r['state'].startswith('PASS'))} testing records PASS",  # info: set facts
             f"{inf['n']} inference requests, {inf['fallbacks']} fallbacks, {inf['nonzero']} non-zero exit codes",  # info: f" { inf [ 'n' ] } inference requests,
             f"{len(pl['fails'])} poller job FAIL lines today", f"poller unit {is_active('rr-rootserver-poller.service')}"]  # info: f" { len ( pl [ 'fails' ]
    facts += [f"sign-off needed: {s}" for s in so[:6]]  # info: set facts
    def pick_signoff(v: str) -> str:  # NEXT must name a real sign-off item; never an unqualified instruction
        for s_ in so:  # info: for s_ in so :
            core = re.sub(r"[`*:]", "", s_).lower().split(" — ")[0][:24]  # info: set core
            if core and core in re.sub(r"[`*:]", "", v).lower():  # info: if core and core in re . sub
                return f"Alexander sign-off: {s_}"  # info: return f" Alexander sign-off: { s_ } "
        return ""  # info: return ""
    d = draft({"PURPOSE": "one or two sentences: what this digest covers", "NEXT": "copy one item from the sign-off list",  # info: set d
               "STATUS": "one short line summarising the day"}, facts, mode, f, log, {"NEXT": pick_signoff})  # info: "STATUS" : "one short line summarising the day" } , facts , mode
    purpose = d["PURPOSE"] or f"Automated digest of desk activity on {f.day}, built from testing records, the AI inference log, poller logs and the operator worklog."  # info: set purpose
    nxt = d["NEXT"] or (f"Alexander sign-off: {so[0]}" if so else "Review this digest.")  # info: set nxt
    status = d["STATUS"] or f"{'ACTIVE' if live else 'CLOSED'} — {len(tr)} testing records, {inf['n']} inference requests, {len(pl['fails'])} poller FAIL lines."  # info: set status
    L = [f"# System Operator Worklogs — Session {f.session}", "",
         f"**Date:** {f.day}  ", "**Session:** Automated digest (template_fill.py)  ", "**Timezone:** HST  ",  # info: f" **Date:** { f . day }
         f"**Window:** {w0}–{w1} HST  ", f"**Status:** {'ACTIVE' if live else 'CLOSED'}  ", "**Operator:** RootRecord", "", "---", "",  # info: f" **Window:** { w0 } – { w1
         "## Purpose", "", purpose, "",
         "This is a manual operator worklog (not a full architecture redesign). Record what was actually done.", "", "---", "",  # info: "This is a manual operator worklog (not a full architecture redesign). Record what was actually done." , "" , 
         f"## Approximate timetable ({f.day} HST)", "", "| Time (approx.) | Event |", "| --- | --- |"]
    L += [f"| {a} | {cell(b, 140)} |" for a, b in ev] or [f"| {hm(f.t)} | No recorded events in the sources |"]  # info: set L
    L += ["", "---", "", "## Completed this session", "", "### Testing records", ""]
    L += [f"- [{'x' if r['state'].startswith('PASS') else ' '}] {cell(r['title'], 90)} — {cell(r['state'], 70)}" for r in tr] or ["- [ ] No testing records for this date"]  # info: set L
    L += ["", "### AI inference and poller", ""]
    L += [f"- [{'x' if inf['n'] else ' '}] {inf['n']} inference requests (routes: {', '.join(inf['routes']) or 'none'}); p50 {inf['p50'] if inf['p50'] is not None else 'not recorded'} ms, max {inf['max'] if inf['max'] is not None else 'not recorded'} ms",  # info: set L
          f"- [{'x' if not inf['fallbacks'] else ' '}] Ollama fallbacks: {inf['fallbacks']}; non-zero exit codes: {inf['nonzero']}",  # info: f" - [ { 'x' if not inf [
          f"- [{'x' if not pl['fails'] else ' '}] Poller log: {pl['runs']} job runs, {len(pl['fails'])} FAIL lines"]  # info: f" - [ { 'x' if not pl [
    L += ["", "### Explicit non-goals", "", "- Automation does not restart services, use sudo, send messages or write into the Library.",
          "- Decisions and sign-offs stay with the operator; this digest only aggregates sources.", "", "---", "",  # info: "- Decisions and sign-offs stay with the operator; this digest only aggregates sources." , "" , "---" , "" ,
          "## Blockers / residual items", "", "| Item | Notes |", "| --- | --- |"]
    L += [f"| {cell(s, 90)} | Needs Alexander sign-off (operator worklog) |" for s in so] or ["| None recorded | Operator worklog has no open sign-off items |"]  # info: set L
    L += ["", "---", "", "## Decisions (if any)", "", "> No decisions are recorded by automation.", "",
          "Rationale: decisions come from the operator; this digest only aggregates measured sources.", "", "---", "",  # info: "Rationale: decisions come from the operator; this digest only aggregates measured sources." , "" , "---" , ""
          f"## State at session close (~{hm(f.t)} HST)", "",
          f"- **Runtime:** poller `{is_active('rr-rootserver-poller.service')}`; BLE `{is_active('ava-ecoflow-ble.service')}`; last poller log line {pl['last_time'] or 'none'} HST",  # info: f" - **Runtime:** poller ` { is_active ( 'rr-rootserver-poller.service' ) }
          f"- **Library / docs:** {len(tr)} testing records dated {f.day} in the 07-Testing index",  # info: f" - **Library / docs:** { len ( tr ) }
          f"- **GitHub / sync:** {'issues in recent github_sync_all lines' if pl['gh_bad'] else ('ok (last github_sync_all line ' + pl['gh_last_time'] + ' HST)' if pl['gh_last_time'] else 'no github_sync_all line today')}",  # info: f" - **GitHub / sync:** { 'issues in recent github_sync_all lines' if pl [ 'gh_bad'
          f"- **Next useful step:** {nxt}", "", f"**Status:** {status}", "", "---", ""]  # info: f" - **Next useful step:** { nxt } " , ""
    L.append(section_verbatim(t, "## Archive note", {"{{YYYY-MM-DD}}": f.day, "{{SESSION_NN}}": f.session}))
    f.add(*facts, purpose, nxt, status)  # info: f . add ( * facts , purpose
    return "\n".join(L) + "\n"  # info: return "\n" . join ( L ) +


# ====================================================
# SECTION: function render_checkpoint
# What it does: render checkpoint.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_checkpoint(f: Facts, mode: str, log: dict) -> str:  # info: def render_checkpoint
    t = tpl("TEMPLATE RootRecord Checkpoint.md")  # info: set t
    h, en, pl, so, idl = host(f), energy(f), poller(f), signoff_items(f), ideas(f)  # info: h , en , pl , so ,
    subs = subsystems(f, h, en, pl)  # info: set subs
    pa = is_active("rr-rootserver-poller.service")  # info: set pa
    poller_state = "active" if pa == "active" else ("inactive" if pa in ("inactive", "failed") else "unknown")  # info: set poller_state
    dash = procs_matching(lambda c: "poller-dashboard.py" in c)  # info: set dash
    verified = [f"Host sample {hm(h['at'])} HST: load1 {h['load1']}, CPU {h['cpu']}%, MemAvailable {h['mem_avail_mb']} MB" if h["at"] else "Host sample: not found"]  # info: set verified
    verified += [f"{e['pack']} SOC {e['soc']}% at {hm(e['at'])} HST ({e['source']})" for e in en]  # info: set verified
    periods = energy_periods(f)  # info: set periods
    verified += periods  # info: verified includes the closed hour, day, week, and month
    verified += [f"{n}: {s} — {note}" for n, s, note in subs]  # info: set verified
    deferred = [f"{cell(r['title'], 80)} — {cell(r['state'], 60)}" for r in idl if "PROPOSED" in r["state"]] or ["None recorded in 08-Ideas"]  # info: set deferred
    facts = [f"poller {poller_state}", f"{sum(1 for s in subs if s[1] == 'ok')} of {len(subs)} subsystems ok"] + \
            [f"{n} {s}" for n, s, _ in subs] + periods + [f"sign-off needed: {s}" for s in so[:4]]  # info: [ f" { n } { s
    d = draft({"PRINCIPLE": "one short operating principle grounded in the facts", "STATUS": "one short status line"}, facts, mode, f, log)  # info: set d
    principle = d["PRINCIPLE"] or "Measured or explicitly unknown: record what the sources show and change nothing without operator approval."  # info: set principle
    ok_n = sum(1 for s in subs if s[1] == "ok")  # info: set ok_n
    status = d["STATUS"] or f"{ok_n} of {len(subs)} subsystems ok; poller {poller_state}; {len(so)} sign-off items open."  # info: set status
    L = [f"# RootRecord Checkpoint — {f.day} {hm(f.t)} HST", "", "## Checkpoint Purpose", "",
         f"Snapshot of Pacific RootRecord state at **{hm(f.t)} HST** on **{f.day}**.", "",  # info: f" Snapshot of Pacific RootRecord state at ** { hm ( f . t
         "This checkpoint records what was verified and what remains intentionally deferred. It does not retroactively rewrite earlier logs.",  # info: "This checkpoint records what was verified and what remains intentionally deferred. It does not retroactively 
         "", "---", "", "## Current State", "", "### Runtime", "",
         f"- Poller: {poller_state} — `rr-rootserver-poller.service`",  # info: f" - Poller: { poller_state } — `rr-rootserver-poller.service` " ,
         f"- HTTP listener: {'127.0.0.1:8799' if port_open(8799) else 'N/A'}",  # info: f" - HTTP listener: { '127.0.0.1:8799' if port_open ( 8799
         f"- Poller log: `{POLLER_LOG}`",  # info: f" - Poller log: ` { POLLER_LOG } ` " ,
         f"- Pretty poller: {'manual' if dash else 'not running'}", "", "### Core subsystems", "",
         "| Subsystem | Status | Notes |", "| --- | --- | --- |"]  # info: "| Subsystem | Status | Notes |" , "| --- | --- | --- |" ]
    L += [f"| {n} | {s} | {cell(note, 120)} |" for n, s, note in subs]  # info: set L
    L += ["", "### Services (user systemd)", "", "| Unit | State |", "| --- | --- |"]
    for u in ("rr-rootserver-poller.service", "ava-ecoflow-ble.service", "network-globe-hawaii.service"):  # info: for u in ( "rr-rootserver-poller.service" , "ava-ecoflow-ble.service" ,
        L.append(f"| `{u}` | {'active' if is_active(u) == 'active' else 'inactive'} |")  # info: L . append ( f" | ` { u
    L += ["", "---", "", "## Verified this checkpoint", ""] + [f"- {cell(v, 160)}" for v in verified]
    L += ["", "---", "", "## Intentionally deferred", ""] + [f"- {v}" for v in deferred]
    L += ["", "---", "", "## Blockers", "", "| Blocker | Owner | Next step |", "| --- | --- | --- |"]
    L += [f"| {cell(s, 90)} | Alexander | Sign-off (operator worklog) |" for s in so] or ["| None recorded | — | — |"]  # info: set L
    L += ["", "---", "", "## Operating principle at checkpoint", "", principle, "", "---", "", "## Checkpoint time", "",
          f"**{f.day} {hm(f.t)} HST**", "", f"**Status:** {status}", "", "---", ""]  # info: f" ** { f . day }
    L.append(section_verbatim(t, "## Archive note", {"{{YYYY-MM-DD}}": f.day, "{{HH_MM}}": f.t.strftime("%H_%M")}))
    f.add(*verified, *deferred, principle, status, str(POLLER_LOG))  # info: f . add ( * verified , *
    return "\n".join(L) + "\n"  # info: return "\n" . join ( L ) +


# ====================================================
# SECTION: function render_event
# What it does: render event.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_event(f: Facts, mode: str, log: dict) -> str:  # info: def render_event
    t = tpl("TEMPLATE Event Action Log.md")  # info: set t
    inf = inference(f)  # info: set inf
    title = "AI Inference Activity Log"  # info: set title
    live = f.day == f.t.strftime("%Y-%m-%d")  # info: set live
    tl = []  # info: set tl
    if len(inf["rows"]) <= 30:  # info: if len ( inf [ "rows" ] )
        for r in inf["rows"]:  # info: for r in inf [ "rows" ] :
            tl.append(f"{hm(r['_ts'])} — {r.get('route')} `{r.get('model')}` for {r.get('target')} (caller {r.get('caller')}): "  # info: tl . append ( f" { hm (
                      f"{r.get('latency_ms')} ms, rc {r.get('exit_code')}{', cold start' if r.get('flm_cold_start') else ''}{', Ollama fallback' if r.get('fallback') else ''}")  # info: f" { r . get ( 'latency_ms' )
    else:  # aggregate per hour; approximate marker per template
        by = {}  # info: set by
        for r in inf["rows"]:  # info: for r in inf [ "rows" ] :
            by.setdefault(r["_ts"].strftime("%H"), []).append(r)  # info: by . setdefault ( r [ "_ts" ]
        for hh, rs in sorted(by.items()):  # info: for hh , rs in sorted ( by
            tl.append(f"~{hh}:00 — {len(rs)} requests; max {max(x.get('latency_ms', 0) for x in rs)} ms; {sum(1 for x in rs if x.get('fallback'))} fallbacks")  # info: tl . append ( f" ~ { hh
            f.add(len(rs), max(x.get('latency_ms', 0) for x in rs))  # info: f . add ( len ( rs )
    facts = [f"{inf['n']} inference requests on {f.day}", f"routes {', '.join(inf['routes']) or 'none'}",  # info: set facts
             f"p50 latency {inf['p50']} ms, max {inf['max']} ms", f"{inf['fallbacks']} Ollama fallbacks", f"{inf['nonzero']} non-zero exit codes",  # info: f" p50 latency { inf [ 'p50' ] }
             f"lowest MemAvailable after a request {inf['min_mem']} MB"]  # info: f" lowest MemAvailable after a request { inf [ 'min_mem' ] }
    d = draft({"SCOPE": "one line: what this log covers", "STATUS": "one short close status line"}, facts, mode, f, log)  # info: set d
    scope = d["SCOPE"] or f"Inference requests recorded by run-infer.sh on {f.day} (metadata only, no prompt text)."  # info: set scope
    status = d["STATUS"] or f"{inf['n']} requests, {inf['fallbacks']} fallbacks, {inf['nonzero']} non-zero exit codes."  # info: set status
    L = [f"# {title}", "", f"**Date:** {f.day}  ", f"**Scope:** {scope}  ", "**Timezone:** HST  ",
         f"**Status:** {'IN PROGRESS' if live else 'CLOSED'}", "", "---", "", "## Timeline", ""]
    for x in tl or [f"{hm(f.t)} — No inference requests recorded for this date"]:  # info: for x in tl or [ f" {
        L += [x, ""]  # info: set L
    L += ["---", "", "## Outcomes", "",
          f"- {inf['n']} requests; p50 {inf['p50'] if inf['p50'] is not None else 'not recorded'} ms, max {inf['max'] if inf['max'] is not None else 'not recorded'} ms",  # info: f" - { inf [ 'n' ] }
          f"- {inf['fallbacks']} Ollama fallbacks, {inf['nonzero']} non-zero exit codes; lowest MemAvailable after a request {inf['min_mem'] if inf['min_mem'] is not None else 'not recorded'} MB",  # info: f" - { inf [ 'fallbacks' ] }
          "", "---", "", "## Artifacts / paths", "", "| Path or artifact | Role |", "| --- | --- |",
          f"| `{INFER_LOG}` | Inference JSONL (metadata only) |",  # info: f" | ` { INFER_LOG } ` | Inference JSONL (metadata only) | " ,
          "| `System/scripts/plumbing/run-infer.sh` | Writes one line per request |", "", "---", ""]  # info: "| `System/scripts/plumbing/run-infer.sh` | Writes one line per request |" , "" , "---" , "" ]
    L.append(section_verbatim(t, "## Notes", {}))
    L += ["", "---", "", "## Close", "", f"**Closed:** {f.day} {hm(f.t)} HST  ", f"**Status:** {status}", "", "---", ""]
    L.append(section_verbatim(t, "## Archive note", {"{{YYYY-MM-DD}} {{EVENT_TITLE}}.md": f"{f.day} {title}.md"}))
    f.add(*tl, *facts, scope, status, str(INFER_LOG))  # info: f . add ( * tl , *
    return "\n".join(L) + "\n"  # info: return "\n" . join ( L ) +


# ====================================================
# SECTION: function render_workorder
# What it does: render workorder.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_workorder(f: Facts, mode: str, log: dict) -> str:  # info: def render_workorder
    t = tpl("TEMPLATE Work Order.md")  # info: set t
    tr, wos, so, inf, pl = testing_records(f), work_orders(f), signoff_items(f), inference(f), poller(f)  # info: tr , wos , so , inf ,
    code, short = "GEN", "Desk_Signoff_Backlog"  # info: code , short = "GEN" , "Desk_Signoff_Backlog"
    friction = [f"{cell(r['title'], 80)} — {cell(r['state'], 60)}" for r in tr if re.search(r"FAIL|BLOCKED|VERIFY PENDING", r["state"])]  # info: set friction
    friction += [f"Poller job `{x['job']}` FAIL at {x['time']} HST" for x in pl["fails"]]  # info: set friction
    if inf["fallbacks"] or inf["nonzero"]:  # info: if inf [ "fallbacks" ] or inf [
        friction.append(f"Inference: {inf['fallbacks']} Ollama fallbacks, {inf['nonzero']} non-zero exit codes")  # info: friction . append ( f" Inference: { inf
    facts = [f"{len(so)} operator sign-off items open"] + [f"sign-off: {s}" for s in so[:6]] + \
            [f"{len(friction)} friction items from testing records and logs", f"{len(wos)} work orders in the Library index folder"]  # info: [ f" { len ( friction ) }
    d = draft({"INTENT": "one or two sentences: why this backlog work order exists", "SCOPE": "one sentence: what is in and out of scope"}, facts, mode, f, log)  # info: set d
    intent = d["INTENT"] or "Collect the open operator sign-off items and measured friction for the day in one place, so they can be accepted or closed deliberately."  # info: set intent
    scope = d["SCOPE"] or "In scope: the listed sign-off items and friction from today's sources. Not in scope: executing any of them; this is a generated draft."  # info: set scope
    L = ["# WORK ORDER — Desk Sign-off Backlog (generated draft)", "", "| Field | Value |", "| --- | --- |",
         f"| **Work Order ID** | WO-{code}-{f.day} |", f"| **Date** | {f.day} (HST) |",  # info: f" | **Work Order ID** | WO- { code } - { f
         "| **Status** | OPEN — generated draft, not on the active index |", "| **Owner** | RootRecord |",  # info: "| **Status** | OPEN — generated draft, not on the active index |" , "| **Owner** | RootRecord |" ,
         "| **Related** | Library 07-Testing, 08-Ideas and the operator worklog of the day |", "",  # info: "| **Related** | Library 07-Testing, 08-Ideas and the operator worklog of the day |" , "" ,
         f"**Scope:** {scope}", "", "---", "", "## 1. Intent", "", intent, "", "---", "", "## 2. Current reality", "",
         "### 2.1 What exists", "", "| Item | Location / status |", "| --- | --- |"]
    L += [f"| {cell(w['file'], 70)} | {w['status']} |" for w in wos]  # info: set L
    L += ["", "### 2.2 Completed so far", ""]
    L += [f"- [{'x' if r['state'].startswith('PASS') else ' '}] {cell(r['title'], 90)} — {cell(r['state'], 60)}" for r in tr] or ["- [ ] No testing records for this date"]  # info: set L
    L += ["", "### 2.3 Known friction", ""] + ([f"- {x}" for x in friction] or ["- None recorded in today's sources"])
    L += ["", "---", "", "## 3. Tasks", ""] + ([f"{i}. {s}" for i, s in enumerate(so, 1)] or ["1. No open sign-off items"])
    L += ["", "---", "", "## 4. Non-goals", "", "- Executing any task listed here (generated drafts are never auto-promoted).",
          "- Writing into the Library or changing runtime services.", "", "---", "", "## 5. Key file / path reference", "",
          "| Path | Role |", "|------|------|",  # info: "| Path | Role |" , "|------|------|" ,
          "| `Library Documentation/07-Testing/README.md` | Testing record index (source) |",  # info: "| `Library Documentation/07-Testing/README.md` | Testing record index (source) |" ,
          "| `Library Documentation/01-Operations/0 - Human Operator Work Logs/` | Operator worklogs; sign-off list (source) |",  # info: "| `Library Documentation/01-Operations/0 - Human Operator Work Logs/` | Operator worklogs; sign-off list (sou
          f"| `{INFER_LOG}` | Inference JSONL (source) |", f"| `{POLLER_LOG}` | Poller log (source) |", "", "---", ""]  # info: f" | ` { INFER_LOG } ` | Inference JSONL (source) | " ,
    L.append(section_verbatim(t, "## 6. Open items", {}))
    L += ["", "---", "", "## 7. Notes & constraints", "", "- No force-push.", "- Secrets stay out of git.", "- Prefer small reversible steps.",
          f"- Generated by `Reports/template_fill.py` from measured sources; free text drafted by `{SPECIALIST}` under a facts-only prompt.",  # info: f" - Generated by `Reports/template_fill.py` from measured sources; free text drafted by ` { SPECIALIST } ` un
          "", "---", "", f"*Work order prepared {f.day} HST. Update status when closed.*", "", "---", ""]  # info: "" , "---" , "" , f" *Work order prepared
    L.append(section_verbatim(t, "## Archive / location note", {"{{Short_Name}}": short, "{{CODE}}": code, "{{YYYY-MM-DD}}": f.day,
                                                               "{{short-title}}": "desk-signoff-backlog"}))  # info: "{{short-title}}" : "desk-signoff-backlog" } ) )
    f.add(*facts, *friction, intent, scope, str(INFER_LOG), str(POLLER_LOG), *[w["status"] for w in wos])  # info: f . add ( * facts , *
    return "\n".join(L) + "\n"  # info: return "\n" . join ( L ) +


# ====================================================
# SECTION: TEMPLATES
# What it does: Set TEMPLATES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
TEMPLATES = {  # info: set TEMPLATES
    "worklog": {"file": "TEMPLATE System Operator Worklog — Session.md", "out": "System-Operator-Worklog-Session", "render": render_worklog,  # info: "worklog" : { "file" : "TEMPLATE System Operator Worklog — Session.md" , "out"
                "vocab": [{"desc": "header Status", "regex": r"^\*\*Status:\*\* (.+?)\s*$", "allowed": ["ACTIVE", "CLOSED"], "first_only": True}]},  # info: "vocab" : [ { "desc" : "header Status" ,
    "checkpoint": {"file": "TEMPLATE RootRecord Checkpoint.md", "out": "RootRecord-Checkpoint", "render": render_checkpoint,  # info: "checkpoint" : { "file" : "TEMPLATE RootRecord Checkpoint.md" , "out"
                   "vocab": [{"desc": "Poller state", "regex": r"^- Poller: (\w+) — ", "allowed": ["active", "inactive", "unknown"]},  # info: "vocab" : [ { "desc" : "Poller state" ,
                             {"desc": "subsystem Status", "regex": r"^\| (?:System / telemetry|Worklog scan|Ollama|EcoFlow BLE|A-EYES|Weather|GitHub sync|Cloudflare tunnel) \| (\w+) \|", "allowed": ["ok", "degraded", "down"]},  # info: { "desc" : "subsystem Status" , "regex" : r"^\| (?:System / telemetry|Worklog scan|Ollama|EcoFlow BLE|A-EYES|W
                             {"desc": "service State", "regex": r"^\| `[^`]+\.service` \| (\w+) \|$", "allowed": ["active", "inactive"]},  # info: { "desc" : "service State" , "regex" : r"^\| `[^`]+\.service` \| (\w+) \|$"
                             {"desc": "Pretty poller", "regex": r"^- Pretty poller: (.+)$", "allowed": ["manual", "auto", "not running"]}]},  # info: { "desc" : "Pretty poller" , "regex" : r"^- Pretty poller: (.+)$"
    "event": {"file": "TEMPLATE Event Action Log.md", "out": "Event-Action-Log", "render": render_event,  # info: "event" : { "file" : "TEMPLATE Event Action Log.md" , "out"
              "vocab": [{"desc": "header Status", "regex": r"^\*\*Status:\*\* (.+?)\s*$", "allowed": ["IN PROGRESS", "CLOSED"], "first_only": True},  # info: "vocab" : [ { "desc" : "header Status" ,
                        {"desc": "timeline time format", "regex": r"^(~?\d{2}:\d{2}) — ", "allowed": [r"~?\d{2}:\d{2}"]}]},  # info: { "desc" : "timeline time format" , "regex" : r"^(~?\d{2}:\d{2}) — "
    "workorder": {"file": "TEMPLATE Work Order.md", "out": "Work-Order", "render": render_workorder,  # info: "workorder" : { "file" : "TEMPLATE Work Order.md" , "out"
                  "vocab": [{"desc": "Status", "regex": r"^\| \*\*Status\*\* \| (.+?) \|$", "allowed": [r"OPEN — .+"]},  # info: "vocab" : [ { "desc" : "Status" ,
                            {"desc": "Work Order ID", "regex": r"^\| \*\*Work Order ID\*\* \| (.+?) \|$", "allowed": [r"WO-[A-Z0-9]+-\d{4}-\d{2}-\d{2}"]}]},  # info: { "desc" : "Work Order ID" , "regex" : r"^\| \*\*Work Order ID\*\* \| (.+?) \|$"
}  # info: }


# ====================================================
# SECTION: function guard_out
# What it does: guard out.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def guard_out(p: Path) -> None:  # info: def guard_out
    rp = p.resolve()  # info: set rp
    if str(rp).startswith(str(LIB.resolve())):  # info: if str ( rp ) . startswith (
        raise SystemExit(f"[fail] refusing to write into the Library: {rp}")  # info: raise SystemExit ( f" [fail] refusing to write into the Library: { rp }


# ====================================================
# SECTION: function write_rotating
# What it does: write rotating.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_rotating(name: str, text: str, dry: bool) -> str:  # info: def write_rotating
    cur = OUT_DIR / f"{name}_current.md"  # info: set cur
    guard_out(cur)  # info: call guard_out
    if dry:  # info: if dry :
        return str(cur) + " (dry-run, not written)"  # info: return str ( cur ) + " (dry-run, not written)"
    OUT_DIR.mkdir(parents=True, exist_ok=True)  # info: OUT_DIR . mkdir ( parents = True ,
    body = lambda s: "\n".join(ln for ln in s.splitlines() if not ln.startswith("<!-- generated"))  # info: set body
    if cur.is_file():  # info: if cur . is_file ( ) :
        old = read(cur)  # info: set old
        if body(old) == body(text):  # info: if body ( old ) == body (
            return str(cur) + " (unchanged)"  # info: return str ( cur ) + " (unchanged)"
        arch = OUT_DIR / "Archive"  # info: set arch
        arch.mkdir(exist_ok=True)  # info: arch . mkdir ( exist_ok = True )
        stamp = datetime.fromtimestamp(cur.stat().st_mtime).strftime("%Y-%m-%dT%H%M")  # info: set stamp
        shutil.move(str(cur), str(arch / f"{name}_{stamp}.md"))  # info: shutil . move ( str ( cur )
    tmp = cur.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(text, encoding="utf-8")  # info: tmp . write_text ( text , encoding =
    tmp.replace(cur)  # info: tmp . replace ( cur )
    return str(cur)  # info: return str ( cur )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    ap = argparse.ArgumentParser(description="Fill Library operations templates from measured desk data.")  # info: set ap
    ap.add_argument("--template", default="all", choices=["all", *TEMPLATES])  # info: ap . add_argument ( "--template" , default =
    ap.add_argument("--all", action="store_true", help="same as --template all (used by jobs.py)")  # info: ap . add_argument ( "--all" , action =
    ap.add_argument("--date", default=now().strftime("%Y-%m-%d"))  # info: ap . add_argument ( "--date" , default =
    ap.add_argument("--session", default="01", help="SESSION_NN for the worklog template")  # info: ap . add_argument ( "--session" , default =
    ap.add_argument("--draft", default="auto", choices=["none", "model", "auto"],  # info: ap . add_argument ( "--draft" , default =
                    help="free-text drafting: none = deterministic text; model/auto = specialist via run-infer.sh (auto skips when memory < 3 GB or the lock is busy)")  # info: set help
    ap.add_argument("--model-templates", default="", help="comma list limiting which templates call the model (default: all selected)")  # info: ap . add_argument ( "--model-templates" , default =
    ap.add_argument("--dry-run", action="store_true")  # info: ap . add_argument ( "--dry-run" , action =
    a = ap.parse_args(argv)  # info: set a
    keys = list(TEMPLATES) if (a.all or a.template == "all") else [a.template]  # info: set keys
    only = set(filter(None, a.model_templates.split(","))) or set(keys)  # info: set only
    report = {"generated": now().isoformat(timespec="seconds"), "date": a.date, "specialist": SPECIALIST, "results": {}}  # info: set report
    rc = 0  # info: set rc
    for k in keys:  # info: for k in keys :
        spec = TEMPLATES[k]  # info: set spec
        f = Facts(a.date)  # info: set f
        f.session = a.session  # info: f . session = a . session
        log: dict = {}  # info: set log
        mode = a.draft if k in only else "none"  # info: set mode
        text = spec["render"](f, mode, log)  # info: set text
        text = text.rstrip("\n") + "\n"  # info: set text
        v = tv.validate(tpl(spec["file"]), text, "\n".join(f.corpus), spec["vocab"])  # info: set v
        if v["ok"]:  # info: if v [ "ok" ] :
            where = write_rotating(spec["out"], text, a.dry_run)  # info: set where
        else:  # info: else :
            rc = 1  # info: set rc
            where = str(OUT_DIR / f"{spec['out']}_rejected.md")  # info: set where
            guard_out(Path(where))  # info: call guard_out
            if not a.dry_run:  # info: if not a . dry_run :
                OUT_DIR.mkdir(parents=True, exist_ok=True)  # info: OUT_DIR . mkdir ( parents = True ,
                Path(where).write_text(text, encoding="utf-8")  # info: call Path
        report["results"][k] = {"template": spec["file"], "output": where, "validation": v, "draft": log}  # info: report [ "results" ] [ k ] =
        print(f"[{'ok' if v['ok'] else 'REJECTED'}] {k}: {where}  headings={v['headings']} tables={v['tables']} "  # info: call print
              f"unsupported_numbers={v['unsupported_numbers'][:8]} draft={log.get('fields', log.get('skip_reason', mode))}")  # info: f" unsupported_numbers= { v [ 'unsupported_numbers' ] [
        for e in v["errors"]:  # info: for e in v [ "errors" ] :
            print("   error:", e)  # info: call print
    if not a.dry_run:  # info: if not a . dry_run :
        vp = OUT_DIR / "template-fill-validation_current.json"  # info: set vp
        guard_out(vp)  # info: call guard_out
        if vp.is_file() and len(keys) < len(TEMPLATES):  # single-template run: keep the other templates' last results
            try:  # info: try :
                old = json.loads(read(vp)).get("results", {})  # info: set old
                report["results"] = {**old, **report["results"]}  # info: report [ "results" ] = { ** old
            except ValueError:  # info: except ValueError :
                pass  # info: pass
        vp.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")  # info: vp . write_text ( json . dumps (
    return rc  # info: return rc


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main(sys.argv[1:]))  # info: sys . exit ( main ( sys .
