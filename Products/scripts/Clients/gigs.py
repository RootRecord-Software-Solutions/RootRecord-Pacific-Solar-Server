# ==============================================================================
# FILE: Products/scripts/Clients/gigs.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Gig index. Domain and page names only. The client site is not rehosted."""  # info: """Gig index. Domain and page names only. The client site is not rehosted."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
from pathlib import Path  # info: from pathlib import Path

GIGS = Path(  # info: set GIGS
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/Clients/gigs.json"  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/Clients/gigs.json"
)  # info: )


# ====================================================
# SECTION: function load
# What it does: load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load() -> dict:  # info: def load
    data = json.loads(GIGS.read_text(encoding="utf-8"))  # info: set data
    if not isinstance(data, dict):  # info: if not isinstance ( data , dict )
        raise SystemExit("gigs file is not an object")  # info: raise SystemExit ( "gigs file is not an object" )
    return data  # info: return data


# ====================================================
# SECTION: function lines
# What it does: lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lines(data: dict) -> list[str]:  # info: def lines
    out = ["Web-dev gigs (not memberships):"]  # info: set out
    rows = data.get("gigs") or []  # info: set rows
    if not rows:  # info: if not rows :
        out.append("- none on file")  # info: out . append ( "- none on file" )
        return out  # info: return out
    for row in rows:  # info: for row in rows :
        if not isinstance(row, dict):  # info: if not isinstance ( row , dict )
            continue  # info: continue
        pages = ", ".join(str(p) for p in (row.get("pages") or []))  # info: set pages
        out.append(f"- {row.get('domain')}: {pages}")  # info: out . append ( f" - { row
        note = str(row.get("note") or "").strip()  # info: set note
        if note:  # info: if note :
            out.append(f"  {note}")  # info: out . append ( f" { note
    return out  # info: return out


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    for line in lines(load()):  # info: for line in lines ( load ( )
        print(line)  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
