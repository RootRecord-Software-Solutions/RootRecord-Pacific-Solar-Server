"""Three-layer change detection: conditional HTTP -> Content-Length fallback
-> SHA-256 content hash as final authority. Per nws_plan.md Section 3.

Pure logic module: takes what core/http_client.py and core/manifest.py
already know and returns a verdict. Makes no HTTP calls and touches no disk
itself.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from core.manifest import ResourceState


def sha256_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass
class DetectionVerdict:
    changed: bool
    reason: str
    new_sha256: str | None = None  # populated whenever content was hashed


def detect(
    state: ResourceState,
    *,
    was_304: bool,
    response_etag: str | None,
    response_last_modified: str | None,
    response_content_length: int | None,
    content: bytes | None,
) -> DetectionVerdict:
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
    if was_304:
        return DetectionVerdict(changed=False, reason="304 Not Modified (conditional GET)")

    if content is None:
        # Defensive: a non-304 response with no body shouldn't happen given
        # http_client's contract, but never claim "changed" on nothing.
        return DetectionVerdict(changed=False, reason="empty response body, treating as unchanged")

    new_hash = sha256_of(content)

    # Layers 1/2 already exhausted (no 304) -- hash is authoritative.
    if state.content_sha256 is not None and new_hash == state.content_sha256:
        reason = "200 response but content hash matches stored hash"
        if response_etag and response_etag == state.etag:
            reason += " (etag also matched)"
        elif response_content_length is not None and response_content_length == state.content_length:
            reason += " (content-length also matched)"
        return DetectionVerdict(changed=False, reason=reason, new_sha256=new_hash)

    return DetectionVerdict(changed=True, reason="content hash differs from stored hash", new_sha256=new_hash)
