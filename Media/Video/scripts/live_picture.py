# ==============================================================================
# FILE: Media/Video/scripts/live_picture.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Full-bleed still plus the live-desk numbers, then the mainland thumb.

  python3 live_picture.py

The background is the cover-cropped photo. The overlay is the same desk the
/live page draws: clock, River, Delta, network, volcano, moon, and quake
change. One PNG is written and copied to the encoder still. No motion video.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import subprocess  # info: import subprocess
import sys  # info: import sys
import time  # info: import time
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from pathlib import Path  # info: from pathlib import Path
from urllib.request import Request, urlopen  # info: from urllib . request import Request , urlopen
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont  # info: from PIL import Image , ImageDraw , ImageFont

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
HERE = Path(__file__).resolve()  # info: set HERE
PACIFIC = HERE.parents[3]  # info: set PACIFIC
BG = PACIFIC / "Website" / "Home" / "assets" / "broadcast-bg.jpg"  # info: set BG
SOURCE = Path("/home/rootrecord/Downloads/IbxbN.jpg")  # info: set SOURCE
OUT = PACIFIC / "Media" / "Video" / "live-frame.png"  # info: set OUT
ENERGY = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy")  # info: set ENERGY
LATENCY = PACIFIC / "Media" / "Video" / "live-picture-latency.json"  # info: set LATENCY
ENCODER_WAIT = 1.0  # info: encoder checks the thumb once a second
API = "https://api.rootrecord.cloud"  # info: set API
USGS = "https://earthquake.usgs.gov/fdsnws/event/1/query"  # info: set USGS
HOST = os.environ.get("RR_RADIO_SSH", "ml1")  # info: set HOST
REMOTE = os.environ.get("RR_YT_THUMB", "/home/ubuntu/youtube-stills/thumb.png")  # info: set REMOTE
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # info: set FONT
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # info: set FONT_B


# ====================================================
# SECTION: function _font
# What it does: Load a DejaVu face at the requested size.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:  # info: def _font
    path = FONT_B if bold else FONT  # info: set path
    return ImageFont.truetype(path, size)  # info: return ImageFont . truetype


# ====================================================
# SECTION: function _get
# What it does: GET JSON, or None when the host does not answer.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _get(url: str, timeout: float = 20) -> dict | None:  # info: def _get
    try:  # info: try
        req = Request(url, headers={"User-Agent": "RootRecord-LivePicture/1.0", "Accept": "application/json"})  # info: set req
        with urlopen(req, timeout=timeout) as resp:  # info: with urlopen
            data = json.loads(resp.read().decode("utf-8"))  # info: set data
        return data if isinstance(data, dict) else None  # info: return dict or none
    except (OSError, ValueError):  # info: except
        return None  # info: return None


# ====================================================
# SECTION: function _cover
# What it does: Center-crop the source photo to 1920 by 1080.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cover() -> None:  # info: def _cover
    if not SOURCE.is_file():  # info: if the download is gone
        return  # info: return
    BG.parent.mkdir(parents=True, exist_ok=True)  # info: BG . parent . mkdir
    subprocess.run(  # info: subprocess . run
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(SOURCE),  # info: ffmpeg cover scale
         "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080", str(BG)],  # info: crop command
        check=False,  # info: check False
    )  # info: )


# ====================================================
# SECTION: function _pct
# What it does: Percent change, or new when the earlier window was empty.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pct(cur: int, prev: int):  # info: def _pct
    if prev <= 0:  # info: if prev <= 0
        return "new" if cur else 0  # info: return new or zero
    return int(round((cur - prev) * 100 / prev))  # info: return int percent


# ====================================================
# SECTION: function _quake_change
# What it does: Magnitude 2.5 counts for the last day and week against the windows before them.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _quake_change(events: list) -> dict:  # info: def _quake_change
    now = datetime.now(timezone.utc)  # info: set now

    def between(lo: float, hi: float) -> int:  # info: def between
        total = 0  # info: set total
        for event in events:  # info: for event
            props = (event.get("properties") or {}) if "properties" in event else event  # info: set props
            try:  # info: try
                mag = float(props.get("mag"))  # info: set mag
            except (TypeError, ValueError):  # info: except
                continue  # info: continue
            raw = props.get("time")  # info: set raw
            if isinstance(raw, (int, float)):  # info: if epoch ms
                when = datetime.fromtimestamp(raw / 1000.0, timezone.utc)  # info: set when
            else:  # info: else
                try:  # info: try
                    when = datetime.fromisoformat(str(event.get("time_utc") or ""))  # info: set when
                except ValueError:  # info: except
                    continue  # info: continue
                if when.tzinfo is None:  # info: if naive
                    when = when.replace(tzinfo=timezone.utc)  # info: set when
            age = (now - when).total_seconds() / 3600.0  # info: set age
            if mag >= 2.5 and lo <= age < hi:  # info: if in window
                total += 1  # info: total += 1
        return total  # info: return total

    day, day_prev = between(0, 24), between(24, 48)  # info: day counts
    week, week_prev = between(0, 168), between(168, 336)  # info: week counts
    return {"day": day, "day_pct": _pct(day, day_prev), "week": week, "week_pct": _pct(week, week_prev)}  # info: return


