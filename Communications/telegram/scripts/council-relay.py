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
import importlib.util, json, os, re, subprocess, sys, time, urllib.error, urllib.request  # info: import importlib . util , json , os , re , subprocess
from pathlib import Path  # info: from pathlib import Path
from datetime import datetime  # info: from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
CONF = ROOT / "config" / "relay.conf"  # info: set CONF
VOICES = ROOT / "config" / "voices.conf"  # info: set VOICES
PIPELINE_ORDER = ("ava", "bruce", "carly", "ava")  # info: set PIPELINE_ORDER
# Desk-safe NPU tags only. gemma3:4b and larger FLM weights are refused: llama3.2:3b already maps ~10 GB.
SAFE_NPU_MODELS = {"llama3.2:1b", "llama3.2:3b", "gemma3:1b"}  # info: set SAFE_NPU_MODELS
SILENCE_RE = re.compile(  # info: set SILENCE_RE
    r"do not say anything|don'?t say anything|say nothing|stay silent|no replies?|nowhere near ready",  # info: r"do not say anything|don'?t say anything|say nothing|stay silent|no replies?|nowhere near ready" ,
    re.I,  # info: re . I ,
)  # info: )
LEAK_RE = re.compile(r"DESK_LIVE|HARD RULES FOR THIS TURN|Do NOT state watts|standing envelopes|\[desk:|do not say you lack access|do not summarize|do not quote|measured\. If they answer", re.I)  # info: set LEAK_RE
GROUP_HELLO_RE = re.compile(r"^(hi|hey|hello|yo)( guys| all| everyone| team)?[.!?]*$", re.I)  # info: set GROUP_HELLO_RE
HUMAN_AT_RE = re.compile(r"@[A-Za-z][A-Za-z0-9_]{3,}")  # info: set HUMAN_AT_RE
READING_RE = re.compile(r"\b(weather|forecast|temperature|temp|rain|showers|wind|watts|soc|battery|power)\b", re.I)  # info: set READING_RE
WEATHER_RE = re.compile(r"\b(weather|forecast|temperature|temp|rain|showers)\b", re.I)  # info: set WEATHER_RE
CORRECTION_RE = re.compile(  # info: set CORRECTION_RE
    r"terrible response|you do though|you have access|ignore the data|didn'?t build|do not ignore|don'?t ignore|stop saying|use the (?:data|database|files)",  # info: correction phrases
    re.I,  # info: re . I
)  # info: )
STARTER_LESSONS = [  # info: set STARTER_LESSONS
    "Use the desk and the forecast on this turn. Do not say you lack access when those lines answer the question.",  # info: starter lesson
    "Root: You do though. You have access to the entire database.",  # info: starter lesson from the room
]  # info: ]
CORRECTION_RE = re.compile(r"terrible response|you do though|you have access|ignore the data|didn'?t build|do not ignore|don'?t ignore|stop saying|use the (?:data|database|files)", re.I)  # info: set CORRECTION_RE
STARTER_LESSONS = [  # info: set STARTER_LESSONS
    "Use the desk and the forecast on this turn. Do not say you lack access when those lines answer the question.",  # info: "Use the desk and the forecast
    "Root: You do though. You have access to the entire database.",  # info: "Root: You do though
]  # info: ]
SFP = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Weather/Hawai'i/reports/0 Level Processing/sfp_state_forecast_current.md")  # info: set SFP

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
# What it does: Original council answers when COUNCIL_REPLIES=1. Sandbox answers when SANDBOX_REPLIES=1. Anything else needs RR_RELAY_REPLIES=1.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def replies_for_chat(cfg, chat: str) -> bool:  # info: def replies_for_chat
    chat = str(chat)  # info: set chat
    sandbox = (cfg.get("SANDBOX_CHAT_ID") or "").strip()  # info: set sandbox
    if sandbox and chat == sandbox and (cfg.get("SANDBOX_REPLIES") or "0").strip() == "1":  # info: if sandbox and chat == sandbox
        return True  # info: return True
    council = (cfg.get("COUNCIL_CHAT_ID") or "").strip()  # info: set council
    if council and chat == council and (cfg.get("COUNCIL_REPLIES") or "0").strip() == "1":  # info: if council and chat == council
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
        flm = parts[6].strip() if len(parts) > 6 else ""  # info: set flm
        if enabled != "1":  # info: if enabled != "1" :
            continue  # info: continue
        voices[vid] = {"user": user, "token_env": token_env, "model": model, "fallback": fallback, "flm": flm}  # info: voices [ vid ] = { "user" :
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
# SECTION: function addresses_group
# What it does: True when the room is being spoken to and no single voice was named.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def addresses_group(text, voices):  # info: def addresses_group
    if group_hello(text):  # info: if group_hello ( text ) :
        return True  # info: return True
    if mentioned_voice(text, voices):  # info: if mentioned_voice ( text , voices ) :
        return False  # info: return False
    return bool(re.search(r"\b(you guys|guys|everyone|you all|all of you)\b", text, re.I))  # info: return bool ( re . search

