# ==============================================================================
# FILE: Media/RadioRss/scripts/pipeline.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Poll feeds, cluster stories, write scripts, and hand one item toward the existing radio path."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import re  # info: import re
import subprocess  # info: import subprocess
from datetime import timedelta  # info: from datetime import timedelta
from pathlib import Path  # info: from pathlib import Path

from common import PACIFIC, ROOT, digest, iso, log_line, parse_iso, utc_now  # info: from common import PACIFIC , ROOT , digest , iso , log_line , parse_iso , utc_now
from fetch import fetch_url  # info: from fetch import fetch_url
from parse_feed import parse_document  # info: from parse_feed import parse_document
from registry import category_of, configured_on  # info: from registry import category_of , configured_on
from store import (  # info: from store import (
    connect,  # info: connect ,
    ensure_cluster,  # info: ensure_cluster ,
    feed_row,  # info: feed_row ,
    items_today,  # info: items_today ,
    recent_stories,  # info: recent_stories ,
    save_feed,  # info: save_feed ,
    upsert_story,  # info: upsert_story ,
    write_raw,  # info: write_raw ,
    write_story,  # info: write_story ,
)  # info: )
from stories import barred, fresh, normalize, same_event, sports, violent  # info: from stories import barred , fresh , normalize , same_event , sports , violent

WEIGHT = {"urgent": 4, "high": 3, "normal": 2, "low": 1}  # info: set WEIGHT
SENTENCE = re.compile(r"(?<=[.!?])\s+")  # info: set SENTENCE


# ====================================================
# SECTION: function _minutes
# What it does: Return the poll interval for one feed. A feed override wins over the priority default.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _minutes(feed: dict, policy: dict) -> int:  # info: def _minutes
    if feed.get("interval_minutes"):  # info: if feed . get ( "interval_minutes" ) :
        return int(feed["interval_minutes"])  # info: return int ( feed [ "interval_minutes" ] )
    table = (policy.get("fetch") or {}).get("intervals_minutes") or {}  # info: set table
    return int(table.get(feed.get("priority") or "medium", 30))  # info: return int ( table . get ( feed . get ( "priority" ) or "medium" , 30 ) )


# ====================================================
# SECTION: function _due
# What it does: Choose the configured feeds whose interval has elapsed. Highest priority goes first.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _due(registry: dict, conn, now) -> list[dict]:  # info: def _due
    chosen = []  # info: set chosen
    for feed in registry["feeds"]:  # info: for feed in registry [ "feeds" ]
        if not configured_on(feed):  # info: if not configured_on ( feed ) :
            continue  # info: continue
        state = feed_row(conn, feed["id"])  # info: set state
        if state and int(state.get("runtime_enabled") if state.get("runtime_enabled") is not None else 1) == 0:  # info: if state and int ( state . get ( "runtime_enabled" ) if state . get ( "runtime_enabled" ) is not None else 1 ) == 0 :
            continue  # info: continue
        last = parse_iso(state.get("last_poll_at") or "")  # info: set last
        if last and now < last + timedelta(minutes=_minutes(feed, registry["policy"])):  # info: if last and now < last + timedelta ( minutes = _minutes ( feed , registry [ "policy" ] ) ) :
            continue  # info: continue
        chosen.append(feed)  # info: chosen . append ( feed )
    chosen.sort(key=lambda feed: (-WEIGHT.get({"high": "high", "medium": "normal", "low": "low"}.get(feed["priority"], "normal"), 2), feed["id"]))  # info: chosen . sort ( key = lambda feed : ( - WEIGHT . get ( { "high" : "high" , "medium" : "normal" , "low" : "low" } . get ( feed [ "priority" ] , "normal" ) , 2 ) , feed [ "id" ] ) )
    budget = int((registry["policy"].get("fetch") or {}).get("max_feeds_per_run") or 6)  # info: set budget
    return chosen[:budget]  # info: return chosen [ : budget ]


# ====================================================
# SECTION: function _state
# What it does: Start a health row from the previous one so a failure keeps the last good cache headers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _state(feed_id: str, previous: dict) -> dict:  # info: def _state
    row = dict(previous)  # info: set row
    row["feed_id"] = feed_id  # info: row [ "feed_id" ] = feed_id
    row["runtime_enabled"] = int(previous.get("runtime_enabled") if previous.get("runtime_enabled") is not None else 1)  # info: row [ "runtime_enabled" ] = int ( previous . get ( "runtime_enabled" ) if previous . get ( "runtime_enabled" ) is not None else 1 )
    row["consecutive_failures"] = int(previous.get("consecutive_failures") or 0)  # info: row [ "consecutive_failures" ] = int ( previous . get ( "consecutive_failures" ) or 0 )
    return row  # info: return row


