#!/usr/bin/env python3
"""test_settings_io.py — Root Monitor settings editor tests on TEMPORARY COPIES only (added 2026-09-29).

Never writes a real config file. For every registry file of an editable format it copies the file into a private
0700 temp dir, then: edits one setting (masked diff -> commit with backups into a temp backup root), checks
comments / key order / other lines / permissions are preserved, reverts and checks the copy is byte-identical,
replaces + clears a secret on secret files, and verifies the diff never shows secret values. All test output is
captured and scanned for the known secret values (only counts are printed). Temp dir is removed at the end.
"""
from __future__ import annotations

import contextlib
import io as _io
import os
import shutil
import stat
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "Lib"))
import rr_config_io as cio  # noqa: E402
import rr_registry as R  # noqa: E402

TMP_PARENT = Path("/home/rootrecord/Database/GITHUB/cps-work")
results: list[tuple[str, str, str]] = []


def rec(name, ok, note=""):
    results.append((name, "PASS" if ok else "FAIL", note))


def pick_value(s):
    v = s.value_text()
    return {"port": "8798" if v != "8798" else "8797", "bool01": "0" if v == "1" else "1", "bool": "false" if v == "true" else "true",
            "int": str(int(v) + 1) if v.lstrip("-").isdigit() else "7", "float": "0.5" if v != "0.5" else "0.25",
            "url": "http://127.0.0.1:9/x", "host": "127.0.0.1" if v != "127.0.0.1" else "localhost"}.get(s.kind, (v or "x") + "_t")


def comments(text):
    return [ln for ln in text.splitlines() if ln.lstrip().startswith(("#", ";"))]


