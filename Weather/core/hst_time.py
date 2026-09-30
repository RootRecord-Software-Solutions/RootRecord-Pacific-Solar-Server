# ==============================================================================
# FILE: Weather/core/hst_time.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Single source of truth for Hawaii Standard Time conversion.

Hawaii does not observe DST, so HST is a fixed UTC-10 offset year-round.
Nothing else in this skill computes an HST offset independently — every
module that needs "what HST date/time is this UTC timestamp" imports from
here, per weather_skill_architecture.md Section 3.
"""
from __future__ import annotations  # info: from __future__ import annotations

from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone

HST_OFFSET = timedelta(hours=-10)  # info: set HST_OFFSET
HST = timezone(HST_OFFSET, name="HST")  # info: set HST

# Archived filename timestamp format, per nws_plan.md Section 2:
#   YYYYMMDDTHHMMSS-HHMM  e.g. 20260924T143207-1000.gif
ARCHIVE_TIMESTAMP_FMT = "%Y%m%dT%H%M%S-1000"  # info: set ARCHIVE_TIMESTAMP_FMT

# Date-folder format, per nws_plan.md Section 1/2: MM-DD-YYYY
DATE_FOLDER_FMT = "%m-%d-%Y"  # info: set DATE_FOLDER_FMT


# ====================================================
# SECTION: function utc_now
# What it does: Current time, timezone-aware UTC. Use this instead of datetime.utcnow().
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def utc_now() -> datetime:  # info: def utc_now
    """Current time, timezone-aware UTC. Use this instead of datetime.utcnow()."""  # info: """Current time, timezone-aware UTC. Use this instead of datetime.utcnow()."""
    return datetime.now(timezone.utc)  # info: return datetime . now ( timezone . utc


# ====================================================
# SECTION: function to_hst
# What it does: Convert any timezone-aware datetime to HST. Naive input is assumed UTC.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def to_hst(dt: datetime) -> datetime:  # info: def to_hst
    """Convert any timezone-aware datetime to HST. Naive input is assumed UTC."""  # info: """Convert any timezone-aware datetime to HST. Naive input is assumed UTC."""
    if dt.tzinfo is None:  # info: if dt . tzinfo is None :
        dt = dt.replace(tzinfo=timezone.utc)  # info: set dt
    return dt.astimezone(HST)  # info: return dt . astimezone ( HST )


# ====================================================
# SECTION: function hst_now
# What it does: Current time in HST.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hst_now() -> datetime:  # info: def hst_now
    """Current time in HST."""  # info: """Current time in HST."""
    return to_hst(utc_now())  # info: return to_hst ( utc_now ( ) )


# ====================================================
# SECTION: function hst_date_folder
# What it does: The MM-DD-YYYY archive date-folder name for a given timestamp (any tz).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hst_date_folder(dt: datetime) -> str:  # info: def hst_date_folder
    """The MM-DD-YYYY archive date-folder name for a given timestamp (any tz)."""  # info: """The MM-DD-YYYY archive date-folder name for a given timestamp (any tz)."""
    return to_hst(dt).strftime(DATE_FOLDER_FMT)  # info: return to_hst ( dt ) . strftime (


# ====================================================
# SECTION: function hst_archive_timestamp
# What it does: The YYYYMMDDTHHMMSS-1000 filename timestamp for a given timestamp (any tz). Hawaii's offset is fixed, so the trailing "-1000" is hardcoded rather than derived from strftime's %z (w
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hst_archive_timestamp(dt: datetime) -> str:  # info: def hst_archive_timestamp
    """The YYYYMMDDTHHMMSS-1000 filename timestamp for a given timestamp (any tz).

    Hawaii's offset is fixed, so the trailing "-1000" is hardcoded rather than
    derived from strftime's %z (which would require attaching a genuine
    zoneinfo object) -- this keeps the single source of truth simple and
    correct without a zoneinfo dependency.
    """
    return to_hst(dt).strftime(ARCHIVE_TIMESTAMP_FMT)  # info: return to_hst ( dt ) . strftime (


# ====================================================
# SECTION: function is_new_hst_day
# What it does: True if `current` has rolled into a later HST calendar date than `previous`. Used by scheduler/run_cycle.py to fire archive/consolidate.py exactly once per HST midnight rollover, p
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_new_hst_day(previous: datetime, current: datetime) -> bool:  # info: def is_new_hst_day
    """True if `current` has rolled into a later HST calendar date than `previous`.

    Used by scheduler/run_cycle.py to fire archive/consolidate.py exactly once
    per HST midnight rollover, per nws_plan.md Section 8.
    """
    return hst_date_folder(current) != hst_date_folder(previous)  # info: return hst_date_folder ( current ) != hst_date_folder (
