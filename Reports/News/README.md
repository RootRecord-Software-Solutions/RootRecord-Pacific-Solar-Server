# Reports/News — Hawaiʻi state news collector (G3 port)

| Field | Value |
| --- | --- |
| **Ported from** | G0 `rootrecordsoftwaresolutions/old` `operations/news/_collector.py` + `operations/news/hawaii/news.py` (scheduled by `operations/cronologicals/on-time/10:00/hawaii-news.py`). G0 files KEPT, unchanged |
| **Date** | 2026-09-29 14:03 HST (old-repo migration, breadth pass) |
| **State** | LANDED · Hawaiʻi seeded 2026-09-29 ~14:20 HST: **PASS, 278 posts** from 16 feeds (temp root) · job **PROPOSED, not registered**. WO-MIG-12 adds the other 49 states and the global index (jobs **PROPOSED, not in jobs.py**). Public page: desk folder `3 - RootRecord-Website/` was removed 2026-09-30. Do not start it again. The public Vercel app is remote only. |
| **Secrets** | none (public official pages only) |

```text
scripts/_collector.py    shared official-source collector (G0, logic unchanged; timeouts capped at RR_NEWS_TIMEOUT ≤ 10 s,
                         crawl limits RR_NEWS_MAX_FEEDS/_PAGES/_SITEMAPS/_ARTICLES, defaults = G0 40/12/8/80)
scripts/hawaii_news.py   Hawaiʻi wrapper (portal https://www.hawaii.gov/, checkpoint 2026-03-31, SEED_FEEDS: 16 feeds)
                         RR_NEWS_SEEDS_ONLY=1 = seeds only, skip portal discovery
config/state_portals.json
config/state_event_sources.json   config only (weather and earthquakes stay out; NWS calendar is not fetched)
scripts/state_news.py    one wrapper for the other 49 slugs (`--state`). Refuses hawaii.
scripts/build_state_news.py
                         freshness orchestrator (55 min, empty DB = --backfill, 2 workers). Hawaiʻi via hawaii_news.py.
scripts/build_global_news.py
                         reads state DBs, writes Database Reports/News/global/global-news-last.json. locations is [].
```

Writes Database `Reports/News/hawaii/hawaii_news.db` (SQLite: sources, posts, events, source_health; **git-ignored**) and `Reports/News/hawaii/hawaii-news-last.json` (counts, source health, 10 newest posts).

Discovery stays inside the official `hawaii.gov` namespace (G0 rule: portal host + same-state `.gov` hosts; no other domains). Seed feeds are an explicit list (fetched first, not subject to that rule): 15 `*.hawaii.gov` feeds + the County of Maui news flash (`mauicounty.gov`). Each was checked for HTTP 200 with at least one RSS item on 2026-09-29.

## Smoke test (2026-09-29, temp Database root)

- 14:02 HST caps 3/3/1/5: rc 0, 3.7 s, 30 MB, 6 sources checked, all HTTP 404.
- 14:03 HST G0 caps (articles 20): rc 0, 12.3 s, 31 MB, 13 feeds + 12 pages checked, **25 × HTTP 404, 0 posts**. `https://www.hawaii.gov/` itself answers 200, but discovery only found guessed paths. The site's news links are probably script-rendered.
- ~14:20 HST with seeds, `RR_NEWS_SEEDS_ONLY=1`: rc 0, 11.6 s, 32 MB, 16 feeds all `ok`, **278 posts** (Maui 134, 10 each from most state feeds). Newest: Maui County SMA meeting reminder; Hawaiʻi National Guard / Hurricane Nolo; Governor's Land Use Commission appointments.
- Same with discovery too: rc 0, 22.8 s, 32 MB, 278 posts + the same 25 × 404.
- WO-MIG-12 ~23:58 HST, `state_news.py --state wyoming` then `build_global_news.py`, temp root `/tmp/rr-mig-12`, caps 3/2/1/5: both rc 0. Wyoming db + last JSON written. Global index: 50 health rows, Wyoming `empty` (0 posts, source health 2 empty / 3 error), `locations` []. Live Database `Reports/News/` unchanged.
- Not seeded: `health.hawaii.gov/feed/`, `dlnr.hawaii.gov/blog/feed/`, `honolulu.gov/feed/` (200, 0 items); `dcr.hawaii.gov/feed/`, Hawaiʻi County `RSSFeed.aspx` (403); Kauaʻi `RSSFeed.aspx` (404).

