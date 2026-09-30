# ==============================================================================
# FILE: Media/Playback/scripts/play.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Play one Kokoro WAV already on disk. Speakers stay closed unless gated.

  python3 play.py --report NAME [--dry-run | --play] [--force]
  python3 play.py --clip Persona/slug [--dry-run | --play] [--force]

Default is --dry-run. That writes last-play.json and does not open a device.
Live play needs both RR_PLAYBACK=1 and --play, then uses aplay.
Quiet hours 22:00–06:00 HST skip a live play unless --force.
--force does not bypass RR_PLAYBACK. A second caller gets busy.
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import fcntl  # info: import fcntl
import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get(  # info: set DB
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
))  # info: ) )
VOICE = DB / "Media" / "Audio" / "Voice"  # info: set VOICE
STATE = DB / "Media" / "Playback"  # info: set STATE
LOG_DIR = DB / "Logs" / "Media" / "Playback"  # info: set LOG_DIR
LAST = STATE / "last-play.json"  # info: set LAST
LOCK = STATE / "play.lock"  # info: set LOCK
PERSONAS = {"Ava", "Bruce", "Carly"}  # info: set PERSONAS
NAME = re.compile(r"[A-Za-z0-9_-]+")  # info: set NAME
CLIP = re.compile(r"(Ava|Bruce|Carly)/[A-Za-z0-9_-]+")  # info: set CLIP


# ====================================================
# SECTION: function now_hst
# What it does: now hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> datetime:  # info: def now_hst
    return datetime.now(HST)  # info: return datetime . now ( HST )


# ====================================================
# SECTION: function quiet_hours
# What it does: quiet hours.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def quiet_hours(now: datetime | None = None) -> bool:  # info: def quiet_hours
    hour = (now or now_hst()).hour  # info: set hour
    return hour >= 22 or hour < 6  # info: return hour >= 22 or hour < 6


# ====================================================
# SECTION: function resolve
# What it does: Map a report name or Persona/slug onto a WAV under Voice. Refuse anything else.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def resolve(report: str | None, clip: str | None) -> Path:  # info: def resolve
    """Map a report name or Persona/slug onto a WAV under Voice. Refuse anything else."""  # info: """Map a report name or Persona/slug onto a WAV under Voice. Refuse anything else."""
    if bool(report) == bool(clip):  # info: if bool ( report ) == bool (
        raise ValueError("pass one of --report or --clip")  # info: raise ValueError ( "pass one of --report or --clip" )
    if report is not None:  # info: if report is not None :
        if not NAME.fullmatch(report):  # info: if not NAME . fullmatch ( report )
            raise ValueError("refused")  # info: raise ValueError ( "refused" )
        path = (VOICE / f"{report}_current.wav").resolve()  # info: set path
    else:  # info: else :
        if not CLIP.fullmatch(clip or ""):  # info: if not CLIP . fullmatch ( clip or
            raise ValueError("refused")  # info: raise ValueError ( "refused" )
        persona, slug = (clip or "").split("/", 1)  # info: persona , slug = ( clip or ""
        if persona not in PERSONAS:  # info: if persona not in PERSONAS :
            raise ValueError("refused")  # info: raise ValueError ( "refused" )
        path = (VOICE / "Clips" / persona / f"{slug}.wav").resolve()  # info: set path
    voice = VOICE.resolve()  # info: set voice
    if not path.is_relative_to(voice):  # info: if not path . is_relative_to ( voice )
        raise ValueError("refused")  # info: raise ValueError ( "refused" )
    return path  # info: return path


