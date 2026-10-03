# ==============================================================================
# FILE: Communications/BruceStats/scripts/bruce_stats.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Bruce measured desk sample from live host and EcoFlow last files.

Once per hour slot at 07, 15, and 21 HST. Dry-run by default: no Telegram,
no token load. Never invents watts. A missing last file is DOWN.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]  # info: set ROOT
SCRIPTS = Path(__file__).resolve().parent  # info: set SCRIPTS
PACIFIC = ROOT.parents[1]  # info: set PACIFIC
DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")  # info: set DB
HOST_LAST = DB / "System" / "last" / "host_current.json"  # info: set HOST_LAST
ENERGY = DB / "Energy"  # info: set ENERGY
DATA = DB / "Communications" / "BruceStats"  # info: set DATA
LOG_DIR = DB / "Logs" / "Communications" / "BruceStats"  # info: set LOG_DIR
SLOT_NAME = "slot.json"  # info: set SLOT_NAME
TEXT_NAME = "last-text.txt"  # info: set TEXT_NAME
LOG_NAME = "bruce-stats.jsonl"  # info: set LOG_NAME
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HOURS = (7, 15, 21)  # info: set HOURS
PACKS = (("delta2", "DELTA 2"), ("river2pro", "RIVER 2 PRO"))  # info: set PACKS
# ====================================================
# SECTION: WATT_KEYS
# What it does: Set WATT_KEYS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
WATT_KEYS = (  # info: set WATT_KEYS
    ("ac_output_power", "AC out"),  # info: call (
    ("solar_input_power", "solar"),  # info: call (
    ("ac_input_power", "AC in"),  # info: call (
    ("usbc_output_power", "USB-C out"),  # info: call (
)  # info: )

if str(SCRIPTS) not in sys.path:  # info: if str ( SCRIPTS ) not in sys
    sys.path.insert(0, str(SCRIPTS))  # info: sys . path . insert ( 0 ,


# ====================================================
# SECTION: function send_enabled
# What it does: send enabled.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def send_enabled() -> bool:  # info: def send_enabled
    return os.environ.get("RR_BRUCE_STATS_SEND", "0").strip() == "1"  # info: return os . environ . get ( "RR_BRUCE_STATS_SEND"


# ====================================================
# SECTION: function load_json
# What it does: load json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_json(path: Path):  # info: def load_json
    if not path.is_file():  # info: if not path . is_file ( ) :
        return None  # info: return None
    try:  # info: try :
        data = json.loads(path.read_text(encoding="utf-8"))  # info: set data
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return None  # info: return None
    return data if isinstance(data, dict) else None  # info: return data if isinstance ( data , dict


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
# SECTION: function _num
# What it does:  num.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _num(value):  # info: def _num
    if isinstance(value, bool) or not isinstance(value, (int, float)):  # info: if isinstance ( value , bool ) or
        return None  # info: return None
    return value  # info: return value


# ====================================================
# SECTION: function _field
# What it does:  field.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _field(fields: dict, name: str):  # info: def _field
    row = fields.get(name)  # info: set row
    if not isinstance(row, dict):  # info: if not isinstance ( row , dict )
        return None  # info: return None
    return _num(row.get("value"))  # info: return _num ( row . get ( "value"


# ====================================================
# SECTION: function host_line
# What it does: host line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_line(snap) -> str:  # info: def host_line
    if not isinstance(snap, dict):  # info: if not isinstance ( snap , dict )
        return "Host: DOWN"  # info: return "Host: DOWN"
    fields = snap.get("fields") if isinstance(snap.get("fields"), dict) else {}  # info: set fields
    bits = []  # info: set bits
    at = str(snap.get("at") or "").strip()  # info: set at
    if at:  # info: if at :
        bits.append(f"last {at}")  # info: bits . append ( f" last { at
    cpu = _field(fields, "cpu_percent")  # info: set cpu
    mem = _field(fields, "mem_used_percent")  # info: set mem
    load1 = _field(fields, "load1")  # info: set load1
    if cpu is not None:  # info: if cpu is not None :
        bits.append(f"CPU {cpu:g}%")  # info: bits . append ( f" CPU { cpu
    if mem is not None:  # info: if mem is not None :
        bits.append(f"RAM {mem:g}%")  # info: bits . append ( f" RAM { mem
    if load1 is not None:  # info: if load1 is not None :
        bits.append(f"load {load1:g}")  # info: bits . append ( f" load { load1
    if not bits:  # info: if not bits :
        return "Host: DOWN"  # info: return "Host: DOWN"
    return "Host: " + ", ".join(bits)  # info: return "Host: " + ", " . join ( bits


