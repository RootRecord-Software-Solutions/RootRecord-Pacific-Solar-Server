"""The actual dispatch loop. Calls into fetch/, alerts/, and hurricanes/ on
their respective schedules -- makes no HTTP calls itself, per
scheduler/README.md's boundary rule.

Entry point: `run_forever(base_dir, hurricanes_base_dir)`. `run_once` does a
single dispatch pass and is what tests/ calls, since a real scheduler loop
isn't something a smoke test should sit through in real time.

ROBUSTNESS NOTE (added when this was wired up to run as an always-on
background daemon under automations/): every individual resource fetch
inside `fetch/_engine.py`'s `run_resource()` already catches its own
network/HTTP exceptions and records a "failed" outcome -- one bad resource
never takes down a fetch module. But nothing above that level was
similarly guarded: a whole module's `fetch_all()` raising (a config bug, a
JSON shape surprise, etc.), or `hurricanes.scripts.sources.poll()` (which
calls `http_client.get()` directly, with NO try/except of its own -- unlike
every `fetch/*.py` module), could previously propagate all the way out of
`run_once()` and kill the daemon outright, requiring a manual restart.
That was an acceptable gap for a smoke-tested/not-yet-networked build; it
is not acceptable for something meant to run unattended for weeks. Every
dispatch below is now wrapped so one module's exception is logged and
skipped, never fatal to the process.
"""
from __future__ import annotations

import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

# Every due fetch module (+ hurricanes) runs as its own thread now (see
# run_once). core/http_client.py's per-host locking is what makes this safe:
# two threads hitting the SAME host still serialize behind that host's own
# rate floor; threads hitting different hosts never wait on each other.
# Capped rather than unbounded purely so a future module addition doesn't
# silently spawn dozens of threads -- there are 10 fetch modules + hurricanes
# today (11), so this cap isn't expected to bind in practice.
MAX_CONCURRENT_MODULES = 16

from core import hst_time
from core.manifest import Manifest
from scheduler import tiers
from fetch import (
    alerts as fetch_alerts,
    analyses,
    aviation,
    climate,
    maps,
    marine,
    ndfd_gridpoint,
    radar,
    satellite,
    text_products,
    misc,
    gis,
)
from alerts import county_map, severity, dedupe
from hurricanes.scripts import sources as hurricane_sources
from reports import generator as weather_reports
from reports import county_generator as county_reports
from reports import official_generator as official_reports


def _log(msg: str) -> None:
    """Plain stdout line, timestamped in HST -- picked up by whatever
    supervises this process (see scripts/ensure-weather-poller.sh, which
    redirects stdout to a log file under Database/WEATHER/Hawai'i/logs/).
    Deliberately not a logging.Logger: nothing else in this tree uses one,
    and a single print-style line matches automations/'s own job-log
    convention (see rootserver_poller.py's `log()`).
    """
    print(f"{hst_time.hst_now().isoformat(timespec='seconds')} {msg}", flush=True)


# module_name -> fetch_all(manifest, base_dir) entry point. Order matters
# only in that alerts runs first, since alerts/'s own processing step reads
# its output immediately after (see _run_module below).
FETCH_MODULES: dict[str, Callable] = {
    "alerts": fetch_alerts.fetch_all,
    "text_products": text_products.fetch_all,
    "satellite": satellite.fetch_all,
    "analyses": analyses.fetch_all,
    "radar": radar.fetch_all,
    "marine": marine.fetch_all,
    "aviation": aviation.fetch_all,
    "climate": climate.fetch_all,
    "maps": maps.fetch_all,
    "ndfd_gridpoint": ndfd_gridpoint.fetch_all,
    "misc": misc.fetch_all,
    "gis": gis.fetch_all,
}

# HURRICANES_CADENCE_SECONDS: the plan (hurricanes/SKILL.md) never states
# an explicit cadence for this sub-skill. 900s (15 min) was originally a
# placeholder; the user confirmed keeping 900s as the real value (session
# after nextagent.md's handoff) rather than tightening or loosening it, so
# this is now a settled decision, not an open item.
HURRICANES_CADENCE_SECONDS = 900.0


class SchedulerState:
    """In-memory last-run tracking, per module + hurricanes + archive
    rollover. Deliberately NOT persisted to disk (unlike core/manifest.py's
    per-resource state) -- a scheduler restart just means everything is
    "due" again on the next tick, which is safe (change_detection still
    no-ops anything actually unchanged) and simpler than adding a second
    state file to reason about.
    """

    def __init__(self) -> None:
        self.last_run_monotonic: dict[str, float] = {}
        self.last_hurricanes_run_monotonic: float | None = None
        self.last_seen_hst_date: str | None = None  # for midnight-rollover detection


