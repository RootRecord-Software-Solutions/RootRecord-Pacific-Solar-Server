# ==============================================================================
# FILE: Weather/tests/fetch/test_engine.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Regression coverage for fetch/_engine.py's run_resource().

No real network happens here -- core.http_client.get is monkeypatched
with a fake FetchResult, same reasoning as tests/scheduler's own httpx
stub (see that file's module docstring): _engine imports core.http_client,
which imports the real `httpx` at module level just to build its request,
so that import must succeed, but no test here needs it to actually do
anything.
"""
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
import types  # info: import types

# ====================================================
# SECTION: block if
# What it does: 'httpx' not in sys.modules
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
if "httpx" not in sys.modules:  # info: if "httpx" not in sys . modules :
    _stub = types.ModuleType("httpx")  # info: set _stub

    class _Headers(dict):  # info: class _Headers
        pass  # info: pass

    class _HTTPStatusError(Exception):  # info: class _HTTPStatusError
        pass  # info: pass

    class _Client:  # info: class _Client
        def __init__(self, *a, **kw):  # info: def __init__
            pass  # info: pass

    _stub.Headers = _Headers  # info: _stub . Headers = _Headers
    _stub.HTTPStatusError = _HTTPStatusError  # info: _stub . HTTPStatusError = _HTTPStatusError
    _stub.Client = _Client  # info: _stub . Client = _Client
    sys.modules["httpx"] = _stub  # info: sys . modules [ "httpx" ] = _stub

import tempfile  # info: import tempfile

from core import http_client  # info: from core import http_client
from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine  # info: from fetch import _engine


# ====================================================
# SECTION: class _FakeResult
# What it does:  FakeResult.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class _FakeResult:  # info: class _FakeResult
    def __init__(self, content: bytes):  # info: def __init__
        self.status_code = 200  # info: self . status_code = 200
        self.headers = {}  # info: self . headers = { }
        self.content = content  # info: self . content = content
        self.not_modified = False  # info: self . not_modified = False


# ====================================================
# SECTION: function test_extract_text_failure_produces_invalid_outcome_not_a_raise
# What it does: test extract text failure produces invalid outcome not a raise.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_extract_text_failure_produces_invalid_outcome_not_a_raise():  # info: def test_extract_text_failure_produces_invalid_outcome_not_a_raise
    # Regression: found live -- text_products.py's extract_text raises
    # ValueError when an NWS product has no current issuance (a normal,
    # expected condition for several product types, not a bug). That
    # raise used to escape run_resource() entirely (the "text" branch had
    # no guard, unlike the "json" branch a few lines above it, which does
    # catch its own parse errors the same way). One product with nothing
    # current was silently truncating every other resource fetched after
    # it in the same module's fetch_all() loop.
    original_get = http_client.get  # info: set original_get
    http_client.get = lambda *a, **k: _FakeResult(b'{"@graph": []}')  # info: http_client . get = lambda * a ,
    try:  # info: try :
        def always_raises(raw_content: bytes) -> str:  # info: def always_raises
            raise ValueError("no products in @graph -- nothing to extract")  # info: raise ValueError ( "no products in @graph -- nothing to extract" )

        manifest = Manifest(tempfile.mkdtemp())  # info: set manifest
        outcome = _engine.run_resource(  # info: set outcome
            manifest, tempfile.mkdtemp(), "some_product", "https://example.invalid/product",  # info: manifest , tempfile . mkdtemp ( ) ,
            method="text",  # info: set method
            extract_text=always_raises,  # info: set extract_text
        )  # info: )

        assert outcome.status == "invalid"  # info: assert outcome . status == "invalid"
        assert "no products in @graph" in outcome.detail  # info: assert "no products in @graph" in outcome . detail
        # And it was recorded as a failure, not left in limbo.
        state = manifest.get("some_product")  # info: set state
        assert state.consecutive_failures == 1  # info: assert state . consecutive_failures == 1
    finally:  # info: finally :
        http_client.get = original_get  # info: http_client . get = original_get


# ====================================================
# SECTION: function test_extract_text_failure_does_not_abort_subsequent_resources_in_a_module_loop
# What it does: test extract text failure does not abort subsequent resources in a module loop.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_extract_text_failure_does_not_abort_subsequent_resources_in_a_module_loop():  # info: def test_extract_text_failure_does_not_abort_subsequent_resources_in_a_module_loop
    # The actual failure mode seen live: text_products.fetch_all() iterates
    # PRODUCT_TYPES and calls run_resource() once per product. Simulate
    # that shape directly (rather than importing the real module, which
    # would hit real NWS URLs) to prove the loop-level symptom is fixed:
    # one product with no current issuance must not stop the ones after it.
    original_get = http_client.get  # info: set original_get
    http_client.get = lambda *a, **k: _FakeResult(b'{"@graph": []}')  # info: http_client . get = lambda * a ,
    try:  # info: try :
        def raises_for_the_empty_one(raw_content: bytes) -> str:  # info: def raises_for_the_empty_one
            raise ValueError("no products in @graph -- nothing to extract")  # info: raise ValueError ( "no products in @graph -- nothing to extract" )

        def succeeds(raw_content: bytes) -> str:  # info: def succeeds
            return "THIS IS A REAL PRODUCT BODY " * 10  # clears looks_like_product's length floor

        manifest = Manifest(tempfile.mkdtemp())  # info: set manifest
        base_dir = tempfile.mkdtemp()  # info: set base_dir

        product_specs = [  # info: set product_specs
            ("empty_product", raises_for_the_empty_one),  # info: call (
            ("product_after_the_empty_one", succeeds),  # info: call (
        ]  # info: ]

        outcomes = []  # info: set outcomes
        for resource_id, extractor in product_specs:  # info: for resource_id , extractor in product_specs :
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, resource_id, f"https://example.invalid/{resource_id}",  # info: manifest , base_dir , resource_id , f" https://example.invalid/
                    method="text",  # info: set method
                    extract_text=extractor,  # info: set extract_text
                )  # info: )
            )  # info: )

        # Both resources got a real outcome -- the second one was reached
        # and actually ran, it wasn't skipped because the first one raised.
        assert [o.resource_id for o in outcomes] == ["empty_product", "product_after_the_empty_one"]  # info: assert [ o . resource_id for o in
        assert outcomes[0].status == "invalid"  # info: assert outcomes [ 0 ] . status ==
        assert outcomes[1].status == "written"  # info: assert outcomes [ 1 ] . status ==
    finally:  # info: finally :
        http_client.get = original_get  # info: http_client . get = original_get
