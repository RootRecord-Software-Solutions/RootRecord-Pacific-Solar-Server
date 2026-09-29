"""Static/miscellaneous weather resources that do not fit text/image categories."""
from __future__ import annotations
from core.manifest import Manifest
from core import hst_time
from fetch import _engine

def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    outcomes = []
    for item in config.get("misc", []):
        url = item.get("url")
        if item.get("url_template"):
            year = hst_time.hst_now().year
            url = item["url_template"].format(year=year)
        if not url:
            continue
        outcomes.append(_engine.run_resource(
            manifest, base_dir, item["id"], url,
            method=item.get("method", "binary"),
            expected_ext=item.get("expected_ext"),
        ))
    return outcomes
