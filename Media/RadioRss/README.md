# RadioRss (Pacific pointer)

**Canonical code:** `1 - Servers/3 - RootRecord-US-Mainland-Two/vendor/RadioRss/`  
**Collector:** `collectors/radio_rss.py`  
**Data bank:** `2 - RootRecord-Database/Media/RadioRss/`

Pacific jobs call the ML2 tree only:

| Job | Path |
| --- | --- |
| `radio_rss_poll` (fail-safe) | `ML2/scripts/run-local-bank.sh --only radio_rss` |
| `radio_news_update` (speak) | `ML2/vendor/RadioRss/scripts/rss_radio.py news-hour --speak` |

When `RR_LOCAL_DATA_POLL=0`, remote ML2 owns the poll; Pacific poll job is gated off.
