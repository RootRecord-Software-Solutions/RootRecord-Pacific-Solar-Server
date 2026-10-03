# ==============================================================================
# FILE: Automations/scripts/schedule_runtime.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Schedule JSON is timing authority. When disconnected or disarmed, nothing fires."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get(  # info: set DB
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: default Database
))  # info: )
SCHEDULE_DIR = DB / "System" / "control-panel" / "schedules"  # info: set SCHEDULE_DIR
DISCONNECT_PATH = DB / "System" / "control-panel" / "polling-disconnected.json"  # info: set DISCONNECT_PATH


# ====================================================
# SECTION: function _read_json
# What it does: Load a JSON object or return the fallback.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_json(path: Path, fallback: dict) -> dict:  # info: def _read_json
    try:  # info: try
        doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, json.JSONDecodeError):  # info: except
        return dict(fallback)  # info: return dict ( fallback )
    return doc if isinstance(doc, dict) else dict(fallback)  # info: return


# ====================================================
# SECTION: function polling_disconnected
# What it does: True when a schedule file on disk says the desk must not fire. A missing schedule and a missing flag mean jobs.py timing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def polling_disconnected(server: str = "pacific") -> bool:  # info: def polling_disconnected
    sched_path = SCHEDULE_DIR / f"{server}.json"  # info: set sched_path
    if not DISCONNECT_PATH.is_file() and not sched_path.is_file():  # info: if the database schedule was removed
        return False  # info: return False
    if DISCONNECT_PATH.is_file():  # info: if DISCONNECT_PATH . is_file
        flag = _read_json(DISCONNECT_PATH, {"polling_disconnected": True, "armed": False})  # info: set flag
        if flag.get("polling_disconnected", True) or not flag.get("armed", False):  # info: if global off
            return True  # info: return True
    if sched_path.is_file():  # info: if sched_path . is_file
        sched = load_schedule(server)  # info: set sched
        if sched.get("polling_disconnected", True) or not sched.get("armed", False):  # info: if schedule off
            return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function load_schedule
# What it does: Load one server schedule JSON.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_schedule(server: str = "pacific") -> dict:  # info: def load_schedule
    return _read_json(  # info: return _read_json
        SCHEDULE_DIR / f"{server}.json",  # info: path
        {"version": 1, "server": server, "armed": False, "polling_disconnected": True, "entries": []},  # info: fallback
    )  # info: )


# ====================================================
# SECTION: function load_catalog
# What it does: Load one server function catalog.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_catalog(server: str = "pacific") -> dict:  # info: def load_catalog
    return _read_json(SCHEDULE_DIR / f"catalog-{server}.json", {"version": 1, "server": server, "functions": []})  # info: return


# ====================================================
# SECTION: function schedule_mtime
# What it does: Mtime of the schedule file, or 0.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def schedule_mtime(server: str = "pacific") -> float:  # info: def schedule_mtime
    try:  # info: try
        return (SCHEDULE_DIR / f"{server}.json").stat().st_mtime  # info: return mtime
    except OSError:  # info: except OSError
        return 0.0  # info: return 0.0


# ====================================================
# SECTION: function schedule_active
# What it does: True when the schedule file is on disk and versioned. A missing file is not an active schedule.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def schedule_active(server: str = "pacific") -> bool:  # info: def schedule_active
    path = SCHEDULE_DIR / f"{server}.json"  # info: set path
    if not path.is_file():  # info: if not path . is_file
        return False  # info: return False
    sched = load_schedule(server)  # info: set sched
    return int(sched.get("version") or 0) >= 1 and isinstance(sched.get("entries"), list)  # info: return


# ====================================================
# SECTION: function function_index
# What it does: Map function_id to catalog function dict.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def function_index(server: str = "pacific") -> dict[str, dict]:  # info: def function_index
    cat = load_catalog(server)  # info: set cat
    out: dict[str, dict] = {}  # info: set out
    for fn in cat.get("functions") or []:  # info: for fn
        if isinstance(fn, dict) and fn.get("id"):  # info: if usable
            out[str(fn["id"])] = fn  # info: out [ id ] = fn
    return out  # info: return out


