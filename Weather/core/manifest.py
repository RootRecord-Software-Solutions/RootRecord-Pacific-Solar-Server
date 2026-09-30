# ==============================================================================
# FILE: Weather/core/manifest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Per-resource state tracking (etag, hash, fetch timestamps, failures).

Single JSON file per nws_plan.md Section 6: `hfo/_manifest.json`. This module
only reads/writes that state -- it has no opinion on what "changed" means
(that's core/change_detection.py) and makes no HTTP calls of its own.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import threading  # info: import threading
from dataclasses import dataclass, field, asdict  # info: from dataclasses import dataclass , field , asdict
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from typing import Any  # info: from typing import Any


MANIFEST_FILENAME = "_manifest.json"  # info: set MANIFEST_FILENAME


# ====================================================
# SECTION: class ResourceState
# What it does: ResourceState.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class ResourceState:  # info: class ResourceState
    resource_id: str  # info: set resource_id
    url: str  # info: set url
    local_resource_dir: str  # info: set local_resource_dir
    current_fetch_timestamp_hst: str | None = None  # ISO string, HST
    etag: str | None = None  # info: set etag
    last_modified: str | None = None  # info: set last_modified
    content_length: int | None = None  # info: set content_length
    content_sha256: str | None = None  # info: set content_sha256
    consecutive_failures: int = 0  # info: set consecutive_failures
    last_failure_at: str | None = None  # info: set last_failure_at
    last_success_at: str | None = None  # info: set last_success_at

    def to_dict(self) -> dict[str, Any]:  # info: def to_dict
        return asdict(self)  # info: return asdict ( self )

    @classmethod  # info: decorator classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ResourceState":  # info: def from_dict
        known = {f: d.get(f) for f in cls.__dataclass_fields__}  # info: set known
        return cls(**known)  # info: return cls ( ** known )


# ====================================================
# SECTION: class Manifest
# What it does: Loads/holds/saves the full `_manifest.json` for one base_dir (e.g. `hfo/`).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Manifest:  # info: class Manifest
    """Loads/holds/saves the full `_manifest.json` for one base_dir (e.g. `hfo/`)."""  # info: """Loads/holds/saves the full `_manifest.json` for one base_dir (e.g. `hfo/`)."""

    def __init__(self, base_dir: str):  # info: def __init__
        self.base_dir = base_dir  # info: self . base_dir = base_dir
        self.path = Path(base_dir) / MANIFEST_FILENAME  # info: self . path = Path ( base_dir )
        self._data: dict[str, ResourceState] = {}  # info: self . _data : dict [ str ,
        # Fetch modules now run concurrently (scheduler/run_cycle.py), each
        # calling get_or_create/record_* on this SAME Manifest instance from
        # its own thread -- guard every read/write of _data so that's safe
        # (a bare dict was fine when everything ran on one thread in
        # sequence; it is not fine once two modules can call save() or
        # get_or_create() for a not-yet-seen resource_id at the same time).
        self._lock = threading.Lock()  # info: self . _lock = threading . Lock (

    def load(self) -> "Manifest":  # info: def load
        if self.path.is_file():  # info: if self . path . is_file ( )
            try:  # info: try :
                raw = json.loads(self.path.read_text(encoding="utf-8"))  # info: set raw
            except (json.JSONDecodeError, OSError):  # info: except ( json . JSONDecodeError , OSError )
                raw = {}  # info: set raw
            self._data = {  # info: self . _data = {
                rid: ResourceState.from_dict(entry) for rid, entry in raw.items()  # info: set rid
            }  # info: }
        return self  # info: return self

    def save(self) -> None:  # info: def save
        # The scheduler runs fetch modules concurrently.  The snapshot and the
        # temp-file replace must stay under the SAME lock: otherwise two
        # concurrent saves can each take a valid snapshot and then race their
        # writes, allowing an older snapshot to overwrite a newer one.  That
        # can silently erase a freshly recorded content_sha256 and make the
        # next poll treat unchanged content as changed again.
        with self._lock:  # info: with self . _lock :
            self.path.parent.mkdir(parents=True, exist_ok=True)  # info: self . path . parent . mkdir (
            serializable = {rid: state.to_dict() for rid, state in self._data.items()}  # info: set serializable
            tmp = self.path.with_suffix(".tmp")  # info: set tmp
            tmp.write_text(  # info: tmp . write_text (
                json.dumps(serializable, indent=2, ensure_ascii=False),  # info: json . dumps ( serializable , indent =
                encoding="utf-8",  # info: set encoding
            )  # info: )
            tmp.replace(self.path)  # atomic swap while the manifest lock is held

    def get(self, resource_id: str) -> ResourceState | None:  # info: def get
        with self._lock:  # info: with self . _lock :
            return self._data.get(resource_id)  # info: return self . _data . get ( resource_id

    def get_or_create(self, resource_id: str, url: str, local_resource_dir: str) -> ResourceState:  # info: def get_or_create
        with self._lock:  # info: with self . _lock :
            state = self._data.get(resource_id)  # info: set state
            if state is None:  # info: if state is None :
                state = ResourceState(resource_id=resource_id, url=url, local_resource_dir=local_resource_dir)  # info: set state
                self._data[resource_id] = state  # info: self . _data [ resource_id ] = state
            return state  # info: return state

    def record_success(self, resource_id: str, *, etag: str | None, last_modified: str | None,  # info: def record_success
                        content_length: int | None, content_sha256: str | None,  # info: set content_length
                        fetched_at_hst_iso: str) -> None:  # info: set fetched_at_hst_iso
        with self._lock:  # info: with self . _lock :
            state = self._data[resource_id]  # info: set state
            state.etag = etag  # info: state . etag = etag
            state.last_modified = last_modified  # info: state . last_modified = last_modified
            state.content_length = content_length  # info: state . content_length = content_length
            state.content_sha256 = content_sha256  # info: state . content_sha256 = content_sha256
            state.current_fetch_timestamp_hst = fetched_at_hst_iso  # info: state . current_fetch_timestamp_hst = fetched_at_hst_iso
            state.consecutive_failures = 0  # info: state . consecutive_failures = 0
            state.last_success_at = fetched_at_hst_iso  # info: state . last_success_at = fetched_at_hst_iso

    def record_unchanged(self, resource_id: str, *, confirmed_at_hst_iso: str) -> None:  # info: def record_unchanged
        """A 304/matched-hash result -- update the 'still fresh' timestamp only.

        Per nws_plan.md Section 3, this does NOT touch current_fetch_timestamp_hst
        (that stays as the timestamp of the version actually on disk, which is
        what archiver.py needs when the NEXT real change is detected).
        """
        with self._lock:  # info: with self . _lock :
            state = self._data[resource_id]  # info: set state
            state.last_success_at = confirmed_at_hst_iso  # info: state . last_success_at = confirmed_at_hst_iso
            state.consecutive_failures = 0  # info: state . consecutive_failures = 0

    def record_failure(self, resource_id: str, *, failed_at_hst_iso: str) -> None:  # info: def record_failure
        with self._lock:  # info: with self . _lock :
            state = self._data[resource_id]  # info: set state
            state.consecutive_failures += 1  # info: state . consecutive_failures += 1
            state.last_failure_at = failed_at_hst_iso  # info: state . last_failure_at = failed_at_hst_iso

    def all_states(self) -> dict[str, ResourceState]:  # info: def all_states
        with self._lock:  # info: with self . _lock :
            return dict(self._data)  # info: return dict ( self . _data )
