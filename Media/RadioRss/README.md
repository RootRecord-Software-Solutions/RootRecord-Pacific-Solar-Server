# Radio RSS

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

The poller job is `radio_rss_poll`. It runs when `RR_RADIO_RSS=1` (the poller script defaults that on). The job does not speak and does not push audio.

`news-hour` polls markets, defence, SpaceX, Hawaii, tech/chips, world news across every continent, U.S. mainland weather, centrist mainland politics, science, universities, and also, then writes one script aimed at twenty to twenty-five spoken minutes. A verified sample was ~22.7 minutes, with Ava, Bruce, and Carly balanced. Solar remains a separate 5–7 minute desk. Hawaii items matching the violence list and sports items are dropped; sports matching uses word edges to avoid false hits such as conflict, influenza, and sportswear. Centrist politics feeds also drop partisan phrasing. The build added `doj_news` and `defense_gov` feeds and raised defence/politics budgets. `--speak` renders that script with Ava, Bruce, and Carly rotating by the Hawaii hour, replaces `news_update_current.wav`, and `radio_push.py` encodes that one report to `news_update_current.opus` (24 kbps mono) on the Mainland runtime. The poller job is `radio_news_update` at minute 20, with a 2400-second timeout. At the Report Instructor's ~11:53 HST read, `RR_RADIO_NEWS=1` and the news job is on; the soft poller restart is only needed to adopt that timeout change.

`handoff` without `--speak` shows the next queued brief and leaves it queued. `--speak` renders with the existing Kokoro path. Hawaii still renders a WAV. `radio_push.py` encodes that one report to `<report>_current.opus` and replaces it on `/home/ubuntu/rootrecord-radio`. Prune keeps both `*_current.ogg` and `*_current.opus` until that report is replaced, then deletes only that report's old ogg.

Culture feeds are not in this set. Offbeat science stays behind alerts, launches, and security items.
