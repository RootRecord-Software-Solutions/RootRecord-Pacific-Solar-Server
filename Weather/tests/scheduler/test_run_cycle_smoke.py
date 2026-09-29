"""Smoke test for scheduler/run_cycle.py's dispatch loop.

No real network happens here: every fetch/alerts/hurricanes entry point is
monkeypatched with a fake before run_once is ever called. The only reason
this file needs a stub `httpx` module at all is that `scheduler.run_cycle`
imports the whole `fetch` package at module level, and `fetch/_engine.py`
transitively imports `core/http_client.py`, which does `import httpx` at
its own module level -- that import must succeed for the module to load,
even though no code path in this test ever calls into it. If the real
`httpx` is installed, this stub is simply unused (sys.modules already has
it, so this is a no-op in that case only if httpx isn't already imported;
safest to skip installing the stub if httpx already loaded correctly).
"""
from __future__ import annotations

import sys
import types

if "httpx" not in sys.modules:
    _stub = types.ModuleType("httpx")

    class _Headers(dict):
        pass

    class _HTTPStatusError(Exception):
        pass

    class _Client:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    _stub.Headers = _Headers
    _stub.HTTPStatusError = _HTTPStatusError
    _stub.Client = _Client
    sys.modules["httpx"] = _stub

from scheduler import run_cycle, tiers  # noqa: E402  (import after stub install)


class _FakeManifest:
    """Stands in for core.manifest.Manifest without touching disk."""

    def load(self):
        return self

    def save(self):
        pass


def _patch_manifest(monkeypatch_calls):
    import core.manifest as manifest_mod
    monkeypatch_calls.append((manifest_mod, "Manifest", manifest_mod.Manifest))
    manifest_mod.Manifest = lambda base_dir: _FakeManifest()
    run_cycle.Manifest = manifest_mod.Manifest


def _restore(monkeypatch_calls):
    for mod, name, original in monkeypatch_calls:
        setattr(mod, name, original)


def test_run_once_dispatches_every_module_on_first_tick():
    calls = []
    restore = []
    _patch_manifest(restore)
    try:
        fake_modules = {}
        for name in run_cycle.FETCH_MODULES:
            def make_fake(n):
                def fake(manifest, base_dir):
                    calls.append(n)
                    return []
                return fake
            fake_modules[name] = make_fake(name)

        original_modules = dict(run_cycle.FETCH_MODULES)
        run_cycle.FETCH_MODULES = fake_modules

        original_poll = run_cycle.hurricane_sources.poll
        hurricane_calls = []
        run_cycle.hurricane_sources.poll = lambda base_dir: hurricane_calls.append(base_dir)

        state = run_cycle.SchedulerState()
        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")

        # First-ever tick: every module has last_run_monotonic=None -> due.
        assert set(calls) == set(original_modules.keys())
        assert hurricane_calls == ["/fake/hurricanes"]
        # State recorded a run time for every dispatched module.
        assert set(state.last_run_monotonic.keys()) == set(original_modules.keys())

        run_cycle.FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll
    finally:
        _restore(restore)


def test_run_once_skips_modules_not_yet_due():
    calls = []
    restore = []
    _patch_manifest(restore)
    try:
        original_modules = dict(run_cycle.FETCH_MODULES)

        def fake(manifest, base_dir):
            calls.append("alerts")
            return []

        run_cycle.FETCH_MODULES = {"alerts": fake}

        original_poll = run_cycle.hurricane_sources.poll
        run_cycle.hurricane_sources.poll = lambda base_dir: None

        state = run_cycle.SchedulerState()
        # Pretend alerts (tier 0) just ran a moment ago -- tier 0's cadence
        # (fastest tier, per config/tiers.yaml) should not have elapsed yet.
        import time
        state.last_run_monotonic["alerts"] = time.monotonic()

        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")

        assert calls == []  # not due yet, correctly skipped

        run_cycle.FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll
    finally:
        _restore(restore)


