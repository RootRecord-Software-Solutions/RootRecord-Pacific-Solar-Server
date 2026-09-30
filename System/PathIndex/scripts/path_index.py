# ==============================================================================
# FILE: System/PathIndex/scripts/path_index.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Scoped path index (WO-MIG-42).

Lists path and kind for three Ecosystem source trees. Does not read file bytes,
hash files, or store symlink targets. A root outside the allowlist exits
before any index file is replaced.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
ECOSYSTEM = Path("/home/rootrecord/RootRecord-Ecosystem")  # info: set ECOSYSTEM
DB = ECOSYSTEM / "2 - RootRecord-Database"  # info: set DB
DATA = DB / "System" / "PathIndex"  # info: set DATA
LOG_DIR = DB / "Logs" / "System" / "PathIndex"  # info: set LOG_DIR

# ====================================================
# SECTION: ALLOW
# What it does: Set ALLOW.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
ALLOW = (  # info: set ALLOW
    ECOSYSTEM / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server",  # info: ECOSYSTEM / "1 - Servers" / "1 - RootRecord-Pacific-Solar-Server" ,
    ECOSYSTEM / "5 - RootRecord-Library",  # info: ECOSYSTEM / "5 - RootRecord-Library" ,
    ECOSYSTEM / "6 - Android Development",  # info: ECOSYSTEM / "6 - Android Development" ,
)  # info: )

STUB_NAMES = frozenset({"node_modules", ".venv", "venv", "__pycache__"})  # info: set STUB_NAMES


# ====================================================
# SECTION: function now_iso
# What it does: now iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_iso() -> str:  # info: def now_iso
    return datetime.now(HST).isoformat(timespec="seconds")  # info: return datetime . now ( HST ) .


# ====================================================
# SECTION: function is_stub
# What it does: is stub.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def is_stub(path: Path) -> bool:  # info: def is_stub
    if path.name in STUB_NAMES:  # info: if path . name in STUB_NAMES :
        return True  # info: return True
    return path.name == "objects" and path.parent.name == ".git"  # info: return path . name == "objects" and path


# ====================================================
# SECTION: function under
# What it does: under.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def under(path: Path, root: Path) -> bool:  # info: def under
    try:  # info: try :
        path.resolve().relative_to(root.resolve())  # info: path . resolve ( ) . relative_to (
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return False  # info: return False
    return True  # info: return True


# ====================================================
# SECTION: function accepted
# What it does: accepted.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def accepted(path: Path, *, fixture: bool) -> bool:  # info: def accepted
    if fixture:  # info: if fixture :
        return under(path, Path(tempfile.gettempdir()))  # info: return under ( path , Path ( tempfile
    return any(under(path, root) for root in ALLOW)  # info: return any ( under ( path , root


# ====================================================
# SECTION: function fmt
# What it does: fmt.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fmt(path: Path, kind: str) -> str:  # info: def fmt
    return f"{path.as_posix()}\t{kind}"  # info: return f" { path . as_posix ( )


# ====================================================
# SECTION: function load_mtimes
# What it does: load mtimes.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_mtimes(path: Path) -> dict[str, float]:  # info: def load_mtimes
    if not path.is_file():  # info: if not path . is_file ( ) :
        return {}  # info: return { }
    try:  # info: try :
        raw = json.loads(path.read_text(encoding="utf-8"))  # info: set raw
    except (OSError, json.JSONDecodeError):  # info: except ( OSError , json . JSONDecodeError )
        return {}  # info: return { }
    return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict


# ====================================================
# SECTION: function load_old
# What it does: load old.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_old(path: Path) -> list[str]:  # info: def load_old
    if not path.is_file():  # info: if not path . is_file ( ) :
        return []  # info: return [ ]
    try:  # info: try :
        return path.read_text(encoding="utf-8", errors="replace").splitlines()  # info: return path . read_text ( encoding = "utf-8"
    except OSError:  # info: except OSError :
        return []  # info: return [ ]


