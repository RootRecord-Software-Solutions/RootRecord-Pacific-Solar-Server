"""rr_config_io.py — comment-preserving read/edit/save for RootRecord config files (Control Panel settings pages).

INFO — MUST HAVE (future agents), added 2026-09-29 (control-panel-settings pass):
- NEVER print, log or return a secret VALUE to UI text. Use mask()/describe() -> "set (len N)" / "empty".
- Every save: re-read the file, apply edits, validate by type, build a MASKED diff (caller shows it + confirm),
  then backup (same mode; 0600 for secret files) -> temp file in the same dir -> fsync -> os.replace.
  Aborts if the file changed between the read the diff was built from and the write.
- Nothing here restarts anything. Callers show "takes effect after <service> restart".
- Formats: env/key=value (shell style), ini (incl. systemd units + Environment=K=V), json (key order + indent kept),
  yaml (line-based scalar edits, comments kept), tsv tables (column edits), raw single-value secret files.
"""
from __future__ import annotations  # info: from __future__ import annotations

import difflib  # info: import difflib
import hashlib  # info: import hashlib
import io  # info: import io
import json  # info: import json
import os  # info: import os
import re  # info: import re
import shutil  # info: import shutil
import stat  # info: import stat
import tempfile  # info: import tempfile
import time  # info: import time
from dataclasses import dataclass, field  # info: from dataclasses import dataclass , field
from pathlib import Path  # info: from pathlib import Path
from urllib.parse import urlparse  # info: from urllib . parse import urlparse

SECRET_TOKENS = {"TOKEN", "TOKENS", "KEY", "KEYS", "SECRET", "SECRETS", "PASS", "PASSWORD", "PASSWD", "PAT", "WEBHOOK",  # info: set SECRET_TOKENS
                 "WEBHOOKS", "AUTH", "COOKIE", "COOKIES", "APIKEY", "CREDENTIAL", "CREDENTIALS", "PRIVATE", "ACCESS"}  # info: "WEBHOOKS" , "AUTH" , "COOKIE" , "COOKIES" ,
SECRET_SUFFIXES = ("TOKEN", "SECRET", "PASSWORD", "APIKEY", "WEBHOOK", "COOKIE")  # info: set SECRET_SUFFIXES
BACKUP_ROOT = Path(os.environ.get("RR_CP_BACKUP_ROOT", "/home/rootrecord/Database/GITHUB/control-panel-settings-backups"))  # info: set BACKUP_ROOT


# ====================================================
# SECTION: function is_secret_key
# What it does: is secret key.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_secret_key(key: str) -> bool:  # info: def is_secret_key
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", key.upper()) if p]  # info: set parts
    return any(p in SECRET_TOKENS or p.endswith(SECRET_SUFFIXES) for p in parts)  # info: return any ( p in SECRET_TOKENS or p


# ====================================================
# SECTION: function describe
# What it does: Masked description of a secret value. Never contains the value.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def describe(value) -> str:  # info: def describe
    """Masked description of a secret value. Never contains the value."""  # info: """Masked description of a secret value. Never contains the value."""
    if value is None:  # info: if value is None :
        return "not set"  # info: return "not set"
    s = str(value)  # info: set s
    return "empty" if s == "" else f"set (len {len(s)})"  # info: return "empty" if s == "" else f"


# ------------------------------------------------------------------ validation
# ====================================================
# SECTION: function validate
# What it does: Return (ok, normalized_text_or_error). raw is the user's text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def validate(kind: str, raw: str):  # info: def validate
    """Return (ok, normalized_text_or_error). raw is the user's text."""  # info: """Return (ok, normalized_text_or_error). raw is the user's text."""
    if "\n" in raw or "\r" in raw or "\0" in raw:  # info: if "\n" in raw or "\r" in raw
        return False, "newlines / NUL are not allowed"  # info: return False , "newlines / NUL are not allowed"
    k = kind or "str"  # info: set k
    if k == "port":  # info: if k == "port" :
        if not re.fullmatch(r"\d{1,5}", raw.strip()) or not (1 <= int(raw) <= 65535):  # info: if not re . fullmatch ( r"\d{1,5}" ,
            return False, "port must be an integer 1–65535"  # info: return False , "port must be an integer 1–65535"
        return True, str(int(raw))  # info: return True , str ( int ( raw
    if k == "bool01":  # info: if k == "bool01" :
        if raw.strip() not in ("0", "1"):  # info: if raw . strip ( ) not in
            return False, "boolean must be 0 or 1"  # info: return False , "boolean must be 0 or 1"
        return True, raw.strip()  # info: return True , raw . strip ( )
    if k == "bool":  # info: if k == "bool" :
        if raw.strip().lower() not in ("true", "false"):  # info: if raw . strip ( ) . lower
            return False, "boolean must be true or false"  # info: return False , "boolean must be true or false"
        return True, raw.strip().lower()  # info: return True , raw . strip ( )
    if k == "int":  # info: if k == "int" :
        if not re.fullmatch(r"-?\d+", raw.strip()):  # info: if not re . fullmatch ( r"-?\d+" ,
            return False, "must be an integer"  # info: return False , "must be an integer"
        return True, raw.strip()  # info: return True , raw . strip ( )
    if k == "float":  # info: if k == "float" :
        try:  # info: try :
            float(raw)  # info: call float
        except ValueError:  # info: except ValueError :
            return False, "must be a number"  # info: return False , "must be a number"
        return True, raw.strip()  # info: return True , raw . strip ( )
    if k == "url":  # info: if k == "url" :
        u = urlparse(raw.strip())  # info: set u
        if u.scheme not in ("http", "https", "rtsp", "ws", "wss", "tcp") or not u.netloc:  # info: if u . scheme not in ( "http"
            return False, "URL must be http(s)/rtsp/ws(s)/tcp with a host"  # info: return False , "URL must be http(s)/rtsp/ws(s)/tcp with a host"
        try:  # info: try :
            _ = u.port  # info: set _
        except ValueError:  # info: except ValueError :
            return False, "URL port is invalid"  # info: return False , "URL port is invalid"
        return True, raw.strip()  # info: return True , raw . strip ( )
    if k == "host":  # info: if k == "host" :
        if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", raw.strip()):  # info: if not re . fullmatch ( r"[A-Za-z0-9.-]{1,253}" ,
            return False, "hostname / IP expected"  # info: return False , "hostname / IP expected"
        return True, raw.strip()  # info: return True , raw . strip ( )
    return True, raw  # info: return True , raw


