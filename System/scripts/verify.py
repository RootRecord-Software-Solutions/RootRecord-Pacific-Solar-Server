# ==============================================================================
# FILE: System/scripts/verify.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Print PASS, WARN, or FAIL for the live desk. Does not send, launch, or restart."""
from __future__ import annotations  # info: from __future__ import annotations
import json, os, sys  # info: import json , os , sys
from pathlib import Path  # info: from pathlib import Path

ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
PACIFIC = ROOT / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server"  # info: set PACIFIC
LINES: list[tuple[str, str]] = []  # info: set LINES

# ====================================================
# SECTION: function add
# What it does: Record one verify line. Does not exit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add(level: str, text: str) -> None:  # info: def add
    LINES.append((level, text))  # info: LINES . append ( ( level , text ) )

# ====================================================
# SECTION: function read
# What it does: Read a text file or return empty. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read(path: Path) -> str:  # info: def read
    try:  # info: try :
        return path.read_text(encoding="utf-8")  # info: return path . read_text ( encoding = "utf-8" )
    except OSError:  # info: except OSError :
        return ""  # info: return ""

# ====================================================
# SECTION: function python_scripts
# What it does: Count python processes whose argv runs one script. Does not signal them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def python_scripts(script_name: str) -> int:  # info: def python_scripts
    count = 0  # info: set count
    for name in os.listdir("/proc"):  # info: for name in os . listdir ( "/proc" )
        if not name.isdigit():  # info: if not name . isdigit ( )
            continue  # info: continue
        try:  # info: try :
            raw = Path(f"/proc/{name}/cmdline").read_bytes()  # info: set raw
        except OSError:  # info: except OSError :
            continue  # info: continue
        cmd = raw.replace(b"\0", b" ").decode("utf-8", "replace")  # info: set cmd
        toks = cmd.split()  # info: set toks
        if len(toks) < 2 or toks[0].rsplit("/", 1)[-1] not in ("python", "python3"):  # info: if len ( toks ) < 2 or toks [ 0 ] . rsplit
            continue  # info: continue
        if any(t.rsplit("/", 1)[-1] == script_name for t in toks[1:]):  # info: if any ( t . rsplit ( "/" , 1 ) [ - 1 ] == script_name for t in toks [ 1 : ] )
            count += 1  # info: set count
    return count  # info: return count

# ====================================================
# SECTION: function exe_present
# What it does: True when a process path ends with this executable name. Ignores editor sandboxes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def exe_present(exe: str) -> bool:  # info: def exe_present
    for name in os.listdir("/proc"):  # info: for name in os . listdir ( "/proc" )
        if not name.isdigit():  # info: if not name . isdigit ( )
            continue  # info: continue
        try:  # info: try :
            raw = Path(f"/proc/{name}/cmdline").read_bytes()  # info: set raw
        except OSError:  # info: except OSError :
            continue  # info: continue
        cmd = raw.replace(b"\0", b" ").decode("utf-8", "replace")  # info: set cmd
        if "cursorsandbox" in cmd:  # info: if "cursorsandbox" in cmd
            continue  # info: continue
        if any(t.rsplit("/", 1)[-1] == exe for t in cmd.split()):  # info: if any ( t . rsplit ( "/" , 1 ) [ - 1 ] == exe for t in cmd . split ( ) )
            return True  # info: return True
    return False  # info: return False

