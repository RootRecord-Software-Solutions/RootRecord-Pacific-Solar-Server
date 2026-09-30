# ==============================================================================
# FILE: Weather/fetch/text_products_fallback.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""forecast.weather.gov/product.php scrape -- fallback path only, called by
text_products.py when the api.weather.gov products API fails. Also the
PRIMARY path for products that have no confirmed API type mapping yet
(SFT, PFM, FWF, aviation, marine, climate -- see config/resources.yaml).
"""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re

from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine  # info: from fetch import _engine

# Fallback / primary-by-necessity URLs, keyed by the same resource_id used
# in config/resources.yaml, so a caller can look one up without duplicating
# the URL here.
# ====================================================
# SECTION: FALLBACK_URLS
# What it does: Set FALLBACK_URLS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
FALLBACK_URLS: dict[str, str] = {  # info: set FALLBACK_URLS
    "sfp_state_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=SFT&issuedby=HFO",  # info: "sfp_state_forecast" : "https://forecast.weather.gov/product.php?site=HFO&product=SFT&issuedby=HFO" ,
    "sft_tabular_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=SFT&issuedby=HFO",  # info: "sft_tabular_forecast" : "https://forecast.weather.gov/product.php?site=HFO&product=SFT&issuedby=HFO" ,
    "pfm_point_forecast_matrix": "https://forecast.weather.gov/product.php?site=HFO&product=PFM&issuedby=HFO",  # info: "pfm_point_forecast_matrix" : "https://forecast.weather.gov/product.php?site=HFO&product=PFM&issuedby=HFO" ,
    "fwf_fire_weather_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=FWF&issuedby=HFO",  # info: "fwf_fire_weather_forecast" : "https://forecast.weather.gov/product.php?site=HFO&product=FWF&issuedby=HFO" ,
    "zfp_zone_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=ZFP&issuedby=HFO",  # info: "zfp_zone_forecast" : "https://forecast.weather.gov/product.php?site=HFO&product=ZFP&issuedby=HFO" ,
    "afd_area_forecast_discussion": "https://forecast.weather.gov/product.php?site=HFO&product=AFD&issuedby=HFO",  # info: "afd_area_forecast_discussion" : "https://forecast.weather.gov/product.php?site=HFO&product=AFD&issuedby=HFO" 
    "nowhfo_short_term_forecast": "https://forecast.weather.gov/product.php?site=HFO&product=NOW&issuedby=HFO",  # info: "nowhfo_short_term_forecast" : "https://forecast.weather.gov/product.php?site=HFO&product=NOW&issuedby=HFO" ,
    "hwo_hazardous_weather_outlook": "https://forecast.weather.gov/product.php?site=HFO&product=HWO&issuedby=HFO",  # info: "hwo_hazardous_weather_outlook" : "https://forecast.weather.gov/product.php?site=HFO&product=HWO&issuedby=HFO"
    "cwf_coastal_waters": "https://forecast.weather.gov/product.php?site=HFO&product=CWF&issuedby=HFO",  # info: "cwf_coastal_waters" : "https://forecast.weather.gov/product.php?site=HFO&product=CWF&issuedby=HFO" ,
}  # info: }

# The product text on a product.php page sits inside a single <pre> block.
_PRE_BLOCK_RE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.DOTALL | re.IGNORECASE)  # info: set _PRE_BLOCK_RE


# ====================================================
# SECTION: function _unescape_product_text
# What it does:  unescape product text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _unescape_product_text(text: str) -> str:  # info: def _unescape_product_text
    for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'"), ("&nbsp;", " ")):
        text = text.replace(entity, char)  # info: set text
    return text.strip()  # info: return text . strip ( )


# ====================================================
# SECTION: function extract_pre_text
# What it does: extract pre text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def extract_pre_text(html_bytes: bytes) -> str:  # info: def extract_pre_text
    html = html_bytes.decode("utf-8", errors="replace")  # info: set html
    match = _PRE_BLOCK_RE.search(html)  # info: set match
    if not match:  # info: if not match :
        raise ValueError("no <pre> block found -- page shape may have changed or returned an error page")  # info: raise ValueError ( "no <pre> block found -- page shape may have changed or returned an error page" )
    # Some HFO pages (the marine matrix) put the product in <pre> but still
    # separate lines with <br>. Turn those into newlines and drop the tags.
    text = match.group(1)  # info: set text
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)  # info: set text
    text = _TAG_RE.sub("", text)  # info: set text
    return _unescape_product_text(text)  # info: return _unescape_product_text ( text )


_ITEM_RE = re.compile(r"<item\b[^>]*>(.*?)</item>", re.DOTALL | re.IGNORECASE)  # info: set _ITEM_RE
_DESC_RE = re.compile(r"<description\b[^>]*>(.*?)</description>", re.DOTALL | re.IGNORECASE)  # info: set _DESC_RE
_CDATA_RE = re.compile(r"<!\[CDATA\[(.*?)\]\]>", re.DOTALL)  # info: set _CDATA_RE
_TAG_RE = re.compile(r"<[^>]+>")  # info: set _TAG_RE


# ====================================================
# SECTION: function extract_rss_descriptions
# What it does: Pull forecast text out of an HFO RSS/XML feed. Item descriptions are either plain product text (TAFs) or HTML that wraps the product. Prefer a <pre> block when the description has 
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def extract_rss_descriptions(xml_bytes: bytes) -> str:  # info: def extract_rss_descriptions
    """Pull forecast text out of an HFO RSS/XML feed.

    Item descriptions are either plain product text (TAFs) or HTML that
    wraps the product. Prefer a <pre> block when the description has one.
    """
    xml = xml_bytes.decode("utf-8", errors="replace")  # info: set xml
    chunks: list[str] = []  # info: set chunks
    for item in _ITEM_RE.findall(xml):  # info: for item in _ITEM_RE . findall ( xml
        desc_match = _DESC_RE.search(item)  # info: set desc_match
        if not desc_match:  # info: if not desc_match :
            continue  # info: continue
        desc = desc_match.group(1).strip()  # info: set desc
        cdata = _CDATA_RE.search(desc)  # info: set cdata
        if cdata:  # info: if cdata :
            desc = cdata.group(1)  # info: set desc
        pre = _PRE_BLOCK_RE.search(desc)  # info: set pre
        text = pre.group(1) if pre else _TAG_RE.sub(" ", desc)  # info: set text
        text = _unescape_product_text(text)  # info: set text
        text = re.sub(r"[ \t]+\n", "\n", text)  # info: set text
        text = re.sub(r"\n{3,}", "\n\n", text).strip()  # info: set text
        if text:  # info: if text :
            chunks.append(text)  # info: chunks . append ( text )
    if not chunks:  # info: if not chunks :
        raise ValueError("no RSS item descriptions -- feed had no product text")  # info: raise ValueError ( "no RSS item descriptions -- feed had no product text" )
    # HFO archive feeds list newest first. Keep a bounded set so a 90-day
    # rainfall file stays a product body rather than the whole history.
    return "\n\n".join(chunks[:12])  # info: return "\n\n" . join ( chunks [ :


# ====================================================
# SECTION: function fetch_one
# What it does: fetch one.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_one(manifest: Manifest, base_dir: str, resource_id: str) -> _engine.FetchOutcome | None:  # info: def fetch_one
    url = FALLBACK_URLS.get(resource_id)  # info: set url
    if url is None:  # info: if url is None :
        return None  # info: return None
    return _engine.run_resource(  # info: return _engine . run_resource (
        manifest, base_dir, resource_id, url,  # info: manifest , base_dir , resource_id , url ,
        method="text",  # info: set method
        clean_text_body=True,  # info: set clean_text_body
        extract_text=extract_pre_text,  # info: set extract_text
        expected_ext="txt",  # info: set expected_ext
        resource_id_hint=resource_id,  # product.php URLs disambiguate by query string
    )  # info: )


# ====================================================
# SECTION: function fetch_all
# What it does: Direct-run entry point for products that don't have a confirmed API type yet and so use this scrape as their primary (not just fallback) path -- see config/resources.yaml `method: 
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    """Direct-run entry point for products that don't have a confirmed API
    type yet and so use this scrape as their primary (not just fallback)
    path -- see config/resources.yaml `method: scrape` entries.
    """
    outcomes = []  # info: set outcomes
    for resource_id in FALLBACK_URLS:  # info: for resource_id in FALLBACK_URLS :
        outcome = fetch_one(manifest, base_dir, resource_id)  # info: set outcome
        if outcome is not None:  # info: if outcome is not None :
            outcomes.append(outcome)  # info: outcomes . append ( outcome )
    return outcomes  # info: return outcomes
