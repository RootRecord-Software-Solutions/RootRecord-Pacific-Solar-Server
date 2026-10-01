# ==============================================================================
# FILE: Automations/execution/interaction.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Record sandbox requests, run the council on a request file, and stop before Cursor unless gates allow it."""
from __future__ import annotations  # info: from __future__ import annotations
import json, os, re, subprocess, sys  # info: import json , os , re , subprocess , sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

import audit  # info: import audit
import gates  # info: import gates

ROOT = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ROOT
LIB = ROOT / "5 - RootRecord-Library" / "Documentation" / "02-agents"  # info: set LIB
PRINCIPALS = Path(os.environ.get("RR_PRINCIPAL_REGISTRY", str(LIB / "identity" / "principal-registry.json")))  # info: set PRINCIPALS
REQUESTS = Path(os.environ.get("RR_REQUEST_DIR", str(ROOT / "2 - RootRecord-Database" / "System" / "status" / "requests")))  # info: set REQUESTS
CAPS = LIB / "capabilities" / "capability-registry.json"  # info: set CAPS
ORDERS = LIB / "work-orders"  # info: set ORDERS
INFER = ROOT / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server" / "System" / "scripts" / "plumbing" / "run-infer.sh"  # info: set INFER
VERIFIER = Path(__file__).resolve().parent / "verifier.py"  # info: set VERIFIER
QUESTION_CAP = 3  # info: set QUESTION_CAP
SANDBOX_CHAT = "-1004406495175"  # info: set SANDBOX_CHAT
BUILD_RE = re.compile(r"\b(build|implement|add|fix|change|create)\b", re.I)  # info: set BUILD_RE
DIAGNOSE_RE = re.compile(r"\b(status|soc|inspect|health)\b", re.I)  # info: set DIAGNOSE_RE
CONVO_RE = re.compile(r"^(hi|hey|hello|thanks|thank you)\b", re.I)  # info: set CONVO_RE
WRITE_PERMS = {"BUILD", "MODIFY_FILES", "COMMIT", "PUSH", "CREATE_PR", "MERGE", "DEPLOY", "RECOVER"}  # info: set WRITE_PERMS

# ====================================================
# SECTION: function now
# What it does: Local timestamp. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> str:  # info: def now
    return datetime.now().astimezone().isoformat(timespec="seconds")  # info: return datetime . now ( ) . astimezone ( ) . isoformat ( timespec = "seconds" )

# ====================================================
# SECTION: function read_json
# What it does: Load one JSON object or an empty dict. Does not launch.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_json(path: Path) -> dict:  # info: def read_json
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance ( data , dict ) else { }

# ====================================================
# SECTION: function write_json
# What it does: Write one JSON file mode 0600. Does not commit it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_json(path: Path, doc: dict) -> None:  # info: def write_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents = True , exist_ok = True )
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps ( doc , indent = 2 ) + "\n" , encoding = "utf-8" )
    os.chmod(path, 0o600)  # info: os . chmod ( path , 0o600 )

# ====================================================
# SECTION: function principals
# What it does: Load the principal registry. Does not trust usernames as permission.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def principals() -> dict:  # info: def principals
    return read_json(PRINCIPALS)  # info: return read_json ( PRINCIPALS )

# ====================================================
# SECTION: function classify_principal
# What it does: Match from.id to a build principal. A username hit with a different id stays unknown for build.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def classify_principal(from_id, username: str) -> dict:  # info: def classify_principal
    label = username or ""  # info: set label
    try:  # info: try :
        numeric = int(from_id)  # info: set numeric
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError )
        numeric = None  # info: set numeric
    for row in principals().get("authorized_build_operators") or []:  # info: for row in principals ( ) . get ( "authorized_build_operators" ) or [ ]
        bound = row.get("telegram_user_id")  # info: set bound
        if bound is None or numeric is None or int(bound) != numeric:  # info: if bound is None or numeric is None or int ( bound ) != numeric
            continue  # info: continue
        return {"class": "authorized_admin", "ceiling": "build", "principal_id": row.get("principal_id"), "telegram_user_id": numeric, "username_label": label, "build_authorized": True}  # info: return { "class" : "authorized_admin" , "ceiling" : "build"
    return {"class": "standard_user", "ceiling": "work_order", "principal_id": None, "telegram_user_id": numeric, "username_label": label, "build_authorized": False}  # info: return { "class" : "standard_user" , "ceiling" : "work_order"

