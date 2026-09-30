"""api.weather.gov/products/types/{TYPE}/locations/HFO -- PRIMARY path for
text products, per NWS_Hawaii_Resource_Map.md Section 3B. Falls back to
text_products_fallback.py's product.php scrape only if this fails.
"""
from __future__ import annotations

import json

from core import http_client
from core.manifest import Manifest
from fetch import _engine, text_products_fallback


def _extract_latest_product_text(list_json_bytes: bytes) -> str:
    """Resolve the latest product entry to its full productText record.

    The products/types endpoint returns an @graph index, not the report body.
    The first entry's @id is the authoritative second-hop product record.
    """
    envelope = json.loads(list_json_bytes.decode("utf-8"))
    graph = envelope.get("@graph", [])
    if not graph:
        raise ValueError("no products in @graph -- nothing to extract")

    product_url = graph[0].get("@id")
    if not isinstance(product_url, str) or not product_url.strip():
        raise ValueError("latest product has no @id")

    result = http_client.get(
        product_url,
        accept="application/ld+json",
    )
    if result.not_modified or not result.content:
        raise ValueError("latest product record returned no body")

    try:
        product = json.loads(result.content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"latest product record is not valid JSON: {exc}") from exc

    product_text = product.get("productText")
    if not isinstance(product_text, str) or not product_text.strip():
        raise ValueError("latest product record has no productText")

    return product_text.strip()


# One entry per text product this module owns (primary API path). Each maps
# to a `types/{AWIPS}/locations/HFO` products-API URL, per the resource map.
PRODUCT_TYPES: dict[str, str] = {
    "sfp_state_forecast": "SFP",
    "zfp_zone_forecast": "ZFP",
    "afd_area_forecast_discussion": "AFD",
    "nowhfo_short_term_forecast": "NOW",
    "hwo_hazardous_weather_outlook": "HWO",
    "cwf_coastal_waters": "CWF",
}


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    outcomes = []
    for resource_id, awips_type in PRODUCT_TYPES.items():
        url = f"https://api.weather.gov/products/types/{awips_type}/locations/HFO"
        outcome = _engine.run_resource(
            manifest, base_dir, resource_id, url,
            method="text",
            accept="application/ld+json",
            clean_text_body=True,
            extract_text=_extract_latest_product_text,
        )
        if (
            resource_id in {"nowhfo_short_term_forecast", "hwo_hazardous_weather_outlook"}
            and outcome.status in {"failed", "invalid"}
        ):
            # HFO often has no active NOW/HWO in the products API. The
            # configured fallback page is the live office product (a nowcast
            # page, or the hazard feed) rather than an empty product.php shell.
            page_outcome = _fetch_configured_fallback(manifest, base_dir, resource_id)
            if page_outcome is not None and page_outcome.status not in {"failed", "invalid"}:
                outcomes.append(page_outcome)
                continue
            if page_outcome is not None:
                outcome = page_outcome
        if outcome.status in {"failed", "invalid"}:
            # Primary path down -- fall back to the product.php scrape for
            # whichever product has a known fallback URL configured.
            fallback_outcome = text_products_fallback.fetch_one(manifest, base_dir, resource_id)
            if fallback_outcome is not None and fallback_outcome.status not in {"failed", "invalid"}:
                outcomes.append(fallback_outcome)
            else:
                outcomes.append(outcome)
        else:
            outcomes.append(outcome)
    return outcomes


def _fetch_configured_fallback(manifest: Manifest, base_dir: str, resource_id: str):
    config = _engine.load_resources_yaml()
    item = next((entry for entry in config.get("text_products", []) if entry.get("id") == resource_id), None)
    if not item:
        return None
    url = item.get("fallback_url")
    if not url:
        return None
    extract = text_products_fallback.extract_rss_descriptions if url.endswith(".xml") else text_products_fallback.extract_pre_text
    return _engine.run_resource(
        manifest, base_dir, resource_id, url,
        method="text",
        clean_text_body=True,
        extract_text=extract,
        expected_ext="txt",
        resource_id_hint=resource_id,
    )
