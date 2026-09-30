"""forecast.weather.gov/product.php scrape -- fallback path only, called by
text_products.py when the api.weather.gov products API fails. Also the
PRIMARY path for products that have no confirmed API type mapping yet
(SFT, PFM, FWF, aviation, marine, climate -- see config/resources.yaml).
"""
from __future__ import annotations

import re

from core.manifest import Manifest
from fetch import _engine

# Fallback / primary-by-necessity URLs, keyed by the same resource_id used
# in config/resources.yaml, so a caller can look one up without duplicating
# the URL here.
FALLBACK_URLS: dict[str, str] = {
    "sfp_state_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=SFT&issuedby=HFO",
    "sft_tabular_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=SFT&issuedby=HFO",
    "pfm_point_forecast_matrix": "https://forecast.weather.gov/product.php?site=HFO&product=PFM&issuedby=HFO",
    "fwf_fire_weather_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=FWF&issuedby=HFO",
    "zfp_zone_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=ZFP&issuedby=HFO",
    "afd_area_forecast_discussion": "https://forecast.weather.gov/product.php?site=HFO&product=AFD&issuedby=HFO",
    "nowhfo_short_term_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=NOW&issuedby=HFO",
    "hwo_hazardous_weather_outlook": "https://forecast.weather.gov/product.php?site=HFO&product=HWO&issuedby=HFO",
    "cwf_coastal_waters": "https://forecast.weather.gov/product.php?site=HFO&product=CWF&issuedby=HFO",
}

# The product text on a product.php page sits inside a single <pre> block.
_PRE_BLOCK_RE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.DOTALL | re.IGNORECASE)


def _unescape_product_text(text: str) -> str:
    for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")):
        text = text.replace(entity, char)
    return text.strip()


def extract_pre_text(html_bytes: bytes) -> str:
    html = html_bytes.decode("utf-8", errors="replace")
    match = _PRE_BLOCK_RE.search(html)
    if not match:
        raise ValueError("no <pre> block found -- page shape may have changed or returned an error page")
    # Minimal unescape -- product.php text is plain enough that the common
    # HTML entities are the only ones likely to appear.
    return _unescape_product_text(match.group(1))


_ITEM_RE = re.compile(r"<item\b[^>]*>(.*?)</item>", re.DOTALL | re.IGNORECASE)
_DESC_RE = re.compile(r"<description\b[^>]*>(.*?)</description>", re.DOTALL | re.IGNORECASE)
_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def extract_rss_descriptions(xml_bytes: bytes) -> str:
    """Pull forecast text out of an HFO RSS/XML feed.

    Item descriptions are either plain product text (TAFs) or HTML that
    wraps the product. Prefer a <pre> block when the description has one.
    """
    xml = xml_bytes.decode("utf-8", errors="replace")
    chunks: list[str] = []
    for item in _ITEM_RE.findall(xml):
        desc_match = _DESC_RE.search(item)
        if not desc_match:
            continue
        desc = desc_match.group(1).strip()
        cdata = _CDATA_RE.search(desc)
        if cdata:
            desc = cdata.group(1)
        pre = _PRE_BLOCK_RE.search(desc)
        text = pre.group(1) if pre else _TAG_RE.sub(" ", desc)
        text = _unescape_product_text(text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            chunks.append(text)
    if not chunks:
        raise ValueError("no RSS item descriptions -- feed had no product text")
    # HFO archive feeds list newest first. Keep a bounded set so a 90-day
    # rainfall file stays a product body rather than the whole history.
    return "\n\n".join(chunks[:12])


def fetch_one(manifest: Manifest, base_dir: str, resource_id: str) -> _engine.FetchOutcome | None:
    url = FALLBACK_URLS.get(resource_id)
    if url is None:
        return None
    return _engine.run_resource(
        manifest, base_dir, resource_id, url,
        method="text",
        clean_text_body=True,
        extract_text=extract_pre_text,
        expected_ext="txt",
        resource_id_hint=resource_id,  # product.php URLs disambiguate by query string
    )


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    """Direct-run entry point for products that don't have a confirmed API
    type yet and so use this scrape as their primary (not just fallback)
    path -- see config/resources.yaml `method: scrape` entries.
    """
    outcomes = []
    for resource_id in FALLBACK_URLS:
        outcome = fetch_one(manifest, base_dir, resource_id)
        if outcome is not None:
            outcomes.append(outcome)
    return outcomes
