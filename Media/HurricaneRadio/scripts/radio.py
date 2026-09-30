# ==============================================================================
# FILE: Media/HurricaneRadio/scripts/radio.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Hand the hurricane desk WAV to Report playback. No speaker.

  python3 radio.py run

Always passes --dry-run. Never calls aplay. Never loads Kokoro.
Skips with night_sleep when System/NightSleep says sleeping.
A missing player is player_missing. A missing WAV is audio_missing.
A busy player is the overlap skip.

State: Database Media/HurricaneRadio/last-radio.json
Logs:  Database Logs/Media/HurricaneRadio/radio.log
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
PACIFIC = Path(os.environ.get(  # info: set PACIFIC
    "RR_PACIFIC_ROOT",  # info: "RR_PACIFIC_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server",  # info: "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server" ,
))  # info: ) )
DB = Path(os.environ.get(  # info: set DB
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
))  # info: ) )
STATE_DIR = DB / "Media" / "HurricaneRadio"  # info: set STATE_DIR
STATE_PATH = STATE_DIR / "last-radio.json"  # info: set STATE_PATH
LOG_DIR = DB / "Logs" / "Media" / "HurricaneRadio"  # info: set LOG_DIR
LOG_PATH = LOG_DIR / "radio.log"  # info: set LOG_PATH
PLAYER = PACIFIC / "Media" / "Playback" / "scripts" / "play.py"  # info: set PLAYER
NIGHT = PACIFIC / "System" / "NightSleep" / "scripts" / "night_sleep.py"  # info: set NIGHT
REPORT = "hurricane_desk"  # info: set REPORT


# ====================================================
# SECTION: function now_hst
# What it does: now hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> datetime:  # info: def now_hst
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function _write_state
# What it does:  write state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_state(payload: dict) -> None:  # info: def _write_state
    STATE_DIR.mkdir(parents=True, exist_ok=True)  # info: STATE_DIR . mkdir ( parents = True ,
    body = dict(payload)  # info: set body
    body["at"] = now_hst().isoformat()  # info: body [ "at" ] = now_hst ( )
    tmp = STATE_PATH.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, STATE_PATH)  # info: os . replace ( tmp , STATE_PATH )


# ====================================================
# SECTION: function _log
# What it does:  log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log(payload: dict) -> None:  # info: def _log
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    line = json.dumps(payload, ensure_ascii=False)  # info: set line
    with LOG_PATH.open("a", encoding="utf-8") as fh:  # info: with LOG_PATH . open ( "a" , encoding
        fh.write(line + "\n")  # info: fh . write ( line + "\n" )
    print(line)  # info: call print


# ====================================================
# SECTION: function night_sleeping
# What it does: Read NightSleep.sleeping. Missing module or a bad file means not sleeping.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def night_sleeping() -> bool:  # info: def night_sleeping
    """Read NightSleep.sleeping. Missing module or a bad file means not sleeping."""  # info: """Read NightSleep.sleeping. Missing module or a bad file means not sleeping."""
    if not NIGHT.is_file():  # info: if not NIGHT . is_file ( ) :
        return False  # info: return False
    spec = importlib.util.spec_from_file_location("rr_night_sleep", NIGHT)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader
        return False  # info: return False
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    return bool(mod.sleeping())  # info: return bool ( mod . sleeping ( )


# ====================================================
# SECTION: function _handoff
# What it does:  handoff.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _handoff() -> dict:  # info: def _handoff
    proc = subprocess.run(  # info: set proc
        [sys.executable, str(PLAYER), "--report", REPORT, "--dry-run"],  # info: [ sys . executable , str ( PLAYER
        capture_output=True,  # info: set capture_output
        text=True,  # info: set text
        timeout=30,  # info: set timeout
        check=False,  # info: set check
        env=os.environ.copy(),  # info: set env
    )  # info: )
    detail = None  # info: set detail
    played = False  # info: set played
    line = (proc.stdout or "").strip().splitlines()  # info: set line
    if line:  # info: if line :
        try:  # info: try :
            body = json.loads(line[-1])  # info: set body
        except ValueError:  # info: except ValueError :
            body = {}  # info: set body
        detail = body.get("detail")  # info: set detail
        played = bool(body.get("played"))  # info: set played
    if proc.returncode != 0 and not detail:  # info: if proc . returncode != 0 and not
        detail = f"player_rc_{proc.returncode}"  # info: set detail
    return {"detail": detail, "played": played, "rc": proc.returncode}  # info: return { "detail" : detail , "played" :


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run() -> dict:  # info: def run
    if night_sleeping():  # info: if night_sleeping ( ) :
        result = {"ok": True, "played": False, "detail": "night_sleep", "report": REPORT}  # info: set result
        _write_state(result)  # info: call _write_state
        _log(result)  # info: call _log
        return result  # info: return result

    if not PLAYER.is_file():  # info: if not PLAYER . is_file ( ) :
        result = {  # info: set result
            "ok": False,  # info: "ok" : False ,
            "played": False,  # info: "played" : False ,
            "detail": "player_missing",  # info: "detail" : "player_missing" ,
            "function": "Report playback",  # info: "function" : "Report playback" ,
            "report": REPORT,  # info: "report" : REPORT ,
        }  # info: }
        _write_state(result)  # info: call _write_state
        _log(result)  # info: call _log
        return result  # info: return result

    player = _handoff()  # info: set player
    detail = str(player.get("detail") or "player_output")  # info: set detail
    result = {  # info: set result
        "ok": player.get("rc") in {0, 3},  # info: "ok" : player . get ( "rc" )
        "played": False,  # info: "played" : False ,
        "detail": detail,  # info: "detail" : detail ,
        "report": REPORT,  # info: "report" : REPORT ,
        "speaker": False,  # info: "speaker" : False ,
    }  # info: }
    _write_state(result)  # info: call _write_state
    _log(result)  # info: call _log
    return result  # info: return result


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(sys.argv[1:] if argv is None else argv)  # info: set args
    if args and args[0] not in {"run"}:  # info: if args and args [ 0 ] not
        result = {"ok": False, "played": False, "detail": "bad_args"}  # info: set result
        _log(result)  # info: call _log
        return 1  # info: return 1
    result = run()  # info: set result
    return 0 if result.get("ok") else 1  # info: return 0 if result . get ( "ok"


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
