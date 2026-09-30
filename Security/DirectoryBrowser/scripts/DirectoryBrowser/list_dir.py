# ==============================================================================
# FILE: Security/DirectoryBrowser/scripts/DirectoryBrowser/list_dir.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""List one directory level under an explicit root.

Does not read file bytes, follow directory symlinks, or open a port.
A symlink whose resolved path is outside the root is refused.
"""
from __future__ import annotations  # info: from __future__ import annotations

import stat  # info: import stat
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path


# ====================================================
# SECTION: function _norm_rel
# What it does:  norm rel.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _norm_rel(rel: str) -> str:  # info: def _norm_rel
    rel = (rel or "").replace("\\", "/").strip("/")  # info: set rel
    parts = [p for p in rel.split("/") if p and p != "."]  # info: set parts
    if any(p == ".." for p in parts):  # info: if any ( p == ".." for p
        raise ValueError("path traversal")  # info: raise ValueError ( "path traversal" )
    return "/".join(parts)  # info: return "/" . join ( parts )


# ====================================================
# SECTION: function _inside
# What it does:  inside.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _inside(root: Path, target: Path) -> bool:  # info: def _inside
    try:  # info: try :
        target.resolve().relative_to(root)  # info: target . resolve ( ) . relative_to (
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function list_dir
# What it does: Return one level of names under ``root``. ``root`` is required and must already be a directory. There is no default.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def list_dir(root: Path | str, rel: str = "") -> dict:  # info: def list_dir
    """Return one level of names under ``root``.

    ``root`` is required and must already be a directory. There is no default.
    """
    root_path = Path(root)  # info: set root_path
    if not root_path.is_dir():  # info: if not root_path . is_dir ( ) :
        raise ValueError("root is not a directory")  # info: raise ValueError ( "root is not a directory" )
    root_resolved = root_path.resolve()  # info: set root_resolved
    rel_norm = _norm_rel(rel)  # info: set rel_norm

    current = root_resolved  # info: set current
    if rel_norm:  # info: if rel_norm :
        for part in rel_norm.split("/"):  # info: for part in rel_norm . split ( "/"
            current = current / part  # info: set current
            try:  # info: try :
                st = current.lstat()  # info: set st
            except OSError as exc:  # info: except OSError as exc :
                raise ValueError("not a directory") from exc  # info: raise ValueError ( "not a directory" ) from exc
            if stat.S_ISLNK(st.st_mode):  # info: if stat . S_ISLNK ( st . st_mode
                raise ValueError("symlink directory")  # info: raise ValueError ( "symlink directory" )
            if not stat.S_ISDIR(st.st_mode):  # info: if not stat . S_ISDIR ( st .
                raise ValueError("not a directory")  # info: raise ValueError ( "not a directory" )

    entries: list[dict] = []  # info: set entries
    refused: list[dict] = []  # info: set refused
    try:  # info: try :
        children = list(current.iterdir())  # info: set children
    except OSError as exc:  # info: except OSError as exc :
        raise ValueError(str(exc)) from exc  # info: raise ValueError ( str ( exc ) )

    for child in sorted(children, key=lambda p: p.name.lower()):  # info: for child in sorted ( children , key
        try:  # info: try :
            st = child.lstat()  # info: set st
        except OSError:  # info: except OSError :
            refused.append({"name": child.name, "reason": "unreadable"})  # info: refused . append ( { "name" : child
            continue  # info: continue
        if stat.S_ISLNK(st.st_mode):  # info: if stat . S_ISLNK ( st . st_mode
            try:  # info: try :
                target = child.readlink()  # info: set target
            except OSError:  # info: except OSError :
                refused.append({"name": child.name, "reason": "symlink"})  # info: refused . append ( { "name" : child
                continue  # info: continue
            resolved = target if target.is_absolute() else (child.parent / target)  # info: set resolved
            if not _inside(root_resolved, resolved):  # info: if not _inside ( root_resolved , resolved )
                refused.append({"name": child.name, "reason": "outside root"})  # info: refused . append ( { "name" : child
                continue  # info: continue
            kind = "link"  # info: set kind
            size = st.st_size  # info: set size
        elif stat.S_ISDIR(st.st_mode):  # info: elif stat . S_ISDIR ( st . st_mode
            kind = "dir"  # info: set kind
            size = None  # info: set size
        elif stat.S_ISREG(st.st_mode):  # info: elif stat . S_ISREG ( st . st_mode
            kind = "file"  # info: set kind
            size = st.st_size  # info: set size
        else:  # info: else :
            kind = "other"  # info: set kind
            size = st.st_size  # info: set size
        entries.append(  # info: entries . append (
            {  # info: {
                "name": child.name,  # info: "name" : child . name ,
                "type": kind,  # info: "type" : kind ,
                "size": size,  # info: "size" : size ,
                "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),  # info: "mtime" : datetime . fromtimestamp ( st .
            }  # info: }
        )  # info: )

    return {  # info: return {
        "ok": True,  # info: "ok" : True ,
        "root": str(root_resolved),  # info: "root" : str ( root_resolved ) ,
        "rel": rel_norm,  # info: "rel" : rel_norm ,
        "count": len(entries),  # info: "count" : len ( entries ) ,
        "entries": entries,  # info: "entries" : entries ,
        "refused": refused,  # info: "refused" : refused ,
    }  # info: }
