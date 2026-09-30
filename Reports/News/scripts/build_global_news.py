# ==============================================================================
# FILE: Reports/News/scripts/build_global_news.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""Build the global news index from state databases already on disk (WO-MIG-12).

Does not collect. Does not invent stories. Empty and missing states stay visible
in collection_health. locations stays empty until the country location pollers land.
Writes Database Reports/News/global/global-news-last.json. The job stays off
until RR_GLOBAL_NEWS=1 is registered in jobs.py.
"""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import sqlite3  # info: import sqlite3
import time  # info: import time
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
PORTALS_PATH = HERE.parent / 'config' / 'state_portals.json'  # info: set PORTALS_PATH
DB_ROOT = Path(os.environ.get('RR_DATABASE_ROOT', '/home/rootrecord/RootRecord-Ecosystem/2 - RootRecord-Database'))  # info: set DB_ROOT
NEWS_ROOT = DB_ROOT / 'Reports' / 'News'  # info: set NEWS_ROOT
OUT = NEWS_ROOT / 'global' / 'global-news-last.json'  # info: set OUT
LOG = DB_ROOT / 'Logs' / 'Reports' / 'News' / 'build-global-news-last.json'  # info: set LOG

# ====================================================
# SECTION: DISPLAY
# What it does: Set DISPLAY.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
DISPLAY = {  # info: set DISPLAY
    'new-york': 'New York', 'new-jersey': 'New Jersey',  # info: 'new-york' : 'New York' , 'new-jersey' : 'New Jersey' ,
    'north-carolina': 'North Carolina', 'south-carolina': 'South Carolina',  # info: 'north-carolina' : 'North Carolina' , 'south-carolina' : 'South Carolina' ,
    'north-dakota': 'North Dakota', 'south-dakota': 'South Dakota',  # info: 'north-dakota' : 'North Dakota' , 'south-dakota' : 'South Dakota' ,
    'west-virginia': 'West Virginia', 'new-mexico': 'New Mexico',  # info: 'west-virginia' : 'West Virginia' , 'new-mexico' : 'New Mexico' ,
    'rhode-island': 'Rhode Island', 'new-hampshire': 'New Hampshire',  # info: 'rhode-island' : 'Rhode Island' , 'new-hampshire' : 'New Hampshire' ,
}  # info: }
# ====================================================
# SECTION: STATE_CODES
# What it does: Set STATE_CODES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
STATE_CODES = {  # info: set STATE_CODES
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA', 'Colorado': 'CO',  # info: 'Alabama' : 'AL' , 'Alaska' : 'AK' ,
    'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',  # info: 'Connecticut' : 'CT' , 'Delaware' : 'DE' ,
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA',  # info: 'Illinois' : 'IL' , 'Indiana' : 'IN' ,
    'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',  # info: 'Maine' : 'ME' , 'Maryland' : 'MD' ,
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',  # info: 'Mississippi' : 'MS' , 'Missouri' : 'MO' ,
    'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',  # info: 'New Hampshire' : 'NH' , 'New Jersey' : 'NJ' ,
    'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',  # info: 'North Dakota' : 'ND' , 'Ohio' : 'OH' ,
    'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX',  # info: 'Rhode Island' : 'RI' , 'South Carolina' : 'SC' ,
    'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV',  # info: 'Utah' : 'UT' , 'Vermont' : 'VT' ,
    'Wisconsin': 'WI', 'Wyoming': 'WY',  # info: 'Wisconsin' : 'WI' , 'Wyoming' : 'WY' ,
}  # info: }
# ====================================================
# SECTION: REGION
# What it does: Set REGION.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
REGION = {  # info: set REGION
    'AL': 'south', 'AK': 'north-america', 'AZ': 'southwest', 'AR': 'south', 'CA': 'west', 'CO': 'west',  # info: 'AL' : 'south' , 'AK' : 'north-america' ,
    'CT': 'northeast', 'DE': 'northeast', 'FL': 'south', 'GA': 'south', 'HI': 'pacific', 'ID': 'west',  # info: 'CT' : 'northeast' , 'DE' : 'northeast' ,
    'IL': 'midwest', 'IN': 'midwest', 'IA': 'midwest', 'KS': 'midwest', 'KY': 'south', 'LA': 'south',  # info: 'IL' : 'midwest' , 'IN' : 'midwest' ,
    'ME': 'northeast', 'MD': 'northeast', 'MA': 'northeast', 'MI': 'midwest', 'MN': 'midwest', 'MS': 'south',  # info: 'ME' : 'northeast' , 'MD' : 'northeast' ,
    'MO': 'midwest', 'MT': 'west', 'NE': 'midwest', 'NV': 'west', 'NH': 'northeast', 'NJ': 'northeast',  # info: 'MO' : 'midwest' , 'MT' : 'west' ,
    'NM': 'southwest', 'NY': 'northeast', 'NC': 'south', 'ND': 'midwest', 'OH': 'midwest', 'OK': 'south',  # info: 'NM' : 'southwest' , 'NY' : 'northeast' ,
    'OR': 'west', 'PA': 'northeast', 'RI': 'northeast', 'SC': 'south', 'SD': 'midwest', 'TN': 'south',  # info: 'OR' : 'west' , 'PA' : 'northeast' ,
    'TX': 'south', 'UT': 'west', 'VT': 'northeast', 'VA': 'south', 'WA': 'west', 'WV': 'south',  # info: 'TX' : 'south' , 'UT' : 'west' ,
    'WI': 'midwest', 'WY': 'west',  # info: 'WI' : 'midwest' , 'WY' : 'west' ,
}  # info: }
# ====================================================
# SECTION: WEIGHTS
# What it does: Set WEIGHTS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
WEIGHTS = {  # info: set WEIGHTS
    'emergency': 100, 'hazards': 100, 'health': 85, 'government': 80, 'science': 70,  # info: 'emergency' : 100 , 'hazards' : 100 ,
    'environment': 70, 'infrastructure': 65, 'utilities': 65, 'education': 55,  # info: 'environment' : 70 , 'infrastructure' : 65 ,
    'business': 50, 'community': 45, 'culture': 45, 'events': 35,  # info: 'business' : 50 , 'community' : 45 ,
}  # info: }


# ====================================================
# SECTION: function score
# What it does: score.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def score(category) -> int:  # info: def score
    c = (category or 'general').lower()  # info: set c
    for key, weight in WEIGHTS.items():  # info: for key , weight in WEIGHTS . items
        if key in c:  # info: if key in c :
            return weight  # info: return weight
    return 40  # info: return 40


# ====================================================
# SECTION: function parse_ts
# What it does: parse ts.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def parse_ts(value) -> int:  # info: def parse_ts
    if not value:  # info: if not value :
        return 0  # info: return 0
    text = str(value)  # info: set text
    for fmt, n in (('%Y-%m-%dT%H:%M:%S', 19), ('%Y-%m-%d', 10)):  # info: for fmt , n in ( ( '%Y-%m-%dT%H:%M:%S'
        try:  # info: try :
            return int(time.mktime(time.strptime(text[:n], fmt)))  # info: return int ( time . mktime ( time
        except Exception:  # info: except Exception :
            continue  # info: continue
    return 0  # info: return 0


# ====================================================
# SECTION: function display_name
# What it does: display name.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def display_name(slug: str) -> str:  # info: def display_name
    return DISPLAY.get(slug, slug.replace('-', ' ').title())  # info: return DISPLAY . get ( slug , slug


# ====================================================
# SECTION: function db_health
# What it does: db health.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def db_health(path: Path) -> dict:  # info: def db_health
    result = {'database': str(path), 'posts': 0, 'events': 0, 'sources': 0, 'source_health': {}}  # info: set result
    try:  # info: try :
        con = sqlite3.connect(path)  # info: set con
        result['posts'] = con.execute('select count(*) from posts').fetchone()[0]  # info: result [ 'posts' ] = con . execute
        result['events'] = con.execute('select count(*) from events').fetchone()[0]  # info: result [ 'events' ] = con . execute
        result['sources'] = con.execute('select count(*) from sources').fetchone()[0]  # info: result [ 'sources' ] = con . execute
        try:  # info: try :
            for status, count in con.execute('select status,count(*) from source_health group by status'):  # info: for status , count in con . execute
                result['source_health'][status] = count  # info: result [ 'source_health' ] [ status ] =
        except sqlite3.Error:  # info: except sqlite3 . Error :
            pass  # info: pass
        con.close()  # info: con . close ( )
    except sqlite3.Error as exc:  # info: except sqlite3 . Error as exc :
        result['error'] = str(exc)  # info: result [ 'error' ] = str ( exc
    return result  # info: return result


# ====================================================
# SECTION: function read_db
# What it does: read db.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def read_db(path: Path, slug: str):  # info: def read_db
    con = sqlite3.connect(path)  # info: set con
    con.row_factory = sqlite3.Row  # info: con . row_factory = sqlite3 . Row
    posts, events = [], []  # info: posts , events = [ ] , [
    st = display_name(slug)  # info: set st
    code = STATE_CODES.get(st)  # info: set code
    region = REGION.get(code, 'north-america')  # info: set region
    try:  # info: try :
        for r in con.execute('select p.*, s.publisher from posts p left join sources s on p.source_id=s.source_id'):  # info: for r in con . execute ( 'select p.*, s.publisher from posts p left join sources s on p.source_id=s.source_id'
            posts.append({  # info: posts . append ( {
                'title': r['title'], 'summary': r['summary'], 'link': r['url'],  # info: 'title' : r [ 'title' ] , 'summary'
                'published_label': r['published_at'], 'published_ts': parse_ts(r['published_at']),  # info: 'published_label' : r [ 'published_at' ] , 'published_ts'
                'category': r['category'] or 'general',  # info: 'category' : r [ 'category' ] or 'general'
                'category_label': (r['category'] or 'General').replace('-', ' ').title(),  # info: call 'category_label'
                'source_id': r['source_id'], 'source': r['publisher'] or r['source_id'] or 'Source',  # info: 'source_id' : r [ 'source_id' ] , 'source'
                'country_code': 'US', 'region': region,  # info: 'country_code' : 'US' , 'region' : region ,
                'state_code': code, 'state_name': st, 'location': None,  # info: 'state_code' : code , 'state_name' : st ,
                'importance': score(r['category']),  # info: 'importance' : score ( r [ 'category' ]
            })  # info: } )
        for r in con.execute('select e.*, s.publisher from events e left join sources s on e.source_id=s.source_id'):  # info: for r in con . execute ( 'select e.*, s.publisher from events e left join sources s on e.source_id=s.source_id
            events.append({  # info: events . append ( {
                'title': r['title'], 'description': r['description'], 'link': r['url'],  # info: 'title' : r [ 'title' ] , 'description'
                'start_label': r['start_at'], 'start_ts': parse_ts(r['start_at']),  # info: 'start_label' : r [ 'start_at' ] , 'start_ts'
                'location': r['location'], 'type': r['category'] or 'Event',  # info: 'location' : r [ 'location' ] , 'type'
                'source': r['publisher'] or r['source_id'] or 'Source',  # info: 'source' : r [ 'publisher' ] or r
                'state_code': code, 'state_name': st, 'country_code': 'US', 'region': region,  # info: 'state_code' : code , 'state_name' : st ,
            })  # info: } )
    finally:  # info: finally :
        con.close()  # info: con . close ( )
    return posts, events  # info: return posts , events


# ====================================================
# SECTION: function write_json
# What it does: write json.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def write_json(path: Path, payload: dict) -> None:  # info: def write_json
    path.parent.mkdir(parents=True, exist_ok=True)  # info: path . parent . mkdir ( parents =
    tmp = path.with_suffix(path.suffix + '.tmp')  # info: set tmp
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')  # info: tmp . write_text ( json . dumps (
    os.replace(tmp, path)  # info: os . replace ( tmp , path )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    portals = json.loads(PORTALS_PATH.read_text(encoding='utf-8'))  # info: set portals
    items, ev, health = [], [], []  # info: items , ev , health = [ ]
    for slug in sorted(portals):  # info: for slug in sorted ( portals ) :
        db = NEWS_ROOT / slug / f'{slug}_news.db'  # info: set db
        if not db.is_file():  # info: if not db . is_file ( ) :
            health.append({'state': slug, 'database': None, 'posts': 0, 'events': 0, 'sources': 0, 'status': 'missing_database'})  # info: health . append ( { 'state' : slug
            continue  # info: continue
        h = db_health(db)  # info: set h
        h.update({'state': slug, 'status': 'ok' if h['posts'] or h['events'] else 'empty'})  # info: h . update ( { 'state' : slug
        health.append(h)  # info: health . append ( h )
        if h.get('error'):  # info: if h . get ( 'error' ) :
            continue  # info: continue
        p, e = read_db(db, slug)  # info: p , e = read_db ( db ,
        items.extend(p)  # info: items . extend ( p )
        ev.extend(e)  # info: ev . extend ( e )
    uniq = {x['link']: x for x in items if x.get('link')}  # info: set uniq
    items = sorted(uniq.values(), key=lambda x: (x['importance'], x['published_ts']), reverse=True)  # info: set items
    ev = sorted(  # info: set ev
        {(x['title'], x.get('start_label'), x.get('link')): x for x in ev}.values(),  # info: call {
        key=lambda x: x.get('start_ts', 0),  # info: set key
    )  # info: )
    payload = {  # info: set payload
        'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),  # info: 'generated_at' : datetime . now ( ) .
        'items': items[:5000],  # info: 'items' : items [ : 5000 ] ,
        'events': ev[:1000],  # info: 'events' : ev [ : 1000 ] ,
        'collection_health': health,  # info: 'collection_health' : health ,
        'locations': [],  # info: 'locations' : [ ] ,
    }  # info: }
    write_json(OUT, payload)  # info: call write_json
    write_json(LOG, {  # info: call write_json
        'at': payload['generated_at'],  # info: 'at' : payload [ 'generated_at' ] ,
        'posts': len(items),  # info: 'posts' : len ( items ) ,
        'events': len(ev),  # info: 'events' : len ( ev ) ,
        'states': len(health),  # info: 'states' : len ( health ) ,
        'out': str(OUT),  # info: 'out' : str ( OUT ) ,
    })  # info: } )
    print(f'global news index: {len(items)} posts, {len(ev)} events, {len(health)} states -> {OUT}')  # info: call print
    for h in health:  # info: for h in health :
        print(f"  {h.get('state')}: {h.get('status')} posts={h.get('posts', 0)} events={h.get('events', 0)}")  # info: call print
    return 0  # info: return 0


if __name__ == '__main__':  # info: if __name__ == '__main__' :
    raise SystemExit(main())  # info: raise SystemExit ( main ( ) )
