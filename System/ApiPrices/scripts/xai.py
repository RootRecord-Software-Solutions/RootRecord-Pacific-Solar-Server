# ==============================================================================
# FILE: System/ApiPrices/scripts/xai.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""xAI chat and TTS. Package ApiPrices.

Refuses unless RR_API_SPEND=1 and may_spend('xai') is true.
Does not call Kokoro, speakers, or report writers.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any

import api_ledger  # info: import api_ledger
import envload  # info: import envload

CHAT_URL = "https://api.x.ai/v1/chat/completions"  # info: set CHAT_URL
TTS_URL = "https://api.x.ai/v1/tts"  # info: set TTS_URL
DEFAULT_MODEL = api_ledger.DEFAULT_XAI_MODEL  # info: set DEFAULT_MODEL
GROK_DOWN_HOURS = 6  # info: set GROK_DOWN_HOURS


# ====================================================
# SECTION: class XAIError
# What it does: XAIError.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class XAIError(RuntimeError):  # info: class XAIError
    pass  # info: pass


# ====================================================
# SECTION: function _status_path
# What it does:  status path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _status_path() -> Path:  # info: def _status_path
    return api_ledger.data_dir() / "grok-status.json"  # info: return api_ledger . data_dir ( ) / "grok-status.json"


# ====================================================
# SECTION: function _load_status
# What it does:  load status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_status() -> dict[str, Any]:  # info: def _load_status
    path = _status_path()  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {"ok": True}  # info: return { "ok" : True }
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {"ok": True}  # info: return { "ok" : True }
    return data if isinstance(data, dict) else {"ok": True}  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function _save_status
