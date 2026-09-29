#!/usr/bin/env python3
"""conky_readout.py — tiny read-only helper for Conky/rootrecord.conkyrc (added 2026-09-29).

Usage (called by conky ${execi}/${execibar}):
  conky_readout.py soc river2pro|delta2   -> number 0-100 (for execibar), 0 if unknown
  conky_readout.py soctext river2pro|delta2 -> "12.0% · 3m05s ago"
  conky_readout.py laptop                 -> number 0-100
  conky_readout.py laptoptext             -> "100% Full AC"
  conky_readout.py cpu | mem              -> number from System/last/host-last.json
  conky_readout.py npu                    -> one-line NPU / FLM / lock state
  conky_readout.py poller                 -> PASS/WARN/FAIL (proc count)
Read-only: JSON files, sysfs, /proc only. Never runs npu-status.sh (keeps the widget cheap).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Lib"))
import rr_settings  # noqa: E402
import rr_sources as src  # noqa: E402


def main() -> None:
    s = rr_settings.load()
    p = src.Paths(s["database_root"], s["pacific_root"])
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    arg = sys.argv[2] if len(sys.argv) > 2 else ""
    if what in ("soc", "soctext"):
        d = src.read_json(p.energy / f"soc/{arg}-last.json") or {}
        v = d.get("soc")
        if what == "soc":
            print(int(v) if isinstance(v, (int, float)) else 0)
        else:
            a = src.age_s(d.get("at"))
            stale = " STALE" if a is not None and a > s["stale_after_sec"] else ""
            print(f"{v:.1f}% · {src.fmt_age(a)}{stale}" if isinstance(v, (int, float)) else "n/a")
    elif what in ("laptop", "laptoptext"):
        lap = src.laptop_battery()
        if what == "laptop":
            print(int(lap[0]) if lap else 0)
        else:
            print(f"{lap[0]:.0f}% {lap[1]} {'AC' if lap[2] else 'battery'}" if lap else "n/a")
    elif what in ("cpu", "mem"):
        sy = src.system(p)
        v = sy["cpu" if what == "cpu" else "mem"]
        print(int(v) if isinstance(v, (int, float)) else 0)
    elif what == "npu":
        n = src.npu(p, flm_port=int(s.get("flm_port", 52625)))
        print(f"{'accel ok' if n['accel'] else 'no accel'} · {n['state'].split(' —')[0]} · lock {n['lock'].split(' ')[0]}")
    elif what == "poller":
        print(src.poller_quick(src.proc_argvs())[0])
    else:
        print("?")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never break the widget
        print(f"err {type(e).__name__}", file=sys.stdout)
        os._exit(0)
