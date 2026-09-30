#!/usr/bin/env python3
"""Code review pack. Writes markdown only. Never patches the tree.

Evidence is git status plus error lines from an allowlisted set of Database logs.
The coder section stays off unless RR_CODE_REVIEW_CODER=1. That flag stays unset.
No qwen pull. No cloud call on the default path.

  python3 code_review.py
  python3 code_review.py --root /tmp/rr-mig-34
"""
from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
ECOSYSTEM = Path("/home/rootrecord/RootRecord-Ecosystem")
DEFAULT_DB = ECOSYSTEM / "2 - RootRecord-Database"
PACIFIC = ECOSYSTEM / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server"
GIT_CAP = 4000
TAIL_BYTES = 256_000
TAIL_LINES = 400
ERR_LIMIT = 40
LINE_CAP = 240
SKIP = ("password", "api_key", "token=", "secret", "sk-", "bot")
LOG_ALLOW = (
    "Logs/Automations/automations_current.log",
    "Logs/Energy/ava-ecoflow-ble.log",
    "Logs/Communications/council-relay.log",
)


def _tail(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            handle.seek(max(0, size - TAIL_BYTES))
            raw = handle.read()
    except OSError:
        return []
    return raw.decode("utf-8", errors="replace").splitlines()[-TAIL_LINES:]


def _secret(line: str) -> bool:
    low = line.lower()
    return any(token in low for token in SKIP)


def _git_short() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short", "-uno"],
            cwd=ECOSYSTEM,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"(unavailable: {type(exc).__name__})"
    text = ((result.stdout or "") + (result.stderr or "")).strip()
    if not text:
        return "(clean or git unavailable)"
    return text[:GIT_CAP]


def _log_errors() -> list[str]:
    hits: list[str] = []
    for rel in LOG_ALLOW:
        path = DEFAULT_DB / rel
        for line in _tail(path):
            if _secret(line):
                continue
            low = line.lower()
            if "error" in low or "exception" in low or "traceback" in low:
                hits.append(f"{path.name}: {line[:LINE_CAP]}")
    return hits[:ERR_LIMIT]


def _coder_notes(evidence: str) -> str:
    if os.environ.get("RR_CODE_REVIEW_CODER", "0") != "1":
        return "_Coder off._\n"
    infer = PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"
    prompt = (
        "List up to 8 concrete gaps from the evidence. "
        "For each: one-line title, why it matters, and a task in one sentence. "
        "No patches. If evidence is thin, say that.\n\n"
        + evidence[:6000]
    )
    try:
        result = subprocess.run(
            ["bash", str(infer), "ava", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            env=dict(os.environ, RR_CALLER="code_review"),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"_Coder skipped: {type(exc).__name__}_\n"
    raw = " ".join(
        line for line in (result.stdout or "").splitlines() if not line.startswith("[ok]")
    ).strip()
    if result.returncode != 0 or not raw:
        return "_Coder skipped: no note._\n"
    return f"_Coder on (RR_CODE_REVIEW_CODER=1)._\n\n{raw[:4000]}\n"


def _pack(git_text: str, errors: list[str], coder: str, when: datetime) -> str:
    err_block = "\n".join(f"- `{line}`" for line in errors) or "- (none in the last log tail)"
    return (
        "# Code review pack — evaluate only\n\n"
        "Suggest fixes in a reply. This file does not change the live tree.\n\n"
        "- Live numbers only from the evidence below. If evidence is missing, say so.\n"
        "- Do not print secrets, tokens, or env values.\n\n"
        f"Live tree: `{ECOSYSTEM}`\n\n"
        f"## Evidence — {when.isoformat()}\n\n"
        "### Git (uncommitted, not staged by this job)\n\n"
        f"```\n{git_text}\n```\n\n"
        "### Recent log errors\n\n"
        f"{err_block}\n\n"
        "## Local coder suggestions (not applied)\n\n"
        f"{coder}"
    )


def write_pack(root: Path) -> dict:
    when = datetime.now(HST)
    out = root / "CodeReview"
    log_dir = root / "Logs" / "CodeReview"
    out.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    git_text = _git_short()
    errors = _log_errors()
    evidence = f"{git_text}\n" + "\n".join(errors)
    coder = _coder_notes(evidence)
    body = _pack(git_text, errors, coder, when)
    stamp = when.strftime("%Y-%m-%d-%H%M")
    dated = out / f"{stamp}.md"
    current = out / "CURRENT.md"
    dated.write_text(body, encoding="utf-8")
    current.write_text(body, encoding="utf-8")
    line = (
        f"{when.isoformat()} pack={dated.name} bytes={dated.stat().st_size} "
        f"coder={'on' if os.environ.get('RR_CODE_REVIEW_CODER', '0') == '1' else 'off'}\n"
    )
    with (log_dir / "code-review.log").open("a", encoding="utf-8") as handle:
        handle.write(line)
    return {
        "ok": True,
        "applied": False,
        "current": str(current),
        "dated": str(dated),
        "coder": os.environ.get("RR_CODE_REVIEW_CODER", "0") == "1",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a code review evidence pack.")
    parser.add_argument(
        "--root",
        default="",
        help="Database root for this run. Default is the live Database folder.",
    )
    args = parser.parse_args()
    root = Path(args.root) if args.root else DEFAULT_DB
    result = write_pack(root)
    print(f"ok current={result['current']} dated={result['dated']} coder={result['coder']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