# ====================================================
# SECTION: function _fail
# What it does: Count a feed failure and disable it in runtime state after the configured limit. The YAML source stays.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fail(conn, feed: dict, previous: dict, registry: dict, error: str, status: int, latency: int) -> None:  # info: def _fail
    row = _state(feed["id"], previous)  # info: set row
    row["consecutive_failures"] = int(row.get("consecutive_failures") or 0) + 1  # info: row [ "consecutive_failures" ] = int ( row . get ( "consecutive_failures" ) or 0 ) + 1
    row["last_failure"] = iso(utc_now())  # info: row [ "last_failure" ] = iso ( utc_now ( ) )
    row["last_error"] = error[:300]  # info: row [ "last_error" ] = error [ : 300 ]
    row["http_status"] = status  # info: row [ "http_status" ] = status
    row["parse_status"] = "failed"  # info: row [ "parse_status" ] = "failed"
    row["latency_ms"] = latency  # info: row [ "latency_ms" ] = latency
    row["last_poll_at"] = iso(utc_now())  # info: row [ "last_poll_at" ] = iso ( utc_now ( ) )
    limit = int((registry["policy"].get("fetch") or {}).get("unhealthy_after_failures") or 5)  # info: set limit
    if row["consecutive_failures"] >= limit:  # info: if row [ "consecutive_failures" ] >= limit :
        row["runtime_enabled"] = 0  # info: row [ "runtime_enabled" ] = 0
        row["disable_reason"] = "feed_unhealthy"  # info: row [ "disable_reason" ] = "feed_unhealthy"
    save_feed(conn, row)  # info: save_feed ( conn , row )
    log_line(f"fail {feed['id']} {error}")  # info: log_line ( f"fail { feed [ 'id' ] } { error }" )


# ====================================================
# SECTION: function _cluster_for
# What it does: Attach a story to an existing multi-source cluster or open a new one.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cluster_for(conn, story: dict, registry: dict) -> str:  # info: def _cluster_for
    hours = float((registry["policy"].get("fetch") or {}).get("cluster_window_hours") or 48)  # info: set hours
    since = iso(utc_now() - timedelta(hours=hours))  # info: set since
    for prior in recent_stories(conn, since):  # info: for prior in recent_stories ( conn , since )
        if same_event(story, prior, registry):  # info: if same_event ( story , prior , registry ) :
            return prior.get("cluster_id") or ("c_" + prior["id"][:16])  # info: return prior . get ( "cluster_id" ) or ( "c_" + prior [ "id" ] [ : 16 ] )
    return "c_" + story["id"][:16]  # info: return "c_" + story [ "id" ] [ : 16 ]


# ====================================================
# SECTION: function _accept
# What it does: Store one normalized story and count whether it was new or a duplicate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _accept(conn, story: dict, registry: dict, root: Path) -> str:  # info: def _accept
    if not fresh(story, registry):  # info: if not fresh ( story , registry ) :
        story["status"] = "archived"  # info: story [ "status" ] = "archived"
    story["cluster_id"] = _cluster_for(conn, story, registry) if story["status"] == "new" else ""  # info: story [ "cluster_id" ] = _cluster_for ( conn , story , registry ) if story [ "status" ] == "new" else ""
    kind = upsert_story(conn, story)  # info: set kind
    if kind == "new":  # info: if kind == "new" :
        write_story(story, root)  # info: write_story ( story , root )
        if story["cluster_id"]:  # info: if story [ "cluster_id" ] :
            ensure_cluster(conn, story, story["cluster_id"])  # info: ensure_cluster ( conn , story , story [ "cluster_id" ] )
    return kind  # info: return kind


