# ==============================================================================
# FILE: Communications/telegram/scripts/relay-inbox-replay.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""relay-inbox-replay.py — list / answer messages the council relay held while quiet.

Approved 2026-09-29 (Library 08-Ideas/2026-09-29-relay-quiet-mode-message-hold.md).

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
from __future__ import annotations  # info: from __future__ import annotations
import argparse, importlib.util, json, os, sys, time  # info: import argparse , importlib . util , json
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
_spec = importlib.util.spec_from_file_location("council_relay", HERE / "council-relay.py")  # info: set _spec
relay = importlib.util.module_from_spec(_spec)  # info: set relay
_spec.loader.exec_module(relay)  # definitions only (main() is __main__-guarded)

LEDGER = "replayed.jsonl"  # info: set LEDGER


# ====================================================
# SECTION: function key
# What it does: key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def key(rec: dict) -> str:  # info: def key
    return f"{rec.get('chat_id')}:{rec.get('message_id')}"  # info: return f" { rec . get ( 'chat_id'


# ====================================================
# SECTION: function load_records
# What it does: load records.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_records(inbox: Path) -> tuple[list[dict], int]:  # info: def load_records
    files = sorted((inbox / "Archive").glob("*/relay-inbox_*.jsonl")) + [inbox / relay.INBOX_CURRENT]  # info: set files
    recs, bad = [], 0  # info: recs , bad = [ ] , 0
    for f in files:  # info: for f in files :
        if not f.is_file():  # info: if not f . is_file ( ) :
            continue  # info: continue
        for line in f.read_text(encoding="utf-8").splitlines():  # info: for line in f . read_text ( encoding
            if not line.strip():  # info: if not line . strip ( ) :
                continue  # info: continue
            try:  # info: try :
                r = json.loads(line)  # info: set r
                r["_file"] = str(f.relative_to(inbox))  # info: r [ "_file" ] = str ( f
                recs.append(r)  # info: recs . append ( r )
            except json.JSONDecodeError:  # info: except json . JSONDecodeError :
                bad += 1  # info: set bad
    recs.sort(key=lambda r: (r.get("ts") or "", r.get("update_id") or 0))  # info: recs . sort ( key = lambda r
    return recs, bad  # info: return recs , bad


# ====================================================
# SECTION: function load_done
# What it does: load done.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_done(inbox: Path) -> set[str]:  # info: def load_done
    f = inbox / LEDGER  # info: set f
    if not f.is_file():  # info: if not f . is_file ( ) :
        return set()  # info: return set ( )
    done = set()  # info: set done
    for line in f.read_text(encoding="utf-8").splitlines():  # info: for line in f . read_text ( encoding
        try:  # info: try :
            done.add(json.loads(line)["key"])  # info: done . add ( json . loads (
        except (json.JSONDecodeError, KeyError):  # info: except ( json . JSONDecodeError , KeyError )
            pass  # info: pass
    return done  # info: return done


# ====================================================
# SECTION: function mark
# What it does: mark.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def mark(inbox: Path, rec: dict, result: str) -> None:  # info: def mark
    f = inbox / LEDGER  # info: set f
    with f.open("a", encoding="utf-8") as fh:  # info: with f . open ( "a" , encoding
        fh.write(json.dumps({"key": key(rec), "ts": datetime.now().astimezone().isoformat(timespec="seconds"), "result": result}) + "\n")  # info: fh . write ( json . dumps (
    os.chmod(f, 0o600)  # info: os . chmod ( f , 0o600 )


