#!/usr/bin/env python3
# ==============================================================================
# # INFO — route-specialist.py: keyword/regex topic router for RootRecord specialists
# ------------------------------------------------------------------------------
# Usage:
#   route-specialist.py [--voice ava|bruce|carly] [--explain|--json|--shell] [prompt...]
#   echo "prompt" | route-specialist.py --shell --voice ava
#   route-specialist.py --list                 # specialist table
#   route-specialist.py --system rr-energy     # print a specialist's SYSTEM block (FLM route)
#   route-specialist.py --force rr-exec --shell --with-system   # explicit specialist (run-infer.sh RR_SPECIALIST)
# Config: System/config/specialist-routes.json (tracked). Stdlib only. Never runs a model.
# Output: chosen specialist + confidence; below the threshold -> "generic" (caller voice model).
# Log: one metadata-only JSON line per decision -> Database Logs/AI/Routing/routing_current.jsonl
#      (prompt length + matched keyword/rule NAMES; never prompt text). RR_ROUTE_LOG=0 or --no-log disables.
# FLM/NPU: flm cannot load Ollama Modelfiles, so for prefer=flm the SYSTEM block is sent as the system
#      message to the FLM base model (llama3.2:1b). --with-system adds RR_SPEC_SYSTEM to --shell output.
# Gate: run-infer.sh hook LANDED 2026-09-29 ~04:56, OFF unless RR_SPECIALIST_ROUTING=1 — see Library
#      Documentation/00-architecture/AI-Specialist-Models-and-Routing.md. Fail-safe: errors -> generic, exit 0.
# HOW TO ADD a specialist: see the "_info" block in the config and the Library doc.
# Created 2026-09-29 HST (g3-specialists). Bak snapshots: 2 - RootRecord-Database/Archive/Github-desk-backups/
# ==============================================================================
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import math  # info: import math
import os  # info: import os
import re  # info: import re
import shlex  # info: import shlex
import sys  # info: import sys
import time  # info: import time
import unicodedata  # info: import unicodedata
import urllib.request  # info: import urllib . request
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
PACIFIC = HERE.parent.parent.parent  # info: set PACIFIC
DEFAULT_CONFIG = PACIFIC / "System" / "config" / "specialist-routes.json"  # info: set DEFAULT_CONFIG
ROUTER_VERSION = "3.0"  # v3 (2026-09-29): keyword matching treats space / hyphen / underscore alike

_OKINA = dict.fromkeys(map(ord, "\u02bb\u2018\u2019\u02bc'`\u00b4"), None)  # info: set _OKINA


# ====================================================
# SECTION: function normalize
# What it does: Lowercase, strip diacritics and ʻokina so Hawaiʻi/Kīlauea match hawaii/kilauea.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def normalize(text: str) -> str:  # info: def normalize
    """Lowercase, strip diacritics and ʻokina so Hawaiʻi/Kīlauea match hawaii/kilauea."""  # info: """Lowercase, strip diacritics and ʻokina so Hawaiʻi/Kīlauea match hawaii/kilauea."""
    t = unicodedata.normalize("NFKD", text or "")  # info: set t
    t = "".join(ch for ch in t if not unicodedata.combining(ch))  # info: set t
    return t.translate(_OKINA).lower()  # info: return t . translate ( _OKINA ) .


_SEP = re.compile(r"[\s\-_]+")  # info: set _SEP


# ====================================================
# SECTION: function kw_normalize
# What it does: Keyword view: normalize() + space/hyphen/underscore runs -> one space ("master_key" = "master-key" = "master key"). Regex rules still see _norm_keep_backticks() text, so patterns s
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def kw_normalize(text: str) -> str:  # info: def kw_normalize
    """Keyword view: normalize() + space/hyphen/underscore runs -> one space ("master_key" = "master-key" = "master key").
    Regex rules still see _norm_keep_backticks() text, so patterns such as wo-[a-z]+ or token shapes keep their separators."""
    return _SEP.sub(" ", normalize(text)).strip()  # info: return _SEP . sub ( " " , normalize


