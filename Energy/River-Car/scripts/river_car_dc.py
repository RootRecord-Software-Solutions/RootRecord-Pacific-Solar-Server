# ==============================================================================
# FILE: Energy/River-Car/scripts/river_car_dc.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""River 2 Pro car/12V policy for external drives. Dry-run unless execute is signed off.

Never switches AC. Never calls the EcoFlow cloud API. The only actuator is the live
BLE scripts river2pro-dc-on.sh / river2pro-dc-off.sh, and only when --execute is
set and RR_RIVER_CAR_EXECUTE=1.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
PACIFIC = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server")  # info: set PACIFIC
DATABASE = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE
STATE_DIR = DATABASE / "Energy" / "River-Car"  # info: set STATE_DIR
LOG_DIR = DATABASE / "Energy" / "logs" / "River-Car"  # info: set LOG_DIR
SAMPLES = DATABASE / "Energy" / "samples"  # info: set SAMPLES
PORTS = DATABASE / "Energy" / "ports"  # info: set PORTS
ACTIONS = PACIFIC / "Energy" / "scripts" / "actions"  # info: set ACTIONS
STATE_NAME = "river-car-dc.json"  # info: set STATE_NAME
LOG_NAME = "river-car.log"  # info: set LOG_NAME
PURPOSE = "external-drives"  # info: set PURPOSE
EXECUTE_ENV = "RR_RIVER_CAR_EXECUTE"  # info: set EXECUTE_ENV


# ====================================================
# SECTION: function _log
# What it does:  log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log(msg: str) -> None:  # info: def _log
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    line = f"{datetime.now(HST).isoformat(timespec='seconds')} {msg}\n"  # info: set line
    with (LOG_DIR / LOG_NAME).open("a", encoding="utf-8") as fh:  # info: with ( LOG_DIR / LOG_NAME ) . open
        fh.write(line)  # info: fh . write ( line )


# ====================================================
# SECTION: function state_path
# What it does: state path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def state_path() -> Path:  # info: def state_path
    return STATE_DIR / STATE_NAME  # info: return STATE_DIR / STATE_NAME


# ====================================================
# SECTION: function load_state
# What it does: load state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_state() -> dict[str, Any]:  # info: def load_state
    base: dict[str, Any] = {  # info: set base
        "purpose": PURPOSE,  # info: "purpose" : PURPOSE ,
        "wanted": False,  # info: "wanted" : False ,
        "last_car_on": None,  # info: "last_car_on" : None ,
        "last_action": None,  # info: "last_action" : None ,
        "last_action_at": None,  # info: "last_action_at" : None ,
        "note": "External drives on River car DC. Default off. Copy is a stub. No AC.",  # info: "note" : "External drives on River car DC. Default off. Copy is a stub. No AC." ,
    }  # info: }
    path = state_path()  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return base  # info: return base
    try:  # info: try :
        raw = json.loads(path.read_text(encoding="utf-8"))  # info: set raw
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return base  # info: return base
    if isinstance(raw, dict):  # info: if isinstance ( raw , dict ) :
        base.update(raw)  # info: base . update ( raw )
    return base  # info: return base


# ====================================================
# SECTION: function save_state
# What it does: save state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_state(state: dict[str, Any]) -> None:  # info: def save_state
    STATE_DIR.mkdir(parents=True, exist_ok=True)  # info: STATE_DIR . mkdir ( parents = True ,
    path = state_path()  # info: set path
    tmp = path.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(path)  # info: tmp . replace ( path )


# ====================================================
# SECTION: function _boolish
# What it does:  boolish.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _boolish(value: Any) -> bool | None:  # info: def _boolish
    if isinstance(value, bool):  # info: if isinstance ( value , bool ) :
        return value  # info: return value
    if value is None:  # info: if value is None :
        return None  # info: return None
    if isinstance(value, (int, float)):  # info: if isinstance ( value , ( int ,
        return bool(int(value))  # info: return bool ( int ( value ) )
    if isinstance(value, str):  # info: if isinstance ( value , str ) :
        token = value.strip().lower()  # info: set token
        if token in {"1", "true", "on", "yes"}:  # info: if token in { "1" , "true" ,
            return True  # info: return True
        if token in {"0", "false", "off", "no"}:  # info: if token in { "0" , "false" ,
            return False  # info: return False
    return None  # info: return None


