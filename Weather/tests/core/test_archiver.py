# ==============================================================================
# FILE: Weather/tests/core/test_archiver.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/archiver.py's age-out-and-write mechanic."""  # info: """Smoke tests for core/archiver.py's age-out-and-write mechanic."""
from __future__ import annotations  # info: from __future__ import annotations

import tempfile  # info: import tempfile
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path

from core.archiver import age_out_and_write  # info: from core . archiver import age_out_and_write
from core.manifest import ResourceState  # info: from core . manifest import ResourceState
from core.path_resolver import resolve  # info: from core . path_resolver import resolve


# ====================================================
# SECTION: function test_first_write_has_no_archive_move
# What it does: test first write has no archive move.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_first_write_has_no_archive_move():  # info: def test_first_write_has_no_archive_move
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        resolved = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")  # info: set resolved
        state = ResourceState(resource_id="r1", url="u", local_resource_dir="d")  # info: set state
        now = datetime(2026, 9, 24, 14, 0, 0, tzinfo=timezone.utc)  # info: set now

        written = age_out_and_write(tmp, resolved, state, b"frame1", now)  # info: set written

        assert written.is_file()  # info: assert written . is_file ( )
        assert written.read_bytes() == b"frame1"  # info: assert written . read_bytes ( ) == b"frame1"
        archive_dir = Path(resolved.archive_dir(tmp))  # info: set archive_dir
        assert not archive_dir.exists() or not any(archive_dir.rglob("*"))  # info: assert not archive_dir . exists ( ) or


# ====================================================
# SECTION: function test_second_write_ages_out_first_under_its_own_timestamp
# What it does: test second write ages out first under its own timestamp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_second_write_ages_out_first_under_its_own_timestamp():  # info: def test_second_write_ages_out_first_under_its_own_timestamp
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        resolved = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")  # info: set resolved
        state = ResourceState(resource_id="r1", url="u", local_resource_dir="d")  # info: set state
        t1 = datetime(2026, 9, 24, 14, 0, 0, tzinfo=timezone.utc)  # 04:00 HST
        t2 = datetime(2026, 9, 24, 20, 0, 0, tzinfo=timezone.utc)  # 10:00 HST

        age_out_and_write(tmp, resolved, state, b"frame1", t1)  # info: call age_out_and_write
        state.current_fetch_timestamp_hst = t1.astimezone(timezone.utc).isoformat()  # info: state . current_fetch_timestamp_hst = t1 . astimezone (
        # Emulate what fetch/_engine.py does: record the fetch timestamp in
        # HST (via hst_time.hst_now().isoformat()) before the next write.
        from core import hst_time  # info: from core import hst_time
        state.current_fetch_timestamp_hst = hst_time.to_hst(t1).isoformat()  # info: state . current_fetch_timestamp_hst = hst_time . to_hst (

        written2 = age_out_and_write(tmp, resolved, state, b"frame2", t2)  # info: set written2

        assert written2.read_bytes() == b"frame2"  # info: assert written2 . read_bytes ( ) == b"frame2"
        archive_dir = Path(resolved.archive_dir(tmp))  # info: set archive_dir
        archived_files = list(archive_dir.rglob("*.gif"))  # info: set archived_files
        assert len(archived_files) == 1  # info: assert len ( archived_files ) == 1
        assert archived_files[0].read_bytes() == b"frame1"  # info: assert archived_files [ 0 ] . read_bytes (
        # Archived under t1's HST date folder, not t2's.
        assert "09-24-2026" in str(archived_files[0])  # info: assert "09-24-2026" in str ( archived_files [ 0
