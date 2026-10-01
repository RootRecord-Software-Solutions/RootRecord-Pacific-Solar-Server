# ==============================================================================
# FILE: Communications/Discord/scripts/review.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Ava-led Discord review pipeline. Transport stays in lib/api.py.

Off unless RR_DISCORD_REVIEW_PIPELINE=1. Bruce and Carly review in process.
Only Ava's public text is returned for Discord. Telegram is not involved.
Identity is loaded from Library Agent Context through CouncilPersona.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
import json  # info: import json
import os  # info: import os
import re  # info: import re
import subprocess  # info: import subprocess
import sys  # info: import sys
from dataclasses import dataclass  # info: from dataclasses import dataclass
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent  # info: set HERE
DISCORD = HERE.parent  # info: set DISCORD
COMMS = DISCORD.parent  # info: set COMMS
PACIFIC = COMMS.parent  # info: set PACIFIC
RUN_INFER = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"  # info: set RUN_INFER
PERSONAS = COMMS / "CouncilPersona" / "scripts" / "personas.py"  # info: set PERSONAS
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
LOG_PATH = DB / "Logs" / "Communications" / "Discord" / "poll.log"  # info: set LOG_PATH
SEEN_PATH = DB / "Communications" / "Discord" / "review-seen.json"  # info: set SEEN_PATH
REVIEW_FLAG = "RR_DISCORD_REVIEW_PIPELINE"  # info: set REVIEW_FLAG
LEAK_RE = re.compile(r"DESK_LIVE:|HARD RULES FOR THIS TURN|Do NOT state watts|standing envelopes|\[desk:", re.I)  # info: set LEAK_RE
AVA_RE = re.compile(r"\bava\b", re.I)  # info: set AVA_RE
_PERSONA: dict[str, str] = {}  # info: set _PERSONA


# ====================================================
# SECTION: class DiscordReviewRequest
# What it does: Hold the user text, context, and Ava's draft for the reviewers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass
class DiscordReviewRequest:  # info: class DiscordReviewRequest
    user_message: str  # info: user_message : str
    conversation_context: str  # info: conversation_context : str
    ava_draft: str  # info: ava_draft : str


# ====================================================
# SECTION: class StageReview
# What it does: One internal review. status is reviewed or unavailable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass
class StageReview:  # info: class StageReview
    voice: str  # info: voice : str
    status: str  # info: status : str
    decision: str  # info: decision : str
    notes: str  # info: notes : str


# ====================================================
# SECTION: class PipelineResult
# What it does: Internal chain result. public_text is the only Discord payload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass
class PipelineResult:  # info: class PipelineResult
    public_text: str  # info: public_text : str
    ava_draft: str  # info: ava_draft : str
    bruce: StageReview  # info: bruce : StageReview
    carly: StageReview  # info: carly : StageReview
    ava_final_status: str  # info: ava_final_status : str
    final_response: str  # info: final_response : str


# ====================================================
# SECTION: function pipeline_enabled
# What it does: True only when RR_DISCORD_REVIEW_PIPELINE=1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pipeline_enabled() -> bool:  # info: def pipeline_enabled
    return os.environ.get(REVIEW_FLAG, "0").strip() == "1"  # info: return os . environ . get ( REVIEW_FLAG , "0" ) . strip ( ) == "1"


# ====================================================
# SECTION: function stage_log
# What it does: Append one stage label. Callers must not pass message text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stage_log(line: str, path: Path | None = None) -> None:  # info: def stage_log
    dest = path or LOG_PATH  # info: set dest
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents = True ,
    stamp = datetime.now(HST).isoformat(timespec="seconds")  # info: set stamp
    with dest.open("a", encoding="utf-8") as handle:  # info: with dest . open ( "a" , encoding = "utf-8" ) as handle
        handle.write(f"{stamp} {line}\n")  # info: handle . write ( f" { stamp } { line } \n" )


