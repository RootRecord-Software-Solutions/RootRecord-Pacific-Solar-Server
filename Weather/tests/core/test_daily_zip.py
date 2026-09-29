"""Smoke tests for core/daily_zip.py's discover -> zip -> verify -> delete
flow, per nws_plan.md Section 8."""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from core.daily_zip import consolidate_day


def _make_resource_archive(base: Path, resource_rel: str, date_folder: str, filename: str, content: bytes):
    d = base / resource_rel / "archive" / date_folder
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_bytes(content)


def test_nothing_to_zip_when_no_dated_folders():
    with tempfile.TemporaryDirectory() as tmp:
        result = consolidate_day(tmp, "09-24-2026")
        assert result.status == "nothing_to_do"


def test_consolidates_multiple_resources_and_removes_originals():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        _make_resource_archive(base, "weather.gov/images/hfo/satellite/Hawaii_IR", "09-24-2026",
                                "Hawaii_IR_20260924T040000-1000.gif", b"frame-a")
        _make_resource_archive(base, "api.weather.gov/alerts/active/area=HI", "09-24-2026",
                                "area=HI_20260924T050000-1000.json", b'{"a":1}')
        # A folder for a DIFFERENT date should NOT be swept up.
        _make_resource_archive(base, "weather.gov/images/hfo/satellite/Hawaii_IR", "09-25-2026",
                                "Hawaii_IR_20260925T040000-1000.gif", b"frame-b")

        result = consolidate_day(tmp, "09-24-2026")

        assert result.status == "consolidated"
        assert result.files_written == 2
        assert result.deleted_source_dirs == 2
        assert Path(result.zip_path).is_file()

        with zipfile.ZipFile(result.zip_path) as zf:
            names = set(zf.namelist())
        assert any(n.endswith("Hawaii_IR_20260924T040000-1000.gif") for n in names)
        assert any(n.endswith("area=HI_20260924T050000-1000.json") for n in names)

        # 09-24 folders gone, 09-25 folder untouched.
        assert not (base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive/09-24-2026").exists()
        assert (base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive/09-25-2026").is_dir()
        # Parent archive/ dirs stay in place (empty or with today's folder).
        assert (base / "weather.gov/images/hfo/satellite/Hawaii_IR/archive").is_dir()


def test_does_not_sweep_the_consolidated_archives_output_folder():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        _make_resource_archive(base, "weather.gov/x", "09-24-2026", "x_1.gif", b"a")
        first = consolidate_day(tmp, "09-24-2026")
        assert first.status == "consolidated"

        # Running again for the same date should find nothing left to zip
        # (and must not choke on scanning its own output folder).
        second = consolidate_day(tmp, "09-24-2026")
        assert second.status == "nothing_to_do"
