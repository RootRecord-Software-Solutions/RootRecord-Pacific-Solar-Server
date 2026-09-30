# ==============================================================================
# FILE: Weather/tests/scheduler/test_run_cycle_smoke.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
import types  # info: import types

# ====================================================
# SECTION: block if
# What it does: 'httpx' not in sys.modules
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
if "httpx" not in sys.modules:  # info: if "httpx" not in sys . modules :
    _stub = types.ModuleType("httpx")  # info: set _stub

    class _Headers(dict):  # info: class _Headers
        pass  # info: pass

    class _HTTPStatusError(Exception):  # info: class _HTTPStatusError
        pass  # info: pass

    class _Client:  # info: class _Client
        def __init__(self, *a, **kw):  # info: def __init__
            pass  # info: pass

        def __enter__(self):  # info: def __enter__
            return self  # info: return self

        def __exit__(self, *a):  # info: def __exit__
            return False  # info: return False

    _stub.Headers = _Headers  # info: _stub . Headers = _Headers
    _stub.HTTPStatusError = _HTTPStatusError  # info: _stub . HTTPStatusError = _HTTPStatusError
    _stub.Client = _Client  # info: _stub . Client = _Client
    sys.modules["httpx"] = _stub  # info: sys . modules [ "httpx" ] = _stub

from scheduler import run_cycle, tiers  # noqa: E402  (import after stub install)


# ====================================================
# SECTION: class _FakeManifest
# What it does: Stands in for core.manifest.Manifest without touching disk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class _FakeManifest:  # info: class _FakeManifest
    """Stands in for core.manifest.Manifest without touching disk."""  # info: """Stands in for core.manifest.Manifest without touching disk."""

    def load(self):  # info: def load
        return self  # info: return self

    def save(self):  # info: def save
        pass  # info: pass


# ====================================================
# SECTION: function _patch_manifest
# What it does:  patch manifest.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _patch_manifest(monkeypatch_calls):  # info: def _patch_manifest
    import core.manifest as manifest_mod  # info: import core . manifest as manifest_mod
    monkeypatch_calls.append((manifest_mod, "Manifest", manifest_mod.Manifest))  # info: monkeypatch_calls . append ( ( manifest_mod , "Manifest"
    manifest_mod.Manifest = lambda base_dir: _FakeManifest()  # info: manifest_mod . Manifest = lambda base_dir : _FakeManifest
    run_cycle.Manifest = manifest_mod.Manifest  # info: run_cycle . Manifest = manifest_mod . Manifest


# ====================================================
# SECTION: function _restore
# What it does:  restore.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _restore(monkeypatch_calls):  # info: def _restore
    for mod, name, original in monkeypatch_calls:  # info: for mod , name , original in monkeypatch_calls
        setattr(mod, name, original)  # info: call setattr


# ====================================================
# SECTION: function test_run_once_dispatches_every_module_on_first_tick
# What it does: test run once dispatches every module on first tick.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_run_once_dispatches_every_module_on_first_tick():  # info: def test_run_once_dispatches_every_module_on_first_tick
    calls = []  # info: set calls
    restore = []  # info: set restore
    _patch_manifest(restore)  # info: call _patch_manifest
    try:  # info: try :
        fake_modules = {}  # info: set fake_modules
        for name in run_cycle.FETCH_MODULES:  # info: for name in run_cycle . FETCH_MODULES :
            def make_fake(n):  # info: def make_fake
                def fake(manifest, base_dir):  # info: def fake
                    calls.append(n)  # info: calls . append ( n )
                    return []  # info: return [ ]
                return fake  # info: return fake
            fake_modules[name] = make_fake(name)  # info: fake_modules [ name ] = make_fake ( name

        original_modules = dict(run_cycle.FETCH_MODULES)  # info: set original_modules
        run_cycle.FETCH_MODULES = fake_modules  # info: run_cycle . FETCH_MODULES = fake_modules

        original_poll = run_cycle.hurricane_sources.poll  # info: set original_poll
        hurricane_calls = []  # info: set hurricane_calls
        run_cycle.hurricane_sources.poll = lambda base_dir: hurricane_calls.append(base_dir)  # info: run_cycle . hurricane_sources . poll = lambda base_dir

        state = run_cycle.SchedulerState()  # info: set state
        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")  # info: run_cycle . run_once ( state , "/fake/base" ,

        # First-ever tick: every module has last_run_monotonic=None -> due.
        assert set(calls) == set(original_modules.keys())  # info: assert set ( calls ) == set (
        assert hurricane_calls == ["/fake/hurricanes"]  # info: assert hurricane_calls == [ "/fake/hurricanes" ]
        # State recorded a run time for every dispatched module.
        assert set(state.last_run_monotonic.keys()) == set(original_modules.keys())  # info: assert set ( state . last_run_monotonic . keys

        run_cycle.FETCH_MODULES = original_modules  # info: run_cycle . FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll  # info: run_cycle . hurricane_sources . poll = original_poll
    finally:  # info: finally :
        _restore(restore)  # info: call _restore


