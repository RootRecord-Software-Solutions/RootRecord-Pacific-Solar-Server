# ==============================================================================
# FILE: Communications/CouncilPersona/scripts/personas.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Load Ava, Bruce, and Carly chat system text for the council relay.

Canonical identity stays in Library Agent Context. These prompts are the
Telegram rendering of that identity. SPEAK_LOCK is prefixed from speech_scrub.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
from pathlib import Path  # info: from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
PROMPTS = ROOT / "prompts"  # info: set PROMPTS
PACIFIC = ROOT.parents[1]  # info: set PACIFIC
VOICES = ("ava", "bruce", "carly")  # info: set VOICES

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
# SECTION: function system_for
# What it does: Return SPEAK_LOCK plus that voice's chat prompt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def system_for(voice: str) -> str:  # info: def system_for
    key = (voice or "").strip().lower()  # info: set key
    if key not in VOICES:  # info: if key not in VOICES
        raise KeyError(key)  # info: raise KeyError
    body = (PROMPTS / f"{key}.md").read_text(encoding="utf-8").strip()  # info: set body
    if not body:  # info: if not body
        raise RuntimeError(f"empty persona prompt: {key}")  # info: raise RuntimeError
    return speak_lock() + "\n\n" + body  # info: return speak_lock ( ) + "\n\n" + body
