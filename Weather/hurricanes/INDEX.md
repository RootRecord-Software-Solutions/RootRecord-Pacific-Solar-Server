# hurricanes — index

Tropical cyclone sub-skill of `weather/`. See `SKILL.md` for what it is and
how it fires; see `references/sources.md` for endpoint notes.

| Path | Role |
| --- | --- |
| `scripts/sources.py` | NHC `CurrentStorms.json` baseline poll, relevance filter, per-storm `track.json` updates. `poll()` is the entry point `scheduler/run_cycle.py` calls. |
| `scripts/distance.py` | The 800nmi-from-Hawaii (or CPHC-advisory-regardless-of-distance) relevance rule, isolated and independently testable. |
| `scripts/narration.py` | Builds a plain-language "toward/away, lat/lon, ocean region" summary from a storm's accumulated `track.json` — text only, no I/O. |
| `references/sources.md` | NHC/CPHC/RAMMB/JTWC endpoint notes; which sources are live vs. not-yet-confirmed. |

Data this sub-skill reads/writes lives entirely under
`Database/WEATHER/Hawai'i/hurricanes/tracking/<storm_name>_<TIMESTAMP>/` —
see `SKILL.md`'s "Data placement" note. Nothing under this folder itself
holds fetched data.
