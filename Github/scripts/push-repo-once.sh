#!/usr/bin/env bash
# ==============================================================================
# push-repo-once.sh  — one check-stage-commit-push for a repos.conf id
# Usage: push-repo-once.sh <id>
# Size guard: skip files > MAX_FILE_MB (default 90). Token from master-key.env.
# Baks/logs: 2 - RootRecord-Database/Github/  Worktrees: Github-worktrees/ (umbrella root)
#
# When GitHub merges into the live Pacific (or legacy skills) tree, arm +
# schedule a deferred full poller stack reload via Pacific Automations.
# Never reset --hard. Never force-push.
# ==============================================================================
set -euo pipefail  # info: set
# shellcheck disable=SC1091
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"  # info: source
ensure_bak_root  # info: ensure_bak_root
mkdir -p "$BAK_ROOT/flags" "$BAK_ROOT/logs"  # info: mkdir
load_token || true  # info: load_token

ID="${1:-}"  # info: set ID
[[ -n "$ID" ]] || { echo "usage: $0 <repo-id>"; exit 2; }  # info: command

# ====================================================
# SECTION: function remote_url
# What it does: remote url.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
remote_url() { echo "git@github.com:${1}.git"; }  # info: remote_url

# Live runtime is Pacific — not G2 automations
RELOAD_SCRIPT="/home/rootrecord/RootRecord-Ecosystem/1 - Servers/1 - RootRecord-Pacific-Solar-Server/Automations/scripts/stack/schedule-stack-reload.sh"  # info: set RELOAD_SCRIPT

# True when this repo hosts poller/jobs code that must reload after merge
# ====================================================
# SECTION: function is_runtime_code_tree
# What it does: is runtime code tree.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
is_runtime_code_tree() {  # info: is_runtime_code_tree
  local id="$1" local_path="$2"  # info: local
  # The public page lives under Pacific but is not poller code. A website merge must not reload the stack.
  [[ "$id" == website || "$id" == website-* ]] && return 1  # info: command
  # G2 (~/.ollama/skills) pulls are NOT runtime code: syncs must not restart the poller (2026-09-29).
  [[ "$id" == "pacific" ]] && return 0  # info: command
  [[ "$local_path" == *"RootRecord-Pacific-Solar-Server"* ]] && return 0  # info: command
  return 1  # info: return
}  # info: command

# Public umbrella contains the live Pacific tree plus high-churn database files.
# Reload only when a pull changes Pacific runtime code. Database telemetry must not.
# ====================================================
# SECTION: function ecosystem_pull_needs_reload
# What it does: ecosystem pull needs reload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ecosystem_pull_needs_reload() {  # info: ecosystem_pull_needs_reload
  local old="$1" new="$2" f files  # info: local
  [[ -n "$old" && -n "$new" ]] || return 1  # info: command
  files="$(git -c core.quotePath=false diff --name-only "$old" "$new" 2>/dev/null)" || return 1  # info: set files
  while IFS= read -r f; do  # info: while
    [[ -n "$f" ]] || continue  # info: command
    case "$f" in  # info: case
      "1 - Servers/1 - RootRecord-Pacific-Solar-Server/"*)  # info: command
        case "${f##*/}" in
          *.md|*.MD|*.markdown|README|README.*) ;;  # info: command
          *) return 0 ;;  # info: command
        esac  # info: esac
        ;;  # info: command
    esac  # info: esac
  done <<< "$files"  # info: done
  return 1  # info: return
}  # info: command

# Drop live telemetry from the index after git add -A. Worktree files stay.
# ====================================================
# SECTION: function unstage_ecosystem_runtime
# What it does: unstage ecosystem runtime.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
unstage_ecosystem_runtime() {  # info: unstage_ecosystem_runtime
  local spec skip_file="$GITHUB_SCRIPTS/ecosystem-skip-autocommit.txt"  # info: local
  [[ -f "$skip_file" ]] || return 0  # info: command
  while IFS= read -r spec || [[ -n "${spec:-}" ]]; do  # info: while
    [[ -z "${spec:-}" || "$spec" =~ ^[[:space:]]*# ]] && continue
    git reset -q -- "$spec" 2>/dev/null || true  # info: git
  done < "$skip_file"  # info: done
}  # info: command

# True when every file changed old..new is documentation (*.md, *.markdown, README*).
# Docs-only pulls must not restart the poller stack (Alexander 2026-09-29). Unknown/empty diff -> false (reload as before).
# ====================================================
# SECTION: function pull_is_docs_only
# What it does: pull is docs only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
pull_is_docs_only() {  # info: pull_is_docs_only
  local old="$1" new="$2" f files any=0  # info: local
  [[ -n "$old" && -n "$new" ]] || return 1  # info: command
  files="$(git -c core.quotePath=false diff --name-only "$old" "$new" 2>/dev/null)" || return 1  # info: set files
  while IFS= read -r f; do  # info: while
    [[ -n "$f" ]] || continue  # info: command
    any=1  # info: set any
    case "${f##*/}" in
      *.md|*.MD|*.markdown|README|README.*) ;;  # info: command
      *) return 1 ;;  # info: command
    esac  # info: esac
  done <<< "$files"  # info: done
  (( any ))  # info: command
}  # info: command