def test_midnight_rollover_fires_exactly_once_per_hst_day_change():
    from core import hst_time
    from datetime import datetime, timezone

    state = run_cycle.SchedulerState()
    rollover_calls = []

    import archive.consolidate as consolidate_mod
    original = consolidate_mod.consolidate_yesterday
    consolidate_mod.consolidate_yesterday = lambda base_dir, yesterday_folder: rollover_calls.append(
        (base_dir, yesterday_folder)
    )

    original_hst_now = hst_time.hst_now
    try:
        # First call establishes the baseline day -- no rollover fires.
        hst_time.hst_now = lambda: datetime(2026, 9, 25, 9, 0, 0, tzinfo=timezone.utc)
        run_cycle._check_midnight_rollover(state, "/fake/base")
        assert rollover_calls == []
        assert state.last_seen_hst_date == hst_time.hst_date_folder(hst_time.hst_now())

        # Same HST day again -- still no rollover.
        run_cycle._check_midnight_rollover(state, "/fake/base")
        assert rollover_calls == []

        # Now cross into the next HST day -- rollover should fire once.
        hst_time.hst_now = lambda: datetime(2026, 9, 26, 10, 30, 0, tzinfo=timezone.utc)
        run_cycle._check_midnight_rollover(state, "/fake/base")
        assert len(rollover_calls) == 1

        # Ticking again on the same new day must NOT fire a second time.
        run_cycle._check_midnight_rollover(state, "/fake/base")
        assert len(rollover_calls) == 1
    finally:
        hst_time.hst_now = original_hst_now
        consolidate_mod.consolidate_yesterday = original


def test_a_broken_module_does_not_crash_the_rest_of_the_pass():
    # Regression for the hardening added when this was wired up to run as
    # an always-on daemon: one module raising must not stop the others
    # from running, and must not propagate out of run_once at all.
    calls = []
    restore = []
    _patch_manifest(restore)
    try:
        def broken(manifest, base_dir):
            raise RuntimeError("simulated config bug")

        def fine(manifest, base_dir):
            calls.append("fine")
            return []

        original_modules = dict(run_cycle.FETCH_MODULES)
        run_cycle.FETCH_MODULES = {"alerts": broken, "text_products": fine}

        original_poll = run_cycle.hurricane_sources.poll
        run_cycle.hurricane_sources.poll = lambda base_dir: None

        state = run_cycle.SchedulerState()
        # Must not raise.
        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")

        assert calls == ["fine"]  # the working module still ran
        # The broken module is still marked as "just attempted" so it
        # backs off to its own tier cadence rather than retrying every tick.
        assert "alerts" in state.last_run_monotonic

        run_cycle.FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll
    finally:
        _restore(restore)


def test_broken_hurricanes_poll_does_not_crash_run_once():
    restore = []
    _patch_manifest(restore)
    try:
        original_modules = dict(run_cycle.FETCH_MODULES)
        run_cycle.FETCH_MODULES = {}  # isolate this test to the hurricanes phase

        original_poll = run_cycle.hurricane_sources.poll

        def broken_poll(base_dir):
            raise ConnectionError("simulated offline NWS/NHC")

        run_cycle.hurricane_sources.poll = broken_poll

        state = run_cycle.SchedulerState()
        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")  # must not raise

        assert state.last_hurricanes_run_monotonic is not None

        run_cycle.FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll
    finally:
        _restore(restore)


def test_alerts_processing_ignores_the_wwamap_png_outcome():
    # Regression: fetch/alerts.py's fetch_all() returns TWO outcomes, in
    # this order -- the alerts_active_hi JSON feed FIRST, then the
    # wwamap_png image (see config/resources.yaml). _run_alerts_processing
    # used to iterate over every outcome and json.loads() its path
    # unconditionally; since the JSON one is processed first, dedupe/etc.
    # already ran successfully by the time it hit the PNG's binary bytes
    # and raised an uncaught UnicodeDecodeError. That's why asserting
    # "dedupe was called" or "the module was attempted" doesn't actually
    # catch this bug -- both are true either way. The real, load-bearing
    # assertion is that the function returns normally (this stdlib test
    # runner reports a FAIL if it raises) AND that its output file, whose
    # write is the very last line of the function, actually landed on
    # disk -- proving the PNG outcome was reached and skipped, not that
    # the function died partway through it.
    import json
    import tempfile
    from pathlib import Path

    from fetch import _engine

    tmp_dir = tempfile.mkdtemp()
    json_path = Path(tmp_dir) / "area=HI_current.json"
    json_path.write_text(json.dumps({"features": []}), encoding="utf-8")
    png_path = Path(tmp_dir) / "hfo.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"not really a png but binary")

    outcomes = [
        _engine.FetchOutcome(
            resource_id="alerts_active_hi", status="written",
            detail="ok", path=str(json_path),
        ),
        _engine.FetchOutcome(
            resource_id="wwamap_png", status="written",
            detail="ok", path=str(png_path),
        ),
    ]

    run_cycle._run_alerts_processing(outcomes, tmp_dir)  # must not raise

    enriched_path = Path(tmp_dir) / "alerts_enriched_current.json"
    assert enriched_path.exists()
    assert json.loads(enriched_path.read_text(encoding="utf-8")) == []
