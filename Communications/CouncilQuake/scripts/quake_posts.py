# ==============================================================================
# FILE: Communications/CouncilQuake/scripts/quake_posts.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Carly per-quake Telegram notices from hawaii_current.json and global_current.json.

Reads the existing Geology files. Does not fetch USGS. Dry-run by default:
no Telegram, no Kokoro, no token load. Each feed seeds once and posts nothing
on that first pass. A fixture run with an empty seen list prints the notice.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
SCRIPTS = Path(__file__).resolve().parent  # info: set SCRIPTS
PACIFIC = ROOT.parents[1]  # info: set PACIFIC
DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DB
HAWAII = DB / "Geology" / "Earthquakes" / "hawaii_current.json"  # info: set HAWAII
GLOBAL = DB / "Geology" / "Earthquakes" / "global_current.json"  # info: set GLOBAL
DATA = DB / "Communications" / "CouncilQuake"  # info: set DATA
LOG_DIR = DB / "Logs" / "Communications" / "CouncilQuake"  # info: set LOG_DIR
SEEN_NAME = "seen.json"  # info: set SEEN_NAME
LAST_NAME = "last.json"  # info: set LAST_NAME
LOG_NAME = "quake-posts.jsonl"  # info: set LOG_NAME
MIN_MAG = 2.0  # info: set MIN_MAG
MAX_POSTS = 4  # info: set MAX_POSTS
RELAY_CONF = PACIFIC / "Communications" / "telegram" / "config" / "relay.conf"  # info: set RELAY_CONF

if str(SCRIPTS) not in sys.path:  # info: if str ( SCRIPTS ) not in sys
    sys.path.insert(0, str(SCRIPTS))  # info: sys . path . insert ( 0 ,


# ====================================================
# SECTION: function send_enabled
# What it does: send enabled.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def send_enabled() -> bool:  # info: def send_enabled
    return os.environ.get("RR_COUNCIL_QUAKE_SEND", "0").strip() == "1"  # info: return os . environ . get ( "RR_COUNCIL_QUAKE_SEND"


# ====================================================
# SECTION: function wav_enabled
# What it does: wav enabled.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wav_enabled() -> bool:  # info: def wav_enabled
    return os.environ.get("RR_COUNCIL_QUAKE_WAV", "0").strip() == "1"  # info: return os . environ . get ( "RR_COUNCIL_QUAKE_WAV"


# ====================================================
# SECTION: function _mag
# What it does:  mag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _mag(event: dict) -> float | None:  # info: def _mag
    try:  # info: try :
        return float(event.get("mag"))  # info: return float ( event . get ( "mag"
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        return None  # info: return None


# ====================================================
# SECTION: function _fmt_time
# What it does:  fmt time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fmt_time(event: dict) -> str:  # info: def _fmt_time
    raw = str(event.get("time_hst") or "").strip()  # info: set raw
    if not raw:  # info: if not raw :
        return "time unknown"  # info: return "time unknown"
    try:  # info: try :
        dt = datetime.fromisoformat(raw)  # info: set dt
    except ValueError:  # info: except ValueError :
        return "time unknown"  # info: return "time unknown"
    hour = dt.strftime("%I").lstrip("0") or "12"  # info: set hour
    return f"{dt.strftime('%b')} {dt.day}, {hour}:{dt.strftime('%M')} {dt.strftime('%p')} HST"  # info: return f" { dt . strftime ( '%b'


# ====================================================
# SECTION: function format_quake
# What it does: format quake.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def format_quake(event: dict, region: str = "Hawaii region") -> str:  # info: def format_quake
    mag = _mag(event)  # info: set mag
    mag_s = f"{mag:.1f}" if mag is not None else "—"  # info: set mag_s
    place = str(event.get("place") or "location unknown").strip()  # info: set place
    label = "worldwide" if region == "worldwide" else "Hawaii region"  # info: set label
    lines = [  # info: set lines
        f"Earthquake — USGS ({label})",  # info: f" Earthquake — USGS ( { label } ) " ,
        f"M {mag_s} · {place}",  # info: f" M { mag_s } · { place
        _fmt_time(event),  # info: call _fmt_time
    ]  # info: ]
    try:  # info: try :
        lines.append(f"Depth {float(event.get('depth_km')):g} km")  # info: lines . append ( f" Depth { float
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        pass  # info: pass
    url = str(event.get("url") or "").strip()  # info: set url
    qid = str(event.get("id") or "").strip()  # info: set qid
    if not url and qid:  # info: if not url and qid :
        url = f"https://earthquake.usgs.gov/earthquakes/eventpage/{qid}"  # info: set url
    if url:  # info: if url :
        lines.append(url)  # info: lines . append ( url )
    return "\n".join(lines)  # info: return "\n" . join ( lines )


