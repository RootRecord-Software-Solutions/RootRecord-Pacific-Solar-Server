# ==============================================================================
# FILE: Weather/tests/fetch/test_ndfd_gridpoint.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Smoke test for fetch/ndfd_gridpoint.py's fetch_all() config reading.

No network: resolve_gridpoint and manifest are both monkeypatched. This
targets the specific bug fixed this session -- fetch_all() previously
treated `config["ndfd"]["items"]` (a list) as if it were a dict, so it
always returned [] even once `points` existed. Also requires the httpx
import-time dependency to be stubbed, same reasoning as
tests/scheduler/test_run_cycle_smoke.py.
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

        def __enter__(self):  # info: def __enter__
            return self  # info: return self

        def __exit__(self, *a):  # info: def __exit__
            return False  # info: return False

    _stub.Headers = _Headers  # info: _stub . Headers = _Headers
    _stub.HTTPStatusError = _HTTPStatusError  # info: _stub . HTTPStatusError = _HTTPStatusError
    _stub.Client = _Client  # info: _stub . Client = _Client
    sys.modules["httpx"] = _stub  # info: sys . modules [ "httpx" ] = _stub

from fetch import ndfd_gridpoint, _engine  # noqa: E402


# ====================================================
# SECTION: function test_fetch_all_returns_empty_when_no_points_key_present
# What it does: test fetch all returns empty when no points key present.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_fetch_all_returns_empty_when_no_points_key_present():  # info: def test_fetch_all_returns_empty_when_no_points_key_present
    original = _engine.load_resources_yaml  # info: set original
    _engine.load_resources_yaml = lambda: {"ndfd": {"items": [{"id": "points_resolver"}]}}  # info: _engine . load_resources_yaml = lambda : { "ndfd"
    try:  # info: try :
        result = ndfd_gridpoint.fetch_all(manifest=None, base_dir="/fake")  # info: set result
        assert result == []  # info: assert result == [ ]
    finally:  # info: finally :
        _engine.load_resources_yaml = original  # info: _engine . load_resources_yaml = original


# ====================================================
# SECTION: function test_fetch_all_finds_points_nested_inside_the_items_list
# What it does: test fetch all finds points nested inside the items list.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_fetch_all_finds_points_nested_inside_the_items_list():  # info: def test_fetch_all_finds_points_nested_inside_the_items_list
    # Regression: this exact shape (points nested one level down, inside
    # the items LIST's points_resolver entry) is what config/resources.yaml
    # actually looks like -- the pre-fix code could never see this.
    fake_config = {  # info: set fake_config
        "ndfd": {  # info: "ndfd" : {
            "items": [  # info: "items" : [
                {  # info: {
                    "id": "points_resolver",  # info: "id" : "points_resolver" ,
                    "points": [  # info: "points" : [
                        {"id": "HNL", "lat": 21.3187, "lon": -157.9225},  # info: { "id" : "HNL" , "lat" : 21.3187
                        {"id": "LIH", "lat": 21.976, "lon": -159.339},  # info: { "id" : "LIH" , "lat" : 21.976
                    ],  # info: ] ,
                }  # info: }
            ]  # info: ]
        }  # info: }
    }  # info: }
    original_config = _engine.load_resources_yaml  # info: set original_config
    original_resolve = ndfd_gridpoint.resolve_gridpoint  # info: set original_resolve
    original_run_resource = _engine.run_resource  # info: set original_run_resource

    resolved_points = []  # info: set resolved_points
    run_resource_calls = []  # info: set run_resource_calls

    _engine.load_resources_yaml = lambda: fake_config  # info: _engine . load_resources_yaml = lambda : fake_config
    ndfd_gridpoint.resolve_gridpoint = lambda lat, lon: resolved_points.append((lat, lon)) or "https://fake/forecast"  # info: ndfd_gridpoint . resolve_gridpoint = lambda lat , lon
    _engine.run_resource = lambda manifest, base_dir, resource_id, url, **kw: run_resource_calls.append(resource_id)  # info: _engine . run_resource = lambda manifest , base_dir

    try:  # info: try :
        result = ndfd_gridpoint.fetch_all(manifest=None, base_dir="/fake")  # info: set result
        assert resolved_points == [(21.3187, -157.9225), (21.976, -159.339)]  # info: assert resolved_points == [ ( 21.3187 , -
        assert run_resource_calls == ["ndfd_gridpoint_HNL", "ndfd_gridpoint_LIH"]  # info: assert run_resource_calls == [ "ndfd_gridpoint_HNL" , "ndfd_gridpoint_LIH" ]
        assert len(result) == 2  # info: assert len ( result ) == 2
    finally:  # info: finally :
        _engine.load_resources_yaml = original_config  # info: _engine . load_resources_yaml = original_config
        ndfd_gridpoint.resolve_gridpoint = original_resolve  # info: ndfd_gridpoint . resolve_gridpoint = original_resolve
        _engine.run_resource = original_run_resource  # info: _engine . run_resource = original_run_resource
