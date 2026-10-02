# ==============================================================================
# FILE: System/scripts/uptime_log.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Desk-up / desk-down event log (G3 port of G1 uptime-log/scripts/uptime_log.py). Live stamps only — never invent hours.

  python3 uptime_log.py [tick|facts|recent]

Same event kinds (origin_start, heartbeat_gap, desk_up), same KEEP=400 rolling JSONL and GAP_S=180 gap rule.
G3 changes (documented): stdlib only (psutil.boot_time -> /proc/uptime); the "origin" is the Pacific poller (tick runs
from jobs.py); gap timing uses wall clock + kernel boot_id instead of time.monotonic() (monotonic resets on reboot,
so G1 could not see a reboot gap) and a boot_id change logs a `boot` event. G1 origin_start/stop hooks were called
by Ava-Core origin; G3 has no such hook, so the first tick after a start logs origin_start(inferred=True) as G1 did.
Files: Database System/uptime/uptime-events.jsonl + uptime-last.json (marker). Gated RR_UPTIME_LOG=1 (every 60 s).
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import time  # info: import time
import math  # info: import math
from datetime import datetime, timezone  # info: from datetime import datetime , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))  # info: set DB
DIR = DB / "System" / "uptime"  # info: set DIR
PATH, MARKER = DIR / "uptime-events.jsonl", DIR / "uptime-last.json"  # info: PATH , MARKER = DIR / "uptime-events.jsonl" ,
PRESENCE = DIR / "presence.json"  # info: set PRESENCE
OFFLINE_PATH = DIR / "offline-samples.jsonl"  # info: set OFFLINE_PATH
RETURN_PATH = DIR / "return-samples.jsonl"  # info: set RETURN_PATH
DAILY_PATH = DIR / "connectivity-daily.json"  # info: set DAILY_PATH
KEEP, GAP_S = 400, 180  # info: KEEP , GAP_S = 400 , 180
RETURN_GAP_S = 30 * 60  # info: a morning or next-day return, not a short restart
HST = ZoneInfo("Pacific/Honolulu")  # info: set HST


# ====================================================
# SECTION: function _now_iso
# What it does:  now iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _now_iso() -> str:  # info: def _now_iso
    return datetime.now(timezone.utc).isoformat()  # info: return datetime . now ( timezone . utc


# ====================================================
# SECTION: function _boot_uptime_s
# What it does:  boot uptime s.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _boot_uptime_s() -> int:  # info: def _boot_uptime_s
    with open("/proc/uptime") as f:  # info: with open ( "/proc/uptime" ) as f :
        return int(float(f.read().split()[0]))  # info: return int ( float ( f . read


# ====================================================
# SECTION: function _boot_id
# What it does:  boot id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _boot_id() -> str:  # info: def _boot_id
    try:  # info: try :
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()  # info: return Path ( "/proc/sys/kernel/random/boot_id" ) . read_text (
    except OSError:  # info: except OSError :
        return ""  # info: return ""


# ====================================================
# SECTION: function _append
# What it does:  append.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _append(kind: str, **extra) -> None:  # info: def _append
    PATH.parent.mkdir(parents=True, exist_ok=True)  # info: PATH . parent . mkdir ( parents =
    with PATH.open("a", encoding="utf-8") as fh:  # info: with PATH . open ( "a" , encoding
        fh.write(json.dumps({"at": _now_iso(), "kind": kind, **extra}, default=str) + "\n")  # info: fh . write ( json . dumps (
    lines = PATH.read_text(encoding="utf-8", errors="replace").splitlines()  # info: set lines
    if len(lines) > KEEP:  # info: if len ( lines ) > KEEP :
        tmp = PATH.with_name(PATH.name + ".tmp")  # info: set tmp
        tmp.write_text("\n".join(lines[-KEEP:]) + "\n", encoding="utf-8")  # info: tmp . write_text ( "\n" . join (
        os.replace(tmp, PATH)  # info: os . replace ( tmp , PATH )


# ====================================================
# SECTION: function _marker
# What it does:  marker.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _marker() -> dict:  # info: def _marker
    try:  # info: try :
        raw = json.loads(MARKER.read_text(encoding="utf-8"))  # info: set raw
        return raw if isinstance(raw, dict) else {}  # info: return raw if isinstance ( raw , dict
    except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
        return {}  # info: return { }


