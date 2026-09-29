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
from __future__ import annotations

import gzip
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
GEO = DB / "Geology"
EQ, VO = GEO / "Earthquakes", GEO / "Volcanoes"
UA = "RootRecord-Pacific-Geology/1.0 (+https://rootrecord.cloud)"
TIMEOUT = min(10.0, float(os.environ.get("RR_GEOLOGY_TIMEOUT", "10")))

FDSN = "https://earthquake.usgs.gov/fdsnws/event/1/query"
GLOBAL_FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
HANS_MONITORED = "https://volcanoes.usgs.gov/hans-public/api/volcano/getMonitoredVolcanoes"
HANS_NEWEST = "https://volcanoes.usgs.gov/hans-public/api/notice/getNewestOrRecent"
HAWAII_BBOX = {"minlatitude": 18.5, "maxlatitude": 22.5, "minlongitude": -160.5, "maxlongitude": -154.5}  # G1
HAWAII_M_MIN, LOCAL_M2 = 1.0, 2.0          # G1 _fetch minmagnitude / _LOCAL_M_MIN
KILAUEA_LATLON, KILAUEA_RADIUS_KM = (19.421, -155.287), 150  # G1 rr-kilauea USGS_QUAKE_URL
LOCATIONS_FILE = Path(__file__).resolve().parents[1] / "config" / "global-locations.json"  # G0 old/config/locations (copy)
NEAREST_MAX_KM = 250  # G0 operations/earthquakes/global/poller.py nearest(): no tag beyond 250 km
_LOCATIONS: list[dict] | None = None
VOLCANOES = {"332010": "kilauea", "332020": "mauna-loa"}      # vnum -> last-file stem
MULTIPLIERS = {"normal": 1.0, "advisory": 2.0, "watch": 2.5, "eruption": 3.0}  # G1 rr-kilauea
MAX_EVENTS_LAST = 100


# ------------------------------------------------------------------ io helpers
def now_hst() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def get_json(url: str):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json", "Accept-Encoding": "gzip"})
    with urlopen(req, timeout=TIMEOUT) as r:
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
    return json.loads(raw.decode("utf-8"))


def write_json(path: Path, data, dry: bool) -> None:
    if dry:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def daily_path(folder: Path, stem: str, day: datetime) -> Path:
    return folder / "Daily" / f"{stem}-{day:%Y%m%d}.jsonl"


def seen_ids(folder: Path, stem: str, t: datetime, key: str = "id") -> set[str]:
    out: set[str] = set()
    for day in (t, t - timedelta(days=1)):
        p = daily_path(folder, stem, day)
        try:
            for ln in p.read_text(encoding="utf-8").splitlines():
                try:
                    out.add(str(json.loads(ln)[key]))
                except (ValueError, KeyError, TypeError):
                    continue
        except OSError:
            continue
    return out


def append_daily(folder: Path, stem: str, t: datetime, rows: list[dict], dry: bool) -> None:
    if dry or not rows:
        return
    p = daily_path(folder, stem, t)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def _ms_iso(ms, tz=timezone.utc) -> str | None:
    try:
        return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc).astimezone(tz).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))


def nearest_location(lat, lon) -> dict | None:
    """G0 global poller nearest(): closest registry location (country capitals, US state capitals, staged Hawaii
    places) within 250 km, else None. Adds country_code / admin1_code / location_id like the G0 SQLite columns."""
    global _LOCATIONS
    if lat is None or lon is None:
        return None
    if _LOCATIONS is None:
        try:
            _LOCATIONS = json.loads(LOCATIONS_FILE.read_text(encoding="utf-8")).get("locations") or []
        except (OSError, ValueError):
            _LOCATIONS = []
    best, best_km = None, float("inf")
    for x in _LOCATIONS:
        if x.get("lat") is None or x.get("lon") is None:
            continue
        d = haversine_km((float(lat), float(lon)), (float(x["lat"]), float(x["lon"])))
        if d < best_km:
            best, best_km = x, d
    if best is None or best_km > NEAREST_MAX_KM:
        return None
    return {"location_id": best.get("id"), "name": best.get("name"), "country_code": best.get("country_code"),
            "admin1_code": best.get("admin1_code") or None, "km": round(best_km, 1)}


# ------------------------------------------------------------------ earthquakes
def norm_event(f: dict) -> dict:
    p, c = f.get("properties") or {}, (f.get("geometry") or {}).get("coordinates") or [None, None, None]
    return {"id": f.get("id"), "mag": p.get("mag"), "mag_type": p.get("magType"), "place": p.get("place") or "",
            "time_utc": _ms_iso(p.get("time")), "time_hst": _ms_iso(p.get("time"), HST),
            "lon": c[0], "lat": c[1], "depth_km": c[2] if len(c) > 2 else None,
            "status": p.get("status"), "tsunami": p.get("tsunami"), "type": p.get("type"), "url": p.get("url"),
            "nearest": nearest_location(c[1], c[0])}


def _mag(e: dict) -> float | None:
    try:
        return float(e.get("mag"))
    except (TypeError, ValueError):
        return None


