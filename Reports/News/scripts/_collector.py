# ==============================================================================
# FILE: Reports/News/scripts/_collector.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Shared official-state news/event collector.

The state wrappers provide identity and an official state portal.  This collector
uses several publisher-native discovery paths instead of assuming that every
state site exposes the same RSS URL.  It records source health in SQLite so a
failed state is visible instead of silently looking like an empty state.

G3 port (2026-09-29, old-repo migration) of G0 `old/operations/news/_collector.py`. Logic unchanged except:
every HTTP timeout is capped at RR_NEWS_TIMEOUT (default 10 s) and the crawl limits can be lowered with
RR_NEWS_MAX_FEEDS / _PAGES / _SITEMAPS / _ARTICLES (defaults = G0 values).
2026-09-29 (breadth 2): run() takes optional seed_feeds (explicit, operator-confirmed feed URLs, fetched first and
not subject to host_ok); RR_NEWS_SEEDS_ONLY=1 skips portal discovery / sitemap / page crawl entirely.
"""
from __future__ import annotations  # info: from __future__ import annotations

import gzip  # info: import gzip
import hashlib  # info: import hashlib
import html  # info: import html
import json  # info: import json
import os  # info: import os
import re  # info: import re
import sqlite3  # info: import sqlite3
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from html.parser import HTMLParser  # info: from html . parser import HTMLParser
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import urljoin, urlparse  # info: from urllib . parse import urljoin , urlparse
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen
import xml.etree.ElementTree as ET  # info: import xml . etree . ElementTree as ET

UA = 'Ava-Ivy/1.1 (+https://www.avaivy.cloud/news/)'  # info: set UA
CHECKPOINT = '2026-03-31T00:00:00Z'  # info: set CHECKPOINT
MAX_FEEDS = int(os.environ.get('RR_NEWS_MAX_FEEDS', '40'))  # info: set MAX_FEEDS
MAX_PAGES = int(os.environ.get('RR_NEWS_MAX_PAGES', '12'))  # info: set MAX_PAGES
MAX_SITEMAPS = int(os.environ.get('RR_NEWS_MAX_SITEMAPS', '8'))  # info: set MAX_SITEMAPS
MAX_ARTICLES = int(os.environ.get('RR_NEWS_MAX_ARTICLES', '80'))  # info: set MAX_ARTICLES
TIMEOUT_CAP = min(10.0, float(os.environ.get('RR_NEWS_TIMEOUT', '10')))  # info: set TIMEOUT_CAP
NEWS_WORDS = ('news', 'press', 'release', 'announcement', 'media', 'latest', 'briefing', 'story', 'update')  # info: set NEWS_WORDS
# ====================================================
# SECTION: NEWS_PATHS
# What it does: Set NEWS_PATHS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
NEWS_PATHS = (  # info: set NEWS_PATHS
    '/news', '/news/', '/newsroom', '/newsroom/', '/press', '/press/',  # info: '/news' , '/news/' , '/newsroom' , '/newsroom/' ,
    '/press-releases', '/press-releases/', '/media', '/media/',  # info: '/press-releases' , '/press-releases/' , '/media' , '/media/' ,
    '/announcements', '/announcements/', '/latest-news', '/latest-news/',  # info: '/announcements' , '/announcements/' , '/latest-news' , '/latest-news/' ,
    '/government/news', '/governor/news', '/governor/newsroom',  # info: '/government/news' , '/governor/news' , '/governor/newsroom' ,
)  # info: )
# ====================================================
# SECTION: FEED_SUFFIXES
# What it does: Set FEED_SUFFIXES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
FEED_SUFFIXES = (  # info: set FEED_SUFFIXES
    '/feed', '/feed/', '/rss', '/rss/', '/rss.xml', '/feed.xml',  # info: '/feed' , '/feed/' , '/rss' , '/rss/' ,
    '/atom.xml', '/news/feed/', '/news/rss.xml', '/news/atom.xml',  # info: '/atom.xml' , '/news/feed/' , '/news/rss.xml' , '/news/atom.xml' ,
    '/newsroom/feed/', '/newsroom/rss.xml', '/press-releases/feed/',  # info: '/newsroom/feed/' , '/newsroom/rss.xml' , '/press-releases/feed/' ,
)  # info: )


# ====================================================
# SECTION: function now_iso
# What it does: now iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_iso() -> str:  # info: def now_iso
    return datetime.now(timezone.utc).isoformat()  # info: return datetime . now ( timezone . utc


# ====================================================
# SECTION: function get
# What it does: get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def get(url: str, timeout: int = 20):  # info: def get
    req = Request(url, headers={  # info: set req
        'User-Agent': UA,  # info: 'User-Agent' : UA ,
        'Accept': 'application/rss+xml,application/atom+xml,application/xml,text/html;q=0.95,*/*;q=0.5',  # info: 'Accept' : 'application/rss+xml,application/atom+xml,application/xml,text/html;q=0.95,*/*;q=0.5' ,
        'Accept-Encoding': 'gzip',  # info: 'Accept-Encoding' : 'gzip' ,
    })  # info: } )
    with urlopen(req, timeout=min(timeout, TIMEOUT_CAP)) as r:  # info: with urlopen ( req , timeout = min
        raw = r.read()  # info: set raw
        if 'gzip' in (r.headers.get('content-encoding') or '').lower():  # info: if 'gzip' in ( r . headers .
            raw = gzip.decompress(raw)  # info: set raw
        return raw, r.headers.get('content-type', '')  # info: return raw , r . headers . get


# ====================================================
# SECTION: function init_db
# What it does: init db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def init_db(path: Path):  # info: def init_db
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    c = sqlite3.connect(path)  # info: set c
    c.executescript('''
    CREATE TABLE IF NOT EXISTS sources(
      source_id TEXT PRIMARY KEY,
      publisher TEXT,
      feed_url TEXT,
      homepage_url TEXT,
      kind TEXT,
      active INTEGER DEFAULT 1,
      last_checked_at TEXT
    );
    CREATE TABLE IF NOT EXISTS posts(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_id TEXT,
      title TEXT,
      summary TEXT,
      url TEXT,
      published_at TEXT,
      category TEXT,
      state TEXT,
      collected_at TEXT,
      content_hash TEXT UNIQUE
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_url ON posts(url);
    CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published_at);
    CREATE TABLE IF NOT EXISTS events(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_id TEXT,
      title TEXT,
      description TEXT,
      url TEXT,
      start_at TEXT,
      end_at TEXT,
      location TEXT,
      category TEXT,
      state TEXT,
      collected_at TEXT,
      content_hash TEXT UNIQUE
    );
    CREATE TABLE IF NOT EXISTS backfill_runs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      started_at TEXT,
      checkpoint TEXT,
      status TEXT,
      notes TEXT
    );
    CREATE TABLE IF NOT EXISTS collector_state(key TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE IF NOT EXISTS source_health(
      source_url TEXT PRIMARY KEY,
      kind TEXT,
      status TEXT,
      http_status INTEGER,
      items_found INTEGER DEFAULT 0,
      last_checked_at TEXT,
      last_error TEXT
    );
    ''')
    c.commit()  # info: c . commit ( )
    return c  # info: return c


# ====================================================
# SECTION: function text
# What it does: text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def text(v) -> str:  # info: def text
    return re.sub(r'\s+', ' ', html.unescape(v or '')).strip()  # info: return re . sub ( r'\s+' , ' '


# ====================================================
# SECTION: function parse_date
# What it does: parse date.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_date(v):  # info: def parse_date
    if not v:  # info: if not v :
        return None  # info: return None
    v = text(v)  # info: set v
    try:  # info: try :
        return datetime.fromisoformat(v.replace('Z', '+00:00')).astimezone(timezone.utc).isoformat()  # info: return datetime . fromisoformat ( v . replace
    except Exception:  # info: except Exception :
        # Common RFC-822 feed dates.
        try:  # info: try :
            from email.utils import parsedate_to_datetime  # info: from email . utils import parsedate_to_datetime
            return parsedate_to_datetime(v).astimezone(timezone.utc).isoformat()  # info: return parsedate_to_datetime ( v ) . astimezone (
        except Exception:  # info: except Exception :
            return v  # info: return v


# ====================================================
# SECTION: class PageParser
# What it does: PageParser.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class PageParser(HTMLParser):  # info: class PageParser
    def __init__(self):  # info: def __init__
        super().__init__(convert_charrefs=True)  # info: call super
        self.links = []  # info: self . links = [ ]
        self.meta = {}  # info: self . meta = { }
        self.jsonld = []  # info: self . jsonld = [ ]
        self._tag = None  # info: self . _tag = None
        self._attrs = {}  # info: self . _attrs = { }
        self._buf = []  # info: self . _buf = [ ]
        self._script_buf = []  # info: self . _script_buf = [ ]

    def handle_starttag(self, tag, attrs):  # info: def handle_starttag
        a = dict(attrs)  # info: set a
        t = tag.lower()  # info: set t
        if t == 'a' and a.get('href'):  # info: if t == 'a' and a . get
            self.links.append((a.get('href'), ''))  # info: self . links . append ( ( a
        elif t == 'link' and a.get('href'):  # info: elif t == 'link' and a . get
            self.links.append((a.get('href'), a.get('title') or a.get('rel') or a.get('type') or ''))  # info: self . links . append ( ( a
        elif t == 'meta':  # info: elif t == 'meta' :
            key = a.get('property') or a.get('name') or a.get('itemprop')  # info: set key
            if key and a.get('content'):  # info: if key and a . get ( 'content'
                self.meta[key.lower()] = a['content']  # info: self . meta [ key . lower (
        if t == 'script' and (a.get('type') or '').lower() == 'application/ld+json':  # info: if t == 'script' and ( a .
            self._tag = 'jsonld'  # info: self . _tag = 'jsonld'
            self._script_buf = []  # info: self . _script_buf = [ ]

    def handle_data(self, data):  # info: def handle_data
        if self._tag == 'jsonld':  # info: if self . _tag == 'jsonld' :
            self._script_buf.append(data)  # info: self . _script_buf . append ( data )

    def handle_endtag(self, tag):  # info: def handle_endtag
        if tag.lower() == 'script' and self._tag == 'jsonld':  # info: if tag . lower ( ) == 'script'
            raw = ''.join(self._script_buf).strip()  # info: set raw
            if raw:  # info: if raw :
                try:  # info: try :
                    self.jsonld.append(json.loads(raw))  # info: self . jsonld . append ( json .
                except Exception:  # info: except Exception :
                    pass  # info: pass
            self._tag = None  # info: self . _tag = None
            self._script_buf = []  # info: self . _script_buf = [ ]


# ====================================================
# SECTION: function parse_feed
# What it does: parse feed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_feed(raw, base):  # info: def parse_feed
    try:  # info: try :
        root = ET.fromstring(raw)  # info: set root
    except Exception:  # info: except Exception :
        return []  # info: return [ ]
    out = []  # info: set out
    for item in root.iter():  # info: for item in root . iter ( )
        kind = item.tag.split('}')[-1].lower()  # info: set kind
        if kind not in ('item', 'entry'):  # info: if kind not in ( 'item' , 'entry'
            continue  # info: continue
        vals = {}  # info: set vals
        for child in item:  # info: for child in item :
            n = child.tag.split('}')[-1].lower()  # info: set n
            val = child.attrib.get('href') or text(child.text)  # info: set val
            if n in ('title', 'description', 'summary', 'content', 'published', 'updated', 'pubdate', 'date', 'link', 'id', 'start', 'dtstart', 'location'):  # info: if n in ( 'title' , 'description' ,
                vals.setdefault(n, val)  # info: vals . setdefault ( n , val )
        link = vals.get('link') or vals.get('id')  # info: set link
        if link and not link.startswith('http'):  # info: if link and not link . startswith (
            link = urljoin(base, link)  # info: set link
        published = vals.get('published') or vals.get('updated') or vals.get('pubdate') or vals.get('date')  # info: set published
        out.append({  # info: out . append ( {
            'title': vals.get('title') or 'Untitled',  # info: 'title' : vals . get ( 'title' )
            'summary': vals.get('summary') or vals.get('description') or vals.get('content') or '',  # info: 'summary' : vals . get ( 'summary' )
            'url': link,  # info: 'url' : link ,
            'published_at': published,  # info: 'published_at' : published ,
            'event_start': vals.get('start') or vals.get('dtstart'),  # info: 'event_start' : vals . get ( 'start' )
            'location': vals.get('location') or '',  # info: 'location' : vals . get ( 'location' )
        })  # info: } )
    return out  # info: return out


# ====================================================
# SECTION: function _official_state_root
# What it does: Return the state's registrable government domain. State portals commonly link to agency/governor/news domains under the same state .gov namespace (for example portal.ct.gov -> ct.g
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _official_state_root(hostname: str) -> str:  # info: def _official_state_root
    """Return the state's registrable government domain.

    State portals commonly link to agency/governor/news domains under the
    same state .gov namespace (for example portal.ct.gov -> ct.gov or
    governor.alabama.gov -> alabama.gov). The old collector rejected those
    links because it only allowed the exact portal hostname.
    """
    host = (hostname or "").lower().strip(".")  # info: set host
    parts = host.split(".")  # info: set parts
    if len(parts) >= 2 and parts[-1] == "gov":  # info: if len ( parts ) >= 2 and
        return ".".join(parts[-2:])  # info: return "." . join ( parts [ -
    return host  # info: return host


# ====================================================
# SECTION: function host_ok
# What it does: host ok.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def host_ok(base, candidate, state_slug=None):  # info: def host_ok
    a = urlparse(base).hostname or ""  # info: set a
    b = urlparse(candidate).hostname or ""  # info: set b
    if not a or not b:  # info: if not a or not b :
        return False  # info: return False

    if a == b or b.endswith("." + a):  # info: if a == b or b . endswith
        return True  # info: return True

    # Allow only official .gov hosts inside the same state government
    # namespace. This is the critical fix for portals whose News link points
    # at a governor/agency/newsroom host instead of the portal hostname.
    state_root = _official_state_root(a)  # info: set state_root
    candidate_root = _official_state_root(b)  # info: set candidate_root
    if state_root.endswith(".gov") and candidate_root == state_root:  # info: if state_root . endswith ( ".gov" ) and
        return True  # info: return True

    return False  # info: return False


# ====================================================
# SECTION: function get_page
# What it does: Fetch a page and return its final URL after redirects.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def get_page(url: str, timeout: int = 20):  # info: def get_page
    """Fetch a page and return its final URL after redirects."""  # info: """Fetch a page and return its final URL after redirects."""
    req = Request(url, headers={  # info: set req
        'User-Agent': UA,  # info: 'User-Agent' : UA ,
        'Accept': 'application/rss+xml,application/atom+xml,application/xml,text/html;q=0.95,*/*;q=0.5',  # info: 'Accept' : 'application/rss+xml,application/atom+xml,application/xml,text/html;q=0.95,*/*;q=0.5' ,
        'Accept-Encoding': 'gzip',  # info: 'Accept-Encoding' : 'gzip' ,
    })  # info: } )
    with urlopen(req, timeout=min(timeout, TIMEOUT_CAP)) as r:  # info: with urlopen ( req , timeout = min
        raw = r.read()  # info: set raw
        if 'gzip' in (r.headers.get('content-encoding') or '').lower():  # info: if 'gzip' in ( r . headers .
            raw = gzip.decompress(raw)  # info: set raw
        return raw, r.headers.get('content-type', ''), r.geturl()  # info: return raw , r . headers . get


# ====================================================
# SECTION: function is_feed_content
# What it does: is feed content.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_feed_content(raw, ctype=''):  # info: def is_feed_content
    ct = (ctype or '').lower()  # info: set ct
    if 'rss' in ct or 'atom' in ct or 'xml' in ct:  # info: if 'rss' in ct or 'atom' in ct
        return True  # info: return True
    head = raw[:500].lstrip().lower()  # info: set head
    return head.startswith(b'<?xml') or b'<rss' in head or b'<feed' in head  # info: return head . startswith ( b'<?xml' ) or


# ====================================================
# SECTION: function candidate_score
# What it does: candidate score.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def candidate_score(url, label=''):  # info: def candidate_score
    s = (urlparse(url).path + ' ' + label).lower()  # info: set s
    return sum(3 for w in NEWS_WORDS if w in s)  # info: return sum ( 3 for w in NEWS_WORDS


# ====================================================
# SECTION: function discover
# What it does: discover.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def discover(homepage, state_slug=None):  # info: def discover
    found = []  # info: set found
    pages = []  # info: set pages
    sitemaps = []  # info: set sitemaps
    errors = []  # info: set errors

    def add(items, bucket):  # info: def add
        for u in items:  # info: for u in items :
            if not u or not u.startswith(('http://', 'https://')) or not host_ok(homepage, u, state_slug):  # info: if not u or not u . startswith
                continue  # info: continue
            if u not in bucket:  # info: if u not in bucket :
                bucket.append(u)  # info: bucket . append ( u )

    try:  # info: try :
        raw, ctype, effective_homepage = get_page(homepage)  # info: raw , ctype , effective_homepage = get_page (
        discovery_base = effective_homepage or homepage  # info: set discovery_base
        if is_feed_content(raw, ctype):  # info: if is_feed_content ( raw , ctype ) :
            found.append(discovery_base)  # info: found . append ( discovery_base )
        p = PageParser()  # info: set p
        p.feed(raw.decode('utf-8', 'ignore'))  # info: p . feed ( raw . decode (
        for href, label in p.links:  # info: for href , label in p . links
            u = urljoin(discovery_base, href)  # info: set u
            low = (label + ' ' + u).lower()  # info: set low
            if 'rss' in low or 'atom' in low or 'feed' in low:  # info: if 'rss' in low or 'atom' in low
                add([u], found)  # info: call add
            if any(w in low for w in NEWS_WORDS):  # info: if any ( w in low for w
                add([u], pages)  # info: call add
        for suffix in NEWS_PATHS:  # info: for suffix in NEWS_PATHS :
            add([urljoin(discovery_base, suffix)], pages)  # info: call add
        for suffix in FEED_SUFFIXES:  # info: for suffix in FEED_SUFFIXES :
            add([urljoin(discovery_base, suffix)], found)  # info: call add
        for key, value in p.meta.items():  # info: for key , value in p . meta
            if key in ('rss', 'alternate', 'application/rss+xml', 'application/atom+xml'):  # info: if key in ( 'rss' , 'alternate' ,
                add([urljoin(discovery_base, value)], found)  # info: call add
    except Exception as e:  # info: except Exception as e :
        errors.append(f'homepage: {type(e).__name__}: {e}')  # info: errors . append ( f' homepage: { type

    try:  # info: try :
        rb, _ = get(urljoin(discovery_base, '/robots.txt'))  # info: rb , _ = get ( urljoin (
        add(re.findall(r'(?im)^sitemap:\s*(\S+)', rb.decode('utf-8', 'ignore')), sitemaps)  # info: call add
    except Exception as e:  # info: except Exception as e :
        errors.append(f'robots: {type(e).__name__}: {e}')  # info: errors . append ( f' robots: { type

    return found[:MAX_FEEDS], pages[:MAX_PAGES], sitemaps[:MAX_SITEMAPS], errors  # info: return found [ : MAX_FEEDS ] , pages


# ====================================================
# SECTION: function sitemap_urls
# What it does: sitemap urls.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sitemap_urls(url, limit=250):  # info: def sitemap_urls
    try:  # info: try :
        raw, _ = get(url)  # info: raw , _ = get ( url )
        root = ET.fromstring(raw)  # info: set root
    except Exception:  # info: except Exception :
        return [], []  # info: return [ ] , [ ]
    locs = []  # info: set locs
    for e in root.iter():  # info: for e in root . iter ( )
        if e.tag.split('}')[-1].lower() == 'loc' and e.text:  # info: if e . tag . split ( '}'
            locs.append(text(e.text))  # info: locs . append ( text ( e .
    kind = root.tag.split('}')[-1].lower()  # info: set kind
    if kind == 'sitemapindex':  # info: if kind == 'sitemapindex' :
        return locs[:MAX_SITEMAPS], []  # info: return locs [ : MAX_SITEMAPS ] , [
    return [], locs[:limit]  # info: return [ ] , locs [ : limit


# ====================================================
# SECTION: function article_candidates
# What it does: article candidates.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def article_candidates(page_url, raw):  # info: def article_candidates
    p = PageParser()  # info: set p
    p.feed(raw.decode('utf-8', 'ignore'))  # info: p . feed ( raw . decode (
    out = []  # info: set out
    for href, label in p.links:  # info: for href , label in p . links
        u = urljoin(page_url, href)  # info: set u
        if not u.startswith(('http://', 'https://')) or not host_ok(page_url, u):  # info: if not u . startswith ( ( 'http://'
            continue  # info: continue
        if candidate_score(u, label) >= 3:  # info: if candidate_score ( u , label ) >=
            out.append((u, label))  # info: out . append ( ( u , label
    for obj in p.jsonld:  # info: for obj in p . jsonld :
        objs = obj if isinstance(obj, list) else [obj]  # info: set objs
        for x in objs:  # info: for x in objs :
            if not isinstance(x, dict):  # info: if not isinstance ( x , dict )
                continue  # info: continue
            typ = x.get('@type')  # info: set typ
            types = typ if isinstance(typ, list) else [typ]  # info: set types
            if not any(str(t).lower() in ('newsarticle', 'article', 'reportage') for t in types):  # info: if not any ( str ( t )
                continue  # info: continue
            u = x.get('url') or x.get('@id')  # info: set u
            if u:  # info: if u :
                out.append((urljoin(page_url, u), x.get('headline') or x.get('name') or ''))  # info: out . append ( ( urljoin ( page_url
    clean = []  # info: set clean
    for u, label in sorted(out, key=lambda x: candidate_score(x[0], x[1]), reverse=True):  # info: for u , label in sorted ( out
        if u not in [x[0] for x in clean]:  # info: if u not in [ x [ 0
            clean.append((u, label))  # info: clean . append ( ( u , label
    return clean[:MAX_ARTICLES]  # info: return clean [ : MAX_ARTICLES ]


# ====================================================
# SECTION: function page_articles
# What it does: page articles.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def page_articles(page_url, raw):  # info: def page_articles
    p = PageParser()  # info: set p
    p.feed(raw.decode('utf-8', 'ignore'))  # info: p . feed ( raw . decode (
    items = []  # info: set items
    # JSON-LD is the most reliable HTML fallback.
    for obj in p.jsonld:  # info: for obj in p . jsonld :
        objs = obj if isinstance(obj, list) else [obj]  # info: set objs
        for x in objs:  # info: for x in objs :
            if not isinstance(x, dict):  # info: if not isinstance ( x , dict )
                continue  # info: continue
            typ = x.get('@type')  # info: set typ
            types = typ if isinstance(typ, list) else [typ]  # info: set types
            if not any(str(t).lower() in ('newsarticle', 'article', 'reportage') for t in types):  # info: if not any ( str ( t )
                continue  # info: continue
            u = x.get('url') or x.get('@id')  # info: set u
            if not u:  # info: if not u :
                continue  # info: continue
            items.append({  # info: items . append ( {
                'title': x.get('headline') or x.get('name') or 'Untitled',  # info: 'title' : x . get ( 'headline' )
                'summary': x.get('description') or '',  # info: 'summary' : x . get ( 'description' )
                'url': urljoin(page_url, u),  # info: 'url' : urljoin ( page_url , u )
                'published_at': x.get('datePublished') or x.get('dateModified'),  # info: 'published_at' : x . get ( 'datePublished' )
                'event_start': None,  # info: 'event_start' : None ,
                'location': '',  # info: 'location' : '' ,
            })  # info: } )
    # Meta/anchor fallback catches simple government newsroom pages.
    default_summary = p.meta.get('description') or p.meta.get('og:description') or ''  # info: set default_summary
    for href, label in p.links:  # info: for href , label in p . links
        u = urljoin(page_url, href)  # info: set u
        if not u.startswith(('http://', 'https://')) or not host_ok(page_url, u):  # info: if not u . startswith ( ( 'http://'
            continue  # info: continue
        if candidate_score(u, label) < 3:  # info: if candidate_score ( u , label ) <
            continue  # info: continue
        title = text(label)  # info: set title
        if len(title) < 8 or title.lower() in ('news', 'press', 'media', 'read more', 'learn more'):  # info: if len ( title ) < 8 or
            continue  # info: continue
        items.append({'title': title, 'summary': default_summary, 'url': u, 'published_at': None, 'event_start': None, 'location': ''})  # info: items . append ( { 'title' : title
    clean = []  # info: set clean
    seen = set()  # info: set seen
    for x in items:  # info: for x in items :
        u = x.get('url')  # info: set u
        if not u or u in seen:  # info: if not u or u in seen :
            continue  # info: continue
        seen.add(u)  # info: seen . add ( u )
        clean.append(x)  # info: clean . append ( x )
    return clean[:MAX_ARTICLES]  # info: return clean [ : MAX_ARTICLES ]


# ====================================================
# SECTION: function health
# What it does: health.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def health(c, url, kind, status, items=0, error='', http_status=None):  # info: def health
    c.execute('''INSERT INTO source_health(source_url,kind,status,http_status,items_found,last_checked_at,last_error)
                 VALUES(?,?,?,?,?,?,?)
                 ON CONFLICT(source_url) DO UPDATE SET
                   kind=excluded.kind,status=excluded.status,http_status=excluded.http_status,
                   items_found=excluded.items_found,last_checked_at=excluded.last_checked_at,last_error=excluded.last_error''',
              (url, kind, status, http_status, items, now_iso(), error[:1000]))  # info: call (


# ====================================================
# SECTION: function store_items
# What it does: store items.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def store_items(c, state_slug, homepage, feed_url, items, now, backfill, checkpoint):  # info: def store_items
    source_id = hashlib.sha1(feed_url.encode()).hexdigest()[:16]  # info: set source_id
    c.execute('''INSERT INTO sources(source_id,publisher,feed_url,homepage_url,kind,last_checked_at)
                 VALUES(?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET last_checked_at=excluded.last_checked_at''',
              (source_id, state_slug.replace('-', ' ').title(), feed_url, homepage, 'official', now))  # info: call (
    new_posts = new_events = 0  # info: set new_posts
    for x in items:  # info: for x in items :
        if not x.get('url'):  # info: if not x . get ( 'url' )
            continue  # info: continue
        pub = parse_date(x.get('published_at'))  # info: set pub
        if backfill and pub and pub < checkpoint:  # info: if backfill and pub and pub < checkpoint
            continue  # info: continue
        title = text(x.get('title') or 'Untitled')  # info: set title
        summary = text(x.get('summary') or '')  # info: set summary
        h = hashlib.sha256((title + '|' + x['url']).encode()).hexdigest()  # info: set h
        cur = c.execute('''INSERT OR IGNORE INTO posts(source_id,title,summary,url,published_at,category,state,collected_at,content_hash)
                           VALUES(?,?,?,?,?,?,?,?,?)''',
                        (source_id, title, summary, x['url'], pub, 'government', state_slug, now, h))  # info: call (
        new_posts += cur.rowcount  # info: set new_posts
        if x.get('event_start'):  # info: if x . get ( 'event_start' ) :
            eh = hashlib.sha256((title + '|' + x['url'] + '|event').encode()).hexdigest()  # info: set eh
            cur = c.execute('''INSERT OR IGNORE INTO events(source_id,title,description,url,start_at,end_at,location,category,state,collected_at,content_hash)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                            (source_id, title, summary, x['url'], parse_date(x['event_start']), None,  # info: call (
                             text(x.get('location')), 'public', state_slug, now, eh))  # info: call text
            new_events += cur.rowcount  # info: set new_events
    return new_posts, new_events  # info: return new_posts , new_events


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run(state_slug, homepage, db_path, backfill=False, checkpoint=CHECKPOINT, seed_feeds=()):  # info: def run
    c = init_db(db_path)  # info: set c
    now = now_iso()  # info: set now
    if os.environ.get('RR_NEWS_SEEDS_ONLY') == '1' and seed_feeds:  # info: if os . environ . get ( 'RR_NEWS_SEEDS_ONLY'
        feeds, pages, sitemaps, discovery_errors = [], [], [], []  # info: feeds , pages , sitemaps , discovery_errors =
    else:  # info: else :
        feeds, pages, sitemaps, discovery_errors = discover(homepage, state_slug)  # info: feeds , pages , sitemaps , discovery_errors =
    feeds = list(dict.fromkeys(list(seed_feeds) + list(feeds)))  # seeds first; G0 discovery order kept after
    new_posts = new_events = 0  # info: set new_posts
    attempted = set()  # info: set attempted

    # Feed-first collection.
    for feed in feeds:  # info: for feed in feeds :
        if feed in attempted:  # info: if feed in attempted :
            continue  # info: continue
        attempted.add(feed)  # info: attempted . add ( feed )
        try:  # info: try :
            raw, ctype = get(feed)  # info: raw , ctype = get ( feed )
            items = parse_feed(raw, feed)  # info: set items
            if not items:  # info: if not items :
                health(c, feed, 'feed', 'empty', 0)  # info: call health
                continue  # info: continue
            p, e = store_items(c, state_slug, homepage, feed, items, now, backfill, checkpoint)  # info: p , e = store_items ( c ,
            new_posts += p; new_events += e  # info: set new_posts
            health(c, feed, 'feed', 'ok', len(items))  # info: call health
        except Exception as exc:  # info: except Exception as exc :
            health(c, feed, 'feed', 'error', 0, f'{type(exc).__name__}: {exc}')  # info: call health

    # Crawl a few official newsroom/press landing pages.
    page_queue = list(pages)  # info: set page_queue
    sitemap_queue = list(sitemaps)  # info: set sitemap_queue
    seen_sitemaps = set()  # info: set seen_sitemaps
    for _ in range(MAX_SITEMAPS):  # info: for _ in range ( MAX_SITEMAPS ) :
        if not sitemap_queue:  # info: if not sitemap_queue :
            break  # info: break
        sm = sitemap_queue.pop(0)  # info: set sm
        if sm in seen_sitemaps:  # info: if sm in seen_sitemaps :
            continue  # info: continue
        seen_sitemaps.add(sm)  # info: seen_sitemaps . add ( sm )
        children, urls = sitemap_urls(sm)  # info: children , urls = sitemap_urls ( sm )
        sitemap_queue.extend(children[:MAX_SITEMAPS])  # info: sitemap_queue . extend ( children [ : MAX_SITEMAPS
        for u in urls:  # info: for u in urls :
            if candidate_score(u) >= 3:  # info: if candidate_score ( u ) >= 3 :
                page_queue.append(u)  # info: page_queue . append ( u )

    # Prefer pages that actually look like news/press endpoints.
    page_queue = sorted(set(page_queue), key=candidate_score, reverse=True)[:MAX_PAGES]  # info: set page_queue
    article_queue = []  # info: set article_queue
    for page in page_queue:  # info: for page in page_queue :
        if page in attempted:  # info: if page in attempted :
            continue  # info: continue
        attempted.add(page)  # info: attempted . add ( page )
        try:  # info: try :
            raw, ctype = get(page)  # info: raw , ctype = get ( page )
            if is_feed_content(raw, ctype):  # info: if is_feed_content ( raw , ctype ) :
                items = parse_feed(raw, page)  # info: set items
                if items:  # info: if items :
                    p, e = store_items(c, state_slug, homepage, page, items, now, backfill, checkpoint)  # info: p , e = store_items ( c ,
                    new_posts += p; new_events += e  # info: set new_posts
                    health(c, page, 'discovered-feed', 'ok', len(items))  # info: call health
                    continue  # info: continue
            items = page_articles(page, raw)  # info: set items
            article_queue.extend(article_candidates(page, raw))  # info: article_queue . extend ( article_candidates ( page ,
            health(c, page, 'news-page', 'ok' if items else 'empty', len(items))  # info: call health
            if items:  # info: if items :
                p, e = store_items(c, state_slug, homepage, page, items, now, backfill, checkpoint)  # info: p , e = store_items ( c ,
                new_posts += p; new_events += e  # info: set new_posts
        except Exception as exc:  # info: except Exception as exc :
            health(c, page, 'news-page', 'error', 0, f'{type(exc).__name__}: {exc}')  # info: call health

    # Fetch a bounded number of individual article pages when a newsroom only
    # exposes ordinary HTML links instead of a feed.
    seen_articles = set()  # info: set seen_articles
    for article_url, label in article_queue[:MAX_ARTICLES]:  # info: for article_url , label in article_queue [ :
        if article_url in seen_articles or article_url in attempted:  # info: if article_url in seen_articles or article_url in attempted
            continue  # info: continue
        seen_articles.add(article_url)  # info: seen_articles . add ( article_url )
        try:  # info: try :
            raw, _ = get(article_url, timeout=15)  # info: raw , _ = get ( article_url ,
            items = page_articles(article_url, raw)  # info: set items
            # If JSON-LD is absent, retain the link text as the title.
            if not items and label:  # info: if not items and label :
                items = [{'title': label, 'summary': '', 'url': article_url, 'published_at': None, 'event_start': None, 'location': ''}]  # info: set items
            if items:  # info: if items :
                p, e = store_items(c, state_slug, homepage, article_url, items[:3], now, backfill, checkpoint)  # info: p , e = store_items ( c ,
                new_posts += p; new_events += e  # info: set new_posts
        except Exception:  # info: except Exception :
            continue  # info: continue

    if backfill:  # info: if backfill :
        notes = f'official-source pass; feeds={len(feeds)} pages={len(page_queue)} sitemap_roots={len(sitemaps)}'  # info: set notes
        if discovery_errors:  # info: if discovery_errors :
            notes += '; discovery_errors=' + ' | '.join(discovery_errors)  # info: set notes
        c.execute('INSERT INTO backfill_runs(started_at,checkpoint,status,notes) VALUES(?,?,?,?)',  # info: c . execute ( 'INSERT INTO backfill_runs(started_at,checkpoint,status,notes) VALUES(?,?,?,?)' ,
                  (now, checkpoint, 'completed', notes))  # info: call (
    c.execute("INSERT INTO collector_state(key,value) VALUES('last_run',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (now,))  # info: c . execute ( "INSERT INTO collector_state(key,value) VALUES('last_run',?) ON CONFLICT(key) DO UPDATE SET valu
    c.execute("INSERT INTO collector_state(key,value) VALUES('last_discovery_errors',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (' | '.join(discovery_errors)[:4000],))  # info: c . execute ( "INSERT INTO collector_state(key,value) VALUES('last_discovery_errors',?) ON CONFLICT(key) DO UP
    c.commit()  # info: c . commit ( )

    health_rows = c.execute("SELECT status,COUNT(*) FROM source_health GROUP BY status ORDER BY status").fetchall()  # info: set health_rows
    c.close()  # info: c . close ( )
    print({  # info: call print
        'state': state_slug,  # info: 'state' : state_slug ,
        'feeds_checked': len(feeds),  # info: 'feeds_checked' : len ( feeds ) ,
        'pages_checked': len(page_queue),  # info: 'pages_checked' : len ( page_queue ) ,
        'new_posts': new_posts,  # info: 'new_posts' : new_posts ,
        'new_events': new_events,  # info: 'new_events' : new_events ,
        'health': dict(health_rows),  # info: 'health' : dict ( health_rows ) ,
        'backfill': backfill,  # info: 'backfill' : backfill ,
    })  # info: } )
