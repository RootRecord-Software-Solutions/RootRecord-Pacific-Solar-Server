#!/usr/bin/env bash
# ============================================================================
# github/scripts/setup-remote.sh — ensure origin remote for one repos.conf id
# ----------------------------------------------------------------------------
# WHAT: Configure remote URL with token (never printed). Args: <id>
# Layout style (standing): keep this header.
# ============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck disable=SC1091
source "$HERE/common.sh"

ID="${1:?id required}"

load_token

# Read the tab-separated row for this repo id.
line="$(awk -F '\t' -v want="$ID" '$1 == want { print; exit }' "$REPOS_CONF" || true)"

[[ -n "$line" ]] || {
  echo "ERROR: id $ID not in repos.conf" >&2
  exit 1
}

IFS=$'\t' read -r id enabled mode local_path slug remote_name <<<"$line"

if [[ "$mode" == "mirror" ]]; then
  work="$BAK_ROOT/worktrees/$id"
  if [[ ! -d "$work/.git" ]]; then
    rm -rf "$work"
    echo "[clone] $id → $work"
    git clone --branch main "git@github.com:${slug}.git" "$work"
  fi
  git -C "$work" remote set-url "$remote_name" "git@github.com:${slug}.git" 2>/dev/null \
    || git -C "$work" remote add "$remote_name" "git@github.com:${slug}.git"
  echo "[ok] $id mirror → github.com/$slug"
  exit 0
fi

mkdir -p "$local_path"

if [[ ! -d "$local_path/.git" ]]; then
  echo "[skip] $id — no .git at $local_path"
  exit 0
fi

url="https://x-access-token:${GITHUB_TOKEN}@github.com/${slug}.git"

git -C "$local_path" remote remove "$remote_name" 2>/dev/null || true
git -C "$local_path" remote add "$remote_name" "$url"

echo "[ok] $id remote $remote_name → github.com/$slug"
