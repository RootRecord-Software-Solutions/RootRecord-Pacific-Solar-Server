#!/usr/bin/env python3
"""EcoFlow cloud quota poll. Dry status unless RR_ECOFLOW_CLOUD=1.

Default run prints cloud=off, device aliases, and whether key names are set.
It does not call EcoFlow, does not write samples, and does not print secret values.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ENERGY_LIB = HERE.parents[1] / "lib"
if str(ENERGY_LIB) not in sys.path:
    sys.path.insert(0, str(ENERGY_LIB))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from config import device as device_cfg, load as load_conf  # noqa: E402
from ecoflow_api import map_quota_to_fields  # noqa: E402
from envload import ALLOW, load_env  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")
SKIP = {"paths", "inventory", "ble", "env"}
KEY_NAMES = (
    "ECOFLOW_ACCESS",
    "ECOFLOW_SECRET",
    "ECOFLOW_REGION",
    "ECOFLOW_DELTA_2",
    "ECOFLOW_RIVER_2_PRO",
    "ECOFLOW_DELTA_2_SECONDARY",
)


def aliases() -> list[str]:
    cp = load_conf()
    return [section for section in cp.sections() if section not in SKIP]


def key_state(name: str) -> str:
    if name not in ALLOW:
        return "not-allowlisted"
    value = (os.environ.get(name) or "").strip()
    if not value:
        return "missing"
    return "set"


def status_lines() -> list[str]:
    mapped = map_quota_to_fields({"pd.soc": 55})
    lines = [
        "cloud=off",
        "aliases: " + ", ".join(aliases()),
    ]
    lines.extend(f"{name}: {key_state(name)}" for name in KEY_NAMES)
    lines.append(f"fixture pd.soc={mapped.get('soc')}")
    return lines


def poll_cloud() -> int:
    """Signed-off path. Reached only when RR_ECOFLOW_CLOUD=1."""
    from ecoflow_api import EcoflowApiError, fetch_device_fields
    from store import write_cloud_snapshot

    print("cloud=on")
    print("aliases: " + ", ".join(aliases()))
    failed = False
    for alias in aliases():
        try:
            cfg = device_cfg(alias)
        except KeyError:
            print(f"alias={alias} skip=unknown")
            failed = True
            continue
        if not (cfg.get("sn") or "").strip():
            print(f"alias={alias} skip=no-sn")
            failed = True
            continue
        try:
            fields = fetch_device_fields(cfg["sn"].strip())
        except EcoflowApiError as exc:
            print(f"alias={alias} error={type(exc).__name__}: {exc}")
            failed = True
            continue
        snap = {
            "alias": alias,
            "fields": fields,
            "at": datetime.now(HST).isoformat(timespec="seconds"),
            "source": "cloud",
        }
        path = write_cloud_snapshot(snap)
        print(f"alias={alias} source=cloud wrote={path.name}")
    return 1 if failed else 0


def main() -> int:
    load_env()
    if os.environ.get("RR_ECOFLOW_CLOUD", "0") != "1":
        print("\n".join(status_lines()))
        return 0
    return poll_cloud()


if __name__ == "__main__":
    raise SystemExit(main())
