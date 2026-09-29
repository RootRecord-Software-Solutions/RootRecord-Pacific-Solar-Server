#!/usr/bin/env python3
# ==============================================================================
# # INFO — template_fill.py: fill the Library operations templates from measured desk data (stdlib)
# ------------------------------------------------------------------------------
# Usage: template_fill.py [--all | --template worklog|checkpoint|event|workorder] [--date YYYY-MM-DD]
#                         [--draft none|model|auto] [--model-templates worklog,workorder] [--dry-run]
# Templates (read-only): Library Documentation/01-operations/templates/TEMPLATE *.md — same headings,
#   tables, field order, date formats (YYYY-MM-DD, HH:MM HST, HH_MM in filenames) and status vocabulary.
# Sources: Library 07-testing index, 08-ideas index, Work-Orders, operator worklogs of the day (sign-off list);
#   Database Logs/AI/Inference JSONL, Logs/Automations poller log (+ hourly Archive), System/last host sample,
#   Energy/soc, Media/Images, Weather reports, Worklog; read-only systemctl --user is-active / process checks.
# Free text ONLY (purpose, status line, next step, principle, scope, intent) is drafted by a specialist via
#   System/scripts/plumbing/run-infer.sh (TARGET rr-exec: NPU on demand, Ollama fallback keep_alive 0) with a
#   strict "use only the facts given" prompt. Drafts with unsupported numbers / bad shape -> deterministic text.
# Out: Database Reports/Generated/<Template-Name>_current.md (previous copy -> Archive/<name>_YYYY-MM-DDTHHMM.md
#   if changed) + template-fill-validation_current.json. NEVER writes into the Library (guarded).
# Validator: Reports/template_validate.py — structural mismatch => output rejected (<name>_rejected.md).
# Job: jobs.py id template_reports_daily, OFF unless RR_TEMPLATE_REPORTS=1 at poller start.
# HOW TO ADD a template: add a render_<key>() + TEMPLATES row (file, output name, vocab rules, free-text keys).
# Created 2026-09-29 HST (g3-template-reports). Bak: /home/rootrecord/Database/GITHUB/
# ==============================================================================
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import statistics
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parent
sys.path.insert(0, str(HERE))
import template_validate as tv  # noqa: E402

ECO = Path("/home/rootrecord/RootRecord-Ecosystem")
DB = Path(os.environ.get("RR_DATABASE_ROOT", str(ECO / "2 - RootRecord-Database")))
LIB = Path(os.environ.get("RR_LIBRARY_ROOT", str(ECO / "5 - RootRecord-Library")))
DOCS = LIB / "Documentation"
TPL_DIR = DOCS / "01-operations" / "templates"
OUT_DIR = Path(os.environ.get("RR_TEMPLATE_OUT", str(ECO / "test-reports" / "Templates")))
RUN_INFER = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"
SF = PACIFIC / "System" / "scripts" / "plumbing" / "single-flight.sh"
POLLER_LOG = DB / "Logs" / "Automations" / "automations_current.log"
INFER_LOG = DB / "Logs" / "AI" / "Inference" / "inference_current.jsonl"
SPECIALIST = os.environ.get("RR_TEMPLATE_SPECIALIST", "rr-exec")
MIN_MEM_MB_FOR_MODEL = 3072


# ------------------------------------------------------------------ helpers
def now() -> datetime:
    return datetime.now().astimezone()


def hm(dt: datetime) -> str:
    return dt.astimezone().strftime("%H:%M")


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def cell(s: str, n: int = 110) -> str:
    s = re.sub(r"\s+", " ", (s or "").replace("|", "/")).strip()
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)  # drop md links inside cells
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def mem_avail_mb() -> int:
    for ln in read(Path("/proc/meminfo")).splitlines():
        if ln.startswith("MemAvailable:"):
            return int(ln.split()[1]) // 1024
    return 0


def is_active(unit: str) -> str:
    try:
        r = subprocess.run(["systemctl", "--user", "is-active", unit], capture_output=True, text=True, timeout=3)
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def procs_matching(pred) -> int:
    n = 0
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            cmd = (d / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        except OSError:
            continue
        if pred(cmd):
            n += 1
    return n


def procs_by_comm(name: str) -> int:
    n = 0
    for d in Path("/proc").iterdir():
        if d.name.isdigit():
            try:
                n += (d / "comm").read_text().strip() == name
            except OSError:
                pass
    return n


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def age_min(dt: datetime | None, ref: datetime) -> float | None:
    return None if dt is None else (ref - dt).total_seconds() / 60


def newest_mtime(root: Path, pattern: str = "*", max_files: int = 200000) -> datetime | None:
    best = None
    try:
        for i, e in enumerate(os.scandir(root)):
            if i > max_files:
                break
            if e.is_file() and Path(e.name).match(pattern):
                m = e.stat().st_mtime
                best = m if best is None or m > best else best
    except OSError:
        return None
    return datetime.fromtimestamp(best).astimezone() if best else None


# ------------------------------------------------------------------ sources
class Facts:
    """Everything a report may state. corpus = every source string used (for the number check)."""

    def __init__(self, day: str):
        self.day, self.t = day, now()
        self.corpus: list[str] = [day, hm(self.t), self.t.strftime("%H_%M")]

    def add(self, *s):
        self.corpus.extend(str(x) for x in s)


def testing_records(f: Facts) -> list[dict]:
    rows = []
    for ln in read(DOCS / "07-testing" / "README.md").splitlines():
        m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s+(~?\d{2}:\d{2})\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(.+?)\s*\|\s*$", ln)
        if m and m.group(1) == f.day:
            rows.append({"time": m.group(2), "title": m.group(3), "file": m.group(4), "state": m.group(5)})
            f.add(ln)
    rows.sort(key=lambda r: r["time"].lstrip("~"))
    return rows


def ideas(f: Facts) -> list[dict]:
    rows = []
    for ln in read(DOCS / "08-ideas" / "README.md").splitlines():
        m = re.match(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*\[([^\]]+)\]\([^)]+\)\s*\|\s*(.+?)\s*\|", ln)
        if m:
            rows.append({"date": m.group(1), "title": m.group(2), "state": m.group(3)})
            f.add(ln)
    return rows


