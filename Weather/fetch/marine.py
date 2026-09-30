"""Marine text products + marine zone map images. Text entries use the
product.php scrape (no confirmed structured-API type for most of these yet);
image entries are static charts. Data-driven from config/resources.yaml.
"""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine, text_products_fallback


def _extract_marine_text(body: bytes) -> str:
    if b"<pre" in body.lower():
        return text_products_fallback.extract_pre_text(body)
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        raise ValueError("empty marine product body")
    return text


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    marine = config["marine"]
    outcomes = []

    for item in marine:
        if item["id"] == "cwf_coastal_waters":
            # Sole owner is fetch/text_products.py, which already handles the
            # CWF API resource. Running it here as well creates two concurrent
            # writers for the same manifest resource_id.
            continue

        method = item["method"]
        if method == "image":
            outcomes.append(
                _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")
            )
        elif method == "scrape" and "product.php" in item["url"]:
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                    extract_text=text_products_fallback.extract_pre_text,
                    resource_id_hint=item["id"],
                )
            )
        elif method == "scrape":
            # /hfo/MFM, /hfo/SRF, /hfo/surfreports wrap the product in <pre>.
            # Plain-text successors (tgftp high-seas bulletins) have no tags;
            # extract_pre falls through to the raw body for those.
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                    extract_text=_extract_marine_text,
                    resource_id_hint=item["id"],
                    expected_ext="txt",
                )
            )

    return outcomes
