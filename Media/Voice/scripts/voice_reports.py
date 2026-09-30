#!/usr/bin/env python3
"""G3 voice reports (template-first ports of G1 desks). Stdlib only; run with system python3.

  python3 voice_reports.py <report> [--no-voice]
  reports: hourly_chime · nws_weather · energy_report · remaining_tasks · morning_report · midday_report · late_report
           · earthquake_report · hurricane_desk · kilauea_report · solar_desk · security_desk · bandwidth_desk

Each run writes Database Media/Audio/Voice/Reports/<report>_current.md (old copy -> Reports/Archive/
<report>_YYYYMMDDTHHMM.md) and a stitched WAV Media/Audio/Voice/<report>_current.wav via voice-render.sh
(single-flight lock, nice 10, phrase-clip cache, non-resident). If the lock is busy the WAV is skipped
(rc 75 recorded) and the text still lands. NO delivery (Telegram / radio / speakers).
Only G3 data that exists is read: Database Energy/{soc,watts}/*-last.json (EcoFlow BLE), Database
Weather/Hawai'i (NWS alerts + SFP state forecast, Pacific weather poller), Library Work-Order checkboxes,
/proc, and Database Geology/Earthquakes/{hawaii,global}-last.json (Pacific Geology/scripts/geology_collect.py,
job geology_collect gated RR_GEOLOGY=1). earthquake_report = G1 earthquake-hourly spoken script (Carly), job gated
RR_VOICE_QUAKE=1 (2026-09-29, migration-geology). G1 council_quake (Telegram per-quake posts) stays NOT ported.
hurricane_desk = G1 weather/hurricane-desk Hawaiʻi block (Carly), fed from Database Weather/Hawai'i/hurricanes/
tracking/*/track.json (Pacific weather poller, NHC CurrentStorms, Hawaiʻi-relevant storms only) + NWS HI alerts; job gated
RR_VOICE_HURRICANE=1. G1 global JTWC/RAMMB board, OBS and radio push stay NOT ported.
kilauea_report = G1 hourly Kīlauea desk line (persona._kilauea_line) + the cached HVO-notice lead-in, from Database
Geology/Volcanoes/{kilauea,mauna-loa}-last.json; job gated RR_VOICE_KILAUEA=1. G1 rr-kilauea Grok draft / Discord post NOT ported.
solar_desk / security_desk / bandwidth_desk = G1 hourly-clip-reports desks (Bruce solar; Carly security + bandwidth) from
Database Energy/{soc,watts,sun} and Pacific System/scripts/host_desks.py (net samples in Database System/network/).
Gates PROPOSED (RR_VOICE_SOLAR / RR_VOICE_SECURITY / RR_VOICE_BANDWIDTH) - not registered in jobs.py (sign-off).
Roll-ups can append an LLM summary via run-infer.sh only when RR_VOICE_ROLLUP_LLM=1 (off by default).
Scheduling: jobs.py, one env gate per report (read at poller start). Added 2026-09-29 (g3-voice-reports2).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from speakable import spoken_clock  # noqa: E402
from speakers import retire_current  # noqa: E402

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
LIB = Path(os.environ.get("RR_LIBRARY_ROOT", "/home/rootrecord/RootRecord-Ecosystem/5 - RootRecord-Library"))
PACIFIC = HERE.parents[2]
REPORTS = Path(os.environ.get("RR_VOICE_REPORT_OUT", str(DB.parent / "test-reports" / "Voice")))
WX = DB / "Weather" / "Hawai'i"
ALERTS = WX / "hfo" / "api.weather.gov" / "alerts" / "active" / "area=HI" / "area=HI_current.json"
SFP = WX / "reports" / "0 Level Processing" / "sfp_state_forecast_current.md"
ENERGY = DB / "Energy"
QUAKES = DB / "Geology" / "Earthquakes"
QUAKE_STATE = REPORTS / "earthquake_report_seen.json"  # G1 earthquake-hourly.json seen_ids (new since last report)
QUAKE_STALE_MIN = 20
VOLCANOES = DB / "Geology" / "Volcanoes"
HVO_STALE_MIN = 30
_MAX_HI, _MAX_GLOBAL = 6, 8  # G1 spoken caps
HURRICANES = WX / "hurricanes" / "tracking"  # <Storm>_<first-seen>/track.json (Pacific Weather/hurricanes/scripts/sources.py)
HUR_ACTIVE_H = 6  # a track polled within this many hours counts as on the board
HAWAII_THREAT_NM = 800  # G1 hurricane_desk
HAWAII_POS = {"Honolulu": (21.3069, -157.8583), "Hilo": (19.7297, -155.0900), "Līhuʻe": (21.9811, -159.3711),
              "Kona": (19.6390, -155.9969)}  # G1 hurricane_desk HAWAII_POS
TROPICAL_EVENTS = ("hurricane", "tropical storm", "tropical depression", "typhoon", "cyclone", "storm surge")
COMPASS = ("north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest")
STORM_CLASS = {"HU": "Hurricane", "TS": "Tropical Storm", "TD": "Tropical Depression", "STS": "Subtropical Storm",
               "SS": "Subtropical Storm", "SD": "Subtropical Depression", "PTC": "Post-tropical Cyclone",
               "PC": "Post-tropical Cyclone", "TY": "Typhoon", "STY": "Super Typhoon"}  # NHC classification codes
DEVICES = (("delta2", "Delta 2"), ("river2pro", "River 2 Pro"))
STALE_MIN = 30
KIND = {"hourly_chime": "chime", "nws_weather": "nws", "energy_report": "energy", "remaining_tasks": "remaining",
        "morning_report": "morning", "midday_report": "midday", "late_report": "late", "earthquake_report": "earthquake",
        "hurricane_desk": "hurricane", "kilauea_report": "kilauea",
        "solar_desk": "solar", "security_desk": "security", "bandwidth_desk": "bandwidth"}


def now() -> datetime:
    return datetime.now().astimezone().replace(microsecond=0)


def clock(t: datetime) -> str:
    return spoken_clock(t.hour, t.minute)


def jload(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ------------------------------------------------------------------ data readers (existing G3 sources only)
def energy_facts(t: datetime) -> list[dict]:
    out = []
    for key, name in DEVICES:
        soc, watts = jload(ENERGY / "soc" / f"{key}-last.json"), jload(ENERGY / "watts" / f"{key}-last.json") or {}
        if not soc or "soc" not in soc:
            out.append({"name": name, "ok": False})
            continue
        try:
            age = int((t - datetime.fromisoformat(soc["at"])).total_seconds() // 60)
        except (KeyError, ValueError):
            age = None
        out.append({"name": name, "ok": True, "soc": round(float(soc["soc"])), "at": soc.get("at"), "age_min": age,
                    "solar_w": watts.get("solar_input_power"), "ac_out_w": watts.get("ac_output_power"),
                    "usbc_out_w": watts.get("usbc_output_power"), "ac_in_w": watts.get("ac_input_power"),
                    "charge": watts.get("charge_source")})
    return out


def alerts() -> tuple[list[dict], str | None]:
    d = jload(ALERTS)
    if not isinstance(d, dict):
        return [], None
    rows = []
    for f in d.get("features") or []:
        p = f.get("properties") or {}
        rows.append({"event": p.get("event") or "Alert", "area": (p.get("areaDesc") or "").replace(";", ","),
                     "expires": p.get("expires") or p.get("ends")})
    return rows, d.get("updated")


def sfp_today() -> tuple[str | None, str | None]:
    """First forecast period of the NWS HFO State Forecast (SFP) for Kauai–Oahu–Maui–Molokai–Lanai."""
    try:
        txt = SFP.read_text(encoding="utf-8")
    except OSError:
        return None, None
    issued = re.search(r"^\d{3,4} [AP]M HST .+ \d{4}$", txt, re.M)
    m = re.search(r"^\.([A-Z][A-Z ]+)\.\.\.(.+?)(?=^\.[A-Z]|```|\Z)", txt, re.M | re.S)
    if not m:
        return None, issued.group(0) if issued else None
    body = " ".join(m.group(2).split())
    return f"{m.group(1).title()}: {body}", issued.group(0) if issued else None


def open_tasks() -> tuple[int, list[tuple[int, str]]]:
    wo = LIB / "Documentation" / "06-development" / "Work-Orders"
    per = []
    for f in sorted(wo.glob("*.md")):
        try:
            n = len(re.findall(r"^\s*- \[ \]", f.read_text(encoding="utf-8"), re.M))
        except OSError:
            continue
        if n:
            code = re.search(r"(WO-[A-Z0-9-]+?)(?:-\d{4}-\d{2}-\d{2})?(?:\.md|-Action)", f.name)
            per.append((n, code.group(1) if code else f.stem))
    per.sort(key=lambda x: (-x[0], x[1]))
    return sum(n for n, _ in per), per


def host() -> dict:
    def snap():
        v = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        return sum(v), v[3] + (v[4] if len(v) > 4 else 0)
    t1, i1 = snap(); time.sleep(0.5); t2, i2 = snap()
    m = {ln.split(":")[0]: int(ln.split()[1]) for ln in open("/proc/meminfo")}
    return {"cpu": round(100 * (1 - (i2 - i1) / max(1, t2 - t1))), "mem": round(100 * (1 - m["MemAvailable"] / m["MemTotal"]))}


def quake_facts(t: datetime) -> dict:
    """Database Geology/Earthquakes last files (written by Pacific Geology/scripts/geology_collect.py)."""
    out = {}
    for key in ("hawaii", "global"):
        d = jload(QUAKES / f"{key}-last.json")
        if not isinstance(d, dict) or not isinstance(d.get("events"), list):
            out[key] = None
            continue
        try:
            age = int((t - datetime.fromisoformat(d["at"])).total_seconds() // 60)
        except (KeyError, TypeError, ValueError):
            age = None
        out[key] = dict(d, age_min=age)
    return out


def _m25(events: list[dict]) -> list[dict]:
    out = []
    for e in events:
        try:
            if float(e.get("mag") or 0) >= 2.5:
                out.append(e)
        except (TypeError, ValueError):
            continue
    return out


# ------------------------------------------------------------------ builders: (markdown, spoken sentences)
def b_hourly_chime(t: datetime):
    h, mi = t.hour, (0 if t.minute < 15 else 30 if t.minute < 45 else 0)
    if t.minute >= 45:
        h = (h + 1) % 24
    line = f"It's {spoken_clock(h, mi)}.".replace("..", ".")
    return f"# Hourly chime — {t.isoformat()}\n\n{line}\n", [line]


def b_nws_weather(t: datetime):
    rows, upd = alerts()
    today, issued = sfp_today()
    sp = ["NWS Hawaii Report."]
    md = [f"# NWS Hawaii — {t.isoformat()}", "", f"- Alerts source: `api.weather.gov/alerts/active?area=HI` (updated {upd or 'n/a'})",
          f"- Forecast source: NWS HFO State Forecast (SFP), issued {issued or 'n/a'}", "", "## Active alerts", ""]
    if rows:
        sp.append(f"{len(rows)} active alert{'s' if len(rows) != 1 else ''} for Hawaii.")
        for r in rows[:3]:
            sp.append(f"{r['event']} for {r['area']}.")
        md += [f"- **{r['event']}** — {r['area']} (expires {r['expires']})" for r in rows]
    else:
        sp.append("No active HI alerts from the API sample.")
        md.append("- none")
    md += ["", "## State forecast (first period)", "", today or "_not on file_", ""]
    if today:
        sp.append(f"State forecast for {today.split(':', 1)[0].lower()}.")
        sp.append(today.split(":", 1)[1].strip().rstrip(".") + ".")
    return "\n".join(md), sp


def b_energy_report(t: datetime):
    facts = energy_facts(t)
    sp = ["Energy desk report."]
    md = [f"# Energy desk — {t.isoformat()}", "", "| Device | SOC | Solar in | AC out | USB-C out | Reading at | Age |", "|---|---|---|---|---|---|---|"]
    if not any(f["ok"] for f in facts):
        sp.append("EcoFlow is offline.")
    for f in facts:
        if not f["ok"]:
            md.append(f"| {f['name']} | no reading | | | | | |")
            continue
        md.append(f"| {f['name']} | {f['soc']}% | {f['solar_w']} W | {f['ac_out_w']} W | {f['usbc_out_w']} W | {f['at']} | {f['age_min']} min |")
        s = f"{f['name']} battery {f['soc']}%"
        if f["solar_w"] is not None:
            s += f", solar input {spoken_watts(f['solar_w'])}"
        out = sum(x for x in (f["ac_out_w"], f["usbc_out_w"]) if isinstance(x, (int, float)))
        if f["ac_out_w"] is not None or f["usbc_out_w"] is not None:
            s += f", output {spoken_watts(out)}"
        sp.append(s + ".")
        if f["age_min"] is not None and f["age_min"] > STALE_MIN:
            sp.append(f"That {f['name']} reading is {f['age_min']} minutes old.")
    md += ["", "_Source: Database Energy/soc + Energy/watts (*-last.json, EcoFlow BLE). Vision caption not used._", ""]
    return "\n".join(md), sp


def b_earthquake_report(t: datetime):
    """G1 earthquake-hourly build_spoken + report lines, fed from Database Geology/ instead of a live USGS call."""
    q = quake_facts(t)
    hi, gl = q.get("hawaii"), q.get("global")
    md = [f"# Earthquake report — {t.isoformat()}", ""]
    if not hi and not gl:
        md += ["_No USGS data on file (Database Geology/Earthquakes/*-last.json missing). Run geology_collect.py._", ""]
        return "\n".join(md), ["Earthquake data is not on file."]
    prev = jload(QUAKE_STATE) or {}
    seen = set(prev.get("seen_ids") or [])
    hi_ev, gl_ev = list((hi or {}).get("events") or []), list((gl or {}).get("events") or [])
    fresh_hi = [e for e in hi_ev if e.get("id") and e["id"] not in seen]
    fresh_gl = [e for e in gl_ev if e.get("id") and e["id"] not in seen]
    sp = [f"USGS earthquake report at {clock(t)} Hawaiian Standard Time.".replace("..", ".")]
    if hi is None:
        sp.append("Hawaii earthquake data is not on file.")
    elif fresh_hi:
        sp.append(f"{len(fresh_hi)} new Hawaii earthquake{'s' if len(fresh_hi) != 1 else ''}.")
        sp += [f"Magnitude {e.get('mag')} {e.get('place')}." for e in fresh_hi[:_MAX_HI]]
    else:
        sp.append("No new Hawaii earthquakes since the last report.")
    if hi is not None:
        sp.append(f"Hawaii last twenty four hours: {len(_m25(hi_ev))} magnitude 2.5 or greater.")
    if gl is None:
        sp.append("Global earthquake data is not on file.")
    elif fresh_gl:
        sp.append(f"{len(fresh_gl)} new global earthquake{'s' if len(fresh_gl) != 1 else ''}.")
        sp += [f"Magnitude {e.get('mag')} {e.get('place')}." for e in fresh_gl[:_MAX_GLOBAL]]
    else:
        sp.append("No new global earthquakes since the last report.")
    if gl is not None:
        sp.append(f"Global last twenty four hours: {len(_m25(gl_ev))} magnitude 2.5 or greater.")
    for label, d in (("Hawaii", hi), ("global", gl)):
        if d and d.get("age_min") is not None and d["age_min"] > QUAKE_STALE_MIN:
            sp.append(f"The {label} USGS data is {d['age_min']} minutes old.")
    for label, d, fresh in (("Hawaii", hi, fresh_hi), ("Global", gl, fresh_gl)):
        md += [f"## {label} Changes Since Last Report"]
        md += [f"- M{e.get('mag')} {e.get('place')} ({e.get('time_hst')})" for e in fresh[:12]] or ["- No new earthquakes."]
        if len(fresh) > 12:
            md.append(f"- ...and {len(fresh) - 12} more new earthquakes.")
        ev = list((d or {}).get("events") or [])
        big = max((float(e["mag"]) for e in _m25(ev)), default=None)
        md += ["", f"## {label} 24-Hour M2.5+ Summary",
               f"- {len(_m25(ev))} earthquakes" + (f"; largest M{big:g}." if big is not None else "."),
               f"- Source: `{(d or {}).get('source', 'n/a')}` (collected {(d or {}).get('at', 'n/a')})", ""]
    if not os.environ.get("RR_VOICE_QUAKE_DRY"):
        ids = [e["id"] for e in hi_ev + gl_ev if e.get("id")]
        state = {"seen_ids": (list(seen) + [i for i in ids if i not in seen])[-400:], "updated_at": t.isoformat()}
        QUAKE_STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = QUAKE_STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, QUAKE_STATE)
    return "\n".join(md), sp


def _gc_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 3440.065 * math.asin(min(1.0, math.sqrt(a)))


def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math  # G1 hurricane_desk._bearing
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _compass(deg: float) -> str:
    return COMPASS[int((deg + 22.5) // 45) % 8]


def _nearest_island(lat: float, lon: float) -> tuple[str, float]:
    return min(((k, _gc_nm(v[0], v[1], lat, lon)) for k, v in HAWAII_POS.items()), key=lambda kv: kv[1])


def hurricane_facts(t: datetime) -> list[dict]:
    """Storms from the G3 weather poller's track.json files (latest position, movement from the last two distinct fixes)."""
    out = []
    for tr in sorted(HURRICANES.glob("*/track.json")) if HURRICANES.is_dir() else []:
        d = jload(tr) or {}
        pos = [p for p in d.get("positions") or [] if p.get("lat") is not None and p.get("lon") is not None]
        if not pos:
            continue
        last = pos[-1]
        try:
            lat, lon = float(last["lat"]), float(last["lon"])
            age_h = (t - datetime.fromisoformat(last["polled_at_hst"])).total_seconds() / 3600
        except (KeyError, TypeError, ValueError):
            continue
        fixes = []  # first poll time of each distinct position
        for p in pos:
            key = (float(p["lat"]), float(p["lon"]))
            if not fixes or fixes[-1][0] != key:
                fixes.append((key, p.get("polled_at_hst")))
        island, nm = _nearest_island(lat, lon)
        move_c = move_kt = approach = None
        if len(fixes) >= 2:
            (a, ta), (b, tb) = fixes[-2], fixes[-1]
            move_c = _compass(_bearing(a[0], a[1], b[0], b[1]))
            try:
                hrs = (datetime.fromisoformat(tb) - datetime.fromisoformat(ta)).total_seconds() / 3600
                move_kt = round(_gc_nm(a[0], a[1], b[0], b[1]) / hrs) if hrs > 0.5 else None
            except (TypeError, ValueError):
                move_kt = None
            prev_nm = _nearest_island(a[0], a[1])[1]
            approach = "toward" if nm < prev_nm - 5 else "away" if nm > prev_nm + 5 else "steady"
        try:
            kt = int(round(float(last.get("intensity")))) if last.get("intensity") not in (None, "") else None
        except (TypeError, ValueError):
            kt = None
        code = str(last.get("classification") or "").upper()
        out.append({"name": str(d.get("storm_name") or tr.parent.name.split("_")[0]).replace("_", " "),
                    "label": STORM_CLASS.get(code, "Tropical system"), "code": code, "lat": lat, "lon": lon,
                    "knots": kt, "island": island, "nm": int(round(nm)),
                    "bearing": _compass(_bearing(HAWAII_POS[island][0], HAWAII_POS[island][1], lat, lon)),
                    "movement_compass": move_c, "movement_kt": move_kt, "approach": approach, "fixes": len(fixes),
                    "polled_at": last.get("polled_at_hst"), "age_h": round(age_h, 1), "active": age_h <= HUR_ACTIVE_H,
                    "path": str(tr.relative_to(DB))})
    return sorted(out, key=lambda s: s["nm"])


