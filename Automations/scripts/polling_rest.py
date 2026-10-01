# ==============================================================================
# FILE: Automations/scripts/polling_rest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Stop the polling stack at one time and start it again later.

systemd user timers do the work, so the stack can start while the poller is
stopped. Saving a rest does not stop the poller. The laptop stays on.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import uuid  # info: import uuid
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
PACIFIC = ROOT / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server"  # info: set PACIFIC
POLLER_UNIT = "rr-rootserver-poller.service"  # info: set POLLER_UNIT
GLOBE_UNIT = "network-globe-hawaii.service"  # info: set GLOBE_UNIT
ID_RE = re.compile(r"^pr-[0-9a-f]{8}$")  # info: set ID_RE


# ====================================================
# SECTION: function rest_path
# What it does: JSON path for polling rests. Does not create the file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def rest_path() -> Path:  # info: def rest_path
    override = os.environ.get("RR_POLLING_REST", "").strip()  # info: set override
    if override:  # info: if override
        return Path(override)  # info: return Path ( override )
    base = Path(os.environ.get("RR_DATABASE_ROOT", str(ROOT / "2 - RootRecord-Database")))  # info: set base
    return base / "System" / "control-panel" / "polling-rest.json"  # info: return base / "System" / "control-panel" / "polling-rest.json"


# ====================================================
# SECTION: function unit_dir
# What it does: User systemd directory. Does not create it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def unit_dir() -> Path:  # info: def unit_dir
    override = os.environ.get("RR_SYSTEMD_USER_DIR", "").strip()  # info: set override
    if override:  # info: if override
        return Path(override)  # info: return Path ( override )
    return Path.home() / ".config" / "systemd" / "user"  # info: return Path . home ( ) / ".config" / "systemd" / "user"


# ====================================================
# SECTION: function stop_script
# What it does: Path of the existing stack stop script. Does not run it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stop_script() -> Path:  # info: def stop_script
    override = os.environ.get("RR_POLLING_REST_STOP", "").strip()  # info: set override
    if override:  # info: if override
        return Path(override)  # info: return Path ( override )
    return PACIFIC / "Automations" / "scripts" / "stack" / "stop-poller-stack.sh"  # info: return PACIFIC / "Automations" / "scripts" / "stack" / "stop-poller-stack.sh"


# ====================================================
# SECTION: function load
# What it does: Read rests. A missing or broken file is an empty list.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load() -> dict:  # info: def load
    path = rest_path()  # info: set path
    if not path.is_file():  # info: if not path . is_file ( )
        return {"items": []}  # info: return { "items" : [ ] }
    try:  # info: try
        doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {"items": []}  # info: return { "items" : [ ] }
    if not isinstance(doc, dict) or not isinstance(doc.get("items"), list):  # info: if not isinstance ( doc , dict ) or not isinstance
        return {"items": []}  # info: return { "items" : [ ] }
    return doc  # info: return doc


# ====================================================
# SECTION: function _save
# What it does: Write the rest file atomically. Creates the parent directory.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save(doc: dict) -> None:  # info: def _save
    path = rest_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    tmp.replace(path)  # info: tmp . replace ( path )


# ====================================================
# SECTION: function _run
# What it does: Run one command. Returns the exit code. Tests pass their own runner.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _run(argv: list[str], runner=None) -> int:  # info: def _run
    if runner is not None:  # info: if runner is not None
        return int(runner(argv))  # info: return int ( runner ( argv ) )
    done = subprocess.run(argv, check=False, capture_output=True, text=True)  # info: set done
    return int(done.returncode)  # info: return int ( done . returncode )


# ====================================================
# SECTION: function validate
# What it does: Reject a rest whose return time is not after the off time, or whose once-off time has passed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def validate(repeat: str, off_at: datetime, on_at: datetime, now: datetime | None = None) -> str:  # info: def validate
    now = now or datetime.now(HST)  # info: set now
    if repeat not in ("once", "daily"):  # info: if repeat not in ( "once" , "daily" )
        return "Repeat must be once or daily."  # info: return "Repeat must be once or daily."
    if on_at <= off_at:  # info: if on_at <= off_at
        return "The boot time has to be after the off time."  # info: return "The boot time has to be after the off time."
    if repeat == "once" and off_at < now - timedelta(minutes=1):  # info: if repeat == "once" and off_at < now - timedelta ( minutes = 1 )
        return "The off time has to be in the future."  # info: return "The off time has to be in the future."
    return ""  # info: return ""


