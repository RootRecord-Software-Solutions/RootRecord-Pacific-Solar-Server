#!/usr/bin/env python3
"""Write a labeled cloud quota snapshot. Does not call EcoFlow."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ENERGY_LIB = Path(__file__).resolve().parents[2] / "lib"
if str(ENERGY_LIB) not in sys.path:
    sys.path.insert(0, str(ENERGY_LIB))

from paths import CLOUD_QUOTA, CLOUD_QUOTA_LOG  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")


def write_cloud_snapshot(snap: dict) -> Path:
    """Persist one cloud snapshot and append one log line. No secrets."""
    CLOUD_QUOTA.mkdir(parents=True, exist_ok=True)
    CLOUD_QUOTA_LOG.mkdir(parents=True, exist_ok=True)
    alias = str(snap.get("alias") or "unknown")
    stamp = datetime.now(HST).strftime("%Y%m%d-%H%M%S")
    path = CLOUD_QUOTA / f"read-{alias}-{stamp}.json"
    path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    soc = (snap.get("fields") or {}).get("soc")
    line = f"{snap.get('at')} alias={alias} source=cloud soc={soc}\n"
    with (CLOUD_QUOTA_LOG / "quota.log").open("a", encoding="utf-8") as fh:
        fh.write(line)
    return path
