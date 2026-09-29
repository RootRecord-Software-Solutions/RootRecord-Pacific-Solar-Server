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
# Created 2026-09-29 HST (g3-specialists). Bak: /home/rootrecord/Database/GITHUB/
# ==============================================================================
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shlex
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parent.parent.parent
DEFAULT_CONFIG = PACIFIC / "System" / "config" / "specialist-routes.json"
ROUTER_VERSION = "1.0"

_OKINA = dict.fromkeys(map(ord, "\u02bb\u2018\u2019\u02bc'`\u00b4"), None)


def normalize(text: str) -> str:
    """Lowercase, strip diacritics and ʻokina so Hawaiʻi/Kīlauea match hawaii/kilauea."""
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return t.translate(_OKINA).lower()


def _norm_keep_backticks(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return t.translate(dict.fromkeys(map(ord, "\u02bb\u2018\u2019\u02bc'\u00b4"), None)).lower()


def term_pattern(term: str) -> re.Pattern:
    t = normalize(term).strip()
    prefix = t.endswith("*")
    if prefix:
        t = t[:-1]
    body = r"\s+".join(re.escape(p) for p in t.split())
    tail = r"[a-z0-9_-]*" if prefix else ""
    return re.compile(r"(?<![a-z0-9_])" + body + tail + r"(?![a-z0-9_])")


def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    for name, spec in cfg["specialists"].items():
        spec["_kw"] = [(k, int(w), term_pattern(k)) for k, w in spec.get("keywords", {}).items()]
        spec["_rx"] = [(r["name"], int(r["weight"]), re.compile(r["pattern"], re.M)) for r in spec.get("regex", [])]
    return cfg


def score(cfg: dict, prompt: str) -> list[dict]:
    text = normalize(prompt)
    text_bt = _norm_keep_backticks(prompt)  # regexes like inline_code need backticks
    rows = []
    prio = {n: i for i, n in enumerate(cfg.get("priority", []))}
    for name, spec in cfg["specialists"].items():
        total, matched = 0, []
        for kw, w, pat in spec["_kw"]:
            if pat.search(text):
                total += w
                matched.append(kw)
        for rname, w, pat in spec["_rx"]:
            if pat.search(text_bt):
                total += w
                matched.append("re:" + rname)
        rows.append({"name": name, "score": total, "matched": matched, "prio": prio.get(name, 999)})
    rows.sort(key=lambda r: (-r["score"], r["prio"]))
    return rows


def confidence(cfg: dict, top: int, second: int) -> float:
    if top <= 0:
        return 0.0
    sat = float(cfg.get("saturation", 6.0))
    strength = min(1.0, top / sat)
    margin = (top - second) / top
    return round(strength * (0.6 + 0.4 * margin), 3)


def parse_modelfile(path: Path) -> dict:
    """SYSTEM block + temperature/num_predict/num_ctx for the FLM system-message route."""
    out = {"system": "", "params": {}}
    try:
        txt = path.read_text(encoding="utf-8")
    except OSError:
        return out
    m = re.search(r'^SYSTEM\s+"""\n?(.*?)\n?"""', txt, re.S | re.M)
    if m:
        out["system"] = m.group(1).strip()
    for pm in re.finditer(r"^PARAMETER\s+(temperature|num_predict|num_ctx|top_p)\s+(\S+)", txt, re.M):
        try:
            out["params"][pm.group(1)] = float(pm.group(2)) if "." in pm.group(2) else int(pm.group(2))
        except ValueError:
            pass
    return out


def installed_models(timeout: float = 1.0) -> set[str] | None:
    host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    if not host.startswith("http"):
        host = "http://" + host
    try:
        with urllib.request.urlopen(host.rstrip("/") + "/api/tags", timeout=timeout) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return None
    names = set()
    for m in data.get("models", []):
        n = m.get("name") or m.get("model") or ""
        names.add(n)
        if n.endswith(":latest"):
            names.add(n[: -len(":latest")])
    return names


def decide(cfg: dict, prompt: str, voice: str | None, verify: bool = False) -> dict:
    rows = score(cfg, prompt)
    top, second = rows[0], (rows[1] if len(rows) > 1 else {"score": 0, "name": None})
    conf = confidence(cfg, top["score"], second["score"])
    thr = float(cfg.get("threshold", 0.3))
    dflt = cfg["default"]
    voice_model = dflt.get("voice_models", {}).get((voice or "").lower())
    if conf >= thr and top["score"] > 0:
        spec = cfg["specialists"][top["name"]]
        d = {
            "specialist": top["name"], "function": spec.get("function"), "default_used": False,
            "ollama_model": spec["ollama_model"], "prefer": spec.get("prefer", "flm"),
            "fallback": spec.get("fallback") or voice_model or dflt.get("fallback"),
            "modelfile": str(Path(cfg["modelfile_root"]) / spec["modelfile"]),
            "matched": top["matched"],
        }
    else:
        d = {
            "specialist": dflt.get("name", "generic"), "function": "default", "default_used": True,
            "ollama_model": voice_model or dflt.get("fallback"), "prefer": dflt.get("prefer", "flm"),
            "fallback": voice_model or dflt.get("fallback"), "modelfile": "", "matched": [],
        }
    d.update({
        "confidence": conf, "threshold": thr, "score": top["score"],
        "runner_up": second["name"] if second["score"] > 0 else None, "runner_up_score": second["score"],
        "flm_model": cfg.get("flm", {}).get("base_model", "llama3.2:1b"), "voice": voice or None,
        "model_verified": None, "_rows": rows,
    })
    if verify and d["ollama_model"]:
        have = installed_models()
        if have is not None:
            ok = d["ollama_model"] in have
            d["model_verified"] = ok
            if not ok and d.get("fallback"):
                d["ollama_model"] = d["fallback"]
    return d


def forced(cfg: dict, name: str, voice: str | None, verify: bool = False) -> dict:
    """Explicit specialist request (run-infer.sh RR_SPECIALIST=<name>, or TARGET=rr-*): no scoring, confidence 1.0.
    Unknown name -> generic (fail-safe)."""
    if name not in cfg["specialists"]:
        d = decide(cfg, "", voice, verify)
        d["matched"] = ["forced-unknown"]
        return d
    spec = cfg["specialists"][name]
    dflt = cfg["default"]
    voice_model = dflt.get("voice_models", {}).get((voice or "").lower())
    d = {"specialist": name, "function": spec.get("function"), "default_used": False, "ollama_model": spec["ollama_model"],
         "prefer": spec.get("prefer", "flm"), "fallback": spec.get("fallback") or voice_model or dflt.get("fallback"),
         "modelfile": str(Path(cfg["modelfile_root"]) / spec["modelfile"]), "matched": ["forced"],
         "confidence": 1.0, "threshold": float(cfg.get("threshold", 0.3)), "score": 0, "runner_up": None, "runner_up_score": 0,
         "flm_model": cfg.get("flm", {}).get("base_model", "llama3.2:1b"), "voice": voice or None, "model_verified": None, "_rows": []}
    if verify:
        have = installed_models()
        if have is not None:
            d["model_verified"] = d["ollama_model"] in have
            if not d["model_verified"] and d.get("fallback"):
                d["ollama_model"] = d["fallback"]
    return d


def log_decision(cfg: dict, d: dict, prompt: str, caller: str, elapsed_us: int, error: str | None = None) -> None:
    if os.environ.get("RR_ROUTE_LOG", "1") != "1":
        return
    path = Path(os.environ.get("RR_ROUTE_LOG_FILE") or cfg.get("log_file", ""))
    if not str(path):
        return
    rec = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "router": ROUTER_VERSION, "caller": re.sub(r"[^A-Za-z0-9._:@/+-]", "", caller or "unknown")[:64],
        "voice": d.get("voice"), "specialist": d.get("specialist"), "default_used": d.get("default_used"),
        "confidence": d.get("confidence"), "score": d.get("score"), "threshold": d.get("threshold"),
        "runner_up": d.get("runner_up"), "runner_up_score": d.get("runner_up_score"),
        "matched": d.get("matched", []),  # config keyword / rule NAMES only
        "prefer": d.get("prefer"), "ollama_model": d.get("ollama_model"), "model_verified": d.get("model_verified"),
        "prompt_chars": len(prompt or ""), "elapsed_us": elapsed_us,
    }
    if error:
        rec["error"] = error[:120]
    try:
        import fcntl
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging must never break routing