# ====================================================
# SECTION: function _write_marker
# What it does:  write marker.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_marker(payload: dict) -> None:  # info: def _write_marker
    MARKER.parent.mkdir(parents=True, exist_ok=True)  # info: MARKER . parent . mkdir ( parents =
    tmp = MARKER.with_name(MARKER.name + ".tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, MARKER)  # info: os . replace ( tmp , MARKER )


# ====================================================
# SECTION: function tick
# What it does: Heartbeat: stamp presence; log a gap if the desk was gone long enough.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def tick() -> dict:  # info: def tick
    """Heartbeat: stamp presence; log a gap if the desk was gone long enough."""  # info: """Heartbeat: stamp presence; log a gap if the desk was gone long enough."""
    now, m, bid = time.time(), _marker(), _boot_id()  # info: now , m , bid = time .
    if not m.get("recording_since"):  # info: if not m . get ( "recording_since" )
        m["recording_since"] = _now_iso()  # info: testing stamps before this are not samples
        last = 0  # info: set last
    else:  # info: else
        last = float(m.get("last_tick_epoch") or 0)  # info: set last
    gap = int(now - last) if last else 0  # info: set gap
    rebooted = bool(m.get("boot_id") and bid and bid != m["boot_id"])  # info: set rebooted
    if last and (gap >= GAP_S or rebooted):  # info: if last and ( gap >= GAP_S or rebooted )
        note_offline(last, now)  # info: call note_offline
    if rebooted:  # info: if rebooted
        _append("boot", boot_uptime_s=_boot_uptime_s(), gap_s=gap)  # info: call _append
    if last and gap >= GAP_S:  # info: if last and gap >= GAP_S
        _append("heartbeat_gap", gap_s=gap)  # info: call _append
        _append("desk_up", after_gap_s=gap)  # info: call _append
    m.update(last_tick_at=_now_iso(), last_tick_epoch=now, boot_id=bid)  # info: m . update ( last_tick_at = _now_iso (
    if not m.get("origin_started_at"):  # info: if not m . get ( "origin_started_at" )
        m["origin_started_at"] = _now_iso()  # info: m [ "origin_started_at" ] = _now_iso ( )
        _append("origin_start", inferred=True, boot_uptime_s=_boot_uptime_s())  # info: call _append
    _write_marker(m)  # info: call _write_marker
    _write_presence(now)  # info: call _write_presence
    refresh_daily(now)  # info: call refresh_daily
    return m  # info: return m


# ====================================================
# SECTION: function recent
# What it does: recent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def recent(limit: int = 24) -> list[dict]:  # info: def recent
    try:  # info: try :
        lines = PATH.read_text(encoding="utf-8", errors="replace").splitlines()  # info: set lines
    except OSError:  # info: except OSError :
        return []  # info: return [ ]
    out = []  # info: set out
    for line in lines[-limit:]:  # info: for line in lines [ - limit :
        try:  # info: try :
            row = json.loads(line)  # info: set row
        except ValueError:  # info: except ValueError :
            continue  # info: continue
        if isinstance(row, dict):  # info: if isinstance ( row , dict ) :
            out.append(row)  # info: out . append ( row )
    return out  # info: return out


# ====================================================
# SECTION: function last_return
# What it does: last return.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def last_return() -> dict | None:  # info: def last_return
    return next((r for r in reversed(recent(80)) if r.get("kind") in {"origin_start", "desk_up"}), None)  # info: return next ( ( r for r in


# ====================================================
# SECTION: function facts
# What it does: facts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def facts(*, process_uptime_s: int | None = None) -> dict:  # info: def facts
    m, desk_s = _marker(), None  # info: m , desk_s = _marker ( ) ,
    if m.get("origin_started_at"):  # info: if m . get ( "origin_started_at" ) :
        try:  # info: try :
            desk_s = int((datetime.now(timezone.utc) - datetime.fromisoformat(m["origin_started_at"])).total_seconds())  # info: set desk_s
        except ValueError:  # info: except ValueError :
            desk_s = None  # info: set desk_s
    ret = last_return() or {}  # info: set ret
    return {"process_uptime_s": process_uptime_s, "boot_uptime_s": _boot_uptime_s(),  # info: return { "process_uptime_s" : process_uptime_s , "boot_uptime_s" :
            "desk_uptime_s": desk_s if desk_s is not None else process_uptime_s,  # info: "desk_uptime_s" : desk_s if desk_s is not None
            "origin_started_at": m.get("origin_started_at"), "last_return_at": ret.get("at"),  # info: "origin_started_at" : m . get ( "origin_started_at" )
            "last_return_kind": ret.get("kind"), "recent": recent(12)}  # info: "last_return_kind" : ret . get ( "kind" )


# ====================================================
# SECTION: function _append_sample
# What it does: Append one JSON object to a sample log.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _append_sample(path: Path, row: dict) -> None:  # info: def _append_sample
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir
    with path.open("a", encoding="utf-8") as fh:  # info: with path . open
        fh.write(json.dumps(row, default=str) + "\n")  # info: fh . write


# ====================================================
# SECTION: function _read_samples
# What it does: Read a sample log. Bad lines are skipped.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _read_samples(path: Path) -> list[dict]:  # info: def _read_samples
    try:  # info: try
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()  # info: set lines
    except OSError:  # info: except OSError
        return []  # info: return
    out = []  # info: set out
    for line in lines:  # info: for line in lines
        try:  # info: try
            row = json.loads(line)  # info: set row
        except ValueError:  # info: except ValueError
            continue  # info: continue
        if isinstance(row, dict):  # info: if isinstance
            out.append(row)  # info: out . append
    return out  # info: return out


# ====================================================
# SECTION: function _is_return
# What it does: True when a gap is a morning or next-day boot, not a short restart.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _is_return(down: datetime, up: datetime, offline_s: int) -> bool:  # info: def _is_return
    if offline_s < RETURN_GAP_S:  # info: if offline_s < RETURN_GAP_S
        return False  # info: return False
    if down.astimezone(HST).date() != up.astimezone(HST).date():  # info: if the gap crosses a Hawaii day
        return True  # info: return True
    return up.astimezone(HST).hour < 12  # info: return a same-day morning return


# ====================================================
# SECTION: function note_offline
# What it does: Record one completed offline stretch, and a return time when it is a morning or next-day boot.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def note_offline(down_epoch: float, up_epoch: float) -> dict:  # info: def note_offline
    """Record one completed offline stretch, and a return time when it is a morning or next-day boot."""  # info: docstring
    offline_s = max(0, int(up_epoch - down_epoch))  # info: set offline_s
    down = datetime.fromtimestamp(down_epoch, HST)  # info: set down
    up = datetime.fromtimestamp(up_epoch, HST)  # info: set up
    row = {"down_at": down.isoformat(timespec="seconds"), "up_at": up.isoformat(timespec="seconds"), "offline_s": offline_s}  # info: set row
    _append_sample(OFFLINE_PATH, row)  # info: call _append_sample
    if _is_return(down, up, offline_s):  # info: if _is_return
        minute = up.hour * 60 + up.minute  # info: set minute
        _append_sample(RETURN_PATH, {"at": row["up_at"], "minute_of_day": minute, "offline_s": offline_s})  # info: call _append_sample
        row["return_minute"] = minute  # info: row [ "return_minute" ] = minute
    refresh_daily(up_epoch)  # info: call refresh_daily
    return row  # info: return row


# ====================================================
# SECTION: function _mean_clock
# What it does: Circular mean of minute-of-day values, as hour and minute.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _mean_clock(minutes: list[int]) -> tuple[int, int] | None:  # info: def _mean_clock
    if not minutes:  # info: if not minutes
        return None  # info: return None
    angles = [2 * math.pi * (m % 1440) / 1440 for m in minutes]  # info: set angles
    avg = math.atan2(sum(math.sin(a) for a in angles), sum(math.cos(a) for a in angles))  # info: set avg
    minute = int(round((avg % (2 * math.pi)) / (2 * math.pi) * 1440)) % 1440  # info: set minute
    return minute // 60, minute % 60  # info: return hour , minute


# ====================================================
# SECTION: function refresh_daily
# What it does: Rewrite the daily connectivity summary from samples recorded since recording began.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def refresh_daily(now_epoch: float | None = None) -> dict:  # info: def refresh_daily
    """Rewrite the daily connectivity summary from samples recorded since recording began."""  # info: docstring
    now_epoch = time.time() if now_epoch is None else now_epoch  # info: set now_epoch
    now = datetime.fromtimestamp(now_epoch, HST)  # info: set now
    m = _marker()  # info: set m
    since_raw = m.get("recording_since")  # info: set since_raw
    try:  # info: try
        since = datetime.fromisoformat(since_raw).astimezone(HST) if since_raw else now  # info: set since
    except ValueError:  # info: except ValueError
        since = now  # info: set since
    window = max(1, int((now - since).total_seconds()))  # info: set window
    offline_rows = []  # info: set offline_rows
    for row in _read_samples(OFFLINE_PATH):  # info: for row in _read_samples
        try:  # info: try
            up_at = datetime.fromisoformat(row["up_at"])  # info: set up_at
        except (KeyError, ValueError):  # info: except
            continue  # info: continue
        if up_at >= since:  # info: if up_at >= since
            offline_rows.append(row)  # info: offline_rows . append
    offline_vals = [int(row["offline_s"]) for row in offline_rows if isinstance(row.get("offline_s"), int)]  # info: set offline_vals
    offline_sum = sum(offline_vals)  # info: set offline_sum
    returns = []  # info: set returns
    for row in _read_samples(RETURN_PATH):  # info: for row in _read_samples
        try:  # info: try
            at = datetime.fromisoformat(row["at"])  # info: set at
        except (KeyError, ValueError):  # info: except
            continue  # info: continue
        if at >= since and isinstance(row.get("minute_of_day"), int):  # info: if at >= since
            returns.append(int(row["minute_of_day"]))  # info: returns . append
    clock = _mean_clock(returns)  # info: set clock
    pct = int(round(100 * max(0, window - offline_sum) / window))  # info: set pct
    summary = {  # info: set summary
        "updated_on": now.date().isoformat(),  # info: "updated_on"
        "updated_at": now.isoformat(timespec="seconds"),  # info: "updated_at"
        "recording_since": since.isoformat(timespec="seconds"),  # info: "recording_since"
        "uptime_pct": pct,  # info: "uptime_pct"
        "offline_samples": len(offline_vals),  # info: "offline_samples"
        "avg_offline_s": int(round(sum(offline_vals) / len(offline_vals))) if offline_vals else None,  # info: "avg_offline_s"
        "return_samples": len(returns),  # info: "return_samples"
        "avg_return_hour": clock[0] if clock else None,  # info: "avg_return_hour"
        "avg_return_minute": clock[1] if clock else None,  # info: "avg_return_minute"
    }  # info: }
    DAILY_PATH.parent.mkdir(parents=True, exist_ok=True)  # info: DAILY_PATH . parent . mkdir
    tmp = DAILY_PATH.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, DAILY_PATH)  # info: os . replace
    return summary  # info: return summary


