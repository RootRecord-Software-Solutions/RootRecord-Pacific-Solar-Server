# ==============================================================================
# FILE: Communications/Discord/tests/test_review.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Offline tests for the Discord Ava review pipeline. No Discord HTTP and no inference."""  # info: """Offline tests for the Discord Ava review pipeline. No Discord HTTP and no inference."""
from __future__ import annotations  # info: from __future__ import annotations

import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import tempfile  # info: import tempfile
import unittest  # info: import unittest
from pathlib import Path  # info: from pathlib import Path
from unittest.mock import patch  # info: from unittest . mock import patch

DISCORD = Path(__file__).resolve().parents[1]  # info: set DISCORD
sys.path.insert(0, str(DISCORD))  # info: sys . path . insert ( 0 , str ( DISCORD ) )
sys.path.insert(0, str(DISCORD / "scripts"))  # info: sys . path . insert ( 0 , str ( DISCORD / "scripts" ) )
import review  # noqa: E402
from lib.api import post_message  # noqa: E402

USER = "Ava, can you explain tides?"  # info: set USER
DRAFT = "Draft answer about tides."  # info: set DRAFT
BRUCE = "APPROVE\nOptional enhancement: name the unit."  # info: set BRUCE
CARLY = "APPROVE\nNo additional concerns."  # info: set CARLY
FINAL = "Tides are the rise and fall of the sea."  # info: set FINAL


# ====================================================
# SECTION: class ScriptedInfer
# What it does: Record voice order and return one scripted reply per hop.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class ScriptedInfer:  # info: class ScriptedInfer
    def __init__(self, bruce=BRUCE, carly=CARLY, final=FINAL, draft=DRAFT, fail=None):  # info: def __init__
        self.calls = []  # info: self . calls = [ ]
        self.bruce = bruce  # info: self . bruce = bruce
        self.carly = carly  # info: self . carly = carly
        self.final = final  # info: self . final = final
        self.draft = draft  # info: self . draft = draft
        self.fail = fail or set()  # info: self . fail = fail or set ( )

    def __call__(self, voice, prompt):  # info: def __call__
        self.calls.append((voice, prompt))  # info: self . calls . append ( ( voice , prompt ) )
        ava_n = sum(1 for item, _ in self.calls if item == "ava")  # info: set ava_n
        hop = "ava-draft" if voice == "ava" and ava_n == 1 else voice  # info: set hop
        if voice == "ava" and ava_n == 2:  # info: if voice == "ava" and ava_n == 2
            hop = "ava-final"  # info: set hop
        if hop in self.fail or voice in self.fail:  # info: if hop in self . fail or voice in self . fail
            raise TimeoutError(hop)  # info: raise TimeoutError ( hop )
        if hop == "ava-draft":  # info: if hop == "ava-draft"
            return self.draft  # info: return self . draft
        if voice == "bruce":  # info: if voice == "bruce"
            return self.bruce  # info: return self . bruce
        if voice == "carly":  # info: if voice == "carly"
            return self.carly  # info: return self . carly
        return self.final  # info: return self . final