# ====================================================
# SECTION: function _norm_keep_backticks
# What it does:  norm keep backticks.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _norm_keep_backticks(text: str) -> str:  # info: def _norm_keep_backticks
    t = unicodedata.normalize("NFKD", text or "")  # info: set t
    t = "".join(ch for ch in t if not unicodedata.combining(ch))  # info: set t
    return t.translate(dict.fromkeys(map(ord, "\u02bb\u2018\u2019\u02bc'\u00b4"), None)).lower()  # info: return t . translate ( dict . fromkeys


# ====================================================
# SECTION: function term_pattern
# What it does: term pattern.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def term_pattern(term: str) -> re.Pattern:  # info: def term_pattern
    t = kw_normalize(term)  # info: set t
    prefix = t.endswith("*")  # info: set prefix
    if prefix:  # info: if prefix :
        t = t[:-1]  # info: set t
    body = r"\s+".join(re.escape(p) for p in t.split())  # info: set body
    tail = r"[a-z0-9_-]*" if prefix else ""  # info: set tail
    return re.compile(r"(?<![a-z0-9_])" + body + tail + r"(?![a-z0-9_])")  # info: return re . compile ( r"(?<![a-z0-9_])" + body


# ====================================================
# SECTION: function load_config
# What it does: load config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_config(path: Path) -> dict:  # info: def load_config
    cfg = json.loads(path.read_text(encoding="utf-8"))  # info: set cfg
    for name, spec in cfg["specialists"].items():  # info: for name , spec in cfg [ "specialists"
        uniq: dict[str, tuple[str, int]] = {}  # v3: "time-lapse" and "time lapse" now collide -> keep one, max weight
        for k, w in spec.get("keywords", {}).items():  # info: for k , w in spec . get
            nk = kw_normalize(k)  # info: set nk
            if nk not in uniq or int(w) > uniq[nk][1]:  # info: if nk not in uniq or int (
                uniq[nk] = (uniq.get(nk, (k, 0))[0], int(w))  # info: uniq [ nk ] = ( uniq .
        spec["_kw"] = [(k, w, term_pattern(k)) for k, w in uniq.values()]  # info: spec [ "_kw" ] = [ ( k
        spec["_rx"] = [(r["name"], int(r["weight"]), re.compile(r["pattern"], re.M)) for r in spec.get("regex", [])]  # info: spec [ "_rx" ] = [ ( r
    return cfg  # info: return cfg


# ====================================================
# SECTION: function score
# What it does: score.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def score(cfg: dict, prompt: str) -> list[dict]:  # info: def score
    text = kw_normalize(prompt)  # info: set text
    text_bt = _norm_keep_backticks(prompt)  # regexes like inline_code need backticks
    rows = []  # info: set rows
    prio = {n: i for i, n in enumerate(cfg.get("priority", []))}  # info: set prio
    for name, spec in cfg["specialists"].items():  # info: for name , spec in cfg [ "specialists"
        total, matched = 0, []  # info: total , matched = 0 , [ ]
        for kw, w, pat in spec["_kw"]:  # info: for kw , w , pat in spec
            if pat.search(text):  # info: if pat . search ( text ) :
                total += w  # info: set total
                matched.append(kw)  # info: matched . append ( kw )
        for rname, w, pat in spec["_rx"]:  # info: for rname , w , pat in spec
            if pat.search(text_bt):  # info: if pat . search ( text_bt ) :
                total += w  # info: set total
                matched.append("re:" + rname)  # info: matched . append ( "re:" + rname )
        rows.append({"name": name, "score": total, "matched": matched, "prio": prio.get(name, 999)})  # info: rows . append ( { "name" : name
    rows.sort(key=lambda r: (-r["score"], r["prio"]))  # info: rows . sort ( key = lambda r
    return rows  # info: return rows


# ====================================================
# SECTION: function confidence
# What it does: confidence.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def confidence(cfg: dict, top: int, second: int) -> float:  # info: def confidence
    if top <= 0:  # info: if top <= 0 :
        return 0.0  # info: return 0.0
    sat = float(cfg.get("saturation", 6.0))  # info: set sat
    strength = min(1.0, top / sat)  # info: set strength
    margin = (top - second) / top  # info: set margin
    return round(strength * (0.6 + 0.4 * margin), 3)  # info: return round ( strength * ( 0.6 +