# ====================================================
# SECTION: function poll_feed
# What it does: Fetch and store one feed. Any error is recorded. It does not escape to the caller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poll_feed(registry: dict, conn, feed: dict, fetcher, root: Path) -> dict:  # info: def poll_feed
    previous = feed_row(conn, feed["id"])  # info: set previous
    try:  # info: try
        result = fetcher(feed["url"], registry["policy"], previous.get("etag") or "", previous.get("last_modified") or "")  # info: set result
    except Exception as exc:  # info: except Exception as exc
        _fail(conn, feed, previous, registry, type(exc).__name__, 0, 0)  # info: _fail ( conn , feed , previous , registry , type ( exc ) . __name__ , 0 , 0 )
        return {"feed": feed["id"], "ok": False}  # info: return { "feed" : feed [ "id" ] , "ok" : False }
    if result.get("skipped") == "robots":  # info: if result . get ( "skipped" ) == "robots" :
        row = _state(feed["id"], previous)  # info: set row
        row["parse_status"] = "robots"  # info: row [ "parse_status" ] = "robots"
        row["last_poll_at"] = iso(utc_now())  # info: row [ "last_poll_at" ] = iso ( utc_now ( ) )
        save_feed(conn, row)  # info: save_feed ( conn , row )
        log_line(f"robots {feed['id']}")  # info: log_line ( f"robots { feed [ 'id' ] }" )
        return {"feed": feed["id"], "ok": True, "skipped": "robots"}  # info: return { "feed" : feed [ "id" ] , "ok" : True , "skipped" : "robots" }
    if not result.get("ok"):  # info: if not result . get ( "ok" ) :
        _fail(conn, feed, previous, registry, result.get("error") or "fetch_failed", int(result.get("status") or 0), int(result.get("latency_ms") or 0))  # info: _fail ( conn , feed , previous , registry , result . get ( "error" ) or "fetch_failed" , int ( result . get ( "status" ) or 0 ) , int ( result . get ( "latency_ms" ) or 0 ) )
        return {"feed": feed["id"], "ok": False}  # info: return { "feed" : feed [ "id" ] , "ok" : False }
    if result.get("not_modified"):  # info: if result . get ( "not_modified" ) :
        row = _state(feed["id"], previous)  # info: set row
        row["etag"] = result.get("etag") or ""  # info: row [ "etag" ] = result . get ( "etag" ) or ""
        row["last_modified"] = result.get("modified") or ""  # info: row [ "last_modified" ] = result . get ( "modified" ) or ""
        row["last_success"] = iso(utc_now())  # info: row [ "last_success" ] = iso ( utc_now ( ) )
        row["consecutive_failures"] = 0  # info: row [ "consecutive_failures" ] = 0
        row["http_status"] = 304  # info: row [ "http_status" ] = 304
        row["parse_status"] = "not_modified"  # info: row [ "parse_status" ] = "not_modified"
        row["items_received"] = 0  # info: row [ "items_received" ] = 0
        row["latency_ms"] = result.get("latency_ms") or 0  # info: row [ "latency_ms" ] = result . get ( "latency_ms" ) or 0
        row["last_poll_at"] = iso(utc_now())  # info: row [ "last_poll_at" ] = iso ( utc_now ( ) )
        save_feed(conn, row)  # info: save_feed ( conn , row )
        return {"feed": feed["id"], "ok": True, "items": 0}  # info: return { "feed" : feed [ "id" ] , "ok" : True , "items" : 0 }
    try:  # info: try
        items = parse_document(result.get("body") or b"")  # info: set items
    except ValueError as exc:  # info: except ValueError as exc
        _fail(conn, feed, previous, registry, str(exc), int(result.get("status") or 0), int(result.get("latency_ms") or 0))  # info: _fail ( conn , feed , previous , registry , str ( exc ) , int ( result . get ( "status" ) or 0 ) , int ( result . get ( "latency_ms" ) or 0 ) )
        return {"feed": feed["id"], "ok": False}  # info: return { "feed" : feed [ "id" ] , "ok" : False }
    write_raw(feed, result.get("body") or b"", root)  # info: write_raw ( feed , result . get ( "body" ) or b"" , root )
    limit = int((registry["policy"].get("fetch") or {}).get("max_items_per_feed") or 20)  # info: set limit
    newest = ""  # info: set newest
    received = 0  # info: set received
    duplicates = 0  # info: set duplicates
    for item in items[:limit]:  # info: for item in items [ : limit ]
        received += 1  # info: set received
        story = normalize(feed, item, registry)  # info: set story
        if story is None:  # info: if story is None :
            continue  # info: continue
        if (story.get("published_at") or "") > newest:  # info: if ( story . get ( "published_at" ) or "" ) > newest :
            newest = story["published_at"]  # info: set newest
        if _accept(conn, story, registry, root) == "duplicate":  # info: if _accept ( conn , story , registry , root ) == "duplicate" :
            duplicates += 1  # info: set duplicates
    row = _state(feed["id"], previous)  # info: set row
    row["etag"] = result.get("etag") or ""  # info: row [ "etag" ] = result . get ( "etag" ) or ""
    row["last_modified"] = result.get("modified") or ""  # info: row [ "last_modified" ] = result . get ( "modified" ) or ""
    row["last_success"] = iso(utc_now())  # info: row [ "last_success" ] = iso ( utc_now ( ) )
    row["consecutive_failures"] = 0  # info: row [ "consecutive_failures" ] = 0
    row["last_error"] = ""  # info: row [ "last_error" ] = ""
    row["http_status"] = int(result.get("status") or 200)  # info: row [ "http_status" ] = int ( result . get ( "status" ) or 200 )
    row["parse_status"] = "ok"  # info: row [ "parse_status" ] = "ok"
    row["items_received"] = received  # info: row [ "items_received" ] = received
    row["duplicate_pct"] = round((duplicates / received) * 100, 1) if received else 0  # info: row [ "duplicate_pct" ] = round ( ( duplicates / received ) * 100 , 1 ) if received else 0
    row["latency_ms"] = result.get("latency_ms") or 0  # info: row [ "latency_ms" ] = result . get ( "latency_ms" ) or 0
    row["last_item_published"] = newest or previous.get("last_item_published") or ""  # info: row [ "last_item_published" ] = newest or previous . get ( "last_item_published" ) or ""
    row["last_poll_at"] = iso(utc_now())  # info: row [ "last_poll_at" ] = iso ( utc_now ( ) )
    row["runtime_enabled"] = 1  # info: row [ "runtime_enabled" ] = 1
    row["disable_reason"] = ""  # info: row [ "disable_reason" ] = ""
    save_feed(conn, row)  # info: save_feed ( conn , row )
    return {"feed": feed["id"], "ok": True, "items": received, "duplicates": duplicates}  # info: return { "feed" : feed [ "id" ] , "ok" : True , "items" : received , "duplicates" : duplicates }


# ====================================================
# SECTION: function poll
# What it does: Poll due feeds. One broken feed does not stop the others or the station.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def poll(registry: dict, conn=None, fetcher=None, root: Path | None = None, only: str = "") -> dict:  # info: def poll
    own = conn or connect(root)  # info: set own
    base = root or ROOT  # info: set base
    call = fetcher or fetch_url  # info: set call
    if only:  # info: if only :
        feeds = [feed for feed in registry["feeds"] if feed["id"] == only and configured_on(feed)]  # info: set feeds
    else:  # info: else
        feeds = _due(registry, own, utc_now())  # info: set feeds
    results = []  # info: set results
    for feed in feeds:  # info: for feed in feeds
        try:  # info: try
            results.append(poll_feed(registry, own, feed, call, base))  # info: results . append ( poll_feed ( registry , own , feed , call , base ) )
        except Exception as exc:  # info: except Exception as exc
            log_line(f"isolated {feed['id']} {type(exc).__name__}")  # info: log_line ( f"isolated { feed [ 'id' ] } { type ( exc ) . __name__ }" )
            results.append({"feed": feed["id"], "ok": False})  # info: results . append ( { "feed" : feed [ "id" ] , "ok" : False } )
    try:  # info: try
        composed = compose(registry, own, base)  # info: set composed
        write_health(registry, own, base)  # info: write_health ( registry , own , base )
        export_queue(own, base)  # info: export_queue ( own , base )
    except Exception as exc:  # info: except Exception as exc
        log_line(f"compose_failed {type(exc).__name__}")  # info: log_line ( f"compose_failed { type ( exc ) . __name__ }" )
        composed = []  # info: set composed
    return {"ok": True, "polled": results, "composed": composed}  # info: return { "ok" : True , "polled" : results , "composed" : composed }


