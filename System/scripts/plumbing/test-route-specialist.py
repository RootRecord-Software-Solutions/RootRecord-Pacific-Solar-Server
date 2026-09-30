#!/usr/bin/env python3
# ==============================================================================
# # INFO — unit-style test for route-specialist.py (no models are run)
# Usage: test-route-specialist.py [--out <markdown table path>] [--heldout <file.json> ...]
# Routes labelled sample prompts, prints an accuracy table, and checks the JSONL log is
# metadata-only (no prompt text) using a throwaway log file. Exit 0 = accuracy >= 90% and privacy OK.
# HOW TO ADD: append (prompt, expected, voice) rows to CASES when a specialist or keyword changes.
# Created 2026-09-29 HST (g3-specialists).
# ==============================================================================
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import importlib.util  # info: import importlib . util
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
spec = importlib.util.spec_from_file_location("route_specialist", HERE / "route-specialist.py")  # info: set spec
rs = importlib.util.module_from_spec(spec)  # info: set rs
spec.loader.exec_module(rs)  # info: spec . loader . exec_module ( rs )

# ====================================================
# SECTION: CASES
# What it does: Set CASES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
CASES = [  # info: set CASES
    # (prompt, expected specialist, voice)
    ("What's the battery SOC on the Delta 2 right now?", "rr-energy", "bruce"),  # info: call (
    ("How many watts are the solar panels making?", "rr-energy", "ava"),  # info: call (
    ("Is the River 2 Pro charging the laptop?", "rr-energy", "carly"),  # info: call (
    ("Can we afford to run the 3b model on our power budget tonight?", "rr-energy", "bruce"),  # info: call (
    ("Any rain or high surf advisory for Hilo this weekend?", "rr-weather", "ava"),  # info: call (
    ("Is Kīlauea erupting today?", "rr-weather", "carly"),  # info: call (
    ("Was there an earthquake near Hawaiʻi last night?", "rr-weather", "ava"),  # info: call (
    ("Is that hurricane going to hit the islands?", "rr-weather", "bruce"),  # info: call (
    ("Why is the poller down again?", "rr-system", "bruce"),  # info: call (
    ("How much RAM and swap is the desk using?", "rr-system", "bruce"),  # info: call (
    ("Is the NPU busy or is flm stuck?", "rr-system", "ava"),  # info: call (
    ("Check whether the cloudflared tunnel service is running", "rr-system", "bruce"),  # info: call (
    ("Did someone leak the Telegram bot token in chat?", "rr-security", "carly"),  # info: call (
    ("How should we harden SSH on the desk?", "rr-security", "carly"),  # info: call (
    ("Is this link a phishing scam?", "rr-security", "ava"),  # info: call (
    ("Check the failed login attempts and firewall rules", "rr-security", "carly"),  # info: call (
    ("Is camera ch1 grabbing frames?", "rr-cameras", "bruce"),  # info: call (
    ("Did the daily timelapse render finish?", "rr-cameras", "ava"),  # info: call (
    ("The Night Owl DVR footage looks blurry", "rr-cameras", "carly"),  # info: call (
    ("Give me a one-liner to find files bigger than 100 MB", "rr-exec", "bruce"),  # info: call (
    ("Write a bash script that backs up the config folder", "rr-exec", "bruce"),  # info: call (
    ("Convert this list to JSON", "rr-exec", "ava"),  # info: call (
    ("Compare the pros and cons of FLM versus Ollama for chat", "rr-reason", "ava"),  # info: call (
    ("Explain the trade-off between a single relay and two pollers", "rr-reason", "bruce"),  # info: call (
    ("Should we migrate first or build new features?", "rr-reason", "carly"),  # info: call (
    ("Ava, what do you think of the new website copy and tagline?", "rr-council-ava", "ava"),  # info: call (
    ("Draft a press release for Kīlauea Alerts branding", "rr-council-ava", "ava"),  # info: call (
    ("Bruce, write the runbook and rollout plan for the upgrade", "rr-council-bruce", "bruce"),  # info: call (
    ("Is this feasible for reliability, from an SRE view?", "rr-council-bruce", "bruce"),  # info: call (
    ("Carly, seal this public claim before it ships", "rr-council-carly", "carly"),  # info: call (
    ("Draft a work order for the billing tiers", "rr-council-carly", "carly"),  # info: call (
    ("hey ava", "generic", "ava"),  # info: call (
    ("good night everyone", "generic", "bruce"),  # info: call (
    ("thanks, that helped a lot", "generic", "carly"),  # info: call (
    ("lol", "generic", "ava"),  # info: call (
    # v2 tuning rows (g3-router-v2, 2026-09-29): phrasing taken from Library domain docs (energy/weather/system/A-EYES/
    # security/public-surface WOs). Tuned against; the fresh held-out file below is NOT.
    ("What's the PV output on the panels today?", "rr-energy", "bruce"),  # info: call (
    ("Is the power bank charged enough for tonight?", "rr-energy", "ava"),  # info: call (
    ("Heavy showers expected on Maui?", "rr-weather", "ava"),  # info: call (
    ("What's the surf and swell looking like?", "rr-weather", "carly"),  # info: call (
    ("Did the auto-sync push to GitHub?", "rr-system", "bruce"),  # info: call (
    ("Is the internet down again?", "rr-system", "bruce"),  # info: call (
    ("Why does the tunnel keep disconnecting?", "rr-system", "bruce"),  # info: call (
    ("Show me the latest stills from A-EYES.", "rr-cameras", "ava"),  # info: call (
    ("Is the camera feed still recording?", "rr-cameras", "carly"),  # info: call (
    ("Was a bot token pushed to the public repo?", "rr-security", "carly"),  # info: call (
    ("Is it safe to expose port 8799?", "rr-security", "bruce"),  # info: call (
    ("Somebody tried to log in as root, is that an attack?", "rr-security", "carly"),  # info: call (
    ("Convert these timestamps into a markdown table.", "rr-exec", "ava"),  # info: call (
    ("Exact command to tail the automations log?", "rr-exec", "bruce"),  # info: call (
    ("What are the downsides of one NPU for everything?", "rr-reason", "bruce"),  # info: call (
    ("Walk me through whether to split the repos.", "rr-reason", "ava"),  # info: call (
    ("Write website copy for the solar board launch.", "rr-council-ava", "ava"),  # info: call (
    ("Hello there!", "generic", "bruce"),  # info: call (
]  # info: ]

