# ==============================================================================
# FILE: Energy/lib/read_runner.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Read live snapshot (BLE preferred, cloud quota only when RR_ECOFLOW_CLOUD=1)."""  # info: """Read live snapshot (BLE preferred, cloud quota only when RR_ECOFLOW_CLOUD=1)."""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import asyncio  # info: import asyncio
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
sys.path.insert(0, str(HERE.parent.parent))  # info: sys . path . insert ( 0 ,

from paths import SAMPLES, SOC, WATTS, ensure_dirs  # noqa: E402
from ble_client import connect, BleUnavailable, eflib_ready  # noqa: E402
from config import device as device_cfg, load as load_conf  # noqa: E402
from Energy.db.ingest import persist_eflow_device  # noqa: E402
from Energy.db.condense import condense_closed_periods  # noqa: E402

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST


# ====================================================
# SECTION: function _fields_from_ble
# What it does:  fields from ble.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _fields_from_ble(device) -> dict:  # info: def _fields_from_ble
    def g(n, d=None):  # info: def g
        return getattr(device, n, d)  # info: return getattr ( device , n , d

    solar = g("xt60_input_power")  # info: set solar
    if solar is None:  # info: if solar is None :
        solar = g("solar_input_power")  # info: set solar
    return {  # info: return {
        "ac_ports": g("ac_ports"),  # info: "ac_ports" : g ( "ac_ports" ) ,
        "usb_ports": g("usb_ports"),  # info: "usb_ports" : g ( "usb_ports" ) ,
        "dc_12v_port": g("dc_12v_port"),  # info: "dc_12v_port" : g ( "dc_12v_port" ) ,
        "ac_output_power": g("ac_output_power"),  # info: "ac_output_power" : g ( "ac_output_power" ) ,
        "ac_input_power": g("ac_input_power"),  # info: "ac_input_power" : g ( "ac_input_power" ) ,
        "usbc_output_power": g("usbc_output_power"),  # info: "usbc_output_power" : g ( "usbc_output_power" ) ,
        "usba_output_power": g("usba_output_power"),  # info: "usba_output_power" : g ( "usba_output_power" ) ,
        "solar_input_power": solar,  # info: "solar_input_power" : solar ,
        "soc": g("battery_level", g("soc")),  # info: "soc" : g ( "battery_level" , g (
    }  # info: }


# ====================================================
# SECTION: function _ble_reason_token
# What it does: One SUMMARY token. The poller splits the line on spaces.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ble_reason_token(ble_err: str | None) -> str:  # info: def _ble_reason_token
    """One SUMMARY token. The poller splits the line on spaces."""  # info: """One SUMMARY token. The poller splits the line on spaces."""
    if not ble_err:  # info: if not ble_err :
        return ""  # info: return ""
    token = "_".join(ble_err.split()).replace("=", "-")  # info: set token
    if len(token) > 160:  # info: if len ( token ) > 160 :
        token = token[:157] + "..."  # info: set token
    return f" ble={token}"  # info: return f" ble= { token } "


# ====================================================
# SECTION: function _summary_line
# What it does:  summary line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _summary_line(  # info: def _summary_line
    alias: str,  # info: set alias
    fields: dict,  # info: set fields
    db_ok: bool,  # info: set db_ok
    source: str,  # info: set source
    charge_source: str,  # info: set charge_source
    ble_err: str | None = None,  # info: set ble_err
) -> str:  # info: ) -> str :
    def fmt(v, unit=""):  # info: def fmt
        if v is None:  # info: if v is None :
            return "—"  # info: return "—"
        if isinstance(v, float) and v == int(v):  # info: if isinstance ( v , float ) and
            v = int(v)  # info: set v
        return f"{v}{unit}"  # info: return f" { v } { unit }

    cs = f" charge={charge_source}" if charge_source and charge_source != "none" else ""  # info: set cs
    why = _ble_reason_token(ble_err) if source != "ble" else ""  # info: set why
    return (  # info: return (
        f"SUMMARY={alias}"  # info: f" SUMMARY= { alias } "
        f" soc={fmt(fields.get('soc'), '%')}"  # info: f" soc= { fmt ( fields . get
        f" solar={fmt(fields.get('solar_input_power'), 'W')}"  # info: f" solar= { fmt ( fields . get
        f" ac_out={fmt(fields.get('ac_output_power'), 'W')}"  # info: f" ac_out= { fmt ( fields . get
        f" usbc={fmt(fields.get('usbc_output_power'), 'W')}"  # info: f" usbc= { fmt ( fields . get
        f" src={source}{cs}"  # info: f" src= { source } { cs }
        f" db={'ok' if db_ok else 'fail'}"  # info: f" db= { 'ok' if db_ok else 'fail'
        f"{why}"  # info: f" { why } "
    )  # info: )


