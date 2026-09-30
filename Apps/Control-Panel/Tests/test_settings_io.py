# ==============================================================================
# FILE: Apps/Control-Panel/Tests/test_settings_io.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""test_settings_io.py — Root Monitor settings editor tests on TEMPORARY COPIES only (added 2026-09-29).

Never writes a real config file. For every registry file of an editable format it copies the file into a private
0700 temp dir, then: edits one setting (masked diff -> commit with backups into a temp backup root), checks
comments / key order / other lines / permissions are preserved, reverts and checks the copy is byte-identical,
replaces + clears a secret on secret files, and verifies the diff never shows secret values. All test output is
captured and scanned for the known secret values (only counts are printed). Temp dir is removed at the end.
"""
from __future__ import annotations  # info: from __future__ import annotations

import contextlib  # info: import contextlib
import io as _io  # info: import io as _io
import os  # info: import os
import shutil  # info: import shutil
import stat  # info: import stat
import sys  # info: import sys
import tempfile  # info: import tempfile
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # info: set HERE
sys.path.insert(0, str(HERE / "Lib"))  # info: sys . path . insert ( 0 ,
import rr_config_io as cio  # noqa: E402
import rr_registry as R  # noqa: E402

TMP_PARENT = Path("/home/rootrecord/Database/GITHUB/cps-work")  # info: set TMP_PARENT
results: list[tuple[str, str, str]] = []  # info: set results


# ====================================================
# SECTION: function rec
# What it does: rec.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def rec(name, ok, note=""):  # info: def rec
    results.append((name, "PASS" if ok else "FAIL", note))  # info: results . append ( ( name , "PASS"


# ====================================================
# SECTION: function pick_value
# What it does: pick value.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pick_value(s):  # info: def pick_value
    v = s.value_text()  # info: set v
    return {"port": "8798" if v != "8798" else "8797", "bool01": "0" if v == "1" else "1", "bool": "false" if v == "true" else "true",  # info: return { "port" : "8798" if v !=
            "int": str(int(v) + 1) if v.lstrip("-").isdigit() else "7", "float": "0.5" if v != "0.5" else "0.25",  # info: "int" : str ( int ( v )
            "url": "http://127.0.0.1:9/x", "host": "127.0.0.1" if v != "127.0.0.1" else "localhost"}.get(s.kind, (v or "x") + "_t")  # info: "url" : "http://127.0.0.1:9/x" , "host" : "127.0.0.1" if


# ====================================================
# SECTION: function comments
# What it does: comments.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def comments(text):  # info: def comments
    return [ln for ln in text.splitlines() if ln.lstrip().startswith(("#", ";"))]


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main():  # info: def main
    reg = R.Registry()  # info: set reg
    secrets = reg.secret_values()  # info: set secrets
    tmp = Path(tempfile.mkdtemp(prefix="rm-settings-test-", dir=str(TMP_PARENT)))  # info: set tmp
    os.chmod(tmp, 0o700)  # info: os . chmod ( tmp , 0o700 )
    bak_root = tmp / "backups"  # info: set bak_root
    buf = _io.StringIO()  # info: set buf
    try:  # info: try :
        with contextlib.redirect_stdout(buf):  # info: with contextlib . redirect_stdout ( buf ) :
            # ---- validation
            for kind, raw, want in (("port", "0", False), ("port", "65536", False), ("port", "8799", True), ("port", "80a", False),  # info: for kind , raw , want in (
                                    ("bool01", "2", False), ("bool01", "1", True), ("url", "notaurl", False),  # info: call (
                                    ("url", "https://x.example/a", True), ("int", "1.5", False), ("float", "abc", False)):  # info: call (
                ok, _n = cio.validate(kind, raw)  # info: ok , _n = cio . validate (
                rec(f"validate {kind} {raw!r}", ok == want)  # info: call rec
            seen_fmt = set()  # info: set seen_fmt
            for spec in R.FILES:  # info: for spec in R . FILES :
                if spec.fmt not in ("env", "ini", "json", "yaml", "tsv", "raw") or not spec.path.exists():  # info: if spec . fmt not in ( "env"
                    continue  # info: continue
                try:  # info: try :
                    orig = spec.path.read_bytes()  # info: set orig
                except PermissionError:  # info: except PermissionError :
                    continue  # info: continue
                cp = tmp / f"{spec.id.replace(':', '_').replace('/', '_')}{spec.path.suffix}"  # info: set cp
                cp.write_bytes(orig)  # info: cp . write_bytes ( orig )
                os.chmod(cp, stat.S_IMODE(spec.path.stat().st_mode))  # info: os . chmod ( cp , stat .
                mode0 = stat.S_IMODE(cp.stat().st_mode)  # info: set mode0
                text0 = orig.decode("utf-8", "surrogateescape")  # info: set text0
                sets = [s for s in reg.file_settings(spec) if s.key != "(file)"]  # info: set sets
                secret_keys = {s.key for s in sets if s.secret}  # info: set secret_keys
                # masking of the whole file
                mt = cio.masked_text(spec.fmt, text0, secret_keys, spec.secret_file, spec.columns)  # info: set mt
                rec(f"mask {spec.id}", not any(v in mt for v in secrets if len(v) >= 6))  # info: call rec
                # editable candidates: format rules only (read-only reasons of the REAL file are respected for real
                # saves; here we test the writer on copies)
                cand = [s for s in sets if not s.secret and s.kind not in ("complex", "info", "job") and not s.dup  # info: set cand
                        and not s.key.endswith(".id") and "structural" not in (s.ro_reason or "")]  # info: and not s . key . endswith (
                if cand:  # info: if cand :
                    s = cand[0]  # info: set s
                    new = pick_value(s)  # info: set new
                    ok, norm = cio.validate(s.kind, new)  # info: ok , norm = cio . validate (
                    if ok:  # info: if ok :
                        ino0 = cp.stat().st_ino  # info: set ino0
                        plan = cio.plan_edit(cp, spec.fmt, s.key, new, s.kind, secret_keys=secret_keys, whole_file_secret=spec.secret_file,  # info: set plan
                                             restart_note=spec.restart, columns=spec.columns)  # info: set restart_note
                        leak = any(v in plan.diff for v in secrets if len(v) >= 6)  # info: set leak
                        res = cio.commit(plan, bak_root)  # info: set res
                        t1 = cp.read_text(encoding="utf-8", errors="surrogateescape")  # info: set t1
                        changed = sum(1 for a, b in zip(text0.splitlines(), t1.splitlines()) if a != b)  # info: set changed
                        bak = Path(res["backup"])  # info: set bak
                        rec(f"edit {spec.fmt} {spec.id}:{s.key}",  # info: call rec
                            comments(t1) == comments(text0) and changed <= 1 and len(t1.splitlines()) == len(text0.splitlines())  # info: call comments
                            and stat.S_IMODE(cp.stat().st_mode) == mode0 and cp.stat().st_ino != ino0 and bak.read_bytes() == orig  # info: and stat . S_IMODE ( cp . stat
                            and stat.S_IMODE(bak.stat().st_mode) == (0o600 if plan.secret else mode0) and not leak,  # info: and stat . S_IMODE ( bak . stat
                            f"lines changed {changed}, mode {oct(mode0)}, backup mode {oct(stat.S_IMODE(bak.stat().st_mode))}")  # info: f" lines changed { changed } , mode { oct
                        # revert -> byte identical
                        oldv = s.value_text()  # info: set oldv
                        if spec.fmt == "json":  # info: if spec . fmt == "json" :
                            import json as _j  # info: import json as _j
                            oldv = _j.dumps(s._value) if not isinstance(s._value, str) else s._value  # info: set oldv
                        plan2 = cio.plan_edit(cp, spec.fmt, s.key, oldv, "str" if spec.fmt != "json" else s.kind,  # info: set plan2
                                              secret_keys=secret_keys, whole_file_secret=spec.secret_file, restart_note="", columns=spec.columns)  # info: set secret_keys
                        cio.commit(plan2, bak_root)  # info: cio . commit ( plan2 , bak_root )
                        rec(f"round-trip {spec.fmt} {spec.id}", cp.read_bytes() == orig)  # info: call rec
                        seen_fmt.add(spec.fmt)  # info: seen_fmt . add ( spec . fmt )
                        # stale-plan refusal
                        plan3 = cio.plan_edit(cp, spec.fmt, s.key, new, s.kind, secret_keys=secret_keys, whole_file_secret=spec.secret_file,  # info: set plan3
                                              restart_note="", columns=spec.columns)  # info: set restart_note
                        cp.write_bytes(orig + b" ")  # someone else changed the file after the diff was shown
                        try:  # info: try :
                            cio.commit(plan3, bak_root)  # info: cio . commit ( plan3 , bak_root )
                            rec(f"stale-plan refused {spec.id}", False)  # info: call rec
                        except RuntimeError:  # info: except RuntimeError :
                            rec(f"stale-plan refused {spec.id}", True)  # info: call rec
                        cp.write_bytes(orig)  # info: cp . write_bytes ( orig )
                # secret replace / clear on the copy
                sec = [s for s in sets if s.secret and spec.fmt in ("env", "ini", "yaml", "tsv", "json") and s.kind != "complex"  # info: set sec
                       and isinstance(s._value, str) and not isinstance(s._value, bool)]  # info: call and
                if sec:  # info: if sec :
                    s = sec[0]  # info: set s
                    dummy = "RMTESTVALUE_" + "q" * 20  # info: set dummy
                    plan = cio.plan_edit(cp, spec.fmt, s.key, dummy, "str", secret_keys=secret_keys, whole_file_secret=spec.secret_file,  # info: set plan
                                         restart_note="", columns=spec.columns)  # info: set restart_note
                    ok_mask = dummy not in plan.diff and not any(v in plan.diff for v in secrets if len(v) >= 6)  # info: set ok_mask
                    res = cio.commit(plan, bak_root)  # info: set res
                    b = Path(res["backup"])  # info: set b
                    ok_bak = stat.S_IMODE(b.stat().st_mode) == 0o600  # info: set ok_bak
                    plan = cio.plan_edit(cp, spec.fmt, s.key, "", "str", secret_keys=secret_keys, whole_file_secret=spec.secret_file,  # info: set plan
                                         restart_note="", columns=spec.columns)  # info: set restart_note
                    ok_clear = dummy not in plan.diff  # info: set ok_clear
                    rec(f"secret replace+clear {spec.id}", ok_mask and ok_bak and ok_clear, "diff masked, backup 0600")  # info: call rec
                if spec.fmt == "raw" and spec.secret_file:  # info: if spec . fmt == "raw" and spec
                    plan = cio.plan_edit(cp, "raw", "(file)", "RMTESTVALUE_raw", "str", secret_keys=set(), whole_file_secret=True,  # info: set plan
                                         restart_note="", columns=None)  # info: set restart_note
                    rec(f"raw secret diff masked {spec.id}", "RMTESTVALUE_raw" not in plan.diff and not any(v in plan.diff for v in secrets))  # info: call rec
            # git-tracked secret refusal (registry level, real path, nothing written)
            flagged = [s for p, _t in R.PAGES for s in reg.page_settings(p) if s.secret and "git-tracked" in (s.ro_reason or "")]  # info: set flagged
            refused = 0  # info: set refused
            for s in flagged:  # info: for s in flagged :
                try:  # info: try :
                    reg.plan(s, "x")  # info: reg . plan ( s , "x" )
                except ValueError:  # info: except ValueError :
                    refused += 1  # info: set refused
            rec("git-tracked secrets refused", refused == len(flagged), f"{len(flagged)} flagged, {refused} refused")  # info: call rec
            rec("formats covered", {"env", "ini", "json", "yaml", "tsv"} <= seen_fmt, ",".join(sorted(seen_fmt)))  # info: call rec
        out = buf.getvalue()  # info: set out
        leaks = sum(1 for v in secrets if len(v) >= 6 and v in out)  # info: set leaks
    finally:  # info: finally :
        left = [p.name for p in tmp.iterdir() if p.name.endswith(".tmp")] if tmp.exists() else []  # info: set left
        shutil.rmtree(tmp, ignore_errors=True)  # info: shutil . rmtree ( tmp , ignore_errors =
    for n, st, note in results:  # info: for n , st , note in results
        print(f"{st}  {n}" + (f"  ({note})" if note else ""))  # info: call print
    print(f"temp files left behind: {len(left)} · temp dir removed: {not tmp.exists()}")  # info: call print
    print(f"stdout leak scan: {len(secrets)} known secret values vs captured output -> {leaks} leaks")  # info: call print
    fails = sum(1 for _n, st, _x in results if st == "FAIL") + (1 if leaks else 0) + (1 if left else 0)  # info: set fails
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(results)} checks, {fails} failures)")  # info: call print
    return 1 if fails else 0  # info: return 1 if fails else 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
