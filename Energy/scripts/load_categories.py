# ==============================================================================
# FILE: Energy/scripts/load_categories.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""EcoFlow load buckets (G3 port of G1 load-categories/scripts/load_categories.py, 2026-09-29). Measured watts only.

  python3 load_categories.py            read Database Energy/watts/{delta2,river2pro}-last.json + Energy/sun -> print JSON
  python3 load_categories.py --input F  same logic on a JSON file {"devices": [{label, pv_w, ac_in_w, ac_out_w, dc_out_w,
                                        car_w, discharge_w}, ...], "sun": {"after_sunset": bool, ...}}

Ported unchanged: thresholds, same_watts, apply_ebatt (after-sunset MPPT 20-225 W = Ninebot E-Batt, not PV), apply_roles
(Delta<->River AC transfer, >=1000 W appliances, Starlink/lights band 40-250 W, emergency), categories, bank_state,
night_charge_callout. Changed: G1 read EcoFlow cloud-quota keys (inv.*, mppt.*, pd.*) through pack_power(); G3 BLE
last-files only carry ac_output_power / ac_input_power / usbc_output_power / solar_input_power, so the adapter maps
pv_w <- solar_input_power, ac_in_w <- ac_input_power, ac_out_w <- ac_output_power, dc_out_w <- usbc_output_power,
car_w = 0 (no 12 V / car field in G3), discharge_w = ac_out + usbc. device_role(sn) -> label match ("Delta" / "River").
Sun: G1 sun_times.facts() after_sunset / before_sunrise -> computed from Database Energy/sun/sun-times-last.json.
NOT ported: append_history (it deleted load logs older than 14 days) and history_averages. On demand; writes nothing.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
ENERGY = DB / "Energy"  # info: set ENERGY
DEVICES = (("delta2", "Delta 2"), ("river2pro", "River 2 Pro"))  # info: set DEVICES

APPLIANCE_AC_W = 1000.0  # info: set APPLIANCE_AC_W
STARLINK_BAND_LO = 40.0  # info: set STARLINK_BAND_LO
STARLINK_BAND_HI = 250.0  # info: set STARLINK_BAND_HI
CAR_W_MIN = 5.0  # info: set CAR_W_MIN
NIGHT_IN_W = 20.0  # info: set NIGHT_IN_W
PV_FLAT_W = 15.0  # info: set PV_FLAT_W
EBATT_MIN_W = 20.0  # info: set EBATT_MIN_W
EBATT_MAX_W = 225.0  # info: set EBATT_MAX_W
# Recycled Ninebot pack on the MPPT. Nameplate only — no SOC from EcoFlow.
EBATT_WH = 220.0  # info: set EBATT_WH
# ====================================================
# SECTION: USB_KEYS
# What it does: Set USB_KEYS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
USB_KEYS = (  # info: set USB_KEYS
    "pd.usb1Watts",  # info: "pd.usb1Watts" ,
    "pd.usb2Watts",  # info: "pd.usb2Watts" ,
    "pd.qcUsb1Watts",  # info: "pd.qcUsb1Watts" ,
    "pd.typec1Watts",  # info: "pd.typec1Watts" ,
    "pd.typec2Watts",  # info: "pd.typec2Watts" ,
)  # info: )
CAR_KEYS = ("pd.carWatts", "mppt.carOutWatts", "mppt.dcdc12vWatts")  # info: set CAR_KEYS


# ====================================================
# SECTION: function watts
# What it does: watts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def watts(raw) -> float:  # info: def watts
    if raw is None:  # info: if raw is None :
        return 0.0  # info: return 0.0
    n = float(raw)  # info: set n
    if abs(n) >= 10_000:  # info: if abs ( n ) >= 10_000 :
        n = n / 1000.0  # info: set n
    return round(max(0.0, n), 1)  # info: return round ( max ( 0.0 , n


# ====================================================
# SECTION: function same_watts
# What it does: same watts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def same_watts(a: float, b: float) -> bool:  # info: def same_watts
    a, b = float(a or 0), float(b or 0)  # info: a , b = float ( a or
    if a < 20 or b < 20:  # info: if a < 20 or b < 20
        return False  # info: return False
    slack = max(40.0, 0.12 * max(a, b))  # info: set slack
    return abs(a - b) <= slack  # info: return abs ( a - b ) <=