# ====================================================
# SECTION: function pack_phrase
# What it does: pack phrase.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pack_phrase(label: str, soc, watts) -> str:  # info: def pack_phrase
    if soc is None and watts is None:  # info: if soc is None and watts is None
        return f"{label}: DOWN"  # info: return f" { label } : DOWN "
    bits = []  # info: set bits
    soc_at = ""  # info: set soc_at
    if isinstance(soc, dict):  # info: if isinstance ( soc , dict ) :
        level = _num(soc.get("soc"))  # info: set level
        soc_at = str(soc.get("at") or "").strip()  # info: set soc_at
        if level is not None:  # info: if level is not None :
            bit = f"SOC {level:g}%"  # info: set bit
            if soc_at:  # info: if soc_at :
                bit += f" at {soc_at}"  # info: set bit
            bits.append(bit)  # info: bits . append ( bit )
        elif soc_at:  # info: elif soc_at :
            bits.append(f"at {soc_at}")  # info: bits . append ( f" at { soc_at
    else:  # info: else :
        bits.append("SOC DOWN")  # info: bits . append ( "SOC DOWN" )
    if isinstance(watts, dict):  # info: if isinstance ( watts , dict ) :
        for key, name in WATT_KEYS:  # info: for key , name in WATT_KEYS :
            amount = _num(watts.get(key))  # info: set amount
            if amount is not None:  # info: if amount is not None :
                bits.append(f"{name} {amount:g} W")  # info: bits . append ( f" { name }
        watt_at = str(watts.get("at") or "").strip()  # info: set watt_at
        if watt_at and not soc_at:  # info: if watt_at and not soc_at :
            bits.append(f"at {watt_at}")  # info: bits . append ( f" at { watt_at
    else:  # info: else :
        bits.append("watts DOWN")  # info: bits . append ( "watts DOWN" )
    if not bits:  # info: if not bits :
        return f"{label}: DOWN"  # info: return f" { label } : DOWN "
    return f"{label} " + ", ".join(bits)  # info: return f" { label } " +


# ====================================================
# SECTION: function ecoflow_line
# What it does: ecoflow line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ecoflow_line(energy: Path) -> str:  # info: def ecoflow_line
    parts = []  # info: set parts
    for alias, label in PACKS:  # info: for alias , label in PACKS :
        parts.append(  # info: parts . append (
            pack_phrase(  # info: call pack_phrase
                label,  # info: label ,
                load_json(energy / "soc" / f"{alias}_current.json"),  # info: call load_json
                load_json(energy / "watts" / f"{alias}_current.json"),  # info: call load_json
            )  # info: )
        )  # info: )
    return "EcoFlow: " + " | ".join(parts)  # info: return "EcoFlow: " + " | " . join ( parts


# ====================================================
# SECTION: function build_text
# What it does: build text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_text(host_path: Path, energy: Path) -> str:  # info: def build_text
    return (  # info: return (
        "Desk sample (measured)\n"  # info: "Desk sample (measured)\n"
        f"{host_line(load_json(host_path))}\n"  # info: f" { host_line ( load_json ( host_path )
        f"{ecoflow_line(energy)}\n"  # info: f" { ecoflow_line ( energy ) } \n
        "\n"  # info: "\n"
        "Bruce Monitor"  # info: "Bruce Monitor"
    )  # info: )


