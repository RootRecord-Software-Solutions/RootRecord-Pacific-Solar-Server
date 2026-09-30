# ==============================================================================
# FILE: Media/SunriseRestore/scripts/sunrise_restore.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Request reconnect clips after night sleep. Does not open a speaker.

  python3 sunrise_restore.py [--dry-run]

Runs only when Database Media/SunriseRestore/pending.json has pending true.
Reads Energy sun times (no network). Asks Report playback for Ava/battery_reconnect
then Ava/boot_all_systems_running. A missing player or a missing clip is skipped.
Clears pending either way. --dry-run never calls the player and sets played false.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
PACIFIC = Path(os.environ.get(  # info: set PACIFIC
    "RR_PACIFIC_ROOT",  # info: "RR_PACIFIC_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server",  # info: "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server" ,
))  # info: ) )
PENDING = DB / "Media" / "SunriseRestore" / "pending.json"  # info: set PENDING
SUN = DB / "Energy" / "sun" / "sun-times-last.json"  # info: set SUN
LOG = DB / "Logs" / "Media" / "SunriseRestore" / "sunrise-restore.log"  # info: set LOG
PLAY = PACIFIC / "Media" / "Playback" / "scripts" / "play.py"  # info: set PLAY
CLIPS = ("battery_reconnect", "boot_all_systems_running")  # info: set CLIPS


# ====================================================
# SECTION: function _now
# What it does:  now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now() -> str:  # info: def _now
    return datetime.now(HST).replace(microsecond=0).isoformat()  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function _read_json
# What it does:  read json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_json(path: Path) -> dict:  # info: def _read_json
    try:  # info: try :
        raw = json.loads(path.read_text(encoding="utf-8"))  # info: set raw
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }
    return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict


# ====================================================
# SECTION: function _write_json
# What it does:  write json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_json(path: Path, payload: dict) -> None:  # info: def _write_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_name(path.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function _log
# What it does:  log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log(row: dict) -> None:  # info: def _log
    LOG.parent.mkdir(parents=True, exist_ok=True)  # info: LOG . parent . mkdir ( parents =
    with LOG.open("a", encoding="utf-8") as fh:  # info: with LOG . open ( "a" , encoding
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")  # info: fh . write ( json . dumps (


# ====================================================
# SECTION: function _sunrise
# What it does:  sunrise.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sunrise() -> str:  # info: def _sunrise
    return str(_read_json(SUN).get("sunrise") or "")  # info: return str ( _read_json ( SUN ) .


# ====================================================
# SECTION: function _request
# What it does:  request.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _request(slug: str, *, dry_run: bool) -> dict:  # info: def _request
    if dry_run or not PLAY.is_file():  # info: if dry_run or not PLAY . is_file (
        return {  # info: return {
            "clip": slug,  # info: "clip" : slug ,
            "played": False,  # info: "played" : False ,
            "reason": None if dry_run else "player_missing",  # info: "reason" : None if dry_run else "player_missing" ,
        }  # info: }
    cmd = [sys.executable, str(PLAY), "--clip", f"Ava/{slug}", "--dry-run"]  # info: set cmd
    try:  # info: try :
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)  # info: set proc
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired )
        return {"clip": slug, "played": False, "reason": type(exc).__name__}  # info: return { "clip" : slug , "played" :
    detail = None  # info: set detail
    line = (proc.stdout or "").strip().splitlines()  # info: set line
    if line:  # info: if line :
        try:  # info: try :
            detail = json.loads(line[-1]).get("detail")  # info: set detail
        except ValueError:  # info: except ValueError :
            detail = None  # info: set detail
    if proc.returncode != 0 and not detail:  # info: if proc . returncode != 0 and not
        detail = f"player_rc_{proc.returncode}"  # info: set detail
    return {"clip": slug, "played": False, "reason": detail}  # info: return { "clip" : slug , "played" :


# ====================================================
# SECTION: function maybe_run
# What it does: maybe run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def maybe_run(*, dry_run: bool = False) -> dict:  # info: def maybe_run
    state = _read_json(PENDING)  # info: set state
    if not state.get("pending"):  # info: if not state . get ( "pending" )
        out = {"ok": True, "skipped": True, "reason": "not_pending", "played": False}  # info: set out
        return out  # info: return out
    clips = [_request(slug, dry_run=dry_run) for slug in CLIPS]  # info: set clips
    cleared = {**state, "pending": False, "cleared_at": _now()}  # info: set cleared
    _write_json(PENDING, cleared)  # info: call _write_json
    out = {  # info: set out
        "ok": True,  # info: "ok" : True ,
        "ran": True,  # info: "ran" : True ,
        "clips": [row["clip"] for row in clips],  # info: "clips" : [ row [ "clip" ] for
        "played": False,  # info: "played" : False ,
        "sunrise": _sunrise(),  # info: "sunrise" : _sunrise ( ) ,
        "player": str(PLAY) if PLAY.is_file() else "missing",  # info: "player" : str ( PLAY ) if PLAY
        "requests": clips,  # info: "requests" : clips ,
    }  # info: }
    _log({"at": _now(), **out})  # info: call _log
    return out  # info: return out


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    out = maybe_run(dry_run="--dry-run" in sys.argv)  # info: set out
    print(json.dumps(out))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
