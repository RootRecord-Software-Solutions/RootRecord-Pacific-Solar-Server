# ==============================================================================
# FILE: Apps/Control-Panel/Lib/rr_schedule.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Schedule JSON load/save for Root Monitor. Never starts a poller."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import secrets  # info: import secrets
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
SERVERS = ("pacific", "ml1", "ml2")  # info: set SERVERS

# Category tabs inside each server.
# mode: all | sections | every_x
# sections=None with mode all/every_x; frozenset of catalog sections for mode sections.
CATEGORY_TABS: tuple[tuple[str, str, str, frozenset[str] | None], ...] = (  # info: set CATEGORY_TABS
    ("all", "All", "all", None),  # info: all
    ("boot", "Boot order", "sections", frozenset({"ON_BOOT", "SERVICE"})),  # info: boot
    ("once", "Once at start", "sections", frozenset({"ONCE_AT_START", "ENERGY"})),  # info: once + per-device reads
    ("exact", "Hourly sequence", "sections", frozenset({"EXACT_TIME"})),  # info: exact
    ("timer", "Timers", "sections", frozenset({"TIMER"})),  # info: timer
    ("energy", "Energy reads", "sections", frozenset({"ENERGY"})),  # info: energy
    ("power", "Power actions", "sections", frozenset({"POWER"})),  # info: power
    ("builtin", "Builtins", "sections", frozenset({"BUILTIN"})),  # info: builtin
    ("collector", "Collectors", "sections", frozenset({"COLLECTOR"})),  # info: collector
)  # info: )


# ====================================================
# SECTION: function schedules_root
# What it does: Database control-panel/schedules directory.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def schedules_root(database_root: str | Path) -> Path:  # info: def schedules_root
    return Path(database_root) / "System" / "control-panel" / "schedules"  # info: return


# ====================================================
# SECTION: function disconnect_path
# What it does: Global polling-disconnected flag path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def disconnect_path(database_root: str | Path) -> Path:  # info: def disconnect_path
    return Path(database_root) / "System" / "control-panel" / "polling-disconnected.json"  # info: return


# ====================================================
# SECTION: function _read
# What it does: Read a JSON object or return fallback.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read(path: Path, fallback: dict) -> dict:  # info: def _read
    try:  # info: try
        doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, json.JSONDecodeError):  # info: except
        return dict(fallback)  # info: return dict ( fallback )
    return doc if isinstance(doc, dict) else dict(fallback)  # info: return


# ====================================================
# SECTION: function _write
# What it does: Atomic JSON write. Does not start services.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(path: Path, doc: dict) -> None:  # info: def _write
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  # info: tmp . write_text
    tmp.replace(path)  # info: tmp . replace ( path )


# ====================================================
# SECTION: function load_disconnect
# What it does: Load the global disconnect flag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_disconnect(database_root: str | Path) -> dict:  # info: def load_disconnect
    return _read(disconnect_path(database_root), {"polling_disconnected": True, "armed": False})  # info: return


# ====================================================
# SECTION: function save_disconnect
# What it does: Write the global disconnect flag. Never starts a poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_disconnect(database_root: str | Path, disconnected: bool = True, armed: bool = False) -> None:  # info: def save_disconnect
    doc = {  # info: set doc
        "polling_disconnected": bool(disconnected),  # info: "polling_disconnected"
        "armed": bool(armed),  # info: "armed"
        "updated_at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "updated_at"
        "note": "Root Monitor schedule editor. Do not start pollers while disconnected.",  # info: "note"
    }  # info: }
    _write(disconnect_path(database_root), doc)  # info: call _write


# ====================================================
# SECTION: function load_catalog
# What it does: Load one server catalog.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_catalog(database_root: str | Path, server: str) -> dict:  # info: def load_catalog
    path = schedules_root(database_root) / f"catalog-{server}.json"  # info: set path
    return _read(path, {"version": 1, "server": server, "functions": []})  # info: return


# ====================================================
# SECTION: function load_schedule
# What it does: Load one server schedule.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_schedule(database_root: str | Path, server: str) -> dict:  # info: def load_schedule
    path = schedules_root(database_root) / f"{server}.json"  # info: set path
    return _read(path, {"version": 1, "server": server, "armed": False, "polling_disconnected": True, "entries": []})  # info: return


