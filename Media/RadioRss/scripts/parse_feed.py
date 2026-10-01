# ==============================================================================
# FILE: Media/RadioRss/scripts/parse_feed.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Parse RSS 2.0 and Atom into plain item dicts. Refuses XML with a doctype."""
from __future__ import annotations  # info: from __future__ import annotations

import xml.etree.ElementTree as ET  # info: import xml . etree . ElementTree as ET
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from email.utils import parsedate_to_datetime  # info: from email . utils import parsedate_to_datetime

from common import plain  # info: from common import plain


# ====================================================
# SECTION: function _local
# What it does: Strip an XML namespace from a tag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _local(tag: str) -> str:  # info: def _local
    if tag.startswith("{"):  # info: if tag . startswith ( "{" ) :
        return tag.split("}", 1)[1]  # info: return tag . split ( "}" , 1 ) [ 1 ]
    return tag  # info: return tag


# ====================================================
# SECTION: function _child
# What it does: Return the text of the first child with this local name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _child(node: ET.Element, name: str) -> str:  # info: def _child
    for child in list(node):  # info: for child in list ( node )
        if _local(child.tag) == name:  # info: if _local ( child . tag ) == name :
            return plain("".join(child.itertext()), 4000)  # info: return plain ( "" . join ( child . itertext ( ) ) , 4000 )
    return ""  # info: return ""


# ====================================================
# SECTION: function _when
# What it does: Parse an RSS or Atom date into UTC ISO-8601. Unknown dates stay empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _when(value: str) -> str:  # info: def _when
    text = (value or "").strip()  # info: set text
    if not text:  # info: if not text :
        return ""  # info: return ""
    try:  # info: try
        parsed = parsedate_to_datetime(text)  # info: set parsed
    except (TypeError, ValueError, IndexError, OverflowError):  # info: except ( TypeError , ValueError , IndexError , OverflowError )
        parsed = None  # info: set parsed
    if parsed is None:  # info: if parsed is None :
        try:  # info: try
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))  # info: set parsed
        except ValueError:  # info: except ValueError
            return ""  # info: return ""
    if parsed.tzinfo is None:  # info: if parsed . tzinfo is None :
        parsed = parsed.replace(tzinfo=timezone.utc)  # info: set parsed
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # info: return parsed . astimezone ( timezone . utc ) . strftime ( "%Y-%m-%dT%H:%M:%SZ" )


# ====================================================
# SECTION: function _link
# What it does: Read an RSS link or the Atom alternate link.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _link(node: ET.Element) -> str:  # info: def _link
    plain_link = _child(node, "link")  # info: set plain_link
    if plain_link.startswith("http"):  # info: if plain_link . startswith ( "http" ) :
        return plain_link.split()[0]  # info: return plain_link . split ( ) [ 0 ]
    alternate = ""  # info: set alternate
    for child in list(node):  # info: for child in list ( node )
        if _local(child.tag) != "link":  # info: if _local ( child . tag ) != "link" :
            continue  # info: continue
        href = (child.attrib.get("href") or "").strip()  # info: set href
        rel = (child.attrib.get("rel") or "alternate").strip()  # info: set rel
        if href and rel == "alternate":  # info: if href and rel == "alternate" :
            return href  # info: return href
        if href and not alternate:  # info: if href and not alternate :
            alternate = href  # info: set alternate
    return alternate  # info: return alternate


# ====================================================
# SECTION: function _author
# What it does: Read an author name from RSS or Atom.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _author(node: ET.Element) -> str:  # info: def _author
    direct = _child(node, "author") or _child(node, "creator")  # info: set direct
    if direct:  # info: if direct :
        return direct[:200]  # info: return direct [ : 200 ]
    for child in list(node):  # info: for child in list ( node )
        if _local(child.tag) == "author":  # info: if _local ( child . tag ) == "author" :
            name = _child(child, "name")  # info: set name
            if name:  # info: if name :
                return name[:200]  # info: return name [ : 200 ]
    return ""  # info: return ""


# ====================================================
# SECTION: function parse_document
# What it does: Parse RSS or Atom bytes into a list of items. A bad document raises ValueError.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_document(body: bytes) -> list[dict]:  # info: def parse_document
    head = body[:800].lstrip().lower()  # info: set head
    if b"<!doctype" in head or b"<!entity" in body[:4000].lower():  # info: if b"<!doctype" in head or b"<!entity" in body [ : 4000 ] . lower ( ) :
        raise ValueError("refused_doctype")  # info: raise ValueError ( "refused_doctype" )
    try:  # info: try
        root = ET.fromstring(body)  # info: set root
    except ET.ParseError as exc:  # info: except ET . ParseError as exc
        raise ValueError("parse_error") from exc  # info: raise ValueError ( "parse_error" ) from exc
    kind = _local(root.tag)  # info: set kind
    nodes = []  # info: set nodes
    if kind == "rss" or kind == "RDF":  # info: if kind == "rss" or kind == "RDF" :
        for child in root.iter():  # info: for child in root . iter ( )
            if _local(child.tag) == "item":  # info: if _local ( child . tag ) == "item" :
                nodes.append(child)  # info: nodes . append ( child )
    elif kind == "feed":  # info: elif kind == "feed" :
        for child in list(root):  # info: for child in list ( root )
            if _local(child.tag) == "entry":  # info: if _local ( child . tag ) == "entry" :
                nodes.append(child)  # info: nodes . append ( child )
    else:  # info: else
        raise ValueError("not_a_feed")  # info: raise ValueError ( "not_a_feed" )
    items = []  # info: set items
    for node in nodes:  # info: for node in nodes
        title = _child(node, "title")  # info: set title
        summary = _child(node, "description") or _child(node, "summary") or _child(node, "content")  # info: set summary
        published = _when(_child(node, "pubDate") or _child(node, "published") or _child(node, "date") or _child(node, "updated"))  # info: set published
        updated = _when(_child(node, "updated") or _child(node, "modified")) or published  # info: set updated
        guid = _child(node, "guid") or _child(node, "id")  # info: set guid
        items.append({  # info: items . append ( {
            "title": title,  # info: "title" : title ,
            "summary": summary,  # info: "summary" : summary ,
            "url": _link(node),  # info: "url" : _link ( node ) ,
            "published_at": published,  # info: "published_at" : published ,
            "updated_at": updated,  # info: "updated_at" : updated ,
            "author": _author(node),  # info: "author" : _author ( node ) ,
            "guid": guid[:500],  # info: "guid" : guid [ : 500 ] ,
        })  # info: } )
    return items  # info: return items