# ====================================================
# SECTION: function spoken_quake
# What it does: spoken quake.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spoken_quake(event: dict, region: str = "Hawaii region") -> str:  # info: def spoken_quake
    mag = _mag(event)  # info: set mag
    mag_s = f"{mag:.1f}" if mag is not None else "unknown"  # info: set mag_s
    place = str(event.get("place") or "location unknown").strip()  # info: set place
    survey = "U. S. Geological Survey worldwide." if region == "worldwide" else "U. S. Geological Survey Hawaii."  # info: set survey
    bits = [  # info: set bits
        "Earthquake.",  # info: "Earthquake." ,
        survey,  # info: survey ,
        f"Magnitude {mag_s}.",  # info: f" Magnitude { mag_s } . " ,
        f"{place}.",  # info: f" { place } . " ,
    ]  # info: ]
    try:  # info: try :
        bits.append(f"Depth {float(event.get('depth_km')):g} kilometers.")  # info: bits . append ( f" Depth { float
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        pass  # info: pass
    when = _fmt_time(event)  # info: set when
    if when != "time unknown":  # info: if when != "time unknown" :
        bits.append(when.replace(" HST", " Hawaiian Standard Time") + ".")  # info: bits . append ( when . replace (
    return " ".join(bits)  # info: return " " . join ( bits )


# ====================================================
# SECTION: function wanted
# What it does: wanted.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def wanted(feed: dict) -> list[dict]:  # info: def wanted
    events = feed.get("events") if isinstance(feed, dict) else None  # info: set events
    if not isinstance(events, list):  # info: if not isinstance ( events , list )
        return []  # info: return [ ]
    out = []  # info: set out
    for event in events:  # info: for event in events :
        if not isinstance(event, dict):  # info: if not isinstance ( event , dict )
            continue  # info: continue
        qid = str(event.get("id") or "").strip()  # info: set qid
        mag = _mag(event)  # info: set mag
        if qid and mag is not None and mag >= MIN_MAG:  # info: if qid and mag is not None and
            out.append(event)  # info: out . append ( event )
    return out  # info: return out


# ====================================================
# SECTION: function load_json
# What it does: load json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_json(path: Path, default: dict) -> dict:  # info: def load_json
    if not path.is_file():  # info: if not path . is_file ( ) :
        return dict(default)  # info: return dict ( default )
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return dict(default)  # info: return dict ( default )
    return data if isinstance(data, dict) else dict(default)  # info: return data if isinstance ( data , dict


# ====================================================
# SECTION: function save_json
# What it does: save json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_json(path: Path, data: dict) -> None:  # info: def save_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(".tmp")  # info: set tmp
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    tmp.replace(path)  # info: tmp . replace ( path )


# ====================================================
# SECTION: function tick
# What it does: Return posted texts. Live mode seeds once. Fixture mode posts new ids.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tick(feed: dict, state: dict, *, seed_first: bool, region: str = "Hawaii region") -> dict:  # info: def tick
    """Return posted texts. Live mode seeds once. Fixture mode posts new ids."""  # info: """Return posted texts. Live mode seeds once. Fixture mode posts new ids."""
    state = dict(state)  # info: set state
    seen = [str(x) for x in (state.get("seen") or []) if str(x).strip()]  # info: set seen
    seen_set = set(seen)  # info: set seen_set
    candidates = wanted(feed)  # info: set candidates
    if seed_first and not state.get("seeded"):  # info: if seed_first and not state . get (
        for event in candidates:  # info: for event in candidates :
            qid = str(event.get("id") or "")  # info: set qid
            if qid and qid not in seen_set:  # info: if qid and qid not in seen_set :
                seen.append(qid)  # info: seen . append ( qid )
                seen_set.add(qid)  # info: seen_set . add ( qid )
        state["seen"] = seen[-400:]  # info: state [ "seen" ] = seen [ -
        state["seeded"] = True  # info: state [ "seeded" ] = True
        state["posted"] = []  # info: state [ "posted" ] = [ ]
        state["notices"] = []  # info: state [ "notices" ] = [ ]
        return state  # info: return state
    notices = []  # info: set notices
    posted = []  # info: set posted
    for event in candidates:  # info: for event in candidates :
        qid = str(event.get("id") or "")  # info: set qid
        if not qid or qid in seen_set:  # info: if not qid or qid in seen_set :
            continue  # info: continue
        if len(posted) >= MAX_POSTS:  # info: if len ( posted ) >= MAX_POSTS :
            break  # info: break
        notices.append(format_quake(event, region))  # info: notices . append ( format_quake ( event , region )
        posted.append(qid)  # info: posted . append ( qid )
        seen.append(qid)  # info: seen . append ( qid )
        seen_set.add(qid)  # info: seen_set . add ( qid )
    state["seen"] = seen[-400:]  # info: state [ "seen" ] = seen [ -
    state["seeded"] = True  # info: state [ "seeded" ] = True
    state["posted"] = posted  # info: state [ "posted" ] = posted
    state["notices"] = notices  # info: state [ "notices" ] = notices
    return state  # info: return state


