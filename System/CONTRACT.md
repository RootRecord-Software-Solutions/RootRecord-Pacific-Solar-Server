# State aggregator contract

Component: `System/scripts/state-aggregate.py`. Registry: `System/config/program-registry.json`.

## Promises

- One canonical snapshot in Database `System/status/rootrecord-state.json`.
- Projections for agents, a public view, and compact slices. Same facts. Different visibility.
- Every disagreement between a config comment and a running setting is a drift record. The writer does not pick a winner.
- `agent_launchable` stays false. `Automations/execution/execution-broker.py` may answer a read from this snapshot. It refuses restarts, writes, and sends. The poller supervisor remains the only automatic restart.
- Secrets are absent. Credential values are null.

## Consumes

- Process list, `jobs.py` catalog, `relay.conf`, `ensure-relay.sh`, energy last-files, `system-status.json`, `repos.conf`, the migration matrix summary counts, git log subjects.
- The operator ledger path is recorded as present. Its decisions are not turned into permissions.

## Produces

- The snapshot, `rootrecord-state-brief.txt` (the scope slice), and `projections/`.
- Mode 0600. Not auto-committed.

## What can change it

- A measured file changing, or a process starting and stopping.
- An edit to the registry or to this script. Editing the snapshot by hand does nothing: the next reply overwrites it.

## Must never happen

- Launching a program, sending Telegram, opening Bluetooth, or restarting the poller.
- Copying tokens, chat text, or the hostname into `projections/public.json` or the agent slice.
- Treating an empty incident list as all-clear.
- Treating a git commit as a deploy.
