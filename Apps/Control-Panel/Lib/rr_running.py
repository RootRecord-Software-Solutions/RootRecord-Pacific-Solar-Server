"""rr_running.py — READ-ONLY inventory of everything RootRecord runs right now (Root Monitor 'Running' page).

INFO — MUST HAVE (future agents), added 2026-09-29:
- Pure reads: /proc (cmdline, stat, status, fd -> socket inodes), /proc/net/tcp{,6}, sysfs, `systemctl list-units /
  list-timers` (read-only verbs), `crontab -l`, and Ollama's GET /api/ps + /api/version on 127.0.0.1 (lists loaded
  models; never loads one). Nothing is started, stopped or changed. No actions.
- Command lines are MASKED before display: values after --token/--password/... flags, KEY=VALUE args with
  secret-looking keys, and long opaque strings are replaced by <masked len N>.
- systemctl / crontab results are cached for SLOW_TTL seconds so a 5 s refresh stays cheap.
- Each entry carries `settings` = the Root Monitor Settings sub-page that configures it.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path

SLOW_TTL = 15  # info: set SLOW_TTL
ECO = "/home/rootrecord/RootRecord-Ecosystem"  # info: set ECO
RELEVANT = re.compile(r"RootRecord-Ecosystem|/Database/GITHUB/|rootserver|council|cam_server|grab_frame|globe|ble-owner|ecoflow|"  # info: set RELEVANT
                      r"ollama|\bflm\b|cloudflared|conky|rr_control_panel|poller|kokoro|whisper|weather|run_poller|"  # info: r"ollama|\bflm\b|cloudflared|conky|rr_control_panel|poller|kokoro|whisper|weather|run_poller|"
                      r"\.ollama/skills|ava-", re.I)  # info: r"\.ollama/skills|ava-" , re . I )
SECRET_FLAG = re.compile(r"^--?(token|password|passwd|pass|secret|key|api[-_]?key|auth|cookie|webhook|pat)$", re.I)  # info: set SECRET_FLAG
SECRET_KV = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(TOKEN|SECRET|PASS\w*|KEY|PAT|WEBHOOK|AUTH|COOKIE)[A-Za-z0-9_]*)=(.+)$", re.I)  # info: set SECRET_KV
OPAQUE = re.compile(r"^[A-Za-z0-9_\-+/=.]{32,}$")  # info: set OPAQUE

# name pattern -> (label, Settings sub-page)
# ====================================================
# SECTION: SETTINGS_MAP
# What it does: Set SETTINGS_MAP.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SETTINGS_MAP = [  # info: set SETTINGS_MAP
    (r"rootserver_poller|rr-rootserver-poller|jobs\.py|poller", "services"),  # info: call (
    (r"council|telegram|relay|discord|slack", "messaging"),  # info: call (
    (r"cam_server|grab_frame|a-eyes|aeyes|Cameras|timelapse", "cameras"),  # info: call (
    (r"weather|run_poller", "weather"),  # info: call (
    (r"ollama|flm|npu|infer|specialist", "ai"),  # info: call (
    (r"kokoro|voice|whisper|espeak", "voice"),  # info: call (
    (r"cloudflared|tunnel|globe|network|ssh", "network"),  # info: call (
    (r"ble-owner|ecoflow|Energy|devices", "services"),  # info: call (
    (r"github|autopush|sync", "services"),  # info: call (
    (r"rr_control_panel|conky|Root Monitor", "panel"),  # info: call (
]  # info: ]


# ====================================================
# SECTION: function settings_page
# What it does: settings page.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def settings_page(text: str) -> str:  # info: def settings_page
    for rx, page in SETTINGS_MAP:  # info: for rx , page in SETTINGS_MAP :
        if re.search(rx, text, re.I):  # info: if re . search ( rx , text
            return page  # info: return page
    return "environment"  # info: return "environment"


# ====================================================
# SECTION: function mask_argv
# What it does: mask argv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mask_argv(argv: list[str]) -> list[str]:  # info: def mask_argv
    out, hide_next = [], False  # info: out , hide_next = [ ] , False
    for a in argv:  # info: for a in argv :
        if hide_next:  # info: if hide_next :
            out.append(f"<masked len {len(a)}>")  # info: out . append ( f" <masked len { len
            hide_next = False  # info: set hide_next
            continue  # info: continue
        if "=" in a and a.startswith("-"):  # info: if "=" in a and a . startswith
            k, v = a.split("=", 1)  # info: k , v = a . split (
            if SECRET_FLAG.match(k):  # info: if SECRET_FLAG . match ( k ) :
                out.append(f"{k}=<masked len {len(v)}>")  # info: out . append ( f" { k }
                continue  # info: continue
        if SECRET_FLAG.match(a):  # info: if SECRET_FLAG . match ( a ) :
            out.append(a)  # info: out . append ( a )
            hide_next = True  # info: set hide_next
            continue  # info: continue
        m = SECRET_KV.match(a)  # info: set m
        if m:  # info: if m :
            out.append(f"{m.group(1)}=<masked len {len(m.group(3))}>")  # info: out . append ( f" { m .
            continue  # info: continue
        if OPAQUE.match(a) and not a.startswith("/"):  # info: if OPAQUE . match ( a ) and
            out.append(f"<masked len {len(a)}>")  # info: out . append ( f" <masked len { len
            continue  # info: continue
        out.append(a)  # info: out . append ( a )
    return out  # info: return out


# Paths that must never be shown or referenced (private archive / model drafts). Other tools name them in their
# own command lines (e.g. worklog find -prune); Root Monitor replaces them with a neutral tag.
HIDDEN_PATHS = (str(Path.home() / "Desktop/old txt"), f"{ECO}/I'll sort these models tomorrow",  # info: set HIDDEN_PATHS
                "Desktop/old txt", "I'll sort these models tomorrow")  # info: "Desktop/old txt" , "I'll sort these models tomorrow" )


# ====================================================
# SECTION: function hide_paths
# What it does: hide paths.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def hide_paths(s: str) -> str:  # info: def hide_paths
    for h in HIDDEN_PATHS:  # info: for h in HIDDEN_PATHS :
        s = s.replace(h, "<excluded path>")  # info: set s
    return s  # info: return s


# ====================================================
# SECTION: function short_cmd
# What it does: short cmd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def short_cmd(argv: list[str], width=150) -> str:  # info: def short_cmd
    a = [hide_paths(x) for x in mask_argv(argv)]  # info: set a
    if not a:  # info: if not a :
        return ""  # info: return ""
    parts = [os.path.basename(a[0])]  # info: set parts
    for x in a[1:]:  # info: for x in a [ 1 : ]
        parts.append(x.replace(ECO + "/", "…/") if x.startswith(ECO) else x)  # info: parts . append ( x . replace (
    s = " ".join(parts)  # info: set s
    return s if len(s) <= width else s[:width - 1] + "…"  # info: return s if len ( s ) <=


_HZ = os.sysconf("SC_CLK_TCK")  # info: set _HZ
_PAGE = os.sysconf("SC_PAGE_SIZE")  # info: set _PAGE


# ====================================================
# SECTION: function _uptime
# What it does:  uptime.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _uptime() -> float:  # info: def _uptime
    try:  # info: try :
        return float(Path("/proc/uptime").read_text().split()[0])  # info: return float ( Path ( "/proc/uptime" ) .
    except OSError:  # info: except OSError :
        return 0.0  # info: return 0.0


# ====================================================
# SECTION: function fmt_dur
# What it does: fmt dur.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fmt_dur(s: float | None) -> str:  # info: def fmt_dur
    if s is None:  # info: if s is None :
        return "—"  # info: return "—"
    s = int(s)  # info: set s
    d, s = divmod(s, 86400)  # info: d , s = divmod ( s ,
    h, s = divmod(s, 3600)  # info: h , s = divmod ( s ,
    m, s = divmod(s, 60)  # info: m , s = divmod ( s ,
    return f"{d}d{h:02d}h" if d else (f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s")  # info: return f" { d } d { h


# ====================================================
# SECTION: function processes
# What it does: All processes (own user readable), with ppid, age, RSS; masked short cmd.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def processes() -> list[dict]:  # info: def processes
    """All processes (own user readable), with ppid, age, RSS; masked short cmd."""  # info: """All processes (own user readable), with ppid, age, RSS; masked short cmd."""
    up = _uptime()  # info: set up
    out = []  # info: set out
    for d in os.listdir("/proc"):  # info: for d in os . listdir ( "/proc"
        if not d.isdigit():  # info: if not d . isdigit ( ) :
            continue  # info: continue
        try:  # info: try :
            raw = Path(f"/proc/{d}/cmdline").read_bytes()  # info: set raw
            if not raw:  # info: if not raw :
                continue  # info: continue
            argv = [x.decode(errors="replace") for x in raw.split(b"\0") if x]  # info: set argv
            st = Path(f"/proc/{d}/stat").read_text()  # info: set st
            rest = st[st.rfind(")") + 2:].split()  # info: set rest
            ppid, start = int(rest[1]), int(rest[19])  # info: ppid , start = int ( rest [
            rss = int(rest[21]) * _PAGE  # info: set rss
        except (OSError, IndexError, ValueError):  # info: except ( OSError , IndexError , ValueError )
            continue  # info: continue
        out.append({"pid": int(d), "ppid": ppid, "argv": argv, "age": max(0.0, up - start / _HZ), "rss_mb": rss / 1048576})  # info: out . append ( { "pid" : int
    return out  # info: return out


# ====================================================
# SECTION: function descendants
# What it does: descendants.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def descendants(procs: list[dict], root: int) -> list[dict]:  # info: def descendants
    kids: dict[int, list[dict]] = {}  # info: set kids
    for p in procs:  # info: for p in procs :
        kids.setdefault(p["ppid"], []).append(p)  # info: kids . setdefault ( p [ "ppid" ]
    res, stack = [], [(root, 0)]  # info: res , stack = [ ] , [
    while stack:  # info: while stack :
        pid, depth = stack.pop()  # info: pid , depth = stack . pop (
        for c in sorted(kids.get(pid, []), key=lambda x: x["pid"], reverse=True):  # info: for c in sorted ( kids . get
            c = dict(c, depth=depth + 1)  # info: set c
            res.append(c)  # info: res . append ( c )
            stack.append((c["pid"], depth + 1))  # info: stack . append ( ( c [ "pid"
    return res  # info: return res


# ====================================================
# SECTION: function listening
# What it does: socket inode -> (proto, port) for LISTEN tcp sockets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def listening() -> dict[int, tuple[str, int]]:  # info: def listening
    """socket inode -> (proto, port) for LISTEN tcp sockets."""  # info: """socket inode -> (proto, port) for LISTEN tcp sockets."""
    res = {}  # info: set res
    for f, proto in (("/proc/net/tcp", "tcp"), ("/proc/net/tcp6", "tcp6")):  # info: for f , proto in ( ( "/proc/net/tcp"
        try:  # info: try :
            for ln in Path(f).read_text().splitlines()[1:]:  # info: for ln in Path ( f ) .
                p = ln.split()  # info: set p
                if len(p) > 9 and p[3] == "0A":  # info: if len ( p ) > 9 and
                    addr, port = p[1].rsplit(":", 1)  # info: addr , port = p [ 1 ]
                    loc = "127.0.0.1" if addr in ("0100007F", "00000000000000000000000001000000") else ("*" if set(addr) == {"0"} else "lan")  # info: set loc
                    res[int(p[9])] = (f"{proto} {loc}", int(port, 16))  # info: res [ int ( p [ 9 ]
        except OSError:  # info: except OSError :
            pass  # info: pass
    return res  # info: return res


# ====================================================
# SECTION: function ports_of
# What it does: ports of.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ports_of(pid: int, lis: dict) -> list[str]:  # info: def ports_of
    out = []  # info: set out
    try:  # info: try :
        for fd in os.listdir(f"/proc/{pid}/fd"):  # info: for fd in os . listdir ( f"
            try:  # info: try :
                t = os.readlink(f"/proc/{pid}/fd/{fd}")  # info: set t
            except OSError:  # info: except OSError :
                continue  # info: continue
            if t.startswith("socket:["):  # info: if t . startswith ( "socket:[" ) :
                ino = int(t[8:-1])  # info: set ino
                if ino in lis:  # info: if ino in lis :
                    proto, port = lis[ino]  # info: proto , port = lis [ ino ]
                    out.append(f":{port} ({proto})")  # info: out . append ( f" : { port
    except OSError:  # info: except OSError :
        pass  # info: pass
    return sorted(set(out))  # info: return sorted ( set ( out ) )


_slow: dict = {}  # info: set _slow


# ====================================================
# SECTION: function _cached
# What it does:  cached.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cached(key, fn):  # info: def _cached
    now = time.monotonic()  # info: set now
    hit = _slow.get(key)  # info: set hit
    if hit and now - hit[0] < SLOW_TTL:  # info: if hit and now - hit [ 0
        return hit[1]  # info: return hit [ 1 ]
    v = fn()  # info: set v
    _slow[key] = (now, v)  # info: _slow [ key ] = ( now ,
    return v  # info: return v


# ====================================================
# SECTION: function _run
# What it does:  run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _run(argv, timeout=4) -> str:  # info: def _run
    try:  # info: try :
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).stdout  # info: return subprocess . run ( argv , capture_output
    except Exception as e:  # info: except Exception as e :
        return f"(error: {type(e).__name__})"  # info: return f" (error: { type ( e )


# ====================================================
# SECTION: function units
# What it does: units.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def units(user: bool) -> list[dict]:  # info: def units
    def get():  # info: def get
        argv = ["systemctl"] + (["--user"] if user else []) + ["list-units", "--type=service,timer,socket,path",  # info: set argv
                                                               "--all" if user else "--state=running",  # info: "--all" if user else "--state=running" ,
                                                               "--no-legend", "--plain", "--no-pager"]  # info: "--no-legend" , "--plain" , "--no-pager" ]
        res = []  # info: set res
        for ln in _run(argv).splitlines():  # info: for ln in _run ( argv ) .
            p = ln.split(None, 4)  # info: set p
            if len(p) >= 4:  # info: if len ( p ) >= 4 :
                res.append({"unit": p[0], "load": p[1], "active": p[2], "sub": p[3], "desc": p[4] if len(p) > 4 else ""})  # info: res . append ( { "unit" : p
        return res  # info: return res
    return _cached(("units", user), get)  # info: return _cached ( ( "units" , user )


# ====================================================
# SECTION: function timers
# What it does: timers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def timers(user: bool) -> list[str]:  # info: def timers
    def get():  # info: def get
        argv = ["systemctl"] + (["--user"] if user else []) + ["list-timers", "--all", "--no-legend", "--no-pager"]  # info: set argv
        return [re.sub(r"\s{2,}", "  ", ln.strip()) for ln in _run(argv).splitlines() if ln.strip()]  # info: return [ re . sub ( r"\s{2,}" ,
    return _cached(("timers", user), get)  # info: return _cached ( ( "timers" , user )


# ====================================================
# SECTION: function cron
# What it does: cron.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cron() -> dict:  # info: def cron
    def get():  # info: def get
        user = []  # info: set user
        for ln in _run(["crontab", "-l"]).splitlines():  # info: for ln in _run ( [ "crontab" ,
            if ln.strip() and not ln.lstrip().startswith("#"):
                user.append(" ".join(mask_argv(ln.split())))  # info: user . append ( " " . join (
        sysd = []  # info: set sysd
        for d in ("/etc/cron.d", "/etc/cron.hourly", "/etc/cron.daily", "/etc/cron.weekly"):  # info: for d in ( "/etc/cron.d" , "/etc/cron.hourly" ,
            try:  # info: try :
                sysd += [f"{d}/{f}" for f in sorted(os.listdir(d)) if not f.startswith(".")]  # info: set sysd
            except OSError:  # info: except OSError :
                pass  # info: pass
        return {"user": user, "system": sysd}  # info: return { "user" : user , "system" :
    return _cached("cron", get)  # info: return _cached ( "cron" , get )


# ====================================================
# SECTION: function _local_get
# What it does: Tiny HTTP/1.0 GET to 127.0.0.1 (no urllib: keeps http.client/ssl/email out of memory).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _local_get(port: int, path: str, timeout=1.0) -> dict:  # info: def _local_get
    """Tiny HTTP/1.0 GET to 127.0.0.1 (no urllib: keeps http.client/ssl/email out of memory)."""  # info: """Tiny HTTP/1.0 GET to 127.0.0.1 (no urllib: keeps http.client/ssl/email out of memory)."""
    import socket  # info: import socket
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:  # info: with socket . create_connection ( ( "127.0.0.1" ,
        s.settimeout(timeout)  # info: s . settimeout ( timeout )
        s.sendall(f"GET {path} HTTP/1.0\r\nHost: 127.0.0.1\r\nAccept: application/json\r\n\r\n".encode())  # info: s . sendall ( f" GET { path
        buf = b""  # info: set buf
        while len(buf) < 300_000:  # info: while len ( buf ) < 300_000 :
            chunk = s.recv(65536)  # info: set chunk
            if not chunk:  # info: if not chunk :
                break  # info: break
            buf += chunk  # info: set buf
    head, _sep, body = buf.partition(b"\r\n\r\n")  # info: head , _sep , body = buf .
    if b" 200 " not in head.split(b"\r\n", 1)[0]:  # info: if b" 200 " not in head . split (
        raise OSError("HTTP " + head.split(b"\r\n", 1)[0].decode(errors="replace")[:40])  # info: raise OSError ( "HTTP " + head . split
    return json.loads(body or b"{}")  # info: return json . loads ( body or b"{}"


# ====================================================
# SECTION: function ollama
# What it does: Ollama GET /api/version + /api/ps (lists loaded models; never loads one).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ollama() -> dict:  # info: def ollama
    """Ollama GET /api/version + /api/ps (lists loaded models; never loads one)."""  # info: """Ollama GET /api/version + /api/ps (lists loaded models; never loads one)."""
    try:  # info: try :
        ver = _local_get(11434, "/api/version").get("version")  # info: set ver
        ps = _local_get(11434, "/api/ps").get("models", [])  # info: set ps
        return {"up": True, "version": ver,  # info: return { "up" : True , "version" :
                "loaded": [{"name": m.get("name"), "size_mb": round((m.get("size") or 0) / 1048576),  # info: "loaded" : [ { "name" : m .
                            "vram_mb": round((m.get("size_vram") or 0) / 1048576), "until": (m.get("expires_at") or "")[:19]}  # info: "vram_mb" : round ( ( m . get
                           for m in ps]}  # info: for m in ps ] }
    except Exception as e:  # info: except Exception as e :
        return {"up": False, "error": type(e).__name__}  # info: return { "up" : False , "error" :


# ====================================================
# SECTION: function tunnels
# What it does: tunnels.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tunnels(procs: list[dict]) -> list[dict]:  # info: def tunnels
    out = []  # info: set out
    for p in procs:  # info: for p in procs :
        a = p["argv"]  # info: set a
        b = os.path.basename(a[0]) if a else ""  # info: set b
        if b == "cloudflared" or (b in ("ssh", "autossh") and any(x in ("-L", "-R", "-D") or x.startswith(("-L", "-R", "-D")) for x in a)):  # info: if b == "cloudflared" or ( b in
            out.append({"pid": p["pid"], "kind": b, "cmd": short_cmd(a)})  # info: out . append ( { "pid" : p
    ifs = []  # info: set ifs
    try:  # info: try :
        for n in sorted(os.listdir("/sys/class/net")):  # info: for n in sorted ( os . listdir
            if re.match(r"^(wg|tun|tap|tailscale|zt|ppp)", n):  # info: if re . match ( r"^(wg|tun|tap|tailscale|zt|ppp)" , n
                st = Path(f"/sys/class/net/{n}/operstate").read_text().strip()  # info: set st
                ifs.append(f"{n} ({st})")  # info: ifs . append ( f" { n }
    except OSError:  # info: except OSError :
        pass  # info: pass
    cf_run = []  # info: set cf_run
    for t in out:  # info: for t in out :
        if t["kind"] == "cloudflared":  # info: if t [ "kind" ] == "cloudflared" :
            try:  # info: try :
                cf_run.append(os.readlink(f"/proc/{t['pid']}/exe").replace(ECO + "/", "…/"))  # info: cf_run . append ( os . readlink (
            except OSError:  # info: except OSError :
                pass  # info: pass
    import shutil  # info: import shutil
    cf_bin = sorted(set(cf_run)) or [c for c in (shutil.which("cloudflared"),) if c]  # info: set cf_bin
    return [{"summary": f"cloudflared: {', '.join(cf_bin) if cf_bin else 'no binary on PATH and none running'} · "  # info: return [ { "summary" : f" cloudflared: {
                        f"tunnel/VPN interfaces: {', '.join(ifs) or 'none'}"}] + out  # info: f" tunnel/VPN interfaces: { ', ' . join ( ifs


# ====================================================
# SECTION: function snapshot
# What it does: snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def snapshot() -> dict:  # info: def snapshot
    procs = processes()  # info: set procs
    lis = listening()  # info: set lis
    rel = [p for p in procs if RELEVANT.search(" ".join(p["argv"][:6]))]  # info: set rel
    poller = next((p for p in procs if any("rootserver_poller.py" in x for x in p["argv"][:3])), None)  # info: set poller
    kids = descendants(procs, poller["pid"]) if poller else []  # info: set kids
    for p in rel + kids + ([poller] if poller else []):  # info: for p in rel + kids + (
        p["ports"] = ports_of(p["pid"], lis)  # info: p [ "ports" ] = ports_of ( p
        p["cmd"] = short_cmd(p["argv"])  # info: p [ "cmd" ] = short_cmd ( p
        p["settings"] = settings_page(" ".join(p["argv"][:4]))  # info: p [ "settings" ] = settings_page ( " "
    all_ports = sorted({port for _i, (_pr, port) in lis.items()})  # info: set all_ports
    return {"procs": rel, "poller": poller, "children": kids, "listen_ports": all_ports,  # info: return { "procs" : rel , "poller" :
            "user_units": units(True), "system_units": units(False), "user_timers": timers(True),  # info: "user_units" : units ( True ) , "system_units"
            "system_timers": timers(False), "cron": cron(), "tunnels": tunnels(procs), "ollama": ollama(),  # info: "system_timers" : timers ( False ) , "cron"
            "proc_total": len(procs)}  # info: "proc_total" : len ( procs ) }
