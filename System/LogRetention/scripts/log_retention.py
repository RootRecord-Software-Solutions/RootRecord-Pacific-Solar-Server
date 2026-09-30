#!/usr/bin/env python3
"""log_retention.py — log retention (WO-MIG-41).

Same shape as weather retention: --dry-run is the default and changes no log
file. --apply moves aged logs. This script never unlinks, rmdirs, or rmtrees.

Default root:  2 - RootRecord-Database/Logs/
Archive:       2 - RootRecord-Database/Archive/Previous-Datasets/Logs-<YYYYMM>/
Reports:       2 - RootRecord-Database/Logs/System/LogRetention/
State:         2 - RootRecord-Database/System/LogRetention/log-retention.json

--apply on the live Logs root refuses to run unless RR_LOG_RETENTION_APPLY=1.
The scheduled job stays --dry-run.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
LIVE_LOGS = DB / "Logs"
LIVE_ARCHIVE = DB / "Archive" / "Previous-Datasets"
LIVE_REPORT_DIR = LIVE_LOGS / "System" / "LogRetention"
LIVE_STATE = DB / "System" / "LogRetention" / "log-retention.json"
KEEP_DAYS = 7
MAX_LIVE_BYTES = 10 * 1024 * 1024
LOG_KEEP = 5
DATE_IN_NAME = re.compile(r"(?:^|[^0-9])(\d{4}-\d{2}-\d{2})(?:[^0-9]|$)")
ROTATION = re.compile(r"\.log\.\d+$", re.I)
SKIP_DIRS = {"__pycache__", "leveldb", ".config"}


def name_day(name: str) -> date | None:
    m = DATE_IN_NAME.search(name)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None


def is_log_name(name: str) -> bool:
    n = name.lower()
    if n.endswith(".jsonl"):
        return False
    if n.endswith(".log") or n.endswith(".out") or n.endswith(".log.gz") or n.endswith(".log.old"):
        return True
    return bool(ROTATION.search(n))


def is_rotation(name: str) -> bool:
    n = name.lower()
    return bool(ROTATION.search(n) or n.endswith(".log.gz") or n.endswith(".log.old"))


def is_live_writer(name: str) -> bool:
    n = name.lower()
    if "_current.log" in n or n == "latest.log":
        return True
    if name_day(name) is not None or is_rotation(name):
        return False
    return n.endswith(".log") or n.endswith(".out")


def skip_dir(name: str) -> bool:
    return name.lower() in SKIP_DIRS or "local storage" in name.lower()


def file_day(path: Path) -> date | None:
    named = name_day(path.name)
    if named is not None:
        return named
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).date()
    except OSError:
        return None


def age_days(path: Path, today: date) -> int | None:
    day = file_day(path)
    if day is None:
        return None
    return (today - day).days


def dest_for(src: Path, root: Path, archive_root: Path, when: date) -> Path:
    return archive_root / f"Logs-{when.strftime('%Y%m')}" / src.relative_to(root)


def move_file(src: Path, dest: Path) -> Path:
    """Move src to dest. Content stays on disk. Never unlinks."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest = dest.with_name(dest.name + f".dup-{datetime.now():%Y%m%d%H%M%S}")
    shutil.move(str(src), str(dest))
    return dest


def plan(root: Path, archive_root: Path, today: date) -> dict:
    would_move: list[dict] = []
    would_rotate: list[dict] = []
    seen: set[Path] = set()
    scanned = 0
    if not root.is_dir():
        return {"scanned": 0, "would_move": [], "would_rotate": [], "would_delete": 0}

    for dirpath, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if not skip_dir(d)]
        for fname in files:
            path = Path(dirpath) / fname
            if path.is_symlink() or not path.is_file():
                continue
            if skip_dir(path.name) or "local storage" in str(path).lower():
                continue
            if not is_log_name(path.name):
                continue
            scanned += 1
            if is_live_writer(path.name):
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                if path.name.lower().endswith(".log") and size >= MAX_LIVE_BYTES:
                    oldest = path.with_name(f"{path.name}.{LOG_KEEP}")
                    oldest_move = None
                    if oldest.is_file() and not oldest.is_symlink():
                        when = file_day(oldest) or today
                        oldest_move = str(dest_for(oldest, root, archive_root, when))
                        if oldest not in seen:
                            seen.add(oldest)
                            would_move.append({
                                "src": str(oldest),
                                "dest": oldest_move,
                                "bytes": oldest.stat().st_size,
                                "age_days": age_days(oldest, today),
                                "why": "oldest rotation (10 MB x 5)",
                            })
                    would_rotate.append({
                        "src": str(path),
                        "bytes": size,
                        "oldest": str(oldest) if oldest_move else None,
                    })
                continue
            aged = age_days(path, today)
            if aged is None or aged < KEEP_DAYS:
                continue
            if not (name_day(path.name) is not None or is_rotation(path.name)):
                continue
            if path in seen:
                continue
            seen.add(path)
            when = file_day(path) or today
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            would_move.append({
                "src": str(path),
                "dest": str(dest_for(path, root, archive_root, when)),
                "bytes": size,
                "age_days": aged,
                "why": "older than 7 days",
            })
    return {
        "scanned": scanned,
        "would_move": would_move,
        "would_rotate": would_rotate,
        "would_delete": 0,
    }


