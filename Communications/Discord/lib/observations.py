# ==============================================================================
# FILE: Communications/Discord/lib/observations.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Read the recorded host sample. Does not sample the host.

System/scripts/sys-sample.sh owns the measurement. This module only reads
System/last/host-last.json. Ages match Reports/template_fill.py: 15 minutes
fresh, 360 minutes stale, older than that unavailable.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
from dataclasses import dataclass  # info: from dataclasses import dataclass
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
FRESH_MINUTES = 15  # info: set FRESH_MINUTES
STALE_MINUTES = 360  # info: set STALE_MINUTES


# ====================================================
# SECTION: class HostObservation
# What it does: One recorded host sample, or an explicit unavailable result.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass(frozen=True)
class HostObservation:  # info: class HostObservation
    status: str  # info: status : str
    at: str  # info: at : str
    cpu_percent: float | None  # info: cpu_percent : float | None
    mem_used_percent: float | None  # info: mem_used_percent : float | None
    load1: float | None  # info: load1 : float | None
    source: str  # info: source : str


# ====================================================
# SECTION: function unavailable
# What it does: Build an observation that cites no numbers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def unavailable(source: str) -> HostObservation:  # info: def unavailable
    return HostObservation("unavailable", "", None, None, None, source)  # info: return HostObservation


# ====================================================
# SECTION: function measured
# What it does: Return a float only when the field says it was measured.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def measured(fields: dict, name: str) -> float | None:  # info: def measured
    item = fields.get(name)  # info: set item
    if not isinstance(item, dict):  # info: if not isinstance ( item , dict )
        return None  # info: return None
    if item.get("state") != "measured":  # info: if item . get ( "state" ) != "measured"
        return None  # info: return None
    try:  # info: try
        return float(item["value"])  # info: return float ( item [ "value" ] )
    except (TypeError, ValueError, KeyError):  # info: except
        return None  # info: return None


# ====================================================
# SECTION: function parse_at
# What it does: Parse the sample timestamp as UTC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_at(value: str) -> datetime | None:  # info: def parse_at
    text = (value or "").strip()  # info: set text
    if not text:  # info: if not text
        return None  # info: return None
    try:  # info: try
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))  # info: set parsed
    except ValueError:  # info: except ValueError
        return None  # info: return None
    if parsed.tzinfo is None:  # info: if parsed . tzinfo is None
        parsed = parsed.replace(tzinfo=timezone.utc)  # info: set parsed
    return parsed.astimezone(timezone.utc)  # info: return parsed . astimezone ( timezone . utc )


# ====================================================
# SECTION: function load_host
# What it does: Read host-last.json and label it fresh, stale, or unavailable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_host(path: Path, now: datetime | None = None) -> HostObservation:  # info: def load_host
    source = str(path)  # info: set source
    if not path.is_file():  # info: if not path . is_file ( )
        return unavailable(source)  # info: return unavailable ( source )
    try:  # info: try
        payload = json.loads(path.read_text(encoding="utf-8"))  # info: set payload
    except (OSError, ValueError):  # info: except
        return unavailable(source)  # info: return unavailable ( source )
    if not isinstance(payload, dict):  # info: if not isinstance ( payload , dict )
        return unavailable(source)  # info: return unavailable ( source )
    stamp = parse_at(str(payload.get("at") or ""))  # info: set stamp
    if stamp is None:  # info: if stamp is None
        return unavailable(source)  # info: return unavailable ( source )
    moment = now or datetime.now(timezone.utc)  # info: set moment
    if moment.tzinfo is None:  # info: if moment . tzinfo is None
        moment = moment.replace(tzinfo=timezone.utc)  # info: set moment
    age = (moment.astimezone(timezone.utc) - stamp).total_seconds() / 60  # info: set age
    if age < -5 or age > STALE_MINUTES:  # info: if age < -5 or age > STALE_MINUTES
        return unavailable(source)  # info: return unavailable ( source )
    fields = payload.get("fields") if isinstance(payload.get("fields"), dict) else {}  # info: set fields
    shown = stamp.astimezone(HST).isoformat(timespec="seconds")  # info: set shown
    status = "fresh" if age <= FRESH_MINUTES else "stale"  # info: set status
    return HostObservation(  # info: return HostObservation
        status,  # info: status
        shown,  # info: shown
        measured(fields, "cpu_percent"),  # info: measured ( fields , "cpu_percent" )
        measured(fields, "mem_used_percent"),  # info: measured ( fields , "mem_used_percent" )
        measured(fields, "load1"),  # info: measured ( fields , "load1" )
        source,  # info: source
    )  # info: )


# ====================================================
# SECTION: function render_observation
# What it does: Text the model may cite. Unavailable renders no numbers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_observation(obs: HostObservation) -> str:  # info: def render_observation
    if obs.status == "unavailable":  # info: if obs . status == "unavailable"
        return (  # info: return
            "Host measurement: unavailable. No recorded sample is available to cite. "  # info: "Host measurement: unavailable. No recorded sample is available to cite. "
            "Do not invent CPU, memory, disk, network, uptime, power, or service status."  # info: "Do not invent CPU, memory, disk, network, uptime, power, or service status."
        )  # info: )
    bits = [f"Host measurement: recorded at {obs.at}.", f"Status: {obs.status}."]  # info: set bits
    if obs.cpu_percent is not None:  # info: if obs . cpu_percent is not None
        bits.append(f"cpu_percent={obs.cpu_percent}")  # info: bits . append
    if obs.mem_used_percent is not None:  # info: if obs . mem_used_percent is not None
        bits.append(f"mem_used_percent={obs.mem_used_percent}")  # info: bits . append
    if obs.load1 is not None:  # info: if obs . load1 is not None
        bits.append(f"load1={obs.load1}")  # info: bits . append
    if obs.status == "stale":  # info: if obs . status == "stale"
        bits.append("Say that this sample is stale. Do not present it as current.")  # info: bits . append
    else:  # info: else
        bits.append("Cite these figures only, with this time. This is not a newer measurement.")  # info: bits . append
    bits.append("This file is not a service-status observation.")  # info: bits . append
    return " ".join(bits)  # info: return " " . join ( bits )
