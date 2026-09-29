#!/usr/bin/env python3
"""Kīlauea USGS webcam stills + live-stream catalog (G3 port of G1 kilauea/kilauea-cams). Stdlib only.

  python3 kilauea_cams.py [--dry-run] [--keep-dated]

Ported: the G1 DEFAULT_CAMS catalog (USGS V1/V2/V3 Halemaʻumaʻu cams, YouTube live ids, still URLs) and the
USGS still fallback. Each run downloads the three official still images (conditional GET: ETag/Last-Modified,
unchanged -> 304, nothing rewritten) to Database Geology/Volcanoes/Cams/<cam>-last.jpg and writes
Geology/Volcanoes/Cams/cams-last.json (catalog + per-cam http status, bytes, sha256, fetched_at).
--keep-dated also copies a changed still to Cams/Daily/<YYYYMMDD>/<cam>-<HHMMSS>.jpg (off by default: ~0.2–0.3 MB each).
NOT ported: OBS browser-source push (no OBS in G3) and YouTube watch-page scraping for new live ids (G1
_resolve_youtube) — catalog ids are the G1 offline defaults. Images are git-ignored in the Database (*.jpg).
Light: 10 s timeout per request, no retries. Schedule >= 10 min (jobs.py, gated RR_KILAUEA_CAMS=1).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
CAMS = DB / "Geology" / "Volcanoes" / "Cams"
UA = "RootRecord-Pacific-Geology/1.0 (+https://rootrecord.cloud)"
TIMEOUT = min(10.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "10")))

# G1 kilauea_cams.DEFAULT_CAMS (same offline defaults as the Kīlauea Alerts app), OBS scene/input names dropped.
DEFAULT_CAMS = [
    {"id": "usgs_v1", "file": "v1cam", "title": "[V1cam] West Halemaʻumaʻu", "youtube_video_id": "HggWKlZv9yk",
     "still": "https://volcanoes.usgs.gov/observatories/hvo/cams/V1cam/images/M.jpg"},
    {"id": "usgs_v2", "file": "v2cam", "title": "[V2cam] North Halemaʻumaʻu", "youtube_video_id": "Tz5tPqRRv1Y",
     "still": "https://volcanoes.usgs.gov/observatories/hvo/cams/V2cam/images/M.jpg"},
    {"id": "usgs_v3", "file": "v3cam", "title": "[V3cam] Halemaʻumaʻu lava lake", "youtube_video_id": "gXKuUyKt8mc",
     "still": "https://volcanoes.usgs.gov/observatories/hvo/cams/V3cam/images/M.jpg"},
]


def jload(p: Path) -> dict:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def fetch_still(cam: dict, prev: dict, t: datetime, dry: bool, keep: bool) -> dict:
    hdr = {"User-Agent": UA, "Accept": "image/jpeg,image/*;q=0.8"}
    dest = CAMS / f"{cam['file']}-last.jpg"
    if dest.is_file():
        if prev.get("etag"):
            hdr["If-None-Match"] = prev["etag"]
        if prev.get("last_modified"):
            hdr["If-Modified-Since"] = prev["last_modified"]
    out = {"checked_at": t.isoformat()}
    try:
        with urlopen(Request(cam["still"], headers=hdr), timeout=TIMEOUT) as r:
            body = r.read()
            ctype = r.headers.get("Content-Type", "")
            etag, lm = r.headers.get("ETag"), r.headers.get("Last-Modified")
        if not ctype.startswith("image/") or len(body) < 1000:
            return dict(prev, **out, ok=False, http=200, error=f"not an image ({ctype}, {len(body)} B)")
        sha = hashlib.sha256(body).hexdigest()
        changed = sha != prev.get("sha256")
        if not dry and changed:
            CAMS.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_name(dest.name + ".tmp")
            tmp.write_bytes(body)
            os.replace(tmp, dest)
            if keep:
                day = CAMS / "Daily" / f"{t:%Y%m%d}"
                day.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(dest, day / f"{cam['file']}-{t:%H%M%S}.jpg")
        return dict(out, ok=True, http=200, changed=changed, bytes=len(body), sha256=sha, etag=etag,
                    last_modified=lm, fetched_at=t.isoformat() if changed else prev.get("fetched_at"), file=str(dest.name))
    except HTTPError as e:
        if e.code == 304:
            return dict(prev, **out, ok=True, http=304, changed=False)
        return dict(prev, **out, ok=False, http=e.code, error=f"HTTPError {e.code}")
    except Exception as e:  # noqa: BLE001
        return dict(prev, **out, ok=False, error=f"{type(e).__name__}: {e}"[:300])


def main(argv: list[str]) -> int:
    dry, keep = "--dry-run" in argv, "--keep-dated" in argv
    t = datetime.now(HST).replace(microsecond=0)
    last = jload(CAMS / "cams-last.json")
    prev_by = {c.get("id"): c.get("still_status") or {} for c in last.get("cams") or []}
    cams = []
    for cam in DEFAULT_CAMS:
        st = fetch_still(cam, prev_by.get(cam["id"], {}), t, dry, keep)
        vid = cam["youtube_video_id"]
        cams.append({"id": cam["id"], "title": cam["title"], "still": cam["still"], "youtube_video_id": vid,
                     "watch_url": f"https://www.youtube.com/watch?v={vid}",
                     "embed_url": f"https://www.youtube.com/embed/{vid}?autoplay=1&mute=1&playsinline=1&rel=0&modestbranding=1",
                     "still_status": st})
    doc = {"at": t.isoformat(), "source": "USGS HVO webcams (G1 kilauea-cams DEFAULT_CAMS)", "catalog": "g1-offline-defaults",
           "cams": cams}
    if not dry:
        CAMS.mkdir(parents=True, exist_ok=True)
        tmp = CAMS / "cams-last.json.tmp"
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, CAMS / "cams-last.json")
    ok = all(c["still_status"].get("ok") for c in cams)
    print(json.dumps({"ok": ok, "at": t.isoformat(), "dry_run": dry,
                      "cams": {c["id"]: {k: c["still_status"].get(k) for k in ("ok", "http", "changed", "bytes", "error")}
                               for c in cams}}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