def signoff_items(f: Facts) -> list[str]:
    items = []
    logs = sorted((DOCS / "01-operations" / "0 - Human Operator Work Logs").glob(f"{f.day} *.md"))
    for p in logs:
        txt = read(p)
        m = re.search(r"^## Needs Alexander sign-off\s*$(.*?)(?=^## |\Z)", txt, re.M | re.S)
        if not m:
            continue
        for ln in m.group(1).splitlines():
            mm = re.match(r"^- \[ \] (.+)$", ln.strip())
            if mm:
                t = mm.group(1)
                b = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", t)
                if b and b.group(1).endswith(":"):  # "**Hardware tests:** Energy arm/disarm ..." -> keep the first clause
                    items.append(cell(b.group(1) + " " + re.split(r"(?<=[.;(])\s", b.group(2))[0].rstrip(".;("), 100))
                else:
                    items.append(cell(b.group(1).rstrip(".") if b else t, 100))
                f.add(ln)
    seen, out = set(), []
    for i in items:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def work_orders(f: Facts) -> list[dict]:
    rows = []
    for p in sorted((DOCS / "06-development" / "Work-Orders").glob("*.md")):
        if p.name == "README.md":
            continue
        txt = read(p)
        st = re.search(r"^\|\s*\*\*Status\*\*\s*\|\s*(.+?)\s*\|", txt, re.M)
        rows.append({"file": p.stem, "status": cell((st.group(1) if st else "not recorded").replace("**", ""), 80)})
        f.add(p.stem, st.group(0) if st else "")
    return rows


def inference(f: Facts) -> dict:
    files = [DB / "Logs" / "AI" / "Inference" / "Archive" / f"inference_{f.day}.jsonl", INFER_LOG]
    rows = []
    for p in files:
        for ln in read(p).splitlines():
            try:
                r = json.loads(ln)
                ts = datetime.fromisoformat(r["ts"])
            except Exception:
                continue
            if ts.astimezone().strftime("%Y-%m-%d") == f.day:
                r["_ts"] = ts
                rows.append(r)
                f.add(ln)
    rows.sort(key=lambda r: r["_ts"])
    lat = [r.get("latency_ms", 0) for r in rows]
    s = {"rows": rows, "n": len(rows), "fallbacks": sum(1 for r in rows if r.get("fallback")),
         "nonzero": sum(1 for r in rows if r.get("exit_code")), "p50": int(statistics.median(lat)) if lat else None,
         "max": max(lat) if lat else None,
         "min_mem": min((r.get("mem_avail_mb_after") for r in rows if r.get("mem_avail_mb_after")), default=None),
         "routes": sorted({r.get("route", "?") for r in rows})}
    f.add(s["n"], s["fallbacks"], s["nonzero"], s["p50"], s["max"], s["min_mem"])
    return s


def poller(f: Facts) -> dict:
    lines = []
    arch = sorted((DB / "Logs" / "Automations" / "Archive").glob(f"automations_{f.day}_*.log"))
    for p in arch + [POLLER_LOG]:
        lines += [ln for ln in read(p).splitlines() if ln.startswith(f.day)]
    fails = []
    for ln in lines:
        m = re.match(r"^(\S+?)job:(\S+) FAIL(.*)$", ln)
        if m:
            fails.append({"time": m.group(1)[11:16], "job": m.group(2), "detail": m.group(3).strip()})
            f.add(ln)
    runs = sum(1 for ln in lines if re.search(r"job:\S+ RUN ", ln))
    tunnel = [ln for ln in lines if ln[25:].startswith("tunnel ")]
    gh = [ln for ln in lines if "job:github_sync_all" in ln]
    gh_last = gh[-1] if gh else ""
    gh_bad = any(re.search(r"FAIL|error|fatal|rejected", ln, re.I) for ln in gh[-12:])
    s = {"lines": len(lines), "runs": runs, "fails": fails, "gh_last_time": gh_last[11:16] if gh_last else None, "gh_bad": gh_bad,
         "last_time": lines[-1][11:16] if lines else None, "tunnel": tunnel}
    f.add(s["lines"], s["runs"], s["gh_last_time"], s["last_time"])
    return s


