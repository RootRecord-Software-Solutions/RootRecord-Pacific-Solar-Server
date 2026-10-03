# ==============================================================================
# FILE: Reports/Economy-Brief/scripts/economy_brief.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Daily economy brief markdown (G1 economy-brief).

Writes Database Reports/Economy-Brief/economy-brief-YYYY-MM-DD.md from a
MySQL desk-facts snapshot plus Geology Volcanoes/Hawaii/kilauea-last.json.
Gold stays in-game. The file never uses a dollar sign.

Council persona prompts are not used. This script does not build that Folder.

Night sleep: if System/NightSleep/scripts/night_sleep.py exists, call should_run
on a live run. A missing Folder means not sleeping. --dry-run still writes.

Discord is not called. --send refuses unless RR_ECONOMY_BRIEF_SEND=1, and even
then this script does not post. A live post needs a separate sign-off.

  python3 economy_brief.py --fixture snap.json --dry-run
  python3 economy_brief.py
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[2]  # info: set PACIFIC
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
OUT_DIR = DB / "Reports" / "Economy-Brief"  # info: set OUT_DIR
LAST = OUT_DIR / "last.json"  # info: set LAST
LOG = DB / "Logs" / "Reports" / "Economy-Brief" / "economy-brief.jsonl"  # info: set LOG
KILA = DB / "Geology" / "Volcanoes" / "Hawaii" / "kilauea-last.json"  # info: Hawaiʻi volcano bank
FACTS_LAST = DB / "System" / "MysqlDesk" / "facts-last.json"  # info: set FACTS_LAST
MYSQL = PACIFIC / "System" / "MysqlDesk" / "scripts" / "mysql_desk.py"  # info: set MYSQL
GATE = PACIFIC / "System" / "NightSleep" / "scripts" / "night_sleep.py"  # info: set GATE
JOB_ID = "reports_economy_brief"  # info: set JOB_ID
NOTE = "Gold never converts to dollars."  # info: set NOTE


# ====================================================
# SECTION: function now
# What it does: now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> datetime:  # info: def now
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function _load
# What it does:  load.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load(path: Path):  # info: def _load
    spec = importlib.util.spec_from_file_location(path.stem, path)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader
        return None  # info: return None
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    return mod  # info: return mod


# ====================================================
# SECTION: function night_skip
# What it does: None means run. A missing gate Folder is not sleeping.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def night_skip() -> str | None:  # info: def night_skip
    """None means run. A missing gate Folder is not sleeping."""  # info: """None means run. A missing gate Folder is not sleeping."""
    if not GATE.is_file():  # info: if not GATE . is_file ( ) :
        return None  # info: return None
    try:  # info: try :
        mod = _load(GATE)  # info: set mod
        fn = getattr(mod, "should_run", None) if mod else None  # info: set fn
        if not callable(fn):  # info: if not callable ( fn ) :
            return None  # info: return None
        try:  # info: try :
            allowed = fn(JOB_ID)  # info: set allowed
        except TypeError:  # info: except TypeError :
            allowed = fn()  # info: set allowed
    except Exception:  # info: except Exception :
        return None  # info: return None
    return None if allowed else "night_sleep"  # info: return None if allowed else "night_sleep"


# ====================================================
# SECTION: function kilauea
# What it does: kilauea.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def kilauea() -> tuple[str, float]:  # info: def kilauea
    alert, mult = "unknown", 1.0  # info: alert , mult = "unknown" , 1.0
    try:  # info: try :
        if not KILA.is_file():  # info: if not KILA . is_file ( ) :
            return alert, mult  # info: return alert , mult
        data = json.loads(KILA.read_text(encoding="utf-8"))  # info: set data
        if not isinstance(data, dict):  # info: if not isinstance ( data , dict )
            return alert, mult  # info: return alert , mult
        alert = str(data.get("alert_level") or data.get("alert") or alert)  # info: set alert
        mult = float(data.get("multiplier") or 1.0)  # info: set mult
    except Exception:  # info: except Exception :
        return "unknown", 1.0  # info: return "unknown" , 1.0
    return alert, mult  # info: return alert , mult


# ====================================================
# SECTION: function empty_snap
# What it does: empty snap.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def empty_snap() -> dict:  # info: def empty_snap
    return {  # info: return {
        "ok": False,  # info: "ok" : False ,
        "wallets": 0,  # info: "wallets" : 0 ,
        "positive_gold": 0,  # info: "positive_gold" : 0 ,
        "total_gold": 0,  # info: "total_gold" : 0 ,
        "bonds_count": 0,  # info: "bonds_count" : 0 ,
        "bonds_principal": 0,  # info: "bonds_principal" : 0 ,
        "error": "no-snapshot",  # info: "error" : "no-snapshot" ,
    }  # info: }