# ------------------------------------------------------------------ parse/edit per format
# ====================================================
# SECTION: class Entry
# What it does: Entry.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class Entry:  # info: class Entry
    key: str            # dotted path / key name
    value: object       # python value (str for text formats)
    line: int | None = None  # info: set line
    section: str = ""  # info: set section
    dup: bool = False   # key occurs more than once -> edits refused (ambiguous)
    extra: dict = field(default_factory=dict)  # info: set extra


_ENV_RX = re.compile(r"^(?P<pre>\s*(?:export\s+)?)(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P<eq>\s*=\s*)(?P<val>.*?)(?P<post>\s*)$")  # info: set _ENV_RX


# ====================================================
# SECTION: function _unquote
# What it does:  unquote.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _unquote(v: str):  # info: def _unquote
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":  # info: if len ( v ) >= 2 and
        return v[1:-1], v[0]  # info: return v [ 1 : - 1 ]
    return v, ""  # info: return v , ""


# ====================================================
# SECTION: function parse_env
# What it does: parse env.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_env(text: str) -> list[Entry]:  # info: def parse_env
    out, seen = [], {}  # info: out , seen = [ ] , {
    for i, l in enumerate(text.splitlines()):  # info: for i , l in enumerate ( text
        if l.lstrip().startswith("#"):
            continue  # info: continue
        m = _ENV_RX.match(l)  # info: set m
        if m:  # info: if m :
            v, _q = _unquote(m.group("val"))  # info: v , _q = _unquote ( m .
            e = Entry(m.group("key"), v, i)  # info: set e
            if e.key in seen:  # info: if e . key in seen :
                e.dup = True  # info: e . dup = True
                seen[e.key].dup = True  # info: seen [ e . key ] . dup
            seen[e.key] = e  # info: seen [ e . key ] = e
            out.append(e)  # info: out . append ( e )
    return out  # info: return out


# ====================================================
# SECTION: function edit_env
# What it does: edit env.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def edit_env(text: str, key: str, new: str) -> str:  # info: def edit_env
    lines = text.splitlines(keepends=True)  # info: set lines
    hits = [i for i, l in enumerate(lines) if not l.lstrip().startswith("#") and (m := _ENV_RX.match(l.rstrip("\r\n"))) and m.group("key") == key]
    if len(hits) != 1:  # info: if len ( hits ) != 1 :
        raise ValueError(f"{key}: {'not found' if not hits else 'defined more than once — edit refused (ambiguous)'}")  # info: raise ValueError ( f" { key } :
    i = hits[0]  # info: set i
    raw = lines[i]  # info: set raw
    nl = raw[len(raw.rstrip("\r\n")):]  # info: set nl
    m = _ENV_RX.match(raw.rstrip("\r\n"))  # info: set m
    _v, q = _unquote(m.group("val"))  # info: _v , q = _unquote ( m .
    if q == "" and re.search(r"[\s#;&|$`\"'\\]", new) and " " not in _v:
        q = '"'  # info: set q
    if q and q in new:  # info: if q and q in new :
        raise ValueError(f"{key}: value may not contain the {q} quote character")  # info: raise ValueError ( f" { key } : value may not contain the
    lines[i] = f"{m.group('pre')}{key}{m.group('eq')}{q}{new}{q}{m.group('post')}{nl}"  # info: lines [ i ] = f" { m
    return "".join(lines)  # info: return "" . join ( lines )


_SEC_RX = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s*$")  # info: set _SEC_RX
_INI_RX = re.compile(r"^(?P<pre>\s*)(?P<key>[A-Za-z0-9_.\-]+)(?P<eq>\s*=\s*)(?P<val>.*?)(?P<post>\s*)$")  # info: set _INI_RX
_SYSD_ENV_RX = re.compile(r'^(?P<pre>\s*Environment=)(?P<q>"?)(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<val>[^"]*)(?P=q)(?P<post>\s*)$')  # info: set _SYSD_ENV_RX


