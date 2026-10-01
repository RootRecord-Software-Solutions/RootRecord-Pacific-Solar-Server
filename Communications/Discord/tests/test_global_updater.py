# ==============================================================================
# FILE: Communications/Discord/tests/test_global_updater.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Offline tests for the Root Record Global Updater. No Discord HTTP and no inference."""  # info: module docstring
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import tempfile  # info: import tempfile
import unittest  # info: import unittest
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from unittest.mock import patch  # info: from unittest . mock import patch
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

DISCORD = Path(__file__).resolve().parents[1]  # info: set DISCORD
PACIFIC = DISCORD.parents[1]  # info: set PACIFIC
ECOSYSTEM = PACIFIC.parents[1]  # info: set ECOSYSTEM
LIBRARY = ECOSYSTEM / "5 - RootRecord-Library" / "Agent Context" / "Global-Updater-Agent-Context"  # info: set LIBRARY
sys.path.insert(0, str(DISCORD))  # info: sys . path . insert
sys.path.insert(0, str(DISCORD / "scripts"))  # info: sys . path . insert
import global_updater  # noqa: E402
from lib.envload import ALLOW  # noqa: E402
from lib.observations import load_host, render_observation  # noqa: E402
from lib.updater import canonical_intro, enforce, notes_for, system_text  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
SCOPE = {  # info: set SCOPE
    "guild_ids": ["9001"],  # info: guild
    "mention_names": ["Root Record Global Updater", "Global Updater"],  # info: names
    "application_name": "Root Record Global Updater",  # info: application_name
    "application_id": "150028956034740566",  # info: application_id
    "voice": "global-updater",  # info: voice
}  # info: }
NOW = datetime(2026, 9, 30, 21, 0, tzinfo=HST)  # info: set NOW


# ====================================================
# SECTION: function host_file
# What it does: Write one host-last.json sample for a test.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_file(folder: Path, at: str, memory: float = 48.86) -> Path:  # info: def host_file
    path = folder / "host-last.json"  # info: set path
    payload = {  # info: set payload
        "at": at,  # info: at
        "fields": {  # info: fields
            "cpu_percent": {"value": 22.58, "state": "measured", "unit": "%"},  # info: cpu
            "mem_used_percent": {"value": memory, "state": "measured", "unit": "%"},  # info: memory
            "load1": {"value": 2.43, "state": "measured", "unit": "load"},  # info: load
        },  # info: }
    }  # info: }
    path.write_text(json.dumps(payload), encoding="utf-8")  # info: path . write_text
    return path  # info: return path


# ====================================================
# SECTION: function message
# What it does: Build one non-bot guild message.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def message(text: str, mid: str = "m1", guild: str = "9001") -> dict:  # info: def message
    return {"id": mid, "content": text, "author": {"bot": False}, "guild_id": guild}  # info: return dict


