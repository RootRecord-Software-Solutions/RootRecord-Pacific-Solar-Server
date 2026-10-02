# ==============================================================================
# FILE: Energy/lib/ecoflow_api.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Official EcoFlow IoT Open Platform client (Quota API). Stdlib only."""  # info: """Official EcoFlow IoT Open Platform client (Quota API). Stdlib only."""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import hmac  # info: import hmac
import json  # info: import json
import os  # info: import os
import random  # info: import random
import time  # info: import time
import urllib.error  # info: import urllib . error
import urllib.parse  # info: import urllib . parse
import urllib.request  # info: import urllib . request
from typing import Any  # info: from typing import Any

from envload import load_env  # info: from envload import load_env

# Region → base URL
# ====================================================
# SECTION: _BASE
# What it does: Set _BASE.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_BASE = {  # info: set _BASE
    "us": "https://api.ecoflow.com",  # info: "us" : "https://api.ecoflow.com" ,
    "global": "https://api.ecoflow.com",  # info: "global" : "https://api.ecoflow.com" ,
    "eu": "https://api-e.ecoflow.com",  # info: "eu" : "https://api-e.ecoflow.com" ,
    "a": "https://api-a.ecoflow.com",  # info: "a" : "https://api-a.ecoflow.com" ,
}  # info: }


# ====================================================
# SECTION: class EcoflowApiError
# What it does: EcoflowApiError.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class EcoflowApiError(RuntimeError):  # info: class EcoflowApiError
    pass  # info: pass


# ====================================================
# SECTION: function _hmac_sha256
# What it does:  hmac sha256.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _hmac_sha256(data: str, key: str) -> str:  # info: def _hmac_sha256
    return hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()  # info: return hmac . new ( key . encode


# ====================================================
# SECTION: function _sorted_qstr
# What it does:  sorted qstr.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sorted_qstr(d: dict[str, Any]) -> str:  # info: def _sorted_qstr
    return "&".join(f"{k}={d[k]}" for k in sorted(d.keys()))  # info: return "&" . join ( f" { k


