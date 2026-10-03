#!/usr/bin/env python3
"""Solar catch-up: drain Telegram offline datapacks into Database.

When ML2 could not SSH-stream (Pacific down / tunnel fail), Mainland sent
zips to the datapack Telegram chat. This script is the receive side on the
solar desk: poll that chat, unpack allowlisted path_rel into RR_DATABASE_ROOT,
and keep evidence under Network/datapacks/processed/.

Run on a timer and once at boot so a cold solar start still catches up.
Dedicated datapack bot (NOT Ava council-relay). Own getUpdates owner.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

_SYSTEM_LIB = Path(__file__).resolve().parents[3] / "System" / "lib"
if str(_SYSTEM_LIB) not in sys.path:
    sys.path.insert(0, str(_SYSTEM_LIB))
from current_bank import archive_before_replace  # noqa: E402

DB = Path(
    os.environ.get(
        "RR_DATABASE_ROOT",
        "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database",
    )
)
INBOX = Path(
    os.environ.get(
        "RR_DATAPACK_INBOX",
        str(DB / "Network" / "datapacks" / "inbox"),
    )
)
PROCESSED = Path(
    os.environ.get(
        "RR_DATAPACK_PROCESSED",
        str(DB / "Network" / "datapacks" / "processed"),
    )
)
STATE = Path(
    os.environ.get(
        "RR_DATAPACK_STATE",
        str(DB / "Network" / "datapacks" / "state"),
    )
)
OFFSET_FILE = STATE / "telegram-offset.json"

# Must stay aligned with ML2 stream/protocol.py ALLOWED_PATH_PREFIXES —
# Telegram is the offline twin of the SSH bank stream.
ALLOWED = (
    "Geology/",
    "Weather/",
    "Media/RadioRss/",
    "Intake/ml2/",
    "Intake/ml1/",
    "Logs/ML2/",
    "Logs/ML1/",
    "System/metrics/ml2/",
    "System/metrics/ml1/",
)


def _env_load() -> dict:
    d = {}
    for p in (
        Path(os.environ.get("RR_DATAPACK_ENV", "")),
        Path.home() / ".env",
        Path("/home/rootrecord/.env"),
        Path("/etc/rootrecord/datapack.env"),
    ):
        if not p or str(p) == "." or not p.is_file():
            continue
        try:
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    d[k] = v.split("#", 1)[0].strip().strip("'\"")
        except OSError:
            pass
    return d


def token() -> str:
    e = _env_load()
    return (
        os.environ.get("RR_DATAPACK_BOT_TOKEN")
        or os.environ.get("RR_DATAPACK_SEND_BOT_TOKEN")
        or e.get("RR_DATAPACK_BOT_TOKEN")
        or e.get("RR_DATAPACK_SEND_BOT_TOKEN")
        or ""
    )


def api(tok: str, method: str, params: dict | None = None) -> dict:
    url = f"https://api.telegram.org/bot{tok}/{method}"
    data = None
    if params:
        data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def allowed(path_rel: str) -> bool:
    if ".." in path_rel or path_rel.startswith("/"):
        return False
    if "EcoFlow" in path_rel or path_rel.startswith("Energy/"):
        return False
    return any(path_rel.startswith(p) for p in ALLOWED)



def atomic_write(dest: Path, data: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".dp-")
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


def apply_zip(zpath: Path) -> int:
    applied = 0
    with zipfile.ZipFile(zpath, "r") as zf:
        names = set(zf.namelist())
        # prefer envelopes
        envs = [n for n in names if n.endswith(".envelope.json") and n.startswith("handoff/")]
        for ename in envs:
            env = json.loads(zf.read(ename).decode("utf-8"))
            path_rel = env.get("path_rel") or ""
            staging = env.get("staging_file") or ""
            body_name = f"handoff/{Path(staging).name}" if staging else None
            if not body_name or body_name not in names:
                # try same stem
                stem = Path(ename).name.replace(".envelope.json", "")
                body_name = f"handoff/{stem}"
            if body_name not in names:
                print(f"datapack-pickup: missing body for {ename}", file=sys.stderr)
                continue
            if not allowed(path_rel):
                print(f"datapack-pickup: reject {path_rel}", file=sys.stderr)
                continue
            raw = zf.read(body_name)
            dest = DB / path_rel
            archived = archive_before_replace(dest, path_rel)
            atomic_write(dest, raw)
            if archived:
                print(f"archived prior _current -> {archived}")
            # daily append for host-last
            if path_rel.endswith("host_current.json") and path_rel.startswith("System/metrics/"):
                day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                daily = DB / Path(path_rel).parent / "Daily" / f"{day}.jsonl"
                daily.parent.mkdir(parents=True, exist_ok=True)
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except Exception:
                    payload = {"bytes": len(raw)}
                with daily.open("a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "banked_at": datetime.now(timezone.utc)
                                .replace(microsecond=0)
                                .isoformat()
                                .replace("+00:00", "Z"),
                                "via": "telegram_datapack",
                                "path_rel": path_rel,
                                "source_node": env.get("source_node"),
                                "payload": payload,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            applied += 1
            print(f"ok {path_rel} bytes={len(raw)} via=telegram_datapack")
    return applied


def load_offset() -> int:
    if OFFSET_FILE.is_file():
        try:
            return int(json.loads(OFFSET_FILE.read_text(encoding="utf-8")).get("offset") or 0)
        except Exception:
            return 0
    return 0


def save_offset(offset: int) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    OFFSET_FILE.write_text(json.dumps({"offset": offset}, indent=2) + "\n", encoding="utf-8")


def download_file(tok: str, file_id: str, dest: Path) -> Path:
    meta = api(tok, "getFile", {"file_id": file_id})
    fpath = (meta.get("result") or {}).get("file_path")
    if not fpath:
        raise RuntimeError(f"no file_path for {file_id}")
    url = f"https://api.telegram.org/file/bot{tok}/{fpath}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as resp:
        dest.write_bytes(resp.read())
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--local-zip", type=Path, help="Apply a local zip (no Telegram)")
    ap.add_argument("--max-updates", type=int, default=50)
    args = ap.parse_args(argv)

    INBOX.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)

    if args.local_zip:
        n = apply_zip(args.local_zip)
        print(f"datapack-pickup: applied={n} from local zip")
        return 0 if n >= 0 else 1

    tok = token()
    if not tok:
        print("datapack-pickup: no RR_DATAPACK_* token — skip (stage only)", file=sys.stderr)
        return 0

    offset = load_offset()
    if args.dry_run:
        print(json.dumps({"offset": offset, "token_set": True, "inbox": str(INBOX)}, indent=2))
        return 0

    updates = api(
        tok,
        "getUpdates",
        {"offset": offset, "timeout": 0, "limit": args.max_updates},
    )
    if not updates.get("ok"):
        print(f"datapack-pickup: getUpdates fail {updates}", file=sys.stderr)
        return 1

    applied_total = 0
    max_upd = offset
    for upd in updates.get("result") or []:
        upd_id = int(upd["update_id"])
        max_upd = max(max_upd, upd_id + 1)
        msg = upd.get("message") or upd.get("channel_post") or {}
        doc = msg.get("document")
        if not doc:
            continue
        name = doc.get("file_name") or ""
        if not (name.startswith("rootrecord-") and name.endswith(".zip")):
            continue
        file_id = doc["file_id"]
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        zpath = INBOX / f"{stamp}-{name}"
        try:
            download_file(tok, file_id, zpath)
            n = apply_zip(zpath)
            applied_total += n
            # move to processed
            dest = PROCESSED / zpath.name
            zpath.replace(dest)
        except Exception as e:
            print(f"datapack-pickup: fail {name}: {e}", file=sys.stderr)

    if max_upd > offset:
        save_offset(max_upd)

    (STATE / "pickup-last.json").write_text(
        json.dumps(
            {
                "ts": datetime.now(timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "applied": applied_total,
                "offset": max_upd,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"datapack-pickup: applied={applied_total} offset={max_upd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