def host(f: Facts) -> dict:
    try:
        d = json.loads(read(DB / "System" / "last" / "host-last.json"))
        fl = d.get("fields", {})
        obs = d.get("observed_at") or d.get("generated_at")
        at = datetime.fromisoformat(obs.replace("Z", "+00:00")).astimezone() if obs else None
        s = {"at": at, "load1": fl.get("load1", {}).get("value"), "cpu": fl.get("cpu_percent", {}).get("value"),
             "mem_avail_mb": int(fl["mem_available_bytes"]["value"] / 1048576) if "mem_available_bytes" in fl else None}
    except Exception:
        s = {"at": None, "load1": None, "cpu": None, "mem_avail_mb": None}
    if s["at"] is None:  # fall back to file mtime
        s["at"] = newest_mtime(DB / "System" / "last", "*.json")
    f.add(s["load1"], s["cpu"], s["mem_avail_mb"], hm(s["at"]) if s["at"] else "")
    return s


def energy(f: Facts) -> list[dict]:
    out = []
    for p in sorted((DB / "Energy" / "soc").glob("*-last.json")):
        try:
            d = json.loads(read(p))
            out.append({"pack": p.name.replace("-last.json", ""), "soc": d.get("soc"), "at": datetime.fromisoformat(d["at"]), "source": d.get("source")})
            f.add(read(p), hm(datetime.fromisoformat(d["at"])))
        except Exception:
            continue
    return out


def state_by_age(age: float | None, ok_min: float, degraded_min: float) -> str:
    if age is None:
        return "down"
    return "ok" if age <= ok_min else ("degraded" if age <= degraded_min else "down")


def subsystems(f: Facts, h: dict, en: list, pl: dict) -> list[tuple[str, str, str]]:
    t = f.t
    rows = []
    a = age_min(h["at"], t)
    rows.append(("System / telemetry", state_by_age(a, 15, 360), f"`System/last/host-last.json` sample {hm(h['at'])} HST" if h["at"] else "no sample found"))
    wl = newest_mtime(DB / "Worklog", "worklog_current.md")
    rows.append(("Worklog scan", state_by_age(age_min(wl, t), 30, 360), f"`Worklog/worklog_current.md` updated {hm(wl)} HST" if wl else "no worklog file"))
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=2) as r:
            loaded = len(json.loads(r.read().decode()).get("models", []))
        oll = ("ok", f"`ollama.service` API up; {loaded} model(s) resident")
    except Exception:
        oll = ("down", "API not reachable on 127.0.0.1:11434")
    rows.append(("Ollama",) + oll)
    ea = [age_min(e["at"], t) for e in en]
    rows.append(("EcoFlow BLE", state_by_age(min(ea) if ea else None, 15, 360),
                 "; ".join(f"{e['pack']} read {hm(e['at'])} HST ({e['source']})" for e in en) or "no SOC file"))
    im = newest_mtime(DB / "Media" / "Images", "*.jpg")
    rows.append(("A-EYES", state_by_age(age_min(im, t), 30, 360), f"newest still in `Media/Images/` {hm(im)} HST" if im else "no still found"))
    wr = newest_mtime(DB / "Weather" / "Hawai'i" / "reports" / "1 County Processing", "*_current.md")
    rows.append(("Weather", state_by_age(age_min(wr, t), 180, 720), f"county reports updated {hm(wr)} HST" if wr else "no county report found"))
    gh = "degraded" if pl["gh_bad"] else ("ok" if pl["gh_last_time"] else "down")
    rows.append(("GitHub sync", gh, f"last `github_sync_all` line {pl['gh_last_time']} HST" if pl["gh_last_time"] else "no github_sync_all line today"))
    cf = procs_by_comm("cloudflared")
    tun = [ln for ln in pl.get("tunnel", []) if "connected" in ln or "timeout" in ln]
    last = tun[-1] if tun else ""
    cf_state = "down" if not cf else ("degraded" if "timeout" in last else "ok")
    rows.append(("Cloudflare tunnel", cf_state, f"{cf} cloudflared process(es)" + (f"; last tunnel line {last[11:16]} HST: {last[25:].strip()}" if last else "")))
    for r in rows:
        f.add(r[2])
    return rows