# ====================================================
# SECTION: function resolve_job
# What it does: Turn a schedule entry into a poller job dict for run_job.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def resolve_job(entry: dict, catalog: dict[str, dict] | None = None, server: str = "pacific") -> dict | None:  # info: def resolve_job
    fid = str(entry.get("function_id") or "")  # info: set fid
    if not fid:  # info: if not fid :
        return None  # info: return None
    index = catalog if catalog is not None else function_index(server)  # info: set index
    fn = index.get(fid) or {}  # info: set fn
    job = {  # info: set job
        "id": fid,  # info: "id" : fid ,
        "enabled": bool(entry.get("enabled")),  # info: entry owns enable while scheduled
        "description": fn.get("description") or entry.get("label") or "",  # info: description
        "builtin": fn.get("builtin") or "",  # info: builtin
        "command": fn.get("command") or "",  # info: command
        "timeout_sec": fn.get("timeout_sec") or 120,  # info: timeout_sec
        "cwd": fn.get("cwd") or "",  # info: cwd
        "env": fn.get("env") or {},  # info: env
        "needs_internet": bool(fn.get("needs_internet")),  # info: needs_internet
        "from_schedule": True,  # info: from_schedule
        "schedule_entry_id": entry.get("id"),  # info: schedule_entry_id
        "process_match": fn.get("process_match") or "",  # info: process_match
        "every_seconds": entry.get("every_seconds"),  # info: so a late boot can skip the repeating stack
    }  # info: }
    for key in ("public_host", "token_file", "cloudflared_bin", "priority", "process", "terminal", "watch", "local_service"):  # info: for key
        if fn.get(key) is not None:  # info: if present
            job[key] = fn[key]  # info: job [ key ] = fn [ key ]
    if not job["builtin"] and not job["command"]:  # info: if nothing to run
        return None  # info: return None
    return job  # info: return job


# ====================================================
# SECTION: function entry_due
# What it does: True when this placement should fire at the wall-clock step. every_seconds that divides the day lands on the clock (same stack as jobs.py).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def entry_due(entry: dict, step: datetime, last_fire: dict[str, float]) -> bool:  # info: def entry_due
    if not entry.get("enabled"):  # info: if not entry . get ( "enabled" ) :
        return False  # info: return False
    if entry.get("phase"):  # info: boot phases handled separately
        return False  # info: return False
    eid = str(entry.get("id") or "")  # info: set eid
    every = entry.get("every_seconds")  # info: set every
    if every is not None:  # info: if every is not None :
        try:  # info: try
            gap = float(every)  # info: set gap
        except (TypeError, ValueError):  # info: except
            return False  # info: return False
        if gap <= 0:  # info: if gap <= 0 :
            return False  # info: return False
        whole = int(gap)  # info: set whole
        if gap == whole and 86400 % whole == 0:  # info: if the gap divides the day
            clock = step.hour * 3600 + step.minute * 60 + step.second  # info: set clock
            phase = int(entry.get("second") or 0) % whole  # info: set phase
            if clock % whole != phase:  # info: if this second is the other battery or a skip
                return False  # info: return False
            opened = entry.get("from_minute")  # info: set opened
            if opened is not None and step.minute < int(opened):  # info: if before the :30 block
                return False  # info: return False
            key = f"{eid}|{step.date().isoformat()}|{step.hour:02d}:{step.minute:02d}:{step.second:02d}"  # info: set key
            if last_fire.get(key):  # info: if already fired
                return False  # info: return False
            last_fire[key] = step.timestamp()  # info: last_fire [ key ] = step . timestamp ( )
            return True  # info: return True
        prev = float(last_fire.get(eid) or 0)  # info: set prev
        now = step.timestamp()  # info: set now
        if prev and (now - prev) < gap:  # info: if inside gap
            return False  # info: return False
        return True  # info: return True
    hour = entry.get("hour")  # info: set hour
    minute = entry.get("minute")  # info: set minute
    second = entry.get("second")  # info: set second
    if minute is None:  # info: if minute is None :
        return False  # info: return False
    if hour is not None and int(hour) != step.hour:  # info: if hour mismatch
        return False  # info: return False
    if int(minute) != step.minute:  # info: if minute mismatch
        return False  # info: return False
    want_sec = 0 if second is None else int(second)  # info: set want_sec
    if want_sec != step.second:  # info: if second mismatch
        return False  # info: return False
    key = f"{eid}|{step.date().isoformat()}|{step.hour:02d}:{step.minute:02d}:{step.second:02d}"  # info: set key
    if last_fire.get(key):  # info: if already fired
        return False  # info: return False
    last_fire[key] = step.timestamp()  # info: last_fire [ key ] = step . timestamp ( )
    return True  # info: return True


