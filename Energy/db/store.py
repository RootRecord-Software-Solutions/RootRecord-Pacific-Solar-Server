# ==============================================================================
# FILE: Energy/db/store.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""RootRecord SQLite persistence primitives.

This module defines the write boundary for the new data layer. It does not
initialize the production database automatically.
"""

from __future__ import annotations  # info: from __future__ import annotations

import sqlite3  # info: import sqlite3
from pathlib import Path  # info: from pathlib import Path
import os  # info: import os
from typing import Any, Iterable, Mapping, Optional  # info: from typing import Any , Iterable , Mapping

SCHEMA_PATH = Path(__file__).with_name("schema.sql")  # info: set SCHEMA_PATH
DEFAULT_DB_PATH = Path(os.environ.get("ROOTRECORD_DB", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/layers/1sec.db"))  # info: raw samples live in the finest layer file — no separate rootrecord.db


# ====================================================
# SECTION: function connect
# What it does: Open a RootRecord SQLite connection with integrity/safety defaults.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:  # info: def connect
    """Open a RootRecord SQLite connection with integrity/safety defaults."""  # info: """Open a RootRecord SQLite connection with integrity/safety defaults."""
    db_path = Path(db_path)  # info: set db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)  # info: db_path . parent . mkdir ( parents =
    conn = sqlite3.connect(str(db_path))  # info: set conn
    conn.row_factory = sqlite3.Row  # info: conn . row_factory = sqlite3 . Row
    conn.execute("PRAGMA foreign_keys = ON")  # info: conn . execute ( "PRAGMA foreign_keys = ON" )
    conn.execute("PRAGMA journal_mode = WAL")  # info: conn . execute ( "PRAGMA journal_mode = WAL" )
    conn.execute("PRAGMA synchronous = NORMAL")  # info: conn . execute ( "PRAGMA synchronous = NORMAL" )
    return conn  # info: return conn


# ====================================================
# SECTION: function initialize_schema
# What it does: Create raw-telemetry schema objects only. Aggregation layers live in their own per-layer db files now — see initialize_layer_schema().
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def initialize_schema(conn: sqlite3.Connection) -> None:  # info: def initialize_schema
    """Create raw-telemetry schema objects only. Aggregation layers live in
    their own per-layer db files now — see initialize_layer_schema()."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))  # info: conn . executescript ( SCHEMA_PATH . read_text (
    conn.execute(  # info: conn . execute (
        "INSERT OR IGNORE INTO schema_version(version, applied_at) "  # info: "INSERT OR IGNORE INTO schema_version(version, applied_at) "
        "VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"  # info: "VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
    )  # info: )
    conn.execute(  # info: conn . execute (
        "INSERT OR IGNORE INTO schema_version(version, applied_at) "  # info: "INSERT OR IGNORE INTO schema_version(version, applied_at) "
        "VALUES (2, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"  # info: "VALUES (2, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
    )  # info: )
    conn.commit()  # info: conn . commit ( )


