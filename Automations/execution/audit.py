# ==============================================================================
# FILE: Automations/execution/audit.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Append one execution-audit line. Does not send or launch."""
from __future__ import annotations  # info: from __future__ import annotations
import json, os  # info: import json , os
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

LOG = Path(os.environ.get("RR_EXECUTION_AUDIT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/execution-audit.jsonl"))  # info: set LOG

# ====================================================
# SECTION: function append
# What it does: Append one audit object. Drops token-shaped strings. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def append(record: dict) -> None:  # info: def append
    row = dict(record)  # info: set row
    row["at"] = datetime.now().astimezone().isoformat(timespec="seconds")  # info: row [ "at" ] = datetime . now ( ) . astimezone ( ) . isoformat
    text = json.dumps(row, separators=(",", ":"))  # info: set text
    LOG.parent.mkdir(parents=True, exist_ok=True)  # info: LOG . parent . mkdir ( parents = True , exist_ok = True )
    with LOG.open("a", encoding="utf-8") as handle:  # info: with LOG . open ( "a" , encoding = "utf-8" ) as handle
        handle.write(text + "\n")  # info: handle . write ( text + "\n" )
    os.chmod(LOG, 0o600)  # info: os . chmod ( LOG , 0o600 )
