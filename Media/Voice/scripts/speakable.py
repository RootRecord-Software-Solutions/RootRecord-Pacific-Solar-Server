# ==============================================================================
# FILE: Media/Voice/scripts/speakable.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
# G3 port 2026-09-29 (g3-voice-ailog): copied verbatim from G1 old skills/kokoro/scripts/speakable.py (source kept in place).
"""Make report prose speakable for Kokoro. Clocks, units, no name-intros."""  # info: """Make report prose speakable for Kokoro. Clocks, units, no name-intros."""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re
from datetime import datetime  # info: from datetime import datetime

# ====================================================
# SECTION: _ONES
# What it does: Set _ONES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_ONES = (  # info: set _ONES
    "zero",  # info: "zero" ,
    "one",  # info: "one" ,
    "two",  # info: "two" ,
    "three",  # info: "three" ,
    "four",  # info: "four" ,
    "five",  # info: "five" ,
    "six",  # info: "six" ,
    "seven",  # info: "seven" ,
    "eight",  # info: "eight" ,
    "nine",  # info: "nine" ,
    "ten",  # info: "ten" ,
    "eleven",  # info: "eleven" ,
    "twelve",  # info: "twelve" ,
    "thirteen",  # info: "thirteen" ,
    "fourteen",  # info: "fourteen" ,
    "fifteen",  # info: "fifteen" ,
    "sixteen",  # info: "sixteen" ,
    "seventeen",  # info: "seventeen" ,
    "eighteen",  # info: "eighteen" ,
    "nineteen",  # info: "nineteen" ,
)  # info: )
_TENS = ("", "", "twenty", "thirty", "forty", "fifty")  # info: set _TENS
# ====================================================
# SECTION: _HOURS
# What it does: Set _HOURS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_HOURS = {  # info: set _HOURS
    1: "one",  # info: 1 : "one" ,
    2: "two",  # info: 2 : "two" ,
    3: "three",  # info: 3 : "three" ,
    4: "four",  # info: 4 : "four" ,
    5: "five",  # info: 5 : "five" ,
    6: "six",  # info: 6 : "six" ,
    7: "seven",  # info: 7 : "seven" ,
    8: "eight",  # info: 8 : "eight" ,
    9: "nine",  # info: 9 : "nine" ,
    10: "ten",  # info: 10 : "ten" ,
    11: "eleven",  # info: 11 : "eleven" ,
    12: "twelve",  # info: 12 : "twelve" ,
}  # info: }

# ====================================================
# SECTION: _REDUNDANT
# What it does: Set _REDUNDANT.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_REDUNDANT = re.compile(  # info: set _REDUNDANT
    r"(?i)\s*(?:"  # info: r"(?i)\s*(?:"
    r"measured facts only(?:[^.!\n]*)|"  # info: r"measured facts only(?:[^.!\n]*)|"
    r"facts only(?:[^.!\n]*)|"  # info: r"facts only(?:[^.!\n]*)|"
    r"do not invent(?:\s+numbers)?(?:[^.!\n]*)|"  # info: r"do not invent(?:\s+numbers)?(?:[^.!\n]*)|"
    r"no invented numbers(?:[^.!\n]*)|"  # info: r"no invented numbers(?:[^.!\n]*)|"
    r"use only measured facts(?:[^.!\n]*)|"  # info: r"use only measured facts(?:[^.!\n]*)|"
    r"live numbers only from live facts(?:[^.!\n]*)|"  # info: r"live numbers only from live facts(?:[^.!\n]*)|"
    r"do not invent cloud cover(?:[^.!\n]*)"  # info: r"do not invent cloud cover(?:[^.!\n]*)"
    r")[.!]?"  # info: r")[.!]?"
)  # info: )

# ====================================================
# SECTION: _VOICE_SRC
# What it does: Set _VOICE_SRC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_VOICE_SRC = re.compile(  # info: set _VOICE_SRC
    r"(?i)[^.!?\n]*\b(?:"  # info: r"(?i)[^.!?\n]*\b(?:"
    r"voice mode|"  # info: r"voice mode|"
    r"clip packs?|"  # info: r"clip packs?|"
    r"phrase clips|"  # info: r"phrase clips|"
    r"paid (?:cloud )?voice|"  # info: r"paid (?:cloud )?voice|"
    r"paid tts|"  # info: r"paid tts|"
    r"local clip|"  # info: r"local clip|"
    r"kokoro|"  # info: r"kokoro|"
    r"report-generation|"  # info: r"report-generation|"
    r"toggle tts|"  # info: r"toggle tts|"
    r"full report mp3|"  # info: r"full report mp3|"
    r"prefer local phrase|"  # info: r"prefer local phrase|"
    r"voice packs|"  # info: r"voice packs|"
    r"voice engine|"  # info: r"voice engine|"
    r"tts engine|"  # info: r"tts engine|"
    r"generated with|"  # info: r"generated with|"
    r"clip.?stitch"  # info: r"clip.?stitch"
    r")\b[^.!?\n]*[.!]?"  # info: r")\b[^.!?\n]*[.!]?"
)  # info: )

