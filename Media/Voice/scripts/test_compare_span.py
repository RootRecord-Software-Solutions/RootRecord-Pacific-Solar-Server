#!/usr/bin/env python3
"""Percent change lines. A missing period is not spoken."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import compare_span

HST = ZoneInfo("Pacific/Honolulu")
NOW = datetime(2026, 10, 2, 12, 14, tzinfo=HST)


def row(key, value, when):
    return {"key": key, "value": float(value), "at": when}


def test_day_week_and_skip_month():
    rows = [
        row("system.cpu_pct", 10, NOW - timedelta(hours=24)),
        row("system.cpu_pct", 20, NOW - timedelta(days=7)),
    ]
    lines = compare_span.sentences("system.cpu_pct", 15, "CPU", NOW, rows=rows)
    assert lines == ["CPU up 50 percent from yesterday, down 25 percent from last week."]


def test_zero_baseline_is_omitted():
    rows = [row("bandwidth.day_total", 0, NOW - timedelta(hours=23))]
    assert compare_span.sentences("bandwidth.day_total", 40, "Last twenty four hour total", NOW, rows=rows) == []


def test_no_history_is_silent():
    assert compare_span.sentences("tasks.open", 3, "Open work orders", NOW, rows=[]) == []


def test_unchanged():
    rows = [row("nws.alerts", 4, NOW - timedelta(hours=25))]
    lines = compare_span.sentences("nws.alerts", 4, "Active alerts", NOW, rows=rows)
    assert lines == ["Active alerts unchanged from yesterday."]


if __name__ == "__main__":
    test_day_week_and_skip_month()
    test_zero_baseline_is_omitted()
    test_no_history_is_silent()
    test_unchanged()
    print("ok")