# ====================================================
# SECTION: function parse_ini
# What it does: parse ini.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_ini(text: str) -> list[Entry]:  # info: def parse_ini
    out, sec, seen = [], "", {}  # info: out , sec , seen = [ ]
    for i, l in enumerate(text.splitlines()):  # info: for i , l in enumerate ( text
        s = l.strip()  # info: set s
        if not s or s[0] in "#;":
            continue  # info: continue
        m = _SEC_RX.match(l)  # info: set m
        if m:  # info: if m :
            sec = m.group("name").strip()  # info: set sec
            continue  # info: continue
        me = _SYSD_ENV_RX.match(l)  # info: set me
        if me:  # info: if me :
            key = f"{sec}.Environment.{me.group('key')}"  # info: set key
            e = Entry(key, me.group("val"), i, sec)  # info: set e
        else:  # info: else :
            m = _INI_RX.match(l)  # info: set m
            if not m:  # info: if not m :
                continue  # info: continue
            key = f"{sec}.{m.group('key')}" if sec else m.group("key")  # info: set key
            e = Entry(key, m.group("val"), i, sec)  # info: set e
        if key in seen:  # info: if key in seen :
            e.dup = seen[key].dup = True  # info: e . dup = seen [ key ]
        seen[key] = e  # info: seen [ key ] = e
        out.append(e)  # info: out . append ( e )
    return out  # info: return out


# ====================================================
# SECTION: function edit_ini
# What it does: edit ini.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def edit_ini(text: str, key: str, new: str, create: bool = False) -> str:  # info: def edit_ini
    lines = text.splitlines(keepends=True)  # info: set lines
    ents = [e for e in parse_ini(text) if e.key == key]  # info: set ents
    if len(ents) > 1:  # info: if len ( ents ) > 1 :
        raise ValueError(f"{key}: defined more than once — edit refused (ambiguous)")  # info: raise ValueError ( f" { key } : defined more than once — edit refused (ambiguous)
    if not ents:  # info: if not ents :
        if not create:  # info: if not create :
            raise ValueError(f"{key}: not found")  # info: raise ValueError ( f" { key } : not found
        sec, _, rest = key.partition(".")  # info: sec , _ , rest = key .
        env = rest.startswith("Environment.")  # info: set env
        newline = f"Environment={rest.split('.', 1)[1]}={new}\n" if env else f"{rest} = {new}\n"  # info: set newline
        # append at end of the section (or create it)
        cur, last = "", None  # info: cur , last = "" , None
        for i, l in enumerate(lines):  # info: for i , l in enumerate ( lines
            m = _SEC_RX.match(l.rstrip("\r\n"))  # info: set m
            if m:  # info: if m :
                cur = m.group("name").strip()  # info: set cur
            if cur == sec and l.strip():  # info: if cur == sec and l . strip
                last = i  # info: set last
        if last is None:  # info: if last is None :
            if lines and not lines[-1].endswith("\n"):  # info: if lines and not lines [ - 1
                lines[-1] += "\n"  # info: lines [ - 1 ] += "\n"
            lines += ([] if not lines else ["\n"]) + [f"[{sec}]\n", newline]  # info: set lines
        else:  # info: else :
            lines.insert(last + 1, newline)  # info: lines . insert ( last + 1 ,
        return "".join(lines)  # info: return "" . join ( lines )
    e = ents[0]  # info: set e
    raw = lines[e.line]  # info: set raw
    nl = raw[len(raw.rstrip("\r\n")):]  # info: set nl
    body = raw.rstrip("\r\n")  # info: set body
    me = _SYSD_ENV_RX.match(body)  # info: set me
    if me:  # info: if me :
        q = me.group("q") or ('"' if re.search(r"\s", new) else "")  # info: set q
        if '"' in new:  # info: if '"' in new :
            raise ValueError("value may not contain a double quote")  # info: raise ValueError ( "value may not contain a double quote" )
        lines[e.line] = f"{me.group('pre')}{q}{me.group('key')}={new}{q}{me.group('post')}{nl}"  # info: lines [ e . line ] = f"
    else:  # info: else :
        m = _INI_RX.match(body)  # info: set m
        lines[e.line] = f"{m.group('pre')}{m.group('key')}{m.group('eq')}{new}{m.group('post')}{nl}"  # info: lines [ e . line ] = f"
    return "".join(lines)  # info: return "" . join ( lines )


# ====================================================
# SECTION: function parse_json
# What it does: parse json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_json(text: str) -> list[Entry]:  # info: def parse_json
    data = json.loads(text)  # info: set data
    out = []  # info: set out

    def walk(o, pre):  # info: def walk
        if isinstance(o, dict):  # info: if isinstance ( o , dict ) :
            for k, v in o.items():  # info: for k , v in o . items
                p = f"{pre}.{k}" if pre else str(k)  # info: set p
                if isinstance(v, dict) and v:  # info: if isinstance ( v , dict ) and
                    walk(v, p)  # info: call walk
                else:  # info: else :
                    out.append(Entry(p, v))  # info: out . append ( Entry ( p ,
    walk(data, "")  # info: call walk
    return out  # info: return out