# ====================================================
# SECTION: function council_chat_id
# What it does: council chat id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def council_chat_id() -> str:  # info: def council_chat_id
    if not RELAY_CONF.is_file():  # info: if not RELAY_CONF . is_file ( ) :
        return ""  # info: return ""
    for line in RELAY_CONF.read_text(encoding="utf-8").splitlines():  # info: for line in RELAY_CONF . read_text ( encoding
        s = line.strip()  # info: set s
        if s.startswith("COUNCIL_CHAT_ID="):  # info: if s . startswith ( "COUNCIL_CHAT_ID=" ) :
            return s.split("=", 1)[1].strip()  # info: return s . split ( "=" , 1
    return ""  # info: return ""


# ====================================================
# SECTION: function sandbox_chat_id
# What it does: Read SANDBOX_CHAT_ID from relay.conf. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sandbox_chat_id() -> str:  # info: def sandbox_chat_id
    if not RELAY_CONF.is_file():  # info: if not RELAY_CONF . is_file ( ) :
        return ""  # info: return ""
    for line in RELAY_CONF.read_text(encoding="utf-8").splitlines():  # info: for line in RELAY_CONF . read_text ( encoding
        s = line.strip()  # info: set s
        if s.startswith("SANDBOX_CHAT_ID="):  # info: if s . startswith ( "SANDBOX_CHAT_ID=" ) :
            return s.split("=", 1)[1].strip()  # info: return s . split ( "=" , 1
    return ""  # info: return ""


# ====================================================
# SECTION: function dest_chat_id
# What it does: Live council chat, or the sandbox when RR_TELEGRAM_DEST=sandbox. Does not send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def dest_chat_id() -> str:  # info: def dest_chat_id
    if os.environ.get("RR_TELEGRAM_DEST", "").strip().lower() == "sandbox":  # info: if os . environ . get ( "RR_TELEGRAM_DEST"
        return sandbox_chat_id()  # info: return sandbox_chat_id ( )
    return council_chat_id()  # info: return council_chat_id ( )


# ====================================================
# SECTION: function maybe_send
# What it does: Telegram send stays off unless RR_COUNCIL_QUAKE_SEND=1. Never prints the token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def maybe_send(text: str) -> dict:  # info: def maybe_send
    """Telegram send stays off unless RR_COUNCIL_QUAKE_SEND=1. Never prints the token."""  # info: """Telegram send stays off unless RR_COUNCIL_QUAKE_SEND=1. Never prints the token."""
    if not send_enabled():  # info: if not send_enabled ( ) :
        return {"ok": True, "sent": False, "detail": "send gate off"}  # info: return { "ok" : True , "sent" :
    from envload import carly_token  # info: from envload import carly_token

    token = carly_token()  # info: set token
    chat = dest_chat_id()  # info: set chat
    if not token or not chat or not text.strip():  # info: if not token or not chat or not
        return {"ok": False, "sent": False, "detail": "missing token, chat, or text"}  # info: return { "ok" : False , "sent" :
    body = json.dumps(  # info: set body
        {"chat_id": chat, "text": text[:3900], "disable_web_page_preview": True}  # info: { "chat_id" : chat , "text" : text
    ).encode()  # info: ) . encode ( )
    import urllib.request  # info: import urllib . request

    req = urllib.request.Request(  # info: set req
        f"https://api.telegram.org/bot{token}/sendMessage",  # info: f" https://api.telegram.org/bot { token } /sendMessage " ,
        data=body,  # info: set data
        headers={"Content-Type": "application/json"},  # info: set headers
        method="POST",  # info: set method
    )  # info: )
    with urllib.request.urlopen(req, timeout=30) as response:  # info: with urllib . request . urlopen ( req
        payload = json.load(response)  # info: set payload
    return {"ok": bool(payload.get("ok")), "sent": bool(payload.get("ok")), "detail": "sendMessage"}  # info: return { "ok" : bool ( payload .


