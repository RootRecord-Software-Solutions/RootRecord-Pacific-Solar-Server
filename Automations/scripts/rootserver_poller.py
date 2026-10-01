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
_tunnel_ready = threading.Event()  # info: set _tunnel_ready
_tunnel_proc: subprocess.Popen | None = None  # info: set _tunnel_proc
_internet_ok = False  # info: set _internet_ok
_internet_last_log = 0.0  # info: set _internet_last_log
_tunnel_start_attempts = 0  # info: set _tunnel_start_attempts


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
    delta_soc = _read_energy_json("soc/delta2-last.json")  # info: set delta_soc
    river_soc = _read_energy_json("soc/river2pro-last.json")  # info: set river_soc
    delta_w = _read_energy_json("watts/delta2-last.json")  # info: set delta_w
    river_w = _read_energy_json("watts/river2pro-last.json")  # info: set river_w

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
    solar = watt_of(delta_sql, "solar_input_power", delta_w)  # info: set solar
    if solar is None:  # info: if solar is None :
        solar = watt_of(river_sql, "solar_input_power", river_w)  # info: set solar
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
    parts = [f"status={snap.get('status')}", f"B2={snap.get('deltaSoc')}", f"B1={snap.get('riverSoc')}",  # info: set parts
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
        """Reverse-proxy /aeyes* to local a-eyes cam server (127.0.0.1:8791)."""  # info: """Reverse-proxy /aeyes* to local a-eyes cam server (127.0.0.1:8791)."""
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
        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)  # info: set req
        try:  # info: try :
            with urllib.request.urlopen(req, timeout=45) as resp:  # info: with urllib . request . urlopen ( req
                data = resp.read()  # info: set data
                self.send_response(resp.status)  # info: self . send_response ( resp . status )
                for key in ("Content-Type", "Set-Cookie", "Location", "Cache-Control"):  # info: for key in ( "Content-Type" , "Set-Cookie" ,
                    val = resp.headers.get(key)  # info: set val
                    if val:  # info: if val :
                        self.send_header(key, val)  # info: self . send_header ( key , val )
                self.send_header("Content-Length", str(len(data)))  # info: self . send_header ( "Content-Length" , str (
                self.end_headers()  # info: self . end_headers ( )
                self.wfile.write(data)  # info: self . wfile . write ( data )
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
        self._send(404, "not found\n")  # info: self . _send ( 404 , "not found\n" )


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
        r = subprocess.run(["bash", "-lc", cmd], cwd=cwd, env=env, timeout=timeout, capture_output=True, text=True)  # info: set r
        out = (r.stdout or "").strip()  # info: set out
        err = (r.stderr or "").strip()  # info: set err
        if r.returncode == 0:  # info: if r . returncode == 0 :
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
                    log(f"{full_timestamp()}  ✗  {jid} FAIL code={r.returncode}")  # info: call log
            else:  # info: else :
                log(f"{full_timestamp()}job:{jid} FAIL code={r.returncode}")  # info: call log
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
    log(f"{full_timestamp()}job:{jid} UNKNOWN builtin={name!r}")  # info: call log


# ====================================================
# SECTION: function run_job
# What it does: run job.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_job(job: dict) -> None:  # info: def run_job
    if not _job_on(job):  # info: if not _job_on ( job )
        return  # info: return
    # After SIGTERM, start no new jobs (the rest of the scheduler pass used to re-launch the tunnel and
    # wait 45 s for it, so every stop hit TimeoutStopSec=30 + SIGKILL). 2026-09-29.
    if _stop.is_set():  # info: if _stop . is_set ( ) :
        return  # info: return
    if job.get("needs_internet") and not internet_ok(force=True):  # info: if job . get ( "needs_internet" ) and
        log(f"{full_timestamp()}job:{job.get('id', '?')} SKIP — offline (will retry when internet is up)")  # info: call log
        return  # info: return
    if NIGHT_SLEEP_GATE and _night_sleep is not None:  # info: if NIGHT_SLEEP_GATE and _night_sleep is not None :
        jid = str(job.get("id") or "")  # info: set jid
        try:  # info: try :
            allowed = _night_sleep.should_run(jid, enabled=True)  # info: set allowed
        except Exception:  # info: except Exception :
            allowed = True  # info: set allowed
        if not allowed:  # info: if not allowed :
            log(f"{full_timestamp()}job:{jid} SKIP — night sleep")  # info: call log
            return  # info: return
    builtin = (job.get("builtin") or "").strip()  # info: set builtin
    if builtin:  # info: if builtin :
        run_builtin(job)  # info: call run_builtin
        return  # info: return
    run_command_job(job)  # info: call run_command_job