_STORE_SRC = re.compile(  # info: set _STORE_SRC
    r"(?i)\s*\((?:[^)]*(?:source|jsonl|sqlite|from disk|file \d|last \d)[^)]*)\)"  # info: r"(?i)\s*\((?:[^)]*(?:source|jsonl|sqlite|from disk|file \d|last \d)[^)]*)\)"
)  # info: )

_READ_FROM = re.compile(  # info: set _READ_FROM
    r"(?i)\b(?:read|loaded|pulled|fetched|synced)\s+from\b[^.!?\n]*[.!]?"  # info: r"(?i)\b(?:read|loaded|pulled|fetched|synced)\s+from\b[^.!?\n]*[.!]?"
    r"|\bfrom (?:disk|sqlite|jsonl|the store|file)\b[^.!?\n]*[.!]?"  # info: r"|\bfrom (?:disk|sqlite|jsonl|the store|file)\b[^.!?\n]*[.!]?"
)  # info: )

# YYYY-MM-DD HH:MM (space) — park before bare clocks so "16 19" is not a time.
_DATE_CLOCK = re.compile(  # info: set _DATE_CLOCK
    r"\b(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"  # info: r"\b(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)  # info: )

# Colon clocks, or "about 12 37" — never after a digit/hyphen (avoids date day + hour).
# ====================================================
# SECTION: _CLOCK
# What it does: Set _CLOCK.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_CLOCK = re.compile(  # info: set _CLOCK
    r"(?<![\d\-])(?:at\s+|about\s+)?"  # info: r"(?<![\d\-])(?:at\s+|about\s+)?"
    r"(?:"  # info: r"(?:"
    r"([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?"  # info: r"([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?"
    r"|"  # info: r"|"
    r"([01]?\d|2[0-3])\s+([0-5]\d)"  # info: r"([01]?\d|2[0-3])\s+([0-5]\d)"
    r")"  # info: r")"
    r"(?:\s*([AaPp])\.?\s*[Mm]\.?)?\b"  # info: r"(?:\s*([AaPp])\.?\s*[Mm]\.?)?\b"
)  # info: )

_ISO = re.compile(  # info: set _ISO
    r"\b(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"  # info: r"\b(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)  # info: )

# ====================================================
# SECTION: _MONTHS
# What it does: Set _MONTHS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_MONTHS = (  # info: set _MONTHS
    "January",  # info: "January" ,
    "February",  # info: "February" ,
    "March",  # info: "March" ,
    "April",  # info: "April" ,
    "May",  # info: "May" ,
    "June",  # info: "June" ,
    "July",  # info: "July" ,
    "August",  # info: "August" ,
    "September",  # info: "September" ,
    "October",  # info: "October" ,
    "November",  # info: "November" ,
    "December",  # info: "December" ,
)  # info: )


# ====================================================
# SECTION: function _minute_words
# What it does:  minute words.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _minute_words(minute: int) -> str:  # info: def _minute_words
    m = int(minute)  # info: set m
    if m < 20:  # info: if m < 20 :
        return _ONES[m]  # info: return _ONES [ m ]
    tens, ones = divmod(m, 10)  # info: tens , ones = divmod ( m ,
    if ones:  # info: if ones :
        return f"{_TENS[tens]} {_ONES[ones]}"  # info: return f" { _TENS [ tens ] }
    return _TENS[tens]  # info: return _TENS [ tens ]


