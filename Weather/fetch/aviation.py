"""TAFs, AIRMETs, SIGMETs. Data-driven from config/resources.yaml."""
from __future__ import annotations

import re

from core.manifest import Manifest
from fetch import _engine, text_products_fallback


def extract_phfo_sigmets(raw: bytes) -> str:
    """Keep Honolulu-issued blocks from the Aviation Weather Center SIGMET feed.

    The raw feed is worldwide. HFO products are the blocks that name PHFO
    (international, tropical-cyclone, and volcanic-ash SIGMETs).
    """
    text = raw.decode("utf-8", errors="replace")
    parts = re.split(r"\n-{5,}\n|\n(?=Hazard:)", text)
    kept = [part.strip() for part in parts if "PHFO" in part.upper()]
    if not kept:
        raise ValueError("no PHFO SIGMET in the international SIGMET feed")
    return "\n\n".join(kept)


def _extract_for(item: dict) -> object:
    url = item["url"]
    if item["id"] == "aviation_sigmets":
        return extract_phfo_sigmets
    if url.endswith(".xml") or "/xml/" in url:
        return text_products_fallback.extract_rss_descriptions
    return text_products_fallback.extract_pre_text


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    aviation = config["aviation"]
    outcomes = []

    for item in aviation:
        outcomes.append(
            _engine.run_resource(
                manifest, base_dir, item["id"], item["url"],
                method="text", clean_text_body=True,
                extract_text=_extract_for(item),
                resource_id_hint=item["id"],
                expected_ext="txt",
            )
        )

    return outcomes
