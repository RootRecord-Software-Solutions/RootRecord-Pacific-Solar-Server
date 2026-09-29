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
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

SLOW_TTL = 15
ECO = "/home/rootrecord/RootRecord-Ecosystem"
RELEVANT = re.compile(r"RootRecord-Ecosystem|/Database/GITHUB/|rootserver|council|cam_server|grab_frame|globe|ble-owner|ecoflow|"
                      r"ollama|\bflm\b|cloudflared|conky|rr_control_panel|poller|kokoro|whisper|weather|run_poller|"
                      r"\.ollama/skills|ava-", re.I)
SECRET_FLAG = re.compile(r"^--?(token|password|passwd|pass|secret|key|api[-_]?key|auth|cookie|webhook|pat)$", re.I)
SECRET_KV = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*(TOKEN|SECRET|PASS\w*|KEY|PAT|WEBHOOK|AUTH|COOKIE)[A-Za-z0-9_]*)=(.+)$", re.I)
OPAQUE = re.compile(r"^[A-Za-z0-9_\-+/=.]{32,}$")

# name pattern -> (label, Settings sub-page)
SETTINGS_MAP = [
    (r"rootserver_poller|rr-rootserver-poller|jobs\.py|poller", "services"),
    (r"council|telegram|relay|discord|slack", "messaging"),
    (r"cam_server|grab_frame|a-eyes|aeyes|Cameras|timelapse", "cameras"),
    (r"weather|run_poller", "weather"),
    (r"ollama|flm|npu|infer|specialist", "ai"),
    (r"kokoro|voice|whisper|espeak", "voice"),
    (r"cloudflared|tunnel|globe|network|ssh", "network"),
    (r"ble-owner|ecoflow|Energy|devices", "services"),
    (r"github|autopush|sync", "services"),
    (r"rr_control_panel|conky|Root Monitor", "panel"),
]


def settings_page(text: str) -> str:
    for rx, page in SETTINGS_MAP:
        if re.search(rx, text, re.I):
            return page
    return "environment"


def mask_argv(argv: list[str]) -> list[str]:
    out, hide_next = [], False
    for a in argv:
        if hide_next:
            out.append(f"<masked len {len(a)}>")
            hide_next = False
            continue
        if "=" in a and a.startswith("-"):
            k, v = a.split("=", 1)
            if SECRET_FLAG.match(k):
                out.append(f"{k}=<masked len {len(v)}>")
                continue
        if SECRET_FLAG.match(a):
            out.append(a)
            hide_next = True
            continue
        m = SECRET_KV.match(a)
        if m:
            out.append(f"{m.group(1)}=<masked len {len(m.group(3))}>")
            continue
        if OPAQUE.match(a) and not a.startswith("/"):
            out.append(f"<masked len {len(a)}>")
            continue
        out.append(a)
    return out


def short_cmd(argv: list[str], width=150) -> str:
    a = mask_argv(argv)
    if not a:
        return ""
    parts = [os.path.basename(a[0])]
    for x in a[1:]:
        parts.append(x.replace(ECO + "/", "…/") if x.startswith(ECO) else x)
    s = " ".join(parts)
    return s if len(s) <= width else s[:width - 1] + "…"


_HZ = os.sysconf("SC_CLK_TCK")
_PAGE = os.sysconf("SC_PAGE_SIZE")


def _uptime() -> float:
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except OSError:
        return 0.0


def fmt_dur(s: float | None) -> str:
    if s is None:
        return "—"
    s = int(s)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{d}d{h:02d}h" if d else (f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s")


def processes() -> list[dict]:
    """All processes (own user readable), with ppid, age, RSS; masked short cmd."""
    up = _uptime()
    out = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            raw = Path(f"/proc/{d}/cmdline").read_bytes()
            if not raw:
                continue
            argv = [x.decode(errors="replace") for x in raw.split(b"\0") if x]
            st = Path(f"/proc/{d}/stat").read_text()
            rest = st[st.rfind(")") + 2:].split()
            ppid, start = int(rest[1]), int(rest[19])
            rss = int(rest[21]) * _PAGE
        except (OSError, IndexError, ValueError):
            continue
        out.append({"pid": int(d), "ppid": ppid, "argv": argv, "age": max(0.0, up - start / _HZ), "rss_mb": rss / 1048576})
    return out


def descendants(procs: list[dict], root: int) -> list[dict]:
    kids: dict[int, list[dict]] = {}
    for p in procs:
        kids.setdefault(p["ppid"], []).append(p)
    res, stack = [], [(root, 0)]
    while stack:
        pid, depth = stack.pop()
        for c in sorted(kids.get(pid, []), key=lambda x: x["pid"], reverse=True):
            c = dict(c, depth=depth + 1)
            res.append(c)
            stack.append((c["pid"], depth + 1))
    return res


def listening() -> dict[int, tuple[str, int]]:
    """socket inode -> (proto, port) for LISTEN tcp sockets."""
    res = {}
    for f, proto in (("/proc/net/tcp", "tcp"), ("/proc/net/tcp6", "tcp6")):
        try:
            for ln in Path(f).read_text().splitlines()[1:]:
                p = ln.split()
                if len(p) > 9 and p[3] == "0A":
                    addr, port = p[1].rsplit(":", 1)
                    loc = "127.0.0.1" if addr in ("0100007F", "00000000000000000000000001000000") else ("*" if set(addr) == {"0"} else "lan")
                    res[int(p[9])] = (f"{proto} {loc}", int(port, 16))
        except OSError:
            pass
    return res


