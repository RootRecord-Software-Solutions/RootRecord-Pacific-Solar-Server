#!/usr/bin/env python3
"""
Wipe BM **time taxonomy + time entries** for one user (not income/expense or other
owned collections) and insert April 2026 + **May 1, 2026** time data: business, settings,
categories, projects, quick_actions, and time_entries.

Constraints (per product owner):
  - Hawaii standard time (UTC-10, no DST).
  - April 2026 workdays + May 1 (if not Sunday); Sundays have no time entries.
  - **Apr 29–30, 2026:** “no sleep” arc — very early session start, long wall clock into the
    next morning, **13–15h productive** each day, **fewer breaks** (still some 15m).
  - **May 1, 2026:** up at **~5:00 HST** (not noon), then a normal long session to ~02–03 HST May 2.
  - Other April days: ~10–12h productive; noon-ish start; breaks are extra 15m rows.

Output: SQL for `wrangler d1 execute root-record --remote --file=...`
  (no BEGIN/COMMIT — remote D1 rejects explicit transactions).

Usage:
  python redesign_april_workflow_bm.py --email rootrecord@outlook.com --out redesign-april.sql
"""

from __future__ import annotations

import argparse
import json
import random
import uuid
from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Tuple

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
HST = timezone(timedelta(hours=-10))

YEAR, MONTH = 2026, 4
D_NOSLEEP = (date(2026, 4, 29), date(2026, 4, 30))
D_MAY1 = date(2026, 5, 1)


def stable(kind: str, *parts: str) -> str:
    return uuid.uuid5(NS, "rr:bm-apr26|" + "|".join(parts)).hex


def sql_escape(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def sql_json(obj: Dict[str, Any]) -> str:
    return sql_escape(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))


