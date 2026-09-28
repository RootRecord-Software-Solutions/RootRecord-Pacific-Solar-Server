#!/usr/bin/env bash
set -euo pipefail

REPO="/home/rootrecord/Database/WEATHER"
REMOTE="origin"
BRANCH="main"
LOCK="/tmp/rootrecord-weather-db-sync.lock"

exec 9>"$LOCK"
flock -n 9 || exit 0

cleanup_temp_files() {
    # Remove only transient Git/sync artifacts.
    # Never remove tracked weather data.
    find "$REPO/.git" -type f \
        \( -name "*.lock" -o -name "*.tmp" -o -name "*.part" -o -name "*~" -o -name "*.swp" \) \
        -delete 2>/dev/null || true

    find "$REPO" -type f \
        \( -name "*.tmp" -o -name "*.part" -o -name "*.swp" -o -name "*~" \) \
        -not -path "$REPO/.git/*" \
        -delete 2>/dev/null || true
}

trap cleanup_temp_files EXIT

cd "$REPO"

# GitHub may be unreachable during off-grid/network outages.
# Treat that as a deferred sync, not a failed automation.
if ! git fetch "$REMOTE" "$BRANCH" --quiet; then
    echo "Weather database sync: GitHub unavailable; will retry on next scheduled cycle."
    exit 0
fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    git add -A
    if ! git diff --cached --quiet; then
        git commit -m "Initial weather database sync"
    fi
    git push -u "$REMOTE" "$BRANCH"
    exit 0
fi

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "$REMOTE/$BRANCH")"

# If GitHub has moved ahead, propagate remote deletions locally
# before merging. This intentionally does NOT use reset --hard.
if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then
    BASE="$(git merge-base "$LOCAL_SHA" "$REMOTE_SHA")"

    while IFS= read -r path; do
        [ -n "$path" ] || continue
        rm -rf -- "$REPO/$path"
    done < <(git diff --name-only --diff-filter=D "$BASE" "$REMOTE_SHA")

    git add -A

    if ! git diff --cached --quiet; then
        git commit -m "Sync weather database changes"
    fi

    if ! git merge --no-edit "$REMOTE/$BRANCH"; then
        git merge --abort || true
        echo "Weather database sync: merge conflict; leaving local data untouched."
        exit 1
    fi
fi

git add -A

if ! git diff --cached --quiet; then
    git commit -m "Update weather database"
fi

if ! git push "$REMOTE" "$BRANCH" --quiet; then
    echo "Weather database sync: GitHub push unavailable; will retry on next scheduled cycle."
    exit 0
fi