# ====================================================
# SECTION: class ReviewPipelineTests
# What it does: Prove the Discord review contract without calling Discord or run-infer.sh.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class ReviewPipelineTests(unittest.TestCase):  # info: class ReviewPipelineTests
    def test_flag_defaults_off(self):  # info: def test_flag_defaults_off
        os.environ.pop(review.REVIEW_FLAG, None)  # info: os . environ . pop ( review . REVIEW_FLAG , None )
        self.assertFalse(review.pipeline_enabled())  # info: self . assertFalse ( review . pipeline_enabled ( ) )

    def test_chain_order_and_private_reviews(self):  # info: def test_chain_order_and_private_reviews
        infer = ScriptedInfer()  # info: set infer
        logs = []  # info: set logs
        result = review.run_pipeline(USER, "earlier: what is a tide", infer=infer, log=logs.append)  # info: set result
        voices = [voice for voice, _ in infer.calls]  # info: set voices
        self.assertEqual(voices, ["ava", "bruce", "carly", "ava"])  # info: self . assertEqual ( voices , [ "ava" , "bruce" , "carly" , "ava" ] )
        self.assertIn(USER, infer.calls[0][1])  # info: self . assertIn ( USER , infer . calls [ 0 ] [ 1 ] )
        self.assertIn(DRAFT, infer.calls[1][1])  # info: self . assertIn ( DRAFT , infer . calls [ 1 ] [ 1 ] )
        self.assertIn(USER, infer.calls[1][1])  # info: self . assertIn ( USER , infer . calls [ 1 ] [ 1 ] )
        self.assertIn(DRAFT, infer.calls[2][1])  # info: self . assertIn ( DRAFT , infer . calls [ 2 ] [ 1 ] )
        self.assertIn(BRUCE, infer.calls[2][1])  # info: self . assertIn ( BRUCE , infer . calls [ 2 ] [ 1 ] )
        self.assertIn(USER, infer.calls[3][1])  # info: self . assertIn ( USER , infer . calls [ 3 ] [ 1 ] )
        self.assertIn(DRAFT, infer.calls[3][1])  # info: self . assertIn ( DRAFT , infer . calls [ 3 ] [ 1 ] )
        self.assertIn(BRUCE, infer.calls[3][1])  # info: self . assertIn ( BRUCE , infer . calls [ 3 ] [ 1 ] )
        self.assertIn(CARLY, infer.calls[3][1])  # info: self . assertIn ( CARLY , infer . calls [ 3 ] [ 1 ] )
        self.assertEqual(result.public_text, FINAL)  # info: self . assertEqual ( result . public_text , FINAL )
        self.assertEqual(result.final_response, FINAL)  # info: self . assertEqual ( result . final_response , FINAL )
        self.assertNotIn("Optional enhancement", result.public_text)  # info: self . assertNotIn ( "Optional enhancement" , result . public_text )
        self.assertNotIn("No additional concerns", result.public_text)  # info: self . assertNotIn ( "No additional concerns" , result . public_text )
        self.assertEqual(result.bruce.status, "reviewed")  # info: self . assertEqual ( result . bruce . status , "reviewed" )
        self.assertEqual(result.bruce.decision, "APPROVE")  # info: self . assertEqual ( result . bruce . decision , "APPROVE" )
        self.assertEqual(result.carly.status, "reviewed")  # info: self . assertEqual ( result . carly . status , "reviewed" )
        self.assertEqual(result.carly.decision, "APPROVE")  # info: self . assertEqual ( result . carly . decision , "APPROVE" )
        joined = "\n".join(logs)  # info: set joined
        self.assertIn("request received", joined)  # info: self . assertIn ( "request received" , joined )
        self.assertIn("Ava draft completed", joined)  # info: self . assertIn ( "Ava draft completed" , joined )
        self.assertIn("Bruce review completed", joined)  # info: self . assertIn ( "Bruce review completed" , joined )
        self.assertIn("Carly review completed", joined)  # info: self . assertIn ( "Carly review completed" , joined )
        self.assertIn("Ava final completed", joined)  # info: self . assertIn ( "Ava final completed" , joined )
        self.assertNotIn(USER, joined)  # info: self . assertNotIn ( USER , joined )

    def test_transport_receives_only_ava_final(self):  # info: def test_transport_receives_only_ava_final
        infer = ScriptedInfer()  # info: set infer
        posted = []  # info: set posted
        with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
            outcome = review.respond(  # info: set outcome
                "channel-1",  # info: "channel-1"
                [{"id": "m1", "content": USER, "author": {"bot": False}}],  # info: [ { "id" : "m1" , "content" : USER , "author" : { "bot" : False } } ]
                post=lambda channel, content: posted.append((channel, content)) or {"id": "sent"},  # info: post = lambda channel , content : posted . append ( ( channel , content ) ) or { "id" : "sent" }
                log=lambda line: None,  # info: log = lambda line : None
                infer=infer,  # info: infer = infer
                seen_path=Path(tmp) / "seen.json",  # info: seen_path = Path ( tmp ) / "seen.json"
            )  # info: )
        self.assertEqual(posted, [("channel-1", FINAL)])  # info: self . assertEqual ( posted , [ ( "channel-1" , FINAL ) ] )
        self.assertEqual(outcome["public_texts"], [FINAL])  # info: self . assertEqual ( outcome [ "public_texts" ] , [ FINAL ] )
        self.assertNotIn(BRUCE, posted[0][1])  # info: self . assertNotIn ( BRUCE , posted [ 0 ] [ 1 ] )
        self.assertNotIn(CARLY, posted[0][1])  # info: self . assertNotIn ( CARLY , posted [ 0 ] [ 1 ] )
        self.assertEqual(outcome["posted"], 1)  # info: self . assertEqual ( outcome [ "posted" ] , 1 )

    def test_flag_off_does_not_call_pipeline(self):  # info: def test_flag_off_does_not_call_pipeline
        called = []  # info: set called
        outcome = review.apply_review(  # info: set outcome
            "channel-1",  # info: "channel-1"
            [{"id": "m1", "content": USER, "author": {}}],  # info: [ { "id" : "m1" , "content" : USER , "author" : { } } ]
            enabled=False,  # info: enabled = False
            respond_fn=lambda cid, msgs: called.append(cid),  # info: respond_fn = lambda cid , msgs : called . append ( cid )
        )  # info: )
        self.assertEqual(called, [])  # info: self . assertEqual ( called , [ ] )
        self.assertEqual(outcome["handled"], 0)  # info: self . assertEqual ( outcome [ "handled" ] , 0 )

    def test_only_ava_mentions_run(self):  # info: def test_only_ava_mentions_run
        self.assertTrue(review.invokes_ava({"content": "Ava, can you explain X?", "author": {}}))  # info: self . assertTrue ( review . invokes_ava ( { "content" : "Ava, can you explain X?" , "author" : { } } ) )
        self.assertTrue(review.invokes_ava({"content": "hello", "author": {}, "mentions": [{"username": "Ava"}]}))  # info: self . assertTrue ( review . invokes_ava ( { "content" : "hello" , "author" : { } , "mentions" : [ { "username" : "Ava" } ] } ) )
        self.assertFalse(review.invokes_ava({"content": "availability looks fine", "author": {}}))  # info: self . assertFalse ( review . invokes_ava ( { "content" : "availability looks fine" , "author" : { } } ) )
        self.assertFalse(review.invokes_ava({"content": "Bruce, check the host", "author": {}}))  # info: self . assertFalse ( review . invokes_ava ( { "content" : "Bruce, check the host" , "author" : { } } ) )
        self.assertFalse(review.invokes_ava({"content": "Ava, hello", "author": {"bot": True}}))  # info: self . assertFalse ( review . invokes_ava ( { "content" : "Ava, hello" , "author" : { "bot" : True } } ) )

    def test_bruce_unavailable_is_not_approve(self):  # info: def test_bruce_unavailable_is_not_approve
        infer = ScriptedInfer(fail={"bruce"})  # info: set infer
        logs = []  # info: set logs
        result = review.run_pipeline(USER, "", infer=infer, log=logs.append)  # info: set result
        self.assertEqual(result.bruce.status, "unavailable")  # info: self . assertEqual ( result . bruce . status , "unavailable" )
        self.assertEqual(result.bruce.decision, "UNAVAILABLE")  # info: self . assertEqual ( result . bruce . decision , "UNAVAILABLE" )
        self.assertNotEqual(result.bruce.decision, "APPROVE")  # info: self . assertNotEqual ( result . bruce . decision , "APPROVE" )
        self.assertEqual(result.carly.status, "reviewed")  # info: self . assertEqual ( result . carly . status , "reviewed" )
        self.assertIn("Bruce review status: unavailable", infer.calls[2][1])  # info: self . assertIn ( "Bruce review status: unavailable" , infer . calls [ 2 ] [ 1 ] )
        self.assertEqual(result.public_text, FINAL)  # info: self . assertEqual ( result . public_text , FINAL )
        self.assertIn("Bruce review unavailable", "\n".join(logs))  # info: self . assertIn ( "Bruce review unavailable" , "\n" . join ( logs ) )
        self.assertEqual(result.bruce.notes, "")  # info: self . assertEqual ( result . bruce . notes , "" )
        self.assertNotIn("unavailable", result.public_text)  # info: self . assertNotIn ( "unavailable" , result . public_text )

    def test_carly_unavailable_is_not_approve(self):  # info: def test_carly_unavailable_is_not_approve
        infer = ScriptedInfer(fail={"carly"})  # info: set infer
        result = review.run_pipeline(USER, "", infer=infer, log=lambda line: None)  # info: set result
        self.assertEqual(result.bruce.status, "reviewed")  # info: self . assertEqual ( result . bruce . status , "reviewed" )
        self.assertEqual(result.carly.status, "unavailable")  # info: self . assertEqual ( result . carly . status , "unavailable" )
        self.assertEqual(result.carly.decision, "UNAVAILABLE")  # info: self . assertEqual ( result . carly . decision , "UNAVAILABLE" )
        self.assertIn("Carly review status: unavailable", infer.calls[3][1])  # info: self . assertIn ( "Carly review status: unavailable" , infer . calls [ 3 ] [ 1 ] )
        self.assertEqual(result.public_text, FINAL)  # info: self . assertEqual ( result . public_text , FINAL )

    def test_ava_draft_failure_posts_nothing(self):  # info: def test_ava_draft_failure_posts_nothing
        infer = ScriptedInfer(fail={"ava-draft"})  # info: set infer
        result = review.run_pipeline(USER, "", infer=infer, log=lambda line: None)  # info: set result
        self.assertEqual(result.public_text, "")  # info: self . assertEqual ( result . public_text , "" )
        self.assertEqual([voice for voice, _ in infer.calls], ["ava"])  # info: self . assertEqual ( [ voice for voice , _ in infer . calls ] , [ "ava" ] )
        self.assertEqual(result.bruce.status, "unavailable")  # info: self . assertEqual ( result . bruce . status , "unavailable" )
        self.assertEqual(result.ava_final_status, "skipped")  # info: self . assertEqual ( result . ava_final_status , "skipped" )

    def test_ava_final_failure_uses_draft(self):  # info: def test_ava_final_failure_uses_draft
        infer = ScriptedInfer(fail={"ava-final"})  # info: set infer
        result = review.run_pipeline(USER, "", infer=infer, log=lambda line: None)  # info: set result
        self.assertEqual(result.ava_final_status, "unavailable")  # info: self . assertEqual ( result . ava_final_status , "unavailable" )
        self.assertEqual(result.public_text, DRAFT)  # info: self . assertEqual ( result . public_text , DRAFT )
        self.assertNotIn(BRUCE, result.public_text)  # info: self . assertNotIn ( BRUCE , result . public_text )
        self.assertNotIn(CARLY, result.public_text)  # info: self . assertNotIn ( CARLY , result . public_text )

    def test_review_shaped_final_is_not_posted(self):  # info: def test_review_shaped_final_is_not_posted
        infer = ScriptedInfer(final="APPROVE\nlooks fine")  # info: set infer
        result = review.run_pipeline(USER, "", infer=infer, log=lambda line: None)  # info: set result
        self.assertEqual(result.public_text, DRAFT)  # info: self . assertEqual ( result . public_text , DRAFT )

    def test_seen_file_stores_ids_only(self):  # info: def test_seen_file_stores_ids_only
        infer = ScriptedInfer()  # info: set infer
        with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
            path = Path(tmp) / "seen.json"  # info: set path
            review.respond(  # info: call review . respond
                "channel-1",  # info: "channel-1"
                [{"id": "m9", "content": USER, "author": {}}],  # info: [ { "id" : "m9" , "content" : USER , "author" : { } } ]
                post=lambda channel, content: None,  # info: post = lambda channel , content : None
                log=lambda line: None,  # info: log = lambda line : None
                infer=infer,  # info: infer = infer
                seen_path=path,  # info: seen_path = path
            )  # info: )
            raw = path.read_text(encoding="utf-8")  # info: set raw
            self.assertIn("m9", raw)  # info: self . assertIn ( "m9" , raw )
            self.assertNotIn("tides", raw)  # info: self . assertNotIn ( "tides" , raw )
            again = ScriptedInfer()  # info: set again
            review.respond(  # info: call review . respond
                "channel-1",  # info: "channel-1"
                [{"id": "m9", "content": USER, "author": {}}],  # info: [ { "id" : "m9" , "content" : USER , "author" : { } } ]
                post=lambda channel, content: {"id": "x"},  # info: post = lambda channel , content : { "id" : "x" }
                log=lambda line: None,  # info: log = lambda line : None
                infer=again,  # info: infer = again
                seen_path=path,  # info: seen_path = path
            )  # info: )
        self.assertEqual(again.calls, [])  # info: self . assertEqual ( again . calls , [ ] )

    def test_post_gate_still_refuses_http(self):  # info: def test_post_gate_still_refuses_http
        os.environ.pop("RR_DISCORD_POST", None)  # info: os . environ . pop ( "RR_DISCORD_POST" , None )
        with patch("urllib.request.urlopen", side_effect=AssertionError("discord http")):  # info: with patch ( "urllib.request.urlopen" , side_effect = AssertionError ( "discord http" ) )
            self.assertIsNone(post_message("123", "hello"))  # info: self . assertIsNone ( post_message ( "123" , "hello" ) )

    def test_default_infer_uses_run_infer_and_library_persona(self):  # info: def test_default_infer_uses_run_infer_and_library_persona
        self.assertTrue(review.RUN_INFER.is_file())  # info: self . assertTrue ( review . RUN_INFER . is_file ( ) )
        self.assertTrue(str(review.RUN_INFER).endswith("run-infer.sh"))  # info: self . assertTrue ( str ( review . RUN_INFER ) . endswith ( "run-infer.sh" ) )
        with patch.object(review, "persona_system", return_value="CANONICAL-PERSONA") as loaded:  # info: with patch . object ( review , "persona_system" , return_value = "CANONICAL-PERSONA" ) as loaded
            with patch("review.subprocess.run") as run:  # info: with patch ( "review.subprocess.run" ) as run
                run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="hello\n", stderr="")  # info: run . return_value = subprocess . CompletedProcess ( args = [ ] , returncode = 0 , stdout = "hello\n" , stderr = "" )
                out = review.default_infer("bruce", "review this draft")  # info: set out
        self.assertEqual(out, "hello")  # info: self . assertEqual ( out , "hello" )
        loaded.assert_called_once_with("bruce")  # info: loaded . assert_called_once_with ( "bruce" )
        argv = run.call_args.args[0]  # info: set argv
        self.assertTrue(argv[0].endswith("run-infer.sh"))  # info: self . assertTrue ( argv [ 0 ] . endswith ( "run-infer.sh" ) )
        self.assertEqual(argv[1], "bruce")  # info: self . assertEqual ( argv [ 1 ] , "bruce" )
        env = run.call_args.kwargs["env"]  # info: set env
        self.assertEqual(env["RR_PERSONA_SYSTEM"], "CANONICAL-PERSONA")  # info: self . assertEqual ( env [ "RR_PERSONA_SYSTEM" ] , "CANONICAL-PERSONA" )
        self.assertEqual(env["RR_NPU_ONLY"], "1")  # info: self . assertEqual ( env [ "RR_NPU_ONLY" ] , "1" )
        self.assertEqual(env["RR_NPU_PERSONA"], "1")  # info: self . assertEqual ( env [ "RR_NPU_PERSONA" ] , "1" )
        self.assertEqual(env["FLM_MODEL"], "llama3.2:3b")  # info: self . assertEqual ( env [ "FLM_MODEL" ] , "llama3.2:3b" )
        self.assertEqual(env["RR_CALLER"], "discord-review")  # info: self . assertEqual ( env [ "RR_CALLER" ] , "discord-review" )

    def test_persona_loader_reads_library(self):  # info: def test_persona_loader_reads_library
        review._PERSONA.clear()  # info: review . _PERSONA . clear ( )
        ava = review.persona_system("ava")  # info: set ava
        bruce = review.persona_system("bruce")  # info: set bruce
        carly = review.persona_system("carly")  # info: set carly
        self.assertIn("Ava Ivy", ava)  # info: self . assertIn ( "Ava Ivy" , ava )
        self.assertIn("Bruce", bruce)  # info: self . assertIn ( "Bruce" , bruce )
        self.assertIn("Carly", carly)  # info: self . assertIn ( "Carly" , carly )
        self.assertFalse((DISCORD / "personas").exists())  # info: self . assertFalse ( ( DISCORD / "personas" ) . exists ( ) )

    def test_orchestration_does_not_embed_personas_or_telegram(self):  # info: def test_orchestration_does_not_embed_personas_or_telegram
        text = (DISCORD / "scripts" / "review.py").read_text(encoding="utf-8")  # info: set text
        self.assertNotIn("AVA_PROMPT", text)  # info: self . assertNotIn ( "AVA_PROMPT" , text )
        self.assertNotIn("PIPELINE_ORDER", text)  # info: self . assertNotIn ( "PIPELINE_ORDER" , text )
        self.assertNotIn("council-relay", text)  # info: self . assertNotIn ( "council-relay" , text )
        self.assertNotIn("Visionary Architect", text)  # info: self . assertNotIn ( "Visionary Architect" , text )
        api = (DISCORD / "lib" / "api.py").read_text(encoding="utf-8")  # info: set api
        self.assertIn('RR_DISCORD_POST', api)  # info: self . assertIn ( "RR_DISCORD_POST" , api )
        relay = DISCORD.parent / "telegram" / "scripts" / "council-relay.py"  # info: set relay
        self.assertTrue(relay.is_file())  # info: self . assertTrue ( relay . is_file ( ) )
        relay_text = relay.read_text(encoding="utf-8")  # info: set relay_text
        self.assertIn("PIPELINE_ORDER", relay_text)  # info: self . assertIn ( "PIPELINE_ORDER" , relay_text )


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(unittest.main())  # info: raise SystemExit ( unittest . main ( ) )