# ====================================================
# SECTION: function clean_reply
# What it does: Drop leaked instruction lines and keep the rest of the reply. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clean_reply(text: str) -> str | None:  # info: def clean_reply
    if not text or not text.strip():  # info: if not text or not text . strip
        return None  # info: return None
    # strip single-flight noise and drop only the lines that leak instructions
    lines = [ln for ln in text.splitlines() if not ln.startswith("[ok]") and not LEAK_RE.search(ln)]  # info: set lines
    out = "\n".join(lines).strip()  # info: set out
    out = re.sub(r"^(?:ava|bruce|carly)\s*[:—-]\s*", "", out, count=1, flags=re.I).strip()  # info: set out
    return out or None  # info: return out or None

# ====================================================
# SECTION: function refresh_desk
# What it does: Rewrite desk-live.txt and the system state snapshot before a reply. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refresh_desk(cfg):  # info: def refresh_desk
    dest = (cfg.get("DESK_LIVE_FILE") or "").strip()  # info: set dest
    script = ROOT / "scripts" / "desk-live.py"  # info: set script
    state = ROOT.parents[1] / "System" / "scripts" / "state-aggregate.py"  # info: set state
    if dest and script.is_file():  # info: if dest and script . is_file
        try:  # info: try :
            subprocess.run([sys.executable, str(script), "--out", dest], timeout=20, check=False)  # info: call subprocess . run
        except (OSError, subprocess.TimeoutExpired) as e:  # info: except ( OSError , subprocess . TimeoutExpired )
            print(f"[warn] desk refresh failed: {type(e).__name__}", file=sys.stderr)  # info: call print
    if state.is_file():  # info: if state . is_file
        try:  # info: try :
            subprocess.run([sys.executable, str(state)], timeout=90, check=False)  # info: call subprocess . run
        except (OSError, subprocess.TimeoutExpired) as e:  # info: except ( OSError , subprocess . TimeoutExpired )
            print(f"[warn] state refresh failed: {type(e).__name__}", file=sys.stderr)  # info: call print

# ====================================================
# SECTION: function persona_system
# What it does: Load the CouncilPersona system text for ava, bruce, or carly.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona_system(voice):  # info: def persona_system
    loader = ROOT.parent / "CouncilPersona" / "scripts" / "personas.py"  # info: set loader
    spec = importlib.util.spec_from_file_location("rr_council_persona", loader)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader is None
        raise RuntimeError("personas.py is missing")  # info: raise RuntimeError
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    return mod.system_for(voice)  # info: return mod . system_for ( voice )

# ====================================================
# SECTION: function chat_voice
# What it does: Short Telegram voice. The Library pack is not pasted into a chat turn.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chat_voice(voice: str) -> str:  # info: def chat_voice
    name = {"ava": "Ava Ivy", "bruce": "Bruce Monitor", "carly": "Carly Mal"}.get(voice, voice)  # info: set name
    tone = {"ava": "Snappy, warm, direct, a little sharp.", "bruce": "Short, practical, calm.", "carly": "Direct and careful."}.get(voice, "Direct.")  # info: set tone
    return (  # info: return
        f"You are {name}. {tone} "  # info: f"You are { name }
        "You are in a Telegram chat. Answer the latest message in one or two sentences. "  # info: "You are in a Telegram chat
        "Talk like a person. Do not summarize a profile, notes, or a desk. "  # info: "Talk like a person
        "Do not invent watts, weather, or versions."  # info: "Do not invent watts
    )  # info: )

