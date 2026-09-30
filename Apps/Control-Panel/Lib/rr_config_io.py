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
from __future__ import annotations

import difflib
import hashlib
import io
import json
import os
import re
import shutil
import stat
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

SECRET_TOKENS = {"TOKEN", "TOKENS", "KEY", "KEYS", "SECRET", "SECRETS", "PASS", "PASSWORD", "PASSWD", "PAT", "WEBHOOK",
                 "WEBHOOKS", "AUTH", "COOKIE", "COOKIES", "APIKEY", "CREDENTIAL", "CREDENTIALS", "PRIVATE", "ACCESS"}
SECRET_SUFFIXES = ("TOKEN", "SECRET", "PASSWORD", "APIKEY", "WEBHOOK", "COOKIE")
BACKUP_ROOT = Path(os.environ.get("RR_CP_BACKUP_ROOT", "/home/rootrecord/Database/GITHUB/control-panel-settings-backups"))


def is_secret_key(key: str) -> bool:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", key.upper()) if p]
    return any(p in SECRET_TOKENS or p.endswith(SECRET_SUFFIXES) for p in parts)


def describe(value) -> str:
    """Masked description of a secret value. Never contains the value."""
    if value is None:
        return "not set"
    s = str(value)
    return "empty" if s == "" else f"set (len {len(s)})"


# ------------------------------------------------------------------ validation
def validate(kind: str, raw: str):
    """Return (ok, normalized_text_or_error). raw is the user's text."""
    if "\n" in raw or "\r" in raw or "\0" in raw:
        return False, "newlines / NUL are not allowed"
    k = kind or "str"
    if k == "port":
        if not re.fullmatch(r"\d{1,5}", raw.strip()) or not (1 <= int(raw) <= 65535):
            return False, "port must be an integer 1–65535"
        return True, str(int(raw))
    if k == "bool01":
        if raw.strip() not in ("0", "1"):
            return False, "boolean must be 0 or 1"
        return True, raw.strip()
    if k == "bool":
        if raw.strip().lower() not in ("true", "false"):
            return False, "boolean must be true or false"
        return True, raw.strip().lower()
    if k == "int":
        if not re.fullmatch(r"-?\d+", raw.strip()):
            return False, "must be an integer"
        return True, raw.strip()
    if k == "float":
        try:
            float(raw)
        except ValueError:
            return False, "must be a number"
        return True, raw.strip()
    if k == "url":
        u = urlparse(raw.strip())
        if u.scheme not in ("http", "https", "rtsp", "ws", "wss", "tcp") or not u.netloc:
            return False, "URL must be http(s)/rtsp/ws(s)/tcp with a host"
        try:
            _ = u.port
        except ValueError:
            return False, "URL port is invalid"
        return True, raw.strip()
    if k == "host":
        if not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", raw.strip()):
            return False, "hostname / IP expected"
        return True, raw.strip()
    return True, raw


# ------------------------------------------------------------------ parse/edit per format
@dataclass
class Entry:
    key: str            # dotted path / key name
    value: object       # python value (str for text formats)
    line: int | None = None
    section: str = ""
    dup: bool = False   # key occurs more than once -> edits refused (ambiguous)
    extra: dict = field(default_factory=dict)


_ENV_RX = re.compile(r"^(?P<pre>\s*(?:export\s+)?)(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?P<eq>\s*=\s*)(?P<val>.*?)(?P<post>\s*)$")


def _unquote(v: str):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1], v[0]
    return v, ""


def parse_env(text: str) -> list[Entry]:
    out, seen = [], {}
    for i, l in enumerate(text.splitlines()):
        if l.lstrip().startswith("#"):
            continue
        m = _ENV_RX.match(l)
        if m:
            v, _q = _unquote(m.group("val"))
            e = Entry(m.group("key"), v, i)
            if e.key in seen:
                e.dup = True
                seen[e.key].dup = True
            seen[e.key] = e
            out.append(e)
    return out


