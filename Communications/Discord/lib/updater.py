# ==============================================================================
# FILE: Communications/Discord/lib/updater.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Global Updater turn text. Identity is read from the Library pack, not stored here.

The public introduction used when a reply claims to be another agent is the
Public introduction section of IDENTITY.md. This module does not own that sentence.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
import re  # info: import re
from pathlib import Path  # info: from pathlib import Path

from lib.observations import HostObservation  # info: from lib . observations import HostObservation

HERE = Path(__file__).resolve().parent  # info: set HERE
DISCORD = HERE.parent  # info: set DISCORD
COMMS = DISCORD.parent  # info: set COMMS
PERSONAS = COMMS / "CouncilPersona" / "scripts" / "personas.py"  # info: set PERSONAS
VOICE = "global-updater"  # info: set VOICE
LEAK_RE = re.compile(r"DESK_LIVE:|HARD RULES FOR THIS TURN|Do NOT state watts|standing envelopes|\[desk:", re.I)  # info: set LEAK_RE
OTHER_AGENT = re.compile(  # info: set OTHER_AGENT
    r"\b(?:i(?:'| a)?m|this is)\s+(?:ava(?:\s+ivy)?|bruce(?:\s+monitor)?|carly(?:\s+mal)?)\b",  # info: regex
    re.I,  # info: re . I
)  # info: )
STYLE_BREAK = re.compile(r"heyyy|ava here|gamer girl|😎", re.I)  # info: set STYLE_BREAK
SERVICE_CLAIM = re.compile(r"\b(?:is|are)\s+(?:currently\s+)?(?:running|up|healthy|down|offline|online)\b", re.I)  # info: set SERVICE_CLAIM
UNCERTAIN = re.compile(r"\b(?:can't|cannot|can not|don't|do not|unavailable|not sure)\b", re.I)  # info: set UNCERTAIN
HOST_ASK = re.compile(  # info: set HOST_ASK
    r"\b(?:memory|ram|cpu|disk|load|uptime|watts|soc|measurement|service status|current state|current status)\b",  # info: regex
    re.I,  # info: re . I
)  # info: )
METRIC_WORD = ("memory", "ram", "cpu", "disk", "network", "uptime", "load", "watts", "soc")  # info: set METRIC_WORD
_PACK = None  # info: set _PACK
_INTRO = ""  # info: set _INTRO


# ====================================================
# SECTION: function personas
# What it does: Load the existing Library persona reader. Does not copy the pack.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def personas():  # info: def personas
    global _PACK  # info: global _PACK
    if _PACK is not None:  # info: if _PACK is not None
        return _PACK  # info: return _PACK
    spec = importlib.util.spec_from_file_location("rr_council_persona_updater", PERSONAS)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader is None
        raise RuntimeError("personas.py is missing")  # info: raise RuntimeError
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    _PACK = mod  # info: set _PACK
    return mod  # info: return mod


# ====================================================
# SECTION: function system_text
# What it does: Return the Library system text for the Global Updater voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def system_text() -> str:  # info: def system_text
    return personas().system_for(VOICE)  # info: return personas ( ) . system_for ( VOICE )


# ====================================================
# SECTION: function section_text
# What it does: Return one markdown section from a Library file. Empty if the heading is absent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def section_text(path: Path, heading: str) -> str:  # info: def section_text
    if not path.is_file():  # info: if not path . is_file ( )
        return ""  # info: return ""
    lines = path.read_text(encoding="utf-8").splitlines()  # info: set lines
    start = None  # info: set start
    for index, line in enumerate(lines):  # info: for index , line in enumerate ( lines )
        if line.strip() == f"## {heading}":  # info: if line . strip ( ) == f"## { heading } "
            start = index + 1  # info: set start
            break  # info: break
    if start is None:  # info: if start is None
        return ""  # info: return ""
    body = []  # info: set body
    for line in lines[start:]:  # info: for line in lines [ start : ]
        if line.startswith("## "):  # info: if line . startswith ( "## " )
            break  # info: break
        body.append(line)  # info: body . append ( line )
    return "\n".join(body).strip()  # info: return "\n" . join ( body ) . strip ( )