# ====================================================
# SECTION: function _ac_out
# What it does:  ac out.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ac_out(d: dict) -> float:  # info: def _ac_out
    return float(d.get("ac_out_w") or 0)  # info: return float ( d . get ( "ac_out_w"


# ====================================================
# SECTION: function _ac_in
# What it does:  ac in.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ac_in(d: dict) -> float:  # info: def _ac_in
    return max(float(d.get("ac_in_w") or 0), float(d.get("ac_charge_w") or 0))  # info: return max ( float ( d . get


# ====================================================
# SECTION: function _is_night
# What it does:  is night.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_night(sun: dict | None) -> bool:  # info: def _is_night
    sun = sun or {}  # info: set sun
    if sun.get("after_sunset") or sun.get("before_sunrise"):  # info: if sun . get ( "after_sunset" ) or
        return True  # info: return True
    if sun.get("ok") or sun.get("sunset") or sun.get("sunrise"):  # info: if sun . get ( "ok" ) or
        return False  # info: return False
    hour = datetime.now().hour  # info: set hour
    return hour >= 19 or hour < 6  # info: return hour >= 19 or hour < 6


# ====================================================
# SECTION: function solar_in_w
# What it does: solar in w.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def solar_in_w(devices: list[dict]) -> float:  # info: def solar_in_w
    return round(  # info: return round (
        sum(float(d.get("pv_w") or 0) for d in devices if d.get("input_kind") != "ebatt"),  # info: call sum
        1,  # info: 1 ,
    )  # info: )


# ====================================================
# SECTION: function ebatt_in_w
# What it does: ebatt in w.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ebatt_in_w(devices: list[dict]) -> float:  # info: def ebatt_in_w
    return round(  # info: return round (
        sum(  # info: call sum
            float(d.get("ebatt_w") or d.get("pv_w") or 0)  # info: call float
            for d in devices  # info: for d in devices
            if d.get("input_kind") == "ebatt"  # info: if d . get ( "input_kind" ) ==
        ),  # info: ) ,
        1,  # info: 1 ,
    )  # info: )


# ====================================================
# SECTION: function apply_ebatt
# What it does: After sunset, MPPT ≤225 W that Delta is not discharging is the Ninebot, not PV.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_ebatt(devices: list[dict], *, sun: dict | None = None) -> None:  # info: def apply_ebatt
    """After sunset, MPPT ≤225 W that Delta is not discharging is the Ninebot, not PV."""  # info: """After sunset, MPPT ≤225 W that Delta is not discharging is the Ninebot, not PV."""
    for d in devices:  # info: for d in devices :
        d.pop("ebatt_w", None)  # info: d . pop ( "ebatt_w" , None )
        d["input_kind"] = None  # info: d [ "input_kind" ] = None
    if not devices:  # info: if not devices :
        return  # info: return
    if sun is None:  # info: if sun is None :
        sun = sun_facts()  # G3: Database Energy/sun (G1: sun_times.facts())
    if not _is_night(sun):  # info: if not _is_night ( sun ) :
        return  # info: return
    incoming = sum(float(d.get("pv_w") or 0) for d in devices)  # info: set incoming
    if incoming < EBATT_MIN_W or incoming > EBATT_MAX_W:  # info: if incoming < EBATT_MIN_W or incoming > EBATT_MAX_W
        return  # info: return
    delta = next((d for d in devices if _is_delta(d)), None)  # info: set delta
    delta_out = 0.0  # info: set delta_out
    if delta:  # info: if delta :
        delta_out = max(  # info: set delta_out
            float(delta.get("discharge_w") or 0),  # info: call float
            float(delta.get("ac_out_w") or 0),  # info: call float
            float(delta.get("out_w") or 0),  # info: call float
        )  # info: )
    if same_watts(incoming, delta_out):  # info: if same_watts ( incoming , delta_out ) :
        return  # info: return
    for d in devices:  # info: for d in devices :
        w = float(d.get("pv_w") or 0)  # info: set w
        if w >= EBATT_MIN_W:  # info: if w >= EBATT_MIN_W :
            d["input_kind"] = "ebatt"  # info: d [ "input_kind" ] = "ebatt"
            d["ebatt_w"] = round(w, 1)  # info: d [ "ebatt_w" ] = round ( w


