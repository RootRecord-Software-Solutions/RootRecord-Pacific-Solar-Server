# ==============================================================================
# FILE: Geology/scripts/geology_collect.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Pacific Geology collector — USGS earthquakes (Hawaiʻi + global) and HVO volcano status. Stdlib only.

  python3 geology_collect.py [all|quakes|volcanoes] [--dry-run]

G3 port (2026-09-29, migration-geology) of the fetch halves of:
  G1 earthquakes/earthquake-hourly  (FDSN query, Hawaiʻi bbox M>=1.0, global M>=2.5, new local M>=2 detection)
  G1 kilauea/rr-kilauea             (HVO notice + alert level, headline / erupting / multiplier, quakes <=150 km)
  G0 operations/.../quakes.py + earthquakes/global/poller.py (USGS GeoJSON summary feed, global)
Only the data collection is ported. G1 voice, Telegram/Discord posts, Grok drafts and speaker playback are NOT
here (voice: Media/Voice/scripts/voice_reports.py earthquake_report, gated RR_VOICE_QUAKE; posts: BLOCKED/sign-off).

Sources (public, no key):
  https://earthquake.usgs.gov/fdsnws/event/1/query   (Hawaiʻi bbox, last 24 h, M>=1.0)
  https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson   (global M2.5+, last 24 h)
  https://volcanoes.usgs.gov/hans-public/api/volcano/getMonitoredVolcanoes    (HVO alert level / color code)
  https://volcanoes.usgs.gov/hans-public/api/notice/getNewestOrRecent         (HVO notices + synopsis)

Writes (Database, atomic tmp+replace; a failed source never overwrites its last good file):
  Geology/Earthquakes/{hawaii,global}-last.json      Geology/Earthquakes/Daily/{hawaii,global}-YYYYMMDD.jsonl
  Geology/Volcanoes/{hvo,kilauea,mauna-loa}-last.json Geology/Volcanoes/Daily/hvo-notices-YYYYMMDD.jsonl
  Geology/collector-last.json  (per-source ok / error / ms for the last run)