# ====================================================
# SECTION: function append_log
# What it does: append log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def append_log(path: Path, row: dict) -> None:  # info: def append_log
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    with path.open("a", encoding="utf-8") as fh:  # info: with path . open ( "a" , encoding
        fh.write(json.dumps(row, sort_keys=True) + "\n")  # info: fh . write ( json . dumps (


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run(feed_path: Path, seen_path: Path, log_path: Path, *, seed_first: bool, region: str = "Hawaii region", last_name: str = LAST_NAME) -> dict:  # info: def run
    feed = load_json(feed_path, {})  # info: set feed
    state = load_json(seen_path, {"seen": [], "seeded": False})  # info: set state
    out = tick(feed, state, seed_first=seed_first, region=region)  # info: set out
    notices = list(out.get("notices") or [])  # info: set notices
    deliveries = []  # info: set deliveries
    for text in notices:  # info: for text in notices :
        deliveries.append(maybe_send(text))  # info: deliveries . append ( maybe_send ( text )
    spoken = []  # info: set spoken
    if wav_enabled() and notices:  # info: if wav_enabled ( ) and notices :
        spoken.append("wav gate on; render not called in this dry path")  # info: spoken . append ( "wav gate on; render not called in this dry path" )
    row = {  # info: set row
        "at": datetime.now().astimezone().isoformat(timespec="seconds"),  # info: "at" : datetime . now ( ) .
        "seeded": bool(out.get("seeded")),  # info: "seeded" : bool ( out . get (
        "posted": out.get("posted") or [],  # info: "posted" : out . get ( "posted" )
        "count": len(notices),  # info: "count" : len ( notices ) ,
        "sent": any(d.get("sent") for d in deliveries),  # info: "sent" : any ( d . get (
        "wav": bool(spoken),  # info: "wav" : bool ( spoken ) ,
    }  # info: }
    save_json(seen_path, {"seen": out.get("seen") or [], "seeded": True, "last_posted": out.get("posted") or []})  # info: call save_json
    last_path = seen_path.parent / last_name  # info: set last_path
    save_json(last_path, {**row, "notices": notices})  # info: call save_json
    append_log(log_path, row)  # info: call append_log
    for text in notices:  # info: for text in notices :
        print(text)  # info: call print
        print("---")  # info: call print
    print(json.dumps({"count": len(notices), "posted": out.get("posted") or [], "seeded_only": seed_first and not notices}))  # info: call print
    return row  # info: return row


