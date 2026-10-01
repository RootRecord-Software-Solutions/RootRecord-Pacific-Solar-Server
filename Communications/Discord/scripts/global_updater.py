# ==============================================================================
# FILE: Communications/Discord/scripts/global_updater.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Professional Discord replies for the Root Record Global Updater.

Off unless RR_GLOBAL_UPDATER=1. One voice. No Ava, Bruce, or Carly review.
Identity is loaded from Library Agent Context. Transport stays in lib/api.py.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent  # info: set HERE
DISCORD = HERE.parent  # info: set DISCORD
PACIFIC = DISCORD.parents[1]  # info: set PACIFIC
sys.path.insert(0, str(DISCORD))  # info: sys . path . insert
RUN_INFER = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"  # info: set RUN_INFER
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
HOST_LAST = DB / "System" / "last" / "host-last.json"  # info: set HOST_LAST
LOG_PATH = DB / "Logs" / "Communications" / "Discord" / "poll.log"  # info: set LOG_PATH
SEEN_PATH = DB / "Communications" / "Discord" / "updater-seen.json"  # info: set SEEN_PATH
GUILD_FILE = DISCORD / "config" / "guilds.json"  # info: set GUILD_FILE
APP_FILE = DISCORD / "config" / "global-updater.json"  # info: set APP_FILE
FLAG = "RR_GLOBAL_UPDATER"  # info: set FLAG

from lib.observations import load_host, render_observation  # noqa: E402
from lib.updater import VOICE, build_prompt, enforce, notes_for, system_text  # noqa: E402


# ====================================================
# SECTION: function enabled
# What it does: True only when RR_GLOBAL_UPDATER=1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def enabled() -> bool:  # info: def enabled
    return os.environ.get(FLAG, "0").strip() == "1"  # info: return os . environ . get


# ====================================================
# SECTION: function stage_log
# What it does: Append one operational label. Callers must not pass message text or secrets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stage_log(line: str, path: Path | None = None) -> None:  # info: def stage_log
    dest = path or LOG_PATH  # info: set dest
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir
    stamp = datetime.now(HST).isoformat(timespec="seconds")  # info: set stamp
    with dest.open("a", encoding="utf-8") as handle:  # info: with dest . open
        handle.write(f"{stamp} {line}\n")  # info: handle . write


# ====================================================
# SECTION: function load_scope
# What it does: Read the guild allowlist and the application label. Does not read a token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_scope(guild_file: Path | None = None, app_file: Path | None = None) -> dict:  # info: def load_scope
    guilds = json.loads((guild_file or GUILD_FILE).read_text(encoding="utf-8"))  # info: set guilds
    app = json.loads((app_file or APP_FILE).read_text(encoding="utf-8"))  # info: set app
    if not isinstance(guilds, list):  # info: if not isinstance ( guilds , list )
        raise ValueError("guilds must be a JSON list")  # info: raise ValueError
    if not isinstance(app, dict):  # info: if not isinstance ( app , dict )
        raise ValueError("global-updater config must be an object")  # info: raise ValueError
    voice = str(app.get("voice") or VOICE)  # info: set voice
    if voice != VOICE:  # info: if voice != VOICE
        raise RuntimeError("global updater voice must stay global-updater")  # info: raise RuntimeError
    names = app.get("mention_names") or []  # info: set names
    if not isinstance(names, list) or not names:  # info: if not isinstance ( names , list ) or not names
        raise ValueError("mention_names must be a non-empty list")  # info: raise ValueError
    return {  # info: return
        "guild_ids": [str(item).strip() for item in guilds if str(item).strip()],  # info: guild_ids
        "mention_names": [str(item).strip() for item in names if str(item).strip()],  # info: mention_names
        "application_name": str(app.get("application_name") or ""),  # info: application_name
        "application_id": str(app.get("application_id") or ""),  # info: application_id
        "voice": VOICE,  # info: voice
    }  # info: }


# ====================================================
# SECTION: function invokes
# What it does: True for a non-bot message that names the updater inside an allowed guild.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def invokes(message: dict, scope: dict) -> bool:  # info: def invokes
    author = message.get("author") or {}  # info: set author
    if author.get("bot"):  # info: if author . get ( "bot" )
        return False  # info: return False
    allowed = {str(item) for item in (scope.get("guild_ids") or []) if str(item)}  # info: set allowed
    if not allowed:  # info: if not allowed
        return False  # info: return False
    if str(message.get("guild_id") or "") not in allowed:  # info: if str ( message . get ( "guild_id" ) or "" ) not in allowed
        return False  # info: return False
    names = [name.lower() for name in (scope.get("mention_names") or []) if name]  # info: set names
    content = str(message.get("content") or "")  # info: set content
    low = content.lower()  # info: set low
    if any(name in low for name in names):  # info: if any ( name in low for name in names )
        return True  # info: return True
    for mention in message.get("mentions") or []:  # info: for mention in message . get ( "mentions" ) or [ ]
        if not isinstance(mention, dict):  # info: if not isinstance ( mention , dict )
            continue  # info: continue
        label = f"{mention.get('username') or ''} {mention.get('global_name') or ''}".lower()  # info: set label
        if any(name in label for name in names):  # info: if any
            return True  # info: return True
    return False  # info: return False