# ====================================================
# SECTION: function classify_mode
# What it does: Pick an interaction mode inside the principal ceiling. Does not execute.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def classify_mode(text: str, ceiling: str) -> str:  # info: def classify_mode
    if DIAGNOSE_RE.search(text) and not BUILD_RE.search(text):  # info: if DIAGNOSE_RE . search ( text ) and not BUILD_RE . search ( text )
        return "diagnose"  # info: return "diagnose"
    if CONVO_RE.search(text) and not BUILD_RE.search(text):  # info: return "conversation" when the text is only a greeting
        return "conversation"  # info: return "conversation"
    if ceiling == "build" and BUILD_RE.search(text):  # info: if ceiling == "build" and BUILD_RE . search ( text )
        return "build"  # info: return "build"
    return "work_order"  # info: return "work_order"

# ====================================================
# SECTION: function find_existing
# What it does: Return a request already stored for this sandbox message. Does not create one.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def find_existing(chat_id, message_id) -> dict | None:  # info: def find_existing
    if not REQUESTS.is_dir():  # info: if not REQUESTS . is_dir ( )
        return None  # info: return None
    for path in REQUESTS.glob("REQ-*.json"):  # info: for path in REQUESTS . glob ( "REQ-*.json" )
        doc = read_json(path)  # info: set doc
        src = doc.get("original_request") or {}  # info: set src
        if str(src.get("chat_id")) == str(chat_id) and str(src.get("message_id")) == str(message_id):  # info: if str ( src . get ( "chat_id" ) ) == str ( chat_id ) and str ( src . get ( "message_id" ) ) == str ( message_id )
            return doc  # info: return doc
    return None  # info: return None

# ====================================================
# SECTION: function save_request
# What it does: Store the request and a summary that omits the human text. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_request(doc: dict) -> Path:  # info: def save_request
    path = REQUESTS / f"{doc['request_id']}.json"  # info: set path
    write_json(path, doc)  # info: call write_json
    summary = {"request_id": doc["request_id"], "interaction_mode": doc.get("interaction_mode"), "status": doc.get("status"), "matching_work_orders": doc.get("matching_work_orders") or [], "visibility": "agent", "observed_at": now()}  # info: set summary
    write_json(REQUESTS.parent / "interaction-summary.json", summary)  # info: call write_json
    return path  # info: return path

# ====================================================
# SECTION: function seed
# What it does: Record one sandbox message. Refuses the live council chat. Does not infer or send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def seed(payload: dict) -> dict:  # info: def seed
    chat_id = str(payload.get("chat_id") or "")  # info: set chat_id
    sandbox = str(payload.get("sandbox_chat_id") or SANDBOX_CHAT)  # info: set sandbox
    if chat_id != sandbox:  # info: if chat_id != sandbox
        return {"result": "refused", "reason": "sandbox only"}  # info: return { "result" : "refused" , "reason" : "sandbox only" }
    text = payload.get("text") or ""  # info: set text
    message_id = payload.get("message_id")  # info: set message_id
    prior = find_existing(chat_id, message_id)  # info: set prior
    if prior:  # info: if prior
        return prior  # info: return prior
    who = classify_principal(payload.get("from_id"), payload.get("username") or "")  # info: set who
    mode = classify_mode(text, who["ceiling"])  # info: set mode
    if mode == "build" and who["ceiling"] != "build":  # info: if mode == "build" and who [ "ceiling" ] != "build"
        mode = "work_order"  # info: set mode
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")  # info: set stamp
    request_id = f"REQ-{stamp}-{message_id}"  # info: set request_id
    doc = {  # info: set doc
        "schema_version": 1,  # info: "schema_version" : 1 ,
        "request_id": request_id,  # info: "request_id" : request_id ,
        "status": "MODE_SELECTED",  # info: "status" : "MODE_SELECTED" ,
        "interaction_mode": mode,  # info: "interaction_mode" : mode ,
        "mode_history": ["RECEIVED", "CLASSIFIED", "MODE_SELECTED"],  # info: "mode_history" : [ "RECEIVED" , "CLASSIFIED" , "MODE_SELECTED" ] ,
        "original_request": {"text": text, "channel": "telegram", "chat_id": chat_id, "message_id": message_id, "timestamp": payload.get("timestamp") or now()},  # info: "original_request" : { "text" : text , "channel" : "telegram"
        "requested_by": {"telegram_user_id": who["telegram_user_id"], "username_label": who["username_label"], "class": who["class"]},  # info: "requested_by" : { "telegram_user_id" : who [ "telegram_user_id" ] , "username_label" : who [ "username_label" ] , "class" : who [ "class" ] } ,
        "authorization": {"principal_id": who["principal_id"], "telegram_user_id": who["telegram_user_id"] if who["build_authorized"] else None, "build_authorized": who["build_authorized"], "authorized_by": who["principal_id"] if who["build_authorized"] else None, "events": []},  # info: "authorization" : { "principal_id" : who [ "principal_id" ]
        "council_interpretation": [],  # info: "council_interpretation" : [ ] ,
        "questions": [],  # info: "questions" : [ ] ,
        "answers": [],  # info: "answers" : [ ] ,
        "question_round": 0,  # info: "question_round" : 0 ,
        "execution": {"permitted": False},  # info: "execution" : { "permitted" : False } ,
        "visibility": "operator",  # info: "visibility" : "operator" ,
    }  # info: }
    save_request(doc)  # info: call save_request
    return doc  # info: return doc

