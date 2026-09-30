# ==============================================================================
# FILE: Products/scripts/FinanceDesk/fill_bm_time_gaps.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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

from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import random  # info: import random
import statistics  # info: import statistics
import uuid  # info: import uuid
from collections import defaultdict  # info: from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone  # info: from datetime import date , datetime , time
from typing import Any, Dict, List, Optional, Sequence, Tuple  # info: from typing import Any , Dict , List

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # info: set NS

HST = timezone(timedelta(hours=-10))  # info: set HST


# ====================================================
# SECTION: function stable_gap_id
# What it does: stable gap id.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stable_gap_id(user_key: str, d: date, seq: int) -> str:  # info: def stable_gap_id
    return uuid.uuid5(NS, f"rr:bm-gap:v1|{user_key}|{d.isoformat()}|{seq}").hex  # info: return uuid . uuid5 ( NS , f"


# ====================================================
# SECTION: function parse_iso
# What it does: parse iso.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_iso(s: str) -> datetime:  # info: def parse_iso
    return datetime.fromisoformat(s.replace("Z", "+00:00"))  # info: return datetime . fromisoformat ( s . replace


# ====================================================
# SECTION: function sql_escape
# What it does: sql escape.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sql_escape(s: str) -> str:  # info: def sql_escape
    return "'" + s.replace("'", "''") + "'"  # info: return "'" + s . replace ( "'"


# ====================================================
# SECTION: function sql_json
# What it does: sql json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def sql_json(obj: Dict[str, Any]) -> str:  # info: def sql_json
    return sql_escape(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))  # info: return sql_escape ( json . dumps ( obj


# ====================================================
# SECTION: function local_days_touched
# What it does: local days touched.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def local_days_touched(s_utc: datetime, e_utc: datetime) -> set[date]:  # info: def local_days_touched
    s = s_utc.astimezone(HST)  # info: set s
    e = e_utc.astimezone(HST)  # info: set e
    out: set[date] = set()  # info: set out
    d = s.date()  # info: set d
    while d <= e.date():  # info: while d <= e . date ( )
        out.add(d)  # info: out . add ( d )
        d += timedelta(days=1)  # info: set d
    return out  # info: return out


# ====================================================
# SECTION: function load_entries
# What it does: load entries.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def load_entries(path: str) -> List[Dict[str, Any]]:  # info: def load_entries
    raw = json.load(open(path, encoding="utf-8-sig"))  # info: set raw
    rows = raw[0]["results"]  # info: set rows
    return [json.loads(r["doc"]) for r in rows]  # info: return [ json . loads ( r [


