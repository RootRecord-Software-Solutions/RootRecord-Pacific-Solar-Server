# ==============================================================================
# FILE: Energy/scripts/consolidate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Consolidate EcoFlow layer buckets.

  python3 consolidate.py minutes   # :00 — 1sec into 1min, 5min, 15min
  python3 consolidate.py hours     # :30 — hour and above, plus periods.json
"""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

PACIFIC = Path(__file__).resolve().parents[2]  # info: set PACIFIC
if str(PACIFIC) not in sys.path:  # info: if str ( PACIFIC ) not in sys . path
    sys.path.insert(0, str(PACIFIC))  # info: sys . path . insert ( 0 , str ( PACIFIC ) )

from Energy.db.condense import consolidate_minutes, condense_hours  # noqa: E402


# ====================================================
# SECTION: function main
# What it does: Run the minute roll-up or the hour roll-up from the first argument.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    args = list(argv if argv is not None else sys.argv[1:])  # info: set args
    mode = (args[0] if args else "").strip().lower()  # info: set mode
    if mode in ("minutes", "minute", "min"):  # info: if mode is the minute roll-up
        count = consolidate_minutes()  # info: set count
        print(f"SUMMARY=ecoflow_layers minutes={count}")  # info: call print
        return 0  # info: return 0
    if mode in ("hours", "hour"):  # info: if mode is the hour roll-up
        count = condense_hours()  # info: set count
        print(f"SUMMARY=ecoflow_layers hours={count} json=periods.json")  # info: call print
        return 0  # info: return 0
    print("usage: consolidate.py minutes|hours", file=sys.stderr)  # info: call print
    return 2  # info: return 2


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
