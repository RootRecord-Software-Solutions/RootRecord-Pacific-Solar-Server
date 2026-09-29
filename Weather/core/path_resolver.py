"""URL -> local path translation. Pure function module: no network, no disk I/O.

Implements the mirror-the-URL rule from nws_plan.md Section 1:

    https://<host>/<path>/<name>.<ext>
    -> <base_dir>/<host>/<path>/<name>/<name>_current.<ext>
    -> <base_dir>/<host>/<path>/<name>/archive/<MM-DD-YYYY>/<name>_<TIMESTAMP>.<ext>

For URLs with no filename in the path, or disambiguated only by a query
string, the resource name is derived the same way the plan specifies: the
last path segment, or the query-string value that distinguishes it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import urlsplit, parse_qsl

from core import hst_time

DEFAULT_EXT = "txt"  # applied when a URL has no extension and isn't a query-string case


@dataclass(frozen=True)
class ResolvedResource:
    host: str
    resource_dir: str        # e.g. "images/hfo/satellite/Hawaii_IR"
    name: str                # e.g. "Hawaii_IR"
    ext: str                 # e.g. "gif" (no leading dot)

    def base_dir_relative(self) -> str:
        """Path relative to base_dir, e.g. 'weather.gov/images/hfo/satellite/Hawaii_IR'."""
        return f"{self.host}/{self.resource_dir}"

    def current_path(self, base_dir: str) -> str:
        return f"{base_dir}/{self.base_dir_relative()}/{self.name}_current.{self.ext}"

    def archive_path(self, base_dir: str, fetched_at: datetime) -> str:
        date_folder = hst_time.hst_date_folder(fetched_at)
        ts = hst_time.hst_archive_timestamp(fetched_at)
        return (
            f"{base_dir}/{self.base_dir_relative()}/archive/"
            f"{date_folder}/{self.name}_{ts}.{self.ext}"
        )

    def archive_dir(self, base_dir: str) -> str:
        return f"{base_dir}/{self.base_dir_relative()}/archive"


def _name_and_ext_from_path(path: PurePosixPath) -> tuple[str, str]:
    stem = path.stem
    suffix = path.suffix.lstrip(".")
    if not stem:
        # e.g. path was "/" or empty
        return "index", suffix or DEFAULT_EXT
    if not suffix:
        # Extensionless path, e.g. /hfo/SFP -- name is the last segment,
        # extension defaults to .txt (these are always text products).
        return stem, DEFAULT_EXT
    return stem, suffix


def resolve(url: str, resource_id_hint: str | None = None) -> ResolvedResource:
    """Resolve a resource's URL to its on-disk name components.

    `resource_id_hint` is used when a query string is what actually
    disambiguates the resource (e.g. `?area=HI`, `?product=AFD&issuedby=HFO`)
    -- the caller (a fetch/ module, which knows the resource's config/
    resources.yaml id) supplies the value that should become the folder/file
    base name, matching nws_plan.md's example:

        https://api.weather.gov/alerts/active?area=HI
        -> hfo/api.weather.gov/alerts/active/area=HI/area=HI_current.json
    """
    parts = urlsplit(url)
    host = parts.netloc or "www.weather.gov"  # relative /hfo/... URLs default to the main host
    if host.startswith("www."):
        # Matches nws_plan.md's own examples, which drop the "www." prefix
        # in the on-disk host folder (e.g. "hfo/weather.gov/images/...").
        host = host[len("www."):]
    path = PurePosixPath(parts.path)

    if parts.query:
        # Use the query string itself as the distinguishing folder/file name,
        # matching the plan's literal "area=HI" example -- unless a hint
        # was supplied (preferred, since it's cleaner and matches the
        # resource's own config id).
        qname = resource_id_hint or parts.query
        resource_dir = f"{str(path).lstrip('/')}/{qname}" if str(path) != "/" else qname
        ext = "json" if "api.weather.gov" in host else "html"
        return ResolvedResource(host=host, resource_dir=resource_dir, name=qname, ext=ext)

    name, ext = _name_and_ext_from_path(path)
    parent = str(path.parent).lstrip("/")
    resource_dir = f"{parent}/{name}" if parent and parent != "." else name
    return ResolvedResource(host=host, resource_dir=resource_dir, name=name, ext=ext)
