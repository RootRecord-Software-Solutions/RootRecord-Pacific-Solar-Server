# ==============================================================================
# FILE: Weather/fetch/_engine.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Internal shared runner used by every fetch/*.py category module.

Not a resource category itself (hence the underscore prefix) -- exists so
no individual fetch module re-implements the request -> change-detection ->
clean -> validate -> archive -> manifest-update pipeline that
weather_skill_architecture.md Section 4 says belongs to `core/`. Each
category module stays "readable top-to-bottom in under a minute" by calling
into this instead of repeating the pipeline.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
from dataclasses import dataclass  # info: from dataclasses import dataclass
from pathlib import Path  # info: from pathlib import Path
from typing import Any, Callable  # info: from typing import Any , Callable

import yaml  # info: import yaml

from core import hst_time, http_client, change_detection, archiver, validators, text_cleaner  # info: from core import hst_time , http_client , change_detection
from core.manifest import Manifest  # info: from core . manifest import Manifest
from core.path_resolver import resolve  # info: from core . path_resolver import resolve

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"  # info: set _CONFIG_DIR


# ====================================================
# SECTION: function load_resources_yaml
# What it does: load resources yaml.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_resources_yaml() -> dict[str, Any]:  # info: def load_resources_yaml
    with open(_CONFIG_DIR / "resources.yaml", encoding="utf-8") as f:  # info: with open ( _CONFIG_DIR / "resources.yaml" , encoding
        return yaml.safe_load(f)  # info: return yaml . safe_load ( f )


# ====================================================
# SECTION: class FetchOutcome
# What it does: FetchOutcome.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class FetchOutcome:  # info: class FetchOutcome
    resource_id: str  # info: set resource_id
    status: str  # "written" | "unchanged" | "failed" | "invalid"
    detail: str  # info: set detail
    path: str | None = None  # info: set path