# ====================================================
# SECTION: function mark_code_pulled
# What it does: mark code pulled.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
mark_code_pulled() {  # info: mark_code_pulled
  local id="$1"  # info: local
  local local_path="$2"  # info: local
  local remote_head="$3"  # info: local
  local old_head="${4:-}"  # info: local
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) id=$id head=$remote_head path=$local_path" \
    >> "$BAK_ROOT/flags/code-pulled.log"  # info: command
  echo "$remote_head" > "$BAK_ROOT/flags/code-pulled.$id"  # info: echo
  if [[ "$id" == "ecosystem" ]]; then  # info: if
    if ! ecosystem_pull_needs_reload "$old_head" "$remote_head"; then  # info: if
      echo "— [$id] pull did not change Pacific runtime code — no poller stack reload"  # info: echo
      return 0  # info: return
    fi  # info: fi
  elif is_runtime_code_tree "$id" "$local_path" && pull_is_docs_only "$old_head" "$remote_head"; then  # info: elif
    echo "— [$id] docs-only pull (*.md/README) — no poller stack reload"  # info: echo
    return 0  # info: return
  elif ! is_runtime_code_tree "$id" "$local_path"; then  # info: elif
    return 0  # info: return
  fi  # info: fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) runtime-code-pulled id=$id head=$remote_head" \
    > "$BAK_ROOT/flags/reload-poller-stack"  # info: command
  echo "↻ [$id] CODE_PULLED — poller stack reload armed"  # info: echo
  if [[ -f "$RELOAD_SCRIPT" ]]; then  # info: if
    bash "$RELOAD_SCRIPT" || echo "⚠ [$id] schedule-stack-reload failed"  # info: bash
  else  # info: else
    echo "⚠ [$id] missing $RELOAD_SCRIPT — flag left for next sync-all"  # info: echo
  fi  # info: fi
}  # info: command