# ====================================================
# SECTION: function parse_modelfile
# What it does: SYSTEM block + temperature/num_predict/num_ctx for the FLM system-message route.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_modelfile(path: Path) -> dict:  # info: def parse_modelfile
    """SYSTEM block + temperature/num_predict/num_ctx for the FLM system-message route."""  # info: """SYSTEM block + temperature/num_predict/num_ctx for the FLM system-message route."""
    out = {"system": "", "params": {}}  # info: set out
    try:  # info: try :
        txt = path.read_text(encoding="utf-8")  # info: set txt
    except OSError:  # info: except OSError :
        return out  # info: return out
    m = re.search(r'^SYSTEM\s+"""\n?(.*?)\n?"""', txt, re.S | re.M)  # info: set m
    if m:  # info: if m :
        out["system"] = m.group(1).strip()  # info: out [ "system" ] = m . group
    for pm in re.finditer(r"^PARAMETER\s+(temperature|num_predict|num_ctx|top_p)\s+(\S+)", txt, re.M):  # info: for pm in re . finditer ( r"^PARAMETER\s+(temperature|num_predict|num_ctx|top_p)\s+(\S+)"
        try:  # info: try :
            out["params"][pm.group(1)] = float(pm.group(2)) if "." in pm.group(2) else int(pm.group(2))  # info: out [ "params" ] [ pm . group
        except ValueError:  # info: except ValueError :
            pass  # info: pass
    return out  # info: return out


# ====================================================
# SECTION: function installed_models
# What it does: installed models.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def installed_models(timeout: float = 1.0) -> set[str] | None:  # info: def installed_models
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")  # info: set host
    if not host.startswith("http"):  # info: if not host . startswith ( "http" )
        host = "http://" + host  # info: set host
    try:  # info: try :
        with urllib.request.urlopen(host.rstrip("/") + "/api/tags", timeout=timeout) as r:  # info: with urllib . request . urlopen ( host
            data = json.loads(r.read().decode())  # info: set data
    except Exception:  # info: except Exception :
        return None  # info: return None
    names = set()  # info: set names
    for m in data.get("models", []):  # info: for m in data . get ( "models"
        n = m.get("name") or m.get("model") or ""  # info: set n
        names.add(n)  # info: names . add ( n )
        if n.endswith(":latest"):  # info: if n . endswith ( ":latest" ) :
            names.add(n[: -len(":latest")])  # info: names . add ( n [ : -
    return names  # info: return names


