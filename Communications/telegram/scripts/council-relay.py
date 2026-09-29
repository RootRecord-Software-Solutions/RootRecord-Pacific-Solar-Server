#!/usr/bin/env python3
"""Council relay: one getUpdates; single voice default; A>B>C>A on triggers.
Posts only clean replies (never DESK_LIVE / instruction leaks). Prefer FLM/NPU via run-infer.sh."""
from __future__ import annotations
import json, os, re, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "config" / "relay.conf"
VOICES = ROOT / "config" / "voices.conf"
PIPELINE_ORDER = ("ava", "bruce", "carly", "ava")
SILENCE_RE = re.compile(
    r"do not say anything|don'?t say anything|say nothing|stay silent|no replies?|nowhere near ready",
    re.I,
)
LEAK_RE = re.compile(r"DESK_LIVE:|HARD RULES FOR THIS TURN|Do NOT state watts|standing envelopes|\[desk:", re.I)

def load_kv(path: Path) -> dict:
    out = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out

def load_secrets(paths):
    for p in paths:
        fp = Path(p)
        if not fp.is_file():
            continue
        for line in fp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v

def load_voices():
    voices = {}
    for line in VOICES.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        vid, enabled, user, token_env, model, fallback = parts[:6]
        if enabled != "1":
            continue
        voices[vid] = {"user": user, "token_env": token_env, "model": model, "fallback": fallback}
    return voices

def token_for(voice):
    t = (os.environ.get(voice["token_env"]) or "").strip()
    if t:
        return t
    if "AVA" in voice["token_env"]:
        return (os.environ.get("AVA_TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    return ""

def api(token, method, payload=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"} if data else {}, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.load(r)
    if not body.get("ok"):
        raise RuntimeError(f"{method} failed")
    return body

def wants_pipeline(text, triggers):
    t = text.lower()
    for trig in triggers:
        if trig and trig in t:
            return True
    return bool(re.search(r"\ba\s*>\s*b\s*>\s*c\b", t))

def mentioned_voice(text, voices):
    t = text.lower()
    for vid, v in voices.items():
        user = (v.get("user") or "").lower()
        if user and f"@{user}" in t:
            return vid
    hits = []
    if re.search(r"\bava\b|@ava", t):
        hits.append("ava")
    if re.search(r"\bbruce\b|@bruce", t):
        hits.append("bruce")
    if re.search(r"\bcarly\b|@carly", t):
        hits.append("carly")
    if len(hits) == 1:
        return hits[0]
    return None

def clean_reply(text: str) -> str | None:
    if not text or not text.strip():
        return None
    if LEAK_RE.search(text):
        # refuse to post instruction leaks
        return None
    # strip single-flight noise
    lines = [ln for ln in text.splitlines() if not ln.startswith("[ok]")]
    out = "\n".join(lines).strip()
    return out or None

def run_infer(cfg, voice, prompt, prior=""):
    run = cfg.get("RUN_INFER") or cfg.get("RUN_OLLAMA", "").replace("run-ollama.sh", "run-infer.sh")
    if not run or not Path(run).exists():
        run = "/home/rootrecord/.ollama/skills/plumbing/scripts/run-infer.sh"
    full = prompt if not prior else f"Prior turns:\n{prior}\n\nYour turn as {voice}.\nUser:\n{prompt}"
    p = subprocess.run([run, voice, full], capture_output=True, text=True, timeout=600)
    out = (p.stdout or "").strip()
    # stderr may have [ok] FLM lines — ignore
    return clean_reply(out)

def post_as(voice_id, voices, chat_id, text, max_text):
    text = clean_reply(text)
    if not text:
        print(f"[skip] empty/leaky reply for {voice_id}")
        return False
    tok = token_for(voices[voice_id])
    if not tok:
        print(f"[fail] no token {voice_id}", file=sys.stderr)
        return False
    api(tok, "sendMessage", {"chat_id": chat_id, "text": text[:max_text], "disable_web_page_preview": True})
    print(f"[ok] posted as {voice_id}")
    return True

def main():
    cfg = load_kv(CONF)
    if cfg.get("ENABLED", "1") != "1":
        print("[skip] ENABLED=0"); return 0
    load_secrets([cfg.get("SECRETS_1", ""), cfg.get("SECRETS_2", "")])
    desk = (cfg.get("DESK_LIVE_FILE") or "").strip()
    if desk:
        os.environ["DESK_LIVE_FILE"] = desk
    else:
        os.environ.pop("DESK_LIVE_FILE", None)
    voices = load_voices()
    poll_voice = cfg.get("POLL_VOICE", "ava")
    if poll_voice not in voices:
        poll_voice = next(iter(voices))
    token = token_for(voices[poll_voice])
    if not token:
        print("No data: poll token", file=sys.stderr); return 3
    chat_id = cfg.get("COUNCIL_CHAT_ID", "").strip()
    if not chat_id:
        print("No data: COUNCIL_CHAT_ID", file=sys.stderr); return 4
    triggers = [x.strip().lower() for x in cfg.get("PIPELINE_TRIGGERS", "").split(",") if x.strip()]
    default_voice = cfg.get("DEFAULT_SINGLE_VOICE", "ava")
    max_text = int(cfg.get("MAX_TEXT", "3900") or 3900)
    state_dir = Path(cfg.get("STATE_DIR", "/home/rootrecord/Database/intake/council-relay"))
    state_dir.mkdir(parents=True, exist_ok=True)
    offset_file = state_dir / "offset.txt"
    offset = int(offset_file.read_text().strip() or "0") if offset_file.is_file() else 0
    timeout = int(cfg.get("POLL_TIMEOUT", "20") or "20")
    print(f"[ok] relay chat={chat_id} poll={poll_voice} infer=FLM-prefer")

    while True:
        try:
            body = api(token, "getUpdates", {"timeout": timeout, "offset": offset, "allowed_updates": ["message"]})
        except urllib.error.HTTPError as e:
            if e.code == 409:
                print("[fail] 409 dual poller", file=sys.stderr); return 409
            raise
        for upd in body.get("result") or []:
            offset = int(upd["update_id"]) + 1
            offset_file.write_text(str(offset))
            msg = upd.get("message") or {}
            text = (msg.get("text") or "").strip()
            if not text:
                continue
            chat = msg.get("chat") or {}
            ch = str(chat.get("id", ""))
            is_private = chat.get("type") == "private"
            if not is_private and ch != str(chat_id):
                continue
            # Operator silence / not ready
            if SILENCE_RE.search(text):
                print("[ok] silence cue — no post")
                continue

            if is_private:
                reply = run_infer(cfg, poll_voice, text)
                if reply:
                    post_as(poll_voice, voices, ch, reply, max_text)
                continue

            if wants_pipeline(text, triggers):
                prior = ""
                for hop in PIPELINE_ORDER:
                    if hop not in voices:
                        continue
                    reply = run_infer(cfg, hop, text, prior=prior)
                    if reply:
                        post_as(hop, voices, chat_id, reply, max_text)
                        prior += f"\n[{hop}]: {reply}\n"
                    time.sleep(0.4)
                continue

            voice = mentioned_voice(text, voices) or default_voice
            reply = run_infer(cfg, voice, text)
            if reply:
                post_as(voice, voices, chat_id, reply, max_text)
        time.sleep(0.2)

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("[ok] stopped"); raise SystemExit(0)
