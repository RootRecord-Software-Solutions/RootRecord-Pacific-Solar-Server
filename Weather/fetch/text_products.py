# ==============================================================================
# FILE: Weather/fetch/text_products.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""api.weather.gov/products/types/{TYPE}/locations/HFO -- PRIMARY path for
text products, per NWS_Hawaii_Resource_Map.md Section 3B. Falls back to
text_products_fallback.py's product.php scrape only if this fails.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json

from core import http_client  # info: from core import http_client
from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine, text_products_fallback  # info: from fetch import _engine , text_products_fallback


# ====================================================
# SECTION: function _extract_latest_product_text
# What it does: Resolve the latest product entry to its full productText record. The products/types endpoint returns an @graph index, not the report body. The first entry's @id is the authoritativ
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _extract_latest_product_text(list_json_bytes: bytes) -> str:  # info: def _extract_latest_product_text
    """Resolve the latest product entry to its full productText record.

    The products/types endpoint returns an @graph index, not the report body.
    The first entry's @id is the authoritative second-hop product record.
    """
    envelope = json.loads(list_json_bytes.decode("utf-8"))  # info: set envelope
    graph = envelope.get("@graph", [])  # info: set graph
    if not graph:  # info: if not graph :
        raise ValueError("no products in @graph -- nothing to extract")  # info: raise ValueError ( "no products in @graph -- nothing to extract" )

    product_url = graph[0].get("@id")  # info: set product_url
    if not isinstance(product_url, str) or not product_url.strip():  # info: if not isinstance ( product_url , str )
        raise ValueError("latest product has no @id")  # info: raise ValueError ( "latest product has no @id" )

    result = http_client.get(  # info: set result
        product_url,  # info: product_url ,
        accept="application/ld+json",  # info: set accept
    )  # info: )
    if result.not_modified or not result.content:  # info: if result . not_modified or not result .
        raise ValueError("latest product record returned no body")  # info: raise ValueError ( "latest product record returned no body" )

    try:  # info: try :
        product = json.loads(result.content.decode("utf-8"))  # info: set product
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:  # info: except ( json . JSONDecodeError , UnicodeDecodeError )
        raise ValueError(f"latest product record is not valid JSON: {exc}") from exc  # info: raise ValueError ( f" latest product record is not valid JSON: { exc }

    product_text = product.get("productText")  # info: set product_text
    if not isinstance(product_text, str) or not product_text.strip():  # info: if not isinstance ( product_text , str )
        raise ValueError("latest product record has no productText")  # info: raise ValueError ( "latest product record has no productText" )

    return product_text.strip()  # info: return product_text . strip ( )


# One entry per text product this module owns (primary API path). Each maps
# to a `types/{AWIPS}/locations/HFO` products-API URL, per the resource map.
# ====================================================
# SECTION: PRODUCT_TYPES
# What it does: Set PRODUCT_TYPES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
PRODUCT_TYPES: dict[str, str] = {  # info: set PRODUCT_TYPES
    "sfp_state_forecast": "SFP",  # info: "sfp_state_forecast" : "SFP" ,
    "zfp_zone_forecast": "ZFP",  # info: "zfp_zone_forecast" : "ZFP" ,
    "afd_area_forecast_discussion": "AFD",  # info: "afd_area_forecast_discussion" : "AFD" ,
    "nowhfo_short_term_forecast": "NOW",  # info: "nowhfo_short_term_forecast" : "NOW" ,
    "hwo_hazardous_weather_outlook": "HWO",  # info: "hwo_hazardous_weather_outlook" : "HWO" ,
    "cwf_coastal_waters": "CWF",  # info: "cwf_coastal_waters" : "CWF" ,
}  # info: }


# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str, only: set[str] | None = None) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    outcomes = []  # info: set outcomes
    for resource_id, awips_type in PRODUCT_TYPES.items():  # info: for resource_id , awips_type in PRODUCT_TYPES . items
        if only is not None and resource_id not in only:  # info: if only is not None and resource_id not
            continue  # info: continue
        url = f"https://api.weather.gov/products/types/{awips_type}/locations/HFO"  # info: set url
        outcome = _engine.run_resource(  # info: set outcome
            manifest, base_dir, resource_id, url,  # info: manifest , base_dir , resource_id , url ,
            method="text",  # info: set method
            accept="application/ld+json",  # info: set accept
            clean_text_body=True,  # info: set clean_text_body
            extract_text=_extract_latest_product_text,  # info: set extract_text
        )  # info: )
        if (  # info: if (
            resource_id in {"nowhfo_short_term_forecast", "hwo_hazardous_weather_outlook"}  # info: resource_id in { "nowhfo_short_term_forecast" , "hwo_hazardous_weather_outlook" }
            and outcome.status in {"failed", "invalid"}  # info: and outcome . status in { "failed" ,
        ):  # info: ) :
            # HFO often has no active NOW/HWO in the products API. The
            # configured fallback page is the live office product (a nowcast
            # page, or the hazard feed) rather than an empty product.php shell.
            page_outcome = _fetch_configured_fallback(manifest, base_dir, resource_id)  # info: set page_outcome
            if page_outcome is not None and page_outcome.status not in {"failed", "invalid"}:  # info: if page_outcome is not None and page_outcome .
                outcomes.append(page_outcome)  # info: outcomes . append ( page_outcome )
                continue  # info: continue
            if page_outcome is not None:  # info: if page_outcome is not None :
                outcome = page_outcome  # info: set outcome
        if outcome.status in {"failed", "invalid"}:  # info: if outcome . status in { "failed" ,
            # Primary path down -- fall back to the product.php scrape for
            # whichever product has a known fallback URL configured.
            fallback_outcome = text_products_fallback.fetch_one(manifest, base_dir, resource_id)  # info: set fallback_outcome
            if fallback_outcome is not None and fallback_outcome.status not in {"failed", "invalid"}:  # info: if fallback_outcome is not None and fallback_outcome .
                outcomes.append(fallback_outcome)  # info: outcomes . append ( fallback_outcome )
            else:  # info: else :
                outcomes.append(outcome)  # info: outcomes . append ( outcome )
        else:  # info: else :
            outcomes.append(outcome)  # info: outcomes . append ( outcome )
    return outcomes  # info: return outcomes


# ====================================================
# SECTION: function _fetch_configured_fallback
# What it does:  fetch configured fallback.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fetch_configured_fallback(manifest: Manifest, base_dir: str, resource_id: str):  # info: def _fetch_configured_fallback
    config = _engine.load_resources_yaml()  # info: set config
    item = next((entry for entry in config.get("text_products", []) if entry.get("id") == resource_id), None)  # info: set item
    if not item:  # info: if not item :
        return None  # info: return None
    url = item.get("fallback_url")  # info: set url
    if not url:  # info: if not url :
        return None  # info: return None
    extract = text_products_fallback.extract_rss_descriptions if url.endswith(".xml") else text_products_fallback.extract_pre_text  # info: set extract
    return _engine.run_resource(  # info: return _engine . run_resource (
        manifest, base_dir, resource_id, url,  # info: manifest , base_dir , resource_id , url ,
        method="text",  # info: set method
        clean_text_body=True,  # info: set clean_text_body
        extract_text=extract,  # info: set extract_text
        expected_ext="txt",  # info: set expected_ext
        resource_id_hint=resource_id,  # info: set resource_id_hint
    )  # info: )
