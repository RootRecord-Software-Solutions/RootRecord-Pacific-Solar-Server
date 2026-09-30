# ==============================================================================
# FILE: Media/MorningBootReplay/scripts/replay.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Replay today's morning boot_brief WAV until noon HST. No TTS. No speaker.

  python3 replay.py arm
  python3 replay.py run --dry-run
  python3 replay.py disarm --reason operator

Hands the WAV to Media/Playback/scripts/play.py --report boot_brief --dry-run.
This folder never passes --play and never calls aplay. Speaker playback stays
off until Alexander signs off on the player.

State: Database Media/MorningBootReplay/replay-last.json
Logs:  Database Logs/Media/MorningBootReplay/replay.log
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[2]  # info: set PACIFIC
DB = Path(os.environ.get(  # info: set DB
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
))  # info: ) )
STATE_DIR = DB / "Media" / "MorningBootReplay"  # info: set STATE_DIR
STATE_PATH = STATE_DIR / "replay-last.json"  # info: set STATE_PATH
OLD_STATE_PATH = STATE_DIR / "morning-boot-replay.json"  # info: set OLD_STATE_PATH
LOG_DIR = DB / "Logs" / "Media" / "MorningBootReplay"  # info: set LOG_DIR
VOICE = DB / "Media" / "Audio" / "Voice"  # info: set VOICE
WAV_NAME = "boot_brief_current.wav"  # info: set WAV_NAME
PLAYER = PACIFIC / "Media" / "Playback" / "scripts" / "play.py"  # info: set PLAYER
DATED = re.compile(r"(20\d{2}-\d{2}-\d{2})")  # info: set DATED


# ====================================================
# SECTION: function now_hst
# What it does: now hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> datetime:  # info: def now_hst
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function _load
# What it does:  load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load() -> dict:  # info: def _load
    for path in (STATE_PATH, OLD_STATE_PATH):  # info: for path in ( STATE_PATH , OLD_STATE_PATH )
        try:  # info: try :
            data = json.loads(path.read_text(encoding="utf-8-sig"))  # info: set data
        except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
            continue  # info: continue
        if isinstance(data, dict):  # info: if isinstance ( data , dict ) :
            return data  # info: return data
    return {}  # info: return { }


# ====================================================
# SECTION: function _save
# What it does: Write replay-last.json in the active last-file shape (same keys as last-play.json, plus arm fields).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save(data: dict) -> None:  # info: def _save
    """Write replay-last.json in the active last-file shape (same keys as last-play.json, plus arm fields)."""  # info: """Write replay-last.json in the active last-file shape (same keys as last-play.json, plus arm fields)."""
    body = dict(data)  # info: set body
    body["at"] = now_hst().isoformat()  # info: body [ "at" ] = now_hst ( )
    body["report"] = "boot_brief"  # info: body [ "report" ] = "boot_brief"
    body["clip"] = None  # info: body [ "clip" ] = None
    body["speaker"] = False  # info: body [ "speaker" ] = False
    wav = body.get("wav") or body.get("path") or str(default_wav())  # info: set wav
    body["wav"] = str(wav)  # info: body [ "wav" ] = str ( wav
    body["path"] = str(wav)  # info: body [ "path" ] = str ( wav
    if "ok" not in body:  # info: if "ok" not in body :
        body["ok"] = bool(body.get("played") or body.get("enabled"))  # info: body [ "ok" ] = bool ( body
    if "played" not in body:  # info: if "played" not in body :
        body["played"] = False  # info: body [ "played" ] = False
    if "detail" not in body:  # info: if "detail" not in body :
        body["detail"] = "armed" if body.get("enabled") else "idle"  # info: body [ "detail" ] = "armed" if body
    STATE_DIR.mkdir(parents=True, exist_ok=True)  # info: STATE_DIR . mkdir ( parents = True ,
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
    with (LOG_DIR / "replay.log").open("a", encoding="utf-8") as fh:  # info: with ( LOG_DIR / "replay.log" ) . open
        fh.write(line + "\n")  # info: fh . write ( line + "\n" )
    print(line)  # info: call print


