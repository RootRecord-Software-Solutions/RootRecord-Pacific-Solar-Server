# ==============================================================================
# FILE: Reports/pipeline/windows.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Deterministic report windows. The clock argument is the meaning, not the filename."""
from __future__ import annotations  # info: from __future__ import annotations

from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

TZ = "Pacific/Honolulu"  # info: set TZ


# ====================================================
# SECTION: function as_local
# What it does: Put a clock in the report timezone. Naive clocks are read as that zone, not as UTC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def as_local(when: datetime, timezone: str = TZ) -> datetime:  # info: def as_local
    zone = ZoneInfo(timezone)  # info: set zone
    if when.tzinfo is None:  # info: if when . tzinfo is None
        return when.replace(tzinfo=zone)  # info: return when . replace
    return when.astimezone(zone)  # info: return when . astimezone


# ====================================================
# SECTION: function window_for
# What it does: Quantize a clock to the profile cadence. Five-minute windows are 14:00–14:05 style bounds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def window_for(when: datetime, cadence: str, timezone: str = TZ) -> dict:  # info: def window_for
    local = as_local(when, timezone).replace(microsecond=0)  # info: set local
    kind = cadence or "hourly"  # info: set kind
    if kind == "5m":  # info: if kind == "5m"
        start = local.replace(minute=(local.minute // 5) * 5, second=0)  # info: set start
        end = start + timedelta(minutes=5)  # info: set end
    elif kind == "15m":  # info: elif kind == "15m"
        start = local.replace(minute=(local.minute // 15) * 15, second=0)  # info: set start
        end = start + timedelta(minutes=15)  # info: set end
    elif kind == "half":  # info: elif kind == "half"
        start = local.replace(minute=0 if local.minute < 30 else 30, second=0)  # info: set start
        end = start + timedelta(minutes=30)  # info: set end
    elif kind == "daily":  # info: elif kind == "daily"
        start = local.replace(hour=0, minute=0, second=0)  # info: set start
        end = start + timedelta(days=1)  # info: set end
    else:  # info: else
        start = local.replace(minute=0, second=0)  # info: set start
        end = start + timedelta(hours=1)  # info: set end
    return {"window_start": start.isoformat(), "window_end": end.isoformat(), "timezone": timezone}  # info: return window


# ====================================================
# SECTION: function contains
# What it does: True when a clock falls inside a stored window. A null window never matches.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def contains(report: dict, when: datetime) -> bool:  # info: def contains
    start = report.get("window_start") or ""  # info: set start
    end = report.get("window_end") or ""  # info: set end
    if not start or not end:  # info: if not start or not end
        return False  # info: return False
    zone = str(report.get("timezone") or TZ)  # info: set zone
    local = as_local(when, zone)  # info: set local
    return datetime.fromisoformat(start) <= local < datetime.fromisoformat(end)  # info: return start <= local < end


# ====================================================
# SECTION: function due
# What it does: True when this clock is the profile's scheduled minute. Disabled profiles are never due.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def due(profile: dict, when: datetime, timezone: str = TZ) -> bool:  # info: def due
    if not profile.get("enabled", True):  # info: if not profile . get ( "enabled" , True )
        return False  # info: return False
    local = as_local(when, timezone)  # info: set local
    if profile.get("cadence") == "5m":  # info: if cadence is 5m
        return local.minute % 5 == 0 and local.second == 0  # info: return five-minute mark
    minutes = profile.get("minute")  # info: set minutes
    if isinstance(minutes, list) and minutes:  # info: if isinstance ( minutes , list ) and minutes
        return local.minute in minutes and local.second == 0  # info: return local . minute in minutes
    at = str(profile.get("at") or "")  # info: set at
    if at and ":" in at:  # info: if at and ":" in at
        hour, minute = at.split(":", 1)  # info: hour , minute = at . split
        return local.hour == int(hour) and local.minute == int(minute) and local.second == 0  # info: return clock match
    return False  # info: return False