# ====================================================
# SECTION: function _say_pct
# What it does: One short change phrase.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _say_pct(value) -> str:  # info: def _say_pct
    if value == "new":  # info: if value == new
        return "new"  # info: return new
    if not isinstance(value, int):  # info: if not an int
        return "n/a"  # info: return n/a
    if value > 0:  # info: if value > 0
        return f"+{value}%"  # info: return plus
    return f"{value}%"  # info: return signed


# ====================================================
# SECTION: function _card
# What it does: Draw one translucent desk card.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:  # info: def _card
    draw.rounded_rectangle(box, radius=18, fill=(2, 10, 18, 230), outline=(0, 229, 255, 190), width=3)  # info: draw card


# ====================================================
# SECTION: function _text
# What it does: Draw one line of desk text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill: tuple, bold: bool = False) -> None:  # info: def _text
    draw.text(xy, text, font=_font(size, bold), fill=fill)  # info: draw . text


# ====================================================
# SECTION: function _center
# What it does: Draw one line centered on a point.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _center(draw: ImageDraw.ImageDraw, cx: int, cy: int, text: str, size: int, fill: tuple, bold: bool = False) -> None:  # info: def _center
    font = _font(size, bold)  # info: set font
    box = draw.textbbox((0, 0), text, font=font)  # info: set box
    draw.text((cx - (box[2] - box[0]) / 2, cy - (box[3] - box[1]) / 2), text, font=font, fill=fill)  # info: draw centered


# ====================================================
# SECTION: function _pair
# What it does: Draw a label on the left and a value on the right of one row.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _pair(draw: ImageDraw.ImageDraw, left: int, right: int, y: int, name: str, value: str, size: int = 30) -> None:  # info: def _pair
    _text(draw, (left, y), name, size, (190, 225, 238, 255))  # info: name
    font = _font(size, True)  # info: set font
    box = draw.textbbox((0, 0), value, font=font)  # info: set box
    draw.text((right - (box[2] - box[0]), y), value, font=font, fill=(236, 246, 255, 255))  # info: value


# ====================================================
# SECTION: function _gauge
# What it does: Draw a charge ring and its percent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _gauge(draw: ImageDraw.ImageDraw, cx: int, cy: int, pct: float | None, label: str) -> None:  # info: def _gauge
    radius = 78  # info: set radius
    box = (cx - radius, cy - radius, cx + radius, cy + radius)  # info: set box
    draw.arc(box, 0, 360, fill=(255, 255, 255, 55), width=16)  # info: draw track
    if pct is not None:  # info: if pct is not None
        sweep = max(0.0, min(100.0, pct)) * 3.6  # info: set sweep
        draw.arc(box, -90, -90 + sweep, fill=(0, 229, 255, 255), width=16)  # info: draw sweep
        _center(draw, cx, cy - 4, f"{round(pct)}%", 40, (236, 246, 255, 255), True)  # info: percent
    else:  # info: else
        _center(draw, cx, cy - 4, "—", 40, (236, 246, 255, 255), True)  # info: missing
    _center(draw, cx, cy + radius + 32, label, 28, (190, 225, 238, 255), True)  # info: label


