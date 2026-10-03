# ==============================================================================
# FILE: Energy/scripts/push/ml1-energy-stats.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Push live EcoFlow soc/watts to ML1 over SSH every minute. No cloud. No poller."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy")  # info: set DB
PACIFIC = Path(  # info: set PACIFIC
    "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server"  # info: Pacific tree
)  # info: )
LIVE_PICTURE = PACIFIC / "Media" / "Video" / "scripts" / "live_picture.py"  # info: set LIVE_PICTURE
HOST = os.environ.get("RR_ENERGY_ML1_HOST", "ml1")  # info: set HOST
REMOTE_JSON = os.environ.get(  # info: set REMOTE_JSON
    "RR_ENERGY_ML1_JSON", "/home/ubuntu/youtube-stills/energy_current.json"  # info: youtube-stills bank
)  # info: )
REMOTE_HOME = os.environ.get(  # info: set REMOTE_HOME
    "RR_ENERGY_ML1_HOME", "/home/ubuntu/energy_current.json"  # info: home copy; not radio state/stage (mixer eats *.json)
)  # info: )
REMOTE_LINE = os.environ.get(  # info: set REMOTE_LINE
    "RR_ENERGY_ML1_LINE", "/home/ubuntu/youtube-stills/energy_current.txt"  # info: one-line ENERGY
)  # info: )
PUSH_THUMB = os.environ.get("RR_ENERGY_ML1_THUMB", "1").strip() != "0"  # info: also refresh YouTube thumb
PACKS = ("river2pro", "delta2")  # info: set PACKS
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
DISCHARGE_SOC = 5.0  # info: set DISCHARGE_SOC
DISCHARGE_AGE_S = 30 * 60  # info: set DISCHARGE_AGE_S


# ====================================================
# SECTION: function _read
# What it does: Load one JSON object from a Database Energy path, or {}.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read(rel: str) -> dict:  # info: def _read
    path = DB / rel  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {}  # info: return {}
    try:  # info: try
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except
        return {}  # info: return {}
    return data if isinstance(data, dict) else {}  # info: return data if isinstance


# ====================================================
# SECTION: function _age_s
# What it does: Seconds since file mtime, or a huge number when missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _age_s(rel: str) -> float:  # info: def _age_s
    path = DB / rel  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return 1e12  # info: return 1e12
    return max(0.0, time.time() - path.stat().st_mtime)  # info: return age


# ====================================================
# SECTION: function _pack
# What it does: One pack row from soc + watts current files, with discharged flag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pack(alias: str) -> dict:  # info: def _pack
    soc_rel = f"soc/{alias}_current.json"  # info: set soc_rel
    watt_rel = f"watts/{alias}_current.json"  # info: set watt_rel
    soc = _read(soc_rel)  # info: set soc
    watts = _read(watt_rel)  # info: set watts
    age = min(_age_s(soc_rel), _age_s(watt_rel))  # info: freshest of the pair
    charge = soc.get("soc")  # info: set charge
    try:  # info: try
        charge_f = float(charge) if charge is not None else None  # info: set charge_f
    except (TypeError, ValueError):  # info: except
        charge_f = None  # info: set charge_f
    discharged = (  # info: set discharged
        charge_f is not None  # info: have a percent
        and charge_f <= DISCHARGE_SOC  # info: at or under 5%
        and age > DISCHARGE_AGE_S  # info: quiet longer than 30 minutes
    )  # info: )
    return {  # info: return {
        "alias": alias,  # info: "alias" : alias ,
        "soc": charge_f,  # info: "soc" : charge_f ,
        "source": watts.get("source") or soc.get("source"),  # info: prefer watt source
        "at": max(str(soc.get("at") or ""), str(watts.get("at") or "")),  # info: freshest stamp
        "age_s": round(age, 1) if age < 1e11 else None,  # info: None when no file
        "discharged_powered_off": discharged,  # info: "discharged_powered_off" : discharged ,
        "ac_output_power": watts.get("ac_output_power"),  # info: "ac_output_power" : watts . get (
        "ac_input_power": watts.get("ac_input_power"),  # info: "ac_input_power" : watts . get (
        "solar_input_power": watts.get("solar_input_power"),  # info: "solar_input_power" : watts . get (
        "usbc_output_power": watts.get("usbc_output_power"),  # info: "usbc_output_power" : watts . get (
        "charge_source": watts.get("charge_source"),  # info: "charge_source" : watts . get (
    }  # info: }


