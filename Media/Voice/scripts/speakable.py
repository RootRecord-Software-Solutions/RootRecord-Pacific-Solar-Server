# G3 port 2026-09-29 (g3-voice-ailog): copied verbatim from G1 old skills/kokoro/scripts/speakable.py (source kept in place).
"""Make report prose speakable for Kokoro. Clocks, units, no name-intros."""
from __future__ import annotations

import re
from datetime import datetime

_ONES = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)
_TENS = ("", "", "twenty", "thirty", "forty", "fifty")
_HOURS = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
}

_REDUNDANT = re.compile(
    r"(?i)\s*(?:"
    r"measured facts only(?:[^.!\n]*)|"
    r"facts only(?:[^.!\n]*)|"
    r"do not invent(?:\s+numbers)?(?:[^.!\n]*)|"
    r"no invented numbers(?:[^.!\n]*)|"
    r"use only measured facts(?:[^.!\n]*)|"
    r"live numbers only from live facts(?:[^.!\n]*)|"
    r"do not invent cloud cover(?:[^.!\n]*)"
    r")[.!]?"
)

_VOICE_SRC = re.compile(
    r"(?i)[^.!?\n]*\b(?:"
    r"voice mode|"
    r"clip packs?|"
    r"phrase clips|"
    r"paid (?:cloud )?voice|"
    r"paid tts|"
    r"local clip|"
    r"kokoro|"
    r"report-generation|"
    r"toggle tts|"
    r"full report mp3|"
    r"prefer local phrase|"
    r"voice packs|"
    r"voice engine|"
    r"tts engine|"
    r"generated with|"
    r"clip.?stitch"
    r")\b[^.!?\n]*[.!]?"
)

_STORE_SRC = re.compile(
    r"(?i)\s*\((?:[^)]*(?:source|jsonl|sqlite|from disk|file \d|last \d)[^)]*)\)"
)

_READ_FROM = re.compile(
    r"(?i)\b(?:read|loaded|pulled|fetched|synced)\s+from\b[^.!?\n]*[.!]?"
    r"|\bfrom (?:disk|sqlite|jsonl|the store|file)\b[^.!?\n]*[.!]?"
)

