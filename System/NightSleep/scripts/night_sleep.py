# ==============================================================================
# FILE: System/NightSleep/scripts/night_sleep.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Night-sleep scheduler gate (package NightSleep).

Reads Database System/NightSleep/night-mode.json. Missing or invalid file means
not sleeping. Does not write that flag, compute sunrise, or touch hardware.
The poller calls should_run only when RR_NIGHT_SLEEP=1 at process start.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DATA = DB / "System" / "NightSleep"  # info: set DATA
STATE = DATA / "night-mode.json"  # info: set STATE
LAST = DATA / "last-skip.json"  # info: set LAST
LOG_DIR = DB / "Logs" / "System" / "NightSleep"  # info: set LOG_DIR
LOG_FILE = LOG_DIR / "night-sleep.log"  # info: set LOG_FILE

# Live ids that match G1 NIGHT_POLL, plus poller jobs that must keep running.
# ====================================================
# SECTION: ALLOW
# What it does: Set ALLOW.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ALLOW = frozenset({  # info: set ALLOW
    "geology_collect",  # info: "geology_collect" ,
    "geology_kilauea_cams",  # info: "geology_kilauea_cams" ,
    "council_quake_telegram",  # info: "council_quake_telegram" ,
    "heartbeat",  # info: "heartbeat" ,
    "ensure_tunnel_online",  # info: "ensure_tunnel_online" ,
    "service_supervisor",  # info: "service_supervisor" ,
    "sys_stats_cycle",  # info: "sys_stats_cycle" ,
    "network_globe_hawaii",  # info: "network_globe_hawaii" ,
    "security_camera_server",  # info: "security_camera_server" ,
    "security_camera_frame_grab",  # info: "security_camera_frame_grab" ,
})  # info: } )


# ====================================================
# SECTION: function gate_enabled
# What it does: gate enabled.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def gate_enabled() -> bool:  # info: def gate_enabled
    return os.environ.get("RR_NIGHT_SLEEP", "0").strip() == "1"  # info: return os . environ . get ( "RR_NIGHT_SLEEP"


# ====================================================
# SECTION: function sleeping
# What it does: sleeping.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sleeping(path: Path | None = None) -> bool:  # info: def sleeping
    p = path or STATE  # info: set p
    try:  # info: try :
        if not p.is_file():  # info: if not p . is_file ( ) :
            return False  # info: return False
        data = json.loads(p.read_text(encoding="utf-8"))  # info: set data
        if not isinstance(data, dict):  # info: if not isinstance ( data , dict )
            return False  # info: return False
        return bool(data.get("sleeping"))  # info: return bool ( data . get ( "sleeping"
    except Exception:  # info: except Exception :
        return False  # info: return False


# ====================================================
# SECTION: function _record_skip
# What it does:  record skip.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _record_skip(job_id: str) -> None:  # info: def _record_skip
    try:  # info: try :
        DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
        LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")  # info: set stamp
        LAST.write_text(  # info: LAST . write_text (
            json.dumps({"job_id": job_id, "skipped": True, "at": stamp}) + "\n",  # info: json . dumps ( { "job_id" : job_id
            encoding="utf-8",  # info: set encoding
        )  # info: )
        with LOG_FILE.open("a", encoding="utf-8") as fh:  # info: with LOG_FILE . open ( "a" , encoding
            fh.write(f"{stamp} night sleep skip {job_id}\n")  # info: fh . write ( f" { stamp }
    except Exception:  # info: except Exception :
        return  # info: return


# ====================================================
# SECTION: function should_run
# What it does: True when this job may run. Fail open when the gate is off or the file is bad.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def should_run(job_id: str, *, enabled: bool | None = None, state_path: Path | None = None) -> bool:  # info: def should_run
    """True when this job may run. Fail open when the gate is off or the file is bad."""  # info: """True when this job may run. Fail open when the gate is off or the file is bad."""
    if enabled is None:  # info: if enabled is None :
        enabled = gate_enabled()  # info: set enabled
    if not enabled:  # info: if not enabled :
        return True  # info: return True
    jid = str(job_id or "")  # info: set jid
    if jid in ALLOW:  # info: if jid in ALLOW :
        return True  # info: return True
    if not sleeping(state_path):  # info: if not sleeping ( state_path ) :
        return True  # info: return True
    _record_skip(jid)  # info: call _record_skip
    return False  # info: return False


# ====================================================
# SECTION: function _check
# What it does:  check.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _check() -> int:  # info: def _check
    import tempfile  # info: import tempfile

    fd, name = tempfile.mkstemp(prefix="night-mode-", suffix=".json")  # info: fd , name = tempfile . mkstemp (
    os.close(fd)  # info: os . close ( fd )
    path = Path(name)  # info: set path
    try:  # info: try :
        path.write_text(json.dumps({"sleeping": True}), encoding="utf-8")  # info: path . write_text ( json . dumps (
        if not should_run("geology_collect", enabled=True, state_path=path):  # info: if not should_run ( "geology_collect" , enabled =
            print("FAIL geology_collect skipped while sleeping", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if should_run("voice_late_report", enabled=True, state_path=path):  # info: if should_run ( "voice_late_report" , enabled = True
            print("FAIL voice_late_report ran while sleeping", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if not LAST.is_file() or "voice_late_report" not in LAST.read_text(encoding="utf-8"):  # info: if not LAST . is_file ( ) or
            print("FAIL last-skip record missing", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        path.unlink()  # info: path . unlink ( )
        if not should_run("geology_collect", enabled=True, state_path=path):  # info: if not should_run ( "geology_collect" , enabled =
            print("FAIL geology_collect blocked with no file", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if not should_run("voice_late_report", enabled=True, state_path=path):  # info: if not should_run ( "voice_late_report" , enabled =
            print("FAIL voice_late_report blocked with no file", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if not should_run("voice_late_report", enabled=False, state_path=path):  # info: if not should_run ( "voice_late_report" , enabled =
            print("FAIL gate-off blocked a job", file=sys.stderr)  # info: call print
            return 1  # info: return 1
    finally:  # info: finally :
        path.unlink(missing_ok=True)  # info: path . unlink ( missing_ok = True )
    print("PASS night-sleep gate")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    if "--check" in sys.argv:  # info: if "--check" in sys . argv :
        raise SystemExit(_check())  # info: raise SystemExit ( _check ( ) )
    print("night-sleep gate installed; RR_NIGHT_SLEEP default off")  # info: call print
