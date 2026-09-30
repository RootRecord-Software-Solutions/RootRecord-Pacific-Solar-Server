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
from __future__ import annotations

import gzip
import hashlib
import html
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

UA = 'Ava-Ivy/1.1 (+https://www.avaivy.cloud/news/)'
CHECKPOINT = '2026-03-31T00:00:00Z'
MAX_FEEDS = int(os.environ.get('RR_NEWS_MAX_FEEDS', '40'))
MAX_PAGES = int(os.environ.get('RR_NEWS_MAX_PAGES', '12'))
MAX_SITEMAPS = int(os.environ.get('RR_NEWS_MAX_SITEMAPS', '8'))
MAX_ARTICLES = int(os.environ.get('RR_NEWS_MAX_ARTICLES', '80'))
TIMEOUT_CAP = min(10.0, float(os.environ.get('RR_NEWS_TIMEOUT', '10')))
NEWS_WORDS = ('news', 'press', 'release', 'announcement', 'media', 'latest', 'briefing', 'story', 'update')
NEWS_PATHS = (
    '/news', '/news/', '/newsroom', '/newsroom/', '/press', '/press/',
    '/press-releases', '/press-releases/', '/media', '/media/',
    '/announcements', '/announcements/', '/latest-news', '/latest-news/',
    '/government/news', '/governor/news', '/governor/newsroom',
)
FEED_SUFFIXES = (
    '/feed', '/feed/', '/rss', '/rss/', '/rss.xml', '/feed.xml',
    '/atom.xml', '/news/feed/', '/news/rss.xml', '/news/atom.xml',
    '/newsroom/feed/', '/newsroom/rss.xml', '/press-releases/feed/',
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get(url: str, timeout: int = 20):
    req = Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/rss+xml,application/atom+xml,application/xml,text/html;q=0.95,*/*;q=0.5',
        'Accept-Encoding': 'gzip',
    })
    with urlopen(req, timeout=min(timeout, TIMEOUT_CAP)) as r:
        raw = r.read()
        if 'gzip' in (r.headers.get('content-encoding') or '').lower():
            raw = gzip.decompress(raw)
        return raw, r.headers.get('content-type', '')


def init_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path)
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
    c.commit()
    return c


def text(v) -> str:
    return re.sub(r'\s+', ' ', html.unescape(v or '')).strip()


def parse_date(v):
    if not v:
        return None
    v = text(v)
    try:
        return datetime.fromisoformat(v.replace('Z', '+00:00')).astimezone(timezone.utc).isoformat()
    except Exception:
        # Common RFC-822 feed dates.
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(v).astimezone(timezone.utc).isoformat()
        except Exception:
            return v


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.meta = {}
        self.jsonld = []
        self._tag = None
        self._attrs = {}
        self._buf = []
        self._script_buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = tag.lower()
        if t == 'a' and a.get('href'):
            self.links.append((a.get('href'), ''))
        elif t == 'link' and a.get('href'):
            self.links.append((a.get('href'), a.get('title') or a.get('rel') or a.get('type') or ''))
        elif t == 'meta':
            key = a.get('property') or a.get('name') or a.get('itemprop')
            if key and a.get('content'):
                self.meta[key.lower()] = a['content']
        if t == 'script' and (a.get('type') or '').lower() == 'application/ld+json':
            self._tag = 'jsonld'
            self._script_buf = []

    def handle_data(self, data):
        if self._tag == 'jsonld':
            self._script_buf.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'script' and self._tag == 'jsonld':
            raw = ''.join(self._script_buf).strip()
            if raw:
                try:
                    self.jsonld.append(json.loads(raw))
                except Exception:
                    pass
            self._tag = None
            self._script_buf = []


def parse_feed(raw, base):
    try:
        root = ET.fromstring(raw)
    except Exception:
        return []
    out = []
    for item in root.iter():
        kind = item.tag.split('}')[-1].lower()
        if kind not in ('item', 'entry'):
            continue
        vals = {}
        for child in item:
            n = child.tag.split('}')[-1].lower()
            val = child.attrib.get('href') or text(child.text)
            if n in ('title', 'description', 'summary', 'content', 'published', 'updated', 'pubdate', 'date', 'link', 'id', 'start', 'dtstart', 'location'):
                vals.setdefault(n, val)
        link = vals.get('link') or vals.get('id')
        if link and not link.startswith('http'):
            link = urljoin(base, link)
        published = vals.get('published') or vals.get('updated') or vals.get('pubdate') or vals.get('date')
        out.append({
            'title': vals.get('title') or 'Untitled',
            'summary': vals.get('summary') or vals.get('description') or vals.get('content') or '',
            'url': link,
            'published_at': published,
            'event_start': vals.get('start') or vals.get('dtstart'),
            'location': vals.get('location') or '',
        })
    return out


def _official_state_root(hostname: str) -> str:
    """Return the state's registrable government domain.

    State portals commonly link to agency/governor/news domains under the
    same state .gov namespace (for example portal.ct.gov -> ct.gov or
    governor.alabama.gov -> alabama.gov). The old collector rejected those
    links because it only allowed the exact portal hostname.
    """
    host = (hostname or "").lower().strip(".")
    parts = host.split(".")
    if len(parts) >= 2 and parts[-1] == "gov":
        return ".".join(parts[-2:])
    return host


def host_ok(base, candidate, state_slug=None):
    a = urlparse(base).hostname or ""
    b = urlparse(candidate).hostname or ""
    if not a or not b:
        return False

    if a == b or b.endswith("." + a):
        return True

    # Allow only official .gov hosts inside the same state government
    # namespace. This is the critical fix for portals whose News link points
    # at a governor/agency/newsroom host instead of the portal hostname.
    state_root = _official_state_root(a)
    candidate_root = _official_state_root(b)
    if state_root.endswith(".gov") and candidate_root == state_root:
        return True

    return False


def get_page(url: str, timeout: int = 20):
    """Fetch a page and return its final URL after redirects."""
    req = Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/rss+xml,application/atom+xml,application/xml,text/html;q=0.95,*/*;q=0.5',
        'Accept-Encoding': 'gzip',
    })
    with urlopen(req, timeout=min(timeout, TIMEOUT_CAP)) as r:
        raw = r.read()
        if 'gzip' in (r.headers.get('content-encoding') or '').lower():
            raw = gzip.decompress(raw)
        return raw, r.headers.get('content-type', ''), r.geturl()


