"""Smoke tests for core/change_detection.py."""
from __future__ import annotations

from core import change_detection
from core.manifest import ResourceState


def _state(**overrides) -> ResourceState:
    base = dict(resource_id="r1", url="https://example.com/x.gif", local_resource_dir="x")
    base.update(overrides)
    return ResourceState(**base)


def test_304_is_always_unchanged():
    verdict = change_detection.detect(
        _state(), was_304=True, response_etag=None, response_last_modified=None,
        response_content_length=None, content=None,
    )
    assert verdict.changed is False


def test_first_ever_fetch_is_changed():
    verdict = change_detection.detect(
        _state(content_sha256=None), was_304=False, response_etag="abc",
        response_last_modified=None, response_content_length=5, content=b"hello",
    )
    assert verdict.changed is True
    assert verdict.new_sha256 == change_detection.sha256_of(b"hello")


def test_same_hash_is_unchanged_even_on_200():
    h = change_detection.sha256_of(b"hello")
    verdict = change_detection.detect(
        _state(content_sha256=h), was_304=False, response_etag=None,
        response_last_modified=None, response_content_length=5, content=b"hello",
    )
    assert verdict.changed is False


def test_different_hash_is_changed():
    h = change_detection.sha256_of(b"old content")
    verdict = change_detection.detect(
        _state(content_sha256=h), was_304=False, response_etag=None,
        response_last_modified=None, response_content_length=11, content=b"new content",
    )
    assert verdict.changed is True
