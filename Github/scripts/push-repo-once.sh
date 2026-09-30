#!/usr/bin/env bash
# ==============================================================================
# push-repo-once.sh  — one check-stage-commit-push for a repos.conf id
# Usage: push-repo-once.sh <id>
# Size guard: skip files > MAX_FILE_MB (default 90). Token from master-key.env.
# Baks/logs: /home/rootrecord/Database/GITHUB/
#
# When GitHub merges into the live Pacific (or legacy skills) tree, arm +
# schedule a deferred full poller stack reload via Pacific Automations.
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

# Live runtime is Pacific — not G2 automations
RELOAD_SCRIPT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/scripts/stack/schedule-stack-reload.sh"

# True when this repo hosts poller/jobs code that must reload after merge
is_runtime_code_tree() {
  local id="$1" local_path="$2"
  # G2 (~/.ollama/skills) pulls are NOT runtime code: syncs must not restart the poller (2026-09-29).
  [[ "$id" == "pacific" ]] && return 0
  [[ "$local_path" == *"RootRecord-Pacific-Solar-Server"* ]] && return 0
  return 1
}

# Public umbrella contains the live Pacific tree plus high-churn database files.
# Reload only when a pull changes Pacific runtime code. Database telemetry must not.
ecosystem_pull_needs_reload() {
  local old="$1" new="$2" f files
  [[ -n "$old" && -n "$new" ]] || return 1
  files="$(git -c core.quotePath=false diff --name-only "$old" "$new" 2>/dev/null)" || return 1
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    case "$f" in
      "1 - Servers/1 - RootRecord-Pacific-Solar-Server/"*)
        case "${f##*/}" in
          *.md|*.MD|*.markdown|README|README.*) ;;
          *) return 0 ;;
        esac
        ;;
    esac
  done <<< "$files"
  return 1
}

# Drop live telemetry from the index after git add -A. Worktree files stay.
unstage_ecosystem_runtime() {
  local spec skip_file="$GITHUB_SCRIPTS/ecosystem-skip-autocommit.txt"
  [[ -f "$skip_file" ]] || return 0
  while IFS= read -r spec || [[ -n "${spec:-}" ]]; do
    [[ -z "${spec:-}" || "$spec" =~ ^[[:space:]]*# ]] && continue
    git reset -q -- "$spec" 2>/dev/null || true
  done < "$skip_file"
}

# True when every file changed old..new is documentation (*.md, *.markdown, README*).
# Docs-only pulls must not restart the poller stack (Alexander 2026-09-29). Unknown/empty diff -> false (reload as before).
pull_is_docs_only() {
  local old="$1" new="$2" f files any=0
  [[ -n "$old" && -n "$new" ]] || return 1
  files="$(git -c core.quotePath=false diff --name-only "$old" "$new" 2>/dev/null)" || return 1
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    any=1
    case "${f##*/}" in
      *.md|*.MD|*.markdown|README|README.*) ;;
      *) return 1 ;;
    esac
  done <<< "$files"
  (( any ))
}

mark_code_pulled() {
  local id="$1"
  local local_path="$2"
  local remote_head="$3"
  local old_head="${4:-}"
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) id=$id head=$remote_head path=$local_path" \
    >> "$BAK_ROOT/flags/code-pulled.log"
  echo "$remote_head" > "$BAK_ROOT/flags/code-pulled.$id"
  if [[ "$id" == "ecosystem" ]]; then
    if ! ecosystem_pull_needs_reload "$old_head" "$remote_head"; then
      echo "— [$id] pull did not change Pacific runtime code — no poller stack reload"
      return 0
    fi
  elif is_runtime_code_tree "$id" "$local_path" && pull_is_docs_only "$old_head" "$remote_head"; then
    echo "— [$id] docs-only pull (*.md/README) — no poller stack reload"
    return 0
  elif ! is_runtime_code_tree "$id" "$local_path"; then
    return 0
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) runtime-code-pulled id=$id head=$remote_head" \
    > "$BAK_ROOT/flags/reload-poller-stack"
  echo "↻ [$id] CODE_PULLED — poller stack reload armed"
  if [[ -f "$RELOAD_SCRIPT" ]]; then
    bash "$RELOAD_SCRIPT" || echo "⚠ [$id] schedule-stack-reload failed"
  else
    echo "⚠ [$id] missing $RELOAD_SCRIPT — flag left for next sync-all"
  fi
}

found=0
while IFS=$'\t' read -r id enabled mode local_path slug remote_name; do
  [[ "$id" =~ ^#.*$ || -z "${id:-}" ]] && continue
  [[ "$id" == "$ID" ]] || continue
  found=1
  [[ "$enabled" == "1" ]] || { echo "[skip] $id disabled"; exit 0; }

  mirror_writeback() {
    [[ "$mode" == "mirror" ]] || return 0
    rsync -a --exclude '.git' "$root"/ "$local_path"/
    echo "↓ [$id] merged GitHub copy written back to the live folder"
  }

  if [[ "$mode" == "inplace" ]]; then
    root="$local_path"
  else
    root="$BAK_ROOT/worktrees/$id"
    if [[ ! -d "$root/.git" ]]; then
      bash "$GITHUB_SCRIPTS/setup-remote.sh" "$id" || exit 1
    fi
    [[ -d "$root/.git" ]] || { echo "ERROR: mirror worktree missing for $id" >&2; exit 1; }
    rsync -a --delete \
      --exclude '.git' \
      --exclude '.venv' \
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
    if [[ "$id" == "ecosystem" ]]; then
      unstage_ecosystem_runtime
    fi
    if git diff --cached --quiet; then
      n=0
      echo "— [$id] no committable local changes"
    else
      n=$(git diff --cached --name-only | wc -l | tr -d ' ')
      msg="auto: $(date -u +%Y-%m-%dT%H:%MZ) desk sync ($n file(s))"
      git commit -m "$msg" >/dev/null
      echo "↑ [$id] committed $n local file(s)"
    fi
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
    mirror_writeback
    mark_code_pulled "$id" "$local_path" "$(git rev-parse HEAD)" "$local_head"
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
      mirror_writeback
      mark_code_pulled "$id" "$local_path" "$(git rev-parse HEAD)" "$local_head"
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
