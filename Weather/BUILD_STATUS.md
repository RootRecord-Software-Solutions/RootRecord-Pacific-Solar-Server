# Build Status

Tracks progress against `weather_skill_architecture.md` so a new agent session
can pick up exactly where the last one stopped. Update this file at the end of
every checkpoint.

## Checkpoints

- [x] **Foundation** — top-level layout, every folder's `README.md`, top-level
      `SKILL.md`.
- [x] **first scan** — `config/*.yaml` populated from `NWS_Hawaii_Resource_Map.md`.
- [x] **continued building** — all of `core/`, `fetch/` (11 modules incl.
      `_engine.py`), `alerts/` (3 modules), `hurricanes/` (3 scripts +
      docs), `scheduler/`, `archive/consolidate.py`. Dispatch loop wired
      end to end.
- [x] **cleanup phase — tests written AND run for real.** This session had no
      network either (same sandbox restriction as before — `pip install`
      and any live host, including `api.weather.gov`, both come back
      `403 host_not_allowed`), so `pytest`/`httpx` still aren't installed.
      But **none of the actual test files use any pytest-only feature**
      (no fixtures, no `@pytest.mark`, no `monkeypatch`, no `tmp_path` —
      confirmed by grep) — they're plain `assert`-based `test_*` functions.
      That means they run correctly under a ~40-line stdlib-only runner
      with no third-party deps at all. Ran that way, for real, this
      session:
      - `tests/core/` (8 files, 33 tests) — **all pass**
      - `tests/alerts/` (3 files, 12 tests) — **all pass**
      - `tests/hurricanes/` (2 files, **new this session**, 20 tests) —
        **all pass**, covering `distance.py`'s haversine math + 800nmi
        relevance rule, and `narration.py`'s ocean-region classification +
        toward/away bearing trend + full `narrate()` output.
      - `tests/scheduler/` (1 file, **new this session**, 3 tests) — **all
        pass**, covering `run_once`'s per-tier dispatch (due vs. not-due),
        the hurricanes-cadence branch, and `_check_midnight_rollover`
        firing exactly once per HST-date change (not on repeat ticks
        within the same day, not on ticks within the new day either).
      - `tests/fetch/` (1 file, **new this session, added after the two
        open items were resolved**, 2 tests) — **all pass**, targeting the
        `ndfd_gridpoint.fetch_all()` config-reading bug described below.
      - **68/68 tests passing, 0 failed, 0 errored.**
      - Separately, a full import-level cross-check of all 30 non-test
        `.py` modules (`core`, `fetch`, `alerts`, `hurricanes/scripts`,
        `scheduler`, `archive`) against a stub `httpx` — **30/30 import
        cleanly**, and every contract function named in `nextagent.md`
        Section 5 (`change_detection.detect`/`sha256_of`,
        `archiver.age_out_and_write`, `validators.*`, `text_cleaner.*`,
        `county_map.county_keys_for_alert`, `severity.severity_rank`/
        `is_critical`/`is_routine`, `dedupe.dedupe_by_event_and_county`,
        `hurricanes.scripts.sources.poll`) still matches its documented
        signature exactly — re-verified by `grep -n "^def "` against each
        file, not inferred from docstrings.
      - **Real bug found and fixed:** `hurricanes/scripts/narration.py`'s
        `_ocean_region()` mislabeled every positive longitude below 180
        (e.g. 170, a genuinely Western-Pacific position near Guam/the
        Philippines) as "Eastern Pacific", because the original condition
        only matched `lon <= -180` for the Western-Pacific case and never
        handled the positive-longitude side of the basin at all. Fixed;
        regression test is
        `tests/hurricanes/test_narration.py::test_ocean_region_western_pacific_positive_longitude_regression`.
      - Still not done: dead/duplicate-logic diff vs. the old flat skills.
      - File-count sanity check (`nextagent.md` Section 9) still holds:
        41 `.py`, 5 YAML, 14 doc files. Test file count is now 14 (was 11).
- [ ] **verified deployment ready** — still genuinely blocked on network
      access, same as last session: no live call has been made against
      `httpx` or any real NWS endpoint from inside a build sandbox. This
      is an environment limitation, not something the next session should
      assume is now fine because everything else got verified — it isn't
      the same kind of gap as "wasn't tried yet." Manifest/archiving/
      change-detection logic IS now genuinely verified (real test run,
      not just import checks). Deployment checklist not started.

## Resolved this session (were open items in the previous handoff)