# ====================================================
# SECTION: function _ble_pack
# What it does: Charge and watts from the newest BLE sample. A cloud last file is ignored.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ble_pack(alias: str) -> dict:  # info: def _ble_pack
    best_at = ""  # info: set best_at
    fields: dict = {}  # info: set fields
    current = ENERGY / "samples" / f"read-{alias}_current.json"  # info: stable *_current bank
    samples = [current] if current.is_file() else sorted((ENERGY / "samples").glob(f"read-{alias}*.json"))  # info: prefer current
    for path in reversed(samples[-80:]):  # info: for path
        try:  # info: try
            row = json.loads(path.read_text(encoding="utf-8"))  # info: set row
        except (OSError, ValueError):  # info: except
            continue  # info: continue
        if not str(row.get("source") or "").startswith("ble"):  # info: if the sample is not BLE
            continue  # info: continue
        got = row.get("fields") or {}  # info: set got
        nums = [got.get(key) for key in ("soc", "solar_input_power", "ac_output_power", "usbc_output_power")]  # info: set nums
        if all(value in (None, 0, 0.0) for value in nums):  # info: if the sample is an empty miss
            continue  # info: continue
        fields = got  # info: set fields
        best_at = str(row.get("at") or "")  # info: set best_at
        break  # info: break
    for kind, path in (("soc", ENERGY / "soc" / f"{alias}_current.json"), ("watts", ENERGY / "watts" / f"{alias}_current.json")):  # info: for kind , path
        try:  # info: try
            row = json.loads(path.read_text(encoding="utf-8"))  # info: set row
        except (OSError, ValueError):  # info: except
            continue  # info: continue
        if not str(row.get("source") or "").startswith("ble"):  # info: if the last file is not BLE
            continue  # info: continue
        stamp = str(row.get("at") or "")  # info: set stamp
        if stamp < best_at:  # info: if an older file
            continue  # info: continue
        if kind == "soc" and row.get("soc") is not None:  # info: if a newer charge
            fields["soc"] = row.get("soc")  # info: set soc
        if kind == "watts":  # info: if newer watts
            for key in ("solar_input_power", "ac_output_power", "usbc_output_power"):  # info: for key
                if row.get(key) is not None:  # info: if the watt is present
                    fields[key] = row.get(key)  # info: set watt
    return {"soc": {"soc": fields.get("soc")}, "watts": fields}  # info: return pack


# ====================================================
# SECTION: function _soc
# What it does: State of charge from one operations device, or None.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _soc(device: dict | None) -> float | None:  # info: def _soc
    try:  # info: try
        return float((device or {}).get("soc", {}).get("soc"))  # info: return float
    except (TypeError, ValueError):  # info: except
        return None  # info: return None


# ====================================================
# SECTION: function _watts
# What it does: One watt field as a short label.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _watts(device: dict | None, key: str) -> str:  # info: def _watts
    try:  # info: try
        return f"{round(float((device or {}).get('watts', {}).get(key)))} W"  # info: return watts
    except (TypeError, ValueError):  # info: except
        return "—"  # info: return dash


# ====================================================
# SECTION: function _tail
# What it does: Last measured seconds from the clock stamp until the encoder can show the still.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _tail() -> float:  # info: def _tail
    try:  # info: try
        saved = json.loads(LATENCY.read_text(encoding="utf-8"))  # info: set saved
        return max(0.0, min(30.0, float(saved.get("tail_sec", ENCODER_WAIT))))  # info: return saved tail
    except (OSError, ValueError, TypeError):  # info: except
        return ENCODER_WAIT  # info: return the encoder wait


# ====================================================
# SECTION: function _remember_tail
# What it does: Store this run's publish delay plus the encoder wait for the next clock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _remember_tail(drawn_at: datetime) -> None:  # info: def _remember_tail
    spent = (datetime.now(HST) - drawn_at).total_seconds() + ENCODER_WAIT  # info: set spent
    LATENCY.write_text(json.dumps({"tail_sec": round(max(0.0, spent), 2)}), encoding="utf-8")  # info: write tail


# ====================================================
# SECTION: function clock_line
# What it does: Hawaii minute plus the last measured delay, with no seconds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clock_line(when: datetime) -> str:  # info: def clock_line
    shown = when + timedelta(seconds=_tail())  # info: add the last publish delay
    return shown.strftime("%I:%M %p").lstrip("0")  # info: minute only


# ====================================================
# SECTION: function push_clock
# What it does: Write clock.txt on the encoder. Does not touch the still.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def push_clock(when: datetime) -> int:  # info: def push_clock
    sent = subprocess.run(  # info: subprocess . run
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", HOST, "cat > /home/ubuntu/youtube-stills/clock.txt"],  # info: ssh the clock only
        input=clock_line(when) + "\n", capture_output=True, text=True,  # info: write the minute
    )  # info: )
    return sent.returncode  # info: return sent . returncode