# ====================================================
# SECTION: function _publisher
# What it does: Return the spoken publisher name from policy, then the feed provider.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _publisher(provider: str, policy: dict) -> str:  # info: def _publisher
    return str((policy.get("publishers") or {}).get(provider) or provider or "the publisher")  # info: return str ( ( policy . get ( "publishers" ) or { } ) . get ( provider ) or provider or "the publisher" )


# ====================================================
# SECTION: function speak_body
# What it does: Keep the summary and drop a sentence that repeats the headline.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def speak_body(title: str, summary: str, policy: dict) -> str:  # info: def speak_body
    body = _summary(summary, policy)  # info: set body
    title_key = (title or "").strip().lower().rstrip(".")  # info: set title_key
    kept = []  # info: set kept
    for sentence in body.split(". "):  # info: for sentence in body . split
        piece = sentence.strip()  # info: set piece
        key = piece.lower().rstrip(".")  # info: set key
        if title_key and (key == title_key or key.startswith(title_key) or (title_key.startswith(key) and len(key) > 24)):  # info: if sentence repeats the title
            continue  # info: continue
        if piece:  # info: if piece
            kept.append(piece if piece.endswith(".") else piece)  # info: kept . append
    return " ".join(kept)  # info: return " " . join ( kept )


# ====================================================
# SECTION: function _summary
# What it does: Keep the publisher summary and remove sentences that tell a listener how to vote.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _summary(text: str, policy: dict) -> str:  # info: def _summary
    blocked = [str(item).lower() for item in (policy.get("drop_sentence_patterns") or [])]  # info: set blocked
    kept = []  # info: set kept
    for sentence in SENTENCE.split(text or ""):  # info: for sentence in SENTENCE . split ( text or "" )
        low = sentence.lower()  # info: set low
        if any(phrase in low for phrase in blocked):  # info: if any ( phrase in low for phrase in blocked ) :
            continue  # info: continue
        kept.append(sentence.strip())  # info: kept . append ( sentence . strip ( ) )
    return " ".join(part for part in kept if part)[:700]  # info: return " " . join ( part for part in kept if part ) [ : 700 ]


# ====================================================
# SECTION: function _when
# What it does: Speak a publication date with a year digit so the voice gate can see a live fact.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _when(value: str) -> str:  # info: def _when
    parsed = parse_iso(value)  # info: set parsed
    if parsed is None:  # info: if parsed is None :
        return "the publication time was not listed"  # info: return "the publication time was not listed"
    return parsed.strftime("%B ") + str(parsed.day) + parsed.strftime(", %Y")  # info: return parsed . strftime ( "%B " ) + str ( parsed . day ) + parsed . strftime ( ", %Y" )


# ====================================================
# SECTION: function script_for
# What it does: Write an attributed script. The wording stays the publisher's account.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def script_for(cluster: dict, stories: list[dict], registry: dict) -> tuple[str, str]:  # info: def script_for
    policy = registry["policy"]  # info: set policy
    category = category_of(registry, cluster["category"])  # info: set category
    program = (policy.get("programs") or {}).get(category["program"]) or {}  # info: set program
    lead = category.get("lead") or program.get("lead") or "External brief."  # info: set lead
    lines = []  # info: set lines
    names = []  # info: set names
    for story in stories:  # info: for story in stories
        spoken = _publisher(story.get("provider") or "", policy)  # info: set spoken
        if spoken not in names:  # info: if spoken not in names :
            names.append(spoken)  # info: names . append ( spoken )
        body = speak_body(story.get("title") or "", story.get("summary") or "", policy)  # info: set body
        sentence = f"{spoken} reports that {story['title']}."  # info: set sentence
        if body:  # info: if body
            sentence = f"{sentence} {body}"  # info: set sentence
        lines.append(sentence)  # info: lines . append ( sentence )
    if len(names) > 1:  # info: if len ( names ) > 1 :
        opener = f"{lead} {' and '.join(names)} are reporting the same event."  # info: set opener
    else:  # info: else
        opener = lead  # info: set opener
    if stories:  # info: if stories
        opener = f"{opener} Published {_when(stories[0].get('published_at') or '')}."  # info: set opener
    speak = " ".join([opener, *lines])  # info: set speak
    if any(story.get("political") for story in stories) or cluster.get("political"):  # info: if any ( story . get ( "political" ) for story in stories ) or cluster . get ( "political" ) :
        speak += " The claims in this brief are the publisher's."  # info: set speak
    audit = [speak, "", "Sources:"]  # info: set audit
    for story in stories:  # info: for story in stories
        audit.append(f"- {story.get('provider')} | {story.get('title')} | {story.get('url')} | {story.get('published_at')} | {story.get('id')}")  # info: audit . append ( f"- { story . get ( 'provider' ) } | { story . get ( 'title' ) } | { story . get ( 'url' ) } | { story . get ( 'published_at' ) } | { story . get ( 'id' ) }" )
    return speak, "\n".join(audit) + "\n"  # info: return speak , "\n" . join ( audit ) + "\n"


