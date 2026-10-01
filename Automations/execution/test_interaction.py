# ==============================================================================
# FILE: Automations/execution/test_interaction.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Exercise interaction modes without calling the NPU or the Cursor API."""
from __future__ import annotations  # info: from __future__ import annotations
import json, os, subprocess, sys, tempfile  # info: import json , os , subprocess , sys , tempfile
from pathlib import Path  # info: from pathlib import Path

ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
HERE = Path(__file__).resolve().parent  # info: set HERE
SANDBOX = "-1004406495175"  # info: set SANDBOX
FAILS = []  # info: set FAILS

# ====================================================
# SECTION: function check
# What it does: Record one assertion. Does not exit on the first miss.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def check(name: str, ok: bool) -> None:  # info: def check
    print(("PASS " if ok else "FAIL ") + name)  # info: call print
    if not ok:  # info: if not ok
        FAILS.append(name)  # info: FAILS . append ( name )

# ====================================================
# SECTION: function quiet
# What it does: Council stub with no questions. Does not call a model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def quiet(voice: str, prompt: str) -> str:  # info: def quiet
    return '{"interpretation":"ok","questions":[],"proposed_work_order_fields":{"target":"desk"},"objections":[],"stop":true,"reject":false}'  # info: return '{"interpretation":"ok","questions":[],"proposed_work_order_fields":{"target":"desk"},"objections":[],"stop":true,"reject":false}'

# ====================================================
# SECTION: function ask
# What it does: Council stub that always asks one question. Does not call a model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ask(voice: str, prompt: str) -> str:  # info: def ask
    return '{"interpretation":"need","questions":["which repo"],"proposed_work_order_fields":{},"objections":[],"stop":false,"reject":false}'  # info: return '{"interpretation":"need","questions":["which repo"],"proposed_work_order_fields":{},"objections":[],"stop":false,"reject":false}'

# ====================================================
# SECTION: function carly_no
# What it does: Carly rejects. The other voices do not. Does not call a model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def carly_no(voice: str, prompt: str) -> str:  # info: def carly_no
    if voice == "carly":  # info: if voice == "carly"
        return '{"interpretation":"no","questions":[],"proposed_work_order_fields":{},"objections":["unsafe"],"stop":true,"reject":true}'  # info: return '{"interpretation":"no","questions":[],"proposed_work_order_fields":{},"objections":["unsafe"],"stop":true,"reject":true}'
    return quiet(voice, prompt)  # info: return quiet ( voice , prompt )

