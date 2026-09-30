"""List one directory level under an explicit root.

Does not read file bytes, follow directory symlinks, or open a port.
A symlink whose resolved path is outside the root is refused.
"""
from __future__ import annotations

import stat
from datetime import datetime, timezone
from pathlib import Path


def _norm_rel(rel: str) -> str:
    rel = (rel or "").replace("\\", "/").strip("/")
    parts = [p for p in rel.split("/") if p and p != "."]
    if any(p == ".." for p in parts):
        raise ValueError("path traversal")
    return "/".join(parts)


def _inside(root: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(root)
    except (OSError, ValueError):
        return False
    return True


def list_dir(root: Path | str, rel: str = "") -> dict:
    """Return one level of names under ``root``.

    ``root`` is required and must already be a directory. There is no default.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        raise ValueError("root is not a directory")
    root_resolved = root_path.resolve()
    rel_norm = _norm_rel(rel)

    current = root_resolved
    if rel_norm:
        for part in rel_norm.split("/"):
            current = current / part
            try:
                st = current.lstat()
            except OSError as exc:
                raise ValueError("not a directory") from exc
            if stat.S_ISLNK(st.st_mode):
                raise ValueError("symlink directory")
            if not stat.S_ISDIR(st.st_mode):
                raise ValueError("not a directory")

    entries: list[dict] = []
    refused: list[dict] = []
    try:
        children = list(current.iterdir())
    except OSError as exc:
        raise ValueError(str(exc)) from exc

    for child in sorted(children, key=lambda p: p.name.lower()):
        try:
            st = child.lstat()
        except OSError:
            refused.append({"name": child.name, "reason": "unreadable"})
            continue
        if stat.S_ISLNK(st.st_mode):
            try:
                target = child.readlink()
            except OSError:
                refused.append({"name": child.name, "reason": "symlink"})
                continue
            resolved = target if target.is_absolute() else (child.parent / target)
            if not _inside(root_resolved, resolved):
                refused.append({"name": child.name, "reason": "outside root"})
                continue
            kind = "link"
            size = st.st_size
        elif stat.S_ISDIR(st.st_mode):
            kind = "dir"
            size = None
        elif stat.S_ISREG(st.st_mode):
            kind = "file"
            size = st.st_size
        else:
            kind = "other"
            size = st.st_size
        entries.append(
            {
                "name": child.name,
                "type": kind,
                "size": size,
                "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
            }
        )

    return {
        "ok": True,
        "root": str(root_resolved),
        "rel": rel_norm,
        "count": len(entries),
        "entries": entries,
        "refused": refused,
    }
