#!/usr/bin/env python3
"""RootRecord automations poller — tunnel when online, local jobs always.

Internet gate: TCP check to 1.1.1.1/8.8.8.8 before tunnel/GitHub/Telegram.
If offline at boot, tunnel is deferred; ensure_tunnel_online retries every minute.
BLE / Ollama / HTTP local continue regardless.
"""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
import time
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SKILLS_ROOT = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SKILLS_ROOT))
import jobs as jobmod  # noqa: E402

INTERVAL_FALLBACK = float(os.environ.get("POLLER_INTERVAL_SEC", "5"))
HOST = os.environ.get("POLLER_BIND", "127.0.0.1")
PORT = int(os.environ.get("POLLER_PORT", "8799"))
SYSTEM_STATUS_JSON = Path("/home/rootrecord/Database/SYSTEM/status/system-status.json")
ENERGY_ROOT = Path(os.environ.get("ENERGY_ROOT", "/home/rootrecord/Database/ENERGY"))
HOSTNAME = os.environ.get("POLLER_PUBLIC_HOST", "rootserver.rootrecord.cloud")
TOKEN_FILE = Path(os.environ.get("CLOUDFLARED_TOKEN_FILE", str(Path.home() / ".cloudflared" / "rootserver.token")))
CLOUDFLARED_BIN = os.environ.get("CLOUDFLARED_BIN", str(SCRIPTS.parent / "bin" / "cloudflared"))
ENABLE_TUNNEL = os.environ.get("POLLER_ENABLE_TUNNEL", "1") != "0"
TUNNEL_READY_TIMEOUT_SEC = float(os.environ.get("POLLER_TUNNEL_READY_TIMEOUT_SEC", "45"))

_latest = "starting"
_lock = threading.Lock()
_stop = threading.Event()
_tunnel_ready = threading.Event()
_tunnel_proc: subprocess.Popen | None = None
_internet_ok = False
_internet_last_log = 0.0
_tunnel_start_attempts = 0


def full_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def log(msg: str) -> None:
    print(msg, flush=True)


def heartbeat_line() -> str:
    try:
        return f"{full_timestamp()}{_energy_log_line()}"
    except Exception:
        return f"{full_timestamp()}Poller is online."


def internet_ok(force: bool = False) -> bool:
    """TCP reachability — does not use local DNS stub."""
    global _internet_ok
    for host, port in (("1.1.1.1", 443), ("8.8.8.8", 53), ("1.0.0.1", 443)):
        try:
            with socket.create_connection((host, port), timeout=2.5):
                _internet_ok = True
                return True
        except OSError:
            continue
    _internet_ok = False
    return False


def tunnel_alive() -> bool:
    return _tunnel_proc is not None and _tunnel_proc.poll() is None


def ensure_tunnel_online() -> None:
    global _tunnel_start_attempts, _internet_last_log
    if not ENABLE_TUNNEL:
        return
    if internet_ok(force=True):
        if tunnel_alive():
            return
        _tunnel_start_attempts += 1
        log(f"{full_timestamp()}internet OK — starting Cloudflare tunnel (attempt {_tunnel_start_attempts})")
        _tunnel_ready.clear()
        if start_tunnel():
            wait_for_tunnel_ready()
        return
    now = time.time()
    if now - _internet_last_log >= 55:
        log(f"{full_timestamp()}internet DOWN — net services waiting (retry ~60s)")
        _internet_last_log = now


