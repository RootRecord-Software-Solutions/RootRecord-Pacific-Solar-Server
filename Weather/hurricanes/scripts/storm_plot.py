# ==============================================================================
# FILE: Weather/hurricanes/scripts/storm_plot.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Text plot: nearest storm vs Hawaiʻi. File facts from the global board only.

Reads Weather/Hawai'i/hurricanes/global/storms-last.json and writes storm-plot.txt
beside it. No maps, no invented positions, no IR gif download.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import math  # info: import math
import os  # info: import os
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

_DB = Path(os.environ.get(  # info: set _DB
    "RR_DATABASE_ROOT",  # info: "RR_DATABASE_ROOT" ,
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database" ,
))  # info: ) )
BOARD_DIR: Path | None = None  # info: set BOARD_DIR
HAWAII_THREAT_NM = 800  # info: set HAWAII_THREAT_NM
# ====================================================
# SECTION: HAWAII
# What it does: Set HAWAII.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
HAWAII = {  # info: set HAWAII
    "Honolulu": (21.3069, -157.8583),  # info: call "Honolulu"
    "Hilo": (19.7297, -155.0900),  # info: call "Hilo"
    "Līhuʻe": (21.9811, -159.3711),  # info: call "Līhuʻe"
    "Kona": (19.6390, -155.9969),  # info: call "Kona"
}  # info: }


# ====================================================
# SECTION: function board_dir
# What it does: board dir.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def board_dir() -> Path:  # info: def board_dir
    if BOARD_DIR is not None:  # info: if BOARD_DIR is not None :
        return BOARD_DIR  # info: return BOARD_DIR
    return _DB / "Weather" / "Hawai'i" / "hurricanes" / "global"  # info: return _DB / "Weather" / "Hawai'i" / "hurricanes"


# ====================================================
# SECTION: function load_board
# What it does: load board.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_board() -> dict[str, Any]:  # info: def load_board
    path = board_dir() / "storms-last.json"  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {}  # info: return { }
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function _compass
# What it does:  compass.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _compass(deg: float) -> str:  # info: def _compass
    names = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")  # info: set names
    idx = int((deg + 22.5) // 45) % 8  # info: set idx
    return names[idx]  # info: return names [ idx ]


# ====================================================
# SECTION: function _bearing
# What it does:  bearing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:  # info: def _bearing
    p1, p2 = math.radians(lat1), math.radians(lat2)  # info: p1 , p2 = math . radians (
    dl = math.radians(lon2 - lon1)  # info: set dl
    y = math.sin(dl) * math.cos(p2)  # info: set y
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)  # info: set x
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0  # info: return ( math . degrees ( math .


# ====================================================
# SECTION: function _nearest_storm
# What it does:  nearest storm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _nearest_storm(storms: list[Any]) -> dict[str, Any] | None:  # info: def _nearest_storm
    best: dict[str, Any] | None = None  # info: set best
    best_nm = 9e9  # info: set best_nm
    for s in storms:  # info: for s in storms :
        if not isinstance(s, dict):  # info: if not isinstance ( s , dict )
            continue  # info: continue
        nm = s.get("nearest_hawaii_nm")  # info: set nm
        try:  # info: try :
            nmi = float(nm) if nm is not None else None  # info: set nmi
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            nmi = None  # info: set nmi
        if nmi is None:  # info: if nmi is None :
            continue  # info: continue
        if nmi < best_nm:  # info: if nmi < best_nm :
            best_nm = nmi  # info: set best_nm
            best = s  # info: set best
    return best  # info: return best


# ====================================================
# SECTION: function _mark
# What it does:  mark.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _mark(compass: str) -> str:  # info: def _mark
    raw = (compass or "").strip().lower()  # info: set raw
    aliases = {  # info: set aliases
        "n": "N",  # info: "n" : "N" ,
        "north": "N",  # info: "north" : "N" ,
        "ne": "NE",  # info: "ne" : "NE" ,
        "northeast": "NE",  # info: "northeast" : "NE" ,
        "e": "E",  # info: "e" : "E" ,
        "east": "E",  # info: "east" : "E" ,
        "se": "SE",  # info: "se" : "SE" ,
        "southeast": "SE",  # info: "southeast" : "SE" ,
        "s": "S",  # info: "s" : "S" ,
        "south": "S",  # info: "south" : "S" ,
        "sw": "SW",  # info: "sw" : "SW" ,
        "southwest": "SW",  # info: "southwest" : "SW" ,
        "w": "W",  # info: "w" : "W" ,
        "west": "W",  # info: "west" : "W" ,
        "nw": "NW",  # info: "nw" : "NW" ,
        "northwest": "NW",  # info: "northwest" : "NW" ,
    }  # info: }
    c = aliases.get(raw, raw.upper())  # info: set c
    n = "*" if c in {"N", "NE", "NW"} else "|"  # info: set n
    e = "*" if c in {"E", "NE", "SE"} else "-"  # info: set e
    s = "*" if c in {"S", "SE", "SW"} else "|"  # info: set s
    w = "*" if c in {"W", "NW", "SW"} else "-"  # info: set w
    return f"        N\n        {n}\n {w}------+------{e} E     + = Hawaiʻi\n        {s}\n        S"  # info: return f" N\n { n } \n {