def b_hurricane_desk(t: datetime):
    """G1 hurricane_desk.hawaii_block + build spoken text, from G3 track.json + NWS HI alerts (never invents storms)."""
    storms = hurricane_facts(t)
    active = [s for s in storms if s["active"]]
    rows, updated = alerts()
    trop = [r for r in rows if any(k in str(r["event"]).lower() for k in TROPICAL_EVENTS)]
    sp = ["Hurricane global desk, Pacific Root Server."]
    if trop:
        watch = " NWS Honolulu: " + "; ".join(f"{r['event']} for {r['area'] or 'Hawaii'}" for r in trop) + "."
    elif updated is None:
        watch = " NWS Hawaii alert data is not on file."
    else:
        watch = " No tropical watches or warnings for Hawaii in the last NWS pull."
    if not active:
        sp.append("Nearest Hurricane from a Hawaiian island. No tropical system with a mapped position is on the board."
                  + watch)
    else:
        n = active[0]
        local = bool(trop) or n["nm"] < HAWAII_THREAT_NM
        title = "Nearest Hurricane from a Hawaiian island" if local else "Pacific basin cyclone, not a Hawaii threat"
        ns, ew = ("north" if n["lat"] >= 0 else "south"), ("east" if n["lon"] >= 0 else "west")
        move = ""
        if n["movement_kt"] == 0:
            move = " Nearly stationary."
        elif n["movement_compass"]:
            vs = {"toward": "toward Hawaii", "away": "away from Hawaii",
                  "steady": "holding roughly steady relative to Hawaii"}.get(n["approach"] or "", "")
            kt_s = f" at about {n['movement_kt']} knots" if n["movement_kt"] else ""
            move = f" Moving {n['movement_compass']}{kt_s}" + (f", {vs}." if vs else ".")
        wind = f" Maximum sustained winds {n['knots']} knots." if n["knots"] else ""
        hint = ""
        if not local:
            hint = " Do not treat this as a Hawaii local storm."
            if n["bearing"] == "west":
                hint = " West of Kauai is toward Asia and Japan, not toward the islands." + hint
        sp.append(f"{title}. {n['label']} {n['name']} is about {n['nm']} nautical miles from {n['island']}."
                  f" Center {abs(n['lat']):.1f} {ns}, {abs(n['lon']):.1f} {ew}. It bears {n['bearing']} of {n['island']}."
                  f"{hint}{move}{wind}{watch}")
        if len(active) > 1:
            others = "; ".join(f"{s['label']} {s['name']}, about {s['nm']} nautical miles from {s['island']}" for s in active[1:4])
            sp.append(f"{len(active)} tropical systems are on the Hawaii tracking board. Also tracked: {others}.")
    sp.append("Stay with NWS Honolulu for watches and warnings.")
    md = [f"# Hurricane desk — {t.isoformat()}", "", " ".join(sp), "", "## Tracked systems (G3 weather poller)", ""]
    md += ["| Storm | Class | Knots | Position | Nearest island | nm | Bearing | Movement | Last poll (HST) | On board |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {s['name']} | {s['label']} ({s['code'] or '?'}) | {s['knots'] if s['knots'] is not None else 'n/a'} | "
           f"{s['lat']:.1f}, {s['lon']:.1f} | {s['island']} | {s['nm']} | {s['bearing']} | "
           f"{(s['movement_compass'] or 'n/a')} {('~' + str(s['movement_kt']) + ' kt') if s['movement_kt'] else ''} {s['approach'] or ''} | "
           f"{s['polled_at']} ({s['age_h']} h ago) | {'yes' if s['active'] else 'stale'} |" for s in storms] or ["| none on file | | | | | | | | | |"]
    md += ["", f"NWS HI alerts (updated {updated or 'n/a'}): " + (", ".join(r["event"] for r in rows) or "none") +
           f"; tropical: {len(trop)}.", "",
           "_Sources: Database `Weather/Hawai'i/hurricanes/tracking/*/track.json` (NHC CurrentStorms, Hawaiʻi-relevant "
           "storms only: 800 nm or CPHC) and the NWS HI alerts file. Movement is estimated from the last two distinct "
           "tracked fixes. G1's global JTWC/RAMMB board is not collected in G3, so there is no global count._", ""]
    return "\n".join(md), sp


