# ==============================================================================
# FILE: Media/CloudTTS/scripts/route.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Route one spoken line to Kokoro or a gated cloud voice. No speaker.

  python3 -m CloudTTS --engine kokoro
  python3 -m CloudTTS --engine ara
  python3 -m CloudTTS --engine ara --speak   # needs RR_CLOUD_TTS=1

Default engine is kokoro. That writes a route record and does not render.
--engine ara stays gated unless both RR_CLOUD_TTS=1 and --speak are set.
The live path posts to xAI TTS (voice id ara) and does not open a speaker.
Cursor is a text queue in the old synth script. This router does not call it.

State: Database Media/CloudTTS/last-route.json
Logs:  Database Logs/Media/CloudTTS/route.log
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import fcntl  # info: import fcntl
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[2]  # info: set PACIFIC
PLAYBACK = PACIFIC / "Media" / "Playback"  # info: set PLAYBACK
DB = Path(os.environ.get(  # info: set DB
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
))  # info: ) )
STATE = DB / "Media" / "CloudTTS"  # info: set STATE
LOG_DIR = DB / "Logs" / "Media" / "CloudTTS"  # info: set LOG_DIR
LAST = STATE / "last-route.json"  # info: set LAST
LOCK = STATE / "route.lock"  # info: set LOCK
AUDIO = STATE / "ara-last.mp3"  # info: set AUDIO
TTS_URL = "https://api.x.ai/v1/tts"  # info: set TTS_URL
VOICE_ID = "ara"  # info: set VOICE_ID
MAX_CHARS = 2000  # info: set MAX_CHARS

try:  # info: try :
    from .envload import load_env  # info: from . envload import load_env
except ImportError:  # info: except ImportError :
    from envload import load_env  # info: from envload import load_env


# ====================================================
# SECTION: function now_hst
# What it does: now hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> datetime:  # info: def now_hst
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


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
    body["speaker"] = False  # info: body [ "speaker" ] = False
    if state:  # info: if state :
        LAST.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")  # info: LAST . write_text ( json . dumps (
    line = json.dumps(body, ensure_ascii=False)  # info: set line
    with (LOG_DIR / "route.log").open("a", encoding="utf-8") as fh:  # info: with ( LOG_DIR / "route.log" ) . open
        fh.write(line + "\n")  # info: fh . write ( line + "\n" )
    print(line)  # info: call print
    return code  # info: return code


# ====================================================
# SECTION: function gated
# What it does: gated.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def gated(engine: str) -> dict:  # info: def gated
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "engine": engine,  # info: "engine" : engine ,
        "called": False,  # info: "called" : False ,
        "detail": "gated",  # info: "detail" : "gated" ,
        "speaker": False,  # info: "speaker" : False ,
    }  # info: }


