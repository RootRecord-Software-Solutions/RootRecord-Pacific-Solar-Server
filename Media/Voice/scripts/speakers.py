# ==============================================================================
# FILE: Media/Voice/scripts/speakers.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Locked Kokoro voices, report-kind personas and live-data gate (G3 port of G1 speakers.py).

Bruce = Echo (am_echo, 1.0) · Ava = Heart (af_heart, 1.0, default) · Carly = Nova (af_nova, 1.0)

G3 changes (2026-09-29, g3-voice-ailog): retire pattern is now
  <report>_current.wav  ->  Archive/<report>_YYYYMMDDTHHMM.wav  (+ .read.txt / .speak.txt sidecars)
Delivery removed: no AWS radio push, no Telegram, no speaker playback (OFF pending Alexander sign-off).
Persona map (AGENTS / KIND_AGENT), is_live gate and without_name are unchanged from G1.
Grok has no Kokoro voice (cloud Ara retired) — open question, deliberately not mapped.
"""
from __future__ import annotations  # info: from __future__ import annotations

import logging  # info: import logging
import re  # info: import re
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

log = logging.getLogger("rr.voice.speakers")  # info: set log
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST

# ====================================================
# SECTION: AGENTS
# What it does: Set AGENTS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
AGENTS = {  # info: set AGENTS
    "ava": {"name": "Ava", "kokoro": "af_heart", "speed": 1.0},  # info: "ava" : { "name" : "Ava" , "kokoro" : "af_heart" , "speed" : 1.0 } ,
    "bruce": {"name": "Bruce", "kokoro": "am_echo", "speed": 1.0},  # info: "bruce" : { "name" : "Bruce" , "kokoro" : "am_echo" , "speed" : 1.0 } ,
    "carly": {"name": "Carly", "kokoro": "af_nova", "speed": 1.0},  # info: "carly" : { "name" : "Carly" , "kokoro" : "af_nova" , "speed" : 1.0 } ,
}  # info: }

# Automated spoken desks. Keep the three loads even. (verbatim from G1)
# ====================================================
# SECTION: KIND_AGENT
# What it does: Set KIND_AGENT.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
KIND_AGENT = {  # info: set KIND_AGENT
    "morning": "ava",  # info: "morning" : "ava" ,
    "midday": "ava",  # info: "midday" : "ava" ,
    "evening": "ava",  # info: "evening" : "ava" ,
    "late": "ava",  # info: "late" : "ava" ,
    "summary": "ava",  # info: "summary" : "ava" ,
    "weather": "ava",  # info: "weather" : "ava" ,
    "nws": "ava",  # info: "nws" : "ava" ,
    "chime": "ava",  # info: "chime" : "ava" ,
    "official": "ava",  # info: "official" : "ava" ,
    "boot": "ava",  # info: "boot" : "ava" ,
    "current": "ava",  # info: "current" : "ava" ,
    "solar": "bruce",  # info: "solar" : "bruce" ,
    "energy": "carly",  # info: "energy" : "carly" ,
    "system": "bruce",  # info: "system" : "bruce" ,
    "remaining": "bruce",  # info: "remaining" : "bruce" ,
    "hourly": "bruce",  # info: "hourly" : "bruce" ,
    "custom": "bruce",  # info: "custom" : "bruce" ,
    "earthquake": "carly",  # info: "earthquake" : "carly" ,
    "kilauea": "carly",  # info: "kilauea" : "carly" ,
    "hurricane": "carly",  # info: "hurricane" : "carly" ,
    "alerts": "carly",  # info: "alerts" : "carly" ,
    "security": "carly",  # info: "security" : "carly" ,
    "bandwidth": "carly",  # info: "bandwidth" : "carly" ,
    "net": "carly",  # info: "net" : "carly" ,
}  # info: }

# ====================================================
# SECTION: _DEAD
# What it does: Set _DEAD.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_DEAD = (  # info: set _DEAD
    "not live",  # info: "not live" ,
    "offline stub",  # info: "offline stub" ,
    "facts not live",  # info: "facts not live" ,
    "no data",  # info: "no data" ,
    "end of status",  # info: "end of status" ,
)  # info: )


# ====================================================
# SECTION: function is_current_audio
# What it does: is current audio.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_current_audio(path: Path) -> bool:  # info: def is_current_audio
    return Path(path).stem.lower().endswith("_current")  # info: return Path ( path ) . stem .


# ====================================================
# SECTION: function retire_current
# What it does: Move <report>_current.<ext> to Archive/<report>_YYYYMMDDTHHMM.<ext> (its own mtime, HST) with sidecars.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def retire_current(path: Path) -> Path | None:  # info: def retire_current
    """Move <report>_current.<ext> to Archive/<report>_YYYYMMDDTHHMM.<ext> (its own mtime, HST) with sidecars."""  # info: """Move <report>_current.<ext> to Archive/<report>_YYYYMMDDTHHMM.<ext> (its own mtime, HST) with sidecars."""
    path = Path(path)  # info: set path
    if not path.is_file() or path.stat().st_size <= 0:  # info: if not path . is_file ( ) or
        return None  # info: return None
    stamp = datetime.fromtimestamp(path.stat().st_mtime, HST).strftime("%Y%m%dT%H%M")  # info: set stamp
    base = re.sub(r"_current$", "", path.stem, flags=re.I)  # info: set base
    arch = path.parent / "Archive"  # info: set arch
    arch.mkdir(parents=True, exist_ok=True)  # info: arch . mkdir ( parents = True ,
    dest = arch / f"{base}_{stamp}{path.suffix}"  # info: set dest
    n = 0  # info: set n
    while dest.exists():  # info: while dest . exists ( ) :
        n += 1  # info: set n
        dest = arch / f"{base}_{stamp}-{n}{path.suffix}"  # info: set dest
    try:  # info: try :
        path.replace(dest)  # info: path . replace ( dest )
    except OSError:  # info: except OSError :
        return None  # info: return None
    for extra in (".read.txt", ".speak.txt"):  # info: for extra in ( ".read.txt" , ".speak.txt" )
        side = path.with_suffix(extra)  # info: set side
        if side.is_file():  # info: if side . is_file ( ) :
            try:  # info: try :
                side.replace(dest.with_suffix(extra))  # info: side . replace ( dest . with_suffix (
            except OSError:  # info: except OSError :
                pass  # info: pass
    return dest  # info: return dest


# ====================================================
# SECTION: function agent_for
# What it does: agent for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def agent_for(kind: str) -> str:  # info: def agent_for
    key = (kind or "").strip().lower()  # info: set key
    if key in AGENTS:  # info: if key in AGENTS :
        return key  # info: return key
    return KIND_AGENT.get(key, "ava")  # info: return KIND_AGENT . get ( key , "ava"


# ====================================================
# SECTION: function kokoro_voice_for
# What it does: kokoro voice for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def kokoro_voice_for(kind: str) -> str:  # info: def kokoro_voice_for
    return AGENTS[agent_for(kind)]["kokoro"]  # info: return AGENTS [ agent_for ( kind ) ]


# ====================================================
# SECTION: function speed_for
# What it does: speed for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speed_for(kind: str) -> float:  # info: def speed_for
    return AGENTS[agent_for(kind)]["speed"]  # info: return AGENTS [ agent_for ( kind ) ]


# ====================================================
# SECTION: function display_name
# What it does: display name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def display_name(kind: str) -> str:  # info: def display_name
    return AGENTS[agent_for(kind)]["name"]  # info: return AGENTS [ agent_for ( kind ) ]


# ====================================================
# SECTION: function _dead_line
# What it does:  dead line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _dead_line(text: str) -> bool:  # info: def _dead_line
    low = (text or "").strip().lower()  # info: set low
    if not low or len(low) < 12:  # info: if not low or len ( low )
        return True  # info: return True
    if len(low) < 400:  # info: if len ( low ) < 400 :
        if "ecoflow: down" in low or "host: down" in low or "kilauea: down" in low:  # info: if "ecoflow: down" in low or "host: down" in low
            return True  # info: return True
        if "weather: down" in low:  # info: if "weather: down" in low :
            return True  # info: return True
    if any(m in low for m in _DEAD) and not re.search(r"\d", low):  # info: if any ( m in low for m
        return True  # info: return True
    if "this is the ava core root record" in low and not re.search(r"\d", low):  # info: if "this is the ava core root record" in low and not re .
        return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function is_live
# What it does: True only when the spoken body has live facts for that desk. (verbatim G1 rules)
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_live(kind: str, text: str) -> bool:  # info: def is_live
    """True only when the spoken body has live facts for that desk. (verbatim G1 rules)"""  # info: """True only when the spoken body has live facts for that desk. (verbatim G1 rules)"""
    raw = " ".join((text or "").split()).strip()  # info: set raw
    key = (kind or "").strip().lower()  # info: set key
    if key in AGENTS:  # info: if key in AGENTS :
        return len(re.sub(r"\s+", "", raw)) >= 8  # info: return len ( re . sub ( r"\s+"
    if _dead_line(raw):  # info: if _dead_line ( raw ) :
        return False  # info: return False
    if key in {"chime"}:  # info: if key in { "chime" } :
        return bool(re.search(r"\d", raw) or "o'clock" in raw.lower() or "noon" in raw.lower() or "midnight" in raw.lower())  # info: return bool ( re . search ( r"\d"
    if key in {"solar", "energy"}:  # info: if key in { "solar" , "energy" }
        return bool(  # info: return bool (
            re.search(r"\d+\s*%", raw)  # info: re . search ( r"\d+\s*%" , raw )
            or re.search(r"\d+\s*(w|watts|percent)\b", raw, re.I)  # info: or re . search ( r"\d+\s*(w|watts|percent)\b" , raw
            or "rear shed" in raw.lower()  # info: or "rear shed" in raw . lower ( )
            or "solar panel" in raw.lower()  # info: or "solar panel" in raw . lower ( )
            or "energy desk" in raw.lower()  # info: or "energy desk" in raw . lower ( )
        )  # info: )
    if key in {"system", "hourly"}:  # info: if key in { "system" , "hourly" }
        return bool(re.search(r"(cpu|ram|memory|npu|gpu).{0,12}\d+\s*%", raw, re.I) or re.search(r"\d+\s*%", raw))  # info: return bool ( re . search ( r"(cpu|ram|memory|npu|gpu).{0,12}\d+\s*%"
    if key in {"weather", "nws", "official"}:  # info: if key in { "weather" , "nws" ,
        return "nws" in raw.lower() or bool(re.search(r"\d", raw)) or "no active" in raw.lower()  # info: return "nws" in raw . lower ( )
    if key in {"kilauea"}:  # info: if key in { "kilauea" } :
        return "kilauea" in raw.lower() and "down" not in raw.lower()  # info: return "kilauea" in raw . lower ( )
    if key in {"security"}:  # info: if key in { "security" } :
        return bool(re.search(r"\d", raw)) and (  # info: return bool ( re . search ( r"\d"
            "security" in raw.lower()  # info: "security" in raw . lower ( )
            or "firewall" in raw.lower()  # info: or "firewall" in raw . lower ( )
            or "sign-in" in raw.lower()  # info: or "sign-in" in raw . lower ( )
            or "listener" in raw.lower()  # info: or "listener" in raw . lower ( )
        )  # info: )
    if key in {"bandwidth", "net"}:  # info: if key in { "bandwidth" , "net" }
        return bool(re.search(r"\d", raw)) and (  # info: return bool ( re . search ( r"\d"
            "megabyte" in raw.lower()  # info: "megabyte" in raw . lower ( )
            or "gigabyte" in raw.lower()  # info: or "gigabyte" in raw . lower ( )
            or "kilobyte" in raw.lower()  # info: or "kilobyte" in raw . lower ( )
            or "bytes" in raw.lower()  # info: or "bytes" in raw . lower ( )
        )  # info: )
    if key in {"earthquake"}:  # info: if key in { "earthquake" } :
        return "earthquake" in raw.lower() and ("usgs" in raw.lower() or bool(re.search(r"\d", raw)))  # info: return "earthquake" in raw . lower ( )
    if key in {"hurricane"}:  # info: if key in { "hurricane" } :
        return ("storm" in raw.lower() or "hurricane" in raw.lower() or "tropical" in raw.lower()) and (  # info: return ( "storm" in raw . lower (
            bool(re.search(r"\d", raw)) or "no named" in raw.lower() or "quiet" in raw.lower()  # info: call bool
        )  # info: )
    if key in {"remaining"}:  # info: if key in { "remaining" } :
        return bool(re.search(r"\d", raw))  # info: return bool ( re . search ( r"\d"
    if key in {"custom"}:  # info: if key in { "custom" }
        return len(re.sub(r"\s+", "", raw)) >= 8  # info: operator text; length only
    if key in {"morning", "midday", "evening", "late", "summary", "boot", "current"}:  # info: if key in { "morning" , "midday" ,
        return bool(re.search(r"\d", raw))  # info: return bool ( re . search ( r"\d"
    return bool(re.search(r"\d", raw))  # info: return bool ( re . search ( r"\d"


_NAME_LEAD = re.compile(  # info: set _NAME_LEAD
    r"(?i)^(?:this is\s+)?(?:ava ivy|ava|bruce monitor|bruce|carly mal|carly)\s*[,.]\s+"  # info: r"(?i)^(?:this is\s+)?(?:ava ivy|ava|bruce monitor|bruce|carly mal|carly)\s*[,.]\s+"
)  # info: )


# ====================================================
# SECTION: function without_name
# What it does: Spoken reports use the locked Kokoro voice. Do not say the agent name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def without_name(text: str) -> str:  # info: def without_name
    """Spoken reports use the locked Kokoro voice. Do not say the agent name."""  # info: """Spoken reports use the locked Kokoro voice. Do not say the agent name."""
    body = " ".join((text or "").split()).strip()  # info: set body
    while True:  # info: while True :
        nxt = _NAME_LEAD.sub("", body, count=1).strip()  # info: set nxt
        if nxt == body:  # info: if nxt == body :
            return body  # info: return body
        body = nxt  # info: set body
