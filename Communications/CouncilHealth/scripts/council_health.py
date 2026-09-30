# ==============================================================================
# FILE: Communications/CouncilHealth/scripts/council_health.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Council health check for the live relay.

Reports one council-relay.py process, Telegram getMe for Ava/Bruce/Carly, and
409 lines in the relay log. Does not call getUpdates, start or stop the relay,
or load a model unless RR_COUNCIL_HEALTH_PROBE=1 and --probe are both set.
Sends only when --alert and RR_RELAY_REPLIES=1, after a 30-minute cooldown.
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
LIB = ROOT / "lib"  # info: set LIB
sys.path.insert(0, str(LIB))  # info: sys . path . insert ( 0 ,
from envload import load_env  # noqa: E402

PACIFIC = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server")  # info: set PACIFIC
DATA = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Communications/CouncilHealth")  # info: set DATA
LOG_DIR = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/CouncilHealth")  # info: set LOG_DIR
RELAY_LOG = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/council-relay.log")  # info: set RELAY_LOG
RELAY_CONF = PACIFIC / "Communications" / "telegram" / "config" / "relay.conf"  # info: set RELAY_CONF
RUN_INFER = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"  # info: set RUN_INFER
ALERT_COOLDOWN_S = 30 * 60  # info: set ALERT_COOLDOWN_S
BOTS = ("ava", "bruce", "carly")  # info: set BOTS
# ====================================================
# SECTION: TOKEN_KEYS
# What it does: Set TOKEN_KEYS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
TOKEN_KEYS = {  # info: set TOKEN_KEYS
    "ava": "TELEGRAM_AVA_TOKEN",  # info: "ava" : "TELEGRAM_AVA_TOKEN" ,
    "bruce": "TELEGRAM_BRUCE_TOKEN",  # info: "bruce" : "TELEGRAM_BRUCE_TOKEN" ,
    "carly": "TELEGRAM_CARLY_TOKEN",  # info: "carly" : "TELEGRAM_CARLY_TOKEN" ,
}  # info: }


# ====================================================
# SECTION: function _load_kv
# What it does:  load kv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_kv(path: Path) -> dict[str, str]:  # info: def _load_kv
    out: dict[str, str] = {}  # info: set out
    if not path.is_file():  # info: if not path . is_file ( ) :
        return out  # info: return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():  # info: for line in path . read_text ( encoding
        s = line.strip()  # info: set s
        if not s or s.startswith("#") or "=" not in s:
            continue  # info: continue
        k, _, v = s.partition("=")  # info: k , _ , v = s .
        out[k.strip()] = v.strip().strip('"').strip("'")  # info: out [ k . strip ( ) ]
    return out  # info: return out


# ====================================================
# SECTION: function _relay_pids
# What it does:  relay pids.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _relay_pids() -> list[int]:  # info: def _relay_pids
    try:  # info: try :
        out = subprocess.check_output(  # info: set out
            ["pgrep", "-f", r"^python3 .+/council-relay\.py"],  # info: [ "pgrep" , "-f" , r"^python3 .+/council-relay\.py" ] ,
            text=True,  # info: set text
            timeout=5,  # info: set timeout
        )  # info: )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):  # info: except ( subprocess . CalledProcessError , subprocess .
        return []  # info: return [ ]
    pids: list[int] = []  # info: set pids
    for line in out.splitlines():  # info: for line in out . splitlines ( )
        line = line.strip()  # info: set line
        if line.isdigit():  # info: if line . isdigit ( ) :
            pids.append(int(line))  # info: pids . append ( int ( line )
    return pids  # info: return pids