# ====================================================
# SECTION: function _json_indent
# What it does:  json indent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _json_indent(text: str):  # info: def _json_indent
    m = re.search(r"\n([ \t]+)\"", text)  # info: set m
    return m.group(1) if m else None  # info: return m . group ( 1 ) if


# ====================================================
# SECTION: function edit_json
# What it does: edit json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def edit_json(text: str, key: str, new_raw: str, kind: str) -> str:  # info: def edit_json
    data = json.loads(text)  # info: set data
    parts = key.split(".")  # info: set parts
    # keys may contain dots (e.g. "rootrecord.cloud"): walk greedily
    cur, i = data, 0  # info: cur , i = data , 0
    while i < len(parts) - 1:  # info: while i < len ( parts ) -
        for j in range(len(parts) - 1, i, -1):  # info: for j in range ( len ( parts
            k = ".".join(parts[i:j])  # info: set k
            if isinstance(cur, dict) and k in cur and isinstance(cur[k], dict):  # info: if isinstance ( cur , dict ) and
                cur, i = cur[k], j  # info: cur , i = cur [ k ]
                break  # info: break
        else:  # info: else :
            break  # info: break
    last = ".".join(parts[i:])  # info: set last
    if not isinstance(cur, dict) or last not in cur:  # info: if not isinstance ( cur , dict )
        raise ValueError(f"{key}: not found")  # info: raise ValueError ( f" { key } : not found
    old = cur[last]  # info: set old
    if isinstance(old, bool):  # info: if isinstance ( old , bool ) :
        val = new_raw.strip().lower() in ("true", "1")  # info: set val
    elif isinstance(old, int) and not isinstance(old, bool):  # info: elif isinstance ( old , int ) and
        val = int(new_raw)  # info: set val
    elif isinstance(old, float):  # info: elif isinstance ( old , float ) :
        val = float(new_raw)  # info: set val
    elif old is None or isinstance(old, str):  # info: elif old is None or isinstance ( old
        val = new_raw  # info: set val
    else:  # info: else :
        raise ValueError(f"{key}: lists/objects are edited in the file, not here")  # info: raise ValueError ( f" { key } : lists/objects are edited in the file, not here
    # surgical edit: replace only the value token in the original text (keeps formatting, key order, spacing)
    spans = _json_spans(text)  # info: set spans
    full = ".".join(parts[:i] + [last]) if i else last  # info: set full
    if full not in spans:  # info: if full not in spans :
        raise ValueError(f"{key}: value position not found")  # info: raise ValueError ( f" { key } : value position not found
    s, e = spans[full]  # info: s , e = spans [ full ]
    return text[:s] + json.dumps(val, ensure_ascii=False) + text[e:]  # info: return text [ : s ] + json


_JWS = re.compile(r"\s*")  # info: set _JWS


# ====================================================
# SECTION: function _json_spans
# What it does: path -> (start, end) of every leaf value (same paths as parse_json).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _json_spans(text: str) -> dict:  # info: def _json_spans
    """path -> (start, end) of every leaf value (same paths as parse_json)."""  # info: """path -> (start, end) of every leaf value (same paths as parse_json)."""
    dec = json.JSONDecoder()  # info: set dec
    spans: dict = {}  # info: set spans

    def ws(i):  # info: def ws
        return _JWS.match(text, i).end()  # info: return _JWS . match ( text , i

    def obj(i, pre):  # info: def obj
        i = ws(i + 1)  # info: set i
        if text[i] == "}":  # info: if text [ i ] == "}" :
            return i + 1  # info: return i + 1
        while True:  # info: while True :
            k, i = json.decoder.scanstring(text, i + 1)  # info: k , i = json . decoder .
            i = ws(i)  # info: set i
            i = ws(i + 1)  # skip ':'
            path = f"{pre}.{k}" if pre else k  # info: set path
            v, end = dec.raw_decode(text, i)  # info: v , end = dec . raw_decode (
            if isinstance(v, dict) and v:  # info: if isinstance ( v , dict ) and
                end = obj(i, path)  # info: set end
            else:  # info: else :
                spans[path] = (i, end)  # info: spans [ path ] = ( i ,
            i = ws(end)  # info: set i
            if text[i] == ",":  # info: if text [ i ] == "," :
                i = ws(i + 1)  # info: set i
                continue  # info: continue
            return i + 1  # info: return i + 1

    i = ws(0)  # info: set i
    if text[i:i + 1] == "{":  # info: if text [ i : i + 1
        obj(i, "")  # info: call obj
    return spans  # info: return spans


_Y_RX = re.compile(r"^(?P<ind>\s*)(?P<key>[A-Za-z0-9_.\-/]+|\"[^\"]+\"|'[^']+')\s*:(?P<sp>\s*)(?P<val>[^#\n]*?)(?P<cmt>\s+#.*)?\s*$")


