#!/usr/bin/env python3
"""Scoped path index (WO-MIG-42).

Lists path and kind for three Ecosystem source trees. Does not read file bytes,
hash files, or store symlink targets. A root outside the allowlist exits
before any index file is replaced.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
ECOSYSTEM = Path("/home/rootrecord/RootRecord-Ecosystem")
DB = ECOSYSTEM / "2 - RootRecord-Database"
DATA = DB / "System" / "PathIndex"
LOG_DIR = DB / "Logs" / "System" / "PathIndex"

ALLOW = (
    ECOSYSTEM / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server",
    ECOSYSTEM / "5 - RootRecord-Library",
    ECOSYSTEM / "6 - Android Development",
)

STUB_NAMES = frozenset({"node_modules", ".venv", "venv", "__pycache__"})


def now_iso() -> str:
    return datetime.now(HST).isoformat(timespec="seconds")


def is_stub(path: Path) -> bool:
    if path.name in STUB_NAMES:
        return True
    return path.name == "objects" and path.parent.name == ".git"


def under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def accepted(path: Path, *, fixture: bool) -> bool:
    if fixture:
        return under(path, Path(tempfile.gettempdir()))
    return any(under(path, root) for root in ALLOW)


def fmt(path: Path, kind: str) -> str:
    return f"{path.as_posix()}\t{kind}"


def load_mtimes(path: Path) -> dict[str, float]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def load_old(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def slice_prefix(old: list[str], prefix: str) -> list[str]:
    pfx = prefix if prefix.endswith("/") else prefix + "/"
    hit = []
    for line in old:
        base = line.split("\t", 1)[0]
        if base == prefix or base.startswith(pfx):
            hit.append(line)
    return hit


def walk_tree(
    root: Path,
    *,
    old_paths: list[str],
    mtimes: dict[str, float],
    seen: set[tuple[int, int]],
    stats: dict,
) -> list[str]:
    out: list[str] = []
    if not root.exists():
        stats["missing"] += 1
        return [fmt(root, "missing")]

    def rec(cur: Path) -> None:
        stats["visited"] += 1
        try:
            st = cur.lstat()
        except OSError:
            out.append(fmt(cur, "error"))
            stats["errors"] += 1
            return
        key = (st.st_dev, st.st_ino)
        if key in seen:
            out.append(fmt(cur, "error"))
            stats["errors"] += 1
            return
        seen.add(key)
        posix = cur.as_posix()

        if os.path.islink(cur):
            out.append(fmt(cur, "symlink"))
            stats["symlinks"] += 1
            return

        if not cur.is_dir():
            out.append(fmt(cur, "file"))
            stats["files"] += 1
            return

        if is_stub(cur):
            out.append(fmt(cur, "dir-stub"))
            stats["stubs"] += 1
            mtimes[posix] = st.st_mtime
            return

        prev = mtimes.get(posix)
        if prev is not None and prev == st.st_mtime and old_paths:
            reused = slice_prefix(old_paths, posix)
            if reused:
                out.extend(reused)
                stats["reused_dirs"] += 1
                return

        stats["rewalked_dirs"] += 1
        out.append(fmt(cur, "dir"))
        mtimes[posix] = st.st_mtime
        try:
            with os.scandir(cur) as it:
                kids = sorted(it, key=lambda ent: ent.name.lower())
        except OSError:
            out.append(fmt(cur, "error"))
            stats["errors"] += 1
            return
        for ent in kids:
            rec(Path(ent.path))

    rec(root)
    return out


def merge(parts: list[list[str]]) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for block in parts:
        for line in block:
            key = line.split("\t", 1)[0]
            if key in seen:
                continue
            seen.add(key)
            merged.append(line)
    merged.sort(key=lambda line: line.split("\t", 1)[0].lower())
    return merged


def write_current(path: Path, stats: dict, n_paths: int, roots: list[Path]) -> None:
    lines = [
        "# Path index run",
        "",
        f"Generated {now_iso()}.",
        "",
        f"- roots walked: {len(roots)}",
        f"- paths indexed: {n_paths}",
        f"- dir re-walks: {stats.get('rewalked_dirs', 0)}",
        f"- dirs reused: {stats.get('reused_dirs', 0)}",
        f"- stubs: {stats.get('stubs', 0)}",
        f"- errors: {stats.get('errors', 0)}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def run(roots: list[Path], data: Path, log_dir: Path) -> int:
    paths_file = data / "paths.txt"
    mtime_file = data / "dir-mtimes.json"
    current = log_dir / "current.md"
    old_paths = load_old(paths_file)
    mtimes = load_mtimes(mtime_file)
    stats = {
        "visited": 0,
        "rewalked_dirs": 0,
        "reused_dirs": 0,
        "files": 0,
        "stubs": 0,
        "symlinks": 0,
        "errors": 0,
        "missing": 0,
    }
    seen: set[tuple[int, int]] = set()
    blocks = [
        walk_tree(root, old_paths=old_paths, mtimes=mtimes, seen=seen, stats=stats)
        for root in roots
    ]
    merged = merge(blocks)
    body = "\n".join(merged) + ("\n" if merged else "")
    atomic_text(paths_file, body)
    atomic_text(mtime_file, json.dumps(mtimes, indent=0, sort_keys=True) + "\n")
    log_dir.mkdir(parents=True, exist_ok=True)
    write_current(current, stats, len(merged), roots)
    print(
        f"paths={len(merged)} rewalk={stats['rewalked_dirs']} "
        f"reuse_dirs={stats['reused_dirs']} stubs={stats['stubs']} errors={stats['errors']}"
    )
    return 0


def parse_args(argv: list[str]) -> tuple[list[Path], Path, Path, bool]:
    fixture = False
    roots: list[Path] = []
    out: Path | None = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--fixture":
            fixture = True
            i += 1
            if i >= len(argv):
                raise SystemExit("refused: --fixture needs a directory")
            roots.append(Path(argv[i]))
        elif arg == "--out":
            i += 1
            if i >= len(argv):
                raise SystemExit("refused: --out needs a directory")
            out = Path(argv[i])
        elif arg == "--root":
            i += 1
            if i >= len(argv):
                raise SystemExit("refused: --root needs a directory")
            roots.append(Path(argv[i]))
        else:
            raise SystemExit(f"refused: unknown argument {arg}")
        i += 1
    if fixture:
        if out is None:
            raise SystemExit("refused: --fixture needs --out")
        if not under(out, Path(tempfile.gettempdir())):
            raise SystemExit("refused: --out is outside the temp directory")
        return roots, out, out, True
    data, log_dir = DATA, LOG_DIR
    if not roots:
        roots = list(ALLOW)
    return roots, data, log_dir, False


def main(argv: list[str] | None = None) -> int:
    roots, data, log_dir, fixture = parse_args(list(sys.argv[1:] if argv is None else argv))
    for root in roots:
        if not accepted(root, fixture=fixture):
            print(f"refused root: {root}", file=sys.stderr)
            return 2
    return run(roots, data, log_dir)


if __name__ == "__main__":
    raise SystemExit(main())
