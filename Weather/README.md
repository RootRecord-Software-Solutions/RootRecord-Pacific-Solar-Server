# Weather

Weather subsystem ownership: collection, ensure scripts, and related desk weather services.

---

## Status (2026-09-28)

| Item | State |
| --- | --- |
| Domain folder in this repo | **Partial** — `scripts/ensure-weather-poller.sh` (+ sync helpers if present) |
| Full weather daemon | May still live under legacy skills / Weather tree outside this partial copy |
| Published data | `rootrecordsoftwaresolutions/RootRecord-Weather-Database` |
| Local data | Database weather staging (not in this git tree) |

---

## jobs.py references

| Job id | Path note |
| --- | --- |
| `weather_poller` | Command points at `…/skills/Weather/scripts/ensure-weather-poller.sh` (skills-prefixed absolute); ensure script also exists under this domain in-repo |

After full daemon import, align absolute job strings to Ecosystem Servers path.

---

## Layout

```text
Weather/
  README.md
  scripts/
    ensure-weather-poller.sh
    # future: daemon, collectors
```

---

*Docs-only update 2026-09-28 HST.*
