# hurricanes — index

Tropical cyclone sub-skill of `weather/`. See `SKILL.md` for what it is and
how it fires; see `references/sources.md` for endpoint notes.

| Path | Role |
| --- | --- |
| `scripts/sources.py` | NHC `CurrentStorms.json` baseline poll, relevance filter, per-storm `track.json` updates. `poll()` is the entry point `scheduler/run_cycle.py` calls. |
| `scripts/global_board.py` | Worldwide board: NHC + RAMMB index + JTWC, then each kept storm's RAMMB page (IR URL, track tables). |
| `scripts/storm_track.py` | RAMMB history and forecast tables, motion vs Hawaiʻi, `storm-tracks.json`. |
| `scripts/storm_plot.py` | Text plot of the nearest Hawaiʻi storm, `storm-plot.txt`. |
| `scripts/distance.py` | The 800nmi-from-Hawaii (or CPHC-advisory-regardless-of-distance) relevance rule, isolated and independently testable. |
| `scripts/narration.py` | Builds a plain-language "toward/away, lat/lon, ocean region" summary from a storm's accumulated `track.json` — text only, no I/O. |
| `references/sources.md` | NHC/CPHC/RAMMB/JTWC endpoint notes. `sources.py` does not call RAMMB or JTWC. `global_board.py` does. |

Data this sub-skill reads/writes lives under
`Database/Weather/Hawai'i/hurricanes/tracking/<storm_name>_<TIMESTAMP>/`
(Hawaiʻi-relevant NHC tracks) and
`Database/Weather/Hawai'i/hurricanes/global/`
(worldwide board, `storm-tracks.json`, `storm-plot.txt`).
Nothing under this folder itself holds fetched data.