# ====================================================
# SECTION: function load_request
# What it does: Load one request by id. Does not modify it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_request(request_id: str) -> dict:  # info: def load_request
    return read_json(REQUESTS / f"{request_id}.json")  # info: return read_json ( REQUESTS / f" { request_id } . json " )

# ====================================================
# SECTION: function parse_pass
# What it does: Pull one JSON object out of a persona reply. A miss becomes a question, not a plan.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_pass(text: str) -> dict:  # info: def parse_pass
    start, end = text.find("{"), text.rfind("}")  # info: start , end = text . find ( "{" ) , text . rfind ( "}" )
    empty = {"interpretation": "", "questions": ["Council pass did not return JSON."], "proposed_work_order_fields": {}, "objections": [], "stop": False, "reject": False}  # info: set empty
    if start < 0 or end < start:  # info: if start < 0 or end < start
        return empty  # info: return empty
    try:  # info: try :
        data = json.loads(text[start:end + 1])  # info: set data
    except ValueError:  # info: except ValueError
        return empty  # info: return empty
    return data if isinstance(data, dict) else empty  # info: return data if isinstance ( data , dict ) else empty

# ====================================================
# SECTION: function default_infer
# What it does: One persona pass on the NPU 3B model. Does not leave FLM resident and does not raise context.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def default_infer(voice: str, prompt: str) -> str:  # info: def default_infer
    env = os.environ.copy()  # info: set env
    env["RR_NPU_ONLY"] = "1"  # info: env [ "RR_NPU_ONLY" ] = "1"
    env["FLM_MODEL"] = "llama3.2:3b"  # info: env [ "FLM_MODEL" ] = "llama3.2:3b"
    proc = subprocess.run([str(INFER), voice], input=prompt, text=True, capture_output=True, timeout=120, env=env)  # info: set proc
    return proc.stdout or ""  # info: return proc . stdout or ""

