# ==============================================================================
# FILE: Media/RadioRss/scripts/test_rss_radio.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Registry, parse, cluster, overlap, and failure tests for the RSS layer. No live publishers."""
from __future__ import annotations  # info: from __future__ import annotations

import shutil  # info: import shutil
import sys  # info: import sys
import tempfile  # info: import tempfile
import threading  # info: import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer  # info: from http . server import BaseHTTPRequestHandler , ThreadingHTTPServer
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 , str ( HERE ) )

from parse_feed import parse_document  # info: from parse_feed import parse_document
from pipeline import handoff, health_report, poll, trace  # info: from pipeline import handoff , health_report , poll , trace
from registry import load_registry  # info: from registry import load_registry
from store import connect, feed_row  # info: from store import connect , feed_row

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Example</title>
<item><title>{title}</title><link>{link}</link><guid>{guid}</guid>
<pubDate>Wed, 01 Oct 2026 18:00:00 GMT</pubDate>
<description>{summary}</description></item>
</channel></rss>
"""  # info: set RSS
ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Atom</title>
<entry><title>Kernel release 7.2</title><id>urn:kernel:7.2</id>
<link href="https://example.com/kernel-7-2"/><updated>2026-10-01T18:00:00Z</updated>
<summary>A kernel release note.</summary></entry></feed>
"""  # info: set ATOM


# ====================================================
# SECTION: function _feed
# What it does: Build one test feed row.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _feed(feed_id: str, url: str, **extra) -> dict:  # info: def _feed
    row = {  # info: set row
        "id": feed_id, "name": feed_id, "provider": extra.get("provider", "NASA"), "category": extra.get("category", "space"),  # info: "id" : feed_id , "name" : feed_id , "provider" : extra . get ( "provider" , "NASA" ) , "category" : extra . get ( "category" , "space" ) ,
        "type": "rss", "url": url, "enabled": True, "priority": extra.get("priority", "high"),  # info: "type" : "rss" , "url" : url , "enabled" : True , "priority" : extra . get ( "priority" , "high" ) ,
        "native_overlap": extra.get("native_overlap", False), "origin": extra.get("origin", "external"),  # info: "native_overlap" : extra . get ( "native_overlap" , False ) , "origin" : extra . get ( "origin" , "external" ) ,
    }  # info: }
    return row  # info: return row


# ====================================================
# SECTION: function _registry
# What it does: Wrap test feeds with the real category and policy files.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _registry(feeds: list[dict]) -> dict:  # info: def _registry
    base = load_registry(HERE.parent / "config")  # info: set base
    base["feeds"] = feeds  # info: base [ "feeds" ] = feeds
    base["policy"] = dict(base["policy"])  # info: base [ "policy" ] = dict ( base [ "policy" ] )
    fetch = dict(base["policy"].get("fetch") or {})  # info: set fetch
    fetch["unhealthy_after_failures"] = 2  # info: fetch [ "unhealthy_after_failures" ] = 2
    fetch["max_feeds_per_run"] = 10  # info: fetch [ "max_feeds_per_run" ] = 10
    base["policy"]["fetch"] = fetch  # info: base [ "policy" ] [ "fetch" ] = fetch
    return base  # info: return base


# ====================================================
# SECTION: function _xml
# What it does: Fill one RSS document.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _xml(title: str, link: str, guid: str, summary: str = "A published note.") -> bytes:  # info: def _xml
    return RSS.format(title=title, link=link, guid=guid, summary=summary).encode()  # info: return RSS . format ( title = title , link = link , guid = guid , summary = summary ) . encode ( )