def fmt_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def emit_insert(
    lines: List[str],
    user_key: str,
    coll: str,
    row_id: str,
    doc: Dict[str, Any],
    created_at: str,
    updated_at: str,
) -> None:
    lines.append(
        f"INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "
        f"VALUES ({sql_escape(user_key)}, {sql_escape(coll)}, {sql_escape(row_id)}, "
        f"{sql_json(doc)}, {sql_escape(created_at)}, {sql_escape(updated_at)});"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", default="rootrecord@outlook.com")
    ap.add_argument("--seed", type=int, default=202604)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rng = random.Random(int(args.seed))
    user_key = f"user:{args.email.strip().lower()}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    lines: List[str] = []

    # --- business
    bid = stable("biz", user_key, "default")
    emit_insert(
        lines,
        user_key,
        "businesses",
        bid,
        {
            "id": bid,
            "user_id": user_key,
            "name": "Root Record",
            "legal_name": "",
            "owner": "",
            "tax_id": "",
            "email": "",
            "phone": "",
            "website": "",
            "address": "",
            "timezone": "Pacific/Honolulu",
            "invoice_notes": "",
            "is_default": True,
            "created_at": now,
            "updated_at": now,
        },
        now,
        now,
    )

    # --- settings
    emit_insert(
        lines,
        user_key,
        "settings",
        "default",
        {
            "user_id": user_key,
            "currency_default": "USD",
            "theme": "dark",
            "prompt_interval_sec": 900,
            "prompt_first_delay_sec": 120,
            "prompt_response_timeout_sec": 45,
            "default_hourly_cents": 0,
            "show_money_in_dashboard": True,
            "help_bubbles_enabled": True,
            "business_timezone": "Pacific/Honolulu",
            "active_business_id": bid,
            "updated_at": now,
        },
        now,
        now,
    )

    # --- categories (no Planning — former planning time split across Dev / Test / Doc / Research only)
    cat_specs: List[Tuple[str, str, int, int]] = [
        ("Development", "#339af0", 1, 0),
        ("Testing", "#2B8A8F", 1, 2000),
        ("Documentation", "#12b886", 1, 3000),
        ("Research", "#1f6aa5", 1, 4000),
        ("Admin", "#7950F2", 1, 5000),
        ("Break", "#FF0000", 0, 6000),
    ]
    cat_id: Dict[str, str] = {}
    for name, color, billable, so in cat_specs:
        cid = stable("cat", user_key, name)
        cat_id[name] = cid
        emit_insert(
            lines,
            user_key,
            "categories",
            cid,
            {
                "id": cid,
                "user_id": user_key,
                "name": name,
                "color": color,
                "icon": "",
                "kind": "time",
                "billable": billable,
                "archived": 0,
                "sort_order": so,
                "default_hourly_cents": None,
                "created_at": now,
                "updated_at": now,
            },
            now,
            now,
        )

    # --- projects
    proj_specs = [
        ("Root Record Business Manager", "Root Record"),
        ("Root Record Weather Manager", ""),
        ("Overall Operations", ""),
    ]
    proj_id: Dict[str, str] = {}
    for pname, client in proj_specs:
        pid = stable("proj", user_key, pname)
        proj_id[pname] = pid
        emit_insert(
            lines,
            user_key,
            "projects",
            pid,
            {
                "id": pid,
                "user_id": user_key,
                "name": pname,
                "client_name": client,
                "color": "#5C4D7D",
                "default_hourly_cents": None,
                "currency": "USD",
                "notes": "",
                "archived": 0,
                "sort_order": 999,
                "created_at": now,
                "updated_at": now,
            },
            now,
            now,
        )

    # --- quick actions
    qa_specs = [
        ("Deep work", "Development", "Heads-down implementation"),
        ("Day prep", "Development", "Scope, backlog, and first implementation slice"),
        ("Ship checklist", "Testing", "Pre-release verification"),
    ]
    for i, (label, cname, desc) in enumerate(qa_specs):
        qid = stable("qa", user_key, label)
        emit_insert(
            lines,
            user_key,
            "quick_actions",
            qid,
            {
                "id": qid,
                "user_id": user_key,
                "label": label,
                "category_id": cat_id[cname],
                "project_id": proj_id["Root Record Business Manager"],
                "default_description": desc,
                "sort_order": i * 100,
                "created_at": now,
                "updated_at": now,
            },
            now,
            now,
        )

    # --- time: April 2026 + May 1 HST; skip Sundays
    _, last_day = monthrange(YEAR, MONTH)
    work_dates: List[date] = []
    for day in range(1, last_day + 1):
        dd = date(YEAR, MONTH, day)
        if dd.weekday() != 6:
            work_dates.append(dd)
    if D_MAY1.weekday() != 6:
        work_dates.append(D_MAY1)
    # Work-only rotation (natural solo flow). Breaks are injected separately as 15m entries, not in this list.
    workflow = [
        ("Development", "Root Record Business Manager", "Warm-up: scope and first changes"),
        ("Development", "Root Record Business Manager", "Main implementation block"),
        ("Testing", "Root Record Business Manager", "Regression on recent changes"),
        ("Documentation", "Root Record Business Manager", "Notes while context is fresh"),
        ("Research", "Root Record Business Manager", "Spike or API / library check"),
        ("Development", "Root Record Weather Manager", "Weather pipeline or alerts"),
        ("Development", "Root Record Business Manager", "Integration and follow-on fixes"),
        ("Testing", "Root Record Business Manager", "Broader pass / edge cases"),
        ("Documentation", "Root Record Business Manager", "Runbooks and release notes"),
        ("Development", "Root Record Business Manager", "Late polish and hardening"),
        ("Admin", "Root Record Business Manager", "Inbox and loose ends"),
    ]

    def pick_project(weights: List[Tuple[str, float]]) -> str:
        names = [w[0] for w in weights]
        ws = [w[1] for w in weights]
        return rng.choices(names, weights=ws, k=1)[0]

    total_productive_minutes = 0
    work_days = 0

    nosleep_notes = [
        "Overnight push — still up",
        "No sleep between days; kept going",
        "Late merge after long stretch",
        "Powering through the night",
        "Coffee + code (no shutdown)",
    ]

    for d in work_dates:
        work_days += 1

        if d in D_NOSLEEP:
            # Apr 29–30: awake across calendar days — early start, long span, heavy hours, rare breaks.
            if d == date(2026, 4, 29):
                day_start = datetime.combine(
                    d,
                    time(hour=rng.randint(1, 4), minute=rng.randint(0, 55), second=rng.randint(0, 59)),
                    tzinfo=HST,
                )
                close_hst = datetime.combine(
                    date(2026, 4, 30),
                    time(hour=rng.randint(3, 5), minute=rng.randint(0, 55), second=rng.randint(0, 59)),
                    tzinfo=HST,
                )
            else:
                # Start after the prior night’s tail (avoid overlapping Apr 29 entries that end pre-dawn Apr 30).
                day_start = datetime.combine(
                    d,
                    time(hour=rng.randint(6, 8), minute=rng.randint(0, 50), second=rng.randint(0, 59)),
                    tzinfo=HST,
                )
                close_hst = datetime.combine(
                    date(2026, 5, 1),
                    time(hour=rng.randint(3, 4), minute=rng.randint(10, 55), second=rng.randint(0, 59)),
                    tzinfo=HST,
                )
            productive_target = rng.randint(780, 900)
            break_prob_scale = 0.22
        elif d == D_MAY1:
            # May 1: actually up at ~5am HST after the no-sleep stretch.
            day_start = datetime.combine(
                d,
                time(hour=5, minute=rng.randint(0, 12), second=rng.randint(0, 59)),
                tzinfo=HST,
            )
            close_hst = datetime.combine(
                d + timedelta(days=1),
                time(hour=rng.randint(2, 3), minute=rng.randint(0, 55), second=rng.randint(0, 59)),
                tzinfo=HST,
            )
            productive_target = rng.randint(540, 660)
            break_prob_scale = 1.0
        else:
            productive_target = rng.randint(600, 720)
            day_start = datetime.combine(
                d,
                time(hour=12, minute=rng.randint(0, 40), second=rng.randint(0, 59)),
                tzinfo=HST,
            )
            close_hst = datetime.combine(
                d + timedelta(days=1),
                time(hour=rng.randint(2, 3), minute=rng.randint(0, 55), second=rng.randint(0, 59)),
                tzinfo=HST,
            )
            break_prob_scale = 1.0

        total_productive_minutes += productive_target

        cursor = day_start
        productive_done = 0
        minutes_since_break = 0
        seg_idx = 0
        first_seg = True
        break_idx = 0

        desc_pool = {
            "Development": [
                "Feature implementation",
                "Bugfix and hardening",
                "Integration work",
                "Refactor for maintainability",
                "Local build iteration",
                "Environment config",
                "CLI and tooling work",
                "Scope check before deeper coding",
                "Backlog grooming turned into tasks",
            ],
            "Testing": [
                "Manual test pass",
                "Scenario validation",
                "Release smoke tests",
                "End-to-end path checks",
                "Test cases from acceptance notes",
            ],
            "Break": [
                "Break (15m)",
                "Stretch / snack",
                "Away from keyboard",
                "Quick reset",
            ],
            "Documentation": [
                "Update internal docs",
                "Runbook and deployment notes",
                "API and schema notes",
                "Roadmap alignment captured in docs",
                "Design notes for the next milestone",
            ],
            "Research": [
                "Evaluate library / approach",
                "Prototype spike",
                "Architecture comparison",
                "Feasibility check before commit",
            ],
            "Admin": [
                "Email and calendar",
                "Ticket hygiene",
            ],
        }

        def emit_segment(
            wname: str,
            proj_name: str,
            m: int,
            seg_tag: str,
        ) -> None:
            nonlocal cursor
            start = cursor
            end = start + timedelta(minutes=m)
            cursor = end
            desc = rng.choice(desc_pool.get(wname, ["Focused work"]))
            if d in D_NOSLEEP and wname != "Break" and rng.random() < 0.42:
                desc = rng.choice(nosleep_notes) + " — " + desc
            elif d == D_MAY1 and wname != "Break" and rng.random() < 0.38:
                desc = "Up ~5am — " + desc
            tid = stable("time", user_key, d.isoformat(), seg_tag, str(m), str(rng.randint(0, 9999)))
            doc = {
                "id": tid,
                "user_id": user_key,
                "start_utc": fmt_z(start),
                "end_utc": fmt_z(end),
                "category_id": cat_id[wname],
                "project_id": proj_id[proj_name],
                "description": desc,
                "source": "manual",
                "created_at": fmt_z(end),
                "updated_at": fmt_z(end),
            }
            emit_insert(lines, user_key, "time_entries", tid, doc, fmt_z(end), fmt_z(end))

        for _ in range(120):
            if productive_done >= productive_target:
                break
            still = productive_target - productive_done
            slot_left = int((close_hst - cursor).total_seconds() // 60)
            if slot_left < 12:
                break

            if not first_seg:
                micro = rng.randint(0, 6)
                micro = min(micro, max(0, slot_left - 12))
                if micro > 0:
                    cursor += timedelta(minutes=micro)
                slot_left = int((close_hst - cursor).total_seconds() // 60)
            first_seg = False
            if slot_left < 12:
                break

            # Multiple 15m breaks per day, no cap — probability rises the longer since last break.
            if (
                productive_done > 0
                and minutes_since_break >= 35
                and slot_left >= 18
            ):
                p_break = min(0.52, 0.16 + (minutes_since_break - 35) * 0.006) * break_prob_scale
                if rng.random() < p_break:
                    break_idx += 1
                    emit_segment(
                        "Break",
                        "Root Record Business Manager",
                        15,
                        f"brk{break_idx}",
                    )
                    minutes_since_break = 0
                    slot_left = int((close_hst - cursor).total_seconds() // 60)
                    if slot_left < 12:
                        break
                    continue

            wname, default_proj, _desc_template = workflow[seg_idx % len(workflow)]
            seg_idx += 1

            hi = min(150, still + 25, slot_left)
            lo = min(45, hi)
            if hi < 15:
                m = min(still, slot_left)
            elif still <= slot_left and still <= hi:
                m = still
            else:
                m = rng.randint(lo, hi) if hi >= lo else min(still, slot_left)
            m = int(max(10, min(m, still, slot_left)))

            proj_name = default_proj
            if wname == "Development" and rng.random() < 0.35:
                proj_name = pick_project(
                    [
                        ("Root Record Business Manager", 0.55),
                        ("Root Record Weather Manager", 0.35),
                        ("Overall Operations", 0.1),
                    ]
                )

            emit_segment(wname, proj_name, m, f"w{seg_idx}")
            productive_done += m
            minutes_since_break += m

        # If breaks ate clock before hitting productive target, finish without more breaks.
        for _ in range(40):
            if productive_done >= productive_target:
                break
            still = productive_target - productive_done
            slot_left = int((close_hst - cursor).total_seconds() // 60)
            if slot_left < 8:
                break
            wname, default_proj, _ = workflow[seg_idx % len(workflow)]
            seg_idx += 1
            m = int(max(10, min(still, slot_left)))
            proj_name = default_proj
            if wname == "Development" and rng.random() < 0.35:
                proj_name = pick_project(
                    [
                        ("Root Record Business Manager", 0.55),
                        ("Root Record Weather Manager", 0.35),
                        ("Overall Operations", 0.1),
                    ]
                )
            emit_segment(wname, proj_name, m, f"t{seg_idx}")
            productive_done += m
            minutes_since_break += m

    header = (
        "-- redesign_april_workflow_bm.py: Apr 2026 + May 1 HST (wipes time stack only; keeps income/expense)\n"
        f"-- user_key={user_key} | work_days={work_days} | "
        f"productive_minutes={total_productive_minutes} (~{total_productive_minutes / 60:.1f} h; breaks extra)\n"
        "-- Apr 29-30: no-sleep arc (early start, long span). May 1: start ~5am HST.\n"
        "DELETE FROM bm_owned_row WHERE user_key = "
        + sql_escape(user_key)
        + " AND coll IN ("
        + ",".join(
            sql_escape(c)
            for c in (
                "businesses",
                "settings",
                "categories",
                "projects",
                "quick_actions",
                "time_entries",
            )
        )
        + ");"
    )
    open(args.out, "w", encoding="utf-8").write(header + "\n" + "\n".join(lines) + "\n")
    print(
        f"Wrote {args.out} ({len(lines)} lines), ~{total_productive_minutes/60:.1f} productive hours "
        f"across {work_days} work days (incl. May 1)"
    )


if __name__ == "__main__":
    main()
