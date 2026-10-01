#!/bin/bash
# Forced command for the AWS fetch key. Prints one current snapshot only.
set -euo pipefail
ROOT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/network/local-data-globe/rebroadcast"
cmd="${SSH_ORIGINAL_COMMAND:-}"
case "$cmd" in
  ""|cat|hawaii-current.ndjson)
    exec /bin/cat "$ROOT/hawaii-current.ndjson"
    ;;
  status-current.json)
    exec /bin/cat "$ROOT/status-current.json"
    ;;
  *)
    echo "denied" >&2
    exit 1
    ;;
esac
