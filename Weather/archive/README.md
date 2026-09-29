# archive/

**Owns:** the daily consolidation job only.

- `consolidate.py` — thin wrapper around `core/daily_zip.py`, triggered at
  HST midnight (by `scheduler/run_cycle.py`), writes to
  `Database/WEATHER/hfo/archives/<MM-DD-YYYY>_Daily_Archive.zip`.

**Does NOT own:** the actual zip/verify/delete mechanics — that's
`core/daily_zip.py`. This file only decides *when* and *where*, per
`nws_plan.md` Section 8.

**Depends on:** `core/daily_zip.py`, `core/hst_time.py`.
