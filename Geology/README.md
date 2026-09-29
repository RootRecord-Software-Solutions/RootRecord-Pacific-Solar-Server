# Geology

**Canonical Pacific home** for Kīlauea / volcano observation tooling and **all earthquake functions** (Hawaiʻi-local and global).

---

## Status (2026-09-29 ~13:30 HST — migration-geology pass)

| Item | State |
| --- | --- |
| Domain folder | **`Geology/` only** (no parallel `geology` / `kilauea` / `earthquakes` runtime folders on Pacific) |
| Ownership | Desk-side observation, polling, ingest, and operator tooling |
| Scripts | `scripts/geology_collect.py`, `scripts/kilauea_cams.py`, `scripts/earthquakes_backfill.py` — **LANDED**, one manual run each **PASS** (nice 10) |
| `jobs.py` | `geology_collect` (300 s, `RR_GEOLOGY=1`), `geology_kilauea_cams` (600 s, `RR_KILAUEA_CAMS=1`) — **gated OFF**; take effect only at the next poller start with the flag set (after Alexander signs off) |
| Data | Database `2 - RootRecord-Database/Geology/{Earthquakes,Volcanoes}/` — layout in Database `Geology/README.md` |
| Voice | `Media/Voice/scripts/voice_reports.py earthquake_report` reads the Earthquakes last files (job `voice_earthquake_report`, `RR_VOICE_QUAKE=1`, no delivery) |
| Public products | Alert apps / websites may live in product repos; **this domain owns desk runtime** for the same capability |

### Scripts

| Script | Ported from | Sources (public, no key) | Writes |
| --- | --- | --- | --- |
| `scripts/geology_collect.py [all\|quakes\|volcanoes] [--dry-run]` | G1 `earthquakes/earthquake-hourly` (fetch + M≥2 detection), G1 `kilauea/rr-kilauea` (alert level, headline, erupting, multiplier, ≤150 km count), G0 `operations/…/every-5-minutes/quakes.py` | USGS FDSN query (Hawaiʻi bbox, M≥1, 24 h), USGS summary `2.5_day.geojson`, HANS `getMonitoredVolcanoes`, HANS `getNewestOrRecent` | `Earthquakes/{hawaii,global}-last.json`, `Earthquakes/Daily/*.jsonl`, `Volcanoes/{hvo,kilauea,mauna-loa}-last.json`, `Volcanoes/Daily/hvo-notices-*.jsonl`, `collector-last.json` |
| `scripts/kilauea_cams.py [--keep-dated]` | G1 `kilauea/kilauea-cams` (DEFAULT_CAMS + USGS still fallback) | USGS HVO V1/V2/V3 `M.jpg` (conditional GET) | `Volcanoes/Cams/cams-last.json`, `Volcanoes/Cams/v{1,2,3}cam-last.jpg` |
| `scripts/earthquakes_backfill.py [--days N]` | G0 `old/operations/backfillquakes.py` | USGS FDSN `count` + `query` | `Earthquakes/quakes.db` (git-ignored) — on demand only |

Light by design: stdlib only, every HTTP call ≤ 10 s (`RR_GEOLOGY_TIMEOUT`), no retries, one failed source never overwrites its last good file.

**Not ported (need Alexander's sign-off):** G1 Discord/Telegram posts (`earthquake-hourly` Discord, `council-quake` Telegram per-quake posts, `rr-kilauea` public draft queue), Grok report generation (cloud spend), speaker playback, OBS cam push (no OBS in G3), YouTube live-id scraping. G1/G0 sources stay **KEPT** (not retired).

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
  config/
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

*Ownership declared 2026-09-28 HST. Scripts landed 2026-09-29 (migration-geology; Library `Documentation/00-architecture/Old-Repo-Migration-Matrix.md`).*
