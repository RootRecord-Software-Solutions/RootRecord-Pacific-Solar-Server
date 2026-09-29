"""Single HTTP wrapper: enforces per-host rate floor, sets the User-Agent,
handles conditional GET (ETag / If-Modified-Since).

This module never knows what a "resource" is beyond a URL and a rate-limit
floor -- resource identity, tiers, and what-to-do-with-the-body all live in
fetch/. Uses httpx (already a dependency in the old system's scripts).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx
import yaml
from pathlib import Path

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

_last_request_at: dict[str, float] = {}  # host -> monotonic time of last request

# One lock per host, so concurrent fetches to DIFFERENT hosts never wait on
# each other -- only same-host calls serialize behind that host's own floor.
# _locks_meta_lock guards creation of a new per-host Lock the first time a
# given host is seen; after that, all waiting happens on the host's own lock,
# never on _locks_meta_lock itself (per-fetch-module concurrency added
# 2026-09-25 -- a single global sleep was previously serializing every
# resource across every host, turning a ~13min worst-case host queue into
# an ~18-25min whole-pass wait).
_host_locks: dict[str, threading.Lock] = {}
_locks_meta_lock = threading.Lock()


def _lock_for(host: str) -> threading.Lock:
    with _locks_meta_lock:
        lock = _host_locks.get(host)
        if lock is None:
            lock = threading.Lock()
            _host_locks[host] = lock
        return lock


def _load_hosts_config() -> dict[str, Any]:
    with open(_CONFIG_DIR / "hosts.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


_HOSTS_CONFIG = _load_hosts_config()
_DEFAULTS = _HOSTS_CONFIG.get("defaults", {})
_HOST_OVERRIDES = _HOSTS_CONFIG.get("hosts", {})


def _host_settings(host: str) -> dict[str, Any]:
    settings = dict(_DEFAULTS)
    settings.update(_HOST_OVERRIDES.get(host, {}))
    return settings


def _rate_floor_seconds(host: str) -> float:
    return float(_host_settings(host).get("rate_floor_seconds", 10))


def _enforce_rate_floor(host: str) -> None:
    # Held only for this one host's check-sleep-update sequence -- a thread
    # fetching a different host never touches this lock, so it never waits
    # here. A thread fetching the SAME host blocks on this exact section,
    # which is the point: two concurrent requests to api.weather.gov must
    # still be >=30s apart even if they came from two different fetch
    # modules running in parallel.
    with _lock_for(host):
        floor = _rate_floor_seconds(host)
        last = _last_request_at.get(host)
        now = time.monotonic()
        if last is not None:
            elapsed = now - last
            wait = floor - elapsed
            if wait > 0:
                time.sleep(wait)
        _last_request_at[host] = time.monotonic()


@dataclass
class FetchResult:
    status_code: int
    headers: httpx.Headers
    content: bytes | None  # None for a 304 Not Modified
    not_modified: bool


def _headers_for(host: str, accept: str | None,
                  etag: str | None, last_modified: str | None) -> dict[str, str]:
    settings = _host_settings(host)
    headers = {"User-Agent": settings.get("user_agent", _DEFAULTS.get("user_agent", "WeatherSkill/1.0"))}
    accept = accept or settings.get("accept_header")
    if accept:
        headers["Accept"] = accept
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified
    return headers


def get(url: str, *, etag: str | None = None, last_modified: str | None = None,
        accept: str | None = None) -> FetchResult:
    """Conditional GET, respecting the host's rate floor.

    Returns FetchResult with not_modified=True (and content=None) on a 304.
    Raises httpx.HTTPStatusError on 4xx/5xx (caller/scheduler handles backoff
    and increments manifest.record_failure).
    """
    host = urlsplit(url).netloc
    settings = _host_settings(host)
    _enforce_rate_floor(host)

    headers = _headers_for(host, accept, etag, last_modified)
    timeout = float(settings.get("timeout_seconds", 20))

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)

    if resp.status_code == 304:
        return FetchResult(status_code=304, headers=resp.headers, content=None, not_modified=True)

    resp.raise_for_status()
    return FetchResult(status_code=resp.status_code, headers=resp.headers, content=resp.content, not_modified=False)


def head(url: str) -> httpx.Headers:
    """HEAD request, respecting the host's rate floor. Used for the
    Content-Length fallback layer in change_detection.py.
    """
    host = urlsplit(url).netloc
    settings = _host_settings(host)
    _enforce_rate_floor(host)
    headers = _headers_for(host, None, None, None)
    timeout = float(settings.get("timeout_seconds", 20))

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.head(url, headers=headers)
    resp.raise_for_status()
    return resp.headers


def rate_floor_for(url: str) -> float:
    """Exposed for scheduler/tiers.py, which needs to know floors without
    making a request."""
    return _rate_floor_seconds(urlsplit(url).netloc)
