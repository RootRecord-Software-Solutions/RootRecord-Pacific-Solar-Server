# ==============================================================================
# FILE: Weather/tests/hurricanes/test_storm_track_plot.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Fixture test for RAMMB track tables and the Hawaiʻi text plot. No network."""  # info: """Fixture test for RAMMB track tables and the Hawaiʻi text plot. No network."""
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
import tempfile  # info: import tempfile
from pathlib import Path  # info: from pathlib import Path

WEATHER = Path(__file__).resolve().parents[2]  # info: set WEATHER
if str(WEATHER) not in sys.path:  # info: if str ( WEATHER ) not in sys
    sys.path.insert(0, str(WEATHER))  # info: sys . path . insert ( 0 ,

from hurricanes.scripts import storm_plot, storm_track  # noqa: E402

# ====================================================
# SECTION: FIXTURE
# What it does: Set FIXTURE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
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


# ====================================================
# SECTION: function test_fixture_tables_and_plot
# What it does: test fixture tables and plot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_fixture_tables_and_plot():  # info: def test_fixture_tables_and_plot
    parsed = storm_track.parse_rammb_tracks(FIXTURE)  # info: set parsed
    assert parsed["forecast"], parsed  # info: assert parsed [ "forecast" ] , parsed
    assert parsed["history"], parsed  # info: assert parsed [ "history" ] , parsed
    storm = {  # info: set storm
        "id": "wp162026",  # info: "id" : "wp162026" ,
        "lat": 16.8,  # info: "lat" : 16.8 ,
        "lon": 148.2,  # info: "lon" : 148.2 ,
        "name": "Fixture",  # info: "name" : "Fixture" ,
        "label": "Typhoon Fixture",  # info: "label" : "Typhoon Fixture" ,
        "nearest_hawaii_nm": 3200,  # info: "nearest_hawaii_nm" : 3200 ,
        "knots": 60,  # info: "knots" : 60 ,
        "basin": "wp",  # info: "basin" : "wp" ,
        "basin_name": "West Pacific",  # info: "basin_name" : "West Pacific" ,
    }  # info: }
    storm_track.apply_rammb_page(storm, FIXTURE)  # info: storm_track . apply_rammb_page ( storm , FIXTURE )
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        root = Path(tmp)  # info: set root
        storm_track.TRACKS_PATH = root / "storm-tracks.json"  # info: storm_track . TRACKS_PATH = root / "storm-tracks.json"
        storm_track.attach_track(storm, persist=True)  # info: storm_track . attach_track ( storm , persist =
        assert storm_track.TRACKS_PATH.is_file()  # info: assert storm_track . TRACKS_PATH . is_file ( )
        storm_plot.BOARD_DIR = root  # info: storm_plot . BOARD_DIR = root
        written = storm_plot.write_plot({"storms": [storm]})  # info: set written
        text = written.read_text(encoding="utf-8")  # info: set text
    storm_plot.BOARD_DIR = None  # info: storm_plot . BOARD_DIR = None
    assert "History:" in text  # info: assert "History:" in text
    assert "16.5N 149.5E" in text  # info: assert "16.5N 149.5E" in text
    assert "16.8N 148.2E" in text  # info: assert "16.8N 148.2E" in text


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    test_fixture_tables_and_plot()  # info: call test_fixture_tables_and_plot
    print("PASS")  # info: call print
