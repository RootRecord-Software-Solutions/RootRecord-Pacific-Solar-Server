#!/usr/bin/env python3
# ==============================================================================
# # INFO — unit-style test for route-specialist.py (no models are run)
# Usage: test-route-specialist.py [--out <markdown table path>]
# Routes labelled sample prompts, prints an accuracy table, and checks the JSONL log is
# metadata-only (no prompt text) using a throwaway log file. Exit 0 = accuracy >= 90% and privacy OK.
# HOW TO ADD: append (prompt, expected, voice) rows to CASES when a specialist or keyword changes.
# Created 2026-09-29 HST (g3-specialists).
# ==============================================================================
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("route_specialist", HERE / "route-specialist.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

CASES = [
    # (prompt, expected specialist, voice)
    ("What's the battery SOC on the Delta 2 right now?", "rr-energy", "bruce"),
    ("How many watts are the solar panels making?", "rr-energy", "ava"),
    ("Is the River 2 Pro charging the laptop?", "rr-energy", "carly"),
    ("Can we afford to run the 3b model on our power budget tonight?", "rr-energy", "bruce"),
    ("Any rain or high surf advisory for Hilo this weekend?", "rr-weather", "ava"),
    ("Is Kīlauea erupting today?", "rr-weather", "carly"),
    ("Was there an earthquake near Hawaiʻi last night?", "rr-weather", "ava"),
    ("Is that hurricane going to hit the islands?", "rr-weather", "bruce"),
    ("Why is the poller down again?", "rr-system", "bruce"),
    ("How much RAM and swap is the desk using?", "rr-system", "bruce"),
    ("Is the NPU busy or is flm stuck?", "rr-system", "ava"),
    ("Check whether the cloudflared tunnel service is running", "rr-system", "bruce"),
    ("Did someone leak the Telegram bot token in chat?", "rr-security", "carly"),
    ("How should we harden SSH on the desk?", "rr-security", "carly"),
    ("Is this link a phishing scam?", "rr-security", "ava"),
    ("Check the failed login attempts and firewall rules", "rr-security", "carly"),
    ("Is camera ch1 grabbing frames?", "rr-cameras", "bruce"),
    ("Did the daily timelapse render finish?", "rr-cameras", "ava"),
    ("The Night Owl DVR footage looks blurry", "rr-cameras", "carly"),
    ("Give me a one-liner to find files bigger than 100 MB", "rr-exec", "bruce"),
    ("Write a bash script that backs up the config folder", "rr-exec", "bruce"),
    ("Convert this list to JSON", "rr-exec", "ava"),
    ("Compare the pros and cons of FLM versus Ollama for chat", "rr-reason", "ava"),
    ("Explain the trade-off between a single relay and two pollers", "rr-reason", "bruce"),
    ("Should we migrate first or build new features?", "rr-reason", "carly"),
    ("Ava, what do you think of the new website copy and tagline?", "rr-council-ava", "ava"),
    ("Draft a press release for Kīlauea Alerts branding", "rr-council-ava", "ava"),
    ("Bruce, write the runbook and rollout plan for the upgrade", "rr-council-bruce", "bruce"),
    ("Is this feasible for reliability, from an SRE view?", "rr-council-bruce", "bruce"),
    ("Carly, seal this public claim before it ships", "rr-council-carly", "carly"),
    ("Draft a work order for the billing tiers", "rr-council-carly", "carly"),
    ("hey ava", "generic", "ava"),
    ("good night everyone", "generic", "bruce"),
    ("thanks, that helped a lot", "generic", "carly"),
    ("lol", "generic", "ava"),
]

# Held-out prompts written AFTER the keyword table, never tuned against. Reported separately; not part of the gate.
HELDOUT = [
    ("Is it windy up at the site?", "rr-weather", "ava"),
    ("The batteries are almost dead, should we shut the NPU down?", "rr-energy", "bruce"),
    ("Can you check if the relay is running?", "rr-system", "bruce"),
    ("Is the solar panel cam showing glare?", "rr-cameras", "carly"),
    ("What would it cost in power to keep a model loaded all night?", "rr-energy", "bruce"),
    ("Tell me about RootMC", "rr-council-ava", "ava"),
    ("How do I restart the weather poller?", "rr-system", "bruce"),
    ("Someone posted our master-key file, what now?", "rr-security", "carly"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    cfg = rs.load_config(rs.DEFAULT_CONFIG)
    rows, ok = [], 0
    for prompt, want, voice in CASES:
        d = rs.decide(cfg, prompt, voice)
        hit = d["specialist"] == want
        ok += hit
        rows.append((prompt, voice, want, d["specialist"], d["confidence"], ", ".join(d["matched"]) or "-", hit))
    acc = ok / len(CASES)
    hrows, hok = [], 0
    for prompt, want, voice in HELDOUT:
        d = rs.decide(cfg, prompt, voice)
        hit = d["specialist"] == want
        hok += hit
        hrows.append((prompt, voice, want, d["specialist"], d["confidence"], ", ".join(d["matched"]) or "-", hit))

    # privacy: the JSONL line must hold names/lengths only
    with tempfile.TemporaryDirectory() as td:
        lf = Path(td) / "routing_test.jsonl"
        os.environ["RR_ROUTE_LOG_FILE"] = str(lf)
        os.environ["RR_ROUTE_LOG"] = "1"
        secret_prompt = "PRIVATE-MARKER-7731 what is the battery soc"
        d = rs.decide(cfg, secret_prompt, "ava")
        rs.log_decision(cfg, d, secret_prompt, "test", 1)
        line = lf.read_text(encoding="utf-8").strip()
        rec = json.loads(line)
        privacy_ok = ("PRIVATE-MARKER" not in line and "battery soc" not in line
                      and rec["prompt_chars"] == len(secret_prompt) and rec["specialist"] == "rr-energy")

    by = {}
    for r in rows:
        t = by.setdefault(r[2], [0, 0]); t[1] += 1; t[0] += r[6]
    out = [f"# Router test — route-specialist.py ({datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')})", "",
           f"**Accuracy: {ok}/{len(CASES)} = {acc:.1%}** · threshold {cfg['threshold']} · log privacy check: {'PASS' if privacy_ok else 'FAIL'} · no models run", "",
           "| # | Prompt | Voice | Expected | Routed | Confidence | Matched | OK |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {'✅' if r[6] else '❌'} |")
    out += ["", f"## Held-out prompts (not tuned against; informational): {hok}/{len(HELDOUT)} = {hok/len(HELDOUT):.1%}", "",
            "| # | Prompt | Voice | Expected | Routed | Confidence | Matched | OK |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for i, r in enumerate(hrows, 1):
        out.append(f"| H{i} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {'✅' if r[6] else '❌'} |")
    out += ["", "| Expected route | Correct |", "| --- | --- |"] + [f"| {k} | {v[0]}/{v[1]} |" for k, v in by.items()]
    text = "\n".join(out) + "\n"
    print(text)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"[ok] wrote {a.out}")
    return 0 if (acc >= 0.9 and privacy_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