# ====================================================
# SECTION: function _noon
# What it does:  noon.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _noon(day: datetime) -> datetime:  # info: def _noon
    return day.replace(hour=12, minute=0, second=0, microsecond=0)  # info: return day . replace ( hour = 12


# ====================================================
# SECTION: function midday_done
# What it does: midday done.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def midday_done(today: str) -> bool:  # info: def midday_done
    path = DB / "Reports" / "board" / "daily-reports-due.json"  # info: set path
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return False  # info: return False
    if not isinstance(data, dict) or data.get("day") != today:  # info: if not isinstance ( data , dict )
        return False  # info: return False
    mid = (data.get("slots") or {}).get("midday") or {}  # info: set mid
    return str(mid.get("status") or "") == "done"  # info: return str ( mid . get ( "status"


# ====================================================
# SECTION: function default_wav
# What it does: default wav.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def default_wav() -> Path:  # info: def default_wav
    return (VOICE / WAV_NAME).resolve()  # info: return ( VOICE / WAV_NAME ) . resolve


# ====================================================
# SECTION: function morning_wav
# What it does: Return a refusal reason, or None when the file is today's morning boot WAV.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def morning_wav(path: Path, today: str) -> str | None:  # info: def morning_wav
    """Return a refusal reason, or None when the file is today's morning boot WAV."""  # info: """Return a refusal reason, or None when the file is today's morning boot WAV."""
    voice = VOICE.resolve()  # info: set voice
    try:  # info: try :
        if not path.is_relative_to(voice):  # info: if not path . is_relative_to ( voice )
            return "outside_voice"  # info: return "outside_voice"
    except ValueError:  # info: except ValueError :
        return "outside_voice"  # info: return "outside_voice"
    if not path.is_file() or path.stat().st_size <= 0:  # info: if not path . is_file ( ) or
        return "wav_missing"  # info: return "wav_missing"
    low = path.name.lower()  # info: set low
    if "midday" in low or "evening" in low or "late-report" in low:  # info: if "midday" in low or "evening" in low
        return "wrong_wav_type"  # info: return "wrong_wav_type"
    dated = DATED.search(path.name)  # info: set dated
    if dated and dated.group(1) != today:  # info: if dated and dated . group ( 1
        return "stale_wav_day"  # info: return "stale_wav_day"
    try:  # info: try :
        mt = datetime.fromtimestamp(path.stat().st_mtime, HST)  # info: set mt
    except OSError:  # info: except OSError :
        return "wav_stat_failed"  # info: return "wav_stat_failed"
    if mt.strftime("%Y-%m-%d") != today or mt.hour >= 12:  # info: if mt . strftime ( "%Y-%m-%d" ) !=
        return "stale_wav_mtime"  # info: return "stale_wav_mtime"
    return None  # info: return None


# ====================================================
# SECTION: function disarm
# What it does: disarm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def disarm(reason: str) -> dict:  # info: def disarm
    now = now_hst()  # info: set now
    st = _load()  # info: set st
    if not st:  # info: if not st :
        result = {"ok": True, "skipped": True, "reason": "no_state"}  # info: set result
        _log(result)  # info: call _log
        return result  # info: return result
    was = bool(st.get("enabled"))  # info: set was
    st["enabled"] = False  # info: st [ "enabled" ] = False
    st["play_once"] = False  # info: st [ "play_once" ] = False
    st["stopped_at"] = now.isoformat()  # info: st [ "stopped_at" ] = now . isoformat
    st["stop_reason"] = str(reason or "operator")[:160]  # info: st [ "stop_reason" ] = str ( reason
    _save(st)  # info: call _save
    result = {"ok": True, "disarmed": True, "was_enabled": was, "reason": st["stop_reason"]}  # info: set result
    _log(result)  # info: call _log
    return result  # info: return result