# ====================================================
# SECTION: function _closest_island
# What it does:  closest island.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _closest_island(storm: dict[str, Any] | None) -> str:  # info: def _closest_island
    table = (storm or {}).get("hawaii_nm")  # info: set table
    if not isinstance(table, dict) or not table:  # info: if not isinstance ( table , dict )
        return "Līhuʻe"  # info: return "Līhuʻe"
    try:  # info: try :
        return min(table.items(), key=lambda kv: float(kv[1] if kv[1] is not None else 9e9))[0]  # info: return min ( table . items ( )
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return "Līhuʻe"  # info: return "Līhuʻe"


# ====================================================
# SECTION: function plot_text
# What it does: plot text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def plot_text(board: dict[str, Any] | None = None) -> str:  # info: def plot_text
    data = board if isinstance(board, dict) else load_board()  # info: set data
    storms = data.get("storms") if isinstance(data.get("storms"), list) else []  # info: set storms
    near = _nearest_storm(storms)  # info: set near
    name = str((near or {}).get("label") or (near or {}).get("name") or "No mapped storm")  # info: set name
    try:  # info: try :
        nmi = float(near.get("nearest_hawaii_nm")) if near and near.get("nearest_hawaii_nm") is not None else None  # info: set nmi
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        nmi = None  # info: set nmi
    island = _closest_island(near)  # info: set island
    compass = str((near or {}).get("bearing_from_lihue") or "")  # info: set compass
    lat = lon = None  # info: set lat
    if near:  # info: if near :
        try:  # info: try :
            lat = float(near["lat"]) if near.get("lat") is not None else None  # info: set lat
            lon = float(near["lon"]) if near.get("lon") is not None else None  # info: set lon
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            lat = lon = None  # info: set lat
        if not compass and lat is not None and lon is not None:  # info: if not compass and lat is not None
            pos = HAWAII.get(island) or HAWAII["Līhuʻe"]  # info: set pos
            compass = _compass(_bearing(pos[0], pos[1], lat, lon))  # info: set compass
    threat = nmi is not None and nmi < HAWAII_THREAT_NM  # info: set threat
    lines = [  # info: set lines
        "Storm plot vs Hawaiʻi (file facts). + is the islands. History and RAMMB forecast are on-file products, not a landfall call.",  # info: "Storm plot vs Hawaiʻi (file facts). + is the islands. History and RAMMB forecast are on-file products, not a 
        _mark(compass),  # info: call _mark
    ]  # info: ]
    pos_s = ""  # info: set pos_s
    if lat is not None and lon is not None:  # info: if lat is not None and lon is
        ns = "N" if lat >= 0 else "S"  # info: set ns
        ew = "E" if lon >= 0 else "W"  # info: set ew
        pos_s = f" {abs(lat):.1f}{ns} {abs(lon):.1f}{ew}."  # info: set pos_s
    dist = f" {int(nmi)} nmi" if nmi is not None else " distance No data"  # info: set dist
    lines.append(f"{name}.{pos_s}{dist} {compass} of {island}.".replace("  ", " "))  # info: lines . append ( f" { name }
    if near and isinstance(near.get("hawaii_nm"), dict):  # info: if near and isinstance ( near . get
        bits = []  # info: set bits
        for isle, d in sorted(near["hawaii_nm"].items(), key=lambda kv: float(kv[1] or 9e9)):  # info: for isle , d in sorted ( near
            bits.append(f"{isle} {int(float(d))} nmi")  # info: bits . append ( f" { isle }
        if bits:  # info: if bits :
            lines.append("Islands: " + "; ".join(bits) + ".")  # info: lines . append ( "Islands: " + "; " .
    basin = str((near or {}).get("basin_name") or (near or {}).get("basin") or "")  # info: set basin
    if basin:  # info: if basin :
        lines.append(f"Basin: {basin}.")  # info: lines . append ( f" Basin: { basin
    region = str((near or {}).get("region_name") or "")  # info: set region
    if region:  # info: if region :
        lines.append(f"Region: {region}.")  # info: lines . append ( f" Region: { region
    move = str((near or {}).get("movement_compass") or "")  # info: set move
    approach = str((near or {}).get("hawaii_approach") or "")  # info: set approach
    try:  # info: try :
        mkt = (near or {}).get("movement_kt")  # info: set mkt
        mkt_i = int(round(float(mkt))) if mkt is not None else None  # info: set mkt_i
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        mkt_i = None  # info: set mkt_i
    if move:  # info: if move :
        ktbit = f" {mkt_i} kt" if mkt_i is not None else ""  # info: set ktbit
        vs = {"toward": "toward Hawaiʻi", "away": "away from Hawaiʻi", "abeam": "abeam of Hawaiʻi"}.get(approach, "vs Hawaiʻi unknown")  # info: set vs
        lines.append(f"Motion: {move}{ktbit} — {vs}.")  # info: lines . append ( f" Motion: { move
    hist = (near or {}).get("track_history") if isinstance((near or {}).get("track_history"), list) else []  # info: set hist
    if len(hist) >= 2:  # info: if len ( hist ) >= 2 :
        a, b = hist[0], hist[-1]  # info: a , b = hist [ 0 ]
        try:  # info: try :
            lines.append(  # info: lines . append (
                f"History: {abs(float(a['lat'])):.1f}{'N' if float(a['lat'])>=0 else 'S'} "  # info: f" History: { abs ( float ( a
                f"{abs(float(a['lon'])):.1f}{'E' if float(a['lon'])>=0 else 'W'} → "  # info: f" { abs ( float ( a [
                f"{abs(float(b['lat'])):.1f}{'N' if float(b['lat'])>=0 else 'S'} "  # info: f" { abs ( float ( b [
                f"{abs(float(b['lon'])):.1f}{'E' if float(b['lon'])>=0 else 'W'} "  # info: f" { abs ( float ( b [
                f"({len(hist)} RAMMB fixes)."  # info: call f"
            )  # info: )
        except (TypeError, ValueError, KeyError):  # info: except ( TypeError , ValueError , KeyError )
            pass  # info: pass
    fc = str((near or {}).get("forecast_summary") or "")  # info: set fc
    if fc:  # info: if fc :
        lines.append(fc)  # info: lines . append ( fc )
    if threat:  # info: if threat :
        lines.append("Hawaiʻi threat: YES — inside 800 nmi.")  # info: lines . append ( "Hawaiʻi threat: YES — inside 800 nmi." )
    else:  # info: else :
        lines.append(  # info: lines . append (
            "Hawaiʻi threat: NO. ≥800 nmi on this board file. "  # info: "Hawaiʻi threat: NO. ≥800 nmi on this board file. "
            "West of Kauaʻi is Asia/Japan, not toward the islands. Do not alarm."  # info: "West of Kauaʻi is Asia/Japan, not toward the islands. Do not alarm."
        )  # info: )
    return "\n".join(lines)  # info: return "\n" . join ( lines )


# ====================================================
# SECTION: function write_plot
# What it does: write plot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_plot(board: dict[str, Any] | None = None) -> Path:  # info: def write_plot
    text = plot_text(board)  # info: set text
    path = board_dir() / "storm-plot.txt"  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(".txt.tmp")  # info: set tmp
    tmp.write_text(text + "\n", encoding="utf-8")  # info: tmp . write_text ( text + "\n" ,
    os.replace(tmp, path)  # info: os . replace ( tmp , path )
    return path  # info: return path


# ====================================================
# SECTION: function prompt_line
# What it does: prompt line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def prompt_line(*, cap: int = 280, board: dict[str, Any] | None = None) -> str:  # info: def prompt_line
    blob = " ".join(plot_text(board).split())  # info: set blob
    if len(blob) > cap:  # info: if len ( blob ) > cap :
        return blob[: cap - 1] + "…"  # info: return blob [ : cap - 1 ]
    return blob  # info: return blob


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    print(plot_text())  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
