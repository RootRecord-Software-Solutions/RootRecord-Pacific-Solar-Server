# ==============================================================================
# FILE: Apps/Control-Panel/Lib/rr_netstat.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""rr_netstat.py — READ-ONLY network usage for Root Monitor's Network page (added 2026-09-29).

- /proc/net/dev byte/packet counters -> per-interface rx/tx rates (delta between two refreshes) + totals since boot.
- sysfs operstate / speed / MAC-free. Costs a single small file read per refresh; nothing polled when the page is hidden.
- Starlink status comes from ../Starlink/starlink_status.py (separate venv process, started only while the page is
  visible, killed on leave).
"""
from __future__ import annotations  # info: from __future__ import annotations

import time  # info: import time
from pathlib import Path  # info: from pathlib import Path

STARLINK_DIR = Path(__file__).resolve().parent.parent / "Starlink"  # info: set STARLINK_DIR
STARLINK_PY = STARLINK_DIR / ".venv/bin/python"  # info: set STARLINK_PY
STARLINK_SCRIPT = STARLINK_DIR / "starlink_status.py"  # info: set STARLINK_SCRIPT
STARLINK_TARGET = ("192.168.100.1", 9200)  # info: set STARLINK_TARGET


# ====================================================
# SECTION: function read_dev
# What it does: read dev.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_dev() -> dict:  # info: def read_dev
    res = {}  # info: set res
    try:  # info: try :
        for ln in Path("/proc/net/dev").read_text().splitlines()[2:]:  # info: for ln in Path ( "/proc/net/dev" ) .
            name, data = ln.split(":", 1)  # info: name , data = ln . split (
            f = data.split()  # info: set f
            res[name.strip()] = {"rx": int(f[0]), "rx_pk": int(f[1]), "rx_err": int(f[2]), "rx_drop": int(f[3]),  # info: res [ name . strip ( ) ]
                                 "tx": int(f[8]), "tx_pk": int(f[9]), "tx_err": int(f[10]), "tx_drop": int(f[11])}  # info: "tx" : int ( f [ 8 ]
    except (OSError, ValueError, IndexError):  # info: except ( OSError , ValueError , IndexError )
        pass  # info: pass
    return res  # info: return res


# ====================================================
# SECTION: function iface_info
# What it does: iface info.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def iface_info(name: str) -> dict:  # info: def iface_info
    base = Path("/sys/class/net") / name  # info: set base
    def rd(f):  # info: def rd
        try:  # info: try :
            return (base / f).read_text().strip()  # info: return ( base / f ) . read_text
        except OSError:  # info: except OSError :
            return ""  # info: return ""
    kind = "wifi" if (base / "wireless").exists() else ("loopback" if name == "lo" else  # info: set kind
            ("virtual" if not (base / "device").exists() else "ethernet"))  # info: call (
    sp = rd("speed")  # info: set sp
    return {"state": rd("operstate") or "?", "kind": kind, "speed": f"{sp} Mb/s" if sp and sp.lstrip("-").isdigit() and int(sp) > 0 else ""}  # info: return { "state" : rd ( "operstate" )


# ====================================================
# SECTION: class Rates
# What it does: Rates.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Rates:  # info: class Rates
    def __init__(self):  # info: def __init__
        self.prev = None  # info: self . prev = None

    def sample(self) -> list[dict]:  # info: def sample
        now = time.monotonic()  # info: set now
        cur = read_dev()  # info: set cur
        out = []  # info: set out
        for n, c in sorted(cur.items()):  # info: for n , c in sorted ( cur
            r = {"name": n, **c, **iface_info(n), "rx_rate": None, "tx_rate": None}  # info: set r
            if self.prev and n in self.prev[1]:  # info: if self . prev and n in self
                dt = max(0.001, now - self.prev[0])  # info: set dt
                p = self.prev[1][n]  # info: set p
                r["rx_rate"] = max(0, c["rx"] - p["rx"]) / dt  # info: r [ "rx_rate" ] = max ( 0
                r["tx_rate"] = max(0, c["tx"] - p["tx"]) / dt  # info: r [ "tx_rate" ] = max ( 0
            out.append(r)  # info: out . append ( r )
        self.prev = (now, cur)  # info: self . prev = ( now , cur
        return out  # info: return out


# ====================================================
# SECTION: function human_bytes
# What it does: human bytes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def human_bytes(n) -> str:  # info: def human_bytes
    if n is None:  # info: if n is None :
        return "—"  # info: return "—"
    n = float(n)  # info: set n
    for u in ("B", "KB", "MB", "GB", "TB"):  # info: for u in ( "B" , "KB" ,
        if n < 1024 or u == "TB":  # info: if n < 1024 or u == "TB"
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"  # info: return f" { n : .0f }
        n /= 1024  # info: n /= 1024


# ====================================================
# SECTION: function human_rate
# What it does: human rate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def human_rate(bps) -> str:  # info: def human_rate
    if bps is None:  # info: if bps is None :
        return "—"  # info: return "—"
    bits = bps * 8  # info: set bits
    for u in ("b/s", "kb/s", "Mb/s", "Gb/s"):  # info: for u in ( "b/s" , "kb/s" ,
        if bits < 1000 or u == "Gb/s":  # info: if bits < 1000 or u == "Gb/s"
            return f"{bits:.0f} {u}" if u == "b/s" else f"{bits:.1f} {u}"  # info: return f" { bits : .0f }
        bits /= 1000  # info: bits /= 1000


# ====================================================
# SECTION: function starlink_available
# What it does: starlink available.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def starlink_available() -> bool:  # info: def starlink_available
    return STARLINK_PY.exists() and STARLINK_SCRIPT.exists()  # info: return STARLINK_PY . exists ( ) and STARLINK_SCRIPT