def summarize(events: list[dict]) -> dict:
    mags = [m for m in (_mag(e) for e in events) if m is not None]
    big = max(events, key=lambda e: _mag(e) if _mag(e) is not None else -9, default=None)
    return {"count": len(events), "count_m2": sum(m >= 2.0 for m in mags), "count_m25": sum(m >= 2.5 for m in mags),
            "largest": {k: big.get(k) for k in ("id", "mag", "place", "time_hst")} if big and mags else None}


def collect_quakes(t: datetime, dry: bool, status: dict) -> None:
    hi_ids: set[str] = set()
    # Hawaiʻi — FDSN query, bbox, last 24 h
    start = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    url = f"{FDSN}?" + urlencode({"format": "geojson", "orderby": "time", "starttime": start,
                                   "minmagnitude": HAWAII_M_MIN, **HAWAII_BBOX})
    t0 = time.monotonic()
    try:
        data = get_json(url)
        ev = [norm_event(f) for f in data.get("features") or []]
        hi_ids = {e["id"] for e in ev if e.get("id")}
        prev = seen_ids(EQ, "hawaii", t)
        new = [dict(e, first_seen_hst=t.isoformat()) for e in ev if e.get("id") and e["id"] not in prev]
        new_m2 = [e["id"] for e in new if (_mag(e) or 0) >= LOCAL_M2]
        near = [e for e in ev if e.get("lat") is not None and e.get("lon") is not None
                and haversine_km(KILAUEA_LATLON, (e["lat"], e["lon"])) <= KILAUEA_RADIUS_KM]
        last = {"at": t.isoformat(), "source": url, "window_h": 24, "min_mag": HAWAII_M_MIN, "bbox": HAWAII_BBOX,
                **summarize(ev), "kilauea_150km_count": len(near), "new_this_run": len(new), "new_local_m2_ids": new_m2,
                "usgs_generated_utc": _ms_iso((data.get("metadata") or {}).get("generated")),
                "events": ev[:MAX_EVENTS_LAST]}
        write_json(EQ / "hawaii-last.json", last, dry)
        append_daily(EQ, "hawaii", t, new, dry)
        status["hawaii"] = {"ok": True, "count": len(ev), "new": len(new), "new_m2": len(new_m2)}
    except Exception as e:  # noqa: BLE001 — one failed source must not stop the others
        status["hawaii"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}
    status["hawaii"]["ms"] = int((time.monotonic() - t0) * 1000)

    # Global — USGS summary feed M2.5+ day (Hawaiʻi ids dropped, as in G1 fetch_bundle)
    t0 = time.monotonic()
    try:
        data = get_json(GLOBAL_FEED)
        ev = [norm_event(f) for f in data.get("features") or []]
        ev = [e for e in ev if e.get("id") not in hi_ids]
        ev.sort(key=lambda e: e.get("time_utc") or "", reverse=True)
        prev = seen_ids(EQ, "global", t)
        new = [dict(e, first_seen_hst=t.isoformat()) for e in ev if e.get("id") and e["id"] not in prev]
        last = {"at": t.isoformat(), "source": GLOBAL_FEED, "window_h": 24, "min_mag": 2.5, "excludes": "hawaii-last ids",
                **summarize(ev), "new_this_run": len(new),
                "usgs_generated_utc": _ms_iso((data.get("metadata") or {}).get("generated")),
                "events": ev[:MAX_EVENTS_LAST]}
        write_json(EQ / "global-last.json", last, dry)
        append_daily(EQ, "global", t, new, dry)
        status["global"] = {"ok": True, "count": len(ev), "new": len(new)}
    except Exception as e:  # noqa: BLE001
        status["global"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}
    status["global"]["ms"] = int((time.monotonic() - t0) * 1000)


# ------------------------------------------------------------------ volcanoes (HVO)
def get_multiplier(alert_level: str) -> float:  # G1 rr-kilauea, unchanged
    level = (alert_level or "").lower().strip()
    if "erupt" in level or "red" in level or "warning" in level:
        return MULTIPLIERS["eruption"]
    if "watch" in level or "orange" in level:
        return MULTIPLIERS["watch"]
    if "advisory" in level or "yellow" in level:
        return MULTIPLIERS["advisory"]
    return MULTIPLIERS["normal"]


def erupting_from(synopsis: str) -> bool | None:
    """G1 rule: 'is erupting' counts, 'not erupting' / 'paused' does not. None when no synopsis."""
    low = (synopsis or "").lower()
    if "not erupting" in low or "paused" in low or "no active lava" in low:
        return False
    if "is erupting" in low or "currently erupting" in low:
        return True
    return None  # not stated in this synopsis


def headline(alert_level: str, synopsis: str) -> str:  # G1 _headline, synopsis instead of scraped HTML
    low = (synopsis or "").lower()
    lvl = (alert_level or "").lower()
    if "not erupting" in low or "paused" in low:
        return "not erupting — eruption paused"
    if lvl == "warning":
        return "WARNING — check HVO daily update"
    if lvl == "watch":
        return "WATCH — elevated unrest"
    if lvl == "advisory":
        return "ADVISORY — unrest"
    return "quiet"


