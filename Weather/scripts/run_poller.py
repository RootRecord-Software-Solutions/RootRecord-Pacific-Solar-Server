#!/usr/bin/env python3
"""Boot entry point for the `weather` skill's scheduler daemon.

Wires up the real deploy paths (per nextagent.md's stated code/data tree
split -- code under .ollama/skills/weather/, data under Database/) and
starts scheduler/run_cycle.py's run_forever() loop. This file is what
automations/scripts/ensure-weather-poller.sh launches in the background;
it is not meant to be imported.

Not run directly by automations/'s own job dispatcher (which runs each
job's command to completion, blocking, with a timeout) -- this process is
long-running by design, so it's started once as a detached background
daemon instead. See scripts/ensure-weather-poller.sh for the check-and
-start logic, matching the same pattern already used in this stack for
other persistent services (a-eyes cam server, council-relay, Ollama, FLM).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# weather/ itself needs to be importable as the root for `core`, `fetch`,
# `alerts`, `scheduler`, `hurricanes`, `archive` -- exactly how every
# module in this tree and every test file already assumes (see
# tests/run_tests_no_pytest.py's sys.path handling for the same pattern).
_WEATHER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_WEATHER_ROOT))

from scheduler import run_cycle  # noqa: E402

# Per nextagent.md Section 1 (the hard code/data split) and
# hurricanes/scripts/sources.py's own docstring (hurricanes tracking data
# lives in a sibling "hurricanes/" folder next to "hfo/", both under the
# same Hawai'i parent -- NOT nested inside hfo/).
# Pacific import 2026-09-29: data under the canonical Database root (env override kept).
_DATA = os.environ.get("WEATHER_DATA_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/WEATHER/Hawai'i")
BASE_DIR = os.environ.get("WEATHER_BASE_DIR", _DATA + "/hfo")
HURRICANES_BASE_DIR = os.environ.get("WEATHER_HURRICANES_DIR", _DATA + "/hurricanes")

if __name__ == "__main__":
    run_cycle.run_forever(BASE_DIR, HURRICANES_BASE_DIR)
