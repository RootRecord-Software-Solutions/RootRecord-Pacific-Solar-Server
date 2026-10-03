# ==============================================================================
# FILE: CodeReview/scripts/code_review.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Code review pack. Writes markdown only. Never patches the tree.

Evidence is git status plus error lines from an allowlisted set of Database logs.
The coder section stays off unless RR_CODE_REVIEW_CODER=1. That flag stays unset.
No qwen pull. No cloud call on the default path.

  python3 code_review.py
  python3 code_review.py --root /tmp/rr-mig-34
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import os  # info: import os
import subprocess  # info: import subprocess
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
ECOSYSTEM = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ECOSYSTEM
DEFAULT_DB = ECOSYSTEM / "2 - RootRecord-Database"  # info: set DEFAULT_DB
PACIFIC = ECOSYSTEM / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server"  # info: set PACIFIC
GIT_CAP = 4000  # info: set GIT_CAP
TAIL_BYTES = 256_000  # info: set TAIL_BYTES
TAIL_LINES = 400  # info: set TAIL_LINES
ERR_LIMIT = 40  # info: set ERR_LIMIT
LINE_CAP = 240  # info: set LINE_CAP
SKIP = ("password", "api_key", "token=", "secret", "sk-", "bot")  # info: set SKIP
# ====================================================
# SECTION: LOG_ALLOW
# What it does: Set LOG_ALLOW.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
LOG_ALLOW = (  # info: set LOG_ALLOW
    "Logs/Automations/automations_current.log",  # info: "Logs/Automations/automations_current.log" ,
    "Energy/logs/ava-ecoflow-ble.log",  # info: "Energy/logs/ava-ecoflow-ble.log" ,
    "Logs/Communications/council-relay.log",  # info: "Logs/Communications/council-relay.log" ,
)  # info: )


# ====================================================
# SECTION: function _tail
# What it does:  tail.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _tail(path: Path) -> list[str]:  # info: def _tail
    if not path.is_file():  # info: if not path . is_file ( ) :
        return []  # info: return [ ]
    try:  # info: try :
        size = path.stat().st_size  # info: set size
        with path.open("rb") as handle:  # info: with path . open ( "rb" ) as
            handle.seek(max(0, size - TAIL_BYTES))  # info: handle . seek ( max ( 0 ,
            raw = handle.read()  # info: set raw
    except OSError:  # info: except OSError :
        return []  # info: return [ ]
    return raw.decode("utf-8", errors="replace").splitlines()[-TAIL_LINES:]  # info: return raw . decode ( "utf-8" , errors


# ====================================================
# SECTION: function _secret
# What it does:  secret.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _secret(line: str) -> bool:  # info: def _secret
    low = line.lower()  # info: set low
    return any(token in low for token in SKIP)  # info: return any ( token in low for token


# ====================================================
# SECTION: function _git_short
# What it does:  git short.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _git_short() -> str:  # info: def _git_short
    try:  # info: try :
        result = subprocess.run(  # info: set result
            ["git", "status", "--short", "-uno"],  # info: [ "git" , "status" , "--short" , "-uno"
            cwd=ECOSYSTEM,  # info: set cwd
            capture_output=True,  # info: set capture_output
            text=True,  # info: set text
            timeout=20,  # info: set timeout
        )  # info: )
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired )
        return f"(unavailable: {type(exc).__name__})"  # info: return f" (unavailable: { type ( exc )
    text = ((result.stdout or "") + (result.stderr or "")).strip()  # info: set text
    if not text:  # info: if not text :
        return "(clean or git unavailable)"  # info: return "(clean or git unavailable)"
    return text[:GIT_CAP]  # info: return text [ : GIT_CAP ]


# ====================================================
# SECTION: function _log_errors
# What it does:  log errors.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _log_errors() -> list[str]:  # info: def _log_errors
    hits: list[str] = []  # info: set hits
    for rel in LOG_ALLOW:  # info: for rel in LOG_ALLOW :
        path = DEFAULT_DB / rel  # info: set path
        for line in _tail(path):  # info: for line in _tail ( path ) :
            if _secret(line):  # info: if _secret ( line ) :
                continue  # info: continue
            low = line.lower()  # info: set low
            if "error" in low or "exception" in low or "traceback" in low:  # info: if "error" in low or "exception" in low
                hits.append(f"{path.name}: {line[:LINE_CAP]}")  # info: hits . append ( f" { path .
    return hits[:ERR_LIMIT]  # info: return hits [ : ERR_LIMIT ]


