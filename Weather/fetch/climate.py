# ==============================================================================
# FILE: Weather/fetch/climate.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""CLI/CLM/RRA daily+monthly climate summaries, station obhistory. Expands
the per-station `url_template` entries in config/resources.yaml (one
resource per station per product) rather than hand-listing each combination.
"""
from __future__ import annotations  # info: from __future__ import annotations

from core import http_client  # info: from core import http_client
from core.manifest import Manifest  # info: from core . manifest import Manifest
from fetch import _engine, text_products_fallback  # info: from fetch import _engine , text_products_fallback

_CLI_STATIONS = ("HNL", "LIH", "OGG", "ITO")  # info: set _CLI_STATIONS


# ====================================================
# SECTION: function extract_rtp_or_cli
# What it does: Use the RTPHI product when HFO has issued one. The regional table is often unpublished. The four daily climate summaries are the current statewide temp and precip products.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def extract_rtp_or_cli(page_bytes: bytes) -> str:  # info: def extract_rtp_or_cli
    """Use the RTPHI product when HFO has issued one.

    The regional table is often unpublished. The four daily climate
    summaries are the current statewide temp and precip products.
    """
    try:  # info: try :
        text = text_products_fallback.extract_pre_text(page_bytes)  # info: set text
    except ValueError:  # info: except ValueError :
        text = ""  # info: set text
    if text and "none issued" not in text.lower():  # info: if text and "none issued" not in text .
        return text  # info: return text
    parts: list[str] = []  # info: set parts
    for station in _CLI_STATIONS:  # info: for station in _CLI_STATIONS :
        url = (  # info: set url
            "https://forecast.weather.gov/product.php?site=HFO"  # info: "https://forecast.weather.gov/product.php?site=HFO"
            f"&product=CLI&issuedby={station}"  # info: f" &product=CLI&issuedby= { station } "
        )  # info: )
        result = http_client.get(url)  # info: set result
        if result.not_modified or not result.content:  # info: if result . not_modified or not result .
            raise ValueError(f"CLI {station} returned no body")  # info: raise ValueError ( f" CLI { station }
        parts.append(f"CLI{station}\n" + text_products_fallback.extract_pre_text(result.content))  # info: parts . append ( f" CLI { station
    return "\n\n".join(parts)  # info: return "\n\n" . join ( parts )


# ====================================================
# SECTION: function fetch_all
# What it does: fetch all.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_all(manifest: Manifest, base_dir: str, only: set[str] | None = None) -> list[_engine.FetchOutcome]:  # info: def fetch_all
    config = _engine.load_resources_yaml()  # info: set config
    climate = config["climate"]  # info: set climate
    outcomes = []  # info: set outcomes

    for item in climate["items"]:  # info: for item in climate [ "items" ] :
        if only is not None and item["id"] not in only:  # info: if only is not None and item [
            continue  # info: continue
        if "url_template" in item:  # info: if "url_template" in item :
            for station in item["stations"]:  # info: for station in item [ "stations" ] :
                resource_id = f"{item['id']}_{station}"  # info: set resource_id
                url = item["url_template"].format(station=station)  # info: set url
                outcomes.append(  # info: outcomes . append (
                    _engine.run_resource(  # info: _engine . run_resource (
                        manifest, base_dir, resource_id, url,  # info: manifest , base_dir , resource_id , url ,
                        method="text", clean_text_body=item.get("clean_text", True),  # info: set method
                        extract_text=text_products_fallback.extract_pre_text,  # info: set extract_text
                        expected_ext="txt",  # info: set expected_ext
                        resource_id_hint=resource_id,  # info: set resource_id_hint
                    )  # info: )
                )  # info: )
        elif item["method"] == "image":  # info: elif item [ "method" ] == "image" :
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")  # info: _engine . run_resource ( manifest , base_dir ,
            )  # info: )
        elif item["id"] == "rtp_temp_precip_summary":  # info: elif item [ "id" ] == "rtp_temp_precip_summary" :
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                    method="text", clean_text_body=True,  # info: set method
                    extract_text=extract_rtp_or_cli,  # info: set extract_text
                    expected_ext="txt",  # info: set expected_ext
                    resource_id_hint=item["id"],  # info: set resource_id_hint
                )  # info: )
            )  # info: )
        elif item["url"].endswith(".xml"):  # info: elif item [ "url" ] . endswith (
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                    method="text", clean_text_body=True,  # info: set method
                    extract_text=text_products_fallback.extract_rss_descriptions,  # info: set extract_text
                    expected_ext="txt",  # info: set expected_ext
                    resource_id_hint=item["id"],  # info: set resource_id_hint
                )  # info: )
            )  # info: )
        elif "product.php" in item["url"]:  # info: elif "product.php" in item [ "url" ] :
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                    method="text", clean_text_body=True,  # info: set method
                    extract_text=text_products_fallback.extract_pre_text,  # info: set extract_text
                    expected_ext="txt",  # info: set expected_ext
                    resource_id_hint=item["id"],  # info: set resource_id_hint
                )  # info: )
            )  # info: )
        else:  # info: else :
            outcomes.append(  # info: outcomes . append (
                _engine.run_resource(  # info: _engine . run_resource (
                    manifest, base_dir, item["id"], item["url"],  # info: manifest , base_dir , item [ "id" ]
                    method="text", clean_text_body=True,  # info: set method
                )  # info: )
            )  # info: )

    return outcomes  # info: return outcomes


# ====================================================
# SECTION: function fetch_observations
# What it does: Per-station current-obs pages (Section 3 of the resource map). Kept in this module rather than a separate fetch/observations.py per fetch/README.md's note -- promote it later if th
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_observations(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:  # info: def fetch_observations
    """Per-station current-obs pages (Section 3 of the resource map). Kept in
    this module rather than a separate fetch/observations.py per
    fetch/README.md's note -- promote it later if this grows.
    """
    config = _engine.load_resources_yaml()  # info: set config
    obs = config["observations"]  # info: set obs
    outcomes = []  # info: set outcomes
    for icao in obs["stations"]:  # info: for icao in obs [ "stations" ] :
        resource_id = f"obhistory_{icao}"  # info: set resource_id
        url = obs["obhistory_url_template"].format(icao=icao)  # info: set url
        outcomes.append(  # info: outcomes . append (
            _engine.run_resource(manifest, base_dir, resource_id, url, method="text", clean_text_body=False)  # info: _engine . run_resource ( manifest , base_dir ,
        )  # info: )
    return outcomes  # info: return outcomes
