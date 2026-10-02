# Mainland system-monitor intake (Pacific home)

Staged 2026-10-02. Receiver and pickup units are **not installed** by this work.

## Collect paths on home

| Source | Primary | Fallback |
| --- | --- | --- |
| ML1 / ML2 sysmon | SSH NDJSON → `System/scripts/rr_db_stream_receive.py` | Telegram datapack → `Communications/telegram/scripts/datapack-pickup.py` |
| ML2 domain collectors | existing `stream/home_receiver.py` (same allowlist family; deploy as same receiver) | — |

## Database layout

| Path | Role |
| --- | --- |
| `System/metrics/ml1/host-last.json` | Latest ML1 host snapshot (overwrite) |
| `System/metrics/ml1/Daily/YYYY-MM-DD.jsonl` | Pacific long-term bank (append) |
| `System/metrics/ml2/…` | Same for ML2 |
| `Network/datapacks/inbox/` | Brief download staging |
| `Network/datapacks/processed/` | Applied zips |
| `Network/datapacks/state/` | Telegram offset + pickup-last |
| `Logs/System/mainland-stream-receive.jsonl` | SSH receive audit |
| `Logs/ML1/`, `Logs/ML2/` | Reserved for Mainland log handoffs |

## EcoFlow

Unchanged. Pacific-only Energy collectors. Receiver **denies** `Energy/` and EcoFlow path segments.

## Enable later (sign-off)

1. Deploy `rr_db_stream_receive.py` forced-command for stream keys
2. Set `enabled: true` on Mainland `config/sysmon-stream.yaml`
3. Install `rr-datapack-pickup.{timer,service}` only after datapack bot token is in `/etc/rootrecord/datapack.env`
4. Install Mainland `ml1-sysmon` / `ml2-sysmon` timers on hosts
