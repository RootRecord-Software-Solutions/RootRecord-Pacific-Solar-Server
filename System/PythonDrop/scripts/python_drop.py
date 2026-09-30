# ==============================================================================
# FILE: System/PythonDrop/scripts/python_drop.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""PythonDrop allowlist runner (package PythonDrop).

Only a script named in config/catalog.json may run, and only when its path
stays inside this package tree. The shipped catalog has no entries, so
status and tick start nothing.

No drop-folder scan, no clock-slot directories, no GUI terminal, no
restart-on-exit, and no listening port.
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import os  # info: import os
import re  # info: import re
import signal  # info: import signal
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
CATALOG = ROOT / "config" / "catalog.json"  # info: set CATALOG
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DATA = DB / "System" / "PythonDrop"  # info: set DATA
FIRE_PATH = DATA / "last-fire.json"  # info: set FIRE_PATH
LOG_DIR = DB / "Logs" / "System" / "PythonDrop"  # info: set LOG_DIR

INTERVALS = {"5m": 5, "15m": 15, "30m": 30, "1h": 60}  # info: set INTERVALS
HHMM = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")  # info: set HHMM
RUN_TIMEOUT_S = 50  # info: set RUN_TIMEOUT_S


# ====================================================
# SECTION: function _hst_now
# What it does:  hst now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _hst_now() -> datetime:  # info: def _hst_now
    return datetime.now(HST)  # info: return datetime . now ( HST )


