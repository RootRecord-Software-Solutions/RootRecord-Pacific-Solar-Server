# ==============================================================================
# FILE: Weather/scripts/sync-weather-database.sh
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: shell
# ==============================================================================
#!/usr/bin/env bash
set -euo pipefail  # info: set

REPO="/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Weather"  # info: set REPO
REMOTE="origin"  # info: set REMOTE
BRANCH="main"  # info: set BRANCH
LOCK="/tmp/rootrecord-weather-db-sync.lock"  # info: set LOCK

exec 9>"$LOCK"  # info: exec
flock -n 9 || exit 0  # info: flock

# ====================================================
# SECTION: function cleanup_temp_files
# What it does: cleanup temp files.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
cleanup_temp_files() {  # info: cleanup_temp_files
    # Remove only transient Git/sync artifacts.
    # Never remove tracked weather data.
    find "$REPO/.git" -type f \
        \( -name "*.lock" -o -name "*.tmp" -o -name "*.part" -o -name "*~" -o -name "*.swp" \) \
        -delete 2>/dev/null || true  # info: -delete

    find "$REPO" -type f \
        \( -name "*.tmp" -o -name "*.part" -o -name "*.swp" -o -name "*~" \) \
        -not -path "$REPO/.git/*" \
        -delete 2>/dev/null || true  # info: -delete
}  # info: command

trap cleanup_temp_files EXIT  # info: trap

# Guard: without its own .git, git would act on the parent Database repo.
[ -d "$REPO/.git" ] || { echo "Weather database sync: $REPO is not its own git repo; skipping."; exit 0; }  # info: command

cd "$REPO"  # info: cd

# GitHub may be unreachable during off-grid/network outages.
# Treat that as a deferred sync, not a failed automation.
if ! git fetch "$REMOTE" "$BRANCH" --quiet; then  # info: if
    echo "Weather database sync: GitHub unavailable; will retry on next scheduled cycle."  # info: echo
    exit 0  # info: exit
fi  # info: fi

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then  # info: if
    git add -A  # info: git
    if ! git diff --cached --quiet; then  # info: if
        git commit -m "Initial weather database sync"  # info: git
    fi  # info: fi
    git push -u "$REMOTE" "$BRANCH"  # info: git
    exit 0  # info: exit
fi  # info: fi

LOCAL_SHA="$(git rev-parse HEAD)"  # info: set LOCAL_SHA
REMOTE_SHA="$(git rev-parse "$REMOTE/$BRANCH")"  # info: set REMOTE_SHA

# If GitHub has moved ahead, propagate remote deletions locally
# before merging. This intentionally does NOT use reset --hard.
if [ "$LOCAL_SHA" != "$REMOTE_SHA" ]; then  # info: if
    BASE="$(git merge-base "$LOCAL_SHA" "$REMOTE_SHA")"  # info: set BASE

    while IFS= read -r path; do  # info: while
        [ -n "$path" ] || continue  # info: command
        rm -rf -- "$REPO/$path"  # info: rm
    done < <(git diff --name-only --diff-filter=D "$BASE" "$REMOTE_SHA")  # info: done

    git add -A  # info: git

    if ! git diff --cached --quiet; then  # info: if
        git commit -m "Sync weather database changes"  # info: git
    fi  # info: fi

    if ! git merge --no-edit "$REMOTE/$BRANCH"; then  # info: if
        git merge --abort || true  # info: git
        echo "Weather database sync: merge conflict; leaving local data untouched."  # info: echo
        exit 1  # info: exit
    fi  # info: fi
fi  # info: fi

git add -A  # info: git

if ! git diff --cached --quiet; then  # info: if
    git commit -m "Update weather database"  # info: git
fi  # info: fi

if ! git push "$REMOTE" "$BRANCH" --quiet; then  # info: if
    echo "Weather database sync: GitHub push unavailable; will retry on next scheduled cycle."  # info: echo
    exit 0  # info: exit
fi  # info: fi
