#!/usr/bin/env bash
# ==============================================================================
# common.sh — shared paths and helpers for GitHub sync scripts
# ------------------------------------------------------------------------------
# Never print tokens. Sourced by push-repo-once.sh / sync-all.sh / setup-*.
# Layout style (standing): keep SECTION banners.
# ==============================================================================

# ====================================================
# SECTION: PATHS
# ====================================================
DATABASE_ROOT="${DATABASE_ROOT:-/home/rootrecord/Database}"
BAK_ROOT="${BAK_ROOT:-$DATABASE_ROOT/GITHUB}"
INTAKE_ROOT="${INTAKE_ROOT:-$DATABASE_ROOT/intake}"
ENV_FILE="${ENV_FILE:-/home/rootrecord/master/master-key.env}"
GITHUB_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOS_CONF="${REPOS_CONF:-$GITHUB_SCRIPTS/repos.conf}"
MAX_FILE_MB="${MAX_FILE_MB:-90}"

# ====================================================
# SECTION: HELPERS
# ====================================================

ensure_bak_root() {
  mkdir -p "$BAK_ROOT" "$BAK_ROOT/worktrees" "$BAK_ROOT/logs" "$BAK_ROOT/flags" "$INTAKE_ROOT"
}

load_token() {
  if [[ -z "${GITHUB_TOKEN:-}" && -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
  if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    echo "ERROR: GITHUB_TOKEN missing in $ENV_FILE" >&2
    return 1
  fi
}

redact() { sed -E 's#(x-access-token:)[^@]+@#\1***@#g'; }