def main():
    reg = R.Registry()
    secrets = reg.secret_values()
    tmp = Path(tempfile.mkdtemp(prefix="rm-settings-test-", dir=str(TMP_PARENT)))
    os.chmod(tmp, 0o700)
    bak_root = tmp / "backups"
    buf = _io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            # ---- validation
            for kind, raw, want in (("port", "0", False), ("port", "65536", False), ("port", "8799", True), ("port", "80a", False),
                                    ("bool01", "2", False), ("bool01", "1", True), ("url", "notaurl", False),
                                    ("url", "https://x.example/a", True), ("int", "1.5", False), ("float", "abc", False)):
                ok, _n = cio.validate(kind, raw)
                rec(f"validate {kind} {raw!r}", ok == want)
            seen_fmt = set()
            for spec in R.FILES:
                if spec.fmt not in ("env", "ini", "json", "yaml", "tsv", "raw") or not spec.path.exists():
                    continue
                try:
                    orig = spec.path.read_bytes()
                except PermissionError:
                    continue
                cp = tmp / f"{spec.id.replace(':', '_').replace('/', '_')}{spec.path.suffix}"
                cp.write_bytes(orig)
                os.chmod(cp, stat.S_IMODE(spec.path.stat().st_mode))
                mode0 = stat.S_IMODE(cp.stat().st_mode)
                text0 = orig.decode("utf-8", "surrogateescape")
                sets = [s for s in reg.file_settings(spec) if s.key != "(file)"]
                secret_keys = {s.key for s in sets if s.secret}
                # masking of the whole file
                mt = cio.masked_text(spec.fmt, text0, secret_keys, spec.secret_file, spec.columns)
                rec(f"mask {spec.id}", not any(v in mt for v in secrets if len(v) >= 6))
                # editable candidates: format rules only (read-only reasons of the REAL file are respected for real
                # saves; here we test the writer on copies)
                cand = [s for s in sets if not s.secret and s.kind not in ("complex", "info", "job") and not s.dup
                        and not s.key.endswith(".id") and "structural" not in (s.ro_reason or "")]
                if cand:
                    s = cand[0]
                    new = pick_value(s)
                    ok, norm = cio.validate(s.kind, new)
                    if ok:
                        ino0 = cp.stat().st_ino
                        plan = cio.plan_edit(cp, spec.fmt, s.key, new, s.kind, secret_keys=secret_keys, whole_file_secret=spec.secret_file,
                                             restart_note=spec.restart, columns=spec.columns)
                        leak = any(v in plan.diff for v in secrets if len(v) >= 6)
                        res = cio.commit(plan, bak_root)
                        t1 = cp.read_text(encoding="utf-8", errors="surrogateescape")
                        changed = sum(1 for a, b in zip(text0.splitlines(), t1.splitlines()) if a != b)
                        bak = Path(res["backup"])
                        rec(f"edit {spec.fmt} {spec.id}:{s.key}",
                            comments(t1) == comments(text0) and changed <= 1 and len(t1.splitlines()) == len(text0.splitlines())
                            and stat.S_IMODE(cp.stat().st_mode) == mode0 and cp.stat().st_ino != ino0 and bak.read_bytes() == orig
                            and stat.S_IMODE(bak.stat().st_mode) == (0o600 if plan.secret else mode0) and not leak,
                            f"lines changed {changed}, mode {oct(mode0)}, backup mode {oct(stat.S_IMODE(bak.stat().st_mode))}")
                        # revert -> byte identical
                        oldv = s.value_text()
                        if spec.fmt == "json":
                            import json as _j
                            oldv = _j.dumps(s._value) if not isinstance(s._value, str) else s._value
                        plan2 = cio.plan_edit(cp, spec.fmt, s.key, oldv, "str" if spec.fmt != "json" else s.kind,
                                              secret_keys=secret_keys, whole_file_secret=spec.secret_file, restart_note="", columns=spec.columns)
                        cio.commit(plan2, bak_root)
                        rec(f"round-trip {spec.fmt} {spec.id}", cp.read_bytes() == orig)
                        seen_fmt.add(spec.fmt)
                        # stale-plan refusal
                        plan3 = cio.plan_edit(cp, spec.fmt, s.key, new, s.kind, secret_keys=secret_keys, whole_file_secret=spec.secret_file,
                                              restart_note="", columns=spec.columns)
                        cp.write_bytes(orig + (b"\n" if not orig.endswith(b"\n\n") else b""))
                        try:
                            cio.commit(plan3, bak_root)
                            rec(f"stale-plan refused {spec.id}", False)
                        except RuntimeError:
                            rec(f"stale-plan refused {spec.id}", True)
                        cp.write_bytes(orig)
                # secret replace / clear on the copy
                sec = [s for s in sets if s.secret and spec.fmt in ("env", "ini", "yaml", "tsv", "json") and s.kind != "complex"
                       and isinstance(s._value, (str, int, float))]
                if sec:
                    s = sec[0]
                    dummy = "RMTESTVALUE_" + "q" * 20
                    plan = cio.plan_edit(cp, spec.fmt, s.key, dummy, "str", secret_keys=secret_keys, whole_file_secret=spec.secret_file,
                                         restart_note="", columns=spec.columns)
                    ok_mask = dummy not in plan.diff and not any(v in plan.diff for v in secrets if len(v) >= 6)
                    res = cio.commit(plan, bak_root)
                    b = Path(res["backup"])
                    ok_bak = stat.S_IMODE(b.stat().st_mode) == 0o600
                    plan = cio.plan_edit(cp, spec.fmt, s.key, "", "str", secret_keys=secret_keys, whole_file_secret=spec.secret_file,
                                         restart_note="", columns=spec.columns)
                    ok_clear = dummy not in plan.diff
                    rec(f"secret replace+clear {spec.id}", ok_mask and ok_bak and ok_clear, "diff masked, backup 0600")
                if spec.fmt == "raw" and spec.secret_file:
                    plan = cio.plan_edit(cp, "raw", "(file)", "RMTESTVALUE_raw", "str", secret_keys=set(), whole_file_secret=True,
                                         restart_note="", columns=None)
                    rec(f"raw secret diff masked {spec.id}", "RMTESTVALUE_raw" not in plan.diff and not any(v in plan.diff for v in secrets))
            # git-tracked secret refusal (registry level, real path, nothing written)
            flagged = [s for p, _t in R.PAGES for s in reg.page_settings(p) if s.secret and "git-tracked" in (s.ro_reason or "")]
            refused = 0
            for s in flagged:
                try:
                    reg.plan(s, "x")
                except ValueError:
                    refused += 1
            rec("git-tracked secrets refused", refused == len(flagged), f"{len(flagged)} flagged, {refused} refused")
            rec("formats covered", {"env", "ini", "json", "yaml", "tsv"} <= seen_fmt, ",".join(sorted(seen_fmt)))
        out = buf.getvalue()
        leaks = sum(1 for v in secrets if len(v) >= 6 and v in out)
    finally:
        left = [p.name for p in tmp.iterdir() if p.name.endswith(".tmp")] if tmp.exists() else []
        shutil.rmtree(tmp, ignore_errors=True)
    for n, st, note in results:
        print(f"{st}  {n}" + (f"  ({note})" if note else ""))
    print(f"temp files left behind: {len(left)} · temp dir removed: {not tmp.exists()}")
    print(f"stdout leak scan: {len(secrets)} known secret values vs captured output -> {leaks} leaks")
    fails = sum(1 for _n, st, _x in results if st == "FAIL") + (1 if leaks else 0) + (1 if left else 0)
    print(f"RESULT: {'PASS' if not fails else 'FAIL'} ({len(results)} checks, {fails} failures)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
