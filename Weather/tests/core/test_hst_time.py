"""Smoke tests for core/hst_time.py. No network, no disk."""
from __future__ import annotations

from datetime import datetime, timezone

from core import hst_time


def test_to_hst_is_ten_hours_behind_utc():
    utc = datetime(2026, 9, 25, 10, 0, 0, tzinfo=timezone.utc)
    hst = hst_time.to_hst(utc)
    assert hst.hour == 0
    assert hst.day == 25


def test_naive_datetime_assumed_utc():
    naive = datetime(2026, 9, 25, 10, 0, 0)
    hst = hst_time.to_hst(naive)
    assert hst.hour == 0


def test_date_folder_boundary_matches_hst_not_utc():
    # 11:50pm HST on the 24th = 9:50am UTC on the 25th -- must land in the
    # 24th's date folder, per nws_plan.md Section 2's explicit example.
    utc = datetime(2026, 9, 25, 9, 50, 0, tzinfo=timezone.utc)
    assert hst_time.hst_date_folder(utc) == "09-24-2026"

    # 12:10am HST on the 25th = 10:10am UTC on the 25th -- different folder.
    utc_after = datetime(2026, 9, 25, 10, 10, 0, tzinfo=timezone.utc)
    assert hst_time.hst_date_folder(utc_after) == "09-25-2026"


def test_archive_timestamp_format():
    utc = datetime(2026, 9, 24, 14, 32, 7, tzinfo=timezone.utc)  # -> 04:32:07 HST
    ts = hst_time.hst_archive_timestamp(utc)
    assert ts == "20260924T043207-1000"


def test_is_new_hst_day():
    before = datetime(2026, 9, 25, 9, 50, 0, tzinfo=timezone.utc)   # 09-24 HST
    after = datetime(2026, 9, 25, 10, 10, 0, tzinfo=timezone.utc)   # 09-25 HST
    assert hst_time.is_new_hst_day(before, after) is True
    assert hst_time.is_new_hst_day(before, before) is False
