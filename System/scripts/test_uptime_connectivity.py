#!/usr/bin/env python3
"""Connectivity samples start now. Old testing stamps are not an offline average."""
import json
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import uptime_log

HST = ZoneInfo("Pacific/Honolulu")


def _use(tmp: Path) -> None:
    uptime_log.DIR = tmp
    uptime_log.PATH = tmp / "uptime-events.jsonl"
    uptime_log.MARKER = tmp / "uptime-last.json"
    uptime_log.PRESENCE = tmp / "presence.json"
    uptime_log.OFFLINE_PATH = tmp / "offline-samples.jsonl"
    uptime_log.RETURN_PATH = tmp / "return-samples.jsonl"
    uptime_log.DAILY_PATH = tmp / "connectivity-daily.json"


def test_old_gap_is_not_a_sample():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        _use(tmp)
        uptime_log.MARKER.write_text(json.dumps({
            "last_tick_epoch": 1_700_000_000,
            "boot_id": "old",
            "origin_started_at": "2026-09-29T23:26:06+00:00",
        }), encoding="utf-8")
        uptime_log.tick()
        assert not uptime_log.OFFLINE_PATH.exists()
        row = uptime_log.connectivity()
        assert row["uptime_pct"] == 100
        assert row["avg_offline_s"] is None
        assert row["avg_return_hour"] is None
        said = uptime_log.sentences()
        assert said[0].startswith("Root server was last online at ")
        assert any(line.startswith("Uptime 100 percent") for line in said)
        assert not any("Average" in line for line in said)


def test_morning_return_updates_the_average():
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        _use(tmp)
        down = datetime(2026, 10, 2, 22, 0, tzinfo=HST)
        up = datetime(2026, 10, 3, 6, 30, tzinfo=HST)
        uptime_log._write_marker({"recording_since": "2026-10-02T10:00:00-10:00"})
        row = uptime_log.note_offline(down.timestamp(), up.timestamp())
        assert row["offline_s"] == 8 * 3600 + 30 * 60
        assert row["return_minute"] == 6 * 60 + 30
        daily = json.loads(uptime_log.DAILY_PATH.read_text(encoding="utf-8"))
        assert daily["offline_samples"] == 1
        assert daily["avg_return_hour"] == 6
        assert daily["avg_return_minute"] == 30
        said = " ".join(uptime_log.sentences(up))
        assert "Average offline time 8 hours 30 minutes." in said
        assert "Average expected return six thirty a.m." in said


if __name__ == "__main__":
    test_old_gap_is_not_a_sample()
    test_morning_return_updates_the_average()
    print("ok")
