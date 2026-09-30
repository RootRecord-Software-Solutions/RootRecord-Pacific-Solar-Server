# ==============================================================================
# FILE: System/scripts/host_hw.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

import psutil  # info: import psutil

_LINUX_ACCEL = Path("/dev/accel/accel0")  # info: set _LINUX_ACCEL
_LINUX_AMDXDNA = Path("/sys/bus/pci/drivers/amdxdna")  # info: set _LINUX_AMDXDNA
_LINUX_DRM = Path("/sys/class/drm")  # info: set _LINUX_DRM
_LINUX_PROC = Path("/proc")  # info: set _LINUX_PROC
_FDINFO_DRIVER = re.compile(r"^drm-driver:\s+(\S+)", re.M)  # info: set _FDINFO_DRIVER
_FDINFO_CLIENT = re.compile(r"^drm-client-id:\s+(\S+)", re.M)  # info: set _FDINFO_CLIENT
_FDINFO_ENGINE = re.compile(r"^drm-engine-(\S+):\s+(\d+)", re.M)  # info: set _FDINFO_ENGINE


# ====================================================
# SECTION: function host_temp_c
# What it does: Best-effort thermal zone / CPU temp. Returns (celsius, source).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_temp_c() -> tuple[float | None, str | None]:  # info: def host_temp_c
    """Best-effort thermal zone / CPU temp. Returns (celsius, source)."""  # info: """Best-effort thermal zone / CPU temp. Returns (celsius, source)."""
    try:  # info: try :
        temps = getattr(psutil, "sensors_temperatures", lambda: None)() or {}  # info: set temps
    except Exception:  # info: except Exception :
        temps = {}  # info: set temps
    prefer = ("coretemp", "k10temp", "zenpower", "cpu_thermal", "acpitz", "dell_smm")  # info: set prefer
    for name in prefer:  # info: for name in prefer :
        entries = temps.get(name) or []  # info: set entries
        for e in entries:  # info: for e in entries :
            cur = getattr(e, "current", None)  # info: set cur
            if cur is None:  # info: if cur is None :
                continue  # info: continue
            try:  # info: try :
                val = float(cur)  # info: set val
            except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
                continue  # info: continue
            if -20 <= val <= 110:  # info: if - 20 <= val <= 110 :
                return round(val, 1), name  # info: return round ( val , 1 ) ,
        if entries:  # info: if entries :
            try:  # info: try :
                val = float(entries[0].current)  # info: set val
                if -20 <= val <= 110:  # info: if - 20 <= val <= 110 :
                    return round(val, 1), name  # info: return round ( val , 1 ) ,
            except (TypeError, ValueError, IndexError):  # info: except ( TypeError , ValueError , IndexError )
                pass  # info: pass
    for name, entries in temps.items():  # info: for name , entries in temps . items
        for e in entries:  # info: for e in entries :
            try:  # info: try :
                val = float(e.current)  # info: set val
            except (TypeError, ValueError, AttributeError):  # info: except ( TypeError , ValueError , AttributeError )
                continue  # info: continue
            if -20 <= val <= 110:  # info: if - 20 <= val <= 110 :
                return round(val, 1), str(name)  # info: return round ( val , 1 ) ,
    return None, None  # info: return None , None


# ====================================================
# SECTION: function _disk_parent
# What it does:  disk parent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _disk_parent(device: str) -> str:  # info: def _disk_parent
    name = Path(device or "").name  # info: set name
    if not name:  # info: if not name :
        return device or "disk"  # info: return device or "disk"
    if name.startswith("nvme") and "p" in name:  # info: if name . startswith ( "nvme" ) and
        return name.rsplit("p", 1)[0]  # info: return name . rsplit ( "p" , 1
    return re.sub(r"\d+$", "", name) or name  # info: return re . sub ( r"\d+$" , ""


