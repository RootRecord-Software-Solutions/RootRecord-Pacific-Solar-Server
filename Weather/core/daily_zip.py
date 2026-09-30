# ==============================================================================
# FILE: Weather/core/daily_zip.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Section 8's consolidation: discover -> zip -> verify -> delete. Called
by archive/consolidate.py, which is triggered by scheduler/run_cycle.py at
HST midnight rollover.

Walks every per-resource `archive/<MM-DD-YYYY>/` folder under `base_dir`
for the day that just closed, zips them into one file preserving each
file's path relative to `base_dir` (so the zip mirrors the live tree), then
-- only after confirming the zip is intact and its file count matches --
deletes the original dated subfolders. A failed/partial zip leaves the
originals untouched, per the plan's explicit verification gate.
"""
from __future__ import annotations  # info: from __future__ import annotations

import zipfile  # info: import zipfile
from dataclasses import dataclass, field  # info: from dataclasses import dataclass , field
from pathlib import Path  # info: from pathlib import Path


# ====================================================
# SECTION: class ConsolidationResult
# What it does: ConsolidationResult.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class ConsolidationResult:  # info: class ConsolidationResult
    date_folder: str  # MM-DD-YYYY
    zip_path: str | None  # info: set zip_path
    files_discovered: int  # info: set files_discovered
    files_written: int  # info: set files_written
    verified: bool  # info: set verified
    deleted_source_dirs: int  # info: set deleted_source_dirs
    status: str  # "consolidated" | "nothing_to_do" | "verification_failed"
    dirs_removed: list[str] = field(default_factory=list)  # info: set dirs_removed


# ====================================================
# SECTION: function _discover_dated_archive_dirs
# What it does: Every `archive/<date_folder>/` directory anywhere under base_dir -- one per resource that had at least one change archived that day. Excludes the consolidated-zips folder itself (`
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _discover_dated_archive_dirs(base_dir: Path, date_folder: str) -> list[Path]:  # info: def _discover_dated_archive_dirs
    """Every `archive/<date_folder>/` directory anywhere under base_dir --
    one per resource that had at least one change archived that day.
    Excludes the consolidated-zips folder itself (`archives/`, plural,
    distinct from each resource's own `archive/`, singular).
    """
    found = []  # info: set found
    for archive_dir in base_dir.rglob("archive"):  # info: for archive_dir in base_dir . rglob ( "archive"
        if archive_dir.parent.name == "archives":  # info: if archive_dir . parent . name == "archives"
            continue  # never recurse into the consolidated-zip output folder
        dated = archive_dir / date_folder  # info: set dated
        if dated.is_dir():  # info: if dated . is_dir ( ) :
            found.append(dated)  # info: found . append ( dated )
    return found  # info: return found


# ====================================================
# SECTION: function consolidate_day
# What it does: Consolidate every resource's `archive/<date_folder>/` folder under `base_dir` into one `hfo/archives/<date_folder>_Daily_Archive.zip`, then remove the now-redundant dated subfolder
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def consolidate_day(base_dir: str, date_folder: str) -> ConsolidationResult:  # info: def consolidate_day
    """Consolidate every resource's `archive/<date_folder>/` folder under
    `base_dir` into one `hfo/archives/<date_folder>_Daily_Archive.zip`,
    then remove the now-redundant dated subfolders. `date_folder` is
    MM-DD-YYYY, HST, of the day that just closed (i.e. "yesterday" relative
    to the HST midnight rollover that triggered this).
    """
    base = Path(base_dir)  # info: set base
    dated_dirs = _discover_dated_archive_dirs(base, date_folder)  # info: set dated_dirs

    files_to_zip: list[tuple[Path, str]] = []  # (absolute path, arcname relative to base_dir)
    for dated_dir in dated_dirs:  # info: for dated_dir in dated_dirs :
        for f in dated_dir.rglob("*"):  # info: for f in dated_dir . rglob ( "*"
            if f.is_file():  # info: if f . is_file ( ) :
                files_to_zip.append((f, str(f.relative_to(base))))  # info: files_to_zip . append ( ( f , str

    if not files_to_zip:  # info: if not files_to_zip :
        return ConsolidationResult(  # info: return ConsolidationResult (
            date_folder=date_folder, zip_path=None, files_discovered=0,  # info: set date_folder
            files_written=0, verified=True, deleted_source_dirs=0,  # info: set files_written
            status="nothing_to_do",  # info: set status
        )  # info: )

    archives_dir = base / "archives"  # info: set archives_dir
    archives_dir.mkdir(parents=True, exist_ok=True)  # info: archives_dir . mkdir ( parents = True ,
    zip_path = archives_dir / f"{date_folder}_Daily_Archive.zip"  # info: set zip_path
    tmp_zip_path = archives_dir / f".{date_folder}_Daily_Archive.zip.tmp"  # info: set tmp_zip_path

    with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:  # info: with zipfile . ZipFile ( tmp_zip_path , "w"
        for abs_path, arcname in files_to_zip:  # info: for abs_path , arcname in files_to_zip :
            zf.write(abs_path, arcname=arcname)  # info: zf . write ( abs_path , arcname =

    verified, files_written = _verify_zip(tmp_zip_path, expected_count=len(files_to_zip))  # info: verified , files_written = _verify_zip ( tmp_zip_path ,

    if not verified:  # info: if not verified :
        # Leave originals untouched on a bad zip -- verification gates the
        # destructive delete step, per nws_plan.md Section 8 step 5.
        return ConsolidationResult(  # info: return ConsolidationResult (
            date_folder=date_folder, zip_path=str(tmp_zip_path),  # info: set date_folder
            files_discovered=len(files_to_zip), files_written=files_written,  # info: set files_discovered
            verified=False, deleted_source_dirs=0, status="verification_failed",  # info: set verified
        )  # info: )

    tmp_zip_path.replace(zip_path)  # info: tmp_zip_path . replace ( zip_path )

    removed = []  # info: set removed
    for dated_dir in dated_dirs:  # info: for dated_dir in dated_dirs :
        _remove_tree(dated_dir)  # info: call _remove_tree
        removed.append(str(dated_dir))  # info: removed . append ( str ( dated_dir )
        # The resource's parent `archive/` folder itself stays in place,
        # empty, ready for today's new date-folder -- only the dated
        # subfolder is removed, per the plan.

    return ConsolidationResult(  # info: return ConsolidationResult (
        date_folder=date_folder, zip_path=str(zip_path),  # info: set date_folder
        files_discovered=len(files_to_zip), files_written=files_written,  # info: set files_discovered
        verified=True, deleted_source_dirs=len(removed), status="consolidated",  # info: set verified
        dirs_removed=removed,  # info: set dirs_removed
    )  # info: )


# ====================================================
# SECTION: function _verify_zip
# What it does:  verify zip.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _verify_zip(zip_path: Path, expected_count: int) -> tuple[bool, int]:  # info: def _verify_zip
    try:  # info: try :
        with zipfile.ZipFile(zip_path, "r") as zf:  # info: with zipfile . ZipFile ( zip_path , "r"
            bad_file = zf.testzip()  # None if every member is intact
            if bad_file is not None:  # info: if bad_file is not None :
                return False, 0  # info: return False , 0
            names = zf.namelist()  # info: set names
    except (zipfile.BadZipFile, OSError):  # info: except ( zipfile . BadZipFile , OSError )
        return False, 0  # info: return False , 0
    return (len(names) == expected_count), len(names)  # info: return ( len ( names ) == expected_count


# ====================================================
# SECTION: function _remove_tree
# What it does:  remove tree.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _remove_tree(path: Path) -> None:  # info: def _remove_tree
    if not path.is_dir():  # info: if not path . is_dir ( ) :
        return  # info: return
    for child in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):  # info: for child in sorted ( path . rglob
        if child.is_file() or child.is_symlink():  # info: if child . is_file ( ) or child
            child.unlink()  # info: child . unlink ( )
        elif child.is_dir():  # info: elif child . is_dir ( ) :
            child.rmdir()  # info: child . rmdir ( )
    path.rmdir()  # info: path . rmdir ( )
