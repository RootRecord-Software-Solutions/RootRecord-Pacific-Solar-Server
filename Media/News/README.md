# Media/News

Pacific entrypoint for the hourly news cycle.

- **Job:** `news_cycle` at `:35` (`RR_NEWS_CYCLE=1`)
- **Script:** `scripts/run_news_cycle.py` — poll → four lanes → numbered TTS → stitch `news_update` → `radio_push`
- **Bank:** Database `Media/News Data/`
- **Config / code:** ML1 `vendor/RadioRss/`
