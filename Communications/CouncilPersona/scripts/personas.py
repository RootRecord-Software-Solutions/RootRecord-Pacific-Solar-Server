# ==============================================================================
# FILE: Communications/CouncilPersona/scripts/personas.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Read council chat system text from Library Agent Context.

This module does not store identity. SPEAK_LOCK is a speech rule from
speech_scrub.py. The paragraphs come from the Library pack, in place.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
from pathlib import Path  # info: from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
PACIFIC = ROOT.parents[1]  # info: set PACIFIC
ECOSYSTEM = PACIFIC.parents[1]  # info: set ECOSYSTEM
LIBRARY = ECOSYSTEM / "5 - RootRecord-Library" / "Agent Context"  # info: set LIBRARY
VOICES = {  # info: set VOICES
    "ava": "Ava-Agent-Context",  # info: "ava" : "Ava-Agent-Context"
    "bruce": "Bruce-Agent-Context",  # info: "bruce" : "Bruce-Agent-Context"
    "carly": "Carly-Agent-Context",  # info: "carly" : "Carly-Agent-Context"
}  # info: }
# Who the agent is. CONTEXT/, README, CHANGELOG, and HANDOFF-TEMPLATE stay in
# the Library and are not pasted into a 4096-token Telegram turn.
PACK_FILES = ("IDENTITY.md", "ROLE-AND-BOUNDS.md", "PRINCIPLES.md", "WORKFLOW.md")  # info: set PACK_FILES

# ====================================================
# SECTION: function speak_lock
# What it does: Load SPEAK_LOCK from the existing speech scrub module.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speak_lock() -> str:  # info: def speak_lock
    path = PACIFIC / "Media" / "Voice" / "scripts" / "speech_scrub.py"  # info: set path
    spec = importlib.util.spec_from_file_location("rr_speech_scrub", path)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader is None
        raise RuntimeError("speech_scrub.py is missing")  # info: raise RuntimeError
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    text = (getattr(mod, "SPEAK_LOCK", "") or "").strip()  # info: set text
    if not text.startswith("Speak the answer only."):  # info: if not text . startswith
        raise RuntimeError("SPEAK_LOCK missing")  # info: raise RuntimeError
    return text  # info: return text

# ====================================================
# SECTION: function pack_dir
# What it does: Return the Library pack directory for a council voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pack_dir(voice: str) -> Path:  # info: def pack_dir
    key = (voice or "").strip().lower()  # info: set key
    name = VOICES.get(key)  # info: set name
    if not name:  # info: if not name
        raise KeyError(key)  # info: raise KeyError
    path = LIBRARY / name  # info: set path
    if not path.is_dir():  # info: if not path . is_dir
        raise RuntimeError(f"Library pack missing: {path}")  # info: raise RuntimeError
    return path  # info: return path

# ====================================================
# SECTION: function system_for
# What it does: Return SPEAK_LOCK plus the Library identity files for that voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def system_for(voice: str) -> str:  # info: def system_for
    folder = pack_dir(voice)  # info: set folder
    parts = [speak_lock()]  # info: set parts
    for name in PACK_FILES:  # info: for name in PACK_FILES
        file = folder / name  # info: set file
        body = file.read_text(encoding="utf-8").strip()  # info: set body
        if not body:  # info: if not body
            raise RuntimeError(f"empty Library file: {file}")  # info: raise RuntimeError
        parts.append(body)  # info: parts . append ( body )
    return "\n\n".join(parts)  # info: return "\n\n" . join ( parts )
