# Media/News

Pacific entrypoint for the hourly news cycle.

- **Job:** `news_cycle` at `:35` (`RR_NEWS_CYCLE=1`)
- **Script:** `scripts/run_news_cycle.py` — poll → four lanes → numbered TTS → stitch `news_update_current.wav` (no push; `RR_RADIO_PUSH=0`)
- **Air:** `:36` `voice_hour_batch` waits for this process to finish, then folds that WAV after the desk reports into one `report_current` and pushes
- **Bank:** Database `Media/News Data/`
- **Canonical code/config:** `Media/News/radiorss/` (not ML1 vendor — ML1 tree was being overwritten by a stuck sync)

`:30` energy consolidate zips/wipes the News Data bank for a fresh poll.