# What it does:  save status.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _save_status(data: dict[str, Any]) -> None:  # info: def _save_status
    path = _status_path()  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps (


# ====================================================
# SECTION: function grok_is_down
# What it does: grok is down.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def grok_is_down() -> bool:  # info: def grok_is_down
    st = _load_status()  # info: set st
    if st.get("halt"):  # info: if st . get ( "halt" ) :
        return True  # info: return True
    if st.get("ok", True):  # info: if st . get ( "ok" , True
        return False  # info: return False
    until = st.get("until")  # info: set until
    if not until:  # info: if not until :
        return True  # info: return True
    try:  # info: try :
        return datetime.now(timezone.utc) < datetime.fromisoformat(str(until))  # info: return datetime . now ( timezone . utc
    except ValueError:  # info: except ValueError :
        return True  # info: return True


# ====================================================
# SECTION: function mark_grok_down
# What it does: mark grok down.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark_grok_down(reason: str) -> None:  # info: def mark_grok_down
    until = datetime.now(timezone.utc) + timedelta(hours=GROK_DOWN_HOURS)  # info: set until
    _save_status(  # info: call _save_status
        {  # info: {
            "ok": False,  # info: "ok" : False ,
            "reason": reason[:300],  # info: "reason" : reason [ : 300 ] ,
            "at": datetime.now(timezone.utc).isoformat(),  # info: "at" : datetime . now ( timezone .
            "until": until.isoformat(),  # info: "until" : until . isoformat ( ) ,
        }  # info: }
    )  # info: )


# ====================================================
# SECTION: function mark_grok_up
# What it does: mark grok up.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark_grok_up() -> None:  # info: def mark_grok_up
    st = _load_status()  # info: set st
    if st.get("halt"):  # info: if st . get ( "halt" ) :
        return  # info: return
    _save_status({"ok": True, "at": datetime.now(timezone.utc).isoformat()})  # info: call _save_status


# ====================================================
# SECTION: function _blocked
# What it does:  blocked.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _blocked() -> str | None:  # info: def _blocked
    if not api_ledger.spend_gate_open():  # info: if not api_ledger . spend_gate_open ( ) :
        return "rr_api_spend_off"  # info: return "rr_api_spend_off"
    if grok_is_down():  # info: if grok_is_down ( ) :
        return "grok_down"  # info: return "grok_down"
    ok, why = api_ledger.may_spend("xai")  # info: ok , why = api_ledger . may_spend (
    if not ok:  # info: if not ok :
        return why  # info: return why
    if not envload.key_set("XAI_API_KEY"):  # info: if not envload . key_set ( "XAI_API_KEY" )
        return "no_key"  # info: return "no_key"
    return None  # info: return None


# ====================================================
# SECTION: function _headers
# What it does:  headers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _headers() -> dict[str, str]:  # info: def _headers
    envload.load_env()  # info: envload . load_env ( )
    key = (os.environ.get("XAI_API_KEY") or "").strip()  # info: set key
    if not key:  # info: if not key :
        raise XAIError("no_key")  # info: raise XAIError ( "no_key" )
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": api_ledger._UA}  # info: return { "Authorization" : f" Bearer { key


# ====================================================
# SECTION: function chat
# What it does: chat.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chat(  # info: def chat
    messages: list[dict[str, str]],  # info: set messages
    *,  # info: * ,
    model: str | None = None,  # info: set model
    temperature: float = 0.3,  # info: set temperature
    max_tokens: int = 340,  # info: set max_tokens
    timeout: int = 60,  # info: set timeout
) -> str:  # info: ) -> str :
    why = _blocked()  # info: set why
    if why:  # info: if why :
        raise XAIError(why)  # info: raise XAIError ( why )
    chosen = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL  # info: set chosen
    payload = {  # info: set payload
        "model": chosen,  # info: "model" : chosen ,
        "messages": messages,  # info: "messages" : messages ,
        "temperature": temperature,  # info: "temperature" : temperature ,
        "max_tokens": max_tokens,  # info: "max_tokens" : max_tokens ,
    }  # info: }
    raw = json.dumps(payload).encode("utf-8")  # info: set raw
    req = urllib.request.Request(CHAT_URL, data=raw, headers=_headers(), method="POST")  # info: set req
    api_ledger.note_spend()  # info: api_ledger . note_spend ( )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # info: with urllib . request . urlopen ( req
            body = resp.read()  # info: set body
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        err = exc.read()[:400].decode("utf-8", "replace")  # info: set err
        if exc.code in (401, 403, 429):  # info: if exc . code in ( 401 ,
            mark_grok_down(f"HTTP {exc.code}")  # info: call mark_grok_down
        raise XAIError(f"HTTP {exc.code} {err[:180]}") from exc  # info: raise XAIError ( f" HTTP { exc .
    except Exception as exc:  # info: except Exception as exc :
        raise XAIError(str(exc)[:200]) from exc  # info: raise XAIError ( str ( exc ) [
    try:  # info: try :
        data = json.loads(body.decode("utf-8"))  # info: set data
        text = data["choices"][0]["message"]["content"].strip()  # info: set text
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:  # info: except ( KeyError , IndexError , TypeError ,
        raise XAIError("unexpected_response") from exc  # info: raise XAIError ( "unexpected_response" ) from exc
    mark_grok_up()  # info: call mark_grok_up
    usage = data.get("usage") if isinstance(data, dict) else None  # info: set usage
    if isinstance(usage, dict):  # info: if isinstance ( usage , dict ) :
        details = usage.get("prompt_tokens_details")  # info: set details
        cached = int(details.get("cached_tokens") or 0) if isinstance(details, dict) else 0  # info: set cached
        api_ledger.record_usage(  # info: api_ledger . record_usage (
            "xai",  # info: "xai" ,
            model=chosen,  # info: set model
            input_tokens=int(usage.get("prompt_tokens") or 0),  # info: set input_tokens
            output_tokens=int(usage.get("completion_tokens") or 0),  # info: set output_tokens
            cached_tokens=cached,  # info: set cached_tokens
            surface="xai.chat",  # info: set surface
        )  # info: )
    return text  # info: return text


# ====================================================
# SECTION: function try_chat
# What it does: try chat.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def try_chat(messages: list[dict[str, str]], **kwargs) -> str | None:  # info: def try_chat
    if _blocked():  # info: if _blocked ( ) :
        return None  # info: return None
    try:  # info: try :
        return chat(messages, **kwargs)  # info: return chat ( messages , ** kwargs )
    except XAIError:  # info: except XAIError :
        return None  # info: return None


# ====================================================
# SECTION: function tts
# What it does: tts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tts(text: str, out_path: Path, *, voice: str = "ara", language: str = "en", timeout: int = 90) -> Path:  # info: def tts
    why = _blocked()  # info: set why
    if why:  # info: if why :
        raise XAIError(why)  # info: raise XAIError ( why )
    payload = {  # info: set payload
        "text": text or "",  # info: "text" : text or "" ,
        "voice_id": voice,  # info: "voice_id" : voice ,
        "language": language,  # info: "language" : language ,
        "output_format": {"codec": "mp3", "sample_rate": 44100, "bit_rate": 128000},  # info: "output_format" : { "codec" : "mp3" , "sample_rate"
    }  # info: }
    raw = json.dumps(payload).encode("utf-8")  # info: set raw
    req = urllib.request.Request(TTS_URL, data=raw, headers=_headers(), method="POST")  # info: set req
    api_ledger.note_spend()  # info: api_ledger . note_spend ( )
    try:  # info: try :
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # info: with urllib . request . urlopen ( req
            audio = resp.read()  # info: set audio
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        if exc.code in (401, 403, 429):  # info: if exc . code in ( 401 ,
            mark_grok_down(f"HTTP {exc.code}")  # info: call mark_grok_down
        raise XAIError(f"HTTP {exc.code}") from exc  # info: raise XAIError ( f" HTTP { exc .
    except Exception as exc:  # info: except Exception as exc :
        raise XAIError(str(exc)[:200]) from exc  # info: raise XAIError ( str ( exc ) [
    dest = Path(out_path)  # info: set dest
    if dest.suffix.lower() == ".wav":  # info: if dest . suffix . lower ( )
        raise XAIError("wav_not_written_without_signoff")  # info: raise XAIError ( "wav_not_written_without_signoff" )
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir ( parents =
    dest.write_bytes(audio)  # info: dest . write_bytes ( audio )
    api_ledger.record_usage(  # info: api_ledger . record_usage (
        "xai",  # info: "xai" ,
        model="grok-voice-tts",  # info: set model
        usd=api_ledger.REPORT_AUDIO_CLIP_USD,  # info: set usd
        surface="xai.tts",  # info: set surface
        note="report audio clip metered after bytes landed",  # info: set note
    )  # info: )
    return dest  # info: return dest