# ====================================================
# SECTION: function slice_prefix
# What it does: slice prefix.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def slice_prefix(old: list[str], prefix: str) -> list[str]:  # info: def slice_prefix
    pfx = prefix if prefix.endswith("/") else prefix + "/"  # info: set pfx
    hit = []  # info: set hit
    for line in old:  # info: for line in old :
        base = line.split("\t", 1)[0]  # info: set base
        if base == prefix or base.startswith(pfx):  # info: if base == prefix or base . startswith
            hit.append(line)  # info: hit . append ( line )
    return hit  # info: return hit


# ====================================================
# SECTION: function walk_tree
# What it does: walk tree.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def walk_tree(  # info: def walk_tree
    root: Path,  # info: set root
    *,  # info: * ,
    old_paths: list[str],  # info: set old_paths
    mtimes: dict[str, float],  # info: set mtimes
    seen: set[tuple[int, int]],  # info: set seen
    stats: dict,  # info: set stats
) -> list[str]:  # info: ) -> list [ str ] :
    out: list[str] = []  # info: set out
    if not root.exists():  # info: if not root . exists ( ) :
        stats["missing"] += 1  # info: stats [ "missing" ] += 1
        return [fmt(root, "missing")]  # info: return [ fmt ( root , "missing" )

    def rec(cur: Path) -> None:  # info: def rec
        stats["visited"] += 1  # info: stats [ "visited" ] += 1
        try:  # info: try :
            st = cur.lstat()  # info: set st
        except OSError:  # info: except OSError :
            out.append(fmt(cur, "error"))  # info: out . append ( fmt ( cur ,
            stats["errors"] += 1  # info: stats [ "errors" ] += 1
            return  # info: return
        key = (st.st_dev, st.st_ino)  # info: set key
        if key in seen:  # info: if key in seen :
            out.append(fmt(cur, "error"))  # info: out . append ( fmt ( cur ,
            stats["errors"] += 1  # info: stats [ "errors" ] += 1
            return  # info: return
        seen.add(key)  # info: seen . add ( key )
        posix = cur.as_posix()  # info: set posix

        if os.path.islink(cur):  # info: if os . path . islink ( cur
            out.append(fmt(cur, "symlink"))  # info: out . append ( fmt ( cur ,
            stats["symlinks"] += 1  # info: stats [ "symlinks" ] += 1
            return  # info: return

        if not cur.is_dir():  # info: if not cur . is_dir ( ) :
            out.append(fmt(cur, "file"))  # info: out . append ( fmt ( cur ,
            stats["files"] += 1  # info: stats [ "files" ] += 1
            return  # info: return

        if is_stub(cur):  # info: if is_stub ( cur ) :
            out.append(fmt(cur, "dir-stub"))  # info: out . append ( fmt ( cur ,
            stats["stubs"] += 1  # info: stats [ "stubs" ] += 1
            mtimes[posix] = st.st_mtime  # info: mtimes [ posix ] = st . st_mtime
            return  # info: return

        prev = mtimes.get(posix)  # info: set prev
        if prev is not None and prev == st.st_mtime and old_paths:  # info: if prev is not None and prev ==
            reused = slice_prefix(old_paths, posix)  # info: set reused
            if reused:  # info: if reused :
                out.extend(reused)  # info: out . extend ( reused )
                stats["reused_dirs"] += 1  # info: stats [ "reused_dirs" ] += 1
                return  # info: return

        stats["rewalked_dirs"] += 1  # info: stats [ "rewalked_dirs" ] += 1
        out.append(fmt(cur, "dir"))  # info: out . append ( fmt ( cur ,
        mtimes[posix] = st.st_mtime  # info: mtimes [ posix ] = st . st_mtime
        try:  # info: try :
            with os.scandir(cur) as it:  # info: with os . scandir ( cur ) as
                kids = sorted(it, key=lambda ent: ent.name.lower())  # info: set kids
        except OSError:  # info: except OSError :
            out.append(fmt(cur, "error"))  # info: out . append ( fmt ( cur ,
            stats["errors"] += 1  # info: stats [ "errors" ] += 1
            return  # info: return
        for ent in kids:  # info: for ent in kids :
            rec(Path(ent.path))  # info: call rec

    rec(root)  # info: call rec
    return out  # info: return out