# ====================================================
# SECTION: function apply_roles
# What it does: apply roles.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def apply_roles(devices: list[dict]) -> None:  # info: def apply_roles
    for d in devices:  # info: for d in devices :
        d["ac_role"] = None  # info: d [ "ac_role" ] = None
        d["on_generator"] = False  # info: d [ "on_generator" ] = False
        d["transfer_sure"] = False  # info: d [ "transfer_sure" ] = False
        d.pop("transfer_w", None)  # info: d . pop ( "transfer_w" , None )
        d.pop("appliance_w", None)  # info: d . pop ( "appliance_w" , None )
        d.pop("starlink_w", None)  # info: d . pop ( "starlink_w" , None )
        d.pop("emergency_w", None)  # info: d . pop ( "emergency_w" , None )
    delta = next((d for d in devices if _is_delta(d)), None)  # info: set delta
    river = next((d for d in devices if _is_river(d)), None)  # info: set river

    src = dst = None  # info: set src
    transfer = 0.0  # info: set transfer
    if delta and river:  # info: if delta and river :
        d_out, r_out = _ac_out(delta), _ac_out(river)  # info: d_out , r_out = _ac_out ( delta )
        d_in, r_in = _ac_in(delta), _ac_in(river)  # info: d_in , r_in = _ac_in ( delta )
        # AC only — never discharge_w (USB inflates that).
        if same_watts(d_out, r_in):  # info: if same_watts ( d_out , r_in ) :
            src, dst = delta, river  # info: src , dst = delta , river
            transfer = min(d_out, r_in)  # info: set transfer
        elif same_watts(r_out, d_in):  # info: elif same_watts ( r_out , d_in ) :
            src, dst = river, delta  # info: src , dst = river , delta
            transfer = min(r_out, d_in)  # info: set transfer
        if src is not None:  # info: if src is not None :
            src["ac_role"] = "transfer_out"  # info: src [ "ac_role" ] = "transfer_out"
            dst["ac_role"] = "transfer_in"  # info: dst [ "ac_role" ] = "transfer_in"
            src["transfer_sure"] = True  # info: src [ "transfer_sure" ] = True
            dst["transfer_sure"] = True  # info: dst [ "transfer_sure" ] = True
            src["transfer_w"] = round(transfer, 1)  # info: src [ "transfer_w" ] = round ( transfer
            dst["transfer_w"] = round(transfer, 1)  # info: dst [ "transfer_w" ] = round ( transfer

    for d in devices:  # info: for d in devices :
        if d.get("ac_role") == "transfer_in":  # info: if d . get ( "ac_role" ) == "transfer_in" :
            continue  # info: continue
        aci = _ac_in(d)  # info: set aci
        limit = 550.0 if _is_delta(d) else 300.0 if _is_river(d) else None  # info: set limit
        if limit is not None and aci > limit:  # info: if limit is not None and aci > limit :
            d["on_generator"] = True  # info: d [ "on_generator" ] = True
            if d.get("ac_role") != "transfer_out":  # info: if d . get ( "ac_role" ) != "transfer_out" :
                d["ac_role"] = "generator"  # info: d [ "ac_role" ] = "generator"

    leftover: list[tuple[dict, float]] = []  # info: set leftover
    for d in devices:  # info: for d in devices :
        aco = _ac_out(d)  # info: set aco
        house = max(0.0, aco - transfer) if d is src else aco  # info: set house
        if house < 20:  # info: if house < 20 :
            continue  # info: continue
        leftover.append((d, house))  # info: leftover . append ( ( d , house

    kettle_devs = [(d, w) for d, w in leftover if w >= APPLIANCE_AC_W]  # info: set kettle_devs
    house_devs = [(d, w) for d, w in leftover if w < APPLIANCE_AC_W]  # info: set house_devs
    for d, w in kettle_devs:  # info: for d , w in kettle_devs :
        d["ac_role"] = "appliances"  # info: d [ "ac_role" ] = "appliances"
        d["appliance_w"] = round(w, 1)  # info: d [ "appliance_w" ] = round ( w

    starlink_pick: dict | None = None  # info: set starlink_pick
    in_band = [(d, w) for d, w in house_devs if STARLINK_BAND_LO <= w <= STARLINK_BAND_HI]  # info: set in_band
    if len(in_band) == 1:  # info: if len ( in_band ) == 1 :
        starlink_pick = in_band[0][0]  # info: set starlink_pick
    elif house_devs:  # info: elif house_devs :
        starlink_pick = max(house_devs, key=lambda x: x[1])[0]  # info: set starlink_pick

    for d, w in house_devs:  # info: for d , w in house_devs :
        if d is starlink_pick:  # info: if d is starlink_pick :
            d["starlink_w"] = round(w, 1)  # info: d [ "starlink_w" ] = round ( w
            if d.get("ac_role") not in ("transfer_out", "transfer_in"):  # info: if d . get ( "ac_role" ) not
                d["ac_role"] = "starlink_lights"  # info: d [ "ac_role" ] = "starlink_lights"
        else:  # info: else :
            d["emergency_w"] = round(w, 1)  # info: d [ "emergency_w" ] = round ( w
            if d.get("ac_role") not in ("transfer_out", "transfer_in"):  # info: if d . get ( "ac_role" ) not
                d["ac_role"] = "emergency"  # info: d [ "ac_role" ] = "emergency"
    apply_ebatt(devices)  # info: call apply_ebatt