## Proposed job (not in jobs.py — sign-off)

Standing rule: `Automations/scripts/jobs.py` is edited only on Alexander's request or a WO. Block to add to `ON_AT` if approved (G0 ran 10:00 HST daily):

```python
    {
        "id": "reports_hawaii_news",
        "enabled": os.environ.get("RR_HAWAII_NEWS", "0") == "1",
        "description": "Hawaii government news collector (G0 port + 16 seed feeds), daily. hawaii.gov + County of Maui feeds.",
        "at_times": ["10:00"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/News/scripts/hawaii_news.py"',
        "timeout_sec": 300,
        "cwd": f"{PACIFIC}/Reports/News/scripts",
        "env": {"RR_NEWS_SEEDS_ONLY": "1"},
    },
```

## State and global builders (WO-MIG-12)

The other 49 states are one script plus `config/state_portals.json`, not 49 copies of `news.py`. `build_global_news.py` only aggregates databases that are already on disk. `locations` stays `[]` until the country location pollers exist. Runtime SQLite, `*-news-last.json` (except the Hawaiʻi summary), `global-news-last.json`, and `Logs/Reports/News/` stay out of git.

Public page: desk folder `3 - RootRecord-Website/` was removed 2026-09-30. There is no desk checkout. Do not start it again. The public Vercel app is remote only. `https://rootserver.rootrecord.cloud/` is the poller on `127.0.0.1:8799`, not a site. A signed-off remote news route should read `global-news-last.json` with the globe overlay glass card (dark glass, 16px radius, blur). Do not import `news.css` or the old geography news HTML. Do not deploy without a separate sign-off.

Proposed jobs (not in `jobs.py` — shared file, left untouched). Both default off. Paste into `EVERY_HOUR` only when Alexander asks and the file is free:

```python
    {
        "id": "reports_state_news",
        "enabled": os.environ.get("RR_STATE_NEWS", "0") == "1",
        "description": "49 state portals via state_news.py; Hawaiʻi via hawaii_news.py. Skip fresh DBs. Default off.",
        "only_at_hours": [],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/News/scripts/build_state_news.py"',
        "timeout_sec": 3600,
        "needs_internet": True,
        "cwd": f"{PACIFIC}/Reports/News/scripts",
        "env": {},
    },
    {
        "id": "reports_global_news",
        "enabled": os.environ.get("RR_GLOBAL_NEWS", "0") == "1",
        "description": "Aggregate Reports/News state DBs into global/global-news-last.json. Default off.",
        "only_at_hours": [],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/News/scripts/build_global_news.py"',
        "timeout_sec": 120,
        "needs_internet": False,
        "cwd": f"{PACIFIC}/Reports/News/scripts",
        "env": {},
    },
```

**Check later (Alexander):**
1. Review the 16 seed feeds (`SEED_FEEDS` in `hawaii_news.py`): keep the County of Maui feed (not hawaii.gov, 134 items incl. 2013 archive)? Find working Honolulu / Hawaiʻi County / Kauaʻi feeds (403 / 404 / empty today). Keep `RR_NEWS_SEEDS_ONLY=1` or also run discovery?
2. The public news page has no desk checkout. Desk folder `3 - RootRecord-Website/` was removed 2026-09-30. Do not start it again. Data stays in Database `Reports/News/`.
3. The other 49 states and the global builder landed in WO-MIG-12 (one wrapper, not 49 scripts). Jobs `RR_STATE_NEWS` and `RR_GLOBAL_NEWS` stay proposed.
4. Posts older than the checkpoint are kept on a normal run (only `--backfill` filters by checkpoint), so the first run stores the feeds' full history (oldest 2013-11-02, Maui).
