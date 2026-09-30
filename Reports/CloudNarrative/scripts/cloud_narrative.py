#!/usr/bin/env python3
"""Optional cloud prose on the existing template reports. Does not replace them.

Default is a dry-run: write a prompt package and last.json. No HTTP.

  python3 cloud_narrative.py morning --dry-run
  python3 cloud_narrative.py morning|midday|late|merged|kilauea [--dry-run|--spend]

--spend calls the cloud API only when RR_CLOUD_NARRATIVE_SPEND=1 and XAI_API_KEY
is set. merged never calls the model; it copies today's morning narrative.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[2]
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
DATA = DB / "Reports" / "CloudNarrative"
LOG = DB / "Logs" / "Reports" / "CloudNarrative" / "cloud-narrative.jsonl"
TEMPLATES = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))
HST = ZoneInfo("Pacific/Honolulu")
CHAT_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-3"
THIN = 80

TEMPLATE_FILE = {
    "morning": "morning_report_current.md",
    "midday": "midday_report_current.md",
    "late": "late_report_current.md",
    "kilauea": "kilauea_report_current.md",
}
KINDS = ("morning", "midday", "late", "merged", "kilauea")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PACIFIC / "Media" / "Voice" / "scripts"))
import envload  # noqa: E402
from speech_scrub import scrub_speech  # noqa: E402

_WMO = re.compile(r"^\s*0{3}\s+")


def now() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def measured(text: str) -> str:
    if "## Measured" in text:
        rest = text.split("## Measured", 1)[1]
        rest = re.split(r"\n## ", rest, maxsplit=1)[0]
        return rest.strip()
    return text.strip()


def scrub_nws(text: str) -> str:
    """Drop NWS product bodies. Short template lines stay."""
    kept: list[str] = []
    for line in (text or "").splitlines():
        low = line.lower()
        if "nws county spoken script" in low:
            continue
        if ('"raw"' in low or '"description"' in low) and len(line) > 400:
            continue
        if _WMO.match(line):
            continue
        if len(line) > 500 and any(k in low for k in (
            "national weather service", "hurricane local statement", "area forecast discussion",
        )):
            continue
        kept.append(line)
    return "\n".join(kept).strip()


def persona(kind: str) -> str:
    if kind == "kilauea":
        return (
            "You are writing a short Kīlauea notice for easy audio readout. "
            "Use only the FACTS text. Alert levels, eruption state, or quake counts "
            "only if they are in FACTS. Advisory is not erupting. Under 180 words. "
            "End with: End of status. Output only the report text."
        )
    return (
        "You are writing a short desk status for easy audio readout. "
        "Numbers only from the FACTS block. If a hazard is not in FACTS, omit it. "
        "Off-grid only. Short sentences. End with: End of status. Output only the report text."
    )


def prompt_for(kind: str, facts: str) -> str:
    if kind == "kilauea":
        ask = "Write a short Kīlauea notice from FACTS only."
    else:
        ask = f"Write today's {kind} desk status from FACTS only."
    return (
        f"{ask}\n"
        "No invented numbers. No vendor names. End with End of status.\n\n"
        f"FACTS:\n{facts}\n"
    )


def template_path(kind: str) -> Path | None:
    name = TEMPLATE_FILE.get(kind)
    return (TEMPLATES / name) if name else None


def read_template(kind: str) -> tuple[str, Path | None]:
    path = template_path(kind)
    if path is None or not path.is_file():
        return "", path
    return path.read_text(encoding="utf-8", errors="replace"), path


def morning_narrative_today(t: datetime) -> Path | None:
    path = DATA / "morning-current.md"
    if not path.is_file():
        return None
    mt = datetime.fromtimestamp(path.stat().st_mtime, HST)
    if mt.date() != t.date():
        return None
    return path


def write_last(payload: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA / "last.json.tmp"
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, DATA / "last.json")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def cloud_chat(kind: str, facts: str) -> str:
    """One chat completion. Called only after the spend gate passes."""
    import urllib.request

    key = envload.api_key()
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": persona(kind)},
            {"role": "user", "content": prompt_for(kind, facts)},
        ],
        "temperature": 0.3,
        "max_tokens": 600 if kind == "kilauea" else 1800,
    }).encode("utf-8")
    req = urllib.request.Request(
        CHAT_URL,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    return str(data["choices"][0]["message"]["content"] or "")


def run(kind: str, *, spend: bool) -> dict:
    t = now()
    base = {"at": t.isoformat(), "kind": kind, "http": False}
    if kind not in KINDS:
        payload = dict(base, dry_run=True, result="skip", detail="unknown_kind")
        write_last(payload)
        return payload

    if kind == "merged":
        src = morning_narrative_today(t)
        payload = dict(base, dry_run=not spend, result="dry_run" if not spend else "copied",
                       detail="no_model_call", would_copy=src is not None, source=str(src) if src else None)
        if spend and src is not None:
            text = src.read_text(encoding="utf-8", errors="replace")
            dest = DATA / "merged-current.md"
            dest.write_text(text, encoding="utf-8")
            payload["bytes"] = len(text.encode("utf-8"))
        elif spend:
            payload["result"] = "skip"
            payload["detail"] = "no_morning_narrative_today"
        write_last(payload)
        return payload

    raw, path = read_template(kind)
    facts = scrub_speech(scrub_nws(measured(raw)))
    package = (
        f"# Cloud narrative package — {kind}\n\n"
        f"Built: {t.isoformat()}\n"
        f"Template: {path}\n"
        f"Dry-run: {not spend}\n\n"
        f"## System\n\n{persona(kind)}\n\n"
        f"## User\n\n{prompt_for(kind, facts)}\n"
    )
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / f"{kind}-package.md").write_text(package, encoding="utf-8")
    payload = dict(
        base,
        dry_run=not spend,
        template=str(path) if path else None,
        template_present=bool(raw),
        package_chars=len(package),
        facts_chars=len(facts),
    )
    if not raw:
        payload.update(result="skip", detail="template_missing", dry_run=True)
        write_last(payload)
        return payload
    if not spend:
        payload.update(result="dry_run", detail="no_http")
        write_last(payload)
        return payload

    if not envload.api_key():
        payload.update(dry_run=True, result="skip", detail="missing_key", http=False)
        write_last(payload)
        return payload

    try:
        text = scrub_speech(cloud_chat(kind, facts))
    except Exception as e:
        payload.update(result="failed", detail=type(e).__name__, http=True)
        write_last(payload)
        return payload
    payload["http"] = True
    if len(text.strip()) < THIN:
        payload.update(result="rejected", detail="thin_output")
        write_last(payload)
        return payload
    out = DATA / f"{kind}-current.md"
    out.write_text(text.rstrip() + "\n", encoding="utf-8")
    payload.update(result="wrote", detail="cloud_text", bytes=out.stat().st_size)
    write_last(payload)
    return payload


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    kind = (args[0] if args else "morning").strip().lower()
    spend = "--spend" in sys.argv and "--dry-run" not in sys.argv and os.environ.get("RR_CLOUD_NARRATIVE_SPEND") == "1"
    payload = run(kind, spend=spend)
    print(json.dumps(payload, ensure_ascii=False))
    if payload.get("result") == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
