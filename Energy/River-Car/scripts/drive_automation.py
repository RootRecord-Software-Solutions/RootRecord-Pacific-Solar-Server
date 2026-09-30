# ==============================================================================
# FILE: Energy/River-Car/scripts/drive_automation.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""River 2 Pro car DC drive automation. Copy jobs stay a stub.

Never toggles AC. Default car DC off. A tick does nothing until auto is true
and an enabled copy job exists. Copy is not implemented, so the tick does not
spin disks or run the BLE scripts.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

_SCRIPTS = Path(__file__).resolve().parent  # info: set _SCRIPTS
if str(_SCRIPTS) not in sys.path:  # info: if str ( _SCRIPTS ) not in sys
    sys.path.insert(0, str(_SCRIPTS))  # info: sys . path . insert ( 0 ,

from disk_session import prepare, release, snapshot  # noqa: E402
from river_car_dc import (  # noqa: E402
    PURPOSE,  # info: PURPOSE ,
    STATE_DIR,  # info: STATE_DIR ,
    last_car_on,  # info: last_car_on ,
    load_state as load_car_state,  # info: load_state as load_car_state ,
    status as car_status,  # info: status as car_status ,
)  # info: )

STATE_NAME = "drive-automation.json"  # info: set STATE_NAME
LOCK_NAME = "drive-automation.lock"  # info: set LOCK_NAME
PURPOSE_AUTO = "external-drives-automation"  # info: set PURPOSE_AUTO

# ====================================================
# SECTION: DEFAULT
# What it does: Set DEFAULT.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
DEFAULT: dict[str, Any] = {  # info: set DEFAULT
    "purpose": PURPOSE_AUTO,  # info: "purpose" : PURPOSE_AUTO ,
    "auto": False,  # info: "auto" : False ,
    "hold_car_on": False,  # info: "hold_car_on" : False ,
    "copy_jobs": [],  # info: "copy_jobs" : [ ] ,
    "last_tick": None,  # info: "last_tick" : None ,
    "last_action": None,  # info: "last_action" : None ,
    "last_skip": "auto_off",  # info: "last_skip" : "auto_off" ,
    "note": "River car 12V for drives. Copy jobs empty until wired. Never AC.",  # info: "note" : "River car 12V for drives. Copy jobs empty until wired. Never AC." ,
}  # info: }


# ====================================================
# SECTION: function state_path
# What it does: state path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def state_path() -> Path:  # info: def state_path
    return STATE_DIR / STATE_NAME  # info: return STATE_DIR / STATE_NAME


# ====================================================
# SECTION: function lock_path
# What it does: lock path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lock_path() -> Path:  # info: def lock_path
    return STATE_DIR / LOCK_NAME  # info: return STATE_DIR / LOCK_NAME


# ====================================================
# SECTION: function load_config
# What it does: load config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_config() -> dict[str, Any]:  # info: def load_config
    base = dict(DEFAULT)  # info: set base
    path = state_path()  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return base  # info: return base
    try:  # info: try :
        raw = json.loads(path.read_text(encoding="utf-8"))  # info: set raw
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return base  # info: return base
    if isinstance(raw, dict):  # info: if isinstance ( raw , dict ) :
        base.update(raw)  # info: base . update ( raw )
    if not isinstance(base.get("copy_jobs"), list):  # info: if not isinstance ( base . get (
        base["copy_jobs"] = []  # info: base [ "copy_jobs" ] = [ ]
    base["auto"] = bool(base.get("auto"))  # info: base [ "auto" ] = bool ( base
    base["hold_car_on"] = bool(base.get("hold_car_on"))  # info: base [ "hold_car_on" ] = bool ( base
    return base  # info: return base


