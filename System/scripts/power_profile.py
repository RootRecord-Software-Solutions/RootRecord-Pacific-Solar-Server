# ==============================================================================
# FILE: System/scripts/power_profile.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Log the host power profile: performance, balanced, or energy saver.

Reads powerprofilesctl, then the ACPI platform profile. A change closes one
segment. Time in each mode accumulates from the first sample. No mode is set here.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DIR = DB / "System" / "power-profile"  # info: set DIR
STATE = DIR / "mode-last.json"  # info: set STATE
SEGMENTS = DIR / "mode-segments.jsonl"  # info: set SEGMENTS
DAILY = DIR / "mode-use.json"  # info: set DAILY
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
LABELS = {"performance": "performance", "balanced": "balanced", "power-saver": "energy saver", "low-power": "energy saver"}  # info: set LABELS
MODES = ("performance", "balanced", "energy saver")  # info: set MODES


# ====================================================
# SECTION: function read_raw
# What it does: Current profile id, or None when the host does not report one.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_raw() -> str | None:  # info: def read_raw
    """Current profile id, or None when the host does not report one."""  # info: docstring
    try:  # info: try
        out = subprocess.check_output(["powerprofilesctl", "get"], text=True, timeout=3, stderr=subprocess.DEVNULL).strip()  # info: set out
        if out:  # info: if out
            return out.split()[0]  # info: return the profile id
    except (OSError, subprocess.SubprocessError, ValueError):  # info: except
        pass  # info: pass
    try:  # info: try
        text = Path("/sys/firmware/acpi/platform_profile").read_text(encoding="utf-8").strip()  # info: set text
    except OSError:  # info: except OSError
        return None  # info: return None
    return text or None  # info: return text or None


# ====================================================
# SECTION: function label_for
# What it does: Map a raw profile id to performance, balanced, or energy saver.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def label_for(raw: str) -> str:  # info: def label_for
    return LABELS.get(raw, raw)  # info: return LABELS . get


# ====================================================
# SECTION: function _load
# What it does: Read a JSON object. Missing or bad files are empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load(path: Path) -> dict:  # info: def _load
    try:  # info: try
        row = json.loads(path.read_text(encoding="utf-8"))  # info: set row
    except (OSError, ValueError):  # info: except
        return {}  # info: return
    return row if isinstance(row, dict) else {}  # info: return row if isinstance


# ====================================================
# SECTION: function _save
# What it does: Replace a JSON file in place.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save(path: Path, row: dict) -> None:  # info: def _save
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace


# ====================================================
# SECTION: function _blank
# What it does: Zero seconds for each mode.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _blank() -> dict:  # info: def _blank
    return {mode: 0 for mode in MODES}  # info: return


# ====================================================
# SECTION: function note
# What it does: Add elapsed time to the mode that was in use, and close a segment when it changes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def note(now_epoch: float | None = None, raw: str | None = None) -> dict:  # info: def note
    """Add elapsed time to the mode that was in use, and close a segment when it changes."""  # info: docstring
    now_epoch = time.time() if now_epoch is None else now_epoch  # info: set now_epoch
    raw = read_raw() if raw is None else raw  # info: set raw
    if not raw:  # info: if not raw
        return {}  # info: return
    label = label_for(raw)  # info: set label
    now = datetime.fromtimestamp(now_epoch, HST)  # info: set now
    state = _load(STATE)  # info: set state
    use = _load(DAILY)  # info: set use
    seconds = use.get("seconds") if isinstance(use.get("seconds"), dict) else _blank()  # info: set seconds
    today_key = now.date().isoformat()  # info: set today_key
    today = use.get("today_seconds") if use.get("today") == today_key and isinstance(use.get("today_seconds"), dict) else _blank()  # info: set today
    for bucket in (seconds, today):  # info: for bucket in
        for mode in MODES:  # info: for mode in MODES
            bucket.setdefault(mode, 0)  # info: bucket . setdefault
    prev = state.get("label")  # info: set prev
    since = float(state.get("since_epoch") or 0)  # info: set since
    span = float(state.get("span_epoch") or since or 0)  # info: set span
    if prev in MODES and since and now_epoch > since:  # info: if a previous mode has an open interval
        elapsed = int(now_epoch - since)  # info: set elapsed
        seconds[prev] = int(seconds.get(prev) or 0) + elapsed  # info: add elapsed to the running total
        today[prev] = int(today.get(prev) or 0) + elapsed  # info: add elapsed to today
        if prev != label:  # info: if the mode changed
            start = datetime.fromtimestamp(span or since, HST)  # info: set start
            with SEGMENTS.open("a", encoding="utf-8") as fh:  # info: with SEGMENTS . open
                fh.write(json.dumps({  # info: fh . write
                    "mode": prev, "raw": state.get("raw"), "start": start.isoformat(timespec="seconds"),  # info: start of the closed segment
                    "end": now.isoformat(timespec="seconds"), "seconds": int(now_epoch - (span or since)),  # info: whole stretch in that mode
                }) + "\n")  # info: newline
            span = now_epoch  # info: set span
    elif not span:  # info: elif not span
        span = now_epoch  # info: set span
    summary = {  # info: set summary
        "updated_at": now.isoformat(timespec="seconds"),  # info: "updated_at"
        "today": today_key,  # info: "today"
        "mode": label,  # info: "mode"
        "raw": raw,  # info: "raw"
        "since": now.isoformat(timespec="seconds"),  # info: "since"
        "seconds": {mode: int(seconds.get(mode) or 0) for mode in MODES},  # info: "seconds"
        "today_seconds": {mode: int(today.get(mode) or 0) for mode in MODES},  # info: "today_seconds"
    }  # info: }
    _save(DAILY, summary)  # info: call _save
    _save(STATE, {"raw": raw, "label": label, "since": summary["since"], "since_epoch": now_epoch, "span_epoch": span or now_epoch})  # info: call _save
    return summary  # info: return summary


# ====================================================
# SECTION: function current
# What it does: Last logged mode. Does not sample the host.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def current() -> dict:  # info: def current
    row = _load(DAILY)  # info: set row
    if not row.get("mode"):  # info: if not row . get
        return {}  # info: return
    return row  # info: return row


# ====================================================
# SECTION: function sentence
# What it does: One spoken line for the mode in use. Empty when none is logged.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sentence() -> str:  # info: def sentence
    mode = current().get("mode")  # info: set mode
    if not mode:  # info: if not mode
        return ""  # info: return
    return f"Host power mode is {mode}."  # info: return