# Held-out prompts written AFTER the keyword table, never tuned against. Reported separately; not part of the gate.
# ====================================================
# SECTION: HELDOUT
# What it does: Set HELDOUT.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
HELDOUT = [  # info: set HELDOUT
    ("Is it windy up at the site?", "rr-weather", "ava"),  # info: call (
    ("The batteries are almost dead, should we shut the NPU down?", "rr-energy", "bruce"),  # info: call (
    ("Can you check if the relay is running?", "rr-system", "bruce"),  # info: call (
    ("Is the solar panel cam showing glare?", "rr-cameras", "carly"),  # info: call (
    ("What would it cost in power to keep a model loaded all night?", "rr-energy", "bruce"),  # info: call (
    ("Tell me about RootMC", "rr-council-ava", "ava"),  # info: call (
    ("How do I restart the weather poller?", "rr-system", "bruce"),  # info: call (
    ("Someone posted our master-key file, what now?", "rr-security", "carly"),  # info: call (
]  # info: ]


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--out", default="")  # info: ap . add_argument ( "--out" , default =
    ap.add_argument("--heldout", action="append", default=[],  # info: ap . add_argument ( "--heldout" , action =
                    help="extra held-out JSON file(s) ({cases: [[prompt, expected, voice], ...]}); default: System/config/specialist-heldout-*.json")  # info: set help
    a = ap.parse_args()  # info: set a
    extra = [Path(x) for x in a.heldout] or sorted((HERE.parent.parent / "config").glob("specialist-heldout-*.json"))  # info: set extra
    cfg = rs.load_config(rs.DEFAULT_CONFIG)  # info: set cfg
    rows, ok = [], 0  # info: rows , ok = [ ] , 0
    for prompt, want, voice in CASES:  # info: for prompt , want , voice in CASES
        d = rs.decide(cfg, prompt, voice)  # info: set d
        hit = d["specialist"] == want  # info: set hit
        ok += hit  # info: set ok
        rows.append((prompt, voice, want, d["specialist"], d["confidence"], ", ".join(d["matched"]) or "-", hit))  # info: rows . append ( ( prompt , voice
    acc = ok / len(CASES)  # info: set acc
    hrows, hok = [], 0  # info: hrows , hok = [ ] , 0
    for prompt, want, voice in HELDOUT:  # info: for prompt , want , voice in HELDOUT
        d = rs.decide(cfg, prompt, voice)  # info: set d
        hit = d["specialist"] == want  # info: set hit
        hok += hit  # info: set hok
        hrows.append((prompt, voice, want, d["specialist"], d["confidence"], ", ".join(d["matched"]) or "-", hit))  # info: hrows . append ( ( prompt , voice

    # privacy: the JSONL line must hold names/lengths only
    with tempfile.TemporaryDirectory() as td:  # info: with tempfile . TemporaryDirectory ( ) as td
        lf = Path(td) / "routing_test.jsonl"  # info: set lf
        os.environ["RR_ROUTE_LOG_FILE"] = str(lf)  # info: os . environ [ "RR_ROUTE_LOG_FILE" ] = str
        os.environ["RR_ROUTE_LOG"] = "1"  # info: os . environ [ "RR_ROUTE_LOG" ] = "1"
        secret_prompt = "PRIVATE-MARKER-7731 what is the battery soc"  # info: set secret_prompt
        d = rs.decide(cfg, secret_prompt, "ava")  # info: set d
        rs.log_decision(cfg, d, secret_prompt, "test", 1)  # info: rs . log_decision ( cfg , d ,
        line = lf.read_text(encoding="utf-8").strip()  # info: set line
        rec = json.loads(line)  # info: set rec
        privacy_ok = ("PRIVATE-MARKER" not in line and "battery soc" not in line  # info: set privacy_ok
                      and rec["prompt_chars"] == len(secret_prompt) and rec["specialist"] == "rr-energy")  # info: and rec [ "prompt_chars" ] == len (

    by = {}  # info: set by
    for r in rows:  # info: for r in rows :
        t = by.setdefault(r[2], [0, 0]); t[1] += 1; t[0] += r[6]  # info: set t
    out = [f"# Router test — route-specialist.py ({datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')})", "",
           f"**Accuracy: {ok}/{len(CASES)} = {acc:.1%}** · threshold {cfg['threshold']} · log privacy check: {'PASS' if privacy_ok else 'FAIL'} · no models run", "",  # info: f" **Accuracy: { ok } / { len
           "| # | Prompt | Voice | Expected | Routed | Confidence | Matched | OK |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(rows, 1):  # info: for i , r in enumerate ( rows
        out.append(f"| {i} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {'✅' if r[6] else '❌'} |")  # info: out . append ( f" | { i
    out += ["", f"## Held-out prompts (not tuned against; informational): {hok}/{len(HELDOUT)} = {hok/len(HELDOUT):.1%}", "",
            "| # | Prompt | Voice | Expected | Routed | Confidence | Matched | OK |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(hrows, 1):  # info: for i , r in enumerate ( hrows
        out.append(f"| H{i} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {'✅' if r[6] else '❌'} |")  # info: out . append ( f" | H { i
    for hf in extra:  # info: for hf in extra :
        cases = json.loads(hf.read_text(encoding="utf-8"))["cases"]  # info: set cases
        xr = [(p_, v_, w_, rs.decide(cfg, p_, v_)) for p_, w_, v_ in cases]  # info: set xr
        xok = sum(d_["specialist"] == w_ for _, _, w_, d_ in xr)  # info: set xok
        out += ["", f"## Held-out file `{hf.name}` (never tuned against; provenance in the file's _info): {xok}/{len(xr)} = {xok/len(xr):.1%}", "",
                "| # | Prompt | Voice | Expected | Routed | Confidence | Matched | OK |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for i, (p_, v_, w_, d_) in enumerate(xr, 1):  # info: for i , ( p_ , v_ ,
            out.append(f"| X{i} | {p_} | {v_} | {w_} | {d_['specialist']} | {d_['confidence']} | {', '.join(d_['matched']) or '-'} | {'✅' if d_['specialist'] == w_ else '❌'} |")  # info: out . append ( f" | X { i
    out += ["", "| Expected route | Correct |", "| --- | --- |"] + [f"| {k} | {v[0]}/{v[1]} |" for k, v in by.items()]  # info: set out
    text = "\n".join(out) + "\n"  # info: set text
    print(text)  # info: call print
    if a.out:  # info: if a . out :
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)  # info: call Path
        Path(a.out).write_text(text, encoding="utf-8")  # info: call Path
        print(f"[ok] wrote {a.out}")  # info: call print
    return 0 if (acc >= 0.9 and privacy_ok) else 1  # info: return 0 if ( acc >= 0.9 and


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