# ====================================================
# SECTION: function arm
# What it does: arm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def arm() -> dict:  # info: def arm
    now = now_hst()  # info: set now
    today = now.strftime("%Y-%m-%d")  # info: set today
    path = default_wav()  # info: set path
    why = morning_wav(path, today)  # info: set why
    if why:  # info: if why :
        result = {"ok": False, "armed": False, "played": False, "detail": why, "wav": str(path), "speaker": False}  # info: set result
        _save({"enabled": False, "played": False, "detail": why, "wav": str(path), "speaker": False})  # info: call _save
        _log(result)  # info: call _log
        return result  # info: return result
    st = _load()  # info: set st
    st.update({  # info: st . update ( {
        "enabled": True,  # info: "enabled" : True ,
        "ok": True,  # info: "ok" : True ,
        "played": False,  # info: "played" : False ,
        "detail": "armed",  # info: "detail" : "armed" ,
        "day": today,  # info: "day" : today ,
        "until": _noon(now).isoformat(),  # info: "until" : _noon ( now ) . isoformat
        "play_once": False,  # info: "play_once" : False ,
        "wav": str(path),  # info: "wav" : str ( path ) ,
        "current": str(path),  # info: "current" : str ( path ) ,
        "armed_at": now.isoformat(),  # info: "armed_at" : now . isoformat ( ) ,
    })  # info: } )
    st.pop("stopped_at", None)  # info: st . pop ( "stopped_at" , None )
    st.pop("stop_reason", None)  # info: st . pop ( "stop_reason" , None )
    _save(st)  # info: call _save
    result = {"ok": True, "armed": True, "day": today, "until": st["until"], "wav": str(path)}  # info: set result
    _log(result)  # info: call _log
    return result  # info: return result


# ====================================================
# SECTION: function _handoff
# What it does:  handoff.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _handoff(path: Path) -> dict:  # info: def _handoff
    if not PLAYER.is_file():  # info: if not PLAYER . is_file ( ) :
        return {"ok": False, "detail": "report_playback_missing", "function": "Report playback"}  # info: return { "ok" : False , "detail" :
    proc = subprocess.run(  # info: set proc
        [sys.executable, str(PLAYER), "--report", "boot_brief", "--dry-run"],  # info: [ sys . executable , str ( PLAYER
        capture_output=True,  # info: set capture_output
        text=True,  # info: set text
        timeout=60,  # info: set timeout
        env=os.environ.copy(),  # info: set env
    )  # info: )
    last = (proc.stdout or "").strip().splitlines()  # info: set last
    try:  # info: try :
        body = json.loads(last[-1]) if last else {}  # info: set body
    except ValueError:  # info: except ValueError :
        body = {"detail": "player_output"}  # info: set body
    body["rc"] = proc.returncode  # info: body [ "rc" ] = proc . returncode
    if path.name != WAV_NAME:  # info: if path . name != WAV_NAME :
        body["note"] = "player reads boot_brief_current.wav"  # info: body [ "note" ] = "player reads boot_brief_current.wav"
    return body  # info: return body


