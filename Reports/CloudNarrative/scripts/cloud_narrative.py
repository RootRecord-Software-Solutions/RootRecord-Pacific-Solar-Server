# ==============================================================================
# FILE: Reports/CloudNarrative/scripts/cloud_narrative.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Optional cloud prose on the existing template reports. Does not replace them.

Default is a dry-run: write a prompt package and last.json. No HTTP.

  python3 cloud_narrative.py morning --dry-run
  python3 cloud_narrative.py morning|midday|late|merged|kilauea [--dry-run|--spend]

--spend calls the cloud API only when RR_CLOUD_NARRATIVE_SPEND=1 and XAI_API_KEY
is set. merged never calls the model; it copies today's morning narrative.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import re  # info: import re
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parents[2]  # info: set PACIFIC
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DATA = DB / "Reports" / "CloudNarrative"  # info: set DATA
LOG = DB / "Logs" / "Reports" / "CloudNarrative" / "cloud-narrative.jsonl"  # info: set LOG
TEMPLATES = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))  # info: set TEMPLATES
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
CHAT_URL = "https://api.x.ai/v1/chat/completions"  # info: set CHAT_URL
MODEL = "grok-3"  # info: set MODEL
THIN = 80  # info: set THIN

# ====================================================
# SECTION: TEMPLATE_FILE
# What it does: Set TEMPLATE_FILE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
TEMPLATE_FILE = {  # info: set TEMPLATE_FILE
    "morning": "morning_report_current.md",  # info: "morning" : "morning_report_current.md" ,
    "midday": "midday_report_current.md",  # info: "midday" : "midday_report_current.md" ,
    "late": "late_report_current.md",  # info: "late" : "late_report_current.md" ,
    "kilauea": "kilauea_report_current.md",  # info: "kilauea" : "kilauea_report_current.md" ,
}  # info: }
KINDS = ("morning", "midday", "late", "merged", "kilauea")  # info: set KINDS

sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
sys.path.insert(0, str(PACIFIC / "Media" / "Voice" / "scripts"))  # info: sys . path . insert ( 0 ,
import envload  # noqa: E402
from speech_scrub import scrub_speech  # noqa: E402

_WMO = re.compile(r"^\s*0{3}\s+")  # info: set _WMO


# ====================================================
# SECTION: function now
# What it does: now.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now() -> datetime:  # info: def now
    return datetime.now(HST).replace(microsecond=0)  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function measured
# What it does: measured.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def measured(text: str) -> str:  # info: def measured
    if "## Measured" in text:
        rest = text.split("## Measured", 1)[1]
        rest = re.split(r"\n## ", rest, maxsplit=1)[0]
        return rest.strip()  # info: return rest . strip ( )
    return text.strip()  # info: return text . strip ( )


# ====================================================
# SECTION: function scrub_nws
# What it does: Drop NWS product bodies. Short template lines stay.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def scrub_nws(text: str) -> str:  # info: def scrub_nws
    """Drop NWS product bodies. Short template lines stay."""  # info: """Drop NWS product bodies. Short template lines stay."""
    kept: list[str] = []  # info: set kept
    for line in (text or "").splitlines():  # info: for line in ( text or "" )
        low = line.lower()  # info: set low
        if "nws county spoken script" in low:  # info: if "nws county spoken script" in low :
            continue  # info: continue
        if ('"raw"' in low or '"description"' in low) and len(line) > 400:  # info: if ( '"raw"' in low or '"description"' in
            continue  # info: continue
        if _WMO.match(line):  # info: if _WMO . match ( line ) :
            continue  # info: continue
        if len(line) > 500 and any(k in low for k in (  # info: if len ( line ) > 500 and
            "national weather service", "hurricane local statement", "area forecast discussion",  # info: "national weather service" , "hurricane local statement" , "area forecast discussion" ,
        )):  # info: ) ) :
            continue  # info: continue
        kept.append(line)  # info: kept . append ( line )
    return "\n".join(kept).strip()  # info: return "\n" . join ( kept ) .


