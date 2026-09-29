"""HFO-hosted IR satellite gifs + the GOES-18 NESDIS sector gif. Reads
its resource list from config/resources.yaml (`satellite:` section) rather
than hardcoding URLs twice.
"""
from __future__ import annotations

from core.manifest import Manifest
from fetch import _engine


def fetch_all(manifest: Manifest, base_dir: str) -> list[_engine.FetchOutcome]:
    config = _engine.load_resources_yaml()
    satellite = config["satellite"]
    outcomes = []

    for item in satellite["items"]:
        outcomes.append(
            _engine.run_resource(manifest, base_dir, item["id"], item["url"], method="image")
        )

    # Loop frames: {base_url}/{00..10}.gif per sector, per config's
    # loop_frame_sectors block. Each frame gets its own resource id so the
    # manifest/archiver treat them as independent resources (they change
    # independently as the loop advances).
    lfs = satellite.get("loop_frame_sectors", {})
    lo, hi = lfs.get("frame_range", [0, 10])
    for sector in lfs.get("sectors", []):
        for frame in range(lo, hi + 1):
            frame_id = f"satellite_loop_{sector['key']}_{frame:02d}"
            url = f"{sector['base_url']}{frame:02d}.gif"
            outcomes.append(
                _engine.run_resource(manifest, base_dir, frame_id, url, method="image")
            )

    return outcomes