# ====================================================
# SECTION: function _drive_label
# What it does:  drive label.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _drive_label(mount: str) -> str:  # info: def _drive_label
    if mount in {"/", "C:\\", "C:"}:  # info: if mount in { "/" , "C:\\" ,
        return "system drive"  # info: return "system drive"
    tail = mount.rstrip("/").split("/")[-1] or mount  # info: set tail
    return f"{tail} drive"  # info: return f" { tail } drive "


# ====================================================
# SECTION: function host_disks
# What it does: One row per physical drive. Skip snap/loop/tmp mounts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_disks() -> list[dict[str, Any]]:  # info: def host_disks
    """One row per physical drive. Skip snap/loop/tmp mounts."""  # info: """One row per physical drive. Skip snap/loop/tmp mounts."""
    skip_fs = {"squashfs", "overlay", "tmpfs", "devtmpfs", "cgroup", "cgroup2", "fuse.portal"}  # info: set skip_fs
    skip_mp = ("/snap", "/run", "/sys", "/proc", "/dev", "/boot")  # info: set skip_mp
    by_disk: dict[str, dict[str, Any]] = {}  # info: set by_disk
    for part in psutil.disk_partitions(all=False):  # info: for part in psutil . disk_partitions ( all
        fstype = (part.fstype or "").lower()  # info: set fstype
        mp = part.mountpoint or ""  # info: set mp
        dev = (part.device or "").lower()  # info: set dev
        if fstype in skip_fs:  # info: if fstype in skip_fs :
            continue  # info: continue
        if "loop" in dev or "snap" in mp.lower():  # info: if "loop" in dev or "snap" in mp
            continue  # info: continue
        if any(mp == p or mp.startswith(p + "/") for p in skip_mp):  # info: if any ( mp == p or mp
            continue  # info: continue
        try:  # info: try :
            usage = psutil.disk_usage(mp)  # info: set usage
        except OSError:  # info: except OSError :
            continue  # info: continue
        if usage.total < 2 * 1024 ** 3:  # info: if usage . total < 2 * 1024
            continue  # info: continue
        parent = _disk_parent(part.device)  # info: set parent
        row = {  # info: set row
            "disk": parent,  # info: "disk" : parent ,
            "mount": mp,  # info: "mount" : mp ,
            "label": _drive_label(mp),  # info: "label" : _drive_label ( mp ) ,
            "pct": round(float(usage.percent), 1),  # info: "pct" : round ( float ( usage .
            "used_gb": round(usage.used / (1024 ** 3), 1),  # info: "used_gb" : round ( usage . used /
            "total_gb": round(usage.total / (1024 ** 3), 1),  # info: "total_gb" : round ( usage . total /
            "total_bytes": int(usage.total),  # info: "total_bytes" : int ( usage . total )
        }  # info: }
        prev = by_disk.get(parent)  # info: set prev
        if not prev or row["total_bytes"] >= int(prev.get("total_bytes") or 0):  # info: if not prev or row [ "total_bytes" ]
            by_disk[parent] = row  # info: by_disk [ parent ] = row
    return list(by_disk.values())  # info: return list ( by_disk . values ( )


# ====================================================
# SECTION: function host_drives_spoken
# What it does: host drives spoken.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_drives_spoken() -> str:  # info: def host_drives_spoken
    rows = host_disks()  # info: set rows
    if not rows:  # info: if not rows :
        return ""  # info: return ""
    bits = []  # info: set bits
    for d in rows:  # info: for d in rows :
        bits.append(  # info: bits . append (
            f"{d['label']} {d['pct']} percent used, {d['used_gb']} of {d['total_gb']} gigabytes"  # info: f" { d [ 'label' ] }
        )  # info: )
    return "Drives: " + ". ".join(bits) + "."  # info: return "Drives: " + ". " . join ( bits


# ====================================================
# SECTION: function _drm_cards
# What it does:  drm cards.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _drm_cards() -> list[Path]:  # info: def _drm_cards
    if not _LINUX_DRM.is_dir():  # info: if not _LINUX_DRM . is_dir ( ) :
        return []  # info: return [ ]
    return sorted(  # info: return sorted (
        p  # info: p
        for p in _LINUX_DRM.iterdir()  # info: for p in _LINUX_DRM . iterdir ( )
        if p.name.startswith("card") and p.name[4:].isdigit()  # info: if p . name . startswith ( "card"
    )  # info: )


