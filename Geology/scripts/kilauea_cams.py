# ==============================================================================
# FILE: Geology/scripts/kilauea_cams.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Kīlauea USGS webcam stills + live-stream catalog (G3 port of G1 kilauea/kilauea-cams). Stdlib only.

  python3 kilauea_cams.py [--dry-run] [--keep-dated]

Ported: the G1 DEFAULT_CAMS catalog (USGS V1/V2/V3 Halemaʻumaʻu cams, YouTube live ids, still URLs) and the
USGS still fallback. Each run downloads the three official still images (conditional GET: ETag/Last-Modified,
unchanged -> 304, nothing rewritten) to Database Geology/Volcanoes/Hawaii/Cams/<cam>-last.jpg and writes
Geology/Volcanoes/Hawaii/Cams/cams-last.json (catalog + per-cam http status, bytes, sha256, fetched_at).
--keep-dated also copies a changed still to Cams/Daily/<YYYYMMDD>/<cam>-<HHMMSS>.jpg (off by default: ~0.2–0.3 MB each).
NOT ported: OBS browser-source push (no OBS in G3) and YouTube watch-page scraping for new live ids (G1
_resolve_youtube) — catalog ids are the G1 offline defaults. Images are git-ignored in the Database (*.jpg).
Light: 10 s timeout per request, no retries. Schedule >= 10 min (jobs.py, gated RR_KILAUEA_CAMS=1).
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import shutil  # info: import shutil
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from urllib.error import HTTPError  # info: from urllib . error import HTTPError
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
CAMS = DB / "Geology" / "Volcanoes" / "Hawaii" / "Cams"  # info: Hawaiʻi HVO cams bank
UA = "RootRecord-Pacific-Geology/1.0 (+https://rootrecord.cloud)"  # info: set UA
TIMEOUT = min(10.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "10")))  # info: set TIMEOUT

# G1 kilauea_cams.DEFAULT_CAMS (same offline defaults as the Kīlauea Alerts app), OBS scene/input names dropped.
# ====================================================
# SECTION: DEFAULT_CAMS
# What it does: Set DEFAULT_CAMS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
DEFAULT_CAMS = [  # info: set DEFAULT_CAMS
    {"id": "usgs_v1", "file": "v1cam", "title": "[V1cam] West Halemaʻumaʻu", "youtube_video_id": "HggWKlZv9yk",  # info: { "id" : "usgs_v1" , "file" : "v1cam"
     "still": "https://volcanoes.usgs.gov/observatories/hvo/cams/V1cam/images/M.jpg"},  # info: "still" : "https://volcanoes.usgs.gov/observatories/hvo/cams/V1cam/images/M.jpg" } ,
    {"id": "usgs_v2", "file": "v2cam", "title": "[V2cam] North Halemaʻumaʻu", "youtube_video_id": "Tz5tPqRRv1Y",  # info: { "id" : "usgs_v2" , "file" : "v2cam"
     "still": "https://volcanoes.usgs.gov/observatories/hvo/cams/V2cam/images/M.jpg"},  # info: "still" : "https://volcanoes.usgs.gov/observatories/hvo/cams/V2cam/images/M.jpg" } ,
    {"id": "usgs_v3", "file": "v3cam", "title": "[V3cam] Halemaʻumaʻu lava lake", "youtube_video_id": "gXKuUyKt8mc",  # info: { "id" : "usgs_v3" , "file" : "v3cam"
     "still": "https://volcanoes.usgs.gov/observatories/hvo/cams/V3cam/images/M.jpg"},  # info: "still" : "https://volcanoes.usgs.gov/observatories/hvo/cams/V3cam/images/M.jpg" } ,
]  # info: ]


# ====================================================
# SECTION: function jload
# What it does: jload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def jload(p: Path) -> dict:  # info: def jload
    try:  # info: try :
        d = json.loads(p.read_text(encoding="utf-8"))  # info: set d
        return d if isinstance(d, dict) else {}  # info: return d if isinstance ( d , dict
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }


