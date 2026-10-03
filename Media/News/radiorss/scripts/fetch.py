# ==============================================================================
# FILE: Media/RadioRss/scripts/fetch.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Conditional HTTP fetch for RSS and Atom. One failure returns a result. It does not raise."""
from __future__ import annotations  # info: from __future__ import annotations

import socket  # info: import socket
import ssl  # info: import ssl
import time  # info: import time
from http.client import HTTPConnection, HTTPSConnection, HTTPException  # info: from http . client import HTTPConnection , HTTPSConnection , HTTPException
from urllib.parse import urlsplit  # info: from urllib . parse import urlsplit
from urllib.robotparser import RobotFileParser  # info: from urllib . robotparser import RobotFileParser

_ROBOTS: dict[str, RobotFileParser | None] = {}  # info: set _ROBOTS


# ====================================================
# SECTION: function _connection
# What it does: Open one HTTP connection with a short connect timeout.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _connection(parts, connect_timeout: float, https: bool):  # info: def _connection
    port = parts.port or (443 if https else 80)  # info: set port
    if https:  # info: if https :
        conn = HTTPSConnection(parts.hostname, port, timeout=connect_timeout, context=ssl.create_default_context())  # info: set conn
    else:  # info: else
        conn = HTTPConnection(parts.hostname, port, timeout=connect_timeout)  # info: set conn
    return conn  # info: return conn


# ====================================================
# SECTION: function _read_limited
# What it does: Read a response body up to max_bytes. Larger bodies are refused.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_limited(response, max_bytes: int) -> bytes:  # info: def _read_limited
    chunks = []  # info: set chunks
    total = 0  # info: set total
    while True:  # info: while True
        block = response.read(65536)  # info: set block
        if not block:  # info: if not block :
            break  # info: break
        total += len(block)  # info: set total
        if total > max_bytes:  # info: if total > max_bytes :
            raise ValueError("response_too_large")  # info: raise ValueError ( "response_too_large" )
        chunks.append(block)  # info: chunks . append ( block )
    return b"".join(chunks)  # info: return b"" . join ( chunks )


# ====================================================
# SECTION: function _robots_allow
# What it does: Honor robots.txt when it can be read. A robots outage does not block the feed.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _robots_allow(url: str, agent: str, connect_timeout: float) -> bool:  # info: def _robots_allow
    parts = urlsplit(url)  # info: set parts
    host = (parts.scheme, parts.netloc.lower())  # info: set host
    if host not in _ROBOTS:  # info: if host not in _ROBOTS :
        parser = RobotFileParser()  # info: set parser
        robots = f"{parts.scheme}://{parts.netloc}/robots.txt"  # info: set robots
        try:  # info: try
            result = _request(robots, agent, connect_timeout, 10, 200000, {}, 0)  # info: set result
            if result.get("status") == 200 and result.get("body"):  # info: if result . get ( "status" ) == 200 and result . get ( "body" ) :
                parser.parse(result["body"].decode("utf-8", "replace").splitlines())  # info: parser . parse ( result [ "body" ] . decode ( "utf-8" , "replace" ) . splitlines ( ) )
                _ROBOTS[host] = parser  # info: _ROBOTS [ host ] = parser
            else:  # info: else
                _ROBOTS[host] = None  # info: _ROBOTS [ host ] = None
        except Exception:  # info: except Exception
            _ROBOTS[host] = None  # info: _ROBOTS [ host ] = None
    parser = _ROBOTS.get(host)  # info: set parser
    if parser is None:  # info: if parser is None :
        return True  # info: return True
    return parser.can_fetch(agent, url)  # info: return parser . can_fetch ( agent , url )