# ====================================================
# SECTION: function _linux_gpu_name
# What it does:  linux gpu name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _linux_gpu_name() -> str | None:  # info: def _linux_gpu_name
    slot = None  # info: set slot
    for card in _drm_cards():  # info: for card in _drm_cards ( ) :
        uevent = card / "device" / "uevent"  # info: set uevent
        if not uevent.is_file():  # info: if not uevent . is_file ( ) :
            continue  # info: continue
        try:  # info: try :
            text = uevent.read_text(encoding="utf-8", errors="replace")  # info: set text
        except OSError:  # info: except OSError :
            continue  # info: continue
        if "DRIVER=amdgpu" not in text:  # info: if "DRIVER=amdgpu" not in text :
            continue  # info: continue
        for line in text.splitlines():  # info: for line in text . splitlines ( )
            if line.startswith("PCI_SLOT_NAME="):  # info: if line . startswith ( "PCI_SLOT_NAME=" ) :
                slot = line.split("=", 1)[1].strip()  # info: set slot
                break  # info: break
        if slot:  # info: if slot :
            break  # info: break
    if slot:  # info: if slot :
        try:  # info: try :
            out = subprocess.run(  # info: set out
                ["lspci", "-s", slot],  # info: [ "lspci" , "-s" , slot ] ,
                capture_output=True,  # info: set capture_output
                text=True,  # info: set text
                timeout=2,  # info: set timeout
            )  # info: )
        except Exception:  # info: except Exception :
            out = None  # info: set out
        line = ((out.stdout if out else "") or "").strip()  # info: set line
        if line:  # info: if line :
            return line.split(": ", 1)[-1].strip()  # info: return line . split ( ": " , 1
    return "amdgpu" if _linux_gpu_pct() is not None else None  # info: return "amdgpu" if _linux_gpu_pct ( ) is not


# ====================================================
# SECTION: function _linux_gpu_pct
# What it does:  linux gpu pct.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _linux_gpu_pct() -> float | None:  # info: def _linux_gpu_pct
    for card in _drm_cards():  # info: for card in _drm_cards ( ) :
        path = card / "device" / "gpu_busy_percent"  # info: set path
        if not path.is_file():  # info: if not path . is_file ( ) :
            continue  # info: continue
        try:  # info: try :
            return round(min(100.0, max(0.0, float(path.read_text().strip()))), 1)  # info: return round ( min ( 100.0 , max
        except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
            continue  # info: continue
    return None  # info: return None


# ====================================================
# SECTION: function _linux_npu_present
# What it does:  linux npu present.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _linux_npu_present() -> bool:  # info: def _linux_npu_present
    try:  # info: try :
        if _LINUX_ACCEL.exists():  # info: if _LINUX_ACCEL . exists ( ) :
            return True  # info: return True
    except OSError:  # info: except OSError :
        pass  # info: pass
    try:  # info: try :
        if _LINUX_AMDXDNA.is_dir():  # info: if _LINUX_AMDXDNA . is_dir ( ) :
            return True  # info: return True
    except OSError:  # info: except OSError :
        pass  # info: pass
    return False  # info: return False


