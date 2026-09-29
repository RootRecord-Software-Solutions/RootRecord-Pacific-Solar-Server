# alerts/

**Owns:** the processing stage that turns raw alert JSON (from
`fetch/alerts.py`) into structured, county-mapped, deduped alert data:

- `county_map.py` — SAME/UGC → county key, plus area-text regex fallback when
  geocodes are missing. Ported from the old `nws-hawaii` module's approach.
- `severity.py` — tags extreme/severe vs routine, isolated so the threshold
  can change without touching parsing.
- `dedupe.py` — event+county dedupe, keep-newest-sent logic.

**Does NOT own:** fetching. `fetch/alerts.py` calls `api.weather.gov`; this
folder never makes an HTTP request. **Does NOT own:** tropical-cyclone alert
narration — that's `hurricanes/scripts/narration.py`, which has a different
input shape (NHC/CPHC advisories, not `api.weather.gov` alert JSON).

**Depends on:** `config/counties.yaml`, raw alert JSON from `fetch/alerts.py`.