# ------------------------------------------------------------------ free text (specialist)
def draft(keys: dict[str, str], facts_lines: list[str], mode: str, f: Facts, log: dict, checks: dict | None = None) -> dict[str, str]:
    """keys: {KEY: instruction}. Returns {KEY: text}; falls back to '' (caller substitutes deterministic text)."""
    out = {k: "" for k in keys}
    log.update({"draft_mode": mode, "model_called": False})
    if mode == "none":
        return out
    mem = mem_avail_mb()
    try:
        idle = subprocess.run([str(SF), "status"], capture_output=True, text=True, timeout=5).stdout.startswith("IDLE")
    except Exception:
        idle = False
    log.update({"mem_avail_mb_before": mem, "lock_idle": idle})
    if mem < MIN_MEM_MB_FOR_MODEL or not idle:
        log["skip_reason"] = "low memory" if mem < MIN_MEM_MB_FOR_MODEL else "single-flight busy"
        return out
    facts = "\n".join("- " + cell(x, 200) for x in facts_lines[:30])
    prompt = ("Use ONLY the facts below. Do not add any number, name, path, date or claim that is not in the facts. "
              "If the facts do not support a field, write: No data.\n"
              "Reply with exactly these lines and nothing else:\n"
              + "\n".join(f"{k}: <{v}>" for k, v in keys.items()) + "\n\nFACTS:\n" + facts)
    env = {k: v for k, v in os.environ.items() if k != "DESK_LIVE_FILE"}
    env["RR_CALLER"] = "template_fill"
    t0 = now()
    try:
        r = subprocess.run(["nice", "-n", "10", str(RUN_INFER), SPECIALIST, prompt], capture_output=True, text=True, timeout=180, env=env)
        reply = "\n".join(ln for ln in r.stdout.splitlines() if not re.match(r"^\[(ok|warn|busy|fail)\]", ln))
        log.update({"model_called": True, "rc": r.returncode, "latency_ms": int((now() - t0).total_seconds() * 1000),
                    "reply_chars": len(reply), "mem_avail_mb_after": mem_avail_mb(),
                    "backend": "npu-flm" if "FLM/NPU" in r.stderr else ("ollama" if "Ollama" in r.stderr else "unknown")})
    except Exception as e:
        log.update({"model_called": True, "error": type(e).__name__})
        return out
    allowed = tv.corpus_numbers("\n".join(facts_lines) + "\n" + f.day)
    accepted = {}
    for k in keys:
        m = re.search(rf"^[\s>*#\-\d.)]*\**{k}\**\s*\**\s*[:\-—]\s*\**\s*(.*?)\s*$(?:\n\s*([^\n:]+?)\s*$)?", reply, re.M | re.I)
        v = ((m.group(1) or (m.group(2) or "")) if m else "").strip().strip("<>*\"").strip()
        failed_check = False
        if v and checks and k in checks:
            v2 = checks[k](v) or ""
            failed_check, v = (not v2), v2
        bad = [t for t in tv.number_tokens(v) if not tv.number_ok(t, allowed)]
        if v and len(v) <= 300 and "{{" not in v and not bad and not re.fullmatch(r"(?i)no data\.?", v):
            out[k] = v.rstrip()
            accepted[k] = "model"
        else:
            accepted[k] = "fallback" + (f" (unsupported numbers {bad})" if bad else (" (failed field check)" if failed_check else (" (missing)" if not v else " (rejected)")))
    log["fields"] = accepted
    log["reply_preview"] = cell(reply, 300)
    return out


# ------------------------------------------------------------------ template helpers
def tpl(name: str) -> str:
    return read(TPL_DIR / name)


def section_verbatim(t: str, heading: str, subs: dict[str, str]) -> str:
    """Copy a template section (from heading to the next '---' or EOF) verbatim with placeholder subs."""
    i = t.index(heading)
    j = t.find("\n---\n", i)
    body = t[i:] if j < 0 else t[i:j]
    for k, v in subs.items():
        body = body.replace(k, v)
    return body.rstrip("\n")


