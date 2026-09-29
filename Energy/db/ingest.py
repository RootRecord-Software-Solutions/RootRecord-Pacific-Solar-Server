"""EcoFlow snapshot -> canonical SQLite ingestion bridge."""
from __future__ import annotations
import json
from typing import Any
from .store import add_battery_measurement, add_device_measurement, add_electrical_measurement, add_port_measurement, connect, create_observation, initialize_schema, insert_raw_payload, upsert_battery, upsert_device

def _get(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)

def _serial(device: Any) -> str:
    raw = _get(device, "_sn")
    if isinstance(raw, bytes):
        return raw.decode(errors="replace")
    return str(raw or "UNKNOWN")

def _state(device: Any, attr: str, value: Any) -> str:
    """State must match CHECK: measured/defaulted need a value; null → missing/not_applicable."""
    ac_attrs = {
        "ac_output_power", "ac_input_power",
        "ac_output_voltage", "ac_output_current",
        "ac_input_voltage", "ac_input_current",
        "ac_charging", "ac_charging_speed",
    }
    if attr in ac_attrs and getattr(device, "ac_ports", None) is False:
        return "not_applicable"
    if value is not None:
        return "measured"
    # Never return "defaulted" with a null value (violates CHECK).
    return "missing"

def _ensure_port(conn, device_id, port_type, index=0):
    conn.execute("""INSERT INTO device_port(device_id,port_type,port_index)
                    VALUES (?,?,?)
                    ON CONFLICT(device_id,port_type,port_index) DO NOTHING""",
                 (device_id, port_type, index))
    return conn.execute("""SELECT port_id FROM device_port
                           WHERE device_id=? AND port_type=? AND port_index=?""",
                        (device_id, port_type, index)).fetchone()[0]

