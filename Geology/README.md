# Geology (Pacific)

Pacific **receives** Geology bank files into Database. Internet collect code is **ML2 only**.

**Canonical collect:** `1 - Servers/3 - RootRecord-US-Mainland-Two/collectors/{geology,geology_kilauea_cams}.py`  
**Fail-safe:** `ML2/scripts/run-local-bank.sh` when `RR_LOCAL_DATA_POLL=1`

## Kept on Pacific (not ML2 pollers)

| Path | Role |
| --- | --- |
| `scripts/kilauea_look.py` | Report-side vision on banked cams (Ollama/Gemma) |
| `scripts/earthquakes_backfill.py` | On-demand local quake DB backfill |
| `Earthquake-Discord/` | Format/send from Database last files (delivery) |
| `PublicDraftQueue/` | Draft queue from `kilauea-last.json` (no HTTP) |

## Data

`2 - RootRecord-Database/Geology/{Earthquakes,Volcanoes/Hawaii}/`
