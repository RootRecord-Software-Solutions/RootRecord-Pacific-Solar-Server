# ==============================================================================
# FILE: Products/scripts/FinanceDesk/redesign_april_workflow_bm.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
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

from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import json  # info: import json
import random  # info: import random
import uuid  # info: import uuid
from calendar import monthrange  # info: from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone  # info: from datetime import date , datetime , time
from typing import Any, Dict, List, Tuple  # info: from typing import Any , Dict , List

NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # info: set NS
HST = timezone(timedelta(hours=-10))  # info: set HST

YEAR, MONTH = 2026, 4  # info: YEAR , MONTH = 2026 , 4
D_NOSLEEP = (date(2026, 4, 29), date(2026, 4, 30))  # info: set D_NOSLEEP
D_MAY1 = date(2026, 5, 1)  # info: set D_MAY1


# ====================================================
# SECTION: function stable
# What it does: stable.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def stable(kind: str, *parts: str) -> str:  # info: def stable
    return uuid.uuid5(NS, "rr:bm-apr26|" + "|".join(parts)).hex  # info: return uuid . uuid5 ( NS , "rr:bm-apr26|"


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
# SECTION: function fmt_z
# What it does: fmt z.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fmt_z(dt: datetime) -> str:  # info: def fmt_z
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")  # info: return dt . astimezone ( timezone . utc


