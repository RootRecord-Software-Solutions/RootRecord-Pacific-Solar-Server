# Weather (Pacific desk)

Pacific-side **Weather domain**: Database-facing jobs and small standalone scripts. **Hawaiʻi internet fetch** runs on ML2 only (`vendor/Weather/` + `weather_hawaii` → `ml2_db_stream`).

---

## Status (2026-10-02 HST)

| Item | State |
| --- | --- |
| Hawaiʻi fetch / scheduler daemon | **ML2 only** — Pacific `run_poller.py`, ensure script, and duplicate `fetch/` + `scheduler/` tree **removed** 2026-10-02 |
| Canonical collect code | `1 - Servers/3 - RootRecord-US-Mainland-Two/vendor/Weather/` |
| Database tree | `2 - RootRecord-Database/Weather/` (git-ignored; stream + local jobs write here) |
| ML2 → Pacific delivery | **OPEN** — see Desktop `Manual Audit Documentation/07-ml2-ssh-stream-needs-work.md` when tunnel is down |

---

## jobs.py (Pacific)

| Job id | Script |
| --- | --- |
| `weather_radar_zip` | `Weather/RadarZip/scripts/radar_zip.py` |
| `country_location_pollers` | `Weather/CountryLocations/scripts/poll_locations.py` (disabled; empty allowlist) |
| `weather_us_states` | `Weather/US-States/scripts/fetch_us_states.py` (gated when ML2 owns US-States stream) |
| `weather_retention` | `Weather/scripts/weather-retention.py --dry-run` (disabled) |
| *(removed)* | `weather_poller` — 2026-10-02 |

PROPOSED / gated ports (not in active ON_BOOT): `scripts/official_statement.py` (HLS), historical G1 hurricane board — implement on ML2 vendor or re-add Pacific scripts from git if needed.

---

## Layout (Pacific repo)

```text
Weather/
  README.md
  config/          # legacy YAML; Settings registry; ML2 vendor holds the live copy for fetch
  scripts/
    weather-retention.py
    official_statement.py
    sync-weather-database.sh
  RadarZip/
  CountryLocations/
  US-States/
```

---

## Retention

Policy and job: `scripts/weather-retention.py` (dry-run until Alexander reviews). See prior README history in git for growth tables and archive rules.