# ====================================================
# SECTION: function default_infer
# What it does: One Global Updater turn through run-infer.sh. Does not call Ava, Bruce, or Carly.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def default_infer(voice: str, prompt: str) -> str:  # info: def default_infer
    if voice != VOICE:  # info: if voice != VOICE
        raise RuntimeError("global updater voice only")  # info: raise RuntimeError
    if not RUN_INFER.is_file():  # info: if not RUN_INFER . is_file ( )
        raise RuntimeError("run-infer.sh is missing")  # info: raise RuntimeError
    env = os.environ.copy()  # info: set env
    env.pop("DESK_LIVE_FILE", None)  # info: env . pop
    env["RR_PERSONA_SYSTEM"] = system_text()  # info: env [ "RR_PERSONA_SYSTEM" ]
    env["RR_NPU_ONLY"] = "1"  # info: env [ "RR_NPU_ONLY" ]
    env["RR_NPU_PERSONA"] = "1"  # info: env [ "RR_NPU_PERSONA" ]
    env["FLM_MODEL"] = "llama3.2:3b"  # info: env [ "FLM_MODEL" ]
    env["RR_CALLER"] = "discord-global-updater"  # info: env [ "RR_CALLER" ]
    env["RR_SPEC_TEMP"] = "0.2"  # info: env [ "RR_SPEC_TEMP" ]
    env["RR_SPEC_MAXTOK"] = "320"  # info: env [ "RR_SPEC_MAXTOK" ]
    proc = subprocess.run(  # info: set proc
        [str(RUN_INFER), voice, prompt],  # info: argv
        capture_output=True,  # info: capture_output = True
        text=True,  # info: text = True
        timeout=600,  # info: timeout = 600
        env=env,  # info: env = env
    )  # info: )
    out = (proc.stdout or "").strip()  # info: set out
    if proc.returncode != 0 and not out:  # info: if proc . returncode != 0 and not out
        raise RuntimeError(f"infer exit {proc.returncode}")  # info: raise RuntimeError
    if not out:  # info: if not out
        raise RuntimeError("infer empty")  # info: raise RuntimeError
    return out  # info: return out


# ====================================================
# SECTION: function load_seen
# What it does: Read handled Discord message ids. The file stores ids only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_seen(path: Path) -> dict:  # info: def load_seen
    if not path.is_file():  # info: if not path . is_file ( )
        return {}  # info: return { }
    try:  # info: try
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance


# ====================================================
# SECTION: function save_seen
# What it does: Write handled message ids. Does not store message text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_seen(path: Path, data: dict) -> None:  # info: def save_seen
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace


# ====================================================
# SECTION: function apply
# What it does: Answer Global Updater mentions in one voice. Skip unless the gate is on.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply(  # info: def apply
    channel_id: str,  # info: channel_id : str
    messages: list,  # info: messages : list
    *,  # info: keyword only
    enabled: bool,  # info: enabled : bool
    post,  # info: post
    log=None,  # info: log = None
    infer=None,  # info: infer = None
    seen_path: Path | None = None,  # info: seen_path
    scope: dict | None = None,  # info: scope
    host_path: Path | None = None,  # info: host_path
    now: datetime | None = None,  # info: now
) -> dict:  # info: return dict
    empty = {"handled": 0, "posted": 0, "ids": [], "public_texts": []}  # info: set empty
    if not enabled:  # info: if not enabled
        return empty  # info: return empty
    write = log or stage_log  # info: set write
    speak = infer or default_infer  # info: set speak
    rules = scope or load_scope()  # info: set rules
    seen_file = seen_path or SEEN_PATH  # info: set seen_file
    seen = load_seen(seen_file)  # info: set seen
    known = {str(item) for item in (seen.get(channel_id) or []) if str(item)}  # info: set known
    handled = 0  # info: set handled
    posted = 0  # info: set posted
    ids: list[str] = []  # info: set ids
    public_texts: list[str] = []  # info: set public_texts
    sample_path = host_path or HOST_LAST  # info: set sample_path
    for message in reversed(messages or []):  # info: for message in reversed
        if not isinstance(message, dict) or not invokes(message, rules):  # info: if not isinstance or not invokes
            continue  # info: continue
        mid = str(message.get("id") or "")  # info: set mid
        text = str(message.get("content") or "").strip()  # info: set text
        if not mid or mid in known or not text:  # info: if not mid or mid in known or not text
            continue  # info: continue
        write("request received")  # info: call write
        write("agent selected global-updater")  # info: call write
        obs = load_host(sample_path, now=now)  # info: set obs
        write(f"data source consulted host-last:{obs.status}")  # info: call write
        notes = notes_for(text)  # info: set notes
        if notes:  # info: if notes
            write("data source consulted library-context")  # info: call write
        try:  # info: try
            raw = speak(VOICE, build_prompt(text, notes, render_observation(obs)))  # info: set raw
            public = enforce(raw, obs, notes, text)  # info: set public
        except Exception as exc:  # info: except Exception as exc
            write(f"response withheld {type(exc).__name__}")  # info: call write
            continue  # info: continue
        handled += 1  # info: set handled
        if not public:  # info: if not public
            write("response withheld")  # info: call write
            continue  # info: continue
        public_texts.append(public)  # info: public_texts . append
        write(f"response generated chars={len(public)}")  # info: call write
        try:  # info: try
            sent = post(channel_id, public)  # info: set sent
        except Exception as exc:  # info: except Exception as exc
            write(f"response delivered unavailable {type(exc).__name__}")  # info: call write
            continue  # info: continue
        known.add(mid)  # info: known . add
        ids.append(mid)  # info: ids . append
        if sent:  # info: if sent
            posted += 1  # info: set posted
            write("response delivered")  # info: call write
        else:  # info: else
            write("response delivered skipped")  # info: call write
    seen[channel_id] = list(known)[-50:]  # info: seen [ channel_id ]
    if handled:  # info: if handled
        save_seen(seen_file, seen)  # info: call save_seen
    return {"handled": handled, "posted": posted, "ids": ids, "public_texts": public_texts}  # info: return
