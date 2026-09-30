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
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
ENERGY = DB / "Energy"
DEVICES = (("delta2", "Delta 2"), ("river2pro", "River 2 Pro"))

APPLIANCE_AC_W = 1000.0
STARLINK_BAND_LO = 40.0
STARLINK_BAND_HI = 250.0
CAR_W_MIN = 5.0
NIGHT_IN_W = 20.0
PV_FLAT_W = 15.0
EBATT_MIN_W = 20.0
EBATT_MAX_W = 225.0
# Recycled Ninebot pack on the MPPT. Nameplate only — no SOC from EcoFlow.
EBATT_WH = 220.0
USB_KEYS = (
    "pd.usb1Watts",
    "pd.usb2Watts",
    "pd.qcUsb1Watts",
    "pd.typec1Watts",
    "pd.typec2Watts",
)
CAR_KEYS = ("pd.carWatts", "mppt.carOutWatts", "mppt.dcdc12vWatts")


def watts(raw) -> float:
    if raw is None:
        return 0.0
    n = float(raw)
    if abs(n) >= 10_000:
        n = n / 1000.0
    return round(max(0.0, n), 1)


def same_watts(a: float, b: float) -> bool:
    a, b = float(a or 0), float(b or 0)
    if a < 20 or b < 20:
        return False
    slack = max(40.0, 0.12 * max(a, b))
    return abs(a - b) <= slack


def _ac_out(d: dict) -> float:
    return float(d.get("ac_out_w") or 0)


def _ac_in(d: dict) -> float:
    return max(float(d.get("ac_in_w") or 0), float(d.get("ac_charge_w") or 0))


def _is_night(sun: dict | None) -> bool:
    sun = sun or {}
    if sun.get("after_sunset") or sun.get("before_sunrise"):
        return True
    if sun.get("ok") or sun.get("sunset") or sun.get("sunrise"):
        return False
    hour = datetime.now().hour
    return hour >= 19 or hour < 6


def solar_in_w(devices: list[dict]) -> float:
    return round(
        sum(float(d.get("pv_w") or 0) for d in devices if d.get("input_kind") != "ebatt"),
        1,
    )


def ebatt_in_w(devices: list[dict]) -> float:
    return round(
        sum(
            float(d.get("ebatt_w") or d.get("pv_w") or 0)
            for d in devices
            if d.get("input_kind") == "ebatt"
        ),
        1,
    )


def apply_ebatt(devices: list[dict], *, sun: dict | None = None) -> None:
    """After sunset, MPPT ≤225 W that Delta is not discharging is the Ninebot, not PV."""
    for d in devices:
        d.pop("ebatt_w", None)
        d["input_kind"] = None
    if not devices:
        return
    if sun is None:
        sun = sun_facts()  # G3: Database Energy/sun (G1: sun_times.facts())
    if not _is_night(sun):
        return
    incoming = sum(float(d.get("pv_w") or 0) for d in devices)
    if incoming < EBATT_MIN_W or incoming > EBATT_MAX_W:
        return
    delta = next((d for d in devices if _is_delta(d)), None)
    delta_out = 0.0
    if delta:
        delta_out = max(
            float(delta.get("discharge_w") or 0),
            float(delta.get("ac_out_w") or 0),
            float(delta.get("out_w") or 0),
        )
    if same_watts(incoming, delta_out):
        return
    for d in devices:
        w = float(d.get("pv_w") or 0)
        if w >= EBATT_MIN_W:
            d["input_kind"] = "ebatt"
            d["ebatt_w"] = round(w, 1)


