#!/usr/bin/env python3
"""poller-dashboard.py — read-only, flicker-free status window for the rootserver poller.

# INFO — MUST HAVE (future agents), added 2026-09-29 (WO-SRV viewer fix):
# - READ-ONLY. Never starts, stops or restarts anything. Ctrl-C / window close /
#   SIGTERM exit THIS VIEWER ONLY; the poller stack keeps running.
#   (To stop the stack use Automations/scripts/stack/stop-poller-stack.sh.)
# - Survives stack reloads (stop-poller-stack kills only poller-watch.py), so the
#   window no longer flashes closed/open on every code pull.
# - Redraws in place (cursor-home + clear-to-EOL, alternate screen): no flicker.
# - Tails the log by re-reading its last 64 KB, so the hourly cut by
#   Energy/scripts/consolidate.py hours never freezes the view.
# - Errors inside a frame are shown in the footer; the viewer keeps running.
# Opened by poller/open-poller-window.sh (single instance). Bruce's poller-watch.py
# is unchanged and still available for a plain scrolling log view.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
import json  # info: import json
import os  # info: import os
import re  # info: import re
import shutil  # info: import shutil
import signal  # info: import signal
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent  # info: set HERE
DB = Path(os.environ.get("DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
LOG = Path(os.environ.get("POLLER_LOG", str(DB / "Logs/Automations/automations_current.log")))  # info: set LOG
ENERGY = Path(os.environ.get("ENERGY_ROOT", str(DB / "Energy")))  # info: set ENERGY
TZ = ZoneInfo("Pacific/Honolulu")  # info: set TZ
REFRESH = int(os.environ.get("POLLER_DASH_REFRESH", "5"))  # info: set REFRESH

E = "\033["  # info: set E
RST, BOLD, DIM = E + "0m", E + "1m", E + "2m"  # info: RST , BOLD , DIM = E +
GREEN, YELLOW, RED = E + "38;2;133;153;0m", E + "38;2;181;137;0m", E + "38;2;220;50;47m"  # info: GREEN , YELLOW , RED = E +
CYAN, BLUE, BASE0 = E + "38;2;42;161;152m", E + "38;2;38;139;210m", E + "38;2;131;148;150m"  # info: CYAN , BLUE , BASE0 = E +
WHITE, MAGENTA = E + "38;2;238;232;213m", E + "38;2;211;54;130m"  # info: WHITE , MAGENTA = E + "38;2;238;232;213m" ,
BG = E + "48;2;7;54;66m"  # info: set BG
ANSI = re.compile(r"\033\[[0-9;?]*[A-Za-z]")  # info: set ANSI

# Optional: reuse Bruce's colored line formatter + solar state (import only; no handlers run).
_pw = None  # info: set _pw
try:  # info: try :
    _spec = importlib.util.spec_from_file_location("poller_watch", HERE / "poller-watch.py")  # info: set _spec
    _pw = importlib.util.module_from_spec(_spec)  # info: set _pw
    _spec.loader.exec_module(_pw)  # type: ignore[union-attr]
except Exception:  # info: except Exception :
    _pw = None  # info: set _pw

# (label, systemd unit or None, scope, argv suffixes to count, expected count or None=any>=1)
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
    ("ollama", "ollama.service", "system", ("ollama",), None),  # info: call (
    ("tunnel", None, "", ("cloudflared",), None),  # info: call (
]  # info: ]


# ====================================================
# SECTION: function vis_len
# What it does: vis len.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def vis_len(s: str) -> int:  # info: def vis_len
    return len(ANSI.sub("", s))  # info: return len ( ANSI . sub ( ""


# ====================================================
# SECTION: function fit
# What it does: Truncate to visible width, keeping ANSI codes intact.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fit(s: str, width: int) -> str:  # info: def fit
    """Truncate to visible width, keeping ANSI codes intact."""  # info: """Truncate to visible width, keeping ANSI codes intact."""
    out, n, i = [], 0, 0  # info: out , n , i = [ ]
    while i < len(s):  # info: while i < len ( s ) :
        m = ANSI.match(s, i)  # info: set m
        if m:  # info: if m :
            out.append(m.group()); i = m.end(); continue  # info: out . append ( m . group (
        if n >= width:  # info: if n >= width :
            break  # info: break
        out.append(s[i]); n += 1; i += 1  # info: out . append ( s [ i ]
    return "".join(out) + RST  # info: return "" . join ( out ) +


# ====================================================
# SECTION: function proc_argvs
# What it does: proc argvs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def proc_argvs() -> list[list[str]]:  # info: def proc_argvs
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
            res.append([a.decode(errors="replace") for a in raw.split(b"\0") if a][:4])  # info: res . append ( [ a . decode
    return res  # info: return res


# ====================================================
# SECTION: function count
# What it does: count.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def count(argvs, suffixes) -> int:  # info: def count
    n = 0  # info: set n
    for argv in argvs:  # info: for argv in argvs :
        # only the interpreter/binary and its script args — never long shell -c strings
        if any(a.endswith(sfx) for a in argv[:3] for sfx in suffixes if len(a) < 400):  # info: if any ( a . endswith ( sfx
            n += 1  # info: set n
    return n  # info: return n


# ====================================================
# SECTION: function unit_active
# What it does: unit active.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def unit_active(unit: str, scope: str) -> str:  # info: def unit_active
    cmd = ["systemctl"] + (["--user"] if scope == "user" else []) + ["is-active", unit]  # info: set cmd
    try:  # info: try :
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout.strip() or "unknown"  # info: return subprocess . run ( cmd , capture_output
    except Exception:  # info: except Exception :
        return "unknown"  # info: return "unknown"


# ====================================================
# SECTION: function service_rows
# What it does: service rows.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def service_rows():  # info: def service_rows
    argvs = proc_argvs()  # info: set argvs
    rows = []  # info: set rows
    for label, unit, scope, sfx, expect in SERVICES:  # info: for label , unit , scope , sfx
        n = count(argvs, sfx)  # info: set n
        st = unit_active(unit, scope) if unit else None  # info: set st
        if st not in (None, "active") or n == 0:  # info: if st not in ( None , "active"
            state = "FAIL"  # info: set state
        elif expect is not None and n != expect:  # info: elif expect is not None and n !=
            state = "WARN"  # info: set state
        else:  # info: else :
            state = "PASS"  # info: set state
        detail = (f"unit {st}" if unit else "no unit") + f" · {n} proc"  # info: set detail
        rows.append((label, state, detail))  # info: rows . append ( ( label , state
    return rows  # info: return rows


# ====================================================
# SECTION: function read_json
# What it does: read json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_json(p: Path):  # info: def read_json
    try:  # info: try :
        return json.loads(p.read_text())  # info: return json . loads ( p . read_text
    except Exception:  # info: except Exception :
        return None  # info: return None


# ====================================================
# SECTION: function age_s
# What it does: age s.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def age_s(iso: str | None) -> float | None:  # info: def age_s
    try:  # info: try :
        return (datetime.now(TZ) - datetime.fromisoformat(iso)).total_seconds()  # type: ignore[arg-type]
    except Exception:  # info: except Exception :
        return None  # info: return None


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


# ====================================================
# SECTION: function bar
# What it does: bar.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def bar(pct: float | None, width: int = 24) -> str:  # info: def bar
    if pct is None:  # info: if pct is None :
        return f"{DIM}{'·' * width}{RST}   n/a"  # info: return f" { DIM } { '·' *
    pct = max(0.0, min(100.0, pct))  # info: set pct
    col = GREEN if pct >= 50 else YELLOW if pct >= 20 else RED  # info: set col
    full = int(round(pct / 100 * width))  # info: set full
    return f"{col}{'█' * full}{DIM}{'░' * (width - full)}{RST} {col}{BOLD}{pct:5.1f}%{RST}"  # info: return f" { col } { '█' *


# ====================================================
# SECTION: function summary_for
# What it does: summary for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def summary_for(lines, dev):  # info: def summary_for
    for ln in reversed(lines):  # info: for ln in reversed ( lines ) :
        if f"SUMMARY={dev} " in ln:  # info: if f" SUMMARY= { dev } "
            m = re.search(r"SUMMARY=\S+ (.*)", ln)  # info: set m
            return m.group(1) if m else ""  # info: return m . group ( 1 ) if
    return ""  # info: return ""


# ====================================================
# SECTION: function badge
# What it does: badge.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def badge(state: str) -> str:  # info: def badge
    col = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED}.get(state, BASE0)  # info: set col
    return f"{col}{BOLD}● {state:<4}{RST}"  # info: return f" { col } { BOLD }


# ====================================================
# SECTION: function build
# What it does: build.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build(snap, remaining: int, width: int, height: int) -> list[str]:  # info: def build
    now = datetime.now(TZ)  # info: set now
    L = []  # info: set L
    title = " RootRecord · Pacific Solar Server — rootserver poller "  # info: set title
    clock = now.strftime(" %A %d %b %Y  %H:%M:%S HST ")  # info: set clock
    pad = max(1, width - len(title) - len(clock))  # info: set pad
    L.append(f"{BG}{WHITE}{BOLD}{title}{' ' * pad}{CYAN}{clock}{RST}")  # info: L . append ( f" { BG }
    ref = "".join("■" if i < REFRESH - remaining else "□" for i in range(REFRESH))  # info: set ref
    L.append(f" {DIM}read-only viewer · refresh in {RST}{CYAN}{remaining}s{RST} {DIM}{ref}{RST}"  # info: L . append ( f" { DIM
             f"   {DIM}log:{RST} {BASE0}{LOG.name}{RST} {DIM}{snap['log_state']}{RST}")  # info: f" { DIM } log: { RST
    L.append(f" {DIM}{'─' * (width - 2)}{RST}")  # info: L . append ( f" { DIM
    rows = snap["services"]  # info: set rows
    half = (len(rows) + 1) // 2  # info: set half
    for i in range(half):  # info: for i in range ( half ) :
        cells = []  # info: set cells
        for r in (rows[i], rows[i + half] if i + half < len(rows) else None):  # info: for r in ( rows [ i ]
            if r:  # info: if r :
                cells.append(f"  {WHITE}{BOLD}{r[0]:<8}{RST}{badge(r[1])}  {DIM}{r[2]:<22}{RST}")  # info: cells . append ( f" { WHITE
        L.append("".join(cells))  # info: L . append ( "" . join (
    L.append(f" {DIM}{'─' * (width - 2)}{RST}")  # info: L . append ( f" { DIM
    for name, key, dev in (("B1", "b1", "river2pro"), ("B2", "b2", "delta2")):  # info: for name , key , dev in (
        soc, at = snap[key]  # info: soc , at = snap [ key ]
        a = age_s(at)  # info: set a
        age = f"{int(a // 60)}m{int(a % 60):02d}s ago" if a is not None else "no reading"  # info: set age
        stale = f" {YELLOW}stale{RST}" if a is not None and a > 900 else ""  # info: set stale
        L.append(f"  {WHITE}{BOLD}{name}{RST} {DIM}{dev:<9}{RST} {bar(soc)}  {DIM}{age}{RST}{stale}")  # info: L . append ( f" { WHITE
        s = snap["sum_" + key]  # info: set s
        if s:  # info: if s :
            L.append(f"     {DIM}{s}{RST}")  # info: L . append ( f" { DIM
    lap = snap.get("laptop")  # info: set lap
    if lap:  # info: if lap :
        pct, st, ac = lap  # info: pct , st , ac = lap
        src = f"{GREEN}AC{RST}" if ac else f"{YELLOW}on battery{RST}"  # info: set src
        L.append(f"  {WHITE}{BOLD}B3{RST} {DIM}{'laptop':<9}{RST} {bar(pct)}  {DIM}System (laptop) · {st}{RST} · {src}")  # info: L . append ( f" { WHITE
    if snap["system"]:  # info: if snap [ "system" ] :
        L.append(f"  {WHITE}{BOLD}SYS{RST} {DIM}{snap['system']}{RST}")  # info: L . append ( f" { WHITE
    if snap["solar"]:  # info: if snap [ "solar" ] :
        L.append(f"  {WHITE}{BOLD}SUN{RST} {DIM}{snap['solar']}{RST}")  # info: L . append ( f" { WHITE
    L.append(f" {DIM}{'─' * (width - 2)} {RST}")  # info: L . append ( f" { DIM
    L.append(f" {BLUE}{BOLD}recent poller log{RST}")  # info: L . append ( f" { BLUE
    footer = [f" {DIM}Ctrl-C / close = viewer only (poller keeps running) · stop stack: stack/stop-poller-stack.sh{RST}"]  # info: set footer
    if snap.get("error"):  # info: if snap . get ( "error" ) :
        footer.insert(0, f" {RED}viewer note: {snap['error']}{RST}")  # info: footer . insert ( 0 , f"
    room = max(0, height - len(L) - len(footer))  # info: set room
    L.extend(snap["log"][-room:] if room else [])  # info: L . extend ( snap [ "log" ]
    L.extend([""] * max(0, height - len(L) - len(footer)))  # info: L . extend ( [ "" ] *
    L.extend(footer)  # info: L . extend ( footer )
    return [fit(x, width) for x in L[:height]]  # info: return [ fit ( x , width )


# ====================================================
# SECTION: function laptop_battery
# What it does: System (laptop) battery from sysfs, read-only: (pct, status, on_ac) or None. 2026-09-29.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def laptop_battery():  # info: def laptop_battery
    """System (laptop) battery from sysfs, read-only: (pct, status, on_ac) or None. 2026-09-29."""  # info: """System (laptop) battery from sysfs, read-only: (pct, status, on_ac) or None. 2026-09-29."""
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
# SECTION: function snapshot
# What it does: snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def snapshot() -> dict:  # info: def snapshot
    snap = {"error": ""}  # info: set snap
    try:  # info: try :
        snap["services"] = service_rows()  # info: snap [ "services" ] = service_rows ( )
    except Exception as e:  # never die
        snap["services"], snap["error"] = [], f"services: {e}"  # info: snap [ "services" ] , snap [ "error"
    b1 = read_json(ENERGY / "soc/river2pro_current.json") or {}  # info: set b1
    b2 = read_json(ENERGY / "soc/delta2_current.json") or {}  # info: set b2
    snap["b1"] = (b1.get("soc"), b1.get("at"))  # info: snap [ "b1" ] = ( b1 .
    snap["b2"] = (b2.get("soc"), b2.get("at"))  # info: snap [ "b2" ] = ( b2 .
    snap["laptop"] = laptop_battery()  # info: snap [ "laptop" ] = laptop_battery ( )
    lines = tail_lines(LOG)  # info: set lines
    try:  # info: try :
        m = LOG.stat().st_mtime  # info: set m
        snap["log_state"] = f"{int(time.time() - m)}s since last write"  # info: snap [ "log_state" ] = f" { int
    except OSError:  # info: except OSError :
        snap["log_state"] = "missing"  # info: snap [ "log_state" ] = "missing"
    snap["sum_b1"], snap["sum_b2"] = summary_for(lines, "river2pro"), summary_for(lines, "delta2")  # info: snap [ "sum_b1" ] , snap [ "sum_b2"
    snap["system"] = ""  # info: snap [ "system" ] = ""
    for ln in reversed(lines):  # info: for ln in reversed ( lines ) :
        if "| SYSTEM " in ln:  # info: if "| SYSTEM " in ln :
            snap["system"] = re.sub(r"\s+", " ", ln.split("| SYSTEM", 1)[1]).strip()  # info: snap [ "system" ] = re . sub
            break  # info: break
    snap["solar"] = ""  # info: snap [ "solar" ] = ""
    if _pw is not None:  # info: if _pw is not None :
        try:  # info: try :
            snap["solar"] = _pw.aeyes_solar_state() or ""  # info: snap [ "solar" ] = _pw . aeyes_solar_state
        except Exception:  # info: except Exception :
            pass  # info: pass
    out = []  # info: set out
    for ln in lines[-200:]:  # info: for ln in lines [ - 200 :
        try:  # info: try :
            f = _pw.format_line(ln) if _pw is not None else f"  {DIM}{ln}{RST}"  # info: set f
        except Exception:  # info: except Exception :
            f = f"  {DIM}{ln}{RST}"  # info: set f
        if f:  # info: if f :
            out.append(f)  # info: out . append ( f )
    snap["log"] = out  # info: snap [ "log" ] = out
    return snap  # info: return snap


# ====================================================
# SECTION: function restore_and_exit
# What it does: restore and exit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def restore_and_exit(*_a) -> None:  # info: def restore_and_exit
    sys.stdout.write(E + "?25h" + E + "?1049l")  # info: sys . stdout . write ( E +
    sys.stdout.flush()  # info: sys . stdout . flush ( )
    os._exit(0)  # info: os . _exit ( 0 )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):  # info: for s in ( signal . SIGINT ,
        signal.signal(s, restore_and_exit)  # info: signal . signal ( s , restore_and_exit )
    sys.stdout.write("\033]0;RootRecord poller — rootserver\007" + E + "?1049h" + E + "?25l" + E + "2J")  # info: sys . stdout . write ( "\033]0;RootRecord poller — rootserver\007" +
    snap, next_at = None, 0.0  # info: snap , next_at = None , 0.0
    while True:  # info: while True :
        try:  # info: try :
            if snap is None or time.time() >= next_at:  # info: if snap is None or time . time
                snap = snapshot()  # info: set snap
                next_at = time.time() + REFRESH  # info: set next_at
            size = shutil.get_terminal_size((100, 36))  # info: set size
            frame = build(snap, max(0, int(round(next_at - time.time()))), size.columns, size.lines)  # info: set frame
            sys.stdout.write(E + "H" + (E + "K\n").join(frame) + E + "K" + E + "J")  # info: sys . stdout . write ( E +
            sys.stdout.flush()  # info: sys . stdout . flush ( )
        except Exception as e:  # keep the window alive; show the problem instead of exiting
            try:  # info: try :
                sys.stdout.write(E + "H" + E + "2J" + f"viewer error (retrying): {e}\n")  # info: sys . stdout . write ( E +
                sys.stdout.flush()  # info: sys . stdout . flush ( )
            except Exception:  # info: except Exception :
                pass  # info: pass
            snap = None  # info: set snap
        time.sleep(1)  # info: time . sleep ( 1 )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