# ====================================================
# SECTION: function _get_me
# What it does:  get me.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get_me(token: str) -> dict[str, Any]:  # info: def _get_me
    if not token:  # info: if not token :
        return {"ok": False, "detail": "no_token"}  # info: return { "ok" : False , "detail" :
    url = f"https://api.telegram.org/bot{token}/getMe"  # info: set url
    try:  # info: try :
        with urllib.request.urlopen(url, timeout=8) as resp:  # info: with urllib . request . urlopen ( url
            body = json.loads(resp.read().decode("utf-8", errors="replace"))  # info: set body
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(e).__name__}"}  # info: return { "ok" : False , "detail" :
    if isinstance(body, dict) and body.get("ok"):  # info: if isinstance ( body , dict ) and
        user = body.get("result") or {}  # info: set user
        return {"ok": True, "username": user.get("username")}  # info: return { "ok" : True , "username" :
    return {"ok": False, "detail": "getMe_false"}  # info: return { "ok" : False , "detail" :


# ====================================================
# SECTION: function _tail_409
# What it does:  tail 409.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _tail_409(path: Path) -> dict[str, Any]:  # info: def _tail_409
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {"ok": True, "detail": "no_log", "conflict_409": 0}  # info: return { "ok" : True , "detail" :
    try:  # info: try :
        text = path.read_bytes()[-120_000:].decode("utf-8", errors="replace")  # info: set text
    except OSError as e:  # info: except OSError as e :
        return {"ok": False, "detail": f"log_read:{type(e).__name__}", "conflict_409": 0}  # info: return { "ok" : False , "detail" :
    lines = text.splitlines()  # info: set lines
    start = 0  # info: set start
    for i, ln in enumerate(lines):  # info: for i , ln in enumerate ( lines
        if "[ok] relay chat=" in ln:  # info: if "[ok] relay chat=" in ln :
            start = i  # info: set start
    recent = lines[start:]  # info: set recent
    conflict = sum(1 for ln in recent if "409" in ln)  # info: set conflict
    return {"ok": conflict < 1, "conflict_409": conflict, "since_listen": True}  # info: return { "ok" : conflict < 1 ,


# ====================================================
# SECTION: function _probe
# What it does:  probe.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _probe() -> dict[str, Any]:  # info: def _probe
    if os.environ.get("RR_COUNCIL_HEALTH_PROBE", "0").strip() != "1":  # info: if os . environ . get ( "RR_COUNCIL_HEALTH_PROBE"
        return {"ok": None, "detail": "skipped"}  # info: return { "ok" : None , "detail" :
    if not RUN_INFER.is_file():  # info: if not RUN_INFER . is_file ( ) :
        return {"ok": False, "detail": "no_run_infer"}  # info: return { "ok" : False , "detail" :
    try:  # info: try :
        completed = subprocess.run(  # info: set completed
            [str(RUN_INFER), "ava", "Reply with OK only."],  # info: call [
            capture_output=True,  # info: set capture_output
            text=True,  # info: set text
            timeout=120,  # info: set timeout
        )  # info: )
    except (subprocess.TimeoutExpired, OSError) as e:  # info: except ( subprocess . TimeoutExpired , OSError )
        return {"ok": False, "detail": type(e).__name__}  # info: return { "ok" : False , "detail" :
    text = (completed.stdout or "").strip()  # info: set text
    return {"ok": bool(text) and completed.returncode == 0, "preview": text[:40]}  # info: return { "ok" : bool ( text )


