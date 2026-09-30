# ==============================================================================
# FILE: System/scripts/host_desks.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Host network + security desk facts (G3 port of G1 host-metrics/scripts/host_metrics.py, 2026-09-29).

  python3 host_desks.py net-sample     append one byte-counter sample (default route iface) -> Database System/network/
  python3 host_desks.py net-usage      print last-hour / last-24h byte deltas (None until enough samples exist)
  python3 host_desks.py security       print + write the security snapshot (counts only) -> Database System/security/

Ported unchanged: net_counters / _skip_iface / default_net_iface / net_usage_window / spoken_bytes / _auth_fail_counts /
_ufw_start_on_boot / _unit_active / _listen_established / security_snapshot. Changed: G1 appended to one rolling
host-net.jsonl and trimmed it past 1.5 MB; G3 appends to Daily/net-YYYYMMDD.jsonl (git-ignored) and never deletes.
Security output is counts and booleans only (no auth-log lines, no IPs, no usernames). Uses psutil if present, else /proc.
Read-only on the host: reads /proc, /etc/ufw/ufw.conf, /var/log/auth.log (adm group), `systemctl is-active`.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import shutil  # info: import shutil
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
NET = DB / "System" / "network"  # info: set NET
SEC = DB / "System" / "security"  # info: set SEC

_NET_SKIP = ("lo", "docker", "veth", "br-", "virbr", "tun", "tap", "wg")  # info: set _NET_SKIP
_AUTH_FAIL = re.compile(r"failed password|invalid user|failed publickey|authentication failure", re.I)  # info: set _AUTH_FAIL
_AUTH_LOGS = (Path("/var/log/auth.log"), Path("/var/log/auth.log.1"))  # info: set _AUTH_LOGS

try:  # info: try :
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None  # info: set psutil


# ====================================================
# SECTION: function _skip_iface
# What it does:  skip iface.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _skip_iface(name: str) -> bool:  # info: def _skip_iface
    n = (name or "").lower()  # info: set n
    return n == "lo" or any(n.startswith(p) for p in _NET_SKIP)  # info: return n == "lo" or any ( n


# ====================================================
# SECTION: function default_net_iface
# What it does: default net iface.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def default_net_iface() -> str | None:  # info: def default_net_iface
    try:  # info: try :
        lines = Path("/proc/net/route").read_text(encoding="utf-8", errors="replace").splitlines()[1:]  # info: set lines
    except OSError:  # info: except OSError :
        return None  # info: return None
    for line in lines:  # info: for line in lines :
        parts = line.split()  # info: set parts
        if len(parts) >= 2 and parts[1] == "00000000" and not _skip_iface(parts[0]):  # info: if len ( parts ) >= 2 and
            return parts[0]  # info: return parts [ 0 ]
    return None  # info: return None


# ====================================================
# SECTION: function _proc_net_dev
# What it does:  proc net dev.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _proc_net_dev() -> dict[str, tuple[int, int]]:  # info: def _proc_net_dev
    out = {}  # info: set out
    try:  # info: try :
        for line in Path("/proc/net/dev").read_text(encoding="utf-8").splitlines()[2:]:  # info: for line in Path ( "/proc/net/dev" ) .
            name, rest = line.split(":", 1)  # info: name , rest = line . split (
            f = rest.split()  # info: set f
            out[name.strip()] = (int(f[0]), int(f[8]))  # info: out [ name . strip ( ) ]
    except (OSError, ValueError, IndexError):  # info: except ( OSError , ValueError , IndexError )
        pass  # info: pass
    return out  # info: return out


# ====================================================
# SECTION: function net_counters
# What it does: Wi-Fi / Ethernet byte counters. Skip loopback and virtual bridges.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def net_counters() -> dict[str, Any] | None:  # info: def net_counters
    """Wi-Fi / Ethernet byte counters. Skip loopback and virtual bridges."""  # info: """Wi-Fi / Ethernet byte counters. Skip loopback and virtual bridges."""
    pernic = _proc_net_dev()  # info: set pernic
    iface = default_net_iface()  # info: set iface
    if iface not in pernic:  # info: if iface not in pernic :
        named = [n for n in pernic if not _skip_iface(n)]  # info: set named
        iface = named[0] if named else None  # info: set iface
    if not iface or iface not in pernic:  # info: if not iface or iface not in pernic
        return None  # info: return None
    rx, tx = pernic[iface]  # info: rx , tx = pernic [ iface ]
    return {"iface": iface, "link": "wireless" if iface.startswith(("wl", "wlan")) else "wired",  # info: return { "iface" : iface , "link" :
            "rx": rx, "tx": tx, "at": int(time.time() * 1000)}  # info: "rx" : rx , "tx" : tx ,