def apply_roles(devices: list[dict]) -> None:
    for d in devices:
        d["ac_role"] = None
        d["transfer_sure"] = False
        d.pop("transfer_w", None)
        d.pop("appliance_w", None)
        d.pop("starlink_w", None)
        d.pop("emergency_w", None)
    delta = next((d for d in devices if _is_delta(d)), None)
    river = next((d for d in devices if _is_river(d)), None)

    src = dst = None
    transfer = 0.0
    if delta and river:
        d_out, r_out = _ac_out(delta), _ac_out(river)
        d_in, r_in = _ac_in(delta), _ac_in(river)
        # AC only — never discharge_w (USB inflates that).
        if d_out >= 20 and r_in >= 20:
            src, dst = delta, river
            transfer = min(d_out, r_in)
        elif r_out >= 20 and d_in >= 20:
            src, dst = river, delta
            transfer = min(r_out, d_in)
        if src is not None:
            src["ac_role"] = "transfer_out"
            dst["ac_role"] = "transfer_in"
            src["transfer_sure"] = True
            dst["transfer_sure"] = True
            src["transfer_w"] = round(transfer, 1)
            dst["transfer_w"] = round(transfer, 1)

    for d in devices:
        if d.get("ac_role") in ("transfer_out", "transfer_in"):
            continue
        aci = float(d.get("ac_in_w") or 0)
        if aci >= 20:
            d["ac_role"] = "generator"

    leftover: list[tuple[dict, float]] = []
    for d in devices:
        aco = _ac_out(d)
        house = max(0.0, aco - transfer) if d is src else aco
        if house < 20:
            continue
        leftover.append((d, house))

    kettle_devs = [(d, w) for d, w in leftover if w >= APPLIANCE_AC_W]
    house_devs = [(d, w) for d, w in leftover if w < APPLIANCE_AC_W]
    for d, w in kettle_devs:
        d["ac_role"] = "appliances"
        d["appliance_w"] = round(w, 1)

    starlink_pick: dict | None = None
    in_band = [(d, w) for d, w in house_devs if STARLINK_BAND_LO <= w <= STARLINK_BAND_HI]
    if len(in_band) == 1:
        starlink_pick = in_band[0][0]
    elif house_devs:
        starlink_pick = max(house_devs, key=lambda x: x[1])[0]

    for d, w in house_devs:
        if d is starlink_pick:
            d["starlink_w"] = round(w, 1)
            if d.get("ac_role") not in ("transfer_out", "transfer_in"):
                d["ac_role"] = "starlink_lights"
        else:
            d["emergency_w"] = round(w, 1)
            if d.get("ac_role") not in ("transfer_out", "transfer_in"):
                d["ac_role"] = "emergency"
    apply_ebatt(devices)


def categories(devices: list[dict]) -> dict:
    transfer = 0.0
    appliances = 0.0
    starlink = 0.0
    emergency = 0.0
    server = 0.0
    drives = 0.0
    for d in devices:
        transfer += float(d.get("transfer_w") or 0) if d.get("ac_role") == "transfer_out" else 0.0
        appliances += float(d.get("appliance_w") or 0)
        starlink += float(d.get("starlink_w") or 0)
        emergency += float(d.get("emergency_w") or 0)
        usb = float(d.get("dc_out_w") or 0)
        car = float(d.get("car_w") or 0)
        if car >= CAR_W_MIN:
            drives += car
        server += max(0.0, usb)
    return {
        "server_mobile_w": round(server, 1),
        "starlink_lights_w": round(starlink, 1),
        "appliances_w": round(appliances, 1),
        "emergency_pack_w": round(emergency, 1),
        "hard_drives_12v_w": round(drives, 1),
        "transfer_w": round(transfer, 1),
    }


def bank_state(devices: list[dict]) -> str:
    bits: list[str] = []
    cats = categories(devices)
    if cats["appliances_w"] >= 20:
        bits.append("appliances")
    src = next((d.get("label") for d in devices if d.get("ac_role") == "transfer_out"), None)
    dst = next((d.get("label") for d in devices if d.get("ac_role") == "transfer_in"), None)
    if src and dst:
        bits.append(f"transfer {src} -> {dst}")
    elif cats["transfer_w"] >= 20:
        bits.append("AC transfer")
    house_ac = float(cats["starlink_lights_w"] or 0) + float(cats["emergency_pack_w"] or 0)
    if house_ac >= 20:
        bits.append("house AC")
    if cats["hard_drives_12v_w"] >= CAR_W_MIN:
        bits.append("hard drives 12V")
    if ebatt_in_w(devices) >= EBATT_MIN_W:
        bits.append("E-Batt input")
    elif solar_in_w(devices) > 20:
        bits.append("PV charging")
    if cats["server_mobile_w"] > 20:
        bits.append("server + mobile")
    return " | ".join(bits) or "idle"


