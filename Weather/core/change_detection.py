# ==============================================================================
# FILE: Weather/core/change_detection.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Three-layer change detection: conditional HTTP -> Content-Length fallback
-> SHA-256 content hash as final authority. Per nws_plan.md Section 3.

Pure logic module: takes what core/http_client.py and core/manifest.py
already know and returns a verdict. Makes no HTTP calls and touches no disk
itself.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
from dataclasses import dataclass  # info: from dataclasses import dataclass

from core.manifest import ResourceState  # info: from core . manifest import ResourceState


# ====================================================
# SECTION: function sha256_of
# What it does: sha256 of.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sha256_of(content: bytes) -> str:  # info: def sha256_of
    return hashlib.sha256(content).hexdigest()  # info: return hashlib . sha256 ( content ) .


# ====================================================
# SECTION: class DetectionVerdict
# What it does: DetectionVerdict.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class DetectionVerdict:  # info: class DetectionVerdict
    changed: bool  # info: set changed
    reason: str  # info: set reason
    new_sha256: str | None = None  # populated whenever content was hashed


# ====================================================
# SECTION: function detect
# What it does: Decide whether the just-fetched response represents a real change. Layer 1 -- conditional HTTP: `core.http_client.get` already sent If-None-Match / If-Modified-Since using the mani
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def detect(  # info: def detect
    state: ResourceState,  # info: set state
    *,  # info: * ,
    was_304: bool,  # info: set was_304
    response_etag: str | None,  # info: set response_etag
    response_last_modified: str | None,  # info: set response_last_modified
    response_content_length: int | None,  # info: set response_content_length
    content: bytes | None,  # info: set content
) -> DetectionVerdict:  # info: ) -> DetectionVerdict :
    """Decide whether the just-fetched response represents a real change.

    Layer 1 -- conditional HTTP: `core.http_client.get` already sent
    If-None-Match / If-Modified-Since using the manifest's stored etag/
    last-modified. A 304 is the server's own authoritative "unchanged"
    answer -- trust it outright, no further check needed.

    Layer 2 -- Content-Length fallback: some of these hosts (plain static
    file servers, CGI scrape endpoints) don't reliably honor conditional
    GET and just return 200 every time. If the response nonetheless carries
    the same ETag/Last-Modified we already have on file, or the same
    Content-Length as last time, treat that as a strong "probably
    unchanged" signal -- but per the plan, SHA-256 is the *final* authority,
    so this layer alone never short-circuits a "changed" verdict, only
    skips straight to the hash check with no ambiguity.

    Layer 3 -- SHA-256: always computed when we have a body and layers 1-2
    didn't already return an authoritative "unchanged" (a 304). Comparing
    hashes is what actually decides "changed" vs "unchanged" for every
    ordinary 200 response.
    """
    if was_304:  # info: if was_304 :
        return DetectionVerdict(changed=False, reason="304 Not Modified (conditional GET)")  # info: return DetectionVerdict ( changed = False , reason

    if content is None:  # info: if content is None :
        # Defensive: a non-304 response with no body shouldn't happen given
        # http_client's contract, but never claim "changed" on nothing.
        return DetectionVerdict(changed=False, reason="empty response body, treating as unchanged")  # info: return DetectionVerdict ( changed = False , reason

    new_hash = sha256_of(content)  # info: set new_hash

    # Layers 1/2 already exhausted (no 304) -- hash is authoritative.
    if state.content_sha256 is not None and new_hash == state.content_sha256:  # info: if state . content_sha256 is not None and
        reason = "200 response but content hash matches stored hash"  # info: set reason
        if response_etag and response_etag == state.etag:  # info: if response_etag and response_etag == state . etag
            reason += " (etag also matched)"  # info: set reason
        elif response_content_length is not None and response_content_length == state.content_length:  # info: elif response_content_length is not None and response_content_length ==
            reason += " (content-length also matched)"  # info: set reason
        return DetectionVerdict(changed=False, reason=reason, new_sha256=new_hash)  # info: return DetectionVerdict ( changed = False , reason

    return DetectionVerdict(changed=True, reason="content hash differs from stored hash", new_sha256=new_hash)  # info: return DetectionVerdict ( changed = True , reason
