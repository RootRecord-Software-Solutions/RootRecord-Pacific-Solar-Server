# ==============================================================================
# FILE: System/lib/paths.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
from pathlib import Path  # info: from pathlib import Path

# Code home = Pacific System/ (this file lives at System/lib/paths.py)
SYSTEM_ROOT = Path(__file__).resolve().parents[1]  # info: set SYSTEM_ROOT

# Canonical Database root.
DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DATABASE_ROOT
SYSTEM_DATA = DATABASE_ROOT / "System"  # info: set SYSTEM_DATA
SAMPLES = SYSTEM_DATA / "samples"  # info: set SAMPLES
CPU = SYSTEM_DATA / "cpu"  # info: set CPU
MEM = SYSTEM_DATA / "mem"  # info: set MEM
LOAD = SYSTEM_DATA / "load"  # info: set LOAD
LAST = SYSTEM_DATA / "last"  # info: set LAST
LOG_DIR = DATABASE_ROOT / "Logs" / "System"  # info: set LOG_DIR

# SQLite isolation
SYSTEM_DB = SYSTEM_DATA / "system.db"  # info: set SYSTEM_DB
LAYERS_DIR = SYSTEM_DATA / "layers"  # info: set LAYERS_DIR
LAYERS = ("1sec", "1min", "5min", "15min", "1hour", "day", "7days", "month", "year")  # info: set LAYERS


# ====================================================
# SECTION: function ensure_dirs
# What it does: ensure dirs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_dirs():  # info: def ensure_dirs
    for p in (SAMPLES, CPU, MEM, LOAD, LAST, LOG_DIR, LAYERS_DIR):  # info: for p in ( SAMPLES , CPU ,
        p.mkdir(parents=True, exist_ok=True)  # info: p . mkdir ( parents = True ,