# ====================================================
# SECTION: function canonical_intro
# What it does: Read the public introduction from IDENTITY.md. Derived, not a second persona.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def canonical_intro() -> str:  # info: def canonical_intro
    global _INTRO  # info: global _INTRO
    if _INTRO:  # info: if _INTRO
        return _INTRO  # info: return _INTRO
    folder = personas().pack_dir(VOICE)  # info: set folder
    text = section_text(folder / "IDENTITY.md", "Public introduction")  # info: set text
    if not text.startswith("I'm the Root Record Global Updater."):  # info: if not text . startswith
        raise RuntimeError("public introduction missing")  # info: raise RuntimeError
    _INTRO = text  # info: set _INTRO
    return text  # info: return text


# ====================================================
# SECTION: function notes_for
# What it does: Pull the Library section that covers this question. Empty means uncovered.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def notes_for(question: str) -> str:  # info: def notes_for
    folder = personas().pack_dir(VOICE)  # info: set folder
    asked = (question or "").lower()  # info: set asked
    chunks = []  # info: set chunks
    if any(hint in asked for hint in ("who are you", "who is this", "what are you", "your name")):  # info: if any
        chunks.append(section_text(folder / "IDENTITY.md", "Public introduction"))  # info: chunks . append
    if "pacific" in asked:  # info: if "pacific" in asked
        chunks.append(section_text(folder / "CONTEXT" / "INFRASTRUCTURE.md", "RootRecord Pacific Solar Server"))  # info: chunks . append
    elif any(hint in asked for hint in ("what do you do", "what can you", "what information", "help desk", "help-desk")):  # info: elif any
        chunks.append(section_text(folder / "ROLE-AND-BOUNDS.md", "What this agent does"))  # info: chunks . append
    if "agent context" in asked or "where are the agent" in asked:  # info: if "agent context" in asked
        chunks.append(section_text(folder / "ROLE-AND-BOUNDS.md", "Canonical identity"))  # info: chunks . append
    if any(hint in asked for hint in ("telegram", "repository", "documentation", "which system")):  # info: if any
        chunks.append(section_text(folder / "CONTEXT" / "REPOS.md", "Ownership"))  # info: chunks . append
    text = "\n\n".join(part for part in chunks if part)  # info: set text
    return text[:2000]  # info: return text [ : 2000 ]


# ====================================================
# SECTION: function asks_host
# What it does: True when the question is about a measurement or current status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def asks_host(question: str) -> bool:  # info: def asks_host
    return bool(HOST_ASK.search(question or ""))  # info: return bool ( HOST_ASK . search ( question or "" ) )


# ====================================================
# SECTION: function build_prompt
# What it does: Turn instructions plus the Library notes and the observation block.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_prompt(question: str, notes: str, observation: str) -> str:  # info: def build_prompt
    covered = (notes or "").strip() or "(none)"  # info: set covered
    return (  # info: return
        "Authoritative notes:\n"  # info: "Authoritative notes:\n"
        f"{covered}\n\n"  # info: f" { covered } \n\n"
        "Observations:\n"  # info: "Observations:\n"
        f"{observation.strip()}\n\n"  # info: f" { observation . strip ( ) } \n\n"
        "Answer the user from those notes and observations only.\n"  # info: "Answer the user from those notes and observations only.\n"
        "If a measurement is not in Observations, say you do not have it.\n"  # info: "If a measurement is not in Observations, say you do not have it.\n"
        "If Observations says stale, say the sample is stale and give its time.\n"  # info: "If Observations says stale, say the sample is stale and give its time.\n"
        "If the notes and observations do not establish the answer, say you cannot establish it.\n"  # info: "If the notes and observations do not establish the answer, say you cannot establish it.\n"
        "Do not invent measurements. Do not claim to be Ava, Bruce, or Carly.\n"  # info: "Do not invent measurements. Do not claim to be Ava, Bruce, or Carly.\n"
        "Do not use jokes, emoji, or gamer language.\n\n"  # info: "Do not use jokes, emoji, or gamer language.\n\n"
        f"User:\n{(question or '').strip()[:2000]}"  # info: f"User:\n { ( question or '' ) . strip ( ) [ : 2000 ] } "
    )  # info: )


# ====================================================
# SECTION: function clean_reply
# What it does: Drop empty output and instruction leaks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_reply(text: str | None) -> str:  # info: def clean_reply
    raw = (text or "").strip()  # info: set raw
    if not raw or LEAK_RE.search(raw):  # info: if not raw or LEAK_RE . search ( raw )
        return ""  # info: return ""
    lines = [line for line in raw.splitlines() if not line.startswith(("[ok]", "[fail]", "[warn]", "[busy]"))]  # info: set lines
    return "\n".join(lines).strip()  # info: return "\n" . join ( lines ) . strip ( )