# ====================================================
# SECTION: function spoken_clock
# What it does: midnight, noon, one PM, two thirty PM.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spoken_clock(hour: int, minute: int) -> str:  # info: def spoken_clock
    """midnight, noon, one PM, two thirty PM."""  # info: """midnight, noon, one PM, two thirty PM."""
    hour = int(hour) % 24  # info: set hour
    minute = int(minute)  # info: set minute
    if hour == 0 and minute == 0:  # info: if hour == 0 and minute == 0
        return "midnight"  # info: return "midnight"
    if hour == 12 and minute == 0:  # info: if hour == 12 and minute == 0
        return "noon"  # info: return "noon"
    h12 = hour % 12 or 12  # info: set h12
    ampm = "a.m." if hour < 12 else "p.m."  # info: set ampm
    name = _HOURS[h12]  # info: set name
    if minute == 0:  # info: if minute == 0 :
        return f"{name} {ampm}"  # info: return f" { name } { ampm
    if minute < 10:  # 2026-09-29: "two oh one p.m.", not "two one p.m." (clip cache only uses :00 / :30)
        return f"{name} oh {_ONES[minute]} {ampm}"  # info: return f" { name } oh { _ONES
    return f"{name} {_minute_words(minute)} {ampm}"  # info: return f" { name } { _minute_words


# ====================================================
# SECTION: function _apply_meridian
# What it does: Return 0–23. hint may include 'morning' / 'afternoon' when no A/P marker.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _apply_meridian(hour: int, mer: str | None, *, hint: str = "") -> int:  # info: def _apply_meridian
    """Return 0–23. hint may include 'morning' / 'afternoon' when no A/P marker."""  # info: """Return 0–23. hint may include 'morning' / 'afternoon' when no A/P marker."""
    h = int(hour)  # info: set h
    m = (mer or "").upper()[:1]  # info: set m
    hint_l = (hint or "").lower()  # info: set hint_l
    if not m:  # info: if not m :
        if "morning" in hint_l or "a.m" in hint_l:  # info: if "morning" in hint_l or "a.m" in hint_l
            m = "A"  # info: set m
        elif "afternoon" in hint_l or "evening" in hint_l or "p.m" in hint_l or "night" in hint_l:  # info: elif "afternoon" in hint_l or "evening" in hint_l
            m = "P"  # info: set m
    if m == "A":  # info: if m == "A" :
        h = h % 12  # info: set h
    elif m == "P":  # info: elif m == "P" :
        h = h % 12  # info: set h
        h = 12 if h == 0 else h + 12  # info: set h
    return h  # info: return h


# ====================================================
# SECTION: function _clock_match
# What it does:  clock match.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clock_match(m: re.Match, *, after: str = "") -> str:  # info: def _clock_match
    raw = m.group(0)  # info: set raw
    if m.group(1) is not None:  # info: if m . group ( 1 ) is
        hour = int(m.group(1))  # info: set hour
        minute = int(m.group(2))  # info: set minute
        mer = m.group(5)  # info: set mer
    else:  # info: else :
        hour = int(m.group(3))  # info: set hour
        minute = int(m.group(4))  # info: set minute
        mer = m.group(5)  # info: set mer
    hour = _apply_meridian(hour, mer, hint=after)  # info: set hour
    spoken = spoken_clock(hour, minute)  # info: set spoken
    low = raw.lower().lstrip()  # info: set low
    if low.startswith("about"):  # info: if low . startswith ( "about" ) :
        return f"about {spoken}"  # info: return f" about { spoken } "
    if low.startswith("at"):  # info: if low . startswith ( "at" ) :
        return f"at {spoken}"  # info: return f" at { spoken } "
    return spoken  # info: return spoken


# ====================================================
# SECTION: function _date_clock_match
# What it does:  date clock match.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _date_clock_match(m: re.Match) -> str:  # info: def _date_clock_match
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))  # info: year , month , day = int (
    hour, minute = int(m.group(4)), int(m.group(5))  # info: hour , minute = int ( m .
    raw = m.group(0)  # info: set raw
    # If timezone present on a space/T stamp, prefer Honolulu for spoken local.
    if "T" in raw or raw.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", raw):  # info: if "T" in raw or raw . endswith
        try:  # info: try :
            iso = raw.replace(" ", "T", 1)  # info: set iso
            if iso.endswith("Z"):  # info: if iso . endswith ( "Z" ) :
                iso = iso[:-1] + "+00:00"  # info: set iso
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}", iso):  # info: if re . fullmatch ( r"\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}" , iso
                iso = iso + ":00"  # info: set iso
            dt = datetime.fromisoformat(iso)  # info: set dt
            if dt.tzinfo is not None:  # info: if dt . tzinfo is not None :
                from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

                dt = dt.astimezone(ZoneInfo("Pacific/Honolulu"))  # info: set dt
            month, day, hour, minute = dt.month, dt.day, dt.hour, dt.minute  # info: month , day , hour , minute =
        except Exception:  # info: except Exception :
            pass  # info: pass
    if not (1 <= month <= 12):  # info: if not ( 1 <= month <= 12
        return raw  # info: return raw
    return f"{_MONTHS[month - 1]} {day} at {spoken_clock(hour, minute)}"  # info: return f" { _MONTHS [ month - 1