# ------------------------------------------------------------------ renderers
def render_worklog(f: Facts, mode: str, log: dict) -> str:
    t = tpl("TEMPLATE System Operator Worklog — Session.md")
    tr, inf, pl, so = testing_records(f), inference(f), poller(f), signoff_items(f)
    ev = [(r["time"], f"Testing record: {cell(r['title'], 80)} — {cell(r['state'], 60)}") for r in tr]
    ev += [(x["time"], f"Poller job `{x['job']}` FAIL {x['detail']}".strip()) for x in pl["fails"]]
    for r in inf["rows"]:
        if r.get("exit_code") or r.get("fallback"):
            ev.append((hm(r["_ts"]), f"Inference {r.get('route')} `{r.get('model')}` rc {r.get('exit_code')}, fallback {str(r.get('fallback')).lower()}"))
    ev.sort(key=lambda e: e[0].lstrip("~"))
    live = f.day == f.t.strftime("%Y-%m-%d")
    w0 = ev[0][0].lstrip("~") if ev else hm(f.t)
    w1 = hm(f.t) if live else (ev[-1][0].lstrip("~") if ev else hm(f.t))
    facts = [f"date {f.day}", f"{len(tr)} testing records today", f"{sum(1 for r in tr if r['state'].startswith('PASS'))} testing records PASS",
             f"{inf['n']} inference requests, {inf['fallbacks']} fallbacks, {inf['nonzero']} non-zero exit codes",
             f"{len(pl['fails'])} poller job FAIL lines today", f"poller unit {is_active('rr-rootserver-poller.service')}"]
    facts += [f"sign-off needed: {s}" for s in so[:6]]
    def pick_signoff(v: str) -> str:  # NEXT must name a real sign-off item; never an unqualified instruction
        for s_ in so:
            core = re.sub(r"[`*:]", "", s_).lower().split(" — ")[0][:24]
            if core and core in re.sub(r"[`*:]", "", v).lower():
                return f"Alexander sign-off: {s_}"
        return ""
    d = draft({"PURPOSE": "one or two sentences: what this digest covers", "NEXT": "copy one item from the sign-off list",
               "STATUS": "one short line summarising the day"}, facts, mode, f, log, {"NEXT": pick_signoff})
    purpose = d["PURPOSE"] or f"Automated digest of desk activity on {f.day}, built from testing records, the AI inference log, poller logs and the operator worklog."
    nxt = d["NEXT"] or (f"Alexander sign-off: {so[0]}" if so else "Review this digest.")
    status = d["STATUS"] or f"{'ACTIVE' if live else 'CLOSED'} — {len(tr)} testing records, {inf['n']} inference requests, {len(pl['fails'])} poller FAIL lines."
    L = [f"# System Operator Worklogs — Session {f.session}", "",
         f"**Date:** {f.day}  ", "**Session:** Automated digest (template_fill.py)  ", "**Timezone:** HST  ",
         f"**Window:** {w0}–{w1} HST  ", f"**Status:** {'ACTIVE' if live else 'CLOSED'}  ", "**Operator:** RootRecord", "", "---", "",
         "## Purpose", "", purpose, "",
         "This is a manual operator worklog (not a full architecture redesign). Record what was actually done.", "", "---", "",
         f"## Approximate timetable ({f.day} HST)", "", "| Time (approx.) | Event |", "| --- | --- |"]
    L += [f"| {a} | {cell(b, 140)} |" for a, b in ev] or [f"| {hm(f.t)} | No recorded events in the sources |"]
    L += ["", "---", "", "## Completed this session", "", "### Testing records", ""]
    L += [f"- [{'x' if r['state'].startswith('PASS') else ' '}] {cell(r['title'], 90)} — {cell(r['state'], 70)}" for r in tr] or ["- [ ] No testing records for this date"]
    L += ["", "### AI inference and poller", ""]
    L += [f"- [{'x' if inf['n'] else ' '}] {inf['n']} inference requests (routes: {', '.join(inf['routes']) or 'none'}); p50 {inf['p50'] if inf['p50'] is not None else 'not recorded'} ms, max {inf['max'] if inf['max'] is not None else 'not recorded'} ms",
          f"- [{'x' if not inf['fallbacks'] else ' '}] Ollama fallbacks: {inf['fallbacks']}; non-zero exit codes: {inf['nonzero']}",
          f"- [{'x' if not pl['fails'] else ' '}] Poller log: {pl['runs']} job runs, {len(pl['fails'])} FAIL lines"]
    L += ["", "### Explicit non-goals", "", "- Automation does not restart services, use sudo, send messages or write into the Library.",
          "- Decisions and sign-offs stay with the operator; this digest only aggregates sources.", "", "---", "",
          "## Blockers / residual items", "", "| Item | Notes |", "| --- | --- |"]
    L += [f"| {cell(s, 90)} | Needs Alexander sign-off (operator worklog) |" for s in so] or ["| None recorded | Operator worklog has no open sign-off items |"]
    L += ["", "---", "", "## Decisions (if any)", "", "> No decisions are recorded by automation.", "",
          "Rationale: decisions come from the operator; this digest only aggregates measured sources.", "", "---", "",
          f"## State at session close (~{hm(f.t)} HST)", "",
          f"- **Runtime:** poller `{is_active('rr-rootserver-poller.service')}`; BLE `{is_active('ava-ecoflow-ble.service')}`; last poller log line {pl['last_time'] or 'none'} HST",
          f"- **Library / docs:** {len(tr)} testing records dated {f.day} in the 07-testing index",
          f"- **GitHub / sync:** {'issues in recent github_sync_all lines' if pl['gh_bad'] else ('ok (last github_sync_all line ' + pl['gh_last_time'] + ' HST)' if pl['gh_last_time'] else 'no github_sync_all line today')}",
          f"- **Next useful step:** {nxt}", "", f"**Status:** {status}", "", "---", ""]
    L.append(section_verbatim(t, "## Archive note", {"{{YYYY-MM-DD}}": f.day, "{{SESSION_NN}}": f.session}))
    f.add(*facts, purpose, nxt, status)
    return "\n".join(L) + "\n"


