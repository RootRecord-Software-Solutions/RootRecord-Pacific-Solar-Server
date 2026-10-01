# ==============================================================================
# FILE: Media/RadioRss/scripts/store.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""SQLite index plus raw, normalized, and processed files for RSS stories."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import sqlite3  # info: import sqlite3
from pathlib import Path  # info: from pathlib import Path

from common import ROOT, iso, provider_slug, utc_now  # info: from common import ROOT , iso , provider_slug , utc_now

SCHEMA = """
CREATE TABLE IF NOT EXISTS feed_state (
  feed_id TEXT PRIMARY KEY,
  etag TEXT,
  last_modified TEXT,
  last_success TEXT,
  last_failure TEXT,
  last_error TEXT,
  consecutive_failures INTEGER DEFAULT 0,
  http_status INTEGER,
  parse_status TEXT,
  items_received INTEGER DEFAULT 0,
  latency_ms REAL DEFAULT 0,
  duplicate_pct REAL DEFAULT 0,
  last_item_published TEXT,
  runtime_enabled INTEGER DEFAULT 1,
  disable_reason TEXT,
  last_poll_at TEXT
);
CREATE TABLE IF NOT EXISTS stories (
  id TEXT PRIMARY KEY,
  source_id TEXT,
  source_name TEXT,
  provider TEXT,
  category TEXT,
  title TEXT,
  summary TEXT,
  url TEXT,
  canonical_url TEXT,
  published_at TEXT,
  updated_at TEXT,
  author TEXT,
  guid TEXT,
  content_hash TEXT,
  title_norm TEXT,
  priority TEXT,
  status TEXT,
  first_seen_at TEXT,
  processed_at TEXT,
  broadcast_at TEXT,
  cluster_id TEXT,
  political INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS clusters (
  id TEXT PRIMARY KEY,
  title TEXT,
  category TEXT,
  priority TEXT,
  status TEXT,
  created_at TEXT,
  source_count INTEGER DEFAULT 1,
  political INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS queue (
  id TEXT PRIMARY KEY,
  cluster_id TEXT UNIQUE,
  program TEXT,
  report TEXT,
  script_path TEXT,
  speak_path TEXT,
  priority TEXT,
  status TEXT,
  created_at TEXT,
  handed_at TEXT,
  detail TEXT
);
"""  # info: set SCHEMA


# ====================================================
# SECTION: function connect
# What it does: Open the RSS index and create the storage folders. Does not delete a source.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connect(root: Path | None = None) -> sqlite3.Connection:  # info: def connect
    base = root or ROOT  # info: set base
    base.mkdir(parents=True, exist_ok=True)  # info: base . mkdir ( parents = True , exist_ok = True )
    for name in ("raw", "normalized", "processed"):  # info: for name in ( "raw" , "normalized" , "processed" )
        (base / name).mkdir(parents=True, exist_ok=True)  # info: ( base / name ) . mkdir ( parents = True , exist_ok = True )
    conn = sqlite3.connect(base / "stories.sqlite")  # info: set conn
    conn.row_factory = sqlite3.Row  # info: conn . row_factory = sqlite3 . Row
    conn.executescript(SCHEMA)  # info: conn . executescript ( SCHEMA )
    return conn  # info: return conn


# ====================================================
# SECTION: function feed_row
# What it does: Return the saved health row for one feed, or an empty dict.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def feed_row(conn: sqlite3.Connection, feed_id: str) -> dict:  # info: def feed_row
    row = conn.execute("SELECT * FROM feed_state WHERE feed_id=?", (feed_id,)).fetchone()  # info: set row
    return dict(row) if row else {}  # info: return dict ( row ) if row else { }


# ====================================================
# SECTION: function save_feed
# What it does: Replace the health row for one feed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def save_feed(conn: sqlite3.Connection, row: dict) -> None:  # info: def save_feed
    columns = [  # info: set columns
        "feed_id", "etag", "last_modified", "last_success", "last_failure", "last_error",  # info: "feed_id" , "etag" , "last_modified" , "last_success" , "last_failure" , "last_error" ,
        "consecutive_failures", "http_status", "parse_status", "items_received", "latency_ms",  # info: "consecutive_failures" , "http_status" , "parse_status" , "items_received" , "latency_ms" ,
        "duplicate_pct", "last_item_published", "runtime_enabled", "disable_reason", "last_poll_at",  # info: "duplicate_pct" , "last_item_published" , "runtime_enabled" , "disable_reason" , "last_poll_at" ,
    ]  # info: ]
    values = [row.get(name) for name in columns]  # info: set values
    conn.execute(  # info: conn . execute (
        f"INSERT OR REPLACE INTO feed_state ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",  # info: f"INSERT OR REPLACE INTO feed_state ({ ','.join ( columns ) }) VALUES ({ ','.join ( '?' for _ in columns ) })" ,
        values,  # info: values ,
    )  # info: )
    conn.commit()  # info: conn . commit ( )


