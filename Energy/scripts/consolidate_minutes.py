# ==============================================================================
# FILE: Energy/scripts/consolidate_minutes.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Roll closed EcoFlow samples into the minute, 5-minute, and 15-minute buckets."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

PACIFIC = Path(__file__).resolve().parents[2]  # info: set PACIFIC
if str(PACIFIC) not in sys.path:  # info: if str ( PACIFIC ) not in sys . path
    sys.path.insert(0, str(PACIFIC))  # info: sys . path . insert ( 0 , str ( PACIFIC ) )

from Energy.db.condense import consolidate_minutes  # noqa: E402


# ====================================================
# SECTION: function main
# What it does: Consolidate the closed minute buckets and print how many rows were written.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    count = consolidate_minutes()  # info: set count
    print(f"SUMMARY=ecoflow_layers minutes={count}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
