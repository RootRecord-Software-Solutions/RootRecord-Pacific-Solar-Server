# scheduler/

**Owns:** cadence + dispatch only.

- `tiers.py` — reads `config/tiers.yaml`, decides what's due to run right now
  for each tier (0–6).
- `run_cycle.py` — the actual dispatch loop: calls into `fetch/`, `alerts/`,
  and `hurricanes/` on their respective schedules.

**Does NOT own:** any fetch logic of its own. If `run_cycle.py` starts making
HTTP calls directly, that's a boundary violation — it should only ever call
into `fetch/*.py`, `alerts/*.py`, or `hurricanes/scripts/*.py` entry points.

**Depends on:** `config/tiers.yaml`, `core/hst_time.py` (for the HST-midnight
trigger that also drives `archive/consolidate.py`), every module under
`fetch/`, `alerts/`, `hurricanes/`.