# ====================================================
# SECTION: function _is_internal_only
# What it does:  is internal only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_internal_only(alias: str) -> bool:  # info: def _is_internal_only
    try:  # info: try :
        cfg = device_cfg(alias)  # info: set cfg
        return (cfg.get("track") or "").strip().lower() == "internal_only"  # info: return ( cfg . get ( "track" )
    except Exception:  # info: except Exception :
        return False  # info: return False


# ====================================================
# SECTION: function _prefer_api
# What it does:  prefer api.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _prefer_api(alias: str) -> bool:  # info: def _prefer_api
    try:  # info: try :
        cfg = device_cfg(alias)  # info: set cfg
        return (cfg.get("prefer_api") or "0").strip() in ("1", "true", "yes")  # info: return ( cfg . get ( "prefer_api" )
    except Exception:  # info: except Exception :
        return False  # info: return False


# ====================================================
# SECTION: function _has_data
# What it does:  has data.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _has_data(fields: dict) -> bool:  # info: def _has_data
    return any(  # info: return any (
        fields.get(k) is not None  # info: fields . get ( k ) is not
        for k in ("soc", "ac_output_power", "ac_input_power", "solar_input_power", "usbc_output_power")  # info: for k in ( "soc" , "ac_output_power" ,
    )  # info: )


# ====================================================
# SECTION: function derive_charge_source
# What it does: Generator status is API-only (per operator rule).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def derive_charge_source(fields: dict, source: str, other_ac_outs: list[float]) -> str:  # info: def derive_charge_source
    """Generator status is API-only (per operator rule)."""  # info: """Generator status is API-only (per operator rule)."""
    try:  # info: try :
        ac_in = float(fields.get("ac_input_power") or 0)  # info: set ac_in
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        ac_in = 0.0  # info: set ac_in
    if ac_in <= 5:  # info: if ac_in <= 5 :
        return "none"  # info: return "none"
    for out in other_ac_outs:  # info: for out in other_ac_outs :
        if out is not None and out > 20 and abs(out - ac_in) < max(80, ac_in * 0.4):  # info: if out is not None and out >
            return "battery_transfer"  # info: return "battery_transfer"
    if source in ("api", "cloud"):  # info: if source in ( "api" , "cloud" )
        return "generator"  # info: return "generator"
    return "ac"  # info: return "ac"


# ====================================================
# SECTION: function _collect_other_ac_outs
# What it does:  collect other ac outs.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _collect_other_ac_outs(exclude_alias: str) -> list[float]:  # info: def _collect_other_ac_outs
    outs = []  # info: set outs
    try:  # info: try :
        cp = load_conf()  # info: set cp
        for section in cp.sections():  # info: for section in cp . sections ( )
            if section in ("paths", "inventory", "ble", "env") or section == exclude_alias:  # info: if section in ( "paths" , "inventory" ,
                continue  # info: continue
            if not cp.has_option(section, "sn"):  # info: if not cp . has_option ( section ,
                continue  # info: continue
            p = WATTS / f"{section}-last.json"  # info: set p
            if p.is_file():  # info: if p . is_file ( ) :
                try:  # info: try :
                    data = json.loads(p.read_text(encoding="utf-8"))  # info: set data
                    v = data.get("ac_output_power")  # info: set v
                    if v is not None:  # info: if v is not None :
                        outs.append(float(v))  # info: outs . append ( float ( v )
                except Exception:  # info: except Exception :
                    pass  # info: pass
    except Exception:  # info: except Exception :
        pass  # info: pass
    return outs  # info: return outs