# ====================================================
# SECTION: function _iso_match
# What it does:  iso match.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _iso_match(m: re.Match) -> str:  # info: def _iso_match
    try:  # info: try :
        raw = m.group(0)  # info: set raw
        if raw.endswith("Z"):  # info: if raw . endswith ( "Z" ) :
            raw = raw[:-1] + "+00:00"  # info: set raw
        dt = datetime.fromisoformat(raw)  # info: set dt
        if dt.tzinfo is not None:  # info: if dt . tzinfo is not None :
            from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

            dt = dt.astimezone(ZoneInfo("Pacific/Honolulu"))  # info: set dt
        return f"{_MONTHS[dt.month - 1]} {dt.day} at {spoken_clock(dt.hour, dt.minute)}"  # info: return f" { _MONTHS [ dt . month
    except Exception:  # info: except Exception :
        return spoken_clock(int(m.group(2)), int(m.group(3)))  # info: return spoken_clock ( int ( m . group


# ====================================================
# SECTION: function _sub_clocks
# What it does: Expand clocks with trailing morning/afternoon hints.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sub_clocks(text: str) -> str:  # info: def _sub_clocks
    """Expand clocks with trailing morning/afternoon hints."""  # info: """Expand clocks with trailing morning/afternoon hints."""

    def repl(m: re.Match) -> str:  # info: def repl
        return _clock_match(m, after=text[m.end() : m.end() + 32])  # info: return _clock_match ( m , after = text

    return _CLOCK.sub(repl, text)  # info: return _CLOCK . sub ( repl , text


