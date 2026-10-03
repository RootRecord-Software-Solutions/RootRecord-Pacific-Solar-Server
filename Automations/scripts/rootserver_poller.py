# ==============================================================================
# FILE: Automations/scripts/rootserver_poller.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""RootRecord automations poller — tunnel when online, local jobs always.

Internet gate: TCP check to 1.1.1.1/8.8.8.8 before tunnel/GitHub/Telegram.
If offline at boot, tunnel is deferred; ensure_tunnel_online retries every minute.
BLE / Ollama / HTTP local continue regardless.
"""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import signal  # info: import signal
import socket  # info: import socket
import subprocess  # info: import subprocess
import sys  # info: import sys
import threading  # info: import threading
import time  # info: import time
import json  # info: import json
import urllib.parse  # info: import urllib.parse
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # info: from http . server import BaseHTTPRequestHandler , ThreadingHTTPServer
from pathlib import Path  # info: from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent  # info: set SCRIPTS
REPO_ROOT = SCRIPTS.parent.parent  # repo root (Automations/../)
SKILLS_ROOT = REPO_ROOT  # alias: domain folders live at repo root
sys.path.insert(0, str(SCRIPTS))  # info: sys . path . insert ( 0 ,
sys.path.insert(0, str(REPO_ROOT))  # info: sys . path . insert ( 0 ,
import jobs as jobmod  # noqa: E402
try:  # info: try
    import automation_control as actl  # info: import automation_control as actl
except Exception:  # info: except Exception
    actl = None  # info: set actl
try:  # info: try
    import service_notice as svc  # info: import service_notice as svc
except Exception:  # info: except Exception
    svc = None  # info: set svc

INTERVAL_FALLBACK = float(os.environ.get("POLLER_INTERVAL_SEC", "5"))  # info: set INTERVAL_FALLBACK
HOST = os.environ.get("POLLER_BIND", "127.0.0.1")  # info: set HOST
PORT = int(os.environ.get("POLLER_PORT", "8799"))  # info: set PORT
SYSTEM_STATUS_JSON = Path(os.environ.get("SYSTEM_STATUS_JSON", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/System/status/system-status.json"))  # info: set SYSTEM_STATUS_JSON
ENERGY_ROOT = Path(os.environ.get("ENERGY_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy"))  # info: set ENERGY_ROOT
HOSTNAME = os.environ.get("POLLER_PUBLIC_HOST", "rootserver.rootrecord.cloud")  # info: set HOSTNAME
TOKEN_FILE = Path(os.environ.get("CLOUDFLARED_TOKEN_FILE", str(Path.home() / ".cloudflared" / "rootserver.token")))  # info: set TOKEN_FILE
CLOUDFLARED_BIN = os.environ.get(  # info: set CLOUDFLARED_BIN
    "CLOUDFLARED_BIN",  # info: "CLOUDFLARED_BIN" ,
    str(REPO_ROOT / "Communications" / "network" / "cloudflare" / "bin" / "cloudflared"),  # info: call str
)  # info: )
ENABLE_TUNNEL = os.environ.get("POLLER_ENABLE_TUNNEL", "1") != "0"  # info: set ENABLE_TUNNEL
TUNNEL_READY_TIMEOUT_SEC = float(os.environ.get("POLLER_TUNNEL_READY_TIMEOUT_SEC", "45"))  # info: set TUNNEL_READY_TIMEOUT_SEC
# Read once at process start, same moment as jobs.py. Default off: every enabled job still runs.
NIGHT_SLEEP_GATE = os.environ.get("RR_NIGHT_SLEEP", "0").strip() == "1"  # info: set NIGHT_SLEEP_GATE
# Late boot does not replay these. They run only when the clock reaches their slot.
AI_HOLD = frozenset({  # info: set AI_HOLD
    "ai_processing_report_hourly",  # info: "ai_processing_report_hourly" ,
    "ai_usage_report",  # info: "ai_usage_report" ,
    "cloud_narrative_merged",  # info: "cloud_narrative_merged" ,
    "cloud_narrative_kilauea",  # info: "cloud_narrative_kilauea" ,
    "cursor_fallback",  # info: "cursor_fallback" ,
})  # info: }


# ====================================================
# SECTION: function _load_night_sleep
# What it does: Load System/NightSleep by file path. Fail open if the module is missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_night_sleep():  # info: def _load_night_sleep
    """Load System/NightSleep by file path. Fail open if the module is missing."""  # info: """Load System/NightSleep by file path. Fail open if the module is missing."""
    import importlib.util  # info: import importlib . util

    path = REPO_ROOT / "System" / "NightSleep" / "scripts" / "night_sleep.py"  # info: set path
    spec = importlib.util.spec_from_file_location("NightSleep", path)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader
        return None  # info: return None
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    return mod  # info: return mod


try:  # info: try :
    _night_sleep = _load_night_sleep() if NIGHT_SLEEP_GATE else None  # info: set _night_sleep
except Exception:  # info: except Exception :
    _night_sleep = None  # info: set _night_sleep

_latest = "starting"  # info: set _latest
_lock = threading.Lock()  # info: set _lock
_stop = threading.Event()  # info: set _stop
_power_busy = threading.Lock()  # info: set _power_busy
_service_busy = threading.Lock()  # info: set _service_busy
_github_busy = threading.Lock()  # info: github_sync must not block :35/:36/:55 voice slots
_news_busy = threading.Lock()  # info: news_cycle at :35 — may overlap desks; folds when ready
_hour_batch_busy = threading.Lock()  # info: one generate_hour_reports + radio_push lane
_camera_busy = threading.Lock()  # info: security_camera must not block the hour batch tick
_hour_workflow_done: set[str] = set()  # info: "id|YYYY-MM-DD|HH" — catch-up after a missed exact second
_watchdog_last_minute: int | None = None  # info: hour-batch watchdog fires once per clock minute
_tunnel_ready = threading.Event()  # info: set _tunnel_ready
_tunnel_proc: subprocess.Popen | None = None  # info: set _tunnel_proc
_internet_ok = False  # info: set _internet_ok
_internet_last_log = 0.0  # info: set _internet_last_log
_tunnel_start_attempts = 0  # info: set _tunnel_start_attempts
# Survives poller restarts so :55 radio / :36 voice catch-up do not double-fire after a bounce.
_HOUR_DONE_PATH = Path(  # info: set _HOUR_DONE_PATH
    os.environ.get(  # info: os . environ . get (
        "RR_HOUR_WORKFLOW_DONE",  # info: "RR_HOUR_WORKFLOW_DONE" ,
        "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Automations/hour_workflow_done.json",  # info: default path
    )  # info: )
)  # info: )
# One-script hour lane: news banks at :35, generate_hour_reports at :36, radio_push catch-up at :55.
HOUR_WORKFLOW = frozenset({"news_cycle", "voice_hour_batch", "radio_push_hour"})  # info: set HOUR_WORKFLOW
# Camera / BLE / hawaii must not sit in front of the hour workflow on the same :00 tick.
STACK_DEFER = frozenset(  # info: set STACK_DEFER
    {  # info: {
        "security_camera_frame_grab",  # info: "security_camera_frame_grab" ,
        "delta2_read",  # info: "delta2_read" ,
        "river2pro_read",  # info: "river2pro_read" ,
        "hawaii_to_ml2",  # info: "hawaii_to_ml2" ,
        "geology_kilauea_cams",  # info: long-ish; never ahead of :35/:36
        "energy_consolidate_minutes",  # info: defer while hour lane starts
        "energy_consolidate_hours",  # info: defer while hour lane starts
        "system_consolidate_minutes",  # info: defer while hour lane starts
        "system_consolidate_hours",  # info: defer while hour lane starts
    }  # info: }
)  # info: )
# Real generate_hour_reports argv only — never match shells/sandbox that merely mention the path.
_GEN_HOUR_PS_MARK = "Media/Voice/scripts/generate_hour_reports.py"  # info: set _GEN_HOUR_PS_MARK


# ====================================================
# SECTION: function _load_hour_workflow_done
# What it does: Restore today's hour-workflow done keys from disk (and seed voice_hour_batch from Timing if this hour already finished).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_hour_workflow_done() -> None:  # info: def _load_hour_workflow_done
    global _hour_workflow_done  # info: global _hour_workflow_done
    day = datetime.now().astimezone().date().isoformat()  # info: set day
    keys: set[str] = set()  # info: set keys
    try:  # info: try
        if _HOUR_DONE_PATH.is_file():  # info: if file exists
            doc = json.loads(_HOUR_DONE_PATH.read_text(encoding="utf-8"))  # info: set doc
            raw = doc.get("done") if isinstance(doc, dict) else None  # info: set raw
            if isinstance(raw, list):  # info: if isinstance ( raw , list )
                keys = {str(x) for x in raw if isinstance(x, str) and f"|{day}|" in x}  # info: today only
    except Exception:  # info: except Exception
        keys = set()  # info: set keys
    wall = datetime.now().astimezone()  # info: set wall
    # Seed voice/radio done when Timing shows a successful batch already this clock hour.
    try:  # info: try
        sched = Path(  # info: set sched
            "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/Timing/hour_batch_schedule.json"  # info: path
        )  # info: )
        if sched.is_file():  # info: if sched . is_file ( )
            doc = json.loads(sched.read_text(encoding="utf-8"))  # info: set doc
            at = str(doc.get("at") or "")  # info: set at
            if at and doc.get("job_id") == "voice_hour_batch":  # info: if this hour's batch stamp
                stamp = datetime.fromisoformat(at)  # info: set stamp
                if stamp.tzinfo is None:  # info: if stamp . tzinfo is None
                    stamp = stamp.astimezone()  # info: set stamp
                # A late finish just after :00 belongs to the previous hour, not this one.
                if (  # info: if
                    stamp.date() == wall.date()  # info: stamp . date ( ) == wall . date ( )
                    and stamp.hour == wall.hour  # info: and stamp . hour == wall . hour
                    and stamp.minute >= 36  # info: and stamp . minute >= 36
                ):  # info: )
                    keys.add(f"voice_hour_batch|{day}|{wall.hour:02d}")  # info: keys . add
                    keys.add(f"radio_push_hour|{day}|{wall.hour:02d}")  # info: early push already covered :55
    except Exception:  # info: except Exception
        pass  # info: pass
    # Seed news done when this hour already banked a fresh news_update WAV.
    try:  # info: try
        news = Path(  # info: set news
            "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/news_update_current.wav"  # info: path
        )  # info: )
        if news.is_file() and news.stat().st_size > 64:  # info: if news present
            mtime = datetime.fromtimestamp(news.stat().st_mtime).astimezone()  # info: set mtime
            gate = wall.replace(minute=35, second=0, microsecond=0)  # info: set gate
            if wall < gate:  # info: before this hour's :35 — the cycle started last hour
                gate = gate - timedelta(hours=1)  # info: set gate
            if mtime >= gate and (wall - mtime) <= timedelta(hours=2):  # info: this cycle's wav
                keys.add(f"news_cycle|{day}|{wall.hour:02d}")  # info: keys . add
    except Exception:  # info: except Exception
        pass  # info: pass
    _hour_workflow_done = keys  # info: set _hour_workflow_done
    if keys:  # info: if keys
        log(f"{full_timestamp()}hour-lane  restored done={len(keys)}")  # info: call log


# ====================================================
# SECTION: function _save_hour_workflow_done
# What it does: Persist today's hour-workflow done keys so a poller restart does not re-run catch-up.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save_hour_workflow_done() -> None:  # info: def _save_hour_workflow_done
    try:  # info: try
        day = datetime.now().astimezone().date().isoformat()  # info: set day
        keys = sorted(k for k in _hour_workflow_done if k.split("|")[1] == day)  # info: set keys
        _HOUR_DONE_PATH.parent.mkdir(parents=True, exist_ok=True)  # info: ensure dir
        tmp = _HOUR_DONE_PATH.with_suffix(".tmp")  # info: set tmp
        tmp.write_text(json.dumps({"at": datetime.now().astimezone().isoformat(), "done": keys}, indent=2) + "\n", encoding="utf-8")  # info: write tmp
        os.replace(tmp, _HOUR_DONE_PATH)  # info: atomic replace
    except Exception:  # info: except Exception
        pass  # info: pass


# ====================================================
# SECTION: function _mark_hour_workflow_done
# What it does: Record one hour-workflow job as done for this clock hour (memory + disk).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _mark_hour_workflow_done(key: str) -> None:  # info: def _mark_hour_workflow_done
    if not key:  # info: if not key
        return  # info: return
    _hour_workflow_done.add(key)  # info: _hour_workflow_done . add ( key )
    _save_hour_workflow_done()  # info: call _save_hour_workflow_done


# ====================================================
# SECTION: function _generate_hour_reports_running
# What it does: True only when a live python3 process is running generate_hour_reports.py (not bash/sandbox cmdlines that quote the path).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _generate_hour_reports_running() -> bool:  # info: def _generate_hour_reports_running
    try:  # info: try
        proc = subprocess.run(  # info: set proc
            ["ps", "-eo", "pid=,args="],  # info: pid + full args; avoid pgrep -f false positives
            capture_output=True,  # info: capture_output = True
            text=True,  # info: text = True
            timeout=2,  # info: timeout = 2
        )  # info: )
    except Exception:  # info: except Exception
        return False  # info: return False
    for raw in (proc.stdout or "").splitlines():  # info: for raw in lines
        line = raw.strip()  # info: set line
        if _GEN_HOUR_PS_MARK not in line and "generate_hour_reports.py" not in line:  # info: if path not in line
            continue  # info: continue
        # Drop shells / Cursor sandbox / our own probes that only mention the script.
        low = line.lower()  # info: set low
        if "cursorsandbox" in low or "/bin/bash" in low or low.startswith("bash "):  # info: if wrapper shell
            continue  # info: continue
        if "pgrep" in low or " rg " in f" {low} " or low.startswith("rg "):  # info: if probe tools
            continue  # info: continue
        # argv0 must be a python interpreter (nice already replaced itself).
        parts = line.split(None, 1)  # info: set parts
        if len(parts) < 2:  # info: if len ( parts ) < 2
            continue  # info: continue
        args = parts[1]  # info: set args
        head = args.split(None, 1)[0]  # info: set head
        base = Path(head).name  # info: set base
        if not base.startswith("python"):  # info: if not a python binary
            continue  # info: continue
        if "generate_hour_reports.py" in args:  # info: if script is an arg of that python
            return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function full_timestamp
# What it does: full timestamp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def full_timestamp() -> str:  # info: def full_timestamp
    return datetime.now().astimezone().isoformat(timespec="seconds")  # info: return datetime . now ( ) . astimezone


# ====================================================
# SECTION: function log
# What it does: log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log(msg: str) -> None:  # info: def log
    print(msg, flush=True)  # info: call print


# ====================================================
# SECTION: function heartbeat_line
# What it does: heartbeat line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def heartbeat_line() -> str:  # info: def heartbeat_line
    try:  # info: try :
        return f"{full_timestamp()}{_energy_log_line()}"  # info: return f" { full_timestamp ( ) } {
    except Exception:  # info: except Exception :
        return f"{full_timestamp()}Poller is online."  # info: return f" { full_timestamp ( ) } Poller is online.


# ====================================================
# SECTION: function internet_ok
# What it does: TCP reachability — does not use local DNS stub.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def internet_ok(force: bool = False) -> bool:  # info: def internet_ok
    """TCP reachability — does not use local DNS stub."""  # info: """TCP reachability — does not use local DNS stub."""
    global _internet_ok  # info: global _internet_ok
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53), ("1.0.0.1", 443)):  # info: for host , port in ( ( "1.1.1.1"
        try:  # info: try :
            with socket.create_connection((host, port), timeout=2.5):  # info: with socket . create_connection ( ( host ,
                _internet_ok = True  # info: set _internet_ok
                return True  # info: return True
        except OSError:  # info: except OSError :
            continue  # info: continue
    _internet_ok = False  # info: set _internet_ok
    return False  # info: return False


# ====================================================
# SECTION: function tunnel_alive
# What it does: tunnel alive.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tunnel_alive() -> bool:  # info: def tunnel_alive
    return _tunnel_proc is not None and _tunnel_proc.poll() is None  # info: return _tunnel_proc is not None and _tunnel_proc .


# ====================================================
# SECTION: function ensure_tunnel_online
# What it does: ensure tunnel online.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_tunnel_online() -> None:  # info: def ensure_tunnel_online
    global _tunnel_start_attempts, _internet_last_log  # info: global _tunnel_start_attempts , _internet_last_log
    if not ENABLE_TUNNEL:  # info: if not ENABLE_TUNNEL :
        return  # info: return
    if internet_ok(force=True):  # info: if internet_ok ( force = True ) :
        if tunnel_alive():  # info: if tunnel_alive ( ) :
            return  # info: return
        _tunnel_start_attempts += 1  # info: set _tunnel_start_attempts
        log(f"{full_timestamp()}internet OK — starting Cloudflare tunnel (attempt {_tunnel_start_attempts})")  # info: call log
        _tunnel_ready.clear()  # info: _tunnel_ready . clear ( )
        if start_tunnel():  # info: if start_tunnel ( ) :
            wait_for_tunnel_ready()  # info: call wait_for_tunnel_ready
        return  # info: return
    now = time.time()  # info: set now
    if now - _internet_last_log >= 55:  # info: if now - _internet_last_log >= 55 :
        log(f"{full_timestamp()}internet DOWN — net services waiting (retry ~60s)")  # info: call log
        _internet_last_log = now  # info: set _internet_last_log


# ====================================================
# SECTION: function _read_energy_json
# What it does:  read energy json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_energy_json(rel: str):  # info: def _read_energy_json
    try:  # info: try :
        return json.loads((ENERGY_ROOT / rel).read_text(encoding="utf-8"))  # info: return json . loads ( ( ENERGY_ROOT /
    except (OSError, json.JSONDecodeError, TypeError):  # info: except ( OSError , json . JSONDecodeError ,
        return None  # info: return None


# ====================================================
# SECTION: function _fmt_w
# What it does:  fmt w.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fmt_w(n) -> str:  # info: def _fmt_w
    if not isinstance(n, (int, float)):  # info: if not isinstance ( n , ( int
        return "No data"  # info: return "No data"
    if float(n) == int(n):  # info: if float ( n ) == int (
        return f"{int(n)} W"  # info: return f" { int ( n ) }
    return f"{n:.1f} W"  # info: return f" { n : .1f } W


# ====================================================
# SECTION: function _fmt_soc
# What it does:  fmt soc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fmt_soc(n) -> str:  # info: def _fmt_soc
    if not isinstance(n, (int, float)):  # info: if not isinstance ( n , ( int
        return "No data"  # info: return "No data"
    if float(n) == int(n):  # info: if float ( n ) == int (
        return f"{int(n)}%"  # info: return f" { int ( n ) }
    return f"{n:.1f}%"  # info: return f" { n : .1f } %


# ====================================================
# SECTION: function _discharged_off
# What it does: True when the last SOC is 5 percent or less and the file is older than 30 minutes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _discharged_off(blob) -> bool:  # info: def _discharged_off
    if not isinstance(blob, dict):  # info: if not isinstance ( blob , dict ) :
        return False  # info: return False
    try:  # info: try :
        soc = float(blob.get("soc"))  # info: set soc
        age_min = (datetime.now().astimezone() - datetime.fromisoformat(blob["at"])).total_seconds() / 60  # info: set age_min
    except (TypeError, ValueError, KeyError):  # info: except ( TypeError , ValueError , KeyError ) :
        return False  # info: return False
    return soc <= 5 and age_min > 30  # info: return soc <= 5 and age_min > 30


# ====================================================
# SECTION: function _sqlite_board
# What it does:  sqlite board.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sqlite_board() -> dict | None:  # info: def _sqlite_board
    try:  # info: try :
        from energy.db.latest import board_snapshot  # info: from energy . db . latest import board_snapshot
        return board_snapshot()  # info: return board_snapshot ( )
    except Exception:  # info: except Exception :
        return None  # info: return None


# ====================================================
# SECTION: function build_energy_snapshot
# What it does: build energy snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_energy_snapshot() -> dict:  # info: def build_energy_snapshot
    sqlite = _sqlite_board()  # info: set sqlite
    delta_sql = (sqlite or {}).get("delta2") if isinstance(sqlite, dict) else None  # info: set delta_sql
    river_sql = (sqlite or {}).get("river2pro") if isinstance(sqlite, dict) else None  # info: set river_sql
    delta_soc = _read_energy_json("soc/delta2_current.json")  # info: set delta_soc
    river_soc = _read_energy_json("soc/river2pro_current.json")  # info: set river_soc
    delta_w = _read_energy_json("watts/delta2_current.json")  # info: set delta_w
    river_w = _read_energy_json("watts/river2pro_current.json")  # info: set river_w

    def soc_of(sql_row, json_blob):  # info: def soc_of
        if isinstance(sql_row, dict) and sql_row.get("soc") is not None:  # info: if isinstance ( sql_row , dict ) and
            return sql_row["soc"]  # info: return sql_row [ "soc" ]
        if isinstance(json_blob, dict) and json_blob.get("soc") is not None:  # info: if isinstance ( json_blob , dict ) and
            return json_blob["soc"]  # info: return json_blob [ "soc" ]
        return None  # info: return None

    def watt_of(sql_row, key, json_blob):  # info: def watt_of
        if isinstance(sql_row, dict) and sql_row.get(key) is not None:  # info: if isinstance ( sql_row , dict ) and
            return sql_row[key]  # info: return sql_row [ key ]
        if isinstance(json_blob, dict) and json_blob.get(key) is not None:  # info: if isinstance ( json_blob , dict ) and
            return json_blob[key]  # info: return json_blob [ key ]
        return None  # info: return None

    d_soc = soc_of(delta_sql, delta_soc)  # info: set d_soc
    r_soc = soc_of(river_sql, river_soc)  # info: set r_soc
    d_solar = watt_of(delta_sql, "solar_input_power", delta_w)  # info: set d_solar
    r_solar = watt_of(river_sql, "solar_input_power", river_w)  # info: set r_solar
    solar = None if d_solar is None and r_solar is None else (d_solar or 0) + (r_solar or 0)  # info: set solar
    ac = watt_of(delta_sql, "ac_output_power", delta_w)  # info: set ac
    if ac is None:  # info: if ac is None :
        ac = watt_of(river_sql, "ac_output_power", river_w)  # info: set ac
    usbc = watt_of(delta_sql, "usbc_output_power", delta_w)  # info: set usbc
    if usbc is None:  # info: if usbc is None :
        usbc = watt_of(river_sql, "usbc_output_power", river_w)  # info: set usbc
    has_delta = d_soc is not None or isinstance(delta_sql, dict) or bool(delta_soc or delta_w)  # info: set has_delta
    has_river = r_soc is not None or isinstance(river_sql, dict) or bool(river_soc or river_w)  # info: set has_river
    live = has_delta or has_river  # info: set live
    ats = []  # info: set ats
    for row in (delta_sql, river_sql):  # info: for row in ( delta_sql , river_sql )
        if isinstance(row, dict) and row.get("observed_at"):  # info: if isinstance ( row , dict ) and
            ats.append(row["observed_at"])  # info: ats . append ( row [ "observed_at" ]
    for blob in (delta_soc, river_soc, delta_w, river_w):  # info: for blob in ( delta_soc , river_soc ,
        if isinstance(blob, dict) and blob.get("at"):  # info: if isinstance ( blob , dict ) and
            ats.append(blob["at"])  # info: ats . append ( blob [ "at" ]
    updated = sorted(ats)[-1] if ats else None  # info: set updated
    source = "sqlite" if (delta_sql or river_sql) else str(ENERGY_ROOT)  # info: set source
    b3 = None  # info: set b3
    if isinstance(delta_sql, dict):  # info: if isinstance ( delta_sql , dict ) :
        for exp in delta_sql.get("expansions") or []:  # info: for exp in delta_sql . get ( "expansions"
            if exp.get("soc") is not None or exp.get("sn"):  # info: if exp . get ( "soc" ) is
                b3 = {"sn": exp.get("sn"), "slot": exp.get("slot"),  # info: set b3
                      "soc": _fmt_soc(exp.get("soc")) if exp.get("soc") is not None else "No data"}  # info: "soc" : _fmt_soc ( exp . get (
                break  # info: break
    return {  # info: return {
        "status": "live" if live else "Waiting",  # info: "status" : "live" if live else "Waiting" ,
        "solarInW": _fmt_w(solar) if live else "No data",  # info: "solarInW" : _fmt_w ( solar ) if live
        "deltaSoc": _fmt_soc(d_soc) if d_soc is not None else ("No data" if not has_delta else "Waiting"),  # info: "deltaSoc" : _fmt_soc ( d_soc ) if d_soc
        "riverSoc": _fmt_soc(r_soc) if r_soc is not None else ("Waiting" if not has_river else "No data"),  # info: "riverSoc" : _fmt_soc ( r_soc ) if r_soc
        "acOut": _fmt_w(ac) if ac is not None else ("Waiting" if live else "No data"),  # info: "acOut" : _fmt_w ( ac ) if ac
        "usbC": _fmt_w(usbc) if usbc is not None else ("No data" if live else "No data"),  # info: "usbC" : _fmt_w ( usbc ) if usbc
        "b3": b3, "buckets": "Waiting",  # info: "b3" : b3 , "buckets" : "Waiting" ,
        "ports": {"ac": _fmt_w(ac) if ac is not None else "Waiting", "usbc": _fmt_w(usbc) if usbc is not None else "No data"},  # info: "ports" : { "ac" : _fmt_w ( ac
        "source": source,  # info: "source" : source ,
        "files": {"present": {  # info: "files" : { "present" : {
            "delta2Soc": d_soc is not None or bool(delta_soc),  # info: "delta2Soc" : d_soc is not None or bool
            "river2proSoc": r_soc is not None or bool(river_soc),  # info: "river2proSoc" : r_soc is not None or bool
            "delta2Watts": bool(delta_w) or (isinstance(delta_sql, dict) and delta_sql.get("ac_output_power") is not None),  # info: "delta2Watts" : bool ( delta_w ) or (
            "river2proWatts": bool(river_w) or (isinstance(river_sql, dict) and river_sql.get("ac_output_power") is not None),  # info: "river2proWatts" : bool ( river_w ) or (
            "sqlite": bool(delta_sql or river_sql),  # info: "sqlite" : bool ( delta_sql or river_sql )
        }},  # info: } } ,
        "updated": updated,  # info: "updated" : updated ,
        "note": "Measured samples. SQLite canonical; JSON compatibility.",  # info: "note" : "Measured samples. SQLite canonical; JSON compatibility." ,
    }  # info: }


# ====================================================
# SECTION: function _energy_log_line
# What it does:  energy log line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _energy_log_line() -> str:  # info: def _energy_log_line
    snap = build_energy_snapshot()  # info: set snap
    delta_off = _discharged_off(_read_energy_json("soc/delta2_current.json"))  # info: set delta_off
    river_off = _discharged_off(_read_energy_json("soc/river2pro_current.json"))  # info: set river_off
    status = "powered_off" if delta_off and river_off else snap.get("status")  # info: set status
    parts = [f"status={status}", f"B2={'off' if delta_off else snap.get('deltaSoc')}", f"B1={'off' if river_off else snap.get('riverSoc')}",  # info: set parts
             f"solar={snap.get('solarInW')}", f"ac={snap.get('acOut')}", f"usbc={snap.get('usbC')}", f"src={snap.get('source')}"]  # info: f" solar= { snap . get ( 'solarInW'
    b3 = snap.get("b3")  # info: set b3
    if isinstance(b3, dict):  # info: if isinstance ( b3 , dict ) :
        parts.insert(3, f"B3={b3.get('soc')}")  # info: parts . insert ( 3 , f" B3=
    lap = _laptop_battery()  # read-only sysfs, 2026-09-29
    if lap:  # info: if lap :
        parts.append(f"LAP={lap}")  # info: parts . append ( f" LAP= { lap
    return "ENERGY  " + "  ".join(parts)  # info: return "ENERGY " + " " . join ( parts


# ====================================================
# SECTION: function _laptop_battery
# What it does: '100%/Full/AC' from /sys/class/power_supply (read-only); '' if no battery.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _laptop_battery() -> str:  # info: def _laptop_battery
    """'100%/Full/AC' from /sys/class/power_supply (read-only); '' if no battery."""  # info: """'100%/Full/AC' from /sys/class/power_supply (read-only); '' if no battery."""
    try:  # info: try :
        ps = Path("/sys/class/power_supply")  # info: set ps
        bat = next((b for b in sorted(ps.glob("BAT*")) if (b / "capacity").exists()), None)  # info: set bat
        if bat is None:  # info: if bat is None :
            return ""  # info: return ""
        ac = any((m / "online").read_text().strip() == "1" for m in ps.iterdir()  # info: set ac
                 if (m / "type").exists() and (m / "type").read_text().strip() == "Mains" and (m / "online").exists())  # info: if ( m / "type" ) . exists
        return f"{(bat / 'capacity').read_text().strip()}%/{(bat / 'status').read_text().strip()}/{'AC' if ac else 'batt'}"  # info: return f" { ( bat / 'capacity' )
    except Exception:  # info: except Exception :
        return ""  # info: return ""


# ====================================================
# SECTION: class Handler
# What it does: Handler.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Handler(BaseHTTPRequestHandler):  # info: class Handler
    def log_message(self, fmt: str, *args) -> None:  # info: def log_message
        return  # info: return
    def _send(self, code: int, body: str, ctype: str = "text/plain; charset=utf-8") -> None:  # info: def _send
        data = body.encode("utf-8")  # info: set data
        self.send_response(code)  # info: self . send_response ( code )
        self.send_header("Content-Type", ctype)  # info: self . send_header ( "Content-Type" , ctype )
        self.send_header("Content-Length", str(len(data)))  # info: self . send_header ( "Content-Length" , str (
        self.send_header("Cache-Control", "no-store")  # info: self . send_header ( "Cache-Control" , "no-store" )
        self.end_headers()  # info: self . end_headers ( )
        self.wfile.write(data)  # info: self . wfile . write ( data )

    def _proxy_aeyes(self) -> None:  # info: def _proxy_aeyes
        """Reverse-proxy /aeyes* to local a-eyes cam server (127.0.0.1:8791). Streams MJPEG; does not buffer the whole body."""  # info: docstring
        import urllib.error  # info: import urllib . error
        import urllib.request  # info: import urllib . request
        target = f"http://127.0.0.1:8791{self.path}"  # info: set target
        headers = {}  # info: set headers
        if self.headers.get("Cookie"):  # info: if self . headers . get ( "Cookie"
            headers["Cookie"] = self.headers.get("Cookie")  # info: headers [ "Cookie" ] = self . headers
        if self.headers.get("Content-Type"):  # info: if self . headers . get ( "Content-Type"
            headers["Content-Type"] = self.headers.get("Content-Type")  # info: headers [ "Content-Type" ] = self . headers
        body = None  # info: set body
        if self.command == "POST":  # info: if self . command == "POST" :
            length = int(self.headers.get("Content-Length") or 0)  # info: set length
            body = self.rfile.read(length) if length > 0 else b""  # info: set body
        # Live MJPEG never ends; stills/HTML finish quickly. Long timeout only for open.
        stream = ".mjpeg" in (self.path or "")  # info: set stream
        timeout = 300 if stream else 45  # info: set timeout
        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)  # info: set req
        try:  # info: try :
            resp = urllib.request.urlopen(req, timeout=timeout)  # info: set resp
            try:  # info: try :
                self.send_response(resp.status)  # info: self . send_response ( resp . status )
                ctype = resp.headers.get("Content-Type") or ""  # info: set ctype
                for key in ("Content-Type", "Set-Cookie", "Location", "Cache-Control", "Pragma", "Connection"):  # info: for key in
                    val = resp.headers.get(key)  # info: set val
                    if val:  # info: if val :
                        self.send_header(key, val)  # info: self . send_header ( key , val )
                # Multipart live streams have no finite length — do not buffer or set Content-Length.
                if stream or "multipart/" in ctype:  # info: if stream or "multipart/" in ctype :
                    self.end_headers()  # info: self . end_headers ( )
                    while True:  # info: while True :
                        chunk = resp.read(8192)  # info: set chunk
                        if not chunk:  # info: if not chunk :
                            break  # info: break
                        self.wfile.write(chunk)  # info: self . wfile . write ( chunk )
                        self.wfile.flush()  # info: self . wfile . flush ( )
                else:  # info: else :
                    data = resp.read()  # info: set data
                    self.send_header("Content-Length", str(len(data)))  # info: self . send_header ( "Content-Length" , str (
                    self.end_headers()  # info: self . end_headers ( )
                    self.wfile.write(data)  # info: self . wfile . write ( data )
            finally:  # info: finally :
                try:  # info: try :
                    resp.close()  # info: resp . close ( )
                except Exception:  # info: except Exception :
                    pass  # info: pass
        except (BrokenPipeError, ConnectionResetError):  # info: except ( BrokenPipeError , ConnectionResetError ) :
            pass  # client closed the live tab
        except urllib.error.HTTPError as e:  # info: except urllib . error . HTTPError as e
            data = e.read()  # info: set data
            self.send_response(e.code)  # info: self . send_response ( e . code )
            ctype = e.headers.get("Content-Type") if e.headers else None  # info: set ctype
            if ctype:  # info: if ctype :
                self.send_header("Content-Type", ctype)  # info: self . send_header ( "Content-Type" , ctype )
            for key in ("Set-Cookie", "Location"):  # info: for key in ( "Set-Cookie" , "Location" )
                val = e.headers.get(key) if e.headers else None  # info: set val
                if val:  # info: if val :
                    self.send_header(key, val)  # info: self . send_header ( key , val )
            self.send_header("Content-Length", str(len(data)))  # info: self . send_header ( "Content-Length" , str (
            self.end_headers()  # info: self . end_headers ( )
            self.wfile.write(data)  # info: self . wfile . write ( data )
        except Exception as e:  # info: except Exception as e :
            self._send(502, f"a-eyes proxy error: {type(e).__name__}\n")  # info: self . _send ( 502 , f" a-eyes proxy error:

    def do_GET(self) -> None:  # info: def do_GET
        if self.path.startswith("/aeyes"):  # info: if self . path . startswith ( "/aeyes"
            self._proxy_aeyes()  # info: self . _proxy_aeyes ( )
            return  # info: return
        with _lock:  # info: with _lock :
            line = _latest  # info: set line
        if self.path in ("/", "/health", "/poller"):  # info: if self . path in ( "/" ,
            self._send(200, line + "\n"); return  # info: self . _send ( 200 , line +
        if self.path == "/json":  # info: if self . path == "/json" :
            self._send(200, json.dumps({"ok": True, "host": HOSTNAME, "line": line}) + "\n", "application/json; charset=utf-8"); return  # info: self . _send ( 200 , json .
        if self.path in ("/energy", "/energy/", "/api/energy"):  # info: if self . path in ( "/energy" ,
            self._send(200, json.dumps(build_energy_snapshot()) + "\n", "application/json; charset=utf-8"); return  # info: self . _send ( 200 , json .
        if self.path in ("/system-status.json", "/system-status", "/api/system-status"):  # info: if self . path in ( "/system-status.json" ,
            try:  # info: try :
                body = SYSTEM_STATUS_JSON.read_text(encoding="utf-8")  # info: set body
                self._send(200, body if body.endswith("\n") else body + "\n", "application/json; charset=utf-8")  # info: self . _send ( 200 , body if
            except FileNotFoundError:  # info: except FileNotFoundError :
                self._send(503, json.dumps({"ok": False, "error": "system-status not ready"}) + "\n", "application/json; charset=utf-8")  # info: self . _send ( 503 , json .
            except Exception as e:  # info: except Exception as e :
                self._send(500, json.dumps({"ok": False, "error": type(e).__name__}) + "\n", "application/json; charset=utf-8")  # info: self . _send ( 500 , json .
            return  # info: return
        if self.path in ("/api/ops/mobile-dashboard", "/api/ops/mobile-dashboard/"):  # info: if self . path in ( "/api/ops/mobile-dashboard" ,
            try:  # info: try :
                import root_ops_board  # info: import root_ops_board
                payload = json.dumps(root_ops_board.build_board())  # info: set payload
                self._send(200, payload + "\n", "application/json; charset=utf-8")  # info: self . _send ( 200 , payload +
            except Exception as e:  # info: except Exception as e :
                self._send(500, json.dumps({"ok": False, "error": type(e).__name__}) + "\n", "application/json; charset=utf-8")  # info: self . _send ( 500 , json .
            return  # info: return
        parsed = urllib.parse.urlparse(self.path)  # info: set parsed
        if parsed.path == "/api/reports" or parsed.path.startswith("/api/reports/"):  # info: if reports api
            self._send_reports(parsed)  # info: self . _send_reports ( parsed )
            return  # info: return
        self._send(404, "not found\n")  # info: self . _send ( 404 , "not found\n" )


# ====================================================
# SECTION: function _send_reports
# What it does: Answer GET /api/reports from canonical JSON. It does not generate a report.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
    def _send_reports(self, parsed) -> None:  # info: def _send_reports
        folder = str(REPO_ROOT / "Reports" / "pipeline")  # info: set folder
        if folder not in sys.path:  # info: if folder not in sys . path
            sys.path.insert(0, folder)  # info: sys . path . insert
        try:  # info: try
            import store as report_store  # info: import store as report_store
            query = urllib.parse.parse_qs(parsed.query)  # info: set query
            parts = [part for part in parsed.path.split("/") if part]  # info: set parts
            if len(parts) == 2:  # info: if list
                rows = report_store.list_reports(  # info: set rows
                    topic=(query.get("topic") or [""])[0],  # info: topic
                    scope=(query.get("scope") or query.get("region") or [""])[0],  # info: scope
                    status=(query.get("status") or [""])[0],  # info: status
                    date=(query.get("date") or query.get("window") or [""])[0],  # info: date
                )  # info: )
                body = json.dumps({"ok": True, "reports": rows})  # info: set body
            else:  # info: else
                report = report_store.load(parts[2]) if len(parts) >= 3 else None  # info: set report
                if report is None:  # info: if report is None
                    self._send(404, json.dumps({"ok": False, "error": "not_found"}) + "\n", "application/json; charset=utf-8")  # info: self . _send 404
                    return  # info: return
                if len(parts) >= 4 and parts[3] == "assets":  # info: if assets
                    body = json.dumps({"ok": True, "report_id": report["report_id"], "assets": report.get("assets") or []})  # info: set body
                else:  # info: else
                    body = json.dumps({"ok": True, "report": report})  # info: set body
            self._send(200, body + "\n", "application/json; charset=utf-8")  # info: self . _send 200
        except Exception as exc:  # info: except Exception as exc
            self._send(500, json.dumps({"ok": False, "error": type(exc).__name__}) + "\n", "application/json; charset=utf-8")  # info: self . _send 500


    def do_POST(self) -> None:  # info: def do_POST
        if self.path.startswith("/aeyes"):  # info: if self . path . startswith ( "/aeyes"
            self._proxy_aeyes()  # info: self . _proxy_aeyes ( )
            return  # info: return
        self._send(404, "not found\n")  # info: self . _send ( 404 , "not found\n" )


# ====================================================
# SECTION: function _cloudflared_interesting
# What it does:  cloudflared interesting.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cloudflared_interesting(text: str) -> str | None:  # info: def _cloudflared_interesting
    t = text.strip()  # info: set t
    if not t:  # info: if not t :
        return None  # info: return None
    drop_sub = ("CONNECTIVITY PRE-CHECKS", "precheck ", "SUMMARY:", "DNS Resolution", "UDP Connectivity",  # info: set drop_sub
                "TCP Connectivity", "Cloudflare API", "curve preferences", "ICMP proxy", "Generated Connector",  # info: "TCP Connectivity" , "Cloudflare API" , "curve preferences" , "ICMP proxy" ,
                "Initial protocol", "Starting metrics", "Version ", "GOOS:", "Settings: map", "Environmental variables",  # info: "Initial protocol" , "Starting metrics" , "Version " , "GOOS:" ,
                "Autoupdate frequency", "Metrics server")  # info: "Autoupdate frequency" , "Metrics server" )
    if any(s in t for s in drop_sub) or t.startswith("|") or t.startswith("+--"):  # info: if any ( s in t for s
        return None  # info: return None
    low = t.lower()  # info: set low
    if " err " in f" {low} " or t.startswith("ERR") or "error=" in low:  # info: if " err " in f" { low }
        if "timeout" in low:  # info: if "timeout" in low :
            return "tunnel timeout — reconnecting"  # info: return "tunnel timeout — reconnecting"
        if "terminated" in low:  # info: if "terminated" in low :
            return "tunnel connection terminated"  # info: return "tunnel connection terminated"
        if "lookup" in low or "dns" in low or "srv" in low or "argotunnel" in low:  # info: if "lookup" in low or "dns" in low
            return "tunnel DNS/edge discovery failed — check internet + resolver (try 1.1.1.1)"  # info: return "tunnel DNS/edge discovery failed — check internet + resolver (try 1.1.1.1)"
        return f"cloudflared ERR: {t[:120]}"  # info: return f" cloudflared ERR: { t [ : 120
    if t.startswith("WRN") or " WRN " in f" {t} ":  # info: if t . startswith ( "WRN" ) or
        if "timeout" in low:  # info: if "timeout" in low :
            return "tunnel timeout — reconnecting"  # info: return "tunnel timeout — reconnecting"
        return f"cloudflared WRN: {t[:120]}"  # info: return f" cloudflared WRN: { t [ : 120
    if "Registered tunnel connection" in t:  # info: if "Registered tunnel connection" in t :
        idx = loc = ""  # info: set idx
        for part in t.split():  # info: for part in t . split ( )
            if part.startswith("connIndex="):  # info: if part . startswith ( "connIndex=" ) :
                idx = part.split("=", 1)[1]  # info: set idx
            if part.startswith("location="):  # info: if part . startswith ( "location=" ) :
                loc = part.split("=", 1)[1]  # info: set loc
        return f"tunnel connected  conn={idx or '?'}  edge={loc or '?'}"  # info: return f" tunnel connected conn= { idx or '?' }
    if "Starting tunnel" in t:  # info: if "Starting tunnel" in t :
        return "tunnel starting"  # info: return "tunnel starting"
    if "Updated to new configuration" in t:  # info: if "Updated to new configuration" in t :
        if "rootserver.rootrecord.cloud" in t:  # info: if "rootserver.rootrecord.cloud" in t :
            return "tunnel ingress  rootserver.rootrecord.cloud → 127.0.0.1:8799"  # info: return "tunnel ingress rootserver.rootrecord.cloud → 127.0.0.1:8799"
        return "tunnel ingress  updated"  # info: return "tunnel ingress updated"
    if "Connected to Cloudflare" in t:  # info: if "Connected to Cloudflare" in t :
        return "tunnel connected to Cloudflare"  # info: return "tunnel connected to Cloudflare"
    return None  # info: return None


# ====================================================
# SECTION: function start_tunnel
# What it does: start tunnel.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def start_tunnel() -> bool:  # info: def start_tunnel
    global _tunnel_proc  # info: global _tunnel_proc
    if not ENABLE_TUNNEL:  # info: if not ENABLE_TUNNEL :
        log(f"{full_timestamp()}Tunnel disabled (POLLER_ENABLE_TUNNEL=0).")  # info: call log
        _tunnel_ready.set()  # info: _tunnel_ready . set ( )
        return False  # info: return False
    if not Path(CLOUDFLARED_BIN).is_file():  # info: if not Path ( CLOUDFLARED_BIN ) . is_file
        log(f"{full_timestamp()}Tunnel DOWN — cloudflared missing at {CLOUDFLARED_BIN}")  # info: call log
        return False  # info: return False
    if not TOKEN_FILE.is_file():  # info: if not TOKEN_FILE . is_file ( ) :
        log(f"{full_timestamp()}Tunnel DOWN — token file missing: {TOKEN_FILE}")  # info: call log
        return False  # info: return False
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()  # info: set token
    if not token:  # info: if not token :
        log(f"{full_timestamp()}Tunnel DOWN — empty token file")  # info: call log
        return False  # info: return False
    mode = os.environ.get("POLLER_TUNNEL_MODE", "token").lower()  # info: set mode
    if mode == "quick":  # info: if mode == "quick" :
        cmd = [CLOUDFLARED_BIN, "tunnel", "--no-autoupdate", "--url", f"http://{HOST}:{PORT}"]  # info: set cmd
        popen_kwargs: dict = {}  # info: set popen_kwargs
    else:  # info: else :
        cmd = [CLOUDFLARED_BIN, "tunnel", "--no-autoupdate", "run"]  # info: set cmd
        env = os.environ.copy()  # info: set env
        env["TUNNEL_TOKEN"] = token  # info: env [ "TUNNEL_TOKEN" ] = token
        popen_kwargs = {"env": env}  # info: set popen_kwargs
    log(f"{full_timestamp()}Starting cloudflared mode={mode} public_host={HOSTNAME}")  # info: call log
    _tunnel_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, **popen_kwargs)  # info: set _tunnel_proc

    def pump() -> None:  # info: def pump
        assert _tunnel_proc is not None and _tunnel_proc.stdout is not None  # info: assert _tunnel_proc is not None and _tunnel_proc .
        for line in _tunnel_proc.stdout:  # info: for line in _tunnel_proc . stdout :
            text = line.rstrip()  # info: set text
            interesting = _cloudflared_interesting(text)  # info: set interesting
            if interesting:  # info: if interesting :
                log(f"{full_timestamp()}{interesting}")  # info: call log
            if "Registered tunnel connection" in text or "Connected to Cloudflare" in text:  # info: if "Registered tunnel connection" in text or "Connected to Cloudflare" in text
                if not _tunnel_ready.is_set():  # info: if not _tunnel_ready . is_set ( ) :
                    log(f"{full_timestamp()}Tunnel READY — first connection registered.")  # info: call log
                    _tunnel_ready.set()  # info: _tunnel_ready . set ( )
            if _stop.is_set():  # info: if _stop . is_set ( ) :
                break  # info: break
        if _tunnel_proc.poll() is not None and not _tunnel_ready.is_set():  # info: if _tunnel_proc . poll ( ) is not
            log(f"{full_timestamp()}Tunnel DOWN — cloudflared exited before ready (code={_tunnel_proc.returncode}).")  # info: call log

    threading.Thread(target=pump, name="cloudflared-log", daemon=True).start()  # info: threading . Thread ( target = pump ,
    return True  # info: return True


# ====================================================
# SECTION: function wait_for_tunnel_ready
# What it does: wait for tunnel ready.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wait_for_tunnel_ready() -> None:  # info: def wait_for_tunnel_ready
    if not ENABLE_TUNNEL or _tunnel_ready.is_set():  # info: if not ENABLE_TUNNEL or _tunnel_ready . is_set (
        return  # info: return
    log(f"{full_timestamp()}Waiting for tunnel register (timeout={TUNNEL_READY_TIMEOUT_SEC:.0f}s)…")  # info: call log
    if not _tunnel_ready.wait(timeout=TUNNEL_READY_TIMEOUT_SEC):  # info: if not _tunnel_ready . wait ( timeout =
        log(f"{full_timestamp()}Tunnel WAITING — no register within {TUNNEL_READY_TIMEOUT_SEC:.0f}s; continuing.")  # info: call log


# ====================================================
# SECTION: function _is_ecoflow_job
# What it does:  is ecoflow job.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_ecoflow_job(jid: str) -> bool:  # info: def _is_ecoflow_job
    return jid.startswith("ecoflow_") or jid in ("delta2_read", "river2pro_read")  # info: return jid . startswith ( "ecoflow_" ) or


# ====================================================
# SECTION: function run_command_job
# What it does: run command job.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_command_job(job: dict) -> None:  # info: def run_command_job
    jid = job.get("id", "?")  # info: set jid
    cmd = (job.get("command") or "").strip()  # info: set cmd
    if not cmd:  # info: if not cmd :
        log(f"{full_timestamp()}job:{jid} SKIP — empty command")  # info: call log
        return  # info: return
    timeout = float(job.get("timeout_sec") or 120)  # info: set timeout
    cwd = (job.get("cwd") or "").strip() or None  # info: set cwd
    env = os.environ.copy()  # info: set env
    extra = job.get("env") or {}  # info: set extra
    if isinstance(extra, dict):  # info: if isinstance ( extra , dict ) :
        env.update({str(k): str(v) for k, v in extra.items()})  # info: env . update ( { str ( k
    quiet = jid in ("github_sync_all", "github_setup_remotes", "github_autopush")  # info: set quiet
    eco = _is_ecoflow_job(jid)  # info: set eco
    # EcoFlow: no RUN spam — only the final SUMMARY line (or a quiet FAIL)
    if not quiet and not eco:  # info: if not quiet and not eco :
        log(f"{full_timestamp()}job:{jid} RUN  {cmd}")  # info: call log
    try:  # info: try :
        proc = subprocess.Popen(  # info: own process group so a timeout can kill Kokoro children
            ["bash", "-lc", cmd],  # info: [ "bash" , "-lc" , cmd ]
            cwd=cwd,  # info: cwd = cwd
            env=env,  # info: env = env
            stdout=subprocess.PIPE,  # info: stdout = subprocess . PIPE
            stderr=subprocess.PIPE,  # info: stderr = subprocess . PIPE
            text=True,  # info: text = True
            start_new_session=True,  # info: start_new_session = True
        )  # info: )
        try:  # info: try
            out, err = proc.communicate(timeout=timeout)  # info: set out , err
        except subprocess.TimeoutExpired:  # info: except subprocess . TimeoutExpired
            try:  # info: try
                os.killpg(proc.pid, signal.SIGTERM)  # info: kill the whole job, not only bash
            except ProcessLookupError:  # info: except ProcessLookupError
                pass  # info: pass
            try:  # info: try
                proc.communicate(timeout=5)  # info: proc . communicate ( timeout = 5 )
            except subprocess.TimeoutExpired:  # info: except subprocess . TimeoutExpired
                try:  # info: try
                    os.killpg(proc.pid, signal.SIGKILL)  # info: os . killpg ( proc . pid , signal . SIGKILL )
                except ProcessLookupError:  # info: except ProcessLookupError
                    pass  # info: pass
                proc.communicate()  # info: proc . communicate ( )
            raise  # info: raise
        out = (out or "").strip()  # info: set out
        err = (err or "").strip()  # info: set err
        rcode = proc.returncode  # info: set rcode
        if rcode == 0:  # info: if rcode == 0 :
            if eco:  # info: if eco :
                # One clean line: prefer SUMMARY=; fold INTERNAL= the same way.
                # Skip STATUS= (redundant when SUMMARY is present).
                summary = None  # info: set summary
                for ln in out.splitlines():  # info: for ln in out . splitlines ( )
                    s = ln.strip()  # info: set s
                    if s.startswith("SUMMARY=") or s.startswith("INTERNAL="):  # info: if s . startswith ( "SUMMARY=" ) or
                        summary = s  # info: set summary
                        break  # info: break
                if summary:  # info: if summary :
                    log(f"{full_timestamp()}  ▸  {summary}")  # info: call log
                else:  # info: else :
                    log(f"{full_timestamp()}  ▸  {jid} OK")  # info: call log
            elif out:  # info: elif out :
                for line in out.splitlines()[:40]:  # info: for line in out . splitlines ( )
                    line = line.strip()  # info: set line
                    if not line:  # info: if not line :
                        continue  # info: continue
                    if quiet and any(line.startswith(p) for p in ("[ok]", "[skip]", "[clone]", "Updated", "Added", "Done.")):  # info: if quiet and any ( line . startswith
                        continue  # info: continue
                    log(f"{full_timestamp()}job:{jid} | {line}")  # info: call log
            elif not quiet:  # info: elif not quiet :
                log(f"{full_timestamp()}job:{jid} OK")  # info: call log
        else:  # info: else :
            if eco:  # info: if eco :
                # Only log real failures (both BLE and API down) — one line
                reason = ""  # info: set reason
                for ln in (out or err).splitlines():  # info: for ln in ( out or err )
                    s = ln.strip()  # info: set s
                    if s.startswith("No data") or s.startswith("WAITING"):  # info: if s . startswith ( "No data" ) or
                        reason = s  # info: set reason
                        break  # info: break
                if reason:  # info: if reason :
                    log(f"{full_timestamp()}  ✗  {jid}  {reason}")  # info: call log
                else:  # info: else :
                    log(f"{full_timestamp()}  ✗  {jid} FAIL code={rcode}")  # info: call log
            else:  # info: else :
                log(f"{full_timestamp()}job:{jid} FAIL code={rcode}")  # info: call log
                for line in (err or out).splitlines()[:20]:  # info: for line in ( err or out )
                    log(f"{full_timestamp()}job:{jid} ! {line}")  # info: call log
    except subprocess.TimeoutExpired:  # info: except subprocess . TimeoutExpired :
        log(f"{full_timestamp()}job:{jid} TIMEOUT after {timeout:.0f}s")  # info: call log
    except Exception as e:  # info: except Exception as e :
        log(f"{full_timestamp()}job:{jid} ERROR {e}")  # info: call log


# ====================================================
# SECTION: function run_builtin
# What it does: run builtin.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_builtin(job: dict) -> None:  # info: def run_builtin
    global _latest, HOSTNAME, TOKEN_FILE, CLOUDFLARED_BIN, TUNNEL_READY_TIMEOUT_SEC  # info: global _latest , HOSTNAME , TOKEN_FILE , CLOUDFLARED_BIN
    jid = job.get("id", "?")  # info: set jid
    name = (job.get("builtin") or "").strip()  # info: set name
    if name == "heartbeat":  # info: if name == "heartbeat" :
        line = heartbeat_line()  # info: set line
        with _lock:  # info: with _lock :
            _latest = line  # info: set _latest
        log(line)  # info: call log
        return  # info: return
    if name == "self_process":  # info: if name == "self_process" :
        log(f"{full_timestamp()}boot:p0 self_process pid={os.getpid()}")  # info: call log
        return  # info: return
    if name == "tunnel_start":  # info: if name == "tunnel_start" :
        if job.get("public_host"):  # info: if job . get ( "public_host" ) :
            HOSTNAME = str(job["public_host"])  # info: set HOSTNAME
        if job.get("token_file"):  # info: if job . get ( "token_file" ) :
            TOKEN_FILE = Path(str(job["token_file"]))  # info: set TOKEN_FILE
        if job.get("cloudflared_bin"):  # info: if job . get ( "cloudflared_bin" ) :
            CLOUDFLARED_BIN = str(job["cloudflared_bin"])  # info: set CLOUDFLARED_BIN
        if job.get("timeout_sec"):  # info: if job . get ( "timeout_sec" ) :
            TUNNEL_READY_TIMEOUT_SEC = float(job["timeout_sec"])  # info: set TUNNEL_READY_TIMEOUT_SEC
        log(f"{full_timestamp()}boot:p1 cloudflare_tunnel host={HOSTNAME}")  # info: call log
        if not internet_ok(force=True):  # info: if not internet_ok ( force = True )
            log(f"{full_timestamp()}internet DOWN at boot — tunnel DEFERRED; local jobs continue; retry every minute")  # info: call log
            return  # info: return
        log(f"{full_timestamp()}internet OK at boot — starting tunnel")  # info: call log
        if start_tunnel():  # info: if start_tunnel ( ) :
            wait_for_tunnel_ready()  # info: call wait_for_tunnel_ready
        elif ENABLE_TUNNEL:  # info: elif ENABLE_TUNNEL :
            log(f"{full_timestamp()}Tunnel DOWN — continuing with local jobs only.")  # info: call log
        return  # info: return
    if name == "ensure_tunnel_online":  # info: if name == "ensure_tunnel_online" :
        ensure_tunnel_online()  # info: call ensure_tunnel_online
        return  # info: return
    if name == "ble_adapter_cycle":  # info: if name == "ble_adapter_cycle" :
        try:  # info: try
            import schedule_runtime as sch  # info: import schedule_runtime as sch
            result = sch.run_ble_adapter_cycle()  # info: set result
        except Exception as exc:  # info: except Exception as exc
            log(f"{full_timestamp()}job:{jid} ble_adapter_cycle ERROR {exc}")  # info: call log
            return  # info: return
        log(f"{full_timestamp()}job:{jid} ble_adapter_cycle ok={result.get('ok')} code={result.get('code')}")  # info: call log
        return  # info: return
    if name == "ensure_process":  # info: if name == "ensure_process" :
        try:  # info: try
            import schedule_runtime as sch  # info: import schedule_runtime as sch
            result = sch.ensure_process(job)  # info: set result
        except Exception as exc:  # info: except Exception as exc
            log(f"{full_timestamp()}job:{jid} ensure_process ERROR {exc}")  # info: call log
            return  # info: return
        log(f"{full_timestamp()}job:{jid} ensure_process {result.get('detail')}")  # info: call log
        return  # info: return
    log(f"{full_timestamp()}job:{jid} UNKNOWN builtin={name!r}")  # info: call log


def _schedule_updated_since(since: datetime) -> bool:  # info: def _schedule_updated_since
    path = Path(  # info: set path
        "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/Timing/hour_batch_schedule.json"  # info: path
    )  # info: )
    try:  # info: try
        doc = json.loads(path.read_text(encoding="utf-8"))  # info: set doc
        stamp = datetime.fromisoformat(str(doc.get("at") or ""))  # info: set stamp
    except (OSError, ValueError, TypeError):  # info: except
        return False  # info: return False
    if stamp.tzinfo is None:  # info: if stamp . tzinfo is None
        stamp = stamp.astimezone()  # info: set stamp
    return stamp >= since - timedelta(seconds=30)  # info: written during this run


# ====================================================
# SECTION: function _news_update_fresh
# What it does: True when news_update_current.wav belongs to the latest :35 cycle, including a finish just after the next :00.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _news_update_fresh(wall: datetime) -> bool:  # info: def _news_update_fresh
    path = Path(  # info: set path
        "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Media/Audio/Voice/news_update_current.wav"  # info: path
    )  # info: )
    try:  # info: try
        if not path.is_file() or path.stat().st_size <= 64:  # info: if missing or tiny
            return False  # info: return False
        mtime = datetime.fromtimestamp(path.stat().st_mtime).astimezone()  # info: set mtime
    except OSError:  # info: except OSError
        return False  # info: return False
    gate = wall.replace(minute=35, second=0, microsecond=0)  # info: set gate
    if wall < gate:  # info: before this hour's :35 — the cycle started last hour
        gate = gate - timedelta(hours=1)  # info: set gate
    return mtime >= gate and (wall - mtime) <= timedelta(hours=2)  # info: latest :35 cycle, not an older file


# ====================================================
# SECTION: function run_job
# What it does: run job.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_job(job: dict) -> bool:  # info: def run_job — True when work started
    if not _job_on(job):  # info: if not _job_on ( job )
        return False  # info: return False
    # After SIGTERM, start no new jobs (the rest of the scheduler pass used to re-launch the tunnel and
    # wait 45 s for it, so every stop hit TimeoutStopSec=30 + SIGKILL). 2026-09-29.
    if _stop.is_set():  # info: if _stop . is_set ( ) :
        return False  # info: return False
    if job.get("needs_internet") and not internet_ok(force=True):  # info: if job . get ( "needs_internet" ) and
        log(f"{full_timestamp()}job:{job.get('id', '?')} SKIP — offline (will retry when internet is up)")  # info: call log
        return False  # info: return False — catch-up may retry
    if NIGHT_SLEEP_GATE and _night_sleep is not None:  # info: if NIGHT_SLEEP_GATE and _night_sleep is not None :
        jid = str(job.get("id") or "")  # info: set jid
        try:  # info: try :
            allowed = _night_sleep.should_run(jid, enabled=True)  # info: set allowed
        except Exception:  # info: except Exception :
            allowed = True  # info: set allowed
        if not allowed:  # info: if not allowed :
            log(f"{full_timestamp()}job:{jid} SKIP — night sleep")  # info: call log
            return False  # info: return False
    builtin = (job.get("builtin") or "").strip()  # info: set builtin
    if builtin:  # info: if builtin :
        run_builtin(job)  # info: call run_builtin
        return True  # info: return True
    jid = str(job.get("id") or "")  # info: set jid
    # Long / blocking jobs stay off the scheduler thread so :35/:36/:55 still fire.
    if jid == "github_sync_all":  # info: if jid == "github_sync_all"
        if not _github_busy.acquire(blocking=False):  # info: if not _github_busy . acquire ( blocking = False )
            return False  # info: already syncing; skip this tick
        def _github_work() -> None:  # info: def _github_work
            try:  # info: try
                run_command_job(job)  # info: call run_command_job
            finally:  # info: finally
                _github_busy.release()  # info: _github_busy . release ( )
        threading.Thread(target=_github_work, name="github-sync", daemon=True).start()  # info: start side thread
        return True  # info: return True
    if jid == "security_camera_frame_grab":  # info: if jid == "security_camera_frame_grab"
        if not _camera_busy.acquire(blocking=False):  # info: if not _camera_busy . acquire ( blocking = False )
            return False  # info: already grabbing
        def _camera_work() -> None:  # info: def _camera_work
            try:  # info: try
                run_command_job(job)  # info: call run_command_job
            finally:  # info: finally
                _camera_busy.release()  # info: _camera_busy . release ( )
        threading.Thread(target=_camera_work, name="security-camera", daemon=True).start()  # info: start side thread
        return True  # info: return True
    if jid == "voice_kilauea_image_check":  # info: if jid == "voice_kilauea_image_check"
        # Same Kokoro lock as news + hour batch. A :45 fire mid-batch skips a desk WAV (rc 75).
        minute = datetime.now().astimezone().minute  # info: set minute
        if 30 <= minute <= 54 or _generate_hour_reports_running():  # info: :30 job overlaps :35 news; :45 overlaps desks
            log(f"{full_timestamp()}job:{jid} SKIP — hour voice lane owns the Kokoro lock")  # info: call log
            return False  # info: return False — next quarter-hour can try
    # Hour workflow owns the air clock. News TTS must finish before desk TTS (same lock).
    if jid == "news_cycle":  # info: if jid == "news_cycle"
        if not _news_busy.acquire(blocking=False):  # info: if not _news_busy . acquire ( blocking = False )
            log(f"{full_timestamp()}job:{jid} SKIP — news_cycle already running")  # info: call log
            return False  # info: return False
        def _news_work() -> None:  # info: def _news_work
            born = datetime.now().astimezone()  # info: hour this cycle belongs to, even if it finishes after :00
            try:  # info: try
                run_command_job(job)  # info: call run_command_job
            finally:  # info: finally
                _news_busy.release()  # info: _news_busy . release ( )
                key = _workflow_hour_key("news_cycle", born)  # info: set key
                if _news_update_fresh(born):  # info: if wav landed for the hour we started
                    _mark_hour_workflow_done(key)  # info: keep catch-up closed
                else:  # info: else
                    _hour_workflow_done.discard(key)  # info: failed run must not block :36–:39 retry
                    _save_hour_workflow_done()  # info: persist reopen
                    log(f"{full_timestamp()}job:news_cycle  no fresh wav — catch-up stays open")  # info: call log
        threading.Thread(target=_news_work, name="hour-news_cycle", daemon=True).start()  # info: start side thread
        return True  # info: return True
    if jid in ("voice_hour_batch", "radio_push_hour"):  # info: if jid in ( "voice_hour_batch" , "radio_push_hour" )
        if jid == "voice_hour_batch":  # info: if jid == "voice_hour_batch"
            if _generate_hour_reports_running():  # info: real python running the script only
                log(f"{full_timestamp()}job:{jid} SKIP — generate_hour_reports already running")  # info: call log
                # Count as done this hour so catch-up / watchdog do not keep retrying.
                try:  # info: try
                    wall = datetime.now().astimezone()  # info: set wall
                    _mark_hour_workflow_done(_workflow_hour_key(jid, wall))  # info: mark hour done
                except Exception:  # info: except Exception
                    pass  # info: pass
                return True  # info: return True — hour is covered; do not retry
        if not _hour_batch_busy.acquire(blocking=False):  # info: if not _hour_batch_busy . acquire ( blocking = False )
            log(f"{full_timestamp()}job:{jid} SKIP — hour batch already running")  # info: call log
            return False  # info: return False — keep catch-up open
        def _hour_work() -> None:  # info: def _hour_work
            born = datetime.now().astimezone()  # info: hour this batch belongs to
            try:  # info: try
                run_command_job(job)  # info: call run_command_job
            finally:  # info: finally
                _hour_batch_busy.release()  # info: _hour_batch_busy . release ( )
                if jid == "voice_hour_batch" and not _generate_hour_reports_running():  # info: process actually exited
                    key = _workflow_hour_key("voice_hour_batch", born)  # info: set key
                    if not _schedule_updated_since(born):  # info: crashed or timed out before Timing was written
                        _hour_workflow_done.discard(key)  # info: allow watchdog / catch-up to try again
                        _save_hour_workflow_done()  # info: persist reopen
                        log(f"{full_timestamp()}job:voice_hour_batch  no schedule stamp — catch-up stays open")  # info: call log
        threading.Thread(target=_hour_work, name=f"hour-{jid}", daemon=True).start()  # info: start side thread
        return True  # info: return True
    run_command_job(job)  # info: call run_command_job
    return True  # info: return True


# ====================================================
# SECTION: function _job_on
# What it does: True when the override file, or else the jobs.py flag, says this job should run. Fail open to the jobs.py flag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _job_on(job: dict) -> bool:  # info: def _job_on
    if job.get("from_schedule"):  # info: schedule entry enable is the authority
        return bool(job.get("enabled"))  # info: return bool ( job . get ( "enabled" ) )
    if actl is None:  # info: if actl is None
        return bool(job.get("enabled"))  # info: return bool ( job . get ( "enabled" ) )
    try:  # info: try
        return actl.job_enabled(job)  # info: return actl . job_enabled ( job )
    except Exception:  # info: except Exception
        return bool(job.get("enabled"))  # info: return bool ( job . get ( "enabled" ) )


# ====================================================
# SECTION: function enabled_jobs
# What it does: Jobs that should run. The override file wins over the jobs.py flag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def enabled_jobs(section: list) -> list:  # info: def enabled_jobs
    return [j for j in section if isinstance(j, dict) and _job_on(j)]  # info: return [ j for j in section if isinstance


# ====================================================
# SECTION: function _exact_due
# What it does: True when this EXACT_TIME job belongs on this 5-second mark. every_seconds uses at_second as the phase. from_minute holds a job until that minute.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _exact_due(job: dict, step) -> bool:  # info: def _exact_due
    every = job.get("every_seconds")  # info: set every
    if every:  # info: if every
        gap = max(1, int(every))  # info: set gap
        phase = int(job.get("at_second") or 0) % gap  # info: set phase
        # Use seconds-since-midnight so every_seconds > 60 (e.g. 300 / 900) lands on the clock.
        wall = int(step.hour) * 3600 + int(step.minute) * 60 + int(step.second)  # info: set wall
        if wall % gap != phase:  # info: if this wall second is not this job's phase
            return False  # info: return False
        opened = job.get("from_minute")  # info: set opened
        if opened is not None and step.minute < int(opened):  # info: if before the :30 block
            return False  # info: return False
        return True  # info: return True
    if job.get("at_hour") is not None and int(job["at_hour"]) != step.hour:  # info: if this hour is not the one named
        return False  # info: return False
    if int(job.get("at_minute") or 0) != step.minute:  # info: if int ( job . get ( "at_minute" ) or 0 ) != step . minute
        return False  # info: return False
    if int(job.get("at_second") or 0) != step.second:  # info: if int ( job . get ( "at_second" ) or 0 ) != step . second
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function _workflow_hour_key
# What it does: Hour-scoped key so news / voice batch / radio_push catch up once if their exact second was missed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _workflow_hour_key(jid: str, step) -> str:  # info: def _workflow_hour_key
    return f"{jid}|{step.date().isoformat()}|{step.hour:02d}"  # info: return f" { jid } |


# ====================================================
# SECTION: function _workflow_catchup_due
# What it does: True when an hour-workflow job missed its exact second and still has runway before the next gate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _workflow_catchup_due(job: dict, step) -> bool:  # info: def _workflow_catchup_due
    jid = str(job.get("id") or "")  # info: set jid
    if jid not in HOUR_WORKFLOW:  # info: if jid not in HOUR_WORKFLOW
        return False  # info: return False
    if step.second != 0:  # info: once per minute on the :00 mark
        return False  # info: return False
    if _workflow_hour_key(jid, step) in _hour_workflow_done:  # info: already ran this hour
        return False  # info: return False
    at_m = int(job.get("at_minute") or 0)  # info: set at_m
    # news :35 only; voice from scheduled/base minute through :54; radio_push :55→:59
    if jid == "news_cycle":  # info: if jid == "news_cycle"
        # :35 exact; keep trying a few minutes so a late/blocked :35:00 still banks before fold-in.
        return at_m <= step.minute <= min(at_m + 4, 39)  # info: return at_m .. :39
    if jid == "voice_hour_batch":  # info: if jid == "voice_hour_batch"
        # Always open the window from env base (:36) even if a stale job dict still says :42.
        base = int(os.environ.get("RR_VOICE_HOUR_BASE_MINUTE", "36"))  # info: set base
        start = min(at_m, base) if at_m else base  # info: set start
        start = max(0, min(59, start))  # info: clamp start
        return start <= step.minute <= 54  # info: return start <= step . minute <= 54
    if jid == "radio_push_hour":  # info: if jid == "radio_push_hour"
        return at_m <= step.minute <= 59  # info: return at_m <= step . minute <= 59
    return False  # info: return False


# ====================================================
# SECTION: function _kick_hour_batch_watchdog
# What it does: Belt-and-suspenders — if generate_hour_reports has not started this hour by :36+, start it now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _kick_hour_batch_watchdog(wall: datetime) -> None:  # info: def _kick_hour_batch_watchdog
    global _watchdog_last_minute  # info: global _watchdog_last_minute
    if _stop.is_set():  # info: if _stop . is_set ( )
        return  # info: return
    minute = int(wall.minute)  # info: set minute
    if _watchdog_last_minute == minute:  # info: once per clock minute
        return  # info: return
    base = int(os.environ.get("RR_VOICE_HOUR_BASE_MINUTE", "36"))  # info: set base
    resolve = getattr(jobmod, "voice_hour_batch_at_minute", None)  # info: set resolve
    at_m = int(resolve()) if callable(resolve) else base  # info: set at_m
    start = min(at_m, base)  # info: set start
    start = max(0, min(59, start))  # info: clamp
    if minute < start or minute > 54:  # info: outside generate window
        return  # info: return
    key = f"voice_hour_batch|{wall.date().isoformat()}|{wall.hour:02d}"  # info: set key
    if key in _hour_workflow_done:  # info: already started this hour
        _watchdog_last_minute = minute  # info: set _watchdog_last_minute
        return  # info: return
    # External manual run still counts — do not stack a second generate_hour_reports.
    if _generate_hour_reports_running():  # info: real python running the script only
        log(f"{full_timestamp()}watchdog  voice_hour_batch already running externally — mark hour done")  # info: call log
        _mark_hour_workflow_done(key)  # info: mark hour done
        _watchdog_last_minute = minute  # info: set _watchdog_last_minute
        return  # info: return
    job = None  # info: set job
    for j in _scheduled_jobs():  # info: for j in _scheduled_jobs ( )
        if isinstance(j, dict) and j.get("id") == "voice_hour_batch":  # info: if voice hour batch
            job = {**j, "at_minute": at_m}  # info: set job
            break  # info: break
    if job is None:  # info: if job is None
        log(f"{full_timestamp()}watchdog  voice_hour_batch MISSING from enabled jobs")  # info: call log
        _watchdog_last_minute = minute  # info: set _watchdog_last_minute
        return  # info: return
    _watchdog_last_minute = minute  # info: set before start so a failed start retries next minute
    log(  # info: call log
        f"{full_timestamp()}watchdog  START voice_hour_batch  window={start:02d}-54  clock={wall.strftime('%H:%M:%S')}  at_minute={at_m}"  # info: f" ... "
    )  # info: )
    if run_job(job):  # info: if run_job ( job )
        _mark_hour_workflow_done(key)  # info: mark hour done
        log(f"{full_timestamp()}watchdog  voice_hour_batch launched")  # info: call log
    else:  # info: else
        log(f"{full_timestamp()}watchdog  voice_hour_batch launch failed — will retry next minute")  # info: call log
        _watchdog_last_minute = None  # info: allow immediate retry next loop after backoff


# ====================================================
# SECTION: function _fire_exact_step
# What it does: Run every job due on this 5-second mark. Hour workflow first; defer camera/BLE/hawaii on that tick.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fire_exact_step(exact_jobs: list, step, fired_exact: set) -> None:  # info: def _fire_exact_step
    due: list[dict] = []  # info: set due
    for j in exact_jobs:  # info: for j in exact_jobs
        if not isinstance(j, dict):  # info: if not isinstance ( j , dict )
            continue  # info: continue
        if _exact_due(j, step) or _workflow_catchup_due(j, step):  # info: if exact or catch-up
            due.append(j)  # info: due . append ( j )
    if not due:  # info: if not due
        return  # info: return
    # priority 0 = highest (same as ON_BOOT). Hour workflow still ahead of stack at equal priority.
    due.sort(  # info: due . sort
        key=lambda j: (  # info: key = lambda j
            int(j.get("priority") if j.get("priority") is not None else 50),  # info: lower number first
            0 if j.get("id") in HOUR_WORKFLOW else 1,  # info: hour lane before stack
            str(j.get("id") or ""),  # info: stable
        )  # info: )
    )  # info: )
    workflow_due = any(j.get("id") in HOUR_WORKFLOW for j in due)  # info: set workflow_due
    if workflow_due:  # info: if workflow_due
        names = ",".join(str(j.get("id")) for j in due if j.get("id") in HOUR_WORKFLOW)  # info: set names
        log(f"{full_timestamp()}hour-lane  due={names}  at={step.strftime('%H:%M:%S')}")  # info: call log
    for j in due:  # info: for j in due
        jid = str(j.get("id") or "")  # info: set jid
        if workflow_due and jid in STACK_DEFER:  # info: defer stack while hour script must start
            continue  # info: continue — retry next tick; do not mark fired
        key = f"{jid}|{step.date().isoformat()}|{step.hour:02d}:{step.minute:02d}:{step.second:02d}"  # info: set key
        if key in fired_exact:  # info: if key in fired_exact
            continue  # info: continue
        started = run_job(j)  # info: set started
        if not started:  # info: if not started
            if jid in HOUR_WORKFLOW:  # info: if jid in HOUR_WORKFLOW
                log(f"{full_timestamp()}hour-lane  {jid} did not start at {step.strftime('%H:%M:%S')}")  # info: call log
            continue  # info: continue — offline / busy; catch-up may retry
        fired_exact.add(key)  # info: fired_exact . add ( key )
        if jid in HOUR_WORKFLOW:  # info: if jid in HOUR_WORKFLOW
            _mark_hour_workflow_done(_workflow_hour_key(jid, step))  # info: mark hour done for catch-up


# ====================================================
# SECTION: function _scheduled_jobs
# What it does: The repeating lists, filtered by the current override file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _scheduled_jobs() -> list:  # info: def _scheduled_jobs
    jobs = enabled_jobs(getattr(jobmod, "EXACT_TIME", []))  # info: set jobs
    # voice_hour_batch minute is recalculated after each generate_hour_reports run.
    resolve = getattr(jobmod, "voice_hour_batch_at_minute", None)  # info: set resolve
    if not callable(resolve):  # info: if not callable ( resolve )
        return jobs  # info: return jobs
    out = []  # info: set out
    for job in jobs:  # info: for job in jobs
        if isinstance(job, dict) and job.get("id") == "voice_hour_batch":  # info: if voice hour batch
            job = {**job, "at_minute": int(resolve())}  # info: refresh at_minute from Timing schedule
        out.append(job)  # info: out . append ( job )
    return out  # info: return out


# ====================================================
# SECTION: function _kick_power
# What it does: Start due EcoFlow power schedules on a side thread. Skips when one is already running. Does not restart the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _kick_power(step: datetime) -> None:  # info: def _kick_power
    if actl is None or _stop.is_set():  # info: if actl is None or _stop . is_set ( )
        return  # info: return
    try:  # info: try
        doc = actl.load_power()  # info: set doc
        items = [it for it in (doc.get("items") or []) if isinstance(it, dict)]  # info: set items
        master = bool(doc.get("master_enabled", True))  # info: set master
        if not any(actl.item_due(it, step, master) for it in items):  # info: if not any ( actl . item_due ( it , step , master ) for it in items )
            return  # info: return
    except Exception as exc:  # info: except Exception as exc
        log(f"{full_timestamp()}power schedules ERROR {exc}")  # info: call log
        return  # info: return
    if not _power_busy.acquire(blocking=False):  # info: if not _power_busy . acquire ( blocking = False )
        log(f"{full_timestamp()}power schedules still running")  # info: call log
        return  # info: return

    def work():  # info: def work
        try:  # info: try
            actl.run_due(step, log=lambda msg: log(f"{full_timestamp()}{msg}"))  # info: actl . run_due ( step , log = lambda msg : log
        except Exception as exc:  # info: except Exception as exc
            log(f"{full_timestamp()}power schedules ERROR {exc}")  # info: call log
        finally:  # info: finally
            _power_busy.release()  # info: _power_busy . release ( )

    threading.Thread(target=work, name="power-automations", daemon=True).start()  # info: threading . Thread ( target = work , name = "power-automations" , daemon = True ) . start ( )


# ====================================================
# SECTION: function _kick_service
# What it does: Snapshot last-known network counts once when a published service window becomes active. Does not restart the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _kick_service(step: datetime) -> None:  # info: def _kick_service
    if svc is None or _stop.is_set():  # info: if svc is None or _stop . is_set ( )
        return  # info: return
    try:  # info: try
        if not svc.needs_freeze(step):  # info: if not svc . needs_freeze ( step )
            return  # info: return
    except Exception as exc:  # info: except Exception as exc
        log(f"{full_timestamp()}service notice ERROR {exc}")  # info: call log
        return  # info: return
    if not _service_busy.acquire(blocking=False):  # info: if not _service_busy . acquire ( blocking = False )
        return  # info: return

    def work():  # info: def work
        try:  # info: try
            frozen = svc.freeze_due(step)  # info: set frozen
            if frozen:  # info: if frozen
                log(f"{full_timestamp()}service notice frozen {','.join(frozen)}")  # info: call log
        except Exception as exc:  # info: except Exception as exc
            log(f"{full_timestamp()}service notice ERROR {exc}")  # info: call log
        finally:  # info: finally
            _service_busy.release()  # info: _service_busy . release ( )

    threading.Thread(target=work, name="service-notice", daemon=True).start()  # info: threading . Thread ( target = work , name = "service-notice" , daemon = True ) . start ( )


# ====================================================
# SECTION: function _normalize_hhmm
# What it does:  normalize hhmm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _normalize_hhmm(raw: object) -> str | None:  # info: def _normalize_hhmm
    if not isinstance(raw, str) or ":" not in raw:  # info: if not isinstance ( raw , str )
        return None  # info: return None
    try:  # info: try :
        hh, mm = (int(x) for x in raw.strip().split(":", 1))  # info: hh , mm = ( int ( x
    except ValueError:  # info: except ValueError :
        return None  # info: return None
    if not (0 <= hh <= 23 and 0 <= mm <= 59):  # info: if not ( 0 <= hh <= 23
        return None  # info: return None
    return f"{hh:02d}:{mm:02d}"  # info: return f" { hh : 02d } :


# ====================================================
# SECTION: function crossed_slots
# What it does: Minutes after the last slot through now. A long job can cross :00; those minutes still count. Caps at 60.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def crossed_slots(prev: datetime, now: datetime, cap: int = 60) -> list[datetime]:  # info: def crossed_slots
    prev_m = prev.replace(second=0, microsecond=0)  # info: set prev_m
    now_m = now.replace(second=0, microsecond=0)  # info: set now_m
    if now_m <= prev_m:  # info: if now_m <= prev_m
        return []  # info: return [ ]
    if now_m - prev_m > timedelta(minutes=cap):  # info: if now_m - prev_m > timedelta
        prev_m = now_m - timedelta(minutes=cap)  # info: set prev_m
    out: list[datetime] = []  # info: set out
    step = prev_m  # info: set step
    while step < now_m and len(out) < cap:  # info: while step < now_m and len ( out ) < cap
        step = step + timedelta(minutes=1)  # info: set step
        out.append(step)  # info: out . append
    return out  # info: return out


# ====================================================
# SECTION: function crossed_seconds
# What it does: Whole seconds after prev through now. Caps catch-up so a long job does not replay hours.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def crossed_seconds(prev: datetime, now: datetime, cap: int = 120) -> list[datetime]:  # info: def crossed_seconds
    prev_s = prev.replace(microsecond=0)  # info: set prev_s
    now_s = now.replace(microsecond=0)  # info: set now_s
    if now_s <= prev_s:  # info: if now_s <= prev_s :
        return []  # info: return [ ]
    if now_s - prev_s > timedelta(seconds=cap):  # info: if catch-up too large
        prev_s = now_s - timedelta(seconds=cap)  # info: set prev_s
    out: list[datetime] = []  # info: set out
    step = prev_s  # info: set step
    while step < now_s and len(out) < cap:  # info: while step < now_s and len ( out ) < cap :
        step = step + timedelta(seconds=1)  # info: set step
        out.append(step)  # info: out . append ( step )
    return out  # info: return out


# ====================================================
# SECTION: function _schedule_mode_loop
# What it does: Fire only from Database schedule JSON. Idle while disconnected; re-check arming without restart.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _schedule_mode_loop(sch) -> None:  # info: def _schedule_mode_loop
    last_fire: dict[str, float] = {}  # info: set last_fire
    last_second: datetime | None = None  # info: set last_second
    booted = False  # info: set booted
    logged_idle = False  # info: set logged_idle
    log(f"{full_timestamp()}scheduler  MODE=schedule entries={len((sch.load_schedule('pacific').get('entries') or []))}")  # info: call log
    while not _stop.is_set():  # info: while not _stop . is_set ( ) :
        if sch.polling_disconnected("pacific"):  # info: if sch . polling_disconnected ( "pacific" ) :
            if not logged_idle:  # info: if not logged_idle :
                log(f"{full_timestamp()}scheduler  POLLING_DISCONNECTED — no jobs fire until schedules are armed")  # info: call log
                logged_idle = True  # info: set logged_idle
            booted = False  # info: set booted
            last_second = None  # info: set last_second
            _stop.wait(1.0)  # info: _stop . wait ( 1.0 )
            continue  # info: continue
        logged_idle = False  # info: set logged_idle
        if not booted:  # info: if not booted :
            boot = sch.boot_jobs("pacific", "boot")  # info: set boot
            log(f"{full_timestamp()}boot:start  schedule_jobs={len(boot)}")  # info: call log
            for j in boot:  # info: for j in boot :
                log(f"{full_timestamp()}boot:run  priority={j.get('priority', '?')}  id={j.get('id', '?')}")  # info: call log
                run_job(j)  # info: call run_job
            for j in sch.boot_jobs("pacific", "once_at_start"):  # info: for j in sch . boot_jobs
                run_job(j)  # info: call run_job
            log(f"{full_timestamp()}boot:done")  # info: call log
            now = datetime.now().astimezone().replace(microsecond=0)  # info: set now
            opened = now.replace(second=0) - timedelta(seconds=1)  # info: include this minute's :00
            for step in crossed_seconds(opened, now, cap=60):  # info: for step in crossed_seconds
                if step.hour != now.hour or step.minute != now.minute:  # info: if step is the previous minute
                    continue  # info: continue
                for j in sch.due_jobs("pacific", step, last_fire):  # info: for j in sch . due_jobs
                    if j.get("every_seconds") or j.get("id") in AI_HOLD:  # info: stacks run on the next tick; AI waits for its clock
                        continue  # info: continue
                    log(f"{full_timestamp()}boot:catch  id={j.get('id', '?')}  at={step.strftime('%H:%M:%S')}")  # info: call log
                    run_job(j)  # info: call run_job
            last_second = now  # info: set last_second
            booted = True  # info: set booted
            _kick_service(datetime.now().astimezone())  # info: call _kick_service
        wall = datetime.now().astimezone()  # info: set wall
        mark = wall.replace(microsecond=0)  # info: set mark
        if last_second is None:  # info: if last_second is None :
            last_second = mark  # info: set last_second
        elif mark < last_second:  # info: elif clock jumped back
            last_second = mark  # info: set last_second
        elif mark != last_second:  # info: elif mark != last_second :
            for step in crossed_seconds(last_second, mark):  # info: for step in crossed_seconds ( last_second , mark ) :
                for j in sch.due_jobs("pacific", step, last_fire):  # info: for j in sch . due_jobs
                    run_job(j)  # info: call run_job
                if step.second == 0:  # info: minute boundary only
                    _kick_service(step)  # info: call _kick_service
            last_second = mark  # info: set last_second
        _stop.wait(0.25)  # info: _stop . wait ( 0.25 )


# ====================================================
# SECTION: function scheduler_loop
# What it does: Prefer Database schedule JSON when present. Otherwise jobs.py timing. Reloads overrides; power schedules only in legacy mode.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def scheduler_loop() -> None:  # info: def scheduler_loop
    try:  # info: try schedule disconnect gate
        import schedule_runtime as sch  # info: import schedule_runtime as sch
    except Exception:  # info: except Exception
        sch = None  # info: set sch
    if sch is not None and sch.schedule_active("pacific"):  # info: if schedule JSON owns timing
        _schedule_mode_loop(sch)  # info: call _schedule_mode_loop
        return  # info: return
    if sch is not None and sch.polling_disconnected("pacific"):  # info: if schedule says do not fire
        log(f"{full_timestamp()}scheduler  POLLING_DISCONNECTED — no jobs fire until schedules are armed")  # info: call log
        while not _stop.is_set():  # info: idle until stop; do not start work
            _stop.wait(1.0)  # info: _stop . wait ( 1.0 )
        return  # info: return
    exact_jobs = _scheduled_jobs()  # info: exact_jobs = _scheduled_jobs ( )
    last_hour: int | None = None  # info: set last_hour
    last_slot: datetime | None = None  # info: set last_slot
    last_five: datetime | None = None  # info: set last_five
    fired_exact: set[str] = set()  # info: set fired_exact
    _load_hour_workflow_done()  # info: restore catch-up marks across restarts
    log(f"{full_timestamp()}scheduler  MODE=jobs.py exact_time={len(exact_jobs)}")  # info: call log
    now = datetime.now().astimezone().replace(microsecond=0)  # info: set now
    opened = now.replace(second=0) - timedelta(seconds=1)  # info: include this minute's :00
    for step in crossed_seconds(opened, now, cap=60):  # info: for step in crossed_seconds
        if step.hour != now.hour or step.minute != now.minute:  # info: if step is the previous minute
            continue  # info: continue
        if step.second % 5 != 0:  # info: if step . second % 5 != 0
            continue  # info: continue
        # Boot catch: only named clock jobs (not every_seconds stacks); AI waits for its clock.
        boot_jobs = [  # info: set boot_jobs
            j  # info: j
            for j in exact_jobs  # info: for j in exact_jobs
            if not j.get("every_seconds") and j.get("id") not in AI_HOLD  # info: if not j . get ( "every_seconds" ) and
        ]  # info: ]
        before = set(fired_exact)  # info: set before
        _fire_exact_step(boot_jobs, step, fired_exact)  # info: call _fire_exact_step
        for key in fired_exact - before:  # info: for key in fired_exact - before
            jid = key.split("|", 1)[0]  # info: set jid
            log(f"{full_timestamp()}boot:catch  id={jid}  at={step.strftime('%H:%M:%S')}")  # info: call log
    last_hour = now.hour  # info: set last_hour
    last_slot = now.replace(second=0, microsecond=0)  # info: set last_slot
    last_five = now.replace(second=(now.second // 5) * 5, microsecond=0)  # info: set last_five
    ov_stamp = actl.overrides_mtime() if actl is not None else None  # info: set ov_stamp
    _kick_power(datetime.now().astimezone())  # info: call _kick_power
    _kick_service(datetime.now().astimezone())  # info: call _kick_service
    while not _stop.is_set():  # info: while not _stop . is_set ( ) :
        if actl is not None:  # info: if actl is not None
            stamp = actl.overrides_mtime()  # info: set stamp
            if stamp != ov_stamp:  # info: if stamp != ov_stamp
                ov_stamp = stamp  # info: set ov_stamp
                exact_jobs = _scheduled_jobs()  # info: exact_jobs = _scheduled_jobs ( )
        wall = datetime.now().astimezone()  # info: set wall
        minute, hour = wall.minute, wall.hour  # info: minute , hour = wall . minute ,
        day = wall.date().isoformat()  # info: set day
        slot = wall.replace(second=0, microsecond=0)  # info: set slot
        five = wall.replace(second=(wall.second // 5) * 5, microsecond=0)  # info: set five
        if last_slot is None:  # info: if last_slot is None :
            last_hour, last_slot, last_five = hour, slot, five  # info: last_hour , last_slot , last_five = hour , slot , five
        elif slot < last_slot:  # info: elif slot < last_slot :
            last_hour, last_slot, last_five = hour, slot, five  # info: last_hour , last_slot , last_five = hour , slot , five
        else:  # info: else
            # Refresh job list BEFORE firing when the minute rolls — voice at_minute must be current.
            if slot != last_slot:  # info: if slot != last_slot
                exact_jobs = _scheduled_jobs()  # info: refresh voice_hour_batch minute from Timing / env base
                for step in crossed_slots(last_slot, slot):  # info: for step in crossed_slots ( last_slot , slot )
                    _kick_power(step)  # info: call _kick_power
                    _kick_service(step)  # info: call _kick_service
                last_slot = slot  # info: last_slot = slot
            if last_five is not None and five > last_five:  # info: if last_five is not None and five > last_five
                for step in crossed_seconds(last_five, five, cap=600):  # info: was 120 — too small when a long job delayed the loop
                    if step.second % 5 != 0:  # info: if step . second % 5 != 0
                        continue  # info: continue
                    _fire_exact_step(exact_jobs, step, fired_exact)  # info: hour workflow first; stack deferred on that tick
                last_five = five  # info: last_five = five
                if fired_exact:  # info: if fired_exact
                    fired_exact = {k for k in fired_exact if f"|{day}|" in k}  # info: set fired_exact
                # Drop yesterday's hour-workflow done marks.
                before = len(_hour_workflow_done)  # info: set before
                _hour_workflow_done.intersection_update(  # info: _hour_workflow_done . intersection_update
                    {k for k in _hour_workflow_done if k.split("|")[1] == day}  # info: keep today only
                )  # info: )
                if len(_hour_workflow_done) != before:  # info: if pruned
                    _save_hour_workflow_done()  # info: persist prune
        _kick_hour_batch_watchdog(wall)  # info: belt-and-suspenders for generate_hour_reports
        _stop.wait(0.25)  # info: _stop . wait ( 0.25 )


# ====================================================
# SECTION: function shutdown
# What it does: shutdown.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def shutdown(*_args) -> None:  # info: def shutdown
    _stop.set()  # info: _stop . set ( )
    _tunnel_ready.set()  # info: _tunnel_ready . set ( )
    global _tunnel_proc  # info: global _tunnel_proc
    if _tunnel_proc and _tunnel_proc.poll() is None:  # info: if _tunnel_proc and _tunnel_proc . poll ( )
        _tunnel_proc.terminate()  # info: _tunnel_proc . terminate ( )
        try:  # info: try :
            _tunnel_proc.wait(timeout=5)  # info: _tunnel_proc . wait ( timeout = 5 )
        except subprocess.TimeoutExpired:  # info: except subprocess . TimeoutExpired :
            _tunnel_proc.kill()  # info: _tunnel_proc . kill ( )


# ====================================================
# SECTION: function run_on_boot
# What it does: run on boot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_on_boot() -> None:  # info: def run_on_boot
    boot = [j for j in enabled_jobs(getattr(jobmod, "ON_BOOT", [])) if isinstance(j, dict)]  # info: set boot
    boot.sort(key=lambda j: int(j.get("priority", 100)))  # info: boot . sort ( key = lambda j
    log(f"{full_timestamp()}boot:start  jobs={len(boot)}")  # info: call log
    for j in boot:  # info: for j in boot :
        log(f"{full_timestamp()}boot:run  priority={j.get('priority', '?')}  id={j.get('id', '?')}")  # info: call log
        run_job(j)  # info: call run_job
    log(f"{full_timestamp()}boot:done")  # info: call log


# ====================================================
# SECTION: function main
# What it does: main. Schedule JSON owns timing when present; boot for that mode runs inside the scheduler after arm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    signal.signal(signal.SIGTERM, shutdown)  # info: signal . signal ( signal . SIGTERM ,
    signal.signal(signal.SIGINT, shutdown)  # info: signal . signal ( signal . SIGINT ,
    try:  # info: try
        import schedule_runtime as sch  # info: import schedule_runtime as sch
        schedule_owns = sch.schedule_active("pacific")  # info: set schedule_owns
        disconnected = sch.polling_disconnected("pacific")  # info: set disconnected
    except Exception:  # info: except Exception
        sch = None  # info: set sch
        schedule_owns = False  # info: set schedule_owns
        disconnected = False  # info: set disconnected
    server = ThreadingHTTPServer((HOST, PORT), Handler)  # info: set server
    threading.Thread(target=server.serve_forever, name="http", daemon=True).start()  # info: start http
    log(f"{full_timestamp()}HTTP listening on http://{HOST}:{PORT} (open access on bind)")  # info: call log
    if schedule_owns:  # info: schedule mode: boot waits for arm inside the loop
        if disconnected:  # info: if disconnected :
            log(f"{full_timestamp()}POLLING_DISCONNECTED — schedule mode idle until armed (jobs.py timing ignored)")  # info: call log
        else:  # info: else
            log(f"{full_timestamp()}schedule mode armed — jobs.py timing ignored")  # info: call log
        scheduler_loop()  # info: call scheduler_loop
        server.shutdown()  # info: server . shutdown ( )
        shutdown()  # info: call shutdown
        return 0  # info: return 0
    if disconnected:  # info: if disconnected :
        log(f"{full_timestamp()}POLLING_DISCONNECTED — skip boot jobs and do not arm the scheduler")  # info: call log
        scheduler_loop()  # info: idle loop only
        server.shutdown()  # info: server . shutdown ( )
        shutdown()  # info: call shutdown
        return 0  # info: return 0
    run_on_boot()  # info: call run_on_boot
    for j in enabled_jobs(getattr(jobmod, "ONCE_AT_START", [])):  # info: for j in enabled_jobs ( getattr ( jobmod
        run_job(j)  # info: call run_job
    scheduler_loop()  # info: call scheduler_loop
    server.shutdown()  # info: server . shutdown ( )
    shutdown()  # info: call shutdown
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
