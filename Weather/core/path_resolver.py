# ==============================================================================
# FILE: Weather/core/path_resolver.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""URL -> local path translation. Pure function module: no network, no disk I/O.

Implements the mirror-the-URL rule from nws_plan.md Section 1:

    https://<host>/<path>/<name>.<ext>
    -> <base_dir>/<host>/<path>/<name>/<name>_current.<ext>
    -> <base_dir>/<host>/<path>/<name>/archive/<MM-DD-YYYY>/<name>_<TIMESTAMP>.<ext>

For URLs with no filename in the path, or disambiguated only by a query
string, the resource name is derived the same way the plan specifies: the
last path segment, or the query-string value that distinguishes it.
"""
from __future__ import annotations  # info: from __future__ import annotations

from dataclasses import dataclass  # info: from dataclasses import dataclass
from datetime import datetime  # info: from datetime import datetime
from pathlib import PurePosixPath  # info: from pathlib import PurePosixPath
from urllib.parse import urlsplit, parse_qsl  # info: from urllib . parse import urlsplit , parse_qsl

from core import hst_time  # info: from core import hst_time

DEFAULT_EXT = "txt"  # applied when a URL has no extension and isn't a query-string case


# ====================================================
# SECTION: class ResolvedResource
# What it does: ResolvedResource.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass(frozen=True)  # info: decorator dataclass ( frozen
class ResolvedResource:  # info: class ResolvedResource
    host: str  # info: set host
    resource_dir: str        # e.g. "images/hfo/satellite/Hawaii_IR"
    name: str                # e.g. "Hawaii_IR"
    ext: str                 # e.g. "gif" (no leading dot)

    def base_dir_relative(self) -> str:  # info: def base_dir_relative
        """Path relative to base_dir, e.g. 'weather.gov/images/hfo/satellite/Hawaii_IR'."""  # info: """Path relative to base_dir, e.g. 'weather.gov/images/hfo/satellite/Hawaii_IR'."""
        return f"{self.host}/{self.resource_dir}"  # info: return f" { self . host } /

    def current_path(self, base_dir: str) -> str:  # info: def current_path
        return f"{base_dir}/{self.base_dir_relative()}/{self.name}_current.{self.ext}"  # info: return f" { base_dir } / { self

    def archive_path(self, base_dir: str, fetched_at: datetime) -> str:  # info: def archive_path
        date_folder = hst_time.hst_date_folder(fetched_at)  # info: set date_folder
        ts = hst_time.hst_archive_timestamp(fetched_at)  # info: set ts
        return (  # info: return (
            f"{base_dir}/{self.base_dir_relative()}/archive/"  # info: f" { base_dir } / { self .
            f"{date_folder}/{self.name}_{ts}.{self.ext}"  # info: f" { date_folder } / { self .
        )  # info: )

    def archive_dir(self, base_dir: str) -> str:  # info: def archive_dir
        return f"{base_dir}/{self.base_dir_relative()}/archive"  # info: return f" { base_dir } / { self


# ====================================================
# SECTION: function _name_and_ext_from_path
# What it does:  name and ext from path.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _name_and_ext_from_path(path: PurePosixPath) -> tuple[str, str]:  # info: def _name_and_ext_from_path
    stem = path.stem  # info: set stem
    suffix = path.suffix.lstrip(".")  # info: set suffix
    if not stem:  # info: if not stem :
        # e.g. path was "/" or empty
        return "index", suffix or DEFAULT_EXT  # info: return "index" , suffix or DEFAULT_EXT
    if not suffix:  # info: if not suffix :
        # Extensionless path, e.g. /hfo/SFP -- name is the last segment,
        # extension defaults to .txt (these are always text products).
        return stem, DEFAULT_EXT  # info: return stem , DEFAULT_EXT
    return stem, suffix  # info: return stem , suffix


# ====================================================
# SECTION: function resolve
# What it does: Resolve a resource's URL to its on-disk name components. `resource_id_hint` is used when a query string is what actually disambiguates the resource (e.g. `?area=HI`, `?product=AFD&
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def resolve(url: str, resource_id_hint: str | None = None) -> ResolvedResource:  # info: def resolve
    """Resolve a resource's URL to its on-disk name components.

    `resource_id_hint` is used when a query string is what actually
    disambiguates the resource (e.g. `?area=HI`, `?product=AFD&issuedby=HFO`)
    -- the caller (a fetch/ module, which knows the resource's config/
    resources.yaml id) supplies the value that should become the folder/file
    base name, matching nws_plan.md's example:

        https://api.weather.gov/alerts/active?area=HI
        -> hfo/api.weather.gov/alerts/active/area=HI/area=HI_current.json
    """
    parts = urlsplit(url)  # info: set parts
    host = parts.netloc or "www.weather.gov"  # relative /hfo/... URLs default to the main host
    if host.startswith("www."):  # info: if host . startswith ( "www." ) :
        # Matches nws_plan.md's own examples, which drop the "www." prefix
        # in the on-disk host folder (e.g. "hfo/weather.gov/images/...").
        host = host[len("www."):]  # info: set host
    path = PurePosixPath(parts.path)  # info: set path

    if parts.query:  # info: if parts . query :
        # Use the query string itself as the distinguishing folder/file name,
        # matching the plan's literal "area=HI" example -- unless a hint
        # was supplied (preferred, since it's cleaner and matches the
        # resource's own config id).
        qname = resource_id_hint or parts.query  # info: set qname
        resource_dir = f"{str(path).lstrip('/')}/{qname}" if str(path) != "/" else qname  # info: set resource_dir
        ext = "json" if "api.weather.gov" in host else "html"  # info: set ext
        return ResolvedResource(host=host, resource_dir=resource_dir, name=qname, ext=ext)  # info: return ResolvedResource ( host = host , resource_dir

    name, ext = _name_and_ext_from_path(path)  # info: name , ext = _name_and_ext_from_path ( path )
    parent = str(path.parent).lstrip("/")  # info: set parent
    resource_dir = f"{parent}/{name}" if parent and parent != "." else name  # info: set resource_dir
    return ResolvedResource(host=host, resource_dir=resource_dir, name=name, ext=ext)  # info: return ResolvedResource ( host = host , resource_dir
