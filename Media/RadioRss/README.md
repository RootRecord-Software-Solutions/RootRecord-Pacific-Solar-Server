# Radio RSS

External RSS and Atom for RootRecord Radio. This is an upstream content path. It does not replace weather, quakes, volcanoes, solar timing, site energy, bandwidth, security monitoring, or the Hawaiʻi news collector. It does not change the Mainland broadcaster.

The broadcaster still plays the reports and music it already has. This layer writes a queue the station can take from, and `--speak` can hand one finished brief to the existing voice renderer and `radio_push.py`.

| | |
| --- | --- |
| Code | `Media/RadioRss/scripts` |
| Registry | `Media/RadioRss/config/feeds.yaml` |
| Categories | `Media/RadioRss/config/categories.yaml` |
| Policy | `Media/RadioRss/config/policy.yaml` |
| Data | `2 - RootRecord-Database/Media/RadioRss/` |
| Health | `health.txt` and `health.json` in that data folder |
| Queue | `queue.json` in that data folder |
| Logs | `2 - RootRecord-Database/Logs/Media/RadioRss/rss.log` |

Add or remove a feed in `feeds.yaml`. Leave `url` empty and `origin: unavailable` when the publisher has no verified RSS or Atom endpoint. A guessed URL does not belong in the registry.

```text
python3 scripts/rss_radio.py check
python3 scripts/rss_radio.py poll
python3 scripts/rss_radio.py health
python3 scripts/rss_radio.py handoff
python3 scripts/rss_radio.py handoff --speak
python3 scripts/rss_radio.py news-hour
python3 scripts/rss_radio.py news-hour --speak
python3 scripts/rss_radio.py trace STORY_ID
```

`poll` keeps going when a feed fails. After repeated failures the feed is marked `feed_unhealthy` in the runtime index. The YAML entry stays. `enable ID` turns that runtime flag back on.

The poller job is `radio_rss_poll`. It runs when `RR_RADIO_RSS=1` (the poller script defaults that on). The job does not speak and does not push audio.

`news-hour` polls the market, national-security, SpaceX, and Hawaii desks, then writes one script aimed at about five minutes. Hawaii items that match the violence list are dropped. `--speak` renders that script with Ava, Bruce, and Carly rotating by the Hawaii hour, replaces `news_update_current.wav`, and uploads `news_update_current.ogg` to the reports playlist through `radio_push.py`. The poller job is `radio_news_update` at minute 20. It runs when `RR_RADIO_NEWS=1` (the poller script defaults that on).

`handoff` without `--speak` shows the next queued brief and leaves it queued. `--speak` renders with the existing Kokoro path and replaces that one `<report>_current.ogg` through `radio_push.py`.

Culture feeds are not in this set. Offbeat science stays behind alerts, launches, and security items.
