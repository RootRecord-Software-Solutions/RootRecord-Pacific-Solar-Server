from pathlib import Path
SKILL_ROOT = Path("/home/rootrecord/.ollama/skills/system-stats")
SYSTEM_DATA = Path("/home/rootrecord/Database/SYSTEM")
SAMPLES = SYSTEM_DATA / "samples"
CPU = SYSTEM_DATA / "cpu"
MEM = SYSTEM_DATA / "mem"
LOAD = SYSTEM_DATA / "load"
LAST = SYSTEM_DATA / "last"
LOG_DIR = Path("/home/rootrecord/.ollama/skills/logs/store")

def ensure_dirs():
    for p in (SAMPLES, CPU, MEM, LOAD, LAST, LOG_DIR):
        p.mkdir(parents=True, exist_ok=True)