# ====================================================
# SECTION: function source_checks
# What it does: Checks that durable files say the standing rules. Does not need the live desk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def source_checks() -> None:  # info: def source_checks
    handoff = ROOT / "5 - RootRecord-Library" / "Documentation" / "01-operations" / "HANDOFF.md"  # info: set handoff
    add("PASS" if handoff.is_file() else "FAIL", "handoff file")  # info: call add
    relay = read(PACIFIC / "Communications" / "telegram" / "scripts" / "ensure-relay.sh")  # info: set relay
    jobs = read(PACIFIC / "Automations" / "scripts" / "jobs.py")  # info: set jobs
    conf = read(PACIFIC / "Communications" / "telegram" / "config" / "relay.conf")  # info: set conf
    skip = read(PACIFIC / "Github" / "scripts" / "ecosystem-skip-autocommit.txt")  # info: set skip
    registry = read(PACIFIC / "System" / "config" / "program-registry.json")  # info: set registry
    if "RR_NPU_ONLY=1" in relay and "llama3.2:3b" in relay:  # info: if "RR_NPU_ONLY=1" in relay and "llama3.2:3b" in relay
        add("PASS", "relay observes NPU llama3.2:3b")  # info: call add
    else:  # info: else :
        add("FAIL", "relay script missing NPU 3b settings")  # info: call add
    if "Council relay" in jobs and "llama3.2:3b" in jobs and "no Ollama fallback" in jobs:  # info: if "Council relay" in jobs and "llama3.2:3b" in jobs and "no Ollama fallback" in jobs
        add("PASS", "jobs.py council line matches NPU llama3.2:3b")  # info: call add
    else:  # info: else :
        add("WARN", "configuration drift: jobs.py council line does not name llama3.2:3b with no Ollama fallback")  # info: call add
    if "SANDBOX_REPLIES=1" in conf:  # info: if "SANDBOX_REPLIES=1" in conf
        add("PASS", "sandbox replies configured on")  # info: call add
    else:  # info: else :
        add("WARN", "sandbox replies are not 1 in relay.conf")  # info: call add
    add("WARN", "live council and private DMs intentionally gated (RR_RELAY_REPLIES default 0)")  # info: call add
    if '"agent_launchable": true' in registry:  # info: if '"agent_launchable": true' in registry
        add("FAIL", "a program is marked agent_launchable")  # info: call add
    else:  # info: else :
        add("PASS", "no program is agent_launchable")  # info: call add
    caps_path = ROOT / "5 - RootRecord-Library" / "Documentation" / "02-agents" / "capabilities" / "capability-registry.json"  # info: set caps_path
    try:  # info: try :
        caps = json.loads(caps_path.read_text(encoding="utf-8")).get("capabilities") or []  # info: set caps
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        caps = []  # info: set caps
    restart = next((row for row in caps if row.get("id") == "restart_known_service"), None)  # info: set restart
    if restart and restart.get("agent_may_invoke") is False and restart.get("agents", {}).get("bruce") == "denied":  # info: if restart and restart . get ( "agent_may_invoke" ) is False and restart . get ( "agents" , { } ) . get ( "bruce" ) == "denied"
        add("PASS", "restart_known_service stays agent-locked")  # info: call add
    else:  # info: else :
        add("FAIL", "restart capability missing or unlocked")  # info: call add
    if "2 - RootRecord-Database/System/status" in skip:  # info: if "2 - RootRecord-Database/System/status" in skip
        add("PASS", "generated state is on the auto-commit skip list")  # info: call add
    else:  # info: else :
        add("FAIL", "System/status is missing from ecosystem-skip-autocommit.txt")  # info: call add

# ====================================================
# SECTION: function runtime_checks
# What it does: Process and device checks. Skips them when this machine is not the live poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def runtime_checks() -> None:  # info: def runtime_checks
    pollers = python_scripts("rootserver_poller.py")  # info: set pollers
    if pollers == 0:  # info: if pollers == 0
        add("WARN", "poller not running here; process checks skipped")  # info: call add
        return  # info: return
    if pollers == 1:  # info: if pollers == 1
        add("PASS", "rootserver poller")  # info: call add
    else:  # info: else :
        add("FAIL", f"rootserver poller count={pollers}")  # info: call add
    relays = python_scripts("council-relay.py")  # info: set relays
    if relays == 1:  # info: if relays == 1
        add("PASS", "council relay")  # info: call add
    else:  # info: else :
        add("FAIL", f"council relay count={relays}")  # info: call add
    add("PASS" if Path("/dev/accel/accel0").exists() else "FAIL", "NPU device")  # info: call add
    add("PASS" if exe_present("ollama") else "WARN", "Ollama process")  # info: call add
    add("PASS" if not exe_present("flm") else "WARN", "FLM idle between replies" if not exe_present("flm") else "FLM serve is resident")  # info: call add
    add("PASS" if exe_present("cloudflared") else "WARN", "cloudflared")  # info: call add
    desk = ROOT / "2 - RootRecord-Database" / "Intake" / "desk-live.txt"  # info: set desk
    state = ROOT / "2 - RootRecord-Database" / "System" / "status" / "rootrecord-state.json"  # info: set state
    add("PASS" if desk.is_file() else "WARN", "desk telemetry file")  # info: call add
    add("PASS" if state.is_file() else "WARN", "state snapshot file")  # info: call add
    add("WARN", "root monitor not required; unknown is not a failure")  # info: call add

# ====================================================
# SECTION: function main
# What it does: Print the report and exit 1 when any line failed. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    source_checks()  # info: call source_checks
    runtime_checks()  # info: call runtime_checks
    failed = 0  # info: set failed
    for level, text in LINES:  # info: for level , text in LINES
        print(f"[{level}] {text}")  # info: call print
        if level == "FAIL":  # info: if level == "FAIL"
            failed += 1  # info: set failed
    return 1 if failed else 0  # info: return 1 if failed else 0

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