def is_feed_content(raw, ctype=''):
    ct = (ctype or '').lower()
    if 'rss' in ct or 'atom' in ct or 'xml' in ct:
        return True
    head = raw[:500].lstrip().lower()
    return head.startswith(b'<?xml') or b'<rss' in head or b'<feed' in head


def candidate_score(url, label=''):
    s = (urlparse(url).path + ' ' + label).lower()
    return sum(3 for w in NEWS_WORDS if w in s)


def discover(homepage, state_slug=None):
    found = []
    pages = []
    sitemaps = []
    errors = []

    def add(items, bucket):
        for u in items:
            if not u or not u.startswith(('http://', 'https://')) or not host_ok(homepage, u, state_slug):
                continue
            if u not in bucket:
                bucket.append(u)

    try:
        raw, ctype, effective_homepage = get_page(homepage)
        discovery_base = effective_homepage or homepage
        if is_feed_content(raw, ctype):
            found.append(discovery_base)
        p = PageParser()
        p.feed(raw.decode('utf-8', 'ignore'))
        for href, label in p.links:
            u = urljoin(discovery_base, href)
            low = (label + ' ' + u).lower()
            if 'rss' in low or 'atom' in low or 'feed' in low:
                add([u], found)
            if any(w in low for w in NEWS_WORDS):
                add([u], pages)
        for suffix in NEWS_PATHS:
            add([urljoin(discovery_base, suffix)], pages)
        for suffix in FEED_SUFFIXES:
            add([urljoin(discovery_base, suffix)], found)
        for key, value in p.meta.items():
            if key in ('rss', 'alternate', 'application/rss+xml', 'application/atom+xml'):
                add([urljoin(discovery_base, value)], found)
    except Exception as e:
        errors.append(f'homepage: {type(e).__name__}: {e}')

    try:
        rb, _ = get(urljoin(discovery_base, '/robots.txt'))
        add(re.findall(r'(?im)^sitemap:\s*(\S+)', rb.decode('utf-8', 'ignore')), sitemaps)
    except Exception as e:
        errors.append(f'robots: {type(e).__name__}: {e}')

    return found[:MAX_FEEDS], pages[:MAX_PAGES], sitemaps[:MAX_SITEMAPS], errors


def sitemap_urls(url, limit=250):
    try:
        raw, _ = get(url)
        root = ET.fromstring(raw)
    except Exception:
        return [], []
    locs = []
    for e in root.iter():
        if e.tag.split('}')[-1].lower() == 'loc' and e.text:
            locs.append(text(e.text))
    kind = root.tag.split('}')[-1].lower()
    if kind == 'sitemapindex':
        return locs[:MAX_SITEMAPS], []
    return [], locs[:limit]