# ====================================================
# SECTION: function _write_presence
# What it does: Stamp the last moment the root server was online.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_presence(now_epoch: float) -> None:  # info: def _write_presence
    now = datetime.fromtimestamp(now_epoch, HST)  # info: set now
    payload = {"last_online_at": now.isoformat(timespec="seconds"), "hour": now.hour, "minute": now.minute}  # info: set payload
    PRESENCE.parent.mkdir(parents=True, exist_ok=True)  # info: PRESENCE . parent . mkdir
    tmp = PRESENCE.with_suffix(".json.tmp")  # info: set tmp
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")  # info: tmp . write_text
    os.replace(tmp, PRESENCE)  # info: os . replace


# ====================================================
# SECTION: function connectivity
# What it does: Last online time plus averages. Averages stay empty until a sample exists.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def connectivity(now: datetime | None = None) -> dict:  # info: def connectivity
    """Last online time plus averages. Averages stay empty until a sample exists."""  # info: docstring
    clock = now.astimezone(HST) if now else datetime.now(HST)  # info: set clock
    try:  # info: try
        presence = json.loads(PRESENCE.read_text(encoding="utf-8"))  # info: set presence
    except (OSError, ValueError):  # info: except
        presence = {}  # info: set presence
    try:  # info: try
        daily = json.loads(DAILY_PATH.read_text(encoding="utf-8"))  # info: set daily
    except (OSError, ValueError):  # info: except
        daily = {}  # info: set daily
    if not isinstance(presence, dict):  # info: if not isinstance
        presence = {}  # info: set presence
    if not isinstance(daily, dict):  # info: if not isinstance
        daily = {}  # info: set daily
    hour = presence.get("hour")  # info: set hour
    minute = presence.get("minute")  # info: set minute
    if not isinstance(hour, int) or not isinstance(minute, int):  # info: if the presence stamp is missing
        hour, minute = clock.hour, clock.minute  # info: the report itself is proof the server is online
    return {  # info: return
        "last_online_at": presence.get("last_online_at") or clock.isoformat(timespec="seconds"),  # info: "last_online_at"
        "last_online_hour": hour,  # info: "last_online_hour"
        "last_online_minute": minute,  # info: "last_online_minute"
        "uptime_pct": daily.get("uptime_pct") if daily.get("recording_since") else None,  # info: "uptime_pct"
        "avg_offline_s": daily.get("avg_offline_s") if daily.get("offline_samples") else None,  # info: "avg_offline_s"
        "avg_return_hour": daily.get("avg_return_hour") if daily.get("return_samples") else None,  # info: "avg_return_hour"
        "avg_return_minute": daily.get("avg_return_minute") if daily.get("return_samples") else None,  # info: "avg_return_minute"
        "recording_since": daily.get("recording_since"),  # info: "recording_since"
    }  # info: }