# ====================================================
# SECTION: function _coder_notes
# What it does:  coder notes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _coder_notes(evidence: str) -> str:  # info: def _coder_notes
    if os.environ.get("RR_CODE_REVIEW_CODER", "0") != "1":  # info: if os . environ . get ( "RR_CODE_REVIEW_CODER"
        return "_Coder off._\n"  # info: return "_Coder off._\n"
    infer = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"  # info: set infer
    prompt = (  # info: set prompt
        "List up to 8 concrete gaps from the evidence. "  # info: "List up to 8 concrete gaps from the evidence. "
        "For each: one-line title, why it matters, and a task in one sentence. "  # info: "For each: one-line title, why it matters, and a task in one sentence. "
        "No patches. If evidence is thin, say that.\n\n"  # info: "No patches. If evidence is thin, say that.\n\n"
        + evidence[:6000]  # info: + evidence [ : 6000 ]
    )  # info: )
    try:  # info: try :
        result = subprocess.run(  # info: set result
            ["bash", str(infer), "ava", prompt],  # info: [ "bash" , str ( infer ) ,
            capture_output=True,  # info: set capture_output
            text=True,  # info: set text
            timeout=180,  # info: set timeout
            env=dict(os.environ, RR_CALLER="code_review"),  # info: set env
        )  # info: )
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired )
        return f"_Coder skipped: {type(exc).__name__}_\n"  # info: return f" _Coder skipped: { type ( exc )
    raw = " ".join(  # info: set raw
        line for line in (result.stdout or "").splitlines() if not line.startswith("[ok]")  # info: line for line in ( result . stdout
    ).strip()  # info: ) . strip ( )
    if result.returncode != 0 or not raw:  # info: if result . returncode != 0 or not
        return "_Coder skipped: no note._\n"  # info: return "_Coder skipped: no note._\n"
    return f"_Coder on (RR_CODE_REVIEW_CODER=1)._\n\n{raw[:4000]}\n"  # info: return f" _Coder on (RR_CODE_REVIEW_CODER=1)._\n\n { raw [ : 4000


# ====================================================
# SECTION: function _pack
# What it does:  pack.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pack(git_text: str, errors: list[str], coder: str, when: datetime) -> str:  # info: def _pack
    err_block = "\n".join(f"- `{line}`" for line in errors) or "- (none in the last log tail)"  # info: set err_block
    return (  # info: return (
        "# Code review pack — evaluate only\n\n"
        "Suggest fixes in a reply. This file does not change the live tree.\n\n"  # info: "Suggest fixes in a reply. This file does not change the live tree.\n\n"
        "- Live numbers only from the evidence below. If evidence is missing, say so.\n"  # info: "- Live numbers only from the evidence below. If evidence is missing, say so.\n"
        "- Do not print secrets, tokens, or env values.\n\n"  # info: "- Do not print secrets, tokens, or env values.\n\n"
        f"Live tree: `{ECOSYSTEM}`\n\n"  # info: f" Live tree: ` { ECOSYSTEM } `\n\n "
        f"## Evidence — {when.isoformat()}\n\n"
        "### Git (uncommitted, not staged by this job)\n\n"
        f"```\n{git_text}\n```\n\n"  # info: f" ```\n { git_text } \n```\n\n "
        "### Recent log errors\n\n"
        f"{err_block}\n\n"  # info: f" { err_block } \n\n "
        "## Local coder suggestions (not applied)\n\n"
        f"{coder}"  # info: f" { coder } "
    )  # info: )


# ====================================================
# SECTION: function write_pack
# What it does: write pack.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_pack(root: Path) -> dict:  # info: def write_pack
    when = datetime.now(HST)  # info: set when
    out = root / "CodeReview"  # info: set out
    log_dir = root / "Logs" / "CodeReview"  # info: set log_dir
    out.mkdir(parents=True, exist_ok=True)  # info: out . mkdir ( parents = True ,
    log_dir.mkdir(parents=True, exist_ok=True)  # info: log_dir . mkdir ( parents = True ,
    git_text = _git_short()  # info: set git_text
    errors = _log_errors()  # info: set errors
    evidence = f"{git_text}\n" + "\n".join(errors)  # info: set evidence
    coder = _coder_notes(evidence)  # info: set coder
    body = _pack(git_text, errors, coder, when)  # info: set body
    stamp = when.strftime("%Y-%m-%d-%H%M")  # info: set stamp
    dated = out / f"{stamp}.md"  # info: set dated
    current = out / "CURRENT.md"  # info: set current
    dated.write_text(body, encoding="utf-8")  # info: dated . write_text ( body , encoding =
    current.write_text(body, encoding="utf-8")  # info: current . write_text ( body , encoding =
    line = (  # info: set line
        f"{when.isoformat()} pack={dated.name} bytes={dated.stat().st_size} "  # info: f" { when . isoformat ( ) }
        f"coder={'on' if os.environ.get('RR_CODE_REVIEW_CODER', '0') == '1' else 'off'}\n"  # info: f" coder= { 'on' if os . environ
    )  # info: )
    with (log_dir / "code-review.log").open("a", encoding="utf-8") as handle:  # info: with ( log_dir / "code-review.log" ) . open
        handle.write(line)  # info: handle . write ( line )
    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "applied": False,  # info: "applied" : False ,
        "current": str(current),  # info: "current" : str ( current ) ,
        "dated": str(dated),  # info: "dated" : str ( dated ) ,
        "coder": os.environ.get("RR_CODE_REVIEW_CODER", "0") == "1",  # info: "coder" : os . environ . get (
    }  # info: }


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    parser = argparse.ArgumentParser(description="Write a code review evidence pack.")  # info: set parser
    parser.add_argument(  # info: parser . add_argument (
        "--root",  # info: "--root" ,
        default="",  # info: set default
        help="Database root for this run. Default is the live Database folder.",  # info: set help
    )  # info: )
    args = parser.parse_args()  # info: set args
    root = Path(args.root) if args.root else DEFAULT_DB  # info: set root
    result = write_pack(root)  # info: set result
    print(f"ok current={result['current']} dated={result['dated']} coder={result['coder']}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
