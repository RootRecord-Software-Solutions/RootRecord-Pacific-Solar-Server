# ==============================================================================
# FILE: Weather/tests/core/test_daily_zip.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/daily_zip.py's discover -> zip -> verify -> delete
flow, per nws_plan.md Section 8."""
from __future__ import annotations  # info: from __future__ import annotations

import tempfile  # info: import tempfile
import zipfile  # info: import zipfile
from pathlib import Path  # info: from pathlib import Path

from core.daily_zip import consolidate_day  # info: from core . daily_zip import consolidate_day


# ====================================================
# SECTION: function _make_resource_archive
# What it does:  make resource archive.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _make_resource_archive(base: Path, resource_rel: str, date_folder: str, filename: str, content: bytes):  # info: def _make_resource_archive
    d = base / resource_rel / "archive" / date_folder  # info: set d
    d.mkdir(parents=True, exist_ok=True)  # info: d . mkdir ( parents = True ,
    (d / filename).write_bytes(content)  # info: call (


# ====================================================
# SECTION: function test_nothing_to_zip_when_no_dated_folders
# What it does: test nothing to zip when no dated folders.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_nothing_to_zip_when_no_dated_folders():  # info: def test_nothing_to_zip_when_no_dated_folders
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        result = consolidate_day(tmp, "09-24-2026")  # info: set result
        assert result.status == "nothing_to_do"  # info: assert result . status == "nothing_to_do"


# ====================================================
# SECTION: function test_consolidates_multiple_resources_and_removes_originals
# What it does: test consolidates multiple resources and removes originals.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_consolidates_multiple_resources_and_removes_originals():  # info: def test_consolidates_multiple_resources_and_removes_originals
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        base = Path(tmp)  # info: set base
        _make_resource_archive(base, "weather.gov/images/hfo/satellite/Hawaii_IR", "09-24-2026",  # info: call _make_resource_archive
                                "Hawaii_IR_20260924T040000-1000.gif", b"frame-a")  # info: "Hawaii_IR_20260924T040000-1000.gif" , b"frame-a" )
        _make_resource_archive(base, "api.weather.gov/alerts/active/area=HI", "09-24-2026",  # info: call _make_resource_archive
                                "area=HI_20260924T050000-1000.json", b'{"a":1}')  # info: "area=HI_20260924T050000-1000.json" , b'{"a":1}' )
        # A folder for a DIFFERENT date should NOT be swept up.
        _make_resource_archive(base, "weather.gov/images/hfo/satellite/Hawaii_IR", "09-25-2026",  # info: call _make_resource_archive
                                "Hawaii_IR_20260925T040000-1000.gif", b"frame-b")  # info: "Hawaii_IR_20260925T040000-1000.gif" , b"frame-b" )

        result = consolidate_day(tmp, "09-24-2026")  # info: set result

        assert result.status == "consolidated"  # info: assert result . status == "consolidated"
        assert result.files_written == 2  # info: assert result . files_written == 2
        assert result.deleted_source_dirs == 2  # info: assert result . deleted_source_dirs == 2
        assert Path(result.zip_path).is_file()  # info: assert Path ( result . zip_path ) .

        with zipfile.ZipFile(result.zip_path) as zf:  # info: with zipfile . ZipFile ( result . zip_path
            names = set(zf.namelist())  # info: set names
        assert any(n.endswith("Hawaii_IR_20260924T040000-1000.gif") for n in names)  # info: assert any ( n . endswith ( "Hawaii_IR_20260924T040000-1000.gif"
        assert any(n.endswith("area=HI_20260924T050000-1000.json") for n in names)  # info: assert any ( n . endswith ( "area=HI_20260924T050000-1000.json"

        # 09-24 folders gone, 09-25 folder untouched.
        assert not (base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive/09-24-2026").exists()  # info: assert not ( base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive/09-24-2026" ) .
        assert (base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive/09-25-2026").is_dir()  # info: assert ( base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive/09-25-2026" ) . is_dir
        # Parent archive/ dirs stay in place (empty or with today's folder).
        assert (base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive").is_dir()  # info: assert ( base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive" ) . is_dir


# ====================================================
# SECTION: function test_does_not_sweep_the_consolidated_archives_output_folder
# What it does: test does not sweep the consolidated archives output folder.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_does_not_sweep_the_consolidated_archives_output_folder():  # info: def test_does_not_sweep_the_consolidated_archives_output_folder
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        base = Path(tmp)  # info: set base
        _make_resource_archive(base, "weather.gov/x", "09-24-2026", "x_1.gif", b"a")  # info: call _make_resource_archive
        first = consolidate_day(tmp, "09-24-2026")  # info: set first
        assert first.status == "consolidated"  # info: assert first . status == "consolidated"

        # Running again for the same date should find nothing left to zip
        # (and must not choke on scanning its own output folder).
        second = consolidate_day(tmp, "09-24-2026")  # info: set second
        assert second.status == "nothing_to_do"  # info: assert second . status == "nothing_to_do"
