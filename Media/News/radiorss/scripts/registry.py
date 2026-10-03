# ==============================================================================
# FILE: Media/RadioRss/scripts/registry.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Load the RSS category, policy, and feed registry from YAML."""
from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re
from pathlib import Path  # info: from pathlib import Path

import yaml  # info: import yaml

from common import config_dir  # info: from common import config_dir

FEED_ID = re.compile(r"^[a-z][a-z0-9_]*$")  # info: set FEED_ID
PRIORITIES = {"high", "medium", "low"}  # info: set PRIORITIES
ORIGINS = {"external", "overlapping", "unavailable", "native"}  # info: set ORIGINS


# ====================================================
# SECTION: function _load
# What it does: Read one YAML file into a dict. A missing file is an error.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load(path: Path) -> dict:  # info: def _load
    data = yaml.safe_load(path.read_text(encoding="utf-8"))  # info: set data
    if not isinstance(data, dict):  # info: if not isinstance ( data , dict ) :
        raise ValueError(f"{path.name} must be a mapping")  # info: raise ValueError ( f"{ path . name } must be a mapping" )
    return data  # info: return data


# ====================================================
# SECTION: function load_registry
# What it does: Load categories, policy, and feeds. Reject a feed whose category is not configured.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_registry(folder: Path | None = None) -> dict:  # info: def load_registry
    root = folder or config_dir()  # info: set root
    categories = _load(root / "categories.yaml").get("categories") or []  # info: set categories
    policy = _load(root / "policy.yaml")  # info: set policy
    feeds = _load(root / "feeds.yaml").get("feeds") or []  # info: set feeds
    by_id = {}  # info: set by_id
    for row in categories:  # info: for row in categories
        if not isinstance(row, dict) or not row.get("id"):  # info: if not isinstance ( row , dict ) or not row . get ( "id" ) :
            raise ValueError("each category needs an id")  # info: raise ValueError ( "each category needs an id" )
        by_id[row["id"]] = row  # info: by_id [ row [ "id" ] ] = row
    seen = set()  # info: set seen
    clean = []  # info: set clean
    for feed in feeds:  # info: for feed in feeds
        if not isinstance(feed, dict):  # info: if not isinstance ( feed , dict ) :
            raise ValueError("each feed must be a mapping")  # info: raise ValueError ( "each feed must be a mapping" )
        feed_id = str(feed.get("id") or "")  # info: set feed_id
        if not FEED_ID.fullmatch(feed_id):  # info: if not FEED_ID . fullmatch ( feed_id ) :
            raise ValueError(f"bad feed id: {feed_id}")  # info: raise ValueError ( f"bad feed id: { feed_id }" )
        if feed_id in seen:  # info: if feed_id in seen :
            raise ValueError(f"duplicate feed id: {feed_id}")  # info: raise ValueError ( f"duplicate feed id: { feed_id }" )
        seen.add(feed_id)  # info: seen . add ( feed_id )
        category = str(feed.get("category") or "")  # info: set category
        if category not in by_id:  # info: if category not in by_id :
            raise ValueError(f"{feed_id} category is not configured: {category}")  # info: raise ValueError ( f"{ feed_id } category is not configured: { category }" )
        priority = str(feed.get("priority") or "medium")  # info: set priority
        if priority not in PRIORITIES:  # info: if priority not in PRIORITIES :
            raise ValueError(f"{feed_id} priority must be high, medium, or low")  # info: raise ValueError ( f"{ feed_id } priority must be high, medium, or low" )
        origin = str(feed.get("origin") or "external")  # info: set origin
        if origin not in ORIGINS:  # info: if origin not in ORIGINS :
            raise ValueError(f"{feed_id} origin is not recognized")  # info: raise ValueError ( f"{ feed_id } origin is not recognized" )
        kind = str(feed.get("type") or "rss")  # info: set kind
        if kind not in {"rss", "atom"}:  # info: if kind not in { "rss" , "atom" } :
            raise ValueError(f"{feed_id} type must be rss or atom")  # info: raise ValueError ( f"{ feed_id } type must be rss or atom" )
        item = dict(feed)  # info: set item
        item["url"] = str(feed.get("url") or "").strip()  # info: item [ "url" ] = str ( feed . get ( "url" ) or "" ) . strip ( )
        item["enabled"] = bool(feed.get("enabled"))  # info: item [ "enabled" ] = bool ( feed . get ( "enabled" ) )
        item["native_overlap"] = bool(feed.get("native_overlap"))  # info: item [ "native_overlap" ] = bool ( feed . get ( "native_overlap" ) )
        item["priority"] = priority  # info: item [ "priority" ] = priority
        item["origin"] = origin  # info: item [ "origin" ] = origin
        item["type"] = kind  # info: item [ "type" ] = kind
        item["name"] = str(feed.get("name") or feed_id)  # info: item [ "name" ] = str ( feed . get ( "name" ) or feed_id )
        item["provider"] = str(feed.get("provider") or "")  # info: item [ "provider" ] = str ( feed . get ( "provider" ) or "" )
        clean.append(item)  # info: clean . append ( item )
    return {"categories": by_id, "policy": policy, "feeds": clean}  # info: return { "categories" : by_id , "policy" : policy , "feeds" : clean }


# ====================================================
# SECTION: function category_of
# What it does: Return the category row for an id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def category_of(registry: dict, category_id: str) -> dict:  # info: def category_of
    return registry["categories"][category_id]  # info: return registry [ "categories" ] [ category_id ]


# ====================================================
# SECTION: function configured_on
# What it does: True when the YAML asks for this feed and it has a URL. Native and unavailable stay off.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def configured_on(feed: dict) -> bool:  # info: def configured_on
    if not feed.get("enabled") or not feed.get("url"):  # info: if not feed . get ( "enabled" ) or not feed . get ( "url" ) :
        return False  # info: return False
    if feed.get("origin") in {"native", "unavailable"}:  # info: if feed . get ( "origin" ) in { "native" , "unavailable" } :
        return False  # info: return False
    return True  # info: return True