# ====================================================
# SECTION: function test_run_once_skips_modules_not_yet_due
# What it does: test run once skips modules not yet due.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_run_once_skips_modules_not_yet_due():  # info: def test_run_once_skips_modules_not_yet_due
    calls = []  # info: set calls
    restore = []  # info: set restore
    _patch_manifest(restore)  # info: call _patch_manifest
    try:  # info: try :
        original_modules = dict(run_cycle.FETCH_MODULES)  # info: set original_modules

        def fake(manifest, base_dir):  # info: def fake
            calls.append("alerts")  # info: calls . append ( "alerts" )
            return []  # info: return [ ]

        run_cycle.FETCH_MODULES = {"alerts": fake}  # info: run_cycle . FETCH_MODULES = { "alerts" : fake

        original_poll = run_cycle.hurricane_sources.poll  # info: set original_poll
        run_cycle.hurricane_sources.poll = lambda base_dir: None  # info: run_cycle . hurricane_sources . poll = lambda base_dir

        state = run_cycle.SchedulerState()  # info: set state
        # Pretend alerts (tier 0) just ran a moment ago -- tier 0's cadence
        # (fastest tier, per config/tiers.yaml) should not have elapsed yet.
        import time  # info: import time
        state.last_run_monotonic["alerts"] = time.monotonic()  # info: state . last_run_monotonic [ "alerts" ] = time

        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")  # info: run_cycle . run_once ( state , "/fake/base" ,

        assert calls == []  # not due yet, correctly skipped

        run_cycle.FETCH_MODULES = original_modules  # info: run_cycle . FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll  # info: run_cycle . hurricane_sources . poll = original_poll
    finally:  # info: finally :
        _restore(restore)  # info: call _restore


# ====================================================
# SECTION: function test_midnight_rollover_fires_exactly_once_per_hst_day_change
# What it does: test midnight rollover fires exactly once per hst day change.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_midnight_rollover_fires_exactly_once_per_hst_day_change():  # info: def test_midnight_rollover_fires_exactly_once_per_hst_day_change
    from core import hst_time  # info: from core import hst_time
    from datetime import datetime, timezone  # info: from datetime import datetime , timezone

    state = run_cycle.SchedulerState()  # info: set state
    rollover_calls = []  # info: set rollover_calls

    import archive.consolidate as consolidate_mod  # info: import archive . consolidate as consolidate_mod
    original = consolidate_mod.consolidate_yesterday  # info: set original
    consolidate_mod.consolidate_yesterday = lambda base_dir, yesterday_folder: rollover_calls.append(  # info: consolidate_mod . consolidate_yesterday = lambda base_dir , yesterday_folder
        (base_dir, yesterday_folder)  # info: call (
    )  # info: )

    original_hst_now = hst_time.hst_now  # info: set original_hst_now
    try:  # info: try :
        # First call establishes the baseline day -- no rollover fires.
        hst_time.hst_now = lambda: datetime(2026, 9, 25, 9, 0, 0, tzinfo=timezone.utc)  # info: hst_time . hst_now = lambda : datetime (
        run_cycle._check_midnight_rollover(state, "/fake/base")  # info: run_cycle . _check_midnight_rollover ( state , "/fake/base" )
        assert rollover_calls == []  # info: assert rollover_calls == [ ]
        assert state.last_seen_hst_date == hst_time.hst_date_folder(hst_time.hst_now())  # info: assert state . last_seen_hst_date == hst_time . hst_date_folder

        # Same HST day again -- still no rollover.
        run_cycle._check_midnight_rollover(state, "/fake/base")  # info: run_cycle . _check_midnight_rollover ( state , "/fake/base" )
        assert rollover_calls == []  # info: assert rollover_calls == [ ]

        # Now cross into the next HST day -- rollover should fire once.
        hst_time.hst_now = lambda: datetime(2026, 9, 26, 10, 30, 0, tzinfo=timezone.utc)  # info: hst_time . hst_now = lambda : datetime (
        run_cycle._check_midnight_rollover(state, "/fake/base")  # info: run_cycle . _check_midnight_rollover ( state , "/fake/base" )
        assert len(rollover_calls) == 1  # info: assert len ( rollover_calls ) == 1

        # Ticking again on the same new day must NOT fire a second time.
        run_cycle._check_midnight_rollover(state, "/fake/base")  # info: run_cycle . _check_midnight_rollover ( state , "/fake/base" )
        assert len(rollover_calls) == 1  # info: assert len ( rollover_calls ) == 1
    finally:  # info: finally :
        hst_time.hst_now = original_hst_now  # info: hst_time . hst_now = original_hst_now
        consolidate_mod.consolidate_yesterday = original  # info: consolidate_mod . consolidate_yesterday = original


