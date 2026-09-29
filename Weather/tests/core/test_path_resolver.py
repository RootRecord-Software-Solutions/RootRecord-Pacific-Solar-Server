"""Smoke tests for core/path_resolver.py against the plan's own worked
examples (nws_plan.md Section 1)."""
from __future__ import annotations

from datetime import datetime, timezone

from core.path_resolver import resolve


def test_satellite_gif_url():
    r = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")
    assert r.host == "weather.gov"
    assert r.resource_dir == "images/hfo/satellite/Hawaii_IR"
    assert r.name == "Hawaii_IR"
    assert r.ext == "gif"
    assert r.current_path("hfo") == "hfo/weather.gov/images/hfo/satellite/Hawaii_IR/Hawaii_IR_current.gif"


def test_extensionless_path_defaults_to_txt():
    r = resolve("https://www.weather.gov/hfo/SFP")
    assert r.name == "SFP"
    assert r.ext == "txt"
    assert r.current_path("hfo") == "hfo/weather.gov/hfo/SFP/SFP_current.txt"


def test_query_string_disambiguated_resource():
    r = resolve("https://api.weather.gov/alerts/active?area=HI", resource_id_hint="area=HI")
    assert r.host == "api.weather.gov"
    assert r.name == "area=HI"
    assert r.ext == "json"
    assert r.current_path("hfo") == "hfo/api.weather.gov/alerts/active/area=HI/area=HI_current.json"


def test_archive_path_uses_hst_date_and_timestamp():
    r = resolve("https://www.weather.gov/images/hfo/satellite/Hawaii_IR.gif")
    fetched_at = datetime(2026, 9, 24, 14, 32, 7, tzinfo=timezone.utc)  # 04:32:07 HST
    archive = r.archive_path("hfo", fetched_at)
    assert archive == (
        "hfo/weather.gov/images/hfo/satellite/Hawaii_IR/archive/"
        "09-24-2026/Hawaii_IR_20260924T043207-1000.gif"
    )
