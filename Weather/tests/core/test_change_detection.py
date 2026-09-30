# ==============================================================================
# FILE: Weather/tests/core/test_change_detection.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/change_detection.py."""  # info: """Smoke tests for core/change_detection.py."""
from __future__ import annotations  # info: from __future__ import annotations

from core import change_detection  # info: from core import change_detection
from core.manifest import ResourceState  # info: from core . manifest import ResourceState


# ====================================================
# SECTION: function _state
# What it does:  state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _state(**overrides) -> ResourceState:  # info: def _state
    base = dict(resource_id="r1", url="https://example.com/x.gif", local_resource_dir="x")  # info: set base
    base.update(overrides)  # info: base . update ( overrides )
    return ResourceState(**base)  # info: return ResourceState ( ** base )


# ====================================================
# SECTION: function test_304_is_always_unchanged
# What it does: test 304 is always unchanged.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_304_is_always_unchanged():  # info: def test_304_is_always_unchanged
    verdict = change_detection.detect(  # info: set verdict
        _state(), was_304=True, response_etag=None, response_last_modified=None,  # info: call _state
        response_content_length=None, content=None,  # info: set response_content_length
    )  # info: )
    assert verdict.changed is False  # info: assert verdict . changed is False


# ====================================================
# SECTION: function test_first_ever_fetch_is_changed
# What it does: test first ever fetch is changed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_first_ever_fetch_is_changed():  # info: def test_first_ever_fetch_is_changed
    verdict = change_detection.detect(  # info: set verdict
        _state(content_sha256=None), was_304=False, response_etag="abc",  # info: call _state
        response_last_modified=None, response_content_length=5, content=b"hello",  # info: set response_last_modified
    )  # info: )
    assert verdict.changed is True  # info: assert verdict . changed is True
    assert verdict.new_sha256 == change_detection.sha256_of(b"hello")  # info: assert verdict . new_sha256 == change_detection . sha256_of


# ====================================================
# SECTION: function test_same_hash_is_unchanged_even_on_200
# What it does: test same hash is unchanged even on 200.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_same_hash_is_unchanged_even_on_200():  # info: def test_same_hash_is_unchanged_even_on_200
    h = change_detection.sha256_of(b"hello")  # info: set h
    verdict = change_detection.detect(  # info: set verdict
        _state(content_sha256=h), was_304=False, response_etag=None,  # info: call _state
        response_last_modified=None, response_content_length=5, content=b"hello",  # info: set response_last_modified
    )  # info: )
    assert verdict.changed is False  # info: assert verdict . changed is False


# ====================================================
# SECTION: function test_different_hash_is_changed
# What it does: test different hash is changed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_different_hash_is_changed():  # info: def test_different_hash_is_changed
    h = change_detection.sha256_of(b"old content")  # info: set h
    verdict = change_detection.detect(  # info: set verdict
        _state(content_sha256=h), was_304=False, response_etag=None,  # info: call _state
        response_last_modified=None, response_content_length=11, content=b"new content",  # info: set response_last_modified
    )  # info: )
    assert verdict.changed is True  # info: assert verdict . changed is True
