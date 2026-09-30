"""Strip engine-identity and constraint-narration from spoken replies.

Prompts must not list vendor names. This filter is the backstop.

G3 copy (2026-09-29, old-repo migration) of G1 persona/scripts/speech_scrub.py, logic unchanged. Library function only:
not wired into any LLM path yet (router / specialists / relay are other passes' code). CLI: echo text | python3 speech_scrub.py
"""
from __future__ import annotations

import re

# Positive lock for system prompts. No vendor list — listing names teaches them.
SPEAK_LOCK = (
    "Speak the answer only. If asked who or what you are, give your name. "
    "A missing line: you don't have that live."
)

# Identity / vendor tokens that must never leave a spoken reply.
_ENGINE = re.compile(
    r"[^.!?\n]*\b(?:"
    r"llama(?:\s*\d+(?:\.\d+)?)?|"
    r"qwen(?:\s*\d+(?:\.\d+)?)?|"
    r"grok(?:\s*-?\d+(?:\.\d+)?)?|"
    r"chatgpt|chat\s*gpt|"
    r"claude|"
    r"gemini|"
    r"mistral|mixtral|"
    r"gemma(?:\s*\d+)?|"
    r"gpt-?\d|"
    r"composer-?\d*|"
    r"fastflowlm|"
    r"ollama|"
    r"anthropic|"
    r"openai|"
    r"xai|"
    r"cursor"
    r")\b[^.!?\n]*[.!]?",
    re.IGNORECASE,
)

# Reciting standing orders instead of answering.
_CONSTRAINT = re.compile(
    r"[^.!?\n]*(?:"
    r"as an ai\b|"
    r"as a(?:n)? (?:large )?language model\b|"
    r"i(?:'m| am) (?:an? )?(?:ai|llm|language model)\b|"
    r"i(?:'m| am) not (?:supposed|allowed|permitted) to\b|"
    r"i (?:cannot|can't|won't) (?:mention|discuss|share|say|invent|dump|reveal|talk about)\b|"
    r"i(?:'m| am) (?:instructed|programmed) (?:not )?to\b|"
    r"per my (?:instructions|guidelines|rules|system prompt)\b|"
    r"my (?:instructions|guidelines|rules) (?:say|tell|prevent|forbid|don't allow)\b|"
    r"constraints stay\b|"
    r"i (?:do not|don't) dump\b|"
    r"i (?:will not|won't) invent\b|"
    r"i(?:'m| am) (?:powered by|running on|based on)\b|"
    r"i(?:'m| am) not (?:able|allowed) to (?:discuss|mention|share|say)\b|"
    r"facts only\b|"
    r"measured facts only\b|"
    r"do not invent(?:\s+numbers)?\b|"
    r"no invented numbers\b"
    r")[^.!?\n]*[.!]?",
    re.IGNORECASE,
)


def scrub_speech(text: str) -> str:
    """Drop engine-name sentences and constraint recaps. Keep the rest."""
    clean = (text or "").replace("\r\n", "\n")
    clean = _ENGINE.sub("", clean)
    clean = _CONSTRAINT.sub("", clean)
    clean = re.sub(r"[ \t]+\n", "\n", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)
    clean = re.sub(r"  +", " ", clean)
    return clean.strip()


if __name__ == "__main__":
    import sys

    print(scrub_speech(sys.stdin.read()))
