# ==============================================================================
# FILE: Energy/Cloud-Quota/scripts/quota_poll.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""EcoFlow cloud quota poll. Dry status unless RR_ECOFLOW_CLOUD=1.

Default run prints cloud=off, device aliases, and whether key names are set.
It does not call EcoFlow, does not write samples, and does not print secret values.
"""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent  # info: set HERE
ENERGY_LIB = HERE.parents[1] / "lib"  # info: set ENERGY_LIB
if str(ENERGY_LIB) not in sys.path:  # info: if str ( ENERGY_LIB ) not in sys
    sys.path.insert(0, str(ENERGY_LIB))  # info: sys . path . insert ( 0 ,
if str(HERE) not in sys.path:  # info: if str ( HERE ) not in sys
    sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,

from config import device as device_cfg, load as load_conf  # noqa: E402
from ecoflow_api import map_quota_to_fields  # noqa: E402
from envload import ALLOW, load_env  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
SKIP = {"paths", "inventory", "ble", "env"}  # info: set SKIP
# ====================================================
# SECTION: KEY_NAMES
# What it does: Set KEY_NAMES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
KEY_NAMES = (  # info: set KEY_NAMES
    "ECOFLOW_ACCESS",  # info: "ECOFLOW_ACCESS" ,
    "ECOFLOW_SECRET",  # info: "ECOFLOW_SECRET" ,
    "ECOFLOW_REGION",  # info: "ECOFLOW_REGION" ,
    "ECOFLOW_DELTA_2",  # info: "ECOFLOW_DELTA_2" ,
    "ECOFLOW_RIVER_2_PRO",  # info: "ECOFLOW_RIVER_2_PRO" ,
    "ECOFLOW_DELTA_2_SECONDARY",  # info: "ECOFLOW_DELTA_2_SECONDARY" ,
)  # info: )


# ====================================================
# SECTION: function aliases
# What it does: aliases.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def aliases() -> list[str]:  # info: def aliases
    cp = load_conf()  # info: set cp
    return [section for section in cp.sections() if section not in SKIP]  # info: return [ section for section in cp .


# ====================================================
# SECTION: function key_state
# What it does: key state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def key_state(name: str) -> str:  # info: def key_state
    if name not in ALLOW:  # info: if name not in ALLOW :
        return "not-allowlisted"  # info: return "not-allowlisted"
    value = (os.environ.get(name) or "").strip()  # info: set value
    if not value:  # info: if not value :
        return "missing"  # info: return "missing"
    return "set"  # info: return "set"


# ====================================================
# SECTION: function status_lines
# What it does: status lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def status_lines() -> list[str]:  # info: def status_lines
    mapped = map_quota_to_fields({"pd.soc": 55})  # info: set mapped
    lines = [  # info: set lines
        "cloud=off",  # info: "cloud=off" ,
        "aliases: " + ", ".join(aliases()),  # info: "aliases: " + ", " . join ( aliases (
    ]  # info: ]
    lines.extend(f"{name}: {key_state(name)}" for name in KEY_NAMES)  # info: lines . extend ( f" { name }
    lines.append(f"fixture pd.soc={mapped.get('soc')}")  # info: lines . append ( f" fixture pd.soc= { mapped
    return lines  # info: return lines


# ====================================================
# SECTION: function poll_cloud
# What it does: Signed-off path. Reached only when RR_ECOFLOW_CLOUD=1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poll_cloud() -> int:  # info: def poll_cloud
    """Signed-off path. Reached only when RR_ECOFLOW_CLOUD=1."""  # info: """Signed-off path. Reached only when RR_ECOFLOW_CLOUD=1."""
    from ecoflow_api import EcoflowApiError, fetch_device_fields  # info: from ecoflow_api import EcoflowApiError , fetch_device_fields
    from store import write_cloud_snapshot  # info: from store import write_cloud_snapshot

    print("cloud=on")  # info: call print
    print("aliases: " + ", ".join(aliases()))  # info: call print
    failed = False  # info: set failed
    for alias in aliases():  # info: for alias in aliases ( ) :
        try:  # info: try :
            cfg = device_cfg(alias)  # info: set cfg
        except KeyError:  # info: except KeyError :
            print(f"alias={alias} skip=unknown")  # info: call print
            failed = True  # info: set failed
            continue  # info: continue
        if not (cfg.get("sn") or "").strip():  # info: if not ( cfg . get ( "sn"
            print(f"alias={alias} skip=no-sn")  # info: call print
            failed = True  # info: set failed
            continue  # info: continue
        try:  # info: try :
            fields = fetch_device_fields(cfg["sn"].strip())  # info: set fields
        except EcoflowApiError as exc:  # info: except EcoflowApiError as exc :
            print(f"alias={alias} error={type(exc).__name__}: {exc}")  # info: call print
            failed = True  # info: set failed
            continue  # info: continue
        snap = {  # info: set snap
            "alias": alias,  # info: "alias" : alias ,
            "fields": fields,  # info: "fields" : fields ,
            "at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "at" : datetime . now ( HST )
            "source": "cloud",  # info: "source" : "cloud" ,
        }  # info: }
        path = write_cloud_snapshot(snap)  # info: set path
        print(f"alias={alias} source=cloud wrote={path.name}")  # info: call print
    return 1 if failed else 0  # info: return 1 if failed else 0


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    load_env()  # info: call load_env
    if os.environ.get("RR_ECOFLOW_CLOUD", "0") != "1":  # info: if os . environ . get ( "RR_ECOFLOW_CLOUD"
        print("\n".join(status_lines()))  # info: call print
        return 0  # info: return 0
    return poll_cloud()  # info: return poll_cloud ( )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