# ====================================================
# SECTION: function test_registry
# What it does: The desk registry loads, and a new YAML feed is visible without a code change.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_registry() -> None:  # info: def test_registry
    registry = load_registry(HERE.parent / "config")  # info: set registry
    ids = [feed["id"] for feed in registry["feeds"]]  # info: set ids
    assert "nasa_news" in ids and "github_changelog" in ids  # info: assert "nasa_news" in ids and "github_changelog" in ids
    assert all(feed["category"] in registry["categories"] for feed in registry["feeds"])  # info: assert all ( feed [ "category" ] in registry [ "categories" ] for feed in registry [ "feeds" ] )
    assert all(feed["url"].startswith("http") for feed in registry["feeds"] if feed.get("enabled") and feed.get("origin") != "unavailable")  # info: assert all ( feed [ "url" ] . startswith ( "http" ) for feed in registry [ "feeds" ] if feed . get ( "enabled" ) and feed . get ( "origin" ) != "unavailable" )
    folder = Path(tempfile.mkdtemp())  # info: set folder
    try:  # info: try
        shutil.copy(HERE.parent / "config" / "categories.yaml", folder / "categories.yaml")  # info: shutil . copy ( HERE . parent / "config" / "categories.yaml" , folder / "categories.yaml" )
        shutil.copy(HERE.parent / "config" / "policy.yaml", folder / "policy.yaml")  # info: shutil . copy ( HERE . parent / "config" / "policy.yaml" , folder / "policy.yaml" )
        (folder / "feeds.yaml").write_text(  # info: ( folder / "feeds.yaml" ) . write_text (
            "feeds:\n  - id: extra_desk\n    name: Extra\n    provider: Example\n    category: science\n    type: rss\n    url: https://example.com/rss.xml\n    enabled: true\n    priority: low\n    native_overlap: false\n    origin: external\n",  # info: "feeds:\\n  - id: extra_desk\\n    name: Extra\\n    provider: Example\\n    category: science\\n    type: rss\\n    url: https://example.com/rss.xml\\n    enabled: true\\n    priority: low\\n    native_overlap: false\\n    origin: external\\n" ,
            encoding="utf-8",  # info: encoding = "utf-8" ,
        )  # info: )
        loaded = load_registry(folder)  # info: set loaded
        assert loaded["feeds"][0]["id"] == "extra_desk"  # info: assert loaded [ "feeds" ] [ 0 ] [ "id" ] == "extra_desk"
    finally:  # info: finally
        shutil.rmtree(folder)  # info: shutil . rmtree ( folder )


# ====================================================
# SECTION: function test_parse
# What it does: RSS and Atom both become items.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_parse() -> None:  # info: def test_parse
    rss = parse_document(_xml("Artemis update", "https://example.com/a?utm_source=x", "g1"))  # info: set rss
    assert rss[0]["title"] == "Artemis update" and rss[0]["guid"] == "g1"  # info: assert rss [ 0 ] [ "title" ] == "Artemis update" and rss [ 0 ] [ "guid" ] == "g1"
    atom = parse_document(ATOM.encode())  # info: set atom
    assert atom[0]["url"] == "https://example.com/kernel-7-2"  # info: assert atom [ 0 ] [ "url" ] == "https://example.com/kernel-7-2"
    assert atom[0]["published_at"].startswith("2026-10-01")  # info: assert atom [ 0 ] [ "published_at" ] . startswith ( "2026-10-01" )