- **Hurricanes polling cadence**: user confirmed keeping `900.0` (15 min)
  as the real value, not a placeholder. `scheduler/run_cycle.py`'s comment
  updated to reflect this is now settled.
- **`fetch/ndfd_gridpoint.py` coordinate list**: user chose the four ICAO
  stations already used elsewhere in `config/resources.yaml`
  (`HNL, LIH, OGG, ITO`). Added as `ndfd.items[0].points` with standard
  published airport reference-point coordinates.
  - **Second real bug found and fixed while wiring this up**:
    `fetch_all()` read `config["ndfd"]["items"]` as if it were a dict and
    called `.get("points")` on it directly — but `items` is a LIST
    (one dict per resource entry, matching every other category in the
    file), so `isinstance(..., dict)` was always False and `fetch_all()`
    returned `[]` unconditionally, even once a real `points` key existed.
    Fixed to look up the `points_resolver` entry inside the list. Covered
    by new `tests/fetch/test_ndfd_gridpoint.py` (2 tests, both pass),
    including a regression test using the exact nested shape the real
    config file has. Manually re-verified against the real
    `config/resources.yaml` (not just the test's fake config) — the fixed
    `fetch_all()` correctly finds all 4 points.
  - `fetch/ndfd_gridpoint.py` is otherwise unchanged: `resolve_gridpoint()`
    still needs a real (networked) call to actually resolve these 4 points
    to NDFD forecast URLs and confirm they're valid — that's part of the
    still-open live-HTTP verification item below, not solved here.

## Known open items (flagged in code, not silently resolved)

- **Scheduler dispatches per fetch-module, not strictly per-resource** —
  unchanged, documented as a deliberate simplification in
  `scheduler/tiers.py`'s own docstring.
- **`hurricanes/DAILY.md`** — still a template/stub, unchanged.
- Text-cleaning raw-copy question and daily-zip retention policy
  (`nws_plan.md` Section 9, open items 1 and 3) — still open, unchanged.
- **api.weather.gov product bodies**: some stored product captures contain
  metadata only (no `productText`). Report generation now falls back to a
  compact metadata summary instead of dumping opaque JSON, but the fetch
  layer should eventually store the full product detail payload when the
  listing endpoint does not include text.

## Next steps for whoever continues this

1. **Get real network access** (this is the actual blocker, not a to-do
   this session skipped) — install `pytest`+`httpx` for real and re-run
   the suite one more time as a final sanity check (should be a no-op
   given the stdlib-runner results above, but worth doing once), then make
   one live `http_client.get("https://api.weather.gov/alerts/active?area=HI")`
   call to validate the rate-floor/conditional-GET logic against reality.
2. Resolve the two items above that need user input (hurricanes cadence,
   NDFD coordinate list) — both are product decisions, not code gaps.
3. Cleanup pass: dead/duplicate logic vs. the old flat skills.
4. Full deployment checklist (not scoped yet — see `nextagent.md` Section 10
   step 6 for what "deployment ready" probably needs to mean here).
5. Run one full report-generation cycle on the live host so
   `RootRecord-Weather-Database` publishes the processed README banner
   under `Hawai'i/reports/assets/` and regenerates both READMEs from the
   updated templates.

## Source material this build is derived from

- `weather_skill_architecture.md` / `nws_plan.md` / `NWS_Hawaii_Resource_Map.md`
- Old flat skills (see `nextagent.md` Section 8)

## Notes for the next agent

- Base data directory: `/home/rootrecord/Database/WEATHER/Hawai'i/hfo`
- Base code directory: `/home/rootrecord/.ollama/skills/weather/`
- Nothing in this tree should ever write a fetched file into itself —
  always into the Database tree above.
- **If your sandbox also has no network**: don't assume you're stuck. Check
  whether the test files actually need pytest-only features before
  concluding you can't run them (`grep -rl "tmp_path\|monkeypatch\|@pytest\|fixture" tests/`)
  — if they're plain `assert`-based functions, a tiny stdlib runner (see
  this session's approach) runs them for real. Only the `httpx`-touching
  paths (real live HTTP calls) are genuinely blocked without network; pure
  logic isn't.


## 2026-09-25 — source-isolated official preservation

Implemented a preservation layer distinct from processing levels:

- Added `reports/official_generator.py`.
- Official readable products are mirrored under
  `reports/Official Sources/<source>/`.
- Current source groups include NWS-HFO, NHC, NOAA, and NOAA-NESDIS.
- Each source owns its own `archived/` directory and current/archive lifecycle.
- Level 0 and Level 1 remain processing layers and are not replaced by the
  official-source layer.
- Exact fetched source bytes remain in the URL-mirrored raw data tree.
- Scheduler now updates the official-source layer whenever fetched data
  changes or the source layer is missing.
- NWS GIS catalog pages are now retained as official source artifacts in
  addition to the versioned ZIP/DBX datasets selected from them.
- GIS artifact selection now understands NWS `ddmonyy` version dates instead
  of relying on catalog link ordering.
- Hawaii Level 1 county routing now has explicit SAME/HIC codes:
  HIC001 Hawaii, HIC003 Honolulu, HIC005 Kalawao, HIC007 Kauai, HIC009 Maui.
- Added tests for county UGC routing and official source grouping.

Authoritative NWS GIS sources confirm that public forecast zones are polygon
data and may be subsets of counties, while the Zone/County correlation file
provides the county/FIPS relationship. The current Level 1 routing therefore
has an authoritative UGC/zone-correlation path before text/resource fallbacks.


## 2026-09-25 — provenance cleanup and test-harness clarification

- Corrected official-source classification for legacy relative NWS URLs such as `/hfo/surfreports` and `/hfo/FTM`: these normalize to `NWS-HFO` instead of `unknown-source`.
- Added the `NOAA-GML` source group for `gml.noaa.gov` products, keeping those records separate from generic `NOAA` material.
- Added regression tests for both source-classification boundaries.
- Corrected Level 1 provenance wording: county reports can use a matching Official Sources record directly, with Level 0 as the fallback processing-layer input. Level 1 therefore records the actual `Source layer` rather than claiming every record is derived only from Level 0.
- Confirmed unresolved geography is a safety boundary: unresolved products are preserved under `1 County Processing/unresolved/` and are excluded from county directories and county aggregates. Only explicitly statewide resources are copied to every county.
- The stdlib test runner now suppresses scheduler logging while tests execute. The scheduler's production error handling is unchanged; expected smoke-test exceptions remain asserted by the tests, but their intentional log tracebacks no longer clutter the test summary.
- The current verified test baseline immediately before this documentation checkpoint was **82/82 passing, 0 failed, 0 errored**. A fresh run should be performed after these latest test-harness/source-provenance commits.
- NWS GIS provenance remains grounded in the current official Zone/County correlation and Public Forecast Zone datasets. NWS documents that public zones can be county subsets, while the correlation file provides county/FIPS relationships.


## 2026-09-25 — live README reporting

- The repository README at `weather/reports/README.md` is now generated by the Level 0 statewide report generator.
- Each report generation cycle rebuilds the README from the same current product sections used by `Hawaii_State_Weather_Report_current.md`, so the README cannot become a separately maintained/stale copy of the statewide report.
- The README is a presentation layer: official-source records and raw data remain preserved separately, while the README provides the current human-readable statewide view.
- This is intentionally local-first. Updating the README on disk does not itself imply a Git push; publication/synchronization can be added separately without coupling data generation to Git operations.


## 2026-09-25 — README / banner alignment fix

Problem found during review:

- Live `RootRecord-Weather-Database` README was long-form (status table +
  full statewide sections) and used the **raw** GOES-18 GIF.
- Templates had been reduced to short-form (`CURRENT_CONDITIONS` only).
- `generator.py` only replaced `CURRENT_CONDITIONS` and `README_BANNER_URL`,
  so it could no longer reproduce the published long-form README.
- Processed banner logic in `banner.py` existed, but the published README
  did not use `Hawai'i/reports/assets/GOES18-HI-GEOCOLOR-README-banner.gif`.

Fixed:

- `WEATHER_DATABASE_README_TEMPLATE.md` and `README_TEMPLATE.md` restored to
  long-form with placeholders:
  `README_BANNER_URL`, `CURRENT_CONDITIONS`, `REPORT_UPDATED`,
  `REPORT_SECTION_COUNT`, `REPORT_SECTIONS`.
- `generator.py` now builds and injects the full statewide section body,
  status fields, current-conditions table, and processed banner URL.
- Banner generation still never modifies the raw GOES product; on banner
  failure the generator falls back to the raw collected current GIF URL.
- JSON product extraction prefers `productText`; metadata-only captures get
  a compact readable summary instead of a raw JSON dump.
- Added `tests/reports/test_generator_readme.py` for placeholder rendering.

**Required on the live host (not done from this sandbox):** run one report
generation cycle so the weather database publishes the processed banner
asset and regenerates both READMEs from the fixed pipeline.
