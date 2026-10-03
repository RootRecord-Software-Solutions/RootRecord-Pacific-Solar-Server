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
    draw.rounded_rectangle(box, radius=16, fill=(4, 14, 22, 200), outline=(0, 229, 255, 160), width=2)  # info: draw card


# ====================================================
# SECTION: function _text
# What it does: Draw one line of desk text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill: tuple, bold: bool = False) -> None:  # info: def _text
    draw.text(xy, text, font=_font(size, bold), fill=fill)  # info: draw . text


# ====================================================
# SECTION: function _gauge
# What it does: Draw a charge ring and its percent.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _gauge(draw: ImageDraw.ImageDraw, cx: int, cy: int, pct: float | None, label: str) -> None:  # info: def _gauge
    box = (cx - 54, cy - 54, cx + 54, cy + 54)  # info: set box
    draw.arc(box, 0, 360, fill=(255, 255, 255, 40), width=10)  # info: draw track
    if pct is not None:  # info: if pct is not None
        sweep = max(0.0, min(100.0, pct)) * 3.6  # info: set sweep
        draw.arc(box, -90, -90 + sweep, fill=(0, 229, 255, 255), width=10)  # info: draw sweep
        _text(draw, (cx - 28, cy - 16), f"{round(pct)}%", 22, (232, 244, 255, 255), True)  # info: percent
    else:  # info: else
        _text(draw, (cx - 12, cy - 14), "—", 22, (232, 244, 255, 255), True)  # info: missing
    _text(draw, (cx - 28, cy + 62), label, 16, (180, 220, 235, 255))  # info: label


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
# SECTION: function render
# What it does: Composite the desk overlay on the full-bleed photo.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render(state: dict | None, ops: dict | None, hawaii: dict, world: dict) -> Image.Image:  # info: def render
    base = Image.open(BG).convert("RGBA")  # info: set base
    if base.size != (1920, 1080):  # info: if base . size !=
        base = base.resize((1920, 1080))  # info: resize
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))  # info: set layer
    draw = ImageDraw.Draw(layer)  # info: set draw
    _card(draw, (28, 24, 1892, 118))  # info: top card
    now = datetime.now(HST)  # info: set now
    _text(draw, (52, 40), "ROOT RECORD", 28, (0, 229, 255, 255), True)  # info: brand
    _text(draw, (280, 48), "live desk", 18, (232, 244, 255, 255))  # info: desk label
    _text(draw, (860, 42), "ON AIR", 14, (255, 80, 80, 255), True)  # info: on air
    _text(draw, (960, 38), "Radio", 22, (232, 244, 255, 255), True)  # info: program
    _text(draw, (1500, 34), now.strftime("%d %b %Y"), 16, (180, 220, 235, 255))  # info: date
    _text(draw, (1500, 58), now.strftime("%I:%M %p HST").lstrip("0"), 26, (232, 244, 255, 255), True)  # info: clock
    devices = ((ops or {}).get("power") or {}).get("devices") or {}  # info: set devices
    river, delta = devices.get("river2pro") or {}, devices.get("delta2") or {}  # info: river , delta
    _card(draw, (28, 140, 560, 430))  # info: battery card
    _text(draw, (48, 156), "BATTERY BANK", 14, (0, 229, 255, 255), True)  # info: battery title
    _gauge(draw, 170, 270, _soc(river), "River")  # info: river gauge
    _gauge(draw, 400, 270, _soc(delta), "Delta")  # info: delta gauge
    _card(draw, (28, 448, 560, 760))  # info: watts card
    _text(draw, (48, 464), "TOTALS NOW", 14, (0, 229, 255, 255), True)  # info: totals title
    rows = [  # info: set rows
        ("River solar", _watts(river, "solar_input_power")),  # info: river solar
        ("Delta solar", _watts(delta, "solar_input_power")),  # info: delta solar
        ("River AC out", _watts(river, "ac_output_power")),  # info: river ac
        ("Delta AC out", _watts(delta, "ac_output_power")),  # info: delta ac
        ("River USB-C", _watts(river, "usbc_output_power")),  # info: river usb
        ("Delta USB-C", _watts(delta, "usbc_output_power")),  # info: delta usb
    ]  # info: ]
    y = 500  # info: set y
    for name, value in rows:  # info: for name , value
        _text(draw, (48, y), name, 18, (180, 220, 235, 255))  # info: name
        _text(draw, (340, y), value, 18, (232, 244, 255, 255), True)  # info: value
        y += 40  # info: y += 40
    stats = (state or {}).get("stats") or {}  # info: set stats
    _card(draw, (1360, 140, 1892, 340))  # info: network card
    _text(draw, (1380, 156), "LIVE NETWORK", 14, (0, 229, 255, 255), True)  # info: network title
    _text(draw, (1380, 200), f"Active flows  {stats.get('activeFlows', '—')}", 22, (232, 244, 255, 255))  # info: flows
    _text(draw, (1380, 244), f"Endpoints  {stats.get('endpoints', '—')}", 22, (232, 244, 255, 255))  # info: endpoints
    volcano = ((ops or {}).get("kilauea") or {}).get("status") or {}  # info: set volcano
    moon = ((ops or {}).get("moon") or {}).get("status") or {}  # info: set moon
    _card(draw, (1360, 358, 1892, 620))  # info: geology card
    _text(draw, (1380, 374), "SITE AND MOON", 14, (0, 229, 255, 255), True)  # info: geology title
    _text(draw, (1380, 416), f"Kilauea  {volcano.get('alert_level') or '—'}", 20, (232, 244, 255, 255))  # info: alert
    _text(draw, (1380, 452), f"Color  {volcano.get('color_code') or '—'}", 20, (232, 244, 255, 255))  # info: color
    erupt = volcano.get("erupting")  # info: set erupt
    _text(draw, (1380, 488), f"Eruption  {'yes' if erupt else 'no' if erupt is False else '—'}", 20, (232, 244, 255, 255))  # info: eruption
    _text(draw, (1380, 536), f"{moon.get('phase_name') or 'Moon'}  {moon.get('illumination', '—')}% lit", 20, (232, 244, 255, 255))  # info: moon
    _card(draw, (1360, 638, 1892, 900))  # info: quake card
    _text(draw, (1380, 654), "EARTHQUAKES  M2.5", 14, (0, 229, 255, 255), True)  # info: quake title
    _text(draw, (1380, 700), f"Hawaii 24h  {hawaii.get('day', '—')}  {_say_pct(hawaii.get('day_pct'))}", 20, (232, 244, 255, 255))  # info: hi day
    _text(draw, (1380, 740), f"Hawaii 7d  {hawaii.get('week', '—')}  {_say_pct(hawaii.get('week_pct'))}", 20, (232, 244, 255, 255))  # info: hi week
    _text(draw, (1380, 792), f"World 24h  {world.get('day', '—')}  {_say_pct(world.get('day_pct'))}", 20, (232, 244, 255, 255))  # info: world day
    _text(draw, (1380, 832), f"World 7d  {world.get('week', '—')}  {_say_pct(world.get('week_pct'))}", 20, (232, 244, 255, 255))  # info: world week
    frame = Image.alpha_composite(base, layer).convert("RGB")  # info: set frame
    return frame  # info: return frame


