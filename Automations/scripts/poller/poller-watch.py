#!/usr/bin/env python3
"""Pretty live view of the rootserver poller log (colors + filter).

# INFO — MUST HAVE (future agents):
# Ctrl-C OR closing this window MUST stop the entire stack (poller, cloudflared,
# systemd unit). Never exit the window while leaving those processes up.
"""
from __future__ import annotations

import atexit
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def aeyes_solar_state():
    """
    Solar-aware A-EYES display state from generated NOAA report.
    """
    from pathlib import Path
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import re

    tz = ZoneInfo("Pacific/Honolulu")

    report = Path(
        "/home/rootrecord/Database/WEATHER/Hawai'i/reports/"
        "0 Level Processing/solar_calculation_table_current.md"
    )

    if not report.exists():
        return None

    text = report.read_text(errors="ignore")
    now = datetime.now(tz)

    month_day = now.strftime("%b %-d")

    sunrise = None
    sunset = None

    for line in text.splitlines():
        if month_day in line and "|" in line:
            parts = [x.strip() for x in line.split("|")]
            clocks = [
                x for x in parts
                if re.match(r"^\d{1,2}:\d{2}", x)
            ]
            if len(clocks) >= 2:
                sunrise = clocks[0]
                sunset = clocks[1]
                break

    if not sunrise or not sunset:
        return None

    def parse_clock(v):
        h, m = map(int, v.split(":"))
        return now.replace(hour=h, minute=m, second=0, microsecond=0)

    sr = parse_clock(sunrise)
    ss = parse_clock(sunset)

    if now < sr:
        delta = sr - now
        hours = int(delta.total_seconds() // 3600)
        mins = int((delta.total_seconds() % 3600) // 60)
        return f"waiting — sunrise {sunrise} HST ({hours:02d}h {mins:02d}m)"

    if now > ss:
        tomorrow_sr = sr + timedelta(days=1)
        delta = tomorrow_sr - now
        hours = int(delta.total_seconds() // 3600)
        mins = int((delta.total_seconds() % 3600) // 60)
        return f"night — sunrise {tomorrow_sr.strftime('%H:%M')} HST ({hours:02d}h {mins:02d}m)"

    return f"daylight active — sunset {sunset} HST"



POLLER_DIR = Path(__file__).resolve().parent
SCRIPTS = POLLER_DIR.parent  # Automations/scripts
STOP = SCRIPTS / "stack" / "stop-poller-stack.sh"
LOG = Path(
    os.environ.get(
        "POLLER_LOG",
        "/home/rootrecord/Database/LOGS/Automations/rootserver-poller.log",
    )
)
HOST = os.environ.get("POLLER_PUBLIC_HOST", "rootserver.rootrecord.cloud")
LOCAL = os.environ.get("POLLER_LOCAL", "http://127.0.0.1:8799/")

# Solarized Dark palette — truecolor ANSI
RST = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[38;2;133;153;0m"       # solarized green
BRIGHT_GREEN = "\033[38;2;133;153;0m"
CYAN = "\033[38;2;42;161;152m"      # solarized cyan
YELLOW = "\033[38;2;181;137;0m"      # solarized yellow
RED = "\033[38;2;220;50;47m"         # solarized red
MAGENTA = "\033[38;2;211;54;130m"    # solarized magenta
WHITE = "\033[38;2;238;232;213m"     # solarized base2
BLUE = "\033[38;2;38;139;210m"       # solarized blue
ORANGE = "\033[38;2;203;75;22m"      # solarized orange
BASE0 = "\033[38;2;131;148;150m"     # solarized base0

_stop_done = False


def unit_state() -> str:
    try:
        r = subprocess.run(
            ["systemctl", "--user", "is-active", "rr-rootserver-poller.service"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return (r.stdout or r.stderr or "unknown").strip()
    except Exception:
        return "unknown"


def stop_everything(reason: str = "exit") -> None:
    """Idempotent full stack stop. Called on Ctrl-C, window close, or signals."""
    global _stop_done
    if _stop_done:
        return
    _stop_done = True
    try:
        print(
            f"\n{YELLOW}{reason} — stopping ENTIRE stack "
            f"(poller + tunnel + unit)…{RST}",
            flush=True,
        )
    except Exception:
        pass
    try:
        subprocess.run(["bash", str(STOP)], check=False, timeout=60)
    except Exception as e:
        try:
            print(f"{RED}stop failed: {e}{RST}", flush=True)
        except Exception:
            pass
    try:
        print(f"{DIM}stack stop requested — window exiting{RST}", flush=True)
    except Exception:
        pass


def _on_signal(signum: int, _frame) -> None:
    names = {
        signal.SIGINT: "Ctrl-C",
        signal.SIGTERM: "SIGTERM",
        signal.SIGHUP: "window close (SIGHUP)",
    }
    reason = names.get(signum, f"signal {signum}")
    stop_everything(reason)
    sys.exit(0)


def _install_handlers() -> None:
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            signal.signal(sig, _on_signal)
        except Exception:
            pass
    atexit.register(lambda: stop_everything("window exit"))


def banner() -> None:
    state = unit_state()
    if state == "active":
        st = f"{BRIGHT_GREEN}● {state}{RST}"
    elif state in ("activating", "reloading"):
        st = f"{YELLOW}● {state}{RST}"
    else:
        st = f"{RED}● {state}{RST}"
    width = 64
    bar = "─" * (width - 2)
    print(f"{CYAN}{BOLD}╭─ RootRecord poller {bar}{RST}", flush=True)
    print(f"{CYAN}│{RST}  public   {WHITE}https://{HOST}/{RST}", flush=True)
    print(f"{CYAN}│{RST}  local    {DIM}{LOCAL}{RST}", flush=True)
    print(f"{CYAN}│{RST}  systemd  {st}", flush=True)
    print(f"{CYAN}│{RST}  jobs     {DIM}{SCRIPTS / 'jobs.py'}{RST}", flush=True)
    print(f"{CYAN}│{RST}  log      {DIM}{LOG}{RST}", flush=True)
    print(
        f"{CYAN}│{RST}  {YELLOW}Ctrl-C or close window stops EVERY process"
        f" (poller + cloudflared + unit){RST}",
        flush=True,
    )
    print(f"{CYAN}{BOLD}╰{bar}──{RST}", flush=True)
    print(flush=True)


def split_ts(line: str) -> tuple[str, str]:
    if len(line) >= 25 and line[10:11] == "T" and line[19:20] in "+-":
        return line[:25], line[25:]
    return "", line


def clock(ts: str) -> str:
    if "T" in ts and len(ts) >= 19:
        return ts[11:19]
    return ts or "--:--:--"


def _edge_bits(s: str) -> str:
    idx = loc = ""
    for part in s.replace('"', " ").split():
        if part.startswith("connIndex="):
            idx = part.split("=", 1)[1]
        if part.startswith("location="):
            loc = part.split("=", 1)[1]
    bits = []
    if idx:
        bits.append(f"conn={idx}")
    if loc:
        bits.append(f"edge={loc}")
    return "  ".join(bits)


def format_line(raw: str) -> str | None:
    line = raw.rstrip("\n")
    if not line:
        return None
    ts, rest = split_ts(line)
    t = clock(ts)
    body = rest

    if (
        "Error opening input:" in body
        or ("[in#" in body and "No route" in body)
        or "No route to host" in body
    ):
        return None

    if (
        "a-eyes" in body.lower()
        and (
            "FAILED" in body
            or "No route to host" in body
            or "grab failed" in body.lower()
            or "Connection to tcp://" in body
        )
    ):
        solar = aeyes_solar_state()
        if solar:
            return f"  {DIM}{t}{RST}  {DIM}📷 A-EYES {solar}{RST}"
        return None

    noise = (
        "CONNECTIVITY PRE-CHECKS",
        "precheck ",
        "curve preferences",
        "ICMP proxy",
        "Generated Connector",
        "Initial protocol",
        "Starting metrics",
        "Environmental variables",
        "GOOS:",
        "Settings: map",
        "SUMMARY:",
        "DNS Resolution",
        "UDP Connectivity",
        "TCP Connectivity",
        "Cloudflare API",
        "Updated to new configuration",
        "Version ",
    )
    if any(n in body for n in noise) or body.strip().startswith("|") or body.strip().startswith("+--"):
        return None

    if body.startswith("cloudflared: "):
        raw_cf = body[len("cloudflared: ") :]
        if "Registered tunnel connection" in raw_cf:
            bits = _edge_bits(raw_cf)
            return f"  {DIM}{t}{RST}  {CYAN}◆{RST}  {CYAN}tunnel connected{RST}  {DIM}{bits}{RST}"
        if "Starting tunnel" in raw_cf:
            return f"  {DIM}{t}{RST}  {MAGENTA}▲{RST}  {MAGENTA}tunnel starting{RST}"
        if "error=" in raw_cf.lower() or " ERR" in raw_cf or raw_cf.startswith("ERR"):
            short = "tunnel timeout — reconnecting" if "timeout" in raw_cf.lower() else "tunnel error"
            return f"  {DIM}{t}{RST}  {YELLOW}!{RST}  {YELLOW}{short}{RST}"
        if " WRN" in raw_cf or raw_cf.startswith("WRN"):
            short = "tunnel timeout — reconnecting" if "timeout" in raw_cf.lower() else "tunnel warn"
            return f"  {DIM}{t}{RST}  {YELLOW}!{RST}  {YELLOW}{short}{RST}"
        return None

    if body.startswith("Poller is online"):
        return f"  {DIM}{t}{RST}  {BRIGHT_GREEN}●{RST}  {GREEN}Poller is online.{RST}"
    if "Tunnel READY" in body:
        return f"  {DIM}{t}{RST}  {CYAN}◆{RST}  {CYAN}{BOLD}Tunnel READY{RST}{DIM} — registered{RST}"
    if "Tunnel DOWN" in body or "Tunnel WAITING" in body:
        return f"  {DIM}{t}{RST}  {RED}✗{RST}  {RED}{body}{RST}"
    if body.startswith("Waiting for tunnel"):
        return f"  {DIM}{t}{RST}  {YELLOW}…{RST}  {YELLOW}waiting for tunnel…{RST}"
    if body.startswith("Starting cloudflared"):
        return f"  {DIM}{t}{RST}  {MAGENTA}▲{RST}  {MAGENTA}starting cloudflared{RST}"
    if body.startswith("tunnel starting"):
        return f"  {DIM}{t}{RST}  {MAGENTA}▲{RST}  {MAGENTA}{body}{RST}"
    if body.startswith("tunnel connected"):
        return f"  {DIM}{t}{RST}  {CYAN}◆{RST}  {CYAN}{body}{RST}"
    if body.startswith("tunnel ingress"):
        return f"  {DIM}{t}{RST}  {CYAN}→{RST}  {WHITE}{body}{RST}"
    if body.startswith("HTTP listening"):
        return f"  {DIM}{t}{RST}  {WHITE}○{RST}  HTTP listening on :8799"
    if body.startswith("scheduler"):
        return f"  {DIM}{t}{RST}  {WHITE}☰{RST}  {body}"
    if "OK wrote/updated" in body and "worklog" in body.lower():
        short = body if len(body) <= 90 else body[:87] + "…"
        return f"  {DIM}{t}{RST}  {BRIGHT_GREEN}📓{RST}  {GREEN}{short}{RST}"
    if body.startswith("SYSTEM "):
        return f"  {DIM}{t}{RST}  {CYAN}🖥{RST}  {CYAN}{body}{RST}"
    if body.startswith("ENERGY "):
        return f"  {DIM}{t}{RST}  {YELLOW}⚡{RST}  {YELLOW}{body}{RST}"
    if body.startswith("SUMMARY="):
        payload = body[len("SUMMARY="):].strip()
        fields = dict(part.split("=", 1) for part in payload.split() if "=" in part)
        device = payload.split()[0] if payload else "unknown"
        soc = fields.get("soc", "—")
        solar = fields.get("solar", "—")
        ac = fields.get("ac_out", "—")
        usbc = fields.get("usbc", "—")
        src = fields.get("src", "—")
        src_mark = "✓" if src == "api" else src
        return (
            f"  {DIM}{t}{RST}  {YELLOW}⚡{RST}  "
            f"{YELLOW}ECOFLOW{RST}  {BOLD}{device}{RST}  "
            f"SOC={soc}  solar={solar}  AC={ac}  USB-C={usbc}  "
            f"src={src_mark}"
        )

    if body.startswith("STATUS="):
        return f"  {DIM}{t}{RST}  {DIM}▸{RST}  {body}"
    if body.startswith("job:"):
        if " | " in body:
            payload = body.split(" | ", 1)[1].strip()
            if "FAIL" in payload or "ERROR" in payload or "failed" in payload.lower():
                return f"  {DIM}{t}{RST}  {RED}✗{RST}  {RED}{payload}{RST}"
            repo = ""
            rest = payload
            if "] [" in payload:
                try:
                    after = payload.split("] ", 1)[1]
                    if after.startswith("[") and "]" in after:
                        repo = after[1 : after.index("]")]
                        rest = after[after.index("]") + 1 :].strip()
                except Exception:
                    rest = payload
            if "SUMMARY=" in rest:
                summary = rest.split("SUMMARY=", 1)[1].strip()
                fields = dict(part.split("=", 1) for part in summary.split() if "=" in part)
                device = summary.split()[0] if summary else "unknown"
                soc = fields.get("soc", "—")
                solar = fields.get("solar", "—")
                ac = fields.get("ac_out", "—")
                usbc = fields.get("usbc", "—")
                src = fields.get("src", "—")
                src_mark = "✓" if src == "api" else src
                return (
                    f"  {DIM}{t}{RST}  {YELLOW}⚡{RST}  "
                    f"{YELLOW}ECOFLOW{RST}  {BOLD}{device}{RST}  "
                    f"SOC={soc}  solar={solar}  AC={ac}  USB-C={usbc}  "
                    f"src={src_mark}"
                )
            if (
                "a_eyes_frame_grab" in body.lower()
                or "a-eyes" in rest.lower()
                or "a_eyes" in rest.lower()
                or "a-eyes" in payload.lower()
                or "a_eyes" in payload.lower()
                or "Connection to tcp://" in rest
                or "No route to host" in rest
                or "grab failed" in rest.lower()
            ):
                if (
                    "FAILED" in rest
                    or "FAIL" in rest
                    or "grab failed" in rest.lower()
                    or "No route to host" in rest
                ):
                    solar = aeyes_solar_state()
                    if solar and (solar.startswith("waiting") or solar.startswith("complete")):
                        return f"  {DIM}{t}{RST}  {DIM}📷 A-EYES {solar}{RST}"
                    return f"  {DIM}{t}{RST}  {RED}📷 A-EYES offline — DVR unreachable{RST}"
            if (
                "a_eyes" in rest.lower()
                or "a-eyes" in rest.lower()
                or "a-eyes" in payload.lower()
            ):
                if "FAILED" in rest or "FAIL" in rest or "grab failed" in rest.lower():
                    solar = aeyes_solar_state()
                    if solar and (solar.startswith("waiting") or solar.startswith("complete")):
                        return f"  {DIM}{t}{RST}  {DIM}📷{RST}  {DIM}A-EYES {solar}{RST}"
                    return f"  {DIM}{t}{RST}  {RED}📷{RST}  {RED}A-EYES offline — DVR unreachable{RST}"
                short = rest
                if len(short) > 90:
                    short = short[:87] + "…"
                return f"  {DIM}{t}{RST}  {DIM}📷{RST}  {DIM}A-EYES  {short}{RST}"
            is_github_job = any(
                key in body.lower()
                for key in (
                    "github_sync_all",
                    "github_setup_remotes",
                    "github_autopush",
                    "github repo",
                )
            )
            if is_github_job:
                if "worklog" in rest.lower() or "WORKLOG" in rest or "worklog_current" in rest:
                    short = rest if len(rest) <= 90 else rest[:87] + "…"
                    return f"  {DIM}{t}{RST}  {BRIGHT_GREEN}📓{RST}  {GREEN}{short}{RST}"
                if "no changes" in rest or rest.startswith("—"):
                    if repo:
                        return f"  {DIM}{t}{RST}  {DIM}▸{RST}  {DIM}github {repo} · no changes{RST}"
                    return None
                if rest.startswith("↑") or " files" in rest or "pushed" in rest.lower():
                    n = ""
                    for tok in rest.replace("file(s)", "files").split():
                        if tok.isdigit():
                            n = tok
                            break
                    label = repo or "repo"
                    if n:
                        return f"  {DIM}{t}{RST}  {GREEN}▸{RST}  {GREEN}github {label}{RST}  {DIM}↑ {n} files{RST}"
                    return f"  {DIM}{t}{RST}  {GREEN}▸{RST}  {GREEN}github {label}{RST}  {DIM}{rest}{RST}"
                if rest.startswith("✗") or "FAIL" in rest or "ERROR" in rest:
                    label = repo or "repo"
                    return f"  {DIM}{t}{RST}  {RED}✗{RST}  {RED}github {label}{RST}  {DIM}{rest}{RST}"
                short = rest if len(rest) <= 90 else rest[:87] + "…"
                label = repo or "repo"
                return f"  {DIM}{t}{RST}  {DIM}▸{RST}  {DIM}github {label}{RST}  {DIM}{short}{RST}"
            if "worklog" in rest.lower() or "WORKLOG" in rest:
                short = rest if len(rest) <= 90 else rest[:87] + "…"
                return f"  {DIM}{t}{RST}  {BRIGHT_GREEN}📓{RST}  {GREEN}{short}{RST}"
            short = rest if len(rest) <= 100 else rest[:97] + "…"
            return f"  {DIM}{t}{RST}  {DIM}▸{RST}  {DIM}{short}{RST}"
        if "FAIL" in body or "ERROR" in body:
            return f"  {DIM}{t}{RST}  {RED}✗{RST}  {RED}{body}{RST}"
        return f"  {DIM}{t}{RST}  {DIM}▸{RST}  {DIM}{body}{RST}"

    if "FAIL" in body or "ERROR" in body or "error" in body.lower():
        return f"  {DIM}{t}{RST}  {RED}✗{RST}  {RED}{body}{RST}"
    if body.startswith("boot:"):
        return f"  {DIM}{t}{RST}  {BLUE}▶{RST}  {body}"
    short = body if len(body) <= 110 else body[:107] + "…"
    return f"  {DIM}{t}{RST}  {DIM}▸{RST}  {DIM}{short}{RST}"


def main() -> None:
    _install_handlers()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.touch(exist_ok=True)
    try:
        existing = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        existing = []
    banner()
    for line in existing[-80:]:
        out = format_line(line)
        if out:
            print(out, flush=True)
    with LOG.open("r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if line:
                out = format_line(line)
                if out:
                    print(out, flush=True)
            else:
                time.sleep(0.25)


if __name__ == "__main__":
    main()
