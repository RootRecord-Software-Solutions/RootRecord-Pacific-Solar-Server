# ==============================================================================
# FILE: Weather/core/http_client.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Single HTTP wrapper: enforces per-host rate floor, sets the User-Agent,
handles conditional GET (ETag / If-Modified-Since).

This module never knows what a "resource" is beyond a URL and a rate-limit
floor -- resource identity, tiers, and what-to-do-with-the-body all live in
fetch/. Uses httpx (already a dependency in the old system's scripts).
"""
from __future__ import annotations  # info: from __future__ import annotations

import threading  # info: import threading
import time  # info: import time
from dataclasses import dataclass  # info: from dataclasses import dataclass
from typing import Any  # info: from typing import Any
from urllib.parse import urlsplit  # info: from urllib . parse import urlsplit

import httpx  # info: import httpx
import yaml  # info: import yaml
from pathlib import Path  # info: from pathlib import Path

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"  # info: set _CONFIG_DIR

_last_request_at: dict[str, float] = {}  # host -> monotonic time of last request

# One lock per host, so concurrent fetches to DIFFERENT hosts never wait on
# each other -- only same-host calls serialize behind that host's own floor.
# _locks_meta_lock guards creation of a new per-host Lock the first time a
# given host is seen; after that, all waiting happens on the host's own lock,
# never on _locks_meta_lock itself (per-fetch-module concurrency added
# 2026-09-25 -- a single global sleep was previously serializing every
# resource across every host, turning a ~13min worst-case host queue into
# an ~18-25min whole-pass wait).
_host_locks: dict[str, threading.Lock] = {}  # info: set _host_locks
_locks_meta_lock = threading.Lock()  # info: set _locks_meta_lock


# ====================================================
# SECTION: function _lock_for
# What it does:  lock for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _lock_for(host: str) -> threading.Lock:  # info: def _lock_for
    with _locks_meta_lock:  # info: with _locks_meta_lock :
        lock = _host_locks.get(host)  # info: set lock
        if lock is None:  # info: if lock is None :
            lock = threading.Lock()  # info: set lock
            _host_locks[host] = lock  # info: _host_locks [ host ] = lock
        return lock  # info: return lock


# ====================================================
# SECTION: function _load_hosts_config
# What it does:  load hosts config.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_hosts_config() -> dict[str, Any]:  # info: def _load_hosts_config
    with open(_CONFIG_DIR / "hosts.yaml", encoding="utf-8") as f:  # info: with open ( _CONFIG_DIR / "hosts.yaml" , encoding
        return yaml.safe_load(f)  # info: return yaml . safe_load ( f )


_HOSTS_CONFIG = _load_hosts_config()  # info: set _HOSTS_CONFIG
_DEFAULTS = _HOSTS_CONFIG.get("defaults", {})  # info: set _DEFAULTS
_HOST_OVERRIDES = _HOSTS_CONFIG.get("hosts", {})  # info: set _HOST_OVERRIDES


# ====================================================
# SECTION: function _host_settings
# What it does:  host settings.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _host_settings(host: str) -> dict[str, Any]:  # info: def _host_settings
    settings = dict(_DEFAULTS)  # info: set settings
    settings.update(_HOST_OVERRIDES.get(host, {}))  # info: settings . update ( _HOST_OVERRIDES . get (
    return settings  # info: return settings


# ====================================================
# SECTION: function _rate_floor_seconds
# What it does:  rate floor seconds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _rate_floor_seconds(host: str) -> float:  # info: def _rate_floor_seconds
    return float(_host_settings(host).get("rate_floor_seconds", 10))  # info: return float ( _host_settings ( host ) .


# ====================================================
# SECTION: function _enforce_rate_floor
# What it does:  enforce rate floor.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _enforce_rate_floor(host: str) -> None:  # info: def _enforce_rate_floor
    # Held only for this one host's check-sleep-update sequence -- a thread
    # fetching a different host never touches this lock, so it never waits
    # here. A thread fetching the SAME host blocks on this exact section,
    # which is the point: two concurrent requests to api.weather.gov must
    # still be >=30s apart even if they came from two different fetch
    # modules running in parallel.
    with _lock_for(host):  # info: with _lock_for ( host ) :
        floor = _rate_floor_seconds(host)  # info: set floor
        last = _last_request_at.get(host)  # info: set last
        now = time.monotonic()  # info: set now
        if last is not None:  # info: if last is not None :
            elapsed = now - last  # info: set elapsed
            wait = floor - elapsed  # info: set wait
            if wait > 0:  # info: if wait > 0 :
                time.sleep(wait)  # info: time . sleep ( wait )
        _last_request_at[host] = time.monotonic()  # info: _last_request_at [ host ] = time . monotonic


# ====================================================
# SECTION: class FetchResult
# What it does: FetchResult.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class FetchResult:  # info: class FetchResult
    status_code: int  # info: set status_code
    headers: httpx.Headers  # info: set headers
    content: bytes | None  # None for a 304 Not Modified
    not_modified: bool  # info: set not_modified


# ====================================================
# SECTION: function _is_waf_challenge
# What it does:  is waf challenge.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_waf_challenge(content: bytes | None) -> bool:  # info: def _is_waf_challenge
    if not content:  # info: if not content :
        return False  # info: return False
    head = content[:6000].lower()  # info: set head
    return b"gokuprops" in head or b"awswafcookiedomainlist" in head  # info: return b"gokuprops" in head or b"awswafcookiedomainlist" in head


# ====================================================
# SECTION: function _headers_for
# What it does:  headers for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _headers_for(host: str, accept: str | None,  # info: def _headers_for
                  etag: str | None, last_modified: str | None) -> dict[str, str]:  # info: set etag
    settings = _host_settings(host)  # info: set settings
    headers = {"User-Agent": settings.get("user_agent", _DEFAULTS.get("user_agent", "WeatherSkill/1.0"))}  # info: set headers
    accept = accept or settings.get("accept_header")  # info: set accept
    if accept:  # info: if accept :
        headers["Accept"] = accept  # info: headers [ "Accept" ] = accept
    if etag:  # info: if etag :
        headers["If-None-Match"] = etag  # info: headers [ "If-None-Match" ] = etag
    if last_modified:  # info: if last_modified :
        headers["If-Modified-Since"] = last_modified  # info: headers [ "If-Modified-Since" ] = last_modified
    return headers  # info: return headers


# ====================================================
# SECTION: function get
# What it does: Conditional GET, respecting the host's rate floor. Returns FetchResult with not_modified=True (and content=None) on a 304. Retries 502/503/504 up to the host max_retries. Raises ht
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def get(url: str, *, etag: str | None = None, last_modified: str | None = None,  # info: def get
        accept: str | None = None) -> FetchResult:  # info: set accept
    """Conditional GET, respecting the host's rate floor.

    Returns FetchResult with not_modified=True (and content=None) on a 304.
    Retries 502/503/504 up to the host max_retries. Raises httpx.HTTPStatusError
    on a remaining 4xx/5xx.
    """
    host = urlsplit(url).netloc  # info: set host
    settings = _host_settings(host)  # info: set settings
    _enforce_rate_floor(host)  # info: call _enforce_rate_floor

    headers = _headers_for(host, accept, etag, last_modified)  # info: set headers
    timeout = float(settings.get("timeout_seconds", 20))  # info: set timeout
    extra_tries = max(0, int(settings.get("max_retries", 0)))  # info: set extra_tries
    backoff = float(settings.get("backoff_base_seconds", 5))  # info: set backoff

    resp = None  # info: set resp
    for attempt in range(extra_tries + 1):  # info: for attempt in range ( extra_tries + 1
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:  # info: with httpx . Client ( timeout = timeout
            resp = client.get(url, headers=headers)  # info: set resp
        waf = host == "www.noaa.gov" and _is_waf_challenge(resp.content)  # info: set waf
        if (resp.status_code in {502, 503, 504} or waf) and attempt < extra_tries:  # info: if ( resp . status_code in { 502
            time.sleep(min(backoff, 5.0))  # info: time . sleep ( min ( backoff ,
            continue  # info: continue
        if waf:  # info: if waf :
            raise RuntimeError("NOAA homepage returned a bot-check page instead of the site")  # info: raise RuntimeError ( "NOAA homepage returned a bot-check page instead of the site" )
        break  # info: break

    if resp is None:  # info: if resp is None :
        raise RuntimeError(f"no response for {url}")  # info: raise RuntimeError ( f" no response for { url }

    if resp.status_code == 304:  # info: if resp . status_code == 304 :
        return FetchResult(status_code=304, headers=resp.headers, content=None, not_modified=True)  # info: return FetchResult ( status_code = 304 , headers

    resp.raise_for_status()  # info: resp . raise_for_status ( )
    return FetchResult(status_code=resp.status_code, headers=resp.headers, content=resp.content, not_modified=False)  # info: return FetchResult ( status_code = resp . status_code


# ====================================================
# SECTION: function head
# What it does: HEAD request, respecting the host's rate floor. Used for the Content-Length fallback layer in change_detection.py.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def head(url: str) -> httpx.Headers:  # info: def head
    """HEAD request, respecting the host's rate floor. Used for the
    Content-Length fallback layer in change_detection.py.
    """
    host = urlsplit(url).netloc  # info: set host
    settings = _host_settings(host)  # info: set settings
    _enforce_rate_floor(host)  # info: call _enforce_rate_floor
    headers = _headers_for(host, None, None, None)  # info: set headers
    timeout = float(settings.get("timeout_seconds", 20))  # info: set timeout

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:  # info: with httpx . Client ( timeout = timeout
        resp = client.head(url, headers=headers)  # info: set resp
    resp.raise_for_status()  # info: resp . raise_for_status ( )
    return resp.headers  # info: return resp . headers


# ====================================================
# SECTION: function rate_floor_for
# What it does: Exposed for scheduler/tiers.py, which needs to know floors without making a request.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def rate_floor_for(url: str) -> float:  # info: def rate_floor_for
    """Exposed for scheduler/tiers.py, which needs to know floors without
    making a request."""
    return _rate_floor_seconds(urlsplit(url).netloc)  # info: return _rate_floor_seconds ( urlsplit ( url ) .
