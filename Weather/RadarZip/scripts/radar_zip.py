# ==============================================================================
# FILE: Weather/RadarZip/scripts/radar_zip.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Append Hawaii radar frames the live poller already saved into one all-time zip.

Does not fetch. Does not delete dated folders. Does not rewrite the zip in memory.
A second run adds nothing when every frame name is already a zip member.

  python3 radar_zip.py
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import zipfile  # info: import zipfile
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
LIVE_ARCHIVE = (  # info: set LIVE_ARCHIVE
    DB / "Weather" / "Hawai'i" / "hfo" / "radar.weather.gov" / "ridge" / "standard" / "HAWAII_loop" / "archive"  # info: DB / "Weather" / "Hawai'i" / "hfo" /
)  # info: )
PREVIOUS = DB / "Archive" / "Previous-Datasets"  # info: set PREVIOUS
OUT = DB / "Weather" / "RadarZip"  # info: set OUT
ZIP_PATH = OUT / "radar_archive.zip"  # info: set ZIP_PATH
STATE_PATH = OUT / "radar-archive.json"  # info: set STATE_PATH
LOG_DIR = DB / "Logs" / "Weather" / "RadarZip"  # info: set LOG_DIR
LOG_PATH = LOG_DIR / "radar_zip.log"  # info: set LOG_PATH


# ====================================================
# SECTION: function _gif_files
# What it does: Live dated archive first, then retention copies. One path per filename.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _gif_files() -> list[Path]:  # info: def _gif_files
    """Live dated archive first, then retention copies. One path per filename."""  # info: """Live dated archive first, then retention copies. One path per filename."""
    found: dict[str, Path] = {}  # info: set found

    def take(path: Path) -> None:  # info: def take
        if not path.is_file() or path.suffix.lower() != ".gif":  # info: if not path . is_file ( ) or
            return  # info: return
        found.setdefault(path.name, path)  # info: found . setdefault ( path . name ,

    if LIVE_ARCHIVE.is_dir():  # info: if LIVE_ARCHIVE . is_dir ( ) :
        for path in sorted(LIVE_ARCHIVE.rglob("*.gif")):  # info: for path in sorted ( LIVE_ARCHIVE . rglob
            take(path)  # info: call take

    if PREVIOUS.is_dir():  # info: if PREVIOUS . is_dir ( ) :
        for root in sorted(PREVIOUS.glob("Weather-*")):  # info: for root in sorted ( PREVIOUS . glob
            if not root.is_dir():  # info: if not root . is_dir ( ) :
                continue  # info: continue
            for path in sorted(root.rglob("HAWAII_loop_*.gif")):  # info: for path in sorted ( root . rglob
                rel = str(path)  # info: set rel
                if "radar.weather.gov" in rel or "HAWAII_loop" in rel:  # info: if "radar.weather.gov" in rel or "HAWAII_loop" in rel
                    take(path)  # info: call take

    return [found[name] for name in sorted(found)]  # info: return [ found [ name ] for name


# ====================================================
# SECTION: function _existing_names
# What it does:  existing names.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _existing_names(zip_path: Path) -> set[str]:  # info: def _existing_names
    if not zip_path.is_file():  # info: if not zip_path . is_file ( ) :
        return set()  # info: return set ( )
    with zipfile.ZipFile(zip_path, "r") as archive:  # info: with zipfile . ZipFile ( zip_path , "r"
        return set(archive.namelist())  # info: return set ( archive . namelist ( )


# ====================================================
# SECTION: function append_frames
# What it does: append frames.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def append_frames() -> dict:  # info: def append_frames
    OUT.mkdir(parents=True, exist_ok=True)  # info: OUT . mkdir ( parents = True ,
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    frames = _gif_files()  # info: set frames
    already = _existing_names(ZIP_PATH)  # info: set already
    added: list[str] = []  # info: set added
    pending = [(path, path.name) for path in frames if path.name not in already]  # info: set pending
    if pending:  # info: if pending :
        with zipfile.ZipFile(ZIP_PATH, "a", compression=zipfile.ZIP_DEFLATED) as archive:  # info: with zipfile . ZipFile ( ZIP_PATH , "a"
            for path, name in pending:  # info: for path , name in pending :
                archive.write(path, arcname=name)  # info: archive . write ( path , arcname =
                added.append(name)  # info: added . append ( name )
        already = _existing_names(ZIP_PATH)  # info: set already

    payload = {  # info: set payload
        "ok": True,  # info: "ok" : True ,
        "zip": str(ZIP_PATH),  # info: "zip" : str ( ZIP_PATH ) ,
        "member_count": len(already),  # info: "member_count" : len ( already ) ,
        "added_count": len(added),  # info: "added_count" : len ( added ) ,
        "added": added,  # info: "added" : added ,
        "frame_count": len(frames),  # info: "frame_count" : len ( frames ) ,
        "live_archive": str(LIVE_ARCHIVE),  # info: "live_archive" : str ( LIVE_ARCHIVE ) ,
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "updated_at" : datetime . now ( HST )
    }  # info: }
    tmp = STATE_PATH.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, STATE_PATH)  # info: os . replace ( tmp , STATE_PATH )
    with LOG_PATH.open("a", encoding="utf-8") as log:  # info: with LOG_PATH . open ( "a" , encoding
        log.write(  # info: log . write (
            f"{payload['updated_at']} added={payload['added_count']} members={payload['member_count']}\n"  # info: f" { payload [ 'updated_at' ] } added=
        )  # info: )
    return payload  # info: return payload


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    payload = append_frames()  # info: set payload
    print(json.dumps(payload))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