def _read_energy_json(rel: str):
    try:
        return json.loads((ENERGY_ROOT / rel).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _fmt_w(n) -> str:
    if not isinstance(n, (int, float)):
        return "No data"
    if float(n) == int(n):
        return f"{int(n)} W"
    return f"{n:.1f} W"


def _fmt_soc(n) -> str:
    if not isinstance(n, (int, float)):
        return "No data"
    if float(n) == int(n):
        return f"{int(n)}%"
    return f"{n:.1f}%"


def _sqlite_board() -> dict | None:
    try:
        from energy.db.latest import board_snapshot
        return board_snapshot()
    except Exception:
        return None


def build_energy_snapshot() -> dict:
    sqlite = _sqlite_board()
    delta_sql = (sqlite or {}).get("delta2") if isinstance(sqlite, dict) else None
    river_sql = (sqlite or {}).get("river2pro") if isinstance(sqlite, dict) else None
    delta_soc = _read_energy_json("soc/delta2-last.json")
    river_soc = _read_energy_json("soc/river2pro-last.json")
    delta_w = _read_energy_json("watts/delta2-last.json")
    river_w = _read_energy_json("watts/river2pro-last.json")

    def soc_of(sql_row, json_blob):
        if isinstance(sql_row, dict) and sql_row.get("soc") is not None:
            return sql_row["soc"]
        if isinstance(json_blob, dict) and json_blob.get("soc") is not None:
            return json_blob["soc"]
        return None

    def watt_of(sql_row, key, json_blob):
        if isinstance(sql_row, dict) and sql_row.get(key) is not None:
            return sql_row[key]
        if isinstance(json_blob, dict) and json_blob.get(key) is not None:
            return json_blob[key]
        return None

    d_soc = soc_of(delta_sql, delta_soc)
    r_soc = soc_of(river_sql, river_soc)
    solar = watt_of(delta_sql, "solar_input_power", delta_w)
    if solar is None:
        solar = watt_of(river_sql, "solar_input_power", river_w)
    ac = watt_of(delta_sql, "ac_output_power", delta_w)
    if ac is None:
        ac = watt_of(river_sql, "ac_output_power", river_w)
    usbc = watt_of(delta_sql, "usbc_output_power", delta_w)
    if usbc is None:
        usbc = watt_of(river_sql, "usbc_output_power", river_w)
    has_delta = d_soc is not None or isinstance(delta_sql, dict) or bool(delta_soc or delta_w)
    has_river = r_soc is not None or isinstance(river_sql, dict) or bool(river_soc or river_w)
    live = has_delta or has_river
    ats = []
    for row in (delta_sql, river_sql):
        if isinstance(row, dict) and row.get("observed_at"):
            ats.append(row["observed_at"])
    for blob in (delta_soc, river_soc, delta_w, river_w):
        if isinstance(blob, dict) and blob.get("at"):
            ats.append(blob["at"])
    updated = sorted(ats)[-1] if ats else None
    source = "sqlite" if (delta_sql or river_sql) else str(ENERGY_ROOT)
    b3 = None
    if isinstance(delta_sql, dict):
        for exp in delta_sql.get("expansions") or []:
            if exp.get("soc") is not None or exp.get("sn"):
                b3 = {"sn": exp.get("sn"), "slot": exp.get("slot"),
                      "soc": _fmt_soc(exp.get("soc")) if exp.get("soc") is not None else "No data"}
                break
    return {
        "status": "live" if live else "Waiting",
        "solarInW": _fmt_w(solar) if live else "No data",
        "deltaSoc": _fmt_soc(d_soc) if d_soc is not None else ("No data" if not has_delta else "Waiting"),
        "riverSoc": _fmt_soc(r_soc) if r_soc is not None else ("Waiting" if not has_river else "No data"),
        "acOut": _fmt_w(ac) if ac is not None else ("Waiting" if live else "No data"),
        "usbC": _fmt_w(usbc) if usbc is not None else ("No data" if live else "No data"),
        "b3": b3, "buckets": "Waiting",
        "ports": {"ac": _fmt_w(ac) if ac is not None else "Waiting", "usbc": _fmt_w(usbc) if usbc is not None else "No data"},
        "source": source,
        "files": {"present": {
            "delta2Soc": d_soc is not None or bool(delta_soc),
            "river2proSoc": r_soc is not None or bool(river_soc),
            "delta2Watts": bool(delta_w) or (isinstance(delta_sql, dict) and delta_sql.get("ac_output_power") is not None),
            "river2proWatts": bool(river_w) or (isinstance(river_sql, dict) and river_sql.get("ac_output_power") is not None),
            "sqlite": bool(delta_sql or river_sql),
        }},
        "updated": updated,
        "note": "Measured samples. SQLite canonical; JSON compatibility.",
    }


def _energy_log_line() -> str:
    snap = build_energy_snapshot()
    parts = [f"status={snap.get('status')}", f"B2={snap.get('deltaSoc')}", f"B1={snap.get('riverSoc')}",
             f"solar={snap.get('solarInW')}", f"ac={snap.get('acOut')}", f"usbc={snap.get('usbC')}", f"src={snap.get('source')}"]
    b3 = snap.get("b3")
    if isinstance(b3, dict):
        parts.insert(3, f"B3={b3.get('soc')}")
    return "ENERGY  " + "  ".join(parts)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return
    def _send(self, code: int, body: str, ctype: str = "text/plain; charset=utf-8") -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _proxy_aeyes(self) -> None:
        """Reverse-proxy /aeyes* to local a-eyes cam server (127.0.0.1:8791)."""
        import urllib.error
        import urllib.request
        target = f"http://127.0.0.1:8791{self.path}"
        headers = {}
        if self.headers.get("Cookie"):
            headers["Cookie"] = self.headers.get("Cookie")
        if self.headers.get("Content-Type"):
            headers["Content-Type"] = self.headers.get("Content-Type")
        body = None
        if self.command == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length > 0 else b""
        req = urllib.request.Request(target, data=body, headers=headers, method=self.command)
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
                self.send_response(resp.status)
                for key in ("Content-Type", "Set-Cookie", "Location", "Cache-Control"):
                    val = resp.headers.get(key)
                    if val:
                        self.send_header(key, val)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            ctype = e.headers.get("Content-Type") if e.headers else None
            if ctype:
                self.send_header("Content-Type", ctype)
            for key in ("Set-Cookie", "Location"):
                val = e.headers.get(key) if e.headers else None
                if val:
                    self.send_header(key, val)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self._send(502, f"a-eyes proxy error: {type(e).__name__}\n")

    def do_GET(self) -> None:
        if self.path.startswith("/aeyes"):
            self._proxy_aeyes()
            return
        with _lock:
            line = _latest
        if self.path in ("/", "/health", "/poller"):
            self._send(200, line + "\n"); return
        if self.path == "/json":
            self._send(200, json.dumps({"ok": True, "host": HOSTNAME, "line": line}) + "\n", "application/json; charset=utf-8"); return
        if self.path in ("/energy", "/energy/", "/api/energy"):
            self._send(200, json.dumps(build_energy_snapshot()) + "\n", "application/json; charset=utf-8"); return
        if self.path in ("/system-status.json", "/system-status", "/api/system-status"):
            try:
                body = SYSTEM_STATUS_JSON.read_text(encoding="utf-8")
                self._send(200, body if body.endswith("\n") else body + "\n", "application/json; charset=utf-8")
            except FileNotFoundError:
                self._send(503, json.dumps({"ok": False, "error": "system-status not ready"}) + "\n", "application/json; charset=utf-8")
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "error": type(e).__name__}) + "\n", "application/json; charset=utf-8")
            return
        self._send(404, "not found\n")


    def do_POST(self) -> None:
        if self.path.startswith("/aeyes"):
            self._proxy_aeyes()
            return
        self._send(404, "not found\n")