# ====================================================
# SECTION: function persona_system
# What it does: Load canonical system text for ava, bruce, or carly from CouncilPersona.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona_system(voice: str) -> str:  # info: def persona_system
    key = (voice or "").strip().lower()  # info: set key
    cached = _PERSONA.get(key)  # info: set cached
    if cached:  # info: if cached
        return cached  # info: return cached
    spec = importlib.util.spec_from_file_location("rr_council_persona", PERSONAS)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader is None
        raise RuntimeError("personas.py is missing")  # info: raise RuntimeError ( "personas.py is missing" )
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    text = mod.system_for(key)  # info: set text
    _PERSONA[key] = text  # info: _PERSONA [ key ] = text
    return text  # info: return text


# ====================================================
# SECTION: function clean_reply
# What it does: Drop empty output, instruction leaks, and plumbing status lines.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_reply(text: str | None) -> str:  # info: def clean_reply
    raw = (text or "").strip()  # info: set raw
    if not raw or LEAK_RE.search(raw):  # info: if not raw or LEAK_RE . search ( raw )
        return ""  # info: return ""
    lines = [ln for ln in raw.splitlines() if not ln.startswith(("[ok]", "[fail]", "[warn]", "[busy]"))]  # info: set lines
    return "\n".join(lines).strip()  # info: return "\n" . join ( lines ) . strip ( )


# ====================================================
# SECTION: function parse_review
# What it does: Read APPROVE or CHANGES. Any other text is CHANGES, never a silent approve.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_review(text: str) -> tuple[str, str]:  # info: def parse_review
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]  # info: set lines
    if not lines:  # info: if not lines
        return "UNAVAILABLE", ""  # info: return "UNAVAILABLE" , ""
    head = lines[0].upper().split()[0].strip(".:")  # info: set head
    if head == "APPROVE":  # info: if head == "APPROVE"
        return "APPROVE", text.strip()  # info: return "APPROVE" , text . strip ( )
    return "CHANGES", text.strip()  # info: return "CHANGES" , text . strip ( )


# ====================================================
# SECTION: function invokes_ava
# What it does: True when a non-bot message names Ava. Other Discord traffic stays quiet.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def invokes_ava(message: dict) -> bool:  # info: def invokes_ava
    author = message.get("author") or {}  # info: set author
    if author.get("bot"):  # info: if author . get ( "bot" )
        return False  # info: return False
    content = message.get("content") or ""  # info: set content
    if AVA_RE.search(content):  # info: if AVA_RE . search ( content )
        return True  # info: return True
    for mention in message.get("mentions") or []:  # info: for mention in message . get ( "mentions" ) or [ ]
        if not isinstance(mention, dict):  # info: if not isinstance ( mention , dict )
            continue  # info: continue
        label = f"{mention.get('username') or ''} {mention.get('global_name') or ''}"  # info: set label
        if AVA_RE.search(label):  # info: if AVA_RE . search ( label )
            return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function clip
# What it does: Keep one prompt field inside a fixed character budget.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clip(text: str, limit: int = 2000) -> str:  # info: def clip
    body = (text or "").strip()  # info: set body
    if len(body) <= limit:  # info: if len ( body ) <= limit
        return body  # info: return body
    return body[:limit]  # info: return body [ : limit ]


# ====================================================
# SECTION: function draft_prompt
# What it does: Ask Ava for an internal draft of the Discord user's request.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def draft_prompt(user_message: str, conversation_context: str) -> str:  # info: def draft_prompt
    context = clip(conversation_context) or "(none)"  # info: set context
    return (  # info: return (
        "Write a draft answer to this Discord user. The draft stays internal until you write the final reply.\n"  # info: "Write a draft answer to this Discord user. The draft stays internal until you write the final reply.\n"
        "Answer the request. Do not mention an internal review.\n\n"  # info: "Answer the request. Do not mention an internal review.\n\n"
        f"Conversation context:\n{context}\n\n"  # info: f"Conversation context:\n { context } \n\n"
        f"User:\n{clip(user_message)}"  # info: f"User:\n { clip ( user_message ) } "
    )  # info: )


