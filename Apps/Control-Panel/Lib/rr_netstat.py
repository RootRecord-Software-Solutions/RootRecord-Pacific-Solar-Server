"""rr_netstat.py — READ-ONLY network usage for Root Monitor's Network page (added 2026-09-29).

- /proc/net/dev byte/packet counters -> per-interface rx/tx rates (delta between two refreshes) + totals since boot.
- sysfs operstate / speed / MAC-free. Costs a single small file read per refresh; nothing polled when the page is hidden.
- Starlink status comes from ../Starlink/starlink_status.py (separate venv process, started only while the page is
  visible, killed on leave).
"""
from __future__ import annotations

import time
from pathlib import Path

STARLINK_DIR = Path(__file__).resolve().parent.parent / "Starlink"
STARLINK_PY = STARLINK_DIR / ".venv/bin/python"
STARLINK_SCRIPT = STARLINK_DIR / "starlink_status.py"
STARLINK_TARGET = ("192.168.100.1", 9200)


def read_dev() -> dict:
    res = {}
    try:
        for ln in Path("/proc/net/dev").read_text().splitlines()[2:]:
            name, data = ln.split(":", 1)
            f = data.split()
            res[name.strip()] = {"rx": int(f[0]), "rx_pk": int(f[1]), "rx_err": int(f[2]), "rx_drop": int(f[3]),
                                 "tx": int(f[8]), "tx_pk": int(f[9]), "tx_err": int(f[10]), "tx_drop": int(f[11])}
    except (OSError, ValueError, IndexError):
        pass
    return res


def iface_info(name: str) -> dict:
    base = Path("/sys/class/net") / name
    def rd(f):
        try:
            return (base / f).read_text().strip()
        except OSError:
            return ""
    kind = "wifi" if (base / "wireless").exists() else ("loopback" if name == "lo" else
            ("virtual" if not (base / "device").exists() else "ethernet"))
    sp = rd("speed")
    return {"state": rd("operstate") or "?", "kind": kind, "speed": f"{sp} Mb/s" if sp and sp.lstrip("-").isdigit() and int(sp) > 0 else ""}


class Rates:
    def __init__(self):
        self.prev = None

    def sample(self) -> list[dict]:
        now = time.monotonic()
        cur = read_dev()
        out = []
        for n, c in sorted(cur.items()):
            r = {"name": n, **c, **iface_info(n), "rx_rate": None, "tx_rate": None}
            if self.prev and n in self.prev[1]:
                dt = max(0.001, now - self.prev[0])
                p = self.prev[1][n]
                r["rx_rate"] = max(0, c["rx"] - p["rx"]) / dt
                r["tx_rate"] = max(0, c["tx"] - p["tx"]) / dt
            out.append(r)
        self.prev = (now, cur)
        return out


def human_bytes(n) -> str:
    if n is None:
        return "—"
    n = float(n)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or u == "TB":
            return f"{n:.0f} {u}" if u == "B" else f"{n:.1f} {u}"
        n /= 1024


def human_rate(bps) -> str:
    if bps is None:
        return "—"
    bits = bps * 8
    for u in ("b/s", "kb/s", "Mb/s", "Gb/s"):
        if bits < 1000 or u == "Gb/s":
            return f"{bits:.0f} {u}" if u == "b/s" else f"{bits:.1f} {u}"
        bits /= 1000


def starlink_available() -> bool:
    return STARLINK_PY.exists() and STARLINK_SCRIPT.exists()
