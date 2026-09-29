"""Regression coverage for fetch/_engine.py's run_resource().

No real network happens here -- core.http_client.get is monkeypatched
with a fake FetchResult, same reasoning as tests/scheduler's own httpx
stub (see that file's module docstring): _engine imports core.http_client,
which imports the real `httpx` at module level just to build its request,
so that import must succeed, but no test here needs it to actually do
anything.
"""
from __future__ import annotations

import sys
import types

if "httpx" not in sys.modules:
    _stub = types.ModuleType("httpx")

    class _Headers(dict):
        pass

    class _HTTPStatusError(Exception):
        pass

    class _Client:
        def __init__(self, *a, **kw):
            pass

    _stub.Headers = _Headers
    _stub.HTTPStatusError = _HTTPStatusError
    _stub.Client = _Client
    sys.modules["httpx"] = _stub

import tempfile

from core import http_client
from core.manifest import Manifest
from fetch import _engine


class _FakeResult:
    def __init__(self, content: bytes):
        self.status_code = 200
        self.headers = {}
        self.content = content
        self.not_modified = False


def test_extract_text_failure_produces_invalid_outcome_not_a_raise():
    # Regression: found live -- text_products.py's extract_text raises
    # ValueError when an NWS product has no current issuance (a normal,
    # expected condition for several product types, not a bug). That
    # raise used to escape run_resource() entirely (the "text" branch had
    # no guard, unlike the "json" branch a few lines above it, which does
    # catch its own parse errors the same way). One product with nothing
    # current was silently truncating every other resource fetched after
    # it in the same module's fetch_all() loop.
    original_get = http_client.get
    http_client.get = lambda *a, **k: _FakeResult(b'{"@graph": []}')
    try:
        def always_raises(raw_content: bytes) -> str:
            raise ValueError("no products in @graph -- nothing to extract")

        manifest = Manifest(tempfile.mkdtemp())
        outcome = _engine.run_resource(
            manifest, tempfile.mkdtemp(), "some_product", "https://example.invalid/product",
            method="text",
            extract_text=always_raises,
        )

        assert outcome.status == "invalid"
        assert "no products in @graph" in outcome.detail
        # And it was recorded as a failure, not left in limbo.
        state = manifest.get("some_product")
        assert state.consecutive_failures == 1
    finally:
        http_client.get = original_get


def test_extract_text_failure_does_not_abort_subsequent_resources_in_a_module_loop():
    # The actual failure mode seen live: text_products.fetch_all() iterates
    # PRODUCT_TYPES and calls run_resource() once per product. Simulate
    # that shape directly (rather than importing the real module, which
    # would hit real NWS URLs) to prove the loop-level symptom is fixed:
    # one product with no current issuance must not stop the ones after it.
    original_get = http_client.get
    http_client.get = lambda *a, **k: _FakeResult(b'{"@graph": []}')
    try:
        def raises_for_the_empty_one(raw_content: bytes) -> str:
            raise ValueError("no products in @graph -- nothing to extract")

        def succeeds(raw_content: bytes) -> str:
            return "THIS IS A REAL PRODUCT BODY " * 10  # clears looks_like_product's length floor

        manifest = Manifest(tempfile.mkdtemp())
        base_dir = tempfile.mkdtemp()

        product_specs = [
            ("empty_product", raises_for_the_empty_one),
            ("product_after_the_empty_one", succeeds),
        ]

        outcomes = []
        for resource_id, extractor in product_specs:
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, resource_id, f"https://example.invalid/{resource_id}",
                    method="text",
                    extract_text=extractor,
                )
            )

        # Both resources got a real outcome -- the second one was reached
        # and actually ran, it wasn't skipped because the first one raised.
        assert [o.resource_id for o in outcomes] == ["empty_product", "product_after_the_empty_one"]
        assert outcomes[0].status == "invalid"
        assert outcomes[1].status == "written"
    finally:
        http_client.get = original_get