# ====================================================
# SECTION: function _job_on
# What it does: True when the override file, or else the jobs.py flag, says this job should run. Fail open to the jobs.py flag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _job_on(job: dict) -> bool:  # info: def _job_on
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
# SECTION: function _scheduled_jobs
# What it does: The four repeating lists, filtered by the current override file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _scheduled_jobs() -> tuple:  # info: def _scheduled_jobs
    return (  # info: return (
        enabled_jobs(getattr(jobmod, "EVERY_SECONDS", [])),  # info: enabled_jobs ( getattr ( jobmod , "EVERY_SECONDS" , [ ] ) ) ,
        enabled_jobs(getattr(jobmod, "EVERY_MINUTE", [])),  # info: enabled_jobs ( getattr ( jobmod , "EVERY_MINUTE" , [ ] ) ) ,
        enabled_jobs(getattr(jobmod, "EVERY_HOUR", [])),  # info: enabled_jobs ( getattr ( jobmod , "EVERY_HOUR" , [ ] ) ) ,
        enabled_jobs(getattr(jobmod, "ON_AT", [])),  # info: enabled_jobs ( getattr ( jobmod , "ON_AT" , [ ] ) ) ,
    )  # info: )


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
# SECTION: function scheduler_loop
# What it does: scheduler loop. Reloads job overrides when that file changes, and starts due power schedules. A job that runs across a minute still fires the jobs for each minute it crossed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def scheduler_loop() -> None:  # info: def scheduler_loop
    sec_jobs, min_jobs, hour_jobs, at_jobs = _scheduled_jobs()  # info: sec_jobs , min_jobs , hour_jobs , at_jobs = _scheduled_jobs ( )
    next_due: dict[str, float] = {}  # info: set next_due
    now = time.monotonic()  # info: set now
    for j in sec_jobs:  # info: for j in sec_jobs :
        next_due[j["id"]] = now  # info: next_due [ j [ "id" ] ] =
    last_minute: int | None = None  # info: set last_minute
    last_hour: int | None = None  # info: set last_hour
    last_slot: datetime | None = None  # info: set last_slot
    fired_at: set[str] = set()  # info: set fired_at
    log(f"{full_timestamp()}scheduler  every_seconds={len(sec_jobs)}  every_minute={len(min_jobs)}  every_hour={len(hour_jobs)}  on_at={len(at_jobs)}")  # info: call log
    ov_stamp = actl.overrides_mtime() if actl is not None else None  # info: set ov_stamp
    _kick_power(datetime.now().astimezone())  # info: call _kick_power
    _kick_service(datetime.now().astimezone())  # info: call _kick_service
    while not _stop.is_set():  # info: while not _stop . is_set ( ) :
        if actl is not None:  # info: if actl is not None
            stamp = actl.overrides_mtime()  # info: set stamp
            if stamp != ov_stamp:  # info: if stamp != ov_stamp
                ov_stamp = stamp  # info: set ov_stamp
                sec_jobs, min_jobs, hour_jobs, at_jobs = _scheduled_jobs()  # info: sec_jobs , min_jobs , hour_jobs , at_jobs = _scheduled_jobs ( )
                for j in sec_jobs:  # info: for j in sec_jobs
                    next_due.setdefault(j["id"], time.monotonic())  # info: next_due . setdefault ( j [ "id" ] , time . monotonic ( ) )
        wall = datetime.now().astimezone()  # info: set wall
        mono = time.monotonic()  # info: set mono
        for j in sec_jobs:  # info: for j in sec_jobs :
            jid = j["id"]  # info: set jid
            if mono >= next_due.get(jid, 0):  # info: if mono >= next_due . get ( jid
                run_job(j)  # info: call run_job
                interval = float(j.get("interval_sec") or INTERVAL_FALLBACK)  # info: set interval
                next_due[jid] = time.monotonic() + max(0.2, interval)  # info: next_due [ jid ] = time . monotonic ( ) + max
        wall = datetime.now().astimezone()  # info: set wall
        minute, hour = wall.minute, wall.hour  # info: minute , hour = wall . minute ,
        day = wall.date().isoformat()  # info: set day
        slot = wall.replace(second=0, microsecond=0)  # info: set slot
        if last_slot is None:  # info: if last_slot is None :
            last_minute, last_hour, last_slot = minute, hour, slot  # info: last_minute , last_hour , last_slot = minute , hour , slot
        elif slot < last_slot:  # info: elif slot < last_slot :
            last_minute, last_hour, last_slot = minute, hour, slot  # info: last_minute , last_hour , last_slot = minute , hour , slot
        elif slot != last_slot:  # info: elif slot != last_slot :
            for step in crossed_slots(last_slot, slot):  # info: for step in crossed_slots ( last_slot , slot )
                _kick_power(step)  # info: call _kick_power
                _kick_service(step)  # info: call _kick_service
                hm_step = f"{step.hour:02d}:{step.minute:02d}"  # info: set hm_step
                for j in min_jobs:  # info: for j in min_jobs :
                    only = j.get("only_at_minutes") or []  # info: set only
                    if only and step.minute not in only:  # info: if only and step . minute not in only :
                        continue  # info: continue
                    run_job(j)  # info: call run_job
                for j in at_jobs:  # info: for j in at_jobs :
                    times = {t for raw in (j.get("at_times") or []) if (t := _normalize_hhmm(raw))}  # info: set times
                    if hm_step not in times:  # info: if hm_step not in times :
                        continue  # info: continue
                    key = f"{j['id']}|{step.date().isoformat()}|{hm_step}"  # info: set key
                    if key in fired_at:  # info: if key in fired_at :
                        continue  # info: continue
                    run_job(j)  # info: call run_job
                    fired_at.add(key)  # info: fired_at . add ( key )
                if step.minute == 0:  # info: if step . minute == 0 :
                    for j in hour_jobs:  # info: for j in hour_jobs :
                        only_h = j.get("only_at_hours") or []  # info: set only_h
                        if only_h and step.hour not in only_h:  # info: if only_h and step . hour not in only_h :
                            continue  # info: continue
                        run_job(j)  # info: call run_job
                    last_hour = step.hour  # info: set last_hour
            last_minute, last_slot = minute, slot  # info: last_minute , last_slot = minute , slot
            if fired_at:  # info: if fired_at :
                fired_at = {k for k in fired_at if f"|{day}|" in k}  # info: set fired_at
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
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    signal.signal(signal.SIGTERM, shutdown)  # info: signal . signal ( signal . SIGTERM ,
    signal.signal(signal.SIGINT, shutdown)  # info: signal . signal ( signal . SIGINT ,
    server = ThreadingHTTPServer((HOST, PORT), Handler)  # info: set server
    threading.Thread(target=server.serve_forever, name="http", daemon=True).start()  # info: threading . Thread ( target = server .
    log(f"{full_timestamp()}HTTP listening on http://{HOST}:{PORT} (open access on bind)")  # info: call log
    run_on_boot()  # info: call run_on_boot
    for j in enabled_jobs(getattr(jobmod, "ONCE_AT_START", [])):  # info: for j in enabled_jobs ( getattr ( jobmod
        run_job(j)  # info: call run_job
    scheduler_loop()  # info: call scheduler_loop
    server.shutdown()  # info: server . shutdown ( )
    shutdown()  # info: call shutdown
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
