# ==============================================================================
# FILE: Automations/scripts/service_notice.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Planned service windows published with the public website.

The file is Website/Home/service-notice.json. The website mirror publishes that
folder. This module does not restart the poller, send mail, or spend money.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import urllib.request  # info: import urllib . request
import uuid  # info: import uuid
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
SOON = timedelta(hours=24)  # info: set SOON
STATE_URL = "https://api.rootrecord.cloud/api/state"  # info: set STATE_URL
NOTE_LIMIT = 160  # info: set NOTE_LIMIT


# ====================================================
# SECTION: function notice_path
# What it does: Public service-notice file. Tests set RR_SERVICE_NOTICE. Does not create it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def notice_path() -> Path:  # info: def notice_path
    env = os.environ.get("RR_SERVICE_NOTICE")  # info: set env
    if env:  # info: if env
        return Path(env)  # info: return Path
    return ROOT / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server" / "Website" / "Home" / "service-notice.json"  # info: return ROOT


# ====================================================
# SECTION: function _as_hst
# What it does: Convert a datetime to Pacific/Honolulu.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _as_hst(now: datetime) -> datetime:  # info: def _as_hst
    if now.tzinfo is None:  # info: if now . tzinfo is None
        return now.replace(tzinfo=HST)  # info: return now . replace
    return now.astimezone(HST)  # info: return now . astimezone ( HST )


# ====================================================
# SECTION: function _iso
# What it does: Second-resolution HST timestamp for the public file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _iso(when: datetime) -> str:  # info: def _iso
    return _as_hst(when).isoformat(timespec="seconds")  # info: return _as_hst ( when ) . isoformat


# ====================================================
# SECTION: function _read
# What it does: Load the notice object. A missing or broken file is an empty window list.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read() -> dict:  # info: def _read
    path = notice_path()  # info: set path
    if not path.is_file():  # info: if not path . is_file ( )
        return {"windows": []}  # info: return { "windows" : [ ] }
    try:  # info: try
        doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, json.JSONDecodeError):  # info: except
        return {"windows": []}  # info: return { "windows" : [ ] }
    if not isinstance(doc, dict) or not isinstance(doc.get("windows"), list):  # info: if not isinstance ( doc , dict ) or
        return {"windows": []}  # info: return { "windows" : [ ] }
    return doc  # info: return doc


