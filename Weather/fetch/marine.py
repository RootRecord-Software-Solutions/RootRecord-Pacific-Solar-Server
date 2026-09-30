# ==============================================================================
# FILE: Weather/fetch/marine.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Marine text products + marine zone map images. Text entries use the
product.php scrape (no confirmed structured-API type for most of these yet);
image entries are static charts. Data-driven from config/resources.yaml.
"""
from __future__ import annotations  # info: from __future__ import annotations

from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine, text_products_fallback  # info: from fetch import _engine , text_products_fallback


# ====================================================
# SECTION: function _extract_marine_text
# What it does:  extract marine text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _extract_marine_text(body: bytes) -> str:  # info: def _extract_marine_text
    if b"<pre" in body.lower():  # info: if b"<pre" in body . lower ( )
        return text_products_fallback.extract_pre_text(body)  # info: return text_products_fallback . extract_pre_text ( body )
    text = body.decode("utf-8", errors="replace").strip()  # info: set text
    if not text:  # info: if not text :
        raise ValueError("empty marine product body")  # info: raise ValueError ( "empty marine product body" )
    return text  # info: return text


# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str, only: set[str] | None = None) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    config = _engine.load_resources_yaml()  # info: set config
    marine = config["marine"]  # info: set marine
    outcomes = []  # info: set outcomes

    for item in marine:  # info: for item in marine :
        if only is not None and item["id"] not in only:  # info: if only is not None and item [
            continue  # info: continue
        if item["id"] == "cwf_coastal_waters":  # info: if item [ "id" ] == "cwf_coastal_waters" :
            # Sole owner is fetch/text_products.py, which already handles the
            # CWF API resource. Running it here as well creates two concurrent
            # writers for the same manifest resource_id.
            continue  # info: continue

        method = item["method"]  # info: set method
        if method == "image":  # info: if method == "image" :
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")  # info: _engine . run_resource ( manifest , base_dir ,
            )  # info: )
        elif method == "scrape" and "product.php" in item["url"]:  # info: elif method == "scrape" and "product.php" in item
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                    method="text", clean_text_body=True,  # info: set method
                    extract_text=text_products_fallback.extract_pre_text,  # info: set extract_text
                    resource_id_hint=item["id"],  # info: set resource_id_hint
                )  # info: )
            )  # info: )
        elif method == "scrape":  # info: elif method == "scrape" :
            # /hfo/MFM, /hfo/SRF, /hfo/surfreports wrap the product in <pre>.
            # Plain-text successors (tgftp high-seas bulletins) have no tags;
            # extract_pre falls through to the raw body for those.
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                    method="text", clean_text_body=True,  # info: set method
                    extract_text=_extract_marine_text,  # info: set extract_text
                    resource_id_hint=item["id"],  # info: set resource_id_hint
                    expected_ext="txt",  # info: set expected_ext
                )  # info: )
            )  # info: )

    return outcomes  # info: return outcomes
