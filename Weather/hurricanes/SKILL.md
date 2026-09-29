# hurricanes (sub-skill of weather)

**What it is:** the tropical cyclone subsystem for CPHC's area of
responsibility. Pulls NHC `CurrentStorms.json`, CPHC TCM/TCP/TCD/TCU
advisories, and (once confirmed) RAMMB/JTWC sources; tracks each storm's
position history and forecast cone under
`Database/WEATHER/Hawai'i/hurricanes/tracking/`; and narrates plain-language
storm summaries.

**How it fires:** on its own schedule, independent of the rest of `weather/`
-- see `DAILY.md`. `scheduler/run_cycle.py` dispatches into
`hurricanes/scripts/` the same way it dispatches into `fetch/`.

**Relevance filter:** a storm is tracked only while it's within 800nmi of
Hawaii (see `scripts/distance.py`) or is a named CPHC-area system regardless
of distance. This matches the old system's threshold, isolated here as a
single testable function instead of being buried in a general-purpose file.

**Data placement:** 100% in the database, no exception --
`Database/WEATHER/Hawai'i/hurricanes/tracking/<storm_name>_<TIMESTAMP>/`
holding `track.json`, `forecast_cone.json`, and `sources/`. See this
sub-skill's `references/sources.md` for endpoint notes.

**Public-database note:** this tree is intended to eventually be public. No
API keys, internal hostnames, or credentials belong in anything under
`Database/WEATHER/` -- see `config/hosts.yaml` in the parent skill's code
tree if a key is ever needed for a source here.
