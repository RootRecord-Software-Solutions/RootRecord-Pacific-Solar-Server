"""Smoke tests for core/manifest.py load/save round-trip and state transitions."""
from __future__ import annotations

import tempfile

from core.manifest import Manifest


def test_get_or_create_then_record_success_round_trips():
    with tempfile.TemporaryDirectory() as tmp:
        m = Manifest(tmp).load()
        m.get_or_create("r1", "https://example.com/x", "x")
        m.record_success(
            "r1", etag="abc", last_modified=None, content_length=10,
            content_sha256="deadbeef", fetched_at_hst_iso="2026-09-24T04:00:00-10:00",
        )
        m.save()

        reloaded = Manifest(tmp).load()
        state = reloaded.get("r1")
        assert state is not None
        assert state.etag == "abc"
        assert state.content_sha256 == "deadbeef"
        assert state.consecutive_failures == 0


def test_record_failure_increments_counter():
    with tempfile.TemporaryDirectory() as tmp:
        m = Manifest(tmp).load()
        m.get_or_create("r1", "u", "d")
        m.record_failure("r1", failed_at_hst_iso="2026-09-24T04:00:00-10:00")
        m.record_failure("r1", failed_at_hst_iso="2026-09-24T04:05:00-10:00")
        assert m.get("r1").consecutive_failures == 2


def test_record_success_resets_failure_counter():
    with tempfile.TemporaryDirectory() as tmp:
        m = Manifest(tmp).load()
        m.get_or_create("r1", "u", "d")
        m.record_failure("r1", failed_at_hst_iso="t1")
        m.record_success(
            "r1", etag=None, last_modified=None, content_length=1,
            content_sha256="h", fetched_at_hst_iso="t2",
        )
        assert m.get("r1").consecutive_failures == 0