def edit_env(text: str, key: str, new: str) -> str:
    lines = text.splitlines(keepends=True)
    hits = [i for i, l in enumerate(lines) if not l.lstrip().startswith("#") and (m := _ENV_RX.match(l.rstrip("\r\n"))) and m.group("key") == key]
    if len(hits) != 1:
        raise ValueError(f"{key}: {'not found' if not hits else 'defined more than once — edit refused (ambiguous)'}")
    i = hits[0]
    raw = lines[i]
    nl = raw[len(raw.rstrip("\r\n")):]
    m = _ENV_RX.match(raw.rstrip("\r\n"))
    _v, q = _unquote(m.group("val"))
    if q == "" and re.search(r"[\s#;&|$`\"'\\]", new) and " " not in _v:
        q = '"'
    if q and q in new:
        raise ValueError(f"{key}: value may not contain the {q} quote character")
    lines[i] = f"{m.group('pre')}{key}{m.group('eq')}{q}{new}{q}{m.group('post')}{nl}"
    return "".join(lines)


_SEC_RX = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s*$")
_INI_RX = re.compile(r"^(?P<pre>\s*)(?P<key>[A-Za-z0-9_.\-]+)(?P<eq>\s*=\s*)(?P<val>.*?)(?P<post>\s*)$")
_SYSD_ENV_RX = re.compile(r'^(?P<pre>\s*Environment=)(?P<q>"?)(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<val>[^"]*)(?P=q)(?P<post>\s*)$')


def parse_ini(text: str) -> list[Entry]:
    out, sec, seen = [], "", {}
    for i, l in enumerate(text.splitlines()):
        s = l.strip()
        if not s or s[0] in "#;":
            continue
        m = _SEC_RX.match(l)
        if m:
            sec = m.group("name").strip()
            continue
        me = _SYSD_ENV_RX.match(l)
        if me:
            key = f"{sec}.Environment.{me.group('key')}"
            e = Entry(key, me.group("val"), i, sec)
        else:
            m = _INI_RX.match(l)
            if not m:
                continue
            key = f"{sec}.{m.group('key')}" if sec else m.group("key")
            e = Entry(key, m.group("val"), i, sec)
        if key in seen:
            e.dup = seen[key].dup = True
        seen[key] = e
        out.append(e)
    return out


def edit_ini(text: str, key: str, new: str, create: bool = False) -> str:
    lines = text.splitlines(keepends=True)
    ents = [e for e in parse_ini(text) if e.key == key]
    if len(ents) > 1:
        raise ValueError(f"{key}: defined more than once — edit refused (ambiguous)")
    if not ents:
        if not create:
            raise ValueError(f"{key}: not found")
        sec, _, rest = key.partition(".")
        env = rest.startswith("Environment.")
        newline = f"Environment={rest.split('.', 1)[1]}={new}\n" if env else f"{rest} = {new}\n"
        # append at end of the section (or create it)
        cur, last = "", None
        for i, l in enumerate(lines):
            m = _SEC_RX.match(l.rstrip("\r\n"))
            if m:
                cur = m.group("name").strip()
            if cur == sec and l.strip():
                last = i
        if last is None:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines += ([] if not lines else ["\n"]) + [f"[{sec}]\n", newline]
        else:
            lines.insert(last + 1, newline)
        return "".join(lines)
    e = ents[0]
    raw = lines[e.line]
    nl = raw[len(raw.rstrip("\r\n")):]
    body = raw.rstrip("\r\n")
    me = _SYSD_ENV_RX.match(body)
    if me:
        q = me.group("q") or ('"' if re.search(r"\s", new) else "")
        if '"' in new:
            raise ValueError("value may not contain a double quote")
        lines[e.line] = f"{me.group('pre')}{q}{me.group('key')}={new}{q}{me.group('post')}{nl}"
    else:
        m = _INI_RX.match(body)
        lines[e.line] = f"{m.group('pre')}{m.group('key')}{m.group('eq')}{new}{m.group('post')}{nl}"
    return "".join(lines)


def parse_json(text: str) -> list[Entry]:
    data = json.loads(text)
    out = []

    def walk(o, pre):
        if isinstance(o, dict):
            for k, v in o.items():
                p = f"{pre}.{k}" if pre else str(k)
                if isinstance(v, dict) and v:
                    walk(v, p)
                else:
                    out.append(Entry(p, v))
    walk(data, "")
    return out


def _json_indent(text: str):
    m = re.search(r"\n([ \t]+)\"", text)
    return m.group(1) if m else None


