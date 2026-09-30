"""Text plot: nearest storm vs Hawaiʻi. File facts from the global board only.

Reads Weather/Hawai'i/hurricanes/global/storms-last.json and writes storm-plot.txt
beside it. No maps, no invented positions, no IR gif download.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

_DB = Path(os.environ.get(
    "RR_DATABASE_ROOT",
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
))
BOARD_DIR: Path | None = None
HAWAII_THREAT_NM = 800
HAWAII = {
    "Honolulu": (21.3069, -157.8583),
    "Hilo": (19.7297, -155.0900),
    "Līhuʻe": (21.9811, -159.3711),
    "Kona": (19.6390, -155.9969),
}


def board_dir() -> Path:
    if BOARD_DIR is not None:
        return BOARD_DIR
    return _DB / "Weather" / "Hawai'i" / "hurricanes" / "global"


def load_board() -> dict[str, Any]:
    path = board_dir() / "storms-last.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _compass(deg: float) -> str:
    names = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
    idx = int((deg + 22.5) // 45) % 8
    return names[idx]


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _nearest_storm(storms: list[Any]) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_nm = 9e9
    for s in storms:
        if not isinstance(s, dict):
            continue
        nm = s.get("nearest_hawaii_nm")
        try:
            nmi = float(nm) if nm is not None else None
        except (TypeError, ValueError):
            nmi = None
        if nmi is None:
            continue
        if nmi < best_nm:
            best_nm = nmi
            best = s
    return best


def _mark(compass: str) -> str:
    raw = (compass or "").strip().lower()
    aliases = {
        "n": "N",
        "north": "N",
        "ne": "NE",
        "northeast": "NE",
        "e": "E",
        "east": "E",
        "se": "SE",
        "southeast": "SE",
        "s": "S",
        "south": "S",
        "sw": "SW",
        "southwest": "SW",
        "w": "W",
        "west": "W",
        "nw": "NW",
        "northwest": "NW",
    }
    c = aliases.get(raw, raw.upper())
    n = "*" if c in {"N", "NE", "NW"} else "|"
    e = "*" if c in {"E", "NE", "SE"} else "-"
    s = "*" if c in {"S", "SE", "SW"} else "|"
    w = "*" if c in {"W", "NW", "SW"} else "-"
    return f"        N\n        {n}\n {w}------+------{e} E     + = Hawaiʻi\n        {s}\n        S"


def _closest_island(storm: dict[str, Any] | None) -> str:
    table = (storm or {}).get("hawaii_nm")
    if not isinstance(table, dict) or not table:
        return "Līhuʻe"
    try:
        return min(table.items(), key=lambda kv: float(kv[1] if kv[1] is not None else 9e9))[0]
    except (TypeError, ValueError):
        return "Līhuʻe"


def plot_text(board: dict[str, Any] | None = None) -> str:
    data = board if isinstance(board, dict) else load_board()
    storms = data.get("storms") if isinstance(data.get("storms"), list) else []
    near = _nearest_storm(storms)
    name = str((near or {}).get("label") or (near or {}).get("name") or "No mapped storm")
    try:
        nmi = float(near.get("nearest_hawaii_nm")) if near and near.get("nearest_hawaii_nm") is not None else None
    except (TypeError, ValueError):
        nmi = None
    island = _closest_island(near)
    compass = str((near or {}).get("bearing_from_lihue") or "")
    lat = lon = None
    if near:
        try:
            lat = float(near["lat"]) if near.get("lat") is not None else None
            lon = float(near["lon"]) if near.get("lon") is not None else None
        except (TypeError, ValueError):
            lat = lon = None
        if not compass and lat is not None and lon is not None:
            pos = HAWAII.get(island) or HAWAII["Līhuʻe"]
            compass = _compass(_bearing(pos[0], pos[1], lat, lon))
    threat = nmi is not None and nmi < HAWAII_THREAT_NM
    lines = [
        "Storm plot vs Hawaiʻi (file facts). + is the islands. History and RAMMB forecast are on-file products, not a landfall call.",
        _mark(compass),
    ]
    pos_s = ""
    if lat is not None and lon is not None:
        ns = "N" if lat >= 0 else "S"
        ew = "E" if lon >= 0 else "W"
        pos_s = f" {abs(lat):.1f}{ns} {abs(lon):.1f}{ew}."
    dist = f" {int(nmi)} nmi" if nmi is not None else " distance No data"
    lines.append(f"{name}.{pos_s}{dist} {compass} of {island}.".replace("  ", " "))
    if near and isinstance(near.get("hawaii_nm"), dict):
        bits = []
        for isle, d in sorted(near["hawaii_nm"].items(), key=lambda kv: float(kv[1] or 9e9)):
            bits.append(f"{isle} {int(float(d))} nmi")
        if bits:
            lines.append("Islands: " + "; ".join(bits) + ".")
    basin = str((near or {}).get("basin_name") or (near or {}).get("basin") or "")
    if basin:
        lines.append(f"Basin: {basin}.")
    region = str((near or {}).get("region_name") or "")
    if region:
        lines.append(f"Region: {region}.")
    move = str((near or {}).get("movement_compass") or "")
    approach = str((near or {}).get("hawaii_approach") or "")
    try:
        mkt = (near or {}).get("movement_kt")
        mkt_i = int(round(float(mkt))) if mkt is not None else None
    except (TypeError, ValueError):
        mkt_i = None
    if move:
        ktbit = f" {mkt_i} kt" if mkt_i is not None else ""
        vs = {"toward": "toward Hawaiʻi", "away": "away from Hawaiʻi", "abeam": "abeam of Hawaiʻi"}.get(approach, "vs Hawaiʻi unknown")
        lines.append(f"Motion: {move}{ktbit} — {vs}.")
    hist = (near or {}).get("track_history") if isinstance((near or {}).get("track_history"), list) else []
    if len(hist) >= 2:
        a, b = hist[0], hist[-1]
        try:
            lines.append(
                f"History: {abs(float(a['lat'])):.1f}{'N' if float(a['lat'])>=0 else 'S'} "
                f"{abs(float(a['lon'])):.1f}{'E' if float(a['lon'])>=0 else 'W'} → "
                f"{abs(float(b['lat'])):.1f}{'N' if float(b['lat'])>=0 else 'S'} "
                f"{abs(float(b['lon'])):.1f}{'E' if float(b['lon'])>=0 else 'W'} "
                f"({len(hist)} RAMMB fixes)."
            )
        except (TypeError, ValueError, KeyError):
            pass
    fc = str((near or {}).get("forecast_summary") or "")
    if fc:
        lines.append(fc)
    if threat:
        lines.append("Hawaiʻi threat: YES — inside 800 nmi.")
    else:
        lines.append(
            "Hawaiʻi threat: NO. ≥800 nmi on this board file. "
            "West of Kauaʻi is Asia/Japan, not toward the islands. Do not alarm."
        )
    return "\n".join(lines)


def write_plot(board: dict[str, Any] | None = None) -> Path:
    text = plot_text(board)
    path = board_dir() / "storm-plot.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".txt.tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def prompt_line(*, cap: int = 280, board: dict[str, Any] | None = None) -> str:
    blob = " ".join(plot_text(board).split())
    if len(blob) > cap:
        return blob[: cap - 1] + "…"
    return blob


def main() -> int:
    print(plot_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
