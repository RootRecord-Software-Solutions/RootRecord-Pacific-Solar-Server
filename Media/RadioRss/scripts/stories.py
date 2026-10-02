# ==============================================================================
# FILE: Media/RadioRss/scripts/stories.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Normalize, classify, score, and cluster external stories. Rules come from policy YAML."""
from __future__ import annotations  # info: from __future__ import annotations

from datetime import timedelta  # info: from datetime import timedelta

from common import canonical_url, digest, iso, jaccard, parse_iso, plain, title_norm, tokens, utc_now  # info: from common import canonical_url , digest , iso , jaccard , parse_iso , plain , title_norm , tokens , utc_now

RANK = {"low": 1, "normal": 2, "high": 3, "urgent": 4}  # info: set RANK
NAME = {1: "low", 2: "normal", 3: "high", 4: "urgent"}  # info: set NAME


# ====================================================
# SECTION: function _hit
# What it does: True when any configured phrase appears in the text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _hit(text: str, patterns: list) -> bool:  # info: def _hit
    low = (text or "").lower()  # info: set low
    return any(str(pattern).lower() in low for pattern in patterns or [])  # info: return any ( str ( pattern ) . lower ( ) in low for pattern in patterns or [ ] )


# ====================================================
# SECTION: function _cap
# What it does: Lower a priority when a category cap says so.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cap(priority: str, cap: str | None) -> str:  # info: def _cap
    if not cap:  # info: if not cap :
        return priority  # info: return priority
    if RANK.get(priority, 2) > RANK.get(cap, 4):  # info: if RANK . get ( priority , 2 ) > RANK . get ( cap , 4 ) :
        return cap  # info: return cap
    return priority  # info: return priority


# ====================================================
# SECTION: function classify
# What it does: Start from the feed category and move the item when a configured rule matches.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def classify(feed: dict, item: dict, registry: dict) -> str:  # info: def classify
    category = feed["category"]  # info: set category
    text = f"{item.get('title') or ''} {item.get('summary') or ''}"  # info: set text
    for rule in (registry["policy"].get("category_rules") or []):  # info: for rule in ( registry [ "policy" ] . get ( "category_rules" ) or [ ] )
        target = str(rule.get("category") or "")  # info: set target
        if target not in registry["categories"]:  # info: if target not in registry [ "categories" ] :
            continue  # info: continue
        if _hit(text, rule.get("patterns") or []):  # info: if _hit ( text , rule . get ( "patterns" ) or [ ] ) :
            return target  # info: return target
    return category  # info: return category


# ====================================================
# SECTION: function score
# What it does: Raise priority from configured phrases. The feed priority is only the floor.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def score(feed: dict, item: dict, category: str, registry: dict) -> str:  # info: def score
    policy = registry["policy"]  # info: set policy
    floors = policy.get("priority_floor") or {}  # info: set floors
    level = RANK.get(floors.get(feed.get("priority") or "medium", "normal"), 2)  # info: set level
    text = f"{item.get('title') or ''} {item.get('summary') or ''}"  # info: set text
    signals = policy.get("priority_signals") or {}  # info: set signals
    if _hit(text, signals.get("urgent") or []):  # info: if _hit ( text , signals . get ( "urgent" ) or [ ] ) :
        level = max(level, 4)  # info: set level
    elif _hit(text, signals.get("high") or []):  # info: elif _hit ( text , signals . get ( "high" ) or [ ] ) :
        level = max(level, 3)  # info: set level
    cap = (policy.get("category_priority_cap") or {}).get(category)  # info: set cap
    return _cap(NAME[level], cap)  # info: return _cap ( NAME [ level ] , cap )


# ====================================================
# SECTION: function blocked
# What it does: Drop an item that repeats a RootRecord native desk. Only overlapping feeds use this.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def blocked(feed: dict, item: dict, registry: dict) -> bool:  # info: def blocked
    if not feed.get("native_overlap"):  # info: if not feed . get ( "native_overlap" ) :
        return False  # info: return False
    text = f"{item.get('title') or ''} {item.get('summary') or ''}"  # info: set text
    return _hit(text, registry["policy"].get("overlap_patterns") or [])  # info: return _hit ( text , registry [ "policy" ] . get ( "overlap_patterns" ) or [ ] )


# ====================================================
# SECTION: function violent
# What it does: Drop a violent-crime item when the feed is marked nonviolent. Hawaii uses this.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def violent(feed: dict, item: dict, registry: dict) -> bool:  # info: def violent
    if not feed.get("nonviolent"):  # info: if not feed . get ( "nonviolent" ) :
        return False  # info: return False
    text = f"{item.get('title') or ''} {item.get('summary') or ''}"  # info: set text
    return _hit(text, registry["policy"].get("violence_patterns") or [])  # info: return _hit ( text , registry [ "policy" ] . get ( "violence_patterns" ) or [ ] )



# ====================================================
# SECTION: function sports
# What it does: Drop a sports item from every feed. League names and /sports/ URLs match. Bare "sport" is not used so transportation stays.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sports(feed: dict, item: dict, registry: dict) -> bool:  # info: def sports
    text = f"{item.get('title') or ''} {item.get('summary') or ''} {item.get('url') or ''} {item.get('guid') or ''} {item.get('canonical_url') or ''}"  # info: set text
    return _hit(text, registry["policy"].get("sports_patterns") or [])  # info: return _hit ( text , registry [ "policy" ] . get ( "sports_patterns" ) or [ ] )


