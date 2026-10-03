# Weather (Pacific — receive / pointer only)

**No weather collect code lives here.** Canonical tree:

`1 - Servers/3 - RootRecord-US-Mainland-Two/`  
(`collectors/weather_*` + `vendor/Weather/`)

| Mode | Who runs collect |
| --- | --- |
| `RR_LOCAL_DATA_POLL=0` | Remote ML2 → SSH stream → Database |
| `RR_LOCAL_DATA_POLL=1` | `ML2/scripts/run-local-bank.sh` from that tree |

Pacific jobs are wrappers only (`weather_poller`, `weather_us_states`, `country_location_pollers`, `weather_radar_zip`, `weather_retention`).
