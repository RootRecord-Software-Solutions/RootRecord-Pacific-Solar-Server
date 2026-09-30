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
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import re  # info: import re
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

PH = re.compile(r"\{\{[^{}]*\}\}")  # info: set PH
NUM = re.compile(r"\d+(?:[.:/,\-]\d+)*")  # info: set NUM


# ====================================================
# SECTION: function unfenced
# What it does: unfenced.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def unfenced(text: str) -> list[str]:  # info: def unfenced
    out, fence = [], False  # info: out , fence = [ ] , False
    for ln in text.splitlines():  # info: for ln in text . splitlines ( )
        if ln.strip().startswith("```"):  # info: if ln . strip ( ) . startswith
            fence = not fence  # info: set fence
            continue  # info: continue
        if not fence:  # info: if not fence :
            out.append(ln)  # info: out . append ( ln )
    return out  # info: return out


# ====================================================
# SECTION: function headings
# What it does: headings.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def headings(text: str) -> list[str]:  # info: def headings
    return [ln.strip() for ln in unfenced(text) if re.match(r"^#{1,6}\s", ln)]


# ====================================================
# SECTION: function heading_rx
# What it does: heading rx.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def heading_rx(tpl_heading: str) -> re.Pattern:  # info: def heading_rx
    parts = PH.split(tpl_heading)  # info: set parts
    return re.compile("^" + ".+?".join(re.escape(p) for p in parts) + "$")  # info: return re . compile ( "^" + ".+?"


# ====================================================
# SECTION: function tables
# What it does: tables.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tables(text: str) -> list[list[str]]:  # info: def tables
    lines = unfenced(text)  # info: set lines
    out = []  # info: set out
    for i, ln in enumerate(lines[:-1]):  # info: for i , ln in enumerate ( lines
        if ln.lstrip().startswith("|") and re.match(r"^\s*\|(\s*:?-{3,}:?\s*\|)+\s*$", lines[i + 1]):  # info: if ln . lstrip ( ) . startswith
            out.append([c.strip() for c in ln.strip().strip("|").split("|")])  # info: out . append ( [ c . strip
    return out  # info: return out


# ====================================================
# SECTION: function bold_fields
# What it does: bold fields.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def bold_fields(text: str) -> list[str]:  # info: def bold_fields
    out = []  # info: set out
    for ln in unfenced(text):  # info: for ln in unfenced ( text ) :
        m = re.match(r"^\*\*([^*]+?):\*\*", ln)  # info: set m
        if m:  # info: if m :
            out.append(m.group(1))  # info: out . append ( m . group (
        m = re.match(r"^\|\s*\*\*([^*]+?)\*\*\s*\|", ln)  # info: set m
        if m:  # info: if m :
            out.append("|" + m.group(1))  # info: out . append ( "|" + m .
    return out  # info: return out


# ====================================================
# SECTION: function number_tokens
# What it does: number tokens.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def number_tokens(text: str) -> list[str]:  # info: def number_tokens
    return NUM.findall(text)  # info: return NUM . findall ( text )


# ====================================================
# SECTION: function corpus_numbers
# What it does: corpus numbers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def corpus_numbers(corpus: str) -> set[str]:  # info: def corpus_numbers
    s = set()  # info: set s
    for t in NUM.findall(corpus):  # info: for t in NUM . findall ( corpus
        s.add(t)  # info: s . add ( t )
        for p in re.split(r"[.:/,\-]", t):  # info: for p in re . split ( r"[.:/,\-]"
            if p:  # info: if p :
                s.add(p)  # info: s . add ( p )
                s.add(p.lstrip("0") or "0")  # info: s . add ( p . lstrip (
        if re.fullmatch(r"\d{1,2}:\d{2}:\d{2}", t):  # info: if re . fullmatch ( r"\d{1,2}:\d{2}:\d{2}" , t
            s.add(t[:-3])  # HH:MM:SS also supports HH:MM
    return s  # info: return s


# ====================================================
# SECTION: function number_ok
# What it does: number ok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def number_ok(tok: str, have: set[str]) -> bool:  # info: def number_ok
    if tok in have:  # info: if tok in have :
        return True  # info: return True
    parts = [p for p in re.split(r"[.:/,\-]", tok) if p]  # info: set parts
    return all(p in have or (p.lstrip("0") or "0") in have for p in parts)  # info: return all ( p in have or (


