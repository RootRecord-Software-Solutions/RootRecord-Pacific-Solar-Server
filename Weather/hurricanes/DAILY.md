# hurricanes — daily-cadence notes

Matches the old flat-skill convention of keeping a running daily note
alongside the code (see the superseded `weather/hurricane-tracker/DAILY.md`
under the old system, referenced from this tree's `BUILD_STATUS.md`). This
folder still runs on its own cadence even when the rest of `weather/` is
idle, per `SKILL.md`.

**Not backfilled with fabricated entries here** — the old file's content
was a live operational log (hybrid daily-report timestamps, real storm
positions) written by the running system, not authored by hand. This file
is the template that log gets written into once `scheduler/run_cycle.py`
is actually running against `hurricanes/scripts/sources.py`'s `poll()`
output; it stays empty in the code tree itself, per
`weather_skill_architecture.md`'s "code and data are two different trees"
rule — no exception for this file just because the old convention put
similar-looking notes next to the code.

## Pending

- Confirm the actual cadence this sub-skill should poll at (see
  `scheduler/run_cycle.py`'s `HURRICANES_CADENCE_SECONDS` — currently a
  15-minute placeholder, not yet confirmed against any plan document).
- Decide whether this file should be hand-maintained prose notes (like the
  old system) or an auto-appended log from `poll()`, and wire that up.