# ====================================================
# SECTION: function merge
# What it does: merge.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def merge(parts: list[list[str]]) -> list[str]:  # info: def merge
    seen: set[str] = set()  # info: set seen
    merged: list[str] = []  # info: set merged
    for block in parts:  # info: for block in parts :
        for line in block:  # info: for line in block :
            key = line.split("\t", 1)[0]  # info: set key
            if key in seen:  # info: if key in seen :
                continue  # info: continue
            seen.add(key)  # info: seen . add ( key )
            merged.append(line)  # info: merged . append ( line )
    merged.sort(key=lambda line: line.split("\t", 1)[0].lower())  # info: merged . sort ( key = lambda line
    return merged  # info: return merged


# ====================================================
# SECTION: function write_current
# What it does: write current.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_current(path: Path, stats: dict, n_paths: int, roots: list[Path]) -> None:  # info: def write_current
    lines = [  # info: set lines
        "# Path index run",
        "",  # info: "" ,
        f"Generated {now_iso()}.",  # info: f" Generated { now_iso ( ) } .
        "",  # info: "" ,
        f"- roots walked: {len(roots)}",  # info: f" - roots walked: { len ( roots ) }
        f"- paths indexed: {n_paths}",  # info: f" - paths indexed: { n_paths } " ,
        f"- dir re-walks: {stats.get('rewalked_dirs', 0)}",  # info: f" - dir re-walks: { stats . get ( 'rewalked_dirs'
        f"- dirs reused: {stats.get('reused_dirs', 0)}",  # info: f" - dirs reused: { stats . get ( 'reused_dirs'
        f"- stubs: {stats.get('stubs', 0)}",  # info: f" - stubs: { stats . get ( 'stubs'
        f"- errors: {stats.get('errors', 0)}",  # info: f" - errors: { stats . get ( 'errors'
        "",  # info: "" ,
    ]  # info: ]
    path.write_text("\n".join(lines), encoding="utf-8")  # info: path . write_text ( "\n" . join (


# ====================================================
# SECTION: function atomic_text
# What it does: atomic text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def atomic_text(path: Path, text: str) -> None:  # info: def atomic_text
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(path.suffix + ".tmp")  # info: set tmp
    tmp.write_text(text, encoding="utf-8")  # info: tmp . write_text ( text , encoding =
    tmp.replace(path)  # info: tmp . replace ( path )


# ====================================================
# SECTION: function run
# What it does: run.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run(roots: list[Path], data: Path, log_dir: Path) -> int:  # info: def run
    paths_file = data / "paths.txt"  # info: set paths_file
    mtime_file = data / "dir-mtimes.json"  # info: set mtime_file
    current = log_dir / "current.md"  # info: set current
    old_paths = load_old(paths_file)  # info: set old_paths
    mtimes = load_mtimes(mtime_file)  # info: set mtimes
    stats = {  # info: set stats
        "visited": 0,  # info: "visited" : 0 ,
        "rewalked_dirs": 0,  # info: "rewalked_dirs" : 0 ,
        "reused_dirs": 0,  # info: "reused_dirs" : 0 ,
        "files": 0,  # info: "files" : 0 ,
        "stubs": 0,  # info: "stubs" : 0 ,
        "symlinks": 0,  # info: "symlinks" : 0 ,
        "errors": 0,  # info: "errors" : 0 ,
        "missing": 0,  # info: "missing" : 0 ,
    }  # info: }
    seen: set[tuple[int, int]] = set()  # info: set seen
    blocks = [  # info: set blocks
        walk_tree(root, old_paths=old_paths, mtimes=mtimes, seen=seen, stats=stats)  # info: call walk_tree
        for root in roots  # info: for root in roots
    ]  # info: ]
    merged = merge(blocks)  # info: set merged
    body = "\n".join(merged) + ("\n" if merged else "")  # info: set body
    atomic_text(paths_file, body)  # info: call atomic_text
    atomic_text(mtime_file, json.dumps(mtimes, indent=0, sort_keys=True) + "\n")  # info: call atomic_text
    log_dir.mkdir(parents=True, exist_ok=True)  # info: log_dir . mkdir ( parents = True ,
    write_current(current, stats, len(merged), roots)  # info: call write_current
    print(  # info: call print
        f"paths={len(merged)} rewalk={stats['rewalked_dirs']} "  # info: f" paths= { len ( merged ) }
        f"reuse_dirs={stats['reused_dirs']} stubs={stats['stubs']} errors={stats['errors']}"  # info: f" reuse_dirs= { stats [ 'reused_dirs' ] }
    )  # info: )
    return 0  # info: return 0