# ====================================================
# SECTION: function write_raw
# What it does: Keep the newest raw documents for one feed and return the path just written.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_raw(feed: dict, body: bytes, root: Path | None = None, keep: int = 5) -> Path:  # info: def write_raw
    base = (root or ROOT) / "raw" / provider_slug(feed.get("provider") or "") / feed["id"]  # info: set base
    base.mkdir(parents=True, exist_ok=True)  # info: base . mkdir ( parents = True , exist_ok = True )
    stamp = iso(utc_now()).replace(":", "").replace("-", "")  # info: set stamp
    path = base / f"{stamp}.xml"  # info: set path
    path.write_bytes(body)  # info: path . write_bytes ( body )
    older = sorted(base.glob("*.xml"))  # info: set older
    for stale in older[:-keep]:  # info: for stale in older [ : - keep ]
        stale.unlink(missing_ok=True)  # info: stale . unlink ( missing_ok = True )
    return path  # info: return path


# ====================================================
# SECTION: function write_story
# What it does: Write one normalized story JSON under its category.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_story(story: dict, root: Path | None = None) -> Path:  # info: def write_story
    folder = (root or ROOT) / "normalized" / story["category"]  # info: set folder
    folder.mkdir(parents=True, exist_ok=True)  # info: folder . mkdir ( parents = True , exist_ok = True )
    path = folder / f"{story['id']}.json"  # info: set path
    path.write_text(json.dumps(story, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")  # info: path . write_text ( json . dumps ( story , indent = 2 , ensure_ascii = False ) + "\n" , encoding = "utf-8" )
    return path  # info: return path


# ====================================================
# SECTION: function upsert_story
# What it does: Insert a new story or refresh one already stored. Returns new or duplicate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def upsert_story(conn: sqlite3.Connection, story: dict) -> str:  # info: def upsert_story
    existing = conn.execute("SELECT id, cluster_id, status FROM stories WHERE id=?", (story["id"],)).fetchone()  # info: set existing
    if existing is None and story.get("guid"):  # info: if existing is None and story . get ( "guid" ) :
        existing = conn.execute(  # info: set existing
            "SELECT id, cluster_id, status FROM stories WHERE source_id=? AND guid=?",  # info: "SELECT id, cluster_id, status FROM stories WHERE source_id=? AND guid=?" ,
            (story["source_id"], story["guid"]),  # info: ( story [ "source_id" ] , story [ "guid" ] ) ,
        ).fetchone()  # info: ) . fetchone ( )
    if existing is None and story.get("canonical_url"):  # info: if existing is None and story . get ( "canonical_url" ) :
        existing = conn.execute(  # info: set existing
            "SELECT id, cluster_id, status FROM stories WHERE source_id=? AND canonical_url=?",  # info: "SELECT id, cluster_id, status FROM stories WHERE source_id=? AND canonical_url=?" ,
            (story["source_id"], story["canonical_url"]),  # info: ( story [ "source_id" ] , story [ "canonical_url" ] ) ,
        ).fetchone()  # info: ) . fetchone ( )
    if existing is None and story.get("title_norm"):  # info: if existing is None and story . get ( "title_norm" ) :
        existing = conn.execute(  # info: set existing
            "SELECT id, cluster_id, status FROM stories WHERE source_id=? AND title_norm=?",  # info: "SELECT id, cluster_id, status FROM stories WHERE source_id=? AND title_norm=?" ,
            (story["source_id"], story["title_norm"]),  # info: ( story [ "source_id" ] , story [ "title_norm" ] ) ,
        ).fetchone()  # info: ) . fetchone ( )
    if existing is not None:  # info: if existing is not None :
        conn.execute(  # info: conn . execute (
            "UPDATE stories SET updated_at=?, summary=?, title=? WHERE id=?",  # info: "UPDATE stories SET updated_at=?, summary=?, title=? WHERE id=?" ,
            (story.get("updated_at") or "", story.get("summary") or "", story.get("title") or "", existing["id"]),  # info: ( story . get ( "updated_at" ) or "" , story . get ( "summary" ) or "" , story . get ( "title" ) or "" , existing [ "id" ] ) ,
        )  # info: )
        conn.commit()  # info: conn . commit ( )
        return "duplicate"  # info: return "duplicate"
    columns = [  # info: set columns
        "id", "source_id", "source_name", "provider", "category", "title", "summary", "url",  # info: "id" , "source_id" , "source_name" , "provider" , "category" , "title" , "summary" , "url" ,
        "canonical_url", "published_at", "updated_at", "author", "guid", "content_hash", "title_norm",  # info: "canonical_url" , "published_at" , "updated_at" , "author" , "guid" , "content_hash" , "title_norm" ,
        "priority", "status", "first_seen_at", "processed_at", "broadcast_at", "cluster_id", "political",  # info: "priority" , "status" , "first_seen_at" , "processed_at" , "broadcast_at" , "cluster_id" , "political" ,
    ]  # info: ]
    conn.execute(  # info: conn . execute (
        f"INSERT INTO stories ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",  # info: f"INSERT INTO stories ({ ','.join ( columns ) }) VALUES ({ ','.join ( '?' for _ in columns ) })" ,
        [story.get(name) for name in columns],  # info: [ story . get ( name ) for name in columns ] ,
    )  # info: )
    conn.commit()  # info: conn . commit ( )
    return "new"  # info: return "new"


# ====================================================
# SECTION: function recent_stories
# What it does: Return recent stories used to cluster the same event across publishers.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recent_stories(conn: sqlite3.Connection, since: str, limit: int = 300) -> list[dict]:  # info: def recent_stories
    rows = conn.execute(  # info: set rows
        "SELECT * FROM stories WHERE first_seen_at>=? ORDER BY first_seen_at DESC LIMIT ?",  # info: "SELECT * FROM stories WHERE first_seen_at>=? ORDER BY first_seen_at DESC LIMIT ?" ,
        (since, limit),  # info: ( since , limit ) ,
    ).fetchall()  # info: ) . fetchall ( )
    return [dict(row) for row in rows]  # info: return [ dict ( row ) for row in rows ]


# ====================================================
# SECTION: function ensure_cluster
# What it does: Create a cluster or attach a story to one that already exists.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ensure_cluster(conn: sqlite3.Connection, story: dict, cluster_id: str) -> None:  # info: def ensure_cluster
    row = conn.execute("SELECT id, priority, source_count FROM clusters WHERE id=?", (cluster_id,)).fetchone()  # info: set row
    if row is None:  # info: if row is None :
        conn.execute(  # info: conn . execute (
            "INSERT INTO clusters (id, title, category, priority, status, created_at, source_count, political) VALUES (?,?,?,?,?,?,?,?)",  # info: "INSERT INTO clusters (id, title, category, priority, status, created_at, source_count, political) VALUES (?,?,?,?,?,?,?,?)" ,
            (cluster_id, story["title"], story["category"], story["priority"], "new", story["first_seen_at"], 1, story.get("political") or 0),  # info: ( cluster_id , story [ "title" ] , story [ "category" ] , story [ "priority" ] , "new" , story [ "first_seen_at" ] , 1 , story . get ( "political" ) or 0 ) ,
        )  # info: )
    else:  # info: else
        count = conn.execute("SELECT COUNT(DISTINCT source_id) FROM stories WHERE cluster_id=?", (cluster_id,)).fetchone()[0]  # info: set count
        rank = {"low": 1, "normal": 2, "high": 3, "urgent": 4}  # info: set rank
        priority = story["priority"] if rank.get(story["priority"], 0) > rank.get(row["priority"], 0) else row["priority"]  # info: set priority
        conn.execute(  # info: conn . execute (
            "UPDATE clusters SET source_count=?, priority=?, political=MAX(political, ?) WHERE id=?",  # info: "UPDATE clusters SET source_count=?, priority=?, political=MAX(political, ?) WHERE id=?" ,
            (count, priority, story.get("political") or 0, cluster_id),  # info: ( count , priority , story . get ( "political" ) or 0 , cluster_id ) ,
        )  # info: )
    conn.commit()  # info: conn . commit ( )


# ====================================================
# SECTION: function items_today
# What it does: Count stories stored for one feed in the last day.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def items_today(conn: sqlite3.Connection, feed_id: str, since: str) -> int:  # info: def items_today
    row = conn.execute(  # info: set row
        "SELECT COUNT(*) FROM stories WHERE source_id=? AND first_seen_at>=?",  # info: "SELECT COUNT(*) FROM stories WHERE source_id=? AND first_seen_at>=?" ,
        (feed_id, since),  # info: ( feed_id , since ) ,
    ).fetchone()  # info: ) . fetchone ( )
    return int(row[0])  # info: return int ( row [ 0 ] )