def article_candidates(page_url, raw):
    p = PageParser()
    p.feed(raw.decode('utf-8', 'ignore'))
    out = []
    for href, label in p.links:
        u = urljoin(page_url, href)
        if not u.startswith(('http://', 'https://')) or not host_ok(page_url, u):
            continue
        if candidate_score(u, label) >= 3:
            out.append((u, label))
    for obj in p.jsonld:
        objs = obj if isinstance(obj, list) else [obj]
        for x in objs:
            if not isinstance(x, dict):
                continue
            typ = x.get('@type')
            types = typ if isinstance(typ, list) else [typ]
            if not any(str(t).lower() in ('newsarticle', 'article', 'reportage') for t in types):
                continue
            u = x.get('url') or x.get('@id')
            if u:
                out.append((urljoin(page_url, u), x.get('headline') or x.get('name') or ''))
    clean = []
    for u, label in sorted(out, key=lambda x: candidate_score(x[0], x[1]), reverse=True):
        if u not in [x[0] for x in clean]:
            clean.append((u, label))
    return clean[:MAX_ARTICLES]


def page_articles(page_url, raw):
    p = PageParser()
    p.feed(raw.decode('utf-8', 'ignore'))
    items = []
    # JSON-LD is the most reliable HTML fallback.
    for obj in p.jsonld:
        objs = obj if isinstance(obj, list) else [obj]
        for x in objs:
            if not isinstance(x, dict):
                continue
            typ = x.get('@type')
            types = typ if isinstance(typ, list) else [typ]
            if not any(str(t).lower() in ('newsarticle', 'article', 'reportage') for t in types):
                continue
            u = x.get('url') or x.get('@id')
            if not u:
                continue
            items.append({
                'title': x.get('headline') or x.get('name') or 'Untitled',
                'summary': x.get('description') or '',
                'url': urljoin(page_url, u),
                'published_at': x.get('datePublished') or x.get('dateModified'),
                'event_start': None,
                'location': '',
            })
    # Meta/anchor fallback catches simple government newsroom pages.
    default_summary = p.meta.get('description') or p.meta.get('og:description') or ''
    for href, label in p.links:
        u = urljoin(page_url, href)
        if not u.startswith(('http://', 'https://')) or not host_ok(page_url, u):
            continue
        if candidate_score(u, label) < 3:
            continue
        title = text(label)
        if len(title) < 8 or title.lower() in ('news', 'press', 'media', 'read more', 'learn more'):
            continue
        items.append({'title': title, 'summary': default_summary, 'url': u, 'published_at': None, 'event_start': None, 'location': ''})
    clean = []
    seen = set()
    for x in items:
        u = x.get('url')
        if not u or u in seen:
            continue
        seen.add(u)
        clean.append(x)
    return clean[:MAX_ARTICLES]


def health(c, url, kind, status, items=0, error='', http_status=None):
    c.execute('''INSERT INTO source_health(source_url,kind,status,http_status,items_found,last_checked_at,last_error)
                 VALUES(?,?,?,?,?,?,?)
                 ON CONFLICT(source_url) DO UPDATE SET
                   kind=excluded.kind,status=excluded.status,http_status=excluded.http_status,
                   items_found=excluded.items_found,last_checked_at=excluded.last_checked_at,last_error=excluded.last_error''',
              (url, kind, status, http_status, items, now_iso(), error[:1000]))