LAYERS_DIR = Path(os.environ.get("ROOTRECORD_LAYERS_DIR", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/layers"))  # info: set LAYERS_DIR
LAYER_SCHEMA_PATH = Path(__file__).with_name("schema_layers.sql")  # info: set LAYER_SCHEMA_PATH


# ====================================================
# SECTION: function layer_db_path
# What it does: Path to the standalone db file for one aggregation layer (e.g. '1min.db').
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def layer_db_path(layer: str, layers_dir: Path | str = LAYERS_DIR) -> Path:  # info: def layer_db_path
    """Path to the standalone db file for one aggregation layer (e.g. '1min.db')."""  # info: """Path to the standalone db file for one aggregation layer (e.g. '1min.db')."""
    return Path(layers_dir) / f"{layer}.db"  # info: return Path ( layers_dir ) / f" {


# ====================================================
# SECTION: function initialize_layer_schema
# What it does: initialize layer schema.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def initialize_layer_schema(conn: sqlite3.Connection) -> None:  # info: def initialize_layer_schema
    conn.executescript(LAYER_SCHEMA_PATH.read_text(encoding="utf-8"))  # info: conn . executescript ( LAYER_SCHEMA_PATH . read_text (
    conn.execute(  # info: conn . execute (
        "INSERT OR IGNORE INTO schema_version(version, applied_at) "  # info: "INSERT OR IGNORE INTO schema_version(version, applied_at) "
        "VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"  # info: "VALUES (1, strftime('%Y-%m-%dT%H:%M:%fZ','now'))"
    )  # info: )
    conn.commit()  # info: conn . commit ( )


# ====================================================
# SECTION: function connect_layer
# What it does: Open one layer's own db file. When the raw store is a different file, ATTACH it as 'raw' for aggregate_period(); when raw is layers/1sec.db itself, skip ATTACH so SQLite is not asked to open the same file twice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connect_layer(  # info: def connect_layer
    layer: str,  # info: set layer
    raw_db_path: Path | str = DEFAULT_DB_PATH,  # info: set raw_db_path
    layers_dir: Path | str = LAYERS_DIR,  # info: set layers_dir
) -> sqlite3.Connection:  # info: ) -> sqlite3 . Connection :
    """Open one layer db. ATTACH raw only when it is a different file than this layer."""  # info: docstring
    path = layer_db_path(layer, layers_dir)  # info: set path
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    conn = sqlite3.connect(str(path))  # info: set conn
    conn.row_factory = sqlite3.Row  # info: conn . row_factory = sqlite3 . Row
    conn.execute("PRAGMA foreign_keys = ON")  # info: conn . execute ( "PRAGMA foreign_keys = ON" )
    conn.execute("PRAGMA journal_mode = WAL")  # info: conn . execute ( "PRAGMA journal_mode = WAL" )
    conn.execute("PRAGMA synchronous = NORMAL")  # info: conn . execute ( "PRAGMA synchronous = NORMAL" )
    initialize_layer_schema(conn)  # info: call initialize_layer_schema
    raw_path = Path(raw_db_path)  # info: set raw_path
    if path.resolve() != raw_path.resolve():  # info: same-file ATTACH fails; 1sec holds raw + its aggregates
        conn.execute("ATTACH DATABASE ? AS raw", (str(raw_path),))  # info: conn . execute ( "ATTACH DATABASE ? AS raw" , ( str
    return conn  # info: return conn


# ====================================================
# SECTION: function upsert_device
# What it does: Create/update stable device identity and return device_id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def upsert_device(  # info: def upsert_device
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    serial_number: str,  # info: set serial_number
    model: str,  # info: set model
    alias: Optional[str] = None,  # info: set alias
    role: Optional[str] = None,  # info: set role
    ble_address: Optional[str] = None,  # info: set ble_address
    observed_at: Optional[str] = None,  # info: set observed_at
) -> int:  # info: ) -> int :
    """Create/update stable device identity and return device_id."""  # info: """Create/update stable device identity and return device_id."""
    now = observed_at or "1970-01-01T00:00:00.000Z"  # info: set now
    conn.execute(  # info: conn . execute (
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
        (serial_number, model, alias, role, ble_address, now, now, now, now),  # info: call (
    )  # info: )
    return int(  # info: return int (
        conn.execute(  # info: conn . execute (
            "SELECT device_id FROM device WHERE serial_number=?", (serial_number,)  # info: call "SELECT device_id FROM device WHERE serial_number=?"
        ).fetchone()[0]  # info: ) . fetchone ( ) [ 0 ]
    )  # info: )