# ====================================================
# SECTION: function parse_yaml_scalars
# What it does: Scalar `key: value` lines under nested mappings (lists are skipped).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_yaml_scalars(text: str) -> list[Entry]:  # info: def parse_yaml_scalars
    """Scalar `key: value` lines under nested mappings (lists are skipped)."""  # info: """Scalar `key: value` lines under nested mappings (lists are skipped)."""
    out, stack, seen = [], [], {}  # info: out , stack , seen = [ ]
    for i, l in enumerate(text.splitlines()):  # info: for i , l in enumerate ( text
        if not l.strip() or l.lstrip().startswith("#"):
            continue  # info: continue
        if l.lstrip().startswith("- "):  # info: if l . lstrip ( ) . startswith
            continue  # info: continue
        m = _Y_RX.match(l)  # info: set m
        if not m:  # info: if not m :
            continue  # info: continue
        ind = len(m.group("ind"))  # info: set ind
        while stack and stack[-1][0] >= ind:  # info: while stack and stack [ - 1 ]
            stack.pop()  # info: stack . pop ( )
        k = m.group("key").strip("\"'")  # info: set k
        v = m.group("val").strip()  # info: set v
        path = ".".join([s[1] for s in stack] + [k])  # info: set path
        if v in ("", "|", ">", "|-", ">-"):  # info: if v in ( "" , "|" ,
            stack.append((ind, k))  # info: stack . append ( ( ind , k
            continue  # info: continue
        if v.startswith(("[", "{", "&", "*")):  # info: if v . startswith ( ( "[" ,
            continue  # info: continue
        e = Entry(path, _yaml_unquote(v), i, extra={"raw": v})  # info: set e
        if path in seen:  # info: if path in seen :
            e.dup = seen[path].dup = True  # info: e . dup = seen [ path ]
        seen[path] = e  # info: seen [ path ] = e
        out.append(e)  # info: out . append ( e )
    return out  # info: return out


# ====================================================
# SECTION: function _yaml_unquote
# What it does:  yaml unquote.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _yaml_unquote(v):  # info: def _yaml_unquote
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":  # info: if len ( v ) >= 2 and
        return v[1:-1]  # info: return v [ 1 : - 1 ]
    return v  # info: return v


# ====================================================
# SECTION: function edit_yaml
# What it does: edit yaml.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def edit_yaml(text: str, key: str, new: str) -> str:  # info: def edit_yaml
    ents = [e for e in parse_yaml_scalars(text) if e.key == key]  # info: set ents
    if len(ents) != 1:  # info: if len ( ents ) != 1 :
        raise ValueError(f"{key}: {'not found' if not ents else 'ambiguous'}")  # info: raise ValueError ( f" { key } :
    e = ents[0]  # info: set e
    lines = text.splitlines(keepends=True)  # info: set lines
    raw = lines[e.line]  # info: set raw
    nl = raw[len(raw.rstrip("\r\n")):]  # info: set nl
    m = _Y_RX.match(raw.rstrip("\r\n"))  # info: set m
    oldraw = m.group("val").strip()  # info: set oldraw
    q = oldraw[0] if oldraw[:1] in "\"'" and oldraw[-1:] == oldraw[:1] else ""  # info: set q
    if not q and (re.search(r": |\s#|:$", new) or new[:1] in "!&*{}[],#|>@`%-?" or new != new.strip() or new == ""
                  or new.lower() in ("yes", "no", "on", "off", "null", "~") and not re.fullmatch(r"(yes|no|on|off|null|~)", oldraw.lower())):  # info: or new . lower ( ) in (
        q = '"'  # info: set q
    if q and q in new:  # info: if q and q in new :
        raise ValueError("value may not contain the quote character")  # info: raise ValueError ( "value may not contain the quote character" )
    lines[e.line] = f"{m.group('ind')}{m.group('key')}:{m.group('sp') or ' '}{q}{new}{q}{m.group('cmt') or ''}{nl}"  # info: lines [ e . line ] = f"
    return "".join(lines)  # info: return "" . join ( lines )


# ====================================================
# SECTION: function parse_tsv
# What it does: parse tsv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_tsv(text: str, columns: list[str]) -> list[Entry]:  # info: def parse_tsv
    out = []  # info: set out
    for i, l in enumerate(text.splitlines()):  # info: for i , l in enumerate ( text
        if not l.strip() or l.lstrip().startswith("#"):
            continue  # info: continue
        cells = l.split("\t")  # info: set cells
        rid = cells[0]  # info: set rid
        for c, name in enumerate(columns[1:], start=1):  # info: for c , name in enumerate ( columns
            if c < len(cells):  # info: if c < len ( cells ) :
                out.append(Entry(f"{rid}.{name}", cells[c], i, extra={"col": c}))  # info: out . append ( Entry ( f" {
    return out  # info: return out


