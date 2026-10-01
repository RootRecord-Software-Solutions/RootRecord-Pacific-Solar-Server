# ==============================================================================
# FILE: Media/Voice/scripts/voice_deliver.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Post one voice report to Telegram as a voice note plus a transcript reply.

Stays off unless RR_VOICE_DELIVER=1. Default chat is the sandbox in relay.conf.
RR_TELEGRAM_DEST=council selects the live council chat. Does not poll getUpdates.
Does not print tokens. Skips a report whose spoken text has not changed.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import urllib.error  # info: import urllib . error
import urllib.request  # info: import urllib . request
import uuid  # info: import uuid
from pathlib import Path  # info: from pathlib import Path

import speakers  # info: import speakers

PACIFIC = Path(__file__).resolve().parents[3]  # info: set PACIFIC
RELAY = PACIFIC / "Communications" / "telegram" / "config" / "relay.conf"  # info: set RELAY
VOICES = PACIFIC / "Communications" / "telegram" / "config" / "voices.conf"  # info: set VOICES
DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DB
STATE = DB / "Communications" / "VoiceDeliver" / "sent.json"  # info: set STATE
TOKEN_ENV = {"ava": "TELEGRAM_AVA_TOKEN", "bruce": "TELEGRAM_BRUCE_TOKEN", "carly": "TELEGRAM_CARLY_TOKEN"}  # info: set TOKEN_ENV
TITLES = {  # info: set TITLES
    "nws_weather": "NWS Hawaiʻi",  # info: "nws_weather" : "NWS Hawaiʻi" ,
    "kilauea_report": "Kīlauea",  # info: "kilauea_report" : "Kīlauea" ,
    "security_desk": "Security",  # info: "security_desk" : "Security" ,
    "bandwidth_desk": "Bandwidth",  # info: "bandwidth_desk" : "Bandwidth" ,
    "energy_report": "Energy desk — Solar Panels",  # info: "energy_report" : "Energy desk — Solar Panels" ,
    "remaining_tasks": "Remaining tasks",  # info: "remaining_tasks" : "Remaining tasks" ,
    "system_perf": "System performance",  # info: "system_perf" : "System performance" ,
    "solar_desk": "Hourly solar",  # info: "solar_desk" : "Hourly solar" ,
    "earthquake_report": "Earthquake",  # info: "earthquake_report" : "Earthquake" ,
    "hurricane_desk": "Hurricane desk",  # info: "hurricane_desk" : "Hurricane desk" ,
    "hourly_chime": "Hourly chime",  # info: "hourly_chime" : "Hourly chime" ,
    "morning_report": "Morning report",  # info: "morning_report" : "Morning report" ,
    "midday_report": "Midday report",  # info: "midday_report" : "Midday report" ,
    "late_report": "Late report",  # info: "late_report" : "Late report" ,
    "official_weather": "Official weather",  # info: "official_weather" : "Official weather" ,
    "boot_brief": "Boot brief",  # info: "boot_brief" : "Boot brief" ,
}  # info: }
NOTES = "Reply to this with notes if the report should be better."  # info: set NOTES

# ====================================================
# SECTION: function deliver_enabled
# What it does: True only when RR_VOICE_DELIVER=1. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def deliver_enabled() -> bool:  # info: def deliver_enabled
    return os.environ.get("RR_VOICE_DELIVER", "0").strip() == "1"  # info: return os . environ . get ( "RR_VOICE_DELIVER"

# ====================================================
# SECTION: function load_kv
# What it does: Read key=value lines. Skips comments. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_kv(path: Path) -> dict:  # info: def load_kv
    out = {}  # info: set out
    if not path.is_file():  # info: if not path . is_file
        return out  # info: return out
    for line in path.read_text(encoding="utf-8").splitlines():  # info: for line in path . read_text
        line = line.strip()  # info: set line
        if not line or line.startswith("#") or "=" not in line:  # info: if not line or line . startswith
            continue  # info: continue
        key, _, val = line.partition("=")  # info: key , _ , val = line . partition
        out[key.strip()] = val.strip()  # info: out [ key . strip ( ) ] = val . strip
    return out  # info: return out

