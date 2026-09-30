# CountryLocations

One poller for country and city weather on the one Vercel site. It replaces the 306 identical `operations/locations/**/poller.py` copies. It does not replace the Hawaiʻi weather poller, and it does not collect the US-states dataset.

The public page is `/locations` on the one Vercel app. It reads `locations-last.json`. United States places stay on `/us-states`.

An empty `config/allowlist.json` means the non-US rows in `Geology/config/global-locations.json` (229 places). A non-empty allowlist restricts to those ids. There is no archive backfill. A run skips Open-Meteo when `locations-last.json` is under 55 minutes old. `--force` is the only way to fetch again.

One current fetch finished 2026-09-30 01:07 HST: 229 places, 229 temperatures. The scheduled job stays `enabled: False`.

Job `country_location_pollers` in `jobs.py` is `enabled: False`. `RR_COUNTRY_LOCATIONS` stays unset.

| Role | Path |
| --- | --- |
| Code | `Weather/CountryLocations/scripts/poll_locations.py` |
| Database | `2 - RootRecord-Database/Weather/CountryLocations/` |
| Logs | `2 - RootRecord-Database/Logs/Weather/CountryLocations/` |
| Archive | `Old repos deleted and merged/old/operations/locations/` (612 files). GitHub `old` commit `fe6661a`. |