found=0  # info: set found
while IFS=$'\t' read -r id enabled mode local_path slug remote_name; do  # info: while
  [[ "$id" =~ ^#.*$ || -z "${id:-}" ]] && continue
  [[ "$id" == "$ID" ]] || continue  # info: command
  found=1  # info: set found
  [[ "$enabled" == "1" ]] || { echo "[skip] $id disabled"; exit 0; }  # info: command

# ====================================================
# SECTION: function mirror_writeback
# What it does: mirror writeback.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
  mirror_writeback() {  # info: mirror_writeback
    [[ "$mode" == "mirror" ]] || return 0  # info: command
    if [[ "$id" == "database" ]]; then  # info: if database
      echo "— [$id] one-way: live folder is not replaced from the worktree"  # info: echo
      return 0  # info: return
    fi  # info: fi
    rsync -a --exclude '.git' "$root"/ "$local_path"/  # info: rsync
    # Same direction for every other mirror id after a GitHub merge: worktree → live.
    # Mainland also refreshes Servers from the worktree at sync start (above).
    echo "↓ [$id] worktree/GitHub copy written back to the live folder"  # info: echo
  }  # info: command

  if [[ "$mode" == "inplace" ]]; then  # info: if
    root="$local_path"  # info: set root
  else  # info: else
    root="$WORKTREE_ROOT/$id"  # info: set root
    if [[ ! -d "$root/.git" ]]; then  # info: if
      bash "$GITHUB_SCRIPTS/setup-remote.sh" "$id" || exit 1  # info: bash
    fi  # info: fi
    [[ -d "$root/.git" ]] || { echo "ERROR: mirror worktree missing for $id" >&2; exit 1; }  # info: command
    # Mainland: Github-worktrees/mainland is canonical git truth. Servers umbrella
    # is a read-through mirror only. Never rsync Servers → worktree (that path
    # restored stale DUCK 0.25 over a good worktree 0.1 as auto desk sync).
    # Pacific/library/website keep live-folder → worktree (edit live).
    # Database is one-way: live → worktree only, and a local delete is not
    # pushed as a wipe of the GitHub copy (--delete stays off).
    if [[ "$id" == "mainland" ]]; then  # info: if
      rsync -a --delete \
        --exclude '.git' \
        --exclude '.venv' \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude 'tsconfig.tsbuildinfo' \
        "$root"/ "$local_path"/  # info: command
      echo "↑ [$id] worktree canonical → umbrella Servers mirror refreshed"  # info: echo
    elif [[ "$id" == "database" ]]; then  # info: elif database
      rsync -a \
        --exclude '.git' \
        --exclude '.venv' \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude 'tsconfig.tsbuildinfo' \
        "$local_path"/ "$root"/  # info: command
    else  # info: else
      rsync -a --delete \
        --exclude '.git' \
        --exclude '.venv' \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude 'tsconfig.tsbuildinfo' \
        "$local_path"/ "$root"/  # info: command
    fi  # info: fi
  fi  # info: fi

  [[ -d "$root/.git" ]] || { echo "ERROR: not a git repo: $root" >&2; exit 1; }  # info: command
  cd "$root"  # info: cd
  git remote set-url "$remote_name" "$(remote_url "$slug")" 2>/dev/null \
    || git remote set-url origin "$(remote_url "$slug")"  # info: command

  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"  # info: set branch
  [[ -n "$branch" && "$branch" != "HEAD" ]] || branch=main  # info: command

  # Mainland README carries an AWS-written status block. Keep the GitHub copy
  # of that block so a desk publish does not replace live numbers.
  if [[ "$id" == "mainland" && -f "$root/README.md" ]]; then  # info: if
    if git fetch "$remote_name" "$branch" >/dev/null 2>&1; then  # info: if
      python3 - "$root" << 'PY'  # info: python3
import pathlib, re, subprocess, sys
root = sys.argv[1]
try:
    remote = subprocess.check_output(["git", "show", "FETCH_HEAD:README.md"], cwd=root, text=True)
except subprocess.CalledProcessError:
    raise SystemExit(0)
local_path = pathlib.Path(root) / "README.md"
local = local_path.read_text()
pat = re.compile(r"<!-- aws-status:start -->.*?<!-- aws-status:end -->", re.S)
remote_block = pat.search(remote)
local_block = pat.search(local)
if not remote_block or not local_block or remote_block.group(0) == local_block.group(0):
    raise SystemExit(0)
local_path.write_text(local[: local_block.start()] + remote_block.group(0) + local[local_block.end() :])
print("kept AWS status block from GitHub")
PY
    else  # info: else
      echo "— [$id] status block left as the desk copy; fetch failed" >&2  # info: echo
    fi  # info: fi
  fi  # info: fi

  oversized=0  # info: set oversized
  while IFS= read -r -d '' f; do  # info: while
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)  # info: set sz
    if (( sz > MAX_FILE_MB * 1024 * 1024 )); then  # info: if
      echo "✗ skip oversized (${sz}B): $f"  # info: echo
      oversized=1  # info: set oversized
    fi  # info: fi
  done < <(git ls-files -mo --exclude-standard -z 2>/dev/null || true)  # info: done
  if (( oversized )); then  # info: if
    echo "✗ $id aborted: file(s) over ${MAX_FILE_MB}MB"  # info: echo
    exit 1  # info: exit
  fi  # info: fi

  has_head=0  # info: set has_head
  if git rev-parse --verify HEAD >/dev/null 2>&1; then has_head=1; fi  # info: if
  if [[ "$has_head" == 0 ]] || ! git diff --quiet || ! git diff --cached --quiet || [[ -n "$(git ls-files --others --exclude-standard)" ]]; then  # info: if
    git add -A  # info: git
    if [[ "$id" == "ecosystem" ]]; then  # info: if
      unstage_ecosystem_runtime  # info: unstage_ecosystem_runtime
    fi  # info: fi
    if [[ "$has_head" == 1 ]] && git diff --cached --quiet; then  # info: if
      n=0  # info: set n
      echo "— [$id] no committable local changes"  # info: echo
    else  # info: else
      n=$(git diff --cached --name-only | wc -l | tr -d ' ')  # info: set n
      msg="auto: $(date -u +%Y-%m-%dT%H:%MZ) desk sync ($n file(s))"  # info: set msg
      git commit -m "$msg" >/dev/null  # info: git
      echo "↑ [$id] committed $n local file(s)"  # info: echo
    fi  # info: fi
  else  # info: else
    n=0  # info: set n
    echo "— [$id] no local changes"  # info: echo
  fi  # info: fi

  if ! git ls-remote --exit-code --heads "$remote_name" "$branch" >/dev/null 2>&1; then  # info: if
    echo "↑ [$id] remote has no $branch; creating it"  # info: echo
    if git push -u "$remote_name" "HEAD:refs/heads/$branch" 2>&1 | redact; then  # info: if
      echo "↑ [$id] $n files → $slug ($branch)"  # info: echo
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$id] pushed $branch ($n file(s)) → $slug" >> "$BAK_ROOT/logs/$id.log"  # info: echo
      exit 0  # info: exit
    fi  # info: fi
    echo "✗ [$id] first push failed; local history preserved" >&2  # info: echo
    exit 1  # info: exit
  fi  # info: fi

  echo "↓ [$id] fetching $remote_name/$branch"  # info: echo

  if ! git fetch "$remote_name" "$branch" 2>&1 | redact; then  # info: if
    echo "✗ [$id] fetch failed; local history preserved" >&2  # info: echo
    exit 1  # info: exit
  fi  # info: fi

  remote_ref="$remote_name/$branch"  # info: set remote_ref

  if ! git rev-parse --verify "$remote_ref" >/dev/null 2>&1; then  # info: if
    echo "✗ [$id] remote branch unavailable after fetch: $remote_ref" >&2  # info: echo
    exit 1  # info: exit
  fi  # info: fi

  local_head="$(git rev-parse HEAD)"  # info: set local_head
  remote_head="$(git rev-parse "$remote_ref")"  # info: set remote_head

  if [[ "$local_head" == "$remote_head" ]]; then  # info: if
    echo "— [$id] local and GitHub already match"  # info: echo
  elif git merge-base --is-ancestor "$remote_ref" HEAD; then  # info: elif
    echo "↑ [$id] local is ahead of GitHub"  # info: echo
  else  # info: else
    echo "↓ [$id] GitHub has changes; merging $remote_ref"  # info: echo
    if ! git merge --no-edit "$remote_ref" 2>&1 | redact; then  # info: if
      echo "✗ [$id] merge conflict; aborting safely" >&2  # info: echo
      git merge --abort >/dev/null 2>&1 || true  # info: git
      echo "✗ [$id] local history preserved; nothing was force-pushed" >&2  # info: echo
      exit 1  # info: exit
    fi  # info: fi
    echo "✓ [$id] GitHub changes merged into local $branch"  # info: echo
    mirror_writeback  # info: mirror_writeback
    mark_code_pulled "$id" "$local_path" "$(git rev-parse HEAD)" "$local_head"  # info: mark_code_pulled
  fi  # info: fi

  for attempt in 1 2; do  # info: for
    local_head="$(git rev-parse HEAD)"  # info: set local_head
    git fetch "$remote_name" "$branch" >/dev/null 2>&1 || {  # info: git
      echo "✗ [$id] final fetch failed" >&2  # info: echo
      exit 1  # info: exit
    }  # info: command
    remote_ref="$remote_name/$branch"  # info: set remote_ref
    remote_head="$(git rev-parse "$remote_ref")"  # info: set remote_head

    if [[ "$local_head" == "$remote_head" ]]; then  # info: if
      echo "— [$id] nothing to push"  # info: echo
      exit 0  # info: exit
    fi  # info: fi

    if ! git merge-base --is-ancestor "$remote_ref" HEAD; then  # info: if
      echo "↓ [$id] remote changed during sync; merging before push (attempt $attempt)"  # info: echo
      if ! git merge --no-edit "$remote_ref" 2>&1 | redact; then  # info: if
        git merge --abort >/dev/null 2>&1 || true  # info: git
        echo "✗ [$id] final merge conflict; local history preserved" >&2  # info: echo
        exit 1  # info: exit
      fi  # info: fi
      mirror_writeback  # info: mirror_writeback
      mark_code_pulled "$id" "$local_path" "$(git rev-parse HEAD)" "$local_head"  # info: mark_code_pulled
    fi  # info: fi

    if git push -u "$remote_name" "HEAD:refs/heads/$branch" 2>&1 | redact; then  # info: if
      echo "↑ [$id] $n files → $slug ($branch)"  # info: echo
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$id] pushed $branch ($n file(s)) → $slug" >> "$BAK_ROOT/logs/$id.log"  # info: echo
      exit 0  # info: exit
    fi  # info: fi

    echo "↻ [$id] push raced with another writer; retrying" >&2  # info: echo
  done  # info: done

  echo "✗ [$id] push failed after race-safe retries; local history preserved" >&2  # info: echo
  exit 1  # info: exit
done < <(grep -v '^#' "$REPOS_CONF" | grep -v '^[[:space:]]*$')

(( found )) || { echo "ERROR: id not in repos.conf: $ID" >&2; exit 1; }  # info: command