# ====================================================
# SECTION: function _required
# What it does: Keep an item when the feed lists required phrases. A feed with no list keeps every item.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _required(feed: dict, item: dict) -> bool:  # info: def _required
    patterns = feed.get("require_patterns") or []  # info: set patterns
    if not patterns:  # info: if not patterns :
        return True  # info: return True
    text = f"{item.get('title') or ''} {item.get('summary') or ''}"  # info: set text
    return _hit(text, patterns)  # info: return _hit ( text , patterns )


# ====================================================
# SECTION: function normalize
# What it does: Turn one feed item into the story object. Empty titles, overlap, violence, and sports items are dropped.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def normalize(feed: dict, item: dict, registry: dict) -> dict | None:  # info: def normalize
    title = plain(item.get("title"), 300)  # info: set title
    if not title:  # info: if not title :
        return None  # info: return None
    url = (item.get("url") or "").strip()  # info: set url
    guid = (item.get("guid") or "").strip()  # info: set guid
    if not url and not guid:  # info: if not url and not guid :
        return None  # info: return None
    if blocked(feed, item, registry) or violent(feed, item, registry) or sports(feed, item, registry):  # info: if blocked ( feed , item , registry ) or violent ( feed , item , registry ) or sports ( feed , item , registry ) :
        return None  # info: return None
    if not _required(feed, item):  # info: if not _required ( feed , item ) :
        return None  # info: return None
    category = classify(feed, item, registry)  # info: set category
    summary = plain(item.get("summary"), 1200)  # info: set summary
    norm = title_norm(title)  # info: set norm
    canon = canonical_url(url)  # info: set canon
    political = 1 if _hit(f"{title} {summary}", registry["policy"].get("political_patterns") or []) else 0  # info: set political
    now = iso(utc_now())  # info: set now
    story_id = digest(feed["id"], guid or canon or norm)  # info: set story_id
    return {  # info: return {
        "id": story_id,  # info: "id" : story_id ,
        "source_id": feed["id"],  # info: "source_id" : feed [ "id" ] ,
        "source_name": feed["name"],  # info: "source_name" : feed [ "name" ] ,
        "provider": feed.get("provider") or "",  # info: "provider" : feed . get ( "provider" ) or "" ,
        "category": category,  # info: "category" : category ,
        "title": title,  # info: "title" : title ,
        "summary": summary,  # info: "summary" : summary ,
        "url": url,  # info: "url" : url ,
        "canonical_url": canon,  # info: "canonical_url" : canon ,
        "published_at": item.get("published_at") or "",  # info: "published_at" : item . get ( "published_at" ) or "" ,
        "updated_at": item.get("updated_at") or item.get("published_at") or "",  # info: "updated_at" : item . get ( "updated_at" ) or item . get ( "published_at" ) or "" ,
        "author": plain(item.get("author"), 200),  # info: "author" : plain ( item . get ( "author" ) , 200 ) ,
        "guid": guid,  # info: "guid" : guid ,
        "content_hash": digest(norm, title_norm(summary), n=32),  # info: "content_hash" : digest ( norm , title_norm ( summary ) , n = 32 ) ,
        "title_norm": norm,  # info: "title_norm" : norm ,
        "priority": score(feed, item, category, registry),  # info: "priority" : score ( feed , item , category , registry ) ,
        "status": "new",  # info: "status" : "new" ,
        "first_seen_at": now,  # info: "first_seen_at" : now ,
        "processed_at": None,  # info: "processed_at" : None ,
        "broadcast_at": None,  # info: "broadcast_at" : None ,
        "cluster_id": "",  # info: "cluster_id" : "" ,
        "political": political,  # info: "political" : political ,
    }  # info: }


# ====================================================
# SECTION: function fresh
# What it does: True when the item is new enough to enter the broadcast queue.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fresh(story: dict, registry: dict) -> bool:  # info: def fresh
    published = parse_iso(story.get("published_at") or "")  # info: set published
    if published is None:  # info: if published is None :
        return True  # info: return True
    hours = float((registry["policy"].get("fetch") or {}).get("max_broadcast_age_hours") or 36)  # info: set hours
    return published >= utc_now() - timedelta(hours=hours)  # info: return published >= utc_now ( ) - timedelta ( hours = hours )


# ====================================================
# SECTION: function same_event
# What it does: True when two stories are the same event by URL, title, hash, or word overlap.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def same_event(story: dict, prior: dict, registry: dict) -> bool:  # info: def same_event
    if story["source_id"] == prior["source_id"]:  # info: if story [ "source_id" ] == prior [ "source_id" ] :
        return False  # info: return False
    if story.get("canonical_url") and story["canonical_url"] == prior.get("canonical_url"):  # info: if story . get ( "canonical_url" ) and story [ "canonical_url" ] == prior . get ( "canonical_url" ) :
        return True  # info: return True
    if story.get("content_hash") and story["content_hash"] == prior.get("content_hash"):  # info: if story . get ( "content_hash" ) and story [ "content_hash" ] == prior . get ( "content_hash" ) :
        return True  # info: return True
    if story.get("title_norm") and story["title_norm"] == prior.get("title_norm"):  # info: if story . get ( "title_norm" ) and story [ "title_norm" ] == prior . get ( "title_norm" ) :
        return True  # info: return True
    left = tokens(story.get("title") or "")  # info: set left
    right = tokens(prior.get("title") or "")  # info: set right
    if len(left) < 4 or len(right) < 4:  # info: if len ( left ) < 4 or len ( right ) < 4 :
        return False  # info: return False
    needed = float((registry["policy"].get("fetch") or {}).get("similarity") or 0.62)  # info: set needed
    return jaccard(left, right) >= needed  # info: return jaccard ( left , right ) >= needed
