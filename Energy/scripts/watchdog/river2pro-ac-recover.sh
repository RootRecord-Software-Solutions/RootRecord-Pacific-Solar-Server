#!/usr/bin/env bash
# River entry. BLE-only AC force while the pack is in range. Never forces AC off.
set -euo pipefail
exec "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Energy/scripts/watchdog/ac-force.sh" river2pro "$@"
