"""The "age _current out to archive/MM-DD-YYYY/ under its real fetch
timestamp, then write the new content as _current" mechanic. Per
nws_plan.md Section 2.

Only module that moves/writes fetched bytes to disk. Never makes an HTTP
call and never decides *whether* something changed -- that's
core/change_detection.py's job; by the time this is called, the caller
(fetch/_engine.py) has already decided a real change happened.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.manifest import ResourceState
from core.path_resolver import ResolvedResource


def age_out_and_write(
    base_dir: str,
    resolved: ResolvedResource,
    state: ResourceState,
    body_bytes: bytes,
    fetched_at: datetime,
) -> Path:
    """Move the existing `_current` file to archive/ (under its OWN prior
    fetch timestamp, from the manifest -- not `fetched_at`), then write
    `body_bytes` as the new `_current`. Returns the path written to.

    Sequence, per nws_plan.md Section 2:
      1. Look up the previous _current file's fetch timestamp (manifest).
      2. Move the existing _current file to archive/<MM-DD-YYYY>/<name>_<TS>.<ext>,
         dated by THAT prior timestamp -- never by `fetched_at`.
      3. Write the newly-fetched content as the new _current.

    The manifest itself is updated by the caller (fetch/_engine.py calls
    manifest.record_success after this returns) -- this function only
    touches the filesystem.
    """
    current_path = Path(resolved.current_path(base_dir))
    current_path.parent.mkdir(parents=True, exist_ok=True)

    if current_path.is_file() and state.current_fetch_timestamp_hst:
        prior_fetched_at = datetime.fromisoformat(state.current_fetch_timestamp_hst)
        archive_path = Path(resolved.archive_path(base_dir, prior_fetched_at))
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        # Move, not copy -- no orphaned "extra" _current-tagged file should
        # ever end up in the archive folder, per the plan.
        current_path.replace(archive_path)
    elif current_path.is_file():
        # A _current file exists on disk but the manifest has no timestamp
        # for it (e.g. manifest was lost/reset while data wasn't). Don't
        # silently clobber history with no way to date it -- fall back to
        # this fetch's own timestamp for the outgoing copy rather than
        # deleting it outright.
        archive_path = Path(resolved.archive_path(base_dir, fetched_at))
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        current_path.replace(archive_path)

    current_path.write_bytes(body_bytes)
    return current_path
