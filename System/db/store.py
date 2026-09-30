# ==============================================================================
# FILE: System/db/store.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""SYSTEM raw + per-layer SQLite helpers (mirrors energy/db/store pattern)."""  # info: """SYSTEM raw + per-layer SQLite helpers (mirrors energy/db/store pattern)."""
from __future__ import annotations  # info: from __future__ import annotations
import sqlite3  # info: import sqlite3
import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

# lib/ is on PYTHONPATH when the skill runs; also support direct import
_SKILL = Path(__file__).resolve().parents[1]  # info: set _SKILL
if str(_SKILL / "lib") not in sys.path:  # info: if str ( _SKILL / "lib" ) not
    sys.path.insert(0, str(_SKILL / "lib"))  # info: sys . path . insert ( 0 ,
import paths  # noqa: E402

SCHEMA = Path(__file__).resolve().parent / "schema.sql"  # info: set SCHEMA

# ====================================================
# SECTION: function connect
# What it does: connect.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connect(db_path: Path | None = None) -> sqlite3.Connection:  # info: def connect
    path = Path(db_path) if db_path else paths.SYSTEM_DB  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    conn = sqlite3.connect(str(path), timeout=30)  # info: set conn
    conn.row_factory = sqlite3.Row  # info: conn . row_factory = sqlite3 . Row
    conn.execute("PRAGMA foreign_keys = ON")  # info: conn . execute ( "PRAGMA foreign_keys = ON" )
    conn.execute("PRAGMA journal_mode = WAL")  # info: conn . execute ( "PRAGMA journal_mode = WAL" )
    return conn  # info: return conn

# ====================================================
# SECTION: function connect_layer
# What it does: connect layer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connect_layer(layer: str, layers_dir: Path | None = None) -> sqlite3.Connection:  # info: def connect_layer
    if layer not in paths.LAYERS:  # info: if layer not in paths . LAYERS :
        raise ValueError(f"unknown layer: {layer}")  # info: raise ValueError ( f" unknown layer: { layer }
    d = Path(layers_dir) if layers_dir else paths.LAYERS_DIR  # info: set d
    d.mkdir(parents=True, exist_ok=True)  # info: d . mkdir ( parents = True ,
    path = d / f"{layer}.db"  # info: set path
    conn = connect(path)  # info: set conn
    initialize_schema(conn)  # info: call initialize_schema
    return conn  # info: return conn

# ====================================================
# SECTION: function initialize_schema
# What it does: initialize schema.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def initialize_schema(conn: sqlite3.Connection) -> None:  # info: def initialize_schema
    sql = SCHEMA.read_text(encoding="utf-8")  # info: set sql
    conn.executescript(sql)  # info: conn . executescript ( sql )
    conn.commit()  # info: conn . commit ( )

# ====================================================
# SECTION: function insert_observation
# What it does: insert observation.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def insert_observation(conn: sqlite3.Connection, observed_at: str, host: str, source: str = "proc") -> int:  # info: def insert_observation
    cur = conn.execute(  # info: set cur
        """INSERT INTO observation (observed_at, host, source)
           VALUES (?, ?, ?)
           ON CONFLICT(observed_at, host, source) DO UPDATE SET observed_at=excluded.observed_at
           RETURNING observation_id""",
        (observed_at, host, source),  # info: call (
    )  # info: )
    row = cur.fetchone()  # info: set row
    if row is None:  # info: if row is None :
        row = conn.execute(  # info: set row
            "SELECT observation_id FROM observation WHERE observed_at=? AND host=? AND source=?",  # info: "SELECT observation_id FROM observation WHERE observed_at=? AND host=? AND source=?" ,
            (observed_at, host, source),  # info: call (
        ).fetchone()  # info: ) . fetchone ( )
    return int(row[0])  # info: return int ( row [ 0 ] )

# ====================================================
# SECTION: function insert_measurement
# What it does: insert measurement.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def insert_measurement(conn: sqlite3.Connection, observation_id: int, metric_key: str,  # info: def insert_measurement
                       value, unit: str | None, state: str) -> None:  # info: value , unit : str | None ,
    conn.execute(  # info: conn . execute (
        """INSERT INTO measurement (observation_id, metric_key, value_num, unit, state)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(observation_id, metric_key) DO UPDATE SET
             value_num=excluded.value_num, unit=excluded.unit, state=excluded.state""",
        (observation_id, metric_key, value, unit, state),  # info: call (
    )  # info: )

# ====================================================
# SECTION: function persist_snapshot
# What it does: Write one system snapshot into the raw SYSTEM db. Returns observation_id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persist_snapshot(snap: dict, db_path: Path | None = None) -> int:  # info: def persist_snapshot
    """Write one system snapshot into the raw SYSTEM db. Returns observation_id."""  # info: """Write one system snapshot into the raw SYSTEM db. Returns observation_id."""
    paths.ensure_dirs()  # info: paths . ensure_dirs ( )
    conn = connect(db_path)  # info: set conn
    try:  # info: try :
        initialize_schema(conn)  # info: call initialize_schema
        obs_id = insert_observation(conn, snap["at"], snap.get("host") or "host", snap.get("source") or "proc")  # info: set obs_id
        for key, cell in (snap.get("fields") or {}).items():  # info: for key , cell in ( snap .
            insert_measurement(  # info: call insert_measurement
                conn,  # info: conn ,
                obs_id,  # info: obs_id ,
                key,  # info: key ,
                cell.get("value"),  # info: cell . get ( "value" ) ,
                cell.get("unit"),  # info: cell . get ( "unit" ) ,
                cell.get("state") or "missing",  # info: cell . get ( "state" ) or "missing"
            )  # info: )
        conn.commit()  # info: conn . commit ( )
        return obs_id  # info: return obs_id
    finally:  # info: finally :
        conn.close()  # info: conn . close ( )
