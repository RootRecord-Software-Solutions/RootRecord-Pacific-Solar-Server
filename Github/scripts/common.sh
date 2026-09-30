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
DATABASE_ROOT="${DATABASE_ROOT:-/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database}"  # info: set DATABASE_ROOT
# BAK_ROOT (flags/worktrees/logs/backups) stays OUTSIDE the auto-synced Database git tree;
# must match Automations/scripts/stack/{do,schedule}-stack-reload.sh defaults. (2026-09-29 WO-SRV)
BAK_ROOT="${BAK_ROOT:-/home/rootrecord/Database/GITHUB}"  # info: set BAK_ROOT
INTAKE_ROOT="${INTAKE_ROOT:-$DATABASE_ROOT/Intake}"  # info: set INTAKE_ROOT
ENV_FILE="${ENV_FILE:-/home/rootrecord/master/master-key.env}"  # info: set ENV_FILE
GITHUB_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # info: set GITHUB_SCRIPTS
REPOS_CONF="${REPOS_CONF:-$GITHUB_SCRIPTS/repos.conf}"  # info: set REPOS_CONF
MAX_FILE_MB="${MAX_FILE_MB:-90}"  # info: set MAX_FILE_MB

# ====================================================
# SECTION: HELPERS
# ====================================================

ensure_bak_root() {  # info: ensure_bak_root
  mkdir -p "$BAK_ROOT" "$BAK_ROOT/worktrees" "$BAK_ROOT/logs" "$BAK_ROOT/flags" "$INTAKE_ROOT"  # info: mkdir
}  # info: command

# ====================================================
# SECTION: function load_token
# What it does: load token.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
load_token() {  # info: load_token
  if [[ -z "${GITHUB_TOKEN:-}" && -f "$ENV_FILE" ]]; then  # info: if
    set -a  # info: set
    # shellcheck disable=SC1090
    source "$ENV_FILE"  # info: source
    set +a  # info: set
  fi  # info: fi
  if [[ -z "${GITHUB_TOKEN:-}" ]]; then  # info: if
    echo "ERROR: GITHUB_TOKEN missing in $ENV_FILE" >&2  # info: echo
    return 1  # info: return
  fi  # info: fi
}  # info: command

# ====================================================
# SECTION: function redact
# What it does: redact.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
redact() { sed -E 's#(x-access-token:)[^@]+@#\1***@#g'; }
