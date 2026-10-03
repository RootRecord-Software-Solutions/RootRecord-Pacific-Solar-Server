# Geology (Pacific)

Pacific **receives** Geology bank files into Database. Quake/HVO JSON collect stays **ML2** (fail-safe via `run-local-bank.sh` when `RR_LOCAL_DATA_POLL=1`).

**Canonical collect (quakes / notices):** `1 - Servers/3 - RootRecord-US-Mainland-Two/collectors/geology.py`  
**Kīlauea stills (Pacific report-side):** `Geology/scripts/kilauea_cams.py` → `Volcanoes/Hawaii/Cams/*_current.jpg` (job `geology_kilauea_cams`, gate `RR_KILAUEA_CAMS=1`). ML2 `geology_kilauea_cams` may still stream the same paths.

## Kept on Pacific (not ML2 pollers)

| Path | Role |
| --- | --- |
| `scripts/kilauea_cams.py` | USGS HVO still pull into Cams bank (no vision) |
| `scripts/kilauea_look.py` | Report-side vision on banked cams (Ollama/Gemma) |
| `scripts/earthquakes_backfill.py` | On-demand local quake DB backfill |
| `Earthquake-Discord/` | Format/send from Database last files (delivery) |
| `PublicDraftQueue/` | Draft queue from `kilauea_current.json` (no HTTP) |

## Data

`2 - RootRecord-Database/Geology/{Earthquakes,Volcanoes/Hawaii}/`