def render_checkpoint(f: Facts, mode: str, log: dict) -> str:
    t = tpl("TEMPLATE RootRecord Checkpoint.md")
    h, en, pl, so, idl = host(f), energy(f), poller(f), signoff_items(f), ideas(f)
    subs = subsystems(f, h, en, pl)
    pa = is_active("rr-rootserver-poller.service")
    poller_state = "active" if pa == "active" else ("inactive" if pa in ("inactive", "failed") else "unknown")
    dash = procs_matching(lambda c: "poller-dashboard.py" in c)
    verified = [f"Host sample {hm(h['at'])} HST: load1 {h['load1']}, CPU {h['cpu']}%, MemAvailable {h['mem_avail_mb']} MB" if h["at"] else "Host sample: not found"]
    verified += [f"{e['pack']} SOC {e['soc']}% at {hm(e['at'])} HST ({e['source']})" for e in en]
    verified += [f"{n}: {s} — {note}" for n, s, note in subs]
    deferred = [f"{cell(r['title'], 80)} — {cell(r['state'], 60)}" for r in idl if "PROPOSED" in r["state"]] or ["None recorded in 08-ideas"]
    facts = [f"poller {poller_state}", f"{sum(1 for s in subs if s[1] == 'ok')} of {len(subs)} subsystems ok"] + \
            [f"{n} {s}" for n, s, _ in subs] + [f"sign-off needed: {s}" for s in so[:4]]
    d = draft({"PRINCIPLE": "one short operating principle grounded in the facts", "STATUS": "one short status line"}, facts, mode, f, log)
    principle = d["PRINCIPLE"] or "Measured or explicitly unknown: record what the sources show and change nothing without operator approval."
    ok_n = sum(1 for s in subs if s[1] == "ok")
    status = d["STATUS"] or f"{ok_n} of {len(subs)} subsystems ok; poller {poller_state}; {len(so)} sign-off items open."
    L = [f"# RootRecord Checkpoint — {f.day} {hm(f.t)} HST", "", "## Checkpoint Purpose", "",
         f"Snapshot of Pacific RootRecord state at **{hm(f.t)} HST** on **{f.day}**.", "",
         "This checkpoint records what was verified and what remains intentionally deferred. It does not retroactively rewrite earlier logs.",
         "", "---", "", "## Current State", "", "### Runtime", "",
         f"- Poller: {poller_state} — `rr-rootserver-poller.service`",
         f"- HTTP listener: {'127.0.0.1:8799' if port_open(8799) else 'N/A'}",
         f"- Poller log: `{POLLER_LOG}`",
         f"- Pretty poller: {'manual' if dash else 'not running'}", "", "### Core subsystems", "",
         "| Subsystem | Status | Notes |", "| --- | --- | --- |"]
    L += [f"| {n} | {s} | {cell(note, 120)} |" for n, s, note in subs]
    L += ["", "### Services (user systemd)", "", "| Unit | State |", "| --- | --- |"]
    for u in ("rr-rootserver-poller.service", "ava-ecoflow-ble.service", "network-globe-hawaii.service"):
        L.append(f"| `{u}` | {'active' if is_active(u) == 'active' else 'inactive'} |")
    L += ["", "---", "", "## Verified this checkpoint", ""] + [f"- {cell(v, 160)}" for v in verified]
    L += ["", "---", "", "## Intentionally deferred", ""] + [f"- {v}" for v in deferred]
    L += ["", "---", "", "## Blockers", "", "| Blocker | Owner | Next step |", "| --- | --- | --- |"]
    L += [f"| {cell(s, 90)} | Alexander | Sign-off (operator worklog) |" for s in so] or ["| None recorded | — | — |"]
    L += ["", "---", "", "## Operating principle at checkpoint", "", principle, "", "---", "", "## Checkpoint time", "",
          f"**{f.day} {hm(f.t)} HST**", "", f"**Status:** {status}", "", "---", ""]
    L.append(section_verbatim(t, "## Archive note", {"{{YYYY-MM-DD}}": f.day, "{{HH_MM}}": f.t.strftime("%H_%M")}))
    f.add(*verified, *deferred, principle, status, str(POLLER_LOG))
    return "\n".join(L) + "\n"


def render_event(f: Facts, mode: str, log: dict) -> str:
    t = tpl("TEMPLATE Event Action Log.md")
    inf = inference(f)
    title = "AI Inference Activity Log"
    live = f.day == f.t.strftime("%Y-%m-%d")
    tl = []
    if len(inf["rows"]) <= 30:
        for r in inf["rows"]:
            tl.append(f"{hm(r['_ts'])} — {r.get('route')} `{r.get('model')}` for {r.get('target')} (caller {r.get('caller')}): "
                      f"{r.get('latency_ms')} ms, rc {r.get('exit_code')}{', cold start' if r.get('flm_cold_start') else ''}{', Ollama fallback' if r.get('fallback') else ''}")
    else:  # aggregate per hour; approximate marker per template
        by = {}
        for r in inf["rows"]:
            by.setdefault(r["_ts"].strftime("%H"), []).append(r)
        for hh, rs in sorted(by.items()):
            tl.append(f"~{hh}:00 — {len(rs)} requests; max {max(x.get('latency_ms', 0) for x in rs)} ms; {sum(1 for x in rs if x.get('fallback'))} fallbacks")
            f.add(len(rs), max(x.get('latency_ms', 0) for x in rs))
    facts = [f"{inf['n']} inference requests on {f.day}", f"routes {', '.join(inf['routes']) or 'none'}",
             f"p50 latency {inf['p50']} ms, max {inf['max']} ms", f"{inf['fallbacks']} Ollama fallbacks", f"{inf['nonzero']} non-zero exit codes",
             f"lowest MemAvailable after a request {inf['min_mem']} MB"]
    d = draft({"SCOPE": "one line: what this log covers", "STATUS": "one short close status line"}, facts, mode, f, log)
    scope = d["SCOPE"] or f"Inference requests recorded by run-infer.sh on {f.day} (metadata only, no prompt text)."
    status = d["STATUS"] or f"{inf['n']} requests, {inf['fallbacks']} fallbacks, {inf['nonzero']} non-zero exit codes."
    L = [f"# {title}", "", f"**Date:** {f.day}  ", f"**Scope:** {scope}  ", "**Timezone:** HST  ",
         f"**Status:** {'IN PROGRESS' if live else 'CLOSED'}", "", "---", "", "## Timeline", ""]
    for x in tl or [f"{hm(f.t)} — No inference requests recorded for this date"]:
        L += [x, ""]
    L += ["---", "", "## Outcomes", "",
          f"- {inf['n']} requests; p50 {inf['p50'] if inf['p50'] is not None else 'not recorded'} ms, max {inf['max'] if inf['max'] is not None else 'not recorded'} ms",
          f"- {inf['fallbacks']} Ollama fallbacks, {inf['nonzero']} non-zero exit codes; lowest MemAvailable after a request {inf['min_mem'] if inf['min_mem'] is not None else 'not recorded'} MB",
          "", "---", "", "## Artifacts / paths", "", "| Path or artifact | Role |", "| --- | --- |",
          f"| `{INFER_LOG}` | Inference JSONL (metadata only) |",
          "| `System/scripts/plumbing/run-infer.sh` | Writes one line per request |", "", "---", ""]
    L.append(section_verbatim(t, "## Notes", {}))
    L += ["", "---", "", "## Close", "", f"**Closed:** {f.day} {hm(f.t)} HST  ", f"**Status:** {status}", "", "---", ""]
    L.append(section_verbatim(t, "## Archive note", {"{{YYYY-MM-DD}} {{EVENT_TITLE}}.md": f"{f.day} {title}.md"}))
    f.add(*tl, *facts, scope, status, str(INFER_LOG))
    return "\n".join(L) + "\n"