def _cloudflared_interesting(text: str) -> str | None:
    t = text.strip()
    if not t:
        return None
    drop_sub = ("CONNECTIVITY PRE-CHECKS", "precheck ", "SUMMARY:", "DNS Resolution", "UDP Connectivity",
                "TCP Connectivity", "Cloudflare API", "curve preferences", "ICMP proxy", "Generated Connector",
                "Initial protocol", "Starting metrics", "Version ", "GOOS:", "Settings: map", "Environmental variables",
                "Autoupdate frequency", "Metrics server")
    if any(s in t for s in drop_sub) or t.startswith("|") or t.startswith("+--"):
        return None
    low = t.lower()
    if " err " in f" {low} " or t.startswith("ERR") or "error=" in low:
        if "timeout" in low:
            return "tunnel timeout — reconnecting"
        if "terminated" in low:
            return "tunnel connection terminated"
        if "lookup" in low or "dns" in low or "srv" in low or "argotunnel" in low:
            return "tunnel DNS/edge discovery failed — check internet + resolver (try 1.1.1.1)"
        return f"cloudflared ERR: {t[:120]}"
    if t.startswith("WRN") or " WRN " in f" {t} ":
        if "timeout" in low:
            return "tunnel timeout — reconnecting"
        return f"cloudflared WRN: {t[:120]}"
    if "Registered tunnel connection" in t:
        idx = loc = ""
        for part in t.split():
            if part.startswith("connIndex="):
                idx = part.split("=", 1)[1]
            if part.startswith("location="):
                loc = part.split("=", 1)[1]
        return f"tunnel connected  conn={idx or '?'}  edge={loc or '?'}"
    if "Starting tunnel" in t:
        return "tunnel starting"
    if "Updated to new configuration" in t:
        if "rootserver.rootrecord.cloud" in t:
            return "tunnel ingress  rootserver.rootrecord.cloud → 127.0.0.1:8799"
        return "tunnel ingress  updated"
    if "Connected to Cloudflare" in t:
        return "tunnel connected to Cloudflare"
    return None


