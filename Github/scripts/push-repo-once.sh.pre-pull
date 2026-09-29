#!/usr/bin/env bash
# ==============================================================================
# push-repo-once.sh  — one check-stage-commit-push for a repos.conf id
# Usage: push-repo-once.sh <id>
# Size guard: skip files > MAX_FILE_MB (default 90). Token from master-key.env.
# Baks/logs: /home/rootrecord/Database/GITHUB/
# ==============================================================================
set -euo pipefail
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
ensure_bak_root
# load_token optional — SSH remotes; keep for API tools if needed
load_token || true

ID="${1:-}"
[[ -n "$ID" ]] || { echo "usage: $0 <repo-id>"; exit 2; }

remote_url() { echo "git@github.com:${1}.git"; }

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

  # size guard
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

  if git diff --quiet && git diff --cached --quiet && [[ -z "$(git ls-files --others --exclude-standard)" ]]; then
    echo "— [$id] no changes"
    exit 0
  fi

  git add -A
  n=$(git diff --cached --name-only | wc -l | tr -d ' ')
  msg="auto: $(date -u +%Y-%m-%dT%H:%MZ) desk sync ($n file(s))"
  git commit -m "$msg" >/dev/null
  branch=$(git rev-parse --abbrev-ref HEAD)
  git push -u "$remote_name" "HEAD:refs/heads/$branch" 2>&1 | redact
  echo "↑ [$id] $n files → $slug ($branch)"
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$id] pushed $branch ($n file(s)) → $slug" \
    >> "$BAK_ROOT/logs/${id}.log"
  exit 0
done < <(grep -v '^#' "$REPOS_CONF" | grep -v '^[[:space:]]*$')

(( found )) || { echo "ERROR: id not in repos.conf: $ID" >&2; exit 1; }