# ====================================================
# SECTION: function run_resource
# What it does: Runs the full pipeline for one resource, once. `extract_text` lets a category module pull the actual product text out of a JSON envelope (e.g. api.weather.gov's `productText` field
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_resource(  # info: def run_resource
    manifest: Manifest,  # info: set manifest
    base_dir: str,  # info: set base_dir
    resource_id: str,  # info: set resource_id
    url: str,  # info: set url
    *,  # info: * ,
    method: str,                       # "image" | "json" | "text"
    resource_id_hint: str | None = None,  # info: set resource_id_hint
    accept: str | None = None,  # info: set accept
    clean_text_body: bool = False,  # info: set clean_text_body
    extract_text: Callable[[bytes], str] | None = None,  # info: set extract_text
    expected_ext: str | None = None,  # info: set expected_ext
) -> FetchOutcome:  # info: ) -> FetchOutcome :
    """Runs the full pipeline for one resource, once.

    `extract_text` lets a category module pull the actual product text out of
    a JSON envelope (e.g. api.weather.gov's `productText` field) before
    cleaning/validating/archiving -- the engine doesn't know that shape
    itself, since that's category-specific.
    """
    resolved = resolve(url, resource_id_hint=resource_id_hint)  # info: set resolved
    if expected_ext:  # info: if expected_ext :
        resolved = type(resolved)(host=resolved.host, resource_dir=resolved.resource_dir,  # info: set resolved
                                   name=resolved.name, ext=expected_ext)  # info: set name

    state = manifest.get_or_create(resource_id, url, resolved.base_dir_relative())  # info: set state

    try:  # info: try :
        result = http_client.get(url, etag=state.etag, last_modified=state.last_modified, accept=accept)  # info: set result
    except Exception as e:  # network/HTTP error -- record failure, move on
        manifest.record_failure(resource_id, failed_at_hst_iso=hst_time.hst_now().isoformat())  # info: manifest . record_failure ( resource_id , failed_at_hst_iso =
        return FetchOutcome(resource_id, "failed", f"request failed: {e}")  # info: return FetchOutcome ( resource_id , "failed" , f"

    now = hst_time.hst_now()  # info: set now
    response_etag = result.headers.get("etag")  # info: set response_etag
    response_last_modified = result.headers.get("last-modified")  # info: set response_last_modified
    response_content_length = (  # info: set response_content_length
        int(result.headers["content-length"]) if "content-length" in result.headers else None  # info: call int
    )  # info: )

    # A 304 is authoritative and needs no body processing.
    if result.not_modified:  # info: if result . not_modified :
        manifest.record_unchanged(resource_id, confirmed_at_hst_iso=now.isoformat())  # info: manifest . record_unchanged ( resource_id , confirmed_at_hst_iso =
        return FetchOutcome(resource_id, "unchanged", "304 Not Modified (conditional GET)")  # info: return FetchOutcome ( resource_id , "unchanged" , "304 Not Modified (conditional GET)"

    raw_content = result.content or b""  # info: set raw_content

    # Preserve the exact official HTML response alongside the parsed/cleaned
    # artifact. The raw copy is intentionally independent of parsed-product
    # change detection so the live source remains available for inspection.
    if "text/html" in result.headers.get("content-type", "").lower():  # info: if "text/html" in result . headers . get
        raw_dir = Path(resolved.current_path(base_dir)).parent / "raw"  # info: set raw_dir
        raw_dir.mkdir(parents=True, exist_ok=True)  # info: raw_dir . mkdir ( parents = True ,
        raw_current = raw_dir / f"{resolved.name}_raw_current.html"  # info: set raw_current
        raw_archive = (  # info: set raw_archive
            raw_dir  # info: raw_dir
            / "archive"  # info: / "archive"
            / hst_time.hst_date_folder(now)  # info: / hst_time . hst_date_folder ( now )
            / f"{resolved.name}_raw_{hst_time.hst_archive_timestamp(now)}.html"  # info: / f" { resolved . name } _raw_
        )  # info: )
        raw_unchanged = False  # info: set raw_unchanged
        if raw_current.is_file():  # info: if raw_current . is_file ( ) :
            try:  # info: try :
                raw_unchanged = raw_current.read_bytes() == raw_content  # info: set raw_unchanged
            except OSError:  # info: except OSError :
                raw_unchanged = False  # info: set raw_unchanged
        if not raw_unchanged:  # info: if not raw_unchanged :
            if raw_current.is_file():  # info: if raw_current . is_file ( ) :
                raw_archive.parent.mkdir(parents=True, exist_ok=True)  # info: raw_archive . parent . mkdir ( parents =
                raw_current.replace(raw_archive)  # info: raw_current . replace ( raw_archive )
            raw_current.write_bytes(raw_content)  # info: raw_current . write_bytes ( raw_content )

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
    if method == "image":  # info: if method == "image" :
        body_bytes = raw_content  # info: set body_bytes
        validation = validators.validate_image_magic_bytes(body_bytes, resolved.ext)  # info: set validation
        if not validation.ok:  # info: if not validation . ok :
            manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())  # info: manifest . record_failure ( resource_id , failed_at_hst_iso =
            return FetchOutcome(resource_id, "invalid", validation.reason or "image validation failed")  # info: return FetchOutcome ( resource_id , "invalid" , validation

    elif method == "json":  # info: elif method == "json" :
        # Clean natural-language fields in place, then store the whole JSON
        # document (structured fields untouched, per config/text_cleaning.yaml).
        try:  # info: try :
            obj = json.loads(raw_content.decode("utf-8"))  # info: set obj
        except (json.JSONDecodeError, UnicodeDecodeError) as e:  # info: except ( json . JSONDecodeError , UnicodeDecodeError )
            manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())  # info: manifest . record_failure ( resource_id , failed_at_hst_iso =
            return FetchOutcome(resource_id, "invalid", f"JSON decode failed: {e}")  # info: return FetchOutcome ( resource_id , "invalid" , f"
        cleaned_obj = text_cleaner.clean_json_text_fields(obj) if clean_text_body else obj  # info: set cleaned_obj
        body_bytes = (json.dumps(cleaned_obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")  # info: set body_bytes

    elif method == "binary":  # info: elif method == "binary" :
        # Binary/static source: preserve exact bytes without text/image validation.
        body_bytes = raw_content  # info: set body_bytes

    elif method == "text":  # info: elif method == "text" :
        if extract_text:  # info: if extract_text :
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
            try:  # info: try :
                text_body = extract_text(raw_content)  # info: set text_body
            except Exception as e:  # info: except Exception as e :
                manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())  # info: manifest . record_failure ( resource_id , failed_at_hst_iso =
                return FetchOutcome(resource_id, "invalid", f"extract_text failed: {e}")  # info: return FetchOutcome ( resource_id , "invalid" , f"
        else:  # info: else :
            text_body = raw_content.decode("utf-8", errors="replace")  # info: set text_body
        validation = validators.looks_like_product(text_body)  # info: set validation
        if not validation.ok:  # info: if not validation . ok :
            manifest.record_failure(resource_id, failed_at_hst_iso=now.isoformat())  # info: manifest . record_failure ( resource_id , failed_at_hst_iso =
            return FetchOutcome(resource_id, "invalid", validation.reason or "text validation failed")  # info: return FetchOutcome ( resource_id , "invalid" , validation
        if clean_text_body:  # info: if clean_text_body :
            text_body = text_cleaner.clean_text(text_body)  # info: set text_body
        body_bytes = text_body.encode("utf-8")  # info: set body_bytes

    else:  # info: else :
        raise ValueError(f"unknown fetch method: {method!r}")  # info: raise ValueError ( f" unknown fetch method: { method !

    verdict = change_detection.detect(  # info: set verdict
        state, was_304=False, response_etag=response_etag,  # info: state , was_304 = False , response_etag =
        response_last_modified=response_last_modified,  # info: set response_last_modified
        response_content_length=response_content_length,  # info: set response_content_length
        content=body_bytes,  # info: set content
    )  # info: )

    if not verdict.changed:  # info: if not verdict . changed :
        manifest.record_unchanged(resource_id, confirmed_at_hst_iso=now.isoformat())  # info: manifest . record_unchanged ( resource_id , confirmed_at_hst_iso =
        return FetchOutcome(resource_id, "unchanged", verdict.reason)  # info: return FetchOutcome ( resource_id , "unchanged" , verdict

    written_path = archiver.age_out_and_write(base_dir, resolved, state, body_bytes, now)  # info: set written_path

    manifest.record_success(  # info: manifest . record_success (
        resource_id,  # info: resource_id ,
        etag=response_etag,  # info: set etag
        last_modified=response_last_modified,  # info: set last_modified
        content_length=len(body_bytes),  # info: set content_length
        content_sha256=verdict.new_sha256 or change_detection.sha256_of(body_bytes),  # info: set content_sha256
        fetched_at_hst_iso=now.isoformat(),  # info: set fetched_at_hst_iso
    )  # info: )
    return FetchOutcome(resource_id, "written", verdict.reason, path=str(written_path))  # info: return FetchOutcome ( resource_id , "written" , verdict