# ====================================================
# SECTION: function council
# What it does: Run Ava, Bruce, and Carly against one request. Stops at pending, ready, blocked, or a question cap.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def council(request_id: str, infer=None) -> dict:  # info: def council
    doc = load_request(request_id)  # info: set doc
    if not doc:  # info: if not doc
        return {"result": "refused", "reason": "missing request"}  # info: return { "result" : "refused" , "reason" : "missing request" }
    original = (doc.get("original_request") or {}).get("text") or ""  # info: set original
    mode = doc.get("interaction_mode")  # info: set mode
    gate_doc = gates.load()  # info: set gate_doc
    if mode == "conversation":  # info: if mode == "conversation"
        doc["status"] = "MODE_SELECTED"  # info: doc [ "status" ] = "MODE_SELECTED"
        doc["execution"]["permitted"] = False  # info: doc [ "execution" ] [ "permitted" ] = False
        save_request(doc)  # info: call save_request
        return doc  # info: return doc
    if mode == "diagnose":  # info: if mode == "diagnose"
        doc["status"] = "DISCOVERY"  # info: doc [ "status" ] = "DISCOVERY"
        doc["execution"]["permitted"] = False  # info: doc [ "execution" ] [ "permitted" ] = False
        save_request(doc)  # info: call save_request
        return doc  # info: return doc
    if mode == "build" and not gates.lookup(gate_doc, "modes.build"):  # info: if mode == "build" and not gates . lookup ( gate_doc , "modes.build" )
        doc["status"] = "NEEDS_DECISION"  # info: doc [ "status" ] = "NEEDS_DECISION"
        doc["execution"]["permitted"] = False  # info: doc [ "execution" ] [ "permitted" ] = False
        doc["block_reason"] = "build gate off"  # info: doc [ "block_reason" ] = "build gate off"
        save_request(doc)  # info: call save_request
        return doc  # info: return doc
    if mode == "work_order" and not gates.lookup(gate_doc, "modes.work_order"):  # info: if mode == "work_order" and not gates . lookup ( gate_doc , "modes.work_order" )
        doc["status"] = "BLOCKED"  # info: doc [ "status" ] = "BLOCKED"
        doc["block_reason"] = "work_order gate off"  # info: doc [ "block_reason" ] = "work_order gate off"
        save_request(doc)  # info: call save_request
        return doc  # info: return doc
    infer = infer or default_infer  # info: set infer
    doc["status"] = "DISCOVERY"  # info: doc [ "status" ] = "DISCOVERY"
    questions = []  # info: set questions
    reject = False  # info: set reject
    fields = {}  # info: set fields
    for voice in ("ava", "bruce", "carly"):  # info: for voice in ( "ava" , "bruce" , "carly" )
        prompt = json.dumps({"voice": voice, "original_request": original[:800], "status": doc["status"], "answers": doc.get("answers") or [], "reply_with": ["interpretation", "questions", "proposed_work_order_fields", "objections", "stop", "reject"]})  # info: set prompt
        parsed = parse_pass(infer(voice, prompt))  # info: set parsed
        doc["council_interpretation"].append({"voice": voice, "at": now(), "body": parsed})  # info: doc [ "council_interpretation" ] . append ( { "voice" : voice , "at" : now ( ) , "body" : parsed } )
        questions.extend(parsed.get("questions") or [])  # info: questions . extend ( parsed . get ( "questions" ) or [ ] )
        if voice == "carly" and parsed.get("reject"):  # info: if voice == "carly" and parsed . get ( "reject" )
            reject = True  # info: set reject
        if isinstance(parsed.get("proposed_work_order_fields"), dict):  # info: if isinstance ( parsed . get ( "proposed_work_order_fields" ) , dict )
            fields.update(parsed["proposed_work_order_fields"])  # info: fields . update ( parsed [ "proposed_work_order_fields" ] )
    if questions:  # info: if questions
        doc["question_round"] = int(doc.get("question_round") or 0) + 1  # info: doc [ "question_round" ] = int ( doc . get ( "question_round" ) or 0 ) + 1
        doc["questions"].append({"round": doc["question_round"], "items": questions})  # info: doc [ "questions" ] . append ( { "round" : doc [ "question_round" ] , "items" : questions } )
        doc["status"] = "NEEDS_DECISION" if doc["question_round"] >= QUESTION_CAP else "QUESTIONS_REQUIRED"  # info: doc [ "status" ] = "NEEDS_DECISION" if doc [ "question_round" ] >= QUESTION_CAP else "QUESTIONS_REQUIRED"
        doc["execution"]["permitted"] = False  # info: doc [ "execution" ] [ "permitted" ] = False
        save_request(doc)  # info: call save_request
        return doc  # info: return doc
    draft_id = f"WO-{request_id}"  # info: set draft_id
    draft = REQUESTS / "drafts" / f"{draft_id}.md"  # info: set draft
    draft.parent.mkdir(parents=True, exist_ok=True)  # info: draft . parent . mkdir ( parents = True , exist_ok = True )
    draft.write_text(f"# {draft_id}\n\nStatus: draft\n\nOriginal request is on {request_id}. This file is the council draft. It is not execution.\n\nFields: {json.dumps(fields)}\n", encoding="utf-8")  # info: draft . write_text
    os.chmod(draft, 0o600)  # info: os . chmod ( draft , 0o600 )
    doc["work_order_ref"] = str(draft)  # info: doc [ "work_order_ref" ] = str ( draft )
    doc["work_order_id"] = draft_id  # info: doc [ "work_order_id" ] = draft_id
    doc["status"] = "COUNCIL_REVIEW"  # info: doc [ "status" ] = "COUNCIL_REVIEW"
    if reject:  # info: if reject
        doc["status"] = "BLOCKED"  # info: doc [ "status" ] = "BLOCKED"
        doc["block_reason"] = "carly reject"  # info: doc [ "block_reason" ] = "carly reject"
        doc["execution"]["permitted"] = False  # info: doc [ "execution" ] [ "permitted" ] = False
    elif mode == "build" and doc["authorization"].get("build_authorized") and gates.lookup(gate_doc, "modes.build"):  # info: elif mode == "build" and doc [ "authorization" ] . get ( "build_authorized" ) and gates . lookup ( gate_doc , "modes.build" )
        doc["status"] = "READY_FOR_BUILD"  # info: doc [ "status" ] = "READY_FOR_BUILD"
        doc["execution"]["permitted"] = True  # info: doc [ "execution" ] [ "permitted" ] = True
    else:  # info: else :
        doc["status"] = "PENDING_AUTHORIZATION"  # info: doc [ "status" ] = "PENDING_AUTHORIZATION"
        doc["execution"]["permitted"] = False  # info: doc [ "execution" ] [ "permitted" ] = False
    save_request(doc)  # info: call save_request
    return doc  # info: return doc