# ====================================================
# SECTION: function edit_tsv
# What it does: edit tsv.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def edit_tsv(text: str, key: str, new: str, columns: list[str]) -> str:  # info: def edit_tsv
    if "\t" in new:  # info: if "\t" in new :
        raise ValueError("tabs are not allowed in a TSV cell")  # info: raise ValueError ( "tabs are not allowed in a TSV cell" )
    rid, _, col = key.partition(".")  # info: rid , _ , col = key .
    ci = columns.index(col)  # info: set ci
    lines = text.splitlines(keepends=True)  # info: set lines
    hits = [i for i, l in enumerate(lines) if not l.lstrip().startswith("#") and l.split("\t")[0] == rid]
    if len(hits) != 1:  # info: if len ( hits ) != 1 :
        raise ValueError(f"{key}: row not found / ambiguous")  # info: raise ValueError ( f" { key } : row not found / ambiguous
    i = hits[0]  # info: set i
    raw = lines[i]  # info: set raw
    nl = raw[len(raw.rstrip("\r\n")):]  # info: set nl
    cells = raw.rstrip("\r\n").split("\t")  # info: set cells
    cells[ci] = new  # info: cells [ ci ] = new
    lines[i] = "\t".join(cells) + nl  # info: lines [ i ] = "\t" . join
    return "".join(lines)  # info: return "" . join ( lines )


# ====================================================
# SECTION: function parse
# What it does: parse.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse(fmt: str, text: str, columns=None) -> list[Entry]:  # info: def parse
    if fmt == "env":  # info: if fmt == "env" :
        return parse_env(text)  # info: return parse_env ( text )
    if fmt == "ini":  # info: if fmt == "ini" :
        return parse_ini(text)  # info: return parse_ini ( text )
    if fmt == "json":  # info: if fmt == "json" :
        return parse_json(text)  # info: return parse_json ( text )
    if fmt == "yaml":  # info: if fmt == "yaml" :
        return parse_yaml_scalars(text)  # info: return parse_yaml_scalars ( text )
    if fmt == "tsv":  # info: if fmt == "tsv" :
        return parse_tsv(text, columns or [])  # info: return parse_tsv ( text , columns or [
    if fmt == "raw":  # info: if fmt == "raw" :
        return [Entry("value", text.rstrip("\r\n"), 0)]  # info: return [ Entry ( "value" , text .
    raise ValueError(fmt)  # info: raise ValueError ( fmt )


# ====================================================
# SECTION: function apply_edit
# What it does: apply edit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_edit(fmt: str, text: str, key: str, new: str, kind: str = "str", columns=None, create=False) -> str:  # info: def apply_edit
    if fmt == "env":  # info: if fmt == "env" :
        return edit_env(text, key, new)  # info: return edit_env ( text , key , new
    if fmt == "ini":  # info: if fmt == "ini" :
        return edit_ini(text, key, new, create=create)  # info: return edit_ini ( text , key , new
    if fmt == "json":  # info: if fmt == "json" :
        return edit_json(text, key, new, kind)  # info: return edit_json ( text , key , new
    if fmt == "yaml":  # info: if fmt == "yaml" :
        return edit_yaml(text, key, new)  # info: return edit_yaml ( text , key , new
    if fmt == "tsv":  # info: if fmt == "tsv" :
        return edit_tsv(text, key, new, columns or [])  # info: return edit_tsv ( text , key , new
    if fmt == "raw":  # info: if fmt == "raw" :
        return new + ("\n" if text.endswith("\n") else "")  # info: return new + ( "\n" if text .
    raise ValueError(fmt)  # info: raise ValueError ( fmt )


# ------------------------------------------------------------------ masking + diff
# ====================================================
# SECTION: function masked_text
# What it does: Render text with every secret value replaced by <secret len N> (incl. values that are secrets in OTHER files).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def masked_text(fmt: str, text: str, secret_keys: set[str], whole_file_secret: bool, columns=None) -> str:  # info: def masked_text
    """Render text with every secret value replaced by <secret len N> (incl. values that are secrets in OTHER files)."""  # info: """Render text with every secret value replaced by <secret len N> (incl. values that are secrets in OTHER file
    return _mask_known(_masked_text(fmt, text, secret_keys, whole_file_secret, columns))  # info: return _mask_known ( _masked_text ( fmt , text


