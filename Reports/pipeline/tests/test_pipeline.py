# ==============================================================================
# FILE: Reports/pipeline/tests/test_pipeline.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Window, identity, empty generation, failed audio, and restart recovery."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
import unittest  # info: import unittest
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parents[1]  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert

import generate  # noqa: E402
import model  # noqa: E402
import store  # noqa: E402
import windows  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST


# ====================================================
# SECTION: class PipelineTests
# What it does: Check the report contract without rendering audio or calling a model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class PipelineTests(unittest.TestCase):  # info: class PipelineTests
    def setUp(self):  # info: def setUp
        self.tmp = tempfile.TemporaryDirectory()  # info: set tmp
        root = Path(self.tmp.name)  # info: set root
        os.environ["RR_CANONICAL_DIR"] = str(root / "canonical")  # info: set RR_CANONICAL_DIR
        os.environ["RR_REPORT_LOG"] = str(root / "pipeline.jsonl")  # info: set RR_REPORT_LOG
        store.CANON = root / "canonical"  # info: set store . CANON
        store.LOG = root / "pipeline.jsonl"  # info: set store . LOG

    def tearDown(self):  # info: def tearDown
        self.tmp.cleanup()  # info: call cleanup

    def test_five_minute_window(self):  # info: def test_five_minute_window
        clock = datetime(2026, 9, 1, 14, 27, 40, tzinfo=HST)  # info: set clock
        window = windows.window_for(clock, "5m")  # info: set window
        self.assertEqual(window["window_start"], "2026-09-01T14:25:00-10:00")  # info: assert start
        self.assertEqual(window["window_end"], "2026-09-01T14:30:00-10:00")  # info: assert end
        self.assertEqual(window["timezone"], "Pacific/Honolulu")  # info: assert timezone

    def test_same_id_twice(self):  # info: def test_same_id_twice
        profile = {"id": "news-5m", "slug": "news_5m", "topic": "news", "scope": "hawaii", "cadence": "5m", "generator": "news_select", "owns": ["news"], "assets": {}}  # info: set profile
        clock = datetime(2026, 9, 1, 14, 25, tzinfo=HST)  # info: set clock
        window = windows.window_for(clock, "5m")  # info: set window
        first = model.new_report(profile, window, "2026-09-01T14:25:00-10:00")  # info: set first
        second = model.new_report(profile, window, "2026-09-01T14:26:00-10:00")  # info: set second
        self.assertEqual(first["report_id"], second["report_id"])  # info: assert same id
        store.save(first)  # info: call save
        store.save(second)  # info: call save
        loaded = store.load(first["report_id"])  # info: set loaded
        self.assertEqual(loaded["created_at"], first["created_at"])  # info: assert created_at kept
        self.assertEqual(len(list(store.CANON.glob("rpt_*.json"))), 1)  # info: assert one file

    def test_empty_window(self):  # info: def test_empty_window
        made = generate.deterministic({"window": {"window_start": "2026-09-01T14:25:00-10:00", "window_end": "2026-09-01T14:30:00-10:00"}, "observations": []})  # info: set made
        self.assertIn("Nothing in this window", made["spoken"][0])  # info: assert empty line
        self.assertEqual(made["provider"], "deterministic")  # info: assert provider

    def test_failed_audio_keeps_text(self):  # info: def test_failed_audio_keeps_text
        profile = store.profile_for("nws_weather")  # info: set profile
        window = windows.window_for(datetime(2026, 10, 2, 14, 45, tzinfo=HST), "hourly")  # info: set window
        report = model.new_report(profile, window, "2026-10-02T14:45:00-10:00")  # info: set report
        store.apply_voice(report, "# Weather\n\n- Fair.", ["Fair."], {"ok": False, "rc": 75, "detail": "busy"}, "/tmp/nws_weather_current.md")  # info: call apply_voice
        self.assertEqual(report["stages"]["text"]["status"], "ready")  # info: assert text ready
        self.assertEqual(report["stages"]["audio"]["status"], "failed")  # info: assert audio failed
        self.assertEqual(report["status"], "generated")  # info: assert status generated
        failed = store.mark_publication(report["report_id"], "failed", "youtube down") if False else None  # info: set failed
        store.save(report)  # info: call save
        marked = store.mark_publication(report["report_id"], "failed", "youtube down")  # info: set marked
        self.assertEqual(marked["status"], "generated")  # info: assert report remains
        self.assertEqual(marked["stages"]["text"]["status"], "ready")  # info: assert text remains
        self.assertEqual(marked["publication"]["status"], "failed")  # info: assert publication failed
        self.assertIsNone(failed)  # info: assert unused

    def test_recover_current_window(self):  # info: def test_recover_current_window
        profile = {"id": "news-5m", "slug": "news_5m", "topic": "news", "scope": "hawaii", "cadence": "5m", "generator": "deterministic", "owns": [], "assets": {}}  # info: set profile
        clock = datetime(2026, 9, 1, 14, 27, tzinfo=HST)  # info: set clock
        context = {"window": windows.window_for(clock, "5m"), "observations": [], "sources": []}  # info: set context
        store.record_generated(profile, context, generate.deterministic(context), "2026-09-01T14:25:00-10:00")  # info: call record_generated
        state = store.recover(clock)  # info: set state
        self.assertEqual(len(state["current"]), 1)  # info: assert current
        self.assertEqual(state["current"][0]["window_start"], "2026-09-01T14:25:00-10:00")  # info: assert window

    def test_legacy_index_keeps_files(self):  # info: def test_legacy_index_keeps_files
        voice = Path(self.tmp.name) / "Voice"  # info: set voice
        archive = voice / "Archive"  # info: set archive
        archive.mkdir(parents=True)  # info: archive . mkdir
        (voice / "nws_weather_current.md").write_text("# Weather\n", encoding="utf-8")  # info: write current
        (archive / "nws_weather_20260901T1425.md").write_text("# Old\n", encoding="utf-8")  # info: write archive
        counts = store.index_legacy(voice, None)  # info: set counts
        self.assertEqual(counts["md_before"], counts["md_after"])  # info: assert md count
        self.assertEqual(counts["indexed"], 2)  # info: assert indexed
        again = store.index_legacy(voice, None)  # info: set again
        self.assertEqual(again["indexed"], 0)  # info: assert no second copy
        self.assertTrue((voice / "nws_weather_current.md").is_file())  # info: assert file remains
        legacy = store.list_reports()  # info: set legacy
        self.assertTrue(all(row["window_start"] == "" for row in legacy))  # info: assert null window

    def test_retry_cap(self):  # info: def test_retry_cap
        stage = {"retry": 0}  # info: set stage
        for _ in range(5):  # info: for _ in range ( 5 )
            generate.note_retry(stage)  # info: call note_retry
        self.assertEqual(stage["retry"], 3)  # info: assert cap


if __name__ == "__main__":  # info: if __name__ == "__main__"
    unittest.main()  # info: call unittest . main
