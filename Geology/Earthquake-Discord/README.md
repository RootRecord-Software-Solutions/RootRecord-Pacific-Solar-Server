# Earthquake-Discord

Formats Database `Geology/Earthquakes/{hawaii,global}-last.json` into a short Discord message.

Dry-run is the default. It prints the message and does not write `posted-last.json` or call Discord.

```text
python3 scripts/earthquake_discord_post.py
```

`--send` hands the text to `Communications/Discord`. That pipe still returns without HTTP unless `RR_DISCORD_POST=1`. This folder does not load the bot token.

Job `earthquake_discord_post` in `Automations/scripts/jobs.py` stays off unless `RR_EARTHQUAKE_DISCORD=1` at poller start.

Channel id key name, if a live send is later signed off: `DISCORD_EARTHQUAKE_CHANNEL_ID` in `/home/rootrecord/master/master-key.env`.
