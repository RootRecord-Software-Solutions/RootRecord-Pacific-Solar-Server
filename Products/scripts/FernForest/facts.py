# ==============================================================================
# FILE: Products/scripts/FernForest/facts.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Public Fern Forest lot facts. No owner names, mailing addresses, or watts."""  # info: """Public Fern Forest lot facts. No owner names, mailing addresses, or watts."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
from pathlib import Path  # info: from pathlib import Path

FACTS = Path(  # info: set FACTS
    "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/FernForest/facts.json"  # info: "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Products/FernForest/facts.json"
)  # info: )


# ====================================================
# SECTION: function load
# What it does: load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load() -> dict:  # info: def load
    data = json.loads(FACTS.read_text(encoding="utf-8"))  # info: set data
    if not isinstance(data, dict):  # info: if not isinstance ( data , dict )
        raise SystemExit("facts file is not an object")  # info: raise SystemExit ( "facts file is not an object" )
    return data  # info: return data


# ====================================================
# SECTION: function lines
# What it does: lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lines(data: dict) -> list[str]:  # info: def lines
    out = [  # info: set out
        f"{data.get('place')} — {data.get('acres')} acres, {data.get('class')}",  # info: f" { data . get ( 'place' )
    ]  # info: ]
    for lot in data.get("lots") or []:  # info: for lot in data . get ( "lots"
        if not isinstance(lot, dict):  # info: if not isinstance ( lot , dict )
            continue  # info: continue
        out.append(  # info: out . append (
            f"- TMK {lot.get('tmk')} lot {lot.get('lot')} {lot.get('qpublic')}"  # info: f" - TMK { lot . get ( 'tmk'
        )  # info: )
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