# ====================================================
# SECTION: function decide
# What it does: decide.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def decide(cfg: dict, prompt: str, voice: str | None, verify: bool = False) -> dict:  # info: def decide
    rows = score(cfg, prompt)  # info: set rows
    top, second = rows[0], (rows[1] if len(rows) > 1 else {"score": 0, "name": None})  # info: top , second = rows [ 0 ]
    conf = confidence(cfg, top["score"], second["score"])  # info: set conf
    thr = float(cfg.get("threshold", 0.3))  # info: set thr
    dflt = cfg["default"]  # info: set dflt
    voice_model = dflt.get("voice_models", {}).get((voice or "").lower())  # info: set voice_model
    if conf >= thr and top["score"] > 0:  # info: if conf >= thr and top [ "score"
        spec = cfg["specialists"][top["name"]]  # info: set spec
        d = {  # info: set d
            "specialist": top["name"], "function": spec.get("function"), "default_used": False,  # info: "specialist" : top [ "name" ] , "function"
            "ollama_model": spec["ollama_model"], "prefer": spec.get("prefer", "flm"),  # info: "ollama_model" : spec [ "ollama_model" ] , "prefer"
            "fallback": spec.get("fallback") or voice_model or dflt.get("fallback"),  # info: "fallback" : spec . get ( "fallback" )
            "modelfile": str(Path(cfg["modelfile_root"]) / spec["modelfile"]),  # info: "modelfile" : str ( Path ( cfg [
            "matched": top["matched"],  # info: "matched" : top [ "matched" ] ,
        }  # info: }
    else:  # info: else :
        d = {  # info: set d
            "specialist": dflt.get("name", "generic"), "function": "default", "default_used": True,  # info: "specialist" : dflt . get ( "name" ,
            "ollama_model": voice_model or dflt.get("fallback"), "prefer": dflt.get("prefer", "flm"),  # info: "ollama_model" : voice_model or dflt . get (
            "fallback": voice_model or dflt.get("fallback"), "modelfile": "", "matched": [],  # info: "fallback" : voice_model or dflt . get (
        }  # info: }
    d.update({  # info: d . update ( {
        "confidence": conf, "threshold": thr, "score": top["score"],  # info: "confidence" : conf , "threshold" : thr ,
        "runner_up": second["name"] if second["score"] > 0 else None, "runner_up_score": second["score"],  # info: "runner_up" : second [ "name" ] if second
        "flm_model": cfg.get("flm", {}).get("base_model", "llama3.2:1b"), "voice": voice or None,  # info: "flm_model" : cfg . get ( "flm" ,
        "model_verified": None, "_rows": rows,  # info: "model_verified" : None , "_rows" : rows ,
    })  # info: } )
    if verify and d["ollama_model"]:  # info: if verify and d [ "ollama_model" ] :
        have = installed_models()  # info: set have
        if have is not None:  # info: if have is not None :
            ok = d["ollama_model"] in have  # info: set ok
            d["model_verified"] = ok  # info: d [ "model_verified" ] = ok
            if not ok and d.get("fallback"):  # info: if not ok and d . get (
                d["ollama_model"] = d["fallback"]  # info: d [ "ollama_model" ] = d [ "fallback"
    return d  # info: return d


# ====================================================
# SECTION: function forced
# What it does: Explicit specialist request (run-infer.sh RR_SPECIALIST=<name>, or TARGET=rr-*): no scoring, confidence 1.0. Unknown name -> generic (fail-safe).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def forced(cfg: dict, name: str, voice: str | None, verify: bool = False) -> dict:  # info: def forced
    """Explicit specialist request (run-infer.sh RR_SPECIALIST=<name>, or TARGET=rr-*): no scoring, confidence 1.0.
    Unknown name -> generic (fail-safe)."""
    if name not in cfg["specialists"]:  # info: if name not in cfg [ "specialists" ]
        d = decide(cfg, "", voice, verify)  # info: set d
        d["matched"] = ["forced-unknown"]  # info: d [ "matched" ] = [ "forced-unknown" ]
        return d  # info: return d
    spec = cfg["specialists"][name]  # info: set spec
    dflt = cfg["default"]  # info: set dflt
    voice_model = dflt.get("voice_models", {}).get((voice or "").lower())  # info: set voice_model
    d = {"specialist": name, "function": spec.get("function"), "default_used": False, "ollama_model": spec["ollama_model"],  # info: set d
         "prefer": spec.get("prefer", "flm"), "fallback": spec.get("fallback") or voice_model or dflt.get("fallback"),  # info: "prefer" : spec . get ( "prefer" ,
         "modelfile": str(Path(cfg["modelfile_root"]) / spec["modelfile"]), "matched": ["forced"],  # info: "modelfile" : str ( Path ( cfg [
         "confidence": 1.0, "threshold": float(cfg.get("threshold", 0.3)), "score": 0, "runner_up": None, "runner_up_score": 0,  # info: "confidence" : 1.0 , "threshold" : float (
         "flm_model": cfg.get("flm", {}).get("base_model", "llama3.2:1b"), "voice": voice or None, "model_verified": None, "_rows": []}  # info: "flm_model" : cfg . get ( "flm" ,
    if verify:  # info: if verify :
        have = installed_models()  # info: set have
        if have is not None:  # info: if have is not None :
            d["model_verified"] = d["ollama_model"] in have  # info: d [ "model_verified" ] = d [ "ollama_model"
            if not d["model_verified"] and d.get("fallback"):  # info: if not d [ "model_verified" ] and d
                d["ollama_model"] = d["fallback"]  # info: d [ "ollama_model" ] = d [ "fallback"
    return d  # info: return d


