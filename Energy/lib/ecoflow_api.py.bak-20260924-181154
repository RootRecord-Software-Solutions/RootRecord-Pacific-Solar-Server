#!/usr/bin/env python3
"""Official EcoFlow IoT Open Platform client (Quota API). Stdlib only."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from envload import load_env

# Region → base URL
_BASE = {
    "us": "https://api.ecoflow.com",
    "global": "https://api.ecoflow.com",
    "eu": "https://api-e.ecoflow.com",
    "a": "https://api-a.ecoflow.com",
}


class EcoflowApiError(RuntimeError):
    pass


def _hmac_sha256(data: str, key: str) -> str:
    return hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()


def _sorted_qstr(d: dict[str, Any]) -> str:
    return "&".join(f"{k}={d[k]}" for k in sorted(d.keys()))


class EcoflowApi:
    def __init__(self) -> None:
        load_env()
        self.access_key = (os.environ.get("ECOFLOW_ACCESS_KEY") or "").strip()
        self.secret_key = (os.environ.get("ECOFLOW_SECRET_KEY") or "").strip()
        region = (os.environ.get("ECOFLOW_REGION") or "us").strip().lower()
        self.base = _BASE.get(region, _BASE["us"]).rstrip("/")
        if not self.access_key or not self.secret_key:
            raise EcoflowApiError(
                "ECOFLOW_ACCESS_KEY / ECOFLOW_SECRET_KEY missing in master-key.env"
            )

    def _headers(self, params: dict[str, Any] | None = None) -> dict[str, str]:
        nonce = str(random.randint(100000, 999999))
        timestamp = str(int(time.time() * 1000))
        hdr = {
            "accessKey": self.access_key,
            "nonce": nonce,
            "timestamp": timestamp,
        }
        # Sign string = sorted query params (if any) + accessKey/nonce/timestamp
        sign_parts = []
        if params:
            sign_parts.append(_sorted_qstr({k: str(v) for k, v in params.items()}))
        sign_parts.append(_sorted_qstr(hdr))
        sign_str = "&".join(p for p in sign_parts if p)
        hdr["sign"] = _hmac_sha256(sign_str, self.secret_key)
        return hdr

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        qs = urllib.parse.urlencode(params)
        url = f"{self.base}{path}?{qs}"
        req = urllib.request.Request(url, headers=self._headers(params), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise EcoflowApiError(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}") from e
        except Exception as e:
            raise EcoflowApiError(f"{type(e).__name__}: {e}") from e
        if str(body.get("code", "")) not in ("0", "0.0"):
            raise EcoflowApiError(f"API code={body.get('code')} message={body.get('message')}")
        return body.get("data") or {}

    def quota_all(self, sn: str) -> dict[str, Any]:
        """Return flat quota map for device serial number."""
        return self._get("/iot-open/sign/device/quota/all", {"sn": sn})


# ── field mapping (Delta 2 / River 2 family – best-effort) ──────────────────
# Keys vary by firmware; we try several common names.

def _first(d: dict, *keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def map_quota_to_fields(quota: dict[str, Any]) -> dict[str, Any]:
    """Map EcoFlow quota dict → same shape used by read_runner._fields()."""
    # SOC
    soc = _first(
        quota,
        "pd.soc", "bms_bmsStatus.soc", "bmsMaster.soc", "soc",
        "bmsHeartBeat.soc",
    )
    # AC output
    ac_out = _first(
        quota,
        "inv.outputWatts", "inv.outputWatts", "pd.wattsOutSum",
        "inv.acOutputWatts", "outputWatts",
    )
    # AC input
    ac_in = _first(
        quota,
        "inv.inputWatts", "inv.acInputWatts", "pd.chgPowerAC",
        "pd.wattsInSum", "inputWatts", "inv.cfgAcEnabled",  # last is boolean-ish
    )
    # try numeric only for ac_in
    try:
        ac_in = float(ac_in) if ac_in is not None else None
    except (TypeError, ValueError):
        ac_in = None

    # Solar / XT60
    solar = _first(
        quota,
        "mppt.inWatts", "pd.chgSunPower", "mppt.pv1InputWatts",
        "mppt.pv2InputWatts", "solar_input_power",
    )
    # USB-C
    usbc = _first(
        quota,
        "pd.typec1Watts", "pd.typec2Watts", "pd.typecWatts",
        "usbc_output_power",
    )
    # try sum of type-c if both present
    t1 = quota.get("pd.typec1Watts")
    t2 = quota.get("pd.typec2Watts")
    if t1 is not None or t2 is not None:
        try:
            usbc = (float(t1 or 0) + float(t2 or 0)) or usbc
        except (TypeError, ValueError):
            pass

    # charger type hint (0=none/ac/dc/solar depending on model)
    charger_type = _first(quota, "inv.chargerType", "pd.chargerType", "chargerType")

    return {
        "soc": float(soc) if soc is not None else None,
        "ac_output_power": float(ac_out) if ac_out is not None else None,
        "ac_input_power": float(ac_in) if ac_in is not None else None,
        "solar_input_power": float(solar) if solar is not None else None,
        "usbc_output_power": float(usbc) if usbc is not None else None,
        "usba_output_power": None,
        "ac_ports": None,
        "usb_ports": None,
        "dc_12v_port": None,
        "_raw_charger_type": charger_type,
        "_raw_quota_keys": list(quota.keys())[:40],  # debug aid
    }


def fetch_device_fields(sn: str) -> dict[str, Any]:
    """High-level: return fields dict or raise EcoflowApiError."""
    client = EcoflowApi()
    quota = client.quota_all(sn)
    if not quota:
        raise EcoflowApiError("empty quota response")
    return map_quota_to_fields(quota)
