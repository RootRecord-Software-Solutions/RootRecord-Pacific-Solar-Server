#!/usr/bin/env python3
"""Power-mode time is logged from the first sample. A change closes the previous segment."""
import json
import tempfile
from pathlib import Path

import power_profile


def _use(tmp: Path) -> None:
    power_profile.DIR = tmp
    power_profile.STATE = tmp / "mode-last.json"
    power_profile.SEGMENTS = tmp / "mode-segments.jsonl"
    power_profile.DAILY = tmp / "mode-use.json"


def test_time_accumulates_and_a_change_closes_the_segment():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        _use(tmp)
        first = power_profile.note(1_000.0, "performance")
        assert first["mode"] == "performance"
        assert first["seconds"]["performance"] == 0
        second = power_profile.note(1_120.0, "performance")
        assert second["seconds"]["performance"] == 120
        third = power_profile.note(1_180.0, "power-saver")
        assert third["mode"] == "energy saver"
        assert third["seconds"]["performance"] == 180
        assert third["today_seconds"]["energy saver"] == 0
        segment = json.loads(power_profile.SEGMENTS.read_text(encoding="utf-8"))
        assert segment["mode"] == "performance"
        assert segment["seconds"] == 180
        assert power_profile.sentence() == "Host power mode is energy saver."


def test_unknown_profile_is_skipped():
    with tempfile.TemporaryDirectory() as raw:
        _use(Path(raw))
        assert power_profile.note(1_000.0, "") == {}
        assert power_profile.sentence() == ""


if __name__ == "__main__":
    test_time_accumulates_and_a_change_closes_the_segment()
    test_unknown_profile_is_skipped()
    print("ok")
