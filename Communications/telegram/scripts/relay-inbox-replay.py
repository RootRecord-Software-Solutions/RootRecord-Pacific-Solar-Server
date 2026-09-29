#!/usr/bin/env python3
"""relay-inbox-replay.py — list / answer messages the council relay held while quiet.

Approved 2026-09-29 (Library 08-ideas/2026-09-29-relay-quiet-mode-message-hold.md).

While RR_RELAY_REPLIES=0 (default), council-relay.py consumes each update and appends it to
  2 - RootRecord-Database/Logs/Communications/Relay-Inbox/relay-inbox_current.jsonl
(cut hourly into Relay-Inbox/Archive/YYYY-MM-DD/relay-inbox_YYYY-MM-DD_HH00.jsonl). The folder is
git-ignored because it holds private message text.

Usage (default is a read-only listing; nothing is inferred or sent):
  relay-inbox-replay.py                      # list pending held messages (metadata only)
  relay-inbox-replay.py --show-text          # ... include message text
  relay-inbox-replay.py --json               # machine-readable summary
  RR_RELAY_REPLIES=1 relay-inbox-replay.py --send [--limit N]
                                             # answer up to N pending items (default 5), oldest first,
                                             # as a Telegram reply to the original message_id.
Sending needs BOTH --send and RR_RELAY_REPLIES=1; otherwise it refuses (exit 3). Answered or
failed items are recorded in Relay-Inbox/replayed.jsonl and are not replayed twice.
Options: --inbox DIR (default: relay INBOX_DIR / $RR_RELAY_INBOX_DIR).
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys, time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("council_relay", HERE / "council-relay.py")
relay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(relay)  # definitions only (main() is __main__-guarded)

LEDGER = "replayed.jsonl"


def key(rec: dict) -> str:
    return f"{rec.get('chat_id')}:{rec.get('message_id')}"


def load_records(inbox: Path) -> tuple[list[dict], int]:
    files = sorted((inbox / "Archive").glob("*/relay-inbox_*.jsonl")) + [inbox / relay.INBOX_CURRENT]
    recs, bad = [], 0
    for f in files:
        if not f.is_file():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                r = json.loads(line)
                r["_file"] = str(f.relative_to(inbox))
                recs.append(r)
            except json.JSONDecodeError:
                bad += 1
    recs.sort(key=lambda r: (r.get("ts") or "", r.get("update_id") or 0))
    return recs, bad


def load_done(inbox: Path) -> set[str]:
    f = inbox / LEDGER
    if not f.is_file():
        return set()
    done = set()
    for line in f.read_text(encoding="utf-8").splitlines():
        try:
            done.add(json.loads(line)["key"])
        except (json.JSONDecodeError, KeyError):
            pass
    return done


def mark(inbox: Path, rec: dict, result: str) -> None:
    f = inbox / LEDGER
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"key": key(rec), "ts": datetime.now().astimezone().isoformat(timespec="seconds"), "result": result}) + "\n")
    os.chmod(f, 0o600)


def send_one(rec: dict, cfg: dict, voices: dict, max_text: int) -> str:
    target = rec.get("persona_target") or cfg.get("DEFAULT_SINGLE_VOICE", "ava")
    hops = [h for h in relay.PIPELINE_ORDER if h in voices] if str(target).startswith("pipeline:") else [target]
    prior, posted = "", 0
    for hop in hops:
        if hop not in voices:
            continue
        if not relay.replies_enabled():  # re-checked before every send
            return "refused: replies off"
        reply = relay.run_infer(cfg, hop, rec["text"], prior=prior)
        if not reply:
            continue
        tok = relay.token_for(voices[hop])
        if not tok:
            continue
        relay.api(tok, "sendMessage", {
            "chat_id": rec["chat_id"], "text": reply[:max_text], "disable_web_page_preview": True,
            "reply_to_message_id": rec.get("message_id"), "allow_sending_without_reply": True,
        })
        posted += 1
        prior += f"\n[{hop}]: {reply}\n"
        time.sleep(0.4)
    return f"posted {posted}" if posted else "no reply produced"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--inbox", default=str(relay.INBOX_DIR))
    ap.add_argument("--show-text", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--limit", type=int, default=5)
    a = ap.parse_args()
    inbox = Path(a.inbox)
    recs, bad = load_records(inbox)
    done = load_done(inbox)
    pending = [r for r in recs if key(r) not in done]
    if a.json:
        print(json.dumps({"inbox": str(inbox), "records": len(recs), "pending": len(pending), "done": len(done), "unparsed_lines": bad,
                          "pending_by_target": {t: sum(1 for r in pending if r.get("persona_target") == t) for t in sorted({str(r.get("persona_target")) for r in pending})}}))
    else:
        print(f"[inbox] {inbox}: records={len(recs)} pending={len(pending)} already-replayed={len(done)} unparsed={bad}")
        for r in pending:
            frm = r.get("from") or {}
            line = f"  {r.get('ts')} chat={r.get('chat_id')} msg={r.get('message_id')} from={frm.get('username') or frm.get('name') or frm.get('id')} -> {r.get('persona_target')} [{r.get('_file')}]"
            if a.show_text:
                line += f"\n      {r.get('text', '')!r}"
            print(line)
    if not a.send:
        if not a.json:
            print("[dry] listing only — nothing inferred or sent (use --send with RR_RELAY_REPLIES=1)")
        return 0
    if not relay.replies_enabled():
        print("[refuse] --send needs RR_RELAY_REPLIES=1 — nothing sent", file=sys.stderr)
        return 3
    cfg = relay.load_kv(relay.CONF)
    relay.load_secrets([cfg.get("SECRETS_1", ""), cfg.get("SECRETS_2", "")])
    if cfg.get("DESK_LIVE_FILE"):
        os.environ["DESK_LIVE_FILE"] = cfg["DESK_LIVE_FILE"]
    voices = relay.load_voices()
    max_text = int(cfg.get("MAX_TEXT", "3900") or 3900)
    for r in pending[: max(0, a.limit)]:
        try:
            res = send_one(r, cfg, voices, max_text)
        except Exception as e:  # keep going; record the failure so it is visible
            res = f"error {type(e).__name__}"
        mark(inbox, r, res)
        print(f"[send] {key(r)} -> {res}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
