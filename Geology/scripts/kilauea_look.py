# ==============================================================================
# FILE: Geology/scripts/kilauea_look.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Kīlauea observation image look. Same Gemma/Ollama stack as Security/Cameras/panel_look.

  python3 kilauea_look.py            reuse a fresh look, or look once
  python3 kilauea_look.py --force    look again even if this slot already has a reading
  python3 kilauea_look.py --ensure-ref  download the USGS fountain reference if missing

Prefers Database Geology/Volcanoes/Cams/{v1,v2,v3}cam-last.jpg from geology_kilauea_cams.
When the preferred still is older than RR_KILAUEA_LOOK_STALE_MIN (default 12), fetches one
live USGS HVO still (V3 lava lake first). Writes Geology/Volcanoes/Cams/kilauea-look-last.json.
Optional public-domain USGS fountain reference under Cams/references/ for compare.
Report-side only — not a LOCAL_DATA_POLL collector. Soft-gated via voice_kilauea_image_check.
"""
from __future__ import annotations  # info: from __future__ import annotations

import base64  # info: import base64
import fcntl  # info: import fcntl
import json  # info: import json
import os  # info: import os
import re  # info: import re
import sys  # info: import sys
import urllib.error  # info: import urllib.error
import urllib.request  # info: import urllib.request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
CAMS = DB / "Geology" / "Volcanoes" / "Cams"  # info: set CAMS
OUT = CAMS / "kilauea-look-last.json"  # info: set OUT
REF_DIR = CAMS / "references"  # info: set REF_DIR
REF_PATH = REF_DIR / "lava-fountain-ref.jpg"  # info: set REF_PATH
LOCK = Path("/tmp/kilauea-look.lock")  # info: set LOCK
MODEL = os.environ.get("RR_KILAUEA_LOOK_MODEL", os.environ.get("RR_PANEL_LOOK_MODEL", "gemma4:e4b"))  # info: set MODEL
OLLAMA = os.environ.get("RR_OLLAMA_URL", "http://127.0.0.1:11434/api/chat")  # info: set OLLAMA
STALE_MIN = int(os.environ.get("RR_KILAUEA_LOOK_STALE_MIN", "12"))  # info: set STALE_MIN
SLOT_MIN = int(os.environ.get("RR_KILAUEA_LOOK_SLOT_MIN", "15"))  # info: set SLOT_MIN
UA = "RootRecord-Pacific-Geology/1.0 (+https://rootrecord.cloud)"  # info: set UA
TIMEOUT = min(15.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "15")))  # info: set TIMEOUT

# USGS HVO stills — same catalog as Geology/scripts/kilauea_cams.py DEFAULT_CAMS.
# ====================================================
# SECTION: CAM_STILLS
# What it does: Preferred order of USGS HVO stills for one observation look (V3 lava lake first).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
CAM_STILLS = (  # info: set CAM_STILLS
    ("v3cam", "V3 Halemaʻumaʻu lava lake", "https://volcanoes.usgs.gov/observatories/hvo/cams/V3cam/images/M.jpg"),  # info: v3
    ("v1cam", "V1 West Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V1cam/images/M.jpg"),  # info: v1
    ("v2cam", "V2 North Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V2cam/images/M.jpg"),  # info: v2
)  # info: )

# Public-domain USGS photo (episode 54 north vent fountain, 2026-08-25, C. Gansecki).
REF_URL = os.environ.get(  # info: set REF_URL
    "RR_KILAUEA_FOUNTAIN_REF_URL",  # info: env override
    "https://d9-wret.s3.us-west-2.amazonaws.com/assets/palladium/production/s3fs-public/media/images/Image_-_2026-08-25T122402.709.jpg",  # info: USGS S3 original
)  # info: )

ACTIVITY = {  # info: set ACTIVITY
    "quiet": "quiet crater with no visible lava",  # info: quiet
    "glow": "glow at the vent",  # info: glow
    "incandescent": "incandescent lava visible",  # info: incandescent
    "fountaining": "lava fountaining",  # info: fountaining
    "plume": "a gas or ash plume",  # info: plume
    "unclear": "conditions the camera could not settle",  # info: unclear
}  # info: }

PROMPT = (  # info: set PROMPT
    "This is an official USGS Hawaiian Volcano Observatory webcam still of Kīlauea / Halemaʻumaʻu. "  # info: intro
    "Reply with one JSON object only, no other words. "  # info: json only
    'Keys: "activity", "fountaining", "visible". '  # info: keys
    "activity is one of quiet, glow, incandescent, fountaining, plume, unclear. "  # info: activity enum
    "Use fountaining only when bright vertical lava jets or spray rise clearly above the vent or crater floor. "  # info: fountain rule
    "Use glow for dim red light without jets. Use incandescent for bright lava surfaces without rising jets. "  # info: glow vs lava
    "Use plume for a gas or ash column without clear lava jets. Use quiet when the crater looks dark or inactive. "  # info: plume quiet
    "Use unclear when the frame is too dark, fogged, or blocked to judge. "  # info: unclear
    "fountaining is true only when activity is fountaining, otherwise false. "  # info: bool
    'visible is one short factual phrase of what is on the still, or "" when unclear. Do not invent numbers or times.'  # info: visible
)  # info: )

COMPARE_PROMPT = (  # info: set COMPARE_PROMPT
    "Image 1 is a live USGS HVO webcam still of Kīlauea. "  # info: img1
    "Image 2 is a public-domain USGS photo of known Kīlauea lava fountaining for comparison only. "  # info: img2
    "Reply with one JSON object only, no other words. "  # info: json
    'Keys: "activity", "fountaining", "visible". '  # info: keys
    "activity is one of quiet, glow, incandescent, fountaining, plume, unclear for Image 1 only. "  # info: activity
    "fountaining is true only when Image 1 shows bright vertical lava jets or spray like Image 2. "  # info: compare
    "Do not copy Image 2 into the answer. visible describes Image 1 only in one short factual phrase."  # info: visible
)  # info: )


# ====================================================
# SECTION: function jload
# What it does: Load a JSON object from disk, or {}.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def jload(path: Path) -> dict:  # info: def jload
    try:  # info: try
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
        return data if isinstance(data, dict) else {}  # info: return dict
    except (OSError, ValueError):  # info: except
        return {}  # info: return empty


# ====================================================
# SECTION: function slot_key
# What it does: Fifteen-minute slot label in Hawaii time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def slot_key(t: datetime) -> str:  # info: def slot_key
    minute = (t.minute // SLOT_MIN) * SLOT_MIN  # info: set minute
    return t.strftime("%Y-%m-%dT%H:") + f"{minute:02d}"  # info: return slot


# ====================================================
# SECTION: function ensure_reference
# What it does: Download the USGS public-domain fountain reference once when missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_reference() -> Path | None:  # info: def ensure_reference
    if REF_PATH.is_file() and REF_PATH.stat().st_size > 8000:  # info: if present
        return REF_PATH  # info: return path
    try:  # info: try
        req = urllib.request.Request(REF_URL, headers={"User-Agent": UA, "Accept": "image/jpeg,image/*;q=0.8"})  # info: set req
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:  # info: with urlopen
            body = response.read()  # info: set body
            ctype = response.headers.get("Content-Type", "")  # info: set ctype
        if not ctype.startswith("image/") or len(body) < 8000:  # info: if not image
            return REF_PATH if REF_PATH.is_file() else None  # info: return existing
        REF_DIR.mkdir(parents=True, exist_ok=True)  # info: mkdir
        tmp = REF_PATH.with_suffix(".tmp")  # info: set tmp
        tmp.write_bytes(body)  # info: write
        os.replace(tmp, REF_PATH)  # info: replace
        meta = REF_DIR / "lava-fountain-ref.json"  # info: set meta
        meta.write_text(json.dumps({  # info: write meta
            "source": "USGS public domain",  # info: source
            "credit": "USGS photo by C. Gansecki, episode 54 north vent fountain, 2026-08-25",  # info: credit
            "url": REF_URL,  # info: url
            "page": "https://www.usgs.gov/media/images/august-25-2026-north-vent-episode-54-lava-fountain-kilauea-summit",  # info: page
            "bytes": len(body),  # info: bytes
        }, indent=2) + "\n", encoding="utf-8")  # info: dump
        return REF_PATH  # info: return path
    except Exception:  # noqa: BLE001
        return REF_PATH if REF_PATH.is_file() else None  # info: return existing


# ====================================================
# SECTION: function fetch_still
# What it does: Conditional GET one USGS still into Cams/<file>-last.jpg.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_still(file_stem: str, url: str) -> Path | None:  # info: def fetch_still
    dest = CAMS / f"{file_stem}-last.jpg"  # info: set dest
    hdr = {"User-Agent": UA, "Accept": "image/jpeg,image/*;q=0.8"}  # info: set hdr
    prev = {}  # info: set prev
    for cam in (jload(CAMS / "cams-last.json").get("cams") or []):  # info: for cam
        if isinstance(cam, dict) and str(cam.get("still") or "") == url:  # info: if match
            prev = cam.get("still_status") if isinstance(cam.get("still_status"), dict) else {}  # info: set prev
            break  # info: break
    if dest.is_file():  # info: if dest exists
        if prev.get("etag"):  # info: if etag
            hdr["If-None-Match"] = str(prev["etag"])  # info: set if-none-match
        if prev.get("last_modified"):  # info: if last-modified
            hdr["If-Modified-Since"] = str(prev["last_modified"])  # info: set if-modified-since
    try:  # info: try
        req = urllib.request.Request(url, headers=hdr)  # info: set req
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:  # info: with urlopen
            body = response.read()  # info: set body
            ctype = response.headers.get("Content-Type", "")  # info: set ctype
        if not ctype.startswith("image/") or len(body) < 1000:  # info: if not image
            return dest if dest.is_file() else None  # info: return existing
        CAMS.mkdir(parents=True, exist_ok=True)  # info: mkdir
        tmp = dest.with_name(dest.name + ".tmp")  # info: set tmp
        tmp.write_bytes(body)  # info: write
        os.replace(tmp, dest)  # info: replace
        return dest  # info: return dest
    except urllib.error.HTTPError as exc:  # info: except HTTPError
        if exc.code == 304 and dest.is_file():  # info: if 304
            return dest  # info: return dest
        return dest if dest.is_file() else None  # info: return existing
    except Exception:  # noqa: BLE001
        return dest if dest.is_file() else None  # info: return existing


# ====================================================
# SECTION: function pick_still
# What it does: Prefer a fresh local Cams still; otherwise pull one live USGS frame.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pick_still(t: datetime, force_fetch: bool = False) -> tuple[Path | None, str, str, bool]:  # info: def pick_still
    """Return path, cam file stem, title, and whether a live fetch ran."""  # info: docstring
    best: Path | None = None  # info: set best
    best_meta = ("", "")  # info: set best_meta
    best_age = None  # info: set best_age
    for stem, title, _url in CAM_STILLS:  # info: for cam
        path = CAMS / f"{stem}-last.jpg"  # info: set path
        if not path.is_file():  # info: if missing
            continue  # info: continue
        age = max(0.0, (t.timestamp() - path.stat().st_mtime) / 60.0)  # info: set age
        if best is None or age < (best_age if best_age is not None else 1e9):  # info: if better
            best, best_meta, best_age = path, (stem, title), age  # info: set best
    if best is not None and best_age is not None and best_age <= STALE_MIN and not force_fetch:  # info: if fresh
        return best, best_meta[0], best_meta[1], False  # info: return local
    fetched = False  # info: set fetched
    for stem, title, url in CAM_STILLS:  # info: for cam
        path = fetch_still(stem, url)  # info: set path
        if path and path.is_file():  # info: if ok
            fetched = True  # info: set fetched
            return path, stem, title, fetched  # info: return live
    if best is not None:  # info: if stale local
        return best, best_meta[0], best_meta[1], fetched  # info: return stale
    return None, "", "", fetched  # info: return none


# ====================================================
# SECTION: function ask
# What it does: One Gemma vision read of the still (optional fountain reference as image 2).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ask(path: Path, reference: Path | None = None) -> tuple[str, bool, str]:  # info: def ask
    images = [base64.b64encode(path.read_bytes()).decode()]  # info: set images
    prompt = PROMPT  # info: set prompt
    if reference is not None and reference.is_file():  # info: if reference
        images.append(base64.b64encode(reference.read_bytes()).decode())  # info: append ref
        prompt = COMPARE_PROMPT  # info: use compare prompt
    body = json.dumps({  # info: set body
        "model": MODEL,  # info: model
        "stream": False,  # info: stream
        "think": False,  # info: think
        "keep_alive": 0,  # info: keep_alive
        "messages": [{"role": "user", "content": prompt, "images": images}],  # info: messages
        "options": {"temperature": 0},  # info: options
    }).encode()  # info: encode
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})  # info: set req
    with urllib.request.urlopen(req, timeout=180) as response:  # info: with urlopen
        payload = json.load(response)  # info: set payload
    text = str(((payload.get("message") or {}).get("content") or ""))  # info: set text
    match = re.search(r"\{.*\}", text, re.S)  # info: set match
    if not match:  # info: if no json
        return "unclear", False, ""  # info: return unclear
    try:  # info: try
        row = json.loads(match.group(0))  # info: set row
    except ValueError:  # info: except
        return "unclear", False, ""  # info: return unclear
    activity = str(row.get("activity") or "").strip().lower()  # info: set activity
    if activity not in ACTIVITY:  # info: if bad activity
        activity = "unclear"  # info: force unclear
    fountain = bool(row.get("fountaining")) and activity == "fountaining"  # info: set fountain
    if activity == "fountaining":  # info: if fountaining label
        fountain = True  # info: force true
    visible = str(row.get("visible") or "").strip()  # info: set visible
    if len(visible) > 160:  # info: if long
        visible = visible[:157].rstrip() + "..."  # info: trim
    return activity, fountain, visible  # info: return triple


# ====================================================
# SECTION: function sentence_for
# What it does: Spoken observation line from measured activity.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sentence_for(activity: str, fountaining: bool, visible: str, cam_title: str) -> str:  # info: def sentence_for
    label = ACTIVITY.get(activity, ACTIVITY["unclear"])  # info: set label
    cam = cam_title or "USGS HVO webcam"  # info: set cam
    if fountaining or activity == "fountaining":  # info: if fountain
        base = f"Measured finding: lava fountaining is visible on the {cam} still."  # info: set base
    elif activity == "quiet":  # info: elif quiet
        base = f"Measured finding: {label} on the {cam} still."  # info: set base
    elif activity == "unclear":  # info: elif unclear
        base = f"Measured finding: the {cam} still was unclear."  # info: set base
    else:  # info: else
        base = f"Measured finding: {label} on the {cam} still."  # info: set base
    if visible and activity not in {"quiet", "unclear"}:  # info: if visible detail
        return f"{base} Visible: {visible}."  # info: return with visible
    return base  # info: return base


# ====================================================
# SECTION: function load_cache
# What it does: Last look row, or None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_cache() -> dict | None:  # info: def load_cache
    data = jload(OUT)  # info: set data
    return data or None  # info: return


# ====================================================
# SECTION: function store
# What it does: Write the look file atomically.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def store(row: dict) -> None:  # info: def store
    if not row:  # info: if empty
        return  # info: return
    CAMS.mkdir(parents=True, exist_ok=True)  # info: mkdir
    tmp = OUT.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(row, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  # info: write
    os.replace(tmp, OUT)  # info: replace


# ====================================================
# SECTION: function reuse_slot
# What it does: True when this fifteen-minute slot already has a usable look.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def reuse_slot(cached: dict | None, slot: str, force: bool) -> bool:  # info: def reuse_slot
    if force or not cached:  # info: if force or missing
        return False  # info: return False
    if cached.get("slot") != slot:  # info: if other slot
        return False  # info: return False
    return bool(cached.get("activity") or cached.get("sentence"))  # info: return usable


# ====================================================
# SECTION: function observe
# What it does: One Kīlauea image look for this fifteen-minute slot. Reuses cache unless --force.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def observe(t: datetime, force: bool = False) -> dict:  # info: def observe
    slot = slot_key(t)  # info: set slot
    cached = load_cache()  # info: set cached
    if reuse_slot(cached, slot, force):  # info: if reuse
        return dict(cached)  # info: return cache
    LOCK.parent.mkdir(parents=True, exist_ok=True)  # info: mkdir
    with LOCK.open("a+") as handle:  # info: with lock
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # info: flock
        cached = load_cache()  # info: reload
        if reuse_slot(cached, slot, force):  # info: if reuse after lock
            return dict(cached)  # info: return cache
        path, stem, title, fetched = pick_still(t, force_fetch=force)  # info: pick still
        reference = ensure_reference()  # info: ensure ref
        activity, fountaining, visible = "unclear", False, ""  # info: defaults
        error = ""  # info: set error
        if path is None:  # info: if no still
            error = "no USGS HVO still on file"  # info: set error
        else:  # info: else
            try:  # info: try
                activity, fountaining, visible = ask(path, reference)  # info: ask gemma
            except Exception as exc:  # noqa: BLE001
                error = type(exc).__name__  # info: set error
                activity, fountaining, visible = "unclear", False, ""  # info: clear
        if path is None:  # info: if no still path
            sentence = "Kilauea observation image was checked. No USGS still was available."  # info: missing still
        elif error:  # info: elif vision error
            sentence = f"Kilauea observation image was checked. Vision look failed ({error})."  # info: error line
        else:  # info: else measured
            sentence = "Kilauea observation image was checked. " + sentence_for(activity, fountaining, visible, title)  # info: full line
        row = {  # info: set row
            "slot": slot,  # info: slot
            "at": t.isoformat(timespec="seconds"),  # info: at
            "image": path.name if path else "",  # info: image
            "cam": stem,  # info: cam
            "cam_title": title,  # info: title
            "model": MODEL,  # info: model
            "activity": activity if not error else "",  # info: activity
            "fountaining": bool(fountaining) if not error else False,  # info: fountaining
            "visible": visible if not error else "",  # info: visible
            "fetched_live": fetched,  # info: fetched
            "reference": str(reference.name) if reference else "",  # info: reference
            "error": error,  # info: error
            "sentence": sentence,  # info: sentence
            "source": "USGS HVO webcam still + Gemma look (report-side)",  # info: source
        }  # info: }
        store(row)  # info: store
        return row  # info: return row


# ====================================================
# SECTION: function main
# What it does: Print one observation JSON. --ensure-ref only downloads the fountain reference.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(sys.argv[1:] if argv is None else argv)  # info: set args
    if "--ensure-ref" in args:  # info: if ensure-ref
        path = ensure_reference()  # info: ensure
        print(json.dumps({"ok": path is not None, "reference": str(path) if path else ""}, ensure_ascii=False))  # info: print
        return 0 if path else 1  # info: return
    now = datetime.now(HST).replace(microsecond=0)  # info: set now
    print(json.dumps(observe(now, force="--force" in args), ensure_ascii=False))  # info: print observe
    return 0  # info: return 0


if __name__ == "__main__":  # info: if main
    raise SystemExit(main())  # info: exit
