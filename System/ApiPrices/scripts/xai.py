#!/usr/bin/env python3
"""xAI chat and TTS. Package ApiPrices.

Refuses unless RR_API_SPEND=1 and may_spend('xai') is true.
Does not call Kokoro, speakers, or report writers.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import api_ledger
import envload

CHAT_URL = "https://api.x.ai/v1/chat/completions"
TTS_URL = "https://api.x.ai/v1/tts"
DEFAULT_MODEL = api_ledger.DEFAULT_XAI_MODEL
GROK_DOWN_HOURS = 6


class XAIError(RuntimeError):
    pass


def _status_path() -> Path:
    return api_ledger.data_dir() / "grok-status.json"


def _load_status() -> dict[str, Any]:
    path = _status_path()
    if not path.is_file():
        return {"ok": True}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ok": True}
    return data if isinstance(data, dict) else {"ok": True}


def _save_status(data: dict[str, Any]) -> None:
    path = _status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def grok_is_down() -> bool:
    st = _load_status()
    if st.get("halt"):
        return True
    if st.get("ok", True):
        return False
    until = st.get("until")
    if not until:
        return True
    try:
        return datetime.now(timezone.utc) < datetime.fromisoformat(str(until))
    except ValueError:
        return True


def mark_grok_down(reason: str) -> None:
    until = datetime.now(timezone.utc) + timedelta(hours=GROK_DOWN_HOURS)
    _save_status(
        {
            "ok": False,
            "reason": reason[:300],
            "at": datetime.now(timezone.utc).isoformat(),
            "until": until.isoformat(),
        }
    )


def mark_grok_up() -> None:
    st = _load_status()
    if st.get("halt"):
        return
    _save_status({"ok": True, "at": datetime.now(timezone.utc).isoformat()})


def _blocked() -> str | None:
    if not api_ledger.spend_gate_open():
        return "rr_api_spend_off"
    if grok_is_down():
        return "grok_down"
    ok, why = api_ledger.may_spend("xai")
    if not ok:
        return why
    if not envload.key_set("XAI_API_KEY"):
        return "no_key"
    return None


def _headers() -> dict[str, str]:
    envload.load_env()
    key = (os.environ.get("XAI_API_KEY") or "").strip()
    if not key:
        raise XAIError("no_key")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": api_ledger._UA}


def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.3,
    max_tokens: int = 340,
    timeout: int = 60,
) -> str:
    why = _blocked()
    if why:
        raise XAIError(why)
    chosen = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    payload = {
        "model": chosen,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    raw = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(CHAT_URL, data=raw, headers=_headers(), method="POST")
    api_ledger.note_spend()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
    except urllib.error.HTTPError as exc:
        err = exc.read()[:400].decode("utf-8", "replace")
        if exc.code in (401, 403, 429):
            mark_grok_down(f"HTTP {exc.code}")
        raise XAIError(f"HTTP {exc.code} {err[:180]}") from exc
    except Exception as exc:
        raise XAIError(str(exc)[:200]) from exc
    try:
        data = json.loads(body.decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise XAIError("unexpected_response") from exc
    mark_grok_up()
    usage = data.get("usage") if isinstance(data, dict) else None
    if isinstance(usage, dict):
        details = usage.get("prompt_tokens_details")
        cached = int(details.get("cached_tokens") or 0) if isinstance(details, dict) else 0
        api_ledger.record_usage(
            "xai",
            model=chosen,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            cached_tokens=cached,
            surface="xai.chat",
        )
    return text


def try_chat(messages: list[dict[str, str]], **kwargs) -> str | None:
    if _blocked():
        return None
    try:
        return chat(messages, **kwargs)
    except XAIError:
        return None


def tts(text: str, out_path: Path, *, voice: str = "ara", language: str = "en", timeout: int = 90) -> Path:
    why = _blocked()
    if why:
        raise XAIError(why)
    payload = {
        "text": text or "",
        "voice_id": voice,
        "language": language,
        "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 128000},
    }
    raw = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(TTS_URL, data=raw, headers=_headers(), method="POST")
    api_ledger.note_spend()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            audio = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 429):
            mark_grok_down(f"HTTP {exc.code}")
        raise XAIError(f"HTTP {exc.code}") from exc
    except Exception as exc:
        raise XAIError(str(exc)[:200]) from exc
    dest = Path(out_path)
    if dest.suffix.lower() == ".wav":
        raise XAIError("wav_not_written_without_signoff")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(audio)
    api_ledger.record_usage(
        "xai",
        model="grok-voice-tts",
        usd=api_ledger.REPORT_AUDIO_CLIP_USD,
        surface="xai.tts",
        note="report audio clip metered after bytes landed",
    )
    return dest
