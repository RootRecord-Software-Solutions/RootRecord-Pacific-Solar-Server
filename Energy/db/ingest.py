# ==============================================================================
# FILE: Energy/db/ingest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""EcoFlow snapshot -> canonical SQLite ingestion bridge."""  # info: """EcoFlow snapshot -> canonical SQLite ingestion bridge."""
from __future__ import annotations  # info: from __future__ import annotations
import json  # info: import json
from typing import Any  # info: from typing import Any
from .store import add_battery_measurement, add_device_measurement, add_electrical_measurement, add_port_measurement, connect, create_observation, initialize_schema, insert_raw_payload, upsert_battery, upsert_device  # info: from . store import add_battery_measurement , add_device_measurement ,

# ====================================================
# SECTION: function _get
# What it does:  get.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(obj: Any, name: str, default: Any = None) -> Any:  # info: def _get
    return getattr(obj, name, default)  # info: return getattr ( obj , name , default

# ====================================================
# SECTION: function _serial
# What it does:  serial.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _serial(device: Any) -> str:  # info: def _serial
    raw = _get(device, "_sn")  # info: set raw
    if isinstance(raw, bytes):  # info: if isinstance ( raw , bytes ) :
        return raw.decode(errors="replace")  # info: return raw . decode ( errors = "replace"
    return str(raw or "UNKNOWN")  # info: return str ( raw or "UNKNOWN" )

# ====================================================
# SECTION: function _state
# What it does: State must match CHECK: measured/defaulted need a value; null → missing/not_applicable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _state(device: Any, attr: str, value: Any) -> str:  # info: def _state
    """State must match CHECK: measured/defaulted need a value; null → missing/not_applicable."""  # info: """State must match CHECK: measured/defaulted need a value; null → missing/not_applicable."""
    ac_attrs = {  # info: set ac_attrs
        "ac_output_power", "ac_input_power",  # info: "ac_output_power" , "ac_input_power" ,
        "ac_output_voltage", "ac_output_current",  # info: "ac_output_voltage" , "ac_output_current" ,
        "ac_input_voltage", "ac_input_current",  # info: "ac_input_voltage" , "ac_input_current" ,
        "ac_charging", "ac_charging_speed",  # info: "ac_charging" , "ac_charging_speed" ,
    }  # info: }
    if attr in ac_attrs and getattr(device, "ac_ports", None) is False:  # info: if attr in ac_attrs and getattr ( device
        return "not_applicable"  # info: return "not_applicable"
    if value is not None:  # info: if value is not None :
        return "measured"  # info: return "measured"
    # Never return "defaulted" with a null value (violates CHECK).
    return "missing"  # info: return "missing"

# ====================================================
# SECTION: function _ensure_port
# What it does:  ensure port.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ensure_port(conn, device_id, port_type, index=0):  # info: def _ensure_port
    conn.execute("""INSERT INTO device_port(device_id,port_type,port_index)
                    VALUES (?,?,?)
                    ON CONFLICT(device_id,port_type,port_index) DO NOTHING""",
                 (device_id, port_type, index))  # info: call (
    return conn.execute("""SELECT port_id FROM device_port
                           WHERE device_id=? AND port_type=? AND port_index=?""",
                        (device_id, port_type, index)).fetchone()[0]  # info: call (

