"""Smoke tests for core/archiver.py's age-out-and-write mechanic."""
from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from core.archiver import age_out_and_write
from core.manifest import ResourceState
from core.path_resolver import resolve


def test_first_write_has_no_archive_move():
    with tempfile.TemporaryDirectory() as tmp:
        resolved = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")
        state = ResourceState(resource_id="r1", url="u", local_resource_dir="d")
        now = datetime(2026, 9, 24, 14, 0, 0, tzinfo=timezone.utc)

        written = age_out_and_write(tmp, resolved, state, b"frame1", now)

        assert written.is_file()
        assert written.read_bytes() == b"frame1"
        archive_dir = Path(resolved.archive_dir(tmp))
        assert not archive_dir.exists() or not any(archive_dir.rglob("*"))


def test_second_write_ages_out_first_under_its_own_timestamp():
    with tempfile.TemporaryDirectory() as tmp:
        resolved = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")
        state = ResourceState(resource_id="r1", url="u", local_resource_dir="d")
        t1 = datetime(2026, 9, 24, 14, 0, 0, tzinfo=timezone.utc)  # 04:00 HST
        t2 = datetime(2026, 9, 24, 20, 0, 0, tzinfo=timezone.utc)  # 10:00 HST

        age_out_and_write(tmp, resolved, state, b"frame1", t1)
        state.current_fetch_timestamp_hst = t1.astimezone(timezone.utc).isoformat()
        # Emulate what fetch/_engine.py does: record the fetch timestamp in
        # HST (via hst_time.hst_now().isoformat()) before the next write.
        from core import hst_time
        state.current_fetch_timestamp_hst = hst_time.to_hst(t1).isoformat()

        written2 = age_out_and_write(tmp, resolved, state, b"frame2", t2)

        assert written2.read_bytes() == b"frame2"
        archive_dir = Path(resolved.archive_dir(tmp))
        archived_files = list(archive_dir.rglob("*.gif"))
        assert len(archived_files) == 1
        assert archived_files[0].read_bytes() == b"frame1"
        # Archived under t1's HST date folder, not t2's.
        assert "09-24-2026" in str(archived_files[0])
