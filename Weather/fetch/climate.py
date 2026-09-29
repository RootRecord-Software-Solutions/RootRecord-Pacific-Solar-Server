"""CLI/CLM/RRA daily+monthly climate summaries, station obhistory. Expands
the per-station `url_template` entries in config/resources.yaml (one
resource per station per product) rather than hand-listing each combination.
"""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine, text_products_fallback


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    climate = config["climate"]
    outcomes = []

    for item in climate["items"]:
        if "url_template" in item:
            for station in item["stations"]:
                resource_id = f"{item['id']}_{station}"
                url = item["url_template"].format(station=station)
                outcomes.append(
                    _engine.run_resource(
                        manifest, base_dir, resource_id, url,
                        method="text", clean_text_body=item.get("clean_text", True),
                        extract_text=text_products_fallback.extract_pre_text,
                        expected_ext="txt",
                        resource_id_hint=resource_id,
                    )
                )
        elif item["method"] == "image":
            outcomes.append(
                _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")
            )
        elif "product.php" in item["url"]:
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                    extract_text=text_products_fallback.extract_pre_text,
                    expected_ext="txt",
                    resource_id_hint=item["id"],
                )
            )
        else:
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                )
            )

    return outcomes


def fetch_observations(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    """Per-station current-obs pages (Section 3 of the resource map). Kept in
    this module rather than a separate fetch/observations.py per
    fetch/README.md's note -- promote it later if this grows.
    """
    config = _engine.load_resources_yaml()
    obs = config["observations"]
    outcomes = []
    for icao in obs["stations"]:
        resource_id = f"obhistory_{icao}"
        url = obs["obhistory_url_template"].format(icao=icao)
        outcomes.append(
            _engine.run_resource(manifest, base_dir, resource_id, url, method="text", clean_text_body=False)
        )
    return outcomes
