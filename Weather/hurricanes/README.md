# hurricanes/

**This is a sub-skill, not a plain module folder.** It has its own `SKILL.md`,
`INDEX.md`, `DAILY.md`, `references/`, and `scripts/`, nested inside `weather/`
rather than living as a sibling top-level skill, and it fires on its own
schedule independently of the rest of `weather/`.

**Owns:** everything tropical-cyclone-specific — NHC `CurrentStorms.json`,
CPHC TCM/TCP/TCD/TCU pulls, RAMMB, JTWC, the 800nmi-relevance distance
threshold, and plain-language storm narration. This earned its own subsystem
(rather than a thin `fetch/` module) because the old system had 5 separate
flat modules here (tracker, fetch, obs, desk, radio) — genuinely more surface
area and different data shapes than a flat resource pull.

**Does NOT own:** general alerts processing (`alerts/`), non-tropical
satellite/radar/analyses (`fetch/`). Reuses `core/` the same way every other
part of `weather/` does — no special-cased HTTP client or archiver.

**Depends on:** `core/` (http, archiving, manifest — same mechanism as
everything else), writes to `Database/WEATHER/Hawai'i/hurricanes/tracking/`
per storm, same placement pattern as any other `fetch/` module's corner of
the database.

**Public-database note:** `Database/WEATHER/` is intended to eventually be
public. No API keys, internal hostnames, or credentials belong in any
manifest, User-Agent string, or state file under that tree — if a key is ever
needed for a hurricane data source, it goes in `config/hosts.yaml` in the
code tree, not here.
