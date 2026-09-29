# Tropical cyclone data sources — reference notes

## NHC — confirmed, primary trigger
- `https://www.nhc.noaa.gov/CurrentStorms.json` — full JSON of every active
  tropical cyclone worldwide (NHC + JTWC coverage areas). This is the
  cleanest possible answer to "is anything active right now, anywhere CPHC
  might care about" — no prose parsing required. `scripts/sources.py` polls
  this first, every cycle, regardless of whether a storm is currently being
  tracked.

## CPHC — confirmed, per-storm advisories
Pulled via the same api.weather.gov structured products API used by the rest
of `weather/`'s text products (not a special-cased HTTP path):
- `https://api.weather.gov/products/types/TCM/locations/HFO` — Forecast/Advisory
- `https://api.weather.gov/products/types/TCP/locations/HFO` — Public Advisory
- `https://api.weather.gov/products/types/TCD/locations/HFO` — Discussion
- `https://api.weather.gov/products/types/TCU/locations/HFO` — Position Update
- `https://api.weather.gov/products/types/HLS/locations/HFO` — Local Statement (impacts/evacuations)

AWIPS ID pattern for the above is `{TYPE}CP1` through `{TYPE}CP5` (up to 5
concurrent CPHC-numbered systems) — the products API abstracts this away by
always returning the *latest* of each type for HFO, so `scripts/sources.py`
doesn't need to enumerate CP1-5 by hand.

Also confirmed:
- `https://www.nhc.noaa.gov/gtwo.php?basin=cpac&fdays=5` — Tropical Weather Outlook
- `https://www.nhc.noaa.gov/text/HFOTWSCP.shtml` — Monthly Tropical Weather Summary
- `/hfo/TCSNP`, `/hfo/TCSSP` — satellite-fix summaries (Central/South Pacific)
- `https://www.weather.gov/cphc/` — CPHC landing page

## RAMMB / JTWC — reserved, not yet confirmed
`config/hosts.yaml` (parent skill) has placeholder rate-floor entries for
`www.cpc.ncep.noaa.gov` and `www.metoc.navy.mil` (JTWC) — hosts and exact
paths are not yet confirmed for these. Do not enable `scripts/sources.py`
calls to either until a specific, tested URL is added here. RAMMB imagery in
particular would likely belong in `fetch/satellite.py`-style handling rather
than this sub-skill, if it turns out to be per-sector imagery rather than
storm-specific data — revisit once confirmed.

## The 800nmi relevance rule
A storm anywhere in the world is *tracked* (`CurrentStorms.json` sees it),
but only *escalated* to per-storm TCM/TCP/TCD/TCU polling and given a
`Database/WEATHER/.../tracking/<storm>/` folder when either:
1. its current position is within 800 nautical miles of Hawaii (roughly the
   radius at which a system's forecast cone could plausibly reach the
   islands within the standard 5-day NHC forecast window), or
2. it already carries a CPHC advisory number (i.e. NHC/CPHC has already
   judged it in-area, regardless of raw distance).

This threshold is a single function in `scripts/distance.py` — isolated so
the number itself can be revisited without touching the polling loop or the
JSON-parsing logic around it.
