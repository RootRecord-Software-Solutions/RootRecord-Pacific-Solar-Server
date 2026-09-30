#!/usr/bin/env python3
"""Carly per-quake Telegram notices from hawaii-last.json.

Reads the existing Geology file. Does not fetch USGS. Dry-run by default:
no Telegram, no Kokoro, no token load. The live job seeds once and posts nothing
on that first pass. A fixture run with an empty seen list prints the notice.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
PACIFIC = ROOT.parents[1]
DB = Path("/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database")
HAWAII = DB / "Geology" / "Earthquakes" / "hawaii-last.json"
DATA = DB / "Communications" / "CouncilQuake"
LOG_DIR = DB / "Logs" / "Communications" / "CouncilQuake"
SEEN_NAME = "seen.json"
LAST_NAME = "last.json"
LOG_NAME = "quake-posts.jsonl"
MIN_MAG = 2.0
MAX_POSTS = 4
RELAY_CONF = PACIFIC / "Communications" / "telegram" / "config" / "relay.conf"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def send_enabled() -> bool:
    return os.environ.get("RR_COUNCIL_QUAKE_SEND", "0").strip() == "1"


def wav_enabled() -> bool:
    return os.environ.get("RR_COUNCIL_QUAKE_WAV", "0").strip() == "1"


def _mag(event: dict) -> float | None:
    try:
        return float(event.get("mag"))
    except (TypeError, ValueError):
        return None


def _fmt_time(event: dict) -> str:
    raw = str(event.get("time_hst") or "").strip()
    if not raw:
        return "time unknown"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return "time unknown"
    hour = dt.strftime("%I").lstrip("0") or "12"
    return f"{dt.strftime('%b')} {dt.day}, {hour}:{dt.strftime('%M')} {dt.strftime('%p')} HST"


def format_quake(event: dict) -> str:
    mag = _mag(event)
    mag_s = f"{mag:.1f}" if mag is not None else "—"
    place = str(event.get("place") or "location unknown").strip()
    lines = [
        "Earthquake — USGS (Hawaii region)",
        f"M {mag_s} · {place}",
        _fmt_time(event),
    ]
    try:
        lines.append(f"Depth {float(event.get('depth_km')):g} km")
    except (TypeError, ValueError):
        pass
    url = str(event.get("url") or "").strip()
    qid = str(event.get("id") or "").strip()
    if not url and qid:
        url = f"https://earthquake.usgs.gov/earthquakes/eventpage/{qid}"
    if url:
        lines.append(url)
    return "\n".join(lines)


def spoken_quake(event: dict) -> str:
    mag = _mag(event)
    mag_s = f"{mag:.1f}" if mag is not None else "unknown"
    place = str(event.get("place") or "location unknown").strip()
    bits = [
        "Earthquake.",
        "U. S. Geological Survey Hawaii.",
        f"Magnitude {mag_s}.",
        f"{place}.",
    ]
    try:
        bits.append(f"Depth {float(event.get('depth_km')):g} kilometers.")
    except (TypeError, ValueError):
        pass
    when = _fmt_time(event)
    if when != "time unknown":
        bits.append(when.replace(" HST", " Hawaiian Standard Time") + ".")
    return " ".join(bits)


def wanted(feed: dict) -> list[dict]:
    events = feed.get("events") if isinstance(feed, dict) else None
    if not isinstance(events, list):
        return []
    out = []
    for event in events:
        if not isinstance(event, dict):
            continue
        qid = str(event.get("id") or "").strip()
        mag = _mag(event)
        if qid and mag is not None and mag >= MIN_MAG:
            out.append(event)
    return out


def load_json(path: Path, default: dict) -> dict:
    if not path.is_file():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def tick(feed: dict, state: dict, *, seed_first: bool) -> dict:
    """Return posted texts. Live mode seeds once. Fixture mode posts new ids."""
    state = dict(state)
    seen = [str(x) for x in (state.get("seen") or []) if str(x).strip()]
    seen_set = set(seen)
    candidates = wanted(feed)
    if seed_first and not state.get("seeded"):
        for event in candidates:
            qid = str(event.get("id") or "")
            if qid and qid not in seen_set:
                seen.append(qid)
                seen_set.add(qid)
        state["seen"] = seen[-400:]
        state["seeded"] = True
        state["posted"] = []
        state["notices"] = []
        return state
    notices = []
    posted = []
    for event in candidates:
        qid = str(event.get("id") or "")
        if not qid or qid in seen_set:
            continue
        if len(posted) >= MAX_POSTS:
            break
        notices.append(format_quake(event))
        posted.append(qid)
        seen.append(qid)
        seen_set.add(qid)
    state["seen"] = seen[-400:]
    state["seeded"] = True
    state["posted"] = posted
    state["notices"] = notices
    return state


def council_chat_id() -> str:
    if not RELAY_CONF.is_file():
        return ""
    for line in RELAY_CONF.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("COUNCIL_CHAT_ID="):
            return s.split("=", 1)[1].strip()
    return ""


def maybe_send(text: str) -> dict:
    """Telegram send stays off unless RR_COUNCIL_QUAKE_SEND=1. Never prints the token."""
    if not send_enabled():
        return {"ok": True, "sent": False, "detail": "send gate off"}
    from envload import carly_token

    token = carly_token()
    chat = council_chat_id()
    if not token or not chat or not text.strip():
        return {"ok": False, "sent": False, "detail": "missing token, chat, or text"}
    body = json.dumps(
        {"chat_id": chat, "text": text[:3900], "disable_web_page_preview": True}
    ).encode()
    import urllib.request

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.load(response)
    return {"ok": bool(payload.get("ok")), "sent": bool(payload.get("ok")), "detail": "sendMessage"}


def append_log(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def run(feed_path: Path, seen_path: Path, log_path: Path, *, seed_first: bool) -> dict:
    feed = load_json(feed_path, {})
    state = load_json(seen_path, {"seen": [], "seeded": False})
    out = tick(feed, state, seed_first=seed_first)
    notices = list(out.get("notices") or [])
    deliveries = []
    for text in notices:
        deliveries.append(maybe_send(text))
    spoken = []
    if wav_enabled() and notices:
        spoken.append("wav gate on; render not called in this dry path")
    row = {
        "at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seeded": bool(out.get("seeded")),
        "posted": out.get("posted") or [],
        "count": len(notices),
        "sent": any(d.get("sent") for d in deliveries),
        "wav": bool(spoken),
    }
    save_json(seen_path, {"seen": out.get("seen") or [], "seeded": True, "last_posted": out.get("posted") or []})
    last_path = seen_path.parent / LAST_NAME
    save_json(last_path, {**row, "notices": notices})
    append_log(log_path, row)
    for text in notices:
        print(text)
        print("---")
    print(json.dumps({"count": len(notices), "posted": out.get("posted") or [], "seeded_only": seed_first and not notices}))
    return row


def self_test() -> int:
    """Empty seen list plus one M2.4 prints one notice; the second run prints zero."""
    event = {
        "id": "hv-test-1",
        "mag": 2.4,
        "place": "5 km SSW of Pahala, Hawaii",
        "time_hst": "2026-09-29T13:16:14-10:00",
        "depth_km": 26.02,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/hv-test-1",
    }
    feed = {"events": [event, {"id": "hv-small", "mag": 1.2, "place": "too small"}]}
    with tempfile.TemporaryDirectory(prefix="council-quake-") as tmp:
        root = Path(tmp)
        feed_path = root / "feed.json"
        seen_path = root / "seen.json"
        log_path = root / "log.jsonl"
        feed_path.write_text(json.dumps(feed), encoding="utf-8")
        seen_path.write_text(json.dumps({"seen": [], "seeded": True}), encoding="utf-8")
        os.environ["RR_COUNCIL_QUAKE_SEND"] = "0"
        os.environ["RR_COUNCIL_QUAKE_WAV"] = "0"
        first = run(feed_path, seen_path, log_path, seed_first=False)
        if first["count"] != 1 or first["posted"] != ["hv-test-1"] or first["sent"]:
            print("FAIL first run", file=sys.stderr)
            return 1
        text = (seen_path.parent / LAST_NAME).read_text(encoding="utf-8")
        if "M 2.4 · 5 km SSW of Pahala, Hawaii" not in text:
            print("FAIL notice body", file=sys.stderr)
            return 1
        if "hv-small" in text:
            print("FAIL below-M2 included", file=sys.stderr)
            return 1
        second = run(feed_path, seen_path, log_path, seed_first=False)
        if second["count"] != 0 or second["posted"]:
            print("FAIL second run", file=sys.stderr)
            return 1
        if HAWAII.exists() and "hv-test-1" in HAWAII.read_text(encoding="utf-8"):
            print("FAIL live quake file touched", file=sys.stderr)
            return 1
    print("PASS council quake dry-run")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    feed = HAWAII
    seen = DATA / SEEN_NAME
    log_path = LOG_DIR / LOG_NAME
    seed_first = True
    if "--feed" in argv:
        feed = Path(argv[argv.index("--feed") + 1])
        seed_first = False
    if "--seen" in argv:
        seen = Path(argv[argv.index("--seen") + 1])
    if "--log" in argv:
        log_path = Path(argv[argv.index("--log") + 1])
    if not feed.is_file():
        print(f"No data: {feed}", file=sys.stderr)
        return 2
    run(feed, seen, log_path, seed_first=seed_first)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
