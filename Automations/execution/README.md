# Execution

The broker, the interaction request loop, the verifier, and the audit writer. Capability names stay in Library `Documentation/02-agents/capabilities/`. Do not add a second registry here.

| File | Role |
| --- | --- |
| `execution-broker.py` | `request` answers a read or refuses. `execute` calls Cursor only when `cursor_api` is on. `recover` refuses a restart and may write a BLOCKED draft. |
| `interaction.py` | Sandbox seed, three persona passes, draft, handoff package. |
| `gates.py` | The gate file the broker enforces. Missing write gates stay closed. |
| `verifier.py` | `WO-SRV-RELAY` process check, and `report` for an execution report. |
| `audit.py` | One JSON line per decision. No chat text. |
| `test_interaction.py` | Temp directories. Does not call the NPU or the Cursor API. |

The narrative is Library `Documentation/02-agents/INTERACTION-MODES.md`.
