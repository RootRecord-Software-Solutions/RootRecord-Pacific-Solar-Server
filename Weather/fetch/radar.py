"""radar.weather.gov/ridge/standard/HAWAII_loop.gif (static, Tier 6) + FTM
radar status text. The interactive Ridge2 tile viewer is explicitly out of
scope -- see config/resources.yaml `radar.interactive_reference_only`.
"""
from __future__ import annotations

import re

from core.manifest import Manifest
from fetch import _engine

# /hfo/FTM is a real HTML page (not a plain-text product like the
# api.weather.gov or product.php resources), reporting all FOUR Hawaii
# radars' outage status separately, each inside its own <pre> block:
#   <strong>NAME (CODE)&nbsp;<a href="...">...</a></strong></p>
#   <p>    <pre>STATUS TEXT</pre></p>
# A single "grab the first <pre>" extractor (like
# text_products_fallback.extract_pre_text) would silently drop the other
# three radars' status -- this keeps each block paired with its own label.
# Confirmed against a live fetch of /hfo/FTM on 2026-09-25/26.
_FTM_BLOCK_RE = re.compile(
    r'<strong>([^<]*?)&nbsp;<a[^>]*>.*?</strong>\s*</p>\s*<p>\s*<pre>(.*?)</pre>',
    re.DOTALL,
)


def extract_ftm_status(html_bytes: bytes) -> str:
    """Pulls each per-radar status block out of /hfo/FTM's HTML page,
    keeping each radar's own label attached to its message so four separate
    statuses don't collapse into one unlabeled blob.
    """
    html = html_bytes.decode("utf-8", errors="replace")
    blocks = _FTM_BLOCK_RE.findall(html)
    if not blocks:
        raise ValueError("no radar status blocks found -- page shape may have changed")

    sections = []
    for label, body in blocks:
        label = label.strip()
        for entity, char in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")):
            label = label.replace(entity, char)
            body = body.replace(entity, char)
        sections.append(f"{label}\n{body.strip()}")

    return "\n\n----\n\n".join(sections)


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    radar = config["radar"]
    outcomes = []

    for item in radar["items"]:
        method = item.get("method", "image")
        if method == "image":
            outcomes.append(
                _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")
            )
        else:  # ftm_radar_status -- HTML page, 4 per-radar <pre> blocks (see extract_ftm_status)
            outcomes.append(
                _engine.run_resource(
                    manifest, base_dir, item["id"], item["url"],
                    method="text", clean_text_body=True,
                    extract_text=extract_ftm_status,
                )
            )

    return outcomes
