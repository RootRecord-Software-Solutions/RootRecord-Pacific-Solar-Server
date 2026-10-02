# ==============================================================================
# FILE: Media/Voice/scripts/system_perf.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
import json  # info: import json
import os  # info: import os
import re  # info: import re
import shutil  # info: import shutil
import subprocess  # info: import subprocess
import sys  # info: import sys
import tempfile  # info: import tempfile
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
from speakable import spoken_clock  # noqa: E402
from speakers import retire_current  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
REPORT = "system_perf"  # info: set REPORT
MD = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice"))) / f"{REPORT}_current.md"  # info: set MD


# ====================================================
# SECTION: function cpu_pct
# What it does: cpu pct.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cpu_pct(interval: float = 0.5) -> float:  # info: def cpu_pct
    def snap():  # info: def snap
        v = [int(x) for x in open("/proc/stat").readline().split()[1:]]  # info: set v
        idle = v[3] + (v[4] if len(v) > 4 else 0)  # info: set idle
        return sum(v), idle  # info: return sum ( v ) , idle
    t1, i1 = snap(); time.sleep(interval); t2, i2 = snap()  # info: t1 , i1 = snap ( ) ;
    return round(100.0 * (1 - (i2 - i1) / max(1, t2 - t1)), 1)  # info: return round ( 100.0 * ( 1 -


# ====================================================
# SECTION: function meminfo
# What it does: meminfo.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def meminfo() -> dict:  # info: def meminfo
    out = {}  # info: set out
    for ln in open("/proc/meminfo"):  # info: for ln in open ( "/proc/meminfo" ) :
        k, v = ln.split(":", 1)  # info: k , v = ln . split (
        out[k] = int(v.split()[0])  # info: out [ k ] = int ( v
    return out  # info: return out


# ====================================================
# SECTION: function read
# What it does: read.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read(path: str) -> str | None:  # info: def read
    try:  # info: try :
        return Path(path).read_text().strip()  # info: return Path ( path ) . read_text (
    except OSError:  # info: except OSError :
        return None  # info: return None


# ====================================================
# SECTION: function load_hw
# What it does: Read temperature, iGPU, and NPU from host_hw. Missing values stay None. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_hw() -> dict:  # info: def load_hw
    empty = {"temp_c": None, "temp_source": None, "gpu_name": None, "gpu_pct": None, "npu_present": None, "npu_pct": None}  # info: set empty
    path = HERE.parents[2] / "System" / "scripts" / "host_hw.py"  # info: set path
    if not path.is_file():  # info: if not path . is_file
        return empty  # info: return empty
    try:  # info: try
        spec = importlib.util.spec_from_file_location("rr_host_hw", path)  # info: set spec
        mod = importlib.util.module_from_spec(spec)  # info: set mod
        spec.loader.exec_module(mod)  # info: spec . loader . exec_module
        row = mod.snapshot()  # info: set row
    except Exception:  # info: except Exception
        return empty  # info: return empty
    if not isinstance(row, dict):  # info: if not isinstance ( row , dict )
        return empty  # info: return empty
    empty.update({key: row.get(key) for key in empty})  # info: empty . update
    return empty  # info: return empty


# ====================================================
# SECTION: function sample
# What it does: sample.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sample() -> dict:  # info: def sample
    m = meminfo()  # info: set m
    total, avail = m["MemTotal"] / 1048576, m["MemAvailable"] / 1048576  # info: total , avail = m [ "MemTotal" ]
    du = shutil.disk_usage("/")  # info: set du
    bat = next(iter(sorted(Path("/sys/class/power_supply").glob("BAT*"))), None)  # info: set bat
    ac = next((p for p in Path("/sys/class/power_supply").iterdir() if read(f"{p}/type") == "Mains"), None) if Path("/sys/class/power_supply").is_dir() else None  # info: set ac
    up = float(open("/proc/uptime").read().split()[0])  # info: set up
    return {  # info: return {
        "cpu_pct": cpu_pct(),  # info: "cpu_pct" : cpu_pct ( ) ,
        "load": open("/proc/loadavg").read().split()[:3],  # info: "load" : open ( "/proc/loadavg" ) . read
        "mem_pct": round(100 * (1 - avail / total), 1), "mem_used_gb": round(total - avail, 1), "mem_total_gb": round(total, 1),  # info: "mem_pct" : round ( 100 * ( 1
        "swap_used_gb": round((m.get("SwapTotal", 0) - m.get("SwapFree", 0)) / 1048576, 1),  # info: "swap_used_gb" : round ( ( m . get
        "disk_pct": round(100 * du.used / du.total, 1), "disk_used_gb": round(du.used / 1e9), "disk_total_gb": round(du.total / 1e9),  # info: "disk_pct" : round ( 100 * du .
        "battery_pct": int(read(f"{bat}/capacity")) if bat and read(f"{bat}/capacity") else None,  # info: "battery_pct" : int ( read ( f" {
        "battery_status": read(f"{bat}/status") if bat else None,  # info: "battery_status" : read ( f" { bat }
        "on_ac": (read(f"{ac}/online") == "1") if ac else None,  # info: call "on_ac"
        "uptime_s": int(up),  # info: "uptime_s" : int ( up ) ,
        **load_hw(),  # info: call load_hw
    }  # info: }


