# Reports/News — Hawaiʻi state news collector (G3 port)

| Field | Value |
| --- | --- |
| **Ported from** | G0 `rootrecordsoftwaresolutions/old` `operations/news/_collector.py` + `operations/news/hawaii/news.py` (scheduled by `operations/cronologicals/on-time/10:00/hawaii-news.py`). G0 files KEPT, unchanged |
| **Date** | 2026-09-29 14:03 HST (old-repo migration, breadth pass) |
| **State** | LANDED · seeded 2026-09-29 ~14:20 HST: **PASS, 278 posts** from 16 feeds (temp root) · job **PROPOSED, not registered** |
| **Secrets** | none (public official pages only) |

```text
scripts/_collector.py    shared official-source collector (G0, logic unchanged; timeouts capped at RR_NEWS_TIMEOUT ≤ 10 s,
                         crawl limits RR_NEWS_MAX_FEEDS/_PAGES/_SITEMAPS/_ARTICLES, defaults = G0 40/12/8/80)
scripts/hawaii_news.py   Hawaiʻi wrapper (portal https://www.hawaii.gov/, checkpoint 2026-03-31, SEED_FEEDS: 16 feeds)
                         RR_NEWS_SEEDS_ONLY=1 = seeds only, skip portal discovery
```

Writes Database `Reports/News/hawaii/hawaii_news.db` (SQLite: sources, posts, events, source_health; **git-ignored**) and `Reports/News/hawaii/hawaii-news-last.json` (counts, source health, 10 newest posts).

Discovery stays inside the official `hawaii.gov` namespace (G0 rule: portal host + same-state `.gov` hosts; no other domains). Seed feeds are an explicit list (fetched first, not subject to that rule): 15 `*.hawaii.gov` feeds + the County of Maui news flash (`mauicounty.gov`). Each was checked for HTTP 200 with at least one RSS item on 2026-09-29.

## Smoke test (2026-09-29, temp Database root)

- 14:02 HST caps 3/3/1/5: rc 0, 3.7 s, 30 MB, 6 sources checked, all HTTP 404.
- 14:03 HST G0 caps (articles 20): rc 0, 12.3 s, 31 MB, 13 feeds + 12 pages checked, **25 × HTTP 404, 0 posts**. `https://www.hawaii.gov/` itself answers 200, but discovery only found guessed paths. The site's news links are probably script-rendered.
- ~14:20 HST with seeds, `RR_NEWS_SEEDS_ONLY=1`: rc 0, 11.6 s, 32 MB, 16 feeds all `ok`, **278 posts** (Maui 134, 10 each from most state feeds). Newest: Maui County SMA meeting reminder; Hawaiʻi National Guard / Hurricane Nolo; Governor's Land Use Commission appointments.
- Same with discovery too: rc 0, 22.8 s, 32 MB, 278 posts + the same 25 × 404.
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

**Check later (Alexander):**
1. Review the 16 seed feeds (`SEED_FEEDS` in `hawaii_news.py`): keep the County of Maui feed (not hawaii.gov, 134 items incl. 2013 archive)? Find working Honolulu / Hawaiʻi County / Kauaʻi feeds (403 / 404 / empty today). Keep `RR_NEWS_SEEDS_ONLY=1` or also run discovery?
2. Target decision: G0 wrote a website dataset (avaivy.cloud `data/hawaii-news.json`); G3 keeps it in Database `Reports/News/`. Publishing to a site is out of scope here.
3. Whether the other 49 state wrappers and `build_state_news.py` / `build_global_news.py` should also come across. They were not ported: they are website product data.
4. Posts older than the checkpoint are kept on a normal run (only `--backfill` filters by checkpoint), so the first run stores the feeds' full history (oldest 2013-11-02, Maui).
