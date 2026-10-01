# ==============================================================================
# FILE: Communications/Discord/tests/test_report_relay.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Offline tests for the automated-report Discord relay. No Discord HTTP."""  # info: docstring
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sys  # info: import sys
import tempfile  # info: import tempfile
import unittest  # info: import unittest
from pathlib import Path  # info: from pathlib import Path

DISCORD = Path(__file__).resolve().parents[1]  # info: set DISCORD
sys.path.insert(0, str(DISCORD / "scripts"))  # info: sys . path . insert
import report_relay  # noqa: E402


class ReportRelayTests(unittest.TestCase):  # info: class ReportRelayTests
    def test_clip_drops_spoken_and_caps_length(self):  # info: def test_clip
        text = "# Energy\n\nDelta 2 64%.\n\n## Spoken\n\nEnergy desk at seven."  # info: set text
        self.assertEqual(report_relay.clip(text), "# Energy\n\nDelta 2 64%.")  # info: assert spoken dropped
        long = "A" * 4000  # info: set long
        clipped = report_relay.clip(long, limit=100)  # info: set clipped
        self.assertLessEqual(len(clipped), 100)  # info: assert cap
        self.assertTrue(clipped.endswith("… truncated."))  # info: assert marker

    def test_plan_skips_missing_and_unchanged(self):  # info: def test_plan
        with tempfile.TemporaryDirectory() as tmp:  # info: with tmp
            root = Path(tmp)  # info: set root
            path = root / "energy_report_current.md"  # info: set path
            path.write_text("# Energy\n\n64%\n", encoding="utf-8")  # info: write
            routes = [{"key": "energy_report", "channel_id": "1", "source": "energy_report_current.md"}, {"key": "hurricane_desk", "channel_id": "2", "source": "missing.md"}]  # info: set routes
            first = report_relay.plan(routes, {}, root)  # info: set first
            self.assertEqual([row["key"] for row in first], ["energy_report"])  # info: assert one
            again = report_relay.plan(routes, {"energy_report": first[0]["digest"]}, root)  # info: set again
            self.assertEqual(again, [])  # info: assert unchanged skipped

    def test_relay_remembers_only_accepted_posts(self):  # info: def test_relay
        with tempfile.TemporaryDirectory() as tmp:  # info: with tmp
            root = Path(tmp)  # info: set root
            ledger = root / "ledger.json"  # info: set ledger
            (root / "energy_report_current.md").write_text("# Energy\n\n64%\n", encoding="utf-8")  # info: write
            routes = [{"key": "energy_report", "channel_id": "155", "source": "energy_report_current.md"}]  # info: set routes
            calls = []  # info: set calls

            def hold(channel_id, body):  # info: def hold
                calls.append((channel_id, body))  # info: append
                return None  # info: return None

            report_relay.LEDGER = ledger  # info: point ledger
            held = report_relay.relay(routes, {}, root, post=hold)  # info: set held
            self.assertEqual(held, ["held energy_report"])  # info: assert held
            self.assertFalse(ledger.exists())  # info: assert no ledger
            posted = report_relay.relay(routes, {}, root, post=lambda cid, body: {"id": "9"})  # info: set posted
            self.assertEqual(posted, ["posted energy_report"])  # info: assert posted
            saved = json.loads(ledger.read_text(encoding="utf-8"))  # info: set saved
            self.assertIn("energy_report", saved["posted"])  # info: assert digest stored

    def test_configured_routes_cover_each_report_channel(self):  # info: def test_routes
        data = json.loads((DISCORD / "config" / "report-channels.json").read_text(encoding="utf-8"))  # info: set data
        names = [row["name"] for row in data["reports"]]  # info: set names
        ids = [row["channel_id"] for row in data["reports"]]  # info: set ids
        self.assertEqual(len(names), len(set(names)))  # info: assert unique names
        self.assertEqual(len(ids), len(set(ids)))  # info: assert unique ids
        self.assertIn("earthquake-report", names)  # info: assert earthquake
        self.assertIn("system-perf", names)  # info: assert system
        self.assertEqual(data["category_id"], "1555100597919944746")  # info: assert category
        self.assertEqual(report_relay.ECOSYSTEM.name, "RootRecord-Ecosystem")  # info: assert ecosystem root
        jobs = (DISCORD.parents[1] / "Automations" / "scripts" / "jobs.py").read_text(encoding="utf-8")  # info: set jobs
        self.assertIn('"id": "discord_report_relay"', jobs)  # info: assert job id
        self.assertIn('"RR_DISCORD_POST": "1"', jobs)  # info: assert job gate
        poller = jobs.split('"id": "discord_poller"', 1)[1][:400]  # info: set poller
        self.assertIn('"enabled": False', poller)  # info: assert chat poller stays off


if __name__ == "__main__":  # info: if __name__
    unittest.main()  # info: unittest . main