# ====================================================
# SECTION: function answer
# What it does: Append a human answer. Leaves the original request text unchanged, then continues the council.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def answer(request_id: str, text: str, infer=None) -> dict:  # info: def answer
    doc = load_request(request_id)  # info: set doc
    if not doc:  # info: if not doc
        return {"result": "refused", "reason": "missing request"}  # info: return { "result" : "refused" , "reason" : "missing request" }
    before = (doc.get("original_request") or {}).get("text")  # info: set before
    doc.setdefault("answers", []).append({"text": text, "at": now()})  # info: doc . setdefault ( "answers" , [ ] ) . append ( { "text" : text , "at" : now ( ) } )
    doc["status"] = "QUESTIONS_ANSWERED"  # info: doc [ "status" ] = "QUESTIONS_ANSWERED"
    save_request(doc)  # info: call save_request
    out = council(request_id, infer=infer)  # info: set out
    if (out.get("original_request") or {}).get("text") != before:  # info: if ( out . get ( "original_request" ) or { } ) . get ( "text" ) != before
        out["original_request"]["text"] = before  # info: out [ "original_request" ] [ "text" ] = before
        save_request(out)  # info: call save_request
    return out  # info: return out

# ====================================================
# SECTION: function authorize
# What it does: Let a numeric build principal authorize a pending request. Keeps requested_by.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def authorize(request_id: str, from_id) -> dict:  # info: def authorize
    doc = load_request(request_id)  # info: set doc
    if not doc:  # info: return { "result" : "refused" , "reason" : "missing request" } when the id is unknown
        return {"result": "refused", "reason": "missing request"}  # info: return { "result" : "refused" , "reason" : "missing request" }
    who = classify_principal(from_id, "")  # info: set who
    if not who["build_authorized"]:  # info: if not who [ "build_authorized" ]
        audit.append({"agent": "unknown", "capability": "development.execute_work_order", "permission": "BUILD", "result": "refused", "reason": "requester not in authorized build-operator set"})  # info: call audit . append
        return {"result": "refused", "reason": "not a build principal"}  # info: return { "result" : "refused" , "reason" : "not a build principal" }
    requested = doc.get("requested_by")  # info: set requested
    doc["authorization"]["events"].append({"at": now(), "authorized_by": who["principal_id"], "telegram_user_id": who["telegram_user_id"]})  # info: doc [ "authorization" ] [ "events" ] . append
    doc["authorization"]["authorized_by"] = who["principal_id"]  # info: doc [ "authorization" ] [ "authorized_by" ] = who [ "principal_id" ]
    doc["authorization"]["telegram_user_id"] = who["telegram_user_id"]  # info: doc [ "authorization" ] [ "telegram_user_id" ] = who [ "telegram_user_id" ]
    doc["authorization"]["build_authorized"] = True  # info: doc [ "authorization" ] [ "build_authorized" ] = True
    doc["requested_by"] = requested  # info: doc [ "requested_by" ] = requested
    if doc.get("status") == "PENDING_AUTHORIZATION" and gates.lookup(gates.load(), "modes.build"):  # info: if doc . get ( "status" ) == "PENDING_AUTHORIZATION" and gates . lookup ( gates . load ( ) , "modes.build" )
        doc.setdefault("mode_history", []).append(doc.get("interaction_mode"))  # info: doc . setdefault ( "mode_history" , [ ] ) . append ( doc . get ( "interaction_mode" ) )
        doc["interaction_mode"] = "build"  # info: doc [ "interaction_mode" ] = "build"
        doc["status"] = "READY_FOR_BUILD"  # info: doc [ "status" ] = "READY_FOR_BUILD"
        doc["execution"]["permitted"] = True  # info: doc [ "execution" ] [ "permitted" ] = True
    save_request(doc)  # info: call save_request
    return doc  # info: return doc