# ====================================================
# SECTION: function due_jobs
# What it does: Resolved job dicts due at step. Empty when disconnected.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def due_jobs(server: str, step: datetime, last_fire: dict[str, float]) -> list[dict]:  # info: def due_jobs
    if polling_disconnected(server):  # info: if polling_disconnected ( server ) :
        return []  # info: return [ ]
    sched = load_schedule(server)  # info: set sched
    index = function_index(server)  # info: set index
    out: list[dict] = []  # info: set out
    for entry in sched.get("entries") or []:  # info: for entry
        if not isinstance(entry, dict) or not entry_due(entry, step, last_fire):  # info: if not due
            continue  # info: continue
        if entry.get("every_seconds") is not None:  # info: stamp every_seconds
            last_fire[str(entry.get("id") or "")] = step.timestamp()  # info: last_fire [ id ]
        job = resolve_job(entry, index, server)  # info: set job
        if job is not None:  # info: if job is not None :
            out.append(job)  # info: out . append ( job )
    return out  # info: return out


# ====================================================
# SECTION: function boot_jobs
# What it does: Resolved jobs with phase boot or once_at_start. Empty when disconnected.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def boot_jobs(server: str = "pacific", phase: str = "boot") -> list[dict]:  # info: def boot_jobs
    if polling_disconnected(server):  # info: if polling_disconnected ( server ) :
        return []  # info: return [ ]
    sched = load_schedule(server)  # info: set sched
    index = function_index(server)  # info: set index
    out: list[dict] = []  # info: set out
    for entry in sched.get("entries") or []:  # info: for entry
        if not isinstance(entry, dict) or not entry.get("enabled"):  # info: if off
            continue  # info: continue
        if (entry.get("phase") or "") != phase:  # info: if wrong phase
            continue  # info: continue
        job = resolve_job(entry, index, server)  # info: set job
        if job is not None:  # info: if job is not None :
            if entry.get("phase") == "boot" and job.get("priority") is None:  # info: default priority
                job["priority"] = 100  # info: job [ "priority" ] = 100
            out.append(job)  # info: out . append ( job )
    out.sort(key=lambda j: int(j.get("priority") or 100))  # info: out . sort
    return out  # info: return out


# ====================================================
# SECTION: function run_ble_adapter_cycle
# What it does: Power the adapter off then on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_ble_adapter_cycle() -> dict:  # info: def run_ble_adapter_cycle
    subprocess.run(["bluetoothctl", "power", "off"], capture_output=True, text=True, timeout=20)  # info: power off
    subprocess.run(["sleep", "2"], capture_output=True, text=True, timeout=5)  # info: pause
    ran = subprocess.run(["bluetoothctl", "power", "on"], capture_output=True, text=True, timeout=20)  # info: power on
    return {"ok": ran.returncode == 0, "code": ran.returncode}  # info: return


# ====================================================
# SECTION: function ensure_process
# What it does: Start command if process_match is not already running.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_process(job: dict) -> dict:  # info: def ensure_process
    match = (job.get("process_match") or job.get("id") or "").strip()  # info: set match
    cmd = (job.get("command") or "").strip()  # info: set cmd
    if not cmd:  # info: if not cmd :
        return {"ok": False, "detail": "empty_command"}  # info: return
    try:  # info: try
        chk = subprocess.run(["pgrep", "-f", match], capture_output=True, text=True, timeout=5)  # info: set chk
    except (OSError, subprocess.TimeoutExpired):  # info: except
        chk = None  # info: set chk
    if chk is not None and chk.returncode == 0 and (chk.stdout or "").strip():  # info: if already up
        return {"ok": True, "detail": "already_running"}  # info: return
    cwd = (job.get("cwd") or "").strip() or None  # info: set cwd
    subprocess.Popen(["bash", "-lc", cmd], cwd=cwd, start_new_session=True)  # info: start detached
    return {"ok": True, "detail": "started"}  # info: return