def render_workorder(f: Facts, mode: str, log: dict) -> str:
    t = tpl("TEMPLATE Work Order.md")
    tr, wos, so, inf, pl = testing_records(f), work_orders(f), signoff_items(f), inference(f), poller(f)
    code, short = "GEN", "Desk_Signoff_Backlog"
    friction = [f"{cell(r['title'], 80)} — {cell(r['state'], 60)}" for r in tr if re.search(r"FAIL|BLOCKED|VERIFY PENDING", r["state"])]
    friction += [f"Poller job `{x['job']}` FAIL at {x['time']} HST" for x in pl["fails"]]
    if inf["fallbacks"] or inf["nonzero"]:
        friction.append(f"Inference: {inf['fallbacks']} Ollama fallbacks, {inf['nonzero']} non-zero exit codes")
    facts = [f"{len(so)} operator sign-off items open"] + [f"sign-off: {s}" for s in so[:6]] + \
            [f"{len(friction)} friction items from testing records and logs", f"{len(wos)} work orders in the Library index folder"]
    d = draft({"INTENT": "one or two sentences: why this backlog work order exists", "SCOPE": "one sentence: what is in and out of scope"}, facts, mode, f, log)
    intent = d["INTENT"] or "Collect the open operator sign-off items and measured friction for the day in one place, so they can be accepted or closed deliberately."
    scope = d["SCOPE"] or "In scope: the listed sign-off items and friction from today's sources. Not in scope: executing any of them; this is a generated draft."
    L = ["# WORK ORDER — Desk Sign-off Backlog (generated draft)", "", "| Field | Value |", "| --- | --- |",
         f"| **Work Order ID** | WO-{code}-{f.day} |", f"| **Date** | {f.day} (HST) |",
         "| **Status** | OPEN — generated draft, not on the active index |", "| **Owner** | RootRecord |",
         "| **Related** | Library 07-testing, 08-ideas and the operator worklog of the day |", "",
         f"**Scope:** {scope}", "", "---", "", "## 1. Intent", "", intent, "", "---", "", "## 2. Current reality", "",
         "### 2.1 What exists", "", "| Item | Location / status |", "| --- | --- |"]
    L += [f"| {cell(w['file'], 70)} | {w['status']} |" for w in wos]
    L += ["", "### 2.2 Completed so far", ""]
    L += [f"- [{'x' if r['state'].startswith('PASS') else ' '}] {cell(r['title'], 90)} — {cell(r['state'], 60)}" for r in tr] or ["- [ ] No testing records for this date"]
    L += ["", "### 2.3 Known friction", ""] + ([f"- {x}" for x in friction] or ["- None recorded in today's sources"])
    L += ["", "---", "", "## 3. Tasks", ""] + ([f"{i}. {s}" for i, s in enumerate(so, 1)] or ["1. No open sign-off items"])
    L += ["", "---", "", "## 4. Non-goals", "", "- Executing any task listed here (generated drafts are never auto-promoted).",
          "- Writing into the Library or changing runtime services.", "", "---", "", "## 5. Key file / path reference", "",
          "| Path | Role |", "|------|------|",
          "| `Library Documentation/07-testing/README.md` | Testing record index (source) |",
          "| `Library Documentation/01-operations/0 - Human Operator Work Logs/` | Operator worklogs; sign-off list (source) |",
          f"| `{INFER_LOG}` | Inference JSONL (source) |", f"| `{POLLER_LOG}` | Poller log (source) |", "", "---", ""]
    L.append(section_verbatim(t, "## 6. Open items", {}))
    L += ["", "---", "", "## 7. Notes & constraints", "", "- No force-push.", "- Secrets stay out of git.", "- Prefer small reversible steps.",
          f"- Generated by `Reports/template_fill.py` from measured sources; free text drafted by `{SPECIALIST}` under a facts-only prompt.",
          "", "---", "", f"*Work order prepared {f.day} HST. Update status when closed.*", "", "---", ""]
    L.append(section_verbatim(t, "## Archive / location note", {"{{Short_Name}}": short, "{{CODE}}": code, "{{YYYY-MM-DD}}": f.day,
                                                               "{{short-title}}": "desk-signoff-backlog"}))
    f.add(*facts, *friction, intent, scope, str(INFER_LOG), str(POLLER_LOG), *[w["status"] for w in wos])
    return "\n".join(L) + "\n"


