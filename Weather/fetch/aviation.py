"""TAFs, AIRMETs, SIGMETs. Data-driven from config/resources.yaml."""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine, text_products_fallback


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    aviation = config["aviation"]
    outcomes = []

    for item in aviation:
        if "product.php" in item["url"]:
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                    extract_text=text_products_fallback.extract_pre_text,
                    resource_id_hint=item["id"],
                )
            )
        else:  # /hfo/TAFPA, /hfo/aviation -- plain page, no <pre> wrapper
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                )
            )

    return outcomes