def _first_sentences(text: str, n: int = 2, cap: int = 420) -> str:
    parts = re.split(r"(?<=[.!?])\s+", " ".join((text or "").split()))
    return " ".join(parts[:n])[:cap].strip()


def b_kilauea_report(t: datetime):
    """G1 hourly Kīlauea desk (persona._kilauea_line wording) + HVO notice excerpt, from Database Geology/Volcanoes/."""
    k, ml = jload(VOLCANOES / "kilauea-last.json"), jload(VOLCANOES / "mauna-loa-last.json")
    hi = jload(QUAKES / "hawaii-last.json") or {}
    md = [f"# Kilauea report — {t.isoformat()}", ""]
    if not isinstance(k, dict) or not k.get("alert_level"):
        md += ["_No HVO data on file (Database Geology/Volcanoes/kilauea-last.json missing). Run geology_collect.py._", ""]
        return "\n".join(md), ["Kilauea: DOWN."]
    level = str(k.get("alert_level") or "unknown").strip().lower()
    erupting = k.get("erupting")
    if erupting:
        state = "is erupting"
    elif level in {"advisory", "watch", "warning", "normal"} and erupting is False:
        state = "not erupting"
    else:
        state = "eruption state unknown"
    color = str(k.get("color_code") or "").lower()
    sp = ["Kilauea Report.", f"It's {clock(t)} Hawaiian Standard Time.".replace("..", "."),
          f"Kilauea volcano alert level: {level}" + (f", aviation color code {color}." if color else ".") +
          f" Kilauea {state}."]
    note = k.get("latest_activity_notice") if erupting and k.get("latest_activity_notice") else k.get("latest_notice")
    note = note if isinstance(note, dict) else {}
    excerpt = _first_sentences(note.get("synopsis") or "")
    if excerpt:
        sp += ["Here is the latest Hawaiian Volcano Observatory notice, unedited for honesty.", excerpt]
    else:
        sp.append("No HVO headline in this sample.")
    if hi.get("kilauea_150km_count") is not None:
        n = int(hi["kilauea_150km_count"])
        sp.append(f"USGS: {n} earthquake{'s' if n != 1 else ''} magnitude 1 or greater within 150 kilometers of Kilauea in the last "
                  f"{hi.get('window_h', 24)} hours.")
    if isinstance(ml, dict) and ml.get("alert_level"):
        sp.append(f"Mauna Loa alert level: {str(ml['alert_level']).lower()}.")
    try:
        age = int((t - datetime.fromisoformat(k["at"])).total_seconds() // 60)
    except (KeyError, TypeError, ValueError):
        age = None
    if age is not None and age > HVO_STALE_MIN:
        sp.append(f"That HVO status is {age} minutes old.")
    md += [f"- **Kīlauea:** {k.get('alert_level')} / {k.get('color_code')} — erupting `{erupting}` — {k.get('headline')}",
           f"- **Latest notice used:** {note.get('type', 'n/a')} ({note.get('sent_utc', 'n/a')} UTC) {note.get('url', '')}",
           f"- **Mauna Loa:** {(ml or {}).get('alert_level', 'n/a')} / {(ml or {}).get('color_code', 'n/a')}",
           f"- **Quakes ≤150 km of Kīlauea (M≥1, {hi.get('window_h', 24)} h):** {hi.get('kilauea_150km_count', 'n/a')}",
           f"- **Collected:** {k.get('at')} (USGS HANS)", "", "## Spoken", "", " ".join(sp), ""]
    return "\n".join(md), sp


def _host_desks():
    sys.path.insert(0, str(PACIFIC / "System" / "scripts"))
    import host_desks  # noqa: E402  (Pacific System/scripts/host_desks.py, G1 host_metrics port)
    return host_desks


def spoken_watts(v) -> str:
    """Spoken power: whole watts; 0 (or 0.0 from the cloud read) -> "zero watts" (2026-09-29 text fix)."""
    w = int(round(float(v)))
    return "zero watts" if w == 0 else ("one watt" if w == 1 else f"{w} watts")


def spoken_hhmm(hhmm) -> str:
    """"06:11" -> "six eleven a.m." (sun times spoken as words; 2026-09-29 text fix). Non-HH:MM passes through."""
    try:
        h, m = (int(x) for x in str(hhmm).split(":")[:2])
    except (TypeError, ValueError):
        return str(hhmm)
    return spoken_clock(h, m)


def b_solar_desk(t: datetime):
    """G1 hourly-clip-reports solar_spoken ("Solar desk at <clock>. <EcoFlow line>") + G1 hourly-solar-weather sun times."""
    facts = energy_facts(t)
    sun = jload(ENERGY / "sun" / "sun-times-last.json") or {}
    sp = [f"Solar desk at {clock(t)} Hawaiian Standard Time.".replace("..", ".")]
    lines, spoken_lines = [], []
    for f in facts:
        if not f["ok"]:
            lines.append(f"{f['name']}: offline")
            spoken_lines.append(f"{f['name']}: offline")
            continue
        bits, sbits = [f"state of charge {f['soc']}%"], [f"state of charge {f['soc']}%"]
        power = [(k, f.get(k)) for k in ("solar_w", "ac_out_w") if f.get(k) is not None]
        for k, v in power:
            bits.append(f"{'solar input' if k == 'solar_w' else 'AC out'} {v} W")
        if power and all(int(round(float(v))) == 0 for _, v in power):
            sbits.append("idle")  # no solar in, no AC out
        else:
            sbits += [f"{'solar input' if k == 'solar_w' else 'AC out'} {spoken_watts(v)}" for k, v in power]
        lines.append(f"{f['name']}: " + ", ".join(bits))
        spoken_lines.append(f"{f['name']}: " + ", ".join(sbits))
    if not any(f["ok"] for f in facts):
        sp.append("EcoFlow is offline.")
    else:
        sp += [x + "." for x in spoken_lines]
        for f in facts:
            if f["ok"] and f.get("age_min") is not None and f["age_min"] > STALE_MIN:
                sp.append(f"That {f['name']} reading is {f['age_min']} minutes old.")
    if sun.get("date") == t.date().isoformat() and sun.get("sunset"):
        if t.strftime("%H:%M") < sun["sunset"]:
            sp.append(f"Sunrise was {spoken_hhmm(sun['sunrise'])}, sunset is {spoken_hhmm(sun['sunset'])}.".replace("..", "."))
        elif sun.get("next_sunrise"):
            sp.append(f"Sunset was {spoken_hhmm(sun['sunset'])}; next sunrise {spoken_hhmm(sun['next_sunrise'])}.".replace("..", "."))
        else:
            sp.append(f"Sunset was {spoken_hhmm(sun['sunset'])}.".replace("..", "."))
    md = [f"# Solar desk — {t.isoformat()}", ""] + [f"- {x}" for x in lines] + [
        f"- Sun: {sun.get('sunrise', 'n/a')} / {sun.get('sunset', 'n/a')} ({sun.get('date', 'n/a')}, Open-Meteo)", "",
        "## Spoken", "", " ".join(sp), "",
        "_Source: Database Energy/soc + Energy/watts (EcoFlow BLE) + Energy/sun/sun-times-last.json._", ""]
    return "\n".join(md), sp


def b_security_desk(t: datetime):
    """G1 host_metrics.security_spoken, unchanged wording, from host_desks.security_snapshot() (counts only)."""
    row = _host_desks().security_snapshot()
    bits = [f"Security desk at {clock(t)} Hawaiian Standard Time.".replace("..", ".")]
    ufw = row.get("ufw_boot")
    if ufw is True:
        bits.append("Uncomplicated Firewall is set to start on boot.")
    elif ufw is False:
        bits.append("Uncomplicated Firewall is not set to start on boot.")
    ssh = row.get("ssh_active")
    if ssh is True:
        bits.append("OpenSSH service is active.")
    elif ssh is False:
        bits.append("OpenSSH service is not active.")
    if row.get("listen_tcp") is not None:
        bits.append(f"{row['listen_tcp']} TCP listeners.")
    if row.get("established") is not None:
        bits.append(f"{row['established']} established connections.")
    if row.get("failed_1h") is not None:
        bits.append(f"Failed sign-ins: {row['failed_1h']} in the last hour, {row['failed_24h']} in the last twenty four hours.")
    else:
        bits.append("The sign-in log is not readable.")
    if row.get("fail2ban"):
        bits.append("Fail2ban is running.")
    md = [f"# Security desk — {t.isoformat()}", "", "```json", json.dumps(row, indent=2), "```", "", "## Spoken", "", " ".join(bits), "",
          "_Source: Pacific System/scripts/host_desks.py (ufw.conf, systemctl is-active, /proc/net/tcp, auth.log counts only)._", ""]
    return "\n".join(md), bits


def b_bandwidth_desk(t: datetime):
    """G1 host_metrics.bandwidth_spoken (records one sample, then last hour / 24 h deltas)."""
    hd = _host_desks()
    net = hd.net_counters()
    if net and not os.environ.get("RR_VOICE_BANDWIDTH_DRY"):
        hd.append_net_sample(net)
    hour, day = hd.net_usage_window(3600, now=net), hd.net_usage_window(86400, now=net)
    md = [f"# Bandwidth desk — {t.isoformat()}", "", f"- iface: {(net or {}).get('iface')} ({(net or {}).get('link')})",
          f"- last hour: {hour}", f"- last 24 h: {day}", ""]
    if hour is None and day is None:
        md += ["_Not enough samples yet (needs samples covering 45 min; run `host_desks.py net-sample` every 5 min)._", ""]
        return "\n".join(md), ["Bandwidth data is not on file yet."]
    sb = hd.spoken_bytes
    bits = [f"Bandwidth desk at {clock(t)} Hawaiian Standard Time.".replace("..", "."), f"This host is on {(net or {}).get('link') or 'network'}."]
    bits.append(f"Last hour: {sb(hour['rx'])} down, {sb(hour['tx'])} up, {sb(hour['total'])} total." if hour else "Last hour is not on file yet.")
    bits.append(f"Last twenty four hours: {sb(day['rx'])} down, {sb(day['tx'])} up, {sb(day['total'])} total." if day
                else "Last twenty four hours is not on file yet.")
    md += ["## Spoken", "", " ".join(bits), ""]
    return "\n".join(md), bits


def _say_code(code: str) -> str:
    """WO-ECO -> 'E C O', WO-RPT-001 -> 'R P T 1' (short acronyms spelled out for Kokoro)."""
    parts = []
    for p in code.removeprefix("WO-").split("-"):
        parts.append(" ".join(p) if p.isalpha() and len(p) <= 4 else str(int(p)) if p.isdigit() else p.title())
    return " ".join(parts)


def b_remaining_tasks(t: datetime):
    total, per = open_tasks()
    md = [f"# Remaining tasks — {t.isoformat()}", "", f"Open checkboxes in Library `Documentation/06-development/Work-Orders/`: **{total}**", "",
          "| Work order | Open |", "|---|---|"] + [f"| {c} | {n} |" for n, c in per] + [""]
    sp = ["Remaining tasks."]
    if total:
        sp.append(f"{total} open items across {len(per)} work orders.")
        top = ", ".join(f"{_say_code(c)} {n}" for n, c in per[:3])
        sp.append(f"Most open: {top}.")
    else:
        sp.append("No open tasks on file.")
    return "\n".join(md), sp


def _rollup(t: datetime, slot: str):
    title = {"morning": "Morning report.", "midday": "Midday report.", "late": "Late report."}[slot]
    facts, (rows, _), (today, _), h, (tasks, per) = energy_facts(t), alerts(), sfp_today(), host(), open_tasks()
    sp = [title, f"It's {clock(t)} Hawaiian Standard Time.".replace("..", ".")]
    lines = []
    ok = [f for f in facts if f["ok"]]
    if ok:
        s = "Batteries: " + ", ".join(f"{f['name']} {f['soc']}%" for f in ok)
        solar = sum(f["solar_w"] or 0 for f in ok)
        # spoken form says "at": "Delta 2 36%" would hit the G1 clock rule ("two thirty six a.m.")
        sp.append("Battery levels: " + ", ".join(f"{f['name']} at {f['soc']}%" for f in ok) + f". Solar input {spoken_watts(solar)}.")
        lines.append(s + f"; solar input {solar} W")
    else:
        sp.append("EcoFlow is offline.")
        lines.append("EcoFlow: no reading")
    if rows:
        sp.append(f"{len(rows)} active weather alert{'s' if len(rows) != 1 else ''}, including {rows[0]['event']}.")
    else:
        sp.append("No active HI alerts from the API sample.")
    lines.append(f"NWS alerts active: {len(rows)}" + (f" ({', '.join(r['event'] for r in rows)})" if rows else ""))
    if today:
        first = re.split(r"(?<=\.)\s", today.split(":", 1)[1].strip())[0]
        sp.append(f"Forecast for {today.split(':', 1)[0].lower()}: {first}")
        lines.append(f"Forecast {today}")
    sp.append(f"Host CPU {h['cpu']}%, memory {h['mem']}% used.")
    lines.append(f"Host CPU {h['cpu']}%, memory {h['mem']}% used")
    sp.append(f"{tasks} open work order items.")
    lines.append(f"Open work-order items: {tasks}")
    summary = llm_summary(lines) if os.environ.get("RR_VOICE_ROLLUP_LLM", "0") == "1" else None
    if summary:
        sp.append(summary)
    sp.append("End of report.")
    md = [f"# {title[:-1]} — {t.isoformat()}", "", "## Measured", ""] + [f"- {x}" for x in lines]
    md += ["", "## LLM summary", "", f"{summary} _(run-infer.sh, RR_VOICE_ROLLUP_LLM=1)_" if summary else "_off (RR_VOICE_ROLLUP_LLM != 1)_", ""]
    return "\n".join(md), sp


def llm_summary(lines: list[str]) -> str | None:
    """Optional, gated: 1–2 sentence summary via run-infer.sh (FLM on demand, single-flight). Metadata-only logging."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    try:
        env = dict(os.environ, DESK_LIVE_FILE=f.name, RR_CALLER="voice_rollup")
        p = subprocess.run(["bash", str(PACIFIC / "System" / "scripts" / "plumbing" / "run-infer.sh"), "ava",
                            "Summarize the measured desk lines in one or two short spoken sentences. Use only those numbers."],
                           capture_output=True, text=True, timeout=180, env=env)
        out = " ".join(ln for ln in (p.stdout or "").splitlines() if not ln.startswith("[ok]")).strip()
        return out[:400] if p.returncode == 0 and out and out != "No live desk data attached." else None
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        os.unlink(f.name)


BUILD = {"hourly_chime": b_hourly_chime, "nws_weather": b_nws_weather, "energy_report": b_energy_report,
         "remaining_tasks": b_remaining_tasks, "morning_report": lambda t: _rollup(t, "morning"),
         "midday_report": lambda t: _rollup(t, "midday"), "late_report": lambda t: _rollup(t, "late"),
         "earthquake_report": b_earthquake_report, "hurricane_desk": b_hurricane_desk,
         "kilauea_report": b_kilauea_report, "solar_desk": b_solar_desk, "security_desk": b_security_desk,
         "bandwidth_desk": b_bandwidth_desk}


def write_md(report: str, md: str) -> Path:
    path = REPORTS / f"{report}_current.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        retire_current(path)
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(md.rstrip() + "\n\n_Template report; measured values only. Delivery OFF._\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def voice(report: str, spoken: list[str]) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(" ".join(spoken))
    cmd = ["bash", str(HERE / "voice-render.sh"), "stitch", "--report", report, "--kind", KIND[report], "--text-file", f.name]
    if report == "hourly_chime":
        cmd.append("--no-gate")  # G1 chimes bypassed the live-facts gate (spelled-out times carry no digits)
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        last = (p.stdout.strip().splitlines() or ["{}"])[-1]
        try:
            res = json.loads(last)
        except ValueError:
            res = {}
        res["rc"] = p.returncode
        if p.returncode == 75:
            res["detail"] = "busy (single-flight) — WAV skipped"
        return res
    finally:
        os.unlink(f.name)


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in BUILD:
        print(json.dumps({"ok": False, "detail": f"usage: voice_reports.py {'|'.join(BUILD)} [--no-voice]"}))
        return 2
    report, t = sys.argv[1], now()
    md, spoken = BUILD[report](t)
    res = {"ok": True, "report": report, "md": str(write_md(report, md)), "sentences": len(spoken)}
    if "--no-voice" not in sys.argv:
        res["voice"] = voice(report, spoken)
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
