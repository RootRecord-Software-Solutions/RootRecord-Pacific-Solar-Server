#!/usr/bin/env python3
"""Worldwide tropical cyclone board (G3 port of G1 weather/hurricane-tracker/scripts/hurricane_tracker.py, 2026-09-29).

  python3 global_board.py   NHC CurrentStorms + RAMMB tc_realtime + JTWC ABPW / ABIO -> Database
                            Weather/Hawai'i/hurricanes/global/storms-last.json (git-ignored with /Weather/), print a summary

Standalone and additive: the weather poller's hurricanes/scripts/sources.py keeps the Hawaiʻi-relevant NHC track.json
files; this adds the G1 global board (Atlantic / Pacific / West Pacific / Indian / Southern Hemisphere).
Ported unchanged: _parse_latlon, _class_label, _basin_name, _windy, _enrich (Florida + Hawaiʻi distance, score, focus),
_from_nhc, _from_rammb, _from_jtwc (+ storm_track.parse_jtwc_moving), _merge (max 14, invests only if close / al / cp).
Also: RAMMB per-storm page (IR gif URL + track tables), storm_track attach / persist, storm_plot text file.
Not ported: NWS radar links, OBS mode / scenes (OBS BLOCKED). Four source GETs plus one storm page per kept storm
(14 s timeout each). Current files only; nothing deleted.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
import storm_plot  # noqa: E402
import storm_track  # noqa: E402

log = logging.getLogger("rr.hurricane_global")
HST = ZoneInfo("Pacific/Honolulu")
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
OUT = DB / "Weather" / "Hawai'i" / "hurricanes" / "global"
HAWAII_THREAT_NM = 800
UA = "RootRecord-Pacific/3 (hurricane global board)"
NHC_URL = "https://www.nhc.noaa.gov/CurrentStorms.json"
RAMMB_URL = "https://rammb-data.cira.colostate.edu/tc_realtime/"
RAMMB_STORM = "https://rammb-data.cira.colostate.edu/tc_realtime/storm.asp?storm_identifier={id}"
JTWC_ABPW = "https://www.metoc.navy.mil/jtwc/products/abpwweb.txt"
JTWC_ABIO = "https://www.metoc.navy.mil/jtwc/products/abioweb.txt"
_JTWC_DIR = {
    "NORTH": 0.0,
    "NORTH-NORTHEAST": 22.5,
    "NORTHEAST": 45.0,
    "EAST-NORTHEAST": 67.5,
    "EAST": 90.0,
    "EAST-SOUTHEAST": 112.5,
    "SOUTHEAST": 135.0,
    "SOUTH-SOUTHEAST": 157.5,
    "SOUTH": 180.0,
    "SOUTH-SOUTHWEST": 202.5,
    "SOUTHWEST": 225.0,
    "WEST-SOUTHWEST": 247.5,
    "WEST": 270.0,
    "WEST-NORTHWEST": 292.5,
    "NORTHWEST": 315.0,
    "NORTH-NORTHWEST": 337.5,
}

FLORIDA = {
    "Miami": (25.7617, -80.1918),
    "Tampa": (27.9506, -82.4572),
    "Key West": (24.5551, -81.7800),
    "Jacksonville": (30.3322, -81.6557),
}

HAWAII = {
    "Honolulu": (21.3069, -157.8583),
    "Hilo": (19.7297, -155.0900),
    "Līhuʻe": (21.9811, -159.3711),
    "Kona": (19.6390, -155.9969),
}


def parse_jtwc_moving(text: str) -> tuple[float | None, int | None]:
    blob = text or ""
    up = blob.upper()
    if re.search(r"NEARLY\s+STATIONARY|\bSTATIONARY\b", up):
        return None, 0
    m = re.search(
        r"MOVING\s+(?:SLOWLY\s+|RAPIDLY\s+)?([A-Z][A-Z\-]*WARD)(?:\s+AT\s+(\d{1,2})\s+KNOTS)?",
        up,
    )
    if not m:
        return None, None
    raw = m.group(1).replace("WARDS", "").replace("WARD", "")
    deg = _JTWC_DIR.get(raw)
    kt = int(m.group(2)) if m.group(2) else None
    return deg, kt


def _get(url: str, timeout: float = 14) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))


def _nm(km: float) -> float:
    return km * 0.539957


def _parse_latlon(lat: str | float | None, lon: str | float | None) -> tuple[float | None, float | None]:
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        return float(lat), float(lon)

    def one(val: str | None, pos: str, neg: str) -> float | None:
        if not val:
            return None
        s = str(val).strip().upper().replace(" ", "")
        m = re.match(r"^([+-]?\d+(?:\.\d+)?)([NSEW])?$", s)
        if not m:
            return None
        n = float(m.group(1))
        hemi = m.group(2)
        if hemi in {neg}:
            n = -abs(n)
        elif hemi in {pos}:
            n = abs(n)
        return n

    return one(str(lat) if lat is not None else None, "N", "S"), one(
        str(lon) if lon is not None else None, "E", "W"
    )


def _class_label(code: str, knots: int | None, text: str = "") -> str:
    blob = f"{code} {text}".upper()
    kt = knots or 0
    if "INVEST" in blob:
        return "Invest"
    if kt >= 137 or "CAT 5" in blob or "CATEGORY 5" in blob:
        return "Category 5 hurricane"
    if kt >= 113 or "CAT 4" in blob:
        return "Category 4 hurricane"
    if kt >= 96 or "CAT 3" in blob or "MAJOR" in blob:
        return "Major hurricane"
    if kt >= 83 or "CAT 2" in blob:
        return "Category 2 hurricane"
    if kt >= 64 or code in {"HU", "TY", "MH"} or "HURRICANE" in blob or "TYPHOON" in blob:
        return "Hurricane" if "TYPHOON" not in blob else "Typhoon"
    if kt >= 34 or code in {"TS", "STS", "TC"} or "TROPICAL STORM" in blob:
        return "Tropical storm"
    if "DEPRESSION" in blob or code in {"TD", "SD"}:
        return "Tropical depression"
    return (text or code or "Tropical cyclone").strip()


def _basin_name(code: str) -> str:
    return {
        "al": "Atlantic",
        "ep": "Eastern Pacific",
        "cp": "Central Pacific",
        "wp": "Western Pacific",
        "io": "North Indian",
        "sh": "Southern Hemisphere",
    }.get(code[:2].lower(), code.upper())


def _windy(lat: float | None, lon: float | None, zoom: int = 6) -> str:
    if lat is None or lon is None:
        return "https://www.windy.com/-Hurricane-tracker/hurricanes?hurricanes,20,-40,3,p:cities"
    return (
        "https://www.windy.com/-Hurricane-tracker/hurricanes"
        f"?hurricanes,{lat:.3f},{lon:.3f},{zoom},p:cities"
    )


def _enrich(storm: dict) -> dict:
    lat, lon = storm.get("lat"), storm.get("lon")
    fl = {}
    hi = {}
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        fl = {
            name: round(_nm(_haversine_km((lat, lon), pos)), 0)
            for name, pos in FLORIDA.items()
        }
        hi = {
            name: round(_nm(_haversine_km((lat, lon), pos)), 0)
            for name, pos in HAWAII.items()
        }
    nearest_fl = min(fl.values()) if fl else None
    nearest_hi = min(hi.values()) if hi else None
    knots = int(storm.get("knots") or 0)
    invest = bool(storm.get("invest"))
    basin = str(storm.get("basin") or "")
    score = knots
    if nearest_fl is not None:
        if nearest_fl < 2500:
            score += 500 + int((2500 - nearest_fl) / 4)
        if nearest_fl < 800:
            score += 400
    if nearest_hi is not None:
        if nearest_hi < 2500:
            score += 550 + int((2500 - nearest_hi) / 4)
        if nearest_hi < 800:
            score += 450
    if basin == "al":
        score += 180
    if basin == "cp":
        score += 220
    if basin == "ep" and nearest_hi and nearest_hi < 2000:
        score += 120
    if invest:
        score -= 90
    name = str(storm.get("name") or storm.get("id") or "Storm")
    scene = f"Storm · {name.title() if name.isupper() else name}"
    if invest:
        scene = f"Storm · {str(storm.get('id') or name).upper()}"
    storm.update(
        {
            "florida_nm": fl,
            "hawaii_nm": hi,
            "nearest_florida_nm": nearest_fl,
            "nearest_hawaii_nm": nearest_hi,
            "focus": (
                "florida"
                if nearest_fl is not None and (nearest_hi is None or nearest_fl <= nearest_hi) and nearest_fl < HAWAII_THREAT_NM
                else "hawaii"
                if nearest_hi is not None and nearest_hi < HAWAII_THREAT_NM
                else "global"
            ),
            "score": score,
            "scene": scene[:80],
            "label": storm.get("label") or _class_label(str(storm.get("class") or ""), knots, name),
            "windy_url": _windy(lat, lon, 6 if not invest else 5),
            "mph": round(knots * 1.15078) if knots else None,
        }
    )
    return storm


def _from_nhc(raw: dict) -> list[dict]:
    out = []
    for s in raw.get("activeStorms") or []:
        lat, lon = s.get("latitudeNumeric"), s.get("longitudeNumeric")
        if lat is None:
            lat, lon = _parse_latlon(s.get("latitude"), s.get("longitude"))
        sid = str(s.get("id") or "").lower()
        basin = sid[:2]
        try:
            knots = int(float(s.get("intensity") or 0))
        except (TypeError, ValueError):
            knots = 0
        name = str(s.get("name") or sid).strip()
        klass = str(s.get("classification") or "")
        bin_no = str(s.get("binNumber") or "")
        graphics = ""
        if bin_no:
            graphics = f"https://www.nhc.noaa.gov/graphics_{bin_no.lower()}.shtml?cone"
        out.append(
            _enrich(
                {
                    "id": sid,
                    "source": "nhc",
                    "basin": basin,
                    "basin_name": _basin_name(basin),
                    "name": name,
                    "class": klass,
                    "knots": knots,
                    "mb": _to_int(s.get("pressure")),
                    "lat": lat,
                    "lon": lon,
                    "movement_dir": s.get("movementDir"),
                    "movement_kt": s.get("movementSpeed"),
                    "updated": s.get("lastUpdate"),
                    "advisory_url": ((s.get("publicAdvisory") or {}).get("url")),
                    "cone_url": graphics,
                    "invest": name.upper() in {"INVEST", "UNKNOWN"} or "INVEST" in klass.upper(),
                }
            )
        )
    return out


def _to_int(v) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _from_rammb(html: str) -> list[dict]:
    out = []
    for m in re.finditer(
        r'storm_identifier=([a-z0-9]+)[^>]*>\s*([A-Z0-9]+)\s*-\s*([^<]+)',
        html,
        re.I,
    ):
        sid = m.group(1).lower()
        label = re.sub(r"<br\s*/?>", "", m.group(3), flags=re.I).strip()
        basin = sid[:2]
        invest = "INVEST" in label.upper()
        year = sid[4:8] if len(sid) >= 8 else datetime.now(timezone.utc).strftime("%Y")
        num = sid[2:4]
        ir = (
            "https://rammb-data.cira.colostate.edu/tc_realtime/products/storms/"
            f"{year}{basin}{num}/4kmirimg/{year}{basin}{num}_4kmirimg.gif"
        )
        out.append(
            {
                "id": sid,
                "source": "rammb",
                "basin": basin,
                "basin_name": _basin_name(basin),
                "name": "INVEST" if invest else re.sub(r"^(Major\s+)?(Hurricane|Typhoon|Tropical Storm|Tropical Depression)\s+", "", label, flags=re.I).strip() or sid,
                "class": "INVEST" if invest else "",
                "label": label.title() if not invest else "Invest",
                "rammb_url": RAMMB_STORM.format(id=sid),
                "ir_guess": ir,
                "invest": invest,
            }
        )
    return out


def _rammb_ir(sid: str, html: str) -> str | None:
    if len(sid) < 8:
        m = None
    else:
        m = re.search(
            rf"/tc_realtime/products/storms/[^\"']+{re.escape(sid[4:8] + sid[:2] + sid[2:4])}?[^\"']*4kmirimg[^\"']+\.gif",
            html,
            re.I,
        )
    if not m:
        m = re.search(r"/tc_realtime/products/storms/[^\"']+4kmirimg[^\"']+\.gif", html, re.I)
    if not m:
        return None
    return "https://rammb-data.cira.colostate.edu" + m.group(0)


def _fill_storm_page(storm: dict) -> None:
    sid = str(storm.get("id") or "")
    if not sid:
        return
    try:
        html = _get(RAMMB_STORM.format(id=sid))
    except Exception as e:  # noqa: BLE001
        log.info("rammb storm page skip %s: %s", sid, e)
        return
    if not html:
        return
    if not storm.get("ir_url"):
        ir = _rammb_ir(sid, html)
        if ir:
            storm["ir_url"] = ir
    try:
        storm_track.apply_rammb_page(storm, html)
    except Exception as e:  # noqa: BLE001
        log.info("rammb track parse skip %s: %s", sid, e)


def _from_jtwc(text: str, default_basin: str) -> list[dict]:
    out = []
    # Named warning: TROPICAL STORM 17W (SAUDEL) WAS LOCATED NEAR 8.5N 154.1E ... 35 KNOTS
    named = re.compile(
        r"(TYPHOON|HURRICANE|TROPICAL STORM|TROPICAL DEPRESSION)\s+(\d{1,2})([WEPACS])"
        r"(?:\s+\(([A-Z][A-Z0-9\- ]+)\))?.*?NEAR\s+(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])"
        r".{0,500}?MAXIMUM\s+SUSTAINED\s+SURFACE\s+WINDS WERE ESTIMATED AT (\d{2,3})\s+KNOTS",
        re.I | re.S,
    )
    for m in named.finditer(text):
        num = int(m.group(2))
        hemi = m.group(3).lower()
        basin = {"w": "wp", "e": "ep", "p": "cp", "a": "al", "c": "cp", "s": "sh"}.get(hemi, default_basin)
        lat = float(m.group(5)) * (1 if m.group(6).upper() == "N" else -1)
        lon = float(m.group(7)) * (1 if m.group(8).upper() == "E" else -1)
        name = (m.group(4) or f"{num}{hemi.upper()}").strip()
        move_dir, move_kt = parse_jtwc_moving(m.group(0))
        out.append(
            {
                "id": f"{basin}{num:02d}{datetime.now(timezone.utc).year}",
                "source": "jtwc",
                "basin": basin,
                "name": name,
                "class": m.group(1),
                "knots": int(m.group(9)),
                "lat": lat,
                "lon": lon,
                "movement_dir": move_dir,
                "movement_kt": move_kt,
                "movement_source": "jtwc" if move_dir is not None or move_kt is not None else None,
                "invest": False,
            }
        )
    invest = re.compile(
        r"INVEST\s+(\d{2})([WEPACS]).*?NEAR\s+(\d+\.?\d*)([NS])\s+(\d+\.?\d*)([EW])"
        r".{0,500}?(\d{2,3})\s+(?:TO\s+\d{2,3}\s+)?KNOTS",
        re.I | re.S,
    )
    for m in invest.finditer(text):
        num = int(m.group(1))
        hemi = m.group(2).lower()
        basin = {"w": "wp", "e": "ep", "p": "cp", "s": "sh", "a": "io", "c": "io"}.get(hemi, default_basin)
        lat = float(m.group(3)) * (1 if m.group(4).upper() == "N" else -1)
        lon = float(m.group(5)) * (1 if m.group(6).upper() == "E" else -1)
        out.append(
            {
                "id": f"{basin}{num:02d}{datetime.now(timezone.utc).year}",
                "source": "jtwc",
                "basin": basin,
                "name": "INVEST",
                "class": "INVEST",
                "knots": int(m.group(7)),
                "lat": lat,
                "lon": lon,
                "invest": True,
            }
        )
    return out


def _merge(rows: list[dict]) -> list[dict]:
    by: dict[str, dict] = {}
    for row in rows:
        sid = str(row.get("id") or "").lower()
        if not sid:
            continue
        cur = by.get(sid)
        if not cur:
            by[sid] = row
            continue
        for k, v in row.items():
            if v in (None, "", [], {}):
                continue
            if k in {"lat", "lon", "knots", "mb"} and cur.get(k) in (None, 0, ""):
                cur[k] = v
            elif k not in cur or cur[k] in (None, "", []):
                cur[k] = v
            elif k == "source" and v == "nhc":
                cur[k] = v
        if row.get("source") == "nhc":
            for k in ("name", "class", "cone_url", "advisory_url", "updated"):
                if row.get(k):
                    cur[k] = row[k]
    storms = [_enrich(s) for s in by.values()]
    storms.sort(key=lambda s: (-int(s.get("score") or 0), -int(s.get("knots") or 0)))
    kept: list[dict] = []
    for s in storms:
        if not s.get("invest"):
            kept.append(s)
            continue
        nfl, nhi = s.get("nearest_florida_nm"), s.get("nearest_hawaii_nm")
        close = (nfl is not None and nfl < 2200) or (nhi is not None and nhi < HAWAII_THREAT_NM)
        if close or s.get("basin") in {"al", "cp"}:
            kept.append(s)
    return kept[:14]


def refresh() -> dict:
    rows, sources, errors = [], [], {}
    for key, url in (("nhc", NHC_URL), ("rammb", RAMMB_URL), ("jtwc-wp", JTWC_ABPW), ("jtwc-io", JTWC_ABIO)):
        try:
            raw = _get(url)
        except Exception as e:  # noqa: BLE001
            errors[key] = f"{type(e).__name__}: {e}"[:200]
            continue
        try:
            if key == "nhc":
                rows.extend(_from_nhc(json.loads(raw)))
            elif key == "rammb":
                rows.extend(_from_rammb(raw))
            else:
                rows.extend(_from_jtwc(raw, "wp" if key == "jtwc-wp" else "io"))
            sources.append(key)
        except Exception as e:  # noqa: BLE001
            errors[key] = f"parse {type(e).__name__}: {e}"[:200]
    storms = _merge(rows)
    storm_track.TRACKS_PATH = OUT / "storm-tracks.json"
    for storm in storms[:14]:
        _fill_storm_page(storm)
    storms = [_enrich(s) for s in storms]
    for storm in storms:
        try:
            storm_track.attach_track(storm, persist=True)
        except Exception as e:  # noqa: BLE001
            log.info("storm track persist skip %s: %s", storm.get("id"), e)
    return {"ok": bool(sources), "ts": datetime.now(timezone.utc).isoformat(),
            "at": datetime.now(HST).isoformat(timespec="seconds"), "sources": sources, "errors": errors,
            "count": len(storms), "storms": storms}


def _append_log(payload: dict) -> None:
    try:
        log_dir = DB / "Logs" / "Weather" / "hurricanes"
        log_dir.mkdir(parents=True, exist_ok=True)
        tracked = sum(
            1 for s in payload.get("storms") or []
            if s.get("track_history") or s.get("forecast_track")
        )
        line = (
            f"{payload.get('at')} ok={payload.get('ok')} storms={payload.get('count')} "
            f"with_tracks={tracked} sources={','.join(payload.get('sources') or [])}\n"
        )
        with (log_dir / "global-board.log").open("a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError as e:
        log.info("hurricane log skip: %s", e)


def main() -> int:
    payload = refresh()
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "storms-last.json.tmp"
    tmp.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, OUT / "storms-last.json")
    storm_plot.BOARD_DIR = OUT
    storm_plot.write_plot(payload)
    _append_log(payload)
    print(json.dumps({"ok": payload["ok"], "sources": payload["sources"], "errors": payload["errors"], "count": payload["count"],
                      "storms": [f"{s.get('label')} {s.get('name')} ({s.get('basin')}, {s.get('knots')} kt, "
                                 f"nearest HI {s.get('nearest_hawaii_nm')} nm, src {s.get('source')})" for s in payload["storms"]]},
                     ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
