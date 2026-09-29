#!/usr/bin/env python3
"""G3 system_perf voice report (Bruce, template only, no LLM) — first ported G1 voice report.

G1: old skills/system-perf/scripts/job.py (APScheduler :06 hourly, CPU/RAM/battery/disk/uptime,
Discord post + Kokoro WAV + AWS radio). G3: stdlib host sample -> text + stitched WAV, NO delivery.

Writes
  Database/System/Reports/system_perf_current.md   (old copy -> Archive/system_perf_YYYYMMDDTHHMM.md)
  Database/Media/Audio/Voice/system_perf_current.wav (+ .read.txt/.speak.txt; old -> Archive/)
WAV via Media/Voice/scripts/voice-render.sh stitch (single-flight lock, nice 10, non-resident);
fixed sentences come from the phrase-clip cache, numbers are rendered live.
Scheduled by jobs.py id voice_system_perf (EVERY_MINUTE only_at_minutes=[6]) — gated OFF unless
RR_VOICE_SYSTEM_PERF=1 in the poller environment at poller start. --no-voice = text only.
Added 2026-09-29 (g3-voice-ailog).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from speakable import spoken_clock  # noqa: E402
from speakers import retire_current  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
REPORT = "system_perf"
MD = DB / "System" / "Reports" / f"{REPORT}_current.md"


def cpu_pct(interval: float = 0.5) -> float:
    def snap():
        v = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        idle = v[3] + (v[4] if len(v) > 4 else 0)
        return sum(v), idle
    t1, i1 = snap(); time.sleep(interval); t2, i2 = snap()
    return round(100.0 * (1 - (i2 - i1) / max(1, t2 - t1)), 1)


def meminfo() -> dict:
    out = {}
    for ln in open("/proc/meminfo"):
        k, v = ln.split(":", 1)
        out[k] = int(v.split()[0])
    return out


def read(path: str) -> str | None:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def sample() -> dict:
    m = meminfo()
    total, avail = m["MemTotal"] / 1048576, m["MemAvailable"] / 1048576
    du = shutil.disk_usage("/")
    bat = next(iter(sorted(Path("/sys/class/power_supply").glob("BAT*"))), None)
    ac = next((p for p in Path("/sys/class/power_supply").iterdir() if read(f"{p}/type") == "Mains"), None) if Path("/sys/class/power_supply").is_dir() else None
    up = float(open("/proc/uptime").read().split()[0])
    return {
        "cpu_pct": cpu_pct(),
        "load": open("/proc/loadavg").read().split()[:3],
        "mem_pct": round(100 * (1 - avail / total), 1), "mem_used_gb": round(total - avail, 1), "mem_total_gb": round(total, 1),
        "swap_used_gb": round((m.get("SwapTotal", 0) - m.get("SwapFree", 0)) / 1048576, 1),
        "disk_pct": round(100 * du.used / du.total, 1), "disk_used_gb": round(du.used / 1e9), "disk_total_gb": round(du.total / 1e9),
        "battery_pct": int(read(f"{bat}/capacity")) if bat and read(f"{bat}/capacity") else None,
        "battery_status": read(f"{bat}/status") if bat else None,
        "on_ac": (read(f"{ac}/online") == "1") if ac else None,
        "uptime_s": int(up),
    }


def texts(s: dict, now: datetime) -> tuple[str, str]:
    ts = now.isoformat(timespec="seconds")
    batt = "not sampled" if s["battery_pct"] is None else f"{s['battery_pct']}% ({s['battery_status']}{', on AC' if s['on_ac'] else ', on battery' if s['on_ac'] is False else ''})"
    up_h, up_m = s["uptime_s"] // 3600, (s["uptime_s"] % 3600) // 60
    md = (
        f"# System Performance — {ts}\n\n"
        f"Host: HI Pacific Solar Root Server\n\n"
        f"| Metric | Value |\n|---|---|\n"
        f"| CPU | {s['cpu_pct']}% (load {' / '.join(s['load'])}) |\n"
        f"| RAM | {s['mem_pct']}% used ({s['mem_used_gb']} / {s['mem_total_gb']} GB); swap used {s['swap_used_gb']} GB |\n"
        f"| Disk / | {s['disk_pct']}% used ({s['disk_used_gb']} / {s['disk_total_gb']} GB) |\n"
        f"| Host battery | {batt} |\n"
        f"| Uptime | {up_h}h {up_m}m |\n\n"
        f"_Template report (no LLM). Measured on the desk at {ts}. Delivery OFF._\n"
    )
    spoken = [
        "System performance report.",
        f"Host desk at {spoken_clock(now.hour, now.minute)} Hawaiian Standard Time.",
        f"CPU {round(s['cpu_pct'])}%.",
        f"Memory {round(s['mem_pct'])}% used, {s['mem_used_gb']} of {s['mem_total_gb']} gigabytes.",
        f"Disk {round(s['disk_pct'])}% used.",
    ]
    if s["battery_pct"] is not None:
        spoken.append(f"Host battery {s['battery_pct']}%, {'on AC' if s['on_ac'] else 'on battery'}.")
    spoken.append(f"Uptime {up_h} hours {up_m} minutes.")
    spoken.append("End of system report.")
    return md, " ".join(spoken)


def write_md(md: str) -> None:
    MD.parent.mkdir(parents=True, exist_ok=True)
    if MD.is_file():
        retire_current(MD)
    tmp = MD.with_suffix(".md.tmp")
    tmp.write_text(md, encoding="utf-8")
    os.replace(tmp, MD)


def main() -> int:
    now = datetime.now().astimezone().replace(microsecond=0)
    s = sample()
    md, spoken = texts(s, now)
    write_md(md)
    res = {"ok": True, "report": REPORT, "md": str(MD), "cpu_pct": s["cpu_pct"], "mem_pct": s["mem_pct"]}
    if "--no-voice" not in sys.argv:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(spoken)
        try:
            p = subprocess.run(["bash", str(HERE / "voice-render.sh"), "stitch", "--report", REPORT, "--kind", "system",
                                "--text-file", f.name], capture_output=True, text=True, timeout=240)
            last = (p.stdout.strip().splitlines() or ["{}"])[-1]
            res["voice_rc"] = p.returncode
            try:
                res["voice"] = json.loads(last)
            except ValueError:
                res["voice"] = {"detail": "busy (single-flight)" if p.returncode == 75 else "no json"}
        finally:
            os.unlink(f.name)
    print(json.dumps(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
