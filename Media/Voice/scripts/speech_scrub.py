# ==============================================================================
# FILE: Media/Voice/scripts/speech_scrub.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Strip engine-identity and constraint-narration from spoken replies.

Prompts must not list vendor names. This filter is the backstop.

G3 copy (2026-09-29, old-repo migration) of G1 persona/scripts/speech_scrub.py, logic unchanged. Library function only:
not wired into any LLM path yet (router / specialists / relay are other passes' code). CLI: echo text | python3 speech_scrub.py
"""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re

# Positive lock for system prompts. No vendor list — listing names teaches them.
SPEAK_LOCK = (  # info: set SPEAK_LOCK
    "Speak the answer only. If asked who or what you are, give your name. "  # info: "Speak the answer only. If asked who or what you are, give your name. "
    "A missing line: you don't have that live."  # info: "A missing line: you don't have that live."
)  # info: )

# Identity / vendor tokens that must never leave a spoken reply.
# ====================================================
# SECTION: _ENGINE
# What it does: Set _ENGINE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_ENGINE = re.compile(  # info: set _ENGINE
    r"[^.!?\n]*\b(?:"  # info: r"[^.!?\n]*\b(?:"
    r"llama(?:\s*\d+(?:\.\d+)?)?|"  # info: r"llama(?:\s*\d+(?:\.\d+)?)?|"
    r"qwen(?:\s*\d+(?:\.\d+)?)?|"  # info: r"qwen(?:\s*\d+(?:\.\d+)?)?|"
    r"grok(?:\s*-?\d+(?:\.\d+)?)?|"  # info: r"grok(?:\s*-?\d+(?:\.\d+)?)?|"
    r"chatgpt|chat\s*gpt|"  # info: r"chatgpt|chat\s*gpt|"
    r"claude|"  # info: r"claude|"
    r"gemini|"  # info: r"gemini|"
    r"mistral|mixtral|"  # info: r"mistral|mixtral|"
    r"gemma(?:\s*\d+)?|"  # info: r"gemma(?:\s*\d+)?|"
    r"gpt-?\d|"  # info: r"gpt-?\d|"
    r"composer-?\d*|"  # info: r"composer-?\d*|"
    r"fastflowlm|"  # info: r"fastflowlm|"
    r"ollama|"  # info: r"ollama|"
    r"anthropic|"  # info: r"anthropic|"
    r"openai|"  # info: r"openai|"
    r"xai|"  # info: r"xai|"
    r"cursor"  # info: r"cursor"
    r")\b[^.!?\n]*[.!]?",  # info: r")\b[^.!?\n]*[.!]?" ,
    re.IGNORECASE,  # info: re . IGNORECASE ,
)  # info: )

# Reciting standing orders instead of answering.
# ====================================================
# SECTION: _CONSTRAINT
# What it does: Set _CONSTRAINT.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_CONSTRAINT = re.compile(  # info: set _CONSTRAINT
    r"[^.!?\n]*(?:"  # info: r"[^.!?\n]*(?:"
    r"as an ai\b|"  # info: r"as an ai\b|"
    r"as a(?:n)? (?:large )?language model\b|"  # info: r"as a(?:n)? (?:large )?language model\b|"
    r"i(?:'m| am) (?:an? )?(?:ai|llm|language model)\b|"  # info: r"i(?:'m| am) (?:an? )?(?:ai|llm|language model)\b|"
    r"i(?:'m| am) not (?:supposed|allowed|permitted) to\b|"  # info: r"i(?:'m| am) not (?:supposed|allowed|permitted) to\b|"
    r"i (?:cannot|can't|won't) (?:mention|discuss|share|say|invent|dump|reveal|talk about)\b|"  # info: r"i (?:cannot|can't|won't) (?:mention|discuss|share|say|invent|dump|reveal|talk about)\b|"
    r"i(?:'m| am) (?:instructed|programmed) (?:not )?to\b|"  # info: r"i(?:'m| am) (?:instructed|programmed) (?:not )?to\b|"
    r"per my (?:instructions|guidelines|rules|system prompt)\b|"  # info: r"per my (?:instructions|guidelines|rules|system prompt)\b|"
    r"my (?:instructions|guidelines|rules) (?:say|tell|prevent|forbid|don't allow)\b|"  # info: r"my (?:instructions|guidelines|rules) (?:say|tell|prevent|forbid|don't allow)\b|"
    r"constraints stay\b|"  # info: r"constraints stay\b|"
    r"i (?:do not|don't) dump\b|"  # info: r"i (?:do not|don't) dump\b|"
    r"i (?:will not|won't) invent\b|"  # info: r"i (?:will not|won't) invent\b|"
    r"i(?:'m| am) (?:powered by|running on|based on)\b|"  # info: r"i(?:'m| am) (?:powered by|running on|based on)\b|"
    r"i(?:'m| am) not (?:able|allowed) to (?:discuss|mention|share|say)\b|"  # info: r"i(?:'m| am) not (?:able|allowed) to (?:discuss|mention|share|say)\b|"
    r"facts only\b|"  # info: r"facts only\b|"
    r"measured facts only\b|"  # info: r"measured facts only\b|"
    r"do not invent(?:\s+numbers)?\b|"  # info: r"do not invent(?:\s+numbers)?\b|"
    r"no invented numbers\b"  # info: r"no invented numbers\b"
    r")[^.!?\n]*[.!]?",  # info: r")[^.!?\n]*[.!]?" ,
    re.IGNORECASE,  # info: re . IGNORECASE ,
)  # info: )


# ====================================================
# SECTION: function scrub_speech
# What it does: Drop engine-name sentences and constraint recaps. Keep the rest.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def scrub_speech(text: str) -> str:  # info: def scrub_speech
    """Drop engine-name sentences and constraint recaps. Keep the rest."""  # info: """Drop engine-name sentences and constraint recaps. Keep the rest."""
    clean = (text or "").replace("\r\n", "\n")  # info: set clean
    clean = _ENGINE.sub("", clean)  # info: set clean
    clean = _CONSTRAINT.sub("", clean)  # info: set clean
    clean = re.sub(r"[ \t]+\n", "\n", clean)  # info: set clean
    clean = re.sub(r"\n{3,}", "\n\n", clean)  # info: set clean
    clean = re.sub(r"  +", " ", clean)  # info: set clean
    return clean.strip()  # info: return clean . strip ( )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    import sys  # info: import sys

    print(scrub_speech(sys.stdin.read()))  # info: call print
