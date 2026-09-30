# ==============================================================================
# FILE: Products/scripts/Look/look.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Look at live stills with the small vision model. llama3.2 still talks.

Moondream (~1.7 GB) captions USGS cam stills and NHC outlook charts.
It does not speak to people. Captions become LOOK notes in live facts.
"""
from __future__ import annotations  # info: from __future__ import annotations

import logging  # info: import logging
import re  # info: import re
import time  # info: import time
import urllib.request  # info: import urllib . request
from pathlib import Path  # info: from pathlib import Path

from apps.core import config  # info: from apps . core import config

log = logging.getLogger("ava.look")  # info: set log

CACHE = config.DATA_DIR / "look"  # info: set CACHE
UA = "AvaIvy/2.0 (https://avaivy.cloud; look)"  # info: set UA
CACHE_S = 180  # info: set CACHE_S

# ====================================================
# SECTION: _LOOK
# What it does: Set _LOOK.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_LOOK = re.compile(  # info: set _LOOK
    r"\b(look|looking|cam|camera|still|picture|photo|screenshot|satellite|outlook|"  # info: r"\b(look|looking|cam|camera|still|picture|photo|screenshot|satellite|outlook|"
    r"nhc map|hurricane map|storm map|cone chart|crater|lava lake|v1cam|v2cam|v3cam|"  # info: r"nhc map|hurricane map|storm map|cone chart|crater|lava lake|v1cam|v2cam|v3cam|"
    r"pack screen|lcd|what does (it|that|the (cam|pack|sky|storm)) look)\b",  # info: r"pack screen|lcd|what does (it|that|the (cam|pack|sky|storm)) look)\b" ,
    re.I,  # info: re . I ,
)  # info: )
_KILAUEA = re.compile(r"\b(kilauea|kīlauea|volcano|lava|cam|camera|crater|halema|v1|v2|v3)\b", re.I)  # info: set _KILAUEA
_NHC = re.compile(r"\b(nhc|hurricane|outlook|satellite|cone|storm map|epac|cpac)\b", re.I)  # info: set _NHC
_PACK = re.compile(r"\b(pack screen|ecoflow screen|lcd|display on the pack)\b", re.I)  # info: set _PACK
_PANELS = re.compile(  # info: set _PANELS
    r"\b(panels?|solar panel|rear shed|energy desk|site cam|shed cam)\b",  # info: r"\b(panels?|solar panel|rear shed|energy desk|site cam|shed cam)\b" ,
    re.I,  # info: re . I ,
)  # info: )

# ====================================================
# SECTION: USGS
# What it does: Set USGS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
USGS = (  # info: set USGS
    ("V1 West Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V1cam/images/M.jpg"),  # info: call (
    ("V2 North Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V2cam/images/M.jpg"),  # info: call (
    ("V3 lava lake", "https://volcanoes.usgs.gov/observatories/hvo/cams/V3cam/images/M.jpg"),  # info: call (
)  # info: )
NHC_FALLBACK = (  # info: set NHC_FALLBACK
    "https://www.nhc.noaa.gov/xgtwo/resize/xgtwo_pac_2d0_w1920.png",  # info: "https://www.nhc.noaa.gov/xgtwo/resize/xgtwo_pac_2d0_w1920.png" ,
    "https://www.nhc.noaa.gov/xgtwo/resize/xgtwo_cpac_2d0_w1920.png",  # info: "https://www.nhc.noaa.gov/xgtwo/resize/xgtwo_cpac_2d0_w1920.png" ,
)  # info: )


# ====================================================
# SECTION: function wants_look
# What it does: wants look.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wants_look(text: str) -> bool:  # info: def wants_look
    return bool(_LOOK.search(text or ""))  # info: return bool ( _LOOK . search ( text


# ====================================================
# SECTION: function _fetch
# What it does:  fetch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fetch(url: str, dest: Path) -> Path | None:  # info: def _fetch
    CACHE.mkdir(parents=True, exist_ok=True)  # info: CACHE . mkdir ( parents = True ,
    if dest.is_file() and (time.time() - dest.stat().st_mtime) < CACHE_S:  # info: if dest . is_file ( ) and (
        return dest  # info: return dest
    try:  # info: try :
        req = urllib.request.Request(url, headers={"User-Agent": UA})  # info: set req
        with urllib.request.urlopen(req, timeout=12) as r:  # info: with urllib . request . urlopen ( req
            raw = r.read()  # info: set raw
        if not raw or len(raw) < 800:  # info: if not raw or len ( raw )
            return dest if dest.is_file() else None  # info: return dest if dest . is_file ( )
        dest.write_bytes(raw)  # info: dest . write_bytes ( raw )
        return dest  # info: return dest
    except Exception as e:  # info: except Exception as e :
        log.info("look fetch miss %s: %s", dest.name, e)  # info: log . info ( "look fetch miss %s: %s" , dest .
        return dest if dest.is_file() else None  # info: return dest if dest . is_file ( )


# ====================================================
# SECTION: function _usgs
# What it does:  usgs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _usgs(asked: str) -> list[tuple[str, Path]]:  # info: def _usgs
    want = USGS  # info: set want
    low = (asked or "").lower()  # info: set low
    if "v1" in low and "v2" not in low and "v3" not in low:  # info: if "v1" in low and "v2" not in
        want = USGS[:1]  # info: set want
    elif "v2" in low:  # info: elif "v2" in low :
        want = USGS[1:2]  # info: set want
    elif "v3" in low or "lake" in low:  # info: elif "v3" in low or "lake" in low
        want = USGS[2:3]  # info: set want
    else:  # info: else :
        want = USGS[:1]  # one still unless they name another
    out = []  # info: set out
    for title, url in want:  # info: for title , url in want :
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:24]  # info: set slug
        path = _fetch(url, CACHE / f"usgs-{slug}.jpg")  # info: set path
        if path:  # info: if path :
            out.append((title, path))  # info: out . append ( ( title , path
    return out  # info: return out


# ====================================================
# SECTION: function _nhc
# What it does:  nhc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _nhc() -> list[tuple[str, Path]]:  # info: def _nhc
    from apps.core.services import nhc_media  # info: from apps . core . services import nhc_media

    files = []  # info: set files
    try:  # info: try :
        current = nhc_media.current_files()  # info: set current
        for slug in ("epac_2day", "cpac_2day", "xgtwo_pac_2d0_w1920", "xgtwo_cpac_2d0_w1920"):  # info: for slug in ( "epac_2day" , "cpac_2day" ,
            p = current.get(slug)  # info: set p
            if p and Path(p).is_file():  # info: if p and Path ( p ) .
                files.append((slug, Path(p)))  # info: files . append ( ( slug , Path
        if not files:  # info: if not files :
            for p in sorted(nhc_media.media_current().glob("*.png"))[:2]:  # info: for p in sorted ( nhc_media . media_current
                files.append((p.stem, p))  # info: files . append ( ( p . stem
    except Exception:  # info: except Exception :
        files = []  # info: set files
    if files:  # info: if files :
        return files[:2]  # info: return files [ : 2 ]
    out = []  # info: set out
    for i, url in enumerate(NHC_FALLBACK[:1]):  # info: for i , url in enumerate ( NHC_FALLBACK
        path = _fetch(url, CACHE / f"nhc-{i}.png")  # info: set path
        if path:  # info: if path :
            out.append(("NHC EPAC 2-day outlook", path))  # info: out . append ( ( "NHC EPAC 2-day outlook" , path
    return out  # info: return out


# ====================================================
# SECTION: function _pack_screens
# What it does:  pack screens.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pack_screens() -> list[tuple[str, Path]]:  # info: def _pack_screens
    from apps.core.services.data_layout import ecoflow_dir  # info: from apps . core . services . data_layout

    roots = (  # info: set roots
        config.PUBLIC_MEDIA / "images" / "ecoflow",  # info: config . PUBLIC_MEDIA / "images" / "ecoflow" ,
        ecoflow_dir() / "screens",  # info: call ecoflow_dir
    )  # info: )
    found: list[tuple[str, Path]] = []  # info: set found
    for root in roots:  # info: for root in roots :
        if not root.is_dir():  # info: if not root . is_dir ( ) :
            continue  # info: continue
        for p in sorted(root.glob("*.png")) + sorted(root.glob("*.jpg")):  # info: for p in sorted ( root . glob
            found.append((p.stem, p))  # info: found . append ( ( p . stem
            if len(found) >= 2:  # info: if len ( found ) >= 2 :
                return found  # info: return found
    return found  # info: return found


# ====================================================
# SECTION: function _panels
# What it does:  panels.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _panels() -> list[tuple[str, Path]]:  # info: def _panels
    root = Path.home() / ".ollama" / "skills" / "panels-cam" / "store" / "frames"  # info: set root
    if not root.is_dir():  # info: if not root . is_dir ( ) :
        return []  # info: return [ ]
    jpgs = sorted(root.glob("ch*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)  # info: set jpgs
    if not jpgs:  # info: if not jpgs :
        return []  # info: return [ ]
    return [("Rear Shed panels", jpgs[0])]  # info: return [ ( "Rear Shed panels" , jpgs [ 0


# ====================================================
# SECTION: function _pick
# What it does:  pick.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pick(asked: str) -> list[tuple[str, Path]]:  # info: def _pick
    if _PANELS.search(asked or ""):  # info: if _PANELS . search ( asked or ""
        shots = _panels()  # info: set shots
        if shots:  # info: if shots :
            return shots  # info: return shots
    if _PACK.search(asked or ""):  # info: if _PACK . search ( asked or ""
        shots = _pack_screens()  # info: set shots
        return shots  # info: return shots
    if _NHC.search(asked or "") and not _KILAUEA.search(asked or ""):  # info: if _NHC . search ( asked or ""
        return _nhc()  # info: return _nhc ( )
    if _KILAUEA.search(asked or "") or wants_look(asked):  # info: if _KILAUEA . search ( asked or ""
        if _NHC.search(asked or ""):  # info: if _NHC . search ( asked or ""
            return _nhc()[:1] + _usgs(asked)[:1]  # info: return _nhc ( ) [ : 1 ]
        if _PANELS.search(asked or ""):  # info: if _PANELS . search ( asked or ""
            return _panels()[:1] + _usgs(asked)[:1]  # info: return _panels ( ) [ : 1 ]
        return _usgs(asked)  # info: return _usgs ( asked )
    return []  # info: return [ ]


# ====================================================
# SECTION: function notes_sync
# What it does: notes sync.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def notes_sync(asked: str) -> str:  # info: def notes_sync
    if not wants_look(asked):  # info: if not wants_look ( asked ) :
        return ""  # info: return ""
    picks = _pick(asked)  # info: set picks
    if _PACK.search(asked or "") and not picks:  # info: if _PACK . search ( asked or ""
        return "LOOK: no pack screen photo on this disk."  # info: return "LOOK: no pack screen photo on this disk."
    if not picks:  # info: if not picks :
        return "LOOK: no still on hand for that."  # info: return "LOOK: no still on hand for that."
    from apps.core.services import ollama as ollama_svc  # info: from apps . core . services import ollama

    lines = []  # info: set lines
    for title, path in picks[:2]:  # info: for title , path in picks [ :
        prompt = (  # info: set prompt
            f"This is a live still: {title}. "  # info: f" This is a live still: { title } . "
            "Describe only what is visible in four short factual sentences. "  # info: "Describe only what is visible in four short factual sentences. "
            "If a number or name is not on the still, omit it. "  # info: "If a number or name is not on the still, omit it. "
            "If it is dark, cloudy, or a map, say that."  # info: "If it is dark, cloudy, or a map, say that."
        )  # info: )
        cap = ollama_svc.look_sync(prompt, [path], timeout=90)  # info: set cap
        if cap:  # info: if cap :
            lines.append(f"LOOK ({title}): {cap.strip()[:700]}")  # info: lines . append ( f" LOOK ( { title
        else:  # info: else :
            lines.append(f"LOOK ({title}): still saved, looker quiet.")  # info: lines . append ( f" LOOK ( { title
    return "\n".join(lines)  # info: return "\n" . join ( lines )


# ====================================================
# SECTION: function notes
# What it does: notes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
async def notes(asked: str) -> str:  # info: async def
    import asyncio  # info: import asyncio

    text = await asyncio.to_thread(notes_sync, asked or "")  # info: set text
    if text and "LOOK (" in text and "looker quiet" not in text:  # info: if text and "LOOK (" in text and "looker quiet"
        try:  # info: try :
            from apps.core.services import voice_events  # info: from apps . core . services import voice_events

            await voice_events.announce("phrase_looker", cooldown_s=120)  # info: await voice_events . announce ( "phrase_looker" , cooldown_s
        except Exception as e:  # info: except Exception as e :
            log.debug("looker voice skip: %s", e)  # info: log . debug ( "looker voice skip: %s" , e )
    return text  # info: return text
