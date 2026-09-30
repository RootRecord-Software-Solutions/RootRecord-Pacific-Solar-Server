# ==============================================================================
# FILE: Website/lib/envload.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Load Stripe and Vercel key names from central master-key.env only. Never print secrets."""  # info: """Load Stripe and Vercel key names from central master-key.env only. Never print secrets."""
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
    "STRIPE_SECRET_KEY",  # info: "STRIPE_SECRET_KEY" ,
    "AVA_STRIPE_SECRET_KEY",  # info: "AVA_STRIPE_SECRET_KEY" ,
    "VERCEL_TOKEN",  # info: "VERCEL_TOKEN" ,
    "VERCEL_API_TOKEN",  # info: "VERCEL_API_TOKEN" ,
    "VERCEL_TEAM_ID",  # info: "VERCEL_TEAM_ID" ,
    "VERCEL_ORG_ID",  # info: "VERCEL_ORG_ID" ,
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
# SECTION: function stripe_secret
# What it does: stripe secret.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stripe_secret() -> str:  # info: def stripe_secret
    load_env()  # info: call load_env
    return (os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("AVA_STRIPE_SECRET_KEY") or "").strip()  # info: return ( os . environ . get (


# ====================================================
# SECTION: function vercel_token
# What it does: vercel token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def vercel_token() -> str:  # info: def vercel_token
    load_env()  # info: call load_env
    return (os.environ.get("VERCEL_TOKEN") or os.environ.get("VERCEL_API_TOKEN") or "").strip()  # info: return ( os . environ . get (


# ====================================================
# SECTION: function vercel_team_id
# What it does: vercel team id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def vercel_team_id() -> str:  # info: def vercel_team_id
    load_env()  # info: call load_env
    return (os.environ.get("VERCEL_TEAM_ID") or os.environ.get("VERCEL_ORG_ID") or "").strip()  # info: return ( os . environ . get (
