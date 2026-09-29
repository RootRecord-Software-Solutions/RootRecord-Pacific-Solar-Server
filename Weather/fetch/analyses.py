"""Streamline/surface/seastate analysis charts. Data-driven from
config/resources.yaml (`analyses:` section) -- the cycle-based gif families
(00/06/12/18Z) are expanded here rather than enumerated by hand in YAML.
"""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    analyses = config["analyses"]
    outcomes = []

    for item in analyses["items"]:
        outcomes.append(
            _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")
        )

    cycle_families = analyses.get("cycle_gif_families", {})
    for family in cycle_families.get("families", []):
        stem = family["stem"]
        base_url = family["base_url"]
        for cycle in family["cycles"]:
            resource_id = f"analyses_{stem}_{cycle}"
            url = f"{base_url}{stem}_{cycle}.gif"
            outcomes.append(
                _engine.run_resource(manifest, base_dir, resource_id, url, method="image")
            )

    return outcomes
