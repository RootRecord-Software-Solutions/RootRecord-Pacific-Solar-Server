# ==============================================================================
# FILE: Energy/lib/action_runner.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""CLI: apply one BLE bool action or report honest WAITING/No data."""  # info: """CLI: apply one BLE bool action or report honest WAITING/No data."""
from __future__ import annotations  # info: from __future__ import annotations
import argparse  # info: import argparse
import asyncio  # info: import asyncio
import json  # info: import json
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent  # info: set HERE
# Energy/lib must win over System/lib so `paths` exposes BLE_LOG/PORTS, not System samples.
sys.path.insert(0, str(HERE.parent.parent / "System" / "lib"))  # info: shared *_current bank helper
sys.path.insert(0, str(HERE))  # info: Energy/lib paths last

from paths import SAMPLES, PORTS, ensure_dirs, BLE_LOG  # noqa: E402
from ble_client import apply_bool, BleUnavailable, eflib_ready  # noqa: E402
from current_bank import write_current_json  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST


# ====================================================
# SECTION: function _log
# What it does:  log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log(msg: str) -> None:  # info: def _log
    BLE_LOG.parent.mkdir(parents=True, exist_ok=True)  # info: create Energy/logs only when an action actually logs
    line = f"{datetime.now(HST).isoformat(timespec='seconds')} action: {msg}\n"  # info: set line
    with BLE_LOG.open("a", encoding="utf-8") as f:  # info: with BLE_LOG . open ( "a" , encoding
        f.write(line)  # info: f . write ( line )
    print(msg)  # info: call print


# ====================================================
# SECTION: function _write_sample
# What it does:  write sample.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_sample(kind: str, payload: dict) -> Path:  # info: def _write_sample
    ensure_dirs()  # info: call ensure_dirs
    path = SAMPLES / f"{kind}_current.json"  # info: stable *_current — no stamp flood
    write_current_json(path, payload)  # info: archive prior _current then write
    (PORTS / f"{payload.get('alias', 'dev')}_current.json").write_text(  # info: call (
        json.dumps(payload, indent=2), encoding="utf-8"  # info: json . dumps ( payload , indent =
    )  # info: )
    return path  # info: return path


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    p = argparse.ArgumentParser(description="EcoFlow atomic BLE action")  # info: set p
    p.add_argument("--device", required=True, help="delta2|river2pro")  # info: p . add_argument ( "--device" , required =
    p.add_argument("--method", required=True, help="eflib enable_* method name")  # info: p . add_argument ( "--method" , required =
    p.add_argument("--want", required=True, choices=("on", "off", "true", "false", "1", "0"))  # info: p . add_argument ( "--want" , required =
    p.add_argument("--label", default="", help="human label for logs")  # info: p . add_argument ( "--label" , default =
    args = p.parse_args()  # info: set args
    want = args.want in ("on", "true", "1")  # info: set want
    ok, reason = eflib_ready()  # info: ok , reason = eflib_ready ( )
    if not ok:  # info: if not ok :
        _log(f"WAITING / No data — {reason}")  # info: call _log
        print("STATUS=WAITING")  # info: call print
        return 2  # info: return 2
    try:  # info: try :
        snap = asyncio.run(apply_bool(args.device, args.method, want))  # info: set snap
    except BleUnavailable as e:  # info: except BleUnavailable as e :
        _log(f"WAITING / No data — {e}")  # info: call _log
        print("STATUS=WAITING")  # info: call print
        return 2  # info: return 2
    except Exception as e:  # info: except Exception as e :
        _log(f"FAIL — {type(e).__name__}: {e}")  # info: call _log
        print("STATUS=FAIL")  # info: call print
        return 1  # info: return 1
    snap["label"] = args.label or f"{args.device}.{args.method}={'on' if want else 'off'}"  # info: snap [ "label" ] = args . label
    snap["at"] = datetime.now(HST).isoformat(timespec="seconds")  # info: snap [ "at" ] = datetime . now
    path = _write_sample(f"{args.device}-{args.method}-{'on' if want else 'off'}", snap)  # info: set path
    _log(f"OK {snap['label']} readback={snap.get('readback')} sample={path}")  # info: call _log
    print("STATUS=OK")  # info: call print
    print(json.dumps(snap))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