# ====================================================
# SECTION: function _alert
# What it does:  alert.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _alert(text: str, chat_id: str) -> dict[str, Any]:  # info: def _alert
    if os.environ.get("RR_RELAY_REPLIES", "0").strip() != "1":  # info: if os . environ . get ( "RR_RELAY_REPLIES"
        return {"ok": False, "detail": "replies_off"}  # info: return { "ok" : False , "detail" :
    load_env()  # info: call load_env
    token = (os.environ.get("TELEGRAM_AVA_TOKEN") or "").strip()  # info: set token
    if not token or not chat_id:  # info: if not token or not chat_id :
        return {"ok": False, "detail": "no_token_or_chat"}  # info: return { "ok" : False , "detail" :
    payload = json.dumps({"chat_id": chat_id, "text": text[:3500], "disable_web_page_preview": True}).encode()  # info: set payload
    req = urllib.request.Request(  # info: set req
        f"https://api.telegram.org/bot{token}/sendMessage",  # info: f" https://api.telegram.org/bot { token } /sendMessage " ,
        data=payload,  # info: set data
        headers={"Content-Type": "application/json"},  # info: set headers
        method="POST",  # info: set method
    )  # info: )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=12) as resp:  # info: with urllib . request . urlopen ( req
            body = json.loads(resp.read().decode("utf-8", errors="replace"))  # info: set body
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "detail": type(e).__name__}  # info: return { "ok" : False , "detail" :
    return {"ok": bool(isinstance(body, dict) and body.get("ok"))}  # info: return { "ok" : bool ( isinstance (