# ====================================================
# SECTION: function _write
# What it does: Atomic write of the public notice. Does not push git by itself.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write(doc: dict) -> None:  # info: def _write
    path = notice_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps({"windows": doc.get("windows") or []}, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace


# ====================================================
# SECTION: function load
# What it does: Public windows. Does not call the network.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load() -> dict:  # info: def load
    return _read()  # info: return _read ( )


# ====================================================
# SECTION: function _num
# What it does: A finite number, or None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _num(value):  # info: def _num
    if isinstance(value, bool) or not isinstance(value, (int, float)):  # info: if isinstance ( value , bool ) or
        return None  # info: return None
    return int(value) if float(value).is_integer() else round(float(value), 1)  # info: return int ( value ) if


# ====================================================
# SECTION: function _fetch_state
# What it does: Read the public network state. Raises on failure. Does not print the body.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fetch_state() -> dict:  # info: def _fetch_state
    req = urllib.request.Request(STATE_URL, headers={"Accept": "application/json"})  # info: set req
    with urllib.request.urlopen(req, timeout=4) as resp:  # info: with urllib . request . urlopen
        payload = json.loads(resp.read().decode("utf-8"))  # info: set payload
    if not isinstance(payload, dict):  # info: if not isinstance ( payload , dict )
        raise ValueError("state")  # info: raise ValueError
    return payload  # info: return payload


# ====================================================
# SECTION: function capture_last_known
# What it does: Snapshot the four public network counts. A failed read still returns the time with empty counts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def capture_last_known(fetch=None, now: datetime | None = None) -> dict:  # info: def capture_last_known
    now = _as_hst(now or datetime.now(HST))  # info: set now
    known = {"at": _iso(now), "hawaii": None, "mainland": None, "flows": None, "endpoints": None}  # info: set known
    try:  # info: try
        payload = fetch() if fetch is not None else _fetch_state()  # info: set payload
    except Exception:  # info: except Exception
        return known  # info: return known
    stats = payload.get("stats") if isinstance(payload, dict) else None  # info: set stats
    if not isinstance(stats, dict):  # info: if not isinstance ( stats , dict )
        return known  # info: return known
    known["hawaii"] = _num(stats.get("hawaiiActiveFlows"))  # info: known [ "hawaii" ] = _num
    known["mainland"] = _num(stats.get("localActiveFlows"))  # info: known [ "mainland" ] = _num
    known["flows"] = _num(stats.get("activeFlows"))  # info: known [ "flows" ] = _num
    known["endpoints"] = _num(stats.get("endpoints"))  # info: known [ "endpoints" ] = _num
    return known  # info: return known


# ====================================================
# SECTION: function parse_when
# What it does: Build an HST datetime from a date and a clock. Returns None when the pieces are invalid.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_when(date_text: str, hour: int, minute: int) -> datetime | None:  # info: def parse_when
    try:  # info: try
        day = datetime.strptime(str(date_text).strip(), "%Y-%m-%d")  # info: set day
        hour_n, minute_n = int(hour), int(minute)  # info: hour_n , minute_n = int
    except (TypeError, ValueError):  # info: except
        return None  # info: return None
    if not (0 <= hour_n <= 23 and 0 <= minute_n <= 59):  # info: if not
        return None  # info: return None
    return datetime(day.year, day.month, day.day, hour_n, minute_n, tzinfo=HST)  # info: return datetime


# ====================================================
# SECTION: function clean_note
# What it does: One public sentence. Empty is allowed. Too long is an error string.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_note(note: str) -> tuple[str, str]:  # info: def clean_note
    text = " ".join(str(note or "").replace("\n", " ").split())  # info: set text
    if len(text) > NOTE_LIMIT:  # info: if len ( text ) > NOTE_LIMIT
        return "", "Note must be 160 characters or less."  # info: return "" , "Note must be 160 characters or less."
    return text, ""  # info: return text , ""


# ====================================================
# SECTION: function validate_window
# What it does: Check a down time and an up time. Returns an error string, or empty when the window can be stored.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def validate_window(down: datetime, up: datetime, now: datetime | None = None) -> str:  # info: def validate_window
    now = _as_hst(now or datetime.now(HST))  # info: set now
    down, up = _as_hst(down), _as_hst(up)  # info: down , up = _as_hst
    if up <= down:  # info: if up <= down
        return "The return time has to be after the down time."  # info: return "The return time has to be after the down time."
    if up <= now:  # info: if up <= now
        return "That window has already ended."  # info: return "That window has already ended."
    return ""  # info: return ""


# ====================================================
# SECTION: function phase
# What it does: upcoming, down, or ended for one window. Disabled windows are off.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def phase(item: dict, now: datetime | None = None) -> str:  # info: def phase
    if not item.get("enabled", True):  # info: if not item . get ( "enabled" , True )
        return "off"  # info: return "off"
    now = _as_hst(now or datetime.now(HST))  # info: set now
    try:  # info: try
        down = datetime.fromisoformat(str(item.get("down_at")))  # info: set down
        up = datetime.fromisoformat(str(item.get("up_at")))  # info: set up
    except ValueError:  # info: except ValueError
        return "off"  # info: return "off"
    down, up = _as_hst(down), _as_hst(up)  # info: down , up = _as_hst
    if now >= up:  # info: if now >= up
        return "ended"  # info: return "ended"
    if now >= down:  # info: if now >= down
        return "down"  # info: return "down"
    return "upcoming"  # info: return "upcoming"


# ====================================================
# SECTION: function current_window
# What it does: The window the public page should show. An active outage wins. An upcoming one shows only inside 24 hours.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def current_window(doc: dict | None = None, now: datetime | None = None) -> dict | None:  # info: def current_window
    now = _as_hst(now or datetime.now(HST))  # info: set now
    doc = load() if doc is None else doc  # info: set doc
    chosen = None  # info: set chosen
    chosen_up = None  # info: set chosen_up
    for item in doc.get("windows") or []:  # info: for item in doc . get ( "windows" ) or [ ]
        if not isinstance(item, dict):  # info: if not isinstance ( item , dict )
            continue  # info: continue
        kind = phase(item, now)  # info: set kind
        if kind == "upcoming":  # info: if kind == "upcoming"
            down = _as_hst(datetime.fromisoformat(str(item["down_at"])))  # info: set down
            if down - now > SOON:  # info: if down - now > SOON
                continue  # info: continue
        elif kind != "down":  # info: elif kind != "down"
            continue  # info: continue
        up = _as_hst(datetime.fromisoformat(str(item["up_at"])))  # info: set up
        chosen_kind = phase(chosen, now) if chosen is not None else ""  # info: set chosen_kind
        take = chosen is None or (kind == "down" and chosen_kind != "down")  # info: set take
        if not take and kind == chosen_kind and chosen_up is not None and up < chosen_up:  # info: if not take and kind == chosen_kind and
            take = True  # info: set take
        if take:  # info: if take
            chosen, chosen_up = item, up  # info: chosen , chosen_up = item , up
    return chosen  # info: return chosen


# ====================================================
# SECTION: function add_window
# What it does: Store one service window and a last-known network snapshot. Does not run a radio command.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_window(down: datetime, up: datetime, note: str = "", fetch=None, now: datetime | None = None) -> dict:  # info: def add_window
    now = _as_hst(now or datetime.now(HST))  # info: set now
    err = validate_window(down, up, now)  # info: set err
    if err:  # info: if err
        raise ValueError(err)  # info: raise ValueError
    text, note_err = clean_note(note)  # info: text , note_err = clean_note
    if note_err:  # info: if note_err
        raise ValueError(note_err)  # info: raise ValueError
    item = {  # info: set item
        "id": "tw-" + uuid.uuid4().hex[:8],  # info: "id"
        "enabled": True,  # info: "enabled"
        "down_at": _iso(down),  # info: "down_at"
        "up_at": _iso(up),  # info: "up_at"
        "note": text,  # info: "note"
        "frozen": phase({"enabled": True, "down_at": _iso(down), "up_at": _iso(up)}, now) == "down",  # info: "frozen"
        "last_known": capture_last_known(fetch=fetch, now=now),  # info: "last_known"
    }  # info: }
    doc = _read()  # info: set doc
    doc["windows"].append(item)  # info: doc [ "windows" ] . append
    _write(doc)  # info: call _write
    return item  # info: return item


# ====================================================
# SECTION: function delete_window
# What it does: Remove one window from the public file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def delete_window(item_id: str) -> bool:  # info: def delete_window
    doc = _read()  # info: set doc
    keep = [it for it in doc["windows"] if not (isinstance(it, dict) and it.get("id") == item_id)]  # info: set keep
    if len(keep) == len(doc["windows"]):  # info: if len ( keep ) == len
        return False  # info: return False
    doc["windows"] = keep  # info: doc [ "windows" ] = keep
    _write(doc)  # info: call _write
    return True  # info: return True


# ====================================================
# SECTION: function refresh_last_known
# What it does: Replace one window's network snapshot from the public feed. Does not change the clock times.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refresh_last_known(item_id: str, fetch=None, now: datetime | None = None) -> bool:  # info: def refresh_last_known
    now = _as_hst(now or datetime.now(HST))  # info: set now
    doc = _read()  # info: set doc
    found = False  # info: set found
    for item in doc["windows"]:  # info: for item in doc [ "windows" ]
        if not isinstance(item, dict) or item.get("id") != item_id:  # info: if not isinstance ( item , dict ) or
            continue  # info: continue
        item["last_known"] = capture_last_known(fetch=fetch, now=now)  # info: item [ "last_known" ] = capture_last_known
        if phase(item, now) == "down":  # info: if phase ( item , now ) == "down"
            item["frozen"] = True  # info: item [ "frozen" ] = True
        found = True  # info: set found
        break  # info: break
    if found:  # info: if found
        _write(doc)  # info: call _write
    return found  # info: return found


# ====================================================
# SECTION: function needs_freeze
# What it does: True when an active window still needs the one snapshot taken as the outage starts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def needs_freeze(now: datetime | None = None) -> bool:  # info: def needs_freeze
    now = _as_hst(now or datetime.now(HST))  # info: set now
    for item in _read().get("windows") or []:  # info: for item in _read ( ) . get ( "windows" ) or [ ]
        if isinstance(item, dict) and phase(item, now) == "down" and not item.get("frozen"):  # info: if isinstance ( item , dict ) and
            return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function freeze_due
# What it does: Take one last-known snapshot for windows that just became active, then stop retrying them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def freeze_due(now: datetime | None = None, fetch=None) -> list[str]:  # info: def freeze_due
    now = _as_hst(now or datetime.now(HST))  # info: set now
    doc = _read()  # info: set doc
    frozen_ids = []  # info: set frozen_ids
    known = None  # info: set known
    for item in doc["windows"]:  # info: for item in doc [ "windows" ]
        if not isinstance(item, dict) or phase(item, now) != "down" or item.get("frozen"):  # info: if not isinstance ( item , dict ) or
            continue  # info: continue
        if known is None:  # info: if known is None
            known = capture_last_known(fetch=fetch, now=now)  # info: set known
        if any(known.get(key) is not None for key in ("hawaii", "mainland", "flows", "endpoints")):  # info: if any
            item["last_known"] = known  # info: item [ "last_known" ] = known
        item["frozen"] = True  # info: item [ "frozen" ] = True
        frozen_ids.append(str(item.get("id")))  # info: frozen_ids . append
    if frozen_ids:  # info: if frozen_ids
        _write(doc)  # info: call _write
    return frozen_ids  # info: return frozen_ids
