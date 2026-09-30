# ==============================================================================
# FILE: Energy/River-Car/scripts/disk_session.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""External-disk session for River 2 Pro car 12V. Never toggles AC. Dry-run default."""  # info: """External-disk session for River 2 Pro car 12V. Never toggles AC. Dry-run default."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import subprocess  # info: import subprocess
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

from river_car_dc import set_car, status as car_status  # info: from river_car_dc import set_car , status as car_status

BLOCKCHAIN_HINTS = ("litecoin", "bitcoin", "blocks", "chainstate")  # info: set BLOCKCHAIN_HINTS


# ====================================================
# SECTION: function _lsblk
# What it does:  lsblk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _lsblk() -> list[dict[str, str]]:  # info: def _lsblk
    try:  # info: try :
        raw = subprocess.check_output(  # info: set raw
            ["lsblk", "-J", "-o", "NAME,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINT,TRAN"],  # info: [ "lsblk" , "-J" , "-o" , "NAME,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINT,TRAN"
            text=True,  # info: set text
            timeout=5,  # info: set timeout
        )  # info: )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):  # info: except ( OSError , subprocess . CalledProcessError ,
        return []  # info: return [ ]
    try:  # info: try :
        data = json.loads(raw)  # info: set data
    except json.JSONDecodeError:  # info: except json . JSONDecodeError :
        return []  # info: return [ ]
    rows: list[dict[str, str]] = []  # info: set rows

    def walk(node: dict[str, Any]) -> None:  # info: def walk
        if not isinstance(node, dict):  # info: if not isinstance ( node , dict )
            return  # info: return
        ntype = str(node.get("type") or "")  # info: set ntype
        name = str(node.get("name") or "")  # info: set name
        if ntype in {"disk", "part"} and not name.startswith("nvme") and not name.startswith("loop"):  # info: if ntype in { "disk" , "part" }
            rows.append(  # info: rows . append (
                {  # info: {
                    "name": name,  # info: "name" : name ,
                    "type": ntype,  # info: "type" : ntype ,
                    "size": str(node.get("size") or ""),  # info: "size" : str ( node . get (
                    "fstype": str(node.get("fstype") or ""),  # info: "fstype" : str ( node . get (
                    "label": str(node.get("label") or ""),  # info: "label" : str ( node . get (
                    "mount": str(node.get("mountpoint") or ""),  # info: "mount" : str ( node . get (
                    "tran": str(node.get("tran") or ""),  # info: "tran" : str ( node . get (
                }  # info: }
            )  # info: )
        for child in node.get("children") or []:  # info: for child in node . get ( "children"
            if isinstance(child, dict):  # info: if isinstance ( child , dict ) :
                walk(child)  # info: call walk

    for dev in data.get("blockdevices") or []:  # info: for dev in data . get ( "blockdevices"
        if isinstance(dev, dict):  # info: if isinstance ( dev , dict ) :
            walk(dev)  # info: call walk
    return rows  # info: return rows


# ====================================================
# SECTION: function mounts_look_like_chain
# What it does: mounts look like chain.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mounts_look_like_chain() -> list[str]:  # info: def mounts_look_like_chain
    hits: list[str] = []  # info: set hits
    for row in _lsblk():  # info: for row in _lsblk ( ) :
        mount = row.get("mount") or ""  # info: set mount
        label = (row.get("label") or "").lower()  # info: set label
        if not mount:  # info: if not mount :
            continue  # info: continue
        blob = f"{mount} {label}".lower()  # info: set blob
        if any(hint in blob for hint in BLOCKCHAIN_HINTS):  # info: if any ( hint in blob for hint
            hits.append(mount)  # info: hits . append ( mount )
        litecoin = Path(mount) / "Litecoin"  # info: set litecoin
        if litecoin.is_dir():  # info: if litecoin . is_dir ( ) :
            hits.append(str(litecoin))  # info: hits . append ( str ( litecoin )
    return hits  # info: return hits


