#!/usr/bin/env bash
echo "target is not on this desk" >&2; exit 1
exec /home/rootrecord/.ollama/skills/companions/scripts/start-dev-desk.sh "$@"
