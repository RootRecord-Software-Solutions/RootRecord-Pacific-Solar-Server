#!/bin/bash
# Forced command for the AWS fetch key. Prints the current snapshot only.
set -euo pipefail
exec /bin/cat "/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Communications/network/local-data-globe/rebroadcast/hawaii-current.ndjson"