# ====================================================
# SECTION: function test_a_broken_module_does_not_crash_the_rest_of_the_pass
# What it does: test a broken module does not crash the rest of the pass.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_a_broken_module_does_not_crash_the_rest_of_the_pass():  # info: def test_a_broken_module_does_not_crash_the_rest_of_the_pass
    # Regression for the hardening added when this was wired up to run as
    # an always-on daemon: one module raising must not stop the others
    # from running, and must not propagate out of run_once at all.
    calls = []  # info: set calls
    restore = []  # info: set restore
    _patch_manifest(restore)  # info: call _patch_manifest
    try:  # info: try :
        def broken(manifest, base_dir):  # info: def broken
            raise RuntimeError("simulated config bug")  # info: raise RuntimeError ( "simulated config bug" )

        def fine(manifest, base_dir):  # info: def fine
            calls.append("fine")  # info: calls . append ( "fine" )
            return []  # info: return [ ]

        original_modules = dict(run_cycle.FETCH_MODULES)  # info: set original_modules
        run_cycle.FETCH_MODULES = {"alerts": broken, "text_products": fine}  # info: run_cycle . FETCH_MODULES = { "alerts" : broken

        original_poll = run_cycle.hurricane_sources.poll  # info: set original_poll
        run_cycle.hurricane_sources.poll = lambda base_dir: None  # info: run_cycle . hurricane_sources . poll = lambda base_dir

        state = run_cycle.SchedulerState()  # info: set state
        # Must not raise.
        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")  # info: run_cycle . run_once ( state , "/fake/base" ,

        assert calls == ["fine"]  # the working module still ran
        # The broken module is still marked as "just attempted" so it
        # backs off to its own tier cadence rather than retrying every tick.
        assert "alerts" in state.last_run_monotonic  # info: assert "alerts" in state . last_run_monotonic

        run_cycle.FETCH_MODULES = original_modules  # info: run_cycle . FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll  # info: run_cycle . hurricane_sources . poll = original_poll
    finally:  # info: finally :
        _restore(restore)  # info: call _restore


# ====================================================
# SECTION: function test_broken_hurricanes_poll_does_not_crash_run_once
# What it does: test broken hurricanes poll does not crash run once.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_broken_hurricanes_poll_does_not_crash_run_once():  # info: def test_broken_hurricanes_poll_does_not_crash_run_once
    restore = []  # info: set restore
    _patch_manifest(restore)  # info: call _patch_manifest
    try:  # info: try :
        original_modules = dict(run_cycle.FETCH_MODULES)  # info: set original_modules
        run_cycle.FETCH_MODULES = {}  # isolate this test to the hurricanes phase

        original_poll = run_cycle.hurricane_sources.poll  # info: set original_poll

        def broken_poll(base_dir):  # info: def broken_poll
            raise ConnectionError("simulated offline NWS/NHC")  # info: raise ConnectionError ( "simulated offline NWS/NHC" )

        run_cycle.hurricane_sources.poll = broken_poll  # info: run_cycle . hurricane_sources . poll = broken_poll

        state = run_cycle.SchedulerState()  # info: set state
        run_cycle.run_once(state, "/fake/base", "/fake/hurricanes")  # must not raise

        assert state.last_hurricanes_run_monotonic is not None  # info: assert state . last_hurricanes_run_monotonic is not None

        run_cycle.FETCH_MODULES = original_modules  # info: run_cycle . FETCH_MODULES = original_modules
        run_cycle.hurricane_sources.poll = original_poll  # info: run_cycle . hurricane_sources . poll = original_poll
    finally:  # info: finally :
        _restore(restore)  # info: call _restore


# ====================================================
# SECTION: function test_alerts_processing_ignores_the_wwamap_png_outcome
# What it does: test alerts processing ignores the wwamap png outcome.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_alerts_processing_ignores_the_wwamap_png_outcome():  # info: def test_alerts_processing_ignores_the_wwamap_png_outcome
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
    import json  # info: import json
    import tempfile  # info: import tempfile
    from pathlib import Path  # info: from pathlib import Path

    from fetch import _engine  # info: from fetch import _engine

    tmp_dir = tempfile.mkdtemp()  # info: set tmp_dir
    json_path = Path(tmp_dir) / "area=HI_current.json"  # info: set json_path
    json_path.write_text(json.dumps({"features": []}), encoding="utf-8")  # info: json_path . write_text ( json . dumps (
    png_path = Path(tmp_dir) / "hfo.png"  # info: set png_path
    png_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"not really a png but binary")  # info: png_path . write_bytes ( b"\x89PNG\r\n\x1a\n" + b"not really a png but binary" )

    outcomes = [  # info: set outcomes
        _engine.FetchOutcome(  # info: _engine . FetchOutcome (
            resource_id="alerts_active_hi", status="written",  # info: set resource_id
            detail="ok", path=str(json_path),  # info: set detail
        ),  # info: ) ,
        _engine.FetchOutcome(  # info: _engine . FetchOutcome (
            resource_id="wwamap_png", status="written",  # info: set resource_id
            detail="ok", path=str(png_path),  # info: set detail
        ),  # info: ) ,
    ]  # info: ]

    run_cycle._run_alerts_processing(outcomes, tmp_dir)  # must not raise

    enriched_path = Path(tmp_dir) / "alerts_enriched_current.json"  # info: set enriched_path
    assert enriched_path.exists()  # info: assert enriched_path . exists ( )
    assert json.loads(enriched_path.read_text(encoding="utf-8")) == []  # info: assert json . loads ( enriched_path . read_text
