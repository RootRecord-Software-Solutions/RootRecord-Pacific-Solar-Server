"""radar.weather.gov/ridge/standard/HAWAII_loop.gif (static, Tier 6) + FTM
radar status text. The interactive Ridge2 tile viewer is explicitly out of
scope -- see config/resources.yaml `radar.interactive_reference_only`.
"""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    radar = config["radar"]
    outcomes = []

    for item in radar["items"]:
        method = item.get("method", "image")
        if method == "image":
            outcomes.append(
                _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")
            )
        else:  # ftm_radar_status -- a plain scrape, no <pre> block (it's /hfo/FTM, not product.php)
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                )
            )

    return outcomes
