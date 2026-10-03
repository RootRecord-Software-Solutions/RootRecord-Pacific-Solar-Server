# ==============================================================================
# FILE: Apps/Control-Panel/rr_radio_lineup.py
# What this file is: order of the next ML1 half-hour, same rules as the live mixer.
# Kind: python
# ==============================================================================
"""Next ML1 cycle order. Locals longest-first, then news. No station control."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Pacific/Honolulu")
DAYPARTS = ("morning_report", "midday_report", "late_report")
SLOT_SEC = 30 * 60
TITLES = {
    "nws_weather": "NWS Hawaiʻi",
    "hurricane_desk": "Hurricane",
    "kilauea_report": "Kīlauea",
    "kilauea_image_check": "Kīlauea image",
    "earthquake_report": "Earthquake",
    "energy_report": "Energy",
    "solar_desk": "Solar",
    "bandwidth_desk": "Bandwidth",
    "security_desk": "Security",
    "system_perf": "Systems",
    "morning_report": "Morning",
    "midday_report": "Midday",
    "late_report": "Late",
    "remaining_tasks": "Tasks",
    "boot_brief": "Boot",
    "current_report": "Current",
    "custom_msg": "Custom message",
    "news_update": "News",
}


def report_id(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    if stem.endswith("_current"):
        stem = stem[: -len("_current")]
    return stem


def daypart(hour: int, minute: int) -> str:
    minute_of_day = hour * 60 + minute
    if 9 * 60 <= minute_of_day < 12 * 60:
        return "morning_report"
    if 12 * 60 <= minute_of_day < 21 * 60:
        return "midday_report"
    return "late_report"


def next_boundary(now: datetime) -> datetime:
    local = now.astimezone(TZ).replace(second=0, microsecond=0)
    if local.minute < 30:
        return local.replace(minute=30)
    return (local.replace(minute=0) + __import__("datetime").timedelta(hours=1))


def order_rows(rows: list[dict], when: datetime) -> tuple[list[dict], list[dict]]:
    """Return (lineup, held). lineup is what the next boundary will queue."""
    slot = next_boundary(when)
    keep = daypart(slot.hour, slot.minute)
    local, news, held = [], [], []
    for row in rows:
        item = dict(row)
        item["id"] = report_id(str(row.get("file") or ""))
        item["title"] = TITLES.get(item["id"], item["id"].replace("_", " "))
        if item["id"] in DAYPARTS and item["id"] != keep:
            held.append(item)
        elif item["id"] == "news_update":
            news.append(item)
        else:
            local.append(item)

    def key(row):
        dur = float(row.get("duration") or 0)
        return (-dur, -int(row.get("bytes") or 0), row["id"])

    local.sort(key=key)
    news.sort(key=key)
    lineup = local + news
    spent = 0.0
    for item in lineup:
        dur = float(item.get("duration") or 0)
        item["starts_sec"] = round(spent, 1)
        spent += dur
        item["cut"] = spent > SLOT_SEC and item["id"] == "news_update"
        if item["id"] != "news_update" and spent > SLOT_SEC:
            item["cut"] = True
    return lineup, held
