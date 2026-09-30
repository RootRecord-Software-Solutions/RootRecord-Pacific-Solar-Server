# Reports/News — Hawaiʻi state news collector (G3 port)

| Field | Value |
| --- | --- |
| **Ported from** | G0 `rootrecordsoftwaresolutions/old` `operations/news/_collector.py` + `operations/news/hawaii/news.py` (scheduled by `operations/cronologicals/on-time/10:00/hawaii-news.py`). G0 files KEPT, unchanged |
| **Date** | 2026-09-29 14:03 HST (old-repo migration, breadth pass) |
| **State** | LANDED · smoke test rc 0 but **FAIL on content**: 0 posts (see below) · job **PROPOSED, not registered** |
| **Secrets** | none (public official pages only) |

```text
scripts/_collector.py    shared official-source collector (G0, logic unchanged; timeouts capped at RR_NEWS_TIMEOUT ≤ 10 s,
                         crawl limits RR_NEWS_MAX_FEEDS/_PAGES/_SITEMAPS/_ARTICLES, defaults = G0 40/12/8/80)
scripts/hawaii_news.py   Hawaiʻi wrapper (portal https://www.hawaii.gov/, checkpoint 2026-03-31)
```

Writes Database `Reports/News/hawaii/hawaii_news.db` (SQLite: sources, posts, events, source_health; **git-ignored**) and `Reports/News/hawaii/hawaii-news-last.json` (counts, source health, 10 newest posts).

The collector stays inside the official `hawaii.gov` namespace (G0 rule: portal host + same-state `.gov` hosts; no other domains).

## Smoke test (2026-09-29, temp Database root)

- 14:02 HST caps 3/3/1/5: rc 0, 3.7 s, 30 MB, 6 sources checked, all HTTP 404.
- 14:03 HST G0 caps (articles 20): rc 0, 12.3 s, 31 MB, 13 feeds + 12 pages checked, **25 × HTTP 404, 0 posts**. `https://www.hawaii.gov/` itself answers 200, but discovery only found guessed paths. The site's news links are probably script-rendered. `https://governor.hawaii.gov/feed/` answers 200 and would be a working feed.

## Proposed job (not in jobs.py — sign-off)

Standing rule: `Automations/scripts/jobs.py` is edited only on Alexander's request or a WO. Block to add to `ON_AT` if approved (G0 ran 10:00 HST daily):

```python
    {
        "id": "reports_hawaii_news",
        "enabled": os.environ.get("RR_HAWAII_NEWS", "0") == "1",
        "description": "Hawaii official state news collector (G0 port), daily. Official hawaii.gov namespace only.",
        "at_times": ["10:00"],
        "builtin": "",
        "command": f'nice -n 10 python3 "{PACIFIC}/Reports/News/scripts/hawaii_news.py"',
        "timeout_sec": 900,
        "cwd": f"{PACIFIC}/Reports/News/scripts",
        "env": {},
    },
```

**Check later (Alexander):**
1. Add `https://governor.hawaii.gov/feed/` (and other official feeds) as explicit seeds, or leave discovery G0-faithful.
2. Target decision: G0 wrote a website dataset (avaivy.cloud `data/hawaii-news.json`); G3 keeps it in Database `Reports/News/`. Publishing to a site is out of scope here.
3. Whether the other 49 state wrappers and `build_state_news.py` / `build_global_news.py` should also come across. They were not ported: they are website product data.