# ====================================================
# SECTION: function send_one
# What it does: send one.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def send_one(rec: dict, cfg: dict, voices: dict, max_text: int) -> str:  # info: def send_one
    target = rec.get("persona_target") or cfg.get("DEFAULT_SINGLE_VOICE", "ava")  # info: set target
    hops = [h for h in relay.PIPELINE_ORDER if h in voices] if str(target).startswith("pipeline:") else [target]  # info: set hops
    prior, posted = "", 0  # info: prior , posted = "" , 0
    for hop in hops:  # info: for hop in hops :
        if hop not in voices:  # info: if hop not in voices :
            continue  # info: continue
        if not relay.replies_enabled():  # re-checked before every send
            return "refused: replies off"  # info: return "refused: replies off"
        reply = relay.run_infer(cfg, hop, rec["text"], prior=prior)  # info: set reply
        if not reply:  # info: if not reply :
            continue  # info: continue
        tok = relay.token_for(voices[hop])  # info: set tok
        if not tok:  # info: if not tok :
            continue  # info: continue
        relay.api(tok, "sendMessage", {  # info: relay . api ( tok , "sendMessage" ,
            "chat_id": rec["chat_id"], "text": reply[:max_text], "disable_web_page_preview": True,  # info: "chat_id" : rec [ "chat_id" ] , "text"
            "reply_to_message_id": rec.get("message_id"), "allow_sending_without_reply": True,  # info: "reply_to_message_id" : rec . get ( "message_id" )
        })  # info: } )
        posted += 1  # info: set posted
        prior += f"\n[{hop}]: {reply}\n"  # info: set prior
        time.sleep(0.4)  # info: time . sleep ( 0.4 )
    return f"posted {posted}" if posted else "no reply produced"  # info: return f" posted { posted } " if


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])  # info: set ap
    ap.add_argument("--inbox", default=str(relay.INBOX_DIR))  # info: ap . add_argument ( "--inbox" , default =
    ap.add_argument("--show-text", action="store_true")  # info: ap . add_argument ( "--show-text" , action =
    ap.add_argument("--json", action="store_true")  # info: ap . add_argument ( "--json" , action =
    ap.add_argument("--send", action="store_true")  # info: ap . add_argument ( "--send" , action =
    ap.add_argument("--limit", type=int, default=5)  # info: ap . add_argument ( "--limit" , type =
    a = ap.parse_args()  # info: set a
    inbox = Path(a.inbox)  # info: set inbox
    recs, bad = load_records(inbox)  # info: recs , bad = load_records ( inbox )
    done = load_done(inbox)  # info: set done
    pending = [r for r in recs if key(r) not in done]  # info: set pending
    if a.json:  # info: if a . json :
        print(json.dumps({"inbox": str(inbox), "records": len(recs), "pending": len(pending), "done": len(done), "unparsed_lines": bad,  # info: call print
                          "pending_by_target": {t: sum(1 for r in pending if r.get("persona_target") == t) for t in sorted({str(r.get("persona_target")) for r in pending})}}))  # info: "pending_by_target" : { t : sum ( 1
    else:  # info: else :
        print(f"[inbox] {inbox}: records={len(recs)} pending={len(pending)} already-replayed={len(done)} unparsed={bad}")  # info: call print
        for r in pending:  # info: for r in pending :
            frm = r.get("from") or {}  # info: set frm
            line = f"  {r.get('ts')} chat={r.get('chat_id')} msg={r.get('message_id')} from={frm.get('username') or frm.get('name') or frm.get('id')} -> {r.get('persona_target')} [{r.get('_file')}]"  # info: set line
            if a.show_text:  # info: if a . show_text :
                line += f"\n      {r.get('text', '')!r}"  # info: set line
            print(line)  # info: call print
    if not a.send:  # info: if not a . send :
        if not a.json:  # info: if not a . json :
            print("[dry] listing only — nothing inferred or sent (use --send with RR_RELAY_REPLIES=1)")  # info: call print
        return 0  # info: return 0
    if not relay.replies_enabled():  # info: if not relay . replies_enabled ( ) :
        print("[refuse] --send needs RR_RELAY_REPLIES=1 — nothing sent", file=sys.stderr)  # info: call print
        return 3  # info: return 3
    cfg = relay.load_kv(relay.CONF)  # info: set cfg
    relay.load_secrets([cfg.get("SECRETS_1", ""), cfg.get("SECRETS_2", "")])  # info: relay . load_secrets ( [ cfg . get
    if cfg.get("DESK_LIVE_FILE"):  # info: if cfg . get ( "DESK_LIVE_FILE" ) :
        os.environ["DESK_LIVE_FILE"] = cfg["DESK_LIVE_FILE"]  # info: os . environ [ "DESK_LIVE_FILE" ] = cfg
    voices = relay.load_voices()  # info: set voices
    max_text = int(cfg.get("MAX_TEXT", "3900") or 3900)  # info: set max_text
    for r in pending[: max(0, a.limit)]:  # info: for r in pending [ : max (
        try:  # info: try :
            res = send_one(r, cfg, voices, max_text)  # info: set res
        except Exception as e:  # keep going; record the failure so it is visible
            res = f"error {type(e).__name__}"  # info: set res
        mark(inbox, r, res)  # info: call mark
        print(f"[send] {key(r)} -> {res}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