# ====================================================
# SECTION: function run_infer
# What it does: run infer with the voice persona. flm_model overrides FLM_MODEL for that voice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_infer(cfg, voice, prompt, prior="", flm_model=""):  # info: def run_infer
    run = cfg.get("RUN_INFER") or cfg.get("RUN_OLLAMA", "").replace("run-ollama.sh", "run-infer.sh")  # info: set run
    if not run or not Path(run).exists():  # info: if not run or not Path ( run
        run = str(ROOT.parent.parent.parent / "System" / "scripts" / "plumbing" / "run-infer.sh")  # info: set run
    full = prompt if not prior else f"Prior turns:\n{prior}\n\nYour turn as {voice}.\nUser:\n{prompt}"  # info: set full
    env = os.environ.copy()  # info: set env
    env["RR_NPU_ONLY"] = "1"  # info: env [ "RR_NPU_ONLY" ] = "1"
    env["FLM_CTX_LEN"] = "4096"  # info: env [ "FLM_CTX_LEN" ] = "4096"
    env["FLM_ON_DEMAND"] = "1"  # info: env [ "FLM_ON_DEMAND" ] = "1"
    if flm_model and flm_model not in SAFE_NPU_MODELS:  # info: if flm_model and flm_model not in SAFE_NPU_MODELS
        print(f"[warn] refused NPU tag {flm_model} — staying on the relay default", file=sys.stderr)  # info: call print
        flm_model = ""  # info: set flm_model
    if flm_model:  # info: if flm_model
        env["FLM_MODEL"] = flm_model  # info: env [ "FLM_MODEL" ] = flm_model
    if not READING_RE.search(full):  # info: if not READING_RE . search ( full )
        env.pop("DESK_LIVE_FILE", None)  # info: env . pop
    env["RR_PERSONA_SYSTEM"] = chat_voice(voice)  # info: env [ "RR_PERSONA_SYSTEM" ] = chat_voice ( voice )
    p = subprocess.run([run, voice, full], capture_output=True, text=True, timeout=600, env=env)  # info: set p
    out = (p.stdout or "").strip()  # info: set out
    # stderr may have [ok] FLM lines — ignore
    return clean_reply(out)  # info: return clean_reply ( out )

# ====================================================
# SECTION: function post_as
# What it does: Post one reply on the user's message. allow=False keeps a chat quiet. Never prints the token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def post_as(voice_id, voices, chat_id, text, max_text, allow=None, reply_to=None, thread_id=None):  # info: def post_as
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
    payload = {"chat_id": chat_id, "text": text[:max_text], "disable_web_page_preview": True}  # info: set payload
    if reply_to:  # info: if reply_to
        payload["reply_to_message_id"] = reply_to  # info: payload [ "reply_to_message_id" ] = reply_to
    if thread_id:  # info: if thread_id
        payload["message_thread_id"] = thread_id  # info: payload [ "message_thread_id" ] = thread_id
    api(tok, "sendMessage", payload)  # info: call api
    print(f"[ok] posted as {voice_id}")  # info: call print
    return True  # info: return True

# ====================================================
# SECTION: function bot_call
# What it does: One Telegram method as a voice. Failures are logged by type. Never prints the token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def bot_call(voice_id, voices, method, payload):  # info: def bot_call
    tok = token_for(voices[voice_id])  # info: set tok
    if not tok:  # info: if not tok :
        return False  # info: return False
    try:  # info: try :
        api(tok, method, payload)  # info: call api
        return True  # info: return True
    except Exception as e:  # info: except Exception as e :
        print(f"[warn] {method} {voice_id} {type(e).__name__}", file=sys.stderr)  # info: call print
        return False  # info: return False

# ====================================================
# SECTION: function mark_seen
# What it does: React with eyes on the user message so the room can see it was read. Does not send text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark_seen(voice_id, voices, chat_id, message_id):  # info: def mark_seen
    if not message_id:  # info: if not message_id :
        return False  # info: return False
    ok = bot_call(voice_id, voices, "setMessageReaction", {  # info: set ok
        "chat_id": chat_id, "message_id": message_id,  # info: "chat_id" : chat_id , "message_id" : message_id
        "reaction": [{"type": "emoji", "emoji": "👀"}],  # info: "reaction" : [ { "type" : "emoji" , "emoji" : "👀" } ]
    })  # info: )
    if ok:  # info: if ok :
        print(f"[ok] seen as {voice_id}")  # info: call print
    return ok  # info: return ok

# ====================================================
# SECTION: function mark_typing
# What it does: Show the Telegram typing indicator for one voice. Does not send text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark_typing(voice_id, voices, chat_id):  # info: def mark_typing
    return bot_call(voice_id, voices, "sendChatAction", {"chat_id": chat_id, "action": "typing"})  # info: return bot_call ( voice_id , voices , "sendChatAction"