# ====================================================
# SECTION: function _linux_npu_fdinfo_busy
# What it does: Per-client amdxdna engine busy nanoseconds from DRM fdinfo.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _linux_npu_fdinfo_busy(proc_root: Path | None = None) -> tuple[dict[str, int], bool]:  # info: def _linux_npu_fdinfo_busy
    """Per-client amdxdna engine busy nanoseconds from DRM fdinfo."""  # info: """Per-client amdxdna engine busy nanoseconds from DRM fdinfo."""
    root = proc_root or _LINUX_PROC  # info: set root
    busy: dict[str, int] = {}  # info: set busy
    found = False  # info: set found
    try:  # info: try :
        procs = list(root.iterdir())  # info: set procs
    except OSError:  # info: except OSError :
        return busy, False  # info: return busy , False
    for proc in procs:  # info: for proc in procs :
        if not proc.name.isdigit():  # info: if not proc . name . isdigit (
            continue  # info: continue
        fdinfo = proc / "fdinfo"  # info: set fdinfo
        try:  # info: try :
            files = list(fdinfo.iterdir())  # info: set files
        except OSError:  # info: except OSError :
            continue  # info: continue
        for path in files:  # info: for path in files :
            try:  # info: try :
                txt = path.read_text(encoding="utf-8", errors="replace")  # info: set txt
            except OSError:  # info: except OSError :
                continue  # info: continue
            drv = _FDINFO_DRIVER.search(txt)  # info: set drv
            if not drv or drv.group(1) != "amdxdna":  # info: if not drv or drv . group (
                continue  # info: continue
            found = True  # info: set found
            cid = (_FDINFO_CLIENT.search(txt) or drv).group(1)  # info: set cid
            for eng, ns in _FDINFO_ENGINE.findall(txt):  # info: for eng , ns in _FDINFO_ENGINE . findall
                try:  # info: try :
                    val = int(ns)  # info: set val
                except ValueError:  # info: except ValueError :
                    continue  # info: continue
                key = f"{cid}:{eng}"  # info: set key
                if val >= busy.get(key, 0):  # info: if val >= busy . get ( key
                    busy[key] = val  # info: busy [ key ] = val
    return busy, found  # info: return busy , found


# ====================================================
# SECTION: function _linux_npu_pct
# What it does: XDNA busy percent. Idle with no client is 0, not missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _linux_npu_pct(*, wait_s: float = 0.15, proc_root: Path | None = None) -> float | None:  # info: def _linux_npu_pct
    """XDNA busy percent. Idle with no client is 0, not missing."""  # info: """XDNA busy percent. Idle with no client is 0, not missing."""
    if not _linux_npu_present():  # info: if not _linux_npu_present ( ) :
        return None  # info: return None
    first, found = _linux_npu_fdinfo_busy(proc_root)  # info: first , found = _linux_npu_fdinfo_busy ( proc_root )
    if not found:  # info: if not found :
        return 0.0  # info: return 0.0
    t0 = time.monotonic_ns()  # info: set t0
    time.sleep(max(0.05, wait_s))  # info: time . sleep ( max ( 0.05 ,
    second, _found2 = _linux_npu_fdinfo_busy(proc_root)  # info: second , _found2 = _linux_npu_fdinfo_busy ( proc_root )
    dt = time.monotonic_ns() - t0  # info: set dt
    if dt <= 0:  # info: if dt <= 0 :
        return 0.0  # info: return 0.0
    delta = 0  # info: set delta
    for key, later in second.items():  # info: for key , later in second . items
        earlier = first.get(key, 0)  # info: set earlier
        if later > earlier:  # info: if later > earlier :
            delta += later - earlier  # info: set delta
    return round(min(100.0, max(0.0, 100.0 * delta / dt)), 1)  # info: return round ( min ( 100.0 , max


# ====================================================
# SECTION: function snapshot
# What it does: snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def snapshot() -> dict[str, Any]:  # info: def snapshot
    temp, src = host_temp_c()  # info: temp , src = host_temp_c ( )
    return {"temp_c": temp, "temp_source": src, "drives": host_disks(), "drives_spoken": host_drives_spoken(),  # info: return { "temp_c" : temp , "temp_source" :
            "gpu_name": _linux_gpu_name(), "gpu_pct": _linux_gpu_pct(),  # info: "gpu_name" : _linux_gpu_name ( ) , "gpu_pct" :
            "npu_present": _linux_npu_present(), "npu_pct": _linux_npu_pct()}  # info: "npu_present" : _linux_npu_present ( ) , "npu_pct" :


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    print(json.dumps(snapshot(), ensure_ascii=False))  # info: call print
