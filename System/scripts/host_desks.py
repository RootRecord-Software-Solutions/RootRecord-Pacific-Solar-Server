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
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
NET = DB / "System" / "network"
SEC = DB / "System" / "security"

_NET_SKIP = ("lo", "docker", "veth", "br-", "virbr", "tun", "tap", "wg")
_AUTH_FAIL = re.compile(r"failed password|invalid user|failed publickey|authentication failure", re.I)
_AUTH_LOGS = (Path("/var/log/auth.log"), Path("/var/log/auth.log.1"))

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover
    psutil = None


def _skip_iface(name: str) -> bool:
    n = (name or "").lower()
    return n == "lo" or any(n.startswith(p) for p in _NET_SKIP)


def default_net_iface() -> str | None:
    try:
        lines = Path("/proc/net/route").read_text(encoding="utf-8", errors="replace").splitlines()[1:]
    except OSError:
        return None
    for line in lines:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "00000000" and not _skip_iface(parts[0]):
            return parts[0]
    return None


def _proc_net_dev() -> dict[str, tuple[int, int]]:
    out = {}
    try:
        for line in Path("/proc/net/dev").read_text(encoding="utf-8").splitlines()[2:]:
            name, rest = line.split(":", 1)
            f = rest.split()
            out[name.strip()] = (int(f[0]), int(f[8]))
    except (OSError, ValueError, IndexError):
        pass
    return out


def net_counters() -> dict[str, Any] | None:
    """Wi-Fi / Ethernet byte counters. Skip loopback and virtual bridges."""
    pernic = _proc_net_dev()
    iface = default_net_iface()
    if iface not in pernic:
        named = [n for n in pernic if not _skip_iface(n)]
        iface = named[0] if named else None
    if not iface or iface not in pernic:
        return None
    rx, tx = pernic[iface]
    return {"iface": iface, "link": "wireless" if iface.startswith(("wl", "wlan")) else "wired",
            "rx": rx, "tx": tx, "at": int(time.time() * 1000)}


def _daily(day: datetime) -> Path:
    return NET / "Daily" / f"net-{day.strftime('%Y%m%d')}.jsonl"


def append_net_sample(net: dict[str, Any]) -> Path:
    path = _daily(datetime.now())
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = {"at": int(net["at"]), "iface": net["iface"], "rx": int(net["rx"]), "tx": int(net["tx"])}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    return path


def load_net_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    today = datetime.now()
    for day in (today - timedelta(days=1), today):
        p = _daily(day)
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
                out.append({"at": int(row["at"]), "iface": str(row.get("iface") or ""), "rx": int(row["rx"]), "tx": int(row["tx"])})
            except (ValueError, KeyError, TypeError):
                continue
    out.sort(key=lambda r: r["at"])
    return out


def _row_at_or_before(rows, target_ms):
    prev = None
    for row in rows:
        if int(row["at"]) <= target_ms:
            prev = row
        else:
            break
    return prev


def net_usage_window(seconds: int, *, now: dict | None = None, rows: list | None = None, min_cover: float = 0.75):
    """Byte delta for a lookback window. None until enough live samples exist. (G1, unchanged.)"""
    now = now or net_counters()
    if not now:
        return None
    series = rows if rows is not None else load_net_rows()
    if not series:
        return None
    now_at = int(now["at"])
    need_ms = int(seconds * min_cover * 1000)
    then = _row_at_or_before(series, now_at - int(seconds * 1000))
    if then is None:
        oldest = series[0]
        if now_at - int(oldest["at"]) < need_ms:
            return None
        then = oldest
    cover_ms = now_at - int(then["at"])
    if cover_ms < need_ms:
        return None
    if now["iface"] and then.get("iface") and now["iface"] != then["iface"]:
        return None
    rx, tx = int(now["rx"]) - int(then["rx"]), int(now["tx"]) - int(then["tx"])
    if rx < 0 or tx < 0:
        return None
    return {"seconds": int(cover_ms / 1000), "rx": rx, "tx": tx, "total": rx + tx, "iface": now.get("iface"), "link": now.get("link")}