# ====================================================
# SECTION: function validate
# What it does: validate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def validate(template: str, output: str, corpus: str = "", vocab: list | None = None) -> dict:  # info: def validate
    errors, flags = [], []  # info: errors , flags = [ ] , [
    th, oh = headings(template), headings(output)  # info: th , oh = headings ( template )
    if len(th) != len(oh):  # info: if len ( th ) != len (
        errors.append(f"heading count {len(oh)} != template {len(th)}")  # info: errors . append ( f" heading count { len
    for i, (t, o) in enumerate(zip(th, oh)):  # info: for i , ( t , o )
        if not heading_rx(t).match(o):  # info: if not heading_rx ( t ) . match
            errors.append(f"heading #{i + 1}: {o!r} does not match template {t!r}")
    tt, ot = tables(template), tables(output)  # info: tt , ot = tables ( template )
    if tt != ot:  # info: if tt != ot :
        errors.append(f"table columns differ: template {tt} vs output {ot}")  # info: errors . append ( f" table columns differ: template { tt
    tf, of = bold_fields(template), bold_fields(output)  # info: tf , of = bold_fields ( template )
    if tf != of:  # info: if tf != of :
        errors.append(f"field order differs: template {tf} vs output {of}")  # info: errors . append ( f" field order differs: template { tf
    left = PH.findall(output)  # info: set left
    if left:  # info: if left :
        errors.append(f"unfilled placeholders: {sorted(set(left))[:5]}")  # info: errors . append ( f" unfilled placeholders: { sorted
    for rule in vocab or []:  # info: for rule in vocab or [ ] :
        desc, rx, allowed = rule["desc"], re.compile(rule["regex"], re.M), rule["allowed"]  # info: desc , rx , allowed = rule [
        vals = rx.findall(output)  # info: set vals
        if rule.get("first_only"):  # info: if rule . get ( "first_only" ) :
            vals = vals[:1]  # info: set vals
        if not vals and rule.get("required", True):  # info: if not vals and rule . get (
            errors.append(f"vocabulary: {desc}: no value found")  # info: errors . append ( f" vocabulary: { desc
        for v in vals:  # info: for v in vals :
            v = v if isinstance(v, str) else v[-1]  # info: set v
            ok = any(re.fullmatch(a, v.strip()) for a in allowed)  # info: set ok
            if not ok:  # info: if not ok :
                errors.append(f"vocabulary: {desc}: {v.strip()!r} not in {allowed}")  # info: errors . append ( f" vocabulary: { desc
    if corpus:  # info: if corpus :
        have = corpus_numbers(corpus + "\n" + template)  # info: set have
        seen = set()  # info: set seen
        for tok in number_tokens(output):  # info: for tok in number_tokens ( output ) :
            if tok not in seen and not number_ok(tok, have):  # info: if tok not in seen and not number_ok
                flags.append(tok)  # info: flags . append ( tok )
            seen.add(tok)  # info: seen . add ( tok )
    return {"ok": not errors, "errors": errors, "unsupported_numbers": flags,  # info: return { "ok" : not errors , "errors"
            "headings": len(oh), "tables": len(ot), "fields": len(of)}  # info: "headings" : len ( oh ) , "tables"


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str]) -> int:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("template")  # info: ap . add_argument ( "template" )
    ap.add_argument("output")  # info: ap . add_argument ( "output" )
    ap.add_argument("--corpus", default="")  # info: ap . add_argument ( "--corpus" , default =
    a = ap.parse_args(argv)  # info: set a
    corpus = Path(a.corpus).read_text(encoding="utf-8") if a.corpus else ""  # info: set corpus
    r = validate(Path(a.template).read_text(encoding="utf-8"), Path(a.output).read_text(encoding="utf-8"), corpus)  # info: set r
    print(json.dumps(r, indent=2, ensure_ascii=False))  # info: call print
    return 0 if r["ok"] else 1  # info: return 0 if r [ "ok" ] else


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main(sys.argv[1:]))  # info: sys . exit ( main ( sys .