# ====================================================
# SECTION: function compose
# What it does: Turn new clusters into queued scripts. Sports stories are left out. It does not speak and it does not call the broadcaster.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def compose(registry: dict, conn, root: Path | None = None) -> list[str]:  # info: def compose
    base = root or ROOT  # info: set base
    made = []  # info: set made
    clusters = conn.execute("SELECT * FROM clusters WHERE status='new'").fetchall()  # info: set clusters
    for cluster in clusters:  # info: for cluster in clusters
        stories = [dict(row) for row in conn.execute("SELECT * FROM stories WHERE cluster_id=? AND status='new' ORDER BY published_at", (cluster["id"],))]  # info: set stories
        kept = [row for row in stories if not sports({}, row, registry) and not violent({}, row, registry) and not barred({}, row, registry)]  # info: set kept
        dropped = [row for row in stories if sports({}, row, registry) or violent({}, row, registry) or barred({}, row, registry)]  # info: set dropped
        if dropped:  # info: if dropped :
            stamp = iso(utc_now())  # info: set stamp
            for row in dropped:  # info: for row in dropped
                conn.execute("UPDATE stories SET status='archived', processed_at=? WHERE id=?", (stamp, row["id"]))  # info: conn . execute ( "UPDATE stories SET status='archived', processed_at=? WHERE id=?" , ( stamp , row [ "id" ] ) )
        stories = kept  # info: set stories
        if not stories:  # info: if not stories :
            conn.execute("UPDATE clusters SET status='archived' WHERE id=? AND status='new'", (cluster["id"],))  # info: conn . execute ( "UPDATE clusters SET status='archived' WHERE id=? AND status='new'" , ( cluster [ "id" ] , ) )
            continue  # info: continue
        category = category_of(registry, cluster["category"])  # info: set category
        program_name = category["program"]  # info: set program_name
        program = (registry["policy"].get("programs") or {}).get(program_name) or {"report": "news_brief"}  # info: set program
        speak, audit = script_for(dict(cluster), stories, registry)  # info: speak , audit = script_for ( dict ( cluster ) , stories , registry )
        folder = base / "processed" / "scripts" / program["report"]  # info: set folder
        folder.mkdir(parents=True, exist_ok=True)  # info: folder . mkdir ( parents = True , exist_ok = True )
        speak_path = folder / f"{cluster['id']}.speak.txt"  # info: set speak_path
        audit_path = folder / f"{cluster['id']}.txt"  # info: set audit_path
        speak_path.write_text(speak + "\n", encoding="utf-8")  # info: speak_path . write_text ( speak + "\n" , encoding = "utf-8" )
        audit_path.write_text(audit, encoding="utf-8")  # info: audit_path . write_text ( audit , encoding = "utf-8" )
        now = iso(utc_now())  # info: set now
        conn.execute(  # info: conn . execute (
            "INSERT OR IGNORE INTO queue (id, cluster_id, program, report, script_path, speak_path, priority, status, created_at, handed_at, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?)",  # info: "INSERT OR IGNORE INTO queue (id, cluster_id, program, report, script_path, speak_path, priority, status, created_at, handed_at, detail) VALUES (?,?,?,?,?,?,?,?,?,?,?)" ,
            (digest(cluster["id"], n=16), cluster["id"], program_name, program["report"], str(audit_path), str(speak_path), cluster["priority"], "queued", now, "", ""),  # info: ( digest ( cluster [ "id" ] , n = 16 ) , cluster [ "id" ] , program_name , program [ "report" ] , str ( audit_path ) , str ( speak_path ) , cluster [ "priority" ] , "queued" , now , "" , "" ) ,
        )  # info: )
        conn.execute("UPDATE stories SET status='processed', processed_at=? WHERE cluster_id=? AND status='new'", (now, cluster["id"]))  # info: conn . execute ( "UPDATE stories SET status='processed', processed_at=? WHERE cluster_id=? AND status='new'" , ( now , cluster [ "id" ] ) )
        conn.execute("UPDATE clusters SET status='processed' WHERE id=?", (cluster["id"],))  # info: conn . execute ( "UPDATE clusters SET status='processed' WHERE id=?" , ( cluster [ "id" ] , ) )
        made.append(cluster["id"])  # info: made . append ( cluster [ "id" ] )
    conn.commit()  # info: conn . commit ( )
    return made  # info: return made