# ====================================================
# SECTION: function weighted_choice
# What it does: weighted choice.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def weighted_choice(pairs: Sequence[Tuple[str, float]], rng: random.Random) -> Optional[str]:  # info: def weighted_choice
    ids = [p[0] for p in pairs]  # info: set ids
    w = [max(0.0, p[1]) for p in pairs]  # info: set w
    s = sum(w)  # info: set s
    if s <= 0:  # info: if s <= 0 :
        return None  # info: return None
    r = rng.random() * s  # info: set r
    acc = 0.0  # info: set acc
    for i, x in enumerate(w):  # info: for i , x in enumerate ( w
        acc += x  # info: set acc
        if r <= acc:  # info: if r <= acc :
            return ids[i]  # info: return ids [ i ]
    return ids[-1]  # info: return ids [ - 1 ]


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--export", required=True)  # info: ap . add_argument ( "--export" , required =
    ap.add_argument("--email", default="rootrecord@outlook.com")  # info: ap . add_argument ( "--email" , default =
    ap.add_argument("--seed", type=int, default=42)  # info: ap . add_argument ( "--seed" , type =
    ap.add_argument("--out", default="-")  # info: ap . add_argument ( "--out" , default =
    args = ap.parse_args()  # info: set args

    rng = random.Random(int(args.seed))  # info: set rng
    user_key = f"user:{args.email.strip().lower()}"  # info: set user_key
    entries = load_entries(args.export)  # info: set entries

    have: set[date] = set()  # info: set have
    for e in entries:  # info: for e in entries :
        have |= local_days_touched(parse_iso(e["start_utc"]), parse_iso(e["end_utc"]))  # info: have |= local_days_touched ( parse_iso ( e [

    first_local = min(parse_iso(e["start_utc"]).astimezone(HST).date() for e in entries)  # info: set first_local
    last_local = max(parse_iso(e["end_utc"]).astimezone(HST).date() for e in entries)  # info: set last_local
    today = datetime.now(HST).date()  # info: set today
    end_fill = max(last_local, today)  # info: set end_fill

    missing: List[date] = []  # info: set missing
    d = first_local  # info: set d
    while d <= end_fill:  # info: while d <= end_fill :
        if d not in have:  # info: if d not in have :
            missing.append(d)  # info: missing . append ( d )
        d += timedelta(days=1)  # info: set d

    fill_days = [x for x in missing if x.weekday() != 6]  # info: set fill_days

    # --- Typical hours: Mon–Sat local days that have data (exclude Sundays)
    sec_by_day: dict[date, int] = defaultdict(int)  # info: set sec_by_day
    for e in entries:  # info: for e in entries :
        s = parse_iso(e["start_utc"])  # info: set s
        f = parse_iso(e["end_utc"])  # info: set f
        dur = max(0, int((f - s).total_seconds()))  # info: set dur
        for ld in local_days_touched(s, f):  # info: for ld in local_days_touched ( s , f
            if ld.weekday() == 6:  # info: if ld . weekday ( ) == 6
                continue  # info: continue
            sec_by_day[ld] += dur  # info: sec_by_day [ ld ] += dur

    day_totals = [v for d, v in sec_by_day.items() if v >= 90 * 60]  # info: set day_totals
    if len(day_totals) >= 3:  # info: if len ( day_totals ) >= 3 :
        mu = statistics.median(day_totals)  # info: set mu
        sigma = statistics.pstdev(day_totals) if len(day_totals) > 1 else 3600  # info: set sigma
    else:  # info: else :
        mu = 5.4 * 3600  # info: set mu
        sigma = 1.0 * 3600  # info: set sigma

    # --- Category / project weights from non-[evaluation] segments (by duration)
    cat_w: dict[str, float] = defaultdict(float)  # info: set cat_w
    proj_w: dict[str, float] = defaultdict(float)  # info: set proj_w
    for e in entries:  # info: for e in entries :
        desc = str(e.get("description") or "")  # info: set desc
        if desc.lstrip().lower().startswith("[evaluation]"):  # info: if desc . lstrip ( ) . lower
            continue  # info: continue
        s = parse_iso(e["start_utc"])  # info: set s
        f = parse_iso(e["end_utc"])  # info: set f
        dur = max(0, float((f - s).total_seconds()))  # info: set dur
        cid = e.get("category_id")  # info: set cid
        pid = e.get("project_id")  # info: set pid
        if cid:  # info: if cid :
            cat_w[str(cid)] += dur  # info: cat_w [ str ( cid ) ] +=
        if pid:  # info: if pid :
            proj_w[str(pid)] += dur  # info: proj_w [ str ( pid ) ] +=

    if not cat_w:  # info: if not cat_w :
        for e in entries:  # info: for e in entries :
            s = parse_iso(e["start_utc"])  # info: set s
            f = parse_iso(e["end_utc"])  # info: set f
            dur = max(0, float((f - s).total_seconds()))  # info: set dur
            cid = e.get("category_id")  # info: set cid
            if cid:  # info: if cid :
                cat_w[str(cid)] += dur  # info: cat_w [ str ( cid ) ] +=
    if not proj_w:  # info: if not proj_w :
        for e in entries:  # info: for e in entries :
            s = parse_iso(e["start_utc"])  # info: set s
            f = parse_iso(e["end_utc"])  # info: set f
            dur = max(0, float((f - s).total_seconds()))  # info: set dur
            pid = e.get("project_id")  # info: set pid
            if pid:  # info: if pid :
                proj_w[str(pid)] += dur  # info: proj_w [ str ( pid ) ] +=

    cat_pairs = list(cat_w.items())  # info: set cat_pairs
    proj_pairs = list(proj_w.items())  # info: set proj_pairs

    blurbs = [  # info: set blurbs
        "Focused work",  # info: "Focused work" ,
        "Product and implementation",  # info: "Product and implementation" ,
        "Review and follow-ups",  # info: "Review and follow-ups" ,
        "Planning and coordination",  # info: "Planning and coordination" ,
        "Documentation and cleanup",  # info: "Documentation and cleanup" ,
    ]  # info: ]

    lines: List[str] = []  # info: set lines
    lines.append(f"-- fill_bm_time_gaps.py user_key={user_key}")  # info: lines . append ( f" -- fill_bm_time_gaps.py user_key= { user_key
    lines.append(f"-- fill_days={','.join(x.isoformat() for x in fill_days)}")  # info: lines . append ( f" -- fill_days= { ','
    lines.append(f"-- skipped_sundays={','.join(x.isoformat() for x in missing if x.weekday()==6)}")  # info: lines . append ( f" -- skipped_sundays= { ','

    for day in sorted(fill_days):  # info: for day in sorted ( fill_days ) :
        target = int(rng.gauss(mu, sigma))  # info: set target
        target = max(3 * 3600, min(int(8.5 * 3600), target))  # info: set target

        # Morning anchor ~08:00–09:15 HST
        start_local = datetime.combine(  # info: set start_local
            day,  # info: day ,
            time(hour=8, minute=rng.randint(0, 55), second=rng.randint(0, 59)),  # info: call time
            tzinfo=HST,  # info: set tzinfo
        )  # info: )

        if target < 4 * 3600 or rng.random() < 0.35:  # info: if target < 4 * 3600 or rng
            # Single block
            chunks = [target]  # info: set chunks
        else:  # info: else :
            a = int(target * rng.uniform(0.48, 0.58))  # info: set a
            lunch = rng.choice([2700, 3000, 3300, 3600])  # info: set lunch
            b = target - a - lunch  # info: set b
            if b < 45 * 60:  # info: if b < 45 * 60 :
                b = target - a  # info: set b
                chunks = [a, b]  # info: set chunks
            else:  # info: else :
                chunks = [a, b]  # info: set chunks

        seq = 0  # info: set seq
        cursor = start_local  # info: set cursor
        for sec in chunks:  # info: for sec in chunks :
            if sec < 300:  # info: if sec < 300 :
                continue  # info: continue
            cat = weighted_choice(cat_pairs, rng) or (cat_pairs[0][0] if cat_pairs else None)  # info: set cat
            proj = weighted_choice(proj_pairs, rng) or (proj_pairs[0][0] if proj_pairs else None)  # info: set proj
            if not cat:  # info: if not cat :
                continue  # info: continue
            end = cursor + timedelta(seconds=sec)  # info: set end
            start_utc = cursor.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")  # info: set start_utc
            end_utc = end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")  # info: set end_utc
            now = end_utc  # info: set now
            row_id = stable_gap_id(user_key, day, seq)  # info: set row_id
            seq += 1  # info: set seq
            doc = {  # info: set doc
                "id": row_id,  # info: "id" : row_id ,
                "user_id": user_key,  # info: "user_id" : user_key ,
                "start_utc": start_utc,  # info: "start_utc" : start_utc ,
                "end_utc": end_utc,  # info: "end_utc" : end_utc ,
                "category_id": cat,  # info: "category_id" : cat ,
                "project_id": proj,  # info: "project_id" : proj ,
                "description": rng.choice(blurbs),  # info: "description" : rng . choice ( blurbs )
                "source": "manual",  # info: "source" : "manual" ,
                "created_at": now,  # info: "created_at" : now ,
                "updated_at": now,  # info: "updated_at" : now ,
            }  # info: }
            lines.append(  # info: lines . append (
                f"INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "  # info: f" INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "
                f"VALUES ({sql_escape(user_key)}, 'time_entries', {sql_escape(row_id)}, "  # info: f" VALUES ( { sql_escape ( user_key ) }
                f"{sql_json(doc)}, {sql_escape(now)}, {sql_escape(now)}) "  # info: f" { sql_json ( doc ) } ,
                f"ON CONFLICT(user_key, coll, id) DO UPDATE SET "  # info: f" ON CONFLICT(user_key, coll, id) DO UPDATE SET "
                f"doc = excluded.doc, updated_at = excluded.updated_at;"  # info: f" doc = excluded.doc, updated_at = excluded.updated_at; "
            )  # info: )
            cursor = end + timedelta(seconds=rng.randint(300, 900))  # info: set cursor

    out = "\n".join(lines) + "\n"  # info: set out
    if args.out == "-":  # info: if args . out == "-" :
        print(out, end="")  # info: call print
    else:  # info: else :
        open(args.out, "w", encoding="utf-8").write(out)  # info: call open
        print(f"Wrote {args.out} ({len(lines) - 3} inserts)")  # info: call print


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
