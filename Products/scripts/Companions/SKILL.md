---
name: companions
description: >-
  Optional companion processes at desk online (poller, local-edge). Does not start OBS or Electron.
---

# companions

This folder **is** the runtime.

Ava-Core `scripts/start-ava-companions.sh` execs this. AVA_ROOT is the Ava-Core tree. Logs and toggles use the `database` skill store.

No Electron. Origin is launch.sh on :8787.

`scripts/start-dev-desk.sh` launches `companions/dev-desk`.

Topic index: `boot-idle-origin`.