def start_tunnel() -> bool:
    global _tunnel_proc
    if not ENABLE_TUNNEL:
        log(f"{full_timestamp()}Tunnel disabled (POLLER_ENABLE_TUNNEL=0).")
        _tunnel_ready.set()
        return False
    if not Path(CLOUDFLARED_BIN).is_file():
        log(f"{full_timestamp()}Tunnel DOWN — cloudflared missing at {CLOUDFLARED_BIN}")
        return False
    if not TOKEN_FILE.is_file():
        log(f"{full_timestamp()}Tunnel DOWN — token file missing: {TOKEN_FILE}")
        return False
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        log(f"{full_timestamp()}Tunnel DOWN — empty token file")
        return False
    mode = os.environ.get("POLLER_TUNNEL_MODE", "token").lower()
    if mode == "quick":
        cmd = [CLOUDFLARED_BIN, "tunnel", "--no-autoupdate", "--url", f"http://{HOST}:{PORT}"]
        popen_kwargs: dict = {}
    else:
        cmd = [CLOUDFLARED_BIN, "tunnel", "--no-autoupdate", "run"]
        env = os.environ.copy()
        env["TUNNEL_TOKEN"] = token
        popen_kwargs = {"env": env}
    log(f"{full_timestamp()}Starting cloudflared mode={mode} public_host={HOSTNAME}")
    _tunnel_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, **popen_kwargs)

    def pump() -> None:
        assert _tunnel_proc is not None and _tunnel_proc.stdout is not None
        for line in _tunnel_proc.stdout:
            text = line.rstrip()
            interesting = _cloudflared_interesting(text)
            if interesting:
                log(f"{full_timestamp()}{interesting}")
            if "Registered tunnel connection" in text or "Connected to Cloudflare" in text:
                if not _tunnel_ready.is_set():
                    log(f"{full_timestamp()}Tunnel READY — first connection registered.")
                    _tunnel_ready.set()
            if _stop.is_set():
                break
        if _tunnel_proc.poll() is not None and not _tunnel_ready.is_set():
            log(f"{full_timestamp()}Tunnel DOWN — cloudflared exited before ready (code={_tunnel_proc.returncode}).")

    threading.Thread(target=pump, name="cloudflared-log", daemon=True).start()
    return True


def wait_for_tunnel_ready() -> None:
    if not ENABLE_TUNNEL or _tunnel_ready.is_set():
        return
    log(f"{full_timestamp()}Waiting for tunnel register (timeout={TUNNEL_READY_TIMEOUT_SEC:.0f}s)…")
    if not _tunnel_ready.wait(timeout=TUNNEL_READY_TIMEOUT_SEC):
        log(f"{full_timestamp()}Tunnel WAITING — no register within {TUNNEL_READY_TIMEOUT_SEC:.0f}s; continuing.")


def _is_ecoflow_job(jid: str) -> bool:
    return jid.startswith("ecoflow_") or jid in ("delta2_read", "river2pro_read")


