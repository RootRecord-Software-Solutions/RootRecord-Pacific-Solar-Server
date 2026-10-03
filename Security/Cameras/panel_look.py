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
An infrared frame is night. Weather is dark. The gray picture is the illuminator, not cloud cover.
A near-black frame has no picture. It is not night vision. Weather and tilt stay unset.
"""
from __future__ import annotations  # info: from __future__ import annotations

import base64  # info: import base64
import fcntl  # info: import fcntl
import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import sys  # info: import sys
import urllib.request  # info: import urllib.request
from datetime import datetime, timedelta  # info: from datetime import datetime, timedelta
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
FRAMES = DB / "Media" / "Images"  # info: set FRAMES
SUN = DB / "Energy" / "sun" / "sun-times_current.json"  # info: set SUN
WATTS = DB / "Energy" / "watts"  # info: set WATTS
OUT = DB / "Energy" / "vision" / "ch1-look-last.json"  # info: set OUT
LOW_SOLAR_W = 20  # info: combined solar input at or below this is low light
FRESH_MIN = 30  # info: a watts file older than this does not count as a light reading
IR_SPAN = 6  # info: mean channel span below this is an infrared grayscale frame
BLANK_LUM = 8  # info: mean brightness below this is a black still, not a night picture
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
    "A grayscale infrared frame has no color. That is night, so weather is dark. Do not call it overcast, clear, fog, or rain. "  # info: "A grayscale infrared frame has no color. That is night, so weather is dark. Do not call it overcast, clear, fog, or rain. "
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
# SECTION: function frame_stats
# What it does: Mean color span and mean brightness of one still. None when the frame cannot be read.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def frame_stats(path: Path) -> tuple[float, float] | None:  # info: def frame_stats
    try:  # info: try
        proc = subprocess.run(  # info: set proc
            ["ffmpeg", "-v", "error", "-i", str(path), "-vf", "scale=80:48", "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],  # info: ffmpeg scale to raw rgb
            capture_output=True,  # info: capture_output = True
            timeout=20,  # info: timeout = 20
        )  # info: )
    except (OSError, subprocess.TimeoutExpired):  # info: except ( OSError , subprocess . TimeoutExpired )
        return None  # info: return None
    raw = proc.stdout  # info: set raw
    if proc.returncode != 0 or len(raw) < 3 or len(raw) % 3:  # info: if proc . returncode != 0 or len ( raw ) < 3 or len ( raw ) % 3
        return None  # info: return None
    span = 0  # info: set span
    bright = 0  # info: set bright
    count = 0  # info: set count
    for i in range(0, len(raw), 3):  # info: for i in range ( 0 , len ( raw ) , 3 )
        red, green, blue = raw[i], raw[i + 1], raw[i + 2]  # info: red , green , blue = raw [ i ] , raw [ i + 1 ] , raw [ i + 2 ]
        span += max(red, green, blue) - min(red, green, blue)  # info: set span
        bright += (red + green + blue) / 3  # info: set bright
        count += 1  # info: set count
    if count == 0:  # info: if count == 0
        return None  # info: return None
    return span / count, bright / count  # info: return span / count , bright / count


# ====================================================
# SECTION: function infrared
# What it does: True when the still is grayscale night vision with a visible scene. A black frame is not night vision.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def infrared(path: Path) -> bool:  # info: def infrared
    stats = frame_stats(path)  # info: set stats
    return stats is not None and stats[1] >= BLANK_LUM and stats[0] < IR_SPAN  # info: return stats is not None and stats [ 1 ] >= BLANK_LUM and stats [ 0 ] < IR_SPAN


# ====================================================
# SECTION: function blank
# What it does: True when the still is near black and has no panel picture.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def blank(path: Path) -> bool:  # info: def blank
    stats = frame_stats(path)  # info: set stats
    return stats is not None and stats[1] < BLANK_LUM  # info: return stats is not None and stats [ 1 ] < BLANK_LUM


# ====================================================
# SECTION: function night_row
# What it does: A black still clears weather and tilt. An infrared still forces weather to dark and keeps the tilt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def night_row(row: dict, image: Path | None) -> dict:  # info: def night_row
    out = dict(row)  # info: set out
    if row.get("blank") and image and row.get("image") and image.name != row.get("image"):  # info: if row . get ( "blank" ) and image and row . get ( "image" ) and image . name != row . get ( "image" )
        return out  # info: return out
    if not image:  # info: if not image
        return out  # info: return out
    stats = frame_stats(image)  # info: set stats
    if stats is not None and stats[1] < BLANK_LUM:  # info: if stats is not None and stats [ 1 ] < BLANK_LUM
        out["blank"] = True  # info: out [ "blank" ] = True
        out["infrared"] = False  # info: out [ "infrared" ] = False
        out["weather"] = ""  # info: out [ "weather" ] = ""
        out["position"] = ""  # info: out [ "position" ] = ""
        out["image"] = image.name  # info: out [ "image" ] = image . name
        return out  # info: return out
    if not stats or stats[0] >= IR_SPAN:  # info: if not stats or stats [ 0 ] >= IR_SPAN
        return out  # info: return out
    out["blank"] = False  # info: out [ "blank" ] = False
    out["weather"] = "dark"  # info: out [ "weather" ] = "dark"
    out["infrared"] = True  # info: out [ "infrared" ] = True
    if not row.get("infrared"):  # info: if not row . get ( "infrared" )
        out["image"] = image.name  # info: out [ "image" ] = image . name
    return out  # info: return out


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
# SECTION: function solar_watts
# What it does: Combined solar input from watts files newer than 30 minutes. None when no fresh reading exists.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def solar_watts(t: datetime) -> int | None:  # info: def solar_watts
    if not WATTS.is_dir():  # info: if not WATTS . is_dir ( )
        return None  # info: return None
    total = 0.0  # info: set total
    found = False  # info: set found
    for path in sorted(WATTS.glob("*-last.json")):  # info: for path in sorted ( WATTS . glob ( "*-last.json" ) )
        try:  # info: try
            data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
        except (OSError, ValueError):  # info: except ( OSError , ValueError )
            continue  # info: continue
        raw = data.get("solar_input_power") if isinstance(data, dict) else None  # info: set raw
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):  # info: if isinstance ( raw , bool ) or not isinstance ( raw , ( int , float ) )
            continue  # info: continue
        try:  # info: try
            at = datetime.fromisoformat(str(data.get("at") or ""))  # info: set at
        except ValueError:  # info: except ValueError
            continue  # info: continue
        if at.tzinfo is None and t.tzinfo is not None:  # info: if at . tzinfo is None and t . tzinfo is not None
            at = at.replace(tzinfo=t.tzinfo)  # info: set at
        age_min = (t - at).total_seconds() / 60  # info: set age_min
        if age_min > FRESH_MIN or age_min < -5:  # info: if age_min > FRESH_MIN or age_min < -5
            continue  # info: continue
        total += float(raw)  # info: set total
        found = True  # info: set found
    return int(total) if found else None  # info: return int ( total ) if found else None


# ====================================================
# SECTION: function late_day
# What it does: True from the later half of the daytime window through the end of evening.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def late_day(t: datetime, rise_hm: str, set_hm: str) -> bool:  # info: def late_day
    def at(hm: str) -> datetime:  # info: def at
        hour, minute = (int(x) for x in hm.split(":"))  # info: hour , minute = ( int ( x ) for x in hm . split ( ":" ) )
        return t.replace(hour=hour, minute=minute, second=0, microsecond=0)  # info: return t . replace
    rise, sett = at(rise_hm), at(set_hm)  # info: rise , sett = at ( rise_hm ) , at ( set_hm )
    start, day_end = rise + timedelta(hours=1), sett - timedelta(hours=1)  # info: start , day_end = rise + timedelta ( hours = 1 ) , sett - timedelta ( hours = 1 )
    if day_end <= start:  # info: if day_end <= start
        return False  # info: return False
    return start + (day_end - start) / 2 <= t < sett + timedelta(minutes=45)  # info: return start + ( day_end - start ) / 2 <= t < sett + timedelta ( minutes = 45 )


# ====================================================
# SECTION: function note_for
# What it does: Sunrise-staging line when late-day light is low and the left side is already up.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def note_for(phase: str, position: str, late: bool, low_light: bool) -> str:  # info: def note_for
    if phase in {"day", "evening"} and position == "left_up" and late and low_light:  # info: if phase in { "day" , "evening" } and position == "left_up" and late and low_light
        return "Solar staged for sunrise."  # info: return "Solar staged for sunrise."
    return ""  # info: return ""


# ====================================================
# SECTION: function warning_for
# What it does: Human-intervention line when the tilt does not match this part of the day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def warning_for(phase: str, position: str, late: bool = False, low_light: bool = False) -> str:  # info: def warning_for
    if position not in POSITION:  # info: if position not in POSITION
        return ""  # info: return ""
    if phase == "morning" and position == "right_up":  # info: if phase == "morning" and position == "right_up"
        return "Human intervention is needed. Tilt the left side up for morning, ahead of sunrise. Flat is also acceptable."  # info: return "Human intervention is needed. Tilt the left side up for morning, ahead of sunrise. Flat is also acceptable."
    if phase == "day" and position != "flat" and not note_for(phase, position, late, low_light):  # info: if phase == "day" and position != "flat" and not note_for ( phase , position , late , low_light )
        return "Human intervention is needed. Daytime calls for the panels flat."  # info: return "Human intervention is needed. Daytime calls for the panels flat."
    if phase == "evening" and position != "right_up" and not note_for(phase, position, late, low_light):  # info: if phase == "evening" and position != "right_up" and not note_for ( phase , position , late , low_light )
        return "Human intervention is needed. Evening calls for the right side up."  # info: return "Human intervention is needed. Evening calls for the right side up."
    if phase == "overnight" and position == "right_up":  # info: if phase == "overnight" and position == "right_up"
        return "Human intervention is needed. Overnight calls for the left side up, ahead of sunrise. Flat is also acceptable."  # info: return "Human intervention is needed. Overnight calls for the left side up, ahead of sunrise. Flat is also acceptable."
    return ""  # info: return ""


# ====================================================
# SECTION: function sentence_for
# What it does: One spoken observation, plus a warning or the sunrise-staging note.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sentence_for(weather: str, position: str, phase: str, late: bool = False, low_light: bool = False) -> str:  # info: def sentence_for
    if not weather and not position:  # info: if not weather and not position
        return "Security camera channel 1 still is black. The panel position is not visible."  # info: return "Security camera channel 1 still is black. The panel position is not visible."
    sky = WEATHER.get(weather, "conditions the camera could not settle")  # info: set sky
    tilt = POSITION.get(position, "a position the camera could not settle")  # info: set tilt
    line = f"Security camera observations indicate {sky}, with solar panels in {tilt}."  # info: set line
    extra = warning_for(phase, position, late, low_light) or note_for(phase, position, late, low_light)  # info: set extra
    return f"{line} {extra}".strip() if extra else line  # info: return f" { line } { extra } " . strip ( ) if extra else line


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
# SECTION: function apply_rules
# What it does: Fill the warning and sentence from weather, tilt, the clock, and fresh solar watts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_rules(row: dict, t: datetime) -> dict:  # info: def apply_rules
    weather, position = str(row.get("weather") or ""), str(row.get("position") or "")  # info: weather , position = str ( row . get ( "weather" ) or "" ) , str ( row . get ( "position" ) or "" )
    rise, sett = str(row.get("sunrise") or ""), str(row.get("sunset") or "")  # info: rise , sett = str ( row . get ( "sunrise" ) or "" ) , str ( row . get ( "sunset" ) or "" )
    if not rise or not sett:  # info: if not rise or not sett
        rise, sett = sun_clocks()  # info: rise , sett = sun_clocks ( )
    phase = phase_of(t, rise, sett) if rise and sett else str(row.get("phase") or "")  # info: set phase
    late = late_day(t, rise, sett) if rise and sett else False  # info: set late
    watts = solar_watts(t)  # info: set watts
    low = watts is not None and watts <= LOW_SOLAR_W  # info: set low
    if row.get("blank"):  # info: if row . get ( "blank" )
        sentence = sentence_for("", "", phase, late, low)  # info: set sentence
    elif weather and position:  # info: elif weather and position
        sentence = sentence_for(weather, position, phase, late, low)  # info: set sentence
    else:  # info: else
        sentence = ""  # info: set sentence
    out = dict(row)  # info: set out
    out["phase"] = phase  # info: out [ "phase" ] = phase
    out["sunrise"] = rise  # info: out [ "sunrise" ] = rise
    out["sunset"] = sett  # info: out [ "sunset" ] = sett
    out["solar_w"] = watts  # info: out [ "solar_w" ] = watts
    out["late"] = late  # info: out [ "late" ] = late
    out["low_light"] = low  # info: out [ "low_light" ] = low
    out["warning"] = warning_for(phase, position, late, low) if sentence else ""  # info: out [ "warning" ] = warning_for ( phase , position , late , low ) if sentence else ""
    out["note"] = note_for(phase, position, late, low) if sentence else ""  # info: out [ "note" ] = note_for ( phase , position , late , low ) if sentence else ""
    out["sentence"] = sentence  # info: out [ "sentence" ] = sentence
    return out  # info: return out


# ====================================================
# SECTION: function store
# What it does: Write one look file when the sentence changed. Does not call the vision model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def store(row: dict) -> None:  # info: def store
    if not row.get("sentence"):  # info: if not row . get ( "sentence" )
        return  # info: return
    previous = load_cache()  # info: set previous
    if previous == row:  # info: if previous == row
        return  # info: return
    OUT.parent.mkdir(parents=True, exist_ok=True)  # info: OUT . parent . mkdir ( parents = True , exist_ok = True )
    tmp = OUT.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, OUT)  # info: os . replace ( tmp , OUT )


# ====================================================
# SECTION: function reuse_hour
# What it does: True when this hour's stored look still stands. A later visible frame replaces a black reading. A new black frame replaces a tilt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def reuse_hour(cached: dict | None, image: Path | None, hour: str, force: bool) -> bool:  # info: def reuse_hour
    if force or not cached or cached.get("hour") != hour:  # info: if force or not cached or cached . get ( "hour" ) != hour
        return False  # info: return False
    if not cached.get("position") and not cached.get("blank"):  # info: if not cached . get ( "position" ) and not cached . get ( "blank" )
        return False  # info: return False
    if image and blank(image) and not cached.get("blank"):  # info: if image and blank ( image ) and not cached . get ( "blank" )
        return False  # info: return False
    if cached.get("blank") and image and image.name != cached.get("image") and not blank(image):  # info: if cached . get ( "blank" ) and image and image . name != cached . get ( "image" ) and not blank ( image )
        try:  # info: try
            looked = datetime.fromisoformat(str(cached.get("at") or ""))  # info: set looked
        except ValueError:  # info: except ValueError
            return True  # info: return True
        if image.stat().st_mtime > looked.timestamp():  # info: if image . stat ( ) . st_mtime > looked . timestamp ( )
            return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function observe
# What it does: Return this hour's reading. A black still gets no model call and no tilt. An infrared still forces the sky to dark.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def observe(t: datetime, force: bool = False) -> dict:  # info: def observe
    hour = t.strftime("%Y-%m-%dT%H")  # info: set hour
    cached = load_cache()  # info: set cached
    image = newest_ch1()  # info: set image
    if reuse_hour(cached, image, hour, force):  # info: if reuse_hour ( cached , image , hour , force )
        ruled = apply_rules(night_row(cached, image), t)  # info: set ruled
        store(ruled)  # info: call store
        return ruled  # info: return ruled
    LOCK.parent.mkdir(parents=True, exist_ok=True)  # info: LOCK . parent . mkdir
    with LOCK.open("a+") as handle:  # info: with LOCK . open ( "a+" ) as handle
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # info: fcntl . flock ( handle . fileno ( ) , fcntl . LOCK_EX )
        cached = load_cache()  # info: set cached
        image = newest_ch1()  # info: set image
        if reuse_hour(cached, image, hour, force):  # info: if reuse_hour ( cached , image , hour , force )
            ruled = apply_rules(night_row(cached, image), t)  # info: set ruled
            store(ruled)  # info: call store
            return ruled  # info: return ruled
        rise, sett = sun_clocks()  # info: rise , sett = sun_clocks ( )
        phase = phase_of(t, rise, sett) if rise and sett else ""  # info: set phase
        weather, position = ("", "")  # info: weather , position = ( "" , "" )
        error = ""  # info: set error
        if image is None:  # info: if image is None
            error = "no channel 1 still"  # info: set error
        elif blank(image):  # info: elif blank ( image )
            weather, position = "", ""  # info: weather , position = "" , ""
        else:  # info: else
            try:  # info: try
                weather, position = ask(image)  # info: weather , position = ask ( image )
            except Exception as exc:  # info: except Exception as exc
                error = type(exc).__name__  # info: set error
        row = apply_rules(night_row({  # info: set row
            "hour": hour,  # info: "hour" : hour
            "at": t.isoformat(timespec="seconds"),  # info: "at" : t . isoformat ( timespec = "seconds" )
            "image": image.name if image else "",  # info: "image" : image . name if image else ""
            "model": MODEL,  # info: "model" : MODEL
            "weather": weather,  # info: "weather" : weather
            "position": position,  # info: "position" : position
            "phase": phase,  # info: "phase" : phase
            "sunrise": rise,  # info: "sunrise" : rise
            "sunset": sett,  # info: "sunset" : sett
            "error": error,  # info: "error" : error
        }, image), t)  # info: } , image ) , t )
        if not row.get("sentence"):  # info: if not row . get ( "sentence" )
            row["hour"] = ""  # info: row [ "hour" ] = ""
        store(row)  # info: call store
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
            ("day", "flat"), ("day", "left_up"), ("day", "right_up"), ("evening", "right_up"), ("evening", "flat"),  # info: ( "day" , "flat" ) , ( "day" , "left_up" ) , ( "day" , "right_up" ) , ( "evening" , "right_up" ) , ( "evening" , "flat" )
            ("overnight", "left_up"), ("overnight", "flat"), ("overnight", "right_up"),  # info: ( "overnight" , "left_up" ) , ( "overnight" , "flat" ) , ( "overnight" , "right_up" )
        ]  # info: ]
        for phase, position in samples:  # info: for phase , position in samples
            print(phase, position, sentence_for("rain", position, phase))  # info: call print
        print("day", "left_up", "late-low", sentence_for("rain", "left_up", "day", True, True))  # info: call print
        print("day", "right_up", "late-low", sentence_for("rain", "right_up", "day", True, True))  # info: call print
        print("evening", "left_up", "late-low", sentence_for("rain", "left_up", "evening", True, True))  # info: call print
        return 0  # info: return 0
    now = datetime.now().astimezone().replace(microsecond=0)  # info: set now
    print(json.dumps(observe(now, force="--force" in sys.argv), ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
