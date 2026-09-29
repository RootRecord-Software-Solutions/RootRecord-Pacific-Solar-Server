"""Single source of truth for Hawaii Standard Time conversion.

Hawaii does not observe DST, so HST is a fixed UTC-10 offset year-round.
Nothing else in this skill computes an HST offset independently — every
module that needs "what HST date/time is this UTC timestamp" imports from
here, per weather_skill_architecture.md Section 3.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

HST_OFFSET = timedelta(hours=-10)
HST = timezone(HST_OFFSET, name="HST")

# Archived filename timestamp format, per nws_plan.md Section 2:
#   YYYYMMDDTHHMMSS-HHMM  e.g. 20260924T143207-1000.gif
ARCHIVE_TIMESTAMP_FMT = "%Y%m%dT%H%M%S-1000"

# Date-folder format, per nws_plan.md Section 1/2: MM-DD-YYYY
DATE_FOLDER_FMT = "%m-%d-%Y"


def utc_now() -> datetime:
    """Current time, timezone-aware UTC. Use this instead of datetime.utcnow()."""
    return datetime.now(timezone.utc)


def to_hst(dt: datetime) -> datetime:
    """Convert any timezone-aware datetime to HST. Naive input is assumed UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(HST)


def hst_now() -> datetime:
    """Current time in HST."""
    return to_hst(utc_now())


def hst_date_folder(dt: datetime) -> str:
    """The MM-DD-YYYY archive date-folder name for a given timestamp (any tz)."""
    return to_hst(dt).strftime(DATE_FOLDER_FMT)


def hst_archive_timestamp(dt: datetime) -> str:
    """The YYYYMMDDTHHMMSS-1000 filename timestamp for a given timestamp (any tz).

    Hawaii's offset is fixed, so the trailing "-1000" is hardcoded rather than
    derived from strftime's %z (which would require attaching a genuine
    zoneinfo object) -- this keeps the single source of truth simple and
    correct without a zoneinfo dependency.
    """
    return to_hst(dt).strftime(ARCHIVE_TIMESTAMP_FMT)


def is_new_hst_day(previous: datetime, current: datetime) -> bool:
    """True if `current` has rolled into a later HST calendar date than `previous`.

    Used by scheduler/run_cycle.py to fire archive/consolidate.py exactly once
    per HST midnight rollover, per nws_plan.md Section 8.
    """
    return hst_date_folder(current) != hst_date_folder(previous)