# ====================================================
# SECTION: function check
# What it does: check.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def check(*, alert: bool, probe_chat: bool, network: bool) -> dict[str, Any]:  # info: def check
    load_env()  # info: call load_env
    pids = _relay_pids()  # info: set pids
    problems: list[str] = []  # info: set problems
    if len(pids) == 0:  # info: if len ( pids ) == 0 :
        problems.append("council relay process missing")  # info: problems . append ( "council relay process missing" )
    elif len(pids) > 1:  # info: elif len ( pids ) > 1 :
        problems.append(f"duplicate council relay pids={pids}")  # info: problems . append ( f" duplicate council relay pids= { pids

    if network:  # info: if network :
        bots = {name: _get_me(os.environ.get(TOKEN_KEYS[name], "")) for name in BOTS}  # info: set bots
        for name, row in bots.items():  # info: for name , row in bots . items
            if not row.get("ok"):  # info: if not row . get ( "ok" )
                problems.append(f"{name} getMe failed ({row.get('detail')})")  # info: problems . append ( f" { name }
    else:  # info: else :
        bots = {name: {"ok": None, "detail": "skipped"} for name in BOTS}  # info: set bots

    log_issues = _tail_409(RELAY_LOG)  # info: set log_issues
    if not log_issues.get("ok"):  # info: if not log_issues . get ( "ok" )
        problems.append(f"getUpdates 409×{log_issues.get('conflict_409')} since last relay listen")  # info: problems . append ( f" getUpdates 409× { log_issues

    if probe_chat:  # info: if probe_chat :
        chat_probe = _probe()  # info: set chat_probe
        if chat_probe.get("ok") is False:  # info: if chat_probe . get ( "ok" ) is
            problems.append(f"model probe failed ({chat_probe.get('detail')})")  # info: problems . append ( f" model probe failed ( { chat_probe
    else:  # info: else :
        chat_probe = {"ok": None, "detail": "skipped"}  # info: set chat_probe

    ok = not problems  # info: set ok
    report: dict[str, Any] = {  # info: set report
        "ok": ok,  # info: "ok" : ok ,
        "ts": time.time(),  # info: "ts" : time . time ( ) ,
        "relay_pids": pids,  # info: "relay_pids" : pids ,
        "bots": bots,  # info: "bots" : bots ,
        "log": log_issues,  # info: "log" : log_issues ,
        "chat_probe": chat_probe,  # info: "chat_probe" : chat_probe ,
        "problems": problems,  # info: "problems" : problems ,
        "alerted": False,  # info: "alerted" : False ,
    }  # info: }

    state_path = DATA / "state.json"  # info: set state_path
    state: dict[str, Any] = {}  # info: set state
    if state_path.is_file():  # info: if state_path . is_file ( ) :
        try:  # info: try :
            raw = json.loads(state_path.read_text(encoding="utf-8"))  # info: set raw
            if isinstance(raw, dict):  # info: if isinstance ( raw , dict ) :
                state = raw  # info: set state
        except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
            state = {}  # info: set state
    state["last"] = {k: report[k] for k in ("ok", "ts", "problems", "alerted")}  # info: state [ "last" ] = { k :
    state["last_ok"] = time.time() if ok else state.get("last_ok")  # info: state [ "last_ok" ] = time . time
    state["last_fail"] = None if ok else time.time()  # info: state [ "last_fail" ] = None if ok

    if alert and problems:  # info: if alert and problems :
        last_alert = float(state.get("last_alert_ts") or 0)  # info: set last_alert
        if time.time() - last_alert >= ALERT_COOLDOWN_S:  # info: if time . time ( ) - last_alert
            chat_id = _load_kv(RELAY_CONF).get("COUNCIL_CHAT_ID", "")  # info: set chat_id
            msg = (  # info: set msg
                "Council health check — systems not fully functional:\n"  # info: "Council health check — systems not fully functional:\n"
                + "\n".join(f"• {p}" for p in problems[:8])  # info: + "\n" . join ( f" • {
            )  # info: )
            sent = _alert(msg, chat_id)  # info: set sent
            if sent.get("ok"):  # info: if sent . get ( "ok" ) :
                state["last_alert_ts"] = time.time()  # info: state [ "last_alert_ts" ] = time . time
                report["alerted"] = True  # info: report [ "alerted" ] = True
                state["last"]["alerted"] = True  # info: state [ "last" ] [ "alerted" ] =

    DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
    LOG_DIR.mkdir(parents=True, exist_ok=True)  # info: LOG_DIR . mkdir ( parents = True ,
    (DATA / "latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")  # info: call (
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")  # info: state_path . write_text ( json . dumps (
    line = {  # info: set line
        "ts": report["ts"],  # info: "ts" : report [ "ts" ] ,
        "ok": ok,  # info: "ok" : ok ,
        "problems": problems,  # info: "problems" : problems ,
        "alerted": report["alerted"],  # info: "alerted" : report [ "alerted" ] ,
        "pids": pids,  # info: "pids" : pids ,
    }  # info: }
    with (LOG_DIR / "council-health.jsonl").open("a", encoding="utf-8") as fh:  # info: with ( LOG_DIR / "council-health.jsonl" ) . open
        fh.write(json.dumps(line) + "\n")  # info: fh . write ( json . dumps (
    return report  # info: return report


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    parser = argparse.ArgumentParser(description="Council relay health check")  # info: set parser
    parser.add_argument("--no-alert", action="store_true")  # info: parser . add_argument ( "--no-alert" , action =
    parser.add_argument("--alert", action="store_true")  # info: parser . add_argument ( "--alert" , action =
    parser.add_argument("--no-probe", action="store_true")  # info: parser . add_argument ( "--no-probe" , action =
    parser.add_argument("--probe", action="store_true")  # info: parser . add_argument ( "--probe" , action =
    parser.add_argument("--no-network", action="store_true")  # info: parser . add_argument ( "--no-network" , action =
    parser.add_argument("--json", action="store_true")  # info: parser . add_argument ( "--json" , action =
    args = parser.parse_args(argv)  # info: set args
    alert = bool(args.alert) and not args.no_alert  # info: set alert
    probe = bool(args.probe) and not args.no_probe  # info: set probe
    report = check(alert=alert, probe_chat=probe, network=not args.no_network)  # info: set report
    if args.json:  # info: if args . json :
        print(json.dumps(report, indent=2))  # info: call print
    else:  # info: else :
        status = "OK" if report.get("ok") else "FAIL"  # info: set status
        print(f"council-health {status}")  # info: call print
        for prob in report.get("problems") or []:  # info: for prob in report . get ( "problems"
            print(f"  - {prob}")  # info: call print
        print(f"  alerted={report.get('alerted')}")  # info: call print
    if args.no_network:  # info: if args . no_network :
        return 0  # info: return 0
    return 0 if report.get("ok") else 1  # info: return 0 if report . get ( "ok"


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
