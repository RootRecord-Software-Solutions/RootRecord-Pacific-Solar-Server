# ==============================================================================
# FILE: Weather/tests/core/test_hst_time.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/hst_time.py. No network, no disk."""  # info: """Smoke tests for core/hst_time.py. No network, no disk."""
from __future__ import annotations  # info: from __future__ import annotations

from datetime import datetime, timezone  # info: from datetime import datetime , timezone

from core import hst_time  # info: from core import hst_time


# ====================================================
# SECTION: function test_to_hst_is_ten_hours_behind_utc
# What it does: test to hst is ten hours behind utc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_to_hst_is_ten_hours_behind_utc():  # info: def test_to_hst_is_ten_hours_behind_utc
    utc = datetime(2026, 9, 25, 10, 0, 0, tzinfo=timezone.utc)  # info: set utc
    hst = hst_time.to_hst(utc)  # info: set hst
    assert hst.hour == 0  # info: assert hst . hour == 0
    assert hst.day == 25  # info: assert hst . day == 25


# ====================================================
# SECTION: function test_naive_datetime_assumed_utc
# What it does: test naive datetime assumed utc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_naive_datetime_assumed_utc():  # info: def test_naive_datetime_assumed_utc
    naive = datetime(2026, 9, 25, 10, 0, 0)  # info: set naive
    hst = hst_time.to_hst(naive)  # info: set hst
    assert hst.hour == 0  # info: assert hst . hour == 0


# ====================================================
# SECTION: function test_date_folder_boundary_matches_hst_not_utc
# What it does: test date folder boundary matches hst not utc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_date_folder_boundary_matches_hst_not_utc():  # info: def test_date_folder_boundary_matches_hst_not_utc
    # 11:50pm HST on the 24th = 9:50am UTC on the 25th -- must land in the
    # 24th's date folder, per nws_plan.md Section 2's explicit example.
    utc = datetime(2026, 9, 25, 9, 50, 0, tzinfo=timezone.utc)  # info: set utc
    assert hst_time.hst_date_folder(utc) == "09-24-2026"  # info: assert hst_time . hst_date_folder ( utc ) ==

    # 12:10am HST on the 25th = 10:10am UTC on the 25th -- different folder.
    utc_after = datetime(2026, 9, 25, 10, 10, 0, tzinfo=timezone.utc)  # info: set utc_after
    assert hst_time.hst_date_folder(utc_after) == "09-25-2026"  # info: assert hst_time . hst_date_folder ( utc_after ) ==


# ====================================================
# SECTION: function test_archive_timestamp_format
# What it does: test archive timestamp format.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_archive_timestamp_format():  # info: def test_archive_timestamp_format
    utc = datetime(2026, 9, 24, 14, 32, 7, tzinfo=timezone.utc)  # -> 04:32:07 HST
    ts = hst_time.hst_archive_timestamp(utc)  # info: set ts
    assert ts == "20260924T043207-1000"  # info: assert ts == "20260924T043207-1000"


# ====================================================
# SECTION: function test_is_new_hst_day
# What it does: test is new hst day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_is_new_hst_day():  # info: def test_is_new_hst_day
    before = datetime(2026, 9, 25, 9, 50, 0, tzinfo=timezone.utc)   # 09-24 HST
    after = datetime(2026, 9, 25, 10, 10, 0, tzinfo=timezone.utc)   # 09-25 HST
    assert hst_time.is_new_hst_day(before, after) is True  # info: assert hst_time . is_new_hst_day ( before , after
    assert hst_time.is_new_hst_day(before, before) is False  # info: assert hst_time . is_new_hst_day ( before , before