# ====================================================
# SECTION: function run
# What it does: Decide, then hand off with --dry-run. dry_run is always the speaker mode.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run(dry_run: bool = True) -> dict:  # info: def run
    """Decide, then hand off with --dry-run. dry_run is always the speaker mode."""  # info: """Decide, then hand off with --dry-run. dry_run is always the speaker mode."""
    del dry_run  # this folder never opens a speaker
    now = now_hst()  # info: set now
    today = now.strftime("%Y-%m-%d")  # info: set today
    st = _load()  # info: set st
    if not st.get("enabled"):  # info: if not st . get ( "enabled" )
        # A disarm for today stays off. A new morning WAV may arm once.
        if str(st.get("day") or "") == today or midday_done(today):  # info: if str ( st . get ( "day"
            result = {"ok": True, "skipped": True, "reason": "disabled"}  # info: set result
            _log(result)  # info: call _log
            return result  # info: return result
        armed = arm()  # info: set armed
        if not armed.get("armed"):  # info: if not armed . get ( "armed" )
            return armed  # info: return armed
        st = _load()  # info: set st

    until_raw = str(st.get("until") or "").strip()  # info: set until_raw
    try:  # info: try :
        until = datetime.fromisoformat(until_raw)  # info: set until
        if until.tzinfo is None:  # info: if until . tzinfo is None :
            until = until.replace(tzinfo=HST)  # info: set until
    except ValueError:  # info: except ValueError :
        until = _noon(now)  # info: set until
    noon = _noon(until)  # info: set noon
    if until > noon:  # info: if until > noon :
        until = noon  # info: set until
    if now >= until:  # info: if now >= until :
        return disarm("past_until")  # info: return disarm ( "past_until" )

    armed_day = str(st.get("day") or st.get("armed_day") or "").strip()  # info: set armed_day
    if not armed_day:  # info: if not armed_day :
        for key in ("until", "armed_at"):  # info: for key in ( "until" , "armed_at" )
            raw = str(st.get(key) or "")  # info: set raw
            if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":  # info: if len ( raw ) >= 10 and
                armed_day = raw[:10]  # info: set armed_day
                break  # info: break
    if armed_day and armed_day != today:  # info: if armed_day and armed_day != today :
        return disarm("stale_day")  # info: return disarm ( "stale_day" )

    if midday_done(today):  # info: if midday_done ( today ) :
        return disarm("midday_ok")  # info: return disarm ( "midday_ok" )

    play_once = bool(st.get("play_once"))  # info: set play_once
    if not play_once and now.minute != 32:  # info: if not play_once and now . minute !=
        result = {"ok": True, "skipped": True, "reason": "not_:32"}  # info: set result
        _log(result)  # info: call _log
        return result  # info: return result

    path = default_wav()  # info: set path
    why = morning_wav(path, today)  # info: set why
    if why in {"wrong_wav_type", "stale_wav_day", "stale_wav_mtime"}:  # info: if why in { "wrong_wav_type" , "stale_wav_day" ,
        return disarm(why)  # info: return disarm ( why )
    if why:  # info: if why :
        result = {"ok": False, "played": False, "detail": why, "wav": str(path)}  # info: set result
        _log(result)  # info: call _log
        return result  # info: return result

    player = _handoff(path)  # info: set player
    # play.py reports audio_missing with ok=true. Only a dry-run of the real file counts.
    if player.get("rc") != 0 or player.get("detail") != "dry_run":  # info: if player . get ( "rc" ) !=
        result = {"ok": False, "played": False, "detail": player.get("detail") or "player_failed", "player": player, "wav": str(path)}  # info: set result
        _log(result)  # info: call _log
        return result  # info: return result

    st["play_once"] = False  # info: st [ "play_once" ] = False
    st["ok"] = True  # info: st [ "ok" ] = True
    st["played"] = True  # info: st [ "played" ] = True
    st["detail"] = "dry_run"  # info: st [ "detail" ] = "dry_run"
    st["speaker"] = False  # info: st [ "speaker" ] = False
    st["last_played_at"] = now.isoformat()  # info: st [ "last_played_at" ] = now . isoformat
    st["last_played"] = str(path)  # info: st [ "last_played" ] = str ( path
    _save(st)  # info: call _save
    result = {  # info: set result
        "ok": True,  # info: "ok" : True ,
        "played": True,  # info: "played" : True ,
        "wav": str(path),  # info: "wav" : str ( path ) ,
        "play_once_cleared": play_once,  # info: "play_once_cleared" : play_once ,
        "player": player.get("detail"),  # info: "player" : player . get ( "detail" )
        "speaker": False,  # info: "speaker" : False ,
    }  # info: }
    _log(result)  # info: call _log
    return result  # info: return result


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(sys.argv[1:] if argv is None else argv)  # info: set args
    cmd = "run"  # info: set cmd
    if args and args[0] in {"arm", "run", "disarm"}:  # info: if args and args [ 0 ] in
        cmd = args.pop(0)  # info: set cmd
    reason = "operator"  # info: set reason
    if "--reason" in args:  # info: if "--reason" in args :
        i = args.index("--reason")  # info: set i
        if i + 1 < len(args):  # info: if i + 1 < len ( args
            reason = args[i + 1]  # info: set reason
    if cmd == "arm":  # info: if cmd == "arm" :
        result = arm()  # info: set result
    elif cmd == "disarm":  # info: elif cmd == "disarm" :
        result = disarm(reason)  # info: set result
    else:  # info: else :
        result = run(dry_run=True)  # info: set result
    return 0 if result.get("ok") else 1  # info: return 0 if result . get ( "ok"


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