# ====================================================
# SECTION: function log_decision
# What it does: log decision.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def log_decision(cfg: dict, d: dict, prompt: str, caller: str, elapsed_us: int, error: str | None = None) -> None:  # info: def log_decision
    if os.environ.get("RR_ROUTE_LOG", "1") != "1":  # info: if os . environ . get ( "RR_ROUTE_LOG"
        return  # info: return
    path = Path(os.environ.get("RR_ROUTE_LOG_FILE") or cfg.get("log_file", ""))  # info: set path
    if not str(path):  # info: if not str ( path ) :
        return  # info: return
    rec = {  # info: set rec
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),  # info: "ts" : datetime . now ( ) .
        "router": ROUTER_VERSION, "caller": re.sub(r"[^A-Za-z0-9._:@/+-]", "", caller or "unknown")[:64],  # info: "router" : ROUTER_VERSION , "caller" : re .
        "voice": d.get("voice"), "specialist": d.get("specialist"), "default_used": d.get("default_used"),  # info: "voice" : d . get ( "voice" )
        "confidence": d.get("confidence"), "score": d.get("score"), "threshold": d.get("threshold"),  # info: "confidence" : d . get ( "confidence" )
        "runner_up": d.get("runner_up"), "runner_up_score": d.get("runner_up_score"),  # info: "runner_up" : d . get ( "runner_up" )
        "matched": d.get("matched", []),  # config keyword / rule NAMES only
        "prefer": d.get("prefer"), "ollama_model": d.get("ollama_model"), "model_verified": d.get("model_verified"),  # info: "prefer" : d . get ( "prefer" )
        "prompt_chars": len(prompt or ""), "elapsed_us": elapsed_us,  # info: "prompt_chars" : len ( prompt or "" )
    }  # info: }
    if error:  # info: if error :
        rec["error"] = error[:120]  # info: rec [ "error" ] = error [ :
    try:  # info: try :
        import fcntl  # info: import fcntl
        path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
        with open(path, "a", encoding="utf-8") as fh:  # info: with open ( path , "a" , encoding
            fcntl.flock(fh, fcntl.LOCK_EX)  # info: fcntl . flock ( fh , fcntl .
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")  # info: fh . write ( json . dumps (
    except Exception:  # info: except Exception :
        pass  # logging must never break routing