# ====================================================
# SECTION: function _read_ble
# What it does:  read ble.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
async def _read_ble(alias: str):  # info: async def
    device = await connect(alias)  # info: set device
    await asyncio.sleep(2.0)  # info: await asyncio . sleep ( 2.0 )
    fields = _fields_from_ble(device)  # info: set fields
    if not _has_data(fields):  # info: if not _has_data ( fields ) :
        # Connected but no usable telemetry — BLE miss. Cloud runs only if the flag is on.
        try:  # info: try :
            await device.disconnect()  # info: await device . disconnect ( )
        except Exception:  # info: except Exception :
            pass  # info: pass
        raise BleUnavailable("BLE connected but fields empty/None")  # info: raise BleUnavailable ( "BLE connected but fields empty/None" )
    return device, fields  # info: return device , fields


# ====================================================
# SECTION: function _read_api
# What it does:  read api.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_api(alias: str) -> dict:  # info: def _read_api
    from ecoflow_api import fetch_device_fields, EcoflowApiError  # info: from ecoflow_api import fetch_device_fields , EcoflowApiError
    if os.environ.get("RR_ECOFLOW_CLOUD", "0") != "1":  # info: if os . environ . get ( "RR_ECOFLOW_CLOUD"
        raise EcoflowApiError("cloud=off")  # info: raise EcoflowApiError ( "cloud=off" )
    cfg = device_cfg(alias)  # info: set cfg
    sn = (cfg.get("sn") or "").strip()  # info: set sn
    if not sn:  # info: if not sn :
        raise EcoflowApiError(f"no sn for {alias}")  # info: raise EcoflowApiError ( f" no sn for { alias }
    return fetch_device_fields(sn)  # info: return fetch_device_fields ( sn )


