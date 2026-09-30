# Communications/MetaAI — on-demand Meta AI chat

| Field | Value |
| --- | --- |
| **Ported from** | `old/operations/meta/meta.py` |
| **Date** | 2026-09-30 (HST) |
| **State** | On demand only. No job. |
| **Secrets** | none |

`python3 scripts/meta.py --check` reports whether `meta-ai-api` can be imported. It does not install the package and does not call `MetaAI().prompt`.

`python3 scripts/meta.py --send` (or `--send "one message"`) is a send to meta.ai and stays off until Alexander signs off. A signed-off send writes `last.json` under `2 - RootRecord-Database/Communications/MetaAI` and a line under `2 - RootRecord-Database/Logs/Communications/MetaAI`.

With no arguments the script prints the same check JSON and does not send.