def store_items(c, state_slug, homepage, feed_url, items, now, backfill, checkpoint):
    source_id = hashlib.sha1(feed_url.encode()).hexdigest()[:16]
    c.execute('''INSERT INTO sources(source_id,publisher,feed_url,homepage_url,kind,last_checked_at)
                 VALUES(?,?,?,?,?,?) ON CONFLICT(source_id) DO UPDATE SET last_checked_at=excluded.last_checked_at''',
              (source_id, state_slug.replace('-', ' ').title(), feed_url, homepage, 'official', now))
    new_posts = new_events = 0
    for x in items:
        if not x.get('url'):
            continue
        pub = parse_date(x.get('published_at'))
        if backfill and pub and pub < checkpoint:
            continue
        title = text(x.get('title') or 'Untitled')
        summary = text(x.get('summary') or '')
        h = hashlib.sha256((title + '|' + x['url']).encode()).hexdigest()
        cur = c.execute('''INSERT OR IGNORE INTO posts(source_id,title,summary,url,published_at,category,state,collected_at,content_hash)
                           VALUES(?,?,?,?,?,?,?,?,?)''',
                        (source_id, title, summary, x['url'], pub, 'government', state_slug, now, h))
        new_posts += cur.rowcount
        if x.get('event_start'):
            eh = hashlib.sha256((title + '|' + x['url'] + '|event').encode()).hexdigest()
            cur = c.execute('''INSERT OR IGNORE INTO events(source_id,title,description,url,start_at,end_at,location,category,state,collected_at,content_hash)
                               VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                            (source_id, title, summary, x['url'], parse_date(x['event_start']), None,
                             text(x.get('location')), 'public', state_slug, now, eh))
            new_events += cur.rowcount
    return new_posts, new_events


def run(state_slug, homepage, db_path, backfill=False, checkpoint=CHECKPOINT, seed_feeds=()):
    c = init_db(db_path)
    now = now_iso()
    if os.environ.get('RR_NEWS_SEEDS_ONLY') == '1' and seed_feeds:
        feeds, pages, sitemaps, discovery_errors = [], [], [], []
    else:
        feeds, pages, sitemaps, discovery_errors = discover(homepage, state_slug)
    feeds = list(dict.fromkeys(list(seed_feeds) + list(feeds)))  # seeds first; G0 discovery order kept after
    new_posts = new_events = 0
    attempted = set()

    # Feed-first collection.
    for feed in feeds:
        if feed in attempted:
            continue
        attempted.add(feed)
        try:
            raw, ctype = get(feed)
            items = parse_feed(raw, feed)
            if not items:
                health(c, feed, 'feed', 'empty', 0)
                continue
            p, e = store_items(c, state_slug, homepage, feed, items, now, backfill, checkpoint)
            new_posts += p; new_events += e
            health(c, feed, 'feed', 'ok', len(items))
        except Exception as exc:
            health(c, feed, 'feed', 'error', 0, f'{type(exc).__name__}: {exc}')

    # Crawl a few official newsroom/press landing pages.
    page_queue = list(pages)
    sitemap_queue = list(sitemaps)
    seen_sitemaps = set()
    for _ in range(MAX_SITEMAPS):
        if not sitemap_queue:
            break
        sm = sitemap_queue.pop(0)
        if sm in seen_sitemaps:
            continue
        seen_sitemaps.add(sm)
        children, urls = sitemap_urls(sm)
        sitemap_queue.extend(children[:MAX_SITEMAPS])
        for u in urls:
            if candidate_score(u) >= 3:
                page_queue.append(u)

    # Prefer pages that actually look like news/press endpoints.
    page_queue = sorted(set(page_queue), key=candidate_score, reverse=True)[:MAX_PAGES]
    article_queue = []
    for page in page_queue:
        if page in attempted:
            continue
        attempted.add(page)
        try:
            raw, ctype = get(page)
            if is_feed_content(raw, ctype):
                items = parse_feed(raw, page)
                if items:
                    p, e = store_items(c, state_slug, homepage, page, items, now, backfill, checkpoint)
                    new_posts += p; new_events += e
                    health(c, page, 'discovered-feed', 'ok', len(items))
                    continue
            items = page_articles(page, raw)
            article_queue.extend(article_candidates(page, raw))
            health(c, page, 'news-page', 'ok' if items else 'empty', len(items))
            if items:
                p, e = store_items(c, state_slug, homepage, page, items, now, backfill, checkpoint)
                new_posts += p; new_events += e
        except Exception as exc:
            health(c, page, 'news-page', 'error', 0, f'{type(exc).__name__}: {exc}')

    # Fetch a bounded number of individual article pages when a newsroom only
    # exposes ordinary HTML links instead of a feed.
    seen_articles = set()
    for article_url, label in article_queue[:MAX_ARTICLES]:
        if article_url in seen_articles or article_url in attempted:
            continue
        seen_articles.add(article_url)
        try:
            raw, _ = get(article_url, timeout=15)
            items = page_articles(article_url, raw)
            # If JSON-LD is absent, retain the link text as the title.
            if not items and label:
                items = [{'title': label, 'summary': '', 'url': article_url, 'published_at': None, 'event_start': None, 'location': ''}]
            if items:
                p, e = store_items(c, state_slug, homepage, article_url, items[:3], now, backfill, checkpoint)
                new_posts += p; new_events += e
        except Exception:
            continue

    if backfill:
        notes = f'official-source pass; feeds={len(feeds)} pages={len(page_queue)} sitemap_roots={len(sitemaps)}'
        if discovery_errors:
            notes += '; discovery_errors=' + ' | '.join(discovery_errors)
        c.execute('INSERT INTO backfill_runs(started_at,checkpoint,status,notes) VALUES(?,?,?,?)',
                  (now, checkpoint, 'completed', notes))
    c.execute("INSERT INTO collector_state(key,value) VALUES('last_run',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (now,))
    c.execute("INSERT INTO collector_state(key,value) VALUES('last_discovery_errors',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (' | '.join(discovery_errors)[:4000],))
    c.commit()

    health_rows = c.execute("SELECT status,COUNT(*) FROM source_health GROUP BY status ORDER BY status").fetchall()
    c.close()
    print({
        'state': state_slug,
        'feeds_checked': len(feeds),
        'pages_checked': len(page_queue),
        'new_posts': new_posts,
        'new_events': new_events,
        'health': dict(health_rows),
        'backfill': backfill,
    })