# ====================================================
# SECTION: function _daily
# What it does:  daily.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _daily(day: datetime) -> Path:  # info: def _daily
    return NET / "Daily" / f"net-{day.strftime('%Y%m%d')}.jsonl"  # info: return NET / "Daily" / f" net- {


# ====================================================
# SECTION: function append_net_sample
# What it does: append net sample.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def append_net_sample(net: dict[str, Any]) -> Path:  # info: def append_net_sample
    path = _daily(datetime.now())  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    rec = {"at": int(net["at"]), "iface": net["iface"], "rx": int(net["rx"]), "tx": int(net["tx"])}  # info: set rec
    with path.open("a", encoding="utf-8") as fh:  # info: with path . open ( "a" , encoding
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")  # info: fh . write ( json . dumps (
    return path  # info: return path


# ====================================================
# SECTION: function load_net_rows
# What it does: load net rows.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_net_rows() -> list[dict[str, Any]]:  # info: def load_net_rows
    out: list[dict[str, Any]] = []  # info: set out
    today = datetime.now()  # info: set today
    for day in (today - timedelta(days=1), today):  # info: for day in ( today - timedelta (
        p = _daily(day)  # info: set p
        if not p.is_file():  # info: if not p . is_file ( ) :
            continue  # info: continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():  # info: for line in p . read_text ( encoding
            try:  # info: try :
                row = json.loads(line)  # info: set row
                out.append({"at": int(row["at"]), "iface": str(row.get("iface") or ""), "rx": int(row["rx"]), "tx": int(row["tx"])})  # info: out . append ( { "at" : int
            except (ValueError, KeyError, TypeError):  # info: except ( ValueError , KeyError , TypeError )
                continue  # info: continue
    out.sort(key=lambda r: r["at"])  # info: out . sort ( key = lambda r
    return out  # info: return out


# ====================================================
# SECTION: function _row_at_or_before
# What it does:  row at or before.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _row_at_or_before(rows, target_ms):  # info: def _row_at_or_before
    prev = None  # info: set prev
    for row in rows:  # info: for row in rows :
        if int(row["at"]) <= target_ms:  # info: if int ( row [ "at" ] )
            prev = row  # info: set prev
        else:  # info: else :
            break  # info: break
    return prev  # info: return prev


# ====================================================
# SECTION: function net_usage_window
# What it does: Byte delta for a lookback window. None until enough live samples exist. (G1, unchanged.)
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def net_usage_window(seconds: int, *, now: dict | None = None, rows: list | None = None, min_cover: float = 0.75):  # info: def net_usage_window
    """Byte delta for a lookback window. None until enough live samples exist. (G1, unchanged.)"""  # info: """Byte delta for a lookback window. None until enough live samples exist. (G1, unchanged.)"""
    now = now or net_counters()  # info: set now
    if not now:  # info: if not now :
        return None  # info: return None
    series = rows if rows is not None else load_net_rows()  # info: set series
    if not series:  # info: if not series :
        return None  # info: return None
    now_at = int(now["at"])  # info: set now_at
    need_ms = int(seconds * min_cover * 1000)  # info: set need_ms
    then = _row_at_or_before(series, now_at - int(seconds * 1000))  # info: set then
    if then is None:  # info: if then is None :
        oldest = series[0]  # info: set oldest
        if now_at - int(oldest["at"]) < need_ms:  # info: if now_at - int ( oldest [ "at"
            return None  # info: return None
        then = oldest  # info: set then
    cover_ms = now_at - int(then["at"])  # info: set cover_ms
    if cover_ms < need_ms:  # info: if cover_ms < need_ms :
        return None  # info: return None
    if now["iface"] and then.get("iface") and now["iface"] != then["iface"]:  # info: if now [ "iface" ] and then .
        return None  # info: return None
    rx, tx = int(now["rx"]) - int(then["rx"]), int(now["tx"]) - int(then["tx"])  # info: rx , tx = int ( now [
    if rx < 0 or tx < 0:  # info: if rx < 0 or tx < 0
        return None  # info: return None
    return {"seconds": int(cover_ms / 1000), "rx": rx, "tx": tx, "total": rx + tx, "iface": now.get("iface"), "link": now.get("link")}  # info: return { "seconds" : int ( cover_ms /


