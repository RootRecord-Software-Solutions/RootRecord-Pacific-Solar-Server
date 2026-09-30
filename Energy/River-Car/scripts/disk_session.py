"""External-disk session for River 2 Pro car 12V. Never toggles AC. Dry-run default."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from river_car_dc import set_car, status as car_status

BLOCKCHAIN_HINTS = ("litecoin", "bitcoin", "blocks", "chainstate")


def _lsblk() -> list[dict[str, str]]:
    try:
        raw = subprocess.check_output(
            ["lsblk", "-J", "-o", "NAME,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINT,TRAN"],
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    rows: list[dict[str, str]] = []

    def walk(node: dict[str, Any]) -> None:
        if not isinstance(node, dict):
            return
        ntype = str(node.get("type") or "")
        name = str(node.get("name") or "")
        if ntype in {"disk", "part"} and not name.startswith("nvme") and not name.startswith("loop"):
            rows.append(
                {
                    "name": name,
                    "type": ntype,
                    "size": str(node.get("size") or ""),
                    "fstype": str(node.get("fstype") or ""),
                    "label": str(node.get("label") or ""),
                    "mount": str(node.get("mountpoint") or ""),
                    "tran": str(node.get("tran") or ""),
                }
            )
        for child in node.get("children") or []:
            if isinstance(child, dict):
                walk(child)

    for dev in data.get("blockdevices") or []:
        if isinstance(dev, dict):
            walk(dev)
    return rows


def mounts_look_like_chain() -> list[str]:
    hits: list[str] = []
    for row in _lsblk():
        mount = row.get("mount") or ""
        label = (row.get("label") or "").lower()
        if not mount:
            continue
        blob = f"{mount} {label}".lower()
        if any(hint in blob for hint in BLOCKCHAIN_HINTS):
            hits.append(mount)
        litecoin = Path(mount) / "Litecoin"
        if litecoin.is_dir():
            hits.append(str(litecoin))
    return hits


def snapshot() -> dict[str, Any]:
    disks = _lsblk()
    return {
        "ok": True,
        "usb_or_sata_present": bool(disks),
        "disks": disks,
        "chain_mounts": mounts_look_like_chain(),
        "car": car_status(),
        "nvme_only": not disks,
        "note": "External disks stay off until River car DC is on and a volume mounts.",
    }


def prepare(*, execute: bool = False, wait_s: int = 20) -> dict[str, Any]:
    """Want drives. execute=True may run the BLE on script after the execute gate."""
    snap = snapshot()
    if snap.get("chain_mounts"):
        snap["ready"] = True
        return snap
    car = set_car(want_on=True, execute=bool(execute))
    snap["car_action"] = car
    snap["ok"] = bool(car.get("ok"))
    if not execute:
        snap["ready"] = False
        snap["blocked"] = "dry_run"
        return snap
    if not car.get("ok") or not car.get("spawned"):
        snap["ready"] = False
        snap["blocked"] = "power_on_refused" if car.get("error") == "refused" else "power_on_failed"
        return snap
    deadline = time.time() + max(2, int(wait_s))
    while time.time() < deadline:
        time.sleep(2)
        now = snapshot()
        if now.get("usb_or_sata_present") or now.get("chain_mounts"):
            now["ready"] = bool(now.get("chain_mounts"))
            now["car_action"] = car
            now["ok"] = True
            return now
    snap = snapshot()
    snap["ready"] = bool(snap.get("chain_mounts"))
    snap["car_action"] = car
    snap["ok"] = bool(snap["ready"])
    snap["blocked"] = "no_disk_after_wait"
    return snap


def release(*, execute: bool = False, force: bool = False) -> dict[str, Any]:
    """Turn car DC off. An explicit execute still has to pass RR_RIVER_CAR_EXECUTE."""
    use_force = True if force or execute else False
    return set_car(want_on=False, execute=bool(execute), force=use_force)
