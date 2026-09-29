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
| Local data | `/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/WEATHER/Hawai'i/` (git-ignored in Database; old dataset archived under `Archive/Previous-Datasets/G2-old-root-20260929/WEATHER/`) |
| Growth watch | ~17 MB observed over 8 minutes during the post-import pass (~3.1 GB/day if sustained); retention rule is a future maintenance item |

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

---

*Updated 2026-09-29 HST — current reports passing; growth under watch.*