# ====================================================
# SECTION: function _masked_text
# What it does:  masked text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _masked_text(fmt: str, text: str, secret_keys: set[str], whole_file_secret: bool, columns=None) -> str:  # info: def _masked_text
    if whole_file_secret and fmt == "raw":  # info: if whole_file_secret and fmt == "raw" :
        return f"<secret {describe(text.rstrip(chr(10)))}>\n"  # info: return f" <secret { describe ( text .
    lines = text.splitlines(keepends=True)  # info: set lines
    try:  # info: try :
        ents = parse(fmt, text, columns)  # info: set ents
    except Exception:  # info: except Exception :
        return "<unparseable — not shown>\n"  # info: return "<unparseable — not shown>\n"
    if fmt == "json":  # info: if fmt == "json" :
        data = json.loads(text)  # info: set data

        def walk(o, pre):  # info: def walk
            if isinstance(o, dict):  # info: if isinstance ( o , dict ) :
                for k in list(o):  # info: for k in list ( o ) :
                    p = f"{pre}.{k}" if pre else str(k)  # info: set p
                    if isinstance(o[k], dict) and o[k]:  # info: if isinstance ( o [ k ] ,
                        walk(o[k], p)  # info: call walk
                    elif whole_file_secret or p in secret_keys or is_secret_key(p.rsplit(".", 1)[-1]):  # info: elif whole_file_secret or p in secret_keys or is_secret_key
                        o[k] = f"<secret {describe(o[k] if not isinstance(o[k], (list, dict)) else json.dumps(o[k]))}>"  # info: o [ k ] = f" <secret {
        walk(data, "")  # info: call walk
        return json.dumps(data, indent=_json_indent(text), ensure_ascii=False) + "\n"  # info: return json . dumps ( data , indent
    for e in ents:  # info: for e in ents :
        if e.line is None:  # info: if e . line is None :
            continue  # info: continue
        leaf = e.key.rsplit(".", 1)[-1]  # info: set leaf
        if not (whole_file_secret or e.key in secret_keys or is_secret_key(leaf)):  # info: if not ( whole_file_secret or e . key
            continue  # info: continue
        raw = lines[e.line]  # info: set raw
        nl = raw[len(raw.rstrip("\r\n")):]  # info: set nl
        body = raw.rstrip("\r\n")  # info: set body
        tag = f"<secret {describe(e.value)}>"  # info: set tag
        if fmt == "env":  # info: if fmt == "env" :
            m = _ENV_RX.match(body)  # info: set m
            body = f"{m.group('pre')}{m.group('key')}{m.group('eq')}{tag}"  # info: set body
        elif fmt == "ini":  # info: elif fmt == "ini" :
            me = _SYSD_ENV_RX.match(body)  # info: set me
            if me:  # info: if me :
                body = f"{me.group('pre')}{me.group('key')}={tag}"  # info: set body
            else:  # info: else :
                m = _INI_RX.match(body)  # info: set m
                body = f"{m.group('pre')}{m.group('key')}{m.group('eq')}{tag}"  # info: set body
        elif fmt == "yaml":  # info: elif fmt == "yaml" :
            m = _Y_RX.match(body)  # info: set m
            body = f"{m.group('ind')}{m.group('key')}: {tag}"  # info: set body
        elif fmt == "tsv":  # info: elif fmt == "tsv" :
            cells = body.split("\t")  # info: set cells
            cells[e.extra["col"]] = tag  # info: cells [ e . extra [ "col" ]
            body = "\t".join(cells)  # info: set body
        else:  # info: else :
            body = tag  # info: set body
        lines[e.line] = body + nl  # info: lines [ e . line ] = body
    return "".join(lines)  # info: return "" . join ( lines )


KNOWN_SECRETS: list[str] = []   # filled by rr_registry.secret_values(): secret values held in OTHER files (never printed)


# ====================================================
# SECTION: function _mask_known
# What it does:  mask known.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _mask_known(s: str) -> str:  # info: def _mask_known
    for v in KNOWN_SECRETS:  # info: for v in KNOWN_SECRETS :
        if v and v in s:  # info: if v and v in s :
            s = s.replace(v, f"<secret len {len(v)}>")  # info: set s
    return s  # info: return s


# ====================================================
# SECTION: function masked_diff
# What it does: masked diff.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def masked_diff(fmt, old, new, secret_keys, whole_file_secret, name="file", columns=None) -> str:  # info: def masked_diff
    a = masked_text(fmt, old, secret_keys, whole_file_secret, columns).splitlines(keepends=True)  # info: set a
    b = masked_text(fmt, new, secret_keys, whole_file_secret, columns).splitlines(keepends=True)  # info: set b
    d = "".join(difflib.unified_diff(a, b, f"{name} (current)", f"{name} (new)", n=1))  # info: set d
    return d or "(no change)"  # info: return d or "(no change)"


# ------------------------------------------------------------------ save pipeline
# ====================================================
# SECTION: function sha
# What it does: sha.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sha(text: str) -> str:  # info: def sha
    return hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()  # info: return hashlib . sha256 ( text . encode


# ====================================================
# SECTION: class Plan
# What it does: Plan.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
@dataclass  # info: decorator dataclass
class Plan:  # info: class Plan
    path: Path  # info: set path
    fmt: str  # info: set fmt
    old_text: str  # info: set old_text
    new_text: str  # info: set new_text
    old_sha: str  # info: set old_sha
    diff: str  # info: set diff
    secret: bool  # info: set secret
    restart_note: str  # info: set restart_note


# ====================================================
# SECTION: function plan_edit
# What it does: plan edit.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def plan_edit(path: Path, fmt: str, key: str, new_raw: str, kind: str, *, secret_keys: set[str], whole_file_secret: bool,  # info: def plan_edit
              restart_note: str, columns=None, create=False) -> Plan:  # info: set restart_note
    p = Path(path)  # info: set p
    if p.exists():  # info: if p . exists ( ) :
        old = p.read_text(encoding="utf-8", errors="surrogateescape")  # info: set old
    elif create:  # info: elif create :
        old = ""  # info: set old
    else:  # info: else :
        raise FileNotFoundError(path)  # info: raise FileNotFoundError ( path )
    ok, norm = validate(kind, new_raw)  # info: ok , norm = validate ( kind ,
    if not ok:  # info: if not ok :
        raise ValueError(norm)  # info: raise ValueError ( norm )
    new = apply_edit(fmt, old, key, norm, kind, columns, create)  # info: set new
    # sanity: result must still parse
    parse(fmt, new, columns)  # info: call parse
    diff = masked_diff(fmt, old, new, secret_keys | {key} if (whole_file_secret or key in secret_keys or is_secret_key(key.rsplit('.', 1)[-1])) else secret_keys,  # info: set diff
                       whole_file_secret, Path(path).name, columns)  # info: whole_file_secret , Path ( path ) . name
    return Plan(Path(path), fmt, old, new, sha(old), diff, whole_file_secret or bool(secret_keys), restart_note)  # info: return Plan ( Path ( path ) ,


