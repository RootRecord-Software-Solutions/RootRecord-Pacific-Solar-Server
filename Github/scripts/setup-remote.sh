#!/usr/bin/env bash
# ============================================================================
# github/scripts/setup-remote.sh — ensure origin remote for one repos.conf id
# ----------------------------------------------------------------------------
# WHAT: Configure remote URL with token (never printed). Args: <id>
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail  # info: set

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set HERE

# shellcheck disable=SC1091
source "$HERE/common.sh"  # info: source

ID="${1:?id required}"  # info: set ID

load_token  # info: load_token

# Read the tab-separated row for this repo id.
line="$(awk -F '\t' -v want="$ID" '$1 == want { print; exit }' "$REPOS_CONF" || true)"  # info: set line

[[ -n "$line" ]] || {  # info: command
  echo "ERROR: id $ID not in repos.conf" >&2  # info: echo
  exit 1  # info: exit
}  # info: command

IFS=$'\t' read -r id enabled mode local_path slug remote_name <<<"$line"  # info: set IFS

if [[ "$mode" == "mirror" ]]; then  # info: if
  work="$WORKTREE_ROOT/$id"  # info: set work
  if [[ ! -d "$work/.git" ]]; then  # info: if
    rm -rf "$work"  # info: rm
    echo "[clone] $id → $work"  # info: echo
    git clone --branch main "git@github.com:${slug}.git" "$work"  # info: git
  fi  # info: fi
  git -C "$work" remote set-url "$remote_name" "git@github.com:${slug}.git" 2>/dev/null \
    || git -C "$work" remote add "$remote_name" "git@github.com:${slug}.git"  # info: command
  echo "[ok] $id mirror → github.com/$slug"  # info: echo
  exit 0  # info: exit
fi  # info: fi

mkdir -p "$local_path"  # info: mkdir

if [[ ! -d "$local_path/.git" ]]; then  # info: if
  echo "[skip] $id — no .git at $local_path"  # info: echo
  exit 0  # info: exit
fi  # info: fi

url="https://x-access-token:${GITHUB_TOKEN}@github.com/${slug}.git"  # info: set url

git -C "$local_path" remote remove "$remote_name" 2>/dev/null || true  # info: git
git -C "$local_path" remote add "$remote_name" "$url"  # info: git

echo "[ok] $id remote $remote_name → github.com/$slug"  # info: echo
