# ==============================================================================
# FILE: Weather/core/validators.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Sanity checks run before anything touches disk: image magic-byte checks
and the "_looks_like_product" text check, both ported concepts from the old
system per BUILD_STATUS.md.

Never talks to disk or network -- pure validation over bytes/text already
in memory, called by fetch/_engine.py after a change is detected but before
core/archiver.py writes anything.
"""
from __future__ import annotations  # info: from __future__ import annotations

from dataclasses import dataclass  # info: from dataclasses import dataclass

# Magic-byte signatures for every image extension this skill fetches
# (satellite/analyses/radar/marine gifs, wwamap/marine-zone pngs and jpgs).
# ====================================================
# SECTION: _MAGIC_BYTES
# What it does: Set _MAGIC_BYTES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_MAGIC_BYTES: dict[str, tuple[bytes, ...]] = {  # info: set _MAGIC_BYTES
    "gif": (b"GIF87a", b"GIF89a"),  # info: call "gif"
    "png": (b"\x89PNG\r\n\x1a\n",),  # info: call "png"
    "jpg": (b"\xff\xd8\xff",),  # info: call "jpg"
    "jpeg": (b"\xff\xd8\xff",),  # info: call "jpeg"
    "tif": (b"II*\x00", b"MM\x00*"),  # info: call "tif"
    "tiff": (b"II*\x00", b"MM\x00*"),  # info: call "tiff"
}  # info: }

# A response body under this size is almost certainly an error page, empty
# placeholder, or truncated transfer rather than a real product/image.
_MIN_TEXT_LENGTH = 15  # info: set _MIN_TEXT_LENGTH
_MIN_IMAGE_BYTES = 64  # info: set _MIN_IMAGE_BYTES

# Telltale signs the "product" we got back is actually an HTML error/
# redirect page rather than the plain-text product forecast.weather.gov or
# api.weather.gov was supposed to return.
_HTML_ERROR_MARKERS = (  # info: set _HTML_ERROR_MARKERS
    "<html", "404 not found", "page not found", "temporarily unavailable",  # info: "<html" , "404 not found" , "page not found" , "temporarily unavailable" ,
    "internal server error", "<!doctype html",  # info: "internal server error" , "<!doctype html" ,
)  # info: )


# ====================================================
# SECTION: class ValidationResult
# What it does: ValidationResult.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class ValidationResult:  # info: class ValidationResult
    ok: bool  # info: set ok
    reason: str | None = None  # info: set reason


# ====================================================
# SECTION: function validate_image_magic_bytes
# What it does: Confirms `body` actually starts with the magic bytes expected for `ext` (case-insensitive). Catches the common failure mode of a host returning an HTML error page or empty body wit
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def validate_image_magic_bytes(body: bytes, ext: str) -> ValidationResult:  # info: def validate_image_magic_bytes
    """Confirms `body` actually starts with the magic bytes expected for
    `ext` (case-insensitive). Catches the common failure mode of a host
    returning an HTML error page or empty body with a 200 status for what
    should have been binary image content.
    """
    if len(body) < _MIN_IMAGE_BYTES:  # info: if len ( body ) < _MIN_IMAGE_BYTES :
        return ValidationResult(ok=False, reason=f"body too small ({len(body)} bytes) to be a real image")  # info: return ValidationResult ( ok = False , reason

    signatures = _MAGIC_BYTES.get(ext.lower())  # info: set signatures
    if signatures is None:  # info: if signatures is None :
        # Unknown/unlisted extension -- nothing to check against, don't
        # fail closed on an extension this validator simply doesn't know.
        return ValidationResult(ok=True, reason=f"no magic-byte signature registered for .{ext}, skipped")  # info: return ValidationResult ( ok = True , reason

    if any(body.startswith(sig) for sig in signatures):  # info: if any ( body . startswith ( sig
        return ValidationResult(ok=True)  # info: return ValidationResult ( ok = True )

    return ValidationResult(  # info: return ValidationResult (
        ok=False,  # info: set ok
        reason=f"body does not start with expected magic bytes for .{ext} "  # info: set reason
               f"(got {body[:8]!r})",  # info: f" (got { body [ : 8 ]
    )  # info: )


# ====================================================
# SECTION: function looks_like_product
# What it does: Sanity check that `text` is plausibly a real NWS forecaster product and not an HTML error page, empty response, or a scrape that grabbed the wrong element. Deliberately lenient -- 
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def looks_like_product(text: str) -> ValidationResult:  # info: def looks_like_product
    """Sanity check that `text` is plausibly a real NWS forecaster product
    and not an HTML error page, empty response, or a scrape that grabbed
    the wrong element. Deliberately lenient -- this gates against obvious
    junk, not against products the checker doesn't recognize the format of.
    """
    stripped = text.strip()  # info: set stripped
    if len(stripped) < _MIN_TEXT_LENGTH:  # info: if len ( stripped ) < _MIN_TEXT_LENGTH :
        return ValidationResult(ok=False, reason=f"body too short ({len(stripped)} chars) to be a real product")  # info: return ValidationResult ( ok = False , reason

    lowered = stripped.lower()  # info: set lowered
    for marker in _HTML_ERROR_MARKERS:  # info: for marker in _HTML_ERROR_MARKERS :
        if marker == "temporarily unavailable":  # info: if marker == "temporarily unavailable" :
            # Real HFO products mention a station that is temporarily
            # unavailable. That sentence is not an error page.
            if "national weather service" in lowered and len(stripped) > 400:  # info: if "national weather service" in lowered and len ( stripped
                continue  # info: continue
        if marker in lowered:  # info: if marker in lowered :
            return ValidationResult(ok=False, reason=f"body looks like an HTML error/placeholder page (found {marker!r})")  # info: return ValidationResult ( ok = False , reason

    return ValidationResult(ok=True)  # info: return ValidationResult ( ok = True )
