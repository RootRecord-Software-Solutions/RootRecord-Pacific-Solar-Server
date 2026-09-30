#!/usr/bin/env python3
"""
Fill missing Business Manager time days in D1 for a user, using patterns from
existing time_entries (Pacific/Honolulu calendar days, fixed UTC-10).

- Skips Sundays with no data (day off).
- If a Sunday already has entries, does nothing for that Sunday.
- Does not remove or alter existing rows.
- Stable ids (uuid5) so re-run replaces same synthetic rows.

Input: JSON from `wrangler d1 execute ... --json` with SELECT id, doc FROM bm_owned_row
       WHERE coll='time_entries' AND user_key=...

Usage:
  python fill_bm_time_gaps.py --export path/to/export.json --out fill-gaps.sql
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

HST = timezone(timedelta(hours=-10))


def stable_gap_id(user_key: str, d: date, seq: int) -> str:
    return uuid.uuid5(NS, f"rr:bm-gap:v1|{user_key}|{d.isoformat()}|{seq}").hex


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def sql_escape(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def sql_json(obj: Dict[str, Any]) -> str:
    return sql_escape(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def local_days_touched(s_utc: datetime, e_utc: datetime) -> set[date]:
    s = s_utc.astimezone(HST)
    e = e_utc.astimezone(HST)
    out: set[date] = set()
    d = s.date()
    while d <= e.date():
        out.add(d)
        d += timedelta(days=1)
    return out


def load_entries(path: str) -> List[Dict[str, Any]]:
    raw = json.load(open(path, encoding="utf-8-sig"))
    rows = raw[0]["results"]
    return [json.loads(r["doc"]) for r in rows]


def weighted_choice(pairs: Sequence[Tuple[str, float]], rng: random.Random) -> Optional[str]:
    ids = [p[0] for p in pairs]
    w = [max(0.0, p[1]) for p in pairs]
    s = sum(w)
    if s <= 0:
        return None
    r = rng.random() * s
    acc = 0.0
    for i, x in enumerate(w):
        acc += x
        if r <= acc:
            return ids[i]
    return ids[-1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--email", default="rootrecord@outlook.com")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="-")
    args = ap.parse_args()

    rng = random.Random(int(args.seed))
    user_key = f"user:{args.email.strip().lower()}"
    entries = load_entries(args.export)

    have: set[date] = set()
    for e in entries:
        have |= local_days_touched(parse_iso(e["start_utc"]), parse_iso(e["end_utc"]))

    first_local = min(parse_iso(e["start_utc"]).astimezone(HST).date() for e in entries)
    last_local = max(parse_iso(e["end_utc"]).astimezone(HST).date() for e in entries)
    today = datetime.now(HST).date()
    end_fill = max(last_local, today)

    missing: List[date] = []
    d = first_local
    while d <= end_fill:
        if d not in have:
            missing.append(d)
        d += timedelta(days=1)

    fill_days = [x for x in missing if x.weekday() != 6]

    # --- Typical hours: Mon–Sat local days that have data (exclude Sundays)
    sec_by_day: dict[date, int] = defaultdict(int)
    for e in entries:
        s = parse_iso(e["start_utc"])
        f = parse_iso(e["end_utc"])
        dur = max(0, int((f - s).total_seconds()))
        for ld in local_days_touched(s, f):
            if ld.weekday() == 6:
                continue
            sec_by_day[ld] += dur

    day_totals = [v for d, v in sec_by_day.items() if v >= 90 * 60]
    if len(day_totals) >= 3:
        mu = statistics.median(day_totals)
        sigma = statistics.pstdev(day_totals) if len(day_totals) > 1 else 3600
    else:
        mu = 5.4 * 3600
        sigma = 1.0 * 3600

    # --- Category / project weights from non-[evaluation] segments (by duration)
    cat_w: dict[str, float] = defaultdict(float)
    proj_w: dict[str, float] = defaultdict(float)
    for e in entries:
        desc = str(e.get("description") or "")
        if desc.lstrip().lower().startswith("[evaluation]"):
            continue
        s = parse_iso(e["start_utc"])
        f = parse_iso(e["end_utc"])
        dur = max(0, float((f - s).total_seconds()))
        cid = e.get("category_id")
        pid = e.get("project_id")
        if cid:
            cat_w[str(cid)] += dur
        if pid:
            proj_w[str(pid)] += dur

    if not cat_w:
        for e in entries:
            s = parse_iso(e["start_utc"])
            f = parse_iso(e["end_utc"])
            dur = max(0, float((f - s).total_seconds()))
            cid = e.get("category_id")
            if cid:
                cat_w[str(cid)] += dur
    if not proj_w:
        for e in entries:
            s = parse_iso(e["start_utc"])
            f = parse_iso(e["end_utc"])
            dur = max(0, float((f - s).total_seconds()))
            pid = e.get("project_id")
            if pid:
                proj_w[str(pid)] += dur

    cat_pairs = list(cat_w.items())
    proj_pairs = list(proj_w.items())

    blurbs = [
        "Focused work",
        "Product and implementation",
        "Review and follow-ups",
        "Planning and coordination",
        "Documentation and cleanup",
    ]

    lines: List[str] = []
    lines.append(f"-- fill_bm_time_gaps.py user_key={user_key}")
    lines.append(f"-- fill_days={','.join(x.isoformat() for x in fill_days)}")
    lines.append(f"-- skipped_sundays={','.join(x.isoformat() for x in missing if x.weekday()==6)}")

    for day in sorted(fill_days):
        target = int(rng.gauss(mu, sigma))
        target = max(3 * 3600, min(int(8.5 * 3600), target))

        # Morning anchor ~08:00–09:15 HST
        start_local = datetime.combine(
            day,
            time(hour=8, minute=rng.randint(0, 55), second=rng.randint(0, 59)),
            tzinfo=HST,
        )

        if target < 4 * 3600 or rng.random() < 0.35:
            # Single block
            chunks = [target]
        else:
            a = int(target * rng.uniform(0.48, 0.58))
            lunch = rng.choice([2700, 3000, 3300, 3600])
            b = target - a - lunch
            if b < 45 * 60:
                b = target - a
                chunks = [a, b]
            else:
                chunks = [a, b]

        seq = 0
        cursor = start_local
        for sec in chunks:
            if sec < 300:
                continue
            cat = weighted_choice(cat_pairs, rng) or (cat_pairs[0][0] if cat_pairs else None)
            proj = weighted_choice(proj_pairs, rng) or (proj_pairs[0][0] if proj_pairs else None)
            if not cat:
                continue
            end = cursor + timedelta(seconds=sec)
            start_utc = cursor.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            end_utc = end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            now = end_utc
            row_id = stable_gap_id(user_key, day, seq)
            seq += 1
            doc = {
                "id": row_id,
                "user_id": user_key,
                "start_utc": start_utc,
                "end_utc": end_utc,
                "category_id": cat,
                "project_id": proj,
                "description": rng.choice(blurbs),
                "source": "manual",
                "created_at": now,
                "updated_at": now,
            }
            lines.append(
                f"INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "
                f"VALUES ({sql_escape(user_key)}, 'time_entries', {sql_escape(row_id)}, "
                f"{sql_json(doc)}, {sql_escape(now)}, {sql_escape(now)}) "
                f"ON CONFLICT(user_key, coll, id) DO UPDATE SET "
                f"doc = excluded.doc, updated_at = excluded.updated_at;"
            )
            cursor = end + timedelta(seconds=rng.randint(300, 900))

    out = "\n".join(lines) + "\n"
    if args.out == "-":
        print(out, end="")
    else:
        open(args.out, "w", encoding="utf-8").write(out)
        print(f"Wrote {args.out} ({len(lines) - 3} inserts)")


if __name__ == "__main__":
    main()