def spoken_bytes(n: int) -> str:
    n = max(0, int(n))
    if n < 1024:
        return f"{n} bytes"
    kb = n / 1024.0
    if kb < 1024:
        return f"{kb:.1f} kilobytes"
    mb = kb / 1024.0
    if mb < 1024:
        return f"{mb:.1f} megabytes"
    return f"{mb / 1024.0:.2f} gigabytes"


def _auth_fail_counts(now_s: float | None = None) -> dict[str, int | None]:
    now_s = now_s if now_s is not None else time.time()
    hour, day = now_s - 3600, now_s - 86400
    c1 = c24 = 0
    readable = False
    for path in _AUTH_LOGS:
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        readable = True
        for line in lines:
            if not _AUTH_FAIL.search(line):
                continue
            try:
                ts = datetime.fromisoformat(line.split(" ", 1)[0]).timestamp()
            except ValueError:
                continue
            c1 += ts >= hour
            c24 += ts >= day
    if not readable:
        return {"failed_1h": None, "failed_24h": None}
    return {"failed_1h": c1, "failed_24h": c24}


def _ufw_start_on_boot() -> bool | None:
    try:
        text = Path("/etc/ufw/ufw.conf").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        if line.strip().upper().startswith("ENABLED="):
            return line.split("=", 1)[1].strip().lower() in {"yes", "true", "1"}
    return None


def _unit_active(name: str) -> bool | None:
    exe = shutil.which("systemctl")
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "is-active", name], capture_output=True, text=True, timeout=2)
    except Exception:
        return None
    val = (out.stdout or "").strip().lower()
    return val == "active" if val in {"active", "inactive", "failed"} else None


def _listen_established() -> tuple[int | None, int | None]:
    if psutil is not None:
        try:
            conns = psutil.net_connections(kind="inet")
            return (sum(1 for c in conns if str(c.status) == "LISTEN"), sum(1 for c in conns if str(c.status) == "ESTABLISHED"))
        except Exception:
            pass
    listen = est = 0
    ok = False
    for f in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            rows = Path(f).read_text().splitlines()[1:]
        except OSError:
            continue
        ok = True
        for r in rows:
            st = r.split()[3]
            listen += st == "0A"
            est += st == "01"
    return (listen, est) if ok else (None, None)


def security_snapshot() -> dict[str, Any]:
    fails = _auth_fail_counts()
    listen, est = _listen_established()
    ssh = _unit_active("ssh")
    if ssh is None:
        ssh = _unit_active("sshd")
    return {"failed_1h": fails["failed_1h"], "failed_24h": fails["failed_24h"], "listen_tcp": listen, "established": est,
            "ufw_boot": _ufw_start_on_boot(), "ssh_active": ssh, "fail2ban": Path("/var/run/fail2ban/fail2ban.pid").is_file()}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else ""
    at = datetime.now().astimezone().isoformat(timespec="seconds")
    if cmd == "net-sample":
        net = net_counters()
        if not net:
            print(json.dumps({"ok": False, "detail": "no interface"}))
            return 1
        p = append_net_sample(net)
        hour, day = net_usage_window(3600, now=net), net_usage_window(86400, now=net)
        _write_json(NET / "net-last.json", {"at": at, **{k: net[k] for k in ("iface", "link")}, "hour": hour, "day": day})
        print(json.dumps({"ok": True, "file": str(p), "iface": net["iface"], "hour": hour, "day": day}))
        return 0
    if cmd == "net-usage":
        net = net_counters()
        print(json.dumps({"ok": bool(net), "hour": net_usage_window(3600, now=net), "day": net_usage_window(86400, now=net)}))
        return 0
    if cmd == "security":
        snap = {"at": at, **security_snapshot()}
        _write_json(SEC / "security-last.json", snap)
        print(json.dumps(snap))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
