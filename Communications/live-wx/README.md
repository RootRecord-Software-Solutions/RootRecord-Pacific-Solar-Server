# Communications / live-wx

Live weather lines for chat (G3 port of G1 `weather/live-wx`, 2026-09-29 old-repo migration pass).

| Script | What | Run |
| --- | --- | --- |
| `scripts/live_wx.py` | NWS point forecast (current + next two periods; "tonight" after 18:00), NWS HI alert names (Big Island flagged), nearest hurricane from G3 `track.json` | on demand; `--offline` = no HTTP |

- Reads: Database `Weather/Hawai'i/hfo/api.weather.gov/alerts/active/area=HI/area=HI_current.json`, `Weather/Hawai'i/hurricanes/tracking/*/track.json` (via `Media/Voice/scripts/voice_reports.py`).
- Network: `api.weather.gov` only (points → forecast, 10 s timeout), skipped with `--offline`. Writes nothing.
- Not wired to council chat (relay replies BLOCKED). No job.