def apply_plan(root: Path, archive_root: Path, p: dict) -> list[str]:
    actions: list[str] = []
    for item in p["would_move"]:
        src, dest = Path(item["src"]), Path(item["dest"])
        if not src.is_file() or src.is_symlink():
            continue
        landed = move_file(src, dest)
        actions.append(f"moved {src} -> {landed}")
    for item in p["would_rotate"]:
        live = Path(item["src"])
        if not live.is_file() or live.is_symlink():
            continue
        try:
            if live.stat().st_size < MAX_LIVE_BYTES:
                continue
        except OSError:
            continue
        oldest = live.with_name(f"{live.name}.{LOG_KEEP}")
        if oldest.is_file() and not oldest.is_symlink():
            when = file_day(oldest) or datetime.now().astimezone().date()
            landed = move_file(oldest, dest_for(oldest, root, archive_root, when))
            actions.append(f"moved oldest rotation {oldest} -> {landed}")
        for i in range(LOG_KEEP - 1, 0, -1):
            src = live.with_name(f"{live.name}.{i}")
            if src.is_file() and not src.is_symlink():
                os.replace(src, live.with_name(f"{live.name}.{i + 1}"))
        shutil.copy2(live, live.with_name(f"{live.name}.1"))
        with live.open("r+b") as fh:
            fh.truncate(0)
        actions.append(f"copytruncated {live.name} (kept the file)")
    return actions


def render(p: dict, mode: str, root: Path, archive_root: Path, now: datetime, actions: list[str]) -> str:
    move_bytes = sum(m["bytes"] for m in p["would_move"])
    lines = [
        f"# Log retention — {mode.upper()} — {now.isoformat(timespec='seconds')}",
        "",
        f"Root: `{root}`",
        f"Archive: `{archive_root}/Logs-<YYYYMM>/` (move, never delete).",
        f"Scanned log files: {p['scanned']}.",
        f"**Would move:** {len(p['would_move'])} files, {move_bytes} bytes.",
        f"**Would copytruncate:** {len(p['would_rotate'])} live logs over 10 MB.",
        "**Would delete:** 0.",
        "",
    ]
    if p["would_move"]:
        lines.append("## Move candidates")
        lines.append("")
        for m in p["would_move"][:200]:
            lines.append(f"- `{m['src']}` ({m['bytes']} B, age {m['age_days']} d, {m['why']}) → `{m['dest']}`")
        if len(p["would_move"]) > 200:
            lines.append(f"- … {len(p['would_move']) - 200} more")
        lines.append("")
    if p["would_rotate"]:
        lines.append("## Copytruncate candidates")
        lines.append("")
        for r in p["would_rotate"][:50]:
            lines.append(f"- `{r['src']}` ({r['bytes']} B)")
        lines.append("")
    if actions:
        lines.append("## Actions")
        lines.append("")
        lines.extend(f"- {a}" for a in actions)
        lines.append("")
    return "\n".join(lines)


def write_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Log retention (dry-run by default)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="default: read-only report")
    g.add_argument("--apply", action="store_true", help="move logs past 7 days (live root needs RR_LOG_RETENTION_APPLY=1)")
    ap.add_argument("--root", default="", help="scan root (default: Database Logs)")
    ap.add_argument("--archive", default="", help="archive root (default: Archive/Previous-Datasets)")
    ap.add_argument("--report", default="")
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    mode = "apply" if a.apply else "dry-run"
    root = Path(a.root).expanduser() if a.root else LIVE_LOGS
    archive_root = Path(a.archive).expanduser() if a.archive else LIVE_ARCHIVE
    root = root.resolve()
    archive_root = archive_root.resolve()
    if mode == "apply" and root == LIVE_LOGS.resolve() and os.environ.get("RR_LOG_RETENTION_APPLY") != "1":
        print("refusing --apply on live Logs without RR_LOG_RETENTION_APPLY=1", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"No log root: {root}", file=sys.stderr)
        return 1
    lock = open("/tmp/log-retention.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("[skip] another log-retention run holds the lock")
        return 0
    now = datetime.now().astimezone()
    planned = plan(root, archive_root, now.date())
    actions = apply_plan(root, archive_root, planned) if mode == "apply" else []
    text = render(planned, mode, root, archive_root, now, actions)
    print(text)
    if not a.no_save:
        if a.report:
            out = Path(a.report)
        elif root == LIVE_LOGS.resolve():
            out = LIVE_REPORT_DIR / f"log-retention_{mode}_{now:%Y-%m-%d_%H%M}.md"
        else:
            out = root / "System" / "LogRetention" / f"log-retention_{mode}_{now:%Y-%m-%d_%H%M}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"[saved] {out}")
        state_path = LIVE_STATE if root == LIVE_LOGS.resolve() else root / "log-retention.json"
        write_state(state_path, {
            "ok": True,
            "mode": mode,
            "ts": now.isoformat(timespec="seconds"),
            "root": str(root),
            "archive": str(archive_root),
            "scanned": planned["scanned"],
            "would_delete": 0,
            "would_move_count": len(planned["would_move"]),
            "would_move": [m["src"] for m in planned["would_move"]],
            "would_rotate": [r["src"] for r in planned["would_rotate"]],
            "actions": actions,
        })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