# ====================================================
# SECTION: function _ordered
# What it does: Order the queue so urgent and multi-source world, chips, weather, and politics items come before offbeat briefs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ordered(registry: dict, conn) -> list[dict]:  # info: def _ordered
    rows = []  # info: set rows
    for item in conn.execute("SELECT * FROM queue WHERE status='queued'").fetchall():  # info: for item in conn . execute ( "SELECT * FROM queue WHERE status='queued'" ) . fetchall ( )
        cluster = conn.execute("SELECT * FROM clusters WHERE id=?", (item["cluster_id"],)).fetchone()  # info: set cluster
        if cluster is None:  # info: if cluster is None :
            continue  # info: continue
        category = registry["categories"].get(cluster["category"]) or {"rank": 50}  # info: set category
        multi = 0  # info: set multi
        boost = {"global_news", "chips", "mainland_weather", "mainland_politics", "artificial_intelligence"}  # info: set boost
        if cluster["category"] in boost and int(cluster["source_count"] or 0) >= 2:  # info: if cluster [ "category" ] in boost and int ( cluster [ "source_count" ] or 0 ) >= 2 :
            multi = 1  # info: set multi
        rows.append((WEIGHT.get(item["priority"], 2), multi, -int(category.get("rank") or 50), item["created_at"], dict(item)))  # info: rows . append ( ( WEIGHT . get ( item [ "priority" ] , 2 ) , multi , - int ( category . get ( "rank" ) or 50 ) , item [ "created_at" ] , dict ( item ) ) )
    rows.sort(key=lambda row: (row[0], row[1], row[2], row[3]), reverse=True)  # info: rows . sort ( key = lambda row : ( row [ 0 ] , row [ 1 ] , row [ 2 ] , row [ 3 ] ) , reverse = True )
    return [row[4] for row in rows]  # info: return [ row [ 4 ] for row in rows ]


# ====================================================
# SECTION: function export_queue
# What it does: Write the persistent queue the existing broadcaster can read later. This file does not start playback.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def export_queue(conn, root: Path | None = None) -> Path:  # info: def export_queue
    base = root or ROOT  # info: set base
    items = []  # info: set items
    for row in conn.execute("SELECT * FROM queue WHERE status='queued' ORDER BY created_at").fetchall():  # info: for row in conn . execute ( "SELECT * FROM queue WHERE status='queued' ORDER BY created_at" ) . fetchall ( )
        sources = []  # info: set sources
        for story in conn.execute("SELECT provider, title, url, published_at, source_name FROM stories WHERE cluster_id=?", (row["cluster_id"],)):  # info: for story in conn . execute ( "SELECT provider, title, url, published_at, source_name FROM stories WHERE cluster_id=?" , ( row [ "cluster_id" ] , ) )
            sources.append({"publisher": story["provider"], "source": story["source_name"], "title": story["title"], "url": story["url"], "published_at": story["published_at"]})  # info: sources . append ( { "publisher" : story [ "provider" ] , "source" : story [ "source_name" ] , "title" : story [ "title" ] , "url" : story [ "url" ] , "published_at" : story [ "published_at" ] } )
        items.append({"id": row["id"], "cluster_id": row["cluster_id"], "program": row["program"], "report": row["report"], "priority": row["priority"], "script": row["script_path"], "speak": row["speak_path"], "sources": sources})  # info: items . append ( { "id" : row [ "id" ] , "cluster_id" : row [ "cluster_id" ] , "program" : row [ "program" ] , "report" : row [ "report" ] , "priority" : row [ "priority" ] , "script" : row [ "script_path" ] , "speak" : row [ "speak_path" ] , "sources" : sources } )
    path = base / "queue.json"  # info: set path
    path.write_text(json.dumps({"ok": True, "items": items}, indent=2) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps ( { "ok" : True , "items" : items } , indent = 2 ) + "\n" , encoding = "utf-8" )
    return path  # info: return path


# ====================================================
# SECTION: function _speak
# What it does: Ask the existing voice renderer and radio_push for one report. A failure stays in the queue.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _speak(report: str, speak_path: str, voice: str) -> dict:  # info: def _speak
    script = PACIFIC / "Media" / "Voice" / "scripts" / "voice-render.sh"  # info: set script
    cmd = ["bash", str(script), "stitch", "--report", report, "--kind", "rss", "--text-file", speak_path, "--voice", voice]  # info: set cmd
    try:  # info: try
        ran = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # info: set ran
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired ) as exc
        return {"ok": False, "detail": type(exc).__name__}  # info: return { "ok" : False , "detail" : type ( exc ) . __name__ }
    if ran.returncode != 0:  # info: if ran . returncode != 0 :
        return {"ok": False, "detail": "speak_failed", "code": ran.returncode}  # info: return { "ok" : False , "detail" : "speak_failed" , "code" : ran . returncode }
    import sys  # info: import sys
    voice_dir = str(PACIFIC / "Media" / "Voice" / "scripts")  # info: set voice_dir
    if voice_dir not in sys.path:  # info: if voice_dir not in sys . path :
        sys.path.insert(0, voice_dir)  # info: sys . path . insert ( 0 , voice_dir )
    import radio_push  # info: import radio_push
    pushed = radio_push.push_report(report)  # info: set pushed
    return pushed if isinstance(pushed, dict) else {"ok": False, "detail": "push_failed"}  # info: return pushed if isinstance ( pushed , dict ) else { "ok" : False , "detail" : "push_failed" }


