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
"""Write a labeled cloud quota snapshot from Energy/layers/1sec.db. Does not call EcoFlow."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

PACIFIC = Path(__file__).resolve().parents[3]  # info: set PACIFIC
ENERGY_LIB = Path(__file__).resolve().parents[2] / "lib"  # info: set ENERGY_LIB
SYSTEM_LIB = PACIFIC / "System" / "lib"  # info: set SYSTEM_LIB
for path in (str(PACIFIC), str(ENERGY_LIB), str(SYSTEM_LIB)):  # info: for path in ( str ( PACIFIC ) , str ( ENERGY_LIB ) )
    if path not in sys.path:  # info: if path not in sys . path
        sys.path.insert(0, path)  # info: sys . path . insert ( 0 , path )

from paths import CLOUD_QUOTA, CLOUD_QUOTA_LOG  # noqa: E402
from Energy.db.latest import latest_for_alias  # noqa: E402
from current_bank import write_current_json  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
BOARD_KEYS = (  # info: same keys BLE samples use on the desk
    "soc",  # info: soc
    "ac_output_power",  # info: ac_output_power
    "ac_input_power",  # info: ac_input_power
    "solar_input_power",  # info: solar_input_power
    "usbc_output_power",  # info: usbc_output_power
    "usba_output_power",  # info: usba_output_power
    "ac_ports",  # info: ac_ports
    "usb_ports",  # info: usb_ports
    "dc_12v_port",  # info: dc_12v_port
)  # info: end BOARD_KEYS


# ====================================================
# SECTION: function write_cloud_snapshot
# What it does: Rebuild one Cloud-Quota JSON file and quota.log line from Energy/layers/1sec.db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_cloud_snapshot(snap: dict | None = None, alias: str | None = None) -> Path | None:  # info: def write_cloud_snapshot
    """Rebuild one Cloud-Quota JSON file and quota.log line from Energy/layers/1sec.db."""  # info: docstring
    name = alias or (snap or {}).get("alias") or "unknown"  # info: set name
    row = latest_for_alias(str(name))  # info: set row
    if not row:  # info: if not row
        return None  # info: return None
    CLOUD_QUOTA.mkdir(parents=True, exist_ok=True)  # info: CLOUD_QUOTA . mkdir
    path = CLOUD_QUOTA / f"read-{name}_current.json"  # info: stable *_current live path — no stamp flood
    source = (snap or {}).get("source") or "cloud"  # info: set source
    payload = {  # info: set payload
        "alias": row.get("alias") or name,  # info: "alias"
        "at": row.get("observed_at"),  # info: "at"
        "source": source,  # info: "source"
        "fields": {key: row.get(key) for key in BOARD_KEYS},  # info: same board field set as BLE
    }  # info: end payload
    write_current_json(path, payload)  # info: archive prior _current then write
    line = f"{payload['at']} alias={name} source={source} soc={payload['fields'].get('soc')}\n"  # info: set line
    with (CLOUD_QUOTA_LOG / "quota.log").open("a", encoding="utf-8") as fh:  # info: quota.log next to Cloud-Quota JSON
        fh.write(line)  # info: fh . write
    return path  # info: return path
