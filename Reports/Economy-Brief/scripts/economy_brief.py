#!/usr/bin/env python3
"""Daily economy brief markdown (G1 economy-brief).

Writes Database Reports/Economy-Brief/economy-brief-YYYY-MM-DD.md from a
MySQL desk-facts snapshot plus Geology Volcanoes/kilauea-last.json.
Gold stays in-game. The file never uses a dollar sign.

Council persona prompts are not used. This script does not build that Folder.

Night sleep: if System/NightSleep/scripts/night_sleep.py exists, call should_run
on a live run. A missing Folder means not sleeping. --dry-run still writes.

Discord is not called. --send refuses unless RR_ECONOMY_BRIEF_SEND=1, and even
then this script does not post. A live post needs a separate sign-off.

  python3 economy_brief.py --fixture snap.json --dry-run
  python3 economy_brief.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HST = ZoneInfo("Pacific/Honolulu")
HERE = Path(__file__).resolve().parent
PACIFIC = HERE.parents[2]
DB = Path(os.environ.get("RR_DATABASE_ROOT", "/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database"))
OUT_DIR = DB / "Reports" / "Economy-Brief"
LAST = OUT_DIR / "last.json"
LOG = DB / "Logs" / "Reports" / "Economy-Brief" / "economy-brief.jsonl"
KILA = DB / "Geology" / "Volcanoes" / "kilauea-last.json"
FACTS_LAST = DB / "System" / "MysqlDesk" / "facts-last.json"
MYSQL = PACIFIC / "System" / "MysqlDesk" / "scripts" / "mysql_desk.py"
GATE = PACIFIC / "System" / "NightSleep" / "scripts" / "night_sleep.py"
JOB_ID = "reports_economy_brief"
NOTE = "Gold never converts to dollars."


def now() -> datetime:
    return datetime.now(HST).replace(microsecond=0)


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def night_skip() -> str | None:
    """None means run. A missing gate Folder is not sleeping."""
    if not GATE.is_file():
        return None
    try:
        mod = _load(GATE)
        fn = getattr(mod, "should_run", None) if mod else None
        if not callable(fn):
            return None
        try:
            allowed = fn(JOB_ID)
        except TypeError:
            allowed = fn()
    except Exception:
        return None
    return None if allowed else "night_sleep"


def kilauea() -> tuple[str, float]:
    alert, mult = "unknown", 1.0
    try:
        if not KILA.is_file():
            return alert, mult
        data = json.loads(KILA.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return alert, mult
        alert = str(data.get("alert_level") or data.get("alert") or alert)
        mult = float(data.get("multiplier") or 1.0)
    except Exception:
        return "unknown", 1.0
    return alert, mult


def empty_snap() -> dict:
    return {
        "ok": False,
        "wallets": 0,
        "positive_gold": 0,
        "total_gold": 0,
        "bonds_count": 0,
        "bonds_principal": 0,
        "error": "no-snapshot",
    }


def load_snapshot(fixture: Path | None, dry: bool) -> dict:
    if fixture is not None:
        data = json.loads(fixture.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit("fixture must be a JSON object")
        return data
    if dry and FACTS_LAST.is_file():
        data = json.loads(FACTS_LAST.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    if dry or not MYSQL.is_file():
        return empty_snap()
    mod = _load(MYSQL)
    fn = getattr(mod, "facts", None) if mod else None
    if not callable(fn):
        snap = empty_snap()
        snap["error"] = "mysql-desk-facts-missing"
        return snap
    snap = fn()
    return snap if isinstance(snap, dict) else empty_snap()


def brief_markdown(snap: dict, t: datetime, alert: str, mult: float) -> str:
    stamp = t.strftime("%Y-%m-%d")
    lines = [
        f"# Economy brief — {stamp} HST",
        "",
        f"Generated {t.isoformat()}",
        "",
        "## Live MySQL snapshot",
        f"- ok: `{snap.get('ok')}`",
        f"- wallets: `{snap.get('wallets')}`",
        f"- circulating (+) gold: `{snap.get('positive_gold')}` g",
        f"- net sum gold: `{snap.get('total_gold')}` g",
        f"- bonds outstanding: `{snap.get('bonds_count')}` / principal `{snap.get('bonds_principal')}` g",
        f"- Kīlauea alert: `{alert}` · multiplier `{mult}`",
        "",
        "## Notes",
        "- Sourced from Shockbyte `root_economy_balances` (local mirror fallback).",
        f"- {NOTE}",
        "",
    ]
    text = "\n".join(lines)
    if "$" in text:
        raise SystemExit("brief contained a dollar sign")
    return text


def discord_card(snap: dict, t: datetime, alert: str, mult: float) -> str:
    """Old #automations card. Composed only. This function does not post it."""
    now_hst = t.strftime("%Y-%m-%d %H:%M HST")
    if not snap.get("ok"):
        body = (
            f"**Player economy** — {now_hst}\n"
            f"MySQL snapshot failed: `{snap.get('error') or 'unknown'}`"
        )
    else:
        body = (
            f"**Player economy (live MySQL)** — {now_hst}\n"
            f"Wallets: **{snap.get('wallets')}** · "
            f"Circulating (+): **{snap.get('positive_gold')} g** · "
            f"Net sum: **{snap.get('total_gold')} g**\n"
            f"Bonds outstanding: **{snap.get('bonds_count')}** · "
            f"Principal: **{snap.get('bonds_principal')} g**\n"
            "_Gold stays in-game. No USD conversion._"
        )
    if float(mult) != 1.0:
        body += f"\nKīlauea {alert} — multiplier ×{float(mult):.1f}"
    return body[:1900]


