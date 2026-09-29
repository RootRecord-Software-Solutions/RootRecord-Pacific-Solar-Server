# Weather

Weather subsystem ownership: collection, ensure scripts, and related desk weather services.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Partial** — ensure scripts |
| Full daemon | G2 / residual skills path |
| G1 Old packets | `weather/live-wx`, `nws-hawaii`, `rr-noaa`, `hurricane-*`, `radar-archive`, … |
| Published data | `RootRecord-Weather-Database` |
| Local data | Database weather staging (not this git tree) |

**Import order:** G2 weather daemon/ensure alignment first; then selective G1 packets (skip bulk media archives into git).

---

## jobs.py

| Job id | Path note |
| --- | --- |
| `weather_poller` | skills-prefixed absolute; ensure also in-repo under `Weather/scripts/` |

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

*Docs-only 2026-09-28 HST.*