# ====================================================
# SECTION: function _clock
# What it does: Build an HST datetime from a date and a clock. Returns None when the date is not YYYY-MM-DD.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clock(date_text: str, hour: int, minute: int) -> datetime | None:  # info: def _clock
    try:  # info: try
        day = datetime.strptime(date_text.strip(), "%Y-%m-%d").date()  # info: set day
    except ValueError:  # info: except ValueError
        return None  # info: return None
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:  # info: if hour < 0 or hour > 23 or minute < 0 or minute > 59
        return None  # info: return None
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=HST)  # info: return datetime


# ====================================================
# SECTION: function _calendar
# What it does: systemd OnCalendar text in HST. Does not install a timer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _calendar(item: dict, side: str) -> str:  # info: def _calendar
    if item.get("repeat") == "daily":  # info: if item . get ( "repeat" ) == "daily"
        hour = int(item[f"{side}_hour"])  # info: set hour
        minute = int(item[f"{side}_minute"])  # info: set minute
        return f"*-*-* {hour:02d}:{minute:02d}:00 Pacific/Honolulu"  # info: return f" *-*-* { hour : 02d } : { minute : 02d } : 00 Pacific/Honolulu "
    stamp = datetime.fromisoformat(str(item[f"{side}_at"]))  # info: set stamp
    local = stamp.astimezone(HST)  # info: set local
    return local.strftime("%Y-%m-%d %H:%M:00 Pacific/Honolulu")  # info: return local . strftime


# ====================================================
# SECTION: function _unit_names
# What it does: Service and timer names for one rest. Does not touch systemd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _unit_names(item_id: str) -> list[str]:  # info: def _unit_names
    names = []  # info: set names
    for side in ("off", "on"):  # info: for side in ( "off" , "on" )
        names.append(f"rr-polling-rest-{side}-{item_id}.service")  # info: names . append
        names.append(f"rr-polling-rest-{side}-{item_id}.timer")  # info: names . append
    return names  # info: return names


# ====================================================
# SECTION: function _write_units
# What it does: Write the four user units for one rest. Does not enable them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_units(item: dict) -> None:  # info: def _write_units
    folder = unit_dir()  # info: set folder
    folder.mkdir(parents=True, exist_ok=True)  # info: folder . mkdir
    item_id = str(item["id"])  # info: set item_id
    script = Path(__file__).resolve()  # info: set script
    python = os.environ.get("RR_POLLING_REST_PYTHON", "/usr/bin/python3")  # info: set python
    for side, title in (("off", "Stop the polling stack"), ("on", "Start the polling stack")):  # info: for side , title in
        service = folder / f"rr-polling-rest-{side}-{item_id}.service"  # info: set service
        timer = folder / f"rr-polling-rest-{side}-{item_id}.timer"  # info: set timer
        service.write_text(  # info: service . write_text
            "[Unit]\n"  # info: "[Unit] \n"
            f"Description=Root Record polling rest {side} {item_id}\n"  # info: f" Description=Root Record polling rest { side } { item_id } \n"
            "\n[Service]\n"  # info: " \n[Service] \n"
            "Type=oneshot\n"  # info: "Type=oneshot \n"
            f"ExecStart={python} {json.dumps(str(script))} fire {side} {item_id}\n",  # info: f" ExecStart= { python } { json . dumps ( str ( script ) ) } fire { side } { item_id } \n" ,
            encoding="utf-8")  # info: encoding = "utf-8" )
        timer.write_text(  # info: timer . write_text
            "[Unit]\n"  # info: "[Unit] \n"
            f"Description={title}\n"  # info: f" Description= { title } \n"
            "\n[Timer]\n"  # info: " \n[Timer] \n"
            f"OnCalendar={_calendar(item, side)}\n"  # info: f" OnCalendar= { _calendar ( item , side ) } \n"
            "AccuracySec=15s\n"  # info: "AccuracySec=15s \n"
            "Persistent=true\n"  # info: "Persistent=true \n"
            f"Unit=rr-polling-rest-{side}-{item_id}.service\n"  # info: f" Unit=rr-polling-rest- { side } - { item_id } .service \n"
            "\n[Install]\n"  # info: " \n[Install] \n"
            "WantedBy=timers.target\n",  # info: "WantedBy=timers.target \n" ,
            encoding="utf-8")  # info: encoding = "utf-8" )


