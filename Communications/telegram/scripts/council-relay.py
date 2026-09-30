# ==============================================================================
# FILE: Communications/telegram/scripts/council-relay.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Council relay: one getUpdates; single voice default; A>B>C>A on triggers.
Posts only clean replies (never DESK_LIVE / instruction leaks). Prefer FLM/NPU via run-infer.sh."""
from __future__ import annotations  # info: from __future__ import annotations
import json, os, re, subprocess, sys, time, urllib.error, urllib.request  # info: import json , os , re , subprocess
from pathlib import Path  # info: from pathlib import Path
from datetime import datetime  # info: from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
CONF = ROOT / "config" / "relay.conf"  # info: set CONF
VOICES = ROOT / "config" / "voices.conf"  # info: set VOICES
PIPELINE_ORDER = ("ava", "bruce", "carly", "ava")  # info: set PIPELINE_ORDER
SILENCE_RE = re.compile(  # info: set SILENCE_RE
    r"do not say anything|don'?t say anything|say nothing|stay silent|no replies?|nowhere near ready",  # info: r"do not say anything|don'?t say anything|say nothing|stay silent|no replies?|nowhere near ready" ,
    re.I,  # info: re . I ,
)  # info: )
LEAK_RE = re.compile(r"DESK_LIVE:|HARD RULES FOR THIS TURN|Do NOT state watts|standing envelopes|\[desk:", re.I)  # info: set LEAK_RE
GROUP_HELLO_RE = re.compile(r"^(hi|hey|hello|yo)( guys| all| everyone| team)?[.!?]*$", re.I)  # info: set GROUP_HELLO_RE

# Replies are OPT-IN (Alexander 2026-09-29): RR_RELAY_REPLIES=1 enables infer+post.
# Default 0 = quiet: login + getUpdates polling only, messages consumed, nothing posted.
# ====================================================
# SECTION: function replies_enabled
# What it does: replies enabled.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def replies_enabled() -> bool:  # info: def replies_enabled
    return os.environ.get("RR_RELAY_REPLIES", "0").strip() == "1"  # info: return os . environ . get ( "RR_RELAY_REPLIES"

# ====================================================
# SECTION: function replies_for_chat
# What it does: Live council stays quiet unless RR_RELAY_REPLIES=1. The sandbox chat answers when SANDBOX_REPLIES=1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def replies_for_chat(cfg, chat: str) -> bool:  # info: def replies_for_chat
    sandbox = (cfg.get("SANDBOX_CHAT_ID") or "").strip()  # info: set sandbox
    if sandbox and str(chat) == sandbox and (cfg.get("SANDBOX_REPLIES") or "0").strip() == "1":  # info: if sandbox and str ( chat ) == sandbox
        return True  # info: return True
    return replies_enabled()  # info: return replies_enabled ( )

# ====================================================
# SECTION: function load_kv
# What it does: load kv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_kv(path: Path) -> dict:  # info: def load_kv
    out = {}  # info: set out
    if not path.is_file():  # info: if not path . is_file ( ) :
        return out  # info: return out
    for line in path.read_text(encoding="utf-8").splitlines():  # info: for line in path . read_text ( encoding
        line = line.strip()  # info: set line
        if not line or line.startswith("#") or "=" not in line:
            continue  # info: continue
        k, _, v = line.partition("=")  # info: k , _ , v = line .
        out[k.strip()] = v.strip()  # info: out [ k . strip ( ) ]
    return out  # info: return out

# ====================================================
# SECTION: function load_secrets
# What it does: load secrets.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_secrets(paths):  # info: def load_secrets
    for p in paths:  # info: for p in paths :
        fp = Path(p)  # info: set fp
        if not fp.is_file():  # info: if not fp . is_file ( ) :
            continue  # info: continue
        for line in fp.read_text(encoding="utf-8").splitlines():  # info: for line in fp . read_text ( encoding
            line = line.strip()  # info: set line
            if not line or line.startswith("#") or "=" not in line:
                continue  # info: continue
            k, _, v = line.partition("=")  # info: k , _ , v = line .
            k, v = k.strip(), v.strip().strip("'").strip('"')  # info: k , v = k . strip (
            if k and k not in os.environ:  # info: if k and k not in os .
                os.environ[k] = v  # info: os . environ [ k ] = v

# ====================================================
# SECTION: function load_voices
# What it does: load voices.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_voices():  # info: def load_voices
    voices = {}  # info: set voices
    for line in VOICES.read_text(encoding="utf-8").splitlines():  # info: for line in VOICES . read_text ( encoding
        if not line.strip() or line.startswith("#"):
            continue  # info: continue
        parts = line.split("\t")  # info: set parts
        if len(parts) < 6:  # info: if len ( parts ) < 6 :
            continue  # info: continue
        vid, enabled, user, token_env, model, fallback = parts[:6]  # info: vid , enabled , user , token_env ,
        if enabled != "1":  # info: if enabled != "1" :
            continue  # info: continue
        voices[vid] = {"user": user, "token_env": token_env, "model": model, "fallback": fallback}  # info: voices [ vid ] = { "user" :
    return voices  # info: return voices

# ====================================================
# SECTION: function token_for
# What it does: token for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def token_for(voice):  # info: def token_for
    t = (os.environ.get(voice["token_env"]) or "").strip()  # info: set t
    if t:  # info: if t :
        return t  # info: return t
    if "AVA" in voice["token_env"]:  # info: if "AVA" in voice [ "token_env" ] :
        return (os.environ.get("AVA_TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()  # info: return ( os . environ . get (
    return ""  # info: return ""

# ====================================================
# SECTION: function api
# What it does: api.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def api(token, method, payload=None):  # info: def api
    url = f"https://api.telegram.org/bot{token}/{method}"  # info: set url
    data = None if payload is None else json.dumps(payload).encode()  # info: set data
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {}, method="POST" if data else "GET")  # info: set req
    with urllib.request.urlopen(req, timeout=60) as r:  # info: with urllib . request . urlopen ( req
        body = json.load(r)  # info: set body
    if not body.get("ok"):  # info: if not body . get ( "ok" )
        raise RuntimeError(f"{method} failed")  # info: raise RuntimeError ( f" { method } failed
    return body  # info: return body

# ====================================================
# SECTION: function group_hello
# What it does: True when the message is only a greeting to the group, such as hi guys.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def group_hello(text):  # info: def group_hello
    return bool(GROUP_HELLO_RE.match(text.strip()))  # info: return bool ( GROUP_HELLO_RE . match ( text . strip ( ) ) )

# ====================================================
# SECTION: function wants_pipeline
# What it does: wants pipeline.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wants_pipeline(text, triggers):  # info: def wants_pipeline
    t = text.lower()  # info: set t
    for trig in triggers:  # info: for trig in triggers :
        if trig and trig in t:  # info: if trig and trig in t :
            return True  # info: return True
    return bool(re.search(r"\ba\s*>\s*b\s*>\s*c\b", t))  # info: return bool ( re . search ( r"\ba\s*>\s*b\s*>\s*c\b"

# ====================================================
# SECTION: function mentioned_voice
# What it does: mentioned voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mentioned_voice(text, voices):  # info: def mentioned_voice
    t = text.lower()  # info: set t
    for vid, v in voices.items():  # info: for vid , v in voices . items
        user = (v.get("user") or "").lower()  # info: set user
        if user and f"@{user}" in t:  # info: if user and f" @ { user }
            return vid  # info: return vid
    hits = []  # info: set hits
    if re.search(r"\bava\b|@ava", t):  # info: if re . search ( r"\bava\b|@ava" , t
        hits.append("ava")  # info: hits . append ( "ava" )
    if re.search(r"\bbruce\b|@bruce", t):  # info: if re . search ( r"\bbruce\b|@bruce" , t
        hits.append("bruce")  # info: hits . append ( "bruce" )
    if re.search(r"\bcarly\b|@carly", t):  # info: if re . search ( r"\bcarly\b|@carly" , t
        hits.append("carly")  # info: hits . append ( "carly" )
    if len(hits) == 1:  # info: if len ( hits ) == 1 :
        return hits[0]  # info: return hits [ 0 ]
    return None  # info: return None

# ====================================================
# SECTION: function clean_reply
# What it does: clean reply.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_reply(text: str) -> str | None:  # info: def clean_reply
    if not text or not text.strip():  # info: if not text or not text . strip
        return None  # info: return None
    if LEAK_RE.search(text):  # info: if LEAK_RE . search ( text ) :
        # refuse to post instruction leaks
        return None  # info: return None
    # strip single-flight noise
    lines = [ln for ln in text.splitlines() if not ln.startswith("[ok]")]  # info: set lines
    out = "\n".join(lines).strip()  # info: set out
    return out or None  # info: return out or None

# ====================================================
# SECTION: function run_infer
# What it does: run infer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_infer(cfg, voice, prompt, prior=""):  # info: def run_infer
    run = cfg.get("RUN_INFER") or cfg.get("RUN_OLLAMA", "").replace("run-ollama.sh", "run-infer.sh")  # info: set run
    if not run or not Path(run).exists():  # info: if not run or not Path ( run
        run = str(ROOT.parent.parent.parent / "System" / "scripts" / "plumbing" / "run-infer.sh")  # info: set run
    full = prompt if not prior else f"Prior turns:\n{prior}\n\nYour turn as {voice}.\nUser:\n{prompt}"  # info: set full
    p = subprocess.run([run, voice, full], capture_output=True, text=True, timeout=600)  # info: set p
    out = (p.stdout or "").strip()  # info: set out
    # stderr may have [ok] FLM lines — ignore
    return clean_reply(out)  # info: return clean_reply ( out )

# ====================================================
# SECTION: function post_as
# What it does: Post one reply. allow=False keeps a chat quiet. Never prints the token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def post_as(voice_id, voices, chat_id, text, max_text, allow=None):  # info: def post_as
    if allow is None:  # info: if allow is None :
        allow = replies_enabled()  # info: set allow
    if not allow:  # info: if not allow :
        print(f"[quiet] replies off — not posting as {voice_id}")  # info: call print
        return False  # info: return False
    text = clean_reply(text)  # info: set text
    if not text:  # info: if not text :
        print(f"[skip] empty/leaky reply for {voice_id}")  # info: call print
        return False  # info: return False
    tok = token_for(voices[voice_id])  # info: set tok
    if not tok:  # info: if not tok :
        print(f"[fail] no token {voice_id}", file=sys.stderr)  # info: call print
        return False  # info: return False
    api(tok, "sendMessage", {"chat_id": chat_id, "text": text[:max_text], "disable_web_page_preview": True})  # info: call api
    print(f"[ok] posted as {voice_id}")  # info: call print
    return True  # info: return True

# Quiet-mode inbox (Alexander 2026-09-29, Library 08-ideas relay-quiet-mode-message-hold): while replies are
# OFF, each consumed message (metadata + text) is appended to a git-ignored JSONL so it can be answered later
# with relay-inbox-replay.py. Cut hourly into Archive/YYYY-MM-DD/. Local file only; never sends anything.
INBOX_DIR = Path(os.environ.get("RR_RELAY_INBOX_DIR", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Logs/Communications/Relay-Inbox"))  # info: set INBOX_DIR
INBOX_CURRENT = "relay-inbox_current.jsonl"  # info: set INBOX_CURRENT

# ====================================================
# SECTION: function persona_target
# What it does: persona target.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona_target(text, is_private, poll_voice, voices, triggers, default_voice):  # info: def persona_target
    if is_private:  # info: if is_private :
        return poll_voice  # info: return poll_voice
    if wants_pipeline(text, triggers):  # info: if wants_pipeline ( text , triggers ) :
        return "pipeline:" + ">".join(PIPELINE_ORDER)  # info: return "pipeline:" + ">" . join ( PIPELINE_ORDER
    return mentioned_voice(text, voices) or default_voice  # info: return mentioned_voice ( text , voices ) or

# ====================================================
# SECTION: function inbox_rotate
# What it does: Move relay-inbox_current.jsonl to Archive/YYYY-MM-DD/relay-inbox_YYYY-MM-DD_HH00.jsonl once its first record is from an earlier hour than now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def inbox_rotate(inbox_dir=None, now=None):  # info: def inbox_rotate
    """Move relay-inbox_current.jsonl to Archive/YYYY-MM-DD/relay-inbox_YYYY-MM-DD_HH00.jsonl once its first
    record is from an earlier hour than now."""
    inbox_dir = Path(inbox_dir or INBOX_DIR)  # info: set inbox_dir
    cur = inbox_dir / INBOX_CURRENT  # info: set cur
    if not cur.is_file() or cur.stat().st_size == 0:  # info: if not cur . is_file ( ) or
        return None  # info: return None
    now = now or datetime.now().astimezone()  # info: set now
    with cur.open(encoding="utf-8") as fh:  # info: with cur . open ( encoding = "utf-8"
        first = json.loads(fh.readline() or "{}")  # info: set first
    t0 = datetime.fromisoformat(first.get("received_ts") or now.isoformat())  # info: set t0
    if t0.strftime("%Y-%m-%d_%H") == now.strftime("%Y-%m-%d_%H"):  # info: if t0 . strftime ( "%Y-%m-%d_%H" ) ==
        return None  # info: return None
    day = inbox_dir / "Archive" / t0.strftime("%Y-%m-%d")  # info: set day
    day.mkdir(parents=True, exist_ok=True, mode=0o700)  # info: day . mkdir ( parents = True ,
    dest = day / f"relay-inbox_{t0.strftime('%Y-%m-%d_%H')}00.jsonl"  # info: set dest
    if dest.exists():  # info: if dest . exists ( ) :
        with dest.open("a", encoding="utf-8") as out:  # info: with dest . open ( "a" , encoding
            out.write(cur.read_text(encoding="utf-8"))  # info: out . write ( cur . read_text (
        cur.write_text("", encoding="utf-8")  # info: cur . write_text ( "" , encoding =
    else:  # info: else :
        os.replace(cur, dest)  # info: os . replace ( cur , dest )
    os.chmod(dest, 0o600)  # info: os . chmod ( dest , 0o600 )
    return dest  # info: return dest

# ====================================================
# SECTION: function inbox_hold
# What it does: Append one consumed quiet-mode message to relay-inbox_current.jsonl (0600). Returns the path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def inbox_hold(upd, msg, text, target, inbox_dir=None):  # info: def inbox_hold
    """Append one consumed quiet-mode message to relay-inbox_current.jsonl (0600). Returns the path."""  # info: """Append one consumed quiet-mode message to relay-inbox_current.jsonl (0600). Returns the path."""
    inbox_dir = Path(inbox_dir or INBOX_DIR)  # info: set inbox_dir
    inbox_dir.mkdir(parents=True, exist_ok=True, mode=0o700)  # info: inbox_dir . mkdir ( parents = True ,
    inbox_rotate(inbox_dir)  # info: call inbox_rotate
    chat, frm = msg.get("chat") or {}, msg.get("from") or {}  # info: chat , frm = msg . get (
    rec = {  # info: set rec
        "ts": datetime.fromtimestamp(int(msg.get("date") or time.time())).astimezone().isoformat(timespec="seconds"),  # info: "ts" : datetime . fromtimestamp ( int (
        "received_ts": datetime.now().astimezone().isoformat(timespec="seconds"),  # info: "received_ts" : datetime . now ( ) .
        "update_id": upd.get("update_id"),  # info: "update_id" : upd . get ( "update_id" )
        "chat_id": chat.get("id"),  # info: "chat_id" : chat . get ( "id" )
        "chat_type": chat.get("type"),  # info: "chat_type" : chat . get ( "type" )
        "from": {"id": frm.get("id"), "username": frm.get("username"), "name": " ".join(x for x in (frm.get("first_name"), frm.get("last_name")) if x)},  # info: "from" : { "id" : frm . get
        "persona_target": target,  # info: "persona_target" : target ,
        "message_id": msg.get("message_id"),  # info: "message_id" : msg . get ( "message_id" )
        "text": text,  # info: "text" : text ,
        "status": "held",  # info: "status" : "held" ,
    }  # info: }
    cur = inbox_dir / INBOX_CURRENT  # info: set cur
    with cur.open("a", encoding="utf-8") as fh:  # info: with cur . open ( "a" , encoding
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")  # info: fh . write ( json . dumps (
    os.chmod(cur, 0o600)  # info: os . chmod ( cur , 0o600 )
    return cur  # info: return cur

# ====================================================
# SECTION: function main
# What it does: Poll one getUpdates. Answer the sandbox when SANDBOX_REPLIES=1. Keep the live council quiet unless RR_RELAY_REPLIES=1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main():  # info: def main
    cfg = load_kv(CONF)  # info: set cfg
    if cfg.get("ENABLED", "1") != "1":  # info: if cfg . get ( "ENABLED" , "1"
        print("[skip] ENABLED=0"); return 0  # info: call print
    load_secrets([cfg.get("SECRETS_1", ""), cfg.get("SECRETS_2", "")])  # info: call load_secrets
    desk = (cfg.get("DESK_LIVE_FILE") or "").strip()  # info: set desk
    if desk:  # info: if desk :
        os.environ["DESK_LIVE_FILE"] = desk  # info: os . environ [ "DESK_LIVE_FILE" ] = desk
    else:  # info: else :
        os.environ.pop("DESK_LIVE_FILE", None)  # info: os . environ . pop ( "DESK_LIVE_FILE" ,
    voices = load_voices()  # info: set voices
    poll_voice = cfg.get("POLL_VOICE", "ava")  # info: set poll_voice
    if poll_voice not in voices:  # info: if poll_voice not in voices :
        poll_voice = next(iter(voices))  # info: set poll_voice
    token = token_for(voices[poll_voice])  # info: set token
    if not token:  # info: if not token :
        print("No data: poll token", file=sys.stderr); return 3  # info: call print
    chat_id = cfg.get("COUNCIL_CHAT_ID", "").strip()  # info: set chat_id
    if not chat_id:  # info: if not chat_id :
        print("No data: COUNCIL_CHAT_ID", file=sys.stderr); return 4  # info: call print
    sandbox_id = cfg.get("SANDBOX_CHAT_ID", "").strip()  # info: set sandbox_id
    allowed = {str(chat_id)}  # info: set allowed
    if sandbox_id:  # info: if sandbox_id :
        allowed.add(str(sandbox_id))  # info: allowed . add ( str ( sandbox_id ) )
    triggers = [x.strip().lower() for x in cfg.get("PIPELINE_TRIGGERS", "").split(",") if x.strip()]  # info: set triggers
    default_voice = cfg.get("DEFAULT_SINGLE_VOICE", "ava")  # info: set default_voice
    max_text = int(cfg.get("MAX_TEXT", "3900") or 3900)  # info: set max_text
    state_dir = Path(cfg.get("STATE_DIR", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Intake/council-relay"))  # info: set state_dir
    state_dir.mkdir(parents=True, exist_ok=True)  # info: state_dir . mkdir ( parents = True ,
    offset_file = state_dir / "offset.txt"  # info: set offset_file
    offset = int(offset_file.read_text().strip() or "0") if offset_file.is_file() else 0  # info: set offset
    timeout = int(cfg.get("POLL_TIMEOUT", "20") or "20")  # info: set timeout
    sandbox_note = f" sandbox={sandbox_id} sandbox_replies={'ON' if replies_for_chat(cfg, sandbox_id) else 'OFF'}" if sandbox_id else ""  # info: set sandbox_note
    print(f"[ok] relay chat={chat_id}{sandbox_note} poll={poll_voice} infer=FLM-prefer replies={'ON' if replies_enabled() else 'OFF (quiet; set RR_RELAY_REPLIES=1 to opt in)'}")  # info: call print

    last_rotate = 0.0  # info: set last_rotate
    while True:  # info: while True :
        if not replies_enabled() and time.time() - last_rotate >= 60:  # info: if not replies_enabled ( ) and time .
            last_rotate = time.time()  # info: set last_rotate
            try:  # info: try :
                inbox_rotate()  # info: call inbox_rotate
            except Exception as e:  # info: except Exception as e :
                print(f"[warn] relay inbox rotate failed: {type(e).__name__}", file=sys.stderr)  # info: call print
        try:  # info: try :
            body = api(token, "getUpdates", {"timeout": timeout, "offset": offset, "allowed_updates": ["message"]})  # info: set body
        except urllib.error.HTTPError as e:  # info: except urllib . error . HTTPError as e
            if e.code == 409:  # info: if e . code == 409 :
                print("[fail] 409 dual poller", file=sys.stderr); return 409  # info: call print
            raise  # info: raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:  # info: except ( urllib . error . URLError ,
            # Transient network error (e.g. read timeout 01:39 HST 2026-09-29): retry instead of exiting.
            print(f"[warn] getUpdates transient error: {type(e).__name__}; retry in 10s", file=sys.stderr)  # info: call print
            time.sleep(10)  # info: time . sleep ( 10 )
            continue  # info: continue
        for upd in body.get("result") or []:  # info: for upd in body . get ( "result"
            offset = int(upd["update_id"]) + 1  # info: set offset
            offset_file.write_text(str(offset))  # info: offset_file . write_text ( str ( offset )
            msg = upd.get("message") or {}  # info: set msg
            text = (msg.get("text") or "").strip()  # info: set text
            if not text:  # info: if not text :
                continue  # info: continue
            chat = msg.get("chat") or {}  # info: set chat
            ch = str(chat.get("id", ""))  # info: set ch
            is_private = chat.get("type") == "private"  # info: set is_private
            if not is_private and ch not in allowed:  # info: if not is_private and ch not in allowed :
                continue  # info: continue
            # Operator silence / not ready
            if SILENCE_RE.search(text):  # info: if SILENCE_RE . search ( text ) :
                print("[ok] silence cue — no post")  # info: call print
                continue  # info: continue
            allow_reply = replies_enabled() if is_private else replies_for_chat(cfg, ch)  # info: set allow_reply
            if not allow_reply:  # info: if not allow_reply :
                try:  # info: try :
                    inbox_hold(upd, msg, text, persona_target(text, is_private, poll_voice, voices, triggers, default_voice))  # info: call inbox_hold
                    held = "held in Relay-Inbox"  # info: set held
                except Exception as e:  # info: except Exception as e :
                    held = f"inbox write FAILED ({type(e).__name__})"  # info: set held
                print(f"[quiet] update {offset - 1} consumed — replies OFF (RR_RELAY_REPLIES=0): no infer, no post; {held}")  # info: call print
                continue  # info: continue

            if is_private:  # info: if is_private :
                reply = run_infer(cfg, poll_voice, text)  # info: set reply
                if reply:  # info: if reply :
                    post_as(poll_voice, voices, ch, reply, max_text, allow=True)  # info: call post_as
                continue  # info: continue

            if group_hello(text):  # info: if group_hello ( text ) :
                for hop in ("ava", "bruce", "carly"):  # info: for hop in ( "ava" , "bruce" , "carly" ) :
                    if hop not in voices:  # info: if hop not in voices :
                        continue  # info: continue
                    reply = run_infer(cfg, hop, "Greet the room in one or two sentences. User said: " + text)  # info: set reply
                    if reply:  # info: if reply :
                        post_as(hop, voices, ch, reply, max_text, allow=True)  # info: call post_as
                    time.sleep(0.4)  # info: time . sleep ( 0.4 )
                continue  # info: continue

            if wants_pipeline(text, triggers):  # info: if wants_pipeline ( text , triggers ) :
                prior = ""  # info: set prior
                for hop in PIPELINE_ORDER:  # info: for hop in PIPELINE_ORDER :
                    if hop not in voices:  # info: if hop not in voices :
                        continue  # info: continue
                    reply = run_infer(cfg, hop, text, prior=prior)  # info: set reply
                    if reply:  # info: if reply :
                        post_as(hop, voices, ch, reply, max_text, allow=True)  # info: call post_as
                        prior += f"\n[{hop}]: {reply}\n"  # info: set prior
                    time.sleep(0.4)  # info: time . sleep ( 0.4 )
                continue  # info: continue

            voice = mentioned_voice(text, voices) or default_voice  # info: set voice
            reply = run_infer(cfg, voice, text)  # info: set reply
            if reply:  # info: if reply :
                post_as(voice, voices, ch, reply, max_text, allow=True)  # info: call post_as
        time.sleep(0.2)  # info: time . sleep ( 0.2 )

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    try:  # info: try :
        raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
    except KeyboardInterrupt:  # info: except KeyboardInterrupt :
        print("[ok] stopped"); raise SystemExit(0)  # info: call print
