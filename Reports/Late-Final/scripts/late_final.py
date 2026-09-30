# ==============================================================================
# FILE: Reports/Late-Final/scripts/late_final.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""23:30 second chance for the optional late roll-up (G1 late-final-report).

Same report as voice_reports.py late_report. Skips when the board slot late is
already done or running. Text only (--no-voice). Never plays audio.

Night sleep: if System/NightSleep/scripts/night_sleep.py exists, call should_run.
A missing Folder means not sleeping (G1 missing night-mode.json). This script
does not implement that gate.

  python3 late_final.py            run the template when the late slot is open
  python3 late_final.py --dry-run  print skip or would-run; write last JSON only
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[2]  # info: set PACIFIC
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
STATE = DB / "Reports" / "board" / "daily-reports-due.json"  # info: set STATE
LAST = DB / "Reports" / "Late-Final" / "last.json"  # info: set LAST
LOG = DB / "Logs" / "Reports" / "Late-Final" / "late-final.jsonl"  # info: set LOG
REPORTS = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))  # info: set REPORTS
VOICE = PACIFIC / "Media" / "Voice" / "scripts" / "voice_reports.py"  # info: set VOICE
GATE = PACIFIC / "System" / "NightSleep" / "scripts" / "night_sleep.py"  # info: set GATE
JOB_ID = "voice_late_final_report"  # info: set JOB_ID
LATE_HOUR, LATE_MINUTE = 21, 2  # info: LATE_HOUR , LATE_MINUTE = 21 , 2


# ====================================================
# SECTION: function now
# What it does: now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> datetime:  # info: def now
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function late_status
# What it does: done / running / open. Read-only. Does not seed or rewrite the board.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def late_status(t: datetime) -> str:  # info: def late_status
    """done / running / open. Read-only. Does not seed or rewrite the board."""  # info: """done / running / open. Read-only. Does not seed or rewrite the board."""
    day = t.strftime("%Y-%m-%d")  # info: set day
    try:  # info: try :
        d = json.loads(STATE.read_text(encoding="utf-8"))  # info: set d
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        d = {}  # info: set d
    if isinstance(d, dict) and d.get("day") == day:  # info: if isinstance ( d , dict ) and
        row = (d.get("slots") or {}).get("late")  # info: set row
        if isinstance(row, dict) and row.get("status") in ("done", "running"):  # info: if isinstance ( row , dict ) and
            return str(row["status"])  # info: return str ( row [ "status" ] )
    f = REPORTS / "late_report_current.md"  # info: set f
    if f.is_file():  # info: if f . is_file ( ) :
        mt = datetime.fromtimestamp(f.stat().st_mtime, HST)  # info: set mt
        due = t.replace(hour=LATE_HOUR, minute=LATE_MINUTE, second=0, microsecond=0)  # info: set due
        if mt.date() == t.date() and mt >= due:  # info: if mt . date ( ) == t
            return "done"  # info: return "done"
    return "open"  # info: return "open"


# ====================================================
# SECTION: function night_skip
# What it does: None means run. 'night_sleep' means the NightSleep gate said skip. A missing gate Folder is not sleeping. Errors in the gate are not sleeping, matching G1 night_sleeping() on a bad
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def night_skip() -> str | None:  # info: def night_skip
    """None means run. 'night_sleep' means the NightSleep gate said skip.

    A missing gate Folder is not sleeping. Errors in the gate are not sleeping,
    matching G1 night_sleeping() on a bad file.
    """
    if not GATE.is_file():  # info: if not GATE . is_file ( ) :
        return None  # info: return None
    spec = importlib.util.spec_from_file_location("night_sleep", GATE)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader
        return None  # info: return None
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    try:  # info: try :
        spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
        fn = getattr(mod, "should_run", None)  # info: set fn
        if not callable(fn):  # info: if not callable ( fn ) :
            return None  # info: return None
        try:  # info: try :
            allowed = fn(JOB_ID)  # info: set allowed
        except TypeError:  # info: except TypeError :
            allowed = fn()  # info: set allowed
    except Exception:  # info: except Exception :
        return None  # info: return None
    return None if allowed else "night_sleep"  # info: return None if allowed else "night_sleep"


# ====================================================
# SECTION: function write_last
# What it does: write last.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_last(payload: dict, dry_run: bool) -> None:  # info: def write_last
    LAST.parent.mkdir(parents=True, exist_ok=True)  # info: LAST . parent . mkdir ( parents =
    tmp = LAST.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, LAST)  # info: os . replace ( tmp , LAST )
    if dry_run:  # info: if dry_run :
        return  # info: return
    LOG.parent.mkdir(parents=True, exist_ok=True)  # info: LOG . parent . mkdir ( parents =
    with LOG.open("a", encoding="utf-8") as f:  # info: with LOG . open ( "a" , encoding
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")  # info: f . write ( json . dumps (


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    dry = "--dry-run" in sys.argv  # info: set dry
    t = now()  # info: set t
    status = late_status(t)  # info: set status
    base = {"at": t.isoformat(), "job": JOB_ID, "late_status": status, "dry_run": dry,  # info: set base
            "night_sleep_folder": GATE.is_file(), "voice": False}  # info: "night_sleep_folder" : GATE . is_file ( ) ,
    skip = night_skip()  # info: set skip
    if skip:  # info: if skip :
        payload = dict(base, result="skip", detail=skip)  # info: set payload
    elif status in ("done", "running"):  # info: elif status in ( "done" , "running" )
        payload = dict(base, result="skip", detail="already_done" if status == "done" else "already_running")  # info: set payload
    elif dry:  # info: elif dry :
        payload = dict(base, result="would-run", detail="late_slot_open")  # info: set payload
    else:  # info: else :
        cmd = ["nice", "-n", "10", sys.executable, str(VOICE), "late_report", "--no-voice"]  # info: set cmd
        try:  # info: try :
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # info: set p
            ok = p.returncode == 0  # info: set ok
            payload = dict(base, result="ran" if ok else "failed", rc=p.returncode,  # info: set payload
                           out=(p.stdout or "").strip()[-400:], err=(p.stderr or "").strip()[-400:])  # info: set out
        except (OSError, subprocess.TimeoutExpired) as e:  # info: except ( OSError , subprocess . TimeoutExpired )
            payload = dict(base, result="failed", detail=type(e).__name__)  # info: set payload
            ok = False  # info: set ok
        write_last(payload, dry_run=False)  # info: call write_last
        print(json.dumps(payload, ensure_ascii=False))  # info: call print
        return 0 if payload.get("result") == "ran" else 1  # info: return 0 if payload . get ( "result"
    write_last(payload, dry_run=dry)  # info: call write_last
    print(json.dumps(payload, ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
