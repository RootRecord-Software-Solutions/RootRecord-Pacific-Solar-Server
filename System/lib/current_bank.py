# ==============================================================================
# FILE: System/lib/current_bank.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Stable *_current bank writes with archive-on-replace.

Live path stays *_current for LLM/desk reads. On replace, the previous file
moves to archive/YYYYMMDD/<stem>_<HHMMSS><ext> (HST). Do not stamp a new live
file for every sample.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import tempfile  # info: import tempfile
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST


# ====================================================
# SECTION: function is_current_product
# What it does: True when the bank filename contains _current (stable live path).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_current_product(path_rel: str, dest: Path | None = None) -> bool:  # info: def is_current_product
    """True when the bank filename contains _current (stable live path)."""  # info: docstring
    name = (dest.name if dest is not None else Path(path_rel).name)  # info: set name
    return "_current" in name  # info: return "_current" in name


# ====================================================
# SECTION: function archive_before_replace
# What it does: If dest exists and basename contains _current, rename into sibling archive/YYYYMMDD/.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def archive_before_replace(dest: Path, path_rel: str = "") -> str | None:  # info: def archive_before_replace
    """Keep the stable *_current path; move the previous file under archive/."""  # info: docstring
    if not dest.is_file():  # info: if not dest . is_file ( )
        return None  # info: return None
    if not is_current_product(path_rel or dest.name, dest):  # info: if not is_current_product
        return None  # info: return None
    now = datetime.now(HST).replace(microsecond=0)  # info: set now
    archive_dir = dest.parent / "archive" / now.strftime("%Y%m%d")  # info: set archive_dir
    archive_dir.mkdir(parents=True, exist_ok=True)  # info: archive_dir . mkdir
    archived = archive_dir / f"{dest.stem}_{now.strftime('%H%M%S')}{dest.suffix}"  # info: set archived
    if archived.exists():  # info: if archived . exists ( )
        archived = archive_dir / f"{dest.stem}_{now.strftime('%H%M%S')}_{os.getpid()}{dest.suffix}"  # info: set archived
    os.rename(dest, archived)  # info: os . rename ( dest , archived )
    return str(archived)  # info: return str ( archived )


# ====================================================
# SECTION: function write_current_bytes
# What it does: Archive the previous *_current file if present, then atomically write the new bytes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_current_bytes(dest: Path, data: bytes) -> Path:  # info: def write_current_bytes
    """Archive-on-replace then atomic write for a *_current product."""  # info: docstring
    if "_current" not in dest.name:  # info: if "_current" not in dest . name
        raise ValueError(f"live bank path must contain _current: {dest.name}")  # info: raise ValueError
    dest.parent.mkdir(parents=True, exist_ok=True)  # info: dest . parent . mkdir
    archive_before_replace(dest)  # info: call archive_before_replace
    fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".current-")  # info: set fd , tmp
    try:  # info: try
        with os.fdopen(fd, "wb") as f:  # info: with os . fdopen ( fd , "wb" )
            f.write(data)  # info: f . write ( data )
        os.replace(tmp, dest)  # info: os . replace ( tmp , dest )
    finally:  # info: finally
        if os.path.exists(tmp):  # info: if os . path . exists ( tmp )
            try:  # info: try
                os.unlink(tmp)  # info: os . unlink ( tmp )
            except OSError:  # info: except OSError
                pass  # info: pass
    return dest  # info: return dest


# ====================================================
# SECTION: function write_current_json
# What it does: Archive-on-replace then write one JSON object to a *_current path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_current_json(dest: Path, obj: Any) -> Path:  # info: def write_current_json
    """Archive-on-replace then write one JSON object to a *_current path."""  # info: docstring
    raw = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")  # info: set raw
    return write_current_bytes(dest, raw)  # info: return write_current_bytes
