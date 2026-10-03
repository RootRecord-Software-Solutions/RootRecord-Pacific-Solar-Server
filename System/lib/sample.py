# ==============================================================================
# FILE: System/lib/sample.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
from __future__ import annotations  # info: from __future__ import annotations
import json, os, sys, time  # info: import json , os , sys , time
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

from paths import SYSTEM_DB, ensure_dirs  # info: from paths import SYSTEM_DB , ensure_dirs

# db helpers (skill root on path)
_SKILL = Path(__file__).resolve().parents[1]  # info: set _SKILL
if str(_SKILL) not in sys.path:  # info: if str ( _SKILL ) not in sys
    sys.path.insert(0, str(_SKILL))  # info: sys . path . insert ( 0 ,
from db.store import persist_snapshot  # noqa: E402

LOCAL = ZoneInfo("Pacific/Honolulu")  # info: set LOCAL

# ====================================================
# SECTION: function _now_iso
# What it does:  now iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now_iso():  # info: def _now_iso
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")  # info: return datetime . now ( timezone . utc

# ====================================================
# SECTION: function _local_stamp
# What it does:  local stamp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _local_stamp():  # info: def _local_stamp
    return datetime.now(LOCAL).strftime("%Y%m%d-%H%M%S")  # info: return datetime . now ( LOCAL ) .

# ====================================================
# SECTION: function _read_load
# What it does:  read load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_load():  # info: def _read_load
    try:  # info: try :
        with open("/proc/loadavg") as f:  # info: with open ( "/proc/loadavg" ) as f :
            a, b, c, *_ = f.read().split()  # info: a , b , c , * _
        return float(a), float(b), float(c), "measured"  # info: return float ( a ) , float (
    except OSError:  # info: except OSError :
        return None, None, None, "missing"  # info: return None , None , None , "missing"

# ====================================================
# SECTION: function _read_mem
# What it does:  read mem.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_mem():  # info: def _read_mem
    total = avail = None  # info: set total
    try:  # info: try :
        with open("/proc/meminfo") as f:  # info: with open ( "/proc/meminfo" ) as f :
            for line in f:  # info: for line in f :
                if line.startswith("MemTotal:"):  # info: if line . startswith ( "MemTotal:" ) :
                    total = int(line.split()[1]) * 1024  # info: set total
                elif line.startswith("MemAvailable:"):  # info: elif line . startswith ( "MemAvailable:" ) :
                    avail = int(line.split()[1]) * 1024  # info: set avail
        if total and avail is not None:  # info: if total and avail is not None :
            return total, avail, 100.0 * (1.0 - avail / total), "measured"  # info: return total , avail , 100.0 * (
    except Exception:  # info: except Exception :
        pass  # info: pass
    return None, None, None, "missing"  # info: return None , None , None , "missing"

# ====================================================
# SECTION: function _read_cpu_pct
# What it does:  read cpu pct.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_cpu_pct(sample_s=0.35):  # info: def _read_cpu_pct
    def ticks():  # info: def ticks
        with open("/proc/stat") as f:  # info: with open ( "/proc/stat" ) as f :
            nums = [int(x) for x in f.readline().split()[1:]]  # info: set nums
        idle = nums[3] + (nums[4] if len(nums) > 4 else 0)  # info: set idle
        return idle, sum(nums)  # info: return idle , sum ( nums )
    try:  # info: try :
        i1, t1 = ticks()  # info: i1 , t1 = ticks ( )
        time.sleep(sample_s)  # info: time . sleep ( sample_s )
        i2, t2 = ticks()  # info: i2 , t2 = ticks ( )
        dt, di = t2 - t1, i2 - i1  # info: dt , di = t2 - t1 ,
        if dt <= 0:  # info: if dt <= 0 :
            return None, "missing"  # info: return None , "missing"
        return max(0.0, min(100.0, 100.0 * (1.0 - di / dt))), "measured"  # info: return max ( 0.0 , min ( 100.0
    except Exception:  # info: except Exception :
        return None, "missing"  # info: return None , "missing"