# ====================================================
# SECTION: function handoff
# What it does: Take the next queued brief. Dry-run leaves it queued. Speak uses the existing voice and radio push.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def handoff(registry: dict, conn, speak: bool = False, root: Path | None = None) -> dict:  # info: def handoff
    base = root or ROOT  # info: set base
    items = _ordered(registry, conn)  # info: set items
    export_queue(conn, base)  # info: export_queue ( conn , base )
    if not items:  # info: if not items :
        return {"ok": True, "detail": "empty"}  # info: return { "ok" : True , "detail" : "empty" }
    item = items[0]  # info: set item
    if not speak:  # info: if not speak :
        return {"ok": True, "detail": "dry_run", "id": item["id"], "report": item["report"], "program": item["program"], "speak": item["speak_path"]}  # info: return { "ok" : True , "detail" : "dry_run" , "id" : item [ "id" ] , "report" : item [ "report" ] , "program" : item [ "program" ] , "speak" : item [ "speak_path" ] }
    program = (registry["policy"].get("programs") or {}).get(item["program"]) or {}  # info: set program
    result = _speak(item["report"], item["speak_path"], str(program.get("voice") or "af_heart"))  # info: set result
    now = iso(utc_now())  # info: set now
    if not result.get("ok"):  # info: if not result . get ( "ok" ) :
        conn.execute("UPDATE queue SET detail=? WHERE id=?", (str(result.get("detail") or "speak_failed")[:200], item["id"]))  # info: conn . execute ( "UPDATE queue SET detail=? WHERE id=?" , ( str ( result . get ( "detail" ) or "speak_failed" ) [ : 200 ] , item [ "id" ] ) )
        conn.commit()  # info: conn . commit ( )
        log_line(f"speak_failed {item['id']} {result.get('detail')}")  # info: log_line ( f"speak_failed { item [ 'id' ] } { result . get ( 'detail' ) }" )
        return {"ok": True, "detail": "speak_failed", "id": item["id"]}  # info: return { "ok" : True , "detail" : "speak_failed" , "id" : item [ "id" ] }
    conn.execute("UPDATE queue SET status='broadcast', handed_at=?, detail='radio_push' WHERE id=?", (now, item["id"]))  # info: conn . execute ( "UPDATE queue SET status='broadcast', handed_at=?, detail='radio_push' WHERE id=?" , ( now , item [ "id" ] ) )
    conn.execute("UPDATE stories SET status='broadcast', broadcast_at=? WHERE cluster_id=?", (now, item["cluster_id"]))  # info: conn . execute ( "UPDATE stories SET status='broadcast', broadcast_at=? WHERE cluster_id=?" , ( now , item [ "cluster_id" ] ) )
    conn.execute("UPDATE clusters SET status='broadcast' WHERE id=?", (item["cluster_id"],))  # info: conn . execute ( "UPDATE clusters SET status='broadcast' WHERE id=?" , ( item [ "cluster_id" ] , ) )
    conn.commit()  # info: conn . commit ( )
    export_queue(conn, base)  # info: export_queue ( conn , base )
    return {"ok": True, "detail": "broadcast", "id": item["id"], "report": item["report"]}  # info: return { "ok" : True , "detail" : "broadcast" , "id" : item [ "id" ] , "report" : item [ "report" ] }


# ====================================================
# SECTION: function _label
# What it does: Name one feed's health for the operational board.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _label(feed: dict, state: dict) -> str:  # info: def _label
    if feed.get("origin") == "unavailable" or not feed.get("url"):  # info: if feed . get ( "origin" ) == "unavailable" or not feed . get ( "url" ) :
        return "UNAVAILABLE"  # info: return "UNAVAILABLE"
    if feed.get("origin") == "native" or not feed.get("enabled"):  # info: if feed . get ( "origin" ) == "native" or not feed . get ( "enabled" ) :
        return "DISABLED"  # info: return "DISABLED"
    if state and int(state.get("runtime_enabled") if state.get("runtime_enabled") is not None else 1) == 0:  # info: if state and int ( state . get ( "runtime_enabled" ) if state . get ( "runtime_enabled" ) is not None else 1 ) == 0 :
        return "UNHEALTHY"  # info: return "UNHEALTHY"
    if not state or not state.get("last_poll_at"):  # info: if not state or not state . get ( "last_poll_at" ) :
        return "UNKNOWN"  # info: return "UNKNOWN"
    if int(state.get("consecutive_failures") or 0) > 0:  # info: if int ( state . get ( "consecutive_failures" ) or 0 ) > 0 :
        return "DEGRADED"  # info: return "DEGRADED"
    return "HEALTHY"  # info: return "HEALTHY"