# ====================================================
# SECTION: function claims_service
# What it does: True when a sentence states a live service condition. Negated wording is not a claim.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def claims_service(sentence: str) -> bool:  # info: def claims_service
    if not SERVICE_CLAIM.search(sentence or ""):  # info: if not SERVICE_CLAIM . search
        return False  # info: return False
    if re.search(r"\b(?:not|whether|without)\b", sentence, re.I):  # info: if re . search
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function metric_keys
# What it does: Metric words present in one sentence.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def metric_keys(sentence: str) -> list[str]:  # info: def metric_keys
    low = sentence.lower()  # info: set low
    return [key for key in METRIC_WORD if re.search(rf"\b{key}\b", low)]  # info: return list comprehension


# ====================================================
# SECTION: function recorded_values
# What it does: Figures the reply may cite for this sample status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recorded_values(obs: HostObservation) -> dict[str, float]:  # info: def recorded_values
    if obs.status == "unavailable":  # info: if obs . status == "unavailable"
        return {}  # info: return { }
    values: dict[str, float] = {}  # info: set values
    if obs.cpu_percent is not None:  # info: if obs . cpu_percent is not None
        values["cpu"] = obs.cpu_percent  # info: values [ "cpu" ] = obs . cpu_percent
    if obs.mem_used_percent is not None:  # info: if obs . mem_used_percent is not None
        values["memory"] = obs.mem_used_percent  # info: values [ "memory" ] = obs . mem_used_percent
        values["ram"] = obs.mem_used_percent  # info: values [ "ram" ] = obs . mem_used_percent
    if obs.load1 is not None:  # info: if obs . load1 is not None
        values["load"] = obs.load1  # info: values [ "load" ] = obs . load1
    return values  # info: return values


# ====================================================
# SECTION: function unavailable_sentence
# What it does: Honest sentence when that metric was not supplied.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def unavailable_sentence(keys: list[str]) -> str:  # info: def unavailable_sentence
    if any(key in keys for key in ("memory", "ram")):  # info: if any
        return "I don't currently have a fresh memory measurement."  # info: return
    if "cpu" in keys:  # info: if "cpu" in keys
        return "I don't currently have a fresh CPU measurement."  # info: return
    if "load" in keys:  # info: if "load" in keys
        return "I don't currently have a fresh host-load measurement."  # info: return
    if "disk" in keys:  # info: if "disk" in keys
        return "I don't currently have a fresh disk measurement."  # info: return
    if "network" in keys:  # info: if "network" in keys
        return "I don't currently have a fresh network measurement."  # info: return
    if "uptime" in keys:  # info: if "uptime" in keys
        return "I don't currently have a fresh uptime measurement."  # info: return
    if any(key in keys for key in ("watts", "soc")):  # info: if any
        return "I don't currently have a fresh power measurement."  # info: return
    return "I don't currently have a fresh host measurement."  # info: return


# ====================================================
# SECTION: function fresh_sentence
# What it does: Cite only the recorded fresh figures and their time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fresh_sentence(obs: HostObservation) -> str:  # info: def fresh_sentence
    parts = [f"The latest recorded host measurement I have is from {obs.at}."]  # info: set parts
    if obs.cpu_percent is not None:  # info: if obs . cpu_percent is not None
        parts.append(f"CPU is {obs.cpu_percent}%.")  # info: parts . append
    if obs.mem_used_percent is not None:  # info: if obs . mem_used_percent is not None
        parts.append(f"Memory used is {obs.mem_used_percent}%.")  # info: parts . append
    if obs.load1 is not None:  # info: if obs . load1 is not None
        parts.append(f"Host load (1 minute) is {obs.load1}.")  # info: parts . append
    parts.append("I do not have a newer measurement.")  # info: parts . append
    return " ".join(parts)  # info: return " " . join ( parts )


# ====================================================
# SECTION: function stale_sentence
# What it does: Cite the sample time and say the sample is stale.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stale_sentence(obs: HostObservation) -> str:  # info: def stale_sentence
    return (  # info: return
        f"The latest recorded host measurement I have is from {obs.at}. "  # info: f"The latest recorded host measurement I have is from { obs . at } . "
        "That sample is stale. I do not have a newer measurement."  # info: "That sample is stale. I do not have a newer measurement."
    )  # info: )


