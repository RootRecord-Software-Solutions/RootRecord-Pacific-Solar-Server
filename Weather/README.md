# Weather

Weather subsystem ownership: collection, ensure scripts, and related desk weather services.

---

## Status (2026-09-29 HST)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Imported** — G2 weather daemon copied here 2026-09-29 (G2 copy kept) |
| Full daemon | Pacific `Weather/scripts/run_poller.py`, venv `Weather/.venv` (git-ignored, `requirements.txt`), job `weather_poller` enabled |
| Latest verification | **PASS** — statewide and county reports generated at ~01:59 HST; solar calculation table present for viewer sunrise/sunset consumption |
| Runtime | One Weather process observed running; no errors reported in the verification pass |
| Published data | `RootRecord-Weather-Database` |
| Local data | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Weather/Hawai'i/` (git-ignored in Database; old dataset archived under `Archive/Previous-Datasets/G2-old-root-20260929/WEATHER/`) |
| Growth watch | 320 MB at 02:44 HST (207 MB 01:54, 227 MB 02:07). The early ~2.5 MB/min was mostly first fetches of overwrite-in-place `_current` imagery (GOES19 EEP ~13–15 MB each); steady growth is the dated `archive/` copies ≈ 0.16 MB/min (≈ 0.23 GB/day). Retention: PROPOSED below |

**Import order:** G2 weather daemon/ensure alignment first; then selective G1 packets (skip bulk media archives into git).

---

## jobs.py

| Job id | Path note |
| --- | --- |
| `weather_poller` | ON_BOOT, enabled 2026-09-29 → Pacific `Weather/scripts/ensure-weather-poller.sh` |

---

## G1 packets (after G2)

| Packet | Note |
| --- | --- |
| live-wx, nws-hawaii, rr-noaa | Core collectors |
| hurricane-desk, -fetch, -obs, -radio, -tracker | Storm tooling |
| radar-archive, official-weather-media | Prefer Database / Weather-Database, not G3 bloat |

---

## Layout

```text
Weather/
  README.md
  scripts/
    ensure-weather-poller.sh
    # daemon, collectors after import
```

---

## Retention

Weather data is intentionally retained in the Database tree rather than Git. The current growth rate is acceptable for the present disk headroom, but a retention/archival rule should be added before the dataset becomes a multi-month accumulation.

### PROPOSED retention policy (2026-09-29 02:50 HST — not applied; needs Alexander sign-off)

Measured at 02:44 HST: `Weather/Hawai'i` = 320 MB. `hfo/cdn.star.nesdis.noaa.gov` (GOES imagery) is 198 MB, `hfo/weather.gov` 104 MB, `reports` 12 MB. There are 282 `*_current*` files (220 MB, overwritten in place) and 550 dated `archive/` files (95 MB, growing ≈ 0.16 MB/min).

| Class | Where | Proposed rule |
| --- | --- | --- |
| `*_current*` snapshots | every resource folder | keep (overwritten in place; plateaus once each product is fetched once) |
| Dated text/HTML archives | `*/archive/MM-DD-YYYY/`, `*/raw/archive/…` | existing daily zip at HST rollover (`archive/consolidate.py` → `core/daily_zip.py`; verify the first run after 00:00 HST 2026-09-30); keep zips 90 days locally |
| Imagery archives | GOES / radar / IR-loop `archive/` | keep 14 days of dated folders/zips locally |
| Generated reports | `reports/*/archived/` | keep 30 days |
| Hurricanes | `hurricanes/` | keep all (small, high value) |
| Daemon log | `logs/weather-poller.log` | rotate at 10 MB × 5 |
| Older than the windows | — | **move** (never delete) to `2 - RootRecord-Database/Archive/Previous-Datasets/Weather-<YYYYMM>/` or the RootRecord-Weather-Database repo; deletion only with Alexander sign-off |
| Budget alarm | — | WARN when `Weather/` > 20 GB or disk free < 50 GB |

---

*Updated 2026-09-29 HST — current reports passing; growth under watch.*