def explain(cfg: dict, d: dict, prompt: str) -> str:
    lines = [f"prompt_chars={len(prompt)}  voice={d['voice'] or '-'}  threshold={d['threshold']}  saturation={cfg.get('saturation', 6.0)}",
             "confidence = min(1, top/saturation) * (0.6 + 0.4*(top-second)/top)", "",
             f"{'specialist':<18} {'score':>5}  matched"]
    for r in d["_rows"]:
        lines.append(f"{r['name']:<18} {r['score']:>5}  {', '.join(r['matched']) or '-'}")
    lines += ["", f"-> {d['specialist']}  confidence={d['confidence']}  default_used={d['default_used']}",
              f"   ollama_model={d['ollama_model']}  prefer={d['prefer']}  flm_model={d['flm_model']}  fallback={d['fallback']}"]
    if d["modelfile"]:
        lines.append(f"   modelfile={d['modelfile']}")
    if d["prefer"] == "flm" and not d["default_used"]:
        lines.append("   FLM route: SYSTEM block of the modelfile is sent as the system message to " + d["flm_model"])
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="RootRecord specialist router (keyword/regex scoring).")
    ap.add_argument("prompt", nargs="*")
    ap.add_argument("--voice", default=os.environ.get("RR_VOICE", ""))
    ap.add_argument("--config", default=os.environ.get("RR_SPECIALIST_ROUTES", str(DEFAULT_CONFIG)))
    ap.add_argument("--caller", default=os.environ.get("RR_CALLER", ""))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--explain", action="store_true", help="show per-specialist scores and matched terms")
    g.add_argument("--json", action="store_true")
    g.add_argument("--shell", action="store_true", help="KEY=VALUE lines (shell-quoted) for eval in run-infer.sh")
    g.add_argument("--list", action="store_true")
    g.add_argument("--system", metavar="SPECIALIST", help="print the specialist's SYSTEM block")
    ap.add_argument("--with-system", action="store_true", help="--shell: also emit RR_SPEC_SYSTEM (+ temperature/max tokens)")
    ap.add_argument("--verify-model", action="store_true", help="check ollama /api/tags; use fallback if model missing")
    ap.add_argument("--no-log", action="store_true")
    ap.add_argument("--force", metavar="SPECIALIST", default="", help="explicit specialist (no scoring, confidence 1.0); unknown -> generic")
    a = ap.parse_args(argv)

    t0 = time.perf_counter_ns()
    try:
        cfg = load_config(Path(a.config))
    except Exception as e:  # fail-safe: behave like routing is off
        print(f"[warn] route-specialist: config unreadable ({type(e).__name__}); generic", file=sys.stderr)
        if a.shell:
            print("RR_SPEC_NAME=generic\nRR_SPEC_DEFAULT=1\nRR_SPEC_CONFIDENCE=0")
        else:
            print("generic 0")
        return 0

    if a.list:
        print(f"{'specialist':<18} {'function':<10} {'prefer':<7} {'ollama_model':<18} fallback")
        for n, s in cfg["specialists"].items():
            print(f"{n:<18} {s.get('function',''):<10} {s.get('prefer',''):<7} {s['ollama_model']:<18} {s.get('fallback','')}")
        return 0
    if a.system:
        spec = cfg["specialists"].get(a.system)
        if not spec:
            print(f"[fail] unknown specialist {a.system}", file=sys.stderr)
            return 2
        print(parse_modelfile(Path(cfg["modelfile_root"]) / spec["modelfile"])["system"])
        return 0

    prompt = " ".join(a.prompt) if a.prompt else ("" if sys.stdin.isatty() else sys.stdin.read())
    caller = a.caller or (Path(f"/proc/{os.getppid()}/comm").read_text().strip() if Path(f"/proc/{os.getppid()}/comm").exists() else "")
    err = None
    try:
        d = (forced(cfg, a.force, a.voice or None, verify=a.verify_model) if a.force
             else decide(cfg, prompt, a.voice or None, verify=a.verify_model))
    except Exception as e:
        err = type(e).__name__
        d = {"specialist": "generic", "default_used": True, "confidence": 0.0, "score": 0, "threshold": cfg.get("threshold"),
             "ollama_model": cfg["default"].get("voice_models", {}).get((a.voice or "").lower()) or cfg["default"].get("fallback"),
             "prefer": "flm", "fallback": cfg["default"].get("fallback"), "matched": [], "modelfile": "", "voice": a.voice or None,
             "flm_model": cfg.get("flm", {}).get("base_model"), "runner_up": None, "runner_up_score": 0, "model_verified": None, "_rows": []}
    elapsed_us = (time.perf_counter_ns() - t0) // 1000
    if not a.no_log:
        log_decision(cfg, d, prompt, caller, elapsed_us, err)

    if a.explain:
        print(explain(cfg, d, prompt))
    elif a.json:
        print(json.dumps({k: v for k, v in d.items() if not k.startswith("_")}, ensure_ascii=False))
    elif a.shell:
        kv = {
            "RR_SPEC_NAME": d["specialist"], "RR_SPEC_DEFAULT": "1" if d["default_used"] else "0",
            "RR_SPEC_CONFIDENCE": d["confidence"], "RR_SPEC_OLLAMA_MODEL": d["ollama_model"] or "",
            "RR_SPEC_PREFER": d["prefer"], "RR_SPEC_FLM_MODEL": d["flm_model"] or "", "RR_SPEC_FALLBACK": d["fallback"] or "",
            "RR_SPEC_MODELFILE": d["modelfile"],
        }
        if a.with_system and d["modelfile"]:
            mf = parse_modelfile(Path(d["modelfile"]))
            kv["RR_SPEC_SYSTEM"] = mf["system"]
            kv["RR_SPEC_TEMPERATURE"] = mf["params"].get("temperature", "")
            kv["RR_SPEC_MAX_TOKENS"] = mf["params"].get("num_predict", "")
        for k, v in kv.items():
            print(f"{k}={shlex.quote(str(v))}")
    else:
        print(f"{d['specialist']} {d['confidence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