# ====================================================
# SECTION: function _enable
# What it does: Reload user systemd and enable both timers. Does not start the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _enable(item_id: str, runner=None) -> str:  # info: def _enable
    if _run(["systemctl", "--user", "daemon-reload"], runner) != 0:  # info: if _run ( [ "systemctl" , "--user" , "daemon-reload" ] , runner ) != 0
        return "systemd did not reload the user timers."  # info: return "systemd did not reload the user timers."
    for side in ("off", "on"):  # info: for side in ( "off" , "on" )
        timer = f"rr-polling-rest-{side}-{item_id}.timer"  # info: set timer
        if _run(["systemctl", "--user", "enable", "--now", timer], runner) != 0:  # info: if _run
            return f"Could not arm {timer}."  # info: return f" Could not arm { timer } . "
    return ""  # info: return ""


# ====================================================
# SECTION: function _remove_units
# What it does: Disable and delete the four units. Does not start or stop the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _remove_units(item_id: str, runner=None) -> None:  # info: def _remove_units
    for name in _unit_names(item_id):  # info: for name in _unit_names ( item_id )
        if name.endswith(".timer"):  # info: if name . endswith ( ".timer" )
            _run(["systemctl", "--user", "disable", "--now", name], runner)  # info: call _run
        path = unit_dir() / name  # info: set path
        if path.is_file():  # info: if path . is_file ( )
            path.unlink()  # info: path . unlink ( )
    _run(["systemctl", "--user", "daemon-reload"], runner)  # info: call _run


# ====================================================
# SECTION: function add_rest
# What it does: Save one rest and arm its timers. Does not stop the poller now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_rest(repeat: str, off_at: datetime, on_at: datetime, now: datetime | None = None, runner=None) -> dict:  # info: def add_rest
    err = validate(repeat, off_at, on_at, now)  # info: set err
    if err:  # info: if err
        raise ValueError(err)  # info: raise ValueError ( err )
    item_id = "pr-" + uuid.uuid4().hex[:8]  # info: set item_id
    item = {  # info: set item
        "id": item_id,  # info: "id"
        "enabled": True,  # info: "enabled"
        "repeat": repeat,  # info: "repeat"
        "off_at": off_at.astimezone(HST).isoformat(timespec="seconds"),  # info: "off_at"
        "on_at": on_at.astimezone(HST).isoformat(timespec="seconds"),  # info: "on_at"
        "off_hour": off_at.hour,  # info: "off_hour"
        "off_minute": off_at.minute,  # info: "off_minute"
        "on_hour": on_at.hour,  # info: "on_hour"
        "on_minute": on_at.minute,  # info: "on_minute"
        "off_done_at": "",  # info: "off_done_at"
        "on_done_at": "",  # info: "on_done_at"
    }  # info: }
    doc = load()  # info: set doc
    doc["items"].append(item)  # info: doc [ "items" ] . append ( item )
    _save(doc)  # info: call _save
    try:  # info: try
        _write_units(item)  # info: call _write_units
        err = _enable(item_id, runner)  # info: set err
        if err:  # info: if err
            raise RuntimeError(err)  # info: raise RuntimeError ( err )
    except Exception:  # info: except Exception
        _remove_units(item_id, runner)  # info: call _remove_units
        doc = load()  # info: set doc
        doc["items"] = [row for row in doc["items"] if row.get("id") != item_id]  # info: doc [ "items" ] = [ row for row in doc [ "items" ] if row . get ( "id" ) != item_id ]
        _save(doc)  # info: call _save
        raise  # info: raise
    return item  # info: return item