def _arg(flag: str) -> Path | None:
    if flag not in sys.argv:
        return None
    i = sys.argv.index(flag)
    if i + 1 >= len(sys.argv):
        raise SystemExit(f"{flag} needs a path")
    return Path(sys.argv[i + 1])


def write_outputs(text: str, payload: dict, dry: bool) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    day = payload["day"]
    out = OUT_DIR / f"economy-brief-{day}.md"
    out.write_text(text, encoding="utf-8")
    payload["path"] = str(out)
    tmp = LAST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, LAST)
    if not dry:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return out


def main() -> int:
    dry = "--dry-run" in sys.argv
    send = "--send" in sys.argv
    fixture = _arg("--fixture")
    t = now()
    skip = None if dry else night_skip()
    alert, mult = kilauea()
    if skip:
        payload = {
            "at": t.isoformat(),
            "job": JOB_ID,
            "day": t.strftime("%Y-%m-%d"),
            "result": "skip",
            "detail": skip,
            "dry_run": dry,
            "posted": False,
        }
        LAST.parent.mkdir(parents=True, exist_ok=True)
        LAST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload))
        return 0
    snap = load_snapshot(fixture, dry)
    text = brief_markdown(snap, t, alert, mult)
    payload = {
        "at": t.isoformat(),
        "job": JOB_ID,
        "day": t.strftime("%Y-%m-%d"),
        "result": "dry-run" if dry else "wrote",
        "ok": bool(snap.get("ok")),
        "wallets": snap.get("wallets"),
        "alert": alert,
        "multiplier": mult,
        "dry_run": dry,
        "posted": False,
        "fixture": str(fixture) if fixture else None,
    }
    out = write_outputs(text, payload, dry)
    if send:
        card = discord_card(snap, t, alert, mult)
        if "$" in card:
            print("send refused: card contained a dollar sign", file=sys.stderr)
            return 2
        if os.environ.get("RR_ECONOMY_BRIEF_SEND", "0").strip() != "1":
            print("send refused: RR_ECONOMY_BRIEF_SEND is not 1", file=sys.stderr)
            return 2
        print("send refused: Discord post is not signed off", file=sys.stderr)
        return 2
    print(json.dumps({"result": payload["result"], "path": str(out), "posted": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