def run_command_job(job: dict) -> None:
    jid = job.get("id", "?")
    cmd = (job.get("command") or "").strip()
    if not cmd:
        log(f"{full_timestamp()}job:{jid} SKIP — empty command")
        return
    timeout = float(job.get("timeout_sec") or 120)
    cwd = (job.get("cwd") or "").strip() or None
    env = os.environ.copy()
    extra = job.get("env") or {}
    if isinstance(extra, dict):
        env.update({str(k): str(v) for k, v in extra.items()})
    quiet = jid in ("github_sync_all", "github_setup_remotes", "github_autopush")
    eco = _is_ecoflow_job(jid)
    # EcoFlow: no RUN spam — only the final SUMMARY line (or a quiet FAIL)
    if not quiet and not eco:
        log(f"{full_timestamp()}job:{jid} RUN  {cmd}")
    try:
        r = subprocess.run(["bash", "-lc", cmd], cwd=cwd, env=env, timeout=timeout, capture_output=True, text=True)
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        if r.returncode == 0:
            if eco:
                # One clean line: prefer SUMMARY=; fold INTERNAL= the same way.
                # Skip STATUS= (redundant when SUMMARY is present).
                summary = None
                for ln in out.splitlines():
                    s = ln.strip()
                    if s.startswith("SUMMARY=") or s.startswith("INTERNAL="):
                        summary = s
                        break
                if summary:
                    log(f"{full_timestamp()}  ▸  {summary}")
                else:
                    log(f"{full_timestamp()}  ▸  {jid} OK")
            elif out:
                for line in out.splitlines()[:40]:
                    line = line.strip()
                    if not line:
                        continue
                    if quiet and any(line.startswith(p) for p in ("[ok]", "[skip]", "[clone]", "Updated", "Added", "Done.")):
                        continue
                    log(f"{full_timestamp()}job:{jid} | {line}")
            elif not quiet:
                log(f"{full_timestamp()}job:{jid} OK")
        else:
            if eco:
                # Only log real failures (both BLE and API down) — one line
                reason = ""
                for ln in (out or err).splitlines():
                    s = ln.strip()
                    if s.startswith("No data") or s.startswith("WAITING"):
                        reason = s
                        break
                if reason:
                    log(f"{full_timestamp()}  ✗  {jid}  {reason}")
                else:
                    log(f"{full_timestamp()}  ✗  {jid} FAIL code={r.returncode}")
            else:
                log(f"{full_timestamp()}job:{jid} FAIL code={r.returncode}")
                for line in (err or out).splitlines()[:20]:
                    log(f"{full_timestamp()}job:{jid} ! {line}")
    except subprocess.TimeoutExpired:
        log(f"{full_timestamp()}job:{jid} TIMEOUT after {timeout:.0f}s")
    except Exception as e:
        log(f"{full_timestamp()}job:{jid} ERROR {e}")


def run_builtin(job: dict) -> None:
    global _latest, HOSTNAME, TOKEN_FILE, CLOUDFLARED_BIN, TUNNEL_READY_TIMEOUT_SEC
    jid = job.get("id", "?")
    name = (job.get("builtin") or "").strip()
    if name == "heartbeat":
        line = heartbeat_line()
        with _lock:
            _latest = line
        log(line)
        return
    if name == "self_process":
        log(f"{full_timestamp()}boot:p0 self_process pid={os.getpid()}")
        return
    if name == "tunnel_start":
        if job.get("public_host"):
            HOSTNAME = str(job["public_host"])
        if job.get("token_file"):
            TOKEN_FILE = Path(str(job["token_file"]))
        if job.get("cloudflared_bin"):
            CLOUDFLARED_BIN = str(job["cloudflared_bin"])
        if job.get("timeout_sec"):
            TUNNEL_READY_TIMEOUT_SEC = float(job["timeout_sec"])
        log(f"{full_timestamp()}boot:p1 cloudflare_tunnel host={HOSTNAME}")
        if not internet_ok(force=True):
            log(f"{full_timestamp()}internet DOWN at boot — tunnel DEFERRED; local jobs continue; retry every minute")
            return
        log(f"{full_timestamp()}internet OK at boot — starting tunnel")
        if start_tunnel():
            wait_for_tunnel_ready()
        elif ENABLE_TUNNEL:
            log(f"{full_timestamp()}Tunnel DOWN — continuing with local jobs only.")
        return
    if name == "ensure_tunnel_online":
        ensure_tunnel_online()
        return
    log(f"{full_timestamp()}job:{jid} UNKNOWN builtin={name!r}")