# ====================================================
# SECTION: function clock_loop
# What it does: Write the clock at each new Hawaii minute, even while another job holds the poller.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def clock_loop() -> int:  # info: def clock_loop
    while True:  # info: while True
        now = datetime.now(HST)  # info: set now
        if push_clock(now) != 0:  # info: if the clock was not written
            print(json.dumps({"ok": False, "detail": "clock-ssh"}), flush=True)  # info: print the miss
        else:  # info: else
            print(json.dumps({"ok": True, "clock": clock_line(now)}), flush=True)  # info: print the minute
        nxt = now.replace(second=0, microsecond=0) + timedelta(minutes=1)  # info: the next minute
        time.sleep(max(0.2, (nxt - datetime.now(HST)).total_seconds()))  # info: sleep until that minute opens


# ====================================================
# SECTION: function render
# What it does: Composite the desk overlay on the full-bleed photo.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render(state: dict | None, ops: dict | None, hawaii: dict, world: dict, when: datetime) -> Image.Image:  # info: def render
    base = Image.open(BG).convert("RGBA")  # info: set base
    if base.size != (1920, 1080):  # info: if base . size !=
        base = base.resize((1920, 1080))  # info: resize
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))  # info: set layer
    draw = ImageDraw.Draw(layer)  # info: set draw
    now = when  # info: set now
    river, delta = _ble_pack("river2pro"), _ble_pack("delta2")  # info: BLE files, not the cloud snapshot
    _card(draw, (20, 16, 636, 322))  # info: clock card above the title
    _text(draw, (48, 32), "ON AIR", 26, (255, 90, 90, 255), True)  # info: on air
    _center(draw, 328, 230, now.strftime("%d %b %Y") + "  HST", 32, (190, 225, 238, 255))  # info: date
    _card(draw, (652, 16, 1268, 322))  # info: battery card above the title
    _text(draw, (680, 32), "BATTERY BANK", 26, (0, 229, 255, 255), True)  # info: battery title
    _gauge(draw, 820, 168, _soc(river), "River")  # info: river gauge
    _gauge(draw, 1100, 168, _soc(delta), "Delta")  # info: delta gauge
    _card(draw, (1284, 16, 1900, 322))  # info: watts card above the title
    _text(draw, (1312, 32), "TOTALS NOW", 26, (0, 229, 255, 255), True)  # info: totals title
    rows = [  # info: set rows
        ("River solar", _watts(river, "solar_input_power")),  # info: river solar
        ("Delta solar", _watts(delta, "solar_input_power")),  # info: delta solar
        ("River AC out", _watts(river, "ac_output_power")),  # info: river ac
        ("Delta AC out", _watts(delta, "ac_output_power")),  # info: delta ac
        ("River USB-C", _watts(river, "usbc_output_power")),  # info: river usb
        ("Delta USB-C", _watts(delta, "usbc_output_power")),  # info: delta usb
    ]  # info: ]
    y = 78  # info: set y
    for name, value in rows:  # info: for name , value
        _pair(draw, 1312, 1872, y, name, value, 28)  # info: watt row
        y += 38  # info: y += 38
    stats = (state or {}).get("stats") or {}  # info: set stats
    _card(draw, (20, 840, 636, 1064))  # info: network card below the title
    _text(draw, (48, 860), "LIVE NETWORK", 26, (0, 229, 255, 255), True)  # info: network title
    _pair(draw, 48, 608, 924, "Active flows", str(stats.get("activeFlows", "—")), 36)  # info: flows
    _pair(draw, 48, 608, 988, "Endpoints", str(stats.get("endpoints", "—")), 36)  # info: endpoints
    volcano = ((ops or {}).get("kilauea") or {}).get("status") or {}  # info: set volcano
    moon = ((ops or {}).get("moon") or {}).get("status") or {}  # info: set moon
    erupt = volcano.get("erupting")  # info: set erupt
    _card(draw, (652, 840, 1268, 1064))  # info: geology card below the title
    _text(draw, (680, 856), "SITE AND MOON", 26, (0, 229, 255, 255), True)  # info: geology title
    _pair(draw, 680, 1240, 902, "Kilauea", str(volcano.get("alert_level") or "—"), 28)  # info: alert
    _pair(draw, 680, 1240, 942, "Color", str(volcano.get("color_code") or "—"), 28)  # info: color
    _pair(draw, 680, 1240, 982, "Eruption", "yes" if erupt else "no" if erupt is False else "—", 28)  # info: eruption
    _pair(draw, 680, 1240, 1022, str(moon.get("phase_name") or "Moon"), f"{moon.get('illumination', '—')}% lit", 26)  # info: moon
    _card(draw, (1284, 840, 1900, 1064))  # info: quake card below the title
    _text(draw, (1312, 856), "EARTHQUAKES  M2.5+", 26, (0, 229, 255, 255), True)  # info: quake title
    _pair(draw, 1312, 1872, 902, "Hawaii 24h", f"{hawaii.get('day', '—')}   {_say_pct(hawaii.get('day_pct'))}", 28)  # info: hi day
    _pair(draw, 1312, 1872, 942, "Hawaii 7d", f"{hawaii.get('week', '—')}   {_say_pct(hawaii.get('week_pct'))}", 28)  # info: hi week
    _pair(draw, 1312, 1872, 982, "World 24h", f"{world.get('day', '—')}   {_say_pct(world.get('day_pct'))}", 28)  # info: world day
    _pair(draw, 1312, 1872, 1022, "World 7d", f"{world.get('week', '—')}   {_say_pct(world.get('week_pct'))}", 28)  # info: world week
    frame = Image.alpha_composite(base, layer).convert("RGB")  # info: set frame
    return frame  # info: return frame