# ====================================================
# SECTION: function persona
# What it does: persona.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona(kind: str) -> str:  # info: def persona
    if kind == "kilauea":  # info: if kind == "kilauea" :
        return (  # info: return (
            "You are writing a short Kīlauea notice for easy audio readout. "  # info: "You are writing a short Kīlauea notice for easy audio readout. "
            "Use only the FACTS text. Alert levels, eruption state, or quake counts "  # info: "Use only the FACTS text. Alert levels, eruption state, or quake counts "
            "only if they are in FACTS. Advisory is not erupting. Under 180 words. "  # info: "only if they are in FACTS. Advisory is not erupting. Under 180 words. "
            "End with: End of status. Output only the report text."  # info: "End with: End of status. Output only the report text."
        )  # info: )
    return (  # info: return (
        "You are writing a short desk status for easy audio readout. "  # info: "You are writing a short desk status for easy audio readout. "
        "Numbers only from the FACTS block. If a hazard is not in FACTS, omit it. "  # info: "Numbers only from the FACTS block. If a hazard is not in FACTS, omit it. "
        "Off-grid only. Short sentences. End with: End of status. Output only the report text."  # info: "Off-grid only. Short sentences. End with: End of status. Output only the report text."
    )  # info: )


# ====================================================
# SECTION: function energy_windows
# What it does: Hour, day, week, and month lines from Energy/layers/periods.json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def energy_windows() -> str:  # info: def energy_windows
    if str(PACIFIC) not in sys.path:  # info: if str ( PACIFIC ) not in sys . path
        sys.path.insert(0, str(PACIFIC))  # info: sys . path . insert ( 0 , str ( PACIFIC ) )
    from Energy.db.report_json import REPORT_JSON, period_lines  # info: from Energy . db . report_json import REPORT_JSON
    try:  # info: try
        doc = json.loads(REPORT_JSON.read_text(encoding="utf-8"))  # info: set doc
    except (OSError, ValueError):  # info: except ( OSError , ValueError )
        return ""  # info: return ""
    return "\n".join(period_lines(doc))  # info: return the hour, day, week, and month lines


# ====================================================
# SECTION: function prompt_for
# What it does: prompt for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def prompt_for(kind: str, facts: str) -> str:  # info: def prompt_for
    if kind == "kilauea":  # info: if kind == "kilauea" :
        ask = "Write a short Kīlauea notice from FACTS only."  # info: set ask
    else:  # info: else :
        ask = f"Write today's {kind} desk status from FACTS only."  # info: set ask
    return (  # info: return (
        f"{ask}\n"  # info: f" { ask } \n "
        "No invented numbers. No vendor names. End with End of status.\n\n"  # info: "No invented numbers. No vendor names. End with End of status.\n\n"
        f"FACTS:\n{facts}\n"  # info: f" FACTS:\n { facts } \n "
    )  # info: )


# ====================================================
# SECTION: function template_path
# What it does: template path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def template_path(kind: str) -> Path | None:  # info: def template_path
    name = TEMPLATE_FILE.get(kind)  # info: set name
    return (TEMPLATES / name) if name else None  # info: return ( TEMPLATES / name ) if name


# ====================================================
# SECTION: function read_template
# What it does: read template.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_template(kind: str) -> tuple[str, Path | None]:  # info: def read_template
    path = template_path(kind)  # info: set path
    if path is None or not path.is_file():  # info: if path is None or not path .
        return "", path  # info: return "" , path
    return path.read_text(encoding="utf-8", errors="replace"), path  # info: return path . read_text ( encoding = "utf-8"