# ====================================================
# SECTION: function self_test
# What it does: Empty seen list plus one M2.4 prints one notice; the second run prints zero.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def self_test() -> int:  # info: def self_test
    """Empty seen list plus one M2.4 prints one notice; the second run prints zero."""  # info: """Empty seen list plus one M2.4 prints one notice; the second run prints zero."""
    event = {  # info: set event
        "id": "hv-test-1",  # info: "id" : "hv-test-1" ,
        "mag": 2.4,  # info: "mag" : 2.4 ,
        "place": "5 km SSW of Pahala, Hawaii",  # info: "place" : "5 km SSW of Pahala, Hawaii" ,
        "time_hst": "2026-09-29T13:16:14-10:00",  # info: "time_hst" : "2026-09-29T13:16:14-10:00" ,
        "depth_km": 26.02,  # info: "depth_km" : 26.02 ,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/hv-test-1",  # info: "url" : "https://earthquake.usgs.gov/earthquakes/eventpage/hv-test-1" ,
    }  # info: }
    feed = {"events": [event, {"id": "hv-small", "mag": 1.2, "place": "too small"}]}  # info: set feed
    with tempfile.TemporaryDirectory(prefix="council-quake-") as tmp:  # info: with tempfile . TemporaryDirectory ( prefix = "council-quake-"
        root = Path(tmp)  # info: set root
        feed_path = root / "feed.json"  # info: set feed_path
        seen_path = root / "seen.json"  # info: set seen_path
        log_path = root / "log.jsonl"  # info: set log_path
        feed_path.write_text(json.dumps(feed), encoding="utf-8")  # info: feed_path . write_text ( json . dumps (
        seen_path.write_text(json.dumps({"seen": [], "seeded": True}), encoding="utf-8")  # info: seen_path . write_text ( json . dumps (
        os.environ["RR_COUNCIL_QUAKE_SEND"] = "0"  # info: os . environ [ "RR_COUNCIL_QUAKE_SEND" ] = "0"
        os.environ["RR_COUNCIL_QUAKE_WAV"] = "0"  # info: os . environ [ "RR_COUNCIL_QUAKE_WAV" ] = "0"
        first = run(feed_path, seen_path, log_path, seed_first=False)  # info: set first
        if first["count"] != 1 or first["posted"] != ["hv-test-1"] or first["sent"]:  # info: if first [ "count" ] != 1 or
            print("FAIL first run", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        last = json.loads((seen_path.parent / LAST_NAME).read_text(encoding="utf-8"))  # info: set last
        notice = "\n".join(last.get("notices") or [])  # info: set notice
        if "Earthquake — USGS (Hawaii region)" not in notice or "M 2.4 · 5 km SSW of Pahala, Hawaii" not in notice:  # info: if "Earthquake — USGS (Hawaii region)" not in notice or "M 2.4 · 5 km SSW of Pahala, Hawaii" not in notice :
            print("FAIL notice body", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if "hv-small" in notice:  # info: if "hv-small" in notice :
            print("FAIL below-M2 included", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        second = run(feed_path, seen_path, log_path, seed_first=False)  # info: set second
        if second["count"] != 0 or second["posted"]:  # info: if second [ "count" ] != 0 or
            print("FAIL second run", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if HAWAII.exists() and "hv-test-1" in HAWAII.read_text(encoding="utf-8"):  # info: if HAWAII . exists ( ) and "hv-test-1"
            print("FAIL live quake file touched", file=sys.stderr)  # info: call print
            return 1  # info: return 1
    world = format_quake({"id": "us-test-1", "mag": 5.0, "place": "south of the Fiji Islands"}, "worldwide")  # info: set world
    if "Earthquake — USGS (worldwide)" not in world or "M 5.0" not in world:  # info: if "Earthquake — USGS (worldwide)" not in world or "M 5.0" not in world :
        print("FAIL worldwide notice", file=sys.stderr)  # info: call print
        return 1  # info: return 1
    seeded = tick({"events": [event]}, {"seen": [], "seeded": False}, seed_first=True, region="worldwide")  # info: set seeded
    if seeded.get("notices") or seeded.get("posted"):  # info: if seeded . get ( "notices" ) or seeded . get ( "posted" ) :
        print("FAIL first seed posted", file=sys.stderr)  # info: call print
        return 1  # info: return 1
    print("PASS council quake dry-run")  # info: call print
    return 0  # info: return 0


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    if "--self-test" in argv:  # info: if "--self-test" in argv :
        return self_test()  # info: return self_test ( )
    if "--feed" in argv:  # info: if "--feed" in argv :
        feed = Path(argv[argv.index("--feed") + 1])  # info: set feed
        seen = Path(argv[argv.index("--seen") + 1]) if "--seen" in argv else DATA / SEEN_NAME  # info: set seen
        log_path = Path(argv[argv.index("--log") + 1]) if "--log" in argv else LOG_DIR / LOG_NAME  # info: set log_path
        if not feed.is_file():  # info: if not feed . is_file ( ) :
            print(f"No data: {feed}", file=sys.stderr)  # info: call print
            return 2  # info: return 2
        run(feed, seen, log_path, seed_first=False, region="Hawaii region")  # info: call run
        return 0  # info: return 0
    if not HAWAII.is_file() and not GLOBAL.is_file():  # info: if not HAWAII . is_file ( ) and not GLOBAL . is_file ( ) :
        print(f"No data: {HAWAII}", file=sys.stderr)  # info: call print
        return 2  # info: return 2
    if HAWAII.is_file():  # info: if HAWAII . is_file ( ) :
        run(HAWAII, DATA / SEEN_NAME, LOG_DIR / LOG_NAME, seed_first=True, region="Hawaii region", last_name=LAST_NAME)  # info: call run
    if GLOBAL.is_file():  # info: if GLOBAL . is_file ( ) :
        run(GLOBAL, DATA / "seen-global.json", LOG_DIR / LOG_NAME, seed_first=True, region="worldwide", last_name="last-global.json")  # info: call run
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv[1:]))  # info: raise SystemExit ( main ( sys . argv
