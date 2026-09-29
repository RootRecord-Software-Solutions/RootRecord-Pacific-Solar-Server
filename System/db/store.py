"""SYSTEM raw + per-layer SQLite helpers (mirrors energy/db/store pattern)."""
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

# lib/ is on PYTHONPATH when the skill runs; also support direct import
_SKILL = Path(__file__).resolve().parents[1]
if str(_SKILL / "lib") not in sys.path:
    sys.path.insert(0, str(_SKILL / "lib"))
import paths  # noqa: E402

SCHEMA = Path(__file__).resolve().parent / "schema.sql"

def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else paths.SYSTEM_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def connect_layer(layer: str, layers_dir: Path | None = None) -> sqlite3.Connection:
    if layer not in paths.LAYERS:
        raise ValueError(f"unknown layer: {layer}")
    d = Path(layers_dir) if layers_dir else paths.LAYERS_DIR
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{layer}.db"
    conn = connect(path)
    initialize_schema(conn)
    return conn

def initialize_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()

def insert_observation(conn: sqlite3.Connection, observed_at: str, host: str, source: str = "proc") -> int:
    cur = conn.execute(
        """INSERT INTO observation (observed_at, host, source)
           VALUES (?, ?, ?)
           ON CONFLICT(observed_at, host, source) DO UPDATE SET observed_at=excluded.observed_at
           RETURNING observation_id""",
        (observed_at, host, source),
    )
    row = cur.fetchone()
    if row is None:
        row = conn.execute(
            "SELECT observation_id FROM observation WHERE observed_at=? AND host=? AND source=?",
            (observed_at, host, source),
        ).fetchone()
    return int(row[0])

def insert_measurement(conn: sqlite3.Connection, observation_id: int, metric_key: str,
                       value, unit: str | None, state: str) -> None:
    conn.execute(
        """INSERT INTO measurement (observation_id, metric_key, value_num, unit, state)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(observation_id, metric_key) DO UPDATE SET
             value_num=excluded.value_num, unit=excluded.unit, state=excluded.state""",
        (observation_id, metric_key, value, unit, state),
    )

def persist_snapshot(snap: dict, db_path: Path | None = None) -> int:
    """Write one system snapshot into the raw SYSTEM db. Returns observation_id."""
    paths.ensure_dirs()
    conn = connect(db_path)
    try:
        initialize_schema(conn)
        obs_id = insert_observation(conn, snap["at"], snap.get("host") or "host", snap.get("source") or "proc")
        for key, cell in (snap.get("fields") or {}).items():
            insert_measurement(
                conn,
                obs_id,
                key,
                cell.get("value"),
                cell.get("unit"),
                cell.get("state") or "missing",
            )
        conn.commit()
        return obs_id
    finally:
        conn.close()