def persist_eflow_device(device: Any, alias: str, observed_at: str) -> int:
    conn = connect()
    try:
        initialize_schema(conn)
        row = conn.execute("""SELECT source_id FROM observation_source
                              WHERE source_type='BLE' AND source_name='eflib'
                              LIMIT 1""").fetchone()
        if row:
            source_id = row[0]
        else:
            source_id = conn.execute("""INSERT INTO observation_source
                (source_type,source_name,parser_name,parser_version,created_at)
                VALUES ('BLE','eflib','RootRecord EcoFlow ingest','1',
                        strftime('%Y-%m-%dT%H:%M:%fZ','now'))""").lastrowid

        device_id = upsert_device(
            conn, serial_number=_serial(device),
            model=str(_get(device, "device", type(device).__name__)),
            alias=alias, role="primary_power_storage",
            observed_at=observed_at)
        observation_id = create_observation(
            conn, device_id=device_id, observed_at=observed_at,
            source_id=source_id, online=True, connection_state="connected")

        primary = upsert_battery(
            conn, device_id=device_id, battery_role="primary", battery_slot=0,
            serial_number=None, enabled=True, observed_at=observed_at)

        for attr, metric, unit in [
            ("battery_level","soc_percent","%"),
            ("battery_voltage","voltage_v","V"),
            ("max_cell_voltage","cell_voltage_max_v","V"),
            ("min_cell_voltage","cell_voltage_min_v","V"),
            ("cell_temperature","temperature_c","C"),
            ("battery_charge_limit_min","charge_limit_min_pct","%"),
            ("battery_charge_limit_max","charge_limit_max_pct","%"),
            ("remaining_time_charging","remaining_charge_s","s"),
            ("remaining_time_discharging","remaining_discharge_s","s")]:
            if hasattr(device, attr):
                v=_get(device,attr)
                add_battery_measurement(conn, observation_id=observation_id,
                    battery_id=primary, metric_key=metric, value=v, unit=unit,
                    state=_state(device, attr, v))

        for attr, metric, unit in [
            ("input_power","input_power","W"),("output_power","output_power","W"),
            ("battery_charge_limit_min","battery_charge_limit_min","%"),
            ("battery_charge_limit_max","battery_charge_limit_max","%"),
            ("remaining_time_charging","remaining_time_charging","s"),
            ("remaining_time_discharging","remaining_time_discharging","s"),
            ("energy_backup","energy_backup",None),("energy_backup_battery_level","energy_backup_battery_level","%"),
            ("ac_ports","ac_ports",None),("usb_ports","usb_ports",None),
            ("dc_12v_port","dc_12v_port",None),("ac_charging","ac_charging",None),
            ("ac_charging_speed","ac_charging_speed","W"),("dc_mode","dc_mode",None),
            ("dc_charging_max_amps","dc_charging_max_amps","A")]:
            if hasattr(device, attr):
                v=_get(device,attr)
                add_device_measurement(conn, observation_id=observation_id,
                    metric_key=metric, value=v, unit=unit, state=_state(device, attr, v))

        for attr, channel, metric, unit in [
            ("input_power","input_total","power_w","W"),("output_power","output_total","power_w","W"),
            ("ac_input_power","ac_input","power_w","W"),("ac_output_power","ac_output","power_w","W"),
            ("xt60_input_power","xt60_input","power_w","W"),("solar_input_power","solar_input","power_w","W"),
            ("car_input_power","car_input","power_w","W"),("dc12v_output_power","dc12v_output","power_w","W"),
            ("dc12v_output_voltage","dc12v_output","voltage_v","V"),("dc12v_output_current","dc12v_output","current_a","A"),
            ("dc_input_voltage","dc_input","voltage_v","V"),("dc_input_current","dc_input","current_a","A"),
            ("usbc_output_power","usb_c_1","power_w","W"),("usbc2_output_power","usb_c_2","power_w","W"),
            ("usba_output_power","usb_a_1","power_w","W"),("usba2_output_power","usb_a_2","power_w","W"),
            ("qc_usb1_output_power","qc_usb_1","power_w","W"),("qc_usb2_output_power","qc_usb_2","power_w","W"),
            ("ac_input_voltage","ac_input","voltage_v","V"),("ac_input_current","ac_input","current_a","A"),
            ("ac_output_voltage","ac_output","voltage_v","V"),("ac_output_current","ac_output","current_a","A")]:
            if hasattr(device, attr):
                v=_get(device,attr)
                add_electrical_measurement(conn, observation_id=observation_id,
                    channel=channel, metric_key=metric, value=v, unit=unit, state=_state(device, attr, v))

        for ptype, attr in [("ac","ac_ports"),("usb","usb_ports"),("dc12v","dc_12v_port")]:
            if hasattr(device,attr):
                pid=_ensure_port(conn,device_id,ptype)
                v=_get(device,attr)
                add_port_measurement(conn,observation_id=observation_id,port_id=pid,
                    metric_key="enabled",value=v,state=_state(device, attr, v))

        for slot, prefix in ((1,"battery_1"),(2,"battery_2")):
            if not hasattr(device, f"{prefix}_enabled"):
                continue
            enabled=_get(device,f"{prefix}_enabled")
            bid=upsert_battery(conn,device_id=device_id,battery_role="expansion",
                battery_slot=slot,serial_number=_get(device,f"{prefix}_sn"),
                enabled=enabled,observed_at=observed_at)
            for attr,metric,unit in [
                (f"{prefix}_battery_level","soc_percent","%"),
                (f"{prefix}_voltage","voltage_v","V"),
                (f"{prefix}_max_cell_voltage","cell_voltage_max_v","V"),
                (f"{prefix}_min_cell_voltage","cell_voltage_min_v","V"),
                (f"{prefix}_cell_temperature","temperature_c","C")]:
                if hasattr(device,attr):
                    v=_get(device,attr)
                    add_battery_measurement(conn,observation_id=observation_id,
                        battery_id=bid,metric_key=metric,value=v,unit=unit,state=_state(device, attr, v))

        insert_raw_payload(conn,observation_id=observation_id,
            payload_format="normalized_snapshot",
            payload=json.dumps({"alias":alias,"serial_number":_serial(device),
                                "model":str(_get(device,"device",type(device).__name__))},
                               separators=(",",":")),
            parser_name="RootRecord EcoFlow ingest",parser_version="1")
        conn.commit()
        return observation_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