# Quiet-mode inbox (Alexander 2026-09-29, Library 08-Ideas relay-quiet-mode-message-hold): while replies are
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
# SECTION: function note_mod
# What it does: Load voice_deliver once so a reply to a report can be stored. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def note_mod():  # info: def note_mod
    cached = getattr(note_mod, "mod", None)  # info: set cached
    if cached is not None:  # info: if cached is not None
        return cached  # info: return cached
    import importlib.util  # info: import importlib . util
    path = ROOT.parents[1] / "Media" / "Voice" / "scripts" / "voice_deliver.py"  # info: set path
    spec = importlib.util.spec_from_file_location("voice_deliver", path)  # info: set spec
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module
    note_mod.mod = mod  # info: note_mod . mod = mod
    return mod  # info: return mod

# ====================================================
# SECTION: function seed_interaction
# What it does: Record a sandbox message as an interaction request. Does not infer, send, or touch the live council chat.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def seed_interaction(msg, text, ch, sandbox_id):  # info: def seed_interaction
    frm = msg.get("from") or {}  # info: set frm
    payload = json.dumps({"chat_id": ch, "sandbox_chat_id": sandbox_id, "text": text, "message_id": msg.get("message_id"), "from_id": frm.get("id"), "username": frm.get("username") or ""})  # info: set payload
    script = Path("/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/execution/interaction.py")  # info: set script
    try:  # info: try :
        proc = subprocess.run([sys.executable, str(script), "seed"], input=payload, text=True, capture_output=True, timeout=5)  # info: set proc
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired ) as exc
        print(f"[warn] interaction seed failed: {type(exc).__name__}", file=sys.stderr)  # info: call print
        return  # info: return
    if proc.returncode != 0:  # info: if proc . returncode != 0
        print("[warn] interaction seed refused", file=sys.stderr)  # info: call print
        return  # info: return
    if os.environ.get("RR_INTERACTION_COUNCIL") != "1":  # info: if os . environ . get ( "RR_INTERACTION_COUNCIL" ) != "1"
        return  # info: return
    try:  # info: try :
        seeded = json.loads(proc.stdout or "{}")  # info: set seeded
    except ValueError:  # info: except ValueError
        return  # info: return
    if seeded.get("interaction_mode") not in ("work_order", "build"):  # info: if seeded . get ( "interaction_mode" ) not in ( "work_order" , "build" )
        return  # info: return
    subprocess.Popen([sys.executable, str(script), "council", seeded.get("request_id", "")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # info: call subprocess . Popen

# ====================================================
# SECTION: function context_path
# What it does: Path of the recent-chat file. Does not send or read the file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def context_path(state_dir):  # info: def context_path
    return Path(state_dir) / "chat-context.json"  # info: return Path ( state_dir ) / "chat-context.json"

# ====================================================
# SECTION: function load_context
# What it does: Read recent chat lines already seen. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_context(state_dir):  # info: def load_context
    path = context_path(state_dir)  # info: set path
    if not path.is_file():  # info: if not path . is_file
        return {}  # info: return { }
    try:  # info: try
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return {}  # info: return { }
    return data if isinstance(data, dict) else {}  # info: return data if isinstance ( data , dict ) else { }

# ====================================================
# SECTION: function remember_turn
# What it does: Keep the last eight lines for one chat. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def remember_turn(state_dir, chat_id, who, text, message_id):  # info: def remember_turn
    clean = " ".join((text or "").split())[:500]  # info: set clean
    if not clean:  # info: if not clean
        return  # info: return
    data = load_context(state_dir)  # info: set data
    key = str(chat_id)  # info: set key
    rows = data.get(key) if isinstance(data.get(key), list) else []  # info: set rows
    rows.append({"who": who, "text": clean, "message_id": message_id})  # info: rows . append
    data[key] = rows[-8:]  # info: data [ key ] = rows [ -8 : ]
    path = context_path(state_dir)  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace

# ====================================================
# SECTION: function chat_transcript
# What it does: Recent lines for one chat, oldest first. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chat_transcript(state_dir, chat_id) -> str:  # info: def chat_transcript
    rows = load_context(state_dir).get(str(chat_id)) or []  # info: set rows
    lines = []  # info: set lines
    prev = ""  # info: set prev
    for row in rows:  # info: for row in rows
        if isinstance(row, dict) and row.get("text"):  # info: if isinstance ( row , dict ) and row . get ( "text" )
            body = re.sub(r"^(?:ava|bruce|carly)\s*:\s*", "", row["text"], count=1, flags=re.I)  # info: set body
            line = f"{row.get('who') or 'user'} — {body}"  # info: set line
            if line == prev or LEAK_RE.search(row["text"]):  # info: if line == prev or LEAK_RE . search
                continue  # info: continue
            prev = line  # info: set prev
            lines.append(line)  # info: lines . append
    return "\n".join(lines)  # info: return "\n" . join ( lines )

# ====================================================
# SECTION: function only_for_a_person
# What it does: True when the message @names a person and does not name Ava, Bruce, or Carly. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def only_for_a_person(text, voices) -> bool:  # info: def only_for_a_person
    if mentioned_voice(text, voices) or addresses_group(text, voices):  # info: if mentioned_voice ( text , voices ) or addresses_group
        return False  # info: return False
    return bool(HUMAN_AT_RE.search(text or ""))  # info: return bool ( HUMAN_AT_RE . search ( text or "" ) )

# ====================================================
# SECTION: function forecast_excerpt
# What it does: The current Hawaii day and night from the NWS state forecast, including the highs and lows. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def forecast_excerpt() -> str:  # info: def forecast_excerpt
    try:  # info: try
        txt = SFP.read_text(encoding="utf-8")  # info: set txt
    except OSError:  # info: except OSError
        return ""  # info: return ""
    clock = datetime.now().astimezone()  # info: set clock
    day = clock.strftime("%A").upper()  # info: set day
    if clock.hour < 6:  # info: if clock . hour < 6
        wanted = ("REST OF TONIGHT", "TONIGHT", day, "TODAY", f"{day} NIGHT")  # info: set wanted
    else:  # info: else
        wanted = (day, "TODAY", f"{day} NIGHT", "TONIGHT", "REST OF TONIGHT")  # info: set wanted
    lines = []  # info: set lines
    for name in wanted:  # info: for name in wanted
        hit = re.search(rf"(?ms)^\.{re.escape(name)}\.\.\.(.+?)(?=^\.[A-Z]|```|\Z)", txt)  # info: set hit
        if not hit:  # info: if not hit
            continue  # info: continue
        lines.append(f"{name.title()}: {' '.join(hit.group(1).split())[:280]}")  # info: lines . append
        if len(lines) == 3:  # info: if len ( lines ) == 3
            break  # info: break
    return "\n".join(lines)  # info: return "\n" . join ( lines )

# ====================================================
# SECTION: function data_block
# What it does: Desk readings and the NWS forecast for this turn. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def data_block() -> str:  # info: def data_block
    chunks = []  # info: set chunks
    desk = (os.environ.get("DESK_LIVE_FILE") or "").strip()  # info: set desk
    if desk:  # info: if desk
        try:  # info: try
            raw = Path(desk).read_text(encoding="utf-8").splitlines()  # info: set raw
        except OSError:  # info: except OSError
            raw = []  # info: set raw
        body = [ln.strip() for ln in raw if ln.strip() and not ln.strip().startswith("#") and not ln.startswith("desk_written")]  # info: set body
        if body:  # info: if body
            chunks.append("Desk:\n" + "\n".join(body[:24]))  # info: chunks . append
    forecast = forecast_excerpt()  # info: set forecast
    if forecast:  # info: if forecast
        chunks.append("Forecast:\n" + forecast)  # info: chunks . append
    return "\n\n".join(chunks)  # info: return "\n\n" . join ( chunks )

# ====================================================
# SECTION: function lessons_path
# What it does: Path of the shared correction file. Does not send or read it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lessons_path(state_dir):  # info: def lessons_path
    return Path(state_dir) / "lessons.json"  # info: return Path ( state_dir ) / "lessons.json"

# ====================================================
# SECTION: function load_lessons
# What it does: Read corrections already accepted. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_lessons(state_dir) -> list:  # info: def load_lessons
    path = lessons_path(state_dir)  # info: set path
    if not path.is_file():  # info: if not path . is_file
        return []  # info: return [ ]
    try:  # info: try
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return []  # info: return [ ]
    if not isinstance(data, list):  # info: if not isinstance ( data , list )
        return []  # info: return [ ]
    return [str(row).strip() for row in data if str(row).strip()]  # info: return filtered rows

# ====================================================
# SECTION: function save_lessons
# What it does: Write the last eight corrections. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_lessons(state_dir, rows):  # info: def save_lessons
    path = lessons_path(state_dir)  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    tmp = path.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(list(rows)[-8:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, path)  # info: os . replace

# ====================================================
# SECTION: function ensure_lessons
# What it does: Seed the shared corrections once. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_lessons(state_dir):  # info: def ensure_lessons
    if load_lessons(state_dir):  # info: if load_lessons ( state_dir )
        return  # info: return
    save_lessons(state_dir, list(STARTER_LESSONS))  # info: call save_lessons

# ====================================================
# SECTION: function remember_lesson
# What it does: Store a room correction for Ava, Bruce, and Carly. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def remember_lesson(state_dir, who, text) -> bool:  # info: def remember_lesson
    raw = " ".join((text or "").split())  # info: set raw
    if not raw or not CORRECTION_RE.search(raw):  # info: if not raw or not CORRECTION_RE . search ( raw )
        return False  # info: return False
    line = f"{who}: {raw[:220]}"  # info: set line
    rows = load_lessons(state_dir)  # info: set rows
    if line in rows:  # info: if line in rows
        return False  # info: return False
    rows.append(line)  # info: rows . append
    save_lessons(state_dir, rows)  # info: call save_lessons
    return True  # info: return True

# ====================================================
# SECTION: function lesson_block
# What it does: Corrections the next reply must follow. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lesson_block(state_dir) -> str:  # info: def lesson_block
    rows = load_lessons(state_dir)  # info: set rows
    if not rows:  # info: if not rows
        return ""  # info: return ""
    lines = "\n".join(f"- {row}" for row in rows[-6:])  # info: set lines
    return "Corrections already accepted. Follow them:\n" + lines  # info: return the block

# ====================================================
# SECTION: function turn_preamble
# What it does: Data and accepted corrections for one voice. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def turn_preamble(voice, state_dir) -> str:  # info: def turn_preamble
    parts = [f"Answer as {voice}."]  # info: set parts
    data = data_block()  # info: set data
    if data:  # info: if data
        parts.append("Data on file. Measured. If these lines answer the person, use them. Do not say you lack access.\n" + data)  # info: parts . append
    lessons = lesson_block(state_dir)  # info: set lessons
    if lessons:  # info: if lessons
        parts.append(lessons)  # info: parts . append
    parts.append("On a greeting, do not recite every reading. On a question the data answers, answer from the data.")  # info: parts . append
    parts.append("Reply to the person who just spoke. Do not address anyone else by name.")  # info: parts . append
    return "\n\n".join(parts)  # info: return "\n\n" . join ( parts )

# ====================================================
# SECTION: function quoted_line
# What it does: The message this update replies to. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def quoted_line(msg) -> str:  # info: def quoted_line
    reply = msg.get("reply_to_message") or {}  # info: set reply
    text = (reply.get("text") or reply.get("caption") or "").strip()  # info: set text
    if not text:  # info: if not text
        return ""  # info: return ""
    who = ((reply.get("from") or {}).get("first_name") or "someone")  # info: set who
    return f"{who}: {' '.join(text.split())[:500]}"  # info: return f" { who }

# ====================================================
# SECTION: function continue_prompt
# What it does: Ask one voice to answer the latest message. Desk lines are included only when the person asked for a reading. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def continue_prompt(transcript, quoted, text, voice, state_dir) -> str:  # info: def continue_prompt
    parts = []  # info: set parts
    if READING_RE.search(text or ""):  # info: if READING_RE . search ( text or "" )
        data = data_block()  # info: set data
        if data:  # info: if data
            parts.append(data)  # info: parts . append
    elif CORRECTION_RE.search(text or ""):  # info: elif CORRECTION_RE . search ( text or "" )
        lessons = lesson_block(state_dir)  # info: set lessons
        if lessons:  # info: if lessons
            parts.append(lessons)  # info: parts . append
    if transcript:  # info: if transcript
        parts.append(transcript)  # info: parts . append
    if quoted:  # info: if quoted
        parts.append(quoted)  # info: parts . append
    parts.append(text)  # info: parts . append
    return "\n\n".join(parts)  # info: return "\n\n" . join ( parts )

# ====================================================
# SECTION: function continue_reply
# What it does: Ava answers a follow-up unless the text names one AI. Posts as a reply to that message. Does not start a second poll.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def continue_reply(cfg, state_dir, voices, voice, msg, text, max_text):  # info: def continue_reply
    chat = msg.get("chat") or {}  # info: set chat
    ch = str(chat.get("id", ""))  # info: set ch
    mid = msg.get("message_id")  # info: set mid
    thread_id = msg.get("message_thread_id")  # info: set thread_id
    prior = chat_transcript(state_dir, ch)  # info: set prior
    quote = quoted_line(msg)  # info: set quote
    sender = ((msg.get("from") or {}).get("first_name") or "user")  # info: set sender
    remember_turn(state_dir, ch, sender, text, mid)  # info: call remember_turn
    mark_seen(voice, voices, ch, mid)  # info: call mark_seen
    mark_typing(voice, voices, ch)  # info: call mark_typing
    reply = run_infer(cfg, voice, continue_prompt(prior, quote, text, voice, state_dir), flm_model=(voices.get(voice) or {}).get("flm") or "")  # info: set reply
    if not reply:  # info: if not reply
        return False  # info: return False
    posted = post_as(voice, voices, ch, reply, max_text, allow=True, reply_to=mid, thread_id=thread_id)  # info: set posted
    if posted:  # info: if posted
        remember_turn(state_dir, ch, voice, reply, None)  # info: call remember_turn
    return posted  # info: return posted

# ====================================================
# SECTION: function main
# What it does: Poll one getUpdates. Answer the original council when COUNCIL_REPLIES=1. A follow-up with no name is Ava, using recent chat. Answer the sandbox only when SANDBOX_REPLIES=1. Private DMs stay quiet unless RR_RELAY_REPLIES=1.
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
    ensure_lessons(state_dir)  # info: call ensure_lessons
    offset_file = state_dir / "offset.txt"  # info: set offset_file
    offset = int(offset_file.read_text().strip() or "0") if offset_file.is_file() else 0  # info: set offset
    timeout = int(cfg.get("POLL_TIMEOUT", "20") or "20")  # info: set timeout
    sandbox_note = f" sandbox={sandbox_id} sandbox_replies={'ON' if replies_for_chat(cfg, sandbox_id) else 'OFF'}" if sandbox_id else ""  # info: set sandbox_note
    council_note = f" council_replies={'ON' if replies_for_chat(cfg, chat_id) else 'OFF'}"  # info: set council_note
    ava_flm = (voices.get("ava") or {}).get("flm") or os.environ.get("FLM_MODEL", "llama3.2:3b")  # info: set ava_flm
    print(f"[ok] relay chat={chat_id}{council_note}{sandbox_note} poll={poll_voice} ava_model={ava_flm} infer=FLM-prefer replies={'ON' if replies_enabled() else 'OFF (private DMs quiet; RR_RELAY_REPLIES=0)'}")  # info: call print

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
            if not text or (msg.get("from") or {}).get("is_bot"):  # info: if not text or ( msg . get ( "from" ) or { } ) . get ( "is_bot" )
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
            if sandbox_id and ch == str(sandbox_id):  # info: if sandbox_id and ch == str ( sandbox_id )
                seed_interaction(msg, text, ch, sandbox_id)  # info: call seed_interaction
            if msg.get("reply_to_message"):  # info: if msg . get ( "reply_to_message" )
                try:  # info: try
                    if note_mod().record_note(msg):  # info: if note_mod ( ) . record_note ( msg )
                        print("[ok] report note recorded")  # info: call print
                except Exception as e:  # info: except Exception as e
                    print(f"[warn] report note failed: {type(e).__name__}", file=sys.stderr)  # info: call print
            if not allow_reply:  # info: if not allow_reply :
                try:  # info: try :
                    inbox_hold(upd, msg, text, persona_target(text, is_private, poll_voice, voices, triggers, default_voice))  # info: call inbox_hold
                    held = "held in Relay-Inbox"  # info: set held
                except Exception as e:  # info: except Exception as e :
                    held = f"inbox write FAILED ({type(e).__name__})"  # info: set held
                print(f"[quiet] update {offset - 1} consumed — replies OFF (RR_RELAY_REPLIES=0): no infer, no post; {held}")  # info: call print
                continue  # info: continue

            mid = msg.get("message_id")  # info: set mid
            thread_id = msg.get("message_thread_id")  # info: set thread_id
            sender = ((msg.get("from") or {}).get("first_name") or "user")  # info: set sender
            if remember_lesson(state_dir, sender, text):  # info: if remember_lesson
                print("[ok] lesson stored")  # info: call print
            if not is_private and only_for_a_person(text, voices):  # info: if not is_private and only_for_a_person
                print("[ok] named a person, not a council voice — no reply")  # info: call print
                continue  # info: continue
            named = None if is_private else mentioned_voice(text, voices)  # info: set named
            if named:  # info: if named
                mark_seen(named, voices, ch, mid)  # info: call mark_seen
                mark_typing(named, voices, ch)  # info: call mark_typing
            refresh_desk(cfg)  # info: call refresh_desk
            if is_private:  # info: if is_private :
                continue_reply(cfg, state_dir, voices, poll_voice, msg, text, max_text)  # info: call continue_reply
                continue  # info: continue

            if wants_pipeline(text, triggers):  # info: if wants_pipeline ( text , triggers ) :
                prior = chat_transcript(state_dir, ch)  # info: set prior
                remember_turn(state_dir, ch, (msg.get("from") or {}).get("first_name") or "user", text, mid)  # info: call remember_turn
                for hop in PIPELINE_ORDER:  # info: for hop in PIPELINE_ORDER :
                    if hop not in voices:  # info: if hop not in voices :
                        continue  # info: continue
                    mark_seen(hop, voices, ch, mid)  # info: call mark_seen
                    hop_prompt = turn_preamble(hop, state_dir) + "\n\nRecent chat:\n" + prior + "\n\nUser: " + text  # info: set hop_prompt
                    reply = run_infer(cfg, hop, hop_prompt, flm_model=(voices.get(hop) or {}).get("flm") or "")  # info: set reply
                    if reply:  # info: if reply :
                        mark_typing(hop, voices, ch)  # info: call mark_typing
                        post_as(hop, voices, ch, reply, max_text, allow=True, reply_to=mid, thread_id=thread_id)  # info: call post_as
                        prior += f"\n[{hop}]: {reply}\n"  # info: set prior
                        remember_turn(state_dir, ch, hop, reply, None)  # info: call remember_turn
                    time.sleep(0.4)  # info: time . sleep ( 0.4 )
                continue  # info: continue

            if addresses_group(text, voices):  # info: if addresses_group ( text , voices ) :
                room = [hop for hop in ("ava", "bruce", "carly") if hop in voices]  # info: set room
                prior_chat = chat_transcript(state_dir, ch)  # info: set prior_chat
                quote = quoted_line(msg)  # info: set quote
                remember_turn(state_dir, ch, (msg.get("from") or {}).get("first_name") or "user", text, mid)  # info: call remember_turn
                for hop in room:  # info: for hop in room :
                    mark_seen(hop, voices, ch, mid)  # info: call mark_seen
                for hop in room:  # info: for hop in room :
                    ask = turn_preamble(hop, state_dir)  # info: set ask
                    if group_hello(text):  # info: if group_hello ( text )
                        ask += "\n\nGreet the room in one or two sentences."  # info: set ask
                    if prior_chat:  # info: if prior_chat
                        ask += "\n\nRecent chat:\n" + prior_chat  # info: set ask
                    if quote:  # info: if quote
                        ask += "\n\nThis message replies to:\n" + quote  # info: set ask
                    ask += "\n\nUser: " + text  # info: set ask
                    reply = run_infer(cfg, hop, ask, flm_model=(voices.get(hop) or {}).get("flm") or "")  # info: set reply
                    if reply:  # info: if reply :
                        mark_typing(hop, voices, ch)  # info: call mark_typing
                        if post_as(hop, voices, ch, reply, max_text, allow=True, reply_to=mid, thread_id=thread_id):  # info: if post_as
                            remember_turn(state_dir, ch, hop, reply, None)  # info: call remember_turn
                    time.sleep(0.4)  # info: time . sleep ( 0.4 )
                continue  # info: continue

            voice = mentioned_voice(text, voices) or default_voice  # info: set voice
            continue_reply(cfg, state_dir, voices, voice, msg, text, max_text)  # info: call continue_reply
        time.sleep(0.2)  # info: time . sleep ( 0.2 )

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    try:  # info: try :
        raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
    except KeyboardInterrupt:  # info: except KeyboardInterrupt :
        print("[ok] stopped"); raise SystemExit(0)  # info: call print
