#!/usr/bin/env python3
"""Pacific home receiver for Mainland SSH NDJSON streams (collectors + sysmon).

Staged on desk. Install path expectation (NOT done by this scaffold):
  forced-command for ml1/ml2 stream keys → this script only.

Writes atomically under RR_DATABASE_ROOT / path_rel when allowlisted.
Same tree desks/voice/LLMs already read — twin of Telegram datapack-pickup.
Before replace, if the destination filename contains _current, the prior file
is renamed into sibling archive/YYYYMMDD/ (HST); live *_current path stays stable.
Also appends a one-line audit to Logs/System/mainland-stream-receive.jsonl when possible.
Never writes Energy/ or EcoFlow paths.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_LIB = Path(__file__).resolve().parents[1] / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from current_bank import archive_before_replace  # noqa: E402

ALLOWED_PATH_PREFIXES = (
    "Geology/",
    "Weather/",
    "Media/RadioRss/",
    "Communications/Discord/",
    "Communications/Telegram/",
    "Intake/ml2/",
    "Intake/ml1/",
    "Logs/ML2/",
    "Logs/ML1/",
    "System/metrics/ml2/",
    "System/metrics/ml1/",
    "Network/datapacks/",
)

DENY_SUBSTRINGS = ("EcoFlow", "ecoflow", "Energy/")

DB = Path(
    os.environ.get(
        "RR_DATABASE_ROOT",
        "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
    )
)


def allowed(path_rel: str) -> bool:
    if ".." in path_rel or path_rel.startswith("/") or path_rel.startswith("\\"):
        return False
    for d in DENY_SUBSTRINGS:
        if d in path_rel:
            return False
    return any(path_rel.startswith(p) for p in ALLOWED_PATH_PREFIXES)



def atomic_write(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".ml-recv-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def append_daily(path_rel: str, raw: bytes, meta: dict) -> None:
    """For System/metrics/mlN/host-last.json also append JSONL under Daily/."""
    if not path_rel.startswith("System/metrics/") or not path_rel.endswith("host-last.json"):
        return
    parts = path_rel.split("/")
    # System/metrics/ml1/host-last.json → System/metrics/ml1/Daily/YYYY-MM-DD.jsonl
    if len(parts) < 4:
        return
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily = DB / "/".join(parts[:3]) / "Daily" / f"{day}.jsonl"
    daily.parent.mkdir(parents=True, exist_ok=True)
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception:
        obj = {"raw_bytes": len(raw)}
    line = {
        "banked_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "path_rel": path_rel,
        "source_node": meta.get("source_node"),
        "payload": obj,
    }
    with daily.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def audit(msg: dict) -> None:
    try:
        path = DB / "Logs" / "System" / "mainland-stream-receive.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main() -> int:
    written = 0
    errors = 0
    for line_no, line in enumerate(sys.stdin, 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            path_rel = obj["path_rel"]
            if not allowed(path_rel):
                raise ValueError(f"path not allowed: {path_rel}")
            raw = base64.b64decode(obj["body_b64"])
            dest = DB / path_rel
            archived = archive_before_replace(dest, path_rel)
            atomic_write(dest, raw)
            append_daily(path_rel, raw, obj)
            written += 1
            msg = f"ok {path_rel} bytes={len(raw)}"
            if archived:
                msg += f" archived={archived}"
            print(msg)
            audit(
                {
                    "ts": datetime.now(timezone.utc)
                    .replace(microsecond=0)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "ok": True,
                    "path_rel": path_rel,
                    "source_node": obj.get("source_node"),
                    "bytes": len(raw),
                    "archived": archived,
                }
            )
        except Exception as e:
            errors += 1
            print(f"err line={line_no} {e}", file=sys.stderr)
            audit({"ok": False, "line": line_no, "error": str(e)})
    print(f"summary written={written} errors={errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