# ====================================================
# SECTION: function test_pipeline
# What it does: Cluster two publishers, drop native overlap, keep going after a failed feed, and trace the source.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_pipeline() -> None:  # info: def test_pipeline
    root = Path(tempfile.mkdtemp())  # info: set root
    bodies = {  # info: set bodies
        "http://feeds.test/nasa": _xml("Artemis lunar flyby window confirmed", "https://news.test/artemis", "nasa-1", "NASA published the window."),  # info: "http://feeds.test/nasa" : _xml ( "Artemis lunar flyby window confirmed" , "https://news.test/artemis" , "nasa-1" , "NASA published the window." ) ,
        "http://feeds.test/ars": _xml("Artemis lunar flyby window confirmed", "https://news.test/artemis?utm_source=ars", "ars-1", "Ars published the same window."),  # info: "http://feeds.test/ars" : _xml ( "Artemis lunar flyby window confirmed" , "https://news.test/artemis?utm_source=ars" , "ars-1" , "Ars published the same window." ) ,
        "http://feeds.test/quake": _xml("Magnitude earthquake near Kilauea", "https://news.test/quake", "q1"),  # info: "http://feeds.test/quake" : _xml ( "Magnitude earthquake near Kilauea" , "https://news.test/quake" , "q1" ) ,
        "http://feeds.test/cyber": _xml("Library is actively exploited", "https://news.test/cve", "c1", "An emergency directive."),  # info: "http://feeds.test/cyber" : _xml ( "Library is actively exploited" , "https://news.test/cve" , "c1" , "An emergency directive." ) ,
        "http://feeds.test/vote": _xml("Election night count", "https://news.test/vote", "v1", "The party said voters should vote for the incumbent."),  # info: "http://feeds.test/vote" : _xml ( "Election night count" , "https://news.test/vote" , "v1" , "The party said voters should vote for the incumbent." ) ,
    }  # info: }
    calls = {"bad": 0}  # info: set calls

    def fetcher(url, policy, etag, modified):  # info: def fetcher
        if url == "http://feeds.test/bad":  # info: if url == "http://feeds.test/bad" :
            calls["bad"] += 1  # info: calls [ "bad" ] += 1
            raise RuntimeError("down")  # info: raise RuntimeError ( "down" )
        return {"ok": True, "status": 200, "body": bodies[url], "etag": "v1", "modified": "", "latency_ms": 3, "error": "", "not_modified": False, "skipped": ""}  # info: return { "ok" : True , "status" : 200 , "body" : bodies [ url ] , "etag" : "v1" , "modified" : "" , "latency_ms" : 3 , "error" : "" , "not_modified" : False , "skipped" : "" }

    feeds = [  # info: set feeds
        _feed("nasa_desk", "http://feeds.test/nasa"),  # info: _feed ( "nasa_desk" , "http://feeds.test/nasa" ) ,
        _feed("ars_desk", "http://feeds.test/ars", provider="Ars Technica", category="technology", priority="medium"),  # info: _feed ( "ars_desk" , "http://feeds.test/ars" , provider = "Ars Technica" , category = "technology" , priority = "medium" ) ,
        _feed("quake_desk", "http://feeds.test/quake", native_overlap=True, origin="overlapping"),  # info: _feed ( "quake_desk" , "http://feeds.test/quake" , native_overlap = True , origin = "overlapping" ) ,
        _feed("native_desk", "http://feeds.test/nasa", origin="native", category="science"),  # info: _feed ( "native_desk" , "http://feeds.test/nasa" , origin = "native" , category = "science" ) ,
        _feed("bad_desk", "http://feeds.test/bad", provider="NIST", category="cybersecurity"),  # info: _feed ( "bad_desk" , "http://feeds.test/bad" , provider = "NIST" , category = "cybersecurity" ) ,
        _feed("cyber_desk", "http://feeds.test/cyber", provider="NIST", category="cybersecurity"),  # info: _feed ( "cyber_desk" , "http://feeds.test/cyber" , provider = "NIST" , category = "cybersecurity" ) ,
        _feed("vote_desk", "http://feeds.test/vote", provider="NPR", category="global_news", priority="medium"),  # info: _feed ( "vote_desk" , "http://feeds.test/vote" , provider = "NPR" , category = "global_news" , priority = "medium" ) ,
    ]  # info: ]
    registry = _registry(feeds)  # info: set registry
    conn = connect(root)  # info: set conn
    try:  # info: try
        first = poll(registry, conn, fetcher=fetcher, root=root)  # info: set first
        assert first["ok"] is True  # info: assert first [ "ok" ] is True
        polled = {row["feed"] for row in first["polled"]}  # info: set polled
        assert "native_desk" not in polled and "bad_desk" in polled  # info: assert "native_desk" not in polled and "bad_desk" in polled
        second = poll(registry, conn, fetcher=fetcher, root=root, only="bad_desk")  # info: set second
        assert second["ok"] is True  # info: assert second [ "ok" ] is True
        state = feed_row(conn, "bad_desk")  # info: set state
        assert state["runtime_enabled"] == 0 and state["disable_reason"] == "feed_unhealthy"  # info: assert state [ "runtime_enabled" ] == 0 and state [ "disable_reason" ] == "feed_unhealthy"
        assert any(feed["id"] == "bad_desk" for feed in registry["feeds"])  # info: assert any ( feed [ "id" ] == "bad_desk" for feed in registry [ "feeds" ] )
        clusters = conn.execute("SELECT COUNT(*) FROM clusters").fetchone()[0]  # info: set clusters
        nasa = conn.execute("SELECT cluster_id FROM stories WHERE source_id='nasa_desk'").fetchone()  # info: set nasa
        ars = conn.execute("SELECT cluster_id FROM stories WHERE source_id='ars_desk'").fetchone()  # info: set ars
        assert nasa["cluster_id"] == ars["cluster_id"]  # info: assert nasa [ "cluster_id" ] == ars [ "cluster_id" ]
        assert conn.execute("SELECT COUNT(*) FROM stories WHERE source_id='quake_desk'").fetchone()[0] == 0  # info: assert conn . execute ( "SELECT COUNT(*) FROM stories WHERE source_id='quake_desk'" ) . fetchone ( ) [ 0 ] == 0
        cyber = conn.execute("SELECT priority FROM stories WHERE source_id='cyber_desk'").fetchone()  # info: set cyber
        assert cyber["priority"] == "urgent"  # info: assert cyber [ "priority" ] == "urgent"
        shown = handoff(registry, conn, speak=False, root=root)  # info: set shown
        assert shown["detail"] == "dry_run" and shown["program"] == "CYBER_BRIEF"  # info: assert shown [ "detail" ] == "dry_run" and shown [ "program" ] == "CYBER_BRIEF"
        vote = conn.execute("SELECT id FROM stories WHERE source_id='vote_desk'").fetchone()  # info: set vote
        found = trace(conn, vote["id"])  # info: set found
        assert found["story"]["url"] == "https://news.test/vote"  # info: assert found [ "story" ] [ "url" ] == "https://news.test/vote"
        script = Path(found["queue"]["script_path"]).read_text(encoding="utf-8")  # info: set script
        assert "NPR reports that" in script and "vote for" not in script.lower() and "https://news.test/vote" in script  # info: assert "NPR reports that" in script and "vote for" not in script . lower ( ) and "https://news.test/vote" in script
        board = health_report(registry, conn)  # info: set board
        labels = {row["id"]: row["status"] for row in board["feeds"]}  # info: set labels
        assert labels["bad_desk"] == "UNHEALTHY" and labels["nasa_desk"] == "HEALTHY"  # info: assert labels [ "bad_desk" ] == "UNHEALTHY" and labels [ "nasa_desk" ] == "HEALTHY"
        assert clusters >= 1  # info: assert clusters >= 1
    finally:  # info: finally
        conn.close()  # info: conn . close ( )
        shutil.rmtree(root)  # info: shutil . rmtree ( root )