# ====================================================
# SECTION: function load_secrets
# What it does: Load token env names from the relay secret files. Does not print them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_secrets(cfg: dict) -> None:  # info: def load_secrets
    for key in ("SECRETS_1", "SECRETS_2"):  # info: for key in ( "SECRETS_1" , "SECRETS_2" )
        path = Path((cfg.get(key) or "").strip())  # info: set path
        if not path.is_file():  # info: if not path . is_file
            continue  # info: continue
        for line in path.read_text(encoding="utf-8").splitlines():  # info: for line in path . read_text
            line = line.strip()  # info: set line
            if not line or line.startswith("#") or "=" not in line:  # info: if not line or line . startswith
                continue  # info: continue
            name, _, val = line.partition("=")  # info: name , _ , val = line . partition
            name, val = name.strip(), val.strip().strip("'").strip('"')  # info: name , val = name . strip ( ) , val . strip
            if name in TOKEN_ENV.values() and name not in os.environ:  # info: if name in TOKEN_ENV . values ( ) and name not in os . environ
                os.environ[name] = val  # info: os . environ [ name ] = val

# ====================================================
# SECTION: function chat_id
# What it does: Sandbox chat, or the live council when RR_TELEGRAM_DEST=council. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chat_id(cfg: dict) -> str:  # info: def chat_id
    if os.environ.get("RR_TELEGRAM_DEST", "sandbox").strip().lower() == "council":  # info: if os . environ . get ( "RR_TELEGRAM_DEST"
        return (cfg.get("COUNCIL_CHAT_ID") or "").strip()  # info: return ( cfg . get ( "COUNCIL_CHAT_ID" ) or "" ) . strip
    return (cfg.get("SANDBOX_CHAT_ID") or "").strip()  # info: return ( cfg . get ( "SANDBOX_CHAT_ID" ) or "" ) . strip

# ====================================================
# SECTION: function persona
# What it does: Map a report kind to ava, bruce, or carly. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona(kind: str) -> str:  # info: def persona
    return speakers.KIND_AGENT.get(kind) or "ava"  # info: return speakers . KIND_AGENT . get ( kind ) or "ava"

# ====================================================
# SECTION: function to_ogg
# What it does: Convert a wav to OGG Opus beside the wav Archive. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def to_ogg(wav: Path) -> Path:  # info: def to_ogg
    arch = wav.parent / "Archive"  # info: set arch
    arch.mkdir(parents=True, exist_ok=True)  # info: arch . mkdir
    dest = arch / f"{wav.stem}.ogg"  # info: set dest
    subprocess.run(  # info: call subprocess . run
        ["ffmpeg", "-y", "-i", str(wav), "-c:a", "libopus", "-b:a", "32k", "-vn", str(dest)],  # info: [ "ffmpeg" , "-y" , "-i" , str ( wav )
        check=True,  # info: check = True
        capture_output=True,  # info: capture_output = True
        timeout=60,  # info: timeout = 60
    )  # info: )
    return dest  # info: return dest

# ====================================================
# SECTION: function form_body
# What it does: Build one multipart body. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def form_body(fields: dict, file_field: str, filename: str, data: bytes) -> tuple[bytes, str]:  # info: def form_body
    boundary = "----RootRecordVoice" + uuid.uuid4().hex  # info: set boundary
    parts = []  # info: set parts
    for key, val in fields.items():  # info: for key , val in fields . items
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{val}\r\n".encode())  # info: parts . append
    parts.append(  # info: parts . append
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\nContent-Type: audio/ogg\r\n\r\n".encode()  # info: f" -- { boundary }
        + data  # info: + data
        + b"\r\n"  # info: + b"\r\n"
    )  # info: )
    parts.append(f"--{boundary}--\r\n".encode())  # info: parts . append
    return b"".join(parts), boundary  # info: return b"" . join ( parts ) , boundary

# ====================================================
# SECTION: function post
# What it does: POST one Telegram method. Never includes the token in the error text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def post(token: str, method: str, body: bytes, content_type: str) -> dict:  # info: def post
    req = urllib.request.Request(  # info: set req
        f"https://api.telegram.org/bot{token}/{method}",  # info: f" https://api.telegram.org/bot { token } / { method } "
        data=body,  # info: data = body
        headers={"Content-Type": content_type},  # info: headers = { "Content-Type" : content_type }
        method="POST",  # info: method = "POST"
    )  # info: )
    try:  # info: try
        with urllib.request.urlopen(req, timeout=60) as response:  # info: with urllib . request . urlopen
            payload = json.load(response)  # info: set payload
    except urllib.error.HTTPError as exc:  # info: except urllib . error . HTTPError as exc
        return {"ok": False, "detail": f"http {exc.code}"}  # info: return { "ok" : False , "detail" : f" http { exc . code } " }
    except (urllib.error.URLError, TimeoutError, OSError):  # info: except
        return {"ok": False, "detail": "telegram unreachable"}  # info: return { "ok" : False , "detail" : "telegram unreachable" }
    if not payload.get("ok"):  # info: if not payload . get ( "ok" )
        return {"ok": False, "detail": "telegram refused"}  # info: return { "ok" : False , "detail" : "telegram refused" }
    return payload  # info: return payload