# ====================================================
# SECTION: function build
# What it does: Combined energy_current payload for ML1. Measured files only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build() -> dict:  # info: def build
    packs = {alias: _pack(alias) for alias in PACKS}  # info: set packs
    river = packs["river2pro"]  # info: set river
    delta = packs["delta2"]  # info: set delta
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")  # info: set now
    hst = datetime.now(HST).isoformat(timespec="seconds")  # info: set hst
    line = (  # info: set line
        "ENERGY  "  # info: ENERGY prefix
        + f"B1={'off' if river.get('discharged_powered_off') else river.get('soc')} "  # info: River
        + f"B2={'off' if delta.get('discharged_powered_off') else delta.get('soc')} "  # info: Delta
        + f"ac={river.get('ac_output_power')} "  # info: River AC out (live pack)
        + f"solar_r={river.get('solar_input_power')} solar_d={delta.get('solar_input_power')} "  # info: solar
        + f"src_r={river.get('source')} src_d={delta.get('source')}"  # info: sources
    )  # info: )
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "pushed_at": now,  # info: "pushed_at" : now ,
        "hst": hst,  # info: "hst" : hst ,
        "line": line.strip(),  # info: "line" : line . strip ( ) ,
        "packs": packs,  # info: "packs" : packs ,
        "note": "Pacific BLE/watt current files over SSH. Cloud not used.",  # info: note
    }  # info: }


# ====================================================
# SECTION: function _ssh_write
# What it does: Write bytes to a remote path over ssh BatchMode. Return True on ok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ssh_write(remote: str, body: str) -> bool:  # info: def _ssh_write
    cmd = [  # info: set cmd
        "ssh",  # info: ssh
        "-o",  # info: -o
        "BatchMode=yes",  # info: BatchMode
        "-o",  # info: -o
        "ConnectTimeout=20",  # info: ConnectTimeout
        HOST,  # info: HOST
        f"mkdir -p -- {json.dumps(str(Path(remote).parent))} && cat > {json.dumps(remote)}",  # info: mkdir + cat
    ]  # info: ]
    try:  # info: try
        ran = subprocess.run(  # info: set ran
            cmd,  # info: cmd
            input=body,  # info: input
            text=True,  # info: text
            capture_output=True,  # info: capture
            timeout=40,  # info: timeout
        )  # info: )
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except
        print(f"ml1-energy-stats FAIL ssh {remote}: {exc}", flush=True)  # info: call print
        return False  # info: return False
    if ran.returncode != 0:  # info: if ran . returncode != 0 :
        err = (ran.stderr or ran.stdout or "").strip()[:240]  # info: set err
        print(f"ml1-energy-stats FAIL ssh {remote} rc={ran.returncode} {err}", flush=True)  # info: call print
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function push_json
# What it does: Write energy_current.json (+ line) to ML1 youtube-stills and radio state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def push_json(payload: dict) -> dict:  # info: def push_json
    body = json.dumps(payload, indent=2, sort_keys=True) + "\n"  # info: set body
    line = (payload.get("line") or "") + "\n"  # info: set line
    ok_json = _ssh_write(REMOTE_JSON, body)  # info: set ok_json
    ok_home = _ssh_write(REMOTE_HOME, body)  # info: set ok_home
    ok_line = _ssh_write(REMOTE_LINE, line)  # info: set ok_line
    return {"json": ok_json, "home": ok_home, "line": ok_line}  # info: return


# ====================================================
# SECTION: function push_thumb
# What it does: Re-render YouTube thumb with fresh BLE gauges and scp to ML1 (energy mode).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def push_thumb() -> dict:  # info: def push_thumb
    if not PUSH_THUMB:  # info: if not PUSH_THUMB
        return {"skipped": True}  # info: return skipped
    if not LIVE_PICTURE.is_file():  # info: if not LIVE_PICTURE . is_file ( ) :
        return {"ok": False, "detail": "live_picture missing"}  # info: return miss
    try:  # info: try
        ran = subprocess.run(  # info: set ran
            [sys.executable, str(LIVE_PICTURE), "energy"],  # info: energy-only still
            capture_output=True,  # info: capture
            text=True,  # info: text
            timeout=120,  # info: timeout
            cwd=str(LIVE_PICTURE.parent),  # info: cwd
        )  # info: )
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except
        return {"ok": False, "detail": str(exc)}  # info: return fail
    out = (ran.stdout or "").strip().splitlines()  # info: set out
    last = out[-1] if out else ""  # info: set last
    return {"ok": ran.returncode == 0, "rc": ran.returncode, "detail": last[:300]}  # info: return


# ====================================================
# SECTION: function main
# What it does: Build the snapshot, SSH it to ML1, optionally refresh the thumb.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    payload = build()  # info: set payload
    files = push_json(payload)  # info: set files
    thumb = push_thumb()  # info: set thumb
    ok = bool(files.get("json"))  # info: youtube-stills JSON is the required landing
    print(  # info: call print
        json.dumps(  # info: json . dumps
            {  # info: {
                "ok": ok,  # info: "ok" : ok ,
                "hst": payload.get("hst"),  # info: "hst" : payload . get ( "hst" ) ,
                "line": payload.get("line"),  # info: "line" : payload . get ( "line" ) ,
                "files": files,  # info: "files" : files ,
                "thumb": thumb,  # info: "thumb" : thumb ,
                "river_src": (payload.get("packs") or {}).get("river2pro", {}).get("source"),  # info: river
                "delta_src": (payload.get("packs") or {}).get("delta2", {}).get("source"),  # info: delta
            },  # info: } ,
            sort_keys=True,  # info: sort_keys
        ),  # info: )
        flush=True,  # info: flush
    )  # info: )
    return 0 if ok else 1  # info: return 0 if ok else 1


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
