"""Storm location, history, official forecast, and motion vs Hawaiʻi.

File facts only. RAMMB history/forecast and NHC/JTWC motion — no invented tracks.
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

_DB = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
TRACKS_PATH = _DB / "Weather" / "Hawai'i" / "hurricanes" / "global" / "storm-tracks.json"
HAWAII_THREAT_NM = 800
LIHUE = (21.9811, -159.3711)
HAWAII = {
    "Honolulu": (21.3069, -157.8583),
    "Hilo": (19.7297, -155.0900),
    "Līhuʻe": LIHUE,
    "Kona": (19.6390, -155.9969),
}

_EIGHT = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
_EIGHT_WORD = (
    "north",
    "northeast",
    "east",
    "southeast",
    "south",
    "southwest",
    "west",
    "northwest",
)
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


def _haversine_nm(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    km = 6371.0 * 2 * math.asin(min(1.0, math.sqrt(h)))
    return km * 0.539957


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def compass8(deg: float) -> str:
    idx = int((deg + 22.5) // 45) % 8
    return _EIGHT[idx]


def compass8_word(deg: float) -> str:
    idx = int((deg + 22.5) // 45) % 8
    return _EIGHT_WORD[idx]


def nearest_hawaii_nm(lat: float, lon: float) -> tuple[str, float]:
    best_name = "Līhuʻe"
    best = 9e9
    for name, pos in HAWAII.items():
        nm = _haversine_nm((lat, lon), pos)
        if nm < best:
            best = nm
            best_name = name
    return best_name, round(best, 0)


def ocean_region(lat: float, lon: float) -> dict[str, str]:
    """Named ocean box from lat/lon. Not a landfall call."""
    island, nm = nearest_hawaii_nm(lat, lon)
    if nm < HAWAII_THREAT_NM:
        return {
            "id": "hawaii",
            "name": "Near the Hawaiian Islands",
            "note": f"Inside {HAWAII_THREAT_NM:.0f} nmi of {island}.",
        }
    if -180.0 <= lon <= -140.0 and 5.0 <= lat <= 32.0:
        return {
            "id": "cpac",
            "name": "Central North Pacific",
            "note": "Hawaiian longitudes, still outside the local 800 nmi gate." if nm < 1800 else "Central Pacific, not a local Hawaiʻi threat on distance.",
        }
    if -140.0 < lon <= -80.0 and 0.0 <= lat <= 35.0:
        return {
            "id": "epac",
            "name": "Eastern North Pacific",
            "note": "Mexico/Central America side of the Pacific, not west of Kauaʻi.",
        }
    if -100.0 <= lon <= 0.0 and 5.0 <= lat <= 50.0:
        return {
            "id": "atlantic",
            "name": "North Atlantic",
            "note": "Atlantic basin. Not the Hawaiian Islands.",
        }
    if 100.0 <= lon <= 180.0 and -5.0 <= lat <= 45.0:
        if lat >= 20.0 and 120.0 <= lon <= 150.0:
            return {
                "id": "wpac-japan",
                "name": "Western North Pacific (Japan / East China / Philippine Sea)",
                "note": "West of the date line, Asia/Japan side. West of Kauaʻi is not toward Hawaiʻi.",
            }
        return {
            "id": "wpac",
            "name": "Western North Pacific",
            "note": "West of the date line. Asia/Japan waters, not the Hawaiian Islands.",
        }
    if -180.0 <= lon < -160.0:
        return {
            "id": "dateline",
            "name": "West of Hawaiʻi / date line approach",
            "note": "Between the date line and Kauaʻi longitudes.",
        }
    return {
        "id": "other",
        "name": "Outside the Hawaiʻi / EastPac / WestPac desks",
        "note": "Mapped position is not a Hawaiian-island board storm on distance.",
    }


def angle_delta(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def hawaii_approach(lat: float, lon: float, course_deg: float | None) -> str:
    """toward / away / abeam from the storm's course vs bearing to Līhuʻe."""
    if course_deg is None:
        return "unknown"
    to_hi = bearing_deg(lat, lon, LIHUE[0], LIHUE[1])
    delta = angle_delta(course_deg, to_hi)
    if delta <= 50:
        return "toward"
    if delta >= 130:
        return "away"
    return "abeam"


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