# ====================================================
# SECTION: function save_config
# What it does: save config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_config(cfg: dict[str, Any]) -> dict[str, Any]:  # info: def save_config
    STATE_DIR.mkdir(parents=True, exist_ok=True)  # info: STATE_DIR . mkdir ( parents = True ,
    path = state_path()  # info: set path
    out = dict(DEFAULT)  # info: set out
    out.update(cfg)  # info: out . update ( cfg )
    out["auto"] = bool(out.get("auto"))  # info: out [ "auto" ] = bool ( out
    out["hold_car_on"] = bool(out.get("hold_car_on"))  # info: out [ "hold_car_on" ] = bool ( out
    if not isinstance(out.get("copy_jobs"), list):  # info: if not isinstance ( out . get (
        out["copy_jobs"] = []  # info: out [ "copy_jobs" ] = [ ]
    tmp = path.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(path)  # info: tmp . replace ( path )
    return out  # info: return out


# ====================================================
# SECTION: function enabled_copy_jobs
# What it does: enabled copy jobs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def enabled_copy_jobs(cfg: dict[str, Any] | None = None) -> list[dict[str, Any]]:  # info: def enabled_copy_jobs
    cfg = cfg if isinstance(cfg, dict) else load_config()  # info: set cfg
    out: list[dict[str, Any]] = []  # info: set out
    for raw in cfg.get("copy_jobs") or []:  # info: for raw in cfg . get ( "copy_jobs"
        if not isinstance(raw, dict) or not raw.get("enabled"):  # info: if not isinstance ( raw , dict )
            continue  # info: continue
        if not str(raw.get("id") or "").strip():  # info: if not str ( raw . get (
            continue  # info: continue
        out.append(raw)  # info: out . append ( raw )
    return out  # info: return out


# ====================================================
# SECTION: function run_copy_jobs
# What it does: Stub. Does not rsync or unmount.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_copy_jobs(jobs: list[dict[str, Any]] | None = None) -> dict[str, Any]:  # info: def run_copy_jobs
    """Stub. Does not rsync or unmount."""  # info: """Stub. Does not rsync or unmount."""
    pending = jobs if jobs is not None else enabled_copy_jobs()  # info: set pending
    if not pending:  # info: if not pending :
        return {"ok": True, "ran": 0, "skipped": "no_copy_jobs"}  # info: return { "ok" : True , "ran" :
    ids = [str(job.get("id") or "") for job in pending]  # info: set ids
    return {  # info: return {
        "ok": False,  # info: "ok" : False ,
        "ran": 0,  # info: "ran" : 0 ,
        "skipped": "copy_not_implemented",  # info: "skipped" : "copy_not_implemented" ,
        "pending": ids,  # info: "pending" : ids ,
        "note": "Power path is gated. This stub will not rsync.",  # info: "note" : "Power path is gated. This stub will not rsync." ,
    }  # info: }