# YYYY-MM-DD HH:MM (space) — park before bare clocks so "16 19" is not a time.
_DATE_CLOCK = re.compile(
    r"\b(\d{4})-(\d{2})-(\d{2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)

# Colon clocks, or "about 12 37" — never after a digit/hyphen (avoids date day + hour).
_CLOCK = re.compile(
    r"(?<![\d\-])(?:at\s+|about\s+)?"
    r"(?:"
    r"([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?"
    r"|"
    r"([01]?\d|2[0-3])\s+([0-5]\d)"
    r")"
    r"(?:\s*([AaPp])\.?\s*[Mm]\.?)?\b"
)

_ISO = re.compile(
    r"\b(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)

_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _minute_words(minute: int) -> str:
    m = int(minute)
    if m < 20:
        return _ONES[m]
    tens, ones = divmod(m, 10)
    if ones:
        return f"{_TENS[tens]} {_ONES[ones]}"
    return _TENS[tens]


def spoken_clock(hour: int, minute: int) -> str:
    """midnight, noon, one PM, two thirty PM."""
    hour = int(hour) % 24
    minute = int(minute)
    if hour == 0 and minute == 0:
        return "midnight"
    if hour == 12 and minute == 0:
        return "noon"
    h12 = hour % 12 or 12
    ampm = "a.m." if hour < 12 else "p.m."
    name = _HOURS[h12]
    if minute == 0:
        return f"{name} {ampm}"
    return f"{name} {_minute_words(minute)} {ampm}"


def _apply_meridian(hour: int, mer: str | None, *, hint: str = "") -> int:
    """Return 0–23. hint may include 'morning' / 'afternoon' when no A/P marker."""
    h = int(hour)
    m = (mer or "").upper()[:1]
    hint_l = (hint or "").lower()
    if not m:
        if "morning" in hint_l or "a.m" in hint_l:
            m = "A"
        elif "afternoon" in hint_l or "evening" in hint_l or "p.m" in hint_l or "night" in hint_l:
            m = "P"
    if m == "A":
        h = h % 12
    elif m == "P":
        h = h % 12
        h = 12 if h == 0 else h + 12
    return h


def _clock_match(m: re.Match, *, after: str = "") -> str:
    raw = m.group(0)
    if m.group(1) is not None:
        hour = int(m.group(1))
        minute = int(m.group(2))
        mer = m.group(5)
    else:
        hour = int(m.group(3))
        minute = int(m.group(4))
        mer = m.group(5)
    hour = _apply_meridian(hour, mer, hint=after)
    spoken = spoken_clock(hour, minute)
    low = raw.lower().lstrip()
    if low.startswith("about"):
        return f"about {spoken}"
    if low.startswith("at"):
        return f"at {spoken}"
    return spoken


def _date_clock_match(m: re.Match) -> str:
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    hour, minute = int(m.group(4)), int(m.group(5))
    raw = m.group(0)
    # If timezone present on a space/T stamp, prefer Honolulu for spoken local.
    if "T" in raw or raw.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", raw):
        try:
            iso = raw.replace(" ", "T", 1)
            if iso.endswith("Z"):
                iso = iso[:-1] + "+00:00"
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}", iso):
                iso = iso + ":00"
            dt = datetime.fromisoformat(iso)
            if dt.tzinfo is not None:
                from zoneinfo import ZoneInfo

                dt = dt.astimezone(ZoneInfo("Pacific/Honolulu"))
            month, day, hour, minute = dt.month, dt.day, dt.hour, dt.minute
        except Exception:
            pass
    if not (1 <= month <= 12):
        return raw
    return f"{_MONTHS[month - 1]} {day} at {spoken_clock(hour, minute)}"


def _iso_match(m: re.Match) -> str:
    try:
        raw = m.group(0)
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is not None:
            from zoneinfo import ZoneInfo

            dt = dt.astimezone(ZoneInfo("Pacific/Honolulu"))
        return f"{_MONTHS[dt.month - 1]} {dt.day} at {spoken_clock(dt.hour, dt.minute)}"
    except Exception:
        return spoken_clock(int(m.group(2)), int(m.group(3)))


def _sub_clocks(text: str) -> str:
    """Expand clocks with trailing morning/afternoon hints."""

    def repl(m: re.Match) -> str:
        return _clock_match(m, after=text[m.end() : m.end() + 32])

    return _CLOCK.sub(repl, text)


def _expand_units(text: str) -> str:
    out = text
    out = re.sub(r"(?i)\berupting\s*=\s*false\b", "not erupting", out)
    out = re.sub(r"(?i)\berupting\s*=\s*true\b", "is erupting", out)
    out = re.sub(r"(?i)\bsource\s*=\s*[A-Za-z0-9_-]+", "", out)
    out = re.sub(r"\b([A-Za-z][A-Za-z0-9_-]*)=([A-Za-z0-9._-]+)", r"\1 \2", out)
    out = out.replace(" — ", ". ")
    out = out.replace(" – ", ". ")
    out = out.replace(" | ", ". ")
    out = re.sub(r"\s*/\s*", ", ", out)
    out = re.sub(r"\bi_gpu\b", "graphics", out, flags=re.I)
    out = re.sub(r"\bnpu\b", "neural processor", out, flags=re.I)
    out = out.replace("_", " ")
    out = re.sub(r"~", " about ", out)
    out = re.sub(r"(?i)\bjsonl\b", "", out)
    out = re.sub(r"(?i)\b(?:jsonl|sqlite|from disk)\b", "", out)
    out = re.sub(r"(?i)\bWeather\s*\([^)]*\)\s*:?", "Weather.", out)
    out = re.sub(r"(?i)\bEcoFlow\s*\([^)]*\)\s*:?", "EcoFlow.", out)
    out = re.sub(r"(?i)\bHost:\s*last [^,]+,\s*", "Host: ", out)
    out = re.sub(r"(?i)(?<=\d)\s*°?\s*F\b", " degrees Fahrenheit", out)
    out = re.sub(r"(?i)(?<=\d)°?F\b", " degrees Fahrenheit", out)
    out = re.sub(r"(?i)(?<=\d)\s*deg(?:rees?)?\s*F\b", " degrees Fahrenheit", out)
    out = re.sub(r"(?<=\d)\s*degrees\b(?!\s+Fahrenheit)", " degrees Fahrenheit", out)
    out = re.sub(r"(?i)(\d+(?:\.\d+)?)\s*h(?:ours?|rs?)?\s*old", r"about \1 hours old", out)
    out = re.sub(r"(?<=\d)\s*hrs?\b", " hours", out)
    out = re.sub(r"(?<=\d)\s*h(?!ours|\d)\b", " hours", out)
    out = re.sub(r"\(\s*,", "(", out)
    out = re.sub(r",\s*\)", ")", out)
    out = re.sub(r"\(\s*\)", "", out)
    out = re.sub(r"\bSoC\b", "state of charge", out)
    out = re.sub(r"\bSOC\b", "state of charge", out)
    out = re.sub(r"(?i)\bstate of charge\b", "state of charge", out)
    out = re.sub(r"\bkWh\b", "kilowatt hours", out)
    out = re.sub(r"\bWh\b", "watt hours", out)
    out = re.sub(r"\bkW\b", "kilowatts", out)
    out = re.sub(r"(?<=\d)\s*W\b", " watts", out)
    out = re.sub(r"(?<=\d)W\b", " watts", out)
    out = re.sub(r"\bmph\b", "miles per hour", out)
    out = re.sub(r"(?i)\bmiles per hour\b", "miles per hour", out)
    out = re.sub(r"\bnmi\b", "nautical miles", out)
    out = re.sub(r"(?<=\d)\s*nm\b", " nautical miles", out)
    out = re.sub(r"\bNWS\b", "National Weather Service", out)
    out = re.sub(r"\bUSGS\b", "U. S. Geological Survey", out)
    out = re.sub(r"\bHST\b", "Hawaiian Standard Time", out)
    out = re.sub(r"\bHI alerts\b", "Hawaii alerts", out)
    out = re.sub(r"(?i)\bH(?:\.|\s)*I\.?\b", "Hawaii", out)
    out = re.sub(r"\bHI\b", "Hawaii", out)
    out = re.sub(r"(?<=\d)\s*km\b", " kilometers", out)
    out = re.sub(r"(?<=\d)km\b", " kilometers", out)
    out = re.sub(r"(?i)(?<=\d)\s*mi\b(?!\w)", " miles", out)
    out = re.sub(r"(?i)(?<=\d)mi\b(?!\w)", " miles", out)
    out = re.sub(r"\bSSW\b", "south-southwest", out)
    out = re.sub(r"\bSSE\b", "south-southeast", out)
    out = re.sub(r"\bNNE\b", "north-northeast", out)
    out = re.sub(r"\bNNW\b", "north-northwest", out)
    out = re.sub(r"\bENE\b", "east-northeast", out)
    out = re.sub(r"\bESE\b", "east-southeast", out)
    out = re.sub(r"\bWNW\b", "west-northwest", out)
    out = re.sub(r"\bWSW\b", "west-southwest", out)
    out = re.sub(r"\bNE\b", "northeast", out)
    out = re.sub(r"\bNW\b", "northwest", out)
    out = re.sub(r"\bSE\b", "southeast", out)
    out = re.sub(r"\bSW\b", "southwest", out)
    out = re.sub(r"\bS of\b", "south of", out)
    out = re.sub(r"\bN of\b", "north of", out)
    out = re.sub(r"\bE of\b", "east of", out)
    out = re.sub(r"\bW of\b", "west of", out)
    out = re.sub(r"\bCPU\b", "processor", out)
    out = re.sub(r"\bRAM\b", "memory", out)
    out = re.sub(r"\bNPU\b", "neural processor", out)
    out = re.sub(r"\bi_gpu\b", "graphics", out, flags=re.I)
    out = re.sub(r"\bGPU\b", "graphics", out)
    out = re.sub(r"\bPV\b", "solar", out)
    out = re.sub(r"\bkt\b", "knots", out)
    out = re.sub(r"\bmb\b", "millibars", out)
    out = re.sub(r"(?<=\d)\s*%", " percent", out)
    out = re.sub(r"(?<=\d)%", " percent", out)
    return out


def speakable(text: str) -> str:
    out = " ".join((text or "").replace("\u00a0", " ").split())
    try:
        from hawaiian_lexicon import fold_place_spellings, pronounce_places
    except ImportError:
        try:
            from apps.voice.hawaiian_lexicon import fold_place_spellings, pronounce_places
        except ImportError:
            fold_place_spellings = lambda t: t  # noqa: E731
            pronounce_places = lambda t: t  # noqa: E731
    # Park [Name](/ipa/) so slash cleanup cannot destroy them; later → English.
    _tag_slots: list[str] = []

    def _park_tag(m: re.Match) -> str:
        _tag_slots.append(m.group(0))
        return f"\0IPATAG{len(_tag_slots) - 1}\0"

    out = re.sub(r"\[[^\]]+\]\(/[^)]+/\)", _park_tag, out)
    out = fold_place_spellings(out)
    out = re.sub(r"(?i)\bHI-res\b", "high-res", out)
    out = re.sub(r"(?i)\bH(?:\.|\s)*I\.?\b", "Hawaii", out)
    out = re.sub(r"(?i)\bHI alerts\b", "Hawaii alerts", out)
    out = re.sub(r"(?i)\s*Not on the roof\.?", " ", out)
    out = re.sub(r"(?i)\bGround-mounted PV\b", "Ground-mounted solar", out)
    out = _REDUNDANT.sub(" ", out)
    out = _VOICE_SRC.sub(" ", out)
    out = _STORE_SRC.sub(" ", out)
    out = _READ_FROM.sub(" ", out)
    out = _DATE_CLOCK.sub(_date_clock_match, out)
    out = _ISO.sub(_iso_match, out)
    out = _sub_clocks(out)
    out = _expand_units(out)
    out = re.sub(r"(?i)\bnot erupting(?:[. ]+not erupting)+\b", "not erupting", out)
    out = re.sub(r"(?i)\bis erupting(?:[. ]+is erupting)+\b", "is erupting", out)
    out = re.sub(r"\bWATCH\b", "watch", out)
    out = re.sub(r"(?i)(watch[. ]+not erupting)[. ]+watch\b", r"\1", out)
    out = re.sub(r"(?i)\bWeather:\s*Weather\.?", "Weather.", out)
    out = re.sub(r"\(\s+", "(", out)
    out = re.sub(r"\s+\)", ")", out)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([.,:])", r"\1", out)
    out = re.sub(r"([.!?]){2,}", r"\1", out)
    for i, tag in enumerate(_tag_slots):
        out = out.replace(f"\0IPATAG{i}\0", tag)
    # Keep HST whole — otherwise "Hawaiian" → place syllables mid-phrase.
    _hst_slots: list[str] = []

    def _park_hst(m: re.Match) -> str:
        _hst_slots.append(m.group(0))
        return f"\0HSTPHRASE{len(_hst_slots) - 1}\0"

    out = re.sub(r"(?i)\bHawaii(?:an)? Standard Time\b", _park_hst, out)
    # Place names → spaced English (Kill ah way uh). Not IPA tags.
    out = pronounce_places(out)
    for i, phrase in enumerate(_hst_slots):
        # Keep "Standard Time" intact — do not run place respell on this phrase.
        out = out.replace(f"\0HSTPHRASE{i}\0", "Hawaii Standard Time")
    # Do not strip "." — that would turn "a.m." into "a.m".
    return out.strip(" ,;")