# ====================================================
# SECTION: function texts
# What it does: texts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def texts(s: dict, now: datetime) -> tuple[str, str]:  # info: def texts
    ts = now.isoformat(timespec="seconds")  # info: set ts
    batt = "not sampled" if s["battery_pct"] is None else f"{s['battery_pct']}% ({s['battery_status']}{', on AC' if s['on_ac'] else ', on battery' if s['on_ac'] is False else ''})"  # info: set batt
    up_h, up_m = s["uptime_s"] // 3600, (s["uptime_s"] % 3600) // 60  # info: up_h , up_m = s [ "uptime_s" ]
    md = (  # info: set md
        f"# System Performance — {ts}\n\n"
        f"Host: HI Pacific Solar Root Server\n\n"  # info: f" Host: HI Pacific Solar Root Server\n\n "
        f"| Metric | Value |\n|---|---|\n"  # info: f" | Metric | Value |\n|---|---|\n "
        f"| CPU | {s['cpu_pct']}% (load {' / '.join(s['load'])}) |\n"  # info: f" | CPU | { s [ 'cpu_pct' ] }
        f"| RAM | {s['mem_pct']}% used ({s['mem_used_gb']} / {s['mem_total_gb']} GB); swap used {s['swap_used_gb']} GB |\n"  # info: f" | RAM | { s [ 'mem_pct' ] }
        f"| Disk / | {s['disk_pct']}% used ({s['disk_used_gb']} / {s['disk_total_gb']} GB) |\n"  # info: f" | Disk / | { s [ 'disk_pct' ] }
        f"| Host battery | {batt} |\n"  # info: f" | Host battery | { batt } |\n "
        f"| Uptime | {up_h}h {up_m}m |\n"  # info: f" | Uptime | { up_h } h { up_m
    )  # info: )
    spoken = [  # info: set spoken
        "System performance report.",  # info: "System performance report." ,
        f"Report generated at {spoken_clock(now.hour, now.minute)}.",  # info: f" Report generated at { spoken_clock ( now . hour , now . minute ) } . " ,
        f"CPU {round(s['cpu_pct'])}%.",  # info: f" CPU { round ( s [ 'cpu_pct'
        f"Memory {round(s['mem_pct'])}% used, {s['mem_used_gb']} of {s['mem_total_gb']} gigabytes.",  # info: f" Memory { round ( s [ 'mem_pct'
        f"Disk {round(s['disk_pct'])}% used.",  # info: f" Disk { round ( s [ 'disk_pct'
    ]  # info: ]
    import compare_span  # info: import compare_span
    spoken.extend(compare_span.sentences("system.cpu_pct", round(s["cpu_pct"]), "CPU", now))  # info: spoken . extend cpu change
    spoken.extend(compare_span.sentences("system.mem_pct", round(s["mem_pct"]), "Memory", now))  # info: spoken . extend memory change
    spoken.extend(compare_span.sentences("system.disk_pct", round(s["disk_pct"]), "Disk", now))  # info: spoken . extend disk change
    if s["battery_pct"] is not None:  # info: if s [ "battery_pct" ] is not None
        spoken.append(f"Host battery {s['battery_pct']}%, {'on AC' if s['on_ac'] else 'on battery'}.")  # info: spoken . append ( f" Host battery { s
        spoken.extend(compare_span.sentences("system.battery_pct", s["battery_pct"], "Host battery", now))  # info: spoken . extend battery change
    spoken.append(f"Uptime {up_h} hour{'s' if up_h != 1 else ''} {up_m} minute{'s' if up_m != 1 else ''}.")  # info: spoken . append ( f" Uptime { up_h
    if s.get("temp_c") is not None:  # info: if s . get ( "temp_c" ) is not None
        src = f" ({s['temp_source']})" if s.get("temp_source") else ""  # info: set src
        md += f"| Temp | {s['temp_c']}°C{src} |\n"  # info: set md
        spoken.append(f"Temperature {s['temp_c']} degrees Celsius.")  # info: spoken . append ( f" Temperature { s [ 'temp_c' ] } degrees Celsius. " )
        spoken.extend(compare_span.sentences("system.temp_c", s["temp_c"], "Temperature", now))  # info: spoken . extend temperature change
    if s.get("gpu_pct") is not None:  # info: if s . get ( "gpu_pct" ) is not None
        name = s.get("gpu_name") or "iGPU"  # info: set name
        md += f"| iGPU | {name} — {s['gpu_pct']}% |\n"  # info: set md
        spoken.append(f"Integrated GPU {s['gpu_pct']} percent.")  # info: spoken . append
        spoken.extend(compare_span.sentences("system.gpu_pct", s["gpu_pct"], "Integrated GPU", now))  # info: spoken . extend gpu change
    elif s.get("gpu_name"):  # info: elif s . get ( "gpu_name" )
        md += f"| iGPU | {s['gpu_name']} |\n"  # info: set md
    if s.get("npu_present") is True and s.get("npu_pct") is not None:  # info: if s . get ( "npu_present" ) is True and s . get ( "npu_pct" )
        md += f"| NPU | {s['npu_pct']}% (present) |\n"  # info: set md
        spoken.append(f"NPU {s['npu_pct']} percent, present.")  # info: spoken . append
        spoken.extend(compare_span.sentences("system.npu_pct", s["npu_pct"], "NPU", now))  # info: spoken . extend npu change
    elif s.get("npu_present") is True:  # info: elif s . get ( "npu_present" ) is True
        md += "| NPU | present, busy percent not sampled |\n"  # info: set md
        spoken.append("NPU is present. Busy percent was not sampled.")  # info: spoken . append
    elif s.get("npu_present") is False:  # info: elif s . get ( "npu_present" ) is False
        md += "| NPU | not present |\n"  # info: set md
        spoken.append("NPU is not present.")  # info: spoken . append
    md += f"\n_Template report (no LLM). Measured on the desk at {ts}. A missing hardware row was not sampled._\n"  # info: set md
    spoken.append("End of system report.")  # info: spoken . append ( "End of system report." )
    return md, " ".join(spoken)  # info: return md , " " . join ( spoken


