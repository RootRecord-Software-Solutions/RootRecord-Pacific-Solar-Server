# Radio RSS

2026-10-02 ~16:58 HST: feeds off, and stored rows from them are dropped by `blocked_sources`: The Guardian, every BBC feed, MarketWatch, Honolulu Civil Beat, Honolulu Star-Advertiser, Hawaii News Now, NPR National, NPR Politics, and Department of Justice. NPR News and NPR World stay. `news_hour.py` reads at most two items from one publisher on a desk. Hurricane Center speech is the public advisory only, with no coordinates. The poller job `radio_news_update` is minute [8], timeout 2400 seconds, and it pushes part 1 and part 2 only. Older sentences below that say minute 20, a single `news_update_current` file, or that `doj_news` was added are that hour’s record. `test_rss_radio.py` passed. No new audio from this note.

External RSS and Atom for RootRecord Radio. This is an upstream content path. It does not replace weather, quakes, volcanoes, solar timing, site energy, bandwidth, security monitoring, or the Hawaiʻi news collector. It does not change the Mainland broadcaster.

This layer writes a queue the station can take from, and `--speak` can hand one finished brief to the existing voice renderer and `radio_push.py`. The live Mainland host has no music bed. The public station is not playing one. The station library is Opus. The public mix is `https://radio.rootrecord.cloud/radio/live.mp3`.

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

The poller job is `radio_rss_poll`. It runs at minute :05 when `RR_RADIO_RSS=1` (the poller script defaults that on) and pulls every enabled feed in one list. The job does not speak and does not push audio.

`news-hour` builds from stories already pulled at :05 (markets, defence, SpaceX, Hawaii, tech/chips, world news, weather, politics, science, universities). It writes one script aimed at twenty to twenty-five spoken minutes. A verified sample was ~22.7 minutes, with Ava, Bruce, and Carly balanced. Solar remains a separate 5–7 minute desk. Hawaii items matching the violence list and sports items are dropped; sports matching uses word edges to avoid false hits such as conflict, influenza, and sportswear. Centrist politics feeds also drop partisan phrasing. `defense_gov` is on the national security desk. MarketWatch, the BBC, The Guardian, NPR, Justice, Honolulu Civil Beat, the Honolulu Star-Advertiser, and Hawaii News Now are not in the feed list. `--speak` renders that script with Ava, Bruce, and Carly rotating by the Hawaii hour, replaces `news_update_current.wav`, and `radio_push.py` encodes that one report to `news_update_current.opus` (24 kbps mono) on the Mainland runtime. The poller job is `radio_news_update` at minute 20, with a 2400-second timeout. At the Report Instructor's ~11:53 HST read, `RR_RADIO_NEWS=1` and the news job is on; the soft poller restart is only needed to adopt that timeout change.

`handoff` without `--speak` shows the next queued brief and leaves it queued. `--speak` renders with the existing Kokoro path. Hawaii still renders a WAV. `radio_push.py` encodes that one report to `<report>_current.opus` and replaces it on `/home/ubuntu/rootrecord-radio`. Prune keeps both `*_current.ogg` and `*_current.opus` until that report is replaced, then deletes only that report's old ogg.

Culture feeds are not in this set. Offbeat science stays behind alerts, launches, and security items.