# ====================================================
# SECTION: function handoff
# What it does: Write the Cursor context package from READY_FOR_BUILD. Does not call the Cursor API.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def handoff(request_id: str) -> dict:  # info: def handoff
    doc = load_request(request_id)  # info: set doc
    if not doc:  # info: if not doc
        return {"result": "refused", "reason": "missing request"}  # info: return { "result" : "refused" , "reason" : "missing request" }
    if doc.get("status") != "READY_FOR_BUILD":  # info: if doc . get ( "status" ) != "READY_FOR_BUILD"
        return {"result": "refused", "reason": "not READY_FOR_BUILD", "status": doc.get("status")}  # info: return { "result" : "refused" , "reason" : "not READY_FOR_BUILD"
    if not gates.lookup(gates.load(), "steps.build.handoff"):  # info: if not gates . lookup ( gates . load ( ) , "steps.build.handoff" )
        return {"result": "refused", "reason": "handoff gate off", "status": doc.get("status")}  # info: return { "result" : "refused" , "reason" : "handoff gate off"
    auth = doc.get("authorization") or {}  # info: set auth
    if not auth.get("build_authorized") or auth.get("telegram_user_id") is None:  # info: if not auth . get ( "build_authorized" ) or auth . get ( "telegram_user_id" ) is None
        doc["status"] = "BLOCKED"  # info: doc [ "status" ] = "BLOCKED"
        doc["block_reason"] = "numeric principal id required"  # info: doc [ "block_reason" ] = "numeric principal id required"
        save_request(doc)  # info: call save_request
        return doc  # info: return doc
    versions = doc.get("council_interpretation") or []  # info: set versions
    package = {  # info: set package
        "schema_version": 1,  # info: "schema_version" : 1 ,
        "request_id": request_id,  # info: "request_id" : request_id ,
        "work_order_id": doc.get("work_order_id"),  # info: "work_order_id" : doc . get ( "work_order_id" ) ,
        "interaction_mode": "build",  # info: "interaction_mode" : "build" ,
        "original_request": doc.get("original_request"),  # info: "original_request" : doc . get ( "original_request" ) ,
        "council_interpretation_version": len(versions),  # info: "council_interpretation_version" : len ( versions ) ,
        "authorized_by": auth.get("principal_id"),  # info: "authorized_by" : auth . get ( "principal_id" ) ,
        "requested_by": doc.get("requested_by"),  # info: "requested_by" : doc . get ( "requested_by" ) ,
        "executor": "cursor",  # info: "executor" : "cursor" ,
        "capability": "development.execute_work_order",  # info: "capability" : "development.execute_work_order" ,
        "allowed_steps": ["create_branch", "modify_files", "run_tests", "generate_execution_report", "generate_verification_report"],  # info: "allowed_steps" : [ "create_branch" , "modify_files" , "run_tests" , "generate_execution_report" , "generate_verification_report" ] ,
        "scope_paths": [doc.get("work_order_ref") or str(REQUESTS)],  # info: "scope_paths" : [ doc . get ( "work_order_ref" ) or str ( REQUESTS ) ] ,
        "out_of_scope_paths": ["2 - RootRecord-Database/System/status", ".env", "Security"],  # info: "out_of_scope_paths" : [ "2 - RootRecord-Database/System/status" , ".env" , "Security" ] ,
        "verification": ["request_record_present", "handoff_package_present", "execution_report_present"],  # info: "verification" : [ "request_record_present" , "handoff_package_present" , "execution_report_present" ] ,
        "resource_limits": {"no_second_relay": True, "no_resident_flm": True, "max_context": 4096, "no_secret_files": True, "no_arbitrary_shell": True},  # info: "resource_limits" : { "no_second_relay" : True , "no_resident_flm" : True , "max_context" : 4096 , "no_secret_files" : True , "no_arbitrary_shell" : True } ,
    }  # info: }
    path = REQUESTS / "handoff" / f"{request_id}.json"  # info: set path
    write_json(path, package)  # info: call write_json
    doc["handoff_ref"] = str(path)  # info: doc [ "handoff_ref" ] = str ( path )
    doc["status"] = "CURSOR_HANDOFF"  # info: doc [ "status" ] = "CURSOR_HANDOFF"
    save_request(doc)  # info: call save_request
    return doc  # info: return doc

# ====================================================
# SECTION: function cursor_sdk_prompt
# What it does: Call the Cursor SDK with the package text. Fail closed when the SDK or key is missing.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cursor_sdk_prompt(package_text: str) -> dict:  # info: def cursor_sdk_prompt
    key = os.environ.get("CURSOR_API_KEY") or ""  # info: set key
    if not key:  # info: if not key
        raise RuntimeError("CURSOR_API_KEY missing")  # info: raise RuntimeError ( "CURSOR_API_KEY missing" )
    from cursor_sdk import Agent, AgentOptions, LocalAgentOptions  # info: from cursor_sdk import Agent , AgentOptions , LocalAgentOptions
    result = Agent.prompt(package_text, AgentOptions(api_key=key, model="composer-2.5", local=LocalAgentOptions(cwd=str(ROOT))))  # info: set result
    return {"status": str(getattr(result, "status", "completed")), "result": "cursor returned"}  # info: return { "status" : str ( getattr ( result , "status" , "completed" ) ) , "result" : "cursor returned" }

# ====================================================
# SECTION: function write_execution_report
# What it does: Store the attempt. Does not claim the desk is healthy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_execution_report(doc: dict, status: str, steps: list) -> dict:  # info: def write_execution_report
    started = now()  # info: set started
    report = {"schema_version": 1, "report_id": f"EX-{doc['request_id']}", "request_id": doc["request_id"], "work_order_id": doc.get("work_order_id"), "executor": "cursor", "authorization_ref": doc.get("authorization"), "started_at": started, "finished_at": now(), "steps": steps, "files_changed": [], "audit_ids": [started], "status": status, "visibility": "operator"}  # info: set report
    path = REQUESTS / "reports" / "execution" / f"{report['report_id']}.json"  # info: set path
    write_json(path, report)  # info: call write_json
    doc["execution_report_ref"] = str(path)  # info: doc [ "execution_report_ref" ] = str ( path )
    return report  # info: return report