def edit_json(text: str, key: str, new_raw: str, kind: str) -> str:
    data = json.loads(text)
    parts = key.split(".")
    # keys may contain dots (e.g. "rootrecord.cloud"): walk greedily
    cur, i = data, 0
    while i < len(parts) - 1:
        for j in range(len(parts) - 1, i, -1):
            k = ".".join(parts[i:j])
            if isinstance(cur, dict) and k in cur and isinstance(cur[k], dict):
                cur, i = cur[k], j
                break
        else:
            break
    last = ".".join(parts[i:])
    if not isinstance(cur, dict) or last not in cur:
        raise ValueError(f"{key}: not found")
    old = cur[last]
    if isinstance(old, bool):
        val = new_raw.strip().lower() in ("true", "1")
    elif isinstance(old, int) and not isinstance(old, bool):
        val = int(new_raw)
    elif isinstance(old, float):
        val = float(new_raw)
    elif old is None or isinstance(old, str):
        val = new_raw
    else:
        raise ValueError(f"{key}: lists/objects are edited in the file, not here")
    # surgical edit: replace only the value token in the original text (keeps formatting, key order, spacing)
    spans = _json_spans(text)
    full = ".".join(parts[:i] + [last]) if i else last
    if full not in spans:
        raise ValueError(f"{key}: value position not found")
    s, e = spans[full]
    return text[:s] + json.dumps(val, ensure_ascii=False) + text[e:]


_JWS = re.compile(r"\s*")


def _json_spans(text: str) -> dict:
    """path -> (start, end) of every leaf value (same paths as parse_json)."""
    dec = json.JSONDecoder()
    spans: dict = {}

    def ws(i):
        return _JWS.match(text, i).end()

    def obj(i, pre):
        i = ws(i + 1)
        if text[i] == "}":
            return i + 1
        while True:
            k, i = json.decoder.scanstring(text, i + 1)
            i = ws(i)
            i = ws(i + 1)  # skip ':'
            path = f"{pre}.{k}" if pre else k
            v, end = dec.raw_decode(text, i)
            if isinstance(v, dict) and v:
                end = obj(i, path)
            else:
                spans[path] = (i, end)
            i = ws(end)
            if text[i] == ",":
                i = ws(i + 1)
                continue
            return i + 1

    i = ws(0)
    if text[i:i + 1] == "{":
        obj(i, "")
    return spans


_Y_RX = re.compile(r"^(?P<ind>\s*)(?P<key>[A-Za-z0-9_.\-/]+|\"[^\"]+\"|'[^']+')\s*:(?P<sp>\s*)(?P<val>[^#\n]*?)(?P<cmt>\s+#.*)?\s*$")


def parse_yaml_scalars(text: str) -> list[Entry]:
    """Scalar `key: value` lines under nested mappings (lists are skipped)."""
    out, stack, seen = [], [], {}
    for i, l in enumerate(text.splitlines()):
        if not l.strip() or l.lstrip().startswith("#"):
            continue
        if l.lstrip().startswith("- "):
            continue
        m = _Y_RX.match(l)
        if not m:
            continue
        ind = len(m.group("ind"))
        while stack and stack[-1][0] >= ind:
            stack.pop()
        k = m.group("key").strip("\"'")
        v = m.group("val").strip()
        path = ".".join([s[1] for s in stack] + [k])
        if v in ("", "|", ">", "|-", ">-"):
            stack.append((ind, k))
            continue
        if v.startswith(("[", "{", "&", "*")):
            continue
        e = Entry(path, _yaml_unquote(v), i, extra={"raw": v})
        if path in seen:
            e.dup = seen[path].dup = True
        seen[path] = e
        out.append(e)
    return out


