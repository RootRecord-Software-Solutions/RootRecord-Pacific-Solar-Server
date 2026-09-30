# ==============================================================================
# FILE: Energy/lib/envload.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Load EcoFlow keys from central master-key.env only. Never print secrets."""  # info: """Load EcoFlow keys from central master-key.env only. Never print secrets."""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
from pathlib import Path  # info: from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")  # info: set MASTER_KEY_ENV
# ====================================================
# SECTION: ALLOW
# What it does: Set ALLOW.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ALLOW = frozenset({  # info: set ALLOW
    "AVA_ECOFLOW_USER_ID",  # info: "AVA_ECOFLOW_USER_ID" ,
    "ECOFLOW_ACCOUNT_ID",  # info: "ECOFLOW_ACCOUNT_ID" ,
    "ECOFLOW_DELTA_2",  # info: "ECOFLOW_DELTA_2" ,
    "ECOFLOW_RIVER_2_PRO",  # info: "ECOFLOW_RIVER_2_PRO" ,
    "ECOFLOW_DELTA_2_SECONDARY",  # info: "ECOFLOW_DELTA_2_SECONDARY" ,
    "ECOFLOW_DELTA_2_NAME",  # info: "ECOFLOW_DELTA_2_NAME" ,
    "ECOFLOW_DELTA_2_SECONDARY_NAME",  # info: "ECOFLOW_DELTA_2_SECONDARY_NAME" ,
    "ECOFLOW_RIVER_2_PRO_NAME",  # info: "ECOFLOW_RIVER_2_PRO_NAME" ,
    "ECOFLOW_ACCESS",  # info: "ECOFLOW_ACCESS" ,
    "ECOFLOW_SECRET",  # info: "ECOFLOW_SECRET" ,
    "ECOFLOW_REGION",  # info: "ECOFLOW_REGION" ,
})  # info: } )


# ====================================================
# SECTION: function load_env
# What it does: load env.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_env(paths: list[Path] | None = None) -> None:  # info: def load_env
    for env in paths or [MASTER_KEY_ENV]:  # info: for env in paths or [ MASTER_KEY_ENV ]
        if not env.is_file():  # info: if not env . is_file ( ) :
            continue  # info: continue
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():  # info: for line in env . read_text ( encoding
            s = line.strip()  # info: set s
            if not s or s.startswith("#") or "=" not in s:
                continue  # info: continue
            k, _, v = s.partition("=")  # info: k , _ , v = s .
            k, v = k.strip(), v.strip().strip('"').strip("'")  # info: k , v = k . strip (
            if not k or k not in ALLOW:  # info: if not k or k not in ALLOW
                continue  # info: continue
            if k not in os.environ:  # info: if k not in os . environ :
                os.environ[k] = v  # info: os . environ [ k ] = v


# ====================================================
# SECTION: function user_id
# What it does: user id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def user_id() -> str:  # info: def user_id
    load_env()  # info: call load_env
    uid = (os.environ.get("AVA_ECOFLOW_USER_ID") or "").strip()  # info: set uid
    if not uid:  # info: if not uid :
        uid = (os.environ.get("ECOFLOW_ACCOUNT_ID") or "").strip()  # info: set uid
    return uid  # info: return uid


# ====================================================
# SECTION: function api_keys
# What it does: api keys.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def api_keys() -> tuple[str, str]:  # info: def api_keys
    load_env()  # info: call load_env
    access = (os.environ.get("ECOFLOW_ACCESS") or "").strip()  # info: set access
    secret = (os.environ.get("ECOFLOW_SECRET") or "").strip()  # info: set secret
    return access, secret  # info: return access , secret


# ====================================================
# SECTION: function env_sn
# What it does: Resolve SN from env the same way BLE inventory names are set.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def env_sn(alias: str) -> str:  # info: def env_sn
    """Resolve SN from env the same way BLE inventory names are set."""  # info: """Resolve SN from env the same way BLE inventory names are set."""
    load_env()  # info: call load_env
    key = {  # info: set key
        "delta2": "ECOFLOW_DELTA_2",  # info: "delta2" : "ECOFLOW_DELTA_2" ,
        "river2pro": "ECOFLOW_RIVER_2_PRO",  # info: "river2pro" : "ECOFLOW_RIVER_2_PRO" ,
        "security": "ECOFLOW_DELTA_2_SECONDARY",  # info: "security" : "ECOFLOW_DELTA_2_SECONDARY" ,
        "b3": "ECOFLOW_DELTA_2_SECONDARY",  # info: "b3" : "ECOFLOW_DELTA_2_SECONDARY" ,
    }.get(alias, "")  # info: } . get ( alias , "" )
    return (os.environ.get(key) or "").strip() if key else ""  # info: return ( os . environ . get (


# ====================================================
# SECTION: function env_name
# What it does: env name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def env_name(alias: str) -> str:  # info: def env_name
    load_env()  # info: call load_env
    key = {  # info: set key
        "delta2": "ECOFLOW_DELTA_2_NAME",  # info: "delta2" : "ECOFLOW_DELTA_2_NAME" ,
        "river2pro": "ECOFLOW_RIVER_2_PRO_NAME",  # info: "river2pro" : "ECOFLOW_RIVER_2_PRO_NAME" ,
        "security": "ECOFLOW_DELTA_2_SECONDARY_NAME",  # info: "security" : "ECOFLOW_DELTA_2_SECONDARY_NAME" ,
        "b3": "ECOFLOW_DELTA_2_SECONDARY_NAME",  # info: "b3" : "ECOFLOW_DELTA_2_SECONDARY_NAME" ,
    }.get(alias, "")  # info: } . get ( alias , "" )
    return (os.environ.get(key) or "").strip() if key else ""  # info: return ( os . environ . get (
