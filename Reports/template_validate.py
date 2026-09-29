#!/usr/bin/env python3
# ==============================================================================
# # INFO — template_validate.py: structure + number check for template-filled reports (stdlib)
# ------------------------------------------------------------------------------
# Usage: template_validate.py <template.md> <output.md> [--corpus <facts.txt>]
# Compares the output with its Library template and REJECTS any mismatch in:
#   headings (order + text; {{PLACEHOLDER}} spans match any text), table header columns (order),
#   bold field order (**Field:** lines and | **Field** | rows), leftover {{placeholders}},
#   and per-template status vocabulary rules (passed in by template_fill.py).
# FLAGS (does not reject) every number in the output that is not present in the source corpus.
# Fenced code blocks are ignored for headings/tables/fields. Used by Reports/template_fill.py.
# Created 2026-09-29 HST (g3-template-reports).
# ==============================================================================
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PH = re.compile(r"\{\{[^{}]*\}\}")
NUM = re.compile(r"\d+(?:[.:/,\-]\d+)*")


def unfenced(text: str) -> list[str]:
    out, fence = [], False
    for ln in text.splitlines():
        if ln.strip().startswith("```"):
            fence = not fence
            continue
        if not fence:
            out.append(ln)
    return out


def headings(text: str) -> list[str]:
    return [ln.strip() for ln in unfenced(text) if re.match(r"^#{1,6}\s", ln)]


def heading_rx(tpl_heading: str) -> re.Pattern:
    parts = PH.split(tpl_heading)
    return re.compile("^" + ".+?".join(re.escape(p) for p in parts) + "$")


def tables(text: str) -> list[list[str]]:
    lines = unfenced(text)
    out = []
    for i, ln in enumerate(lines[:-1]):
        if ln.lstrip().startswith("|") and re.match(r"^\s*\|(\s*:?-{3,}:?\s*\|)+\s*$", lines[i + 1]):
            out.append([c.strip() for c in ln.strip().strip("|").split("|")])
    return out


def bold_fields(text: str) -> list[str]:
    out = []
    for ln in unfenced(text):
        m = re.match(r"^\*\*([^*]+?):\*\*", ln)
        if m:
            out.append(m.group(1))
        m = re.match(r"^\|\s*\*\*([^*]+?)\*\*\s*\|", ln)
        if m:
            out.append("|" + m.group(1))
    return out


def number_tokens(text: str) -> list[str]:
    return NUM.findall(text)


def corpus_numbers(corpus: str) -> set[str]:
    s = set()
    for t in NUM.findall(corpus):
        s.add(t)
        for p in re.split(r"[.:/,\-]", t):
            if p:
                s.add(p)
                s.add(p.lstrip("0") or "0")
        if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}", t):
            s.add(t[:-3])  # HH:MM:SS also supports HH:MM
    return s


def number_ok(tok: str, have: set[str]) -> bool:
    if tok in have:
        return True
    parts = [p for p in re.split(r"[.:/,\-]", tok) if p]
    return all(p in have or (p.lstrip("0") or "0") in have for p in parts)


def validate(template: str, output: str, corpus: str = "", vocab: list | None = None) -> dict:
    errors, flags = [], []
    th, oh = headings(template), headings(output)
    if len(th) != len(oh):
        errors.append(f"heading count {len(oh)} != template {len(th)}")
    for i, (t, o) in enumerate(zip(th, oh)):
        if not heading_rx(t).match(o):
            errors.append(f"heading #{i + 1}: {o!r} does not match template {t!r}")
    tt, ot = tables(template), tables(output)
    if tt != ot:
        errors.append(f"table columns differ: template {tt} vs output {ot}")
    tf, of = bold_fields(template), bold_fields(output)
    if tf != of:
        errors.append(f"field order differs: template {tf} vs output {of}")
    left = PH.findall(output)
    if left:
        errors.append(f"unfilled placeholders: {sorted(set(left))[:5]}")
    for rule in vocab or []:
        desc, rx, allowed = rule["desc"], re.compile(rule["regex"], re.M), rule["allowed"]
        vals = rx.findall(output)
        if rule.get("first_only"):
            vals = vals[:1]
        if not vals and rule.get("required", True):
            errors.append(f"vocabulary: {desc}: no value found")
        for v in vals:
            v = v if isinstance(v, str) else v[-1]
            ok = any(re.fullmatch(a, v.strip()) for a in allowed)
            if not ok:
                errors.append(f"vocabulary: {desc}: {v.strip()!r} not in {allowed}")
    if corpus:
        have = corpus_numbers(corpus + "\n" + template)
        seen = set()
        for tok in number_tokens(output):
            if tok not in seen and not number_ok(tok, have):
                flags.append(tok)
            seen.add(tok)
    return {"ok": not errors, "errors": errors, "unsupported_numbers": flags,
            "headings": len(oh), "tables": len(ot), "fields": len(of)}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("output")
    ap.add_argument("--corpus", default="")
    a = ap.parse_args(argv)
    corpus = Path(a.corpus).read_text(encoding="utf-8") if a.corpus else ""
    r = validate(Path(a.template).read_text(encoding="utf-8"), Path(a.output).read_text(encoding="utf-8"), corpus)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