# ====================================================
# SECTION: function honest_for
# What it does: Replace one unsupported measurement or service claim.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def honest_for(sentence: str, obs: HostObservation) -> str:  # info: def honest_for
    if claims_service(sentence):  # info: if claims_service ( sentence )
        return "I don't currently have a service-status observation."  # info: return
    keys = metric_keys(sentence)  # info: set keys
    recorded = recorded_values(obs)  # info: set recorded
    if obs.status == "unavailable" or any(key not in recorded for key in keys):  # info: if obs . status == "unavailable" or any
        return unavailable_sentence(keys)  # info: return unavailable_sentence ( keys )
    if obs.status == "stale":  # info: if obs . status == "stale"
        return stale_sentence(obs)  # info: return stale_sentence ( obs )
    return fresh_sentence(obs)  # info: return fresh_sentence ( obs )


# ====================================================
# SECTION: function numbers_in
# What it does: Numeric tokens in a sentence, skipping nothing yet.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def numbers_in(sentence: str) -> list[float]:  # info: def numbers_in
    found = []  # info: set found
    for token in re.findall(r"\d+(?:\.\d+)?", sentence):  # info: for token in re . findall
        try:  # info: try
            found.append(float(token))  # info: found . append ( float ( token ) )
        except ValueError:  # info: except ValueError
            continue  # info: continue
    return found  # info: return found


# ====================================================
# SECTION: function sentence_allowed
# What it does: True when a metric sentence cites only supplied figures.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sentence_allowed(sentence: str, obs: HostObservation) -> bool:  # info: def sentence_allowed
    if claims_service(sentence):  # info: if claims_service ( sentence )
        return False  # info: return False
    keys = metric_keys(sentence)  # info: set keys
    if not keys:  # info: if not keys
        return True  # info: return True
    if not re.search(r"\d", sentence):  # info: if not re . search
        return bool(UNCERTAIN.search(sentence))  # info: return bool ( UNCERTAIN . search ( sentence ) )
    recorded = recorded_values(obs)  # info: set recorded
    if any(key not in recorded for key in keys):  # info: if any
        return False  # info: return False
    nums = numbers_in(sentence)  # info: set nums
    for key in keys:  # info: for key in keys
        if not any(abs(num - recorded[key]) <= 0.5 for num in nums):  # info: if not any
            return False  # info: return False
    if obs.status == "stale" and "stale" not in sentence.lower():  # info: if obs . status == "stale"
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function split_sentences
# What it does: Split a reply on sentence boundaries.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def split_sentences(text: str) -> list[str]:  # info: def split_sentences
    parts = re.split(r"(?<=[.!?])\s+", text.strip())  # info: set parts
    return [part.strip() for part in parts if part.strip()]  # info: return list comprehension


# ====================================================
# SECTION: function enforce
# What it does: Keep a professional reply, or replace invented measurements and other identities.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def enforce(reply: str, obs: HostObservation, notes: str, question: str) -> str:  # info: def enforce
    text = clean_reply(reply)  # info: set text
    if not text:  # info: if not text
        return ""  # info: return ""
    if OTHER_AGENT.search(text) or STYLE_BREAK.search(text):  # info: if OTHER_AGENT . search ( text ) or STYLE_BREAK . search ( text )
        return canonical_intro()  # info: return canonical_intro ( )
    kept: list[str] = []  # info: set kept
    replaced: list[str] = []  # info: set replaced
    for sentence in split_sentences(text):  # info: for sentence in split_sentences ( text )
        if sentence_allowed(sentence, obs):  # info: if sentence_allowed ( sentence , obs )
            kept.append(sentence)  # info: kept . append ( sentence )
        else:  # info: else
            replaced.append(honest_for(sentence, obs))  # info: replaced . append ( honest_for ( sentence , obs ) )
    unique = []  # info: set unique
    for line in replaced:  # info: for line in replaced
        if line not in unique:  # info: if line not in unique
            unique.append(line)  # info: unique . append ( line )
    out = " ".join(kept + unique).strip()  # info: set out
    if obs.status in {"fresh", "stale"} and obs.at and obs.at not in out and metric_keys(out):  # info: if obs . status in
        out = f"{out} The latest recorded host measurement I have is from {obs.at}."  # info: set out
    if not (notes or "").strip() and not asks_host(question) and not UNCERTAIN.search(out):  # info: if not notes and not asks_host
        return "I can't establish that from the information available to me."  # info: return
    return out  # info: return out