# ====================================================
# SECTION: function persist_eflow_device
# What it does: persist eflow device.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persist_eflow_device(device: Any, alias: str, observed_at: str) -> int:  # info: def persist_eflow_device
    conn = connect()  # info: set conn
    try:  # info: try :
        initialize_schema(conn)  # info: call initialize_schema
        row = conn.execute("""SELECT source_id FROM observation_source
                              WHERE source_type='BLE' AND source_name='eflib'
                              LIMIT 1""").fetchone()
        if row:  # info: if row :
            source_id = row[0]  # info: set source_id
        else:  # info: else :
            source_id = conn.execute("""INSERT INTO observation_source
                (source_type,source_name,parser_name,parser_version,created_at)
                VALUES ('BLE','eflib','RootRecord EcoFlow ingest','1',
                        strftime('%Y-%m-%dT%H:%M:%fZ','now'))""").lastrowid

        device_id = upsert_device(  # info: set device_id
            conn, serial_number=_serial(device),  # info: conn , serial_number = _serial ( device )
            model=str(_get(device, "device", type(device).__name__)),  # info: set model
            alias=alias, role="primary_power_storage",  # info: set alias
            observed_at=observed_at)  # info: set observed_at
        observation_id = create_observation(  # info: set observation_id
            conn, device_id=device_id, observed_at=observed_at,  # info: conn , device_id = device_id , observed_at =
            source_id=source_id, online=True, connection_state="connected")  # info: set source_id

        primary = upsert_battery(  # info: set primary
            conn, device_id=device_id, battery_role="primary", battery_slot=0,  # info: conn , device_id = device_id , battery_role =
            serial_number=None, enabled=True, observed_at=observed_at)  # info: set serial_number

        for attr, metric, unit in [  # info: for attr , metric , unit in [
            ("battery_level","soc_percent","%"),  # info: call (
            ("battery_voltage","voltage_v","V"),  # info: call (
            ("max_cell_voltage","cell_voltage_max_v","V"),  # info: call (
            ("min_cell_voltage","cell_voltage_min_v","V"),  # info: call (
            ("cell_temperature","temperature_c","C"),  # info: call (
            ("battery_charge_limit_min","charge_limit_min_pct","%"),  # info: call (
            ("battery_charge_limit_max","charge_limit_max_pct","%"),  # info: call (
            ("remaining_time_charging","remaining_charge_s","s"),  # info: call (
            ("remaining_time_discharging","remaining_discharge_s","s")]:  # info: call (
            if hasattr(device, attr):  # info: if hasattr ( device , attr ) :
                v=_get(device,attr)  # info: set v
                add_battery_measurement(conn, observation_id=observation_id,  # info: call add_battery_measurement
                    battery_id=primary, metric_key=metric, value=v, unit=unit,  # info: set battery_id
                    state=_state(device, attr, v))  # info: set state

        for attr, metric, unit in [  # info: for attr , metric , unit in [
            ("input_power","input_power","W"),("output_power","output_power","W"),  # info: call (
            ("battery_charge_limit_min","battery_charge_limit_min","%"),  # info: call (
            ("battery_charge_limit_max","battery_charge_limit_max","%"),  # info: call (
            ("remaining_time_charging","remaining_time_charging","s"),  # info: call (
            ("remaining_time_discharging","remaining_time_discharging","s"),  # info: call (
            ("energy_backup","energy_backup",None),("energy_backup_battery_level","energy_backup_battery_level","%"),  # info: call (
            ("ac_ports","ac_ports",None),("usb_ports","usb_ports",None),  # info: call (
            ("dc_12v_port","dc_12v_port",None),("ac_charging","ac_charging",None),  # info: call (
            ("ac_charging_speed","ac_charging_speed","W"),("dc_mode","dc_mode",None),  # info: call (
            ("dc_charging_max_amps","dc_charging_max_amps","A")]:  # info: call (
            if hasattr(device, attr):  # info: if hasattr ( device , attr ) :
                v=_get(device,attr)  # info: set v
                add_device_measurement(conn, observation_id=observation_id,  # info: call add_device_measurement
                    metric_key=metric, value=v, unit=unit, state=_state(device, attr, v))  # info: set metric_key

        for attr, channel, metric, unit in [  # info: for attr , channel , metric , unit
            ("input_power","input_total","power_w","W"),("output_power","output_total","power_w","W"),  # info: call (
            ("ac_input_power","ac_input","power_w","W"),("ac_output_power","ac_output","power_w","W"),  # info: call (
            ("xt60_input_power","xt60_input","power_w","W"),("solar_input_power","solar_input","power_w","W"),  # info: call (
            ("car_input_power","car_input","power_w","W"),("dc12v_output_power","dc12v_output","power_w","W"),  # info: call (
            ("dc12v_output_voltage","dc12v_output","voltage_v","V"),("dc12v_output_current","dc12v_output","current_a","A"),  # info: call (
            ("dc_input_voltage","dc_input","voltage_v","V"),("dc_input_current","dc_input","current_a","A"),  # info: call (
            ("usbc_output_power","usb_c_1","power_w","W"),("usbc2_output_power","usb_c_2","power_w","W"),  # info: call (
            ("usba_output_power","usb_a_1","power_w","W"),("usba2_output_power","usb_a_2","power_w","W"),  # info: call (
            ("qc_usb1_output_power","qc_usb_1","power_w","W"),("qc_usb2_output_power","qc_usb_2","power_w","W"),  # info: call (
            ("ac_input_voltage","ac_input","voltage_v","V"),("ac_input_current","ac_input","current_a","A"),  # info: call (
            ("ac_output_voltage","ac_output","voltage_v","V"),("ac_output_current","ac_output","current_a","A")]:  # info: call (
            if hasattr(device, attr):  # info: if hasattr ( device , attr ) :
                v=_get(device,attr)  # info: set v
                add_electrical_measurement(conn, observation_id=observation_id,  # info: call add_electrical_measurement
                    channel=channel, metric_key=metric, value=v, unit=unit, state=_state(device, attr, v))  # info: set channel

        for ptype, attr in [("ac","ac_ports"),("usb","usb_ports"),("dc12v","dc_12v_port")]:  # info: for ptype , attr in [ ( "ac"
            if hasattr(device,attr):  # info: if hasattr ( device , attr ) :
                pid=_ensure_port(conn,device_id,ptype)  # info: set pid
                v=_get(device,attr)  # info: set v
                add_port_measurement(conn,observation_id=observation_id,port_id=pid,  # info: call add_port_measurement
                    metric_key="enabled",value=v,state=_state(device, attr, v))  # info: set metric_key

        for slot, prefix in ((1,"battery_1"),(2,"battery_2")):  # info: for slot , prefix in ( ( 1
            if not hasattr(device, f"{prefix}_enabled"):  # info: if not hasattr ( device , f" {
                continue  # info: continue
            enabled=_get(device,f"{prefix}_enabled")  # info: set enabled
            bid=upsert_battery(conn,device_id=device_id,battery_role="expansion",  # info: set bid
                battery_slot=slot,serial_number=_get(device,f"{prefix}_sn"),  # info: set battery_slot
                enabled=enabled,observed_at=observed_at)  # info: set enabled
            for attr,metric,unit in [  # info: for attr , metric , unit in [
                (f"{prefix}_battery_level","soc_percent","%"),  # info: call (
                (f"{prefix}_voltage","voltage_v","V"),  # info: call (
                (f"{prefix}_max_cell_voltage","cell_voltage_max_v","V"),  # info: call (
                (f"{prefix}_min_cell_voltage","cell_voltage_min_v","V"),  # info: call (
                (f"{prefix}_cell_temperature","temperature_c","C")]:  # info: call (
                if hasattr(device,attr):  # info: if hasattr ( device , attr ) :
                    v=_get(device,attr)  # info: set v
                    add_battery_measurement(conn,observation_id=observation_id,  # info: call add_battery_measurement
                        battery_id=bid,metric_key=metric,value=v,unit=unit,state=_state(device, attr, v))  # info: set battery_id

        insert_raw_payload(conn,observation_id=observation_id,  # info: call insert_raw_payload
            payload_format="normalized_snapshot",  # info: set payload_format
            payload=json.dumps({"alias":alias,"serial_number":_serial(device),  # info: set payload
                                "model":str(_get(device,"device",type(device).__name__))},  # info: "model" : str ( _get ( device ,
                               separators=(",",":")),  # info: set separators
            parser_name="RootRecord EcoFlow ingest",parser_version="1")  # info: set parser_name
        conn.commit()  # info: conn . commit ( )
        return observation_id  # info: return observation_id
    except Exception:  # info: except Exception :
        conn.rollback()  # info: conn . rollback ( )
        raise  # info: raise
    finally:  # info: finally :
        conn.close()  # info: conn . close ( )


