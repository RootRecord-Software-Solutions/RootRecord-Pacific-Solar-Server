# ==============================================================================
# FILE: Reports/pipeline/generate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Generators. Deterministic text is the fallback. Voice builders stay the desk prose."""
from __future__ import annotations  # info: from __future__ import annotations

from model import GENERATOR_VERSION  # info: from model import GENERATOR_VERSION

MAX_RETRY = 3  # info: set MAX_RETRY


# ====================================================
# SECTION: function deterministic
# What it does: Write sections from observations only. An empty window says nothing was in it. It does not invent items.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def deterministic(context: dict) -> dict:  # info: def deterministic
    observations = list(context.get("observations") or [])  # info: set observations
    start = (context.get("window") or {}).get("window_start") or ""  # info: set start
    end = (context.get("window") or {}).get("window_end") or ""  # info: set end
    if not observations:  # info: if not observations
        text = f"Nothing in this window {start} to {end}."  # info: set text
        sections = [{"heading": "Window", "text": text}]  # info: set sections
        spoken = [text]  # info: set spoken
    else:  # info: else
        sections = []  # info: set sections
        spoken = []  # info: set spoken
        for item in observations:  # info: for item in observations
            if isinstance(item, dict):  # info: if isinstance ( item , dict )
                line = str(item.get("title") or item.get("text") or "").strip()  # info: set line
            else:  # info: else
                line = str(item).strip()  # info: set line
            if not line:  # info: if not line
                continue  # info: continue
            sections.append({"heading": "Fact", "text": line})  # info: sections . append
            spoken.append(line if line.endswith(".") else line + ".")  # info: spoken . append
        if not sections:  # info: if not sections
            text = f"Nothing in this window {start} to {end}."  # info: set text
            sections = [{"heading": "Window", "text": text}]  # info: set sections
            spoken = [text]  # info: set spoken
    return {  # info: return {
        "sections": sections,  # info: "sections" : sections
        "spoken": spoken,  # info: "spoken" : spoken
        "provider": "deterministic",  # info: "provider" : "deterministic"
        "model": "template",  # info: "model" : "template"
        "generator_version": GENERATOR_VERSION,  # info: "generator_version"
    }  # info: }


# ====================================================
# SECTION: function from_measured
# What it does: Wrap markdown a voice builder already wrote. It does not call the builder again.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def from_measured(markdown: str, spoken: list, provider: str = "voice_build") -> dict:  # info: def from_measured
    body = (markdown or "").split("\n## Spoken", 1)[0].strip()  # info: set body
    return {  # info: return {
        "sections": [{"heading": "Report", "text": body}],  # info: "sections"
        "spoken": list(spoken or []),  # info: "spoken"
        "provider": provider,  # info: "provider" : provider
        "model": "template",  # info: "model" : "template"
        "generator_version": GENERATOR_VERSION,  # info: "generator_version"
    }  # info: }


# ====================================================
# SECTION: function note_retry
# What it does: Raise a stage retry count by one, capped at three. It does not loop.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def note_retry(stage: dict) -> dict:  # info: def note_retry
    stage["retry"] = min(MAX_RETRY, int(stage.get("retry") or 0) + 1)  # info: stage [ "retry" ] = min
    return stage  # info: return stage