# ====================================================
# SECTION: function health_report
# What it does: Build the RSS FEED HEALTH board from the registry and the last poll.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def health_report(registry: dict, conn) -> dict:  # info: def health_report
    day = iso(utc_now() - timedelta(days=1))  # info: set day
    rows = []  # info: set rows
    for feed in registry["feeds"]:  # info: for feed in registry [ "feeds" ]
        state = feed_row(conn, feed["id"])  # info: set state
        published = parse_iso(state.get("last_item_published") or "")  # info: set published
        age = ""  # info: set age
        if published is not None:  # info: if published is not None :
            age = str(int((utc_now() - published).total_seconds()))  # info: set age
        rows.append({  # info: rows . append ( {
            "id": feed["id"],  # info: "id" : feed [ "id" ] ,
            "name": feed["name"],  # info: "name" : feed [ "name" ] ,
            "provider": feed.get("provider") or "",  # info: "provider" : feed . get ( "provider" ) or "" ,
            "category": feed["category"],  # info: "category" : feed [ "category" ] ,
            "status": _label(feed, state),  # info: "status" : _label ( feed , state ) ,
            "reason": state.get("disable_reason") or feed.get("note") or "",  # info: "reason" : state . get ( "disable_reason" ) or feed . get ( "note" ) or "" ,
            "last_success": state.get("last_success") or "",  # info: "last_success" : state . get ( "last_success" ) or "" ,
            "last_failure": state.get("last_failure") or "",  # info: "last_failure" : state . get ( "last_failure" ) or "" ,
            "consecutive_failures": int(state.get("consecutive_failures") or 0),  # info: "consecutive_failures" : int ( state . get ( "consecutive_failures" ) or 0 ) ,
            "http_status": state.get("http_status") or "",  # info: "http_status" : state . get ( "http_status" ) or "" ,
            "parse_status": state.get("parse_status") or "",  # info: "parse_status" : state . get ( "parse_status" ) or "" ,
            "items_received": int(state.get("items_received") or 0),  # info: "items_received" : int ( state . get ( "items_received" ) or 0 ) ,
            "items_day": items_today(conn, feed["id"], day),  # info: "items_day" : items_today ( conn , feed [ "id" ] , day ) ,
            "latency_ms": state.get("latency_ms") or 0,  # info: "latency_ms" : state . get ( "latency_ms" ) or 0 ,
            "duplicate_pct": state.get("duplicate_pct") or 0,  # info: "duplicate_pct" : state . get ( "duplicate_pct" ) or 0 ,
            "last_item_age_sec": age,  # info: "last_item_age_sec" : age ,
        })  # info: } )
    return {"title": "RSS FEED HEALTH", "feeds": rows}  # info: return { "title" : "RSS FEED HEALTH" , "feeds" : rows }


# ====================================================
# SECTION: function health_text
# What it does: Render the health board as plain text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def health_text(report: dict) -> str:  # info: def health_text
    lines = ["RSS FEED HEALTH", ""]  # info: set lines
    for row in report["feeds"]:  # info: for row in report [ "feeds" ]
        mark = "●" if row["status"] == "HEALTHY" else "○"  # info: set mark
        lines.append(f"{row['name'][:28]:<28} {mark} {row['status']}")  # info: lines . append ( f"{ row [ 'name' ] [ : 28 ] :<28 } { mark } { row [ 'status' ] }" )
    return "\n".join(lines) + "\n"  # info: return "\n" . join ( lines ) + "\n"


# ====================================================
# SECTION: function write_health
# What it does: Store the health board under the RSS data root for operational monitoring.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_health(registry: dict, conn, root: Path | None = None) -> dict:  # info: def write_health
    base = root or ROOT  # info: set base
    report = health_report(registry, conn)  # info: set report
    base.mkdir(parents=True, exist_ok=True)  # info: base . mkdir ( parents = True , exist_ok = True )
    (base / "health.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")  # info: ( base / "health.json" ) . write_text ( json . dumps ( report , indent = 2 ) + "\n" , encoding = "utf-8" )
    (base / "health.txt").write_text(health_text(report), encoding="utf-8")  # info: ( base / "health.txt" ) . write_text ( health_text ( report ) , encoding = "utf-8" )
    return report  # info: return report


# ====================================================
# SECTION: function trace
# What it does: Show the publisher, URL, script, and cluster for one stored story.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def trace(conn, story_id: str) -> dict:  # info: def trace
    story = conn.execute("SELECT * FROM stories WHERE id=?", (story_id,)).fetchone()  # info: set story
    if story is None:  # info: if story is None :
        return {"ok": False, "detail": "missing"}  # info: return { "ok" : False , "detail" : "missing" }
    cluster = conn.execute("SELECT * FROM clusters WHERE id=?", (story["cluster_id"],)).fetchone()  # info: set cluster
    queued = conn.execute("SELECT * FROM queue WHERE cluster_id=?", (story["cluster_id"],)).fetchone()  # info: set queued
    sources = [dict(row) for row in conn.execute("SELECT source_name, provider, title, url, published_at FROM stories WHERE cluster_id=?", (story["cluster_id"],))]  # info: set sources
    return {"ok": True, "story": dict(story), "cluster": dict(cluster) if cluster else {}, "queue": dict(queued) if queued else {}, "sources": sources}  # info: return { "ok" : True , "story" : dict ( story ) , "cluster" : dict ( cluster ) if cluster else { } , "queue" : dict ( queued ) if queued else { } , "sources" : sources }


# ====================================================
# SECTION: function set_runtime
# What it does: Turn a feed back on or mark it unhealthy without deleting it from the registry.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_runtime(conn, feed_id: str, enabled: bool) -> dict:  # info: def set_runtime
    previous = feed_row(conn, feed_id)  # info: set previous
    row = _state(feed_id, previous)  # info: set row
    row["runtime_enabled"] = 1 if enabled else 0  # info: row [ "runtime_enabled" ] = 1 if enabled else 0
    row["disable_reason"] = "" if enabled else "feed_unhealthy"  # info: row [ "disable_reason" ] = "" if enabled else "feed_unhealthy"
    row["consecutive_failures"] = 0 if enabled else int(row.get("consecutive_failures") or 0)  # info: row [ "consecutive_failures" ] = 0 if enabled else int ( row . get ( "consecutive_failures" ) or 0 )
    row["last_poll_at"] = previous.get("last_poll_at") or ""  # info: row [ "last_poll_at" ] = previous . get ( "last_poll_at" ) or ""
    save_feed(conn, row)  # info: save_feed ( conn , row )
    return {"ok": True, "feed": feed_id, "runtime_enabled": row["runtime_enabled"]}  # info: return { "ok" : True , "feed" : feed_id , "runtime_enabled" : row [ "runtime_enabled" ] }
