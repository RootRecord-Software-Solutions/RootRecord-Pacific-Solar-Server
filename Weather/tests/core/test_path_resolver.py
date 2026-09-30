# ==============================================================================
# FILE: Weather/tests/core/test_path_resolver.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/path_resolver.py against the plan's own worked
examples (nws_plan.md Section 1)."""
from __future__ import annotations  # info: from __future__ import annotations

from datetime import datetime, timezone  # info: from datetime import datetime , timezone

from core.path_resolver import resolve  # info: from core . path_resolver import resolve


# ====================================================
# SECTION: function test_satellite_gif_url
# What it does: test satellite gif url.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_satellite_gif_url():  # info: def test_satellite_gif_url
    r = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")  # info: set r
    assert r.host == "weather.gov"  # info: assert r . host == "weather.gov"
    assert r.resource_dir == "images/hfo/satellite/Hawaii_IR"  # info: assert r . resource_dir == "images/hfo/satellite/Hawaii_IR"
    assert r.name == "Hawaii_IR"  # info: assert r . name == "Hawaii_IR"
    assert r.ext == "gif"  # info: assert r . ext == "gif"
    assert r.current_path("hfo") == "hfo/weather.gov/images/hfo/satellite/Hawaii_IR/Hawaii_IR_current.gif"  # info: assert r . current_path ( "hfo" ) ==


# ====================================================
# SECTION: function test_extensionless_path_defaults_to_txt
# What it does: test extensionless path defaults to txt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_extensionless_path_defaults_to_txt():  # info: def test_extensionless_path_defaults_to_txt
    r = resolve("https://www.weather.gov/hfo/SFP")  # info: set r
    assert r.name == "SFP"  # info: assert r . name == "SFP"
    assert r.ext == "txt"  # info: assert r . ext == "txt"
    assert r.current_path("hfo") == "hfo/weather.gov/hfo/SFP/SFP_current.txt"  # info: assert r . current_path ( "hfo" ) ==


# ====================================================
# SECTION: function test_query_string_disambiguated_resource
# What it does: test query string disambiguated resource.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_query_string_disambiguated_resource():  # info: def test_query_string_disambiguated_resource
    r = resolve("https://api.weather.gov/alerts/active?area=HI", resource_id_hint="area=HI")  # info: set r
    assert r.host == "api.weather.gov"  # info: assert r . host == "api.weather.gov"
    assert r.name == "area=HI"  # info: assert r . name == "area=HI"
    assert r.ext == "json"  # info: assert r . ext == "json"
    assert r.current_path("hfo") == "hfo/api.weather.gov/alerts/active/area=HI/area=HI_current.json"  # info: assert r . current_path ( "hfo" ) ==


# ====================================================
# SECTION: function test_archive_path_uses_hst_date_and_timestamp
# What it does: test archive path uses hst date and timestamp.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_archive_path_uses_hst_date_and_timestamp():  # info: def test_archive_path_uses_hst_date_and_timestamp
    r = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")  # info: set r
    fetched_at = datetime(2026, 9, 24, 14, 32, 7, tzinfo=timezone.utc)  # 04:32:07 HST
    archive = r.archive_path("hfo", fetched_at)  # info: set archive
    assert archive == (  # info: assert archive == (
        "hfo/weather.gov/images/hfo/satellite/Hawaii_IR/archive/"  # info: "hfo/weather.gov/images/hfo/satellite/Hawaii_IR/archive/"
        "09-24-2026/Hawaii_IR_20260924T043207-1000.gif"  # info: "09-24-2026/Hawaii_IR_20260924T043207-1000.gif"
    )  # info: )