# ====================================================
# SECTION: function parse_args
# What it does: parse args.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_args(argv: list[str]) -> tuple[list[Path], Path, Path, bool]:  # info: def parse_args
    fixture = False  # info: set fixture
    roots: list[Path] = []  # info: set roots
    out: Path | None = None  # info: set out
    i = 0  # info: set i
    while i < len(argv):  # info: while i < len ( argv ) :
        arg = argv[i]  # info: set arg
        if arg == "--fixture":  # info: if arg == "--fixture" :
            fixture = True  # info: set fixture
            i += 1  # info: set i
            if i >= len(argv):  # info: if i >= len ( argv ) :
                raise SystemExit("refused: --fixture needs a directory")  # info: raise SystemExit ( "refused: --fixture needs a directory" )
            roots.append(Path(argv[i]))  # info: roots . append ( Path ( argv [
        elif arg == "--out":  # info: elif arg == "--out" :
            i += 1  # info: set i
            if i >= len(argv):  # info: if i >= len ( argv ) :
                raise SystemExit("refused: --out needs a directory")  # info: raise SystemExit ( "refused: --out needs a directory" )
            out = Path(argv[i])  # info: set out
        elif arg == "--root":  # info: elif arg == "--root" :
            i += 1  # info: set i
            if i >= len(argv):  # info: if i >= len ( argv ) :
                raise SystemExit("refused: --root needs a directory")  # info: raise SystemExit ( "refused: --root needs a directory" )
            roots.append(Path(argv[i]))  # info: roots . append ( Path ( argv [
        else:  # info: else :
            raise SystemExit(f"refused: unknown argument {arg}")  # info: raise SystemExit ( f" refused: unknown argument { arg }
        i += 1  # info: set i
    if fixture:  # info: if fixture :
        if out is None:  # info: if out is None :
            raise SystemExit("refused: --fixture needs --out")  # info: raise SystemExit ( "refused: --fixture needs --out" )
        if not under(out, Path(tempfile.gettempdir())):  # info: if not under ( out , Path (
            raise SystemExit("refused: --out is outside the temp directory")  # info: raise SystemExit ( "refused: --out is outside the temp directory" )
        return roots, out, out, True  # info: return roots , out , out , True
    data, log_dir = DATA, LOG_DIR  # info: data , log_dir = DATA , LOG_DIR
    if not roots:  # info: if not roots :
        roots = list(ALLOW)  # info: set roots
    return roots, data, log_dir, False  # info: return roots , data , log_dir , False


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(argv: list[str] | None = None) -> int:  # info: def main
    roots, data, log_dir, fixture = parse_args(list(sys.argv[1:] if argv is None else argv))  # info: roots , data , log_dir , fixture =
    for root in roots:  # info: for root in roots :
        if not accepted(root, fixture=fixture):  # info: if not accepted ( root , fixture =
            print(f"refused root: {root}", file=sys.stderr)  # info: call print
            return 2  # info: return 2
    return run(roots, data, log_dir)  # info: return run ( roots , data , log_dir


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