# ====================================================
# SECTION: function _slot
# What it does:  slot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _slot(now: datetime) -> str:  # info: def _slot
    minute = (now.minute // 5) * 5  # info: set minute
    return f"{now.hour:02d}:{minute:02d}"  # info: return f" { now . hour : 02d


# ====================================================
# SECTION: function _schedule_ok
# What it does:  schedule ok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _schedule_ok(schedule: str) -> bool:  # info: def _schedule_ok
    return schedule in INTERVALS or HHMM.fullmatch(schedule) is not None  # info: return schedule in INTERVALS or HHMM . fullmatch


# ====================================================
# SECTION: function schedule_due
# What it does: True when this HST clock is inside the entry's slot. Deduped per day by the caller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def schedule_due(schedule: str, now: datetime) -> bool:  # info: def schedule_due
    """True when this HST clock is inside the entry's slot. Deduped per day by the caller."""  # info: """True when this HST clock is inside the entry's slot. Deduped per day by the caller."""
    if not _schedule_ok(schedule):  # info: if not _schedule_ok ( schedule ) :
        return False  # info: return False
    slot_minute = (now.minute // 5) * 5  # info: set slot_minute
    matched = HHMM.fullmatch(schedule)  # info: set matched
    if matched:  # info: if matched :
        hour = int(matched.group(1))  # info: set hour
        minute = int(matched.group(2))  # info: set minute
        if minute % 5 == 0:  # info: if minute % 5 == 0 :
            return now.hour == hour and slot_minute == minute  # info: return now . hour == hour and slot_minute
        return now.strftime("%H:%M") == schedule  # info: return now . strftime ( "%H:%M" ) ==
    if schedule == "5m":  # info: if schedule == "5m" :
        return True  # info: return True
    if schedule == "15m":  # info: if schedule == "15m" :
        return slot_minute in (0, 15, 30, 45)  # info: return slot_minute in ( 0 , 15 ,
    if schedule == "30m":  # info: if schedule == "30m" :
        return slot_minute in (0, 30)  # info: return slot_minute in ( 0 , 30 )
    return slot_minute == 0  # info: return slot_minute == 0


# ====================================================
# SECTION: function refusal_reason
# What it does: None means the entry is allowed to run. Any string means do not execute it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refusal_reason(root: Path, entry: object) -> str | None:  # info: def refusal_reason
    """None means the entry is allowed to run. Any string means do not execute it."""  # info: """None means the entry is allowed to run. Any string means do not execute it."""
    if not isinstance(entry, dict):  # info: if not isinstance ( entry , dict )
        return "not_an_entry"  # info: return "not_an_entry"
    name = entry.get("name")  # info: set name
    rel = entry.get("path")  # info: set rel
    schedule = entry.get("schedule")  # info: set schedule
    if not isinstance(name, str) or not name.strip():  # info: if not isinstance ( name , str )
        return "missing_name"  # info: return "missing_name"
    if not isinstance(rel, str) or not rel.strip():  # info: if not isinstance ( rel , str )
        return "missing_path"  # info: return "missing_path"
    if not isinstance(schedule, str) or not _schedule_ok(schedule):  # info: if not isinstance ( schedule , str )
        return "bad_schedule"  # info: return "bad_schedule"
    if Path(rel).is_absolute() or rel.startswith("~") or ".." in Path(rel).parts:  # info: if Path ( rel ) . is_absolute (
        return "path_refused"  # info: return "path_refused"
    if not rel.endswith(".py"):  # info: if not rel . endswith ( ".py" )
        return "not_py"  # info: return "not_py"
    try:  # info: try :
        candidate = (root / rel).resolve()  # info: set candidate
        candidate.relative_to(root.resolve())  # info: candidate . relative_to ( root . resolve (
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return "outside_tree"  # info: return "outside_tree"
    if not candidate.is_file():  # info: if not candidate . is_file ( ) :
        return "missing_file"  # info: return "missing_file"
    return None  # info: return None


# ====================================================
# SECTION: function load_catalog
# What it does: load catalog.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_catalog(path: Path | None = None) -> tuple[list, str | None]:  # info: def load_catalog
    catalog = path or CATALOG  # info: set catalog
    if not catalog.is_file():  # info: if not catalog . is_file ( ) :
        return [], None  # info: return [ ] , None
    try:  # info: try :
        data = json.loads(catalog.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return [], "unreadable"  # info: return [ ] , "unreadable"
    entries = data.get("entries") if isinstance(data, dict) else None  # info: set entries
    if not isinstance(entries, list):  # info: if not isinstance ( entries , list )
        return [], "unreadable"  # info: return [ ] , "unreadable"
    return entries, None  # info: return entries , None


# ====================================================
# SECTION: function select_runnable
# What it does: Split catalog entries into (runnable, refused). Refused entries are never spawned.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def select_runnable(entries: list, now: datetime, root: Path | None = None) -> tuple[list, list]:  # info: def select_runnable
    """Split catalog entries into (runnable, refused). Refused entries are never spawned."""  # info: """Split catalog entries into (runnable, refused). Refused entries are never spawned."""
    package = root or ROOT  # info: set package
    runnable: list[dict] = []  # info: set runnable
    refused: list[tuple[dict, str]] = []  # info: set refused
    for entry in entries:  # info: for entry in entries :
        reason = refusal_reason(package, entry)  # info: set reason
        if reason:  # info: if reason :
            refused.append((entry if isinstance(entry, dict) else {}, reason))  # info: refused . append ( ( entry if isinstance
            continue  # info: continue
        if schedule_due(str(entry["schedule"]), now):  # info: if schedule_due ( str ( entry [ "schedule"
            runnable.append(entry)  # info: runnable . append ( entry )
    return runnable, refused  # info: return runnable , refused


# ====================================================
# SECTION: function _fire_id
# What it does:  fire id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fire_id(now: datetime, entry: dict) -> str:  # info: def _fire_id
    day = now.strftime("%Y-%m-%d")  # info: set day
    return f"{day}|{entry['schedule']}|{_slot(now)}|{entry['name']}"  # info: return f" { day } | { entry


# ====================================================
# SECTION: function _read_fire
# What it does:  read fire.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_fire() -> dict:  # info: def _read_fire
    try:  # info: try :
        data = json.loads(FIRE_PATH.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {"version": 1, "fired": {}}  # info: return { "version" : 1 , "fired" :
    if not isinstance(data, dict) or not isinstance(data.get("fired"), dict):  # info: if not isinstance ( data , dict )
        return {"version": 1, "fired": {}}  # info: return { "version" : 1 , "fired" :
    return data  # info: return data


# ====================================================
# SECTION: function _write_fire
# What it does:  write fire.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_fire(data: dict) -> None:  # info: def _write_fire
    DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
    FIRE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")  # info: FIRE_PATH . write_text ( json . dumps (


# ====================================================
# SECTION: function _spawn
# What it does:  spawn.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _spawn(script: Path, fire_id: str) -> int:  # info: def _spawn
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    safe = re.sub(r"[^\w.\-]+", "_", fire_id)[:120]  # info: set safe
    log_path = LOG_DIR / f"{safe}.log"  # info: set log_path
    with log_path.open("a", encoding="utf-8") as handle:  # info: with log_path . open ( "a" , encoding
        handle.write(f"\n--- {_hst_now().isoformat()} start {script.name} ---\n")  # info: handle . write ( f" \n--- { _hst_now
        handle.flush()  # info: handle . flush ( )
        proc = subprocess.Popen(  # info: set proc
            ["python3", str(script)],  # info: [ "python3" , str ( script ) ]
            cwd=str(script.parent),  # info: set cwd
            stdout=handle,  # info: set stdout
            stderr=subprocess.STDOUT,  # info: set stderr
            start_new_session=True,  # info: set start_new_session
        )  # info: )
        try:  # info: try :
            rc = proc.wait(timeout=RUN_TIMEOUT_S)  # info: set rc
        except subprocess.TimeoutExpired:  # info: except subprocess . TimeoutExpired :
            try:  # info: try :
                os.killpg(proc.pid, signal.SIGTERM)  # info: os . killpg ( proc . pid ,
            except OSError:  # info: except OSError :
                proc.kill()  # info: proc . kill ( )
            rc = -9  # info: set rc
        handle.write(f"--- exit {rc} ---\n")  # info: handle . write ( f" --- exit { rc
    return int(rc)  # info: return int ( rc )


# ====================================================
# SECTION: function status_report
# What it does: status report.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def status_report(now: datetime | None = None) -> dict:  # info: def status_report
    moment = now or _hst_now()  # info: set moment
    entries, error = load_catalog()  # info: entries , error = load_catalog ( )
    if error:  # info: if error :
        return {"due": [], "catalog": 0, "spawned": 0, "catalog_error": error}  # info: return { "due" : [ ] , "catalog"
    runnable, _refused = select_runnable(entries, moment)  # info: runnable , _refused = select_runnable ( entries ,
    return {  # info: return {
        "due": [str(entry["name"]) for entry in runnable],  # info: "due" : [ str ( entry [ "name"
        "catalog": len(entries),  # info: "catalog" : len ( entries ) ,
        "spawned": 0,  # info: "spawned" : 0 ,
    }  # info: }


# ====================================================
# SECTION: function tick
# What it does: tick.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tick(now: datetime | None = None) -> dict:  # info: def tick
    moment = now or _hst_now()  # info: set moment
    entries, error = load_catalog()  # info: entries , error = load_catalog ( )
    if error or not entries:  # info: if error or not entries :
        report = {"due": [], "catalog": 0, "spawned": 0}  # info: set report
        if error:  # info: if error :
            report["catalog_error"] = error  # info: report [ "catalog_error" ] = error
        return report  # info: return report
    runnable, _refused = select_runnable(entries, moment)  # info: runnable , _refused = select_runnable ( entries ,
    fire = _read_fire()  # info: set fire
    fired = dict(fire.get("fired") or {})  # info: set fired
    spawned = 0  # info: set spawned
    for entry in runnable:  # info: for entry in runnable :
        fid = _fire_id(moment, entry)  # info: set fid
        if fired.get(fid):  # info: if fired . get ( fid ) :
            continue  # info: continue
        script = (ROOT / str(entry["path"])).resolve()  # info: set script
        # Mark before spawn so a crash does not run the same slot twice.
        fired[fid] = int(moment.timestamp())  # info: fired [ fid ] = int ( moment
        cutoff = moment.timestamp() - 3 * 86400  # info: set cutoff
        fire["fired"] = {key: value for key, value in fired.items() if int(value or 0) >= cutoff}  # info: fire [ "fired" ] = { key :
        _write_fire(fire)  # info: call _write_fire
        _spawn(script, fid)  # info: call _spawn
        spawned += 1  # info: set spawned
    return {  # info: return {
        "due": [str(entry["name"]) for entry in runnable],  # info: "due" : [ str ( entry [ "name"
        "catalog": len(entries),  # info: "catalog" : len ( entries ) ,
        "spawned": spawned,  # info: "spawned" : spawned ,
    }  # info: }


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    parser = argparse.ArgumentParser(description="PythonDrop allowlist runner")  # info: set parser
    parser.add_argument("command", choices=("status", "tick"))  # info: parser . add_argument ( "command" , choices =
    args = parser.parse_args(argv)  # info: set args
    if args.command == "status":  # info: if args . command == "status" :
        report = status_report()  # info: set report
    else:  # info: else :
        report = tick()  # info: set report
    print(json.dumps(report))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