# ====================================================
# SECTION: function fetch_still
# What it does: fetch still.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_still(cam: dict, prev: dict, t: datetime, dry: bool, keep: bool) -> dict:  # info: def fetch_still
    hdr = {"User-Agent": UA, "Accept": "image/jpeg,image/*;q=0.8"}  # info: set hdr
    dest = CAMS / f"{cam['file']}-last.jpg"  # info: set dest
    if dest.is_file():  # info: if dest . is_file ( ) :
        if prev.get("etag"):  # info: if prev . get ( "etag" ) :
            hdr["If-None-Match"] = prev["etag"]  # info: hdr [ "If-None-Match" ] = prev [ "etag"
        if prev.get("last_modified"):  # info: if prev . get ( "last_modified" ) :
            hdr["If-Modified-Since"] = prev["last_modified"]  # info: hdr [ "If-Modified-Since" ] = prev [ "last_modified"
    out = {"checked_at": t.isoformat()}  # info: set out
    try:  # info: try :
        with urlopen(Request(cam["still"], headers=hdr), timeout=TIMEOUT) as r:  # info: with urlopen ( Request ( cam [ "still"
            body = r.read()  # info: set body
            ctype = r.headers.get("Content-Type", "")  # info: set ctype
            etag, lm = r.headers.get("ETag"), r.headers.get("Last-Modified")  # info: etag , lm = r . headers .
        if not ctype.startswith("image/") or len(body) < 1000:  # info: if not ctype . startswith ( "image/" )
            return dict(prev, **out, ok=False, http=200, error=f"not an image ({ctype}, {len(body)} B)")  # info: return dict ( prev , ** out ,
        sha = hashlib.sha256(body).hexdigest()  # info: set sha
        changed = sha != prev.get("sha256")  # info: set changed
        if not dry and changed:  # info: if not dry and changed :
            CAMS.mkdir(parents=True, exist_ok=True)  # info: CAMS . mkdir ( parents = True ,
            tmp = dest.with_name(dest.name + ".tmp")  # info: set tmp
            tmp.write_bytes(body)  # info: tmp . write_bytes ( body )
            os.replace(tmp, dest)  # info: os . replace ( tmp , dest )
            if keep:  # info: if keep :
                day = CAMS / "Daily" / f"{t:%Y%m%d}"  # info: set day
                day.mkdir(parents=True, exist_ok=True)  # info: day . mkdir ( parents = True ,
                shutil.copyfile(dest, day / f"{cam['file']}-{t:%H%M%S}.jpg")  # info: shutil . copyfile ( dest , day /
        return dict(out, ok=True, http=200, changed=changed, bytes=len(body), sha256=sha, etag=etag,  # info: return dict ( out , ok = True
                    last_modified=lm, fetched_at=t.isoformat() if changed else prev.get("fetched_at"), file=str(dest.name))  # info: set last_modified
    except HTTPError as e:  # info: except HTTPError as e :
        if e.code == 304:  # info: if e . code == 304 :
            return dict(prev, **out, ok=True, http=304, changed=False)  # info: return dict ( prev , ** out ,
        return dict(prev, **out, ok=False, http=e.code, error=f"HTTPError {e.code}")  # info: return dict ( prev , ** out ,
    except Exception as e:  # noqa: BLE001
        return dict(prev, **out, ok=False, error=f"{type(e).__name__}: {e}"[:300])  # info: return dict ( prev , ** out ,


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    dry, keep = "--dry-run" in argv, "--keep-dated" in argv  # info: dry , keep = "--dry-run" in argv ,
    t = datetime.now(HST).replace(microsecond=0)  # info: set t
    last = jload(CAMS / "cams-last.json")  # info: set last
    prev_by = {c.get("id"): c.get("still_status") or {} for c in last.get("cams") or []}  # info: set prev_by
    cams = []  # info: set cams
    for cam in DEFAULT_CAMS:  # info: for cam in DEFAULT_CAMS :
        st = fetch_still(cam, prev_by.get(cam["id"], {}), t, dry, keep)  # info: set st
        vid = cam["youtube_video_id"]  # info: set vid
        cams.append({"id": cam["id"], "title": cam["title"], "still": cam["still"], "youtube_video_id": vid,  # info: cams . append ( { "id" : cam
                     "watch_url": f"https://www.youtube.com/watch?v={vid}",  # info: "watch_url" : f" https://www.youtube.com/watch?v= { vid } "
                     "embed_url": f"https://www.youtube.com/embed/{vid}?autoplay=1&mute=1&playsinline=1&rel=0&modestbranding=1",  # info: "embed_url" : f" https://www.youtube.com/embed/ { vid } ?autoplay=1&mute=1&playsinline=1&rel=0&modestbranding=
                     "still_status": st})  # info: "still_status" : st } )
    doc = {"at": t.isoformat(), "source": "USGS HVO webcams (G1 kilauea-cams DEFAULT_CAMS)", "catalog": "g1-offline-defaults",  # info: set doc
           "cams": cams}  # info: "cams" : cams }
    if not dry:  # info: if not dry :
        CAMS.mkdir(parents=True, exist_ok=True)  # info: CAMS . mkdir ( parents = True ,
        tmp = CAMS / "cams-last.json.tmp"  # info: set tmp
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
        os.replace(tmp, CAMS / "cams-last.json")  # info: os . replace ( tmp , CAMS /
    ok = all(c["still_status"].get("ok") for c in cams)  # info: set ok
    print(json.dumps({"ok": ok, "at": t.isoformat(), "dry_run": dry,  # info: call print
                      "cams": {c["id"]: {k: c["still_status"].get(k) for k in ("ok", "http", "changed", "bytes", "error")}  # info: "cams" : { c [ "id" ] :
                               for c in cams}}, ensure_ascii=False))  # info: for c in cams } } , ensure_ascii
    return 0 if ok else 1  # info: return 0 if ok else 1


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv[1:]))  # info: raise SystemExit ( main ( sys . argv