def _run_module(name: str, fetch_fn: Callable, manifest: Manifest, base_dir: str) -> bool:
    outcomes = fetch_fn(manifest, base_dir)
    changed = any(outcome.status == "written" for outcome in outcomes)
    for outcome in outcomes:
        if outcome.status in ("failed", "invalid"):
            _log(
                f"module:{name} resource:{outcome.resource_id} "
                f"{outcome.status.upper()} -- {outcome.detail}"
            )
    if name == "alerts":
        _run_alerts_processing(outcomes, base_dir)
    return changed


def _run_alerts_processing(alert_fetch_outcomes, base_dir: str) -> None:
    """After fetch/alerts.py writes the raw alerts JSON, run it through
    alerts/'s county-mapping -> severity -> dedupe pipeline. Reads the
    just-written _current file back off disk rather than threading the
    parsed JSON through FetchOutcome, since FetchOutcome only carries a
    path (see fetch/_engine.py) -- keeps the fetch/alerts.py contract
    identical to every other fetch module.
    """
    import json
    from pathlib import Path

    for outcome in alert_fetch_outcomes:
        # fetch/alerts.py's fetch_all() returns two outcomes: the JSON
        # alerts feed (resource_id "alerts_active_hi") AND the wwamap PNG
        # image (resource_id "wwamap_png", see config/resources.yaml).
        # Only the former is alerts data -- json.loads-ing the PNG's bytes
        # as UTF-8 text raised UnicodeDecodeError here (not OSError, not
        # JSONDecodeError, so it wasn't being caught below), which killed
        # this whole processing step for the pass and looked like an
        # "alerts module failure" in the log when the fetch itself was
        # actually fine. Filter to the one resource this function's
        # docstring already says it's meant to process.
        if outcome.resource_id != "alerts_active_hi":
            continue
        if outcome.status != "written" or not outcome.path:
            continue
        try:
            raw = json.loads(Path(outcome.path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        features = raw.get("features", [])
        # Dedupe operates on raw alert features (id + properties), per
        # alerts/dedupe.py's own contract -- county-mapping and severity are
        # then computed per surviving alert, not before, so dedupe always
        # sees the NWS-native (event, county, sent-time) shape it expects.
        deduped_features = dedupe.dedupe_by_event_and_county(features)
        enriched = []
        for feature in deduped_features:
            props = feature.get("properties", {})
            enriched.append({
                "id": feature.get("id"),
                "properties": props,
                "counties": sorted(county_map.county_keys_for_alert(props)),
                "severity_rank": severity.severity_rank(props),
                "critical": severity.is_critical(props),
            })
        deduped = enriched
        # Structured/enriched output is a processing artifact of alerts/,
        # not a raw fetch -- written alongside the raw _current file rather
        # than through core/archiver.py (that mechanic is for raw fetched
        # bytes with their own change-detection lifecycle, which this
        # derived data doesn't have).
        out_path = Path(outcome.path).parent / "alerts_enriched_current.json"
        out_path.write_text(json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8")


def run_once(state: SchedulerState, base_dir: str, hurricanes_base_dir: str) -> None:
    """One dispatch pass: check every fetch module's cadence, run whichever
    are due, check the hurricanes cadence, check for HST midnight rollover.

    CONCURRENCY NOTE (added 2026-09-25): every due module (+ hurricanes, if
    due) now runs in its own thread instead of strictly one-after-another.
    Previously a full pass took the SUM of every resource's own per-host
    rate floor -- ~150+ resources across 7 hosts serialized on one thread
    added up to 18-25 minutes for a single pass, and radar/hurricanes (late
    in dispatch order) were never reached before the process got restarted.
    Running modules concurrently means the pass now takes roughly as long
    as its single slowest host's own queue (core/http_client.py's per-host
    locking is what keeps this correct -- same-host requests still wait
    their turn, different-host requests never block each other).

    manifest.save() now happens after EACH task finishes (inside
    _run_and_save below), not once at the very end of the whole pass --
    previously a slow/interrupted pass meant _manifest.json was never
    written at all, since save() only ran after literally everything
    (hurricanes included) had already completed.

    Each task is individually try/except-guarded (see module docstring) --
    one module's exception is logged and skipped, every other task still
    completes this same pass.
    """
    manifest = Manifest(base_dir).load()
    now_mono = time.monotonic()

    def _run_and_save(label: str, fn: Callable[[], bool]) -> bool:
        try:
            changed = fn()
        except Exception:
            _log(f"module:{label} ERROR (skipped this pass)\n{traceback.format_exc()}")
            changed = False
        manifest.save()
        return changed

    tasks: list[tuple[str, Callable[[], bool]]] = []

    for name, fetch_fn in FETCH_MODULES.items():
        tier = tiers.module_tier(name)
        last_run = state.last_run_monotonic.get(name)
        if tiers.is_due(last_run_monotonic=last_run, now_monotonic=now_mono, tier=tier):
            state.last_run_monotonic[name] = now_mono
            tasks.append((
                name,
                lambda name=name, fetch_fn=fetch_fn: _run_module(name, fetch_fn, manifest, base_dir),
            ))

    hurricanes_due = (
        state.last_hurricanes_run_monotonic is None
        or (now_mono - state.last_hurricanes_run_monotonic) >= HURRICANES_CADENCE_SECONDS
    )
    if hurricanes_due:
        state.last_hurricanes_run_monotonic = now_mono
        tasks.append(("hurricanes", lambda: hurricane_sources.poll(hurricanes_base_dir)))

    data_changed = False

    if tasks:
        _log(f"dispatching {len(tasks)} due task(s) concurrently: {', '.join(t[0] for t in tasks)}")
        with ThreadPoolExecutor(max_workers=min(len(tasks), MAX_CONCURRENT_MODULES)) as pool:
            futures = [pool.submit(_run_and_save, label, fn) for label, fn in tasks]
            for f in futures:
                data_changed = f.result() or data_changed

    reports_root = Path(base_dir).parent / "reports"
    reports_dir = reports_root / weather_reports.LEVEL0_DIRNAME
    aggregate_path = reports_dir / weather_reports.AGGREGATE_FILENAME
    county_root = reports_root / county_reports.LEVEL1_DIRNAME
    county_missing = not county_root.is_dir() or not any(county_root.glob("*_County_Weather_Report_current.md"))
    official_root = reports_root / official_reports.OFFICIAL
    official_missing = not official_root.is_dir() or not any(official_root.glob("*/*_current.md"))
    if data_changed or not aggregate_path.is_file():
        try:
            weather_reports.generate(base_dir)
            _log("reports: regenerated Level 0 statewide Markdown reports")
            data_changed = True
        except Exception:
            _log(f"reports ERROR\n{traceback.format_exc()}")
    # Preserve official-source mirrors before any geographic processing.
    # Level 1 may consume these authoritative source-isolated records.
    if data_changed or official_missing:
        try:
            official_reports.generate(base_dir)
            _log("reports: updated source-isolated official report mirrors")
        except Exception:
            _log(f"official reports ERROR\n{traceback.format_exc()}")
    if data_changed or county_missing:
        try:
            county_reports.generate(base_dir)
            _log("reports: regenerated Level 1 county Markdown reports")
        except Exception:
            _log(f"county reports ERROR\n{traceback.format_exc()}")

    try:
        _check_midnight_rollover(state, base_dir)
    except Exception:
        _log(f"midnight_rollover ERROR\n{traceback.format_exc()}")


def _check_midnight_rollover(state: SchedulerState, base_dir: str) -> None:
    """Fires archive/consolidate.py exactly once per HST calendar-date
    rollover, per nws_plan.md Section 8 / core/hst_time.is_new_hst_day.
    """
    from archive import consolidate

    now_hst = hst_time.hst_now()
    today_folder = hst_time.hst_date_folder(now_hst)

    if state.last_seen_hst_date is None:
        state.last_seen_hst_date = today_folder
        return

    if today_folder != state.last_seen_hst_date:
        yesterday_folder = state.last_seen_hst_date
        consolidate.consolidate_yesterday(base_dir, yesterday_folder)
        state.last_seen_hst_date = today_folder


def run_forever(base_dir: str, hurricanes_base_dir: str, *, tick_seconds: float = 30.0) -> None:
    """The long-running loop `weather`'s SKILL.md describes ("not a
    conversation-triggered skill -- it runs continuously/on-cron"). Ticks
    every `tick_seconds` and lets `run_once` decide what's actually due;
    the tick interval just needs to be shorter than the fastest cadence
    (Tier 0's 60s), 30s comfortably clears that with margin for jitter.

    The first tick fires immediately (no sleep before it) -- so starting
    this process is itself "one full fetch pass on boot", with every
    module's `last_run_monotonic` starting as `None` (= always due, per
    `tiers.is_due`). Ongoing cadence after that is handled entirely by
    `run_once`/`tiers.py`; this loop does not need its own first-run
    special case.

    Top-level try/except per tick is a last-resort safety net beyond the
    three phase-level guards inside `run_once` itself (Manifest.load/save
    failing outright, e.g. a corrupt manifest file, is the kind of thing
    this catches) -- the process logs and keeps ticking rather than dying,
    since this is meant to run unattended.
    """
    _log(f"weather scheduler starting -- base_dir={base_dir} hurricanes_base_dir={hurricanes_base_dir}")
    state = SchedulerState()
    while True:
        try:
            run_once(state, base_dir, hurricanes_base_dir)
        except Exception:
            _log(f"run_once ERROR (tick skipped)\n{traceback.format_exc()}")
        time.sleep(tick_seconds)