def _yaml_unquote(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def edit_yaml(text: str, key: str, new: str) -> str:
    ents = [e for e in parse_yaml_scalars(text) if e.key == key]
    if len(ents) != 1:
        raise ValueError(f"{key}: {'not found' if not ents else 'ambiguous'}")
    e = ents[0]
    lines = text.splitlines(keepends=True)
    raw = lines[e.line]
    nl = raw[len(raw.rstrip("\r\n")):]
    m = _Y_RX.match(raw.rstrip("\r\n"))
    oldraw = m.group("val").strip()
    q = oldraw[0] if oldraw[:1] in "\"'" and oldraw[-1:] == oldraw[:1] else ""
    if not q and (re.search(r": |\s#|:$", new) or new[:1] in "!&*{}[],#|>@`%-?" or new != new.strip() or new == ""
                  or new.lower() in ("yes", "no", "on", "off", "null", "~") and not re.fullmatch(r"(yes|no|on|off|null|~)", oldraw.lower())):
        q = '"'
    if q and q in new:
        raise ValueError("value may not contain the quote character")
    lines[e.line] = f"{m.group('ind')}{m.group('key')}:{m.group('sp') or ' '}{q}{new}{q}{m.group('cmt') or ''}{nl}"
    return "".join(lines)


def parse_tsv(text: str, columns: list[str]) -> list[Entry]:
    out = []
    for i, l in enumerate(text.splitlines()):
        if not l.strip() or l.lstrip().startswith("#"):
            continue
        cells = l.split("\t")
        rid = cells[0]
        for c, name in enumerate(columns[1:], start=1):
            if c < len(cells):
                out.append(Entry(f"{rid}.{name}", cells[c], i, extra={"col": c}))
    return out


def edit_tsv(text: str, key: str, new: str, columns: list[str]) -> str:
    if "\t" in new:
        raise ValueError("tabs are not allowed in a TSV cell")
    rid, _, col = key.partition(".")
    ci = columns.index(col)
    lines = text.splitlines(keepends=True)
    hits = [i for i, l in enumerate(lines) if not l.lstrip().startswith("#") and l.split("\t")[0] == rid]
    if len(hits) != 1:
        raise ValueError(f"{key}: row not found / ambiguous")
    i = hits[0]
    raw = lines[i]
    nl = raw[len(raw.rstrip("\r\n")):]
    cells = raw.rstrip("\r\n").split("\t")
    cells[ci] = new
    lines[i] = "\t".join(cells) + nl
    return "".join(lines)


def parse(fmt: str, text: str, columns=None) -> list[Entry]:
    if fmt == "env":
        return parse_env(text)
    if fmt == "ini":
        return parse_ini(text)
    if fmt == "json":
        return parse_json(text)
    if fmt == "yaml":
        return parse_yaml_scalars(text)
    if fmt == "tsv":
        return parse_tsv(text, columns or [])
    if fmt == "raw":
        return [Entry("value", text.rstrip("\r\n"), 0)]
    raise ValueError(fmt)


def apply_edit(fmt: str, text: str, key: str, new: str, kind: str = "str", columns=None, create=False) -> str:
    if fmt == "env":
        return edit_env(text, key, new)
    if fmt == "ini":
        return edit_ini(text, key, new, create=create)
    if fmt == "json":
        return edit_json(text, key, new, kind)
    if fmt == "yaml":
        return edit_yaml(text, key, new)
    if fmt == "tsv":
        return edit_tsv(text, key, new, columns or [])
    if fmt == "raw":
        return new + ("\n" if text.endswith("\n") else "")
    raise ValueError(fmt)


# ------------------------------------------------------------------ masking + diff
def masked_text(fmt: str, text: str, secret_keys: set[str], whole_file_secret: bool, columns=None) -> str:
    """Render text with every secret value replaced by <secret len N> (incl. values that are secrets in OTHER files)."""
    return _mask_known(_masked_text(fmt, text, secret_keys, whole_file_secret, columns))


def _masked_text(fmt: str, text: str, secret_keys: set[str], whole_file_secret: bool, columns=None) -> str:
    if whole_file_secret and fmt == "raw":
        return f"<secret {describe(text.rstrip(chr(10)))}>\n"
    lines = text.splitlines(keepends=True)
    try:
        ents = parse(fmt, text, columns)
    except Exception:
        return "<unparseable — not shown>\n"
    if fmt == "json":
        data = json.loads(text)

        def walk(o, pre):
            if isinstance(o, dict):
                for k in list(o):
                    p = f"{pre}.{k}" if pre else str(k)
                    if isinstance(o[k], dict) and o[k]:
                        walk(o[k], p)
                    elif whole_file_secret or p in secret_keys or is_secret_key(p.rsplit(".", 1)[-1]):
                        o[k] = f"<secret {describe(o[k] if not isinstance(o[k], (list, dict)) else json.dumps(o[k]))}>"
        walk(data, "")
        return json.dumps(data, indent=_json_indent(text), ensure_ascii=False) + "\n"
    for e in ents:
        if e.line is None:
            continue
        leaf = e.key.rsplit(".", 1)[-1]
        if not (whole_file_secret or e.key in secret_keys or is_secret_key(leaf)):
            continue
        raw = lines[e.line]
        nl = raw[len(raw.rstrip("\r\n")):]
        body = raw.rstrip("\r\n")
        tag = f"<secret {describe(e.value)}>"
        if fmt == "env":
            m = _ENV_RX.match(body)
            body = f"{m.group('pre')}{m.group('key')}{m.group('eq')}{tag}"
        elif fmt == "ini":
            me = _SYSD_ENV_RX.match(body)
            if me:
                body = f"{me.group('pre')}{me.group('key')}={tag}"
            else:
                m = _INI_RX.match(body)
                body = f"{m.group('pre')}{m.group('key')}{m.group('eq')}{tag}"
        elif fmt == "yaml":
            m = _Y_RX.match(body)
            body = f"{m.group('ind')}{m.group('key')}: {tag}"
        elif fmt == "tsv":
            cells = body.split("\t")
            cells[e.extra["col"]] = tag
            body = "\t".join(cells)
        else:
            body = tag
        lines[e.line] = body + nl
    return "".join(lines)


KNOWN_SECRETS: list[str] = []   # filled by rr_registry.secret_values(): secret values held in OTHER files (never printed)


def _mask_known(s: str) -> str:
    for v in KNOWN_SECRETS:
        if v and v in s:
            s = s.replace(v, f"<secret len {len(v)}>")
    return s


def masked_diff(fmt, old, new, secret_keys, whole_file_secret, name="file", columns=None) -> str:
    a = masked_text(fmt, old, secret_keys, whole_file_secret, columns).splitlines(keepends=True)
    b = masked_text(fmt, new, secret_keys, whole_file_secret, columns).splitlines(keepends=True)
    d = "".join(difflib.unified_diff(a, b, f"{name} (current)", f"{name} (new)", n=1))
    return d or "(no change)"


# ------------------------------------------------------------------ save pipeline
def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "surrogateescape")).hexdigest()


