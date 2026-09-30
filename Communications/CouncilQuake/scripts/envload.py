# ==============================================================================
# FILE: Communications/CouncilQuake/scripts/envload.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Load the Carly Telegram token from master-key.env. Never print the value."""  # info: """Load the Carly Telegram token from master-key.env. Never print the value."""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
from pathlib import Path  # info: from pathlib import Path

MASTER_KEY_ENV = Path("/home/rootrecord/master/master-key.env")  # info: set MASTER_KEY_ENV
ALLOW = frozenset({"TELEGRAM_CARLY_TOKEN"})  # info: set ALLOW


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
# SECTION: function carly_token
# What it does: carly token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def carly_token() -> str:  # info: def carly_token
    load_env()  # info: call load_env
    return (os.environ.get("TELEGRAM_CARLY_TOKEN") or "").strip()  # info: return ( os . environ . get (