# ====================================================
# SECTION: function morning_narrative_today
# What it does: morning narrative today.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def morning_narrative_today(t: datetime) -> Path | None:  # info: def morning_narrative_today
    path = DATA / "morning-current.md"  # info: set path
    if not path.is_file():  # info: if not path . is_file ( ) :
        return None  # info: return None
    mt = datetime.fromtimestamp(path.stat().st_mtime, HST)  # info: set mt
    if mt.date() != t.date():  # info: if mt . date ( ) != t
        return None  # info: return None
    return path  # info: return path


# ====================================================
# SECTION: function write_last
# What it does: write last.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_last(payload: dict) -> None:  # info: def write_last
    DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
    LOG.parent.mkdir(parents=True, exist_ok=True)  # info: LOG . parent . mkdir ( parents =
    tmp = DATA / "last.json.tmp"  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, DATA / "last.json")  # info: os . replace ( tmp , DATA /
    with LOG.open("a", encoding="utf-8") as f:  # info: with LOG . open ( "a" , encoding
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")  # info: f . write ( json . dumps (


# ====================================================
# SECTION: function cloud_chat
# What it does: One chat completion. Called only after the spend gate passes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def cloud_chat(kind: str, facts: str) -> str:  # info: def cloud_chat
    """One chat completion. Called only after the spend gate passes."""  # info: """One chat completion. Called only after the spend gate passes."""
    import urllib.request  # info: import urllib . request

    key = envload.api_key()  # info: set key
    body = json.dumps({  # info: set body
        "model": MODEL,  # info: "model" : MODEL ,
        "messages": [  # info: "messages" : [
            {"role": "system", "content": persona(kind)},  # info: { "role" : "system" , "content" : persona
            {"role": "user", "content": prompt_for(kind, facts)},  # info: { "role" : "user" , "content" : prompt_for
        ],  # info: ] ,
        "temperature": 0.3,  # info: "temperature" : 0.3 ,
        "max_tokens": 600 if kind == "kilauea" else 1800,  # info: "max_tokens" : 600 if kind == "kilauea" else
    }).encode("utf-8")  # info: } ) . encode ( "utf-8" )
    req = urllib.request.Request(  # info: set req
        CHAT_URL,  # info: CHAT_URL ,
        data=body,  # info: set data
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},  # info: set headers
        method="POST",  # info: set method
    )  # info: )
    with urllib.request.urlopen(req, timeout=120) as resp:  # info: with urllib . request . urlopen ( req
        data = json.loads(resp.read().decode("utf-8", errors="replace"))  # info: set data
    return str(data["choices"][0]["message"]["content"] or "")  # info: return str ( data [ "choices" ] [


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run(kind: str, *, spend: bool) -> dict:  # info: def run
    t = now()  # info: set t
    base = {"at": t.isoformat(), "kind": kind, "http": False}  # info: set base
    if kind not in KINDS:  # info: if kind not in KINDS :
        payload = dict(base, dry_run=True, result="skip", detail="unknown_kind")  # info: set payload
        write_last(payload)  # info: call write_last
        return payload  # info: return payload

    if kind == "merged":  # info: if kind == "merged" :
        src = morning_narrative_today(t)  # info: set src
        payload = dict(base, dry_run=not spend, result="dry_run" if not spend else "copied",  # info: set payload
                       detail="no_model_call", would_copy=src is not None, source=str(src) if src else None)  # info: set detail
        if spend and src is not None:  # info: if spend and src is not None :
            text = src.read_text(encoding="utf-8", errors="replace")  # info: set text
            dest = DATA / "merged-current.md"  # info: set dest
            dest.write_text(text, encoding="utf-8")  # info: dest . write_text ( text , encoding =
            payload["bytes"] = len(text.encode("utf-8"))  # info: payload [ "bytes" ] = len ( text
        elif spend:  # info: elif spend :
            payload["result"] = "skip"  # info: payload [ "result" ] = "skip"
            payload["detail"] = "no_morning_narrative_today"  # info: payload [ "detail" ] = "no_morning_narrative_today"
        write_last(payload)  # info: call write_last
        return payload  # info: return payload

    raw, path = read_template(kind)  # info: raw , path = read_template ( kind )
    facts = scrub_speech(scrub_nws(measured(raw)))  # info: set facts
    if kind != "kilauea":  # info: if kind != "kilauea"
        windows = energy_windows()  # info: set windows
        if windows:  # info: if windows
            facts = f"{facts}\n\nENERGY WINDOWS:\n{windows}"  # info: append the closed energy windows
    package = (  # info: set package
        f"# Cloud narrative package — {kind}\n\n"
        f"Built: {t.isoformat()}\n"  # info: f" Built: { t . isoformat ( )
        f"Template: {path}\n"  # info: f" Template: { path } \n "
        f"Dry-run: {not spend}\n\n"  # info: f" Dry-run: { not spend } \n\n "
        f"## System\n\n{persona(kind)}\n\n"
        f"## User\n\n{prompt_for(kind, facts)}\n"
    )  # info: )
    DATA.mkdir(parents=True, exist_ok=True)  # info: DATA . mkdir ( parents = True ,
    (DATA / f"{kind}-package.md").write_text(package, encoding="utf-8")  # info: call (
    payload = dict(  # info: set payload
        base,  # info: base ,
        dry_run=not spend,  # info: set dry_run
        template=str(path) if path else None,  # info: set template
        template_present=bool(raw),  # info: set template_present
        package_chars=len(package),  # info: set package_chars
        facts_chars=len(facts),  # info: set facts_chars
    )  # info: )
    if not raw:  # info: if not raw :
        payload.update(result="skip", detail="template_missing", dry_run=True)  # info: payload . update ( result = "skip" ,
        write_last(payload)  # info: call write_last
        return payload  # info: return payload
    if not spend:  # info: if not spend :
        payload.update(result="dry_run", detail="no_http")  # info: payload . update ( result = "dry_run" ,
        write_last(payload)  # info: call write_last
        return payload  # info: return payload

    if not envload.api_key():  # info: if not envload . api_key ( ) :
        payload.update(dry_run=True, result="skip", detail="missing_key", http=False)  # info: payload . update ( dry_run = True ,
        write_last(payload)  # info: call write_last
        return payload  # info: return payload

    try:  # info: try :
        text = scrub_speech(cloud_chat(kind, facts))  # info: set text
    except Exception as e:  # info: except Exception as e :
        payload.update(result="failed", detail=type(e).__name__, http=True)  # info: payload . update ( result = "failed" ,
        write_last(payload)  # info: call write_last
        return payload  # info: return payload
    payload["http"] = True  # info: payload [ "http" ] = True
    if len(text.strip()) < THIN:  # info: if len ( text . strip ( )
        payload.update(result="rejected", detail="thin_output")  # info: payload . update ( result = "rejected" ,
        write_last(payload)  # info: call write_last
        return payload  # info: return payload
    out = DATA / f"{kind}-current.md"  # info: set out
    out.write_text(text.rstrip() + "\n", encoding="utf-8")  # info: out . write_text ( text . rstrip (
    payload.update(result="wrote", detail="cloud_text", bytes=out.stat().st_size)  # info: payload . update ( result = "wrote" ,
    write_last(payload)  # info: call write_last
    return payload  # info: return payload


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    args = [a for a in sys.argv[1:] if not a.startswith("-")]  # info: set args
    kind = (args[0] if args else "morning").strip().lower()  # info: set kind
    spend = "--spend" in sys.argv and "--dry-run" not in sys.argv and os.environ.get("RR_CLOUD_NARRATIVE_SPEND") == "1"  # info: set spend
    payload = run(kind, spend=spend)  # info: set payload
    print(json.dumps(payload, ensure_ascii=False))  # info: call print
    if payload.get("result") == "failed":  # info: if payload . get ( "result" ) ==
        return 1  # info: return 1
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
