# ==============================================================================
# FILE: Apps/Control-Panel/Conky/conky_readout.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
import os  # info: import os
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Lib"))  # info: sys . path . insert ( 0 ,
import rr_settings  # noqa: E402
import rr_sources as src  # noqa: E402


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    s = rr_settings.load()  # info: set s
    p = src.Paths(s["database_root"], s["pacific_root"])  # info: set p
    what = sys.argv[1] if len(sys.argv) > 1 else ""  # info: set what
    arg = sys.argv[2] if len(sys.argv) > 2 else ""  # info: set arg
    if what in ("soc", "soctext"):  # info: if what in ( "soc" , "soctext" )
        d = src.read_json(p.energy / f"soc/{arg}-last.json") or {}  # info: set d
        v = d.get("soc")  # info: set v
        if what == "soc":  # info: if what == "soc" :
            print(int(v) if isinstance(v, (int, float)) else 0)  # info: call print
        else:  # info: else :
            a = src.age_s(d.get("at"))  # info: set a
            stale = " STALE" if a is not None and a > s["stale_after_sec"] else ""  # info: set stale
            print(f"{v:.1f}% · {src.fmt_age(a)}{stale}" if isinstance(v, (int, float)) else "n/a")  # info: call print
    elif what in ("laptop", "laptoptext"):  # info: elif what in ( "laptop" , "laptoptext" )
        lap = src.laptop_battery()  # info: set lap
        if what == "laptop":  # info: if what == "laptop" :
            print(int(lap[0]) if lap else 0)  # info: call print
        else:  # info: else :
            print(f"{lap[0]:.0f}% {lap[1]} {'AC' if lap[2] else 'battery'}" if lap else "n/a")  # info: call print
    elif what in ("cpu", "mem"):  # info: elif what in ( "cpu" , "mem" )
        sy = src.system(p)  # info: set sy
        v = sy["cpu" if what == "cpu" else "mem"]  # info: set v
        print(int(v) if isinstance(v, (int, float)) else 0)  # info: call print
    elif what == "npu":  # info: elif what == "npu" :
        n = src.npu(p, flm_port=int(s.get("flm_port", 52625)))  # info: set n
        print(f"{'accel ok' if n['accel'] else 'no accel'} · {n['state'].split(' —')[0]} · lock {n['lock'].split(' ')[0]}")  # info: call print
    elif what == "poller":  # info: elif what == "poller" :
        print(src.poller_quick(src.proc_argvs())[0])  # info: call print
    else:  # info: else :
        print("?")  # info: call print


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    try:  # info: try :
        main()  # info: call main
    except Exception as e:  # never break the widget
        print(f"err {type(e).__name__}", file=sys.stdout)  # info: call print
        os._exit(0)  # info: os . _exit ( 0 )
