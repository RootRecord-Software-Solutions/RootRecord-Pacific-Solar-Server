"""rr_sources.py — read-only data readers for Root Monitor (GTK, was "RootRecord Control Panel") and Conky readout.

INFO — MUST HAVE (future agents), added 2026-09-29:
- READ-ONLY. Every function here only reads existing JSON / log / report files, sysfs and /proc.
  Nothing here writes, starts, stops, sends or loads a model.
- No network calls, no sqlite. Same sources as poller-dashboard.py and the poller ENERGY status line.
- No GTK import here, so the Conky helper can reuse it cheaply.
- Camera functions are only called by the camera viewer when it is ON and its page is visible.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Pacific/Honolulu")

# (label, systemd unit or None, scope, argv suffixes to count, expected count or None=any>=1)
# Copied from poller-dashboard.py SERVICES (2026-09-29) so the panel shows the same rows.
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

# Counters so --check can prove what was (not) touched.
STATS = {"camera_dir_scans": 0, "camera_files_opened": 0, "camera_http_fetches": 0}


class Paths:
    def __init__(self, database_root: str, pacific_root: str):
        self.db = Path(database_root)
        self.pacific = Path(pacific_root)

    @property
    def energy(self) -> Path:
        return self.db / "Energy"

    @property
    def log(self) -> Path:
        return self.db / "Logs/Automations/automations_current.log"

    @property
    def logs_dir(self) -> Path:
        return self.db / "Logs"

    @property
    def system_last(self) -> Path:
        return self.db / "System/last/host-last.json"

    @property
    def system_status(self) -> Path:
        return self.db / "System/status/system-status.json"

    @property
    def weather_l0(self) -> Path:
        return self.db / "Weather/Hawai'i/reports/0 Level Processing"

    @property
    def inference_log(self) -> Path:
        return self.db / "Logs/AI/Inference/inference_current.jsonl"

    @property
    def routing_log(self) -> Path:
        return self.db / "Logs/AI/Routing/routing_current.jsonl"

    @property
    def ai_report(self) -> Path:
        return self.db / "Logs/AI/Reports/ai-processing-report_current.md"

    @property
    def plumbing_state(self) -> Path:
        return self.db / "Github/plumbing/state"

    @property
    def camera_images(self) -> Path:
        return self.db / "Media/Images"

    @property
    def npu_status_sh(self) -> Path:
        return self.pacific / "System/scripts/plumbing/npu-status.sh"

    @property
    def poller_dashboard(self) -> Path:
        return self.pacific / "Automations/scripts/poller/poller-dashboard.py"

    @property
    def jobs_py(self) -> Path:
        return self.pacific / "Automations/scripts/jobs.py"

    @property
    def cameras_dir(self) -> Path:
        return self.pacific / "Security/Cameras"


# ---------------------------------------------------------------- helpers
def read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def parse_ts(s):
    try:
        s = str(s)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt
    except Exception:
        return None


def age_s(ts) -> float | None:
    dt = parse_ts(ts)
    return None if dt is None else (datetime.now(TZ) - dt).total_seconds()


def fmt_age(a: float | None) -> str:
    if a is None:
        return "no reading"
    a = max(0, int(a))
    if a < 3600:
        return f"{a // 60}m{a % 60:02d}s ago"
    return f"{a // 3600}h{(a % 3600) // 60:02d}m ago"


def hst(ts) -> str:
    dt = parse_ts(ts)
    return dt.astimezone(TZ).strftime("%H:%M:%S HST") if dt else "—"


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


# ---------------------------------------------------------------- energy
def laptop_battery():
    """(pct, status, on_ac) from sysfs, same logic as poller-dashboard.py; None if no battery."""
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


def energy(paths: Paths) -> dict:
    out = {}
    for dev in ("river2pro", "delta2"):
        soc = read_json(paths.energy / f"soc/{dev}-last.json") or {}
        w = read_json(paths.energy / f"watts/{dev}-last.json") or {}
        out[dev] = {
            "soc": soc.get("soc"), "at": soc.get("at"), "source": soc.get("source"),
            "age": age_s(soc.get("at")),
            "solar_in": w.get("solar_input_power"), "ac_out": w.get("ac_output_power"),
            "ac_in": w.get("ac_input_power"), "usbc_out": w.get("usbc_output_power"),
            "charge_source": w.get("charge_source"), "watts_at": w.get("at"),
        }
    out["laptop"] = laptop_battery()
    return out


def log_digest(paths: Paths) -> dict:
    """Latest poller status line (ENERGY heartbeat), SYSTEM line, SUMMARY lines, log age, tail."""
    lines = tail_lines(paths.log)
    d = {"energy_line": "", "energy_line_at": "", "system_line": "", "summary": {}, "lines": lines,
         "b3_expansion": None, "lap_field": None}
    try:
        d["log_age"] = time.time() - paths.log.stat().st_mtime
    except OSError:
        d["log_age"] = None
    for ln in reversed(lines):
        if not d["energy_line"] and "ENERGY  " in ln:
            i = ln.index("ENERGY  ")
            d["energy_line"], d["energy_line_at"] = ln[i:].strip(), ln[:i]
            m = re.search(r"\bB3=(\S+)", ln)
            d["b3_expansion"] = m.group(1) if m else None
            m = re.search(r"\bLAP=(\S+)", ln)
            d["lap_field"] = m.group(1) if m else None
        if not d["system_line"] and "| SYSTEM " in ln:
            d["system_line"] = re.sub(r"\s+", " ", ln.split("| SYSTEM", 1)[1]).strip()
        for dev in ("river2pro", "delta2"):
            if dev not in d["summary"] and f"SUMMARY={dev} " in ln:
                m = re.search(r"SUMMARY=\S+ (.*)", ln)
                d["summary"][dev] = m.group(1) if m else ""
        if d["energy_line"] and d["system_line"] and len(d["summary"]) == 2:
            break
    return d


ANSI = re.compile(r"\033\[[0-9;?]*[A-Za-z]")


def load_poller_watch(paths: Paths):
    """Import poller-watch.py for format_line / aeyes_solar_state (import only, no handlers run),
    exactly like poller-dashboard.py does."""
    import importlib.util
    try:
        p = paths.pacific / "Automations/scripts/poller/poller-watch.py"
        spec = importlib.util.spec_from_file_location("rr_poller_watch_cp", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except Exception:
        return None


def formatted_log(pw, lines: list[str], n: int = 40) -> list[str]:
    out = []
    for ln in lines[-300:]:
        try:
            f = pw.format_line(ln) if pw is not None else ln
        except Exception:
            f = ln
        if f:
            out.append(ANSI.sub("", f).rstrip())
    return out[-n:]


# ---------------------------------------------------------------- system
def system(paths: Paths) -> dict:
    last = read_json(paths.system_last) or {}
    f = last.get("fields") or {}
    val = lambda k: (f.get(k) or {}).get("value")  # noqa: E731
    st = read_json(paths.system_status) or {}
    five = ((st.get("five_min") or {}).get("metrics")) or {}
    avg = lambda k: (five.get(k) or {}).get("avg")  # noqa: E731
    return {
        "cpu": val("cpu_percent"), "mem": val("mem_used_percent"),
        "mem_avail": val("mem_available_bytes"), "mem_total": val("mem_total_bytes"),
        "load": (val("load1"), val("load5"), val("load15")),
        "at": last.get("at"), "age": age_s(last.get("at")), "host": last.get("host"),
        "five_cpu": avg("cpu_percent"), "five_mem": avg("mem_used_percent"),
        "five_start": (st.get("five_min") or {}).get("period_start"),
        "five_end": (st.get("five_min") or {}).get("period_end"),
    }


# ---------------------------------------------------------------- weather
_zfp_cache: dict = {}


def weather(paths: Paths, zone: str, pw=None) -> dict:
    d = {"solar": None, "zone": zone, "today": "", "tonight": "", "advisories": [], "collected": "",
         "state_generated": ""}
    if pw is not None:
        try:
            d["solar"] = pw.aeyes_solar_state()
        except Exception:
            d["solar"] = None
    zfp = paths.weather_l0 / "zfp_zone_forecast_current.md"
    try:
        mt = zfp.stat().st_mtime
    except OSError:
        return d
    key = (str(zfp), mt, zone)
    if _zfp_cache.get("key") != key:
        text = zfp.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"\*\*Collected:\*\*\s*(\S+)", text)
        res = {"collected": m.group(1) if m else ""}
        blocks = re.split(r"\n(?=HIZ\d{3})", text)
        blk = next((b for b in blocks if re.search(rf"^{re.escape(zone)}-\s*$", b, re.M)), "")
        res["advisories"] = sorted(set(re.findall(r"^\.\.\.(.+?)\.\.\.\s*$", blk, re.M)))

        def para(tag):
            m2 = re.search(rf"^\.{tag}\.\.\.(.*?)(?=^\.[A-Z ]+\.\.\.|^\$\$|\Z)", blk, re.M | re.S)
            return re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else ""
        res["today"], res["tonight"] = para("TODAY") or para("THIS AFTERNOON") or para("REST OF TODAY"), para("TONIGHT")
        _zfp_cache.clear()
        _zfp_cache.update(key=key, res=res)
        del text
    d.update(_zfp_cache["res"])
    try:
        with (paths.weather_l0 / "Hawaii_State_Weather_Report_current.md").open("r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(600)
        m = re.search(r"\*\*Generated:\*\*\s*([^\n]+)", head)
        d["state_generated"] = m.group(1).strip() if m else ""
    except OSError:
        pass
    return d


# ---------------------------------------------------------------- NPU
def _listening_ports() -> set[int]:
    ports = set()
    for f in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for ln in Path(f).read_text().splitlines()[1:]:
                parts = ln.split()
                if len(parts) > 3 and parts[3] == "0A":
                    ports.add(int(parts[1].rsplit(":", 1)[1], 16))
        except OSError:
            pass
    return ports


def proc_argvs() -> list[tuple[int, list[str]]]:
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
            res.append((int(d), [a.decode(errors="replace") for a in raw.split(b"\0") if a][:4]))
    return res


def npu(paths: Paths, argvs=None, flm_port: int = 52625) -> dict:
    argvs = argvs if argvs is not None else proc_argvs()
    accel = sorted(p.name for p in Path("/dev/accel").glob("*")) if Path("/dev/accel").exists() else []
    flm = [pid for pid, a in argvs if any(re.search(r"(^|/)flm$", x) for x in a[:1]) and "serve" in a[1:3]]
    holder_f = paths.plumbing_state / "holder.txt"
    try:
        holder = holder_f.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        holder = ""
    port_open = flm_port in _listening_ports()
    state = "IDLE (on demand) — normal" if not flm and not port_open else f"ACTIVE flm serve pid={flm or 'none'} :{flm_port} {'open' if port_open else 'closed'}"
    return {"accel": accel, "flm_pids": flm, "port_open": port_open, "lock": ("BUSY " + holder) if holder else "IDLE",
            "state": state}


# ---------------------------------------------------------------- AI inference log
_ai_cache: dict = {}


def ai_summary(paths: Paths) -> dict:
    p = paths.inference_log
    try:
        st = p.stat()
    except OSError:
        return {"present": False}
    key = (st.st_mtime, st.st_size)
    if _ai_cache.get("key") == key:
        return _ai_cache["res"]
    rows = []
    for ln in tail_lines(p, 262144):
        try:
            rows.append(json.loads(ln))
        except Exception:
            pass
    today = datetime.now(TZ).date().isoformat()
    routes, models, callers = {}, {}, {}
    lat = [r.get("latency_ms") for r in rows if isinstance(r.get("latency_ms"), (int, float))]
    for r in rows:
        routes[r.get("route", "?")] = routes.get(r.get("route", "?"), 0) + 1
        models[r.get("model", "?")] = models.get(r.get("model", "?"), 0) + 1
        callers[r.get("caller", "?")] = callers.get(r.get("caller", "?"), 0) + 1
    res = {
        "present": True, "count": len(rows), "today": sum(1 for r in rows if str(r.get("ts", "")).startswith(today)),
        "routes": routes, "models": models, "callers": callers,
        "fallbacks": sum(1 for r in rows if r.get("fallback")), "errors": sum(1 for r in rows if r.get("exit_code") not in (0, None)),
        "lat_avg": (sum(lat) / len(lat)) if lat else None, "lat_max": max(lat) if lat else None,
        "last": rows[-1] if rows else None, "size": st.st_size,
    }
    try:
        res["routing_rows"] = sum(1 for _ in paths.routing_log.open("rb"))
    except OSError:
        res["routing_rows"] = None
    try:
        with paths.ai_report.open("r", encoding="utf-8", errors="replace") as fh:
            res["report_head"] = fh.read(1200)
    except OSError:
        res["report_head"] = ""
    _ai_cache.clear()
    _ai_cache.update(key=key, res=res)
    return res


# ---------------------------------------------------------------- services
def _count(argvs, suffixes) -> int:
    n = 0
    for _pid, argv in argvs:
        if any(a.endswith(sfx) for a in argv[:3] for sfx in suffixes if len(a) < 400):
            n += 1
    return n


def _units_active(units: list[str], user: bool) -> dict:
    if not units:
        return {}
    cmd = ["systemctl"] + (["--user"] if user else []) + ["show", "-p", "Id,ActiveState,MainPID"] + units
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return {}
    res, cur = {}, {}
    for ln in out.splitlines() + [""]:
        if not ln.strip():
            if cur.get("Id"):
                res[cur["Id"]] = cur
            cur = {}
            continue
        k, _, v = ln.partition("=")
        cur[k] = v
    return res


def services(argvs=None) -> list[tuple[str, str, str]]:
    """Same PASS/WARN/FAIL rule as poller-dashboard.py service_rows()."""
    argvs = argvs if argvs is not None else proc_argvs()
    user = _units_active([u for _l, u, s, _x, _e in SERVICES if u and s == "user"], True)
    sysu = _units_active([u for _l, u, s, _x, _e in SERVICES if u and s == "system"], False)
    rows = []
    for label, unit, scope, sfx, expect in SERVICES:
        n = _count(argvs, sfx)
        st = None
        pid = ""
        if unit:
            info = (user if scope == "user" else sysu).get(unit) or {}
            st = info.get("ActiveState") or "unknown"
            pid = info.get("MainPID", "")
        if st not in (None, "active") or n == 0:
            state = "FAIL"
        elif expect is not None and n != expect:
            state = "WARN"
        else:
            state = "PASS"
        detail = (f"unit {st}" if unit else "no unit") + f" · {n} proc" + (f" · MainPID {pid}" if pid not in ("", "0") else "")
        rows.append((label, state, detail))
    return rows


def poller_quick(argvs) -> tuple[str, int]:
    n = _count(argvs, SERVICES[0][3])
    return ("PASS" if n == 1 else "WARN" if n > 1 else "FAIL"), n


def gated_jobs(paths: Paths) -> list[tuple[str, str, str]]:
    """(job id, RR_* flag, default) for jobs.py entries whose "enabled" is os.environ.get("RR_...").
    Text scan only (no import, no reading any process environment). The real on/off is decided by the
    poller's environment at poller start; defaults are "0" (OFF)."""
    try:
        text = paths.jobs_py.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    pat = re.compile(r'"id":\s*"([^"]+)",\s*"enabled":\s*os\.environ\.get\("(RR_[A-Z0-9_]+)",\s*"([^"]*)"\)')
    return [(m.group(1), m.group(2), m.group(3)) for m in pat.finditer(text)]


