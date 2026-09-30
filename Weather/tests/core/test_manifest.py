# ==============================================================================
# FILE: Weather/tests/core/test_manifest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/manifest.py load/save round-trip and state transitions."""  # info: """Smoke tests for core/manifest.py load/save round-trip and state transitions."""
from __future__ import annotations  # info: from __future__ import annotations

import tempfile  # info: import tempfile

from core.manifest import Manifest  # info: from core . manifest import Manifest


# ====================================================
# SECTION: function test_get_or_create_then_record_success_round_trips
# What it does: test get or create then record success round trips.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_get_or_create_then_record_success_round_trips():  # info: def test_get_or_create_then_record_success_round_trips
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        m = Manifest(tmp).load()  # info: set m
        m.get_or_create("r1", "https://example.com/x", "x")  # info: m . get_or_create ( "r1" , "https://example.com/x" ,
        m.record_success(  # info: m . record_success (
            "r1", etag="abc", last_modified=None, content_length=10,  # info: "r1" , etag = "abc" , last_modified =
            content_sha256="deadbeef", fetched_at_hst_iso="2026-09-24T04:00:00-10:00",  # info: set content_sha256
        )  # info: )
        m.save()  # info: m . save ( )

        reloaded = Manifest(tmp).load()  # info: set reloaded
        state = reloaded.get("r1")  # info: set state
        assert state is not None  # info: assert state is not None
        assert state.etag == "abc"  # info: assert state . etag == "abc"
        assert state.content_sha256 == "deadbeef"  # info: assert state . content_sha256 == "deadbeef"
        assert state.consecutive_failures == 0  # info: assert state . consecutive_failures == 0


# ====================================================
# SECTION: function test_record_failure_increments_counter
# What it does: test record failure increments counter.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_record_failure_increments_counter():  # info: def test_record_failure_increments_counter
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        m = Manifest(tmp).load()  # info: set m
        m.get_or_create("r1", "u", "d")  # info: m . get_or_create ( "r1" , "u" ,
        m.record_failure("r1", failed_at_hst_iso="2026-09-24T04:00:00-10:00")  # info: m . record_failure ( "r1" , failed_at_hst_iso =
        m.record_failure("r1", failed_at_hst_iso="2026-09-24T04:05:00-10:00")  # info: m . record_failure ( "r1" , failed_at_hst_iso =
        assert m.get("r1").consecutive_failures == 2  # info: assert m . get ( "r1" ) .


# ====================================================
# SECTION: function test_record_success_resets_failure_counter
# What it does: test record success resets failure counter.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_record_success_resets_failure_counter():  # info: def test_record_success_resets_failure_counter
    with tempfile.TemporaryDirectory() as tmp:  # info: with tempfile . TemporaryDirectory ( ) as tmp
        m = Manifest(tmp).load()  # info: set m
        m.get_or_create("r1", "u", "d")  # info: m . get_or_create ( "r1" , "u" ,
        m.record_failure("r1", failed_at_hst_iso="t1")  # info: m . record_failure ( "r1" , failed_at_hst_iso =
        m.record_success(  # info: m . record_success (
            "r1", etag=None, last_modified=None, content_length=1,  # info: "r1" , etag = None , last_modified =
            content_sha256="h", fetched_at_hst_iso="t2",  # info: set content_sha256
        )  # info: )
        assert m.get("r1").consecutive_failures == 0  # info: assert m . get ( "r1" ) .