# ====================================================
# SECTION: function _request
# What it does: One GET with redirects, conditional headers, and a size cap. Does not retry.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _request(url: str, agent: str, connect_timeout: float, read_timeout: float, max_bytes: int, condition: dict, redirects: int) -> dict:  # info: def _request
    current = url  # info: set current
    hops = 0  # info: set hops
    while True:  # info: while True
        parts = urlsplit(current)  # info: set parts
        if parts.scheme not in {"http", "https"} or not parts.hostname:  # info: if parts . scheme not in { "http" , "https" } or not parts . hostname :
            return {"ok": False, "status": 0, "error": "bad_url", "body": b"", "headers": {}}  # info: return { "ok" : False , "status" : 0 , "error" : "bad_url" , "body" : b"" , "headers" : { } }
        conn = _connection(parts, connect_timeout, parts.scheme == "https")  # info: set conn
        path = parts.path or "/"  # info: set path
        if parts.query:  # info: if parts . query :
            path = path + "?" + parts.query  # info: set path
        headers = {"User-Agent": agent, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*;q=0.1", "Accept-Encoding": "identity"}  # info: set headers
        if hops == 0:  # info: if hops == 0 :
            headers.update(condition)  # info: headers . update ( condition )
        try:  # info: try
            conn.request("GET", path, headers=headers)  # info: conn . request ( "GET" , path , headers = headers )
            conn.sock.settimeout(read_timeout)  # info: conn . sock . settimeout ( read_timeout )
            response = conn.getresponse()  # info: set response
            status = response.status  # info: set status
            header_map = {key.lower(): value for key, value in response.getheaders()}  # info: set header_map
            if status in {301, 302, 303, 307, 308} and header_map.get("location") and hops < redirects:  # info: if status in { 301 , 302 , 303 , 307 , 308 } and header_map . get ( "location" ) and hops < redirects :
                from urllib.parse import urljoin  # info: from urllib . parse import urljoin
                current = urljoin(current, header_map["location"])  # info: set current
                hops += 1  # info: set hops
                response.read(1024)  # info: response . read ( 1024 )
                conn.close()  # info: conn . close ( )
                continue  # info: continue
            body = b"" if status == 304 else _read_limited(response, max_bytes)  # info: set body
            conn.close()  # info: conn . close ( )
            return {"ok": status in {200, 304}, "status": status, "error": "", "body": body, "headers": header_map, "final_url": current}  # info: return { "ok" : status in { 200 , 304 } , "status" : status , "error" : "" , "body" : body , "headers" : header_map , "final_url" : current }
        except (OSError, TimeoutError, socket.timeout, HTTPException, ValueError) as exc:  # info: except ( OSError , TimeoutError , socket . timeout , HTTPException , ValueError ) as exc
            try:  # info: try
                conn.close()  # info: conn . close ( )
            except OSError:  # info: except OSError
                pass  # info: pass
            return {"ok": False, "status": 0, "error": type(exc).__name__ + ":" + str(exc)[:180], "body": b"", "headers": {}}  # info: return { "ok" : False , "status" : 0 , "error" : type ( exc ) . __name__ + ":" + str ( exc ) [ : 180 ] , "body" : b"" , "headers" : { } }


# ====================================================
# SECTION: function fetch_url
# What it does: Fetch one feed with retries and backoff. 304 is a success. Robots disallow is a skip.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_url(url: str, policy: dict, etag: str = "", modified: str = "") -> dict:  # info: def fetch_url
    fetch = policy.get("fetch") or {}  # info: set fetch
    agent = str(fetch.get("user_agent") or "RootRecord Radio RSS/1.0")  # info: set agent
    connect = float(fetch.get("connect_timeout_sec") or 5)  # info: set connect
    read = float(fetch.get("timeout_sec") or 15)  # info: set read
    retries = int(fetch.get("retries") or 3)  # info: set retries
    backoff = float(fetch.get("backoff_sec") or 1)  # info: set backoff
    max_bytes = int(fetch.get("max_bytes") or 2000000)  # info: set max_bytes
    redirects = int(fetch.get("max_redirects") or 5)  # info: set redirects
    started = time.monotonic()  # info: set started
    if not _robots_allow(url, agent, connect):  # info: if not _robots_allow ( url , agent , connect ) :
        return {"ok": True, "skipped": "robots", "status": 0, "body": b"", "etag": etag, "modified": modified, "latency_ms": 0, "error": ""}  # info: return { "ok" : True , "skipped" : "robots" , "status" : 0 , "body" : b"" , "etag" : etag , "modified" : modified , "latency_ms" : 0 , "error" : "" }
    condition = {}  # info: set condition
    if etag:  # info: if etag :
        condition["If-None-Match"] = etag  # info: condition [ "If-None-Match" ] = etag
    if modified:  # info: if modified :
        condition["If-Modified-Since"] = modified  # info: condition [ "If-Modified-Since" ] = modified
    last = {"ok": False, "status": 0, "error": "not_attempted", "body": b"", "headers": {}}  # info: set last
    for attempt in range(max(1, retries)):  # info: for attempt in range ( max ( 1 , retries ) )
        last = _request(url, agent, connect, read, max_bytes, condition, redirects)  # info: set last
        if last.get("ok") or last.get("status") in {304, 404, 410}:  # info: if last . get ( "ok" ) or last . get ( "status" ) in { 304 , 404 , 410 } :
            break  # info: break
        if attempt + 1 < retries:  # info: if attempt + 1 < retries :
            time.sleep(backoff * (2 ** attempt))  # info: time . sleep ( backoff * ( 2 ** attempt ) )
    headers = last.get("headers") or {}  # info: set headers
    last["latency_ms"] = int((time.monotonic() - started) * 1000)  # info: last [ "latency_ms" ] = int ( ( time . monotonic ( ) - started ) * 1000 )
    last["etag"] = headers.get("etag") or etag  # info: last [ "etag" ] = headers . get ( "etag" ) or etag
    last["modified"] = headers.get("last-modified") or modified  # info: last [ "modified" ] = headers . get ( "last-modified" ) or modified
    last["skipped"] = ""  # info: last [ "skipped" ] = ""
    if last.get("status") == 304:  # info: if last . get ( "status" ) == 304 :
        last["ok"] = True  # info: last [ "ok" ] = True
        last["not_modified"] = True  # info: last [ "not_modified" ] = True
    else:  # info: else
        last["not_modified"] = False  # info: last [ "not_modified" ] = False
    if last.get("status") and last.get("status") >= 400:  # info: if last . get ( "status" ) and last . get ( "status" ) >= 400 :
        last["ok"] = False  # info: last [ "ok" ] = False
        last["error"] = last.get("error") or f"http_{last['status']}"  # info: last [ "error" ] = last . get ( "error" ) or f"http_{ last [ 'status' ] }"
    return last  # info: return last
