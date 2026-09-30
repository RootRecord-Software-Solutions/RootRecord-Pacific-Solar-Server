# Advertising

AdSense and AdMob end-of-day snapshots. Desk reports only. No ad tags and no Discord post.

## Status (2026-09-30 HST — WO-MIG-38)

| Item | State |
| --- | --- |
| Folder | **`Advertising/`** on Pacific. No lowercase twin and no symlink |
| Scripts | `scripts/adsense_eod.py`, `scripts/admob_eod.py`. No-key run writes `not_configured` and does not call Google |
| Keys | `lib/envload.py` reads `/home/rootrecord/master/master-key.env` only. Names: `GOOGLE_ADSENSE_CLIENT_ID`, `GOOGLE_ADSENSE_CLIENT_SECRET`, `GOOGLE_ADSENSE_REFRESH_TOKEN`, `GOOGLE_ADSENSE_ACCOUNT_NAME`, `GOOGLE_ADSENSE_CURRENCY`, `GOOGLE_ADMOB_CLIENT_ID`, `GOOGLE_ADMOB_CLIENT_SECRET`, `GOOGLE_ADMOB_REFRESH_TOKEN`, `GOOGLE_ADMOB_ACCOUNT_NAME`. AdMob client id and secret fall back to the AdSense client names. The AdMob refresh token does not. None of those names are in the file today. Values are never printed |
| Jobs | `adsense_eod` at 21:00 behind `RR_ADSENSE=1`. `admob_eod` at 21:05 behind `RR_ADMOB=1`. Both gated off |
| Data | `2 - RootRecord-Database/Advertising/` |
| Logs | `2 - RootRecord-Database/Logs/Advertising/` |
| Public page | Remote Vercel app only (`/data/advertising`). Status only. Not deployed. Desk folder `3 - RootRecord-Website/` was removed 2026-09-30. Do not start it again |

Live Energy BLE, the poller, Hawaiʻi weather, the globe, cameras, Kokoro, and `geology_collect.py` are not replaced.