# ====================================================
# SECTION: function load_snapshot
# What it does: load snapshot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_snapshot(fixture: Path | None, dry: bool) -> dict:  # info: def load_snapshot
    if fixture is not None:  # info: if fixture is not None :
        data = json.loads(fixture.read_text(encoding="utf-8"))  # info: set data
        if not isinstance(data, dict):  # info: if not isinstance ( data , dict )
            raise SystemExit("fixture must be a JSON object")  # info: raise SystemExit ( "fixture must be a JSON object" )
        return data  # info: return data
    if dry and FACTS_LAST.is_file():  # info: if dry and FACTS_LAST . is_file ( )
        data = json.loads(FACTS_LAST.read_text(encoding="utf-8"))  # info: set data
        if isinstance(data, dict):  # info: if isinstance ( data , dict ) :
            return data  # info: return data
    if dry or not MYSQL.is_file():  # info: if dry or not MYSQL . is_file (
        return empty_snap()  # info: return empty_snap ( )
    mod = _load(MYSQL)  # info: set mod
    fn = getattr(mod, "facts", None) if mod else None  # info: set fn
    if not callable(fn):  # info: if not callable ( fn ) :
        snap = empty_snap()  # info: set snap
        snap["error"] = "mysql-desk-facts-missing"  # info: snap [ "error" ] = "mysql-desk-facts-missing"
        return snap  # info: return snap
    snap = fn()  # info: set snap
    return snap if isinstance(snap, dict) else empty_snap()  # info: return snap if isinstance ( snap , dict


# ====================================================
# SECTION: function brief_markdown
# What it does: brief markdown.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def brief_markdown(snap: dict, t: datetime, alert: str, mult: float) -> str:  # info: def brief_markdown
    stamp = t.strftime("%Y-%m-%d")  # info: set stamp
    lines = [  # info: set lines
        f"# Economy brief — {stamp} HST",
        "",  # info: "" ,
        f"Generated {t.isoformat()}",  # info: f" Generated { t . isoformat ( )
        "",  # info: "" ,
        "## Live MySQL snapshot",
        f"- ok: `{snap.get('ok')}`",  # info: f" - ok: ` { snap . get ( 'ok'
        f"- wallets: `{snap.get('wallets')}`",  # info: f" - wallets: ` { snap . get ( 'wallets'
        f"- circulating (+) gold: `{snap.get('positive_gold')}` g",  # info: f" - circulating (+) gold: ` { snap . get ( 'positive_gold'
        f"- net sum gold: `{snap.get('total_gold')}` g",  # info: f" - net sum gold: ` { snap . get ( 'total_gold'
        f"- bonds outstanding: `{snap.get('bonds_count')}` / principal `{snap.get('bonds_principal')}` g",  # info: f" - bonds outstanding: ` { snap . get ( 'bonds_count'
        f"- Kīlauea alert: `{alert}` · multiplier `{mult}`",  # info: f" - Kīlauea alert: ` { alert } ` · multiplier ` { mult
        "",  # info: "" ,
        "## Notes",
        "- Sourced from Shockbyte `root_economy_balances` (local mirror fallback).",  # info: "- Sourced from Shockbyte `root_economy_balances` (local mirror fallback)." ,
        f"- {NOTE}",  # info: f" - { NOTE } " ,
        "",  # info: "" ,
    ]  # info: ]
    text = "\n".join(lines)  # info: set text
    if "$" in text:  # info: if "$" in text :
        raise SystemExit("brief contained a dollar sign")  # info: raise SystemExit ( "brief contained a dollar sign" )
    return text  # info: return text


# ====================================================
# SECTION: function discord_card
# What it does: Old #automations card. Composed only. This function does not post it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def discord_card(snap: dict, t: datetime, alert: str, mult: float) -> str:  # info: def discord_card
    """Old #automations card. Composed only. This function does not post it."""
    now_hst = t.strftime("%Y-%m-%d %H:%M HST")  # info: set now_hst
    if not snap.get("ok"):  # info: if not snap . get ( "ok" )
        body = (  # info: set body
            f"**Player economy** — {now_hst}\n"  # info: f" **Player economy** — { now_hst } \n "
            f"MySQL snapshot failed: `{snap.get('error') or 'unknown'}`"  # info: f" MySQL snapshot failed: ` { snap . get ( 'error'
        )  # info: )
    else:  # info: else :
        body = (  # info: set body
            f"**Player economy (live MySQL)** — {now_hst}\n"  # info: f" **Player economy (live MySQL)** — { now_hst } \n "
            f"Wallets: **{snap.get('wallets')}** · "  # info: f" Wallets: ** { snap . get ( 'wallets'
            f"Circulating (+): **{snap.get('positive_gold')} g** · "  # info: f" Circulating (+): ** { snap . get ( 'positive_gold'
            f"Net sum: **{snap.get('total_gold')} g**\n"  # info: f" Net sum: ** { snap . get ( 'total_gold'
            f"Bonds outstanding: **{snap.get('bonds_count')}** · "  # info: f" Bonds outstanding: ** { snap . get ( 'bonds_count'
            f"Principal: **{snap.get('bonds_principal')} g**\n"  # info: f" Principal: ** { snap . get ( 'bonds_principal'
            "_Gold stays in-game. No USD conversion._"  # info: "_Gold stays in-game. No USD conversion._"
        )  # info: )
    if float(mult) != 1.0:  # info: if float ( mult ) != 1.0 :
        body += f"\nKīlauea {alert} — multiplier ×{float(mult):.1f}"  # info: set body
    return body[:1900]  # info: return body [ : 1900 ]


