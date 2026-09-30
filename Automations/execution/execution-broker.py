# ==============================================================================
# FILE: Automations/execution/execution-broker.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Answer a capability request from the registry. Refuses restarts, writes, and sends."""
from __future__ import annotations  # info: from __future__ import annotations
import json, subprocess, sys  # info: import json , subprocess , sys
from pathlib import Path  # info: from pathlib import Path

import audit  # info: import audit

ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
REGISTRY = ROOT / "5 - RootRecord-Library" / "Documentation" / "02-agents" / "capabilities" / "capability-registry.json"  # info: set REGISTRY
STATE = ROOT / "2 - RootRecord-Database" / "System" / "status" / "rootrecord-state.json"  # info: set STATE
VERIFY = ROOT / "verify.sh"  # info: set VERIFY

# ====================================================
# SECTION: function load_registry
# What it does: Load the capability list. Does not launch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_registry() -> list[dict]:  # info: def load_registry
    doc = json.loads(REGISTRY.read_text(encoding="utf-8"))  # info: set doc
    return list(doc.get("capabilities") or [])  # info: return list ( doc . get ( "capabilities" ) or [ ] )

# ====================================================
# SECTION: function find_cap
# What it does: Return one capability or None. Does not launch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def find_cap(caps: list[dict], cap_id: str):  # info: def find_cap
    for row in caps:  # info: for row in caps
        if row.get("id") == cap_id:  # info: if row . get ( "id" ) == cap_id
            return row  # info: return row
    return None  # info: return None

# ====================================================
# SECTION: function state_doc
# What it does: Read the snapshot or an empty dict. Does not write it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def state_doc() -> dict:  # info: def state_doc
    try:  # info: try :
        return json.loads(STATE.read_text(encoding="utf-8"))  # info: return json . loads ( STATE . read_text
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return {}  # info: return { }

# ====================================================
# SECTION: function read_body
# What it does: Build the read-only result for an allowed inspect. Does not restart anything.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_body(cap_id: str, service: str) -> dict:  # info: def read_body
    doc = state_doc()  # info: set doc
    if cap_id == "inspect_relay":  # info: if cap_id == "inspect_relay"
        return {"value": (doc.get("services") or {}).get("council_relay")}  # info: return { "value" : ( doc . get ( "services" ) or { } ) . get ( "council_relay" ) }
    if cap_id == "inspect_github_sync":  # info: if cap_id == "inspect_github_sync"
        return {"value": (doc.get("services") or {}).get("github_sync")}  # info: return { "value" : ( doc . get ( "services" ) or { } ) . get ( "github_sync" ) }
    if cap_id == "inspect_energy":  # info: if cap_id == "inspect_energy"
        return {"value": (doc.get("domains") or {}).get("energy")}  # info: return { "value" : ( doc . get ( "domains" ) or { } ) . get ( "energy" ) }
    if cap_id == "inspect_npu":  # info: if cap_id == "inspect_npu"
        return {"value": (doc.get("domains") or {}).get("host", {}).get("npu") or doc.get("npu_device_present")}  # info: return { "value" : ( doc . get ( "domains" ) or { } ) . get ( "host" , { } ) . get ( "npu" ) or doc . get ( "npu_device_present" ) }
    if cap_id == "inspect_system":  # info: if cap_id == "inspect_system"
        resources = (doc.get("system") or {}).get("resources") or {}  # info: set resources
        return {"value": resources.get("value")}  # info: return { "value" : resources . get ( "value" ) }
    if cap_id == "inspect_service":  # info: if cap_id == "inspect_service"
        return {"value": (doc.get("services") or {}).get(service)}  # info: return { "value" : ( doc . get ( "services" ) or { } ) . get ( service ) }
    if cap_id == "run_verification":  # info: if cap_id == "run_verification"
        proc = subprocess.run(["bash", str(VERIFY)], text=True, capture_output=True, timeout=60)  # info: set proc
        return {"exit_code": proc.returncode, "lines": (proc.stdout or "")[-2000:]}  # info: return { "exit_code" : proc . returncode , "lines" : ( proc . stdout or "" ) [ - 2000 : ] }
    return {"value": None, "reason": "no reader"}  # info: return { "value" : None , "reason" : "no reader" }

# ====================================================
# SECTION: function decide
# What it does: Allow a read or refuse. Writes one audit line. Does not launch a side effect.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def decide(agent: str, cap_id: str, service: str) -> tuple[int, dict]:  # info: def decide
    cap = find_cap(load_registry(), cap_id)  # info: set cap
    if cap is None:  # info: if cap is None
        result = {"result": "refused", "reason": "unknown capability"}  # info: set result
        audit.append({"agent": agent, "capability": cap_id, "result": "refused"})  # info: call audit . append
        return 2, result  # info: return 2 , result
    allowed = (cap.get("agents") or {}).get(agent) == "allowed"  # info: set allowed
    if not allowed or not cap.get("agent_may_invoke") or cap.get("side_effects"):  # info: if not allowed or not cap . get ( "agent_may_invoke" ) or cap . get ( "side_effects" )
        why = cap.get("why_not") or {"kind": "gated", "reason": "agent may not invoke this"}  # info: set why
        result = {"result": "refused", "capability": cap_id, "why_not": why}  # info: set result
        audit.append({"agent": agent, "capability": cap_id, "result": "refused", "kind": why.get("kind")})  # info: call audit . append
        return 3, result  # info: return 3 , result
    body = read_body(cap_id, service)  # info: set body
    result = {"result": "ok", "capability": cap_id, "body": body}  # info: set result
    audit.append({"agent": agent, "capability": cap_id, "result": "ok"})  # info: call audit . append
    return 0, result  # info: return 0 , result

# ====================================================
# SECTION: function main
# What it does: Request one capability. Prints JSON. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if len(sys.argv) < 4 or sys.argv[1] != "request":  # info: if len ( sys . argv ) < 4 or sys . argv [ 1 ] != "request"
        print("usage: execution-broker.py request <ava|bruce|carly> <capability> [service]", file=sys.stderr)  # info: call print
        return 2  # info: return 2
    agent, cap_id = sys.argv[2], sys.argv[3]  # info: agent , cap_id = sys . argv [ 2 ] , sys . argv [ 3 ]
    service = sys.argv[4] if len(sys.argv) > 4 else ""  # info: set service
    code, result = decide(agent, cap_id, service)  # info: code , result = decide ( agent , cap_id , service )
    print(json.dumps(result, indent=2))  # info: call print
    return code  # info: return code

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
