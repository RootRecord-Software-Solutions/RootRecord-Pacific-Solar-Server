# Telegram datapack pickup (Pacific)

Staged 2026-10-02. **Not installed** on the live host by this scaffold.

## Role

When Mainland cannot SSH to Pacific, `system-monitor/telegram_datapack.py` sends a zip via the **datapack bot** (`RR_DATAPACK_*`). Telegram is the free buffer — Mainland purges after sendDocument accept.

When Pacific is back online, `scripts/datapack-pickup.py`:

1. `getUpdates` on the datapack bot (separate from Ava council-relay — do not share tokens)
2. Downloads `rootrecord-*.zip` documents
3. Applies envelope `path_rel` into Database allowlist (`System/metrics/ml1|ml2/`, …)
4. Stores zip under `Network/datapacks/processed/`
5. Advances `Network/datapacks/state/telegram-offset.json`

## Dry-run

```bash
./scripts/run-datapack-pickup.sh --dry-run
./scripts/run-datapack-pickup.sh --local-zip /path/to/rootrecord-sysmon-….zip
```

## Must never

- Use Ava / council-relay token for getUpdates here
- Write `Energy/` or EcoFlow paths
- Leave Mainland stacking copies (sender responsibility)

## Historical reference only

ML1 REBUILD OLD FILES: `rr-packer.service`, `ssh-datapack-pull.sh`, `RR_DATAPACK_*`.