# ====================================================
# SECTION: function slot_key
# What it does: slot key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def slot_key(now: datetime) -> str:  # info: def slot_key
    return f"{now.strftime('%Y-%m-%d')}-{now.hour}"  # info: return f" { now . strftime ( '%Y-%m-%d'


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
# SECTION: function deliver
# What it does: Telegram stays off unless RR_BRUCE_STATS_SEND=1. Never prints the token. Chat id comes from dest_chat_id (sandbox when RR_TELEGRAM_DEST=sandbox). Does not call Carly maybe_send.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def deliver(text: str) -> dict:  # info: def deliver
    """Telegram stays off unless RR_BRUCE_STATS_SEND=1. Never prints the token.

    Chat id comes from dest_chat_id. RR_TELEGRAM_DEST=sandbox selects the sandbox.
    This function does not call Carly maybe_send.
    """
    if not send_enabled():  # info: if not send_enabled ( ) :
        return {"ok": True, "sent": False, "detail": "send gate off"}  # info: return { "ok" : True , "sent" :
    quake_scripts = PACIFIC / "Communications" / "CouncilQuake" / "scripts"  # info: set quake_scripts
    if not (quake_scripts / "quake_posts.py").is_file():  # info: if not ( quake_scripts / "quake_posts.py" ) .
        return {"ok": False, "sent": False, "detail": "Council quake Telegram posts folder missing"}  # info: return { "ok" : False , "sent" :
    if str(quake_scripts) not in sys.path:  # info: if str ( quake_scripts ) not in sys
        sys.path.insert(0, str(quake_scripts))  # info: sys . path . insert ( 0 ,
    from envload import bruce_token  # info: from envload import bruce_token
    from quake_posts import dest_chat_id  # info: from quake_posts import dest_chat_id

    token = bruce_token()  # info: set token
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
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run(  # info: def run
    host_path: Path,  # info: set host_path
    energy: Path,  # info: set energy
    data_dir: Path,  # info: set data_dir
    log_path: Path,  # info: set log_path
    *,  # info: * ,
    force: bool = False,  # info: set force
    now: datetime | None = None,  # info: set now
) -> dict:  # info: ) -> dict :
    now = now or datetime.now(HST)  # info: set now
    slot = slot_key(now)  # info: set slot
    slot_path = data_dir / SLOT_NAME  # info: set slot_path
    prior = load_json(slot_path) or {}  # info: set prior
    if not force and now.hour not in HOURS:  # info: if not force and now . hour not
        row = {"ok": True, "skipped": True, "detail": "off slot", "slot": slot, "sent": False}  # info: set row
        print(json.dumps(row))  # info: call print
        return row  # info: return row
    if not force and prior.get("last_slot") == slot:  # info: if not force and prior . get (
        row = {"ok": True, "skipped": True, "detail": "already", "slot": slot, "sent": False}  # info: set row
        print(json.dumps(row))  # info: call print
        return row  # info: return row
    text = build_text(host_path, energy)  # info: set text
    delivery = deliver(text)  # info: set delivery
    save_json(  # info: call save_json
        slot_path,  # info: slot_path ,
        {  # info: {
            "last_slot": slot,  # info: "last_slot" : slot ,
            "sent": bool(delivery.get("sent")),  # info: "sent" : bool ( delivery . get (
            "updated": now.isoformat(timespec="seconds"),  # info: "updated" : now . isoformat ( timespec =
        },  # info: } ,
    )  # info: )
    text_path = data_dir / TEXT_NAME  # info: set text_path
    text_path.parent.mkdir(parents=True, exist_ok=True)  # info: text_path . parent . mkdir ( parents =
    text_path.write_text(text + "\n", encoding="utf-8")  # info: text_path . write_text ( text + "\n" ,
    row = {  # info: set row
        "at": now.isoformat(timespec="seconds"),  # info: "at" : now . isoformat ( timespec =
        "detail": delivery.get("detail"),  # info: "detail" : delivery . get ( "detail" )
        "ok": bool(delivery.get("ok")),  # info: "ok" : bool ( delivery . get (
        "sent": bool(delivery.get("sent")),  # info: "sent" : bool ( delivery . get (
        "skipped": False,  # info: "skipped" : False ,
        "slot": slot,  # info: "slot" : slot ,
    }  # info: }
    append_log(log_path, row)  # info: call append_log
    print(text)  # info: call print
    print(json.dumps({"sent": row["sent"], "slot": slot, "detail": row["detail"]}))  # info: call print
    return row  # info: return row