# ====================================================
# SECTION: function remember
# What it does: Record the spoken-text hash for one report. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def remember(report: str, digest: str, message_id: int) -> None:  # info: def remember
    STATE.parent.mkdir(parents=True, exist_ok=True)  # info: STATE . parent . mkdir
    try:  # info: try
        state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {}  # info: set state
    except (OSError, ValueError):  # info: except
        state = {}  # info: set state
    if not isinstance(state, dict):  # info: if not isinstance ( state , dict )
        state = {}  # info: set state
    state[report] = {"sha256": digest, "message_id": message_id}  # info: state [ report ] = { "sha256" : digest , "message_id" : message_id }
    tmp = STATE.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, STATE)  # info: os . replace

# ====================================================
# SECTION: function deliver
# What it does: Send the voice note and the transcript reply. Skips when the gate is off or the words are unchanged.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def deliver(report: str, wav: str | Path, spoken: str, kind: str) -> dict:  # info: def deliver
    if not deliver_enabled():  # info: if not deliver_enabled
        return {"ok": True, "sent": False, "detail": "deliver gate off"}  # info: return { "ok" : True , "sent" : False , "detail" : "deliver gate off" }
    text = " ".join(spoken.split())  # info: set text
    wav_path = Path(wav)  # info: set wav_path
    if not text or not wav_path.is_file():  # info: if not text or not wav_path . is_file
        return {"ok": False, "sent": False, "detail": "missing wav or spoken text"}  # info: return { "ok" : False , "sent" : False , "detail" : "missing wav or spoken text" }
    digest = hashlib.sha256(text.encode()).hexdigest()  # info: set digest
    try:  # info: try
        prior = json.loads(STATE.read_text(encoding="utf-8")) if STATE.is_file() else {}  # info: set prior
    except (OSError, ValueError):  # info: except
        prior = {}  # info: set prior
    if isinstance(prior, dict) and (prior.get(report) or {}).get("sha256") == digest:  # info: if isinstance ( prior , dict ) and
        return {"ok": True, "sent": False, "detail": "unchanged"}  # info: return { "ok" : True , "sent" : False , "detail" : "unchanged" }
    cfg = load_kv(RELAY)  # info: set cfg
    load_secrets(cfg)  # info: call load_secrets
    who = persona(kind)  # info: set who
    token = (os.environ.get(TOKEN_ENV[who]) or "").strip()  # info: set token
    chat = chat_id(cfg)  # info: set chat
    if not token or not chat:  # info: if not token or not chat
        return {"ok": False, "sent": False, "detail": "missing token or chat"}  # info: return { "ok" : False , "sent" : False , "detail" : "missing token or chat" }
    try:  # info: try
        ogg = to_ogg(wav_path)  # info: set ogg
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):  # info: except
        return {"ok": False, "sent": False, "detail": "ogg convert failed"}  # info: return { "ok" : False , "sent" : False , "detail" : "ogg convert failed" }
    title = TITLES.get(report, report.replace("_", " "))  # info: set title
    body, boundary = form_body(  # info: body , boundary = form_body
        {"chat_id": chat, "caption": f"{title}\n{NOTES}"[:1024]},  # info: { "chat_id" : chat , "caption" : f" { title } \n { NOTES } " [ : 1024 ] }
        "voice",  # info: "voice"
        f"{report}.ogg",  # info: f" { report } .ogg "
        ogg.read_bytes(),  # info: ogg . read_bytes ( )
    )  # info: )
    voice = post(token, "sendVoice", body, f"multipart/form-data; boundary={boundary}")  # info: set voice
    if not voice.get("ok"):  # info: if not voice . get ( "ok" )
        return {"ok": False, "sent": False, "detail": voice.get("detail") or "sendVoice failed", "persona": who}  # info: return { "ok" : False , "sent" : False
    message_id = ((voice.get("result") or {}).get("message_id"))  # info: set message_id
    transcript = json.dumps({"chat_id": chat, "text": f"{title} — transcript\n\n{text}"[:3900], "reply_to_message_id": message_id, "disable_web_page_preview": True}).encode()  # info: set transcript
    note = post(token, "sendMessage", transcript, "application/json")  # info: set note
    if message_id:  # info: if message_id
        remember(report, digest, int(message_id))  # info: call remember
    return {"ok": bool(note.get("ok")), "sent": True, "persona": who, "chat": chat, "message_id": message_id, "transcript": bool(note.get("ok"))}  # info: return { "ok" : bool ( note . get ( "ok" ) ) , "sent" : True