# ====================================================
# SECTION: function categories
# What it does: categories.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def categories(devices: list[dict]) -> dict:  # info: def categories
    transfer = 0.0  # info: set transfer
    appliances = 0.0  # info: set appliances
    starlink = 0.0  # info: set starlink
    emergency = 0.0  # info: set emergency
    server = 0.0  # info: set server
    drives = 0.0  # info: set drives
    for d in devices:  # info: for d in devices :
        transfer += float(d.get("transfer_w") or 0) if d.get("ac_role") == "transfer_out" else 0.0  # info: set transfer
        appliances += float(d.get("appliance_w") or 0)  # info: set appliances
        starlink += float(d.get("starlink_w") or 0)  # info: set starlink
        emergency += float(d.get("emergency_w") or 0)  # info: set emergency
        usb = float(d.get("dc_out_w") or 0)  # info: set usb
        car = float(d.get("car_w") or 0)  # info: set car
        if car >= CAR_W_MIN:  # info: if car >= CAR_W_MIN :
            drives += car  # info: set drives
        server += max(0.0, usb)  # info: set server
    return {  # info: return {
        "server_mobile_w": round(server, 1),  # info: "server_mobile_w" : round ( server , 1 )
        "starlink_lights_w": round(starlink, 1),  # info: "starlink_lights_w" : round ( starlink , 1 )
        "appliances_w": round(appliances, 1),  # info: "appliances_w" : round ( appliances , 1 )
        "emergency_pack_w": round(emergency, 1),  # info: "emergency_pack_w" : round ( emergency , 1 )
        "hard_drives_12v_w": round(drives, 1),  # info: "hard_drives_12v_w" : round ( drives , 1 )
        "transfer_w": round(transfer, 1),  # info: "transfer_w" : round ( transfer , 1 )
    }  # info: }


# ====================================================
# SECTION: function bank_state
# What it does: bank state.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def bank_state(devices: list[dict]) -> str:  # info: def bank_state
    bits: list[str] = []  # info: set bits
    cats = categories(devices)  # info: set cats
    if cats["appliances_w"] >= 20:  # info: if cats [ "appliances_w" ] >= 20 :
        bits.append("appliances")  # info: bits . append ( "appliances" )
    src = next((d.get("label") for d in devices if d.get("ac_role") == "transfer_out"), None)  # info: set src
    dst = next((d.get("label") for d in devices if d.get("ac_role") == "transfer_in"), None)  # info: set dst
    gens = [d.get("label") for d in devices if d.get("on_generator")]  # info: set gens
    if gens:  # info: if gens :
        bits.append("generator " + ", ".join(str(g) for g in gens))  # info: bits . append ( "generator " + ", " . join
    if src and dst:  # info: if src and dst :
        bits.append(f"transfer {src} -> {dst}")  # info: bits . append ( f" transfer { src
    elif cats["transfer_w"] >= 20:  # info: elif cats [ "transfer_w" ] >= 20 :
        bits.append("AC transfer")  # info: bits . append ( "AC transfer" )
    house_ac = float(cats["starlink_lights_w"] or 0) + float(cats["emergency_pack_w"] or 0)  # info: set house_ac
    if house_ac >= 20:  # info: if house_ac >= 20 :
        bits.append("house AC")  # info: bits . append ( "house AC" )
    if cats["hard_drives_12v_w"] >= CAR_W_MIN:  # info: if cats [ "hard_drives_12v_w" ] >= CAR_W_MIN :
        bits.append("hard drives 12V")  # info: bits . append ( "hard drives 12V" )
    if ebatt_in_w(devices) >= EBATT_MIN_W:  # info: if ebatt_in_w ( devices ) >= EBATT_MIN_W :
        bits.append("E-Batt input")  # info: bits . append ( "E-Batt input" )
    elif solar_in_w(devices) > 20:  # info: elif solar_in_w ( devices ) > 20 :
        bits.append("PV charging")  # info: bits . append ( "PV charging" )
    if cats["server_mobile_w"] > 20:  # info: if cats [ "server_mobile_w" ] > 20 :
        bits.append("server + mobile")  # info: bits . append ( "server + mobile" )
    return " | ".join(bits) or "idle"  # info: return " | " . join ( bits ) or


