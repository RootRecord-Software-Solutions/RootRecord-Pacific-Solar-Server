#!/usr/bin/env bash
echo "target is not on this desk" >&2; exit 1
exec /home/rootrecord/.ollama/skills/ecosystem-history/scripts/host-env-snapshot.sh "$@"
