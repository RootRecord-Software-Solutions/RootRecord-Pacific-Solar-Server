"""Smoke tests for core/validators.py."""
from __future__ import annotations

from core.validators import validate_image_magic_bytes, looks_like_product


def test_valid_gif_magic_bytes():
    body = b"GIF89a" + b"\x00" * 100
    assert validate_image_magic_bytes(body, "gif").ok is True


def test_html_error_page_fails_gif_check():
    body = b"<html><body>404 Not Found</body></html>" * 3
    assert validate_image_magic_bytes(body, "gif").ok is False


def test_too_small_body_fails():
    assert validate_image_magic_bytes(b"GIF89a", "gif").ok is False


def test_looks_like_product_accepts_real_text():
    text = "STATE FOREST FORECAST FOR HAWAII...ISSUED BY THE NATIONAL WEATHER SERVICE"
    assert looks_like_product(text).ok is True


def test_looks_like_product_rejects_html_error_page():
    text = "<html><head><title>404 Not Found</title></head></html>"
    assert looks_like_product(text).ok is False


def test_looks_like_product_rejects_empty():
    assert looks_like_product("   ").ok is False
