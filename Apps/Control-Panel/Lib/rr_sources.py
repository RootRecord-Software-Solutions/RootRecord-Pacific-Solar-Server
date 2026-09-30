"""rr_sources.py — read-only data readers for Root Monitor (GTK, was "RootRecord Control Panel") and Conky readout.

INFO — MUST HAVE (future agents), added 2026-09-29:
- READ-ONLY. Every function here only reads existing JSON / log / report files, sysfs and /proc.
  Nothing here writes, starts, stops, sends or loads a model.
- No network calls, no sqlite. Same sources as poller-dashboard.py and the poller ENERGY status line.
- No GTK import here, so the Conky helper can reuse it cheaply.
- Camera functions are only called by the camera viewer when it is ON and its page is visible.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import time  # info: import time
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

TZ = ZoneInfo("Pacific/Honolulu")  # info: set TZ

# (label, systemd unit or None, scope, argv suffixes to count, expected count or None=any>=1)
# Copied from poller-dashboard.py SERVICES (2026-09-29) so the panel shows the same rows.
# ====================================================
# SECTION: SERVICES
# What it does: Set SERVICES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SERVICES = [  # info: set SERVICES
    ("poller", "rr-rootserver-poller.service", "user", ("Automations/scripts/rootserver_poller.py",), 1),  # info: call (
    ("relay", None, "", ("telegram/scripts/council-relay.py",), 1),  # info: call (
    ("BLE", "ava-ecoflow-ble.service", "user", ("scripts/ble/ble-owner.py",), 1),  # info: call (
    ("globe", "network-globe-hawaii.service", "user", ("local-data-globe/collector.js",), 1),  # info: call (
    ("cam", None, "", ("cam_server.py",), 1),  # info: call (
    ("weather", None, "", ("Weather/scripts/run_poller.py", "weather/scripts/run_poller.py"), 1),  # info: call (
    ("ollama", "ollama.service", "system", ("ollama",), None),  # info: call (
    ("tunnel", None, "", ("cloudflared",), None),  # info: call (
]  # info: ]

# Counters so --check can prove what was (not) touched.
STATS = {"camera_dir_scans": 0, "camera_files_opened": 0, "camera_http_fetches": 0}  # info: set STATS


# ====================================================
# SECTION: class Paths
# What it does: Paths.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Paths:  # info: class Paths
    def __init__(self, database_root: str, pacific_root: str):  # info: def __init__
        self.db = Path(database_root)  # info: self . db = Path ( database_root )
        self.pacific = Path(pacific_root)  # info: self . pacific = Path ( pacific_root )

    @property  # info: decorator property
    def energy(self) -> Path:  # info: def energy
        return self.db / "Energy"  # info: return self . db / "Energy"

    @property  # info: decorator property
    def log(self) -> Path:  # info: def log
        return self.db / "Logs/Automations/automations_current.log"  # info: return self . db / "Logs/Automations/automations_current.log"

    @property  # info: decorator property
    def logs_dir(self) -> Path:  # info: def logs_dir
        return self.db / "Logs"  # info: return self . db / "Logs"

    @property  # info: decorator property
    def system_last(self) -> Path:  # info: def system_last
        return self.db / "System/last/host-last.json"  # info: return self . db / "System/last/host-last.json"

    @property  # info: decorator property
    def system_status(self) -> Path:  # info: def system_status
        return self.db / "System/status/system-status.json"  # info: return self . db / "System/status/system-status.json"

    @property  # info: decorator property
    def weather_l0(self) -> Path:  # info: def weather_l0
        return self.db / "Weather/Hawai'i/reports/0 Level Processing"  # info: return self . db / "Weather/Hawai'i/reports/0 Level Processing"

    @property  # info: decorator property
    def inference_log(self) -> Path:  # info: def inference_log
        return self.db / "Logs/AI/Inference/inference_current.jsonl"  # info: return self . db / "Logs/AI/Inference/inference_current.jsonl"

    @property  # info: decorator property
    def routing_log(self) -> Path:  # info: def routing_log
        return self.db / "Logs/AI/Routing/routing_current.jsonl"  # info: return self . db / "Logs/AI/Routing/routing_current.jsonl"

    @property  # info: decorator property
    def ai_report(self) -> Path:  # info: def ai_report
        return self.db / "Logs/AI/Reports/ai-processing-report_current.md"  # info: return self . db / "Logs/AI/Reports/ai-processing-report_current.md"

    @property  # info: decorator property
    def plumbing_state(self) -> Path:  # info: def plumbing_state
        return self.db / "Github/plumbing/state"  # info: return self . db / "Github/plumbing/state"

    @property  # info: decorator property
    def camera_images(self) -> Path:  # info: def camera_images
        return self.db / "Media/Images"  # info: return self . db / "Media/Images"

    @property  # info: decorator property
    def npu_status_sh(self) -> Path:  # info: def npu_status_sh
        return self.pacific / "System/scripts/plumbing/npu-status.sh"  # info: return self . pacific / "System/scripts/plumbing/npu-status.sh"

    @property  # info: decorator property
    def poller_dashboard(self) -> Path:  # info: def poller_dashboard
        return self.pacific / "Automations/scripts/poller/poller-dashboard.py"  # info: return self . pacific / "Automations/scripts/poller/poller-dashboard.py"

    @property  # info: decorator property
    def jobs_py(self) -> Path:  # info: def jobs_py
        return self.pacific / "Automations/scripts/jobs.py"  # info: return self . pacific / "Automations/scripts/jobs.py"

    @property  # info: decorator property
    def cameras_dir(self) -> Path:  # info: def cameras_dir
        return self.pacific / "Security/Cameras"  # info: return self . pacific / "Security/Cameras"


# ---------------------------------------------------------------- helpers
# ====================================================
# SECTION: function read_json
# What it does: read json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_json(p: Path):  # info: def read_json
    try:  # info: try :
        return json.loads(p.read_text(encoding="utf-8"))  # info: return json . loads ( p . read_text
    except Exception:  # info: except Exception :
        return None  # info: return None


# ====================================================
# SECTION: function parse_ts
# What it does: parse ts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_ts(s):  # info: def parse_ts
    try:  # info: try :
        s = str(s)  # info: set s
        if s.endswith("Z"):  # info: if s . endswith ( "Z" ) :
            s = s[:-1] + "+00:00"  # info: set s
        dt = datetime.fromisoformat(s)  # info: set dt
        if dt.tzinfo is None:  # info: if dt . tzinfo is None :
            dt = dt.replace(tzinfo=TZ)  # info: set dt
        return dt  # info: return dt
    except Exception:  # info: except Exception :
        return None  # info: return None


# ====================================================
# SECTION: function age_s
# What it does: age s.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def age_s(ts) -> float | None:  # info: def age_s
    dt = parse_ts(ts)  # info: set dt
    return None if dt is None else (datetime.now(TZ) - dt).total_seconds()  # info: return None if dt is None else (


# ====================================================
# SECTION: function fmt_age
# What it does: fmt age.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fmt_age(a: float | None) -> str:  # info: def fmt_age
    if a is None:  # info: if a is None :
        return "no reading"  # info: return "no reading"
    a = max(0, int(a))  # info: set a
    if a < 3600:  # info: if a < 3600 :
        return f"{a // 60}m{a % 60:02d}s ago"  # info: return f" { a // 60 } m
    return f"{a // 3600}h{(a % 3600) // 60:02d}m ago"  # info: return f" { a // 3600 } h


# ====================================================
# SECTION: function hst
# What it does: hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hst(ts) -> str:  # info: def hst
    dt = parse_ts(ts)  # info: set dt
    return dt.astimezone(TZ).strftime("%H:%M:%S HST") if dt else "—"  # info: return dt . astimezone ( TZ ) .


# ====================================================
# SECTION: function tail_lines
# What it does: tail lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tail_lines(path: Path, nbytes: int = 65536) -> list[str]:  # info: def tail_lines
    try:  # info: try :
        with path.open("rb") as f:  # info: with path . open ( "rb" ) as
            f.seek(0, 2)  # info: f . seek ( 0 , 2 )
            size = f.tell()  # info: set size
            f.seek(max(0, size - nbytes))  # info: f . seek ( max ( 0 ,
            data = f.read().decode("utf-8", errors="replace")  # info: set data
        lines = data.splitlines()  # info: set lines
        return lines[1:] if size > nbytes else lines  # info: return lines [ 1 : ] if size
    except OSError:  # info: except OSError :
        return []  # info: return [ ]


# ---------------------------------------------------------------- energy
# ====================================================
# SECTION: function laptop_battery
# What it does: (pct, status, on_ac) from sysfs, same logic as poller-dashboard.py; None if no battery.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def laptop_battery():  # info: def laptop_battery
    """(pct, status, on_ac) from sysfs, same logic as poller-dashboard.py; None if no battery."""  # info: """(pct, status, on_ac) from sysfs, same logic as poller-dashboard.py; None if no battery."""
    try:  # info: try :
        ps = Path("/sys/class/power_supply")  # info: set ps
        bat = next((b for b in sorted(ps.glob("BAT*")) if (b / "capacity").exists()), None)  # info: set bat
        if bat is None:  # info: if bat is None :
            return None  # info: return None
        ac = any((m / "online").read_text().strip() == "1" for m in ps.iterdir()  # info: set ac
                 if (m / "type").exists() and (m / "type").read_text().strip() == "Mains" and (m / "online").exists())  # info: if ( m / "type" ) . exists
        return (float((bat / "capacity").read_text().strip()), (bat / "status").read_text().strip(), ac)  # info: return ( float ( ( bat / "capacity"
    except Exception:  # info: except Exception :
        return None  # info: return None


# ====================================================
# SECTION: function energy
# What it does: energy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def energy(paths: Paths) -> dict:  # info: def energy
    out = {}  # info: set out
    for dev in ("river2pro", "delta2"):  # info: for dev in ( "river2pro" , "delta2" )
        soc = read_json(paths.energy / f"soc/{dev}-last.json") or {}  # info: set soc
        w = read_json(paths.energy / f"watts/{dev}-last.json") or {}  # info: set w
        out[dev] = {  # info: out [ dev ] = {
            "soc": soc.get("soc"), "at": soc.get("at"), "source": soc.get("source"),  # info: "soc" : soc . get ( "soc" )
            "age": age_s(soc.get("at")),  # info: "age" : age_s ( soc . get (
            "solar_in": w.get("solar_input_power"), "ac_out": w.get("ac_output_power"),  # info: "solar_in" : w . get ( "solar_input_power" )
            "ac_in": w.get("ac_input_power"), "usbc_out": w.get("usbc_output_power"),  # info: "ac_in" : w . get ( "ac_input_power" )
            "charge_source": w.get("charge_source"), "watts_at": w.get("at"),  # info: "charge_source" : w . get ( "charge_source" )
        }  # info: }
    out["laptop"] = laptop_battery()  # info: out [ "laptop" ] = laptop_battery ( )
    return out  # info: return out


# ====================================================
# SECTION: function log_digest
# What it does: Latest poller status line (ENERGY heartbeat), SYSTEM line, SUMMARY lines, log age, tail.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_digest(paths: Paths) -> dict:  # info: def log_digest
    """Latest poller status line (ENERGY heartbeat), SYSTEM line, SUMMARY lines, log age, tail."""  # info: """Latest poller status line (ENERGY heartbeat), SYSTEM line, SUMMARY lines, log age, tail."""
    lines = tail_lines(paths.log)  # info: set lines
    d = {"energy_line": "", "energy_line_at": "", "system_line": "", "summary": {}, "lines": lines,  # info: set d
         "b3_expansion": None, "lap_field": None}  # info: "b3_expansion" : None , "lap_field" : None }
    try:  # info: try :
        d["log_age"] = time.time() - paths.log.stat().st_mtime  # info: d [ "log_age" ] = time . time
    except OSError:  # info: except OSError :
        d["log_age"] = None  # info: d [ "log_age" ] = None
    for ln in reversed(lines):  # info: for ln in reversed ( lines ) :
        if not d["energy_line"] and "ENERGY  " in ln:  # info: if not d [ "energy_line" ] and "ENERGY "
            i = ln.index("ENERGY  ")  # info: set i
            d["energy_line"], d["energy_line_at"] = ln[i:].strip(), ln[:i]  # info: d [ "energy_line" ] , d [ "energy_line_at"
            m = re.search(r"\bB3=(\S+)", ln)  # info: set m
            d["b3_expansion"] = m.group(1) if m else None  # info: d [ "b3_expansion" ] = m . group
            m = re.search(r"\bLAP=(\S+)", ln)  # info: set m
            d["lap_field"] = m.group(1) if m else None  # info: d [ "lap_field" ] = m . group
        if not d["system_line"] and "| SYSTEM " in ln:  # info: if not d [ "system_line" ] and "| SYSTEM "
            d["system_line"] = re.sub(r"\s+", " ", ln.split("| SYSTEM", 1)[1]).strip()  # info: d [ "system_line" ] = re . sub
        for dev in ("river2pro", "delta2"):  # info: for dev in ( "river2pro" , "delta2" )
            if dev not in d["summary"] and f"SUMMARY={dev} " in ln:  # info: if dev not in d [ "summary" ]
                m = re.search(r"SUMMARY=\S+ (.*)", ln)  # info: set m
                d["summary"][dev] = m.group(1) if m else ""  # info: d [ "summary" ] [ dev ] =
        if d["energy_line"] and d["system_line"] and len(d["summary"]) == 2:  # info: if d [ "energy_line" ] and d [
            break  # info: break
    return d  # info: return d


ANSI = re.compile(r"\033\[[0-9;?]*[A-Za-z]")  # info: set ANSI


# ====================================================
# SECTION: function load_poller_watch
# What it does: Import poller-watch.py for format_line / aeyes_solar_state (import only, no handlers run), exactly like poller-dashboard.py does.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_poller_watch(paths: Paths):  # info: def load_poller_watch
    """Import poller-watch.py for format_line / aeyes_solar_state (import only, no handlers run),
    exactly like poller-dashboard.py does."""
    import importlib.util  # info: import importlib . util
    try:  # info: try :
        p = paths.pacific / "Automations/scripts/poller/poller-watch.py"  # info: set p
        spec = importlib.util.spec_from_file_location("rr_poller_watch_cp", p)  # info: set spec
        mod = importlib.util.module_from_spec(spec)  # info: set mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod  # info: return mod
    except Exception:  # info: except Exception :
        return None  # info: return None


# ====================================================
# SECTION: function formatted_log
# What it does: formatted log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def formatted_log(pw, lines: list[str], n: int = 40) -> list[str]:  # info: def formatted_log
    out = []  # info: set out
    for ln in lines[-300:]:  # info: for ln in lines [ - 300 :
        try:  # info: try :
            f = pw.format_line(ln) if pw is not None else ln  # info: set f
        except Exception:  # info: except Exception :
            f = ln  # info: set f
        if f:  # info: if f :
            out.append(ANSI.sub("", f).rstrip())  # info: out . append ( ANSI . sub (
    return out[-n:]  # info: return out [ - n : ]


# ---------------------------------------------------------------- system
# ====================================================
# SECTION: function system
# What it does: system.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def system(paths: Paths) -> dict:  # info: def system
    last = read_json(paths.system_last) or {}  # info: set last
    f = last.get("fields") or {}  # info: set f
    val = lambda k: (f.get(k) or {}).get("value")  # noqa: E731
    st = read_json(paths.system_status) or {}  # info: set st
    five = ((st.get("five_min") or {}).get("metrics")) or {}  # info: set five
    avg = lambda k: (five.get(k) or {}).get("avg")  # noqa: E731
    return {  # info: return {
        "cpu": val("cpu_percent"), "mem": val("mem_used_percent"),  # info: "cpu" : val ( "cpu_percent" ) , "mem"
        "mem_avail": val("mem_available_bytes"), "mem_total": val("mem_total_bytes"),  # info: "mem_avail" : val ( "mem_available_bytes" ) , "mem_total"
        "load": (val("load1"), val("load5"), val("load15")),  # info: call "load"
        "at": last.get("at"), "age": age_s(last.get("at")), "host": last.get("host"),  # info: "at" : last . get ( "at" )
        "five_cpu": avg("cpu_percent"), "five_mem": avg("mem_used_percent"),  # info: "five_cpu" : avg ( "cpu_percent" ) , "five_mem"
        "five_start": (st.get("five_min") or {}).get("period_start"),  # info: call "five_start"
        "five_end": (st.get("five_min") or {}).get("period_end"),  # info: call "five_end"
    }  # info: }


# ---------------------------------------------------------------- weather
_zfp_cache: dict = {}  # info: set _zfp_cache


# ====================================================
# SECTION: function weather
# What it does: weather.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def weather(paths: Paths, zone: str, pw=None) -> dict:  # info: def weather
    d = {"solar": None, "zone": zone, "today": "", "tonight": "", "advisories": [], "collected": "",  # info: set d
         "state_generated": ""}  # info: "state_generated" : "" }
    if pw is not None:  # info: if pw is not None :
        try:  # info: try :
            d["solar"] = pw.aeyes_solar_state()  # info: d [ "solar" ] = pw . aeyes_solar_state
        except Exception:  # info: except Exception :
            d["solar"] = None  # info: d [ "solar" ] = None
    zfp = paths.weather_l0 / "zfp_zone_forecast_current.md"  # info: set zfp
    try:  # info: try :
        mt = zfp.stat().st_mtime  # info: set mt
    except OSError:  # info: except OSError :
        return d  # info: return d
    key = (str(zfp), mt, zone)  # info: set key
    if _zfp_cache.get("key") != key:  # info: if _zfp_cache . get ( "key" ) !=
        text = zfp.read_text(encoding="utf-8", errors="replace")  # info: set text
        m = re.search(r"\*\*Collected:\*\*\s*(\S+)", text)  # info: set m
        res = {"collected": m.group(1) if m else ""}  # info: set res
        blocks = re.split(r"\n(?=HIZ\d{3})", text)  # info: set blocks
        blk = next((b for b in blocks if re.search(rf"^{re.escape(zone)}-\s*$", b, re.M)), "")  # info: set blk
        res["advisories"] = sorted(set(re.findall(r"^\.\.\.(.+?)\.\.\.\s*$", blk, re.M)))  # info: res [ "advisories" ] = sorted ( set

        def para(tag):  # info: def para
            m2 = re.search(rf"^\.{tag}\.\.\.(.*?)(?=^\.[A-Z ]+\.\.\.|^\$\$|\Z)", blk, re.M | re.S)  # info: set m2
            return re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else ""  # info: return re . sub ( r"\s+" , " "
        res["today"], res["tonight"] = para("TODAY") or para("THIS AFTERNOON") or para("REST OF TODAY"), para("TONIGHT")  # info: res [ "today" ] , res [ "tonight"
        _zfp_cache.clear()  # info: _zfp_cache . clear ( )
        _zfp_cache.update(key=key, res=res)  # info: _zfp_cache . update ( key = key ,
        del text  # info: del text
    d.update(_zfp_cache["res"])  # info: d . update ( _zfp_cache [ "res" ]
    try:  # info: try :
        with (paths.weather_l0 / "Hawaii_State_Weather_Report_current.md").open("r", encoding="utf-8", errors="replace") as fh:  # info: with ( paths . weather_l0 / "Hawaii_State_Weather_Report_current.md" )
            head = fh.read(600)  # info: set head
        m = re.search(r"\*\*Generated:\*\*\s*([^\n]+)", head)  # info: set m
        d["state_generated"] = m.group(1).strip() if m else ""  # info: d [ "state_generated" ] = m . group
    except OSError:  # info: except OSError :
        pass  # info: pass
    return d  # info: return d


# ---------------------------------------------------------------- NPU
# ====================================================
# SECTION: function _listening_ports
# What it does:  listening ports.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _listening_ports() -> set[int]:  # info: def _listening_ports
    ports = set()  # info: set ports
    for f in ("/proc/net/tcp", "/proc/net/tcp6"):  # info: for f in ( "/proc/net/tcp" , "/proc/net/tcp6" )
        try:  # info: try :
            for ln in Path(f).read_text().splitlines()[1:]:  # info: for ln in Path ( f ) .
                parts = ln.split()  # info: set parts
                if len(parts) > 3 and parts[3] == "0A":  # info: if len ( parts ) > 3 and
                    ports.add(int(parts[1].rsplit(":", 1)[1], 16))  # info: ports . add ( int ( parts [
        except OSError:  # info: except OSError :
            pass  # info: pass
    return ports  # info: return ports


# ====================================================
# SECTION: function proc_argvs
# What it does: proc argvs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def proc_argvs() -> list[tuple[int, list[str]]]:  # info: def proc_argvs
    me = {os.getpid(), os.getppid()}  # info: set me
    res = []  # info: set res
    for d in os.listdir("/proc"):  # info: for d in os . listdir ( "/proc"
        if not d.isdigit() or int(d) in me:  # info: if not d . isdigit ( ) or
            continue  # info: continue
        try:  # info: try :
            raw = Path(f"/proc/{d}/cmdline").read_bytes()  # info: set raw
        except OSError:  # info: except OSError :
            continue  # info: continue
        if raw:  # info: if raw :
            res.append((int(d), [a.decode(errors="replace") for a in raw.split(b"\0") if a][:4]))  # info: res . append ( ( int ( d
    return res  # info: return res


# ====================================================
# SECTION: function npu
# What it does: npu.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def npu(paths: Paths, argvs=None, flm_port: int = 52625) -> dict:  # info: def npu
    argvs = argvs if argvs is not None else proc_argvs()  # info: set argvs
    accel = sorted(p.name for p in Path("/dev/accel").glob("*")) if Path("/dev/accel").exists() else []  # info: set accel
    flm = [pid for pid, a in argvs if any(re.search(r"(^|/)flm$", x) for x in a[:1]) and "serve" in a[1:3]]  # info: set flm
    holder_f = paths.plumbing_state / "holder.txt"  # info: set holder_f
    try:  # info: try :
        holder = holder_f.read_text(encoding="utf-8", errors="replace").strip()  # info: set holder
    except OSError:  # info: except OSError :
        holder = ""  # info: set holder
    port_open = flm_port in _listening_ports()  # info: set port_open
    state = "IDLE (on demand) — normal" if not flm and not port_open else f"ACTIVE flm serve pid={flm or 'none'} :{flm_port} {'open' if port_open else 'closed'}"  # info: set state
    return {"accel": accel, "flm_pids": flm, "port_open": port_open, "lock": ("BUSY " + holder) if holder else "IDLE",  # info: return { "accel" : accel , "flm_pids" :
            "state": state}  # info: "state" : state }


# ---------------------------------------------------------------- AI inference log
_ai_cache: dict = {}  # info: set _ai_cache


# ====================================================
# SECTION: function ai_summary
# What it does: ai summary.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ai_summary(paths: Paths) -> dict:  # info: def ai_summary
    p = paths.inference_log  # info: set p
    try:  # info: try :
        st = p.stat()  # info: set st
    except OSError:  # info: except OSError :
        return {"present": False}  # info: return { "present" : False }
    key = (st.st_mtime, st.st_size)  # info: set key
    if _ai_cache.get("key") == key:  # info: if _ai_cache . get ( "key" ) ==
        return _ai_cache["res"]  # info: return _ai_cache [ "res" ]
    rows = []  # info: set rows
    for ln in tail_lines(p, 262144):  # info: for ln in tail_lines ( p , 262144
        try:  # info: try :
            rows.append(json.loads(ln))  # info: rows . append ( json . loads (
        except Exception:  # info: except Exception :
            pass  # info: pass
    today = datetime.now(TZ).date().isoformat()  # info: set today
    routes, models, callers = {}, {}, {}  # info: routes , models , callers = { }
    lat = [r.get("latency_ms") for r in rows if isinstance(r.get("latency_ms"), (int, float))]  # info: set lat
    for r in rows:  # info: for r in rows :
        routes[r.get("route", "?")] = routes.get(r.get("route", "?"), 0) + 1  # info: routes [ r . get ( "route" ,
        models[r.get("model", "?")] = models.get(r.get("model", "?"), 0) + 1  # info: models [ r . get ( "model" ,
        callers[r.get("caller", "?")] = callers.get(r.get("caller", "?"), 0) + 1  # info: callers [ r . get ( "caller" ,
    res = {  # info: set res
        "present": True, "count": len(rows), "today": sum(1 for r in rows if str(r.get("ts", "")).startswith(today)),  # info: "present" : True , "count" : len (
        "routes": routes, "models": models, "callers": callers,  # info: "routes" : routes , "models" : models ,
        "fallbacks": sum(1 for r in rows if r.get("fallback")), "errors": sum(1 for r in rows if r.get("exit_code") not in (0, None)),  # info: "fallbacks" : sum ( 1 for r in
        "lat_avg": (sum(lat) / len(lat)) if lat else None, "lat_max": max(lat) if lat else None,  # info: call "lat_avg"
        "last": rows[-1] if rows else None, "size": st.st_size,  # info: "last" : rows [ - 1 ] if
    }  # info: }
    try:  # info: try :
        res["routing_rows"] = sum(1 for _ in paths.routing_log.open("rb"))  # info: res [ "routing_rows" ] = sum ( 1
    except OSError:  # info: except OSError :
        res["routing_rows"] = None  # info: res [ "routing_rows" ] = None
    try:  # info: try :
        with paths.ai_report.open("r", encoding="utf-8", errors="replace") as fh:  # info: with paths . ai_report . open ( "r"
            res["report_head"] = fh.read(1200)  # info: res [ "report_head" ] = fh . read
    except OSError:  # info: except OSError :
        res["report_head"] = ""  # info: res [ "report_head" ] = ""
    _ai_cache.clear()  # info: _ai_cache . clear ( )
    _ai_cache.update(key=key, res=res)  # info: _ai_cache . update ( key = key ,
    return res  # info: return res


# ---------------------------------------------------------------- services
# ====================================================
# SECTION: function _count
# What it does:  count.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _count(argvs, suffixes) -> int:  # info: def _count
    n = 0  # info: set n
    for _pid, argv in argvs:  # info: for _pid , argv in argvs :
        if any(a.endswith(sfx) for a in argv[:3] for sfx in suffixes if len(a) < 400):  # info: if any ( a . endswith ( sfx
            n += 1  # info: set n
    return n  # info: return n


# ====================================================
# SECTION: function _units_active
# What it does:  units active.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _units_active(units: list[str], user: bool) -> dict:  # info: def _units_active
    if not units:  # info: if not units :
        return {}  # info: return { }
    cmd = ["systemctl"] + (["--user"] if user else []) + ["show", "-p", "Id,ActiveState,MainPID"] + units  # info: set cmd
    try:  # info: try :
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout  # info: set out
    except Exception:  # info: except Exception :
        return {}  # info: return { }
    res, cur = {}, {}  # info: res , cur = { } , {
    for ln in out.splitlines() + [""]:  # info: for ln in out . splitlines ( )
        if not ln.strip():  # info: if not ln . strip ( ) :
            if cur.get("Id"):  # info: if cur . get ( "Id" ) :
                res[cur["Id"]] = cur  # info: res [ cur [ "Id" ] ] =
            cur = {}  # info: set cur
            continue  # info: continue
        k, _, v = ln.partition("=")  # info: k , _ , v = ln .
        cur[k] = v  # info: cur [ k ] = v
    return res  # info: return res


# ====================================================
# SECTION: function services
# What it does: Same PASS/WARN/FAIL rule as poller-dashboard.py service_rows().
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def services(argvs=None) -> list[tuple[str, str, str]]:  # info: def services
    """Same PASS/WARN/FAIL rule as poller-dashboard.py service_rows()."""  # info: """Same PASS/WARN/FAIL rule as poller-dashboard.py service_rows()."""
    argvs = argvs if argvs is not None else proc_argvs()  # info: set argvs
    user = _units_active([u for _l, u, s, _x, _e in SERVICES if u and s == "user"], True)  # info: set user
    sysu = _units_active([u for _l, u, s, _x, _e in SERVICES if u and s == "system"], False)  # info: set sysu
    rows = []  # info: set rows
    for label, unit, scope, sfx, expect in SERVICES:  # info: for label , unit , scope , sfx
        n = _count(argvs, sfx)  # info: set n
        st = None  # info: set st
        pid = ""  # info: set pid
        if unit:  # info: if unit :
            info = (user if scope == "user" else sysu).get(unit) or {}  # info: set info
            st = info.get("ActiveState") or "unknown"  # info: set st
            pid = info.get("MainPID", "")  # info: set pid
        if st not in (None, "active") or n == 0:  # info: if st not in ( None , "active"
            state = "FAIL"  # info: set state
        elif expect is not None and n != expect:  # info: elif expect is not None and n !=
            state = "WARN"  # info: set state
        else:  # info: else :
            state = "PASS"  # info: set state
        detail = (f"unit {st}" if unit else "no unit") + f" · {n} proc" + (f" · MainPID {pid}" if pid not in ("", "0") else "")  # info: set detail
        rows.append((label, state, detail))  # info: rows . append ( ( label , state
    return rows  # info: return rows


# ====================================================
# SECTION: function poller_quick
# What it does: poller quick.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poller_quick(argvs) -> tuple[str, int]:  # info: def poller_quick
    n = _count(argvs, SERVICES[0][3])  # info: set n
    return ("PASS" if n == 1 else "WARN" if n > 1 else "FAIL"), n  # info: return ( "PASS" if n == 1 else


# ====================================================
# SECTION: function gated_jobs
# What it does: (job id, RR_* flag, default) for jobs.py entries whose "enabled" is os.environ.get("RR_..."). Text scan only (no import, no reading any process environment). The real on/off is dec
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def gated_jobs(paths: Paths) -> list[tuple[str, str, str]]:  # info: def gated_jobs
    """(job id, RR_* flag, default) for jobs.py entries whose "enabled" is os.environ.get("RR_...").
    Text scan only (no import, no reading any process environment). The real on/off is decided by the
    poller's environment at poller start; defaults are "0" (OFF)."""
    try:  # info: try :
        text = paths.jobs_py.read_text(encoding="utf-8", errors="replace")  # info: set text
    except OSError:  # info: except OSError :
        return []  # info: return [ ]
    pat = re.compile(r'"id":\s*"([^"]+)",\s*"enabled":\s*os\.environ\.get\("(RR_[A-Z0-9_]+)",\s*"([^"]*)"\)')  # info: set pat
    return [(m.group(1), m.group(2), m.group(3)) for m in pat.finditer(text)]  # info: return [ ( m . group ( 1