def collect_volcanoes(t: datetime, dry: bool, status: dict) -> None:
    t0 = time.monotonic()
    notices, latest, latest_van = [], {}, {}
    try:
        for n in get_json(HANS_NEWEST) or []:
            if (n.get("obs") or "").lower() != "hvo":
                continue
            row = {"id": n.get("noticeIdentifier"), "type": n.get("noticeType"), "type_cd": n.get("noticeTypeCd"),
                   "sent_utc": n.get("sentUtc"), "volcanoes": n.get("volcanoes"), "url": n.get("notice_url"),
                   "sections": [{k: s.get(k) for k in ("volcanoName", "vnum", "alertLevel", "colorCode", "synopsis")}
                                for s in n.get("sections") or []]}
            notices.append(row)
            for s in row["sections"]:
                v = s.get("vnum")
                if not v:
                    continue
                item = {"sent_utc": row["sent_utc"], "id": row["id"], "type": row["type"], "url": row["url"],
                        "synopsis": (s.get("synopsis") or "").strip()}
                if v not in latest or (row["sent_utc"] or "") > (latest[v]["sent_utc"] or ""):
                    latest[v] = item
                # VAN / VONA carry the eruption-state sentence (G1 gated on HVO notices, not daily text)
                if row["type_cd"] in {"VAN", "VV"} and (v not in latest_van or (row["sent_utc"] or "") > (latest_van[v]["sent_utc"] or "")):
                    latest_van[v] = item
        prev = seen_ids(VO, "hvo-notices", t)
        new = [dict(r, first_seen_hst=t.isoformat()) for r in notices if r["id"] and r["id"] not in prev]
        append_daily(VO, "hvo-notices", t, new, dry)
        status["hvo_notices"] = {"ok": True, "count": len(notices), "new": len(new)}
    except Exception as e:  # noqa: BLE001
        status["hvo_notices"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}
    status["hvo_notices"]["ms"] = int((time.monotonic() - t0) * 1000)

    t0 = time.monotonic()
    try:
        rows = [v for v in get_json(HANS_MONITORED) or [] if (v.get("obs_abbr") or "").lower() == "hvo"]
        vols = [{"name": v.get("volcano_name"), "vnum": v.get("vnum"), "alert_level": v.get("alert_level"),
                 "color_code": v.get("color_code"), "status_sent_utc": v.get("sent_utc"),
                 "status_notice_id": v.get("notice_identifier"), "status_notice_url": v.get("notice_url")} for v in rows]
        write_json(VO / "hvo-last.json", {"at": t.isoformat(), "source": HANS_MONITORED, "observatory": "HVO",
                                          "count": len(vols), "volcanoes": vols}, dry)
        for v in vols:
            stem = VOLCANOES.get(str(v["vnum"]))
            if not stem:
                continue
            ln = latest.get(str(v["vnum"])) or {}
            van = latest_van.get(str(v["vnum"])) or {}
            lvl = v["alert_level"] or ""
            erupting = erupting_from(ln.get("synopsis", ""))
            if erupting is None:
                erupting = erupting_from(van.get("synopsis", ""))
            write_json(VO / f"{stem}-last.json", {
                "at": t.isoformat(), "name": v["name"], "vnum": v["vnum"], "alert_level": lvl,
                "color_code": v["color_code"], "status_sent_utc": v["status_sent_utc"],
                "status_notice_id": v["status_notice_id"], "status_notice_url": v["status_notice_url"],
                "latest_notice": ln or None, "latest_activity_notice": van or None,
                "headline": headline(lvl, ln.get("synopsis", "") or van.get("synopsis", "")),
                "erupting": erupting, "multiplier": get_multiplier(lvl),
                "sources": [HANS_MONITORED, HANS_NEWEST]}, dry)
        status["hvo_status"] = {"ok": True, "volcanoes": len(vols),
                                "kilauea": next((v["alert_level"] for v in vols if v["vnum"] == "332010"), None),
                                "mauna_loa": next((v["alert_level"] for v in vols if v["vnum"] == "332020"), None)}
    except Exception as e:  # noqa: BLE001
        status["hvo_status"] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:300]}
    status["hvo_status"]["ms"] = int((time.monotonic() - t0) * 1000)


def main(argv: list[str]) -> int:
    what = next((a for a in argv if a in {"all", "quakes", "volcanoes"}), "all")
    dry = "--dry-run" in argv
    t, status = now_hst(), {}
    if what in {"all", "quakes"}:
        collect_quakes(t, dry, status)
    if what in {"all", "volcanoes"}:
        collect_volcanoes(t, dry, status)
    ok = all(s.get("ok") for s in status.values())
    out = {"ok": ok, "at": t.isoformat(), "what": what, "dry_run": dry, "sources": status}
    if not dry:
        prev = {}
        try:
            prev = json.loads((GEO / "collector-last.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        merged = dict(prev.get("sources") or {}, **status)
        write_json(GEO / "collector-last.json", dict(out, sources=merged), dry)
    print(json.dumps(out, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