# ====================================================
# SECTION: function _try_lock
# What it does:  try lock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _try_lock() -> Any:  # info: def _try_lock
    path = lock_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    fh = path.open("a+", encoding="utf-8")  # info: set fh
    try:  # info: try :
        import fcntl  # info: import fcntl

        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: fcntl . flock ( fh . fileno (
    except OSError:  # info: except OSError :
        fh.close()  # info: fh . close ( )
        return None  # info: return None
    return fh  # info: return fh


# ====================================================
# SECTION: function status
# What it does: status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def status(*, live: bool = False) -> dict[str, Any]:  # info: def status
    del live  # kept so the old flag does not start a cloud or BLE read
    cfg = load_config()  # info: set cfg
    car = car_status()  # info: set car
    disks = snapshot()  # info: set disks
    enabled = enabled_copy_jobs(cfg)  # info: set enabled
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "purpose": PURPOSE,  # info: "purpose" : PURPOSE ,
        "auto": bool(cfg.get("auto")),  # info: "auto" : bool ( cfg . get (
        "hold_car_on": bool(cfg.get("hold_car_on")),  # info: "hold_car_on" : bool ( cfg . get (
        "copy_jobs_configured": len(cfg.get("copy_jobs") or []),  # info: "copy_jobs_configured" : len ( cfg . get (
        "copy_jobs_enabled": len(enabled),  # info: "copy_jobs_enabled" : len ( enabled ) ,
        "last_action": cfg.get("last_action"),  # info: "last_action" : cfg . get ( "last_action" )
        "last_skip": cfg.get("last_skip"),  # info: "last_skip" : cfg . get ( "last_skip" )
        "last_tick": cfg.get("last_tick"),  # info: "last_tick" : cfg . get ( "last_tick" )
        "car": {  # info: "car" : {
            "wanted": car.get("wanted"),  # info: "wanted" : car . get ( "wanted" )
            "last_car_on": car.get("last_car_on"),  # info: "last_car_on" : car . get ( "last_car_on" )
            "last_action": car.get("last_action"),  # info: "last_action" : car . get ( "last_action" )
        },  # info: } ,
        "usb_or_sata_present": bool(disks.get("usb_or_sata_present")),  # info: "usb_or_sata_present" : bool ( disks . get (
        "nvme_only": bool(disks.get("nvme_only")),  # info: "nvme_only" : bool ( disks . get (
        "backup_copy": False,  # info: "backup_copy" : False ,
        "note": cfg.get("note"),  # info: "note" : cfg . get ( "note" )
        "state_path": str(state_path()),  # info: "state_path" : str ( state_path ( ) )
        "car_state": load_car_state().get("last_action"),  # info: "car_state" : load_car_state ( ) . get (
    }  # info: }


# ====================================================
# SECTION: function power_on
# What it does: power on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def power_on(*, execute: bool = False, wait_s: int = 20) -> dict[str, Any]:  # info: def power_on
    return prepare(execute=bool(execute), wait_s=wait_s)  # info: return prepare ( execute = bool ( execute


# ====================================================
# SECTION: function power_off
# What it does: power off.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def power_off(*, execute: bool = False) -> dict[str, Any]:  # info: def power_off
    return release(execute=bool(execute))  # info: return release ( execute = bool ( execute


# ====================================================
# SECTION: function session
# What it does: Power on, optional copy stub, power off unless hold or the port was already on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def session(*, execute: bool = False, hold: bool | None = None, wait_s: int = 20) -> dict[str, Any]:  # info: def session
    """Power on, optional copy stub, power off unless hold or the port was already on."""  # info: """Power on, optional copy stub, power off unless hold or the port was already on."""
    cfg = load_config()  # info: set cfg
    hold_on = bool(cfg.get("hold_car_on") if hold is None else hold)  # info: set hold_on
    fh = _try_lock()  # info: set fh
    if fh is None:  # info: if fh is None :
        return {"ok": False, "blocked": "in_progress", "spawned": False}  # info: return { "ok" : False , "blocked" :
    try:  # info: try :
        was_on = last_car_on() is True  # info: set was_on
        on = power_on(execute=bool(execute), wait_s=wait_s)  # info: set on
        report: dict[str, Any] = {  # info: set report
            "ok": bool(on.get("ok")),  # info: "ok" : bool ( on . get (
            "phase": "session",  # info: "phase" : "session" ,
            "execute": bool(execute),  # info: "execute" : bool ( execute ) ,
            "hold": hold_on,  # info: "hold" : hold_on ,
            "was_already_on": was_on,  # info: "was_already_on" : was_on ,
            "power_on": on,  # info: "power_on" : on ,
            "copy": None,  # info: "copy" : None ,
            "power_off": None,  # info: "power_off" : None ,
            "spawned": bool((on.get("car_action") or {}).get("spawned")),  # info: "spawned" : bool ( ( on . get
        }  # info: }
        if not execute:  # info: if not execute :
            report["blocked"] = "dry_run"  # info: report [ "blocked" ] = "dry_run"
            cfg["last_action"] = "dry_run_session"  # info: cfg [ "last_action" ] = "dry_run_session"
            cfg["last_skip"] = "dry_run"  # info: cfg [ "last_skip" ] = "dry_run"
            save_config(cfg)  # info: call save_config
            return report  # info: return report
        if not on.get("ok"):  # info: if not on . get ( "ok" )
            report["blocked"] = "power_on_failed"  # info: report [ "blocked" ] = "power_on_failed"
            cfg["last_action"] = "session_power_on_failed"  # info: cfg [ "last_action" ] = "session_power_on_failed"
            cfg["last_skip"] = on.get("blocked") or "power_on_failed"  # info: cfg [ "last_skip" ] = on . get
            save_config(cfg)  # info: call save_config
            return report  # info: return report
        copy = run_copy_jobs()  # info: set copy
        report["copy"] = copy  # info: report [ "copy" ] = copy
        if hold_on or was_on:  # info: if hold_on or was_on :
            report["power_off"] = {"ok": True, "skipped": "hold" if hold_on else "already_on", "spawned": False}  # info: report [ "power_off" ] = { "ok" :
            report["left_on"] = True  # info: report [ "left_on" ] = True
        else:  # info: else :
            off = power_off(execute=True)  # info: set off
            report["power_off"] = off  # info: report [ "power_off" ] = off
            report["spawned"] = bool(report["spawned"] or off.get("spawned"))  # info: report [ "spawned" ] = bool ( report
            report["ok"] = bool(report["ok"] and off.get("ok"))  # info: report [ "ok" ] = bool ( report
        cfg["last_action"] = "session"  # info: cfg [ "last_action" ] = "session"
        cfg["last_skip"] = copy.get("skipped")  # info: cfg [ "last_skip" ] = copy . get
        cfg["last_tick"] = time.time()  # info: cfg [ "last_tick" ] = time . time
        save_config(cfg)  # info: call save_config
        return report  # info: return report
    finally:  # info: finally :
        try:  # info: try :
            import fcntl  # info: import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)  # info: fcntl . flock ( fh . fileno (
        except Exception:  # info: except Exception :
            pass  # info: pass
        fh.close()  # info: fh . close ( )


# ====================================================
# SECTION: function tick
# What it does: Scheduler entry. No BLE script until auto, a copy job, and copy is implemented.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tick(*, execute: bool = True) -> dict[str, Any]:  # info: def tick
    """Scheduler entry. No BLE script until auto, a copy job, and copy is implemented."""  # info: """Scheduler entry. No BLE script until auto, a copy job, and copy is implemented."""
    cfg = load_config()  # info: set cfg
    cfg["last_tick"] = time.time()  # info: cfg [ "last_tick" ] = time . time
    if not cfg.get("auto"):  # info: if not cfg . get ( "auto" )
        cfg["last_skip"] = "auto_off"  # info: cfg [ "last_skip" ] = "auto_off"
        save_config(cfg)  # info: call save_config
        return {"ok": True, "skipped": "auto_off", "execute": bool(execute), "spawned": False}  # info: return { "ok" : True , "skipped" :
    jobs = enabled_copy_jobs(cfg)  # info: set jobs
    if not jobs:  # info: if not jobs :
        cfg["last_skip"] = "no_copy_jobs"  # info: cfg [ "last_skip" ] = "no_copy_jobs"
        save_config(cfg)  # info: call save_config
        return {"ok": True, "skipped": "no_copy_jobs", "execute": bool(execute), "spawned": False}  # info: return { "ok" : True , "skipped" :
    probe = run_copy_jobs(jobs)  # info: set probe
    if probe.get("skipped") == "copy_not_implemented":  # info: if probe . get ( "skipped" ) ==
        cfg["last_skip"] = "copy_not_implemented"  # info: cfg [ "last_skip" ] = "copy_not_implemented"
        save_config(cfg)  # info: call save_config
        return {  # info: return {
            "ok": True,  # info: "ok" : True ,
            "skipped": "copy_not_implemented",  # info: "skipped" : "copy_not_implemented" ,
            "execute": bool(execute),  # info: "execute" : bool ( execute ) ,
            "pending": probe.get("pending"),  # info: "pending" : probe . get ( "pending" )
            "spawned": False,  # info: "spawned" : False ,
        }  # info: }
    return session(execute=bool(execute), hold=bool(cfg.get("hold_car_on")))  # info: return session ( execute = bool ( execute


# ====================================================
# SECTION: function set_auto
# What it does: set auto.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_auto(on: bool) -> dict[str, Any]:  # info: def set_auto
    cfg = load_config()  # info: set cfg
    cfg["auto"] = bool(on)  # info: cfg [ "auto" ] = bool ( on
    cfg["last_action"] = "auto_on" if on else "auto_off"  # info: cfg [ "last_action" ] = "auto_on" if on
    cfg["last_skip"] = None if on else "auto_off"  # info: cfg [ "last_skip" ] = None if on
    return save_config(cfg)  # info: return save_config ( cfg )


# ====================================================
# SECTION: function _emit
# What it does:  emit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _emit(payload: dict[str, Any]) -> None:  # info: def _emit
    print(json.dumps(payload, indent=2, default=str))  # info: call print
    if payload.get("skipped"):  # info: if payload . get ( "skipped" ) :
        print(f"skipped={payload['skipped']}")  # info: call print


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    import argparse  # info: import argparse

    parser = argparse.ArgumentParser(description="River 2 Pro car DC drive automation (dry-run default).")  # info: set parser
    parser.add_argument("--status", action="store_true")  # info: parser . add_argument ( "--status" , action =
    parser.add_argument("--on", action="store_true", help="Power drives on.")  # info: parser . add_argument ( "--on" , action =
    parser.add_argument("--off", action="store_true", help="Power drives off.")  # info: parser . add_argument ( "--off" , action =
    parser.add_argument("--session", action="store_true", help="On, copy stub, off unless --hold.")  # info: parser . add_argument ( "--session" , action =
    parser.add_argument("--tick", action="store_true", help="Scheduler tick (respects auto).")  # info: parser . add_argument ( "--tick" , action =
    parser.add_argument("--hold", action="store_true", help="Leave car DC on after session.")  # info: parser . add_argument ( "--hold" , action =
    parser.add_argument("--auto", choices=("on", "off"), help="Enable or disable scheduled sessions.")  # info: parser . add_argument ( "--auto" , choices =
    parser.add_argument("--execute", action="store_true", help="Allow the BLE script. Refuses unless RR_RIVER_CAR_EXECUTE=1.")  # info: parser . add_argument ( "--execute" , action =
    args = parser.parse_args(argv)  # info: set args
    if args.auto:  # info: if args . auto :
        _emit(set_auto(args.auto == "on"))  # info: call _emit
        return 0  # info: return 0
    flags = sum(bool(x) for x in (args.on, args.off, args.session, args.tick, args.status))  # info: set flags
    if flags > 1:  # info: if flags > 1 :
        print(json.dumps({"ok": False, "error": "one_action"}))  # info: call print
        return 2  # info: return 2
    if args.execute and not any((args.on, args.off, args.session, args.tick)):  # info: if args . execute and not any (
        print(json.dumps({"ok": False, "error": "refused", "spawned": False}))  # info: call print
        return 1  # info: return 1
    if args.on:  # info: if args . on :
        out = power_on(execute=bool(args.execute))  # info: set out
        _emit(out)  # info: call _emit
        return 0 if out.get("ok") else 1  # info: return 0 if out . get ( "ok"
    if args.off:  # info: if args . off :
        out = power_off(execute=bool(args.execute))  # info: set out
        _emit(out)  # info: call _emit
        return 0 if out.get("ok") else 1  # info: return 0 if out . get ( "ok"
    if args.session:  # info: if args . session :
        out = session(execute=bool(args.execute), hold=bool(args.hold))  # info: set out
        _emit(out)  # info: call _emit
        return 0 if out.get("ok") else 1  # info: return 0 if out . get ( "ok"
    if args.tick:  # info: if args . tick :
        out = tick(execute=bool(args.execute))  # info: set out
        _emit(out)  # info: call _emit
        return 0  # info: return 0
    _emit(status())  # info: call _emit
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
