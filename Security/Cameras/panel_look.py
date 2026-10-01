# ==============================================================================
# FILE: Security/Cameras/panel_look.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""One channel-1 look per hour. Gemma describes weather and panel tilt. This file decides the warning.

  python3 panel_look.py            use the hour cache, or look once
  python3 panel_look.py --force    look again even if this hour already has a reading

Left side up is morning prep for sunrise. Right side up is the evening position.
Flat is the day position. Morning tilt is useful and not required. Overnight left tilt is correct.
In the later half of the daytime window, left side up with low solar input is staged for sunrise.
"""
from __future__ import annotations  # info: from __future__ import annotations

import base64  # info: import base64
import fcntl  # info: import fcntl
import json  # info: import json
import os  # info: import os
import re  # info: import re
import sys  # info: import sys
import urllib.request  # info: import urllib.request
from datetime import datetime, timedelta  # info: from datetime import datetime, timedelta
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
FRAMES = DB / "Media" / "Images"  # info: set FRAMES
SUN = DB / "Energy" / "sun" / "sun-times-last.json"  # info: set SUN
WATTS = DB / "Energy" / "watts"  # info: set WATTS
OUT = DB / "Energy" / "vision" / "ch1-look-last.json"  # info: set OUT
LOW_SOLAR_W = 20  # info: combined solar input at or below this is low light
FRESH_MIN = 30  # info: a watts file older than this does not count as a light reading
LOCK = Path("/tmp/panel-look.lock")  # info: set LOCK
MODEL = os.environ.get("RR_PANEL_LOOK_MODEL", "gemma4:e4b")  # info: set MODEL
OLLAMA = os.environ.get("RR_OLLAMA_URL", "http://127.0.0.1:11434/api/chat")  # info: set OLLAMA

WEATHER = {  # info: set WEATHER
    "rain": "rainy conditions",  # info: "rain" : "rainy conditions"
    "fog": "foggy conditions",  # info: "fog" : "foggy conditions"
    "overcast": "overcast conditions",  # info: "overcast" : "overcast conditions"
    "clear": "clear conditions",  # info: "clear" : "clear conditions"
    "dark": "dark conditions",  # info: "dark" : "dark conditions"
}  # info: }
POSITION = {  # info: set POSITION
    "flat": "flat position",  # info: "flat" : "flat position"
    "left_up": "the morning position, left side up",  # info: "left_up" : "the morning position, left side up"
    "right_up": "the evening position, right side up",  # info: "right_up" : "the evening position, right side up"
}  # info: }
PROMPT = (  # info: set PROMPT
    "This is security camera channel 1, looking at one ground-mounted solar panel. "  # info: "This is security camera channel 1, looking at one ground-mounted solar panel. "
    "Reply with one JSON object only, no other words. "  # info: "Reply with one JSON object only, no other words. "
    'Keys: "weather" and "position". '  # info: 'Keys: "weather" and "position". '
    "weather is one of rain, fog, overcast, clear, dark. "  # info: "weather is one of rain, fog, overcast, clear, dark. "
    "Use rain when water beads or sheets are on the glass, even if no drops are falling. Use fog when mist hides the distance. "  # info: "Use rain when water beads or sheets are on the glass, even if no drops are falling. Use fog when mist hides the distance. "
    "position is one of flat, left_up, right_up. "  # info: "position is one of flat, left_up, right_up. "
    "Look at which end of the panel is propped up. "  # info: "Look at which end of the panel is propped up. "
    "left_up means the left end in the image is raised and the right end is lower. A steep left half with a low right half is left_up, not flat. "  # info: "left_up means the left end in the image is raised and the right end is lower. A steep left half with a low right half is left_up, not flat. "
    "right_up means the right end is raised and the left end is lower. "  # info: "right_up means the right end is raised and the left end is lower. "
    "flat means both ends are at the same height and neither half is propped up. Do not invent numbers."  # info: "flat means both ends are at the same height and neither half is propped up. Do not invent numbers."
)  # info: )


# ====================================================
# SECTION: function newest_ch1
# What it does: Newest channel-1 still on disk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def newest_ch1() -> Path | None:  # info: def newest_ch1
    files = [p for p in FRAMES.glob("ch1-*.jpg") if p.is_file()] if FRAMES.is_dir() else []  # info: set files
    if not files:  # info: if not files
        return None  # info: return None
    return max(files, key=lambda p: p.stat().st_mtime)  # info: return max ( files , key = lambda p : p . stat ( ) . st_mtime )


# ====================================================
# SECTION: function sun_clocks
# What it does: Sunrise and sunset clock strings from the sun file. Empty when missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sun_clocks() -> tuple[str, str]:  # info: def sun_clocks
    try:  # info: try
        data = json.loads(SUN.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return "", ""  # info: return "" , ""
    rise = str(data.get("sunrise") or data.get("next_sunrise") or "")  # info: set rise
    sett = str(data.get("sunset") or "")  # info: set sett
    if not re.fullmatch(r"\d{2}:\d{2}", rise) or not re.fullmatch(r"\d{2}:\d{2}", sett):  # info: if not re . fullmatch
        return "", ""  # info: return "" , ""
    return rise, sett  # info: return rise , sett


# ====================================================
# SECTION: function phase_of
# What it does: morning, day, evening, or overnight from the sun clocks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def phase_of(t: datetime, rise_hm: str, set_hm: str) -> str:  # info: def phase_of
    def at(hm: str) -> datetime:  # info: def at
        hour, minute = (int(x) for x in hm.split(":"))  # info: hour , minute = ( int ( x ) for x in hm . split ( ":" ) )
        return t.replace(hour=hour, minute=minute, second=0, microsecond=0)  # info: return t . replace
    rise, sett = at(rise_hm), at(set_hm)  # info: rise , sett = at ( rise_hm ) , at ( set_hm )
    if rise - timedelta(hours=2) <= t < rise + timedelta(hours=1):  # info: if rise - timedelta ( hours = 2 ) <= t < rise + timedelta ( hours = 1 )
        return "morning"  # info: return "morning"
    if rise + timedelta(hours=1) <= t < sett - timedelta(hours=1):  # info: if rise + timedelta ( hours = 1 ) <= t < sett - timedelta ( hours = 1 )
        return "day"  # info: return "day"
    if sett - timedelta(hours=1) <= t < sett + timedelta(minutes=45):  # info: if sett - timedelta ( hours = 1 ) <= t < sett + timedelta ( minutes = 45 )
        return "evening"  # info: return "evening"
    return "overnight"  # info: return "overnight"


# ====================================================
# SECTION: function warning_for
# What it does: Human-intervention line when the tilt does not match this part of the day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def warning_for(phase: str, position: str) -> str:  # info: def warning_for
    if position not in POSITION:  # info: if position not in POSITION
        return ""  # info: return ""
    if phase == "morning" and position == "right_up":  # info: if phase == "morning" and position == "right_up"
        return "Human intervention is needed. Tilt the left side up for morning, ahead of sunrise. Flat is also acceptable."  # info: return "Human intervention is needed. Tilt the left side up for morning, ahead of sunrise. Flat is also acceptable."
    if phase == "day" and position != "flat":  # info: if phase == "day" and position != "flat"
        return "Human intervention is needed. Daytime calls for the panels flat."  # info: return "Human intervention is needed. Daytime calls for the panels flat."
    if phase == "evening" and position != "right_up":  # info: if phase == "evening" and position != "right_up"
        return "Human intervention is needed. Evening calls for the right side up."  # info: return "Human intervention is needed. Evening calls for the right side up."
    if phase == "overnight" and position == "right_up":  # info: if phase == "overnight" and position == "right_up"
        return "Human intervention is needed. Overnight calls for the left side up, ahead of sunrise. Flat is also acceptable."  # info: return "Human intervention is needed. Overnight calls for the left side up, ahead of sunrise. Flat is also acceptable."
    return ""  # info: return ""


# ====================================================
# SECTION: function sentence_for
# What it does: One spoken observation, plus a warning only when the tilt is wrong for the hour.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sentence_for(weather: str, position: str, phase: str) -> str:  # info: def sentence_for
    sky = WEATHER.get(weather, "conditions the camera could not settle")  # info: set sky
    tilt = POSITION.get(position, "a position the camera could not settle")  # info: set tilt
    line = f"Security camera observations indicate {sky}, with solar panels in {tilt}."  # info: set line
    warn = warning_for(phase, position)  # info: set warn
    return f"{line} {warn}".strip() if warn else line  # info: return f" { line } { warn } " . strip ( ) if warn else line


# ====================================================
# SECTION: function ask
# What it does: One Gemma vision read of the still. Returns weather and position, or empty on failure.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ask(path: Path) -> tuple[str, str]:  # info: def ask
    body = json.dumps({  # info: set body
        "model": MODEL,  # info: "model" : MODEL
        "stream": False,  # info: "stream" : False
        "think": False,  # info: "think" : False
        "keep_alive": 0,  # info: "keep_alive" : 0
        "messages": [{"role": "user", "content": PROMPT, "images": [base64.b64encode(path.read_bytes()).decode()]}],  # info: "messages" : [ { "role" : "user" , "content" : PROMPT , "images" : [ base64 . b64encode ( path . read_bytes ( ) ) . decode ( ) ] } ]
        "options": {"temperature": 0},  # info: "options" : { "temperature" : 0 }
    }).encode()  # info: } ) . encode ( )
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})  # info: set req
    with urllib.request.urlopen(req, timeout=180) as response:  # info: with urllib . request . urlopen ( req , timeout = 180 ) as response
        payload = json.load(response)  # info: set payload
    text = str(((payload.get("message") or {}).get("content") or ""))  # info: set text
    match = re.search(r"\{.*\}", text, re.S)  # info: set match
    if not match:  # info: if not match
        return "", ""  # info: return "" , ""
    try:  # info: try
        row = json.loads(match.group(0))  # info: set row
    except ValueError:  # info: except ValueError
        return "", ""  # info: return "" , ""
    weather = str(row.get("weather") or "").strip().lower()  # info: set weather
    position = str(row.get("position") or "").strip().lower()  # info: set position
    if weather not in WEATHER:  # info: if weather not in WEATHER
        weather = ""  # info: set weather
    if position not in POSITION:  # info: if position not in POSITION
        position = ""  # info: set position
    return weather, position  # info: return weather , position


# ====================================================
# SECTION: function load_cache
# What it does: Last hourly reading, or None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_cache() -> dict | None:  # info: def load_cache
    try:  # info: try
        data = json.loads(OUT.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return None  # info: return None
    return data if isinstance(data, dict) else None  # info: return data if isinstance ( data , dict ) else None


# ====================================================
# SECTION: function observe
# What it does: Return this hour's reading. Calls the vision model only when the hour has no reading yet.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def observe(t: datetime, force: bool = False) -> dict:  # info: def observe
    hour = t.strftime("%Y-%m-%dT%H")  # info: set hour
    cached = load_cache()  # info: set cached
    if cached and cached.get("hour") == hour and cached.get("sentence") and not force:  # info: if cached and cached . get ( "hour" ) == hour and cached . get ( "sentence" ) and not force
        return cached  # info: return cached
    LOCK.parent.mkdir(parents=True, exist_ok=True)  # info: LOCK . parent . mkdir
    with LOCK.open("a+") as handle:  # info: with LOCK . open ( "a+" ) as handle
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # info: fcntl . flock ( handle . fileno ( ) , fcntl . LOCK_EX )
        cached = load_cache()  # info: set cached
        if cached and cached.get("hour") == hour and cached.get("sentence") and not force:  # info: if cached and cached . get ( "hour" ) == hour and cached . get ( "sentence" ) and not force
            return cached  # info: return cached
        image = newest_ch1()  # info: set image
        rise, sett = sun_clocks()  # info: rise , sett = sun_clocks ( )
        phase = phase_of(t, rise, sett) if rise and sett else ""  # info: set phase
        weather, position = ("", "")  # info: weather , position = ( "" , "" )
        error = ""  # info: set error
        if image is None:  # info: if image is None
            error = "no channel 1 still"  # info: set error
        else:  # info: else
            try:  # info: try
                weather, position = ask(image)  # info: weather , position = ask ( image )
            except Exception as exc:  # info: except Exception as exc
                error = type(exc).__name__  # info: set error
        if weather and position and phase:  # info: if weather and position and phase
            sentence = sentence_for(weather, position, phase)  # info: set sentence
        elif weather and position:  # info: elif weather and position
            sentence = sentence_for(weather, position, "")  # info: set sentence
        else:  # info: else
            sentence = ""  # info: set sentence
        row = {  # info: set row
            "hour": hour if sentence else "",  # info: "hour" : hour if sentence else ""
            "at": t.isoformat(timespec="seconds"),  # info: "at" : t . isoformat ( timespec = "seconds" )
            "image": image.name if image else "",  # info: "image" : image . name if image else ""
            "model": MODEL,  # info: "model" : MODEL
            "weather": weather,  # info: "weather" : weather
            "position": position,  # info: "position" : position
            "phase": phase,  # info: "phase" : phase
            "sunrise": rise,  # info: "sunrise" : rise
            "sunset": sett,  # info: "sunset" : sett
            "warning": warning_for(phase, position) if sentence else "",  # info: "warning" : warning_for ( phase , position ) if sentence else ""
            "sentence": sentence,  # info: "sentence" : sentence
            "error": error,  # info: "error" : error
        }  # info: }
        if sentence:  # info: if sentence
            OUT.parent.mkdir(parents=True, exist_ok=True)  # info: OUT . parent . mkdir ( parents = True , exist_ok = True )
            tmp = OUT.with_suffix(".tmp")  # info: set tmp
            tmp.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
            os.replace(tmp, OUT)  # info: os . replace ( tmp , OUT )
        return row  # info: return row


# ====================================================
# SECTION: function main
# What it does: Print one observation. --rules checks the tilt warnings without calling the model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if "--rules" in sys.argv:  # info: if "--rules" in sys . argv
        samples = [  # info: set samples
            ("morning", "left_up"), ("morning", "flat"), ("morning", "right_up"),  # info: ( "morning" , "left_up" ) , ( "morning" , "flat" ) , ( "morning" , "right_up" )
            ("day", "flat"), ("day", "left_up"), ("evening", "right_up"), ("evening", "flat"),  # info: ( "day" , "flat" ) , ( "day" , "left_up" ) , ( "evening" , "right_up" ) , ( "evening" , "flat" )
            ("overnight", "left_up"), ("overnight", "flat"), ("overnight", "right_up"),  # info: ( "overnight" , "left_up" ) , ( "overnight" , "flat" ) , ( "overnight" , "right_up" )
        ]  # info: ]
        for phase, position in samples:  # info: for phase , position in samples
            print(phase, position, sentence_for("rain", position, phase))  # info: call print
        return 0  # info: return 0
    now = datetime.now().astimezone().replace(microsecond=0)  # info: set now
    print(json.dumps(observe(now, force="--force" in sys.argv), ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