@dataclass
class Plan:
    path: Path
    fmt: str
    old_text: str
    new_text: str
    old_sha: str
    diff: str
    secret: bool
    restart_note: str


def plan_edit(path: Path, fmt: str, key: str, new_raw: str, kind: str, *, secret_keys: set[str], whole_file_secret: bool,
              restart_note: str, columns=None, create=False) -> Plan:
    p = Path(path)
    if p.exists():
        old = p.read_text(encoding="utf-8", errors="surrogateescape")
    elif create:
        old = ""
    else:
        raise FileNotFoundError(path)
    ok, norm = validate(kind, new_raw)
    if not ok:
        raise ValueError(norm)
    new = apply_edit(fmt, old, key, norm, kind, columns, create)
    # sanity: result must still parse
    parse(fmt, new, columns)
    diff = masked_diff(fmt, old, new, secret_keys | {key} if (whole_file_secret or key in secret_keys or is_secret_key(key.rsplit('.', 1)[-1])) else secret_keys,
                       whole_file_secret, Path(path).name, columns)
    return Plan(Path(path), fmt, old, new, sha(old), diff, whole_file_secret or bool(secret_keys), restart_note)


def backup_copy(path: Path, secret: bool, root: Path | None = None) -> Path:
    root = Path(root or BACKUP_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    ts = time.strftime("%Y%m%d-%H%M%S")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", str(path).strip("/"))[-150:]
    dst = root / f"{safe}.{ts}.bak"
    n = 1
    while dst.exists():
        dst = root / f"{safe}.{ts}-{n}.bak"
        n += 1
    mode = stat.S_IMODE(os.stat(path).st_mode)
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f, open(path, "rb") as src:
        shutil.copyfileobj(src, f)
    os.chmod(dst, 0o600 if secret else mode)
    return dst


def commit(plan: Plan, backup_root: Path | None = None) -> dict:
    """Backup + atomic write. Refuses if the file changed since plan_edit()."""
    p = plan.path
    if not p.exists():
        if plan.old_sha != sha(""):
            raise RuntimeError(f"{p.name} appeared on disk since the diff was built — re-open and try again")
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
                f.write(plan.new_text)
                f.flush()
                os.fsync(f.fileno())
            os.chmod(tmp, 0o644)
            os.replace(tmp, p)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return {"backup": "(new file, no prior copy)", "mode": "0o644", "note": plan.restart_note}
    cur = p.read_text(encoding="utf-8", errors="surrogateescape")
    if sha(cur) != plan.old_sha:
        raise RuntimeError(f"{p.name} changed on disk since the diff was built — re-open and try again")
    st = os.stat(p)
    mode = stat.S_IMODE(st.st_mode)
    bak = backup_copy(p, plan.secret, backup_root)
    fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(plan.new_text)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, mode)
        try:
            os.chown(tmp, st.st_uid, st.st_gid)
        except PermissionError:
            pass
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return {"backup": str(bak), "mode": oct(mode), "note": plan.restart_note}