# ====================================================
# SECTION: function delete_rest
# What it does: Remove one rest and its timers. Does not start the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def delete_rest(item_id: str, runner=None) -> bool:  # info: def delete_rest
    if not ID_RE.match(item_id or ""):  # info: if not ID_RE . match ( item_id or "" )
        return False  # info: return False
    doc = load()  # info: set doc
    kept = [row for row in doc["items"] if not (isinstance(row, dict) and row.get("id") == item_id)]  # info: set kept
    if len(kept) == len(doc["items"]):  # info: if len ( kept ) == len ( doc [ "items" ] )
        return False  # info: return False
    _remove_units(item_id, runner)  # info: call _remove_units
    doc["items"] = kept  # info: doc [ "items" ] = kept
    _save(doc)  # info: call _save
    return True  # info: return True


# ====================================================
# SECTION: function describe
# What it does: One line for the Automations page. Does not read systemd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def describe(item: dict) -> str:  # info: def describe
    if item.get("repeat") == "daily":  # info: if item . get ( "repeat" ) == "daily"
        when = f"every day off {int(item.get('off_hour', 0)):02d}:{int(item.get('off_minute', 0)):02d} · back {int(item.get('on_hour', 0)):02d}:{int(item.get('on_minute', 0)):02d} HST"  # info: set when
    else:  # info: else
        when = f"once off {item.get('off_at') or '—'} · back {item.get('on_at') or '—'}"  # info: set when
    if item.get("off_done_at") and item.get("on_done_at"):  # info: if item . get ( "off_done_at" ) and item . get ( "on_done_at" )
        state = "finished"  # info: set state
    elif item.get("off_done_at"):  # info: elif item . get ( "off_done_at" )
        state = "stopped, waiting to boot"  # info: set state
    elif item.get("enabled", True):  # info: elif item . get ( "enabled" , True )
        state = "armed"  # info: set state
    else:  # info: else
        state = "off"  # info: set state
    return f"{when} · {state}"  # info: return f" { when } · { state } "


# ====================================================
# SECTION: function fire
# What it does: Stop the stack or start it. A once-timer is disarmed after it fires. Does not power off the laptop.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fire(action: str, item_id: str, runner=None) -> int:  # info: def fire
    if action not in ("off", "on") or not ID_RE.match(item_id or ""):  # info: if action not in ( "off" , "on" ) or not ID_RE . match
        return 2  # info: return 2
    doc = load()  # info: set doc
    item = next((row for row in doc["items"] if isinstance(row, dict) and row.get("id") == item_id), None)  # info: set item
    if item is None or not item.get("enabled", True):  # info: if item is None or not item . get ( "enabled" , True )
        return 0  # info: return 0
    now = datetime.now(HST).isoformat(timespec="seconds")  # info: set now
    if action == "off":  # info: if action == "off"
        code = _run(["bash", str(stop_script())], runner)  # info: set code
        item["off_done_at"] = now  # info: item [ "off_done_at" ] = now
    else:  # info: else
        code = _run(["systemctl", "--user", "start", POLLER_UNIT], runner)  # info: set code
        _run(["systemctl", "--user", "start", GLOBE_UNIT], runner)  # info: call _run
        item["on_done_at"] = now  # info: item [ "on_done_at" ] = now
    if item.get("repeat") == "once":  # info: if item . get ( "repeat" ) == "once"
        _run(["systemctl", "--user", "disable", "--now", f"rr-polling-rest-{action}-{item_id}.timer"], runner)  # info: call _run
        if item.get("off_done_at") and item.get("on_done_at"):  # info: if item . get ( "off_done_at" ) and item . get ( "on_done_at" )
            item["enabled"] = False  # info: item [ "enabled" ] = False
    _save(doc)  # info: call _save
    return code  # info: return code


# ====================================================
# SECTION: function main
# What it does: systemd entry. fire off|on <id>. Does nothing else.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    if len(argv) == 4 and argv[1] == "fire":  # info: if len ( argv ) == 4 and argv [ 1 ] == "fire"
        return fire(argv[2], argv[3])  # info: return fire ( argv [ 2 ] , argv [ 3 ] )
    return 2  # info: return 2


if __name__ == "__main__":  # info: if __name__ == "__main__"
    import sys  # info: import sys
    raise SystemExit(main(sys.argv))  # info: raise SystemExit ( main ( sys . argv ) )