# ====================================================
# SECTION: function speak_ara
# What it does: Post to xAI only when the caller has already passed both gates.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speak_ara(text: str) -> dict:  # info: def speak_ara
    """Post to xAI only when the caller has already passed both gates."""  # info: """Post to xAI only when the caller has already passed both gates."""
    if os.environ.get("RR_CLOUD_TTS", "0") != "1":  # info: if os . environ . get ( "RR_CLOUD_TTS"
        return gated("ara")  # info: return gated ( "ara" )
    spoken = " ".join((text or "").split()).strip()  # info: set spoken
    base = {"engine": "ara", "speaker": False, "called": False}  # info: set base
    if not spoken:  # info: if not spoken :
        base["ok"] = False  # info: base [ "ok" ] = False
        base["detail"] = "empty_text"  # info: base [ "detail" ] = "empty_text"
        return base  # info: return base
    if len(spoken) > MAX_CHARS:  # info: if len ( spoken ) > MAX_CHARS :
        base["ok"] = False  # info: base [ "ok" ] = False
        base["detail"] = "over_cap"  # info: base [ "detail" ] = "over_cap"
        return base  # info: return base
    load_env()  # info: call load_env
    key = (os.environ.get("XAI_API_KEY") or "").strip()  # info: set key
    if not key:  # info: if not key :
        base["ok"] = False  # info: base [ "ok" ] = False
        base["detail"] = "key_missing"  # info: base [ "detail" ] = "key_missing"
        return base  # info: return base
    payload = {  # info: set payload
        "text": spoken,  # info: "text" : spoken ,
        "voice_id": VOICE_ID,  # info: "voice_id" : VOICE_ID ,
        "language": "en",  # info: "language" : "en" ,
        "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 128000},  # info: "output_format" : { "codec" : "mp3" , "sample_rate"
        "text_normalization": True,  # info: "text_normalization" : True ,
    }  # info: }
    req = urllib.request.Request(  # info: set req
        TTS_URL,  # info: TTS_URL ,
        data=json.dumps(payload).encode("utf-8"),  # info: set data
        headers={  # info: set headers
            "Authorization": f"Bearer {key}",  # info: "Authorization" : f" Bearer { key } "
            "Content-Type": "application/json",  # info: "Content-Type" : "application/json" ,
        },  # info: } ,
        method="POST",  # info: set method
    )  # info: )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=90) as resp:  # info: with urllib . request . urlopen ( req
            body = resp.read()  # info: set body
            status = getattr(resp, "status", 200)  # info: set status
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        return {  # info: return {
            "ok": False,  # info: "ok" : False ,
            "engine": "ara",  # info: "engine" : "ara" ,
            "called": True,  # info: "called" : True ,
            "detail": "http_error",  # info: "detail" : "http_error" ,
            "status": exc.code,  # info: "status" : exc . code ,
            "speaker": False,  # info: "speaker" : False ,
        }  # info: }
    except (urllib.error.URLError, TimeoutError, OSError):  # info: except ( urllib . error . URLError ,
        return {  # info: return {
            "ok": False,  # info: "ok" : False ,
            "engine": "ara",  # info: "engine" : "ara" ,
            "called": True,  # info: "called" : True ,
            "detail": "http_error",  # info: "detail" : "http_error" ,
            "speaker": False,  # info: "speaker" : False ,
        }  # info: }
    if status != 200 or len(body) < 1000:  # info: if status != 200 or len ( body
        return {  # info: return {
            "ok": False,  # info: "ok" : False ,
            "engine": "ara",  # info: "engine" : "ara" ,
            "called": True,  # info: "called" : True ,
            "detail": "tiny_audio",  # info: "detail" : "tiny_audio" ,
            "speaker": False,  # info: "speaker" : False ,
        }  # info: }
    STATE.mkdir(parents=True, exist_ok=True)  # info: STATE . mkdir ( parents = True ,
    tmp = AUDIO.with_suffix(".mp3.tmp")  # info: set tmp
    tmp.write_bytes(body)  # info: tmp . write_bytes ( body )
    os.replace(tmp, AUDIO)  # info: os . replace ( tmp , AUDIO )
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "engine": "ara",  # info: "engine" : "ara" ,
        "called": True,  # info: "called" : True ,
        "detail": "ara",  # info: "detail" : "ara" ,
        "path": str(AUDIO),  # info: "path" : str ( AUDIO ) ,
        "bytes": len(body),  # info: "bytes" : len ( body ) ,
        "speaker": False,  # info: "speaker" : False ,
    }  # info: }


