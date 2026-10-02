#!/usr/bin/env python3
"""Measured voice-timing page. No model."""
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import voice_timing_report as v


class VoiceTimingTests(unittest.TestCase):
    def test_wall_time_is_run_to_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "automations_current.log"
            log.write_text(
                "\n".join([
                    "2026-10-01T21:00:00-10:00job:voice_nws_weather RUN  python3 voice_reports.py nws_weather",
                    "2026-10-01T21:00:30-10:00job:voice_nws_weather | {\"ok\": true}",
                    "2026-10-01T21:00:30-10:00job:voice_solar_desk RUN  python3 voice_reports.py solar_desk",
                    "2026-10-01T21:01:30-10:00job:voice_solar_desk | {\"ok\": true}",
                    "noise",
                ]),
                encoding="utf-8",
            )
            rows = v.durations(v.log_files(Path(tmp)))
        self.assertEqual(rows["voice_nws_weather"], [30.0])
        self.assertEqual(rows["voice_solar_desk"], [60.0])

    def test_page_uses_the_handoff_sections_and_no_model(self):
        rows = {
            job: [10.0, 30.0] for job in v.STACK
        }
        text = v.render(
            rows,
            datetime(2026, 10, 1, 23, 50, tzinfo=ZoneInfo("Pacific/Honolulu")),
            [Path("automations_current.log")],
            {"voice_current_report": "[12, 42]"},
        )
        for heading in (
            "### Confirmed facts",
            "### Pages updated",
            "### Evidence",
            "### Still open / unresolved",
            "### Explicitly historical (do not treat as current)",
            "### Next recommended action",
        ):
            self.assertIn(heading, text)
        self.assertIn("**Model:** none", text)
        self.assertIn("| `voice_current_report` | [12, 42] |", text)
        self.assertNotIn("llama", text.lower())

    def test_live_jobs_file_schedules_the_half_hour_set(self):
        if not v.JOBS.is_file():
            self.skipTest("jobs.py is not on this machine")
        sched = v.schedule(v.JOBS.read_text(encoding="utf-8"))
        self.assertEqual(sched.get("voice_current_report"), "[12, 42]")
        self.assertEqual(sched.get("voice_nws_weather"), "[12, 42]")


if __name__ == "__main__":
    unittest.main()
