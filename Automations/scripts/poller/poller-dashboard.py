#!/usr/bin/env python3
"""poller-dashboard.py — read-only, flicker-free status window for the rootserver poller.

# INFO — MUST HAVE (future agents), added 2026-09-29 (WO-SRV viewer fix):
# - READ-ONLY. Never starts, stops or restarts anything. Ctrl-C / window close /
#   SIGTERM exit THIS VIEWER ONLY; the poller stack keeps running.
#   (To stop the stack use Automations/scripts/stack/stop-poller-stack.sh.)
# - Survives stack reloads (stop-poller-stack kills only poller-watch.py), so the
#   window no longer flashes closed/open on every code pull.
# - Redraws in place (cursor-home + clear-to-EOL, alternate screen): no flicker.
# - Tails the log by re-reading its last 64 KB, so the hourly truncation by
#   archive_automations_log_hourly.sh never freezes the view.
# - Errors inside a frame are shown in the footer; the viewer keeps running.
# Opened by poller/open-poller-window.sh (single instance). Bruce's poller-watch.py
# is unchanged and still available for a plain scrolling log view.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
DB = Path(os.environ.get("DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
LOG = Path(os.environ.get("POLLER_LOG", str(DB / "Logs/Automations/automations_current.log")))
ENERGY = Path(os.environ.get("ENERGY_ROOT", str(DB / "Energy")))
TZ = ZoneInfo("Pacific/Honolulu")
REFRESH = int(os.environ.get("POLLER_DASH_REFRESH", "5"))

E = "\033["
RST, BOLD, DIM = E + "0m", E + "1m", E + "2m"
GREEN, YELLOW, RED = E + "38;2;133;153;0m", E + "38;2;181;137;0m", E + "38;2;220;50;47m"
CYAN, BLUE, BASE0 = E + "38;2;42;161;152m", E + "38;2;38;139;210m", E + "38;2;131;148;150m"
WHITE, MAGENTA = E + "38;2;238;232;213m", E + "38;2;211;54;130m"
BG = E + "48;2;7;54;66m"
ANSI = re.compile(r"\033\[[0-9;?]*[A-Za-z]")

# Optional: reuse Bruce's colored line formatter + solar state (import only; no handlers run).
_pw = None
try:
    _spec = importlib.util.spec_from_file_location("poller_watch", HERE / "poller-watch.py")
    _pw = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_pw)  # type: ignore[union-attr]
except Exception:
    _pw = None

# (label, systemd unit or None, scope, argv suffixes to count, expected count or None=any>=1)
SERVICES = [
    ("poller", "rr-rootserver-poller.service", "user", ("Automations/scripts/rootserver_poller.py",), 1),
    ("relay", None, "", ("telegram/scripts/council-relay.py",), 1),
    ("BLE", "ava-ecoflow-ble.service", "user", ("scripts/ble/ble-owner.py",), 1),
    ("globe", "network-globe-hawaii.service", "user", ("local-data-globe/collector.js",), 1),
    ("cam", None, "", ("cam_server.py",), 1),
    ("weather", None, "", ("Weather/scripts/run_poller.py", "weather/scripts/run_poller.py"), 1),
    ("ollama", "ollama.service", "system", ("ollama",), None),
    ("tunnel", None, "", ("cloudflared",), None),
]


def vis_len(s: str) -> int:
    return len(ANSI.sub("", s))


def fit(s: str, width: int) -> str:
    """Truncate to visible width, keeping ANSI codes intact."""
    out, n, i = [], 0, 0
    while i < len(s):
        m = ANSI.match(s, i)
        if m:
            out.append(m.group()); i = m.end(); continue
        if n >= width:
            break
        out.append(s[i]); n += 1; i += 1
    return "".join(out) + RST


def proc_argvs() -> list[list[str]]:
    me = {os.getpid(), os.getppid()}
    res = []
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) in me:
            continue
        try:
            raw = Path(f"/proc/{d}/cmdline").read_bytes()
        except OSError:
            continue
        if raw:
            res.append([a.decode(errors="replace") for a in raw.split(b"\0") if a][:4])
    return res


def count(argvs, suffixes) -> int:
    n = 0
    for argv in argvs:
        # only the interpreter/binary and its script args — never long shell -c strings
        if any(a.endswith(sfx) for a in argv[:3] for sfx in suffixes if len(a) < 400):
            n += 1
    return n


def unit_active(unit: str, scope: str) -> str:
    cmd = ["systemctl"] + (["--user"] if scope == "user" else []) + ["is-active", unit]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def service_rows():
    argvs = proc_argvs()
    rows = []
    for label, unit, scope, sfx, expect in SERVICES:
        n = count(argvs, sfx)
        st = unit_active(unit, scope) if unit else None
        if st not in (None, "active") or n == 0:
            state = "FAIL"
        elif expect is not None and n != expect:
            state = "WARN"
        else:
            state = "PASS"
        detail = (f"unit {st}" if unit else "no unit") + f" · {n} proc"
        rows.append((label, state, detail))
    return rows


def read_json(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def age_s(iso: str | None) -> float | None:
    try:
        return (datetime.now(TZ) - datetime.fromisoformat(iso)).total_seconds()  # type: ignore[arg-type]
    except Exception:
        return None


def tail_lines(path: Path, nbytes: int = 65536) -> list[str]:
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - nbytes))
            data = f.read().decode("utf-8", errors="replace")
        lines = data.splitlines()
        return lines[1:] if size > nbytes else lines
    except OSError:
        return []


def bar(pct: float | None, width: int = 24) -> str:
    if pct is None:
        return f"{DIM}{'·' * width}{RST}   n/a"
    pct = max(0.0, min(100.0, pct))
    col = GREEN if pct >= 50 else YELLOW if pct >= 20 else RED
    full = int(round(pct / 100 * width))
    return f"{col}{'█' * full}{DIM}{'░' * (width - full)}{RST} {col}{BOLD}{pct:5.1f}%{RST}"


def summary_for(lines, dev):
    for ln in reversed(lines):
        if f"SUMMARY={dev} " in ln:
            m = re.search(r"SUMMARY=\S+ (.*)", ln)
            return m.group(1) if m else ""
    return ""


def badge(state: str) -> str:
    col = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED}.get(state, BASE0)
    return f"{col}{BOLD}● {state:<4}{RST}"


def build(snap, remaining: int, width: int, height: int) -> list[str]:
    now = datetime.now(TZ)
    L = []
    title = " RootRecord · Pacific Solar Server — rootserver poller "
    clock = now.strftime(" %a %d %b %Y  %H:%M:%S HST ")
    pad = max(1, width - len(title) - len(clock))
    L.append(f"{BG}{WHITE}{BOLD}{title}{' ' * pad}{CYAN}{clock}{RST}")
    ref = "".join("■" if i < REFRESH - remaining else "□" for i in range(REFRESH))
    L.append(f" {DIM}read-only viewer · refresh in {RST}{CYAN}{remaining}s{RST} {DIM}{ref}{RST}"
             f"   {DIM}log:{RST} {BASE0}{LOG.name}{RST} {DIM}{snap['log_state']}{RST}")
    L.append(f" {DIM}{'─' * (width - 2)}{RST}")
    rows = snap["services"]
    half = (len(rows) + 1) // 2
    for i in range(half):
        cells = []
        for r in (rows[i], rows[i + half] if i + half < len(rows) else None):
            if r:
                cells.append(f"  {WHITE}{BOLD}{r[0]:<8}{RST}{badge(r[1])}  {DIM}{r[2]:<22}{RST}")
        L.append("".join(cells))
    L.append(f" {DIM}{'─' * (width - 2)}{RST}")
    for name, key, dev in (("B1", "b1", "river2pro"), ("B2", "b2", "delta2")):
        soc, at = snap[key]
        a = age_s(at)
        age = f"{int(a // 60)}m{int(a % 60):02d}s ago" if a is not None else "no reading"
        stale = f" {YELLOW}stale{RST}" if a is not None and a > 900 else ""
        L.append(f"  {WHITE}{BOLD}{name}{RST} {DIM}{dev:<9}{RST} {bar(soc)}  {DIM}{age}{RST}{stale}")
        s = snap["sum_" + key]
        if s:
            L.append(f"     {DIM}{s}{RST}")
    lap = snap.get("laptop")
    if lap:
        pct, st, ac = lap
        src = f"{GREEN}AC{RST}" if ac else f"{YELLOW}on battery{RST}"
        L.append(f"  {WHITE}{BOLD}B3{RST} {DIM}{'laptop':<9}{RST} {bar(pct)}  {DIM}System (laptop) · {st}{RST} · {src}")
    if snap["system"]:
        L.append(f"  {WHITE}{BOLD}SYS{RST} {DIM}{snap['system']}{RST}")
    if snap["solar"]:
        L.append(f"  {WHITE}{BOLD}SUN{RST} {DIM}{snap['solar']}{RST}")
    L.append(f" {DIM}{'─' * (width - 2)} {RST}")
    L.append(f" {BLUE}{BOLD}recent poller log{RST}")
    footer = [f" {DIM}Ctrl-C / close = viewer only (poller keeps running) · stop stack: stack/stop-poller-stack.sh{RST}"]
    if snap.get("error"):
        footer.insert(0, f" {RED}viewer note: {snap['error']}{RST}")
    room = max(0, height - len(L) - len(footer))
    L.extend(snap["log"][-room:] if room else [])
    L.extend([""] * max(0, height - len(L) - len(footer)))
    L.extend(footer)
    return [fit(x, width) for x in L[:height]]


def laptop_battery():
    """System (laptop) battery from sysfs, read-only: (pct, status, on_ac) or None. 2026-09-29."""
    try:
        ps = Path("/sys/class/power_supply")
        bat = next((b for b in sorted(ps.glob("BAT*")) if (b / "capacity").exists()), None)
        if bat is None:
            return None
        ac = any((m / "online").read_text().strip() == "1" for m in ps.iterdir()
                 if (m / "type").exists() and (m / "type").read_text().strip() == "Mains" and (m / "online").exists())
        return (float((bat / "capacity").read_text().strip()), (bat / "status").read_text().strip(), ac)
    except Exception:
        return None


def snapshot() -> dict:
    snap = {"error": ""}
    try:
        snap["services"] = service_rows()
    except Exception as e:  # never die
        snap["services"], snap["error"] = [], f"services: {e}"
    b1 = read_json(ENERGY / "soc/river2pro-last.json") or {}
    b2 = read_json(ENERGY / "soc/delta2-last.json") or {}
    snap["b1"] = (b1.get("soc"), b1.get("at"))
    snap["b2"] = (b2.get("soc"), b2.get("at"))
    snap["laptop"] = laptop_battery()
    lines = tail_lines(LOG)
    try:
        m = LOG.stat().st_mtime
        snap["log_state"] = f"{int(time.time() - m)}s since last write"
    except OSError:
        snap["log_state"] = "missing"
    snap["sum_b1"], snap["sum_b2"] = summary_for(lines, "river2pro"), summary_for(lines, "delta2")
    snap["system"] = ""
    for ln in reversed(lines):
        if "| SYSTEM " in ln:
            snap["system"] = re.sub(r"\s+", " ", ln.split("| SYSTEM", 1)[1]).strip()
            break
    snap["solar"] = ""
    if _pw is not None:
        try:
            snap["solar"] = _pw.aeyes_solar_state() or ""
        except Exception:
            pass
    out = []
    for ln in lines[-200:]:
        try:
            f = _pw.format_line(ln) if _pw is not None else f"  {DIM}{ln}{RST}"
        except Exception:
            f = f"  {DIM}{ln}{RST}"
        if f:
            out.append(f)
    snap["log"] = out
    return snap


def restore_and_exit(*_a) -> None:
    sys.stdout.write(E + "?25h" + E + "?1049l")
    sys.stdout.flush()
    os._exit(0)


def main() -> None:
    for s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, restore_and_exit)
    sys.stdout.write("\033]0;RootRecord poller — rootserver\007" + E + "?1049h" + E + "?25l" + E + "2J")
    snap, next_at = None, 0.0
    while True:
        try:
            if snap is None or time.time() >= next_at:
                snap = snapshot()
                next_at = time.time() + REFRESH
            size = shutil.get_terminal_size((100, 36))
            frame = build(snap, max(0, int(round(next_at - time.time()))), size.columns, size.lines)
            sys.stdout.write(E + "H" + (E + "K\n").join(frame) + E + "K" + E + "J")
            sys.stdout.flush()
        except Exception as e:  # keep the window alive; show the problem instead of exiting
            try:
                sys.stdout.write(E + "H" + E + "2J" + f"viewer error (retrying): {e}\n")
                sys.stdout.flush()
            except Exception:
                pass
            snap = None
        time.sleep(1)


if __name__ == "__main__":
    main()