# ====================================================
# SECTION: function spoken_bytes
# What it does: spoken bytes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spoken_bytes(n: int) -> str:  # info: def spoken_bytes
    n = max(0, int(n))  # info: set n
    if n < 1024:  # info: if n < 1024 :
        return f"{n} bytes"  # info: return f" { n } bytes "
    kb = n / 1024.0  # info: set kb
    if kb < 1024:  # info: if kb < 1024 :
        return f"{kb:.1f} kilobytes"  # info: return f" { kb : .1f } kilobytes
    mb = kb / 1024.0  # info: set mb
    if mb < 1024:  # info: if mb < 1024 :
        return f"{mb:.1f} megabytes"  # info: return f" { mb : .1f } megabytes
    return f"{mb / 1024.0:.2f} gigabytes"  # info: return f" { mb / 1024.0 : .2f


# ====================================================
# SECTION: function _auth_fail_counts
# What it does:  auth fail counts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _auth_fail_counts(now_s: float | None = None) -> dict[str, int | None]:  # info: def _auth_fail_counts
    now_s = now_s if now_s is not None else time.time()  # info: set now_s
    hour, day = now_s - 3600, now_s - 86400  # info: hour , day = now_s - 3600 ,
    c1 = c24 = 0  # info: set c1
    readable = False  # info: set readable
    for path in _AUTH_LOGS:  # info: for path in _AUTH_LOGS :
        try:  # info: try :
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()  # info: set lines
        except OSError:  # info: except OSError :
            continue  # info: continue
        readable = True  # info: set readable
        for line in lines:  # info: for line in lines :
            if not _AUTH_FAIL.search(line):  # info: if not _AUTH_FAIL . search ( line )
                continue  # info: continue
            try:  # info: try :
                ts = datetime.fromisoformat(line.split(" ", 1)[0]).timestamp()  # info: set ts
            except ValueError:  # info: except ValueError :
                continue  # info: continue
            c1 += ts >= hour  # info: set c1
            c24 += ts >= day  # info: set c24
    if not readable:  # info: if not readable :
        return {"failed_1h": None, "failed_24h": None}  # info: return { "failed_1h" : None , "failed_24h" :
    return {"failed_1h": c1, "failed_24h": c24}  # info: return { "failed_1h" : c1 , "failed_24h" :


# ====================================================
# SECTION: function _ufw_start_on_boot
# What it does:  ufw start on boot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ufw_start_on_boot() -> bool | None:  # info: def _ufw_start_on_boot
    try:  # info: try :
        text = Path("/etc/ufw/ufw.conf").read_text(encoding="utf-8", errors="replace")  # info: set text
    except OSError:  # info: except OSError :
        return None  # info: return None
    for line in text.splitlines():  # info: for line in text . splitlines ( )
        if line.strip().upper().startswith("ENABLED="):  # info: if line . strip ( ) . upper
            return line.split("=", 1)[1].strip().lower() in {"yes", "true", "1"}  # info: return line . split ( "=" , 1
    return None  # info: return None


# ====================================================
# SECTION: function _unit_active
# What it does:  unit active.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _unit_active(name: str) -> bool | None:  # info: def _unit_active
    exe = shutil.which("systemctl")  # info: set exe
    if not exe:  # info: if not exe :
        return None  # info: return None
    try:  # info: try :
        out = subprocess.run([exe, "is-active", name], capture_output=True, text=True, timeout=2)  # info: set out
    except Exception:  # info: except Exception :
        return None  # info: return None
    val = (out.stdout or "").strip().lower()  # info: set val
    return val == "active" if val in {"active", "inactive", "failed"} else None  # info: return val == "active" if val in {


