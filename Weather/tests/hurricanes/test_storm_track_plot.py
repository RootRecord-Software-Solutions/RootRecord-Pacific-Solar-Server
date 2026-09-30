"""Fixture test for RAMMB track tables and the Hawaiʻi text plot. No network."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

WEATHER = Path(__file__).resolve().parents[2]
if str(WEATHER) not in sys.path:
    sys.path.insert(0, str(WEATHER))

from hurricanes.scripts import storm_plot, storm_track  # noqa: E402

FIXTURE = """
<html><body>
Forecast Hour Latitude Longitude Intensity
0 16.5 200.5 65
Forecast Track Archive
Track History Synoptic Time Latitude Longitude Intensity
2026-09-16 12:00 16.5 149.5 55
2026-09-16 18:00 16.8 148.2 60
About Track History
</body></html>
"""


def test_fixture_tables_and_plot():
    parsed = storm_track.parse_rammb_tracks(FIXTURE)
    assert parsed["forecast"], parsed
    assert parsed["history"], parsed
    storm = {
        "id": "wp162026",
        "lat": 16.8,
        "lon": 148.2,
        "name": "Fixture",
        "label": "Typhoon Fixture",
        "nearest_hawaii_nm": 3200,
        "knots": 60,
        "basin": "wp",
        "basin_name": "West Pacific",
    }
    storm_track.apply_rammb_page(storm, FIXTURE)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        storm_track.TRACKS_PATH = root / "storm-tracks.json"
        storm_track.attach_track(storm, persist=True)
        assert storm_track.TRACKS_PATH.is_file()
        storm_plot.BOARD_DIR = root
        written = storm_plot.write_plot({"storms": [storm]})
        text = written.read_text(encoding="utf-8")
    storm_plot.BOARD_DIR = None
    assert "History:" in text
    assert "16.5N 149.5E" in text
    assert "16.8N 148.2E" in text


if __name__ == "__main__":
    test_fixture_tables_and_plot()
    print("PASS")