# ====================================================
# SECTION: function explain
# What it does: explain.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def explain(cfg: dict, d: dict, prompt: str) -> str:  # info: def explain
    lines = [f"prompt_chars={len(prompt)}  voice={d['voice'] or '-'}  threshold={d['threshold']}  saturation={cfg.get('saturation', 6.0)}",  # info: set lines
             "confidence = min(1, top/saturation) * (0.6 + 0.4*(top-second)/top)", "",  # info: "confidence = min(1, top/saturation) * (0.6 + 0.4*(top-second)/top)" , "" ,
             f"{'specialist':<18} {'score':>5}  matched"]  # info: f" { 'specialist' : <18 } {
    for r in d["_rows"]:  # info: for r in d [ "_rows" ] :
        lines.append(f"{r['name']:<18} {r['score']:>5}  {', '.join(r['matched']) or '-'}")  # info: lines . append ( f" { r [
    lines += ["", f"-> {d['specialist']}  confidence={d['confidence']}  default_used={d['default_used']}",  # info: set lines
              f"   ollama_model={d['ollama_model']}  prefer={d['prefer']}  flm_model={d['flm_model']}  fallback={d['fallback']}"]  # info: f" ollama_model= { d [ 'ollama_model' ] }
    if d["modelfile"]:  # info: if d [ "modelfile" ] :
        lines.append(f"   modelfile={d['modelfile']}")  # info: lines . append ( f" modelfile= { d
    if d["prefer"] == "flm" and not d["default_used"]:  # info: if d [ "prefer" ] == "flm" and
        lines.append("   FLM route: SYSTEM block of the modelfile is sent as the system message to " + d["flm_model"])  # info: lines . append ( " FLM route: SYSTEM block of the modelfile is sent as the system message to " + d [
    return "\n".join(lines)  # info: return "\n" . join ( lines )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    ap = argparse.ArgumentParser(description="RootRecord specialist router (keyword/regex scoring).")  # info: set ap
    ap.add_argument("prompt", nargs="*")  # info: ap . add_argument ( "prompt" , nargs =
    ap.add_argument("--voice", default=os.environ.get("RR_VOICE", ""))  # info: ap . add_argument ( "--voice" , default =
    ap.add_argument("--config", default=os.environ.get("RR_SPECIALIST_ROUTES", str(DEFAULT_CONFIG)))  # info: ap . add_argument ( "--config" , default =
    ap.add_argument("--caller", default=os.environ.get("RR_CALLER", ""))  # info: ap . add_argument ( "--caller" , default =
    g = ap.add_mutually_exclusive_group()  # info: set g
    g.add_argument("--explain", action="store_true", help="show per-specialist scores and matched terms")  # info: g . add_argument ( "--explain" , action =
    g.add_argument("--json", action="store_true")  # info: g . add_argument ( "--json" , action =
    g.add_argument("--shell", action="store_true", help="KEY=VALUE lines (shell-quoted) for eval in run-infer.sh")  # info: g . add_argument ( "--shell" , action =
    g.add_argument("--list", action="store_true")  # info: g . add_argument ( "--list" , action =
    g.add_argument("--system", metavar="SPECIALIST", help="print the specialist's SYSTEM block")  # info: g . add_argument ( "--system" , metavar =
    ap.add_argument("--with-system", action="store_true", help="--shell: also emit RR_SPEC_SYSTEM (+ temperature/max tokens)")  # info: ap . add_argument ( "--with-system" , action =
    ap.add_argument("--verify-model", action="store_true", help="check ollama /api/tags; use fallback if model missing")  # info: ap . add_argument ( "--verify-model" , action =
    ap.add_argument("--no-log", action="store_true")  # info: ap . add_argument ( "--no-log" , action =
    ap.add_argument("--force", metavar="SPECIALIST", default="", help="explicit specialist (no scoring, confidence 1.0); unknown -> generic")  # info: ap . add_argument ( "--force" , metavar =
    a = ap.parse_args(argv)  # info: set a

    t0 = time.perf_counter_ns()  # info: set t0
    try:  # info: try :
        cfg = load_config(Path(a.config))  # info: set cfg
    except Exception as e:  # fail-safe: behave like routing is off
        print(f"[warn] route-specialist: config unreadable ({type(e).__name__}); generic", file=sys.stderr)  # info: call print
        if a.shell:  # info: if a . shell :
            print("RR_SPEC_NAME=generic\nRR_SPEC_DEFAULT=1\nRR_SPEC_CONFIDENCE=0")  # info: call print
        else:  # info: else :
            print("generic 0")  # info: call print
        return 0  # info: return 0

    if a.list:  # info: if a . list :
        print(f"{'specialist':<18} {'function':<10} {'prefer':<7} {'ollama_model':<18} fallback")  # info: call print
        for n, s in cfg["specialists"].items():  # info: for n , s in cfg [ "specialists"
            print(f"{n:<18} {s.get('function',''):<10} {s.get('prefer',''):<7} {s['ollama_model']:<18} {s.get('fallback','')}")  # info: call print
        return 0  # info: return 0
    if a.system:  # info: if a . system :
        spec = cfg["specialists"].get(a.system)  # info: set spec
        if not spec:  # info: if not spec :
            print(f"[fail] unknown specialist {a.system}", file=sys.stderr)  # info: call print
            return 2  # info: return 2
        print(parse_modelfile(Path(cfg["modelfile_root"]) / spec["modelfile"])["system"])  # info: call print
        return 0  # info: return 0

    prompt = " ".join(a.prompt) if a.prompt else ("" if sys.stdin.isatty() else sys.stdin.read())  # info: set prompt
    caller = a.caller or (Path(f"/proc/{os.getppid()}/comm").read_text().strip() if Path(f"/proc/{os.getppid()}/comm").exists() else "")  # info: set caller
    err = None  # info: set err
    try:  # info: try :
        d = (forced(cfg, a.force, a.voice or None, verify=a.verify_model) if a.force  # info: set d
             else decide(cfg, prompt, a.voice or None, verify=a.verify_model))  # info: else decide ( cfg , prompt , a
    except Exception as e:  # info: except Exception as e :
        err = type(e).__name__  # info: set err
        d = {"specialist": "generic", "default_used": True, "confidence": 0.0, "score": 0, "threshold": cfg.get("threshold"),  # info: set d
             "ollama_model": cfg["default"].get("voice_models", {}).get((a.voice or "").lower()) or cfg["default"].get("fallback"),  # info: "ollama_model" : cfg [ "default" ] . get
             "prefer": "flm", "fallback": cfg["default"].get("fallback"), "matched": [], "modelfile": "", "voice": a.voice or None,  # info: "prefer" : "flm" , "fallback" : cfg [
             "flm_model": cfg.get("flm", {}).get("base_model"), "runner_up": None, "runner_up_score": 0, "model_verified": None, "_rows": []}  # info: "flm_model" : cfg . get ( "flm" ,
    elapsed_us = (time.perf_counter_ns() - t0) // 1000  # info: set elapsed_us
    if not a.no_log:  # info: if not a . no_log :
        log_decision(cfg, d, prompt, caller, elapsed_us, err)  # info: call log_decision

    if a.explain:  # info: if a . explain :
        print(explain(cfg, d, prompt))  # info: call print
    elif a.json:  # info: elif a . json :
        print(json.dumps({k: v for k, v in d.items() if not k.startswith("_")}, ensure_ascii=False))  # info: call print
    elif a.shell:  # info: elif a . shell :
        kv = {  # info: set kv
            "RR_SPEC_NAME": d["specialist"], "RR_SPEC_DEFAULT": "1" if d["default_used"] else "0",  # info: "RR_SPEC_NAME" : d [ "specialist" ] , "RR_SPEC_DEFAULT"
            "RR_SPEC_CONFIDENCE": d["confidence"], "RR_SPEC_OLLAMA_MODEL": d["ollama_model"] or "",  # info: "RR_SPEC_CONFIDENCE" : d [ "confidence" ] , "RR_SPEC_OLLAMA_MODEL"
            "RR_SPEC_PREFER": d["prefer"], "RR_SPEC_FLM_MODEL": d["flm_model"] or "", "RR_SPEC_FALLBACK": d["fallback"] or "",  # info: "RR_SPEC_PREFER" : d [ "prefer" ] , "RR_SPEC_FLM_MODEL"
            "RR_SPEC_MODELFILE": d["modelfile"],  # info: "RR_SPEC_MODELFILE" : d [ "modelfile" ] ,
        }  # info: }
        if a.with_system and d["modelfile"]:  # info: if a . with_system and d [ "modelfile"
            mf = parse_modelfile(Path(d["modelfile"]))  # info: set mf
            kv["RR_SPEC_SYSTEM"] = mf["system"]  # info: kv [ "RR_SPEC_SYSTEM" ] = mf [ "system"
            kv["RR_SPEC_TEMPERATURE"] = mf["params"].get("temperature", "")  # info: kv [ "RR_SPEC_TEMPERATURE" ] = mf [ "params"
            kv["RR_SPEC_MAX_TOKENS"] = mf["params"].get("num_predict", "")  # info: kv [ "RR_SPEC_MAX_TOKENS" ] = mf [ "params"
        for k, v in kv.items():  # info: for k , v in kv . items
            print(f"{k}={shlex.quote(str(v))}")  # info: call print
    else:  # info: else :
        print(f"{d['specialist']} {d['confidence']}")  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main(sys.argv[1:]))  # info: sys . exit ( main ( sys .