# ====================================================
# SECTION: function _dc_from_payload
# What it does:  dc from payload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _dc_from_payload(raw: dict[str, Any]) -> bool | None:  # info: def _dc_from_payload
    fields = raw.get("fields") if isinstance(raw.get("fields"), dict) else raw  # info: set fields
    if isinstance(fields, dict) and "dc_12v_port" in fields:  # info: if isinstance ( fields , dict ) and
        return _boolish(fields.get("dc_12v_port"))  # info: return _boolish ( fields . get ( "dc_12v_port"
    if "readback" in raw:  # info: if "readback" in raw :
        return _boolish(raw.get("readback"))  # info: return _boolish ( raw . get ( "readback"
    return None  # info: return None


# ====================================================
# SECTION: function last_car_on
# What it does: Last stored River 2 Pro dc_12v_port. Does not poll BLE or the cloud.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def last_car_on() -> bool | None:  # info: def last_car_on
    """Last stored River 2 Pro dc_12v_port. Does not poll BLE or the cloud."""  # info: """Last stored River 2 Pro dc_12v_port. Does not poll BLE or the cloud."""
    candidates: list[Path] = []  # info: set candidates
    port = PORTS / "river2pro-last.json"  # info: set port
    if port.is_file():  # info: if port . is_file ( ) :
        candidates.append(port)  # info: candidates . append ( port )
    reads = sorted(SAMPLES.glob("read-river2pro-*.json"))  # info: set reads
    if reads:  # info: if reads :
        candidates.append(reads[-1])  # info: candidates . append ( reads [ - 1
    best: Path | None = None  # info: set best
    best_mtime = -1.0  # info: set best_mtime
    for path in candidates:  # info: for path in candidates :
        try:  # info: try :
            mtime = path.stat().st_mtime  # info: set mtime
        except OSError:  # info: except OSError :
            continue  # info: continue
        if mtime >= best_mtime:  # info: if mtime >= best_mtime :
            best_mtime = mtime  # info: set best_mtime
            best = path  # info: set best
    if best is None:  # info: if best is None :
        return None  # info: return None
    try:  # info: try :
        raw = json.loads(best.read_text(encoding="utf-8"))  # info: set raw
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return None  # info: return None
    if not isinstance(raw, dict):  # info: if not isinstance ( raw , dict )
        return None  # info: return None
    return _dc_from_payload(raw)  # info: return _dc_from_payload ( raw )


# ====================================================
# SECTION: function execute_allowed
# What it does: execute allowed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def execute_allowed() -> bool:  # info: def execute_allowed
    return os.environ.get(EXECUTE_ENV, "0") == "1"  # info: return os . environ . get ( EXECUTE_ENV


# ====================================================
# SECTION: function _spawn_dc
# What it does: Run the live BLE action script. Callers must pass the execute gate first.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _spawn_dc(want_on: bool) -> dict[str, Any]:  # info: def _spawn_dc
    """Run the live BLE action script. Callers must pass the execute gate first."""  # info: """Run the live BLE action script. Callers must pass the execute gate first."""
    name = "river2pro-dc-on.sh" if want_on else "river2pro-dc-off.sh"  # info: set name
    script = ACTIONS / name  # info: set script
    if not script.is_file():  # info: if not script . is_file ( ) :
        return {"ok": False, "error": "missing_action_script", "script": name}  # info: return { "ok" : False , "error" :
    try:  # info: try :
        proc = subprocess.run(  # info: set proc
            [str(script)],  # info: call [
            check=False,  # info: set check
            capture_output=True,  # info: set capture_output
            text=True,  # info: set text
            timeout=90,  # info: set timeout
        )  # info: )
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired )
        return {"ok": False, "error": type(exc).__name__, "script": name}  # info: return { "ok" : False , "error" :
    tail = (proc.stdout or "").strip().splitlines()  # info: set tail
    status = next((line for line in tail if line.startswith("STATUS=")), "")  # info: set status
    return {  # info: return {
        "ok": proc.returncode == 0 and status == "STATUS=OK",  # info: "ok" : proc . returncode == 0 and
        "returncode": proc.returncode,  # info: "returncode" : proc . returncode ,
        "status": status or None,  # info: "status" : status or None ,
        "script": name,  # info: "script" : name ,
    }  # info: }