# ====================================================
# SECTION: function _arg
# What it does:  arg.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _arg(flag: str) -> Path | None:  # info: def _arg
    if flag not in sys.argv:  # info: if flag not in sys . argv :
        return None  # info: return None
    i = sys.argv.index(flag)  # info: set i
    if i + 1 >= len(sys.argv):  # info: if i + 1 >= len ( sys
        raise SystemExit(f"{flag} needs a path")  # info: raise SystemExit ( f" { flag } needs a path
    return Path(sys.argv[i + 1])  # info: return Path ( sys . argv [ i


# ====================================================
# SECTION: function write_outputs
# What it does: write outputs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_outputs(text: str, payload: dict, dry: bool) -> Path:  # info: def write_outputs
    OUT_DIR.mkdir(parents=True, exist_ok=True)  # info: OUT_DIR . mkdir ( parents = True ,
    day = payload["day"]  # info: set day
    out = OUT_DIR / f"economy-brief-{day}.md"  # info: set out
    out.write_text(text, encoding="utf-8")  # info: out . write_text ( text , encoding =
    payload["path"] = str(out)  # info: payload [ "path" ] = str ( out
    tmp = LAST.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, LAST)  # info: os . replace ( tmp , LAST )
    if not dry:  # info: if not dry :
        LOG.parent.mkdir(parents=True, exist_ok=True)  # info: LOG . parent . mkdir ( parents =
        with LOG.open("a", encoding="utf-8") as fh:  # info: with LOG . open ( "a" , encoding
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")  # info: fh . write ( json . dumps (
    return out  # info: return out


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    dry = "--dry-run" in sys.argv  # info: set dry
    send = "--send" in sys.argv  # info: set send
    fixture = _arg("--fixture")  # info: set fixture
    t = now()  # info: set t
    skip = None if dry else night_skip()  # info: set skip
    alert, mult = kilauea()  # info: alert , mult = kilauea ( )
    if skip:  # info: if skip :
        payload = {  # info: set payload
            "at": t.isoformat(),  # info: "at" : t . isoformat ( ) ,
            "job": JOB_ID,  # info: "job" : JOB_ID ,
            "day": t.strftime("%Y-%m-%d"),  # info: "day" : t . strftime ( "%Y-%m-%d" )
            "result": "skip",  # info: "result" : "skip" ,
            "detail": skip,  # info: "detail" : skip ,
            "dry_run": dry,  # info: "dry_run" : dry ,
            "posted": False,  # info: "posted" : False ,
        }  # info: }
        LAST.parent.mkdir(parents=True, exist_ok=True)  # info: LAST . parent . mkdir ( parents =
        LAST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: LAST . write_text ( json . dumps (
        print(json.dumps(payload))  # info: call print
        return 0  # info: return 0
    snap = load_snapshot(fixture, dry)  # info: set snap
    text = brief_markdown(snap, t, alert, mult)  # info: set text
    payload = {  # info: set payload
        "at": t.isoformat(),  # info: "at" : t . isoformat ( ) ,
        "job": JOB_ID,  # info: "job" : JOB_ID ,
        "day": t.strftime("%Y-%m-%d"),  # info: "day" : t . strftime ( "%Y-%m-%d" )
        "result": "dry-run" if dry else "wrote",  # info: "result" : "dry-run" if dry else "wrote" ,
        "ok": bool(snap.get("ok")),  # info: "ok" : bool ( snap . get (
        "wallets": snap.get("wallets"),  # info: "wallets" : snap . get ( "wallets" )
        "alert": alert,  # info: "alert" : alert ,
        "multiplier": mult,  # info: "multiplier" : mult ,
        "dry_run": dry,  # info: "dry_run" : dry ,
        "posted": False,  # info: "posted" : False ,
        "fixture": str(fixture) if fixture else None,  # info: "fixture" : str ( fixture ) if fixture
    }  # info: }
    out = write_outputs(text, payload, dry)  # info: set out
    if send:  # info: if send :
        card = discord_card(snap, t, alert, mult)  # info: set card
        if "$" in card:  # info: if "$" in card :
            print("send refused: card contained a dollar sign", file=sys.stderr)  # info: call print
            return 2  # info: return 2
        if os.environ.get("RR_ECONOMY_BRIEF_SEND", "0").strip() != "1":  # info: if os . environ . get ( "RR_ECONOMY_BRIEF_SEND"
            print("send refused: RR_ECONOMY_BRIEF_SEND is not 1", file=sys.stderr)  # info: call print
            return 2  # info: return 2
        print("send refused: Discord post is not signed off", file=sys.stderr)  # info: call print
        return 2  # info: return 2
    print(json.dumps({"result": payload["result"], "path": str(out), "posted": False}))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