# ====================================================
# SECTION: function self_test
# What it does: Fixture last files print the desk sample, write a slot, and do not post.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def self_test() -> int:  # info: def self_test
    """Fixture last files print the desk sample, write a slot, and do not post."""  # info: """Fixture last files print the desk sample, write a slot, and do not post."""
    import urllib.request  # info: import urllib . request

    def _forbid(*_args, **_kwargs):  # info: def _forbid
        raise AssertionError("HTTP is not allowed on the dry run")  # info: raise AssertionError ( "HTTP is not allowed on the dry run" )

    urllib.request.urlopen = _forbid  # info: urllib . request . urlopen = _forbid
    os.environ["RR_BRUCE_STATS_SEND"] = "0"  # info: os . environ [ "RR_BRUCE_STATS_SEND" ] = "0"
    host = {  # info: set host
        "at": "2026-09-30T17:18:00Z",  # info: "at" : "2026-09-30T17:18:00Z" ,
        "fields": {  # info: "fields" : {
            "cpu_percent": {"value": 12.5},  # info: "cpu_percent" : { "value" : 12.5 } ,
            "mem_used_percent": {"value": 40},  # info: "mem_used_percent" : { "value" : 40 } ,
            "load1": {"value": 0.5},  # info: "load1" : { "value" : 0.5 } ,
        },  # info: } ,
    }  # info: }
    when = datetime(2026, 9, 30, 7, 18, tzinfo=HST)  # info: set when
    with tempfile.TemporaryDirectory(prefix="bruce-stats-") as tmp:  # info: with tempfile . TemporaryDirectory ( prefix = "bruce-stats-"
        root = Path(tmp)  # info: set root
        host_path = root / "host_current.json"  # info: set host_path
        energy = root / "Energy"  # info: set energy
        data = root / "data"  # info: set data
        log_path = root / "bruce-stats.jsonl"  # info: set log_path
        host_path.write_text(json.dumps(host), encoding="utf-8")  # info: host_path . write_text ( json . dumps (
        (energy / "soc").mkdir(parents=True)  # info: call (
        (energy / "watts").mkdir(parents=True)  # info: call (
        (energy / "soc" / "delta2_current.json").write_text(  # info: call (
            json.dumps({"soc": 4, "at": "2026-09-30T07:18:00-10:00"}), encoding="utf-8"  # info: json . dumps ( { "soc" : 4
        )  # info: )
        (energy / "watts" / "delta2_current.json").write_text(  # info: call (
            json.dumps({"ac_output_power": 69, "solar_input_power": 0}), encoding="utf-8"  # info: json . dumps ( { "ac_output_power" : 69
        )  # info: )
        (energy / "soc" / "river2pro_current.json").write_text(  # info: call (
            json.dumps({"soc": 1, "at": "2026-09-30T07:18:00-10:00"}), encoding="utf-8"  # info: json . dumps ( { "soc" : 1
        )  # info: )
        first = run(host_path, energy, data, log_path, now=when)  # info: set first
        text = (data / TEXT_NAME).read_text(encoding="utf-8")  # info: set text
        if "Desk sample (measured)" not in text or not text.startswith("Desk sample"):  # info: if "Desk sample (measured)" not in text or not text
            print("FAIL heading", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if "Host: last 2026-09-30T17:18:00Z, CPU 12.5%, RAM 40%, load 0.5" not in text:  # info: if "Host: last 2026-09-30T17:18:00Z, CPU 12.5%, RAM 40%, load 0.5" not in text :
            print("FAIL host line", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if "EcoFlow: DELTA 2 SOC 4% at 2026-09-30T07:18:00-10:00, AC out 69 W, solar 0 W" not in text:  # info: if "EcoFlow: DELTA 2 SOC 4% at 2026-09-30T07:18:00-10:00, AC out 69 W, solar 0 W" not in text :
            print("FAIL ecoflow line", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if "RIVER 2 PRO SOC 1%" not in text or "watts DOWN" not in text:  # info: if "RIVER 2 PRO SOC 1%" not in text or "watts DOWN" not
            print("FAIL missing watts marked DOWN", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        if "Bruce Monitor" not in text:  # info: if "Bruce Monitor" not in text :
            print("FAIL signature", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        slot = json.loads((data / SLOT_NAME).read_text(encoding="utf-8"))  # info: set slot
        if slot.get("last_slot") != "2026-09-30-7" or slot.get("sent") or first.get("sent"):  # info: if slot . get ( "last_slot" ) !=
            print("FAIL slot", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        second = run(host_path, energy, data, log_path, now=when)  # info: set second
        if not second.get("skipped") or second.get("detail") != "already":  # info: if not second . get ( "skipped" )
            print("FAIL second run", file=sys.stderr)  # info: call print
            return 1  # info: return 1
        off = run(host_path, energy, data, log_path, now=when.replace(hour=8), force=False)  # info: set off
        if off.get("detail") != "off slot":  # info: if off . get ( "detail" ) !=
            print("FAIL off slot", file=sys.stderr)  # info: call print
            return 1  # info: return 1
    print("PASS bruce stats dry-run")  # info: call print
    return 0  # info: return 0


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    if "--self-test" in argv:  # info: if "--self-test" in argv :
        return self_test()  # info: return self_test ( )
    host = HOST_LAST  # info: set host
    energy = ENERGY  # info: set energy
    data = DATA  # info: set data
    log_path = LOG_DIR / LOG_NAME  # info: set log_path
    force = "--force" in argv  # info: set force
    if "--host" in argv:  # info: if "--host" in argv :
        host = Path(argv[argv.index("--host") + 1])  # info: set host
    if "--energy" in argv:  # info: if "--energy" in argv :
        energy = Path(argv[argv.index("--energy") + 1])  # info: set energy
    if "--data" in argv:  # info: if "--data" in argv :
        data = Path(argv[argv.index("--data") + 1])  # info: set data
    if "--log" in argv:  # info: if "--log" in argv :
        log_path = Path(argv[argv.index("--log") + 1])  # info: set log_path
    run(host, energy, data, log_path, force=force)  # info: call run
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main(sys.argv[1:]))  # info: raise SystemExit ( main ( sys . argv