# ====================================================
# SECTION: function emit
# What it does: emit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def emit(payload: dict, code: int, *, state: bool = True) -> int:  # info: def emit
    STATE.mkdir(parents=True, exist_ok=True)  # info: STATE . mkdir ( parents = True ,
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    body = dict(payload)  # info: set body
    body["at"] = now_hst().isoformat()  # info: body [ "at" ] = now_hst ( )
    if state:  # info: if state :
        LAST.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")  # info: LAST . write_text ( json . dumps (
    line = json.dumps(body, ensure_ascii=False)  # info: set line
    with (LOG_DIR / "playback.log").open("a", encoding="utf-8") as fh:  # info: with ( LOG_DIR / "playback.log" ) . open
        fh.write(line + "\n")  # info: fh . write ( line + "\n" )
    print(line)  # info: call print
    return code  # info: return code


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    parser = argparse.ArgumentParser(description="Play one existing Kokoro WAV.")  # info: set parser
    parser.add_argument("--report", help="Voice/<name>_current.wav")  # info: parser . add_argument ( "--report" , help =
    parser.add_argument("--clip", help="Voice/Clips/<Persona>/<slug>.wav")  # info: parser . add_argument ( "--clip" , help =
    mode = parser.add_mutually_exclusive_group()  # info: set mode
    mode.add_argument("--dry-run", action="store_true", help="Record intent. Do not open a device.")  # info: mode . add_argument ( "--dry-run" , action =
    mode.add_argument("--play", action="store_true", help="Open the speaker. Needs RR_PLAYBACK=1.")  # info: mode . add_argument ( "--play" , action =
    parser.add_argument("--force", action="store_true", help="Allow live play during quiet hours.")  # info: parser . add_argument ( "--force" , action =
    args = parser.parse_args(argv)  # info: set args
    dry = not args.play  # info: set dry

    try:  # info: try :
        path = resolve(args.report, args.clip)  # info: set path
    except ValueError as exc:  # info: except ValueError as exc :
        detail = "refused" if str(exc) == "refused" else "bad_args"  # info: set detail
        return emit({  # info: return emit ( {
            "ok": False,  # info: "ok" : False ,
            "played": False,  # info: "played" : False ,
            "detail": detail,  # info: "detail" : detail ,
            "report": args.report,  # info: "report" : args . report ,
            "clip": args.clip,  # info: "clip" : args . clip ,
        }, 1)  # info: } , 1 )

    STATE.mkdir(parents=True, exist_ok=True)  # info: STATE . mkdir ( parents = True ,
    lock_fh = LOCK.open("a", encoding="utf-8")  # info: set lock_fh
    try:  # info: try :
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: fcntl . flock ( lock_fh . fileno (
    except BlockingIOError:  # info: except BlockingIOError :
        lock_fh.close()  # info: lock_fh . close ( )
        # Do not overwrite last-play.json. The holder of the lock owns that file.
        return emit({  # info: return emit ( {
            "ok": True,  # info: "ok" : True ,
            "played": False,  # info: "played" : False ,
            "detail": "busy",  # info: "detail" : "busy" ,
            "report": args.report,  # info: "report" : args . report ,
            "clip": args.clip,  # info: "clip" : args . clip ,
            "path": str(path),  # info: "path" : str ( path ) ,
        }, 3, state=False)  # info: } , 3 , state = False )

    present = path.is_file() and path.stat().st_size > 0  # info: set present
    base = {  # info: set base
        "report": args.report,  # info: "report" : args . report ,
        "clip": args.clip,  # info: "clip" : args . clip ,
        "path": str(path),  # info: "path" : str ( path ) ,
        "played": False,  # info: "played" : False ,
    }  # info: }
    try:  # info: try :
        if dry:  # info: if dry :
            base["ok"] = True  # info: base [ "ok" ] = True
            base["detail"] = "dry_run" if present else "audio_missing"  # info: base [ "detail" ] = "dry_run" if present
            return emit(base, 0)  # info: return emit ( base , 0 )

        if os.environ.get("RR_PLAYBACK", "0") != "1":  # info: if os . environ . get ( "RR_PLAYBACK"
            base["ok"] = False  # info: base [ "ok" ] = False
            base["detail"] = "playback_gated"  # info: base [ "detail" ] = "playback_gated"
            return emit(base, 2)  # info: return emit ( base , 2 )

        if quiet_hours() and not args.force:  # info: if quiet_hours ( ) and not args .
            base["ok"] = True  # info: base [ "ok" ] = True
            base["detail"] = "quiet_hours"  # info: base [ "detail" ] = "quiet_hours"
            return emit(base, 0)  # info: return emit ( base , 0 )

        if not present:  # info: if not present :
            base["ok"] = True  # info: base [ "ok" ] = True
            base["detail"] = "audio_missing"  # info: base [ "detail" ] = "audio_missing"
            return emit(base, 0)  # info: return emit ( base , 0 )

        try:  # info: try :
            subprocess.run(["aplay", "-q", str(path)], check=True)  # info: subprocess . run ( [ "aplay" , "-q"
        except (OSError, subprocess.CalledProcessError) as exc:  # info: except ( OSError , subprocess . CalledProcessError )
            base["ok"] = False  # info: base [ "ok" ] = False
            base["detail"] = "play_failed"  # info: base [ "detail" ] = "play_failed"
            base["error"] = str(exc)[:200]  # info: base [ "error" ] = str ( exc
            return emit(base, 1)  # info: return emit ( base , 1 )

        base["ok"] = True  # info: base [ "ok" ] = True
        base["played"] = True  # info: base [ "played" ] = True
        base["detail"] = "played"  # info: base [ "detail" ] = "played"
        return emit(base, 0)  # info: return emit ( base , 0 )
    finally:  # info: finally :
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)  # info: fcntl . flock ( lock_fh . fileno (
        lock_fh.close()  # info: lock_fh . close ( )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