# ====================================================
# SECTION: function bruce_prompt
# What it does: Ask Bruce for a compact review, not a second public answer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def bruce_prompt(req: DiscordReviewRequest) -> str:  # info: def bruce_prompt
    return (  # info: return (
        "Review Ava's draft. Do not write a public answer and do not rewrite the full reply.\n"  # info: "Review Ava's draft. Do not write a public answer and do not rewrite the full reply.\n"
        "Check facts, reasoning, missing information, technical gaps, extra wording, and useful enhancements.\n"  # info: "Check facts, reasoning, missing information, technical gaps, extra wording, and useful enhancements.\n"
        "Return APPROVE on the first line, or CHANGES: followed by short bullets.\n\n"  # info: "Return APPROVE on the first line, or CHANGES: followed by short bullets.\n\n"
        f"Original user message:\n{clip(req.user_message)}\n\n"  # info: f"Original user message:\n { clip ( req . user_message ) } \n\n"
        f"Ava draft:\n{clip(req.ava_draft)}"  # info: f"Ava draft:\n { clip ( req . ava_draft ) } "
    )  # info: )


# ====================================================
# SECTION: function carly_prompt
# What it does: Ask Carly for a compact safety review, not a second public answer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def carly_prompt(req: DiscordReviewRequest, bruce: StageReview) -> str:  # info: def carly_prompt
    notes = clip(bruce.notes) if bruce.notes else "(none)"  # info: set notes
    return (  # info: return (
        "Review Ava's draft for safety, security, privacy, operational risk, omissions, and bad assumptions.\n"  # info: "Review Ava's draft for safety, security, privacy, operational risk, omissions, and bad assumptions.\n"
        "Do not write a public answer and do not rewrite the full reply.\n"  # info: "Do not write a public answer and do not rewrite the full reply.\n"
        "A status of unavailable means that reviewer did not review. Do not treat it as approval.\n"  # info: "A status of unavailable means that reviewer did not review. Do not treat it as approval.\n"
        "Return APPROVE on the first line, or CHANGES: followed by short bullets.\n\n"  # info: "Return APPROVE on the first line, or CHANGES: followed by short bullets.\n\n"
        f"Original user message:\n{clip(req.user_message)}\n\n"  # info: f"Original user message:\n { clip ( req . user_message ) } \n\n"
        f"Ava draft:\n{clip(req.ava_draft)}\n\n"  # info: f"Ava draft:\n { clip ( req . ava_draft ) } \n\n"
        f"Bruce review status: {bruce.status}\nBruce decision: {bruce.decision}\nBruce notes:\n{notes}"  # info: f"Bruce review status: { bruce . status } \nBruce decision: { bruce . decision } \nBruce notes:\n { notes } "
    )  # info: )


# ====================================================
# SECTION: function final_prompt
# What it does: Ask Ava for the only text that may be shown on Discord.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def final_prompt(req: DiscordReviewRequest, bruce: StageReview, carly: StageReview) -> str:  # info: def final_prompt
    bruce_notes = clip(bruce.notes) if bruce.notes else "(none)"  # info: set bruce_notes
    carly_notes = clip(carly.notes) if carly.notes else "(none)"  # info: set carly_notes
    return (  # info: return (
        "Write the final public Discord reply in your own voice.\n"  # info: "Write the final public Discord reply in your own voice.\n"
        "Use the draft and the reviews. Do not mention Bruce, Carly, a review, APPROVE, or CHANGES.\n"  # info: "Use the draft and the reviews. Do not mention Bruce, Carly, a review, APPROVE, or CHANGES.\n"
        "A status of unavailable means that reviewer did not review. Do not treat it as approval.\n\n"  # info: "A status of unavailable means that reviewer did not review. Do not treat it as approval.\n\n"
        f"Original user message:\n{clip(req.user_message)}\n\n"  # info: f"Original user message:\n { clip ( req . user_message ) } \n\n"
        f"Your draft:\n{clip(req.ava_draft)}\n\n"  # info: f"Your draft:\n { clip ( req . ava_draft ) } \n\n"
        f"Bruce review status: {bruce.status}\nBruce decision: {bruce.decision}\nBruce notes:\n{bruce_notes}\n\n"  # info: f"Bruce review status: { bruce . status } \nBruce decision: { bruce . decision } \nBruce notes:\n { bruce_notes } \n\n"
        f"Carly review status: {carly.status}\nCarly decision: {carly.decision}\nCarly notes:\n{carly_notes}"  # info: f"Carly review status: { carly . status } \nCarly decision: { carly . decision } \nCarly notes:\n { carly_notes } "
    )  # info: )