# ====================================================
# SECTION: function _write_sample
# What it does: BLE samples stay in Energy/samples. A cloud read goes under Cloud-Quota.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_sample(snap: dict, alias: str, source: str) -> None:  # info: def _write_sample
    """BLE samples stay in Energy/samples. A cloud read goes under Cloud-Quota."""  # info: """BLE samples stay in Energy/samples. A cloud read goes under Cloud-Quota."""
    if source == "cloud":  # info: if source == "cloud" :
        scripts = HERE.parent / "Cloud-Quota" / "scripts"  # info: set scripts
        if str(scripts) not in sys.path:  # info: if str ( scripts ) not in sys
            sys.path.insert(0, str(scripts))  # info: sys . path . insert ( 0 ,
        from store import write_cloud_snapshot  # info: from store import write_cloud_snapshot
        write_cloud_snapshot(snap)  # info: call write_cloud_snapshot
        return  # info: return
    path = SAMPLES / f"read-{alias}-{datetime.now(HST).strftime('%Y%m%d-%H%M%S')}.json"  # info: set path
    path.write_text(json.dumps(snap, indent=2), encoding="utf-8")  # info: path . write_text ( json . dumps (


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    p = argparse.ArgumentParser()  # info: set p
    p.add_argument("--device", required=True)  # info: p . add_argument ( "--device" , required =
    args = p.parse_args()  # info: set args
    ensure_dirs()  # info: call ensure_dirs
    alias = args.device  # info: set alias

    source = "none"  # info: set source
    fields: dict = {}  # info: set fields
    device = None  # info: set device
    ble_err = None  # info: set ble_err

    # 1) Prefer BLE unless prefer_api=1
    #    Silence eflib/bleak connect spam when falling back to API.
    if not _prefer_api(alias):  # info: if not _prefer_api ( alias ) :
        ok, reason = eflib_ready()  # info: ok , reason = eflib_ready ( )
        if ok:  # info: if ok :
            import io, contextlib  # info: import io , contextlib
            buf_out, buf_err = io.StringIO(), io.StringIO()  # info: buf_out , buf_err = io . StringIO (
            try:  # info: try :
                with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):  # info: with contextlib . redirect_stdout ( buf_out ) ,
                    device, fields = asyncio.run(_read_ble(alias))  # info: device , fields = asyncio . run (
                source = "ble"  # info: set source
                # BLE succeeded — if eflib printed anything non-fatal, ignore it
            except BleUnavailable as e:  # info: except BleUnavailable as e :
                ble_err = str(e)  # info: set ble_err
            except Exception as e:  # info: except Exception as e :
                ble_err = f"{type(e).__name__}: {e}"  # info: set ble_err
        else:  # info: else :
            ble_err = reason  # info: set ble_err

    # 2) Cloud fallback when BLE missing or empty. No HTTP unless RR_ECOFLOW_CLOUD=1.
    if source != "ble":  # info: if source != "ble" :
        try:  # info: try :
            fields = _read_api(alias)  # info: set fields
            source = "cloud"  # info: set source
            device = None  # info: set device
        except Exception as e:  # info: except Exception as e :
            print("WAITING")  # info: call print
            print(f"No data — BLE: {ble_err or 'skipped'}; API: {type(e).__name__}: {e}")  # info: call print
            print("STATUS=WAITING")  # info: call print
            return 2  # info: return 2

    # 3) Charge source
    other_outs = _collect_other_ac_outs(alias)  # info: set other_outs
    charge_source = derive_charge_source(fields, source, other_outs)  # info: set charge_source

    observed_at = (  # info: set observed_at
        datetime.now(timezone.utc)  # info: datetime . now ( timezone . utc )
        .isoformat(timespec="milliseconds")  # info: call .
        .replace("+00:00", "Z")  # info: call .
    )  # info: )
    snap = {  # info: set snap
        "alias": alias,  # info: "alias" : alias ,
        "fields": fields,  # info: "fields" : fields ,
        "at": datetime.now(HST).isoformat(timespec="seconds"),  # info: "at" : datetime . now ( HST )
        "source": source,  # info: "source" : source ,
        "charge_source": charge_source,  # info: "charge_source" : charge_source ,
    }  # info: }

    # 4) Persist
    db_ok = False  # info: set db_ok
    if device is not None:  # info: if device is not None :
        try:  # info: try :
            persist_eflow_device(device, alias, observed_at)  # info: call persist_eflow_device
            condense_closed_periods()  # info: call condense_closed_periods
            db_ok = True  # info: set db_ok
        except Exception as e:  # info: except Exception as e :
            print(f"DB_ERROR: {type(e).__name__}: {e}", file=sys.stderr)  # info: call print
        try:  # info: try :
            asyncio.run(device.disconnect())  # info: asyncio . run ( device . disconnect (
        except Exception:  # info: except Exception :
            pass  # info: pass
    else:  # info: else :
        db_ok = True  # JSON path is authoritative for API reads

    # 5) Samples / last files. Cloud JSON is not written into Energy/samples.
    _write_sample(snap, alias, source)  # info: call _write_sample

    if fields.get("soc") is not None:  # info: if fields . get ( "soc" ) is
        (SOC / f"{alias}-last.json").write_text(  # info: call (
            json.dumps({"soc": fields["soc"], "at": snap["at"], "source": source}, indent=2)  # info: json . dumps ( { "soc" : fields
        )  # info: )
    watts = {  # info: set watts
        k: fields[k]  # info: set k
        for k in ("ac_output_power", "ac_input_power", "usbc_output_power", "solar_input_power")  # info: for k in ( "ac_output_power" , "ac_input_power" ,
        if fields.get(k) is not None  # info: if fields . get ( k ) is
    }  # info: }
    if watts:  # info: if watts :
        (WATTS / f"{alias}-last.json").write_text(  # info: call (
            json.dumps({**watts, "at": snap["at"], "source": source, "charge_source": charge_source}, indent=2)  # info: json . dumps ( { ** watts ,
        )  # info: )

    # 6) Console
    if not _is_internal_only(alias):  # info: if not _is_internal_only ( alias ) :
        print(_summary_line(alias, fields, db_ok, source, charge_source, ble_err))  # info: call print
    else:  # info: else :
        print(f"INTERNAL={alias} soc={fields.get('soc')} src={source} charge={charge_source}")  # info: call print

    if not _has_data(fields):  # info: if not _has_data ( fields ) :
        print("WAITING")  # info: call print
        print("No data — fields empty/None (not inventing)")  # info: call print
        print("STATUS=WAITING")  # info: call print
        return 2  # info: return 2

    print("STATUS=OK" + ("" if db_ok else " (json-only; db failed)"))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
