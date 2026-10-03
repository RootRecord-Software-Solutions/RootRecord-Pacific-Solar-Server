# Media/News

Pacific entrypoint for the hourly news cycle.

- **Job:** `news_cycle` at `:35` (`RR_NEWS_CYCLE=1`)
- **Script:** `scripts/run_news_cycle.py` — poll → four lanes → numbered TTS → stitch `news_update` → `radio_push`
- **Bank:** Database `Media/News Data/`
- **Canonical code/config:** `Media/News/radiorss/` (not ML1 vendor — ML1 tree was being overwritten by a stuck sync)

`:30` energy consolidate zips/wipes the News Data bank for a fresh poll.