# ====================================================
# SECTION: function main
# What it does: Run the mode, handoff, broker, recovery, and gate checks. Does not enable live gates.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    tmp = Path(tempfile.mkdtemp(prefix="rr-interaction-"))  # info: set tmp
    os.environ["RR_REQUEST_DIR"] = str(tmp / "requests")  # info: os . environ [ "RR_REQUEST_DIR" ] = str ( tmp / "requests" )
    os.environ["RR_EXECUTION_GATES"] = str(tmp / "gates.json")  # info: os . environ [ "RR_EXECUTION_GATES" ] = str ( tmp / "gates.json" )
    os.environ["RR_PRINCIPAL_REGISTRY"] = str(tmp / "principals.json")  # info: os . environ [ "RR_PRINCIPAL_REGISTRY" ] = str ( tmp / "principals.json" )
    os.environ["RR_EXECUTION_AUDIT"] = str(tmp / "audit.jsonl")  # info: os . environ [ "RR_EXECUTION_AUDIT" ] = str ( tmp / "audit.jsonl" )
    os.environ["RR_SUPERVISOR_STATE"] = str(tmp / "supervisor")  # info: os . environ [ "RR_SUPERVISOR_STATE" ] = str ( tmp / "supervisor" )
    people = {"schema_version": 1, "match_key": "telegram_user_id", "authorized_build_operators": [{"principal_id": "rootrecordadmin", "username": "rootrecordadmin", "telegram_user_id": 42}, {"principal_id": "WildEcho94", "username": "WildEcho94", "telegram_user_id": None}, {"principal_id": "Crazychickenlady12", "username": "Crazychickenlady12", "telegram_user_id": None}], "agents": {"ava": {"can_build": False}, "bruce": {"can_build": False}, "carly": {"can_build": False}}}  # info: set people
    (tmp / "principals.json").write_text(json.dumps(people), encoding="utf-8")  # info: ( tmp / "principals.json" ) . write_text ( json . dumps ( people ) , encoding = "utf-8" )
    sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 , str ( HERE ) )
    import gates  # info: import gates
    import interaction  # info: import interaction
    raised = False  # info: set raised
    try:  # info: try :
        gates.set_gate("modes.build", True, confirmed=False)  # info: call gates . set_gate
    except PermissionError:  # info: except PermissionError
        raised = True  # info: set raised
    check("enable without confirm fails", raised)  # info: call check
    gates.set_gate("modes.build", True, confirmed=True)  # info: call gates . set_gate
    gates.set_gate("steps.build.handoff", True, confirmed=True)  # info: call gates . set_gate
    live = interaction.seed({"chat_id": "-1004367256267", "sandbox_chat_id": SANDBOX, "text": "build this", "message_id": 1, "from_id": 42, "username": "rootrecordadmin"})  # info: set live
    check("live chat refused", live.get("result") == "refused")  # info: call check
    spoof = interaction.seed({"chat_id": SANDBOX, "sandbox_chat_id": SANDBOX, "text": "build this", "message_id": 2, "from_id": 99, "username": "rootrecordadmin"})  # info: set spoof
    check("username is not the match key", spoof.get("interaction_mode") == "work_order" and spoof["authorization"]["build_authorized"] is False)  # info: call check
    original = spoof["original_request"]["text"]  # info: set original
    asked = interaction.council(spoof["request_id"], infer=ask)  # info: set asked
    asked = interaction.answer(spoof["request_id"], "the library", infer=ask)  # info: set asked
    asked = interaction.answer(spoof["request_id"], "still the library", infer=ask)  # info: set asked
    check("question cap reaches NEEDS_DECISION", asked.get("status") == "NEEDS_DECISION")  # info: call check
    check("original text unchanged", asked["original_request"]["text"] == original)  # info: call check
    standard = interaction.seed({"chat_id": SANDBOX, "sandbox_chat_id": SANDBOX, "text": "please add a page", "message_id": 3, "from_id": 7, "username": "someone"})  # info: set standard
    drafted = interaction.council(standard["request_id"], infer=quiet)  # info: set drafted
    requested = json.dumps(drafted.get("requested_by"))  # info: set requested
    check("standard user stays pending", drafted.get("status") == "PENDING_AUTHORIZATION" and drafted["execution"]["permitted"] is False)  # info: call check
    promoted = interaction.authorize(standard["request_id"], 42)  # info: set promoted
    check("later authorization keeps requested_by", json.dumps(promoted.get("requested_by")) == requested and promoted.get("status") == "READY_FOR_BUILD")  # info: call check
    blocked = interaction.seed({"chat_id": SANDBOX, "sandbox_chat_id": SANDBOX, "text": "please add a dangerous page", "message_id": 4, "from_id": 7, "username": "someone"})  # info: set blocked
    rejected = interaction.council(blocked["request_id"], infer=carly_no)  # info: set rejected
    check("carly reject blocks", rejected.get("status") == "BLOCKED")  # info: call check
    admin = interaction.seed({"chat_id": SANDBOX, "sandbox_chat_id": SANDBOX, "text": "build the handoff", "message_id": 5, "from_id": 42, "username": "rootrecordadmin"})  # info: set admin
    ready = interaction.council(admin["request_id"], infer=quiet)  # info: set ready
    check("numeric id reaches READY_FOR_BUILD", ready.get("status") == "READY_FOR_BUILD" and ready["execution"]["permitted"] is True)  # info: call check
    held = interaction.handoff(admin["request_id"])  # info: set held
    check("handoff stops at the package", held.get("status") == "CURSOR_HANDOFF" and Path(held["handoff_ref"]).is_file())  # info: call check
    package = json.loads(Path(held["handoff_ref"]).read_text(encoding="utf-8"))  # info: set package
    check("package keeps the original sentence", package["original_request"]["text"] == "build the handoff" and package["authorized_by"] == "rootrecordadmin")  # info: call check
    refused = interaction.execute(admin["request_id"], agent_prompt=lambda _t: {"status": "completed"})  # info: set refused
    check("cursor_api off does not run", refused.get("result") == "refused" and refused.get("reason") == "cursor_api gate off")  # info: call check
    gates.set_gate("steps.build.cursor_api", True, confirmed=True)  # info: call gates . set_gate
    done = interaction.execute(admin["request_id"], agent_prompt=lambda _t: {"status": "completed"})  # info: set done
    vpath = Path(done.get("verification_report_ref") or "")  # info: set vpath
    vdoc = json.loads(vpath.read_text(encoding="utf-8")) if vpath.is_file() else {}  # info: set vdoc
    check("cursor path writes both reports", done.get("status") == "STATE_UPDATED" and vdoc.get("status") == "verified" and Path(done["execution_report_ref"]).is_file())  # info: call check
    sup = Path(os.environ["RR_SUPERVISOR_STATE"])  # info: set sup
    sup.mkdir(parents=True, exist_ok=True)  # info: sup . mkdir ( parents = True , exist_ok = True )
    (sup / "relay.blocked").write_text("1\n", encoding="utf-8")  # info: ( sup / "relay.blocked" ) . write_text ( "1\n" , encoding = "utf-8" )
    recovery = interaction.recover("bruce", "council_relay")  # info: set recovery
    check("recovery drafts and does not execute", recovery.get("executed") is False and recovery.get("result") == "refused" and Path(recovery.get("draft") or "").is_file())  # info: call check
    proc = subprocess.run([sys.executable, str(HERE / "execution-broker.py"), "request", "bruce", "development.execute_work_order"], text=True, capture_output=True, env=os.environ.copy())  # info: set proc
    body = json.loads(proc.stdout or "{}")  # info: set body
    check("broker denies agent build", body.get("result") == "refused" and proc.returncode != 0)  # info: call check
    proc = subprocess.run([sys.executable, str(HERE / "execution-broker.py"), "request", "ava", "inspect_npu"], text=True, capture_output=True, env=os.environ.copy())  # info: set proc
    body = json.loads(proc.stdout or "{}")  # info: set body
    check("read inspect still allowed", body.get("result") == "ok" and proc.returncode == 0)  # info: call check
    print(tmp)  # info: call print
    return 1 if FAILS else 0  # info: return 1 if FAILS else 0

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