# ---------------------------------------------------------------- cameras
def discover_cameras(paths: Paths) -> list[str]:
    """Channels from grab_all.sh (`for ch in 1 2 3 4`) — never reads store/CONNECTION.json."""
    try:
        text = (paths.cameras_dir / "grab_all.sh").read_text(encoding="utf-8", errors="replace")
        m = re.search(r"for\s+ch\s+in\s+([0-9 ]+);", text)
        if m:
            return [f"ch{n}" for n in m.group(1).split()]
    except OSError:
        pass
    return ["ch1", "ch2", "ch3", "ch4"]


def latest_stills(paths: Paths, cams: list[str], skip_newer_than: float = 1.5) -> dict:
    """Newest still per camera by file name (chN-YYYYmmddTHHMMSSZ.jpg). Directory listing only;
    the image file itself is opened by the caller. Skips a file younger than skip_newer_than seconds
    (grab may still be writing it)."""
    STATS["camera_dir_scans"] += 1
    best: dict[str, list[str]] = {c: [] for c in cams}
    try:
        with os.scandir(paths.camera_images) as it:
            for e in it:
                n = e.name
                if not n.endswith(".jpg"):
                    continue
                c = n.split("-", 1)[0]
                if c in best:
                    lst = best[c]
                    lst.append(n)
                    if len(lst) > 8:
                        lst.sort()
                        del lst[:-3]
    except OSError:
        return {c: None for c in cams}
    now = time.time()
    res = {}
    for c, lst in best.items():
        res[c] = None
        for n in sorted(lst, reverse=True)[:3]:
            p = paths.camera_images / n
            try:
                if now - p.stat().st_mtime >= skip_newer_than:
                    res[c] = p
                    break
            except OSError:
                continue
    return res


def still_time(p: Path) -> str:
    m = re.search(r"-(\d{8}T\d{6}Z)\.jpg$", p.name)
    if not m:
        return ""
    dt = datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
    return dt.strftime("%H:%M:%S HST")
