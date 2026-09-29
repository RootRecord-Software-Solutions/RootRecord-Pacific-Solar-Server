"""RootRecord SQLite persistence primitives.

This module defines the write boundary for the new data layer. It does not
initialize the production database automatically.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DEFAULT_DB_PATH = Path("/home/rootrecord/Database/ROOTRECORD/rootrecord.db")


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a RootRecord SQLite connection with integrity/safety defaults."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create schema objects without creating any telemetry data."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    columns = {row[1] for row in conn.execute("PRAGMA table_info(aggregate_measurement)")}
    if "observed_span_s" not in columns:
        conn.execute("ALTER TABLE aggregate_measurement ADD COLUMN observed_span_s REAL")
    if "valid_duration_s" not in columns:
        conn.execute("ALTER TABLE aggregate_measurement ADD COLUMN valid_duration_s REAL")
    conn.execute(
        "INSERT OR IGNORE INTO schema_version(version, applied_at) "
        "VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
    )
    conn.execute(
        "INSERT OR IGNORE INTO schema_version(version, applied_at) "
        "VALUES (2, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
    )
    conn.commit()


def upsert_device(
    conn: sqlite3.Connection,
    *,
    serial_number: str,
    model: str,
    alias: Optional[str] = None,
    role: Optional[str] = None,
    ble_address: Optional[str] = None,
    observed_at: Optional[str] = None,
) -> int:
    """Create/update stable device identity and return device_id."""
    now = observed_at or "1970-01-01T00:00:00.000Z"
    conn.execute(
        """
        INSERT INTO device(
            serial_number, model, alias, role, ble_address,
            first_seen_at, last_seen_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(serial_number) DO UPDATE SET
            model=excluded.model,
            alias=COALESCE(excluded.alias, device.alias),
            role=COALESCE(excluded.role, device.role),
            ble_address=COALESCE(excluded.ble_address, device.ble_address),
            first_seen_at=COALESCE(device.first_seen_at, excluded.first_seen_at),
            last_seen_at=excluded.last_seen_at,
            updated_at=excluded.updated_at
        """,
        (serial_number, model, alias, role, ble_address, now, now, now, now),
    )
    return int(
        conn.execute(
            "SELECT device_id FROM device WHERE serial_number=?", (serial_number,)
        ).fetchone()[0]
    )


def upsert_battery(
    conn: sqlite3.Connection,
    *,
    device_id: int,
    battery_role: str,
    battery_slot: Optional[int],
    serial_number: Optional[str],
    enabled: Optional[bool],
    observed_at: str,
) -> int:
    """Create/update a primary or expansion battery identity."""
    conn.execute(
        """
        INSERT INTO battery(
            device_id, battery_role, battery_slot, serial_number, enabled,
            first_seen_at, last_seen_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(device_id, battery_role, battery_slot) DO UPDATE SET
            serial_number=COALESCE(excluded.serial_number, battery.serial_number),
            enabled=COALESCE(excluded.enabled, battery.enabled),
            first_seen_at=COALESCE(battery.first_seen_at, excluded.first_seen_at),
            last_seen_at=excluded.last_seen_at,
            updated_at=excluded.updated_at
        """,
        (
            device_id, battery_role, battery_slot, serial_number,
            None if enabled is None else int(enabled),
            observed_at, observed_at, observed_at, observed_at,
        ),
    )
    row = conn.execute(
        """
        SELECT battery_id FROM battery
        WHERE device_id=? AND battery_role=? AND battery_slot IS ?
        """,
        (device_id, battery_role, battery_slot),
    ).fetchone()
    return int(row[0])


def create_observation(
    conn: sqlite3.Connection,
    *,
    device_id: int,
    observed_at: str,
    source_id: int,
    online: Optional[bool] = None,
    connection_state: Optional[str] = None,
    source_sequence: Optional[int] = None,
    quality: Optional[str] = None,
) -> int:
    """Insert or retrieve an immutable observation envelope."""
    conn.execute(
        """
        INSERT OR IGNORE INTO observation(
            device_id, observed_at, source_id, online, connection_state,
            source_sequence, quality, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        """,
        (
            device_id, observed_at, source_id,
            None if online is None else int(online),
            connection_state, source_sequence, quality,
        ),
    )
    row = conn.execute(
        """
        SELECT observation_id FROM observation
        WHERE device_id=? AND observed_at=? AND source_id=?
          AND source_sequence IS ?
        """,
        (device_id, observed_at, source_id, source_sequence),
    ).fetchone()
    return int(row[0])


def _value_columns(value: Any) -> tuple[Optional[float], Optional[str], Optional[int]]:
    if isinstance(value, bool):
        return None, None, int(value)
    if isinstance(value, (int, float)):
        return float(value), None, None
    if value is None:
        return None, None, None
    return None, str(value), None



def _coerce_state_value(value, state: str):
    n, text_v, boolean = _value_columns(value)
    filled = sum(x is not None for x in (n, text_v, boolean))
    if filled == 0:
        if state in ("measured", "defaulted"):
            state = "missing"
        return None, None, None, state
    if filled > 1:
        if n is not None:
            text_v = boolean = None
        elif boolean is not None:
            n = text_v = None
        else:
            n = boolean = None
    if state in ("missing", "not_applicable"):
        state = "measured"
    return n, text_v, boolean, state

def add_device_measurement(
    conn: sqlite3.Connection,
    *,
    observation_id: int,
    metric_key: str,
    value: Any = None,
    unit: Optional[str] = None,
    state: str = "measured",
) -> None:
    """Persist one device metric while preserving missing/not-applicable state."""
    n, text, boolean, state = _coerce_state_value(value, state)
    conn.execute(
        """
        INSERT INTO device_measurement(
            observation_id, metric_key, value_num, value_text, value_bool,
            unit, state
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(observation_id, metric_key) DO UPDATE SET
            value_num=excluded.value_num,
            value_text=excluded.value_text,
            value_bool=excluded.value_bool,
            unit=excluded.unit,
            state=excluded.state
        """,
        (observation_id, metric_key, n, text, boolean, unit, state),
    )


def add_battery_measurement(
    conn: sqlite3.Connection,
    *,
    observation_id: int,
    battery_id: int,
    metric_key: str,
    value: Any = None,
    unit: Optional[str] = None,
    state: str = "measured",
) -> None:
    """Persist one battery metric."""
    n, text, boolean, state = _coerce_state_value(value, state)
    conn.execute(
        """
        INSERT INTO battery_measurement(
            observation_id, battery_id, metric_key, value_num, value_text,
            value_bool, unit, state
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(observation_id, battery_id, metric_key) DO UPDATE SET
            value_num=excluded.value_num,
            value_text=excluded.value_text,
            value_bool=excluded.value_bool,
            unit=excluded.unit,
            state=excluded.state
        """,
        (observation_id, battery_id, metric_key, n, text, boolean, unit, state),
    )


def add_electrical_measurement(
    conn: sqlite3.Connection,
    *,
    observation_id: int,
    channel: str,
    metric_key: str,
    value: Optional[float] = None,
    unit: Optional[str] = None,
    state: str = "measured",
) -> None:
    """Persist one electrical channel measurement."""
    conn.execute(
        """
        INSERT INTO electrical_measurement(
            observation_id, channel, metric_key, value_num, unit, state
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(observation_id, channel, metric_key) DO UPDATE SET
            value_num=excluded.value_num,
            unit=excluded.unit,
            state=excluded.state
        """,
        (observation_id, channel, metric_key, value, unit, state),
    )


def add_port_measurement(
    conn: sqlite3.Connection,
    *,
    observation_id: int,
    port_id: int,
    metric_key: str,
    value: Any = None,
    unit: Optional[str] = None,
    state: str = "measured",
) -> None:
    """Persist one port measurement."""
    n, text, boolean, state = _coerce_state_value(value, state)
    conn.execute(
        """
        INSERT INTO port_measurement(
            observation_id, port_id, metric_key, value_num, value_text,
            value_bool, unit, state
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(observation_id, port_id, metric_key) DO UPDATE SET
            value_num=excluded.value_num,
            value_text=excluded.value_text,
            value_bool=excluded.value_bool,
            unit=excluded.unit,
            state=excluded.state
        """,
        (observation_id, port_id, metric_key, n, text, boolean, unit, state),
    )


def insert_raw_payload(
    conn: sqlite3.Connection,
    *,
    observation_id: int,
    payload_format: str,
    payload: str,
    parser_name: Optional[str] = None,
    parser_version: Optional[str] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO observation_raw(
            observation_id, payload_format, payload, parser_name, parser_version
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(observation_id) DO UPDATE SET
            payload_format=excluded.payload_format,
            payload=excluded.payload,
            parser_name=excluded.parser_name,
            parser_version=excluded.parser_version
        """,
        (observation_id, payload_format, payload, parser_name, parser_version),
    )
