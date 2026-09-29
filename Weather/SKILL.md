# weather

**What it is:** the NWS Honolulu (HFO) data-mirror skill. Fetches every text
product, image, chart, and API resource on the Hawaii resource map on its own
tiered cadence (Tier 0 = 60s alerts, Tier 6 = best-effort/unconfirmed),
writes/archives it under `Database/WEATHER/Hawai'i/hfo/`, and rolls yesterday's
archive folders into one daily zip at HST midnight.

**How it fires:** on a schedule, dispatched by `scheduler/run_cycle.py`, which
reads `config/tiers.yaml` to decide what's due each cycle. Not a
conversation-triggered skill — it runs continuously/on-cron.

**Companion docs (design intent, not code):**
- `weather_skill_architecture.md` — the code tree this skill follows
- `nws_plan.md` — the storage/archiving/change-detection contract
- `NWS_Hawaii_Resource_Map.md` — the full resource inventory

**Hard rule:** code and data are two different trees. Nothing under this
folder writes application data into itself — every fetched file, archive,
manifest, and per-storm tracking state lives under `Database/WEATHER/`. See
each subfolder's own `README.md` for what it owns.

## Layout

| Folder | Owns |
|---|---|
| `config/` | Static resource/tier/county/host/cleaning definitions (data, no logic) |
| `core/` | Shared engine: http, change-detection, archiving, cleaning, validation |
| `fetch/` | One module per resource category |
| `alerts/` | Alert-specific processing (county mapping, severity, dedupe) |
| `hurricanes/` | Tropical cyclone sub-skill (own SKILL.md, own schedule) |
| `scheduler/` | Tier cadence + job dispatch |
| `archive/` | Daily zip consolidation job |
| `tests/` | Smoke tests, mirrors the tree 1:1 |

## Status

Foundation scaffold — see each folder's `README.md` for build status of that
part. Build checkpoints are tracked in `BUILD_STATUS.md` at this level.
