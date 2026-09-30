# CloudNarrative

Optional cloud prose on the existing morning, midday, late, and Kīlauea template reports. Merged morning copies today's morning narrative and does not call the model again.

The templates in `Media/Voice/scripts/voice_reports.py` stay the measured text. This folder does not replace them, render Kokoro, or send anything.

| Path | Role |
| --- | --- |
| Code | `Reports/CloudNarrative/scripts` |
| Database | `2 - RootRecord-Database/Reports/CloudNarrative/` (gitignored runtime) |
| Logs | `2 - RootRecord-Database/Logs/Reports/CloudNarrative/` |
| Key | `XAI_API_KEY` in `/home/rootrecord/master/master-key.env` only |

```bash
python3 "…/Reports/CloudNarrative/scripts/cloud_narrative.py" morning --dry-run
```

`--dry-run` writes a prompt package and `last.json`. It does not open a socket. A live call is `RR_CLOUD_NARRATIVE_SPEND=1` plus `--spend`, and only after Alexander signs off for that run. The `jobs.py` entry `cloud_narrative_dry_run` is off unless `RR_CLOUD_NARRATIVE=1`, and its command is `--dry-run`.
