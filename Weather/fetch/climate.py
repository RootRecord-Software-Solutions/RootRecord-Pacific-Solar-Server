"""CLI/CLM/RRA daily+monthly climate summaries, station obhistory. Expands
the per-station `url_template` entries in config/resources.yaml (one
resource per station per product) rather than hand-listing each combination.
"""
from __future__ import annotations

from core import http_client
from core.manifest import Manifest
from fetch import _engine, text_products_fallback

_CLI_STATIONS = ("HNL", "LIH", "OGG", "ITO")


def extract_rtp_or_cli(page_bytes: bytes) -> str:
    """Use the RTPHI product when HFO has issued one.

    The regional table is often unpublished. The four daily climate
    summaries are the current statewide temp and precip products.
    """
    try:
        text = text_products_fallback.extract_pre_text(page_bytes)
    except ValueError:
        text = ""
    if text and "none issued" not in text.lower():
        return text
    parts: list[str] = []
    for station in _CLI_STATIONS:
        url = (
            "https://forecast.weather.gov/product.php?site=HFO"
            f"&product=CLI&issuedby={station}"
        )
        result = http_client.get(url)
        if result.not_modified or not result.content:
            raise ValueError(f"CLI {station} returned no body")
        parts.append(f"CLI{station}\n" + text_products_fallback.extract_pre_text(result.content))
    return "\n\n".join(parts)


def fetch_all(manifest: Manifest, base_dir: str, only: set[str] | None = None) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    climate = config["climate"]
    outcomes = []

    for item in climate["items"]:
        if only is not None and item["id"] not in only:
            continue
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
        elif item["id"] == "rtp_temp_precip_summary":
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                    extract_text=extract_rtp_or_cli,
                    expected_ext="txt",
                    resource_id_hint=item["id"],
                )
            )
        elif item["url"].endswith(".xml"):
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                    extract_text=text_products_fallback.extract_rss_descriptions,
                    expected_ext="txt",
                    resource_id_hint=item["id"],
                )
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