# ====================================================
# SECTION: function _listen_established
# What it does:  listen established.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _listen_established() -> tuple[int | None, int | None]:  # info: def _listen_established
    if psutil is not None:  # info: if psutil is not None :
        try:  # info: try :
            conns = psutil.net_connections(kind="inet")  # info: set conns
            return (sum(1 for c in conns if str(c.status) == "LISTEN"), sum(1 for c in conns if str(c.status) == "ESTABLISHED"))  # info: return ( sum ( 1 for c in
        except Exception:  # info: except Exception :
            pass  # info: pass
    listen = est = 0  # info: set listen
    ok = False  # info: set ok
    for f in ("/proc/net/tcp", "/proc/net/tcp6"):  # info: for f in ( "/proc/net/tcp" , "/proc/net/tcp6" )
        try:  # info: try :
            rows = Path(f).read_text().splitlines()[1:]  # info: set rows
        except OSError:  # info: except OSError :
            continue  # info: continue
        ok = True  # info: set ok
        for r in rows:  # info: for r in rows :
            st = r.split()[3]  # info: set st
            listen += st == "0A"  # info: set listen
            est += st == "01"  # info: set est
    return (listen, est) if ok else (None, None)  # info: return ( listen , est ) if ok


# ====================================================
# SECTION: function security_snapshot
# What it does: security snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def security_snapshot() -> dict[str, Any]:  # info: def security_snapshot
    fails = _auth_fail_counts()  # info: set fails
    listen, est = _listen_established()  # info: listen , est = _listen_established ( )
    ssh = _unit_active("ssh")  # info: set ssh
    if ssh is None:  # info: if ssh is None :
        ssh = _unit_active("sshd")  # info: set ssh
    return {"failed_1h": fails["failed_1h"], "failed_24h": fails["failed_24h"], "listen_tcp": listen, "established": est,  # info: return { "failed_1h" : fails [ "failed_1h" ]
            "ufw_boot": _ufw_start_on_boot(), "ssh_active": ssh, "fail2ban": Path("/var/run/fail2ban/fail2ban.pid").is_file()}  # info: "ufw_boot" : _ufw_start_on_boot ( ) , "ssh_active" :


# ====================================================
# SECTION: function _write_json
# What it does:  write json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_json(path: Path, data: dict) -> None:  # info: def _write_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    cmd = argv[1] if len(argv) > 1 else ""  # info: set cmd
    at = datetime.now().astimezone().isoformat(timespec="seconds")  # info: set at
    if cmd == "net-sample":  # info: if cmd == "net-sample" :
        net = net_counters()  # info: set net
        if not net:  # info: if not net :
            print(json.dumps({"ok": False, "detail": "no interface"}))  # info: call print
            return 1  # info: return 1
        p = append_net_sample(net)  # info: set p
        hour, day = net_usage_window(3600, now=net), net_usage_window(86400, now=net)  # info: hour , day = net_usage_window ( 3600 ,
        _write_json(NET / "net-last.json", {"at": at, **{k: net[k] for k in ("iface", "link")}, "hour": hour, "day": day})  # info: call _write_json
        print(json.dumps({"ok": True, "file": str(p), "iface": net["iface"], "hour": hour, "day": day}))  # info: call print
        return 0  # info: return 0
    if cmd == "net-usage":  # info: if cmd == "net-usage" :
        net = net_counters()  # info: set net
        print(json.dumps({"ok": bool(net), "hour": net_usage_window(3600, now=net), "day": net_usage_window(86400, now=net)}))  # info: call print
        return 0  # info: return 0
    if cmd == "security":  # info: if cmd == "security" :
        snap = {"at": at, **security_snapshot()}  # info: set snap
        _write_json(SEC / "security-last.json", snap)  # info: call _write_json
        print(json.dumps(snap))  # info: call print
        return 0  # info: return 0
    print(__doc__)  # info: call print
    return 2  # info: return 2


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv))  # info: raise SystemExit ( main ( sys . argv
