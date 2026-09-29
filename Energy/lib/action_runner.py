#!/usr/bin/env python3
"""CLI: apply one BLE bool action or report honest WAITING/No data."""
from __future__ import annotations
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from paths import SAMPLES, PORTS, ensure_dirs, BLE_LOG  # noqa: E402
from ble_client import apply_bool, BleUnavailable, eflib_ready  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")


def _log(msg: str) -> None:
    ensure_dirs()
    line = f"{datetime.now(HST).isoformat(timespec='seconds')} action: {msg}\n"
    with BLE_LOG.open("a", encoding="utf-8") as f:
        f.write(line)
    print(msg)


def _write_sample(kind: str, payload: dict) -> Path:
    ensure_dirs()
    ts = datetime.now(HST).strftime("%Y%m%d-%H%M%S")
    path = SAMPLES / f"{kind}-{ts}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (PORTS / f"{payload.get('alias', 'dev')}-last.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return path


def main() -> int:
    p = argparse.ArgumentParser(description="EcoFlow atomic BLE action")
    p.add_argument("--device", required=True, help="delta2|river2pro")
    p.add_argument("--method", required=True, help="eflib enable_* method name")
    p.add_argument("--want", required=True, choices=("on", "off", "true", "false", "1", "0"))
    p.add_argument("--label", default="", help="human label for logs")
    args = p.parse_args()
    want = args.want in ("on", "true", "1")
    ok, reason = eflib_ready()
    if not ok:
        _log(f"WAITING / No data — {reason}")
        print("STATUS=WAITING")
        return 2
    try:
        snap = asyncio.run(apply_bool(args.device, args.method, want))
    except BleUnavailable as e:
        _log(f"WAITING / No data — {e}")
        print("STATUS=WAITING")
        return 2
    except Exception as e:
        _log(f"FAIL — {type(e).__name__}: {e}")
        print("STATUS=FAIL")
        return 1
    snap["label"] = args.label or f"{args.device}.{args.method}={'on' if want else 'off'}"
    snap["at"] = datetime.now(HST).isoformat(timespec="seconds")
    path = _write_sample(f"{args.device}-{args.method}-{'on' if want else 'off'}", snap)
    _log(f"OK {snap['label']} readback={snap.get('readback')} sample={path}")
    print("STATUS=OK")
    print(json.dumps(snap))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