# ====================================================
# SECTION: function backup_copy
# What it does: backup copy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def backup_copy(path: Path, secret: bool, root: Path | None = None) -> Path:  # info: def backup_copy
    root = Path(root or BACKUP_ROOT)  # info: set root
    root.mkdir(parents=True, exist_ok=True)  # info: root . mkdir ( parents = True ,
    os.chmod(root, 0o700)  # info: os . chmod ( root , 0o700 )
    ts = time.strftime("%Y%m%d-%H%M%S")  # info: set ts
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", str(path).strip("/"))[-150:]  # info: set safe
    dst = root / f"{safe}.{ts}.bak"  # info: set dst
    n = 1  # info: set n
    while dst.exists():  # info: while dst . exists ( ) :
        dst = root / f"{safe}.{ts}-{n}.bak"  # info: set dst
        n += 1  # info: set n
    mode = stat.S_IMODE(os.stat(path).st_mode)  # info: set mode
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)  # info: set fd
    with os.fdopen(fd, "wb") as f, open(path, "rb") as src:  # info: with os . fdopen ( fd , "wb"
        shutil.copyfileobj(src, f)  # info: shutil . copyfileobj ( src , f )
    os.chmod(dst, 0o600 if secret else mode)  # info: os . chmod ( dst , 0o600 if
    return dst  # info: return dst


# ====================================================
# SECTION: function commit
# What it does: Backup + atomic write. Refuses if the file changed since plan_edit().
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def commit(plan: Plan, backup_root: Path | None = None) -> dict:  # info: def commit
    """Backup + atomic write. Refuses if the file changed since plan_edit()."""  # info: """Backup + atomic write. Refuses if the file changed since plan_edit()."""
    p = plan.path  # info: set p
    if not p.exists():  # info: if not p . exists ( ) :
        if plan.old_sha != sha(""):  # info: if plan . old_sha != sha ( ""
            raise RuntimeError(f"{p.name} appeared on disk since the diff was built — re-open and try again")  # info: raise RuntimeError ( f" { p . name
        p.parent.mkdir(parents=True, exist_ok=True)  # info: p . parent . mkdir ( parents =
        fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))  # info: fd , tmp = tempfile . mkstemp (
        try:  # info: try :
            with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:  # info: with os . fdopen ( fd , "w"
                f.write(plan.new_text)  # info: f . write ( plan . new_text )
                f.flush()  # info: f . flush ( )
                os.fsync(f.fileno())  # info: os . fsync ( f . fileno (
            os.chmod(tmp, 0o644)  # info: os . chmod ( tmp , 0o644 )
            os.replace(tmp, p)  # info: os . replace ( tmp , p )
        except Exception:  # info: except Exception :
            try:  # info: try :
                os.unlink(tmp)  # info: os . unlink ( tmp )
            except OSError:  # info: except OSError :
                pass  # info: pass
            raise  # info: raise
        return {"backup": "(new file, no prior copy)", "mode": "0o644", "note": plan.restart_note}  # info: return { "backup" : "(new file, no prior copy)" , "mode" :
    cur = p.read_text(encoding="utf-8", errors="surrogateescape")  # info: set cur
    if sha(cur) != plan.old_sha:  # info: if sha ( cur ) != plan .
        raise RuntimeError(f"{p.name} changed on disk since the diff was built — re-open and try again")  # info: raise RuntimeError ( f" { p . name
    st = os.stat(p)  # info: set st
    mode = stat.S_IMODE(st.st_mode)  # info: set mode
    bak = backup_copy(p, plan.secret, backup_root)  # info: set bak
    fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))  # info: fd , tmp = tempfile . mkstemp (
    try:  # info: try :
        with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:  # info: with os . fdopen ( fd , "w"
            f.write(plan.new_text)  # info: f . write ( plan . new_text )
            f.flush()  # info: f . flush ( )
            os.fsync(f.fileno())  # info: os . fsync ( f . fileno (
        os.chmod(tmp, mode)  # info: os . chmod ( tmp , mode )
        try:  # info: try :
            os.chown(tmp, st.st_uid, st.st_gid)  # info: os . chown ( tmp , st .
        except PermissionError:  # info: except PermissionError :
            pass  # info: pass
        os.replace(tmp, p)  # info: os . replace ( tmp , p )
    except Exception:  # info: except Exception :
        try:  # info: try :
            os.unlink(tmp)  # info: os . unlink ( tmp )
        except OSError:  # info: except OSError :
            pass  # info: pass
        raise  # info: raise
    return {"backup": str(bak), "mode": oct(mode), "note": plan.restart_note}  # info: return { "backup" : str ( bak )