# ====================================================
# SECTION: function _duration_words
# What it does: Hours and minutes for a spoken offline average.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _duration_words(seconds: int) -> str:  # info: def _duration_words
    hours, minutes = divmod(max(0, int(seconds)) // 60, 60)  # info: hours , minutes = divmod
    parts = []  # info: set parts
    if hours:  # info: if hours
        parts.append(f"{hours} hour" if hours == 1 else f"{hours} hours")  # info: parts . append
    if minutes or not parts:  # info: if minutes or not parts
        parts.append(f"{minutes} minute" if minutes == 1 else f"{minutes} minutes")  # info: parts . append
    return " ".join(parts)  # info: return


# ====================================================
# SECTION: function sentences
# What it does: Spoken connectivity lines. Skip an average that has no sample yet.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sentences(now: datetime | None = None) -> list[str]:  # info: def sentences
    """Spoken connectivity lines. Skip an average that has no sample yet."""  # info: docstring
    voice = Path(__file__).resolve().parents[2] / "Media" / "Voice" / "scripts"  # info: set voice
    if str(voice) not in sys.path:  # info: if str ( voice ) not in sys . path
        sys.path.insert(0, str(voice))  # info: sys . path . insert
    from speakable import spoken_clock  # info: from speakable import spoken_clock
    row = connectivity(now)  # info: set row
    lines = [f"Root server was last online at {spoken_clock(row['last_online_hour'], row['last_online_minute'])}."]  # info: set lines
    if isinstance(row.get("uptime_pct"), int):  # info: if isinstance
        lines.append(f"Uptime {row['uptime_pct']} percent.")  # info: lines . append
    if isinstance(row.get("avg_offline_s"), int):  # info: if isinstance
        lines.append(f"Average offline time {_duration_words(row['avg_offline_s'])}.")  # info: lines . append
    if isinstance(row.get("avg_return_hour"), int) and isinstance(row.get("avg_return_minute"), int):  # info: if a return average exists
        lines.append(f"Average expected return {spoken_clock(row['avg_return_hour'], row['avg_return_minute'])}.")  # info: lines . append
    return lines  # info: return lines


# ====================================================
# SECTION: block if
# What it does: __name__ == '__main__'
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
if __name__ == "__main__":  # info: if __name__ == "__main__" :
    cmd = sys.argv[1] if len(sys.argv) > 1 else "tick"  # info: set cmd
    if cmd == "tick":  # info: if cmd == "tick" :
        tick()  # info: call tick
        print(json.dumps({"ok": True, "facts": {k: v for k, v in facts().items() if k != "recent"}}))  # info: call print
    elif cmd == "recent":  # info: elif cmd == "recent" :
        print(json.dumps(recent(), indent=2))  # info: call print
    else:  # info: else :
        print(json.dumps(facts(), indent=2))  # info: call print