# ====================================================
# SECTION: function snapshot
# What it does: snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def snapshot() -> dict[str, Any]:  # info: def snapshot
    disks = _lsblk()  # info: set disks
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "usb_or_sata_present": bool(disks),  # info: "usb_or_sata_present" : bool ( disks ) ,
        "disks": disks,  # info: "disks" : disks ,
        "chain_mounts": mounts_look_like_chain(),  # info: "chain_mounts" : mounts_look_like_chain ( ) ,
        "car": car_status(),  # info: "car" : car_status ( ) ,
        "nvme_only": not disks,  # info: "nvme_only" : not disks ,
        "note": "External disks stay off until River car DC is on and a volume mounts.",  # info: "note" : "External disks stay off until River car DC is on and a volume mounts." ,
    }  # info: }


# ====================================================
# SECTION: function prepare
# What it does: Want drives. execute=True may run the BLE on script after the execute gate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def prepare(*, execute: bool = False, wait_s: int = 20) -> dict[str, Any]:  # info: def prepare
    """Want drives. execute=True may run the BLE on script after the execute gate."""  # info: """Want drives. execute=True may run the BLE on script after the execute gate."""
    snap = snapshot()  # info: set snap
    if snap.get("chain_mounts"):  # info: if snap . get ( "chain_mounts" ) :
        snap["ready"] = True  # info: snap [ "ready" ] = True
        return snap  # info: return snap
    car = set_car(want_on=True, execute=bool(execute))  # info: set car
    snap["car_action"] = car  # info: snap [ "car_action" ] = car
    snap["ok"] = bool(car.get("ok"))  # info: snap [ "ok" ] = bool ( car
    if not execute:  # info: if not execute :
        snap["ready"] = False  # info: snap [ "ready" ] = False
        snap["blocked"] = "dry_run"  # info: snap [ "blocked" ] = "dry_run"
        return snap  # info: return snap
    if not car.get("ok") or not car.get("spawned"):  # info: if not car . get ( "ok" )
        snap["ready"] = False  # info: snap [ "ready" ] = False
        snap["blocked"] = "power_on_refused" if car.get("error") == "refused" else "power_on_failed"  # info: snap [ "blocked" ] = "power_on_refused" if car
        return snap  # info: return snap
    deadline = time.time() + max(2, int(wait_s))  # info: set deadline
    while time.time() < deadline:  # info: while time . time ( ) < deadline
        time.sleep(2)  # info: time . sleep ( 2 )
        now = snapshot()  # info: set now
        if now.get("usb_or_sata_present") or now.get("chain_mounts"):  # info: if now . get ( "usb_or_sata_present" ) or
            now["ready"] = bool(now.get("chain_mounts"))  # info: now [ "ready" ] = bool ( now
            now["car_action"] = car  # info: now [ "car_action" ] = car
            now["ok"] = True  # info: now [ "ok" ] = True
            return now  # info: return now
    snap = snapshot()  # info: set snap
    snap["ready"] = bool(snap.get("chain_mounts"))  # info: snap [ "ready" ] = bool ( snap
    snap["car_action"] = car  # info: snap [ "car_action" ] = car
    snap["ok"] = bool(snap["ready"])  # info: snap [ "ok" ] = bool ( snap
    snap["blocked"] = "no_disk_after_wait"  # info: snap [ "blocked" ] = "no_disk_after_wait"
    return snap  # info: return snap


# ====================================================
# SECTION: function release
# What it does: Turn car DC off. An explicit execute still has to pass RR_RIVER_CAR_EXECUTE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def release(*, execute: bool = False, force: bool = False) -> dict[str, Any]:  # info: def release
    """Turn car DC off. An explicit execute still has to pass RR_RIVER_CAR_EXECUTE."""  # info: """Turn car DC off. An explicit execute still has to pass RR_RIVER_CAR_EXECUTE."""
    use_force = True if force or execute else False  # info: set use_force
    return set_car(want_on=False, execute=bool(execute), force=use_force)  # info: return set_car ( want_on = False , execute