# ====================================================
# SECTION: function route
# What it does: Choose an engine. Cloud audio stays closed unless both gates are on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def route(engine: str | None, *, speak: bool = False, text: str = "") -> dict:  # info: def route
    """Choose an engine. Cloud audio stays closed unless both gates are on."""  # info: """Choose an engine. Cloud audio stays closed unless both gates are on."""
    name = (engine or "kokoro").strip().lower()  # info: set name
    if name == "kokoro":  # info: if name == "kokoro" :
        return {  # info: return {
            "ok": True,  # info: "ok" : True ,
            "engine": "kokoro",  # info: "engine" : "kokoro" ,
            "called": False,  # info: "called" : False ,
            "detail": "kokoro_local",  # info: "detail" : "kokoro_local" ,
            "speaker": False,  # info: "speaker" : False ,
        }  # info: }
    if name == "cursor":  # info: if name == "cursor" :
        return {  # info: return {
            "ok": True,  # info: "ok" : True ,
            "engine": "cursor",  # info: "engine" : "cursor" ,
            "called": False,  # info: "called" : False ,
            "detail": "cursor_is_text_queue",  # info: "detail" : "cursor_is_text_queue" ,
            "speaker": False,  # info: "speaker" : False ,
        }  # info: }
    if name != "ara":  # info: if name != "ara" :
        return {  # info: return {
            "ok": False,  # info: "ok" : False ,
            "engine": name,  # info: "engine" : name ,
            "called": False,  # info: "called" : False ,
            "detail": "refused",  # info: "detail" : "refused" ,
            "speaker": False,  # info: "speaker" : False ,
        }  # info: }
    if not speak or os.environ.get("RR_CLOUD_TTS", "0") != "1":  # info: if not speak or os . environ .
        return gated("ara")  # info: return gated ( "ara" )
    return speak_ara(text)  # info: return speak_ara ( text )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    parser = argparse.ArgumentParser(description="Route one line to Kokoro or gated Ara.")  # info: set parser
    parser.add_argument("--engine", default="kokoro", help="kokoro (default), ara, or cursor")  # info: parser . add_argument ( "--engine" , default =
    parser.add_argument("--speak", action="store_true", help="Cloud call. Needs RR_CLOUD_TTS=1.")  # info: parser . add_argument ( "--speak" , action =
    parser.add_argument("--text", default="", help="Spoken text. Used only on the live Ara path.")  # info: parser . add_argument ( "--text" , default =
    args = parser.parse_args(argv)  # info: set args

    if not PLAYBACK.is_dir():  # info: if not PLAYBACK . is_dir ( ) :
        return emit({  # info: return emit ( {
            "ok": False,  # info: "ok" : False ,
            "engine": args.engine,  # info: "engine" : args . engine ,
            "called": False,  # info: "called" : False ,
            "detail": "dependency_missing",  # info: "detail" : "dependency_missing" ,
            "dependency": "Report playback",  # info: "dependency" : "Report playback" ,
            "speaker": False,  # info: "speaker" : False ,
        }, 1)  # info: } , 1 )

    STATE.mkdir(parents=True, exist_ok=True)  # info: STATE . mkdir ( parents = True ,
    lock_fh = LOCK.open("a", encoding="utf-8")  # info: set lock_fh
    try:  # info: try :
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # info: fcntl . flock ( lock_fh . fileno (
    except BlockingIOError:  # info: except BlockingIOError :
        lock_fh.close()  # info: lock_fh . close ( )
        return emit({  # info: return emit ( {
            "ok": True,  # info: "ok" : True ,
            "engine": (args.engine or "kokoro").strip().lower(),  # info: call "engine"
            "called": False,  # info: "called" : False ,
            "detail": "busy",  # info: "detail" : "busy" ,
            "speaker": False,  # info: "speaker" : False ,
        }, 3, state=False)  # info: } , 3 , state = False )

    try:  # info: try :
        body = route(args.engine, speak=args.speak, text=args.text)  # info: set body
        if body.get("detail") == "gated" and args.speak:  # info: if body . get ( "detail" ) ==
            return emit(body, 2)  # info: return emit ( body , 2 )
        if body.get("detail") in {"refused", "empty_text", "over_cap", "key_missing", "http_error", "tiny_audio"}:  # info: if body . get ( "detail" ) in
            return emit(body, 1 if body.get("detail") != "key_missing" else 2)  # info: return emit ( body , 1 if body
        return emit(body, 0)  # info: return emit ( body , 0 )
    finally:  # info: finally :
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)  # info: fcntl . flock ( lock_fh . fileno (
        lock_fh.close()  # info: lock_fh . close ( )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
