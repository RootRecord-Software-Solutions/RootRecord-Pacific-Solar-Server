# ==============================================================================
# FILE: Automations/scripts/automation_control.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Desk automations the Root Monitor page and the poller share.

Job on/off flags live in automation-overrides.json. Power schedules live in
power-automations.json. The poller reads both. This module does not restart
the poller and does not send mail or spend money. It runs an EcoFlow action
script only when run_due is called for a schedule that is due.
"""
from __future__ import annotations  # info: from __future__ import annotations

import fcntl  # info: import fcntl
import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import uuid  # info: import uuid
from contextlib import contextmanager  # info: from contextlib import contextmanager
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
RETRY_MINUTES = 15  # info: set RETRY_MINUTES
SECTIONS = (  # info: set SECTIONS
    ("ON_BOOT", "On boot"),  # info: call (
    ("ONCE_AT_START", "Once at start"),  # info: call (
    ("EXACT_TIME", "Hourly process sequence"),  # info: call (
)  # info: )
DEVICES = (("delta2", "Delta 2"), ("river2pro", "River 2 Pro"))  # info: set DEVICES
# device, function id, label, script file. Only these scripts may run.
POWER_FUNCTIONS = (  # info: set POWER_FUNCTIONS
    ("delta2", "ac-off", "AC output off", "delta2-ac-off.sh"),  # info: call (
    ("delta2", "ac-on", "AC output on", "delta2-ac-on.sh"),  # info: call (
    ("delta2", "dc-off", "DC output off", "delta2-dc-off.sh"),  # info: call (
    ("delta2", "dc-on", "DC output on", "delta2-dc-on.sh"),  # info: call (
    ("delta2", "usb-off", "USB output off", "delta2-usb-off.sh"),  # info: call (
    ("delta2", "usb-on", "USB output on", "delta2-usb-on.sh"),  # info: call (
    ("delta2", "ac-charging-off", "AC charging off", "delta2-ac-charging-off.sh"),  # info: call (
    ("delta2", "ac-charging-on", "AC charging on", "delta2-ac-charging-on.sh"),  # info: call (
    ("delta2", "energy-backup-off", "Energy backup off", "delta2-energy-backup-off.sh"),  # info: call (
    ("delta2", "energy-backup-on", "Energy backup on", "delta2-energy-backup-on.sh"),  # info: call (
    ("delta2", "grid-bypass-off", "Grid bypass off", "delta2-grid-bypass-off.sh"),  # info: call (
    ("delta2", "grid-bypass-on", "Grid bypass on", "delta2-grid-bypass-on.sh"),  # info: call (
    ("river2pro", "ac-off", "AC output off", "river2pro-ac-off.sh"),  # info: call (
    ("river2pro", "ac-on", "AC output on", "river2pro-ac-on.sh"),  # info: call (
    ("river2pro", "dc-off", "DC 12V off", "river2pro-dc-off.sh"),  # info: call (
    ("river2pro", "dc-on", "DC 12V on", "river2pro-dc-on.sh"),  # info: call (
    ("river2pro", "xboost-off", "X-Boost off", "river2pro-xboost-off.sh"),  # info: call (
    ("river2pro", "xboost-on", "X-Boost on", "river2pro-xboost-on.sh"),  # info: call (
    ("river2pro", "energy-backup-off", "Energy backup off", "river2pro-energy-backup-off.sh"),  # info: call (
    ("river2pro", "energy-backup-on", "Energy backup on", "river2pro-energy-backup-on.sh"),  # info: call (
    ("river2pro", "ac-always-on-off", "AC always-on off", "river2pro-ac-always-on-off.sh"),  # info: call (
    ("river2pro", "ac-always-on-on", "AC always-on on", "river2pro-ac-always-on-on.sh"),  # info: call (
)  # info: )


# ====================================================
# SECTION: function _database_root
# What it does: Database root. Tests set RR_DATABASE_ROOT. Does not create the directory.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _database_root() -> Path:  # info: def _database_root
    return Path(os.environ.get("RR_DATABASE_ROOT", str(ROOT / "2 - RootRecord-Database")))  # info: return Path


# ====================================================
# SECTION: function overrides_path
# What it does: Path of the job on/off file. Does not create it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def overrides_path() -> Path:  # info: def overrides_path
    env = os.environ.get("RR_AUTOMATION_OVERRIDES")  # info: set env
    if env:  # info: if env
        return Path(env)  # info: return Path
    return _database_root() / "System" / "control-panel" / "automation-overrides.json"  # info: return _database_root ( )


# ====================================================
# SECTION: function power_path
# What it does: Path of the power-schedule file. Does not create it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def power_path() -> Path:  # info: def power_path
    env = os.environ.get("RR_POWER_AUTOMATIONS")  # info: set env
    if env:  # info: if env
        return Path(env)  # info: return Path
    return _database_root() / "System" / "control-panel" / "power-automations.json"  # info: return _database_root ( )


# ====================================================
# SECTION: function actions_dir
# What it does: Directory of EcoFlow action scripts. Tests may point RR_ECOFLOW_ACTIONS at a temp copy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def actions_dir() -> Path:  # info: def actions_dir
    env = os.environ.get("RR_ECOFLOW_ACTIONS")  # info: set env
    if env:  # info: if env
        return Path(env)  # info: return Path
    pacific = Path(os.environ.get(  # info: set pacific
        "RR_PACIFIC_ROOT",  # info: "RR_PACIFIC_ROOT" ,
        str(ROOT / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server"),  # info: call str
    ))  # info: )
    return pacific / "Energy" / "scripts" / "actions"  # info: return pacific / "Energy" / "scripts" / "actions"


# ====================================================
# SECTION: function _lock
# What it does: Exclusive lock beside a JSON file so the page and the poller do not tear a write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@contextmanager  # info: decorator contextmanager
def _lock(path: Path):  # info: def _lock
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    handle = path.with_suffix(path.suffix + ".lock").open("a", encoding="utf-8")  # info: set handle
    try:  # info: try
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)  # info: fcntl . flock
        yield  # info: yield
    finally:  # info: finally
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # info: fcntl . flock
        handle.close()  # info: handle . close ( )


# ====================================================
# SECTION: function _read_json
# What it does: Load a JSON object or return the fallback. A broken file is not overwritten here.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_json(path: Path, fallback: dict) -> dict:  # info: def _read_json
    if not path.is_file():  # info: if not path . is_file ( )
        return dict(fallback)  # info: return dict
    try:  # info: try
        doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, json.JSONDecodeError):  # info: except
        return dict(fallback)  # info: return dict
    return doc if isinstance(doc, dict) else dict(fallback)  # info: return doc if isinstance


# ====================================================
# SECTION: function _write_json
# What it does: Atomic JSON write. Caller holds _lock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_json(path: Path, doc: dict) -> None:  # info: def _write_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace


# ====================================================
# SECTION: function load_overrides
# What it does: Read job overrides. Missing file means no overrides.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_overrides() -> dict:  # info: def load_overrides
    doc = _read_json(overrides_path(), {"jobs": {}})  # info: set doc
    if not isinstance(doc.get("jobs"), dict):  # info: if not isinstance
        doc["jobs"] = {}  # info: doc [ "jobs" ] = { }
    return doc  # info: return doc


# ====================================================
# SECTION: function overrides_mtime
# What it does: mtime of the override file, or 0 when it is absent. The poller uses this to refresh its lists.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def overrides_mtime() -> float:  # info: def overrides_mtime
    path = overrides_path()  # info: set path
    try:  # info: try
        return path.stat().st_mtime if path.is_file() else 0.0  # info: return path . stat ( ) . st_mtime if
    except OSError:  # info: except OSError
        return 0.0  # info: return 0.0


# ====================================================
# SECTION: function job_enabled
# What it does: Whether one poller job should run. A boolean override wins over the jobs.py flag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
# Jobs gated when RR_LOCAL_DATA_POLL=0 (ML2 owns internet data fetches).
# TOGGLE only — do not delete these jobs. Flip env back to 1 (or unset) to restore local polling immediately if ML2 is down.
LOCAL_DATA_POLL_JOBS = frozenset({
    "geology_collect",
    "geology_kilauea_cams",
    "weather_poller",
    "weather_us_states",
    "weather_radar_zip",
    "weather_retention",
    "country_location_pollers",
    "discord_poller",
    # radio_rss_poll is ML1 (not ML2 LOCAL_DATA_POLL) — always uses ML1/scripts/run-radio-rss.sh
})


def local_data_poll_enabled(raw: str | None = None) -> bool:
    """True when Pacific should run internet data-poll jobs (default). False = ML2 offload.

    raw=None → read process env (poller). Root Monitor has no RR_LOCAL_DATA_POLL in its own
    environ; pass the live poller value (or drop-in) via job_enabled(..., local_data_poll=...).
    """
    if raw is None:
        raw = os.environ.get("RR_LOCAL_DATA_POLL")
    v = (str(raw) if raw is not None else "1").strip().lower()
    if v == "":
        return True
    return v not in ("0", "false", "off", "no")


def job_enabled(job: dict, overrides: dict | None = None, *, local_data_poll: bool | None = None) -> bool:  # info: def job_enabled
    jid = str(job.get("id") or "")  # info: set jid
    doc = load_overrides() if overrides is None else overrides  # info: set doc
    flags = doc.get("jobs") if isinstance(doc, dict) else None  # info: set flags
    if isinstance(flags, dict) and isinstance(flags.get(jid), bool):  # info: if isinstance ( flags , dict ) and
        return bool(flags[jid])  # info: return bool
    # Exclusive gate: when local_data_poll is False, LOCAL_DATA_POLL_JOBS stay installed but do not run.
    poll_on = local_data_poll_enabled() if local_data_poll is None else bool(local_data_poll)
    if jid in LOCAL_DATA_POLL_JOBS and not poll_on:
        return False
    return bool(job.get("enabled"))  # info: return bool ( job . get ( "enabled" ) )


# ====================================================
# SECTION: function set_job_override
# What it does: Save one job on/off flag. Drops the key when it matches the jobs.py default. Does not restart the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_job_override(job_id: str, enabled: bool, code_default: bool) -> None:  # info: def set_job_override
    if not job_id or not str(job_id).replace("_", "").isalnum():  # info: if not job_id or not str
        raise ValueError("bad job id")  # info: raise ValueError
    with _lock(overrides_path()):  # info: with _lock
        doc = load_overrides()  # info: set doc
        flags = doc["jobs"]  # info: set flags
        if bool(enabled) == bool(code_default):  # info: if bool ( enabled ) == bool
            flags.pop(str(job_id), None)  # info: flags . pop
        else:  # info: else
            flags[str(job_id)] = bool(enabled)  # info: flags [ str ( job_id ) ] = bool
        _write_json(overrides_path(), doc)  # info: call _write_json


# ====================================================
# SECTION: function schedule_text
# What it does: One short line describing when a jobs.py entry runs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def schedule_text(section: str, job: dict) -> str:  # info: def schedule_text
    if section == "ON_BOOT":  # info: if section == "ON_BOOT"
        return f"boot priority {job.get('priority', '—')}"  # info: return f
    if section == "ONCE_AT_START":  # info: if section == "ONCE_AT_START"
        return "once when the poller starts"  # info: return "once when the poller starts"
    if section == "EXACT_TIME":  # info: if section == "EXACT_TIME"
        every = job.get("every_seconds")  # info: set every
        if every:  # info: if every
            phase = int(job.get("at_second") or 0)  # info: set phase
            opened = job.get("from_minute")  # info: set opened
            extra = f" at :{phase:02d}" if phase else ""  # info: set extra
            if opened is not None:  # info: if opened is not None
                extra += f" from :{int(opened):02d}"  # info: extra += from minute
            return f"every {every}s (stacks){extra}"  # info: return f
        m = int(job.get("at_minute") or 0)  # info: set m
        s = int(job.get("at_second") or 0)  # info: set s
        if job.get("at_hour") is not None:  # info: if at_hour is set
            return f"{int(job['at_hour']):02d}:{m:02d}:{s:02d} every day"  # info: return daily clock
        return f":{m:02d}:{s:02d} every hour"  # info: return f
    return "unscheduled"  # info: return "unscheduled"


# ====================================================
# SECTION: function job_rows
# What it does: Every poller job with its effective on/off state. Does not import jobs until called.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def job_rows(jobmod) -> list[dict]:  # info: def job_rows
    overrides = load_overrides()  # info: set overrides
    rows = []  # info: set rows
    for section, title in SECTIONS:  # info: for section , title in SECTIONS
        for job in getattr(jobmod, section, []) or []:  # info: for job in getattr
            if not isinstance(job, dict) or not job.get("id"):  # info: if not isinstance ( job , dict ) or
                continue  # info: continue
            code_on = bool(job.get("enabled"))  # info: set code_on
            rows.append({  # info: rows . append
                "id": str(job["id"]),  # info: "id"
                "section": section,  # info: "section"
                "section_title": title,  # info: "section_title"
                "description": str(job.get("description") or ""),  # info: "description"
                "schedule": schedule_text(section, job),  # info: "schedule"
                "code_on": code_on,  # info: "code_on"
                "enabled": job_enabled(job, overrides),  # info: "enabled"
            })  # info: }
    return rows  # info: return rows


# ====================================================
# SECTION: function device_label
# What it does: Human name for an EcoFlow alias.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def device_label(device: str) -> str:  # info: def device_label
    for key, label in DEVICES:  # info: for key , label in DEVICES
        if key == device:  # info: if key == device
            return label  # info: return label
    return device  # info: return device


# ====================================================
# SECTION: function functions_for
# What it does: Catalog rows for one device. Does not touch the radio.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def functions_for(device: str) -> list[tuple]:  # info: def functions_for
    return [row for row in POWER_FUNCTIONS if row[0] == device]  # info: return [ row for row in POWER_FUNCTIONS if


# ====================================================
# SECTION: function function_label
# What it does: Human label for one catalog function, or the raw id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def function_label(device: str, function: str) -> str:  # info: def function_label
    for dev, fn, label, _script in POWER_FUNCTIONS:  # info: for dev , fn , label , _script in POWER_FUNCTIONS
        if dev == device and fn == function:  # info: if dev == device and fn == function
            return label  # info: return label
    return function  # info: return function


# ====================================================
# SECTION: function opposite_function
# What it does: The on/off pair of a catalog function, when one exists.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def opposite_function(device: str, function: str) -> str | None:  # info: def opposite_function
    if function.endswith("-off"):  # info: if function . endswith ( "-off" )
        other = function[:-4] + "-on"  # info: set other
    elif function.endswith("-on"):  # info: elif function . endswith ( "-on" )
        other = function[:-3] + "-off"  # info: set other
    else:  # info: else
        return None  # info: return None
    if any(dev == device and fn == other for dev, fn, _label, _script in POWER_FUNCTIONS):  # info: if any
        return other  # info: return other
    return None  # info: return None


# ====================================================
# SECTION: function script_for
# What it does: Absolute path of one catalog script. Refuses any path that is not that file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def script_for(device: str, function: str) -> Path | None:  # info: def script_for
    name = ""  # info: set name
    for dev, fn, _label, script in POWER_FUNCTIONS:  # info: for dev , fn , _label , script in POWER_FUNCTIONS
        if dev == device and fn == function:  # info: if dev == device and fn == function
            name = script  # info: set name
            break  # info: break
    if not name:  # info: if not name
        return None  # info: return None
    root = actions_dir().resolve()  # info: set root
    path = (root / name).resolve()  # info: set path
    if path.parent != root or path.name != name or not path.is_file():  # info: if path . parent != root or
        return None  # info: return None
    return path  # info: return path


# ====================================================
# SECTION: function load_power
# What it does: Read power schedules. Missing file means the master switch is on and the list is empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_power() -> dict:  # info: def load_power
    doc = _read_json(power_path(), {"master_enabled": True, "items": []})  # info: set doc
    if not isinstance(doc.get("items"), list):  # info: if not isinstance
        doc["items"] = []  # info: doc [ "items" ] = [ ]
    if not isinstance(doc.get("master_enabled"), bool):  # info: if not isinstance
        doc["master_enabled"] = True  # info: doc [ "master_enabled" ] = True
    return doc  # info: return doc


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
# SECTION: function _clock
# What it does: Hour and minute from a schedule row, or None when they are not numbers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clock(item: dict) -> tuple[int, int] | None:  # info: def _clock
    try:  # info: try
        hour, minute = int(item.get("hour")), int(item.get("minute"))  # info: hour , minute = int
    except (TypeError, ValueError):  # info: except
        return None  # info: return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):  # info: if not
        return None  # info: return None
    return hour, minute  # info: return hour , minute


# ====================================================
# SECTION: function item_due
# What it does: True when this schedule should run at `now`. A success today is not due again. Failures retry for 15 minutes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def item_due(item: dict, now: datetime, master_enabled: bool = True) -> bool:  # info: def item_due
    if not master_enabled or not item.get("enabled"):  # info: if not master_enabled or not item . get
        return False  # info: return False
    clock = _clock(item)  # info: set clock
    if clock is None:  # info: if clock is None
        return False  # info: return False
    now = _as_hst(now)  # info: set now
    repeat = item.get("repeat")  # info: set repeat
    if repeat == "once" and item.get("date") != now.date().isoformat():  # info: if repeat == "once" and
        return False  # info: return False
    if repeat not in ("once", "daily"):  # info: if repeat not in
        return False  # info: return False
    scheduled = now.replace(hour=clock[0], minute=clock[1], second=0, microsecond=0)  # info: set scheduled
    if now < scheduled or now - scheduled >= timedelta(minutes=RETRY_MINUTES):  # info: if now < scheduled or
        return False  # info: return False
    today = now.date().isoformat()  # info: set today
    if str(item.get("last_status") or "") == "ok" and str(item.get("last_fired") or "")[:10] == today:  # info: if str
        return False  # info: return False
    attempt = str(item.get("last_attempt") or "")  # info: set attempt
    if attempt[:16] == now.strftime("%Y-%m-%dT%H:%M"):  # info: if attempt [ : 16 ] == now . strftime
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function validate_spec
# What it does: Check one new power schedule. Returns an error string, or empty when it is safe to store. Does not write.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def validate_spec(spec: dict, now: datetime | None = None) -> str:  # info: def validate_spec
    device = str(spec.get("device") or "")  # info: set device
    function = str(spec.get("function") or "")  # info: set function
    if not any(dev == device and fn == function for dev, fn, _l, _s in POWER_FUNCTIONS):  # info: if not any
        return "Pick a device function from the list."  # info: return "Pick a device function from the list."
    if script_for(device, function) is None:  # info: if script_for ( device , function ) is None
        return "That action script is not on disk."  # info: return "That action script is not on disk."
    clock = _clock(spec)  # info: set clock
    if clock is None:  # info: if clock is None
        return "Hour must be 0–23 and minute 0–59."  # info: return "Hour must be 0–23 and minute 0–59."
    repeat = spec.get("repeat")  # info: set repeat
    if repeat not in ("daily", "once"):  # info: if repeat not in
        return "Repeat must be every day or once."  # info: return "Repeat must be every day or once."
    if repeat == "once":  # info: if repeat == "once"
        try:  # info: try
            day = datetime.strptime(str(spec.get("date") or ""), "%Y-%m-%d").date()  # info: set day
        except ValueError:  # info: except ValueError
            return "Once needs a date as YYYY-MM-DD."  # info: return "Once needs a date as YYYY-MM-DD."
        now = _as_hst(now or datetime.now(HST))  # info: set now
        when = datetime(day.year, day.month, day.day, clock[0], clock[1], tzinfo=HST)  # info: set when
        if when <= now:  # info: if when <= now
            return "That one-time clock time is already past."  # info: return "That one-time clock time is already past."
    name = str(spec.get("name") or "").replace("\n", " ").strip()  # info: set name
    if len(name) > 80:  # info: if len ( name ) > 80
        return "Name must be 80 characters or less."  # info: return "Name must be 80 characters or less."
    return ""  # info: return ""


# ====================================================
# SECTION: function _clean_name
# What it does: Blank names become the device, function, and clock time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clean_name(spec: dict) -> str:  # info: def _clean_name
    name = str(spec.get("name") or "").replace("\n", " ").strip()  # info: set name
    if name:  # info: if name
        return name[:80]  # info: return name [ : 80 ]
    clock = _clock(spec) or (0, 0)  # info: set clock
    label = function_label(str(spec.get("device")), str(spec.get("function")))  # info: set label
    return f"{device_label(str(spec.get('device')))} {label} at {clock[0]:02d}:{clock[1]:02d}"[:80]  # info: return f


# ====================================================
# SECTION: function add_items
# What it does: Append one or two power schedules after validation. Does not run them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_items(specs: list[dict], now: datetime | None = None) -> list[dict]:  # info: def add_items
    now = _as_hst(now or datetime.now(HST))  # info: set now
    if not specs:  # info: if not specs
        raise ValueError("nothing to add")  # info: raise ValueError
    for spec in specs:  # info: for spec in specs
        err = validate_spec(spec, now)  # info: set err
        if err:  # info: if err
            raise ValueError(err)  # info: raise ValueError
    group = "pg-" + uuid.uuid4().hex[:8] if len(specs) > 1 else ""  # info: set group
    made = []  # info: set made
    for spec in specs:  # info: for spec in specs
        made.append({  # info: made . append
            "id": "pa-" + now.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6],  # info: "id"
            "name": _clean_name(spec),  # info: "name"
            "enabled": True,  # info: "enabled"
            "device": str(spec["device"]),  # info: "device"
            "function": str(spec["function"]),  # info: "function"
            "hour": int(spec["hour"]),  # info: "hour"
            "minute": int(spec["minute"]),  # info: "minute"
            "repeat": spec["repeat"],  # info: "repeat"
            "date": str(spec.get("date") or "") if spec["repeat"] == "once" else "",  # info: "date"
            "group": group,  # info: "group"
            "last_fired": "",  # info: "last_fired"
            "last_attempt": "",  # info: "last_attempt"
            "last_status": "",  # info: "last_status"
            "last_detail": "",  # info: "last_detail"
            "created": now.isoformat(timespec="seconds"),  # info: "created"
        })  # info: }
    with _lock(power_path()):  # info: with _lock
        doc = load_power()  # info: set doc
        doc["items"].extend(made)  # info: doc [ "items" ] . extend
        _write_json(power_path(), doc)  # info: call _write_json
    return made  # info: return made


# ====================================================
# SECTION: function set_master
# What it does: Arm or pause every power schedule. Does not delete them and does not run one now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_master(enabled: bool) -> None:  # info: def set_master
    with _lock(power_path()):  # info: with _lock
        doc = load_power()  # info: set doc
        doc["master_enabled"] = bool(enabled)  # info: doc [ "master_enabled" ] = bool
        _write_json(power_path(), doc)  # info: call _write_json


# ====================================================
# SECTION: function set_item_enabled
# What it does: Arm or pause one power schedule. Does not run it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_item_enabled(item_id: str, enabled: bool) -> bool:  # info: def set_item_enabled
    with _lock(power_path()):  # info: with _lock
        doc = load_power()  # info: set doc
        found = False  # info: set found
        for item in doc["items"]:  # info: for item in doc [ "items" ]
            if isinstance(item, dict) and item.get("id") == item_id:  # info: if isinstance ( item , dict ) and
                item["enabled"] = bool(enabled)  # info: item [ "enabled" ] = bool
                found = True  # info: set found
                break  # info: break
        if found:  # info: if found
            _write_json(power_path(), doc)  # info: call _write_json
        return found  # info: return found


# ====================================================
# SECTION: function delete_item
# What it does: Remove one power schedule. Does not run it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def delete_item(item_id: str) -> bool:  # info: def delete_item
    with _lock(power_path()):  # info: with _lock
        doc = load_power()  # info: set doc
        keep = [it for it in doc["items"] if not (isinstance(it, dict) and it.get("id") == item_id)]  # info: set keep
        if len(keep) == len(doc["items"]):  # info: if len ( keep ) == len
            return False  # info: return False
        doc["items"] = keep  # info: doc [ "items" ] = keep
        _write_json(power_path(), doc)  # info: call _write_json
        return True  # info: return True


# ====================================================
# SECTION: function describe_item
# What it does: One sentence for a schedule row. Does not read the radio.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def describe_item(item: dict, now: datetime | None = None) -> str:  # info: def describe_item
    now = _as_hst(now or datetime.now(HST))  # info: set now
    clock = _clock(item)  # info: set clock
    hm = f"{clock[0]:02d}:{clock[1]:02d}" if clock else "—"  # info: set hm
    when = f"every day at {hm} HST" if item.get("repeat") == "daily" else f"once on {item.get('date') or '—'} at {hm} HST"  # info: set when
    label = f"{device_label(str(item.get('device') or ''))} · {function_label(str(item.get('device') or ''), str(item.get('function') or ''))}"  # info: set label
    status = str(item.get("last_status") or "")  # info: set status
    detail = str(item.get("last_detail") or "").replace("\n", " ")[:120]  # info: set detail
    if status == "ok":  # info: if status == "ok"
        tail = f"last run ok {item.get('last_fired') or ''}"  # info: set tail
    elif status == "fail":  # info: elif status == "fail"
        tail = "last run failed" + (f" · {detail}" if detail else "")  # info: set tail
    elif item.get("enabled"):  # info: elif item . get ( "enabled" )
        tail = "armed"  # info: set tail
    else:  # info: else
        tail = "paused"  # info: set tail
    if item.get("repeat") == "once" and not item.get("enabled") and status == "ok":  # info: if item . get ( "repeat" ) == "once" and
        tail = "finished"  # info: set tail
    pair = " · paired step" if item.get("group") else ""  # info: set pair
    return f"{label} · {when} · {tail}{pair}"  # info: return f


# ====================================================
# SECTION: function _run_script
# What it does: Run one catalog script under the EcoFlow BLE lock. Caller already checked the path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _run_script(script: Path) -> tuple[int, str]:  # info: def _run_script
    cmd = ["flock", "-w", "90", "/tmp/ecoflow-ble.lock", "bash", str(script)]  # info: set cmd
    try:  # info: try
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=120)  # info: set done
    except subprocess.TimeoutExpired:  # info: except subprocess . TimeoutExpired
        return 1, "timeout"  # info: return 1 , "timeout"
    except OSError as exc:  # info: except OSError as exc
        return 1, str(exc)[:300]  # info: return 1 , str
    text = ((done.stdout or "") + "\n" + (done.stderr or "")).strip()  # info: set text
    line = text.splitlines()[-1] if text else ""  # info: set line
    return done.returncode, line[:300]  # info: return done . returncode , line [ : 300 ]


# ====================================================
# SECTION: function run_due
# What it does: Run power schedules that are due at `now`. Marks the attempt first so the same minute cannot start twice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_due(now: datetime, runner=None, log=None) -> list[str]:  # info: def run_due
    now = _as_hst(now)  # info: set now
    stamp = now.isoformat(timespec="seconds")  # info: set stamp
    queued: list[dict] = []  # info: set queued
    with _lock(power_path()):  # info: with _lock
        doc = load_power()  # info: set doc
        if not doc.get("master_enabled"):  # info: if not doc . get ( "master_enabled" )
            return []  # info: return [ ]
        changed = False  # info: set changed
        for item in doc["items"]:  # info: for item in doc [ "items" ]
            if not isinstance(item, dict) or not item_due(item, now, True):  # info: if not isinstance ( item , dict ) or
                continue  # info: continue
            item["last_attempt"] = stamp  # info: item [ "last_attempt" ] = stamp
            changed = True  # info: set changed
            queued.append({"id": item.get("id"), "device": item.get("device"), "function": item.get("function")})  # info: queued . append
        if changed:  # info: if changed
            _write_json(power_path(), doc)  # info: call _write_json
    notes = []  # info: set notes
    for spec in queued:  # info: for spec in queued
        script = script_for(str(spec.get("device") or ""), str(spec.get("function") or ""))  # info: set script
        if script is None:  # info: if script is None
            code, detail = 1, "unknown function"  # info: code , detail = 1 , "unknown function"
        elif runner is None:  # info: elif runner is None
            code, detail = _run_script(script)  # info: code , detail = _run_script ( script )
        else:  # info: else
            code, detail = runner(spec, script)  # info: code , detail = runner ( spec , script )
        status = "ok" if code == 0 else "fail"  # info: set status
        with _lock(power_path()):  # info: with _lock
            doc = load_power()  # info: set doc
            for item in doc["items"]:  # info: for item in doc [ "items" ]
                if not isinstance(item, dict) or item.get("id") != spec.get("id"):  # info: if not isinstance ( item , dict ) or
                    continue  # info: continue
                item["last_status"] = status  # info: item [ "last_status" ] = status
                item["last_detail"] = detail  # info: item [ "last_detail" ] = detail
                if code == 0:  # info: if code == 0
                    item["last_fired"] = stamp  # info: item [ "last_fired" ] = stamp
                    if item.get("repeat") == "once":  # info: if item . get ( "repeat" ) == "once"
                        item["enabled"] = False  # info: item [ "enabled" ] = False
                break  # info: break
            _write_json(power_path(), doc)  # info: call _write_json
        line = f"power:{spec.get('device')}.{spec.get('function')} {'OK' if code == 0 else 'FAIL'} {detail}".rstrip()  # info: set line
        notes.append(line)  # info: notes . append
        if log is not None:  # info: if log is not None
            log(line)  # info: call log
    return notes  # info: return notes


# ====================================================
# SECTION: function poller_pids
# What it does: PIDs whose command line is the RootRecord poller. Does not signal them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poller_pids() -> list[int]:  # info: def poller_pids
    found = []  # info: set found
    proc = Path("/proc")  # info: set proc
    if not proc.is_dir():  # info: if not proc . is_dir ( )
        return found  # info: return found
    for entry in proc.iterdir():  # info: for entry in proc . iterdir ( )
        if not entry.name.isdigit():  # info: if not entry . name . isdigit ( )
            continue  # info: continue
        try:  # info: try
            raw = (entry / "cmdline").read_bytes().replace(b"\x00", b" ")  # info: set raw
        except OSError:  # info: except OSError
            continue  # info: continue
        if b"rootserver_poller.py" in raw:  # info: if b"rootserver_poller.py" in raw
            found.append(int(entry.name))  # info: found . append
    return found  # info: return found


# ====================================================
# SECTION: function _proc_start
# What it does: Unix start time of a process from /proc, or None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _proc_start(pid: int) -> float | None:  # info: def _proc_start
    try:  # info: try
        stat = Path("/proc/stat").read_text(encoding="utf-8")  # info: set stat
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")  # info: set raw
    except OSError:  # info: except OSError
        return None  # info: return None
    btime = 0  # info: set btime
    for line in stat.splitlines():  # info: for line in stat . splitlines ( )
        if line.startswith("btime "):  # info: if line . startswith ( "btime " )
            btime = int(line.split()[1])  # info: set btime
            break  # info: break
    end = raw.rfind(")")  # info: set end
    fields = raw[end + 2:].split()  # info: set fields
    if len(fields) < 20 or btime <= 0:  # info: if len ( fields ) < 20 or btime <= 0
        return None  # info: return None
    ticks = os.sysconf("SC_CLK_TCK") or 100  # info: set ticks
    return btime + int(fields[19]) / ticks  # info: return btime + int


# ====================================================
# SECTION: function poller_control_state
# What it does: live when this poller process started after the control code, restart when it is older, down when it is absent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poller_control_state() -> str:  # info: def poller_control_state
    pids = poller_pids()  # info: set pids
    if not pids:  # info: if not pids
        return "down"  # info: return "down"
    newest = Path(__file__).stat().st_mtime  # info: set newest
    poller = Path(__file__).with_name("rootserver_poller.py")  # info: set poller
    try:  # info: try
        newest = max(newest, poller.stat().st_mtime)  # info: set newest
    except OSError:  # info: except OSError
        pass  # info: pass
    for pid in pids:  # info: for pid in pids
        started = _proc_start(pid)  # info: set started
        if started is None or started + 1 < newest:  # info: if started is None or started + 1 < newest
            return "restart"  # info: return "restart"
    return "live"  # info: return "live"
