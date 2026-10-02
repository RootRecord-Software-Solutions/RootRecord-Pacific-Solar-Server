# Geology

**Canonical Pacific home** for Kīlauea / volcano observation tooling and **all earthquake functions** (Hawaiʻi-local and global).

---

## Status (2026-09-29 ~13:30 HST — migration-geology pass)

| Item | State |
| --- | --- |
| Domain folder | **`Geology/` only** (no parallel `geology` / `kilauea` / `earthquakes` runtime folders on Pacific) |
| Ownership | Desk-side observation, polling, ingest, and operator tooling |
| Scripts | `scripts/geology_collect.py`, `scripts/kilauea_cams.py`, `scripts/earthquakes_backfill.py` — **LANDED**, one manual run each **PASS** (nice 10) |
| `jobs.py` | `geology_collect` (300 s, `RR_GEOLOGY=1`), `geology_kilauea_cams` (600 s, `RR_KILAUEA_CAMS=1`) — **gated OFF**; take effect only at the next poller start with the flag set. Keeping these jobs.py registrations is a **sign-off item** (standing rule: jobs.py only on Alexander's request or a WO; exact blocks in Database `Logs/Migration/migration-jobs-py-additions-20260929.md`) |
| Data | Database `2 - RootRecord-Database/Geology/{Earthquakes,Volcanoes}/` — layout in Database `Geology/README.md` |
| Voice | `Media/Voice/scripts/voice_reports.py earthquake_report` (job `voice_earthquake_report`, `RR_VOICE_QUAKE=1`) and `kilauea_report` (job `voice_kilauea_report`, `RR_VOICE_KILAUEA=1`) read the Geology last files; no delivery |
| Config | `config/global-locations.json` — verbatim copy of G0 `old/config/locations/global-locations.json` (306 public places: country capitals, US state capitals, staged Hawaiʻi locations; sha256 `5defe5c7…b49a`). Used by `geology_collect.py` for the G0 nearest-location tag (≤ 250 km) on every event (`nearest`: location_id, name, country_code, admin1_code, km) — added 2026-09-29 13:49 HST, PASS |
| Public products | Alert apps / websites may live in product repos; **this domain owns desk runtime** for the same capability |

### Scripts

| Script | Ported from | Sources (public, no key) | Writes |
| --- | --- | --- | --- |
| `scripts/geology_collect.py [all\|quakes\|volcanoes] [--dry-run]` | G1 `earthquakes/earthquake-hourly` (fetch + M≥2 detection), G1 `kilauea/rr-kilauea` (alert level, headline, erupting, multiplier, ≤150 km count), G0 `operations/…/every-5-minutes/quakes.py`, G0 `operations/earthquakes/global/poller.py` (nearest-location tag) | USGS FDSN query (Hawaiʻi bbox, M≥1, 24 h), USGS summary `2.5_day.geojson`, HANS `getMonitoredVolcanoes`, HANS `getNewestOrRecent` | `Earthquakes/{hawaii,global}-last.json`, `Earthquakes/Daily/*.jsonl`, `Volcanoes/{hvo,kilauea,mauna-loa}-last.json`, `Volcanoes/Daily/hvo-notices-*.jsonl`, `collector-last.json` |
| `scripts/kilauea_cams.py [--keep-dated]` | G1 `kilauea/kilauea-cams` (DEFAULT_CAMS + USGS still fallback) | USGS HVO V1/V2/V3 `M.jpg` (conditional GET) | `Volcanoes/Cams/cams-last.json`, `Volcanoes/Cams/v{1,2,3}cam-last.jpg` |
| `scripts/earthquakes_backfill.py [--days N]` | G0 `old/operations/backfillquakes.py` | USGS FDSN `count` + `query` | `Earthquakes/quakes.db` (git-ignored) — on demand only |
| `Earthquake-Discord/scripts/earthquake_discord_post.py` | G1 `earthquake-hourly` Discord post only | Database `Earthquakes/{hawaii,global}-last.json` (no USGS fetch) | Dry-run prints. `Earthquake-Discord/posted-last.json` only after a signed-off `--send` |
| `PublicDraftQueue/scripts/queue_draft.py` | G1 `rr-kilauea` public draft queue only | Database `Volcanoes/kilauea-last.json` (no HTTP) | `PublicDraftQueue/queue/*-kilauea-cron.md` on a changed notice id or alert level |

Light by design: stdlib only, every HTTP call ≤ 10 s (`RR_GEOLOGY_TIMEOUT`), no retries, one failed source never overwrites its last good file.

**Earthquake Discord post:** `Earthquake-Discord/scripts/earthquake_discord_post.py` formats `Earthquakes/{hawaii,global}-last.json`. Dry-run by default (2026-09-30). Job `earthquake_discord_post` stays off unless `RR_EARTHQUAKE_DISCORD=1`. Live send still needs sign-off.

**Public draft queue:** `PublicDraftQueue/scripts/queue_draft.py` reads `kilauea-last.json` and queues a markdown draft when the HVO notice id or alert level changes. Job `geology_kilauea_public_draft` stays off unless `RR_KILAUEA_DRAFT=1`. No HTTP and no send.

**Not ported (need Alexander's sign-off):** speaker playback, OBS cam push (no OBS in G3), YouTube live-id scraping. Optional Kīlauea cloud prose is `Reports/CloudNarrative` (WO-MIG-32, dry-run; a live spend still needs sign-off). G1/G0 sources stay **KEPT** (not retired).

### Ecosystem path

```text
/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Geology/
```

---

## Scope (in)

| Area | Examples |
| --- | --- |
| **Kīlauea** | Alerts ingest, status snapshots, cam helpers (if desk-side), volcano-specific weather hooks used only for Kīlauea ops |
| **Earthquakes — local** | Hawaiʻi / Pacific Island region quake feeds, local magnitude filters, island event logging |
| **Earthquakes — global** | Worldwide catalog pulls, significant-event filters, cross-region digests |
| **Shared geology ops** | Schedulers, normalize/store helpers, Database writers for the above |

## Scope (out / adjacency)

| Concern | Home |
| --- | --- |
| General island weather (non-volcano product) | `Weather/` |
| Generic security cams not tied to volcano ops | `Security/` (or A-Eyes) |
| Public marketing site only | Product / Website repos — not a substitute for this domain’s desk code |
| G2 skill paths | Migrate **into `Geology/`**; do not leave long-term runtime under `~/.ollama/skills` |

---

## Naming SOP (standing)

Same as Energy / System (see Library Pacific Domain Import Playbook):

- **One folder:** `Geology/` — no `geology` symlink, no separate `Kilauea/` or `Earthquakes/` top-level on Pacific for runtime.
- Optional **subfolders inside** Geology for clarity, e.g.:

```text
Geology/
  README.md
  scripts/
    kilauea/
    earthquakes/
      local/
      global/
  lib/
  config/      # present: global-locations.json
```

- Python package name, if used: **`Geology`** (matches folder). Rewrite any G2 `import kilauea` / `import earthquakes` package roots accordingly, or use submodules under `Geology/`.

---

## Import sources (when ready)

| Source | Content |
| --- | --- |
| G1 / Old | `kilauea/*`, `earthquakes` packets |
| G2 skills | Any live skill paths still under ollama for volcano/quake |
| Product repos | Copy **desk** scripts only; keep secrets out of git |

Deploy path after import: `jobs.py` entries landed gated (2026-09-29); enabling = set the flag in the poller environment at the next poller start (no reload by agents).

---

## Policy

- All new Kīlauea and earthquake **desk functions** land in **`Geology/`**.
- Do not scatter quake/volcano pollers under Weather or Automations root long-term.
- Database remains the byte authority; Geology owns the code that writes those bytes.

---

*Ownership declared 2026-09-28 HST. Scripts landed 2026-09-29 (migration-geology; Library `Documentation/13-Migration-and-Legacy-Recovery/Old-Repo-Migration-Matrix.md`).*