def ports_of(pid: int, lis: dict) -> list[str]:
    out = []
    try:
        for fd in os.listdir(f"/proc/{pid}/fd"):
            try:
                t = os.readlink(f"/proc/{pid}/fd/{fd}")
            except OSError:
                continue
            if t.startswith("socket:["):
                ino = int(t[8:-1])
                if ino in lis:
                    proto, port = lis[ino]
                    out.append(f":{port} ({proto})")
    except OSError:
        pass
    return sorted(set(out))


_slow: dict = {}


def _cached(key, fn):
    now = time.monotonic()
    hit = _slow.get(key)
    if hit and now - hit[0] < SLOW_TTL:
        return hit[1]
    v = fn()
    _slow[key] = (now, v)
    return v


def _run(argv, timeout=4) -> str:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout).stdout
    except Exception as e:
        return f"(error: {type(e).__name__})"


def units(user: bool) -> list[dict]:
    def get():
        argv = ["systemctl"] + (["--user"] if user else []) + ["list-units", "--type=service,timer,socket,path",
                                                               "--all" if user else "--state=running",
                                                               "--no-legend", "--plain", "--no-pager"]
        res = []
        for ln in _run(argv).splitlines():
            p = ln.split(None, 4)
            if len(p) >= 4:
                res.append({"unit": p[0], "load": p[1], "active": p[2], "sub": p[3], "desc": p[4] if len(p) > 4 else ""})
        return res
    return _cached(("units", user), get)


def timers(user: bool) -> list[str]:
    def get():
        argv = ["systemctl"] + (["--user"] if user else []) + ["list-timers", "--all", "--no-legend", "--no-pager"]
        return [re.sub(r"\s{2,}", "  ", ln.strip()) for ln in _run(argv).splitlines() if ln.strip()]
    return _cached(("timers", user), get)


def cron() -> dict:
    def get():
        user = []
        for ln in _run(["crontab", "-l"]).splitlines():
            if ln.strip() and not ln.lstrip().startswith("#"):
                user.append(" ".join(mask_argv(ln.split())))
        sysd = []
        for d in ("/etc/cron.d", "/etc/cron.hourly", "/etc/cron.daily", "/etc/cron.weekly"):
            try:
                sysd += [f"{d}/{f}" for f in sorted(os.listdir(d)) if not f.startswith(".")]
            except OSError:
                pass
        return {"user": user, "system": sysd}
    return _cached("cron", get)


def ollama() -> dict:
    def get(path):
        with urllib.request.urlopen(f"http://127.0.0.1:11434{path}", timeout=1.0) as r:
            return json.loads(r.read(200_000))
    try:
        ver = get("/api/version").get("version")
        ps = get("/api/ps").get("models", [])
        return {"up": True, "version": ver,
                "loaded": [{"name": m.get("name"), "size_mb": round((m.get("size") or 0) / 1048576),
                            "vram_mb": round((m.get("size_vram") or 0) / 1048576), "until": m.get("expires_at", "")[:19]}
                           for m in ps]}
    except Exception as e:
        return {"up": False, "error": type(e).__name__}


def tunnels(procs: list[dict]) -> list[dict]:
    out = []
    for p in procs:
        a = p["argv"]
        b = os.path.basename(a[0]) if a else ""
        if b == "cloudflared" or (b in ("ssh", "autossh") and any(x in ("-L", "-R", "-D") or x.startswith(("-L", "-R", "-D")) for x in a)):
            out.append({"pid": p["pid"], "kind": b, "cmd": short_cmd(a)})
    ifs = []
    try:
        for n in sorted(os.listdir("/sys/class/net")):
            if re.match(r"^(wg|tun|tap|tailscale|zt|ppp)", n):
                st = Path(f"/sys/class/net/{n}/operstate").read_text().strip()
                ifs.append(f"{n} ({st})")
    except OSError:
        pass
    cf_bin = next((c for c in ("/usr/local/bin/cloudflared", "/usr/bin/cloudflared", str(Path.home() / ".local/bin/cloudflared"))
                   if os.path.exists(c)), None)
    return [{"summary": f"cloudflared binary: {cf_bin or 'NOT INSTALLED'} · tunnel/VPN interfaces: {', '.join(ifs) or 'none'}"}] + out


def snapshot() -> dict:
    procs = processes()
    lis = listening()
    rel = [p for p in procs if RELEVANT.search(" ".join(p["argv"][:6]))]
    poller = next((p for p in procs if any("rootserver_poller.py" in x for x in p["argv"][:3])), None)
    kids = descendants(procs, poller["pid"]) if poller else []
    for p in rel + kids + ([poller] if poller else []):
        p["ports"] = ports_of(p["pid"], lis)
        p["cmd"] = short_cmd(p["argv"])
        p["settings"] = settings_page(" ".join(p["argv"][:4]))
    all_ports = sorted({port for _i, (_pr, port) in lis.items()})
    return {"procs": rel, "poller": poller, "children": kids, "listen_ports": all_ports,
            "user_units": units(True), "system_units": units(False), "user_timers": timers(True),
            "system_timers": timers(False), "cron": cron(), "tunnels": tunnels(procs), "ollama": ollama(),
            "proc_total": len(procs)}