# ====================================================
# SECTION: function execute
# What it does: Invoke Cursor only when cursor_api is on and the package already exists. Agents cannot call this.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def execute(request_id: str, agent_prompt=None) -> dict:  # info: def execute
    doc = load_request(request_id)  # info: set doc
    if not doc:  # info: if not doc
        return {"result": "refused", "reason": "missing request"}  # info: return { "result" : "refused" , "reason" : "missing request" }
    if not gates.lookup(gates.load(), "steps.build.cursor_api"):  # info: if not gates . lookup ( gates . load ( ) , "steps.build.cursor_api" )
        audit.append({"agent": "cursor", "capability": "development.execute_work_order", "permission": "BUILD", "result": "refused", "reason": "cursor_api gate off"})  # info: call audit . append
        return {"result": "refused", "reason": "cursor_api gate off", "status": doc.get("status")}  # info: return { "result" : "refused" , "reason" : "cursor_api gate off"
    if doc.get("status") != "CURSOR_HANDOFF":  # info: if doc . get ( "status" ) != "CURSOR_HANDOFF"
        return {"result": "refused", "reason": "handoff package required", "status": doc.get("status")}  # info: return { "result" : "refused" , "reason" : "handoff package required"
    package = read_json(Path(doc.get("handoff_ref") or ""))  # info: set package
    blocked_steps = [step for step in (package.get("allowed_steps") or []) if step in ("commit", "push", "merge", "deploy") and not gates.lookup(gates.load(), f"steps.build.{step}")]  # info: set blocked_steps
    if blocked_steps:  # info: if blocked_steps
        audit.append({"agent": "cursor", "capability": "development.execute_work_order", "permission": "BUILD", "result": "refused", "reason": "step gate off"})  # info: call audit . append
        return {"result": "refused", "reason": "step gate off", "steps": blocked_steps}  # info: return { "result" : "refused" , "reason" : "step gate off"
    auth = doc.get("authorization") or {}  # info: set auth
    if auth.get("telegram_user_id") is None:  # info: if auth . get ( "telegram_user_id" ) is None
        doc["status"] = "BLOCKED"  # info: doc [ "status" ] = "BLOCKED"
        write_execution_report(doc, "blocked", [{"allowed_step": "cursor_api", "result": "blocked", "evidence_ref": "missing numeric id"}])  # info: call write_execution_report
        save_request(doc)  # info: call save_request
        return doc  # info: return doc
    doc["status"] = "EXECUTING"  # info: doc [ "status" ] = "EXECUTING"
    save_request(doc)  # info: call save_request
    prompt = agent_prompt or cursor_sdk_prompt  # info: set prompt
    try:  # info: try :
        outcome = prompt(json.dumps(package))  # info: set outcome
        step_status = "completed" if outcome.get("status") != "error" else "failed"  # info: set step_status
    except Exception as exc:  # info: except Exception as exc
        outcome = {"status": "blocked"}  # info: set outcome
        step_status = "blocked"  # info: set step_status
        audit.append({"agent": "cursor", "capability": "development.execute_work_order", "permission": "BUILD", "result": "refused", "reason": type(exc).__name__})  # info: call audit . append
    report = write_execution_report(doc, step_status if step_status != "completed" else "completed", [{"capability": "development.execute_work_order", "allowed_step": "cursor_api", "result": outcome.get("status"), "evidence_ref": doc.get("handoff_ref")}])  # info: set report
    doc["status"] = "EXECUTION_REPORTED"  # info: doc [ "status" ] = "EXECUTION_REPORTED"
    save_request(doc)  # info: call save_request
    subprocess.run([sys.executable, str(VERIFIER), "report", doc["execution_report_ref"]], check=False)  # info: call subprocess . run
    verified = read_json(REQUESTS / "reports" / "verification" / f"VR-{doc['request_id']}.json")  # info: set verified
    doc["verification_report_ref"] = str(REQUESTS / "reports" / "verification" / f"VR-{doc['request_id']}.json")  # info: doc [ "verification_report_ref" ] = str ( REQUESTS / "reports" / "verification" / f" VR- { doc [ 'request_id' ] } . json " )
    doc["status"] = "VERIFIED" if verified.get("status") == "verified" else "VERIFICATION_FAILED"  # info: doc [ "status" ] = "VERIFIED" if verified . get ( "status" ) == "verified" else "VERIFICATION_FAILED"
    doc["resulting_state_ref"] = str(REQUESTS.parent / "interaction-summary.json")  # info: doc [ "resulting_state_ref" ] = str ( REQUESTS . parent / "interaction-summary.json" )
    doc["status"] = "STATE_UPDATED"  # info: doc [ "status" ] = "STATE_UPDATED"
    doc["verification_status"] = verified.get("status")  # info: doc [ "verification_status" ] = verified . get ( "status" )
    save_request(doc)  # info: call save_request
    return doc  # info: return doc