# ====================================================
# SECTION: function set_car
# What it does: Want the car port on or off. execute=False is dry-run and does not spawn.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_car(*, want_on: bool, execute: bool = False, force: bool = False) -> dict[str, Any]:  # info: def set_car
    """Want the car port on or off. execute=False is dry-run and does not spawn."""  # info: """Want the car port on or off. execute=False is dry-run and does not spawn."""
    st = load_state()  # info: set st
    already = last_car_on()  # info: set already
    report: dict[str, Any] = {  # info: set report
        "ok": True,  # info: "ok" : True ,
        "wanted": bool(want_on),  # info: "wanted" : bool ( want_on ) ,
        "execute": bool(execute),  # info: "execute" : bool ( execute ) ,
        "would": "car_on" if want_on else "car_off",  # info: "would" : "car_on" if want_on else "car_off" ,
        "already_on": already,  # info: "already_on" : already ,
        "spawned": False,  # info: "spawned" : False ,
    }  # info: }
    if not want_on and already is True and not force:  # info: if not want_on and already is True and
        st["wanted"] = True  # info: st [ "wanted" ] = True
        st["last_action"] = "leave_on_manual"  # info: st [ "last_action" ] = "leave_on_manual"
        st["last_action_at"] = time.time()  # info: st [ "last_action_at" ] = time . time
        st["last_car_on"] = True  # info: st [ "last_car_on" ] = True
        save_state(st)  # info: call save_state
        report["action"] = "leave_on_manual"  # info: report [ "action" ] = "leave_on_manual"
        report["left_on"] = True  # info: report [ "left_on" ] = True
        report["would"] = "leave_on"  # info: report [ "would" ] = "leave_on"
        _log("leave_on_manual")  # info: call _log
        return report  # info: return report
    st["wanted"] = bool(want_on)  # info: st [ "wanted" ] = bool ( want_on
    st["purpose"] = PURPOSE  # info: st [ "purpose" ] = PURPOSE
    if not execute:  # info: if not execute :
        action = f"dry_run_{'on' if want_on else 'off'}"  # info: set action
        st["last_action"] = action  # info: st [ "last_action" ] = action
        st["last_action_at"] = time.time()  # info: st [ "last_action_at" ] = time . time
        save_state(st)  # info: call save_state
        report["action"] = action  # info: report [ "action" ] = action
        _log(action)  # info: call _log
        return report  # info: return report
    if not execute_allowed():  # info: if not execute_allowed ( ) :
        st["last_action"] = "execute_refused"  # info: st [ "last_action" ] = "execute_refused"
        st["last_skip_reason"] = EXECUTE_ENV  # info: st [ "last_skip_reason" ] = EXECUTE_ENV
        st["last_action_at"] = time.time()  # info: st [ "last_action_at" ] = time . time
        save_state(st)  # info: call save_state
        report["ok"] = False  # info: report [ "ok" ] = False
        report["action"] = "execute_refused"  # info: report [ "action" ] = "execute_refused"
        report["error"] = "refused"  # info: report [ "error" ] = "refused"
        report["reason"] = f"{EXECUTE_ENV} is not 1"  # info: report [ "reason" ] = f" { EXECUTE_ENV
        _log("execute_refused")  # info: call _log
        return report  # info: return report
    switched = _spawn_dc(want_on)  # info: set switched
    report["spawned"] = True  # info: report [ "spawned" ] = True
    report["switch"] = {k: switched.get(k) for k in ("ok", "returncode", "status", "error", "script")}  # info: report [ "switch" ] = { k :
    if not switched.get("ok"):  # info: if not switched . get ( "ok" )
        report["ok"] = False  # info: report [ "ok" ] = False
        st["last_action"] = f"switch_failed_{'on' if want_on else 'off'}"  # info: st [ "last_action" ] = f" switch_failed_ {
        st["last_skip_reason"] = switched.get("error") or switched.get("status")  # info: st [ "last_skip_reason" ] = switched . get
        st["last_action_at"] = time.time()  # info: st [ "last_action_at" ] = time . time
        save_state(st)  # info: call save_state
        report["action"] = st["last_action"]  # info: report [ "action" ] = st [ "last_action"
        _log(report["action"])  # info: call _log
        return report  # info: return report
    st["last_action"] = "on" if want_on else "off"  # info: st [ "last_action" ] = "on" if want_on
    st["last_action_at"] = time.time()  # info: st [ "last_action_at" ] = time . time
    st["last_car_on"] = bool(want_on)  # info: st [ "last_car_on" ] = bool ( want_on
    st["last_skip_reason"] = None  # info: st [ "last_skip_reason" ] = None
    save_state(st)  # info: call save_state
    report["action"] = st["last_action"]  # info: report [ "action" ] = st [ "last_action"
    _log(f"switched {report['action']}")  # info: call _log
    return report  # info: return report