# ====================================================
# SECTION: function persist_eflow_fields
# What it does: Persist a cloud (or other non-BLE) fields dict into Energy/rootrecord.db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persist_eflow_fields(fields: dict, alias: str, observed_at: str, source: str = "cloud") -> int:  # info: def persist_eflow_fields
    """Persist the same board field set BLE uses (soc/watts/ports). Cloud cannot invent missing keys."""  # info: docstring
    conn = connect()  # info: set conn
    try:  # info: try
        initialize_schema(conn)  # info: call initialize_schema
        source_type = "CLOUD" if str(source).startswith("cloud") else "API"  # info: set source_type
        row = conn.execute(  # info: set row
            "SELECT source_id FROM observation_source WHERE source_type=? AND source_name='ecoflow_quota' LIMIT 1",  # info: find the cloud source
            (source_type,),  # info: source_type
        ).fetchone()  # info: fetchone
        if row:  # info: if row
            source_id = row[0]  # info: set source_id
        else:  # info: else
            source_id = conn.execute(  # info: set source_id
                """INSERT INTO observation_source
                   (source_type,source_name,parser_name,parser_version,created_at)
                   VALUES (?,?,?,?,strftime('%Y-%m-%dT%H:%M:%fZ','now'))""",  # info: insert cloud source
                (source_type, "ecoflow_quota", "RootRecord EcoFlow cloud ingest", "1"),  # info: values
            ).lastrowid  # info: lastrowid
        existing = conn.execute("SELECT serial_number, model FROM device WHERE alias=? LIMIT 1", (alias,)).fetchone()  # info: set existing
        serial = existing["serial_number"] if existing else f"CLOUD:{alias}"  # info: set serial
        model = existing["model"] if existing else alias  # info: set model
        device_id = upsert_device(conn, serial_number=serial, model=model, alias=alias, role="primary_power_storage", observed_at=observed_at)  # info: set device_id
        observation_id = create_observation(conn, device_id=device_id, observed_at=observed_at, source_id=source_id, online=True, connection_state=str(source))  # info: set observation_id
        primary = upsert_battery(conn, device_id=device_id, battery_role="primary", battery_slot=0, serial_number=None, enabled=True, observed_at=observed_at)  # info: set primary
        soc = fields.get("soc")  # info: set soc
        add_battery_measurement(conn, observation_id=observation_id, battery_id=primary, metric_key="soc_percent", value=soc, unit="%", state="measured" if soc is not None else "missing")  # info: call add_battery_measurement
        for key, channel in (  # info: same watt channels the board reads from BLE
            ("ac_output_power", "ac_output"),  # info: AC out
            ("ac_input_power", "ac_input"),  # info: AC in
            ("solar_input_power", "solar_input"),  # info: solar
            ("usbc_output_power", "usb_c_1"),  # info: USB-C
            ("usba_output_power", "usb_a_1"),  # info: USB-A
        ):  # info: end map
            value = fields.get(key)  # info: set value
            add_electrical_measurement(conn, observation_id=observation_id, channel=channel, metric_key="power_w", value=value, unit="W", state="measured" if value is not None else "missing")  # info: call add_electrical_measurement
        out = fields.get("ac_output_power")  # info: set out
        solar = fields.get("solar_input_power")  # info: set solar
        add_device_measurement(conn, observation_id=observation_id, metric_key="output_power", value=out, unit="W", state="measured" if out is not None else "missing")  # info: call add_device_measurement
        add_device_measurement(conn, observation_id=observation_id, metric_key="input_power", value=solar, unit="W", state="measured" if solar is not None else "missing")  # info: call add_device_measurement
        board_keys = ("soc", "ac_output_power", "ac_input_power", "solar_input_power", "usbc_output_power", "usba_output_power", "ac_ports", "usb_ports", "dc_12v_port")  # info: set board_keys
        for key in ("ac_ports", "usb_ports", "dc_12v_port"):  # info: for key in port switches
            value = fields.get(key)  # info: set value
            add_device_measurement(conn, observation_id=observation_id, metric_key=key, value=value, unit=None, state="measured" if value is not None else "missing")  # info: call add_device_measurement
        for ptype, key in (("ac", "ac_ports"), ("usb", "usb_ports"), ("dc12v", "dc_12v_port")):  # info: for ptype , key
            if fields.get(key) is None:  # info: if fields . get ( key ) is None
                continue  # info: continue
            pid = _ensure_port(conn, device_id, ptype)  # info: set pid
            add_port_measurement(conn, observation_id=observation_id, port_id=pid, metric_key="enabled", value=fields.get(key), state="measured")  # info: call add_port_measurement
        insert_raw_payload(conn, observation_id=observation_id, payload_format="cloud_fields", payload=json.dumps({"alias": alias, "source": source, "fields": {k: fields.get(k) for k in board_keys}}, separators=(",", ":")), parser_name="RootRecord EcoFlow cloud ingest", parser_version="1")  # info: call insert_raw_payload
        conn.commit()  # info: conn . commit
        return observation_id  # info: return observation_id
    except Exception:  # info: except Exception
        conn.rollback()  # info: conn . rollback
        raise  # info: raise
    finally:  # info: finally
        conn.close()  # info: conn . close