# ====================================================
# SECTION: class GlobalUpdaterTests
# What it does: Prove identity, honesty, and Discord isolation without calling Discord or the model.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class GlobalUpdaterTests(unittest.TestCase):  # info: class GlobalUpdaterTests
    def test_identity_pack_is_global_updater(self):  # info: def test_identity_pack_is_global_updater
        text = system_text()  # info: set text
        self.assertIn("I'm the Root Record Global Updater.", text)  # info: self . assertIn
        self.assertIn("not Ava, Bruce, or Carly", text)  # info: self . assertIn
        self.assertIn("data", text)  # info: self . assertIn
        self.assertIn("observations", text)  # info: self . assertIn
        self.assertIn("operational information", text)  # info: self . assertIn
        self.assertIn("help desk", text)  # info: self . assertIn
        self.assertNotIn("gamer girl", text.lower())  # info: self . assertNotIn
        self.assertFalse((DISCORD / "personas").exists())  # info: self . assertFalse
        self.assertFalse((DISCORD / "global-updater" / "prompt.md").exists())  # info: self . assertFalse

    def test_who_are_you_is_not_ava_bruce_or_carly(self):  # info: def test_who_are_you_is_not_ava_bruce_or_carly
        intro = canonical_intro()  # info: set intro
        self.assertTrue(intro.startswith("I'm the Root Record Global Updater."))  # info: self . assertTrue
        for claimed in ("I'm Ava Ivy.", "I'm Bruce.", "I'm Carly Mal.", "Heyyy! Ava here! The server is doing great!"):  # info: for claimed in
            public = enforce(claimed, load_host(Path("/no/host")), notes_for("Who are you?"), "Who are you?")  # info: set public
            self.assertEqual(public, intro)  # info: self . assertEqual
            self.assertNotIn("Ava Ivy", public)  # info: self . assertNotIn
            self.assertNotRegex(public, r"\bI'm Bruce\b")  # info: self . assertNotRegex
            self.assertNotRegex(public, r"\bI'm Carly\b")  # info: self . assertNotRegex

    def test_purpose_notes_list_the_job(self):  # info: def test_purpose_notes_list_the_job
        notes = notes_for("What do you do?")  # info: set notes
        self.assertIn("data", notes)  # info: self . assertIn
        self.assertIn("observations", notes)  # info: self . assertIn
        self.assertIn("operational information", notes)  # info: self . assertIn
        self.assertIn("help desk", notes)  # info: self . assertIn
        role = (LIBRARY / "ROLE-AND-BOUNDS.md").read_text(encoding="utf-8")  # info: set role
        self.assertIn(notes, role)  # info: self . assertIn

    def test_no_measurement_is_not_invented(self):  # info: def test_no_measurement_is_not_invented
        missing = load_host(Path("/no/such/host-last.json"))  # info: set missing
        self.assertEqual(missing.status, "unavailable")  # info: self . assertEqual
        self.assertIsNone(missing.mem_used_percent)  # info: self . assertIsNone
        public = enforce(  # info: set public
            "The server is currently using 42% memory.",  # info: reply
            missing,  # info: missing
            "",  # info: notes
            "What is the current memory?",  # info: question
        )  # info: )
        self.assertNotIn("42", public)  # info: self . assertNotIn
        self.assertIn("I don't currently have a fresh memory measurement.", public)  # info: self . assertIn

    def test_stale_sample_is_labeled(self):  # info: def test_stale_sample_is_labeled
        with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile
            path = host_file(Path(tmp), "2026-09-30T18:00:00-10:00")  # info: set path
            obs = load_host(path, now=NOW)  # info: set obs
        self.assertEqual(obs.status, "stale")  # info: self . assertEqual
        public = enforce("Memory is 48.86%.", obs, "", "What is the current memory?")  # info: set public
        self.assertIn("stale", public.lower())  # info: self . assertIn
        self.assertIn(obs.at, public)  # info: self . assertIn
        self.assertNotIn("42", public)  # info: self . assertNotIn

    def test_wrong_fresh_number_is_replaced(self):  # info: def test_wrong_fresh_number_is_replaced
        with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile
            path = host_file(Path(tmp), "2026-09-30T20:55:00-10:00")  # info: set path
            obs = load_host(path, now=NOW)  # info: set obs
        self.assertEqual(obs.status, "fresh")  # info: self . assertEqual
        public = enforce("Memory is 42%.", obs, "", "What is the current memory?")  # info: set public
        self.assertIn("48.86", public)  # info: self . assertIn
        self.assertIn(obs.at, public)  # info: self . assertIn
        self.assertNotIn("42", public)  # info: self . assertNotIn

    def test_ancient_sample_hides_numbers(self):  # info: def test_ancient_sample_hides_numbers
        with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile
            path = host_file(Path(tmp), "2026-09-01T12:00:00-10:00")  # info: set path
            obs = load_host(path, now=NOW)  # info: set obs
        self.assertEqual(obs.status, "unavailable")  # info: self . assertEqual
        self.assertNotIn("48.86", render_observation(obs))  # info: self . assertNotIn

    def test_documentation_comes_from_the_library(self):  # info: def test_documentation_comes_from_the_library
        question = "What is the purpose of the Pacific server?"  # info: set question
        notes = notes_for(question)  # info: set notes
        infra = (LIBRARY / "CONTEXT" / "INFRASTRUCTURE.md").read_text(encoding="utf-8")  # info: set infra
        self.assertIn("Primary operational environment", notes)  # info: self . assertIn
        self.assertIn(notes, infra)  # info: self . assertIn
        public = enforce(  # info: set public
            "The Pacific server is the primary operational environment for the Hawaiʻi desk.",  # info: reply
            load_host(Path("/no/host")),  # info: obs
            notes,  # info: notes
            question,  # info: question
        )  # info: )
        self.assertIn("primary operational environment", public)  # info: self . assertIn
        where = notes_for("Where are the agent contexts?")  # info: set where
        self.assertIn("Global-Updater-Agent-Context", where)  # info: self . assertIn
        self.assertIn(where, (LIBRARY / "ROLE-AND-BOUNDS.md").read_text(encoding="utf-8"))  # info: self . assertIn

    def test_unknown_question_is_not_invented(self):  # info: def test_unknown_question_is_not_invented
        question = "What is the combination of the warehouse safe?"  # info: set question
        self.assertEqual(notes_for(question), "")  # info: self . assertEqual
        invented = enforce("The combination is 1234.", load_host(Path("/no/host")), "", question)  # info: set invented
        self.assertEqual(invented, "I can't establish that from the information available to me.")  # info: self . assertEqual
        self.assertNotIn("1234", invented)  # info: self . assertNotIn
        honest = "I can't establish that from the information available to me."  # info: set honest
        self.assertEqual(enforce(honest, load_host(Path("/no/host")), "", question), honest)  # info: self . assertEqual

    def test_service_running_is_not_assumed(self):  # info: def test_service_running_is_not_assumed
        public = enforce(  # info: set public
            "The service is currently running.",  # info: reply
            load_host(Path("/no/host")),  # info: obs
            notes_for("What is the current status of the Pacific server?"),  # info: notes
            "What is the current status of the Pacific server?",  # info: question
        )  # info: )
        self.assertIn("I don't currently have a service-status observation.", public)  # info: self . assertIn
        self.assertNotIn("running", public)  # info: self . assertNotIn

    def test_mentions_stay_inside_the_allowed_guild(self):  # info: def test_mentions_stay_inside_the_allowed_guild
        named = message("Global Updater, what is the current status?")  # info: set named
        self.assertTrue(global_updater.invokes(named, SCOPE))  # info: self . assertTrue
        self.assertTrue(global_updater.invokes(message("@Root Record Global Updater Who are you?"), SCOPE))  # info: self . assertTrue
        mentioned = message("status?", guild="9001")  # info: set mentioned
        mentioned["mentions"] = [{"id": "42", "username": "Root Record Global Updater"}]  # info: set mentions
        self.assertTrue(global_updater.invokes(mentioned, SCOPE))  # info: self . assertTrue
        self.assertFalse(global_updater.invokes(message("Ava, hello"), SCOPE))  # info: self . assertFalse
        self.assertFalse(global_updater.invokes(message("availability looks fine"), SCOPE))  # info: self . assertFalse
        bot = message("Global Updater, hello")  # info: set bot
        bot["author"] = {"bot": True}  # info: set author
        self.assertFalse(global_updater.invokes(bot, SCOPE))  # info: self . assertFalse
        self.assertFalse(global_updater.invokes(named, {**SCOPE, "guild_ids": []}))  # info: self . assertFalse
        self.assertFalse(global_updater.invokes(message("Global Updater", guild="minecraft"), SCOPE))  # info: self . assertFalse
        app_mention = message("<@150028956034740566> status?")  # info: set app_mention
        app_mention["mentions"] = [{"id": "150028956034740566", "username": "SomeBot"}]  # info: set mentions
        self.assertFalse(global_updater.invokes(app_mention, SCOPE))  # info: self . assertFalse

    def test_empty_guild_file_answers_nothing(self):  # info: def test_empty_guild_file_answers_nothing
        scope = global_updater.load_scope()  # info: set scope
        self.assertEqual(scope["guild_ids"], [])  # info: self . assertEqual
        self.assertEqual(scope["application_name"], "Root Record Global Updater")  # info: self . assertEqual
        self.assertEqual(scope["voice"], "global-updater")  # info: self . assertEqual
        self.assertFalse(global_updater.invokes(message("Global Updater, hello"), scope))  # info: self . assertFalse

    def test_one_voice_not_the_council(self):  # info: def test_one_voice_not_the_council
        calls = []  # info: set calls

        def infer(voice, prompt):  # info: def infer
            calls.append((voice, prompt))  # info: calls . append
            return "The Pacific server is the primary operational environment for the Hawaiʻi desk."  # info: return

        with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile
            outcome = global_updater.apply(  # info: set outcome
                "channel-1",  # info: channel
                [message("Global Updater, what is the purpose of the Pacific server?")],  # info: messages
                enabled=True,  # info: enabled
                post=lambda channel, content: {"id": "sent"},  # info: post
                log=lambda line: None,  # info: log
                infer=infer,  # info: infer
                seen_path=Path(tmp) / "updater-seen.json",  # info: seen
                scope=SCOPE,  # info: scope
                host_path=Path(tmp) / "missing.json",  # info: host
                now=NOW,  # info: now
            )  # info: )
        self.assertEqual([voice for voice, _ in calls], ["global-updater"])  # info: self . assertEqual
        self.assertNotIn("ava", [voice for voice, _ in calls])  # info: self . assertNotIn
        self.assertNotIn("bruce", [voice for voice, _ in calls])  # info: self . assertNotIn
        self.assertNotIn("carly", [voice for voice, _ in calls])  # info: self . assertNotIn
        self.assertIn("Primary operational environment", calls[0][1])  # info: self . assertIn
        self.assertIn("Do not claim to be Ava, Bruce, or Carly.", calls[0][1])  # info: self . assertIn
        self.assertIn("primary operational environment", outcome["public_texts"][0])  # info: self . assertIn
        self.assertNotIn("Ava", outcome["public_texts"][0])  # info: self . assertNotIn

    def test_flag_off_does_not_infer(self):  # info: def test_flag_off_does_not_infer
        os.environ.pop(global_updater.FLAG, None)  # info: os . environ . pop
        self.assertFalse(global_updater.enabled())  # info: self . assertFalse
        calls = []  # info: set calls
        outcome = global_updater.apply(  # info: set outcome
            "channel-1",  # info: channel
            [message("Global Updater, who are you?")],  # info: messages
            enabled=False,  # info: enabled
            post=lambda channel, content: {"id": "sent"},  # info: post
            infer=lambda voice, prompt: calls.append(voice),  # info: infer
            scope=SCOPE,  # info: scope
        )  # info: )
        self.assertEqual(calls, [])  # info: self . assertEqual
        self.assertEqual(outcome["handled"], 0)  # info: self . assertEqual

    def test_seen_file_stores_ids_only(self):  # info: def test_seen_file_stores_ids_only
        def infer(voice, prompt):  # info: def infer
            return "I provide factual data, observations, operational information, and help-desk assistance."  # info: return

        with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile
            path = Path(tmp) / "updater-seen.json"  # info: set path
            logs = []  # info: set logs
            global_updater.apply(  # info: call apply
                "channel-1",  # info: channel
                [message("Global Updater, what do you do?", "m9")],  # info: messages
                enabled=True,  # info: enabled
                post=lambda channel, content: None,  # info: post
                log=logs.append,  # info: log
                infer=infer,  # info: infer
                seen_path=path,  # info: seen
                scope=SCOPE,  # info: scope
                host_path=Path(tmp) / "missing.json",  # info: host
            )  # info: )
            raw = path.read_text(encoding="utf-8")  # info: set raw
            self.assertIn("m9", raw)  # info: self . assertIn
            self.assertNotIn("help-desk", raw)  # info: self . assertNotIn
            self.assertTrue(any(line == "agent selected global-updater" for line in logs))  # info: self . assertTrue
            self.assertFalse(any("what do you do" in line for line in logs))  # info: self . assertFalse
            again = []  # info: set again
            global_updater.apply(  # info: call apply
                "channel-1",  # info: channel
                [message("Global Updater, what do you do?", "m9")],  # info: messages
                enabled=True,  # info: enabled
                post=lambda channel, content: {"id": "x"},  # info: post
                infer=lambda voice, prompt: again.append(voice),  # info: infer
                seen_path=path,  # info: seen
                scope=SCOPE,  # info: scope
            )  # info: )
        self.assertEqual(again, [])  # info: self . assertEqual

    def test_default_infer_uses_run_infer_and_library_persona(self):  # info: def test_default_infer_uses_run_infer_and_library_persona
        self.assertTrue(global_updater.RUN_INFER.is_file())  # info: self . assertTrue
        with patch.dict(os.environ, {"DESK_LIVE_FILE": "/tmp/desk-live.txt", "FLM_MODEL": "llama3.2:1b"}, clear=False):  # info: with patch . dict
            with patch("global_updater.system_text", return_value="CANONICAL-PERSONA"):  # info: with patch
                with patch("global_updater.subprocess.run") as run:  # info: with patch subprocess
                    run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="hello\n", stderr="")  # info: set return
                    out = global_updater.default_infer("global-updater", "Who are you?")  # info: set out
        self.assertEqual(out, "hello")  # info: self . assertEqual
        argv = run.call_args.args[0]  # info: set argv
        self.assertTrue(argv[0].endswith("run-infer.sh"))  # info: self . assertTrue
        self.assertEqual(argv[1], "global-updater")  # info: self . assertEqual
        env = run.call_args.kwargs["env"]  # info: set env
        self.assertEqual(env["RR_PERSONA_SYSTEM"], "CANONICAL-PERSONA")  # info: self . assertEqual
        self.assertEqual(env["RR_NPU_ONLY"], "1")  # info: self . assertEqual
        self.assertEqual(env["FLM_MODEL"], "llama3.2:3b")  # info: self . assertEqual
        self.assertEqual(env["RR_CALLER"], "discord-global-updater")  # info: self . assertEqual
        self.assertNotIn("DESK_LIVE_FILE", env)  # info: self . assertNotIn
        with self.assertRaises(RuntimeError):  # info: with self . assertRaises
            global_updater.default_infer("ava", "hello")  # info: call default_infer

    def test_token_boundary_and_ava_files(self):  # info: def test_token_boundary_and_ava_files
        self.assertEqual(ALLOW, frozenset({"DISCORD_BOT_TOKEN"}))  # info: self . assertEqual
        self.assertNotIn("AVA_DISCORD_BOT_TOKEN", ALLOW)  # info: self . assertNotIn
        script = (DISCORD / "scripts" / "global_updater.py").read_text(encoding="utf-8")  # info: set script
        self.assertNotIn("run_pipeline", script)  # info: self . assertNotIn
        self.assertNotIn("AVA_DISCORD_BOT_TOKEN", script)  # info: self . assertNotIn
        review = (DISCORD / "scripts" / "review.py").read_text(encoding="utf-8")  # info: set review
        self.assertIn("def invokes_ava", review)  # info: self . assertIn
        self.assertIn("RR_DISCORD_REVIEW_PIPELINE", review)  # info: self . assertIn
        ava = (LIBRARY.parent / "Ava-Agent-Context" / "IDENTITY.md").read_text(encoding="utf-8")  # info: set ava
        self.assertIn("Ava Ivy", ava)  # info: self . assertIn
        self.assertNotIn("Root Record Global Updater", ava)  # info: self . assertNotIn
        voices = (PACIFIC / "Communications" / "telegram" / "config" / "voices.conf").read_text(encoding="utf-8")  # info: set voices
        self.assertNotIn("global-updater", voices)  # info: self . assertNotIn
        relay = (PACIFIC / "Communications" / "telegram" / "scripts" / "council-relay.py").read_text(encoding="utf-8")  # info: set relay
        self.assertIn('PIPELINE_ORDER = ("ava", "bruce", "carly", "ava")', relay)  # info: self . assertIn
        poll = (DISCORD / "scripts" / "poll.py").read_text(encoding="utf-8")  # info: set poll
        self.assertIn("RR_GLOBAL_UPDATER", poll)  # info: self . assertIn
        self.assertIn("RR_DISCORD_REVIEW_PIPELINE", poll)  # info: self . assertIn


if __name__ == "__main__":  # info: if __name__
    raise SystemExit(unittest.main())  # info: raise SystemExit