# ====================================================
# SECTION: function default_infer
# What it does: One voice turn through run-infer.sh with the Library persona on the NPU path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def default_infer(voice: str, prompt: str) -> str:  # info: def default_infer
    if not RUN_INFER.is_file():  # info: if not RUN_INFER . is_file ( )
        raise RuntimeError("run-infer.sh is missing")  # info: raise RuntimeError ( "run-infer.sh is missing" )
    env = os.environ.copy()  # info: set env
    env["RR_PERSONA_SYSTEM"] = persona_system(voice)  # info: env [ "RR_PERSONA_SYSTEM" ] = persona_system ( voice )
    env["RR_NPU_ONLY"] = "1"  # info: env [ "RR_NPU_ONLY" ] = "1"
    env["RR_NPU_PERSONA"] = "1"  # info: env [ "RR_NPU_PERSONA" ] = "1"
    env["FLM_MODEL"] = os.environ.get("FLM_MODEL", "llama3.2:3b")  # info: env [ "FLM_MODEL" ] = os . environ . get ( "FLM_MODEL" , "llama3.2:3b" )
    env["RR_CALLER"] = "discord-review"  # info: env [ "RR_CALLER" ] = "discord-review"
    proc = subprocess.run(  # info: set proc
        [str(RUN_INFER), voice, prompt],  # info: [ str ( RUN_INFER ) , voice , prompt ]
        capture_output=True,  # info: capture_output = True
        text=True,  # info: text = True
        timeout=600,  # info: timeout = 600
        env=env,  # info: env = env
    )  # info: )
    out = clean_reply(proc.stdout)  # info: set out
    if proc.returncode != 0 and not out:  # info: if proc . returncode != 0 and not out
        raise RuntimeError(f"infer exit {proc.returncode}")  # info: raise RuntimeError ( f"infer exit { proc . returncode } " )
    if not out:  # info: if not out
        raise RuntimeError("infer empty")  # info: raise RuntimeError ( "infer empty" )
    return out  # info: return out


# ====================================================
# SECTION: function review_stage
# What it does: Run one reviewer. A failure stays unavailable and is not recorded as APPROVE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def review_stage(voice: str, prompt: str, infer, log) -> StageReview:  # info: def review_stage
    try:  # info: try
        text = clean_reply(infer(voice, prompt))  # info: set text
    except Exception as exc:  # info: except Exception as exc
        log(f"{voice.capitalize()} review unavailable {type(exc).__name__}")  # info: call log
        return StageReview(voice, "unavailable", "UNAVAILABLE", "")  # info: return StageReview ( voice , "unavailable" , "UNAVAILABLE" , "" )
    if not text:  # info: if not text
        log(f"{voice.capitalize()} review unavailable empty")  # info: call log
        return StageReview(voice, "unavailable", "UNAVAILABLE", "")  # info: return StageReview ( voice , "unavailable" , "UNAVAILABLE" , "" )
    decision, notes = parse_review(text)  # info: decision , notes = parse_review ( text )
    log(f"{voice.capitalize()} review completed status=reviewed decision={decision}")  # info: call log
    return StageReview(voice, "reviewed", decision, notes)  # info: return StageReview ( voice , "reviewed" , decision , notes )