# ====================================================
# SECTION: function test_conditional
# What it does: A second fetch sends the saved ETag and accepts HTTP 304.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_conditional() -> None:  # info: def test_conditional
    seen = {}  # info: set seen

    class Handler(BaseHTTPRequestHandler):  # info: class Handler
        def do_GET(self):  # info: def do_GET
            seen["etag"] = self.headers.get("If-None-Match")  # info: seen [ "etag" ] = self . headers . get ( "If-None-Match" )
            if self.path.endswith("robots.txt"):  # info: if self . path . endswith ( "robots.txt" ) :
                self.send_response(404)  # info: self . send_response ( 404 )
                self.end_headers()  # info: self . end_headers ( )
                return  # info: return
            if seen["etag"] == '"one"':  # info: if seen [ "etag" ] == '"one"' :
                self.send_response(304)  # info: self . send_response ( 304 )
                self.end_headers()  # info: self . end_headers ( )
                return  # info: return
            body = _xml("Docking coverage", "https://example.com/dock", "dock-1")  # info: set body
            self.send_response(200)  # info: self . send_response ( 200 )
            self.send_header("Content-Type", "application/rss+xml")  # info: self . send_header ( "Content-Type" , "application/rss+xml" )
            self.send_header("ETag", '"one"')  # info: self . send_header ( "ETag" , '"one"' )
            self.send_header("Content-Length", str(len(body)))  # info: self . send_header ( "Content-Length" , str ( len ( body ) ) )
            self.end_headers()  # info: self . end_headers ( )
            self.wfile.write(body)  # info: self . wfile . write ( body )

        def log_message(self, fmt, *args):  # info: def log_message
            return  # info: return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # info: set server
    thread = threading.Thread(target=server.serve_forever, daemon=True)  # info: set thread
    thread.start()  # info: thread . start ( )
    root = Path(tempfile.mkdtemp())  # info: set root
    try:  # info: try
        url = f"http://127.0.0.1:{server.server_address[1]}/feed.xml"  # info: set url
        registry = _registry([_feed("local_desk", url)])  # info: set registry
        conn = connect(root)  # info: set conn
        poll(registry, conn, root=root, only="local_desk")  # info: poll ( registry , conn , root = root , only = "local_desk" )
        poll(registry, conn, root=root, only="local_desk")  # info: poll ( registry , conn , root = root , only = "local_desk" )
        state = feed_row(conn, "local_desk")  # info: set state
        assert state["http_status"] == 304 and state["parse_status"] == "not_modified"  # info: assert state [ "http_status" ] == 304 and state [ "parse_status" ] == "not_modified"
        conn.close()  # info: conn . close ( )
    finally:  # info: finally
        server.shutdown()  # info: server . shutdown ( )
        shutil.rmtree(root)  # info: shutil . rmtree ( root )


# ====================================================
# SECTION: function main
# What it does: Run the RSS tests and print a one-line result.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    test_registry()  # info: test_registry ( )
    test_parse()  # info: test_parse ( )
    test_pipeline()  # info: test_pipeline ( )
    test_conditional()  # info: test_conditional ( )
    print("rss tests passed")  # info: print ( "rss tests passed" )
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( sys . argv ) )