# ====================================================
# SECTION: function emit_insert
# What it does: emit insert.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def emit_insert(  # info: def emit_insert
    lines: List[str],  # info: set lines
    user_key: str,  # info: set user_key
    coll: str,  # info: set coll
    row_id: str,  # info: set row_id
    doc: Dict[str, Any],  # info: set doc
    created_at: str,  # info: set created_at
    updated_at: str,  # info: set updated_at
) -> None:  # info: ) -> None :
    lines.append(  # info: lines . append (
        f"INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "  # info: f" INSERT INTO bm_owned_row (user_key, coll, id, doc, created_at, updated_at) "
        f"VALUES ({sql_escape(user_key)}, {sql_escape(coll)}, {sql_escape(row_id)}, "  # info: f" VALUES ( { sql_escape ( user_key ) }
        f"{sql_json(doc)}, {sql_escape(created_at)}, {sql_escape(updated_at)});"  # info: f" { sql_json ( doc ) } ,
    )  # info: )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> None:  # info: def main
    ap = argparse.ArgumentParser()  # info: set ap
    ap.add_argument("--email", default="rootrecord@outlook.com")  # info: ap . add_argument ( "--email" , default =
    ap.add_argument("--seed", type=int, default=202604)  # info: ap . add_argument ( "--seed" , type =
    ap.add_argument("--out", required=True)  # info: ap . add_argument ( "--out" , required =
    args = ap.parse_args()  # info: set args

    rng = random.Random(int(args.seed))  # info: set rng
    user_key = f"user:{args.email.strip().lower()}"  # info: set user_key
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  # info: set now

    lines: List[str] = []  # info: set lines

    # --- business
    bid = stable("biz", user_key, "default")  # info: set bid
    emit_insert(  # info: call emit_insert
        lines,  # info: lines ,
        user_key,  # info: user_key ,
        "businesses",  # info: "businesses" ,
        bid,  # info: bid ,
        {  # info: {
            "id": bid,  # info: "id" : bid ,
            "user_id": user_key,  # info: "user_id" : user_key ,
            "name": "Root Record",  # info: "name" : "Root Record" ,
            "legal_name": "",  # info: "legal_name" : "" ,
            "owner": "",  # info: "owner" : "" ,
            "tax_id": "",  # info: "tax_id" : "" ,
            "email": "",  # info: "email" : "" ,
            "phone": "",  # info: "phone" : "" ,
            "website": "",  # info: "website" : "" ,
            "address": "",  # info: "address" : "" ,
            "timezone": "Pacific/Honolulu",  # info: "timezone" : "Pacific/Honolulu" ,
            "invoice_notes": "",  # info: "invoice_notes" : "" ,
            "is_default": True,  # info: "is_default" : True ,
            "created_at": now,  # info: "created_at" : now ,
            "updated_at": now,  # info: "updated_at" : now ,
        },  # info: } ,
        now,  # info: now ,
        now,  # info: now ,
    )  # info: )

    # --- settings
    emit_insert(  # info: call emit_insert
        lines,  # info: lines ,
        user_key,  # info: user_key ,
        "settings",  # info: "settings" ,
        "default",  # info: "default" ,
        {  # info: {
            "user_id": user_key,  # info: "user_id" : user_key ,
            "currency_default": "USD",  # info: "currency_default" : "USD" ,
            "theme": "dark",  # info: "theme" : "dark" ,
            "prompt_interval_sec": 900,  # info: "prompt_interval_sec" : 900 ,
            "prompt_first_delay_sec": 120,  # info: "prompt_first_delay_sec" : 120 ,
            "prompt_response_timeout_sec": 45,  # info: "prompt_response_timeout_sec" : 45 ,
            "default_hourly_cents": 0,  # info: "default_hourly_cents" : 0 ,
            "show_money_in_dashboard": True,  # info: "show_money_in_dashboard" : True ,
            "help_bubbles_enabled": True,  # info: "help_bubbles_enabled" : True ,
            "business_timezone": "Pacific/Honolulu",  # info: "business_timezone" : "Pacific/Honolulu" ,
            "active_business_id": bid,  # info: "active_business_id" : bid ,
            "updated_at": now,  # info: "updated_at" : now ,
        },  # info: } ,
        now,  # info: now ,
        now,  # info: now ,
    )  # info: )

    # --- categories (no Planning — former planning time split across Dev / Test / Doc / Research only)
    cat_specs: List[Tuple[str, str, int, int]] = [  # info: set cat_specs
        ("Development", "#339af0", 1, 0),
        ("Testing", "#2B8A8F", 1, 2000),
        ("Documentation", "#12b886", 1, 3000),
        ("Research", "#1f6aa5", 1, 4000),
        ("Admin", "#7950F2", 1, 5000),
        ("Break", "#FF0000", 0, 6000),
    ]  # info: ]
    cat_id: Dict[str, str] = {}  # info: set cat_id
    for name, color, billable, so in cat_specs:  # info: for name , color , billable , so
        cid = stable("cat", user_key, name)  # info: set cid
        cat_id[name] = cid  # info: cat_id [ name ] = cid
        emit_insert(  # info: call emit_insert
            lines,  # info: lines ,
            user_key,  # info: user_key ,
            "categories",  # info: "categories" ,
            cid,  # info: cid ,
            {  # info: {
                "id": cid,  # info: "id" : cid ,
                "user_id": user_key,  # info: "user_id" : user_key ,
                "name": name,  # info: "name" : name ,
                "color": color,  # info: "color" : color ,
                "icon": "",  # info: "icon" : "" ,
                "kind": "time",  # info: "kind" : "time" ,
                "billable": billable,  # info: "billable" : billable ,
                "archived": 0,  # info: "archived" : 0 ,
                "sort_order": so,  # info: "sort_order" : so ,
                "default_hourly_cents": None,  # info: "default_hourly_cents" : None ,
                "created_at": now,  # info: "created_at" : now ,
                "updated_at": now,  # info: "updated_at" : now ,
            },  # info: } ,
            now,  # info: now ,
            now,  # info: now ,
        )  # info: )

    # --- projects
    proj_specs = [  # info: set proj_specs
        ("Root Record Business Manager", "Root Record"),  # info: call (
        ("Root Record Weather Manager", ""),  # info: call (
        ("Overall Operations", ""),  # info: call (
    ]  # info: ]
    proj_id: Dict[str, str] = {}  # info: set proj_id
    for pname, client in proj_specs:  # info: for pname , client in proj_specs :
        pid = stable("proj", user_key, pname)  # info: set pid
        proj_id[pname] = pid  # info: proj_id [ pname ] = pid
        emit_insert(  # info: call emit_insert
            lines,  # info: lines ,
            user_key,  # info: user_key ,
            "projects",  # info: "projects" ,
            pid,  # info: pid ,
            {  # info: {
                "id": pid,  # info: "id" : pid ,
                "user_id": user_key,  # info: "user_id" : user_key ,
                "name": pname,  # info: "name" : pname ,
                "client_name": client,  # info: "client_name" : client ,
                "color": "#5C4D7D",
                "default_hourly_cents": None,  # info: "default_hourly_cents" : None ,
                "currency": "USD",  # info: "currency" : "USD" ,
                "notes": "",  # info: "notes" : "" ,
                "archived": 0,  # info: "archived" : 0 ,
                "sort_order": 999,  # info: "sort_order" : 999 ,
                "created_at": now,  # info: "created_at" : now ,
                "updated_at": now,  # info: "updated_at" : now ,
            },  # info: } ,
            now,  # info: now ,
            now,  # info: now ,
        )  # info: )

    # --- quick actions
    qa_specs = [  # info: set qa_specs
        ("Deep work", "Development", "Heads-down implementation"),  # info: call (
        ("Day prep", "Development", "Scope, backlog, and first implementation slice"),  # info: call (
        ("Ship checklist", "Testing", "Pre-release verification"),  # info: call (
    ]  # info: ]
    for i, (label, cname, desc) in enumerate(qa_specs):  # info: for i , ( label , cname ,
        qid = stable("qa", user_key, label)  # info: set qid
        emit_insert(  # info: call emit_insert
            lines,  # info: lines ,
            user_key,  # info: user_key ,
            "quick_actions",  # info: "quick_actions" ,
            qid,  # info: qid ,
            {  # info: {
                "id": qid,  # info: "id" : qid ,
                "user_id": user_key,  # info: "user_id" : user_key ,
                "label": label,  # info: "label" : label ,
                "category_id": cat_id[cname],  # info: "category_id" : cat_id [ cname ] ,
                "project_id": proj_id["Root Record Business Manager"],  # info: "project_id" : proj_id [ "Root Record Business Manager" ] ,
                "default_description": desc,  # info: "default_description" : desc ,
                "sort_order": i * 100,  # info: "sort_order" : i * 100 ,
                "created_at": now,  # info: "created_at" : now ,
                "updated_at": now,  # info: "updated_at" : now ,
            },  # info: } ,
            now,  # info: now ,
            now,  # info: now ,
        )  # info: )

    # --- time: April 2026 + May 1 HST; skip Sundays
    _, last_day = monthrange(YEAR, MONTH)  # info: _ , last_day = monthrange ( YEAR ,
    work_dates: List[date] = []  # info: set work_dates
    for day in range(1, last_day + 1):  # info: for day in range ( 1 , last_day
        dd = date(YEAR, MONTH, day)  # info: set dd
        if dd.weekday() != 6:  # info: if dd . weekday ( ) != 6
            work_dates.append(dd)  # info: work_dates . append ( dd )
    if D_MAY1.weekday() != 6:  # info: if D_MAY1 . weekday ( ) != 6
        work_dates.append(D_MAY1)  # info: work_dates . append ( D_MAY1 )
    # Work-only rotation (natural solo flow). Breaks are injected separately as 15m entries, not in this list.
    workflow = [  # info: set workflow
        ("Development", "Root Record Business Manager", "Warm-up: scope and first changes"),  # info: call (
        ("Development", "Root Record Business Manager", "Main implementation block"),  # info: call (
        ("Testing", "Root Record Business Manager", "Regression on recent changes"),  # info: call (
        ("Documentation", "Root Record Business Manager", "Notes while context is fresh"),  # info: call (
        ("Research", "Root Record Business Manager", "Spike or API / library check"),  # info: call (
        ("Development", "Root Record Weather Manager", "Weather pipeline or alerts"),  # info: call (
        ("Development", "Root Record Business Manager", "Integration and follow-on fixes"),  # info: call (
        ("Testing", "Root Record Business Manager", "Broader pass / edge cases"),  # info: call (
        ("Documentation", "Root Record Business Manager", "Runbooks and release notes"),  # info: call (
        ("Development", "Root Record Business Manager", "Late polish and hardening"),  # info: call (
        ("Admin", "Root Record Business Manager", "Inbox and loose ends"),  # info: call (
    ]  # info: ]

    def pick_project(weights: List[Tuple[str, float]]) -> str:  # info: def pick_project
        names = [w[0] for w in weights]  # info: set names
        ws = [w[1] for w in weights]  # info: set ws
        return rng.choices(names, weights=ws, k=1)[0]  # info: return rng . choices ( names , weights

    total_productive_minutes = 0  # info: set total_productive_minutes
    work_days = 0  # info: set work_days

    nosleep_notes = [  # info: set nosleep_notes
        "Overnight push — still up",  # info: "Overnight push — still up" ,
        "No sleep between days; kept going",  # info: "No sleep between days; kept going" ,
        "Late merge after long stretch",  # info: "Late merge after long stretch" ,
        "Powering through the night",  # info: "Powering through the night" ,
        "Coffee + code (no shutdown)",  # info: "Coffee + code (no shutdown)" ,
    ]  # info: ]

    for d in work_dates:  # info: for d in work_dates :
        work_days += 1  # info: set work_days

        if d in D_NOSLEEP:  # info: if d in D_NOSLEEP :
            # Apr 29–30: awake across calendar days — early start, long span, heavy hours, rare breaks.
            if d == date(2026, 4, 29):  # info: if d == date ( 2026 , 4
                day_start = datetime.combine(  # info: set day_start
                    d,  # info: d ,
                    time(hour=rng.randint(1, 4), minute=rng.randint(0, 55), second=rng.randint(0, 59)),  # info: call time
                    tzinfo=HST,  # info: set tzinfo
                )  # info: )
                close_hst = datetime.combine(  # info: set close_hst
                    date(2026, 4, 30),  # info: call date
                    time(hour=rng.randint(3, 5), minute=rng.randint(0, 55), second=rng.randint(0, 59)),  # info: call time
                    tzinfo=HST,  # info: set tzinfo
                )  # info: )
            else:  # info: else :
                # Start after the prior night’s tail (avoid overlapping Apr 29 entries that end pre-dawn Apr 30).
                day_start = datetime.combine(  # info: set day_start
                    d,  # info: d ,
                    time(hour=rng.randint(6, 8), minute=rng.randint(0, 50), second=rng.randint(0, 59)),  # info: call time
                    tzinfo=HST,  # info: set tzinfo
                )  # info: )
                close_hst = datetime.combine(  # info: set close_hst
                    date(2026, 5, 1),  # info: call date
                    time(hour=rng.randint(3, 4), minute=rng.randint(10, 55), second=rng.randint(0, 59)),  # info: call time
                    tzinfo=HST,  # info: set tzinfo
                )  # info: )
            productive_target = rng.randint(780, 900)  # info: set productive_target
            break_prob_scale = 0.22  # info: set break_prob_scale
        elif d == D_MAY1:  # info: elif d == D_MAY1 :
            # May 1: actually up at ~5am HST after the no-sleep stretch.
            day_start = datetime.combine(  # info: set day_start
                d,  # info: d ,
                time(hour=5, minute=rng.randint(0, 12), second=rng.randint(0, 59)),  # info: call time
                tzinfo=HST,  # info: set tzinfo
            )  # info: )
            close_hst = datetime.combine(  # info: set close_hst
                d + timedelta(days=1),  # info: d + timedelta ( days = 1 )
                time(hour=rng.randint(2, 3), minute=rng.randint(0, 55), second=rng.randint(0, 59)),  # info: call time
                tzinfo=HST,  # info: set tzinfo
            )  # info: )
            productive_target = rng.randint(540, 660)  # info: set productive_target
            break_prob_scale = 1.0  # info: set break_prob_scale
        else:  # info: else :
            productive_target = rng.randint(600, 720)  # info: set productive_target
            day_start = datetime.combine(  # info: set day_start
                d,  # info: d ,
                time(hour=12, minute=rng.randint(0, 40), second=rng.randint(0, 59)),  # info: call time
                tzinfo=HST,  # info: set tzinfo
            )  # info: )
            close_hst = datetime.combine(  # info: set close_hst
                d + timedelta(days=1),  # info: d + timedelta ( days = 1 )
                time(hour=rng.randint(2, 3), minute=rng.randint(0, 55), second=rng.randint(0, 59)),  # info: call time
                tzinfo=HST,  # info: set tzinfo
            )  # info: )
            break_prob_scale = 1.0  # info: set break_prob_scale

        total_productive_minutes += productive_target  # info: set total_productive_minutes

        cursor = day_start  # info: set cursor
        productive_done = 0  # info: set productive_done
        minutes_since_break = 0  # info: set minutes_since_break
        seg_idx = 0  # info: set seg_idx
        first_seg = True  # info: set first_seg
        break_idx = 0  # info: set break_idx

        desc_pool = {  # info: set desc_pool
            "Development": [  # info: "Development" : [
                "Feature implementation",  # info: "Feature implementation" ,
                "Bugfix and hardening",  # info: "Bugfix and hardening" ,
                "Integration work",  # info: "Integration work" ,
                "Refactor for maintainability",  # info: "Refactor for maintainability" ,
                "Local build iteration",  # info: "Local build iteration" ,
                "Environment config",  # info: "Environment config" ,
                "CLI and tooling work",  # info: "CLI and tooling work" ,
                "Scope check before deeper coding",  # info: "Scope check before deeper coding" ,
                "Backlog grooming turned into tasks",  # info: "Backlog grooming turned into tasks" ,
            ],  # info: ] ,
            "Testing": [  # info: "Testing" : [
                "Manual test pass",  # info: "Manual test pass" ,
                "Scenario validation",  # info: "Scenario validation" ,
                "Release smoke tests",  # info: "Release smoke tests" ,
                "End-to-end path checks",  # info: "End-to-end path checks" ,
                "Test cases from acceptance notes",  # info: "Test cases from acceptance notes" ,
            ],  # info: ] ,
            "Break": [  # info: "Break" : [
                "Break (15m)",  # info: "Break (15m)" ,
                "Stretch / snack",  # info: "Stretch / snack" ,
                "Away from keyboard",  # info: "Away from keyboard" ,
                "Quick reset",  # info: "Quick reset" ,
            ],  # info: ] ,
            "Documentation": [  # info: "Documentation" : [
                "Update internal docs",  # info: "Update internal docs" ,
                "Runbook and deployment notes",  # info: "Runbook and deployment notes" ,
                "API and schema notes",  # info: "API and schema notes" ,
                "Roadmap alignment captured in docs",  # info: "Roadmap alignment captured in docs" ,
                "Design notes for the next milestone",  # info: "Design notes for the next milestone" ,
            ],  # info: ] ,
            "Research": [  # info: "Research" : [
                "Evaluate library / approach",  # info: "Evaluate library / approach" ,
                "Prototype spike",  # info: "Prototype spike" ,
                "Architecture comparison",  # info: "Architecture comparison" ,
                "Feasibility check before commit",  # info: "Feasibility check before commit" ,
            ],  # info: ] ,
            "Admin": [  # info: "Admin" : [
                "Email and calendar",  # info: "Email and calendar" ,
                "Ticket hygiene",  # info: "Ticket hygiene" ,
            ],  # info: ] ,
        }  # info: }

        def emit_segment(  # info: def emit_segment
            wname: str,  # info: set wname
            proj_name: str,  # info: set proj_name
            m: int,  # info: set m
            seg_tag: str,  # info: set seg_tag
        ) -> None:  # info: ) -> None :
            nonlocal cursor  # info: nonlocal cursor
            start = cursor  # info: set start
            end = start + timedelta(minutes=m)  # info: set end
            cursor = end  # info: set cursor
            desc = rng.choice(desc_pool.get(wname, ["Focused work"]))  # info: set desc
            if d in D_NOSLEEP and wname != "Break" and rng.random() < 0.42:  # info: if d in D_NOSLEEP and wname != "Break"
                desc = rng.choice(nosleep_notes) + " — " + desc  # info: set desc
            elif d == D_MAY1 and wname != "Break" and rng.random() < 0.38:  # info: elif d == D_MAY1 and wname != "Break"
                desc = "Up ~5am — " + desc  # info: set desc
            tid = stable("time", user_key, d.isoformat(), seg_tag, str(m), str(rng.randint(0, 9999)))  # info: set tid
            doc = {  # info: set doc
                "id": tid,  # info: "id" : tid ,
                "user_id": user_key,  # info: "user_id" : user_key ,
                "start_utc": fmt_z(start),  # info: "start_utc" : fmt_z ( start ) ,
                "end_utc": fmt_z(end),  # info: "end_utc" : fmt_z ( end ) ,
                "category_id": cat_id[wname],  # info: "category_id" : cat_id [ wname ] ,
                "project_id": proj_id[proj_name],  # info: "project_id" : proj_id [ proj_name ] ,
                "description": desc,  # info: "description" : desc ,
                "source": "manual",  # info: "source" : "manual" ,
                "created_at": fmt_z(end),  # info: "created_at" : fmt_z ( end ) ,
                "updated_at": fmt_z(end),  # info: "updated_at" : fmt_z ( end ) ,
            }  # info: }
            emit_insert(lines, user_key, "time_entries", tid, doc, fmt_z(end), fmt_z(end))  # info: call emit_insert

        for _ in range(120):  # info: for _ in range ( 120 ) :
            if productive_done >= productive_target:  # info: if productive_done >= productive_target :
                break  # info: break
            still = productive_target - productive_done  # info: set still
            slot_left = int((close_hst - cursor).total_seconds() // 60)  # info: set slot_left
            if slot_left < 12:  # info: if slot_left < 12 :
                break  # info: break

            if not first_seg:  # info: if not first_seg :
                micro = rng.randint(0, 6)  # info: set micro
                micro = min(micro, max(0, slot_left - 12))  # info: set micro
                if micro > 0:  # info: if micro > 0 :
                    cursor += timedelta(minutes=micro)  # info: set cursor
                slot_left = int((close_hst - cursor).total_seconds() // 60)  # info: set slot_left
            first_seg = False  # info: set first_seg
            if slot_left < 12:  # info: if slot_left < 12 :
                break  # info: break

            # Multiple 15m breaks per day, no cap — probability rises the longer since last break.
            if (  # info: if (
                productive_done > 0  # info: productive_done > 0
                and minutes_since_break >= 35  # info: and minutes_since_break >= 35
                and slot_left >= 18  # info: and slot_left >= 18
            ):  # info: ) :
                p_break = min(0.52, 0.16 + (minutes_since_break - 35) * 0.006) * break_prob_scale  # info: set p_break
                if rng.random() < p_break:  # info: if rng . random ( ) < p_break
                    break_idx += 1  # info: set break_idx
                    emit_segment(  # info: call emit_segment
                        "Break",  # info: "Break" ,
                        "Root Record Business Manager",  # info: "Root Record Business Manager" ,
                        15,  # info: 15 ,
                        f"brk{break_idx}",  # info: f" brk { break_idx } " ,
                    )  # info: )
                    minutes_since_break = 0  # info: set minutes_since_break
                    slot_left = int((close_hst - cursor).total_seconds() // 60)  # info: set slot_left
                    if slot_left < 12:  # info: if slot_left < 12 :
                        break  # info: break
                    continue  # info: continue

            wname, default_proj, _desc_template = workflow[seg_idx % len(workflow)]  # info: wname , default_proj , _desc_template = workflow [
            seg_idx += 1  # info: set seg_idx

            hi = min(150, still + 25, slot_left)  # info: set hi
            lo = min(45, hi)  # info: set lo
            if hi < 15:  # info: if hi < 15 :
                m = min(still, slot_left)  # info: set m
            elif still <= slot_left and still <= hi:  # info: elif still <= slot_left and still <= hi
                m = still  # info: set m
            else:  # info: else :
                m = rng.randint(lo, hi) if hi >= lo else min(still, slot_left)  # info: set m
            m = int(max(10, min(m, still, slot_left)))  # info: set m

            proj_name = default_proj  # info: set proj_name
            if wname == "Development" and rng.random() < 0.35:  # info: if wname == "Development" and rng . random
                proj_name = pick_project(  # info: set proj_name
                    [  # info: [
                        ("Root Record Business Manager", 0.55),  # info: call (
                        ("Root Record Weather Manager", 0.35),  # info: call (
                        ("Overall Operations", 0.1),  # info: call (
                    ]  # info: ]
                )  # info: )

            emit_segment(wname, proj_name, m, f"w{seg_idx}")  # info: call emit_segment
            productive_done += m  # info: set productive_done
            minutes_since_break += m  # info: set minutes_since_break

        # If breaks ate clock before hitting productive target, finish without more breaks.
        for _ in range(40):  # info: for _ in range ( 40 ) :
            if productive_done >= productive_target:  # info: if productive_done >= productive_target :
                break  # info: break
            still = productive_target - productive_done  # info: set still
            slot_left = int((close_hst - cursor).total_seconds() // 60)  # info: set slot_left
            if slot_left < 8:  # info: if slot_left < 8 :
                break  # info: break
            wname, default_proj, _ = workflow[seg_idx % len(workflow)]  # info: wname , default_proj , _ = workflow [
            seg_idx += 1  # info: set seg_idx
            m = int(max(10, min(still, slot_left)))  # info: set m
            proj_name = default_proj  # info: set proj_name
            if wname == "Development" and rng.random() < 0.35:  # info: if wname == "Development" and rng . random
                proj_name = pick_project(  # info: set proj_name
                    [  # info: [
                        ("Root Record Business Manager", 0.55),  # info: call (
                        ("Root Record Weather Manager", 0.35),  # info: call (
                        ("Overall Operations", 0.1),  # info: call (
                    ]  # info: ]
                )  # info: )
            emit_segment(wname, proj_name, m, f"t{seg_idx}")  # info: call emit_segment
            productive_done += m  # info: set productive_done
            minutes_since_break += m  # info: set minutes_since_break

    header = (  # info: set header
        "-- redesign_april_workflow_bm.py: Apr 2026 + May 1 HST (wipes time stack only; keeps income/expense)\n"  # info: "-- redesign_april_workflow_bm.py: Apr 2026 + May 1 HST (wipes time stack only; keeps income/expense)\n"
        f"-- user_key={user_key} | work_days={work_days} | "  # info: f" -- user_key= { user_key } | work_days= { work_days
        f"productive_minutes={total_productive_minutes} (~{total_productive_minutes / 60:.1f} h; breaks extra)\n"  # info: f" productive_minutes= { total_productive_minutes } (~ { total_productive_minutes
        "-- Apr 29-30: no-sleep arc (early start, long span). May 1: start ~5am HST.\n"  # info: "-- Apr 29-30: no-sleep arc (early start, long span). May 1: start ~5am HST.\n"
        "DELETE FROM bm_owned_row WHERE user_key = "  # info: "DELETE FROM bm_owned_row WHERE user_key = "
        + sql_escape(user_key)  # info: call +
        + " AND coll IN ("  # info: + " AND coll IN ("
        + ",".join(  # info: + "," . join (
            sql_escape(c)  # info: call sql_escape
            for c in (  # info: for c in (
                "businesses",  # info: "businesses" ,
                "settings",  # info: "settings" ,
                "categories",  # info: "categories" ,
                "projects",  # info: "projects" ,
                "quick_actions",  # info: "quick_actions" ,
                "time_entries",  # info: "time_entries" ,
            )  # info: )
        )  # info: )
        + ");"  # info: + ");"
    )  # info: )
    open(args.out, "w", encoding="utf-8").write(header + "\n" + "\n".join(lines) + "\n")  # info: call open
    print(  # info: call print
        f"Wrote {args.out} ({len(lines)} lines), ~{total_productive_minutes/60:.1f} productive hours "  # info: f" Wrote { args . out } (
        f"across {work_days} work days (incl. May 1)"  # info: f" across { work_days } work days (incl. May 1) "
    )  # info: )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    main()  # info: call main