TEMPLATES = {
    "worklog": {"file": "TEMPLATE System Operator Worklog — Session.md", "out": "System-Operator-Worklog-Session", "render": render_worklog,
                "vocab": [{"desc": "header Status", "regex": r"^\*\*Status:\*\* (.+?)\s*$", "allowed": ["ACTIVE", "CLOSED"], "first_only": True}]},
    "checkpoint": {"file": "TEMPLATE RootRecord Checkpoint.md", "out": "RootRecord-Checkpoint", "render": render_checkpoint,
                   "vocab": [{"desc": "Poller state", "regex": r"^- Poller: (\w+) — ", "allowed": ["active", "inactive", "unknown"]},
                             {"desc": "subsystem Status", "regex": r"^\| (?:System / telemetry|Worklog scan|Ollama|EcoFlow BLE|A-EYES|Weather|GitHub sync|Cloudflare tunnel) \| (\w+) \|", "allowed": ["ok", "degraded", "down"]},
                             {"desc": "service State", "regex": r"^\| `[^`]+\.service` \| (\w+) \|$", "allowed": ["active", "inactive"]},
                             {"desc": "Pretty poller", "regex": r"^- Pretty poller: (.+)$", "allowed": ["manual", "auto", "not running"]}]},
    "event": {"file": "TEMPLATE Event Action Log.md", "out": "Event-Action-Log", "render": render_event,
              "vocab": [{"desc": "header Status", "regex": r"^\*\*Status:\*\* (.+?)\s*$", "allowed": ["IN PROGRESS", "CLOSED"], "first_only": True},
                        {"desc": "timeline time format", "regex": r"^(~?\d{2}:\d{2}) — ", "allowed": [r"~?\d{2}:\d{2}"]}]},
    "workorder": {"file": "TEMPLATE Work Order.md", "out": "Work-Order", "render": render_workorder,
                  "vocab": [{"desc": "Status", "regex": r"^\| \*\*Status\*\* \| (.+?) \|$", "allowed": [r"OPEN — .+"]},
                            {"desc": "Work Order ID", "regex": r"^\| \*\*Work Order ID\*\* \| (.+?) \|$", "allowed": [r"WO-[A-Z0-9]+-\d{4}-\d{2}-\d{2}"]}]},
}


def guard_out(p: Path) -> None:
    rp = p.resolve()
    if str(rp).startswith(str(LIB.resolve())):
        raise SystemExit(f"[fail] refusing to write into the Library: {rp}")


def write_rotating(name: str, text: str, dry: bool) -> str:
    cur = OUT_DIR / f"{name}_current.md"
    guard_out(cur)
    if dry:
        return str(cur) + " (dry-run, not written)"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    body = lambda s: "\n".join(ln for ln in s.splitlines() if not ln.startswith("<!-- generated"))
    if cur.is_file():
        old = read(cur)
        if body(old) == body(text):
            return str(cur) + " (unchanged)"
        arch = OUT_DIR / "Archive"
        arch.mkdir(exist_ok=True)
        stamp = datetime.fromtimestamp(cur.stat().st_mtime).strftime("%Y-%m-%dT%H%M")
        shutil.move(str(cur), str(arch / f"{name}_{stamp}.md"))
    tmp = cur.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(cur)
    return str(cur)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Fill Library operations templates from measured desk data.")
    ap.add_argument("--template", default="all", choices=["all", *TEMPLATES])
    ap.add_argument("--all", action="store_true", help="same as --template all (used by jobs.py)")
    ap.add_argument("--date", default=now().strftime("%Y-%m-%d"))
    ap.add_argument("--session", default="01", help="SESSION_NN for the worklog template")
    ap.add_argument("--draft", default="auto", choices=["none", "model", "auto"],
                    help="free-text drafting: none = deterministic text; model/auto = specialist via run-infer.sh (auto skips when memory < 3 GB or the lock is busy)")
    ap.add_argument("--model-templates", default="", help="comma list limiting which templates call the model (default: all selected)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    keys = list(TEMPLATES) if (a.all or a.template == "all") else [a.template]
    only = set(filter(None, a.model_templates.split(","))) or set(keys)
    report = {"generated": now().isoformat(timespec="seconds"), "date": a.date, "specialist": SPECIALIST, "results": {}}
    rc = 0
    for k in keys:
        spec = TEMPLATES[k]
        f = Facts(a.date)
        f.session = a.session
        log: dict = {}
        mode = a.draft if k in only else "none"
        text = spec["render"](f, mode, log)
        text = text.rstrip("\n") + "\n"
        v = tv.validate(tpl(spec["file"]), text, "\n".join(f.corpus), spec["vocab"])
        if v["ok"]:
            where = write_rotating(spec["out"], text, a.dry_run)
        else:
            rc = 1
            where = str(OUT_DIR / f"{spec['out']}_rejected.md")
            guard_out(Path(where))
            if not a.dry_run:
                OUT_DIR.mkdir(parents=True, exist_ok=True)
                Path(where).write_text(text, encoding="utf-8")
        report["results"][k] = {"template": spec["file"], "output": where, "validation": v, "draft": log}
        print(f"[{'ok' if v['ok'] else 'REJECTED'}] {k}: {where}  headings={v['headings']} tables={v['tables']} "
              f"unsupported_numbers={v['unsupported_numbers'][:8]} draft={log.get('fields', log.get('skip_reason', mode))}")
        for e in v["errors"]:
            print("   error:", e)
    if not a.dry_run:
        vp = OUT_DIR / "template-fill-validation_current.json"
        guard_out(vp)
        if vp.is_file() and len(keys) < len(TEMPLATES):  # single-template run: keep the other templates' last results
            try:
                old = json.loads(read(vp)).get("results", {})
                report["results"] = {**old, **report["results"]}
            except ValueError:
                pass
        vp.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