Daily files are append-only first-seen logs (dedupe by id against today's and yesterday's file); HST dates.
Light: every HTTP call has a timeout <= 10 s (RR_GEOLOGY_TIMEOUT), no retries. Schedule >= 5 min (jobs.py, gated RR_GEOLOGY=1).
"""
from __future__ import annotations  # info: from __future__ import annotations

import gzip  # info: import gzip
import json  # info: import json
import math  # info: import math
import os  # info: import os
import sys  # info: import sys
import time  # info: import time
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import urlencode  # info: from urllib . parse import urlencode
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
GEO = DB / "Geology"  # info: set GEO
EQ, VO = GEO / "Earthquakes", GEO / "Volcanoes"  # info: EQ , VO = GEO / "Earthquakes" ,
UA = "RootRecord-Pacific-Geology/1.0 (+https://rootrecord.cloud)"  # info: set UA
TIMEOUT = min(10.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "10")))  # info: set TIMEOUT

FDSN = "https://earthquake.usgs.gov/fdsnws/event/1/query"  # info: set FDSN
GLOBAL_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"  # info: set GLOBAL_FEED
HANS_MONITORED = "https://volcanoes.usgs.gov/hans-public/api/volcano/getMonitoredVolcanoes"  # info: set HANS_MONITORED
HANS_NEWEST = "https://volcanoes.usgs.gov/hans-public/api/notice/getNewestOrRecent"  # info: set HANS_NEWEST
HAWAII_BBOX = {"minlatitude": 18.5, "maxlatitude": 22.5, "minlongitude": -160.5, "maxlongitude": -154.5}  # G1
HAWAII_M_MIN, LOCAL_M2 = 1.0, 2.0          # G1 _fetch minmagnitude / _LOCAL_M_MIN
KILAUEA_LATLON, KILAUEA_RADIUS_KM = (19.421, -155.287), 150  # G1 rr-kilauea USGS_QUAKE_URL
LOCATIONS_FILE = Path(__file__).resolve().parents[1] / "config" / "global-locations.json"  # G0 old/config/locations (copy)
NEAREST_MAX_KM = 250  # G0 operations/earthquakes/global/poller.py nearest(): no tag beyond 250 km
_LOCATIONS: list[dict] | None = None  # info: set _LOCATIONS
VOLCANOES = {"332010": "kilauea", "332020": "mauna-loa"}      # vnum -> last-file stem
MULTIPLIERS = {"normal": 1.0, "advisory": 2.0, "watch": 2.5, "eruption": 3.0}  # G1 rr-kilauea
MAX_EVENTS_LAST = 100  # info: set MAX_EVENTS_LAST


# ------------------------------------------------------------------ io helpers
# ====================================================
# SECTION: function now_hst
# What it does: now hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> datetime:  # info: def now_hst
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function get_json
# What it does: get json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def get_json(url: str):  # info: def get_json
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"})  # info: set req
    with urlopen(req, timeout=TIMEOUT) as r:  # info: with urlopen ( req , timeout = TIMEOUT
        raw = r.read()  # info: set raw
        if r.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":  # info: if r . headers . get ( "Content-Encoding"
            raw = gzip.decompress(raw)  # info: set raw
    return json.loads(raw.decode("utf-8"))  # info: return json . loads ( raw . decode


# ====================================================
# SECTION: function write_json
# What it does: write json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_json(path: Path, data, dry: bool) -> None:  # info: def write_json
    if dry:  # info: if dry :
        return  # info: return
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_name(path.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function daily_path
# What it does: daily path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def daily_path(folder: Path, stem: str, day: datetime) -> Path:  # info: def daily_path
    return folder / "Daily" / f"{stem}-{day:%Y%m%d}.jsonl"  # info: return folder / "Daily" / f" { stem


# ====================================================
# SECTION: function seen_ids
# What it does: seen ids.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def seen_ids(folder: Path, stem: str, t: datetime, key: str = "id") -> set[str]:  # info: def seen_ids
    out: set[str] = set()  # info: set out
    for day in (t, t - timedelta(days=1)):  # info: for day in ( t , t -
        p = daily_path(folder, stem, day)  # info: set p
        try:  # info: try :
            for ln in p.read_text(encoding="utf-8").splitlines():  # info: for ln in p . read_text ( encoding
                try:  # info: try :
                    out.add(str(json.loads(ln)[key]))  # info: out . add ( str ( json .
                except (ValueError, KeyError, TypeError):  # info: except ( ValueError , KeyError , TypeError )
                    continue  # info: continue
        except OSError:  # info: except OSError :
            continue  # info: continue
    return out  # info: return out


# ====================================================
# SECTION: function append_daily
# What it does: append daily.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def append_daily(folder: Path, stem: str, t: datetime, rows: list[dict], dry: bool) -> None:  # info: def append_daily
    if dry or not rows:  # info: if dry or not rows :
        return  # info: return
    p = daily_path(folder, stem, t)  # info: set p
    p.parent.mkdir(parents=True, exist_ok=True)  # info: p . parent . mkdir ( parents =
    with p.open("a", encoding="utf-8") as f:  # info: with p . open ( "a" , encoding
        for r in rows:  # info: for r in rows :
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")  # info: f . write ( json . dumps (


# ====================================================
# SECTION: function _ms_iso
# What it does:  ms iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ms_iso(ms, tz=timezone.utc) -> str | None:  # info: def _ms_iso
    try:  # info: try :
        return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc).astimezone(tz).isoformat()  # info: return datetime . fromtimestamp ( int ( ms
    except (TypeError, ValueError, OSError):  # info: except ( TypeError , ValueError , OSError )
        return None  # info: return None


# ====================================================
# SECTION: function haversine_km
# What it does: haversine km.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:  # info: def haversine_km
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))  # info: la1 , lo1 , la2 , lo2 =
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2  # info: set h
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))  # info: return 6371.0 * 2 * math . asin


# ====================================================
# SECTION: function nearest_location
# What it does: G0 global poller nearest(): closest registry location (country capitals, US state capitals, staged Hawaii places) within 250 km, else None. Adds country_code / admin1_code / locati
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def nearest_location(lat, lon) -> dict | None:  # info: def nearest_location
    """G0 global poller nearest(): closest registry location (country capitals, US state capitals, staged Hawaii
    places) within 250 km, else None. Adds country_code / admin1_code / location_id like the G0 SQLite columns."""
    global _LOCATIONS  # info: global _LOCATIONS
    if lat is None or lon is None:  # info: if lat is None or lon is None
        return None  # info: return None
    if _LOCATIONS is None:  # info: if _LOCATIONS is None :
        try:  # info: try :
            _LOCATIONS = json.loads(LOCATIONS_FILE.read_text(encoding="utf-8")).get("locations") or []  # info: set _LOCATIONS
        except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
            _LOCATIONS = []  # info: set _LOCATIONS
    best, best_km = None, float("inf")  # info: best , best_km = None , float (
    for x in _LOCATIONS:  # info: for x in _LOCATIONS :
        if x.get("lat") is None or x.get("lon") is None:  # info: if x . get ( "lat" ) is
            continue  # info: continue
        d = haversine_km((float(lat), float(lon)), (float(x["lat"]), float(x["lon"])))  # info: set d
        if d < best_km:  # info: if d < best_km :
            best, best_km = x, d  # info: best , best_km = x , d
    if best is None or best_km > NEAREST_MAX_KM:  # info: if best is None or best_km > NEAREST_MAX_KM
        return None  # info: return None
    return {"location_id": best.get("id"), "name": best.get("name"), "country_code": best.get("country_code"),  # info: return { "location_id" : best . get (
            "admin1_code": best.get("admin1_code") or None, "km": round(best_km, 1)}  # info: "admin1_code" : best . get ( "admin1_code" )


# ------------------------------------------------------------------ earthquakes
# ====================================================
# SECTION: function norm_event
# What it does: norm event.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def norm_event(f: dict) -> dict:  # info: def norm_event
    p, c = f.get("properties") or {}, (f.get("geometry") or {}).get("coordinates") or [None, None, None]  # info: p , c = f . get (
    return {"id": f.get("id"), "mag": p.get("mag"), "mag_type": p.get("magType"), "place": p.get("place") or "",  # info: return { "id" : f . get (
            "time_utc": _ms_iso(p.get("time")), "time_hst": _ms_iso(p.get("time"), HST),  # info: "time_utc" : _ms_iso ( p . get (
            "lon": c[0], "lat": c[1], "depth_km": c[2] if len(c) > 2 else None,  # info: "lon" : c [ 0 ] , "lat"
            "status": p.get("status"), "tsunami": p.get("tsunami"), "type": p.get("type"), "url": p.get("url"),  # info: "status" : p . get ( "status" )
            "nearest": nearest_location(c[1], c[0])}  # info: "nearest" : nearest_location ( c [ 1 ]


# ====================================================
# SECTION: function _mag
# What it does:  mag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _mag(e: dict) -> float | None:  # info: def _mag
    try:  # info: try :
        return float(e.get("mag"))  # info: return float ( e . get ( "mag"
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return None  # info: return None


# ====================================================
# SECTION: function summarize
# What it does: summarize.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def summarize(events: list[dict]) -> dict:  # info: def summarize
    mags = [m for m in (_mag(e) for e in events) if m is not None]  # info: set mags
    big = max(events, key=lambda e: _mag(e) if _mag(e) is not None else -9, default=None)  # info: set big
    return {"count": len(events), "count_m2": sum(m >= 2.0 for m in mags), "count_m25": sum(m >= 2.5 for m in mags),  # info: return { "count" : len ( events )
            "largest": {k: big.get(k) for k in ("id", "mag", "place", "time_hst")} if big and mags else None}  # info: "largest" : { k : big . get


# ====================================================
# SECTION: function collect_quakes
# What it does: collect quakes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def collect_quakes(t: datetime, dry: bool, status: dict) -> None:  # info: def collect_quakes
    hi_ids: set[str] = set()  # info: set hi_ids
    # Hawaiʻi — FDSN query, bbox, last 24 h
    start = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")  # info: set start
    url = f"{FDSN}?" + urlencode({"format": "geojson", "orderby": "time", "starttime": start,  # info: set url
                                   "minmagnitude": HAWAII_M_MIN, **HAWAII_BBOX})  # info: "minmagnitude" : HAWAII_M_MIN , ** HAWAII_BBOX } )
    t0 = time.monotonic()  # info: set t0
    try:  # info: try :
        data = get_json(url)  # info: set data
        ev = [norm_event(f) for f in data.get("features") or []]  # info: set ev
        hi_ids = {e["id"] for e in ev if e.get("id")}  # info: set hi_ids
        prev = seen_ids(EQ, "hawaii", t)  # info: set prev
        new = [dict(e, first_seen_hst=t.isoformat()) for e in ev if e.get("id") and e["id"] not in prev]  # info: set new
        new_m2 = [e["id"] for e in new if (_mag(e) or 0) >= LOCAL_M2]  # info: set new_m2
        near = [e for e in ev if e.get("lat") is not None and e.get("lon") is not None  # info: set near
                and haversine_km(KILAUEA_LATLON, (e["lat"], e["lon"])) <= KILAUEA_RADIUS_KM]  # info: call and
        last = {"at": t.isoformat(), "source": url, "window_h": 24, "min_mag": HAWAII_M_MIN, "bbox": HAWAII_BBOX,  # info: set last
                **summarize(ev), "kilauea_150km_count": len(near), "new_this_run": len(new), "new_local_m2_ids": new_m2,  # info: call **
                "usgs_generated_utc": _ms_iso((data.get("metadata") or {}).get("generated")),  # info: "usgs_generated_utc" : _ms_iso ( ( data . get
                "events": ev[:MAX_EVENTS_LAST]}  # info: "events" : ev [ : MAX_EVENTS_LAST ] }
        write_json(EQ / "hawaii-last.json", last, dry)  # info: call write_json
        append_daily(EQ, "hawaii", t, new, dry)  # info: call append_daily
        status["hawaii"] = {"ok": True, "count": len(ev), "new": len(new), "new_m2": len(new_m2)}  # info: status [ "hawaii" ] = { "ok" :
    except Exception as e:  # noqa: BLE001 — one failed source must not stop the others
        status["hawaii"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}  # info: status [ "hawaii" ] = { "ok" :
    status["hawaii"]["ms"] = int((time.monotonic() - t0) * 1000)  # info: status [ "hawaii" ] [ "ms" ] =

    # Global — USGS summary feed M2.5+ day (Hawaiʻi ids dropped, as in G1 fetch_bundle)
    t0 = time.monotonic()  # info: set t0
    try:  # info: try :
        data = get_json(GLOBAL_FEED)  # info: set data
        ev = [norm_event(f) for f in data.get("features") or []]  # info: set ev
        ev = [e for e in ev if e.get("id") not in hi_ids]  # info: set ev
        ev.sort(key=lambda e: e.get("time_utc") or "", reverse=True)  # info: ev . sort ( key = lambda e
        prev = seen_ids(EQ, "global", t)  # info: set prev
        new = [dict(e, first_seen_hst=t.isoformat()) for e in ev if e.get("id") and e["id"] not in prev]  # info: set new
        last = {"at": t.isoformat(), "source": GLOBAL_FEED, "window_h": 24, "min_mag": 2.5, "excludes": "hawaii-last ids",  # info: set last
                **summarize(ev), "new_this_run": len(new),  # info: call **
                "usgs_generated_utc": _ms_iso((data.get("metadata") or {}).get("generated")),  # info: "usgs_generated_utc" : _ms_iso ( ( data . get
                "events": ev[:MAX_EVENTS_LAST]}  # info: "events" : ev [ : MAX_EVENTS_LAST ] }
        write_json(EQ / "global-last.json", last, dry)  # info: call write_json
        append_daily(EQ, "global", t, new, dry)  # info: call append_daily
        status["global"] = {"ok": True, "count": len(ev), "new": len(new)}  # info: status [ "global" ] = { "ok" :
    except Exception as e:  # noqa: BLE001
        status["global"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}  # info: status [ "global" ] = { "ok" :
    status["global"]["ms"] = int((time.monotonic() - t0) * 1000)  # info: status [ "global" ] [ "ms" ] =


# ------------------------------------------------------------------ volcanoes (HVO)
# ====================================================
# SECTION: function get_multiplier
# What it does: get multiplier.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def get_multiplier(alert_level: str) -> float:  # G1 rr-kilauea, unchanged
    level = (alert_level or "").lower().strip()  # info: set level
    if "erupt" in level or "red" in level or "warning" in level:  # info: if "erupt" in level or "red" in level
        return MULTIPLIERS["eruption"]  # info: return MULTIPLIERS [ "eruption" ]
    if "watch" in level or "orange" in level:  # info: if "watch" in level or "orange" in level
        return MULTIPLIERS["watch"]  # info: return MULTIPLIERS [ "watch" ]
    if "advisory" in level or "yellow" in level:  # info: if "advisory" in level or "yellow" in level
        return MULTIPLIERS["advisory"]  # info: return MULTIPLIERS [ "advisory" ]
    return MULTIPLIERS["normal"]  # info: return MULTIPLIERS [ "normal" ]


# ====================================================
# SECTION: function erupting_from
# What it does: G1 rule: 'is erupting' counts, 'not erupting' / 'paused' does not. None when no synopsis.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def erupting_from(synopsis: str) -> bool | None:  # info: def erupting_from
    """G1 rule: 'is erupting' counts, 'not erupting' / 'paused' does not. None when no synopsis."""  # info: """G1 rule: 'is erupting' counts, 'not erupting' / 'paused' does not. None when no synopsis."""
    low = (synopsis or "").lower()  # info: set low
    if "not erupting" in low or "paused" in low or "no active lava" in low:  # info: if "not erupting" in low or "paused" in low
        return False  # info: return False
    if "is erupting" in low or "currently erupting" in low:  # info: if "is erupting" in low or "currently erupting" in low
        return True  # info: return True
    return None  # not stated in this synopsis


# ====================================================
# SECTION: function headline
# What it does: headline.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def headline(alert_level: str, synopsis: str) -> str:  # G1 _headline, synopsis instead of scraped HTML
    low = (synopsis or "").lower()  # info: set low
    lvl = (alert_level or "").lower()  # info: set lvl
    if "not erupting" in low or "paused" in low:  # info: if "not erupting" in low or "paused" in low
        return "not erupting — eruption paused"  # info: return "not erupting — eruption paused"
    if lvl == "warning":  # info: if lvl == "warning" :
        return "WARNING — check HVO daily update"  # info: return "WARNING — check HVO daily update"
    if lvl == "watch":  # info: if lvl == "watch" :
        return "WATCH — elevated unrest"  # info: return "WATCH — elevated unrest"
    if lvl == "advisory":  # info: if lvl == "advisory" :
        return "ADVISORY — unrest"  # info: return "ADVISORY — unrest"
    return "quiet"  # info: return "quiet"


# ====================================================
# SECTION: function collect_volcanoes
# What it does: collect volcanoes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def collect_volcanoes(t: datetime, dry: bool, status: dict) -> None:  # info: def collect_volcanoes
    t0 = time.monotonic()  # info: set t0
    notices, latest, latest_van = [], {}, {}  # info: notices , latest , latest_van = [ ]
    try:  # info: try :
        for n in get_json(HANS_NEWEST) or []:  # info: for n in get_json ( HANS_NEWEST ) or
            if (n.get("obs") or "").lower() != "hvo":  # info: if ( n . get ( "obs" )
                continue  # info: continue
            row = {"id": n.get("noticeIdentifier"), "type": n.get("noticeType"), "type_cd": n.get("noticeTypeCd"),  # info: set row
                   "sent_utc": n.get("sentUtc"), "volcanoes": n.get("volcanoes"), "url": n.get("notice_url"),  # info: "sent_utc" : n . get ( "sentUtc" )
                   "sections": [{k: s.get(k) for k in ("volcanoName", "vnum", "alertLevel", "colorCode", "synopsis")}  # info: "sections" : [ { k : s .
                                for s in n.get("sections") or []]}  # info: for s in n . get ( "sections"
            notices.append(row)  # info: notices . append ( row )
            for s in row["sections"]:  # info: for s in row [ "sections" ] :
                v = s.get("vnum")  # info: set v
                if not v:  # info: if not v :
                    continue  # info: continue
                item = {"sent_utc": row["sent_utc"], "id": row["id"], "type": row["type"], "url": row["url"],  # info: set item
                        "synopsis": (s.get("synopsis") or "").strip()}  # info: call "synopsis"
                if v not in latest or (row["sent_utc"] or "") > (latest[v]["sent_utc"] or ""):  # info: if v not in latest or ( row
                    latest[v] = item  # info: latest [ v ] = item
                # VAN / VONA carry the eruption-state sentence (G1 gated on HVO notices, not daily text)
                if row["type_cd"] in {"VAN", "VV"} and (v not in latest_van or (row["sent_utc"] or "") > (latest_van[v]["sent_utc"] or "")):  # info: if row [ "type_cd" ] in { "VAN"
                    latest_van[v] = item  # info: latest_van [ v ] = item
        prev = seen_ids(VO, "hvo-notices", t)  # info: set prev
        new = [dict(r, first_seen_hst=t.isoformat()) for r in notices if r["id"] and r["id"] not in prev]  # info: set new
        append_daily(VO, "hvo-notices", t, new, dry)  # info: call append_daily
        status["hvo_notices"] = {"ok": True, "count": len(notices), "new": len(new)}  # info: status [ "hvo_notices" ] = { "ok" :
    except Exception as e:  # noqa: BLE001
        status["hvo_notices"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}  # info: status [ "hvo_notices" ] = { "ok" :
    status["hvo_notices"]["ms"] = int((time.monotonic() - t0) * 1000)  # info: status [ "hvo_notices" ] [ "ms" ] =

    t0 = time.monotonic()  # info: set t0
    try:  # info: try :
        rows = [v for v in get_json(HANS_MONITORED) or [] if (v.get("obs_abbr") or "").lower() == "hvo"]  # info: set rows
        vols = [{"name": v.get("volcano_name"), "vnum": v.get("vnum"), "alert_level": v.get("alert_level"),  # info: set vols
                 "color_code": v.get("color_code"), "status_sent_utc": v.get("sent_utc"),  # info: "color_code" : v . get ( "color_code" )
                 "status_notice_id": v.get("notice_identifier"), "status_notice_url": v.get("notice_url")} for v in rows]  # info: "status_notice_id" : v . get ( "notice_identifier" )
        write_json(VO / "hvo-last.json", {"at": t.isoformat(), "source": HANS_MONITORED, "observatory": "HVO",  # info: call write_json
                                          "count": len(vols), "volcanoes": vols}, dry)  # info: "count" : len ( vols ) , "volcanoes"
        for v in vols:  # info: for v in vols :
            stem = VOLCANOES.get(str(v["vnum"]))  # info: set stem
            if not stem:  # info: if not stem :
                continue  # info: continue
            ln = latest.get(str(v["vnum"])) or {}  # info: set ln
            van = latest_van.get(str(v["vnum"])) or {}  # info: set van
            lvl = v["alert_level"] or ""  # info: set lvl
            erupting = erupting_from(ln.get("synopsis", ""))  # info: set erupting
            if erupting is None:  # info: if erupting is None :
                erupting = erupting_from(van.get("synopsis", ""))  # info: set erupting
            write_json(VO / f"{stem}-last.json", {  # info: call write_json
                "at": t.isoformat(), "name": v["name"], "vnum": v["vnum"], "alert_level": lvl,  # info: "at" : t . isoformat ( ) ,
                "color_code": v["color_code"], "status_sent_utc": v["status_sent_utc"],  # info: "color_code" : v [ "color_code" ] , "status_sent_utc"
                "status_notice_id": v["status_notice_id"], "status_notice_url": v["status_notice_url"],  # info: "status_notice_id" : v [ "status_notice_id" ] , "status_notice_url"
                "latest_notice": ln or None, "latest_activity_notice": van or None,  # info: "latest_notice" : ln or None , "latest_activity_notice" :
                "headline": headline(lvl, ln.get("synopsis", "") or van.get("synopsis", "")),  # info: "headline" : headline ( lvl , ln .
                "erupting": erupting, "multiplier": get_multiplier(lvl),  # info: "erupting" : erupting , "multiplier" : get_multiplier (
                "sources": [HANS_MONITORED, HANS_NEWEST]}, dry)  # info: "sources" : [ HANS_MONITORED , HANS_NEWEST ] }
        status["hvo_status"] = {"ok": True, "volcanoes": len(vols),  # info: status [ "hvo_status" ] = { "ok" :
                                "kilauea": next((v["alert_level"] for v in vols if v["vnum"] == "332010"), None),  # info: "kilauea" : next ( ( v [ "alert_level"
                                "mauna_loa": next((v["alert_level"] for v in vols if v["vnum"] == "332020"), None)}  # info: "mauna_loa" : next ( ( v [ "alert_level"
    except Exception as e:  # noqa: BLE001
        status["hvo_status"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}  # info: status [ "hvo_status" ] = { "ok" :
    status["hvo_status"]["ms"] = int((time.monotonic() - t0) * 1000)  # info: status [ "hvo_status" ] [ "ms" ] =


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    what = next((a for a in argv if a in {"all", "quakes", "volcanoes"}), "all")  # info: set what
    dry = "--dry-run" in argv  # info: set dry
    t, status = now_hst(), {}  # info: t , status = now_hst ( ) ,
    if what in {"all", "quakes"}:  # info: if what in { "all" , "quakes" }
        collect_quakes(t, dry, status)  # info: call collect_quakes
    if what in {"all", "volcanoes"}:  # info: if what in { "all" , "volcanoes" }
        collect_volcanoes(t, dry, status)  # info: call collect_volcanoes
    ok = all(s.get("ok") for s in status.values())  # info: set ok
    out = {"ok": ok, "at": t.isoformat(), "what": what, "dry_run": dry, "sources": status}  # info: set out
    if not dry:  # info: if not dry :
        prev = {}  # info: set prev
        try:  # info: try :
            prev = json.loads((GEO / "collector-last.json").read_text(encoding="utf-8"))  # info: set prev
        except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
            pass  # info: pass
        merged = dict(prev.get("sources") or {}, **status)  # info: set merged
        write_json(GEO / "collector-last.json", dict(out, sources=merged), dry)  # info: call write_json
    print(json.dumps(out, ensure_ascii=False))  # info: call print
    return 0 if ok else 1  # info: return 0 if ok else 1


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv[1:]))  # info: raise SystemExit ( main ( sys . argv