# ====================================================
# SECTION: function recover
# What it does: Notice a machine work order. Refuse agent restart. Draft when the supervisor is BLOCKED.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recover(agent: str, service: str) -> dict:  # info: def recover
    order = read_json(ORDERS / "WO-SRV-RELAY.json") if service in ("relay", "council_relay") else {}  # info: set order
    cap = {}  # info: set cap
    for row in (read_json(CAPS).get("capabilities") or []):  # info: for row in ( read_json ( CAPS ) . get ( "capabilities" ) or [ ] )
        if row.get("id") == "restart_known_service":  # info: if row . get ( "id" ) == "restart_known_service"
            cap = row  # info: set cap
    open_gate = gates.allowed(cap) if cap else False  # info: set open_gate
    may = bool(cap.get("agent_may_invoke")) and (cap.get("agents") or {}).get(agent) == "allowed" and open_gate  # info: set may
    if not may:  # info: if not may
        audit.append({"agent": agent, "capability": "restart_known_service", "permission": "RECOVER", "result": "refused", "reason": "recovery stays with the poller supervisor"})  # info: call audit . append
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", "/run/user/0")) / "rootrecord-supervisor"  # info: set runtime
    if os.environ.get("RR_SUPERVISOR_STATE"):  # info: if os . environ . get ( "RR_SUPERVISOR_STATE" )
        runtime = Path(os.environ["RR_SUPERVISOR_STATE"])  # info: set runtime
    sid = "relay" if service in ("relay", "council_relay") else service  # info: set sid
    blocked = (runtime / f"{sid}.blocked").is_file()  # info: set blocked
    unknown = not order  # info: set unknown
    draft_path = ""  # info: set draft_path
    if blocked or unknown:  # info: if blocked or unknown
        draft_path = str(REQUESTS / "drafts" / f"WO-BLOCKED-{sid}.md")  # info: set draft_path
        Path(draft_path).parent.mkdir(parents=True, exist_ok=True)  # info: Path ( draft_path ) . parent . mkdir ( parents = True , exist_ok = True )
        Path(draft_path).write_text(f"# WO-BLOCKED-{sid}\n\nStatus: draft\n\nThe supervisor owns recovery. This draft does not execute and does not raise max_attempts.\n", encoding="utf-8")  # info: Path ( draft_path ) . write_text
        os.chmod(draft_path, 0o600)  # info: os . chmod ( draft_path , 0o600 )
    return {"result": "refused" if not may else "selected", "capability": "restart_known_service", "executed": False, "blocked": blocked, "draft": draft_path, "work_order": order.get("id")}  # info: return { "result" : "refused" if not may else "selected"

# ====================================================
# SECTION: function main
# What it does: Dispatch one interaction command. Prints JSON. Does not send Telegram.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""  # info: set cmd
    if cmd == "seed":  # info: if cmd == "seed"
        print(json.dumps(seed(json.loads(sys.stdin.read() or "{}")), indent=2))  # info: call print
        return 0  # info: return 0
    if cmd == "council" and len(sys.argv) > 2:  # info: if cmd == "council" and len ( sys . argv ) > 2
        print(json.dumps(council(sys.argv[2]), indent=2))  # info: call print
        return 0  # info: return 0
    if cmd == "answer" and len(sys.argv) > 2:  # info: if cmd == "answer" and len ( sys . argv ) > 2
        print(json.dumps(answer(sys.argv[2], sys.stdin.read()), indent=2))  # info: call print
        return 0  # info: return 0
    if cmd == "authorize" and len(sys.argv) > 3:  # info: if cmd == "authorize" and len ( sys . argv ) > 3
        print(json.dumps(authorize(sys.argv[2], sys.argv[3]), indent=2))  # info: call print
        return 0  # info: return 0
    if cmd == "handoff" and len(sys.argv) > 2:  # info: if cmd == "handoff" and len ( sys . argv ) > 2
        print(json.dumps(handoff(sys.argv[2]), indent=2))  # info: call print
        return 0  # info: return 0
    if cmd == "execute" and len(sys.argv) > 2:  # info: if cmd == "execute" and len ( sys . argv ) > 2
        print(json.dumps(execute(sys.argv[2]), indent=2))  # info: call print
        return 0  # info: return 0
    if cmd == "recover" and len(sys.argv) > 3:  # info: if cmd == "recover" and len ( sys . argv ) > 3
        print(json.dumps(recover(sys.argv[2], sys.argv[3]), indent=2))  # info: call print
        return 0  # info: return 0
    print("usage: interaction.py seed|council|answer|authorize|handoff|execute|recover", file=sys.stderr)  # info: call print
    return 2  # info: return 2

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