# ====================================================
# SECTION: function night_charge_callout
# What it does: Past sunset: E-Batt on the MPPT, or AC/DC in with true PV ~0. No invented watts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def night_charge_callout(devices: list[dict], *, sun: dict | None = None) -> dict | None:  # info: def night_charge_callout
    """Past sunset: E-Batt on the MPPT, or AC/DC in with true PV ~0. No invented watts."""  # info: """Past sunset: E-Batt on the MPPT, or AC/DC in with true PV ~0. No invented watts."""
    sun = sun or {}  # info: set sun
    ebatt = ebatt_in_w(devices)  # info: set ebatt
    if ebatt >= EBATT_MIN_W:  # info: if ebatt >= EBATT_MIN_W :
        return {  # info: return {
            "show": True,  # info: "show" : True ,
            "kind": "ebatt",  # info: "kind" : "ebatt" ,
            "title": "E-Batt input",  # info: "title" : "E-Batt input" ,
            "detail": "Recycled Ninebot 220 Wh on the MPPT. EcoFlow calls this PV. Not solar. Nameplate only — no SOC.",  # info: "detail" : "Recycled Ninebot 220 Wh on the MPPT. EcoFlow calls this PV. Not solar. Nameplate only — no SOC." ,
            "in_w": round(ebatt, 1),  # info: "in_w" : round ( ebatt , 1 )
            "nameplate_wh": EBATT_WH,  # info: "nameplate_wh" : EBATT_WH ,
            "sunset": sun.get("sunset") or "",  # info: "sunset" : sun . get ( "sunset" )
        }  # info: }
    if not sun.get("after_sunset"):  # info: if not sun . get ( "after_sunset" )
        return None  # info: return None
    pv = solar_in_w(devices)  # info: set pv
    if pv > PV_FLAT_W:  # info: if pv > PV_FLAT_W :
        return None  # info: return None
    ac_in = sum(float(d.get("ac_in_w") or 0) for d in devices)  # info: set ac_in
    dc_in = sum(float(d.get("dc_in_w") or 0) for d in devices)  # info: set dc_in
    charge = max(ac_in, dc_in)  # info: set charge
    if charge < NIGHT_IN_W:  # info: if charge < NIGHT_IN_W :
        return None  # info: return None
    emergency = any(d.get("ac_role") == "transfer_in" and _is_river(d) for d in devices)  # info: set emergency
    kind = "emergency_topup" if emergency else "night_charge"  # info: set kind
    title = "Emergency pack top-up" if emergency else "Night charge"  # info: set title
    return {  # info: return {
        "show": True,  # info: "show" : True ,
        "kind": kind,  # info: "kind" : kind ,
        "title": title,  # info: "title" : title ,
        "detail": "Measured charge after sunset. Not solar.",  # info: "detail" : "Measured charge after sunset. Not solar." ,
        "in_w": round(charge, 1),  # info: "in_w" : round ( charge , 1 )
        "sunset": sun.get("sunset") or "",  # info: "sunset" : sun . get ( "sunset" )
    }  # info: }


# ====================================================
# SECTION: function _is_delta
# What it does:  is delta.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_delta(d: dict) -> bool:  # info: def _is_delta
    return "delta" in str(d.get("label") or "").lower()  # info: return "delta" in str ( d . get


# ====================================================
# SECTION: function _is_river
# What it does:  is river.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_river(d: dict) -> bool:  # info: def _is_river
    return "river" in str(d.get("label") or "").lower()  # info: return "river" in str ( d . get


