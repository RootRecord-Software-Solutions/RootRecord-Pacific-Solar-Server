"""Sanity checks run before anything touches disk: image magic-byte checks
and the "_looks_like_product" text check, both ported concepts from the old
system per BUILD_STATUS.md.

Never talks to disk or network -- pure validation over bytes/text already
in memory, called by fetch/_engine.py after a change is detected but before
core/archiver.py writes anything.
"""
from __future__ import annotations

from dataclasses import dataclass

# Magic-byte signatures for every image extension this skill fetches
# (satellite/analyses/radar/marine gifs, wwamap/marine-zone pngs and jpgs).
_MAGIC_BYTES: dict[str, tuple[bytes, ...]] = {
    "gif": (b"GIF87a", b"GIF89a"),
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "tif": (b"II*\x00", b"MM\x00*"),
    "tiff": (b"II*\x00", b"MM\x00*"),
}

# A response body under this size is almost certainly an error page, empty
# placeholder, or truncated transfer rather than a real product/image.
_MIN_TEXT_LENGTH = 15
_MIN_IMAGE_BYTES = 64

# Telltale signs the "product" we got back is actually an HTML error/
# redirect page rather than the plain-text product forecast.weather.gov or
# api.weather.gov was supposed to return.
_HTML_ERROR_MARKERS = (
    "<html", "404 not found", "page not found", "temporarily unavailable",
    "internal server error", "<!doctype html",
)


@dataclass
class ValidationResult:
    ok: bool
    reason: str | None = None


def validate_image_magic_bytes(body: bytes, ext: str) -> ValidationResult:
    """Confirms `body` actually starts with the magic bytes expected for
    `ext` (case-insensitive). Catches the common failure mode of a host
    returning an HTML error page or empty body with a 200 status for what
    should have been binary image content.
    """
    if len(body) < _MIN_IMAGE_BYTES:
        return ValidationResult(ok=False, reason=f"body too small ({len(body)} bytes) to be a real image")

    signatures = _MAGIC_BYTES.get(ext.lower())
    if signatures is None:
        # Unknown/unlisted extension -- nothing to check against, don't
        # fail closed on an extension this validator simply doesn't know.
        return ValidationResult(ok=True, reason=f"no magic-byte signature registered for .{ext}, skipped")

    if any(body.startswith(sig) for sig in signatures):
        return ValidationResult(ok=True)

    return ValidationResult(
        ok=False,
        reason=f"body does not start with expected magic bytes for .{ext} "
               f"(got {body[:8]!r})",
    )


def looks_like_product(text: str) -> ValidationResult:
    """Sanity check that `text` is plausibly a real NWS forecaster product
    and not an HTML error page, empty response, or a scrape that grabbed
    the wrong element. Deliberately lenient -- this gates against obvious
    junk, not against products the checker doesn't recognize the format of.
    """
    stripped = text.strip()
    if len(stripped) < _MIN_TEXT_LENGTH:
        return ValidationResult(ok=False, reason=f"body too short ({len(stripped)} chars) to be a real product")

    lowered = stripped.lower()
    for marker in _HTML_ERROR_MARKERS:
        if marker in lowered:
            return ValidationResult(ok=False, reason=f"body looks like an HTML error/placeholder page (found {marker!r})")

    return ValidationResult(ok=True)