# ====================================================
# SECTION: function status
# What it does: status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def status() -> dict[str, Any]:  # info: def status
    st = load_state()  # info: set st
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "purpose": PURPOSE,  # info: "purpose" : PURPOSE ,
        "wanted": bool(st.get("wanted")),  # info: "wanted" : bool ( st . get (
        "last_car_on": last_car_on(),  # info: "last_car_on" : last_car_on ( ) ,
        "last_action": st.get("last_action"),  # info: "last_action" : st . get ( "last_action" )
        "state_path": str(state_path()),  # info: "state_path" : str ( state_path ( ) )
        "execute_gate": EXECUTE_ENV,  # info: "execute_gate" : EXECUTE_ENV ,
        "execute_allowed": execute_allowed(),  # info: "execute_allowed" : execute_allowed ( ) ,
        "backup_job": False,  # info: "backup_job" : False ,
    }  # info: }


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    import argparse  # info: import argparse

    parser = argparse.ArgumentParser(description="River 2 Pro car DC for external drives (dry-run default).")  # info: set parser
    parser.add_argument("--on", action="store_true", help="Want car DC on (drives).")  # info: parser . add_argument ( "--on" , action =
    parser.add_argument("--off", action="store_true", help="Want car DC off (drives idle).")  # info: parser . add_argument ( "--off" , action =
    parser.add_argument("--status", action="store_true", help="Read state and the last stored car flag.")  # info: parser . add_argument ( "--status" , action =
    parser.add_argument("--execute", action="store_true", help="Run the live BLE script. Refuses unless RR_RIVER_CAR_EXECUTE=1.")  # info: parser . add_argument ( "--execute" , action =
    args = parser.parse_args(argv)  # info: set args
    if args.on and args.off:  # info: if args . on and args . off
        print(json.dumps({"ok": False, "error": "on_and_off"}))  # info: call print
        return 2  # info: return 2
    if args.execute and not args.on and not args.off:  # info: if args . execute and not args .
        print(json.dumps({"ok": False, "error": "refused", "reason": f"{EXECUTE_ENV} action missing"}))  # info: call print
        return 1  # info: return 1
    if args.status or (not args.on and not args.off):  # info: if args . status or ( not args
        print(json.dumps(status(), indent=2))  # info: call print
        return 0  # info: return 0
    report = set_car(want_on=bool(args.on), execute=bool(args.execute))  # info: set report
    print(json.dumps(report, indent=2))  # info: call print
    return 0 if report.get("ok") else 1  # info: return 0 if report . get ( "ok"


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