# ====================================================
# SECTION: function upsert_battery
# What it does: Create/update a primary or expansion battery identity.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def upsert_battery(  # info: def upsert_battery
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    device_id: int,  # info: set device_id
    battery_role: str,  # info: set battery_role
    battery_slot: Optional[int],  # info: set battery_slot
    serial_number: Optional[str],  # info: set serial_number
    enabled: Optional[bool],  # info: set enabled
    observed_at: str,  # info: set observed_at
) -> int:  # info: ) -> int :
    """Create/update a primary or expansion battery identity."""  # info: """Create/update a primary or expansion battery identity."""
    conn.execute(  # info: conn . execute (
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
        (  # info: call (
            device_id, battery_role, battery_slot, serial_number,  # info: device_id , battery_role , battery_slot , serial_number ,
            None if enabled is None else int(enabled),  # info: None if enabled is None else int (
            observed_at, observed_at, observed_at, observed_at,  # info: observed_at , observed_at , observed_at , observed_at ,
        ),  # info: ) ,
    )  # info: )
    row = conn.execute(  # info: set row
        """
        SELECT battery_id FROM battery
        WHERE device_id=? AND battery_role=? AND battery_slot IS ?
        """,
        (device_id, battery_role, battery_slot),  # info: call (
    ).fetchone()  # info: ) . fetchone ( )
    return int(row[0])  # info: return int ( row [ 0 ] )


# ====================================================
# SECTION: function create_observation
# What it does: Insert or retrieve an immutable observation envelope.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def create_observation(  # info: def create_observation
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    device_id: int,  # info: set device_id
    observed_at: str,  # info: set observed_at
    source_id: int,  # info: set source_id
    online: Optional[bool] = None,  # info: set online
    connection_state: Optional[str] = None,  # info: set connection_state
    source_sequence: Optional[int] = None,  # info: set source_sequence
    quality: Optional[str] = None,  # info: set quality
) -> int:  # info: ) -> int :
    """Insert or retrieve an immutable observation envelope."""  # info: """Insert or retrieve an immutable observation envelope."""
    conn.execute(  # info: conn . execute (
        """
        INSERT OR IGNORE INTO observation(
            device_id, observed_at, source_id, online, connection_state,
            source_sequence, quality, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        """,
        (  # info: call (
            device_id, observed_at, source_id,  # info: device_id , observed_at , source_id ,
            None if online is None else int(online),  # info: None if online is None else int (
            connection_state, source_sequence, quality,  # info: connection_state , source_sequence , quality ,
        ),  # info: ) ,
    )  # info: )
    row = conn.execute(  # info: set row
        """
        SELECT observation_id FROM observation
        WHERE device_id=? AND observed_at=? AND source_id=?
          AND source_sequence IS ?
        """,
        (device_id, observed_at, source_id, source_sequence),  # info: call (
    ).fetchone()  # info: ) . fetchone ( )
    return int(row[0])  # info: return int ( row [ 0 ] )


# ====================================================
# SECTION: function _value_columns
# What it does:  value columns.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _value_columns(value: Any) -> tuple[Optional[float], Optional[str], Optional[int]]:  # info: def _value_columns
    if isinstance(value, bool):  # info: if isinstance ( value , bool ) :
        return None, None, int(value)  # info: return None , None , int ( value
    if isinstance(value, (int, float)):  # info: if isinstance ( value , ( int ,
        return float(value), None, None  # info: return float ( value ) , None ,
    if value is None:  # info: if value is None :
        return None, None, None  # info: return None , None , None
    return None, str(value), None  # info: return None , str ( value ) ,



# ====================================================
# SECTION: function _coerce_state_value
# What it does:  coerce state value.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _coerce_state_value(value, state: str):  # info: def _coerce_state_value
    n, text_v, boolean = _value_columns(value)  # info: n , text_v , boolean = _value_columns (
    filled = sum(x is not None for x in (n, text_v, boolean))  # info: set filled
    if filled == 0:  # info: if filled == 0 :
        if state in ("measured", "defaulted"):  # info: if state in ( "measured" , "defaulted" )
            state = "missing"  # info: set state
        return None, None, None, state  # info: return None , None , None , state
    if filled > 1:  # info: if filled > 1 :
        if n is not None:  # info: if n is not None :
            text_v = boolean = None  # info: set text_v
        elif boolean is not None:  # info: elif boolean is not None :
            n = text_v = None  # info: set n
        else:  # info: else :
            n = boolean = None  # info: set n
    if state in ("missing", "not_applicable"):  # info: if state in ( "missing" , "not_applicable" )
        state = "measured"  # info: set state
    return n, text_v, boolean, state  # info: return n , text_v , boolean , state

