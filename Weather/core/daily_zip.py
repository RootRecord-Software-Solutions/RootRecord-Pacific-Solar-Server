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
from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ConsolidationResult:
    date_folder: str  # MM-DD-YYYY
    zip_path: str | None
    files_discovered: int
    files_written: int
    verified: bool
    deleted_source_dirs: int
    status: str  # "consolidated" | "nothing_to_do" | "verification_failed"
    dirs_removed: list[str] = field(default_factory=list)


def _discover_dated_archive_dirs(base_dir: Path, date_folder: str) -> list[Path]:
    """Every `archive/<date_folder>/` directory anywhere under base_dir --
    one per resource that had at least one change archived that day.
    Excludes the consolidated-zips folder itself (`archives/`, plural,
    distinct from each resource's own `archive/`, singular).
    """
    found = []
    for archive_dir in base_dir.rglob("archive"):
        if archive_dir.parent.name == "archives":
            continue  # never recurse into the consolidated-zip output folder
        dated = archive_dir / date_folder
        if dated.is_dir():
            found.append(dated)
    return found


def consolidate_day(base_dir: str, date_folder: str) -> ConsolidationResult:
    """Consolidate every resource's `archive/<date_folder>/` folder under
    `base_dir` into one `hfo/archives/<date_folder>_Daily_Archive.zip`,
    then remove the now-redundant dated subfolders. `date_folder` is
    MM-DD-YYYY, HST, of the day that just closed (i.e. "yesterday" relative
    to the HST midnight rollover that triggered this).
    """
    base = Path(base_dir)
    dated_dirs = _discover_dated_archive_dirs(base, date_folder)

    files_to_zip: list[tuple[Path, str]] = []  # (absolute path, arcname relative to base_dir)
    for dated_dir in dated_dirs:
        for f in dated_dir.rglob("*"):
            if f.is_file():
                files_to_zip.append((f, str(f.relative_to(base))))

    if not files_to_zip:
        return ConsolidationResult(
            date_folder=date_folder, zip_path=None, files_discovered=0,
            files_written=0, verified=True, deleted_source_dirs=0,
            status="nothing_to_do",
        )

    archives_dir = base / "archives"
    archives_dir.mkdir(parents=True, exist_ok=True)
    zip_path = archives_dir / f"{date_folder}_Daily_Archive.zip"
    tmp_zip_path = archives_dir / f".{date_folder}_Daily_Archive.zip.tmp"

    with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for abs_path, arcname in files_to_zip:
            zf.write(abs_path, arcname=arcname)

    verified, files_written = _verify_zip(tmp_zip_path, expected_count=len(files_to_zip))

    if not verified:
        # Leave originals untouched on a bad zip -- verification gates the
        # destructive delete step, per nws_plan.md Section 8 step 5.
        return ConsolidationResult(
            date_folder=date_folder, zip_path=str(tmp_zip_path),
            files_discovered=len(files_to_zip), files_written=files_written,
            verified=False, deleted_source_dirs=0, status="verification_failed",
        )

    tmp_zip_path.replace(zip_path)

    removed = []
    for dated_dir in dated_dirs:
        _remove_tree(dated_dir)
        removed.append(str(dated_dir))
        # The resource's parent `archive/` folder itself stays in place,
        # empty, ready for today's new date-folder -- only the dated
        # subfolder is removed, per the plan.

    return ConsolidationResult(
        date_folder=date_folder, zip_path=str(zip_path),
        files_discovered=len(files_to_zip), files_written=files_written,
        verified=True, deleted_source_dirs=len(removed), status="consolidated",
        dirs_removed=removed,
    )


def _verify_zip(zip_path: Path, expected_count: int) -> tuple[bool, int]:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad_file = zf.testzip()  # None if every member is intact
            if bad_file is not None:
                return False, 0
            names = zf.namelist()
    except (zipfile.BadZipFile, OSError):
        return False, 0
    return (len(names) == expected_count), len(names)


def _remove_tree(path: Path) -> None:
    if not path.is_dir():
        return
    for child in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    path.rmdir()