# ---------------------------------------------------------------- cameras
# ====================================================
# SECTION: function discover_cameras
# What it does: Channels from grab_all.sh (`for ch in 1 2 3 4`) — never reads store/CONNECTION.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def discover_cameras(paths: Paths) -> list[str]:  # info: def discover_cameras
    """Channels from grab_all.sh (`for ch in 1 2 3 4`) — never reads store/CONNECTION.json."""  # info: """Channels from grab_all.sh (`for ch in 1 2 3 4`) — never reads store/CONNECTION.json."""
    try:  # info: try :
        text = (paths.cameras_dir / "grab_all.sh").read_text(encoding="utf-8", errors="replace")  # info: set text
        m = re.search(r"for\s+ch\s+in\s+([0-9 ]+);", text)  # info: set m
        if m:  # info: if m :
            return [f"ch{n}" for n in m.group(1).split()]  # info: return [ f" ch { n } "
    except OSError:  # info: except OSError :
        pass  # info: pass
    return ["ch1", "ch2", "ch3", "ch4"]  # info: return [ "ch1" , "ch2" , "ch3" ,


# ====================================================
# SECTION: function latest_stills
# What it does: Newest still per camera by file name (chN-YYYYmmddTHHMMSSZ.jpg). Directory listing only; the image file itself is opened by the caller. Skips a file younger than skip_newer_than se
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def latest_stills(paths: Paths, cams: list[str], skip_newer_than: float = 1.5) -> dict:  # info: def latest_stills
    """Newest still per camera by file name (chN-YYYYmmddTHHMMSSZ.jpg). Directory listing only;
    the image file itself is opened by the caller. Skips a file younger than skip_newer_than seconds
    (grab may still be writing it)."""
    STATS["camera_dir_scans"] += 1  # info: STATS [ "camera_dir_scans" ] += 1
    best: dict[str, list[str]] = {c: [] for c in cams}  # info: set best
    try:  # info: try :
        with os.scandir(paths.camera_images) as it:  # info: with os . scandir ( paths . camera_images
            for e in it:  # info: for e in it :
                n = e.name  # info: set n
                if not n.endswith(".jpg"):  # info: if not n . endswith ( ".jpg" )
                    continue  # info: continue
                c = n.split("-", 1)[0]  # info: set c
                if c in best:  # info: if c in best :
                    lst = best[c]  # info: set lst
                    lst.append(n)  # info: lst . append ( n )
                    if len(lst) > 8:  # info: if len ( lst ) > 8 :
                        lst.sort()  # info: lst . sort ( )
                        del lst[:-3]  # info: del lst [ : - 3 ]
    except OSError:  # info: except OSError :
        return {c: None for c in cams}  # info: return { c : None for c in
    now = time.time()  # info: set now
    res = {}  # info: set res
    for c, lst in best.items():  # info: for c , lst in best . items
        res[c] = None  # info: res [ c ] = None
        for n in sorted(lst, reverse=True)[:3]:  # info: for n in sorted ( lst , reverse
            p = paths.camera_images / n  # info: set p
            try:  # info: try :
                if now - p.stat().st_mtime >= skip_newer_than:  # info: if now - p . stat ( )
                    res[c] = p  # info: res [ c ] = p
                    break  # info: break
            except OSError:  # info: except OSError :
                continue  # info: continue
    return res  # info: return res


# ====================================================
# SECTION: function still_time
# What it does: still time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def still_time(p: Path) -> str:  # info: def still_time
    m = re.search(r"-(\d{8}T\d{6}Z)\.jpg$", p.name)  # info: set m
    if not m:  # info: if not m :
        return ""  # info: return ""
    dt = datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)  # info: set dt
    return dt.strftime("%H:%M:%S HST")  # info: return dt . strftime ( "%H:%M:%S HST" )
