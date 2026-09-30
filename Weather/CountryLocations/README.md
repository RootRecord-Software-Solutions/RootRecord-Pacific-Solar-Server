# CountryLocations

One poller for country and city weather on the one Vercel site. It replaces the 306 identical `operations/locations/**/poller.py` copies. It does not replace the Hawaiʻi weather poller.

`config/allowlist.json` lists only locations that checked-out site actually routes. It is `[]` until public website checkout exists and names a route. An empty allowlist exits 0, writes a status file, and does not call Open-Meteo. There is no archive backfill.

Job `country_location_pollers` in `jobs.py` is `enabled: False`. `RR_COUNTRY_LOCATIONS` stays unset.

| Role | Path |
| --- | --- |
| Code | `Weather/CountryLocations/scripts/poll_locations.py` |
| Database | `2 - RootRecord-Database/Weather/CountryLocations/` |
| Logs | `2 - RootRecord-Database/Logs/Weather/CountryLocations/` |