def _strip_html(html: str) -> str:
    t = re.sub(r"(?is)<script.*?</script>", " ", html or "")
    t = re.sub(r"(?is)<style.*?</style>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_rammb_tracks(html: str) -> dict[str, list[dict[str, Any]]]:
    """Official RAMMB tables on the storm page. Empty if the page has none."""
    text = _strip_html(html)
    forecast: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    fm = re.search(
        r"Forecast Hour Latitude Longitude Intensity(.*?)(?:Forecast Track Archive|Track History|About Forecast)",
        text,
        re.I,
    )
    if fm:
        for m in re.finditer(
            r"(-?\d+)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})",
            fm.group(1),
        ):
            hour, lat, lon, kt = int(m.group(1)), float(m.group(2)), float(m.group(3)), int(m.group(4))
            if lon > 180:
                lon -= 360
            forecast.append({"hour": hour, "lat": lat, "lon": lon, "knots": kt})
    hm = re.search(
        r"Track History Synoptic Time Latitude Longitude Intensity(.*?)(?:About Track History|Enhanced Infrared|Satellite)",
        text,
        re.I,
    )
    if hm:
        for m in re.finditer(
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(\d{1,3})",
            hm.group(1),
        ):
            lat, lon = float(m.group(2)), float(m.group(3))
            if lon > 180:
                lon -= 360
            history.append({"ts": m.group(1), "lat": lat, "lon": lon, "knots": int(m.group(4))})
        history.sort(key=lambda r: str(r.get("ts") or ""))
    return {"forecast": forecast, "history": history}


def course_from_fixes(fixes: list[dict[str, Any]]) -> dict[str, Any]:
    pts = [f for f in fixes if isinstance(f.get("lat"), (int, float)) and isinstance(f.get("lon"), (int, float))]
    if len(pts) < 2:
        return {"course_deg": None, "course_compass": None, "course_kt": None, "leg_nm": None}
    a, b = pts[-2], pts[-1]
    nm = _haversine_nm((float(a["lat"]), float(a["lon"])), (float(b["lat"]), float(b["lon"])))
    course = bearing_deg(float(a["lat"]), float(a["lon"]), float(b["lat"]), float(b["lon"]))
    kt = None
    ta, tb = str(a.get("ts") or ""), str(b.get("ts") or "")
    if len(ta) >= 16 and len(tb) >= 16 and ta[:16] != tb[:16]:
        try:
            from datetime import datetime

            fa = datetime.fromisoformat(ta.replace("Z", "").replace(" ", "T")[:16])
            fb = datetime.fromisoformat(tb.replace("Z", "").replace(" ", "T")[:16])
            hours = abs((fb - fa).total_seconds()) / 3600.0
            if 0.4 <= hours <= 48:
                kt = int(round(nm / hours))
        except (TypeError, ValueError):
            kt = None
    return {
        "course_deg": round(course, 0),
        "course_compass": compass8_word(course),
        "course_kt": kt,
        "leg_nm": round(nm, 0),
    }


def _fmt_pos(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.1f}{ns} {abs(lon):.1f}{ew}"


def forecast_vs_hawaii(now_lat: float, now_lon: float, forecast: list[dict[str, Any]]) -> dict[str, Any]:
    if not forecast:
        return {
            "summary": "No official forecast track on file.",
            "end_nm": None,
            "closer": None,
            "end_region": None,
        }
    end = forecast[-1]
    _, now_nm = nearest_hawaii_nm(now_lat, now_lon)
    isle, end_nm = nearest_hawaii_nm(float(end["lat"]), float(end["lon"]))
    region = ocean_region(float(end["lat"]), float(end["lon"]))
    closer = end_nm < now_nm - 150 and end_nm < 1800
    hour = end.get("hour")
    hour_s = f"hour {hour}" if hour is not None else "end"
    if closer and end_nm < HAWAII_THREAT_NM:
        extra = f" Forecast point comes inside {HAWAII_THREAT_NM:.0f} nmi of {isle}."
    elif closer:
        extra = f" Forecast comes closer to {isle} but stays outside {HAWAII_THREAT_NM:.0f} nmi on this file."
    else:
        extra = f" Forecast stays away from Hawaiʻi ({int(end_nm)} nmi from {isle} at {hour_s})."
    summary = (
        f"RAMMB forecast on file ends {_fmt_pos(float(end['lat']), float(end['lon']))} "
        f"({region['name']}).{extra} Not a landfall call."
    )
    return {
        "summary": summary,
        "end_nm": end_nm,
        "closer": closer,
        "end_region": region["id"],
        "end_lat": end.get("lat"),
        "end_lon": end.get("lon"),
        "end_hour": hour,
    }


def load_tracks() -> dict[str, Any]:
    path = TRACKS_PATH
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_tracks(data: dict[str, Any]) -> None:
    TRACKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = TRACKS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    tmp.replace(TRACKS_PATH)


def attach_track(storm: dict[str, Any], *, persist: bool = True) -> dict[str, Any]:
    """Mutate storm with region, motion, history, official forecast, vs-Hawaiʻi."""
    lat, lon = storm.get("lat"), storm.get("lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        storm.setdefault("region", None)
        storm.setdefault("hawaii_approach", "unknown")
        return storm

    region = ocean_region(float(lat), float(lon))
    history = storm.get("track_history") if isinstance(storm.get("track_history"), list) else []
    forecast = storm.get("forecast_track") if isinstance(storm.get("forecast_track"), list) else []

    sid = str(storm.get("id") or "").lower()
    store = load_tracks() if persist else {}
    slot = store.get(sid) if isinstance(store.get(sid), dict) else {}
    if not history and isinstance(slot.get("history"), list):
        history = slot["history"]
    if not forecast and isinstance(slot.get("forecast"), list):
        forecast = slot["forecast"]

    if persist and sid:
        if history:
            slot["history"] = history[-24:]
        if forecast:
            slot["forecast"] = forecast
        slot["lat"] = lat
        slot["lon"] = lon
        store[sid] = slot
        save_tracks(store)

    course = course_from_fixes(history) if len(history) >= 2 else {
        "course_deg": None,
        "course_compass": None,
        "course_kt": None,
        "leg_nm": None,
    }
    move_deg = storm.get("movement_dir")
    move_kt = storm.get("movement_kt")
    try:
        move_deg_f = float(move_deg) if move_deg is not None else None
    except (TypeError, ValueError):
        move_deg_f = None
    try:
        move_kt_i = int(round(float(move_kt))) if move_kt is not None else None
    except (TypeError, ValueError):
        move_kt_i = None
    if move_deg_f is None and course.get("course_deg") is not None:
        move_deg_f = float(course["course_deg"])
        storm["movement_dir"] = move_deg_f
        storm["movement_source"] = "track_history"
    if move_kt_i is None and course.get("course_kt") is not None:
        move_kt_i = int(course["course_kt"])
        storm["movement_kt"] = move_kt_i
    if move_deg_f is not None and storm.get("movement_source") != "track_history":
        storm["movement_source"] = storm.get("movement_source") or storm.get("source") or "advisory"

    approach = hawaii_approach(float(lat), float(lon), move_deg_f)
    fc = forecast_vs_hawaii(float(lat), float(lon), forecast)
    bear = bearing_deg(LIHUE[0], LIHUE[1], float(lat), float(lon))
    move_word = compass8_word(move_deg_f) if move_deg_f is not None else None
    if approach == "toward":
        vs = "toward Hawaiʻi"
    elif approach == "away":
        vs = "away from Hawaiʻi"
    elif approach == "abeam":
        vs = "abeam of Hawaiʻi (not aimed at the islands)"
    else:
        vs = "motion vs Hawaiʻi unknown"
    move_s = ""
    if move_word:
        kt_s = f" at {move_kt_i} kt" if move_kt_i is not None else ""
        move_s = f"Moving {move_word}{kt_s}, {vs}."
    elif move_kt_i == 0:
        move_s = "Nearly stationary."
    hist_s = ""
    if len(history) >= 2:
        a, b = history[0], history[-1]
        hist_s = (
            f"RAMMB history {len(history)} fixes: "
            f"{_fmt_pos(float(a['lat']), float(a['lon']))} → {_fmt_pos(float(b['lat']), float(b['lon']))}."
        )
    track_summary = " ".join(
        x for x in (region["name"] + ".", move_s, hist_s, vs.capitalize() + "." if not move_s else "") if x
    ).strip()

    storm.update(
        {
            "region": region["id"],
            "region_name": region["name"],
            "region_note": region["note"],
            "hawaii_approach": approach,
            "bearing_from_lihue_deg": round(bear, 0),
            "bearing_from_lihue": compass8_word(bear),
            "track_history": history,
            "forecast_track": forecast,
            "track_summary": track_summary,
            "forecast_summary": fc["summary"],
            "forecast_closer_to_hawaii": fc["closer"],
            "forecast_end_hawaii_nm": fc["end_nm"],
            "movement_compass": move_word,
        }
    )
    return storm


def apply_rammb_page(storm: dict[str, Any], html: str) -> dict[str, Any]:
    parsed = parse_rammb_tracks(html)
    if parsed["history"]:
        storm["track_history"] = parsed["history"]
        last = parsed["history"][-1]
        if storm.get("lat") is None:
            storm["lat"] = last["lat"]
            storm["lon"] = last["lon"]
        if not storm.get("knots") and last.get("knots"):
            storm["knots"] = last["knots"]
        storm["updated"] = last.get("ts")
    if parsed["forecast"]:
        storm["forecast_track"] = parsed["forecast"]
        z = parsed["forecast"][0]
        if storm.get("lat") is None:
            storm["lat"] = z["lat"]
            storm["lon"] = z["lon"]
        if z.get("knots") and not storm.get("knots"):
            storm["knots"] = z["knots"]
    return storm