# ====================================================
# SECTION: function publish
# What it does: Write the local still and the encoder clock. Does not replace the live picture.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def publish(frame: Image.Image, when: datetime) -> str:  # info: def publish
    OUT.parent.mkdir(parents=True, exist_ok=True)  # info: OUT . parent . mkdir
    frame.save(OUT, "PNG")  # info: frame . save
    if push_clock(when) != 0:  # info: if the clock was not written
        return "local-only"  # info: return local-only
    return "clock"  # info: return clock


# ====================================================
# SECTION: function main
# What it does: Build one still and publish it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    if len(sys.argv) > 1 and sys.argv[1] == "clock":  # info: clock-only mode leaves the encoder alone
        return clock_loop()  # info: return clock_loop
    _cover()  # info: call _cover
    if not BG.is_file():  # info: if not BG . is_file
        print(json.dumps({"ok": False, "detail": "background missing"}))  # info: print missing
        return 1  # info: return 1
    start = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S")  # info: set start
    hi_url = USGS + f"?format=geojson&minmagnitude=2.5&minlatitude=18.5&maxlatitude=22.5&minlongitude=-160.5&maxlongitude=-154.5&starttime={start}"  # info: set hi_url
    gl_url = USGS + f"?format=geojson&minmagnitude=2.5&starttime={start}"  # info: set gl_url
    state = _get(API + "/api/state")  # info: set state
    ops = _get(API + "/api/operations") or {}  # info: set ops
    moon_path = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Weather/moon/moon_current.json")  # info: set moon_path
    if not moon_path.is_file():  # info: drain legacy Energy path
        moon_path = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/moon/moon-last.json")  # info: legacy
    try:  # info: try
        saved = json.loads(moon_path.read_text(encoding="utf-8"))  # info: set saved
        if isinstance(saved, dict) and saved.get("phase_name"):  # info: if a saved moon name is on file
            ops.setdefault("moon", {})["status"] = saved  # info: use the saved moon
    except (OSError, ValueError):  # info: except
        pass  # info: pass
    hi = _quake_change((_get(hi_url) or {}).get("features") or [])  # info: set hi
    world = _quake_change((_get(gl_url, 40) or {}).get("features") or [])  # info: set world
    shown = datetime.now(HST)  # info: the clock is the current Hawaii minute
    frame = render(state, ops, hi, world, shown)  # info: set frame
    detail = publish(frame, shown)  # info: set detail
    if datetime.now(HST).minute in (0, 30):  # info: if the half-hour window just opened
        meta = subprocess.run(  # info: subprocess . run
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", HOST,  # info: ssh metadata
             "python3 /home/ubuntu/youtube-stills/youtube_stills.py"],  # info: metadata only
            capture_output=True, text=True,  # info: capture
        )  # info: )
        detail = detail + (" metadata" if meta.returncode == 0 else " metadata-failed")  # info: set detail
    print(json.dumps({"ok": True, "detail": detail, "path": str(OUT), "size": list(frame.size)}))  # info: print result
    return 0  # info: return 0


if __name__ == "__main__":  # info: if __name__ == __main__
    raise SystemExit(main())  # info: raise SystemExit
