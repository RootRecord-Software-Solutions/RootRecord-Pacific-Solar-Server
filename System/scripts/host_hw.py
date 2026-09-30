#!/usr/bin/env python3
"""Host hardware facts: CPU temperature, physical drives, AMD GPU busy %, XDNA NPU busy % (G3 port of the Linux parts of
G1 host-metrics/scripts/host_metrics.py, 2026-09-29).

  python3 host_hw.py        print JSON {temp_c, temp_source, drives, drives_spoken, gpu_name, gpu_pct, npu_present, npu_pct}

Ported unchanged (Linux paths): host_temp_c (psutil sensors, preferred k10temp / coretemp / acpitz), _disk_parent,
_drive_label, host_disks (one row per physical drive, skips snap / loop / tmpfs / < 2 GB), host_drives_spoken,
_drm_cards, _linux_gpu_name (lspci on the amdgpu slot), _linux_gpu_pct (gpu_busy_percent), _linux_npu_present,
_linux_npu_fdinfo_busy, _linux_npu_pct (amdxdna DRM fdinfo engine-busy delta). Dropped: the Windows PDH / winreg
branches. Needs psutil (present in system python3). Read-only; on demand; writes nothing. Complements
System/scripts/plumbing/npu-status.sh and Media/Voice/scripts/system_perf.py (CPU / RAM / battery / disk / uptime).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import psutil

_LINUX_ACCEL = Path("/dev/accel/accel0")
_LINUX_AMDXDNA = Path("/sys/bus/pci/drivers/amdxdna")
_LINUX_DRM = Path("/sys/class/drm")
_LINUX_PROC = Path("/proc")
_FDINFO_DRIVER = re.compile(r"^drm-driver:\s+(\S+)", re.M)
_FDINFO_CLIENT = re.compile(r"^drm-client-id:\s+(\S+)", re.M)
_FDINFO_ENGINE = re.compile(r"^drm-engine-(\S+):\s+(\d+)", re.M)


def host_temp_c() -> tuple[float | None, str | None]:
    """Best-effort thermal zone / CPU temp. Returns (celsius, source)."""
    try:
        temps = getattr(psutil, "sensors_temperatures", lambda: None)() or {}
    except Exception:
        temps = {}
    prefer = ("coretemp", "k10temp", "zenpower", "cpu_thermal", "acpitz", "dell_smm")
    for name in prefer:
        entries = temps.get(name) or []
        for e in entries:
            cur = getattr(e, "current", None)
            if cur is None:
                continue
            try:
                val = float(cur)
            except (TypeError, ValueError):
                continue
            if -20 <= val <= 110:
                return round(val, 1), name
        if entries:
            try:
                val = float(entries[0].current)
                if -20 <= val <= 110:
                    return round(val, 1), name
            except (TypeError, ValueError, IndexError):
                pass
    for name, entries in temps.items():
        for e in entries:
            try:
                val = float(e.current)
            except (TypeError, ValueError, AttributeError):
                continue
            if -20 <= val <= 110:
                return round(val, 1), str(name)
    return None, None


def _disk_parent(device: str) -> str:
    name = Path(device or "").name
    if not name:
        return device or "disk"
    if name.startswith("nvme") and "p" in name:
        return name.rsplit("p", 1)[0]
    return re.sub(r"\d+$", "", name) or name


def _drive_label(mount: str) -> str:
    if mount in {"/", "C:\\", "C:"}:
        return "system drive"
    tail = mount.rstrip("/").split("/")[-1] or mount
    return f"{tail} drive"


def host_disks() -> list[dict[str, Any]]:
    """One row per physical drive. Skip snap/loop/tmp mounts."""
    skip_fs = {"squashfs", "overlay", "tmpfs", "devtmpfs", "cgroup", "cgroup2", "fuse.portal"}
    skip_mp = ("/snap", "/run", "/sys", "/proc", "/dev", "/boot")
    by_disk: dict[str, dict[str, Any]] = {}
    for part in psutil.disk_partitions(all=False):
        fstype = (part.fstype or "").lower()
        mp = part.mountpoint or ""
        dev = (part.device or "").lower()
        if fstype in skip_fs:
            continue
        if "loop" in dev or "snap" in mp.lower():
            continue
        if any(mp == p or mp.startswith(p + "/") for p in skip_mp):
            continue
        try:
            usage = psutil.disk_usage(mp)
        except OSError:
            continue
        if usage.total < 2 * 1024 ** 3:
            continue
        parent = _disk_parent(part.device)
        row = {
            "disk": parent,
            "mount": mp,
            "label": _drive_label(mp),
            "pct": round(float(usage.percent), 1),
            "used_gb": round(usage.used / (1024 ** 3), 1),
            "total_gb": round(usage.total / (1024 ** 3), 1),
            "total_bytes": int(usage.total),
        }
        prev = by_disk.get(parent)
        if not prev or row["total_bytes"] >= int(prev.get("total_bytes") or 0):
            by_disk[parent] = row
    return list(by_disk.values())


def host_drives_spoken() -> str:
    rows = host_disks()
    if not rows:
        return ""
    bits = []
    for d in rows:
        bits.append(
            f"{d['label']} {d['pct']} percent used, {d['used_gb']} of {d['total_gb']} gigabytes"
        )
    return "Drives: " + ". ".join(bits) + "."


def _drm_cards() -> list[Path]:
    if not _LINUX_DRM.is_dir():
        return []
    return sorted(
        p
        for p in _LINUX_DRM.iterdir()
        if p.name.startswith("card") and p.name[4:].isdigit()
    )


def _linux_gpu_name() -> str | None:
    slot = None
    for card in _drm_cards():
        uevent = card / "device" / "uevent"
        if not uevent.is_file():
            continue
        try:
            text = uevent.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "DRIVER=amdgpu" not in text:
            continue
        for line in text.splitlines():
            if line.startswith("PCI_SLOT_NAME="):
                slot = line.split("=", 1)[1].strip()
                break
        if slot:
            break
    if slot:
        try:
            out = subprocess.run(
                ["lspci", "-s", slot],
                capture_output=True,
                text=True,
                timeout=2,
            )
        except Exception:
            out = None
        line = ((out.stdout if out else "") or "").strip()
        if line:
            return line.split(": ", 1)[-1].strip()
    return "amdgpu" if _linux_gpu_pct() is not None else None


def _linux_gpu_pct() -> float | None:
    for card in _drm_cards():
        path = card / "device" / "gpu_busy_percent"
        if not path.is_file():
            continue
        try:
            return round(min(100.0, max(0.0, float(path.read_text().strip()))), 1)
        except (OSError, ValueError):
            continue
    return None


def _linux_npu_present() -> bool:
    try:
        if _LINUX_ACCEL.exists():
            return True
    except OSError:
        pass
    try:
        if _LINUX_AMDXDNA.is_dir():
            return True
    except OSError:
        pass
    return False


def _linux_npu_fdinfo_busy(proc_root: Path | None = None) -> tuple[dict[str, int], bool]:
    """Per-client amdxdna engine busy nanoseconds from DRM fdinfo."""
    root = proc_root or _LINUX_PROC
    busy: dict[str, int] = {}
    found = False
    try:
        procs = list(root.iterdir())
    except OSError:
        return busy, False
    for proc in procs:
        if not proc.name.isdigit():
            continue
        fdinfo = proc / "fdinfo"
        try:
            files = list(fdinfo.iterdir())
        except OSError:
            continue
        for path in files:
            try:
                txt = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            drv = _FDINFO_DRIVER.search(txt)
            if not drv or drv.group(1) != "amdxdna":
                continue
            found = True
            cid = (_FDINFO_CLIENT.search(txt) or drv).group(1)
            for eng, ns in _FDINFO_ENGINE.findall(txt):
                try:
                    val = int(ns)
                except ValueError:
                    continue
                key = f"{cid}:{eng}"
                if val >= busy.get(key, 0):
                    busy[key] = val
    return busy, found


def _linux_npu_pct(*, wait_s: float = 0.15, proc_root: Path | None = None) -> float | None:
    """XDNA busy percent. Idle with no client is 0, not missing."""
    if not _linux_npu_present():
        return None
    first, found = _linux_npu_fdinfo_busy(proc_root)
    if not found:
        return 0.0
    t0 = time.monotonic_ns()
    time.sleep(max(0.05, wait_s))
    second, _found2 = _linux_npu_fdinfo_busy(proc_root)
    dt = time.monotonic_ns() - t0
    if dt <= 0:
        return 0.0
    delta = 0
    for key, later in second.items():
        earlier = first.get(key, 0)
        if later > earlier:
            delta += later - earlier
    return round(min(100.0, max(0.0, 100.0 * delta / dt)), 1)


def snapshot() -> dict[str, Any]:
    temp, src = host_temp_c()
    return {"temp_c": temp, "temp_source": src, "drives": host_disks(), "drives_spoken": host_drives_spoken(),
            "gpu_name": _linux_gpu_name(), "gpu_pct": _linux_gpu_pct(),
            "npu_present": _linux_npu_present(), "npu_pct": _linux_npu_pct()}


if __name__ == "__main__":
    print(json.dumps(snapshot(), ensure_ascii=False))
