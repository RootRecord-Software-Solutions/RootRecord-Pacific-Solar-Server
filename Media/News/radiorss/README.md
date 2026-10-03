# Radio RSS (ML1)

External RSS and Atom for RootRecord Radio. Canonical home is **this ML1 tree** (`US-Mainland-One/vendor/RadioRss/`). Not on ML2 or Pacific.

This layer writes a queue the station can take from, and `--speak` can hand one finished brief to the existing voice renderer and `radio_push.py`. The station library is Opus. Public air is YouTube only; `radio.rootrecord.cloud` / `live.mp3` are off.

| | |
| --- | --- |
| Code | `vendor/RadioRss/scripts` (this tree) |
| Runner | `scripts/run-radio-rss.sh` (ML1 root) |
| Registry | `config/feeds.yaml` |
| Data | `2 - RootRecord-Database/Media/RadioRss/` |
| Fail-safe | `docs/TOGGLE.md` — `RR_RADIO_MODE=local` / auto → desk `rootrecord-radio/` |

```text
../../scripts/run-radio-rss.sh check
../../scripts/run-radio-rss.sh poll
../../scripts/run-radio-rss.sh health
python3 scripts/rss_radio.py news-hour --speak
```

`poll` keeps going when a feed fails. Jobs: `radio_rss_poll` (`RR_RADIO_RSS=1`), `radio_news_update` (`RR_RADIO_NEWS=1`).