# ====================================================
# SECTION: function publish
# What it does: Write the still and copy it onto the encoder thumb.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def publish(frame: Image.Image) -> str:  # info: def publish
    OUT.parent.mkdir(parents=True, exist_ok=True)  # info: OUT . parent . mkdir
    frame.save(OUT, "PNG")  # info: frame . save
    copy = subprocess.run(  # info: subprocess . run
        ["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", str(OUT), f"{HOST}:{REMOTE}"],  # info: scp thumb
        capture_output=True, text=True,  # info: capture
    )  # info: )
    if copy.returncode != 0:  # info: if copy failed
        return "local-only"  # info: return local-only
    return "published"  # info: return published


# ====================================================
# SECTION: function main
# What it does: Build one still and publish it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    _cover()  # info: call _cover
    if not BG.is_file():  # info: if not BG . is_file
        print(json.dumps({"ok": False, "detail": "background missing"}))  # info: print missing
        return 1  # info: return 1
    start = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S")  # info: set start
    hi_url = USGS + f"?format=geojson&minmagnitude=2.5&minlatitude=18.5&maxlatitude=22.5&minlongitude=-160.5&maxlongitude=-154.5&starttime={start}"  # info: set hi_url
    gl_url = USGS + f"?format=geojson&minmagnitude=2.5&starttime={start}"  # info: set gl_url
    state = _get(API + "/api/state")  # info: set state
    ops = _get(API + "/api/operations") or {}  # info: set ops
    moon_path = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database/Energy/moon/moon-last.json")  # info: set moon_path
    try:  # info: try
        saved = json.loads(moon_path.read_text(encoding="utf-8"))  # info: set saved
        if isinstance(saved, dict) and saved.get("phase_name"):  # info: if a saved moon name is on file
            ops.setdefault("moon", {})["status"] = saved  # info: use the saved moon
    except (OSError, ValueError):  # info: except
        pass  # info: pass
    hi = _quake_change((_get(hi_url) or {}).get("features") or [])  # info: set hi
    world = _quake_change((_get(gl_url, 40) or {}).get("features") or [])  # info: set world
    frame = render(state, ops, hi, world)  # info: set frame
    detail = publish(frame)  # info: set detail
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