# ====================================================
# SECTION: function write_md
# What it does: write md.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_md(md: str) -> None:  # info: def write_md
    MD.parent.mkdir(parents=True, exist_ok=True)  # info: MD . parent . mkdir ( parents =
    if MD.is_file():  # info: if MD . is_file ( ) :
        retire_current(MD)  # info: call retire_current
    tmp = MD.with_suffix(".md.tmp")  # info: set tmp
    tmp.write_text(md, encoding="utf-8")  # info: tmp . write_text ( md , encoding =
    os.replace(tmp, MD)  # info: os . replace ( tmp , MD )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    now = datetime.now().astimezone().replace(microsecond=0)  # info: set now
    s = sample()  # info: set s
    md, spoken = texts(s, now)  # info: md , spoken = texts ( s ,
    write_md(md)  # info: call write_md
    res = {"ok": True, "report": REPORT, "md": str(MD), "cpu_pct": s["cpu_pct"], "mem_pct": s["mem_pct"]}  # info: set res
    if "--no-voice" not in sys.argv:  # info: if "--no-voice" not in sys . argv :
        import status_cue  # info: import status_cue
        res["status_starting"] = status_cue.play(REPORT, "starting")  # info: res [ "status_starting" ] = status_cue . play ( REPORT , "starting" )
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:  # info: with tempfile . NamedTemporaryFile ( "w" , suffix
            f.write(spoken)  # info: f . write ( spoken )
        try:  # info: try :
            p = subprocess.run(["bash", str(HERE / "voice-render.sh"), "stitch", "--report", REPORT, "--kind", "system",  # info: set p
                                "--text-file", f.name], capture_output=True, text=True, timeout=240)  # info: "--text-file" , f . name ] , capture_output
            last = (p.stdout.strip().splitlines() or ["{}"])[-1]  # info: set last
            res["voice_rc"] = p.returncode  # info: res [ "voice_rc" ] = p . returncode
            try:  # info: try :
                res["voice"] = json.loads(last)  # info: res [ "voice" ] = json . loads
            except ValueError:  # info: except ValueError :
                res["voice"] = {"detail": "busy (single-flight)" if p.returncode == 75 else "no json"}  # info: res [ "voice" ] = { "detail" :
            wav = (res.get("voice") or {}).get("wav")  # info: set wav
            if wav:  # info: if wav
                import voice_deliver  # info: import voice_deliver
                res["deliver"] = voice_deliver.deliver(REPORT, wav, spoken, "system", report_text=md)  # info: res [ "deliver" ] = voice_deliver . deliver
            if os.environ.get("RR_RADIO_PUSH", "1") == "1" and p.returncode == 0 and wav:  # info: if os . environ . get ( "RR_RADIO_PUSH" , "1" ) == "1" and p . returncode == 0 and wav
                import radio_push  # info: import radio_push
                res["status_transit"] = status_cue.play(REPORT, "transit")  # info: res [ "status_transit" ] = status_cue . play ( REPORT , "transit" )
                res["radio"] = radio_push.push_report(REPORT)  # info: res [ "radio" ] = radio_push . push_report ( REPORT )
                res["status_send"] = status_cue.after_push(REPORT, res["radio"])  # info: res [ "status_send" ] = status_cue . after_push ( REPORT , res [ "radio" ] )
        finally:  # info: finally :
            os.unlink(f.name)  # info: os . unlink ( f . name )
    print(json.dumps(res))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
