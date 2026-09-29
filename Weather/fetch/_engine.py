"""Internal shared runner used by every fetch/*.py category module.

Not a resource category itself (hence the underscore prefix) -- exists so
no individual fetch module re-implements the request -> change-detection ->
clean -> validate -> archive -> manifest-update pipeline that
weather_skill_architecture.md Section 4 says belongs to `core/`. Each
category module stays "readable top-to-bottom in under a minute" by calling
into this instead of repeating the pipeline.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from core import hst_time, http_client, change_detection, archiver, validators, text_cleaner
from core.manifest import Manifest
from core.path_resolver import resolve

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_resources_yaml() -> dict[str, Any]:
    with open(_CONFIG_DIR / "resources.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class FetchOutcome:
    resource_id: str
    status: str  # "written" | "unchanged" | "failed" | "invalid"
    detail: str
    path: str | None = None


def run_resource(
    manifest: Manifest,
    base_dir: str,
    resource_id: str,
    url: str,
    *,
    method: str,                       # "image" | "json" | "text"
    resource_id_hint: str | None = None,
    accept: str | None = None,
    clean_text_body: bool = False,
    extract_text: Callable[[bytes], str] | None = None,
    expected_ext: str | None = None,
) -> FetchOutcome:
    """Runs the full pipeline for one resource, once.

    `extract_text` lets a category module pull the actual product text out of
    a JSON envelope (e.g. api.weather.gov's `productText` field) before
    cleaning/validating/archiving -- the engine doesn't know that shape
    itself, since that's category-specific.
    """
    resolved = resolve(url, resource_id_hint=resource_id_hint)
    if expected_ext:
        resolved = type(resolved)(host=resolved.host, resource_dir=resolved.resource_dir,
                                   name=resolved.name, ext=expected_ext)

    state = manifest.get_or_create(resource_id, url, resolved.base_dir_relative())

    try:
        result = http_client.get(url, etag=state.etag, last_modified=state.last_modified, accept=accept)
    except Exception as e:  # network/HTTP error -- record failure, move on
        manifest.record_failure(resource_id, failed_at_hst_iso=hst_time.hst_now().isoformat())
        return FetchOutcome(resource_id, "failed", f"request failed: {e}")

    now = hst_time.hst_now()
    response_etag = result.headers.get("etag")
    response_last_modified = result.headers.get("last-modified")
    response_content_length = (
        int(result.headers["content-length"]) if "content-length" in result.headers else None
    )

    # A 304 is authoritative and needs no body processing.
    if result.not_modified:
        manifest.record_unchanged(resource_id, confirmed_at_hst_iso=now.isoformat())
        return FetchOutcome(resource_id, "unchanged", "304 Not Modified (conditional GET)")

    raw_content = result.content or b""

    # Preserve the exact official HTML response alongside the parsed/cleaned
    # artifact. The raw copy is intentionally independent of parsed-product
    # change detection so the live source remains available for inspection.
    if "text/html" in result.headers.get("content-type", "").lower():
        raw_dir = Path(resolved.current_path(base_dir)).parent / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_current = raw_dir / f"{resolved.name}_raw_current.html"
        raw_archive = (
            raw_dir
            / "archive"
            / hst_time.hst_date_folder(now)
            / f"{resolved.name}_raw_{hst_time.hst_archive_timestamp(now)}.html"
        )
        raw_unchanged = False
        if raw_current.is_file():
            try:
                raw_unchanged = raw_current.read_bytes() == raw_content
            except OSError:
                raw_unchanged = False
        if not raw_unchanged:
            if raw_current.is_file():
                raw_archive.parent.mkdir(parents=True, exist_ok=True)
                raw_current.replace(raw_archive)
            raw_current.write_bytes(raw_content)

    # Build the exact byte stream that will be archived FIRST.  Change
    # detection must hash this post-processed representation, not the raw
    # HTTP response.  product.php pages commonly contain HTML generation
    # noise that changes between requests even when the extracted <pre>
    # product text is identical.
    #
    # This ordering is the correctness boundary: the hash must describe
    # what is actually stored on disk.
    #
    # Method-specific handling: pull out the real body to write to disk.
    if method == "image":
        body_bytes = raw_content
        validation = validators.validate_image_magic_bytes(body_bytes, resolved.ext)
        if not validation.ok:
            manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())
            return FetchOutcome(resource_id, "invalid", validation.reason or "image validation failed")

    elif method == "json":
        # Clean natural-language fields in place, then store the whole JSON
        # document (structured fields untouched, per config/text_cleaning.yaml).
        try:
            obj = json.loads(raw_content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())
            return FetchOutcome(resource_id, "invalid", f"JSON decode failed: {e}")
        cleaned_obj = text_cleaner.clean_json_text_fields(obj) if clean_text_body else obj
        body_bytes = (json.dumps(cleaned_obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    elif method == "binary":
        # Binary/static source: preserve exact bytes without text/image validation.
        body_bytes = raw_content

    elif method == "text":
        if extract_text:
            # extract_text is arbitrary, category-specific code (see e.g.
            # fetch/text_products.py's _extract_latest_product_text, which
            # raises ValueError when a product simply has no current
            # issuance -- a normal, expected condition, not a bug). Guard
            # it the same way the json branch above guards json.loads:
            # one resource's extraction failure must produce a clean
            # "invalid" outcome, not propagate out of run_resource and
            # abort every other resource in the caller's fetch_all() loop
            # (text_products.py iterates ~11 products from one call --
            # this was silently truncating that list after the first
            # product with no current issuance).
            try:
                text_body = extract_text(raw_content)
            except Exception as e:
                manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())
                return FetchOutcome(resource_id, "invalid", f"extract_text failed: {e}")
        else:
            text_body = raw_content.decode("utf-8", errors="replace")
        validation = validators.looks_like_product(text_body)
        if not validation.ok:
            manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())
            return FetchOutcome(resource_id, "invalid", validation.reason or "text validation failed")
        if clean_text_body:
            text_body = text_cleaner.clean_text(text_body)
        body_bytes = text_body.encode("utf-8")

    else:
        raise ValueError(f"unknown fetch method: {method!r}")

    verdict = change_detection.detect(
        state, was_304=False, response_etag=response_etag,
        response_last_modified=response_last_modified,
        response_content_length=response_content_length,
        content=body_bytes,
    )

    if not verdict.changed:
        manifest.record_unchanged(resource_id, confirmed_at_hst_iso=now.isoformat())
        return FetchOutcome(resource_id, "unchanged", verdict.reason)

    written_path = archiver.age_out_and_write(base_dir, resolved, state, body_bytes, now)

    manifest.record_success(
        resource_id,
        etag=response_etag,
        last_modified=response_last_modified,
        content_length=len(body_bytes),
        content_sha256=verdict.new_sha256 or change_detection.sha256_of(body_bytes),
        fetched_at_hst_iso=now.isoformat(),
    )
    return FetchOutcome(resource_id, "written", verdict.reason, path=str(written_path))
