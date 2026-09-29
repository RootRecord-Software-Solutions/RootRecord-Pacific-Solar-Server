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
from __future__ import annotations

import sys
from pathlib import Path

_WEATHER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_WEATHER_ROOT))

from core.manifest import Manifest  # noqa: E402
from scheduler import run_cycle  # noqa: E402

BASE_DIR = "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/WEATHER/Hawai'i/hfo"

if __name__ == "__main__":
    manifest = Manifest(BASE_DIR).load()

    total = ok = unchanged = failed = invalid = 0
    for name, fetch_fn in run_cycle.FETCH_MODULES.items():
        print(f"\n=== {name} ===")
        try:
            outcomes = fetch_fn(manifest, BASE_DIR)
        except Exception as e:
            print(f"  MODULE RAISED: {type(e).__name__}: {e}")
            continue
        for o in outcomes:
            total += 1
            if o.status == "written":
                ok += 1
            elif o.status == "unchanged":
                unchanged += 1
            elif o.status == "invalid":
                invalid += 1
            else:
                failed += 1
            print(f"  {o.resource_id:<30} {o.status:<10} {o.detail}")

    manifest.save()
    print(f"\n=== TOTAL: {total}  written={ok}  unchanged={unchanged}  invalid={invalid}  failed={failed} ===")
