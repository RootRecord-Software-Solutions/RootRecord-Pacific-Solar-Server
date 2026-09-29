from pathlib import Path

# Code home = Pacific System/ (this file lives at System/lib/paths.py)
SYSTEM_ROOT = Path(__file__).resolve().parents[1]

# Canonical Database root.
DATABASE_ROOT = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
SYSTEM_DATA = DATABASE_ROOT / "System"
SAMPLES = SYSTEM_DATA / "samples"
CPU = SYSTEM_DATA / "cpu"
MEM = SYSTEM_DATA / "mem"
LOAD = SYSTEM_DATA / "load"
LAST = SYSTEM_DATA / "last"
LOG_DIR = DATABASE_ROOT / "Logs" / "System"

# SQLite isolation
SYSTEM_DB = SYSTEM_DATA / "system.db"
LAYERS_DIR = SYSTEM_DATA / "layers"
LAYERS = ("1sec", "1min", "5min", "15min", "1hour", "day", "7days", "month", "year")


def ensure_dirs():
    for p in (SAMPLES, CPU, MEM, LOAD, LAST, LOG_DIR, LAYERS_DIR):
        p.mkdir(parents=True, exist_ok=True)