def night_charge_callout(devices: list[dict], *, sun: dict | None = None) -> dict | None:
    """Past sunset: E-Batt on the MPPT, or AC/DC in with true PV ~0. No invented watts."""
    sun = sun or {}
    ebatt = ebatt_in_w(devices)
    if ebatt >= EBATT_MIN_W:
        return {
            "show": True,
            "kind": "ebatt",
            "title": "E-Batt input",
            "detail": "Recycled Ninebot 220 Wh on the MPPT. EcoFlow calls this PV. Not solar. Nameplate only — no SOC.",
            "in_w": round(ebatt, 1),
            "nameplate_wh": EBATT_WH,
            "sunset": sun.get("sunset") or "",
        }
    if not sun.get("after_sunset"):
        return None
    pv = solar_in_w(devices)
    if pv > PV_FLAT_W:
        return None
    ac_in = sum(float(d.get("ac_in_w") or 0) for d in devices)
    dc_in = sum(float(d.get("dc_in_w") or 0) for d in devices)
    charge = max(ac_in, dc_in)
    if charge < NIGHT_IN_W:
        return None
    emergency = any(d.get("ac_role") == "transfer_in" and _is_river(d) for d in devices)
    kind = "emergency_topup" if emergency else "night_charge"
    title = "Emergency pack top-up" if emergency else "Night charge"
    return {
        "show": True,
        "kind": kind,
        "title": title,
        "detail": "Measured charge after sunset. Not solar.",
        "in_w": round(charge, 1),
        "sunset": sun.get("sunset") or "",
    }


def _is_delta(d: dict) -> bool:
    return "delta" in str(d.get("label") or "").lower()


def _is_river(d: dict) -> bool:
    return "river" in str(d.get("label") or "").lower()


def sun_facts(t: datetime | None = None) -> dict:
    """G1 sun_times.facts() subset from the G3 sun file: after_sunset / before_sunrise for today."""
    t = t or datetime.now()
    try:
        s = json.loads((ENERGY / "sun" / "sun-times-last.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if s.get("date") != t.date().isoformat():
        return {}
    hm = t.strftime("%H:%M")
    return {"ok": True, "sunrise": s.get("sunrise"), "sunset": s.get("sunset"),
            "before_sunrise": hm < str(s.get("sunrise") or "00:00"), "after_sunset": hm >= str(s.get("sunset") or "99:99")}


def g3_devices() -> list[dict]:
    out = []
    for key, label in DEVICES:
        try:
            w = json.loads((ENERGY / "watts" / f"{key}-last.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        ac_out, usbc = watts(w.get("ac_output_power")), watts(w.get("usbc_output_power"))
        out.append({"label": label, "at": w.get("at"), "source": w.get("source"),
                    "pv_w": watts(w.get("solar_input_power")), "ac_in_w": watts(w.get("ac_input_power")),
                    "ac_out_w": ac_out, "dc_out_w": usbc, "usb_w": usbc, "car_w": 0.0,
                    "discharge_w": round(ac_out + usbc, 1), "dc_in_w": 0.0})
    return out


def evaluate(devices: list[dict], sun: dict) -> dict:
    apply_roles(devices)          # G1 apply_roles ends with apply_ebatt(devices) (sun read from the G3 file)
    apply_ebatt(devices, sun=sun)  # re-run with the caller's sun so --input scenarios are deterministic
    return {"ok": bool(devices), "at": datetime.now().astimezone().isoformat(timespec="seconds"), "sun": sun,
            "categories": categories(devices), "bank_state": bank_state(devices),
            "solar_in_w": solar_in_w(devices), "ebatt_in_w": ebatt_in_w(devices),
            "night_callout": night_charge_callout(devices, sun=sun),
            "devices": [{k: d.get(k) for k in ("label", "at", "pv_w", "ac_in_w", "ac_out_w", "dc_out_w", "ac_role",
                                                 "input_kind", "transfer_w", "appliance_w", "starlink_w", "emergency_w")}
                        for d in devices]}


def main() -> int:
    if "--input" in sys.argv:
        spec = json.loads(Path(sys.argv[sys.argv.index("--input") + 1]).read_text(encoding="utf-8"))
        devices, sun = spec["devices"], spec.get("sun", {})
    else:
        devices, sun = g3_devices(), sun_facts()
    print(json.dumps(evaluate(devices, sun), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