# ====================================================
# SECTION: function choose_public
# What it does: Pick Ava's final text, or her draft when the final pass failed. Never a review note.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def choose_public(final: str, draft: str, bruce: StageReview, carly: StageReview) -> str:  # info: def choose_public
    text = (final or "").strip()  # info: set text
    if not text:  # info: if not text
        text = (draft or "").strip()  # info: set text
    if not text:  # info: if not text
        return ""  # info: return ""
    head = text.splitlines()[0].upper().split()[0].strip(".:")  # info: set head
    if head in {"APPROVE", "CHANGES"}:  # info: if head in { "APPROVE" , "CHANGES" }
        text = (draft or "").strip()  # info: set text
    if text and text in {bruce.notes.strip(), carly.notes.strip()}:  # info: if text and text in { bruce . notes . strip ( ) , carly . notes . strip ( ) }
        text = (draft or "").strip()  # info: set text
    if LEAK_RE.search(text or ""):  # info: if LEAK_RE . search ( text or "" )
        return ""  # info: return ""
    return text  # info: return text


# ====================================================
# SECTION: function empty_result
# What it does: A pipeline result with no public text and both reviews unavailable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def empty_result() -> PipelineResult:  # info: def empty_result
    missing = StageReview("bruce", "unavailable", "UNAVAILABLE", "")  # info: set missing
    carly = StageReview("carly", "unavailable", "UNAVAILABLE", "")  # info: set carly
    return PipelineResult("", "", missing, carly, "skipped", "")  # info: return PipelineResult ( "" , "" , missing , carly , "skipped" , "" )


# ====================================================
# SECTION: function run_pipeline
# What it does: Ava draft, Bruce review, Carly review, Ava final. Public text is Ava only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_pipeline(user_message: str, conversation_context: str = "", infer=None, log=None) -> PipelineResult:  # info: def run_pipeline
    speak = infer or default_infer  # info: set speak
    write = log or stage_log  # info: set write
    write("request received")  # info: call write
    try:  # info: try
        draft = clean_reply(speak("ava", draft_prompt(user_message, conversation_context)))  # info: set draft
    except Exception as exc:  # info: except Exception as exc
        write(f"Ava draft unavailable {type(exc).__name__}")  # info: call write
        return empty_result()  # info: return empty_result ( )
    if not draft:  # info: if not draft
        write("Ava draft unavailable empty")  # info: call write
        return empty_result()  # info: return empty_result ( )
    write(f"Ava draft completed chars={len(draft)}")  # info: call write
    req = DiscordReviewRequest(user_message, conversation_context, draft)  # info: set req
    bruce = review_stage("bruce", bruce_prompt(req), speak, write)  # info: set bruce
    carly = review_stage("carly", carly_prompt(req, bruce), speak, write)  # info: set carly
    final = ""  # info: set final
    try:  # info: try
        final = clean_reply(speak("ava", final_prompt(req, bruce, carly)))  # info: set final
    except Exception as exc:  # info: except Exception as exc
        write(f"Ava final unavailable {type(exc).__name__}")  # info: call write
    if final:  # info: if final
        write(f"Ava final completed chars={len(final)}")  # info: call write
        final_status = "completed"  # info: set final_status
    else:  # info: else
        if not any(isinstance(arg, str) and arg.startswith("Ava final unavailable") for arg in ()):  # info: if not any ( isinstance ( arg , str ) and arg . startswith ( "Ava final unavailable" ) for arg in ( ) )
            write("Ava final unavailable empty")  # info: call write
        final_status = "unavailable"  # info: set final_status
    public = choose_public(final, draft, bruce, carly)  # info: set public
    return PipelineResult(public, draft, bruce, carly, final_status, final)  # info: return PipelineResult ( public , draft , bruce , carly , final_status , final )


