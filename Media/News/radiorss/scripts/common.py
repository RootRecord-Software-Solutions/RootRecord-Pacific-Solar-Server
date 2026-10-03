# ==============================================================================
# FILE: Media/RadioRss/scripts/common.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Paths, clocks, and text helpers for the external RSS layer."""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import html  # info: import html
import os  # info: import os
import re  # info: import re
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit  # info: from urllib . parse import parse_qsl , urlencode , urlsplit , urlunsplit

HERE = Path(__file__).resolve().parent  # info: set HERE
RADIO = HERE.parent  # info: set RADIO
PACIFIC = Path(os.environ.get(  # info: voice / Pacific scripts
    "RR_PACIFIC_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server",
))
DB = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
ROOT = Path(os.environ.get(
    "RR_NEWS_DATA_ROOT",
    str(DB / "Media" / "News Data"),
))
TAG_RE = re.compile(r"<[^>]+>")  # info: set TAG_RE
SPACE_RE = re.compile(r"\s+")  # info: set SPACE_RE
WORD_RE = re.compile(r"[a-z0-9]+")  # info: set WORD_RE
STOP = {  # info: set STOP
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "from",  # info: "a" , "an" , "the" , "and" , "or" , "of" , "to" , "in" , "on" , "for" , "with" , "from" ,
    "by", "at", "as", "is", "are", "was", "be", "its", "it", "that", "this", "after",  # info: "by" , "at" , "as" , "is" , "are" , "was" , "be" , "its" , "it" , "that" , "this" , "after" ,
}  # info: }


# ====================================================
# SECTION: function config_dir
# What it does: Return the YAML directory. RR_RADIO_RSS_CONFIG overrides the desk copy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def config_dir() -> Path:  # info: def config_dir
    raw = os.environ.get("RR_RADIO_RSS_CONFIG", "")  # info: set raw
    if raw:  # info: if raw :
        return Path(raw)  # info: return Path ( raw )
    return RADIO / "config"  # info: return RADIO / "config"


# ====================================================
# SECTION: function utc_now
# What it does: Return the current UTC time with seconds only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def utc_now() -> datetime:  # info: def utc_now
    return datetime.now(timezone.utc).replace(microsecond=0)  # info: return datetime . now ( timezone . utc ) . replace ( microsecond = 0 )


# ====================================================
# SECTION: function iso
# What it does: Format a datetime as UTC ISO-8601. Empty input stays empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def iso(value: datetime | None) -> str:  # info: def iso
    if value is None:  # info: if value is None :
        return ""  # info: return ""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # info: return value . astimezone ( timezone . utc ) . strftime ( "%Y-%m-%dT%H:%M:%SZ" )


# ====================================================
# SECTION: function parse_iso
# What it does: Parse a Zulu timestamp written by iso().
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_iso(value: str | None) -> datetime | None:  # info: def parse_iso
    if not value:  # info: if not value :
        return None  # info: return None
    try:  # info: try
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)  # info: return datetime . strptime ( value , "%Y-%m-%dT%H:%M:%SZ" ) . replace ( tzinfo = timezone . utc )
    except ValueError:  # info: except ValueError
        return None  # info: return None


# ====================================================
# SECTION: function plain
# What it does: Turn HTML or escaped text into one plain line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def plain(value: str | None, limit: int = 1200) -> str:  # info: def plain
    text = html.unescape(value or "")  # info: set text
    text = TAG_RE.sub(" ", text)  # info: set text
    text = SPACE_RE.sub(" ", text).strip()  # info: set text
    if len(text) > limit:  # info: if len ( text ) > limit :
        text = text[: limit - 1].rstrip() + "…"  # info: set text
    return text  # info: return text


# ====================================================
# SECTION: function title_norm
# What it does: Lowercase a title down to words so duplicates can match.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def title_norm(value: str) -> str:  # info: def title_norm
    return " ".join(WORD_RE.findall((value or "").lower()))  # info: return " " . join ( WORD_RE . findall ( ( value or "" ) . lower ( ) ) )


# ====================================================
# SECTION: function tokens
# What it does: Return significant words from a title for similarity.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tokens(value: str) -> set[str]:  # info: def tokens
    return {word for word in WORD_RE.findall((value or "").lower()) if word not in STOP and len(word) > 2}  # info: return { word for word in WORD_RE . findall ( ( value or "" ) . lower ( ) ) if word not in STOP and len ( word ) > 2 }


# ====================================================
# SECTION: function jaccard
# What it does: Score how much two word sets overlap. This is the similarity signal.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def jaccard(left: set[str], right: set[str]) -> float:  # info: def jaccard
    if not left or not right:  # info: if not left or not right :
        return 0.0  # info: return 0.0
    return len(left & right) / len(left | right)  # info: return len ( left & right ) / len ( left | right )


# ====================================================
# SECTION: function digest
# What it does: Short sha256 hex for ids and content hashes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def digest(*parts: str, n: int = 20) -> str:  # info: def digest
    raw = "\n".join(parts).encode("utf-8")  # info: set raw
    return hashlib.sha256(raw).hexdigest()[:n]  # info: return hashlib . sha256 ( raw ) . hexdigest ( ) [ : n ]


# ====================================================
# SECTION: function canonical_url
# What it does: Drop fragments and tracking query keys so the same article matches.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def canonical_url(value: str | None) -> str:  # info: def canonical_url
    if not value:  # info: if not value :
        return ""  # info: return ""
    parts = urlsplit(value.strip())  # info: set parts
    if parts.scheme not in {"http", "https"} or not parts.netloc:  # info: if parts . scheme not in { "http" , "https" } or not parts . netloc :
        return ""  # info: return ""
    query = [  # info: set query
        (key, item)  # info: ( key , item )
        for key, item in parse_qsl(parts.query, keep_blank_values=True)  # info: for key , item in parse_qsl ( parts . query , keep_blank_values = True )
        if not key.lower().startswith("utm_") and key.lower() not in {"fbclid", "mc_cid", "mc_eid"}  # info: if not key . lower ( ) . startswith ( "utm_" ) and key . lower ( ) not in { "fbclid" , "mc_cid" , "mc_eid" }
    ]  # info: ]
    path = parts.path.rstrip("/") or "/"  # info: set path
    return urlunsplit(("https", parts.netloc.lower(), path, urlencode(query), ""))  # info: return urlunsplit ( ( "https" , parts . netloc . lower ( ) , path , urlencode ( query ) , "" ) )


# ====================================================
# SECTION: function provider_slug
# What it does: Make a folder name from a provider label.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def provider_slug(name: str) -> str:  # info: def provider_slug
    slug = "_".join(WORD_RE.findall((name or "source").lower()))  # info: set slug
    return slug or "source"  # info: return slug or "source"


# ====================================================
# SECTION: function log_line
# What it does: Append one RSS log line. A logging failure must not stop the station.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_line(message: str) -> None:  # info: def log_line
    try:  # info: try
        path = DB / "Logs" / "Media" / "RadioRss" / "rss.log"  # info: set path
        path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents = True , exist_ok = True )
        with path.open("a", encoding="utf-8") as handle:  # info: with path . open ( "a" , encoding = "utf-8" ) as handle
            handle.write(iso(utc_now()) + " " + message.strip() + "\n")  # info: handle . write ( iso ( utc_now ( ) ) + " " + message . strip ( ) + "\n" )
    except OSError:  # info: except OSError
        return  # info: return