# ====================================================
# SECTION: function snapshot
# What it does: snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def snapshot():  # info: def snapshot
    ensure_dirs()  # info: call ensure_dirs
    load1, load5, load15, load_st = _read_load()  # info: load1 , load5 , load15 , load_st =
    mem_total, mem_avail, mem_pct, mem_st = _read_mem()  # info: mem_total , mem_avail , mem_pct , mem_st =
    cpu_pct, cpu_st = _read_cpu_pct()  # info: cpu_pct , cpu_st = _read_cpu_pct ( )
    at = _now_iso()  # info: set at
    fields = {  # info: set fields
        "cpu_percent": {"value": round(cpu_pct, 2) if cpu_pct is not None else None, "state": cpu_st, "unit": "%"},  # info: "cpu_percent" : { "value" : round ( cpu_pct
        "load1": {"value": load1, "state": load_st, "unit": "load"},  # info: "load1" : { "value" : load1 , "state"
        "load5": {"value": load5, "state": load_st, "unit": "load"},  # info: "load5" : { "value" : load5 , "state"
        "load15": {"value": load15, "state": load_st, "unit": "load"},  # info: "load15" : { "value" : load15 , "state"
        "mem_total_bytes": {"value": mem_total, "state": mem_st, "unit": "B"},  # info: "mem_total_bytes" : { "value" : mem_total , "state"
        "mem_available_bytes": {"value": mem_avail, "state": mem_st, "unit": "B"},  # info: "mem_available_bytes" : { "value" : mem_avail , "state"
        "mem_used_percent": {"value": round(mem_pct, 2) if mem_pct is not None else None, "state": mem_st, "unit": "%"},  # info: "mem_used_percent" : { "value" : round ( mem_pct
    }  # info: }
    return {"alias": "host", "host": os.uname().nodename, "fields": fields, "at": at, "source": "proc"}  # info: return { "alias" : "host" , "host" :

# ====================================================
# SECTION: function persist
# What it does: Write the sample into System/system.db only. Layers and status come from the db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persist(snap):  # info: def persist
    ensure_dirs()  # info: call ensure_dirs
    db_ok = False  # info: set db_ok
    try:  # info: try :
        persist_snapshot(snap)  # info: call persist_snapshot
        from db.condense import ensure_layers  # info: from db . condense import ensure_layers
        ensure_layers()  # info: leave the layer files; consolidate.py owns the roll-up
        from status_json import write_status_json  # info: from status_json import write_status_json
        write_status_json()  # info: status json is built from system.db + layers/5min.db
        db_ok = True  # info: set db_ok
    except Exception as e:  # info: except Exception as e :
        print(f"DB_ERROR: {type(e).__name__}: {e}", file=sys.stderr)  # info: call print

    return SYSTEM_DB, db_ok  # info: return SYSTEM_DB , db_ok

# ====================================================
# SECTION: function summary_line
# What it does: summary line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def summary_line(snap, db_ok: bool):  # info: def summary_line
    f = snap["fields"]  # info: set f
    def v(key, fmt):  # info: def v
        cell = f.get(key) or {}  # info: set cell
        if cell.get("state") != "measured" or cell.get("value") is None:  # info: if cell . get ( "state" ) !=
            return "—"  # info: return "—"
        return fmt(cell["value"])  # info: return fmt ( cell [ "value" ] )
    src = "sqlite" if db_ok else "proc"  # info: set src
    return f"SYSTEM  cpu={v('cpu_percent', lambda x: f'{x:.0f}%')}  load={v('load1', lambda x: f'{x:.2f}')}  mem={v('mem_used_percent', lambda x: f'{x:.0f}%')}  src={src}"  # info: return f" SYSTEM cpu= { v ( 'cpu_percent' ,

# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main():  # info: def main
    snap = snapshot()  # info: set snap
    path, db_ok = persist(snap)  # info: path , db_ok = persist ( snap )
    print(summary_line(snap, db_ok))  # info: call print
    print(f"OK wrote {path}" + ("" if db_ok else " (db write failed)"))  # info: call print
    return 0  # info: return 0

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