# ====================================================
# SECTION: function add_device_measurement
# What it does: Persist one device metric while preserving missing/not-applicable state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_device_measurement(  # info: def add_device_measurement
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    observation_id: int,  # info: set observation_id
    metric_key: str,  # info: set metric_key
    value: Any = None,  # info: set value
    unit: Optional[str] = None,  # info: set unit
    state: str = "measured",  # info: set state
) -> None:  # info: ) -> None :
    """Persist one device metric while preserving missing/not-applicable state."""  # info: """Persist one device metric while preserving missing/not-applicable state."""
    n, text, boolean, state = _coerce_state_value(value, state)  # info: n , text , boolean , state =
    conn.execute(  # info: conn . execute (
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
        (observation_id, metric_key, n, text, boolean, unit, state),  # info: call (
    )  # info: )


# ====================================================
# SECTION: function add_battery_measurement
# What it does: Persist one battery metric.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_battery_measurement(  # info: def add_battery_measurement
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    observation_id: int,  # info: set observation_id
    battery_id: int,  # info: set battery_id
    metric_key: str,  # info: set metric_key
    value: Any = None,  # info: set value
    unit: Optional[str] = None,  # info: set unit
    state: str = "measured",  # info: set state
) -> None:  # info: ) -> None :
    """Persist one battery metric."""  # info: """Persist one battery metric."""
    n, text, boolean, state = _coerce_state_value(value, state)  # info: n , text , boolean , state =
    conn.execute(  # info: conn . execute (
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
        (observation_id, battery_id, metric_key, n, text, boolean, unit, state),  # info: call (
    )  # info: )


# ====================================================
# SECTION: function add_electrical_measurement
# What it does: Persist one electrical channel measurement.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_electrical_measurement(  # info: def add_electrical_measurement
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    observation_id: int,  # info: set observation_id
    channel: str,  # info: set channel
    metric_key: str,  # info: set metric_key
    value: Optional[float] = None,  # info: set value
    unit: Optional[str] = None,  # info: set unit
    state: str = "measured",  # info: set state
) -> None:  # info: ) -> None :
    """Persist one electrical channel measurement."""  # info: """Persist one electrical channel measurement."""
    n, text, boolean, state = _coerce_state_value(value, state)  # info: n , text , boolean , state =
    conn.execute(  # info: conn . execute (
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
        (observation_id, channel, metric_key, n, unit, state),  # info: call (
    )  # info: )


# ====================================================
# SECTION: function add_port_measurement
# What it does: Persist one port measurement.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def add_port_measurement(  # info: def add_port_measurement
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    observation_id: int,  # info: set observation_id
    port_id: int,  # info: set port_id
    metric_key: str,  # info: set metric_key
    value: Any = None,  # info: set value
    unit: Optional[str] = None,  # info: set unit
    state: str = "measured",  # info: set state
) -> None:  # info: ) -> None :
    """Persist one port measurement."""  # info: """Persist one port measurement."""
    n, text, boolean, state = _coerce_state_value(value, state)  # info: n , text , boolean , state =
    conn.execute(  # info: conn . execute (
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
        (observation_id, port_id, metric_key, n, text, boolean, unit, state),  # info: call (
    )  # info: )


# ====================================================
# SECTION: function insert_raw_payload
# What it does: insert raw payload.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def insert_raw_payload(  # info: def insert_raw_payload
    conn: sqlite3.Connection,  # info: set conn
    *,  # info: * ,
    observation_id: int,  # info: set observation_id
    payload_format: str,  # info: set payload_format
    payload: str,  # info: set payload
    parser_name: Optional[str] = None,  # info: set parser_name
    parser_version: Optional[str] = None,  # info: set parser_version
) -> None:  # info: ) -> None :
    conn.execute(  # info: conn . execute (
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
        (observation_id, payload_format, payload, parser_name, parser_version),  # info: call (
    )  # info: )
