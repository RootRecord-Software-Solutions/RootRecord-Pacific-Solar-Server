"""Locked Kokoro voices, report-kind personas and live-data gate (G3 port of G1 speakers.py).

Bruce = Echo (am_echo, 0.92) · Ava = Heart (af_heart, 0.82, default) · Carly = Nova (af_nova, 0.74)

G3 changes (2026-09-29, g3-voice-ailog): retire pattern is now
  <report>_current.wav  ->  Archive/<report>_YYYYMMDDTHHMM.wav  (+ .read.txt / .speak.txt sidecars)
Delivery removed: no AWS radio push, no Telegram, no speaker playback (OFF pending Alexander sign-off).
Persona map (AGENTS / KIND_AGENT), is_live gate and without_name are unchanged from G1.
Grok has no Kokoro voice (cloud Ara retired) — open question, deliberately not mapped.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

log = logging.getLogger("rr.voice.speakers")
HST = ZoneInfo("Pacific/Honolulu")

AGENTS = {
    "ava": {"name": "Ava", "kokoro": "af_heart", "speed": 0.82},
    "bruce": {"name": "Bruce", "kokoro": "am_echo", "speed": 0.92},
    "carly": {"name": "Carly", "kokoro": "af_nova", "speed": 0.74},
}

# Automated spoken desks. Keep the three loads even. (verbatim from G1)
KIND_AGENT = {
    "morning": "ava",
    "midday": "ava",
    "evening": "ava",
    "late": "ava",
    "summary": "ava",
    "weather": "ava",
    "nws": "ava",
    "chime": "ava",
    "official": "ava",
    "boot": "ava",
    "solar": "bruce",
    "energy": "carly",
    "system": "bruce",
    "remaining": "bruce",
    "hourly": "bruce",
    "earthquake": "carly",
    "kilauea": "carly",
    "hurricane": "carly",
    "alerts": "carly",
    "security": "carly",
    "bandwidth": "carly",
    "net": "carly",
}

_DEAD = (
    "not live",
    "offline stub",
    "facts not live",
    "no data",
    "end of status",
)


def is_current_audio(path: Path) -> bool:
    return Path(path).stem.lower().endswith("_current")


def retire_current(path: Path) -> Path | None:
    """Move <report>_current.<ext> to Archive/<report>_YYYYMMDDTHHMM.<ext> (its own mtime, HST) with sidecars."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size <= 0:
        return None
    stamp = datetime.fromtimestamp(path.stat().st_mtime, HST).strftime("%Y%m%dT%H%M")
    base = re.sub(r"_current$", "", path.stem, flags=re.I)
    arch = path.parent / "Archive"
    arch.mkdir(parents=True, exist_ok=True)
    dest = arch / f"{base}_{stamp}{path.suffix}"
    n = 0
    while dest.exists():
        n += 1
        dest = arch / f"{base}_{stamp}-{n}{path.suffix}"
    try:
        path.replace(dest)
    except OSError:
        return None
    for extra in (".read.txt", ".speak.txt"):
        side = path.with_suffix(extra)
        if side.is_file():
            try:
                side.replace(dest.with_suffix(extra))
            except OSError:
                pass
    return dest


def agent_for(kind: str) -> str:
    key = (kind or "").strip().lower()
    if key in AGENTS:
        return key
    return KIND_AGENT.get(key, "ava")


def kokoro_voice_for(kind: str) -> str:
    return AGENTS[agent_for(kind)]["kokoro"]


def speed_for(kind: str) -> float:
    return AGENTS[agent_for(kind)]["speed"]


def display_name(kind: str) -> str:
    return AGENTS[agent_for(kind)]["name"]


def _dead_line(text: str) -> bool:
    low = (text or "").strip().lower()
    if not low or len(low) < 12:
        return True
    if len(low) < 400:
        if "ecoflow: down" in low or "host: down" in low or "kilauea: down" in low:
            return True
        if "weather: down" in low:
            return True
    if any(m in low for m in _DEAD) and not re.search(r"\d", low):
        return True
    if "this is the ava core root record" in low and not re.search(r"\d", low):
        return True
    return False


def is_live(kind: str, text: str) -> bool:
    """True only when the spoken body has live facts for that desk. (verbatim G1 rules)"""
    raw = " ".join((text or "").split()).strip()
    key = (kind or "").strip().lower()
    if key in AGENTS:
        return len(re.sub(r"\s+", "", raw)) >= 8
    if _dead_line(raw):
        return False
    if key in {"chime"}:
        return bool(re.search(r"\d", raw) or "o'clock" in raw.lower() or "noon" in raw.lower())
    if key in {"solar", "energy"}:
        return bool(
            re.search(r"\d+\s*%", raw)
            or re.search(r"\d+\s*(w|watts|percent)\b", raw, re.I)
            or "rear shed" in raw.lower()
            or "solar panel" in raw.lower()
            or "energy desk" in raw.lower()
        )
    if key in {"system", "hourly"}:
        return bool(re.search(r"(cpu|ram|memory|npu|gpu).{0,12}\d+\s*%", raw, re.I) or re.search(r"\d+\s*%", raw))
    if key in {"weather", "nws", "official"}:
        return "nws" in raw.lower() or bool(re.search(r"\d", raw)) or "no active" in raw.lower()
    if key in {"kilauea"}:
        return "kilauea" in raw.lower() and "down" not in raw.lower()
    if key in {"security"}:
        return bool(re.search(r"\d", raw)) and (
            "security" in raw.lower()
            or "firewall" in raw.lower()
            or "sign-in" in raw.lower()
            or "listener" in raw.lower()
        )
    if key in {"bandwidth", "net"}:
        return bool(re.search(r"\d", raw)) and (
            "megabyte" in raw.lower()
            or "gigabyte" in raw.lower()
            or "kilobyte" in raw.lower()
            or "bytes" in raw.lower()
        )
    if key in {"earthquake"}:
        return "earthquake" in raw.lower() and ("usgs" in raw.lower() or bool(re.search(r"\d", raw)))
    if key in {"hurricane"}:
        return ("storm" in raw.lower() or "hurricane" in raw.lower() or "tropical" in raw.lower()) and (
            bool(re.search(r"\d", raw)) or "no named" in raw.lower() or "quiet" in raw.lower()
        )
    if key in {"remaining"}:
        return bool(re.search(r"\d", raw))
    if key in {"morning", "midday", "evening", "late", "summary", "boot"}:
        return bool(re.search(r"\d", raw))
    return bool(re.search(r"\d", raw))


_NAME_LEAD = re.compile(
    r"(?i)^(?:this is\s+)?(?:ava ivy|ava|bruce monitor|bruce|carly mal|carly)\s*[,.]\s+"
)


def without_name(text: str) -> str:
    """Spoken reports use the locked Kokoro voice. Do not say the agent name."""
    body = " ".join((text or "").split()).strip()
    while True:
        nxt = _NAME_LEAD.sub("", body, count=1).strip()
        if nxt == body:
            return body
        body = nxt
