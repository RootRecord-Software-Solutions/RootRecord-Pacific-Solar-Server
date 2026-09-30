# ==============================================================================
# FILE: Energy/Cloud-Quota/scripts/store.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Write a labeled cloud quota snapshot. Does not call EcoFlow."""  # info: """Write a labeled cloud quota snapshot. Does not call EcoFlow."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

ENERGY_LIB = Path(__file__).resolve().parents[2] / "lib"  # info: set ENERGY_LIB
if str(ENERGY_LIB) not in sys.path:  # info: if str ( ENERGY_LIB ) not in sys
    sys.path.insert(0, str(ENERGY_LIB))  # info: sys . path . insert ( 0 ,

from paths import CLOUD_QUOTA, CLOUD_QUOTA_LOG  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST


# ====================================================
# SECTION: function write_cloud_snapshot
# What it does: Persist one cloud snapshot and append one log line. No secrets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_cloud_snapshot(snap: dict) -> Path:  # info: def write_cloud_snapshot
    """Persist one cloud snapshot and append one log line. No secrets."""  # info: """Persist one cloud snapshot and append one log line. No secrets."""
    CLOUD_QUOTA.mkdir(parents=True, exist_ok=True)  # info: CLOUD_QUOTA . mkdir ( parents = True ,
    CLOUD_QUOTA_LOG.mkdir(parents=True, exist_ok=True)  # info: CLOUD_QUOTA_LOG . mkdir ( parents = True ,
    alias = str(snap.get("alias") or "unknown")  # info: set alias
    stamp = datetime.now(HST).strftime("%Y%m%d-%H%M%S")  # info: set stamp
    path = CLOUD_QUOTA / f"read-{alias}-{stamp}.json"  # info: set path
    path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps (
    soc = (snap.get("fields") or {}).get("soc")  # info: set soc
    line = f"{snap.get('at')} alias={alias} source=cloud soc={soc}\n"  # info: set line
    with (CLOUD_QUOTA_LOG / "quota.log").open("a", encoding="utf-8") as fh:  # info: with ( CLOUD_QUOTA_LOG / "quota.log" ) . open
        fh.write(line)  # info: fh . write ( line )
    return path  # info: return path
