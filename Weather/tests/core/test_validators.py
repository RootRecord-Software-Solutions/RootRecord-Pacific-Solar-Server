# ==============================================================================
# FILE: Weather/tests/core/test_validators.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke tests for core/validators.py."""  # info: """Smoke tests for core/validators.py."""
from __future__ import annotations  # info: from __future__ import annotations

from core.validators import validate_image_magic_bytes, looks_like_product  # info: from core . validators import validate_image_magic_bytes , looks_like_product


# ====================================================
# SECTION: function test_valid_gif_magic_bytes
# What it does: test valid gif magic bytes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_valid_gif_magic_bytes():  # info: def test_valid_gif_magic_bytes
    body = b"GIF89a" + b"\x00" * 100  # info: set body
    assert validate_image_magic_bytes(body, "gif").ok is True  # info: assert validate_image_magic_bytes ( body , "gif" ) .


# ====================================================
# SECTION: function test_html_error_page_fails_gif_check
# What it does: test html error page fails gif check.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_html_error_page_fails_gif_check():  # info: def test_html_error_page_fails_gif_check
    body = b"<html><body>404 Not Found</body></html>" * 3  # info: set body
    assert validate_image_magic_bytes(body, "gif").ok is False  # info: assert validate_image_magic_bytes ( body , "gif" ) .


# ====================================================
# SECTION: function test_too_small_body_fails
# What it does: test too small body fails.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_too_small_body_fails():  # info: def test_too_small_body_fails
    assert validate_image_magic_bytes(b"GIF89a", "gif").ok is False  # info: assert validate_image_magic_bytes ( b"GIF89a" , "gif" ) .


# ====================================================
# SECTION: function test_looks_like_product_accepts_real_text
# What it does: test looks like product accepts real text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_looks_like_product_accepts_real_text():  # info: def test_looks_like_product_accepts_real_text
    text = "STATE FOREST FORECAST FOR HAWAII...ISSUED BY THE NATIONAL WEATHER SERVICE"  # info: set text
    assert looks_like_product(text).ok is True  # info: assert looks_like_product ( text ) . ok is


# ====================================================
# SECTION: function test_looks_like_product_rejects_html_error_page
# What it does: test looks like product rejects html error page.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_looks_like_product_rejects_html_error_page():  # info: def test_looks_like_product_rejects_html_error_page
    text = "<html><head><title>404 Not Found</title></head></html>"  # info: set text
    assert looks_like_product(text).ok is False  # info: assert looks_like_product ( text ) . ok is


# ====================================================
# SECTION: function test_looks_like_product_rejects_empty
# What it does: test looks like product rejects empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_looks_like_product_rejects_empty():  # info: def test_looks_like_product_rejects_empty
    assert looks_like_product("   ").ok is False  # info: assert looks_like_product ( " " ) . ok is
