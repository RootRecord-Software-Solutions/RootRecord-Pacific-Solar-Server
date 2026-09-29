#!/usr/bin/env bash
# ==============================================================================
# push-repo-once.sh  — one check-stage-commit-push for a repos.conf id
# Usage: push-repo-once.sh <id>
# Size guard: skip files > MAX_FILE_MB (default 90). Token from master-key.env.
# Baks/logs: /home/rootrecord/Database/GITHUB/
#
# When GitHub merges into the live skills tree, arm + immediately schedule a
# deferred full poller stack reload (bash schedule-stack-reload.sh). Do not rely
# on the parent sync-all process still running old in-memory code after merge.
# Never reset --hard. Never force-push.
# ==============================================================================
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
ensure_bak_root
mkdir -p "$BAK_ROOT/flags" "$BAK_ROOT/logs"
load_token || true

ID="${1:-}"
[[ -n "$ID" ]] || { echo "usage: $0 <repo-id>"; exit 2; }

remote_url() { echo "git@github.com:${1}.git"; }

RELOAD_SCRIPT="/home/rootrecord/.ollama/skills/automations/scripts/schedule-stack-reload.sh"

mark_code_pulled() {
  local id="$1"
  local local_path="$2"
  local remote_head="$3"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) id=$id head=$remote_head path=$local_path" \
    >> "$BAK_ROOT/flags/code-pulled.log"
  echo "$remote_head" > "$BAK_ROOT/flags/code-pulled.$id"
  # Skills tree runs the poller — merge requires full stack reload.
  if [[ "$id" == "skills" || "$local_path" == *"/.ollama/skills"* || "$local_path" == *"/skills" ]]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) skills-code-pulled id=$id head=$remote_head" \
      > "$BAK_ROOT/flags/reload-poller-stack"
    echo "↻ [$id] CODE_PULLED — poller stack reload armed"
    # Schedule NOW from disk (merged tree), not from parent sync-all's old in-memory script.
    if [[ -f "$RELOAD_SCRIPT" ]]; then
      bash "$RELOAD_SCRIPT" || echo "⚠ [$id] schedule-stack-reload failed"
    else
      echo "⚠ [$id] missing $RELOAD_SCRIPT — flag left for next sync-all"
    fi
  fi
}

found=0
while IFS=$'\t' read -r id enabled mode local_path slug remote_name; do
  [[ "$id" =~ ^#.*$ || -z "${id:-}" ]] && continue
  [[ "$id" == "$ID" ]] || continue
  found=1
  [[ "$enabled" == "1" ]] || { echo "[skip] $id disabled"; exit 0; }

  if [[ "$mode" == "inplace" ]]; then
    root="$local_path"
  else
    root="$BAK_ROOT/worktrees/$id"
    mkdir -p "$root"
    if [[ ! -d "$root/.git" ]]; then
      echo "ERROR: mirror worktree missing — run setup-all-remotes.sh first" >&2
      exit 1
    fi
    rsync -a --delete \
      --exclude '.git' \
      --exclude 'node_modules' \
      --exclude '.next' \
      --exclude 'tsconfig.tsbuildinfo' \
      "$local_path"/ "$root"/
  fi

  [[ -d "$root/.git" ]] || { echo "ERROR: not a git repo: $root" >&2; exit 1; }
  cd "$root"
  git remote set-url "$remote_name" "$(remote_url "$slug")" 2>/dev/null \
    || git remote set-url origin "$(remote_url "$slug")"

  oversized=0
  while IFS= read -r -d '' f; do
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
    if (( sz > MAX_FILE_MB * 1024 * 1024 )); then
      echo "✗ skip oversized (${sz}B): $f"
      oversized=1
    fi
  done < <(git ls-files -mo --exclude-standard -z 2>/dev/null || true)
  if (( oversized )); then
    echo "✗ $id aborted: file(s) over ${MAX_FILE_MB}MB"
    exit 1
  fi

  branch=$(git rev-parse --abbrev-ref HEAD)

  if ! git diff --quiet || ! git diff --cached --quiet || [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
    git add -A
    n=$(git diff --cached --name-only | wc -l | tr -d ' ')
    msg="auto: $(date -u +%Y-%m-%dT%H:%MZ) desk sync ($n file(s))"
    git commit -m "$msg" >/dev/null
    echo "↑ [$id] committed $n local file(s)"
  else
    n=0
    echo "— [$id] no local changes"
  fi

  echo "↓ [$id] fetching $remote_name/$branch"

  if ! git fetch "$remote_name" "$branch" 2>&1 | redact; then
    echo "✗ [$id] fetch failed; local history preserved" >&2
    exit 1
  fi

  remote_ref="$remote_name/$branch"

  if ! git rev-parse --verify "$remote_ref" >/dev/null 2>&1; then
    echo "✗ [$id] remote branch unavailable after fetch: $remote_ref" >&2
    exit 1
  fi

  local_head="$(git rev-parse HEAD)"
  remote_head="$(git rev-parse "$remote_ref")"

  if [[ "$local_head" == "$remote_head" ]]; then
    echo "— [$id] local and GitHub already match"
  elif git merge-base --is-ancestor "$remote_ref" HEAD; then
    echo "↑ [$id] local is ahead of GitHub"
  else
    echo "↓ [$id] GitHub has changes; merging $remote_ref"
    if ! git merge --no-edit "$remote_ref" 2>&1 | redact; then
      echo "✗ [$id] merge conflict; aborting safely" >&2
      git merge --abort >/dev/null 2>&1 || true
      echo "✗ [$id] local history preserved; nothing was force-pushed" >&2
      exit 1
    fi
    echo "✓ [$id] GitHub changes merged into local $branch"
    mark_code_pulled "$id" "$local_path" "$(git rev-parse HEAD)"
  fi

  for attempt in 1 2; do
    local_head="$(git rev-parse HEAD)"
    git fetch "$remote_name" "$branch" >/dev/null 2>&1 || {
      echo "✗ [$id] final fetch failed" >&2
      exit 1
    }
    remote_ref="$remote_name/$branch"
    remote_head="$(git rev-parse "$remote_ref")"

    if [[ "$local_head" == "$remote_head" ]]; then
      echo "— [$id] nothing to push"
      exit 0
    fi

    if ! git merge-base --is-ancestor "$remote_ref" HEAD; then
      echo "↓ [$id] remote changed during sync; merging before push (attempt $attempt)"
      if ! git merge --no-edit "$remote_ref" 2>&1 | redact; then
        git merge --abort >/dev/null 2>&1 || true
        echo "✗ [$id] final merge conflict; local history preserved" >&2
        exit 1
      fi
      mark_code_pulled "$id" "$local_path" "$(git rev-parse HEAD)"
    fi

    if git push -u "$remote_name" "HEAD:refs/heads/$branch" 2>&1 | redact; then
      echo "↑ [$id] $n files → $slug ($branch)"
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$id] pushed $branch ($n file(s)) → $slug" >> "$BAK_ROOT/logs/$id.log"
      exit 0
    fi

    echo "↻ [$id] push raced with another writer; retrying" >&2
  done

  echo "✗ [$id] push failed after race-safe retries; local history preserved" >&2
  exit 1
done < <(grep -v '^#' "$REPOS_CONF" | grep -v '^[[:space:]]*$')

(( found )) || { echo "ERROR: id not in repos.conf: $ID" >&2; exit 1; }