# ====================================================
# SECTION: class EcoflowApi
# What it does: EcoflowApi.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class EcoflowApi:  # info: class EcoflowApi
    def __init__(self) -> None:  # info: def __init__
        from envload import api_keys  # info: from envload import api_keys
        self.access_key, self.secret_key = api_keys()  # info: self . access_key , self . secret_key =
        region = (os.environ.get("ECOFLOW_REGION") or "us").strip().lower()  # info: set region
        self.base = _BASE.get(region, _BASE["us"]).rstrip("/")  # info: self . base = _BASE . get (
        if not self.access_key or not self.secret_key:  # info: if not self . access_key or not self
            raise EcoflowApiError(  # info: raise EcoflowApiError (
                "ECOFLOW_ACCESS / ECOFLOW_SECRET missing or empty in master-key.env"  # info: "ECOFLOW_ACCESS / ECOFLOW_SECRET missing or empty in master-key.env"
            )  # info: )

    def _headers(self, params: dict[str, Any] | None = None) -> dict[str, str]:  # info: def _headers
        nonce = str(random.randint(100000, 999999))  # info: set nonce
        timestamp = str(int(time.time() * 1000))  # info: set timestamp
        hdr = {  # info: set hdr
            "accessKey": self.access_key,  # info: "accessKey" : self . access_key ,
            "nonce": nonce,  # info: "nonce" : nonce ,
            "timestamp": timestamp,  # info: "timestamp" : timestamp ,
        }  # info: }
        # Sign string = sorted query params (if any) + accessKey/nonce/timestamp
        sign_parts = []  # info: set sign_parts
        if params:  # info: if params :
            sign_parts.append(_sorted_qstr({k: str(v) for k, v in params.items()}))  # info: sign_parts . append ( _sorted_qstr ( { k
        sign_parts.append(_sorted_qstr(hdr))  # info: sign_parts . append ( _sorted_qstr ( hdr )
        sign_str = "&".join(p for p in sign_parts if p)  # info: set sign_str
        hdr["sign"] = _hmac_sha256(sign_str, self.secret_key)  # info: hdr [ "sign" ] = _hmac_sha256 ( sign_str
        return hdr  # info: return hdr

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:  # info: def _get
        qs = urllib.parse.urlencode(params)  # info: set qs
        url = f"{self.base}{path}?{qs}"  # info: set url
        req = urllib.request.Request(url, headers=self._headers(params), method="GET")  # info: set req
        try:  # info: try :
            with urllib.request.urlopen(req, timeout=15) as resp:  # info: with urllib . request . urlopen ( req
                body = json.loads(resp.read().decode("utf-8"))  # info: set body
        except urllib.error.HTTPError as e:  # info: except urllib . error . HTTPError as e
            raise EcoflowApiError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}") from e  # info: raise EcoflowApiError ( f" HTTP { e .
        except Exception as e:  # info: except Exception as e :
            raise EcoflowApiError(f"{type(e).__name__}: {e}") from e  # info: raise EcoflowApiError ( f" { type ( e
        if str(body.get("code", "")) not in ("0", "0.0"):  # info: if str ( body . get ( "code"
            raise EcoflowApiError(f"API code={body.get('code')} message={body.get('message')}")  # info: raise EcoflowApiError ( f" API code= { body .
        return body.get("data") or {}  # info: return body . get ( "data" ) or

    def quota_all(self, sn: str) -> dict[str, Any]:  # info: def quota_all
        """Return flat quota map for device serial number."""  # info: """Return flat quota map for device serial number."""
        return self._get("/iot-open/sign/device/quota/all", {"sn": sn})  # info: return self . _get ( "/iot-open/sign/device/quota/all" , {

    def device_list(self) -> dict[str, dict[str, Any]]:  # info: def device_list
        """Serial → list row. Used to skip offline quota, which stays frozen."""  # info: """Serial → list row. Used to skip offline quota, which stays frozen."""
        data = self._get("/iot-open/sign/device/list", {})  # info: set data
        rows = data if isinstance(data, list) else []  # info: set rows
        found: dict[str, dict[str, Any]] = {}  # info: set found
        for row in rows:  # info: for row in rows :
            if isinstance(row, dict) and row.get("sn"):  # info: if isinstance ( row , dict ) and row . get ( "sn" ) :
                found[str(row["sn"])] = row  # info: found [ str ( row [ "sn" ] ) ] = row
        return found  # info: return found


# ── field mapping (Delta 2 / River 2 family – best-effort) ──────────────────
# Keys vary by firmware; we try several common names.

# ====================================================
# SECTION: function _first
# What it does:  first.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _first(d: dict, *keys, default=None):  # info: def _first
    for k in keys:  # info: for k in keys :
        if k in d and d[k] is not None:  # info: if k in d and d [ k
            return d[k]  # info: return d [ k ]
    return default  # info: return default


# ====================================================
# SECTION: function _switch_bool
# What it does: Map a quota switch (1/0) to True/False, or None when the key is absent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _switch_bool(value):  # info: def _switch_bool
    if value is None:  # info: if value is None
        return None  # info: return None
    if isinstance(value, bool):  # info: if isinstance
        return value  # info: return value
    try:  # info: try
        return float(value) != 0.0  # info: return numeric switch
    except (TypeError, ValueError):  # info: except
        text = str(value).strip().lower()  # info: set text
    if text in ("1", "true", "on", "yes"):  # info: if text on
        return True  # info: return True
    if text in ("0", "false", "off", "no"):  # info: if text off
        return False  # info: return False
    return None  # info: return None


# ====================================================
# SECTION: function map_quota_to_fields
# What it does: Map EcoFlow quota dict → same shape used by read_runner._fields().
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def map_quota_to_fields(quota: dict[str, Any]) -> dict[str, Any]:  # info: def map_quota_to_fields
    """Map EcoFlow quota dict → same shape used by read_runner._fields()."""  # info: """Map EcoFlow quota dict → same shape used by read_runner._fields()."""
    # SOC
    soc = _first(  # info: set soc
        quota,  # info: quota ,
        "bms_emsStatus.f32LcdShowSoc", "bms_bmsStatus.f32ShowSoc",  # info: float LCD SOC before the integer pd.soc
        "pd.soc", "bms_bmsStatus.soc", "bmsMaster.soc", "soc",  # info: "pd.soc" , "bms_bmsStatus.soc" , "bmsMaster.soc" , "soc" ,
        "bmsHeartBeat.soc",  # info: "bmsHeartBeat.soc" ,
    )  # info: )
    # AC output. inv.outputWatts is the inverter. pd.wattsOutSum includes USB and DC.
    ac_out = _first(  # info: set ac_out
        quota,  # info: quota ,
        "inv.outputWatts", "inv.acOutputWatts", "pd.dsgPowerAC",  # info: inverter AC out, not the all-port sum
    )  # info: )
    # AC input. cfgAcEnabled is a switch, and wattsInSum includes solar.
    ac_in = _first(  # info: set ac_in
        quota,  # info: quota ,
        "inv.inputWatts", "inv.acInputWatts", "pd.chgPowerAC",  # info: "inv.inputWatts" , "inv.acInputWatts" , "pd.chgPowerAC" ,
    )  # info: )
    # try numeric only for ac_in
    try:  # info: try :
        ac_in = float(ac_in) if ac_in is not None else None  # info: set ac_in
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        ac_in = None  # info: set ac_in

    # Solar / XT60
    solar = _first(  # info: set solar
        quota,  # info: quota ,
        "mppt.inWatts", "pd.chgSunPower", "mppt.pv1InputWatts",  # info: "mppt.inWatts" , "pd.chgSunPower" , "mppt.pv1InputWatts" ,
        "mppt.pv2InputWatts", "solar_input_power",  # info: "mppt.pv2InputWatts" , "solar_input_power" ,
    )  # info: )
    # USB-C
    usbc = _first(  # info: set usbc
        quota,  # info: quota ,
        "pd.typec1Watts", "pd.typec2Watts", "pd.typecWatts",  # info: "pd.typec1Watts" , "pd.typec2Watts" , "pd.typecWatts" ,
        "usbc_output_power",  # info: "usbc_output_power" ,
    )  # info: )
    # try sum of type-c if both present
    t1 = quota.get("pd.typec1Watts")  # info: set t1
    t2 = quota.get("pd.typec2Watts")  # info: set t2
    if t1 is not None or t2 is not None:  # info: if t1 is not None or t2 is
        try:  # info: try :
            usbc = (float(t1 or 0) + float(t2 or 0)) or usbc  # info: set usbc
        except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
            pass  # info: pass

    # charger type hint (0=none/ac/dc/solar depending on model)
    charger_type = _first(quota, "inv.chargerType", "pd.chargerType", "chargerType")  # info: set charger_type

    return {  # info: return {
        "soc": float(soc) if soc is not None else None,  # info: "soc" : float ( soc ) if soc
        "ac_output_power": float(ac_out) if ac_out is not None else None,  # info: "ac_output_power" : float ( ac_out ) if ac_out
        "ac_input_power": float(ac_in) if ac_in is not None else None,  # info: "ac_input_power" : float ( ac_in ) if ac_in
        "solar_input_power": float(solar) if solar is not None else None,  # info: "solar_input_power" : float ( solar ) if solar
        "usbc_output_power": float(usbc) if usbc is not None else None,  # info: "usbc_output_power" : float ( usbc ) if usbc
        "usba_output_power": None,  # info: "usba_output_power" : None ,
        "ac_ports": _switch_bool(_first(  # info: ac outlet switch from quota, not a watt guess
            quota, "mppt.cfgAcEnabled", "pd.cfgAcEnabled", "inv.cfgAcEnabled", "cfgAcEnabled",  # info: River 2 Pro uses mppt.cfgAcEnabled
        )),  # info: "ac_ports"
        "usb_ports": None,  # info: "usb_ports" : None ,
        "dc_12v_port": None,  # info: "dc_12v_port" : None ,
        "_raw_charger_type": charger_type,  # info: "_raw_charger_type" : charger_type ,
        "_raw_quota_keys": list(quota.keys())[:40],  # debug aid
    }  # info: }


# ====================================================
# SECTION: function fetch_device_fields
# What it does: High-level: return fields dict or raise EcoflowApiError.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fetch_device_fields(sn: str) -> dict[str, Any]:  # info: def fetch_device_fields
    """Return fields when the device is cloud-online. Offline quota is left unread."""  # info: """Return fields when the device is cloud-online. Offline quota is left unread."""
    client = EcoflowApi()  # info: set client
    row = client.device_list().get(sn)  # info: set row
    try:  # info: try :
        online = int(row.get("online")) if isinstance(row, dict) else 0  # info: set online
    except (TypeError, ValueError):  # info: except ( TypeError , ValueError ) :
        online = 0  # info: set online
    if online != 1:  # info: if online != 1 :
        raise EcoflowApiError("cloud offline")  # info: raise EcoflowApiError ( "cloud offline" )
    quota = client.quota_all(sn)  # info: set quota
    if not quota:  # info: if not quota :
        raise EcoflowApiError("empty quota response")  # info: raise EcoflowApiError ( "empty quota response" )
    return map_quota_to_fields(quota)  # info: return map_quota_to_fields ( quota )
