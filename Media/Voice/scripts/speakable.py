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
    r"(?<![\d\-])(?:"  # info: r"(?<![\d\-])(?:"
    r"(?:at\s+|about\s+)?([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?"  # info: colon clock, optional at or about
    r"|"  # info: r"|"
    r"(?:at\s+|about\s+)([01]?\d|2[0-3])\s+([0-5]\d)"  # info: spaced clock only after at or about, so "12 km" stays a distance
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
# SECTION: _STATE_NAMES
# What it does: Postal abbreviations spoken as full state names. A comma must come first, so ordinary words stay words.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_STATE_NAMES = {  # info: set _STATE_NAMES
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",  # info: postal codes
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",  # info: postal codes
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",  # info: postal codes
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",  # info: postal codes
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",  # info: postal codes
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",  # info: postal codes
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",  # info: postal codes
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",  # info: postal codes
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",  # info: postal codes
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",  # info: postal codes
    "DC": "District of Columbia",  # info: "DC" : "District of Columbia" ,
}  # info: }


# ====================================================
# SECTION: function _expand_states
# What it does: Turn a comma and a postal code into the state name. Does not expand a code with no comma.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _expand_states(text: str) -> str:  # info: def _expand_states
    def _name(match: re.Match) -> str:  # info: def _name
        full = _STATE_NAMES.get(match.group(1))  # info: set full
        return f", {full}" if full else match.group(0)  # info: return f" , { full } " if full else match . group ( 0 )
    return re.sub(r",\s*([A-Z]{2})\b", _name, text)  # info: return re . sub


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
    out = re.sub(r"(?i)(?<=\d)\s*°\s*C\b", " degrees Celsius", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)°C\b", " degrees Celsius", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*degrees\s+C\b(?!elsius)", " degrees Celsius", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*°?\s*F\b", " degrees Fahrenheit", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)°?F\b", " degrees Fahrenheit", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*deg(?:rees?)?\s*F\b", " degrees Fahrenheit", out)  # info: set out
    out = re.sub(r"(?<=\d)\s*degrees\b(?!\s+(?:Fahrenheit|Celsius))", " degrees Fahrenheit", out)  # info: set out
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
    # NHC field glue: "WINDS.90 MPH" / "MOVEMENT.W OR" → spaced before unit expand.
    out = re.sub(r"(?<=[A-Za-z])\.(?=\d)", " ", out)  # info: split WORD.90
    out = re.sub(r"(?<=[A-Za-z])\.(?=[NSEW]\b)", " ", out)  # info: split MOVEMENT.W
    # Dual metric tags NHC writes as "150 KM, H" / "150 KM/H".
    out = re.sub(r"(?i)(?<=\d)\s*km\s*[,/]\s*h\b", " kilometers per hour", out)  # info: km,h → km/h words
    out = re.sub(r"(?i)\bmph\b", "miles per hour", out)  # info: mph / MPH
    out = re.sub(r"(?i)\bmiles per hour\b", "miles per hour", out)  # info: set out
    out = re.sub(r"(?i)\bnmi\b", "nautical miles", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*nm\b", " nautical miles", out)  # info: set out
    out = re.sub(r"\bNWS\b", "National Weather Service", out)  # info: set out
    out = _expand_states(out)  # info: set out
    out = re.sub(r"\bU\. ?S\. ?G\. ?S\.?", "United States Geological Survey", out)  # info: set out
    out = re.sub(r"\bUSGS\b", "United States Geological Survey", out)  # info: set out
    out = re.sub(r"\bU\. ?S\.", "United States", out)  # info: set out
    out = re.sub(r"\bHST\b", "Hawaiian Standard Time", out)  # info: set out
    out = re.sub(r"\bHI alerts\b", "Hawaii alerts", out)  # info: set out
    out = re.sub(r"(?i)\bH(?:\.|\s)*I\.?\b", "Hawaii", out)  # info: set out
    out = re.sub(r"\bHI\b", "Hawaii", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)\s*km\b", " kilometers", out)  # info: set out
    out = re.sub(r"(?i)(?<=\d)km\b", " kilometers", out)  # info: set out
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
    # Lone cardinal after movement / toward (NHC "PRESENT MOVEMENT W OR 275").
    out = re.sub(r"(?i)\b((?:movement|toward|towards|from|to)\s+)W\b", r"\1west", out)  # info: movement W → west
    out = re.sub(r"(?i)\b((?:movement|toward|towards|from|to)\s+)E\b", r"\1east", out)  # info: movement E → east
    out = re.sub(r"(?i)\b((?:movement|toward|towards|from|to)\s+)N\b", r"\1north", out)  # info: movement N → north
    out = re.sub(r"(?i)\b((?:movement|toward|towards|from|to)\s+)S\b", r"\1south", out)  # info: movement S → south
    out = re.sub(r"\bCPU\b", "processor", out)  # info: set out
    out = re.sub(r"\bRAM\b", "memory", out)  # info: set out
    out = re.sub(r"\bNPU\b", "neural processor", out)  # info: set out
    out = re.sub(r"\bi_gpu\b", "graphics", out, flags=re.I)  # info: set out
    out = re.sub(r"\bGPU\b", "graphics", out)  # info: set out
    out = re.sub(r"\bPV\b", "solar", out)  # info: set out
    # Knots / millibars — case-insensitive so NHC "80 KT" / "80 KTS" never reads as letters.
    out = re.sub(r"(?i)\bkts?\b", "knots", out)  # info: kt / KT / kts → knots
    out = re.sub(r"(?i)\bmb\b", "millibars", out)  # info: mb / MB
    # Drop redundant dual-unit tails (NHC lists knots + mph + km/h).
    out = re.sub(  # info: keep knots, drop following mph
        r"(?i)(\d+(?:\.\d+)?\s*knots)\s+\d+(?:\.\d+)?\s*miles per hour",
        r"\1",
        out,
    )  # info: )
    out = re.sub(  # info: keep knots, drop following km/h
        r"(?i)(\d+(?:\.\d+)?\s*knots)\s+\d+(?:\.\d+)?\s*kilometers per hour",
        r"\1",
        out,
    )  # info: )
    out = re.sub(  # info: keep mph, drop following km/h duplicate
        r"(?i)(\d+(?:\.\d+)?\s*miles per hour)\s+\d+(?:\.\d+)?\s*kilometers per hour",
        r"\1",
        out,
    )  # info: )
    out = re.sub(r"(?<=\d)\s*%", " percent", out)  # info: set out
    out = re.sub(r"(?<=\d)%", " percent", out)  # info: set out
    # Soften NHC ALL-CAPS labels so Kokoro says "winds" not letter-salad.
    out = re.sub(  # info: 4+ letter ALL-CAPS words → lowercase (keep short codes)
        r"\b[A-Z]{4,}\b",
        lambda m: m.group(0) if m.group(0) in {"NWS", "USGS", "UTC", "GMT", "NHC", "NOAA"} else m.group(0).lower(),
        out,
    )  # info: )
    # Short shouted fillers left by NHC products.
    out = re.sub(r"\b(?:TO|OR|AT|OF|IN|ON|BY|AS|IS|MAX|MIN)\b", lambda m: m.group(0).lower(), out)  # info: TO/OR/AT/MAX → lower
    return out  # info: return out


# ====================================================
# SECTION: function _scrub_unspeakable
# What it does: Drop URLs, lat/lon coordinates, and long digit strings before TTS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _scrub_unspeakable(text: str) -> str:  # info: def _scrub_unspeakable
    """Drop URLs, coordinates, NWS/NHC boilerplate, and long digit runs so Kokoro never reads them aloud."""  # info: docstring
    out = text or ""  # info: set out
    # Forecast advisory radii / seas grids BEFORE turning NWS "..." into spaces.
    out = re.sub(r"\b\d{1,3}\s*KT\.+\s*(?:\d{1,3}[NESW]{2}\s*)+", " ", out, flags=re.I)  # info: strip wind radii dotted
    out = re.sub(r"\b\d{1,3}\s*KT\.?\s+(?:\d{1,3}[NESW]{2}\s*){3,}", " ", out, flags=re.I)  # info: strip wind radii spaced
    out = re.sub(r"\b\d\s*M\s*SEAS\.+\s*(?:\d{1,3}[NESW]{2}\s*)+", " ", out, flags=re.I)  # info: strip seas radii dotted
    out = re.sub(r"\b\d\s*M\s*SEAS\.?\s+(?:\d{1,3}[NESW]{2}\s*){3,}", " ", out, flags=re.I)  # info: strip seas radii spaced
    out = re.sub(r"(?i)\brepeat\b\.+\s*center\b", " ", out)  # info: strip REPEAT...CENTER
    out = out.replace("...", " ")  # info: NWS uses ... as separators — turn into spaces
    out = out.replace("…", " ")  # info: unicode ellipsis
    # Full URLs and www hosts (keep the surrounding sentence when possible).
    out = re.sub(r"(?i)\b(?:https?://|www\.)\S+", " ", out)  # info: strip http/https/www
    out = re.sub(r"(?i)\bmore at\b[:\s]*", " ", out)  # info: drop "More at" lead-in left by URL strip
    # Bare domains that news blurbs append (nsf.gov/events/...).
    out = re.sub(r"(?i)\b(?:[\w-]+\.)+(?:gov|com|org|edu|net|io|cloud|us)(?:/[\w./?&=%-]*)?", " ", out)  # info: strip bare domains
    # NHC timezone legend only (keep ordinary "Hawaiian Standard Time" in desk copy).
    out = re.sub(r"(?i)\bz indicates coordinated universal time\b[^.]*\.?", " ", out)  # info: strip Z indicates UTC
    out = re.sub(  # info: strip "Pacific Daylight Time (PDT).SUBTRACT 7 HOURS FROM Z TIME"
        r"(?i)\b(?:pacific|hawaiian|hawaii|eastern|central|mountain|alaska)\s+"
        r"(?:daylight|standard)\s+time\s*(?:\([^)]*\))?\.?\s*"
        r"subtract\s+\d+\s+hours?(?:\s+from\s+z\s+time)?\b",
        " ",
        out,
    )  # info: )
    out = re.sub(r"(?i)\bsubtract\s+\d+\s+hours?\s+from\s+z\s+time\b", " ", out)  # info: strip subtract from Z time
    out = re.sub(r"(?i)\bsubtract\s+\d+\s+hours?\b[^.]*", " ", out)  # info: any leftover subtract-hours line
    # Wind-speed probability table lead-in + chance lines (NHC FOPZ products).
    out = re.sub(  # info: strip probability table block start through next story break when possible
        r"(?i)\bwind speed probability table for specific locations\b.*?(?=\bthe national hurricane center reports\b|\bthat is the news update\b|$)",
        " ",
        out,
    )  # info: )
    out = re.sub(r"(?i)\bchances of sustained\b[^.]*", " ", out)  # info: strip chances-of-sustained lead-in
    out = re.sub(r"\b(?:\d{1,3}[NESW]{2}\s*){3,}", " ", out, flags=re.I)  # info: strip leftover quadrant lists
    out = re.sub(r"(?i)\bwinds and seas vary greatly in each quadrant\b[^.]*\.?", " ", out)  # info: strip radii disclaimer
    out = re.sub(r"(?i)\bradii in nautical miles are the largest radii expected anywhere in that quadrant\b\.?", " ", out)  # info: strip radii disclaimer 2
    # Lat/lon — pairs first so LOCATION...19.4N does not leave 111.8W for the watts expander.
    out = re.sub(r"\b\d{1,3}(?:\.\d+)?\s*°?\s*[NS]\s*[,/]?\s*\d{1,3}(?:\.\d+)?\s*°?\s*[EW]\b", " ", out, flags=re.I)  # info: strip 19.4N 111.8W
    out = re.sub(  # info: near lat/lon pair → short place phrase
        r"(?i)\bnear\s+latitude\s+[-\d.]+\s*(?:north|south)?\s*[.,]?\s*longitude\s+[-\d.]+\s*(?:east|west)?",
        "near its reported position",
        out,
    )  # info: )
    out = re.sub(r"(?i)\blatitude\s+[-\d.]+\s*(?:north|south)?\.?", " ", out)  # info: strip latitude N/S
    out = re.sub(r"(?i)\blongitude\s+[-\d.]+\s*(?:east|west)?\.?", " ", out)  # info: strip longitude E/W
    out = re.sub(  # info: strip LOCATION.19.4N 111.8W / LOCATION...19.4N as a whole
        r"(?i)\blocation\.?\s*[:=]?\s*-?\d{1,3}(?:\.\d+)?\s*[nsew]?(?:\s+-?\d{1,3}(?:\.\d+)?\s*[nsew])?",
        " ",
        out,
    )  # info: )
    out = re.sub(r"(?i)\b(?:lat|lon|long)\.?\s*[:=]?\s*-?\d{1,3}(?:\.\d+)?\s*[nsew]?\b", " ", out)  # info: strip lat=/lon=
    out = re.sub(r"\b-?\d{1,3}\.\d{2,}\s*[,/]\s*-?\d{1,3}\.\d{2,}\b", " ", out)  # info: strip decimal degree pairs
    # Lone degree crumbs (must go before unit expand turns 111.8W into "watts").
    out = re.sub(r"\b\d{1,3}(?:\.\d+)?\s*°?\s*[NSEW]\b", " ", out)  # info: strip lone 19.4N / 111.8W
    out = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", " ", out)  # info: strip IPv4-looking dotted quads
    # NWS / NHC WMO header crumbs: 000 WTPZ43 KNHC 030836 TCDEP3 (also mid-string, not only line-start).
    out = re.sub(r"\b\d{3}\s+[A-Z]{3,5}\d{0,3}\s+K[A-Z]{3}\s+\d{5,6}\s+[A-Z0-9]{4,}\b", " ", out)  # info: strip WMO headers
    out = re.sub(r"\b(?:WTPZ|FOPZ|TCMEP|TCPEP|TCDEP|ABNT|ABPZ|TWOAT|TWOEP|PWSEP|PWSAT)\d{0,3}\b", " ", out, flags=re.I)  # info: strip AWIPS ids
    out = re.sub(r"\bEP\d{6}\b", " ", out)  # info: strip storm product ids EP182026
    out = re.sub(r"\b\d{2}/\d{4}Z\b", " ", out)  # info: strip 03/0900Z stamps
    out = re.sub(r"(?i)\b\$\$\s*forecaster\s+\w+\b", " ", out)  # info: strip $$ Forecaster Name
    out = out.replace("$", " ")  # info: never speak dollar signs (NHC $$ / money crumbs)
    out = out.replace("&", " and ")  # info: never speak ampersands — say "and"
    # If named storms are present, drop contradictory "no tropical cyclones" sentences.
    if re.search(r"(?i)\b(?:hurricane|tropical storm|tropical depression)\s+[A-Za-z]", out):  # info: if named storm present
        out = re.sub(r"(?i)[^.?!]*\bno tropical cyclones\b[^.?!]*[.?!]?", " ", out)  # info: drop quiet basin claims
        out = re.sub(r"(?i)[^.?!]*\bthere are no tropical cyclone\b[^.?!]*[.?!]?", " ", out)  # info: drop no-tropical claims
    out = re.sub(r"-{3,}", " ", out)  # info: strip dash runs from NWS summaries
    # USGS quake feed crumbs that sneak into news titles.
    out = re.sub(r"(?i)\bpager\s*-\s*\w+\b", " ", out)  # info: strip PAGER - GREEN
    out = re.sub(r"(?i)\bshakemap\s*-\s*[IVXLC]+\b", " ", out)  # info: strip ShakeMap - III
    out = re.sub(r"(?i)\bdyfi\??\s*-\s*[IVXLC]+\b", " ", out)  # info: strip DYFI? - IV
    # Long digit runs (product IDs, stamps) — keep shorter spoken numbers (temps, years, percents).
    out = re.sub(r"\b\d{6,}\b", " ", out)  # info: strip 6+ digit runs
    out = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", " ", out, flags=re.I)  # info: strip UUIDs
    out = re.sub(r"\b[0-9a-f]{32,}\b", " ", out, flags=re.I)  # info: strip long hex
    out = re.sub(r"(?i)\bat\s+near\b", "near", out)  # info: fix "at near" after coord strip
    out = re.sub(r"(?i)\blocated\s+near\s+at\b", "located near", out)  # info: fix "located near at" after coord strip
    out = re.sub(r"(?i)\bnear\s+at\b", "near", out)  # info: fix "near at"
    out = re.sub(r"(?i)\bposition\s+accurate\s+within\s+\d+\s*n\.?m\.?\b", " ", out)  # info: strip POSITION ACCURATE WITHIN 20 NM
    out = re.sub(r"(?i)\blocated\s+near\s+position\b", "located near its reported position", out)  # info: fix after coord+stamp strip
    out = re.sub(  # info: fix "located near PRESENT MOVEMENT" after stamp/position strip
        r"(?i)\blocated\s+near\s+(?=present\s+movement\b)",
        "located near its reported position. ",
        out,
    )  # info: )
    out = re.sub(r"(?i)\blocation\s+(?=about\b|maximum\b|present\b)", " ", out)  # info: drop orphan LOCATION field label
    out = re.sub(r"(?i)\beast of\s+\d{1,3}\s+longitude\b", "east of the International Date Line", out)  # info: soften 180 longitude
    out = re.sub(r"\s+([.,;:])", r"\1", out)  # info: trim space before punctuation
    out = re.sub(r"^[.,;:\s]+|[.,;:\s]+$", "", out)  # info: trim orphan punctuation ends
    out = re.sub(r"\s{2,}", " ", out)  # info: collapse spaces
    return out.strip()  # info: return out


# ====================================================
# SECTION: function speakable
# What it does: speakable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speakable(text: str) -> str:  # info: def speakable
    out = " ".join((text or "").replace("\u00a0", " ").split())  # info: set out
    out = _scrub_unspeakable(out)  # info: drop URLs, coordinates, long digit strings first
    out = " ".join(out.split())  # info: collapse spaces left by scrub
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
    _days = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday", "sat": "Saturday"}  # info: short weekdays
    out = re.sub(r"(?i)\b(mon|tue|wed|thu|fri|sat)\b", lambda m: _days[m.group(1).lower()], out)  # info: fri says Friday
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