def run_job(job: dict) -> None:
    if not job.get("enabled"):
        return
    if job.get("needs_internet") and not internet_ok(force=True):
        log(f"{full_timestamp()}job:{job.get('id', '?')} SKIP — offline (will retry when internet is up)")
        return
    builtin = (job.get("builtin") or "").strip()
    if builtin:
        run_builtin(job)
        return
    run_command_job(job)


def enabled_jobs(section: list) -> list:
    return [j for j in section if isinstance(j, dict) and j.get("enabled")]


def _normalize_hhmm(raw: object) -> str | None:
    if not isinstance(raw, str) or ":" not in raw:
        return None
    try:
        hh, mm = (int(x) for x in raw.strip().split(":", 1))
    except ValueError:
        return None
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        return None
    return f"{hh:02d}:{mm:02d}"


def scheduler_loop() -> None:
    sec_jobs = enabled_jobs(getattr(jobmod, "EVERY_SECONDS", []))
    min_jobs = enabled_jobs(getattr(jobmod, "EVERY_MINUTE", []))
    hour_jobs = enabled_jobs(getattr(jobmod, "EVERY_HOUR", []))
    at_jobs = enabled_jobs(getattr(jobmod, "ON_AT", []))
    next_due: dict[str, float] = {}
    now = time.monotonic()
    for j in sec_jobs:
        next_due[j["id"]] = now
    last_minute: int | None = None
    last_hour: int | None = None
    fired_at: set[str] = set()
    log(f"{full_timestamp()}scheduler  every_seconds={len(sec_jobs)}  every_minute={len(min_jobs)}  every_hour={len(hour_jobs)}  on_at={len(at_jobs)}")
    while not _stop.is_set():
        wall = datetime.now().astimezone()
        mono = time.monotonic()
        for j in sec_jobs:
            jid = j["id"]
            if mono >= next_due.get(jid, 0):
                run_job(j)
                interval = float(j.get("interval_sec") or INTERVAL_FALLBACK)
                next_due[jid] = mono + max(0.2, interval)
        minute, hour = wall.minute, wall.hour
        hm = f"{hour:02d}:{minute:02d}"
        day = wall.date().isoformat()
        if last_minute is None:
            last_minute, last_hour = minute, hour
        else:
            if minute != last_minute:
                for j in min_jobs:
                    only = j.get("only_at_minutes") or []
                    if only and minute not in only:
                        continue
                    run_job(j)
                for j in at_jobs:
                    times = {t for raw in (j.get("at_times") or []) if (t := _normalize_hhmm(raw))}
                    if hm not in times:
                        continue
                    key = f"{j['id']}|{day}|{hm}"
                    if key in fired_at:
                        continue
                    run_job(j)
                    fired_at.add(key)
                last_minute = minute
            if hour != last_hour and minute == 0:
                for j in hour_jobs:
                    only = j.get("only_at_hours") or []
                    if only and hour not in only:
                        continue
                    run_job(j)
                last_hour = hour
            elif hour != last_hour:
                last_hour = hour
            if fired_at:
                fired_at = {k for k in fired_at if f"|{day}|" in k}
        _stop.wait(0.25)


def shutdown(*_args) -> None:
    _stop.set()
    _tunnel_ready.set()
    global _tunnel_proc
    if _tunnel_proc and _tunnel_proc.poll() is None:
        _tunnel_proc.terminate()
        try:
            _tunnel_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _tunnel_proc.kill()


def run_on_boot() -> None:
    boot = [j for j in enabled_jobs(getattr(jobmod, "ON_BOOT", [])) if isinstance(j, dict)]
    boot.sort(key=lambda j: int(j.get("priority", 100)))
    log(f"{full_timestamp()}boot:start  jobs={len(boot)}")
    for j in boot:
        log(f"{full_timestamp()}boot:run  priority={j.get('priority', '?')}  id={j.get('id', '?')}")
        run_job(j)
    log(f"{full_timestamp()}boot:done")


def main() -> int:
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    threading.Thread(target=server.serve_forever, name="http", daemon=True).start()
    log(f"{full_timestamp()}HTTP listening on http://{HOST}:{PORT} (open access on bind)")
    run_on_boot()
    for j in enabled_jobs(getattr(jobmod, "ONCE_AT_START", [])):
        run_job(j)
    scheduler_loop()
    server.shutdown()
    shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