# ====================================================
# SECTION: function sun_facts
# What it does: G1 sun_times.facts() subset from the G3 sun file: after_sunset / before_sunrise for today.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sun_facts(t: datetime | None = None) -> dict:  # info: def sun_facts
    """G1 sun_times.facts() subset from the G3 sun file: after_sunset / before_sunrise for today."""  # info: """G1 sun_times.facts() subset from the G3 sun file: after_sunset / before_sunrise for today."""
    t = t or datetime.now()  # info: set t
    try:  # info: try :
        s = json.loads((ENERGY / "sun" / "sun-times-last.json").read_text(encoding="utf-8"))  # info: set s
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }
    if s.get("date") != t.date().isoformat():  # info: if s . get ( "date" ) !=
        return {}  # info: return { }
    hm = t.strftime("%H:%M")  # info: set hm
    return {"ok": True, "sunrise": s.get("sunrise"), "sunset": s.get("sunset"),  # info: return { "ok" : True , "sunrise" :
            "before_sunrise": hm < str(s.get("sunrise") or "00:00"), "after_sunset": hm >= str(s.get("sunset") or "99:99")}  # info: "before_sunrise" : hm < str ( s .


# ====================================================
# SECTION: function g3_devices
# What it does: g3 devices.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def g3_devices() -> list[dict]:  # info: def g3_devices
    out = []  # info: set out
    for key, label in DEVICES:  # info: for key , label in DEVICES :
        try:  # info: try :
            w = json.loads((ENERGY / "watts" / f"{key}-last.json").read_text(encoding="utf-8"))  # info: set w
        except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
            continue  # info: continue
        ac_out, usbc = watts(w.get("ac_output_power")), watts(w.get("usbc_output_power"))  # info: ac_out , usbc = watts ( w .
        out.append({"label": label, "at": w.get("at"), "source": w.get("source"),  # info: out . append ( { "label" : label
                    "pv_w": watts(w.get("solar_input_power")), "ac_in_w": watts(w.get("ac_input_power")),  # info: "pv_w" : watts ( w . get (
                    "ac_out_w": ac_out, "dc_out_w": usbc, "usb_w": usbc, "car_w": 0.0,  # info: "ac_out_w" : ac_out , "dc_out_w" : usbc ,
                    "discharge_w": round(ac_out + usbc, 1), "dc_in_w": 0.0})  # info: "discharge_w" : round ( ac_out + usbc ,
    return out  # info: return out


# ====================================================
# SECTION: function evaluate
# What it does: evaluate.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def evaluate(devices: list[dict], sun: dict) -> dict:  # info: def evaluate
    apply_roles(devices)          # G1 apply_roles ends with apply_ebatt(devices) (sun read from the G3 file)
    apply_ebatt(devices, sun=sun)  # re-run with the caller's sun so --input scenarios are deterministic
    return {"ok": bool(devices), "at": datetime.now().astimezone().isoformat(timespec="seconds"), "sun": sun,  # info: return { "ok" : bool ( devices )
            "categories": categories(devices), "bank_state": bank_state(devices),  # info: "categories" : categories ( devices ) , "bank_state"
            "solar_in_w": solar_in_w(devices), "ebatt_in_w": ebatt_in_w(devices),  # info: "solar_in_w" : solar_in_w ( devices ) , "ebatt_in_w"
            "night_callout": night_charge_callout(devices, sun=sun),  # info: "night_callout" : night_charge_callout ( devices , sun =
            "devices": [{k: d.get(k) for k in ("label", "at", "pv_w", "ac_in_w", "ac_out_w", "dc_out_w", "ac_role",  # info: "devices" : [ { k : d .
                                                 "input_kind", "transfer_w", "appliance_w", "starlink_w", "emergency_w")}  # info: "input_kind" , "transfer_w" , "appliance_w" , "starlink_w" ,
                        for d in devices]}  # info: for d in devices ] }


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if "--input" in sys.argv:  # info: if "--input" in sys . argv :
        spec = json.loads(Path(sys.argv[sys.argv.index("--input") + 1]).read_text(encoding="utf-8"))  # info: set spec
        devices, sun = spec["devices"], spec.get("sun", {})  # info: devices , sun = spec [ "devices" ]
    else:  # info: else :
        devices, sun = g3_devices(), sun_facts()  # info: devices , sun = g3_devices ( ) ,
    print(json.dumps(evaluate(devices, sun), ensure_ascii=False))  # info: call print
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
