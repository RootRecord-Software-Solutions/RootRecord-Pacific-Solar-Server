# ==============================================================================
# FILE: Communications/Discord/tests/test_public_report.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Offline tests for public persona reports and consolidations. No Discord HTTP."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
import tempfile  # info: import tempfile
import unittest  # info: import unittest
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

DISCORD = Path(__file__).resolve().parents[1]  # info: set DISCORD
sys.path.insert(0, str(DISCORD))  # info: sys . path . insert
from lib.public_report import HST, averages, consolidation, persona_name, public_message, samples  # noqa: E402


class PublicReportTests(unittest.TestCase):  # info: class
    def test_personas_match_the_voice_desks(self):  # info: def test_personas
        self.assertEqual(persona_name("nws_weather"), "Ava")  # info: assert ava
        self.assertEqual(persona_name("morning_report"), "Ava")  # info: assert morning
        self.assertEqual(persona_name("solar_desk"), "Bruce")  # info: assert bruce
        self.assertEqual(persona_name("system_perf"), "Bruce")  # info: assert system
        self.assertEqual(persona_name("earthquake_report"), "Carly")  # info: assert carly
        self.assertEqual(persona_name("security_desk"), "Carly")  # info: assert security
        self.assertEqual(persona_name("kilauea_report"), "Carly")  # info: assert kilauea

    def test_public_text_is_spoken_and_links_the_live_page(self):  # info: def test_public
        md = "# Solar desk\n\n- Delta 2: state of charge 64%, AC out 92 W\n\n_Source: Database Energy/soc._\n"  # info: set md
        text = public_message("solar_desk", "solar-desk", md, "Delta 2 battery 64 percent.")  # info: set text
        self.assertTrue(text.startswith("Energy and solar\n"))  # info: assert header
        self.assertIn("Delta 2: state of charge 64%, AC out 92 W", text)  # info: assert measured
        self.assertNotIn("Bruce", text)  # info: assert no persona
        self.assertNotIn("64 percent", text)  # info: assert no transcript
        self.assertIn("https://www.rootrecord.cloud/reports/solar-desk", text)  # info: assert link
        self.assertNotIn("Database", text)  # info: assert no source path

    def test_average_needs_two_readings(self):  # info: def test_average
        one = "| Delta 2 | 64% | 0 W | 90 W | 0 W | at | 1 min |"  # info: set one
        self.assertEqual(averages([one]), [])  # info: assert no average
        two = "| Delta 2 | 70% | 10 W | 80 W | 0 W | at | 1 min |"  # info: set two
        lines = averages([one, two])  # info: set lines
        self.assertIn("Delta 2: average charge 67%, average solar 5 W, average AC out 85 W.", lines)  # info: assert mean

    def test_empty_window_does_not_invent_numbers(self):  # info: def test_empty
        start = datetime(2026, 9, 30, 8, 0, tzinfo=HST)  # info: set start
        end = datetime(2026, 9, 30, 16, 0, tzinfo=HST)  # info: set end
        text = consolidation("hurricane_desk", "hurricane-desk", [], 8, start, end)  # info: set text
        self.assertIn("No reports on file", text)  # info: assert empty
        self.assertIn("Hurricane", text)  # info: assert title
        self.assertNotIn("Carly", text)  # info: assert no persona
        self.assertNotIn("%", text.split("https://", 1)[0])  # info: assert no percent

    def test_samples_stay_inside_the_window(self):  # info: def test_samples
        with tempfile.TemporaryDirectory() as tmp:  # info: with tmp
            root = Path(tmp)  # info: set root
            arch = root / "test-reports" / "Voice" / "Archive"  # info: set arch
            arch.mkdir(parents=True)  # info: mkdir
            (arch / "energy_report_20260930T1200.md").write_text("| Delta 2 | 50% | 1 W | 2 W | 0 W | at | 1 min |\n", encoding="utf-8")  # info: write in
            (arch / "energy_report_20260930T0700.md").write_text("| Delta 2 | 10% | 1 W | 2 W | 0 W | at | 1 min |\n", encoding="utf-8")  # info: write out
            start = datetime(2026, 9, 30, 8, 0, tzinfo=HST)  # info: set start
            end = datetime(2026, 9, 30, 16, 0, tzinfo=HST)  # info: set end
            rows = samples(root, "energy_report", start, end)  # info: set rows
            self.assertEqual(len(rows), 1)  # info: assert one

    def test_voice_reports_render_before_the_radio_snapshot(self):  # info: def test_schedule
        jobs = (DISCORD.parents[1] / "Automations" / "scripts" / "jobs.py").read_text(encoding="utf-8")  # info: set jobs
        for stamp in ("23:30", ":06", ":08", "16:55", "07:18", '"only_at_minutes": [15, 30, 45]'):  # info: for stamp
            self.assertNotIn(stamp, jobs)  # info: assert gone
        self.assertIn('"at_times": ["00:00", "08:00", "16:00"]', jobs)  # info: assert 8h
        self.assertIn('"id": "discord_report_24h"', jobs)  # info: assert noon job
        self.assertIn('"only_at_minutes": [12, 42]', jobs)  # info: assert voice lead
        self.assertIn('"only_at_minutes": [0, 30]', jobs)  # info: assert chime stays on the announcement
        self.assertIn('"at_times": ["09:02"]', jobs)  # info: assert morning inside window
        self.assertIn('"at_times": ["12:02"]', jobs)  # info: assert midday inside window
        self.assertIn('"at_times": ["21:02"]', jobs)  # info: assert late inside window


if __name__ == "__main__":  # info: if main
    unittest.main()  # info: run