# ====================================================
# SECTION: function load_seen
# What it does: Read handled Discord message ids. The file stores ids only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_seen(path: Path) -> dict:  # info: def load_seen
    if not path.is_file():  # info: if not path . is_file ( )
        return {}  # info: return { }
    try:  # info: try
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance ( data , dict ) else { }


# ====================================================
# SECTION: function save_seen
# What it does: Write handled message ids. Does not store message text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_seen(path: Path, data: dict) -> None:  # info: def save_seen
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents = True ,
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps ( data , indent = 2 ) + "\n" , encoding = "utf-8" )
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function context_from
# What it does: Use a referenced Discord message as conversation context when one is present.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def context_from(message: dict) -> str:  # info: def context_from
    ref = message.get("referenced_message") or {}  # info: set ref
    if not isinstance(ref, dict):  # info: if not isinstance ( ref , dict )
        return ""  # info: return ""
    return clip(str(ref.get("content") or ""), 500)  # info: return clip ( str ( ref . get ( "content" ) or "" ) , 500 )


# ====================================================
# SECTION: function respond
# What it does: Run the pipeline for Ava mentions and hand only public_text to post.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def respond(channel_id: str, messages: list, *, post, log=None, infer=None, seen_path: Path | None = None) -> dict:  # info: def respond
    write = log or stage_log  # info: set write
    seen_file = seen_path or SEEN_PATH  # info: set seen_file
    seen = load_seen(seen_file)  # info: set seen
    known = {str(item) for item in (seen.get(channel_id) or []) if str(item)}  # info: set known
    handled = 0  # info: set handled
    posted = 0  # info: set posted
    public_texts: list[str] = []  # info: set public_texts
    ordered = list(reversed(messages or []))  # info: set ordered
    for message in ordered:  # info: for message in ordered
        if not isinstance(message, dict):  # info: if not isinstance ( message , dict )
            continue  # info: continue
        mid = str(message.get("id") or "")  # info: set mid
        if not mid or mid in known or not invokes_ava(message):  # info: if not mid or mid in known or not invokes_ava ( message )
            continue  # info: continue
        text = str(message.get("content") or "").strip()  # info: set text
        if not text:  # info: if not text
            continue  # info: continue
        result = run_pipeline(text, context_from(message), infer=infer, log=write)  # info: set result
        handled += 1  # info: set handled
        if not result.public_text:  # info: if not result . public_text
            write("Discord send withheld")  # info: call write
            continue  # info: continue
        public_texts.append(result.public_text)  # info: public_texts . append ( result . public_text )
        try:  # info: try
            sent = post(channel_id, result.public_text)  # info: set sent
        except Exception as exc:  # info: except Exception as exc
            write(f"Discord send unavailable {type(exc).__name__}")  # info: call write
            continue  # info: continue
        known.add(mid)  # info: known . add ( mid )
        if sent:  # info: if sent
            posted += 1  # info: set posted
            write("Discord send completed")  # info: call write
        else:  # info: else
            write("Discord send skipped")  # info: call write
    seen[channel_id] = list(known)[-50:]  # info: seen [ channel_id ] = list ( known ) [ -50 : ]
    if handled:  # info: if handled
        save_seen(seen_file, seen)  # info: call save_seen
    return {"handled": handled, "posted": posted, "public_texts": public_texts}  # info: return { "handled" : handled , "posted" : posted , "public_texts" : public_texts }


# ====================================================
# SECTION: function apply_review
# What it does: Skip the pipeline unless the Discord review flag is on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_review(channel_id: str, messages: list, *, enabled: bool, respond_fn) -> dict:  # info: def apply_review
    if not enabled:  # info: if not enabled
        return {"handled": 0, "posted": 0, "public_texts": []}  # info: return { "handled" : 0 , "posted" : 0 , "public_texts" : [ ] }
    return respond_fn(channel_id, messages)  # info: return respond_fn ( channel_id , messages )