# ====================================================
# SECTION: function _expand_units
# What it does:  expand units.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _expand_units(text: str) -> str:  # info: def _expand_units
    out = text  # info: set out
    out = re.sub(r"(?i)\berupting\s*=\s*false\b", "not erupting", out)  # info: set out
    out = re.sub(r"(?i)\berupting\s*=\s*true\b", "is erupting", out)  # info: set out
    out = re.sub(r"(?i)\bsource\s*=\s*[A-Za-z0-9_-]+", "", out)  # info: set out
    out = re.sub(r"\b([A-Za-z][A-Za-z0-9_-]*)=([A-Za-z0-9._-]+)", r"\1 \2", out)  # info: set out
    out = out.replace(" — ", ". ")  # info: set out
    out = out.replace(" – ", ". ")  # info: set out
    out = out.replace(" | ", ". ")  # info: set out
    out = re.sub(r"\s*/\s*", ", ", out)  # info: set out
    out = re.sub(r"\bi_gpu\b", "graphics", out, flags=re.I)  # info: set out
    out = re.sub(r"\bnpu\b", "neural processor", out, flags=re.I)  # info: set out
    out = out.replace("_", " ")  # info: set out
    out = re.sub(r"~", " about ", out)  # info: set out
    out = re.sub(r"(?i)\bjsonl\b", "", out)  # info: set out
    out = re.sub(r"(?i)\b(?:jsonl|sqlite|from disk)\b", "", out)  # info: set out
    out = re.sub(r"(?i)\bWeather\s*\([^)]*\)\s*:?", "Weather.", out)  # info: set out
    out = re.sub(r"(?i)\bEcoFlow\s*\([^)]*\)\s*:?", "EcoFlow.", out)  # info: set out
    out = re.sub(r"(?i)\bHost:\s*last [^,]+,\s*", "Host: ", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*°?\s*F\b", " degrees Fahrenheit", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)°?F\b", " degrees Fahrenheit", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*deg(?:rees?)?\s*F\b", " degrees Fahrenheit", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*degrees\b(?!\s+Fahrenheit)", " degrees Fahrenheit", out)  # info: set out
    out = re.sub(r"(?i)(\d+(?:\.\d+)?)\s*h(?:ours?|rs?)?\s*old", r"about \1 hours old", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*hrs?\b", " hours", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*h(?!ours|\d)\b", " hours", out)  # info: set out
    out = re.sub(r"\(\s*,", "(", out)  # info: set out
    out = re.sub(r",\s*\)", ")", out)  # info: set out
    out = re.sub(r"\(\s*\)", "", out)  # info: set out
    out = re.sub(r"\bSoC\b", "state of charge", out)  # info: set out
    out = re.sub(r"\bSOC\b", "state of charge", out)  # info: set out
    out = re.sub(r"(?i)\bstate of charge\b", "state of charge", out)  # info: set out
    out = re.sub(r"\bkWh\b", "kilowatt hours", out)  # info: set out
    out = re.sub(r"\bWh\b", "watt hours", out)  # info: set out
    out = re.sub(r"\bkW\b", "kilowatts", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*W\b", " watts", out)  # info: set out
    out = re.sub(r"(?<=\d)W\b", " watts", out)  # info: set out
    out = re.sub(r"\bmph\b", "miles per hour", out)  # info: set out
    out = re.sub(r"(?i)\bmiles per hour\b", "miles per hour", out)  # info: set out
    out = re.sub(r"\bnmi\b", "nautical miles", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*nm\b", " nautical miles", out)  # info: set out
    out = re.sub(r"\bNWS\b", "National Weather Service", out)  # info: set out
    out = re.sub(r"\bUSGS\b", "U. S. Geological Survey", out)  # info: set out
    out = re.sub(r"\bHST\b", "Hawaiian Standard Time", out)  # info: set out
    out = re.sub(r"\bHI alerts\b", "Hawaii alerts", out)  # info: set out
    out = re.sub(r"(?i)\bH(?:\.|\s)*I\.?\b", "Hawaii", out)  # info: set out
    out = re.sub(r"\bHI\b", "Hawaii", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*km\b", " kilometers", out)  # info: set out
    out = re.sub(r"(?<=\d)km\b", " kilometers", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*mi\b(?!\w)", " miles", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)mi\b(?!\w)", " miles", out)  # info: set out
    out = re.sub(r"\bSSW\b", "south-southwest", out)  # info: set out
    out = re.sub(r"\bSSE\b", "south-southeast", out)  # info: set out
    out = re.sub(r"\bNNE\b", "north-northeast", out)  # info: set out
    out = re.sub(r"\bNNW\b", "north-northwest", out)  # info: set out
    out = re.sub(r"\bENE\b", "east-northeast", out)  # info: set out
    out = re.sub(r"\bESE\b", "east-southeast", out)  # info: set out
    out = re.sub(r"\bWNW\b", "west-northwest", out)  # info: set out
    out = re.sub(r"\bWSW\b", "west-southwest", out)  # info: set out
    out = re.sub(r"\bNE\b", "northeast", out)  # info: set out
    out = re.sub(r"\bNW\b", "northwest", out)  # info: set out
    out = re.sub(r"\bSE\b", "southeast", out)  # info: set out
    out = re.sub(r"\bSW\b", "southwest", out)  # info: set out
    out = re.sub(r"\bS of\b", "south of", out)  # info: set out
    out = re.sub(r"\bN of\b", "north of", out)  # info: set out
    out = re.sub(r"\bE of\b", "east of", out)  # info: set out
    out = re.sub(r"\bW of\b", "west of", out)  # info: set out
    out = re.sub(r"\bCPU\b", "processor", out)  # info: set out
    out = re.sub(r"\bRAM\b", "memory", out)  # info: set out
    out = re.sub(r"\bNPU\b", "neural processor", out)  # info: set out
    out = re.sub(r"\bi_gpu\b", "graphics", out, flags=re.I)  # info: set out
    out = re.sub(r"\bGPU\b", "graphics", out)  # info: set out
    out = re.sub(r"\bPV\b", "solar", out)  # info: set out
    out = re.sub(r"\bkt\b", "knots", out)  # info: set out
    out = re.sub(r"\bmb\b", "millibars", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*%", " percent", out)  # info: set out
    out = re.sub(r"(?<=\d)%", " percent", out)  # info: set out
    return out  # info: return out


# ====================================================
# SECTION: function speakable
# What it does: speakable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speakable(text: str) -> str:  # info: def speakable
    out = " ".join((text or "").replace("\u00a0", " ").split())  # info: set out
    try:  # info: try :
        from hawaiian_lexicon import fold_place_spellings, pronounce_places  # info: from hawaiian_lexicon import fold_place_spellings , pronounce_places
    except ImportError:  # info: except ImportError :
        try:  # info: try :
            from apps.voice.hawaiian_lexicon import fold_place_spellings, pronounce_places  # info: from apps . voice . hawaiian_lexicon import fold_place_spellings
        except ImportError:  # info: except ImportError :
            fold_place_spellings = lambda t: t  # noqa: E731
            pronounce_places = lambda t: t  # noqa: E731
    # Park [Name](/ipa/) so slash cleanup cannot destroy them; later → English.
    _tag_slots: list[str] = []  # info: set _tag_slots

    def _park_tag(m: re.Match) -> str:  # info: def _park_tag
        _tag_slots.append(m.group(0))  # info: _tag_slots . append ( m . group (
        return f"\0IPATAG{len(_tag_slots) - 1}\0"  # info: return f" \0IPATAG { len ( _tag_slots )

    out = re.sub(r"\[[^\]]+\]\(/[^)]+/\)", _park_tag, out)  # info: set out
    out = fold_place_spellings(out)  # info: set out
    out = re.sub(r"(?i)\bHI-res\b", "high-res", out)  # info: set out
    out = re.sub(r"(?i)\bH(?:\.|\s)*I\.?\b", "Hawaii", out)  # info: set out
    out = re.sub(r"(?i)\bHI alerts\b", "Hawaii alerts", out)  # info: set out
    out = re.sub(r"(?i)\s*Not on the roof\.?", " ", out)  # info: set out
    out = re.sub(r"(?i)\bGround-mounted PV\b", "Ground-mounted solar", out)  # info: set out
    out = _REDUNDANT.sub(" ", out)  # info: set out
    out = _VOICE_SRC.sub(" ", out)  # info: set out
    out = _STORE_SRC.sub(" ", out)  # info: set out
    out = _READ_FROM.sub(" ", out)  # info: set out
    out = _DATE_CLOCK.sub(_date_clock_match, out)  # info: set out
    out = _ISO.sub(_iso_match, out)  # info: set out
    out = _sub_clocks(out)  # info: set out
    out = _expand_units(out)  # info: set out
    out = re.sub(r"(?i)\bnot erupting(?:[. ]+not erupting)+\b", "not erupting", out)  # info: set out
    out = re.sub(r"(?i)\bis erupting(?:[. ]+is erupting)+\b", "is erupting", out)  # info: set out
    out = re.sub(r"\bWATCH\b", "watch", out)  # info: set out
    out = re.sub(r"(?i)(watch[. ]+not erupting)[. ]+watch\b", r"\1", out)  # info: set out
    out = re.sub(r"(?i)\bWeather:\s*Weather\.?", "Weather.", out)  # info: set out
    out = re.sub(r"\(\s+", "(", out)  # info: set out
    out = re.sub(r"\s+\)", ")", out)  # info: set out
    out = re.sub(r"\s{2,}", " ", out)  # info: set out
    out = re.sub(r"\s+([.,:])", r"\1", out)  # info: set out
    out = re.sub(r"([.!?]){2,}", r"\1", out)  # info: set out
    for i, tag in enumerate(_tag_slots):  # info: for i , tag in enumerate ( _tag_slots
        out = out.replace(f"\0IPATAG{i}\0", tag)  # info: set out
    # Keep HST whole — otherwise "Hawaiian" → place syllables mid-phrase.
    _hst_slots: list[str] = []  # info: set _hst_slots

    def _park_hst(m: re.Match) -> str:  # info: def _park_hst
        _hst_slots.append(m.group(0))  # info: _hst_slots . append ( m . group (
        return f"\0HSTPHRASE{len(_hst_slots) - 1}\0"  # info: return f" \0HSTPHRASE { len ( _hst_slots )

    out = re.sub(r"(?i)\bHawaii(?:an)? Standard Time\b", _park_hst, out)  # info: set out
    # Place names → spaced English (Kill ah way uh). Not IPA tags.
    out = pronounce_places(out)  # info: set out
    for i, phrase in enumerate(_hst_slots):  # info: for i , phrase in enumerate ( _hst_slots
        # Keep "Standard Time" intact — do not run place respell on this phrase.
        out = out.replace(f"\0HSTPHRASE{i}\0", "Hawaii Standard Time")  # info: set out
    # Do not strip "." — that would turn "a.m." into "a.m".
    return out.strip(" ,;")  # info: return out . strip ( " ,;" )