# ====================================================
# SECTION: function save_schedule
# What it does: Write one server schedule. Keeps polling disconnected unless explicitly armed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_schedule(database_root: str | Path, server: str, doc: dict) -> Path:  # info: def save_schedule
    out = dict(doc)  # info: set out
    out["version"] = 1  # info: out [ "version" ] = 1
    out["server"] = server  # info: out [ "server" ] = server
    out["updated_at"] = datetime.now(HST).isoformat(timespec="seconds")  # info: out [ "updated_at" ]
    # Desk rebuild rule: Save does not arm or reconnect polling.
    out["armed"] = False  # info: out [ "armed" ] = False
    out["polling_disconnected"] = True  # info: out [ "polling_disconnected" ] = True
    path = schedules_root(database_root) / f"{server}.json"  # info: set path
    _write(path, out)  # info: call _write
    save_disconnect(database_root, disconnected=True, armed=False)  # info: keep global flag off
    return path  # info: return path


# ====================================================
# SECTION: function new_entry_id
# What it does: Fresh entry id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def new_entry_id() -> str:  # info: def new_entry_id
    return "e_" + secrets.token_hex(6)  # info: return "e_" + secrets . token_hex ( 6 )


# ====================================================
# SECTION: function make_entry
# What it does: Build one placement dict.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def make_entry(  # info: def make_entry
    function_id: str,  # info: function_id
    *,  # info: *
    minute: int | None = 0,  # info: minute
    second: int = 0,  # info: second
    hour: int | None = None,  # info: hour
    every_seconds: int | None = None,  # info: every_seconds
    phase: str | None = None,  # info: phase
    enabled: bool = False,  # info: enabled
    copy_of: str | None = None,  # info: copy_of
    label: str = "",  # info: label
) -> dict:  # info: ) -> dict
    phase_name = (phase or "").strip() or None  # info: set phase_name
    if phase_name:  # info: boot / once_at_start placements have no clock fields
        return {  # info: return {
            "id": new_entry_id(),  # info: "id"
            "function_id": function_id,  # info: "function_id"
            "enabled": bool(enabled),  # info: "enabled"
            "hour": None,  # info: "hour"
            "minute": None,  # info: "minute"
            "second": None,  # info: "second"
            "every_seconds": None,  # info: "every_seconds"
            "phase": phase_name,  # info: "phase"
            "copy_of": copy_of,  # info: "copy_of"
            "label": label or "",  # info: "label"
        }  # info: }
    return {  # info: return {
        "id": new_entry_id(),  # info: "id"
        "function_id": function_id,  # info: "function_id"
        "enabled": bool(enabled),  # info: "enabled"
        "hour": hour,  # info: "hour"
        "minute": minute,  # info: "minute"
        "second": None if every_seconds is not None else int(second),  # info: "second"
        "every_seconds": every_seconds,  # info: "every_seconds"
        "phase": None,  # info: "phase"
        "copy_of": copy_of,  # info: "copy_of"
        "label": label or "",  # info: "label"
    }  # info: }


# ====================================================
# SECTION: function copy_entry
# What it does: Duplicate one entry onto a new minute/second.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def copy_entry(entry: dict, *, minute: int | None = None, second: int | None = None, hour: int | None = None) -> dict:  # info: def copy_entry
    out = dict(entry)  # info: set out
    out["id"] = new_entry_id()  # info: out [ "id" ]
    out["copy_of"] = entry.get("id")  # info: out [ "copy_of" ]
    if minute is not None:  # info: if minute is not None :
        out["minute"] = int(minute)  # info: out [ "minute" ]
    if second is not None:  # info: if second is not None :
        out["second"] = int(second)  # info: out [ "second" ]
    if hour is not None:  # info: if hour is not None :
        out["hour"] = hour  # info: out [ "hour" ]
    out["enabled"] = False  # info: stay quiet until Alexander arms
    return out  # info: return out


# ====================================================
# SECTION: function entry_label
# What it does: Short display string for one placement.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def entry_label(entry: dict) -> str:  # info: def entry_label
    fid = entry.get("function_id") or "?"  # info: set fid
    if entry.get("every_seconds") is not None:  # info: if every_seconds
        return f"{fid}  every {entry['every_seconds']}s"  # info: return
    if entry.get("phase"):  # info: if phase
        return f"{fid}  [{entry['phase']}]"  # info: return
    hour = entry.get("hour")  # info: set hour
    minute = entry.get("minute")  # info: set minute
    second = entry.get("second")  # info: set second
    hh = "**" if hour is None else f"{int(hour):02d}"  # info: set hh
    mm = "??" if minute is None else f"{int(minute):02d}"  # info: set mm
    ss = "00" if second is None else f"{int(second):02d}"  # info: set ss
    mark = "" if entry.get("enabled") else " [off]"  # info: set mark
    return f"{fid}  {hh}:{mm}:{ss}{mark}"  # info: return
