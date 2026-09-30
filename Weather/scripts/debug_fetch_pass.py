# ==============================================================================
# FILE: Weather/scripts/debug_fetch_pass.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""One-off diagnostic -- NOT part of the deployed daemon, run by hand.

run_once()'s own log only prints on a whole-*module* exception; individual
resource failures inside fetch/_engine.py's run_resource() are caught
there and recorded on the Manifest (status + a counter), but the actual
reason (the exception string, or a validation/change-detection reason) is
carried on the in-memory FetchOutcome and normally just discarded once
run_cycle.py's dispatch loop moves on. This script calls every fetch
module directly, the same way run_once() does, and prints every single
outcome's resource_id / status / detail so a silent batch of failures
(wrong host, timeout, 403, validation failure, etc.) is visible in one
pass instead of needing per-resource instrumentation added and redeployed.

Safe to run any time: same fetch_all() calls run_once() already makes,
against the real base_dir, so it participates in the same manifest /
change-detection / archiving as a normal cycle -- it does not create a
second manifest or a parallel code path.
"""
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

_WEATHER_ROOT = Path(__file__).resolve().parent.parent  # info: set _WEATHER_ROOT
sys.path.insert(0, str(_WEATHER_ROOT))  # info: sys . path . insert ( 0 ,

from core.manifest import Manifest  # noqa: E402
from scheduler import run_cycle  # noqa: E402

BASE_DIR = "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Weather/Hawai'i/hfo"  # info: set BASE_DIR

# ====================================================
# SECTION: block if
# What it does: __name__ == '__main__'
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
if __name__ == "__main__":  # info: if __name__ == "__main__" :
    manifest = Manifest(BASE_DIR).load()  # info: set manifest

    total = ok = unchanged = failed = invalid = 0  # info: set total
    for name, fetch_fn in run_cycle.FETCH_MODULES.items():  # info: for name , fetch_fn in run_cycle . FETCH_MODULES
        print(f"\n=== {name} ===")  # info: call print
        try:  # info: try :
            outcomes = fetch_fn(manifest, BASE_DIR)  # info: set outcomes
        except Exception as e:  # info: except Exception as e :
            print(f"  MODULE RAISED: {type(e).__name__}: {e}")  # info: call print
            continue  # info: continue
        for o in outcomes:  # info: for o in outcomes :
            total += 1  # info: set total
            if o.status == "written":  # info: if o . status == "written" :
                ok += 1  # info: set ok
            elif o.status == "unchanged":  # info: elif o . status == "unchanged" :
                unchanged += 1  # info: set unchanged
            elif o.status == "invalid":  # info: elif o . status == "invalid" :
                invalid += 1  # info: set invalid
            else:  # info: else :
                failed += 1  # info: set failed
            print(f"  {o.resource_id:<30} {o.status:<10} {o.detail}")  # info: call print

    manifest.save()  # info: manifest . save ( )
    print(f"\n=== TOTAL: {total}  written={ok}  unchanged={unchanged}  invalid={invalid}  failed={failed} ===")  # info: call print
