"""Smoke test for fetch/ndfd_gridpoint.py's fetch_all() config reading.

No network: resolve_gridpoint and manifest are both monkeypatched. This
targets the specific bug fixed this session -- fetch_all() previously
treated `config["ndfd"]["items"]` (a list) as if it were a dict, so it
always returned [] even once `points` existed. Also requires the httpx
import-time dependency to be stubbed, same reasoning as
tests/scheduler/test_run_cycle_smoke.py.
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

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    _stub.Headers = _Headers
    _stub.HTTPStatusError = _HTTPStatusError
    _stub.Client = _Client
    sys.modules["httpx"] = _stub

from fetch import ndfd_gridpoint, _engine  # noqa: E402


def test_fetch_all_returns_empty_when_no_points_key_present():
    original = _engine.load_resources_yaml
    _engine.load_resources_yaml = lambda: {"ndfd": {"items": [{"id": "points_resolver"}]}}
    try:
        result = ndfd_gridpoint.fetch_all(manifest=None, base_dir="/fake")
        assert result == []
    finally:
        _engine.load_resources_yaml = original


def test_fetch_all_finds_points_nested_inside_the_items_list():
    # Regression: this exact shape (points nested one level down, inside
    # the items LIST's points_resolver entry) is what config/resources.yaml
    # actually looks like -- the pre-fix code could never see this.
    fake_config = {
        "ndfd": {
            "items": [
                {
                    "id": "points_resolver",
                    "points": [
                        {"id": "HNL", "lat": 21.3187, "lon": -157.9225},
                        {"id": "LIH", "lat": 21.976, "lon": -159.339},
                    ],
                }
            ]
        }
    }
    original_config = _engine.load_resources_yaml
    original_resolve = ndfd_gridpoint.resolve_gridpoint
    original_run_resource = _engine.run_resource

    resolved_points = []
    run_resource_calls = []

    _engine.load_resources_yaml = lambda: fake_config
    ndfd_gridpoint.resolve_gridpoint = lambda lat, lon: resolved_points.append((lat, lon)) or "https://fake/forecast"
    _engine.run_resource = lambda manifest, base_dir, resource_id, url, **kw: run_resource_calls.append(resource_id)

    try:
        result = ndfd_gridpoint.fetch_all(manifest=None, base_dir="/fake")
        assert resolved_points == [(21.3187, -157.9225), (21.976, -159.339)]
        assert run_resource_calls == ["ndfd_gridpoint_HNL", "ndfd_gridpoint_LIH"]
        assert len(result) == 2
    finally:
        _engine.load_resources_yaml = original_config
        ndfd_gridpoint.resolve_gridpoint = original_resolve
        _engine.run_resource = original_run_resource
