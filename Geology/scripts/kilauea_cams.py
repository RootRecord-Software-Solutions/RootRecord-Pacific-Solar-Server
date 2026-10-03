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
"""Pull USGS HVO Kīlauea stills into Database Cams (Pacific report-side bank).

  python3 kilauea_cams.py

Writes Geology/Volcanoes/Hawaii/Cams/v{1,2,3}cam_current.jpg and cams_current.json.
Same catalog URLs as ML2 collectors/geology_kilauea_cams.py. No vision, no send.
ML2 may still stream the same paths when RR_LOCAL_DATA_POLL=0; this keeps the bank
fresh for kilauea_look / voice_kilauea_image_check on Pacific.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
CAMS = DB / "Geology" / "Volcanoes" / "Hawaii" / "Cams"  # info: set CAMS
OUT = CAMS / "cams_current.json"  # info: set OUT
UA = "RootRecord-Pacific-Geology/1.0 (+https://rootrecord.cloud; Kilauea cams)"  # info: set UA
TIMEOUT = min(15.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "15")))  # info: set TIMEOUT

# ====================================================
# SECTION: CAM_STILLS
# What it does: USGS HVO still catalog (V3 lava lake first). Same URLs as ML2 geology_kilauea_cams.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
CAM_STILLS = (  # info: set CAM_STILLS
    ("v3cam", "usgs_v3", "V3 Halemaʻumaʻu lava lake", "https://volcanoes.usgs.gov/observatories/hvo/cams/V3cam/images/M.jpg"),  # info: v3
    ("v1cam", "usgs_v1", "V1 West Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V1cam/images/M.jpg"),  # info: v1
    ("v2cam", "usgs_v2", "V2 North Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V2cam/images/M.jpg"),  # info: v2
)  # info: )


# ====================================================
# SECTION: function now_hst
# What it does: Current Hawaii wall time without microseconds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> datetime:  # info: def now_hst
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) . replace ( microsecond = 0 )


# ====================================================
# SECTION: function now_utc_z
# What it does: UTC Z timestamp string for fetched_at.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_utc_z() -> str:  # info: def now_utc_z
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")  # info: return utc Z


# ====================================================
# SECTION: function fetch_one
# What it does: GET one USGS still into Cams/<stem>_current.jpg. Returns a cite row; does not invent pixels.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_one(stem: str, cam_id: str, title: str, url: str, checked_at: datetime) -> dict:  # info: def fetch_one
    dest = CAMS / f"{stem}_current.jpg"  # info: set dest
    path_rel = f"Geology/Volcanoes/Hawaii/Cams/{stem}_current.jpg"  # info: set path_rel
    row = {  # info: set row
        "id": cam_id,  # info: id
        "file": stem,  # info: file
        "label": title,  # info: label
        "title": title,  # info: title
        "still": url,  # info: still
        "source_url": url,  # info: source_url
        "path_rel": path_rel,  # info: path_rel
        "checked_at": checked_at.isoformat(),  # info: checked_at
        "ok": False,  # info: ok
        "viewed": False,  # info: viewed
        "bytes": 0,  # info: bytes
        "sha256": "",  # info: sha256
        "fetched_at": "",  # info: fetched_at
        "error": "",  # info: error
    }  # info: }
    hdr = {"User-Agent": UA, "Accept": "image/jpeg,image/*;q=0.8"}  # info: set hdr
    try:  # info: try
        req = urllib.request.Request(url, headers=hdr)  # info: set req
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:  # info: with urlopen
            body = response.read()  # info: set body
            ctype = response.headers.get("Content-Type", "")  # info: set ctype
            etag = response.headers.get("ETag")  # info: set etag
            lm = response.headers.get("Last-Modified")  # info: set lm
        if not ctype.startswith("image/") or len(body) < 1000:  # info: if not a real still
            row["error"] = f"not an image ({ctype}, {len(body)} B)"  # info: set error
            return row  # info: return row
        CAMS.mkdir(parents=True, exist_ok=True)  # info: CAMS . mkdir
        tmp = dest.with_name(dest.name + ".tmp")  # info: set tmp
        tmp.write_bytes(body)  # info: tmp . write_bytes ( body )
        os.replace(tmp, dest)  # info: os . replace ( tmp , dest )
        sha = hashlib.sha256(body).hexdigest()  # info: set sha
        fetched = now_utc_z()  # info: set fetched
        row.update(  # info: row . update
            {  # info: {
                "ok": True,  # info: ok
                "viewed": True,  # info: viewed
                "bytes": len(body),  # info: bytes
                "sha256": sha,  # info: sha256
                "fetched_at": fetched,  # info: fetched_at
                "etag": etag,  # info: etag
                "last_modified": lm,  # info: last_modified
                "error": "",  # info: error
            }  # info: }
        )  # info: )
        return row  # info: return row
    except urllib.error.HTTPError as exc:  # info: except HTTPError
        row["error"] = f"HTTPError {exc.code}"  # info: set error
        return row  # info: return row
    except Exception as exc:  # noqa: BLE001
        row["error"] = f"{type(exc).__name__}: {exc}"[:300]  # info: set error
        return row  # info: return row


# ====================================================
# SECTION: function pull_all
# What it does: Fetch V1/V2/V3 stills, write cams_current.json, return the document. No vision.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pull_all() -> dict:  # info: def pull_all
    t = now_hst()  # info: set t
    rows = [fetch_one(stem, cam_id, title, url, t) for stem, cam_id, title, url in CAM_STILLS]  # info: set rows
    ok_n = sum(1 for r in rows if r.get("ok"))  # info: set ok_n
    doc = {  # info: set doc
        "ok": ok_n == len(CAM_STILLS),  # info: ok
        "at": t.isoformat(),  # info: at
        "checked_at": t.isoformat(),  # info: checked_at
        "collected_at": now_utc_z(),  # info: collected_at
        "source": "USGS HVO webcams (Pacific kilauea_cams)",  # info: source
        "catalog": "g1-offline-defaults",  # info: catalog
        "collector": "pacific.kilauea_cams",  # info: collector
        "photo_viewed": ok_n > 0,  # info: photo_viewed
        "photos_ok": ok_n,  # info: photos_ok
        "photos_total": len(CAM_STILLS),  # info: photos_total
        "cams": rows,  # info: cams
    }  # info: }
    CAMS.mkdir(parents=True, exist_ok=True)  # info: CAMS . mkdir
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # info: OUT . write_text
    return doc  # info: return doc


# ====================================================
# SECTION: function main
# What it does: Pull all stills and print one JSON summary line. Exit 0 only when all three ok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    doc = pull_all()  # info: set doc
    summary = {  # info: set summary
        "ok": doc.get("ok"),  # info: ok
        "photo_viewed": doc.get("photo_viewed"),  # info: photo_viewed
        "photos_ok": doc.get("photos_ok"),  # info: photos_ok
        "photos_total": doc.get("photos_total"),  # info: photos_total
        "at": doc.get("at"),  # info: at
        "collector": doc.get("collector"),  # info: collector
        "cams": {r["file"]: {"ok": r.get("ok"), "bytes": r.get("bytes"), "error": r.get("error") or None} for r in doc.get("cams") or []},  # info: cams
    }  # info: }
    print(json.dumps(summary, ensure_ascii=False))  # info: call print
    return 0 if doc.get("ok") else 1  # info: return 0 if doc . get ( "ok" ) else 1


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
