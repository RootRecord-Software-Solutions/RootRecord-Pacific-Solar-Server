# CountryLocations

One poller for country and city weather on the one Vercel site. It replaces the 306 identical `operations/locations/**/poller.py` copies. It does not replace the Hawaiʻi weather poller, and it does not collect the US-states dataset.

`config/allowlist.json` lists only locations that the checked-out site actually routes as a country or city page. Rechecked 2026-09-30 00:39 HST: `3 - RootRecord-Website/src/app/` has `/`, `/us-states`, `/status`, `/reports`, `/blog`, `/goals`, `/login`, `/dev`, `/timeline`, `/clients`, `/fern-forest`, `/pantry`, and `/product-prices`. None of those is a country or city route. `/us-states` belongs to `Weather/US-States` (WO-MIG-11) and reads `Weather/US-States/us-last.json`. State and global news (WO-MIG-12) stay under `Reports/News/`. The allowlist stays `[]`.

An empty allowlist exits 0, writes a status file, and does not call Open-Meteo. There is no archive backfill. Recheck 2026-09-30 00:39 HST: exit 0, `locations` 0, `http_calls` 0.

Job `country_location_pollers` in `jobs.py` is `enabled: False`. `RR_COUNTRY_LOCATIONS` stays unset.

| Role | Path |
| --- | --- |
| Code | `Weather/CountryLocations/scripts/poll_locations.py` |
| Database | `2 - RootRecord-Database/Weather/CountryLocations/` |
| Logs | `2 - RootRecord-Database/Logs/Weather/CountryLocations/` |
| Archive | `Old repos deleted and merged/old/operations/locations/` (612 files). GitHub `old` commit `fe6661a`. |
