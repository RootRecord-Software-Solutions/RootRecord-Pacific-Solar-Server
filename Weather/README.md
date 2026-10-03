# Weather (Pacific desk)

Pacific owns **Database bank maintenance** only (retention, RadarZip).  
**All internet weather pollers** live under ML2:

`1 - Servers/3 - RootRecord-US-Mainland-Two/`  
(`collectors/weather_*` + `vendor/Weather/`)

---

## Toggle

| `RR_LOCAL_DATA_POLL` | Who collects |
| --- | --- |
| `0` (live) | Remote ML2 host → SSH stream → Database |
| `1` / unset | Pacific fail-safe runs **the same ML2 tree** via `ML2/scripts/run-local-bank.sh` (no Pacific poller copies) |

---

## Pacific jobs (thin wrappers → ML2)

| Job id | Command |
| --- | --- |
| `weather_poller` | `run-local-bank.sh --only weather_hawaii` |
| `weather_us_states` | `run-local-bank.sh --only weather_us_states` |
| `country_location_pollers` | `run-local-bank.sh --only weather_country_locations` |
| `weather_radar_zip` | `Weather/RadarZip/scripts/radar_zip.py` (bank-side; not an ML2 poller) |
| `weather_retention` | `Weather/scripts/weather-retention.py` (bank-side) |

---

## Layout (Pacific)

```text
Weather/
  RadarZip/          # archive GIFs into Database zip
  scripts/           # retention + helpers (no fetch daemon)
  config/            # legacy YAML reference; live fetch config is ML2 vendor
```
