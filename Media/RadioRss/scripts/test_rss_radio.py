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

from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from parse_feed import parse_document  # info: from parse_feed import parse_document
from stories import barred, deadline, normalize, partisan, sports, violent  # info: from stories import barred , deadline , normalize , partisan , sports , violent
from news_hour import _take, balance_personas, build_update, persona_for  # info: from news_hour import _take , build_update , persona_for
from pipeline import handoff, health_report, nhc_spoken, poll, trace  # info: from pipeline import handoff , health_report , nhc_spoken , poll , trace
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
        _feed("vote_desk", "http://feeds.test/vote", provider="France 24", category="global_news", priority="medium"),  # info: _feed ( "vote_desk" , "http://feeds.test/vote" , provider = "France 24" , category = "global_news" , priority = "medium" ) ,
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
        assert "France 24 reports that" in script and "vote for" not in script.lower() and "https://news.test/vote" in script  # info: assert vote sentence dropped
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


def test_news_update() -> None:  # info: def test_news_update
    registry = load_registry(HERE.parent / "config")  # info: set registry
    assert "markets" in registry["categories"] and "spacex" in registry["categories"]  # info: assert "markets" in registry [ "categories" ] and "spacex" in registry [ "categories" ]
    assert "chips" in registry["categories"] and "mainland_weather" in registry["categories"]  # info: assert "chips" in registry [ "categories" ] and "mainland_weather" in registry [ "categories" ]
    assert "mainland_politics" in registry["categories"] and "universities" in registry["categories"]  # info: assert "mainland_politics" in registry [ "categories" ] and "universities" in registry [ "categories" ]
    assert persona_for(0, 0, ("ava", "bruce", "carly")) == "ava"  # info: assert persona_for ( 0 , 0 , ( "ava" , "bruce" , "carly" ) ) == "ava"
    assert persona_for(1, 0, ("ava", "bruce", "carly")) == "bruce"  # info: assert persona_for ( 1 , 0 , ( "ava" , "bruce" , "carly" ) ) == "bruce"
    assert persona_for(0, 1, ("ava", "bruce", "carly")) == "bruce"  # info: assert persona_for ( 0 , 1 , ( "ava" , "bruce" , "carly" ) ) == "bruce"
    cfg = registry["policy"]["news_update"]  # info: set cfg
    assert int(cfg.get("target_words") or 0) >= 3000  # info: assert int ( cfg . get ( "target_words" ) or 0 ) >= 3000
    hawaii = {"id": "hi", "nonviolent": True, "category": "hawaii", "provider": "Hawaii DBEDT", "name": "Hawaii DBEDT", "priority": "high"}  # info: set hawaii
    crime = {"title": "Shooting in Honolulu", "summary": "A man was killed.", "url": "https://news.test/crime", "guid": "crime"}  # info: set crime
    calm = {"title": "Harbor ferry schedule", "summary": "The state published a new timetable.", "url": "https://news.test/ferry", "guid": "ferry", "published_at": "2026-10-01T18:00:00Z"}  # info: set calm
    assert violent(hawaii, crime, registry) is True  # info: assert violent ( hawaii , crime , registry ) is True
    assert normalize(hawaii, crime, registry) is None  # info: assert normalize ( hawaii , crime , registry ) is None
    world = {"id": "world", "category": "global_news", "provider": "France 24", "name": "France 24", "priority": "medium"}  # info: set world
    gang = {"title": "Gang fight downtown", "summary": "Police reported the fight.", "url": "https://news.test/gang", "guid": "gang"}  # info: set gang
    assert violent(world, gang, registry) is True  # info: assert violent ( world , gang , registry ) is True
    budget_end = {"title": "Launch deadline moved", "summary": "The deadlock on the budget ended.", "url": "https://news.test/deadline", "guid": "deadline"}  # info: set budget_end
    assert violent(world, budget_end, registry) is False  # info: assert violent ( world , budget_end , registry ) is False
    bodies = {"title": "Men trying to end violence against women", "summary": "The discovery of 12 women's bodies near Johannesburg.", "url": "https://www.bbc.com/news/bodies", "guid": "bodies"}  # info: set bodies
    assert violent(world, bodies, registry) is True  # info: assert violent ( world , bodies , registry ) is True
    skirt = {"title": "Women given shorts to prevent upskirting", "summary": "Voyeuristic videos on social media.", "url": "https://www.bbc.com/news/skirt", "guid": "skirt"}  # info: set skirt
    assert violent(world, skirt, registry) is True  # info: assert violent ( world , skirt , registry ) is True
    guardian = {"id": "g", "category": "global_news", "provider": "The Guardian", "name": "The Guardian International", "priority": "high"}  # info: set guardian
    beer = {"title": "Sustainable beers", "summary": "Brewers cut packaging.", "url": "https://www.theguardian.com/food/beer", "guid": "beer", "provider": "The Guardian"}  # info: set beer
    assert barred(guardian, beer, registry) is True  # info: assert barred ( guardian , beer , registry ) is True
    assert normalize(guardian, beer, registry) is None  # info: assert normalize ( guardian , beer , registry ) is None
    assert all(feed["id"] != "guardian_international" for feed in registry["feeds"])  # info: assert guardian feed is gone
    bbc = {"id": "bbc", "category": "markets", "provider": "BBC", "name": "BBC Business", "priority": "high"}  # info: set bbc
    diesel = {"title": "G7 oil release", "summary": "Prices fell.", "url": "https://www.bbc.com/news/business/oil", "guid": "oil", "provider": "BBC"}  # info: set diesel
    assert barred(bbc, diesel, registry) is True  # info: assert barred ( bbc , diesel , registry ) is True
    assert normalize(bbc, diesel, registry) is None  # info: assert normalize ( bbc , diesel , registry ) is None
    assert all(not str(feed.get("id") or "").startswith("bbc_") for feed in registry["feeds"])  # info: assert every bbc feed is gone
    advisory = "LOCATION...19.3N 111.1W ABOUT 260 MI...420 KM SSW OF THE SOUTHERN TIP OF BAJA CALIFORNIA MAXIMUM SUSTAINED WINDS...105 MPH...165 KM/H PRESENT MOVEMENT...W OR 265 DEGREES AT 5 MPH...7 KM/H ...RACHEL CONTINUES LASHING SOCORRO ISLAND AS IT MOVES SLOWLY WESTWARD..."  # info: set advisory
    said = nhc_spoken("Hurricane Rachel Public Advisory Number 23", advisory)  # info: set said
    assert "260 miles south-southwest" in said and "socorro island" in said.lower()  # info: assert place and headline
    assert "19.3" not in said and "latitude" not in said.lower() and "longitude" not in said.lower()  # info: assert no coordinates
    assert nhc_spoken("Hurricane Rachel Wind Speed Probabilities Number 23", "LATITUDE 19.3 NORTH...LONGITUDE 111.1 WEST") == ""  # info: assert probability table is silent
    assert nhc_spoken("Hurricane Rachel Forecast Discussion Number 23", "000 WTPZ43 KNHC") == ""  # info: assert discussion is silent
    assert nhc_spoken("There are no tropical cyclones at this time", "No tropical cyclones as of Sat") == "There are no tropical cyclones in that basin."  # info: assert quiet basin
    doj = {"id": "doj", "category": "mainland_politics", "provider": "Department of Justice", "name": "Department of Justice News", "priority": "high", "centrist": True}  # info: set doj
    due = {"title": "FY27 Q4 Report Due", "summary": "", "url": "https://www.justice.gov/oip/event/fy27-q4-report-due", "guid": "due"}  # info: set due
    charge = {"title": "Final two defendants sentenced in an auto theft conspiracy", "summary": "A court sentenced the last two defendants.", "url": "https://www.justice.gov/opa/pr/sentenced", "guid": "charge"}  # info: set charge
    assert deadline(doj, due, registry) is True  # info: assert deadline ( doj , due , registry ) is True
    assert normalize(doj, due, registry) is None  # info: assert normalize ( doj , due , registry ) is None
    assert deadline(doj, charge, registry) is False  # info: assert deadline ( doj , charge , registry ) is False
    assert barred(doj, charge, registry) is True  # info: assert justice is off
    assert normalize(doj, charge, registry) is None  # info: assert normalize drops justice
    watch = {"title": "Wage note", "summary": "Prices moved.", "url": "https://www.marketwatch.com/story/wages", "guid": "mw", "provider": "MarketWatch", "source_id": "marketwatch_top"}  # info: set watch
    assert barred({"id": "marketwatch_top", "provider": "MarketWatch", "name": "MarketWatch Top Stories"}, watch, registry) is True  # info: assert marketwatch is off
    npr_ok = {"title": "A research note", "summary": "A lab published a result.", "url": "https://www.npr.org/2026/10/02/research", "guid": "npr-ok", "provider": "NPR", "source_name": "NPR News", "source_id": "npr_news"}  # info: set npr_ok
    assert barred({"id": "npr_news", "provider": "NPR", "name": "NPR News"}, npr_ok, registry) is True  # info: assert npr news is off
    npr_world = {"title": "A world note", "summary": "A desk filed a note.", "url": "https://www.npr.org/2026/10/02/world", "guid": "npr-world", "provider": "NPR", "source_name": "NPR World", "source_id": "npr_world"}  # info: set npr_world
    assert barred({"id": "npr_world", "provider": "NPR", "name": "NPR World"}, npr_world, registry) is True  # info: assert npr world is off
    npr_nat = {"title": "A hearing", "summary": "A committee met.", "url": "https://www.npr.org/2026/10/02/hearing", "guid": "npr-nat", "provider": "NPR", "source_name": "NPR National", "source_id": "npr_national"}  # info: set npr_nat
    assert barred({}, npr_nat, registry) is True  # info: assert npr national is off
    gone = {"marketwatch_top", "civil_beat", "star_advertiser", "hawaii_news_now", "npr_news", "npr_world", "npr_national", "npr_politics", "doj_news", "guardian_international"}  # info: set gone
    assert gone.isdisjoint({feed["id"] for feed in registry["feeds"]})  # info: assert those feeds are deleted
    campus = []  # info: set campus
    for index, (publisher, title) in enumerate([  # info: for index
        ("MIT News", "Warehouse dedication"), ("MIT News", "Endowment figures"), ("MIT News", "Computational tools"),  # info: three MIT items
        ("MIT News", "Tech worker movement"), ("MIT News", "Space economy guide"),  # info: two more MIT items
        ("UC Berkeley", "Woodland study"), ("Harvard Gazette", "Campus lab"),  # info: other universities
    ]):  # info: end pairs
        campus.append({  # info: campus . append
            "id": f"campus-{index}", "category": "universities", "provider": publisher, "title": title,  # info: identity
            "title_norm": title.lower(), "summary": "A short campus note with a live figure.", "url": f"https://news.test/campus/{index}",  # info: text
            "canonical_url": f"https://news.test/campus/{index}", "cluster_id": f"campus-{index}", "priority": "high",  # info: keys
            "published_at": f"2026-10-01T1{index}:00:00Z", "political": 0,  # info: time
        })  # info: end story
    _lines, picked, _used = _take(campus, ["universities"], 400, registry, set())  # info: set picked
    assert sum(1 for story in picked if story["provider"] == "MIT News") == 2  # info: assert two MIT items
    assert any(story["provider"] == "UC Berkeley" for story in picked)  # info: assert Berkeley still fits
    from pipeline import speak_body  # info: from pipeline import speak_body
    body = speak_body("Harbor ferry schedule", "Harbor ferry schedule. The state published a new timetable.", registry["policy"])  # info: set body
    assert body.lower().count("harbor ferry schedule") == 0  # info: assert headline not repeated
    game = {"title": "Prep football preview", "summary": "OIA playoff puzzle.", "url": "https://www.staradvertiser.com/2026/10/01/sports/hawaii-prep-world/prep-football/", "guid": "sports-1"}  # info: set game
    assert sports(hawaii, game, registry) is True  # info: assert sports ( hawaii , game , registry ) is True
    assert normalize(hawaii, game, registry) is None  # info: assert normalize ( hawaii , game , registry ) is None
    transit = {"title": "Harbor ferry schedule", "summary": "Transportation brief for Honolulu Harbor.", "url": "https://news.test/transportation", "guid": "transit"}  # info: set transit
    assert sports(hawaii, transit, registry) is False  # info: assert sports ( hawaii , transit , registry ) is False
    conflict = {"title": "SEC Charges Adviser for Failure to Disclose Conflict of Interest", "summary": "Inflation and influence concerns.", "url": "https://www.sec.gov/newsroom/press-releases/conflict", "guid": "conflict"}  # info: set conflict
    assert sports(hawaii, conflict, registry) is False  # info: assert sports ( hawaii , conflict , registry ) is False
    wear = {"title": "Nike sportswear outlook", "summary": "The sportswear brand cut guidance.", "url": "https://news.test/markets/nike", "guid": "nike"}  # info: set wear
    assert sports(hawaii, wear, registry) is False  # info: assert sports ( hawaii , wear , registry ) is False
    nfl = {"title": "NASA astronaut to join NFL fans", "summary": "Pre-game event in Baltimore.", "url": "https://www.nasa.gov/news-release/nasa-astronaut-reid-wiseman-to-join-nfl-fans-in-baltimore/", "guid": "nfl-1"}  # info: set nfl
    assert sports(hawaii, nfl, registry) is True  # info: assert sports ( hawaii , nfl , registry ) is True
    politics = {"id": "pol", "centrist": True, "category": "mainland_politics", "provider": "NPR", "name": "NPR Politics", "priority": "high"}  # info: set politics
    rant = {"title": "Far-left radicals storm the capital", "summary": "A deep state witch hunt.", "url": "https://news.test/rant", "guid": "rant"}  # info: set rant
    assert partisan(politics, rant, registry) is True  # info: assert partisan ( politics , rant , registry ) is True
    assert normalize(politics, rant, registry) is None  # info: assert normalize ( politics , rant , registry ) is None
    gated = {"id": "sx", "category": "spacex", "provider": "Spaceflight Now", "name": "Spaceflight Now", "priority": "high", "require_patterns": ["spacex", "starship"]}  # info: set gated
    assert normalize(gated, {"title": "Canada rocket test", "summary": "An engine site.", "url": "https://news.test/rocket", "guid": "rocket"}, registry) is None  # info: assert normalize ( gated , { "title" : "Canada rocket test" , "summary" : "An engine site." , "url" : "https://news.test/rocket" , "guid" : "rocket" } , registry ) is None
    assert normalize(gated, {"title": "Starship test", "summary": "A flight.", "url": "https://news.test/star", "guid": "star"}, registry) is not None  # info: assert normalize ( gated , { "title" : "Starship test" , "summary" : "A flight." , "url" : "https://news.test/star" , "guid" : "star" } , registry ) is not None
    kept = normalize(hawaii, calm, registry)  # info: set kept
    assert kept is not None and kept["category"] == "hawaii"  # info: assert kept is not None and kept [ "category" ] == "hawaii"
    long = "The agency published a market note. " * 40  # info: set long
    stories = []  # info: set stories
    categories = ["markets", "national_security", "spacex", "hawaii", "chips", "global_news", "mainland_weather", "mainland_politics", "science", "universities", "space"]  # info: set categories
    for index, category in enumerate(categories):  # info: for index , category in enumerate ( categories )
        for copy in range(8):  # info: for copy in range ( 8 )
            stories.append({  # info: stories . append ( {
                "id": f"{category}-{copy}", "category": category, "provider": "France 24", "title": f"{category} item {copy} with a live figure {copy}",  # info: "id" : f"{ category }-{ copy }" , "category" : category , "provider" : "France 24" , "title" : f"{ category } item { copy } with a live figure { copy }" ,
                "summary": long, "url": f"https://news.test/{category}/{copy}", "published_at": f"2026-10-01T{10 + (copy % 9):02d}:00:00Z",  # info: "summary" : long , "url" : f"https://news.test/{ category }/{ copy }" , "published_at" : f"2026-10-01T{ 10 + ( copy % 9 ) :02d }:00:00Z" ,
                "priority": "high", "cluster_id": f"c-{category}-{copy}", "political": 0, "canonical_url": f"https://news.test/{category}/{copy}",  # info: "priority" : "high" , "cluster_id" : f"c-{ category }-{ copy }" , "political" : 0 , "canonical_url" : f"https://news.test/{ category }/{ copy }" ,
            })  # info: } )
    when = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)  # info: set when
    built = build_update(stories, registry, when)  # info: set built
    assert built["words"] <= 4200  # info: assert built [ "words" ] <= 4200
    assert built["words"] >= 2000  # info: assert built [ "words" ] >= 2000
    ids = [section["id"] for section in built["sections"]]  # info: set ids
    assert "chips" in ids and "world" in ids and "mainland_weather" in ids and "mainland_politics" in ids  # info: assert "chips" in ids and "world" in ids and "mainland_weather" in ids and "mainland_politics" in ids
    assert "science" in ids and "universities" in ids  # info: assert "science" in ids and "universities" in ids
    voice_words = {"ava": 0, "bruce": 0, "carly": 0}  # info: set voice_words
    for section in built["sections"]:  # info: for section in built [ "sections" ]
        voice_words[section["persona"]] = voice_words.get(section["persona"], 0) + len(section["text"].split())  # info: voice_words [ section [ "persona" ] ] = voice_words . get ( section [ "persona" ] , 0 ) + len ( section [ "text" ] . split ( ) )
    assert set(voice_words) >= {"ava", "bruce", "carly"}  # info: assert set ( voice_words ) >= { "ava" , "bruce" , "carly" }
    values = list(voice_words.values())  # info: set values
    assert max(values) - min(values) <= max(120, int(0.25 * (sum(values) / 3)))  # info: assert max ( values ) - min ( values ) <= max ( 120 , int ( 0.25 * ( sum ( values ) / 3 ) ) )
    assert "Markets." in built["speak"] and "SpaceX." in built["speak"] and "Tech and chips." in built["speak"]  # info: assert "Markets." in built [ "speak" ] and "SpaceX." in built [ "speak" ] and "Tech and chips." in built [ "speak" ]
    assert "World." in built["speak"] and "Universities." in built["speak"] and "killed" not in built["speak"].lower()  # info: assert "World." in built [ "speak" ] and "Universities." in built [ "speak" ] and "killed" not in built [ "speak" ] . lower ( )
    assert "football" not in built["speak"].lower() and "sports" not in built["speak"].lower()  # info: assert "football" not in built [ "speak" ] . lower ( ) and "sports" not in built [ "speak" ] . lower ( )
    assert "2026" in built["speak"]  # info: assert "2026" in built [ "speak" ]


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
    test_news_update()  # info: test_news_update ( )
    print("rss tests passed")  # info: print ( "rss tests passed" )
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__"
    raise SystemExit(main())  # info: raise SystemExit ( main ( sys . argv ) )
