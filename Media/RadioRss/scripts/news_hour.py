# ==============================================================================
# FILE: Media/RadioRss/scripts/news_hour.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Hourly five-minute news update. Ava, Bruce, and Carly rotate by the Hawaii hour."""
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import os  # info: import os
import shutil  # info: import shutil
import subprocess  # info: import subprocess
import sys  # info: import sys
import tempfile  # info: import tempfile
from datetime import datetime, timedelta, timezone  # info: from datetime import datetime , timedelta , timezone
from pathlib import Path  # info: from pathlib import Path
from zoneinfo import ZoneInfo  # info: from zoneinfo import ZoneInfo

from common import DB, PACIFIC, iso, parse_iso, utc_now  # info: from common import DB , PACIFIC , iso , parse_iso , utc_now
from pipeline import _publisher, _summary, _when, poll_feed  # info: from pipeline import _publisher , _summary , _when , poll_feed
from registry import configured_on  # info: from registry import configured_on

HST = ZoneInfo("Pacific/Honolulu")  # info: set HST
RANK = {"urgent": 4, "high": 3, "normal": 2, "low": 1}  # info: set RANK
VOICE_DIR = DB / "Media" / "Audio" / "Voice"  # info: set VOICE_DIR
REPORT_TEXT = DB.parent / "test-reports" / "Voice"  # info: set REPORT_TEXT


# ====================================================
# SECTION: function _words
# What it does: Count words in one spoken line.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _words(text: str) -> int:  # info: def _words
    return len([part for part in (text or "").split() if part])  # info: return len ( [ part for part in ( text or "" ) . split ( ) if part ] )


# ====================================================
# SECTION: function _cfg
# What it does: Return the news_update block from policy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _cfg(registry: dict) -> dict:  # info: def _cfg
    block = registry["policy"].get("news_update") or {}  # info: set block
    return block if isinstance(block, dict) else {}  # info: return block if isinstance ( block , dict ) else { }


# ====================================================
# SECTION: function persona_for
# What it does: Leapfrog Ava, Bruce, and Carly. The Hawaii hour picks the first desk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def persona_for(hour: int, index: int, roster: tuple[str, ...]) -> str:  # info: def persona_for
    names = roster or ("ava", "bruce", "carly")  # info: set names
    return names[(int(hour) + int(index)) % len(names)]  # info: return names [ ( int ( hour ) + int ( index ) ) % len ( names ) ]


# ====================================================
# SECTION: function _recent
# What it does: True when a story was published inside the hour window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _recent(story: dict, now: datetime, hours: float) -> bool:  # info: def _recent
    stamp = parse_iso(story.get("published_at") or "") or parse_iso(story.get("first_seen_at") or "")  # info: set stamp
    if stamp is None:  # info: if stamp is None :
        return True  # info: return True
    return stamp >= now - timedelta(hours=hours)  # info: return stamp >= now - timedelta ( hours = hours )


# ====================================================
# SECTION: function _line
# What it does: One attributed sentence. The wording stays the publisher's account.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _line(story: dict, registry: dict) -> str:  # info: def _line
    spoken = _publisher(story.get("provider") or "", registry["policy"])  # info: set spoken
    body = _summary(story.get("summary") or "", registry["policy"])  # info: set body
    line = f"{spoken} reports that {story.get('title') or 'an update'}."  # info: set line
    if body:  # info: if body :
        line = f"{line} {body}"  # info: set line
    line = f"{line} Published {_when(story.get('published_at') or '')}."  # info: set line
    return line  # info: return line


# ====================================================
# SECTION: function _ordered
# What it does: Urgent and newer stories come first inside one desk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _ordered(stories: list[dict]) -> list[dict]:  # info: def _ordered
    return sorted(stories, key=lambda story: (RANK.get(story.get("priority") or "normal", 2), story.get("published_at") or ""), reverse=True)  # info: return sorted ( stories , key = lambda story : ( RANK . get ( story . get ( "priority" ) or "normal" , 2 ) , story . get ( "published_at" ) or "" ) , reverse = True )


# ====================================================
# SECTION: function _take
# What it does: Fill one desk up to a word budget. The same cluster is read once.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _take(stories: list[dict], categories: list, budget: int, registry: dict, seen: set) -> tuple[list[str], list[dict], int]:  # info: def _take
    lines = []  # info: set lines
    picked = []  # info: set picked
    used = 0  # info: set used
    wanted = set(categories or [])  # info: set wanted
    for story in _ordered(stories):  # info: for story in _ordered ( stories )
        if story.get("category") not in wanted:  # info: if story . get ( "category" ) not in wanted :
            continue  # info: continue
        key = story.get("cluster_id") or story.get("canonical_url") or story.get("id")  # info: set key
        if not key or key in seen:  # info: if not key or key in seen :
            continue  # info: continue
        line = _line(story, registry)  # info: set line
        count = _words(line)  # info: set count
        if used and used + count > budget:  # info: if used and used + count > budget :
            continue  # info: continue
        if not used and count > budget:  # info: if not used and count > budget :
            short = line.split(". ")[0].strip()  # info: set short
            if not short.endswith("."):  # info: if not short . endswith ( "." ) :
                short += "."  # info: set short
            line = short  # info: set line
            count = _words(line)  # info: set count
            if count > budget:  # info: if count > budget :
                continue  # info: continue
        lines.append(line)  # info: lines . append ( line )
        picked.append(story)  # info: picked . append ( story )
        seen.add(key)  # info: seen . add ( key )
        used += count  # info: set used
        if used >= budget:  # info: if used >= budget :
            break  # info: break
    return lines, picked, used  # info: return lines , picked , used


# ====================================================
# SECTION: function _desk_lines
# What it does: Prefer the fresh window, then older items when the desk is still thin.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _desk_lines(desk: dict, fresh: list[dict], older: list[dict], budget: int, registry: dict, seen: set) -> tuple[list[str], list[dict]]:  # info: def _desk_lines
    categories = list(desk.get("categories") or [])  # info: set categories
    lines, picked, used = _take(fresh, categories, budget, registry, seen)  # info: lines , picked , used = _take ( fresh , categories , budget , registry , seen )
    if used < min(40, budget):  # info: if used < min ( 40 , budget ) :
        more, more_picked, _more_used = _take(older, categories, budget - used, registry, seen)  # info: more , more_picked , _more_used = _take ( older , categories , budget - used , registry , seen )
        lines.extend(more)  # info: lines . extend ( more )
        picked.extend(more_picked)  # info: picked . extend ( more_picked )
    return lines, picked  # info: return lines , picked


# ====================================================
# SECTION: function build_update
# What it does: Write the desks for one hour. The first voice follows the Hawaii hour.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_update(stories: list[dict], registry: dict, when: datetime) -> dict:  # info: def build_update
    cfg = _cfg(registry)  # info: set cfg
    roster = tuple(str(name) for name in (cfg.get("roster") or ["ava", "bruce", "carly"]))  # info: set roster
    local = when.astimezone(HST)  # info: set local
    now = when.astimezone(timezone.utc)  # info: set now
    fresh_hours = float(cfg.get("fresh_hours") or 18)  # info: set fresh_hours
    backfill_hours = float(cfg.get("backfill_hours") or 36)  # info: set backfill_hours
    desk_words = int(cfg.get("desk_words") or 150)  # info: set desk_words
    target = int(cfg.get("target_words") or 750)  # info: set target
    fresh = [story for story in stories if _recent(story, now, fresh_hours)]  # info: set fresh
    older = [story for story in stories if _recent(story, now, backfill_hours)]  # info: set older
    desks = [desk for desk in (cfg.get("desks") or []) if isinstance(desk, dict)]  # info: set desks
    primary = [desk for desk in desks if not desk.get("fill")]  # info: set primary
    fill = next((desk for desk in desks if desk.get("fill")), None)  # info: set fill
    opener = f"RootRecord news update for {local.strftime('%B')} {local.day}, {local.year}."  # info: set opener
    seen: set = set()  # info: set seen
    sections = []  # info: set sections
    for index, desk in enumerate(primary):  # info: for index , desk in enumerate ( primary )
        lead = str(desk.get("lead") or desk.get("name") or "News.")  # info: set lead
        overhead = _words(lead) + (_words(opener) if index == 0 else 0)  # info: set overhead
        budget = max(24, desk_words - overhead)  # info: set budget
        lines, picked = _desk_lines(desk, fresh, older, budget, registry, seen)  # info: lines , picked = _desk_lines ( desk , fresh , older , budget , registry , seen )
        if not lines:  # info: if not lines :
            lines = [f"No fresh items on the {desk.get('name') or 'news'} desk."]  # info: set lines
        parts = [lead, *lines]  # info: set parts
        if index == 0:  # info: if index == 0 :
            parts = [opener, *parts]  # info: set parts
        if any(story.get("political") for story in picked):  # info: if any ( story . get ( "political" ) for story in picked ) :
            parts.append("The claims in this desk are the publisher's.")  # info: parts . append ( "The claims in this desk are the publisher's." )
        sections.append({  # info: sections . append ( {
            "id": desk.get("id") or "desk",  # info: "id" : desk . get ( "id" ) or "desk" ,
            "persona": persona_for(local.hour, index, roster),  # info: "persona" : persona_for ( local . hour , index , roster ) ,
            "text": " ".join(parts),  # info: "text" : " " . join ( parts ) ,
            "sources": [_source(story) for story in picked],  # info: "sources" : [ _source ( story ) for story in picked ] ,
        })  # info: } )
    spent = sum(_words(section["text"]) for section in sections)  # info: set spent
    if fill is not None and target - spent > 40:  # info: if fill is not None and target - spent > 40 :
        lead = str(fill.get("lead") or "Also in the news.")  # info: set lead
        budget = max(24, target - spent - _words(lead) - 6)  # info: set budget
        lines, picked = _desk_lines(fill, fresh, older, budget, registry, seen)  # info: lines , picked = _desk_lines ( fill , fresh , older , budget , registry , seen )
        if lines:  # info: if lines :
            parts = [lead, *lines]  # info: set parts
            if any(story.get("political") for story in picked):  # info: if any ( story . get ( "political" ) for story in picked ) :
                parts.append("The claims in this desk are the publisher's.")  # info: parts . append ( "The claims in this desk are the publisher's." )
            sections.append({  # info: sections . append ( {
                "id": fill.get("id") or "also",  # info: "id" : fill . get ( "id" ) or "also" ,
                "persona": persona_for(local.hour, len(sections), roster),  # info: "persona" : persona_for ( local . hour , len ( sections ) , roster ) ,
                "text": " ".join(parts),  # info: "text" : " " . join ( parts ) ,
                "sources": [_source(story) for story in picked],  # info: "sources" : [ _source ( story ) for story in picked ] ,
            })  # info: } )
    if sections:  # info: if sections :
        sections[-1]["text"] = sections[-1]["text"].rstrip() + " That is the news update."  # info: sections [ - 1 ] [ "text" ] = sections [ - 1 ] [ "text" ] . rstrip ( ) + " That is the news update."
    speak = " ".join(section["text"] for section in sections)  # info: set speak
    return {  # info: return {
        "report": str(cfg.get("report") or "news_update"),  # info: "report" : str ( cfg . get ( "report" ) or "news_update" ) ,
        "hour": local.hour,  # info: "hour" : local . hour ,
        "words": _words(speak),  # info: "words" : _words ( speak ) ,
        "sections": sections,  # info: "sections" : sections ,
        "speak": speak,  # info: "speak" : speak ,
    }  # info: }


# ====================================================
# SECTION: function _source
# What it does: Keep the publisher, title, and URL for the audit copy.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _source(story: dict) -> dict:  # info: def _source
    return {  # info: return {
        "publisher": story.get("provider") or "",  # info: "publisher" : story . get ( "provider" ) or "" ,
        "title": story.get("title") or "",  # info: "title" : story . get ( "title" ) or "" ,
        "url": story.get("url") or "",  # info: "url" : story . get ( "url" ) or "" ,
        "published_at": story.get("published_at") or "",  # info: "published_at" : story . get ( "published_at" ) or "" ,
    }  # info: }


# ====================================================
# SECTION: function _roundup_feeds
# What it does: Feeds whose category is on a news-update desk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _roundup_feeds(registry: dict) -> list[dict]:  # info: def _roundup_feeds
    categories = set()  # info: set categories
    for desk in (_cfg(registry).get("desks") or []):  # info: for desk in ( _cfg ( registry ) . get ( "desks" ) or [ ] )
        if isinstance(desk, dict) and not desk.get("fill"):  # info: if isinstance ( desk , dict ) and not desk . get ( "fill" ) :
            categories.update(desk.get("categories") or [])  # info: categories . update ( desk . get ( "categories" ) or [ ] )
    return [feed for feed in registry["feeds"] if configured_on(feed) and feed.get("category") in categories]  # info: return [ feed for feed in registry [ "feeds" ] if configured_on ( feed ) and feed . get ( "category" ) in categories ]


# ====================================================
# SECTION: function _load
# What it does: Read stories still inside the backfill window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load(conn, since: str) -> list[dict]:  # info: def _load
    rows = conn.execute(  # info: set rows
        "SELECT * FROM stories WHERE status!='archived' AND (published_at>=? OR published_at='' OR first_seen_at>=?)",  # info: "SELECT * FROM stories WHERE status!='archived' AND (published_at>=? OR published_at='' OR first_seen_at>=?)" ,
        (since, since),  # info: ( since , since ) ,
    ).fetchall()  # info: ) . fetchall ( )
    return [dict(row) for row in rows]  # info: return [ dict ( row ) for row in rows ]


# ====================================================
# SECTION: function _write_script
# What it does: Store the spoken script and the source list under the RSS data root.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _write_script(built: dict, root: Path) -> Path:  # info: def _write_script
    folder = root / "processed" / "scripts" / built["report"]  # info: set folder
    folder.mkdir(parents=True, exist_ok=True)  # info: folder . mkdir ( parents = True , exist_ok = True )
    speak_path = folder / "news_update.speak.txt"  # info: set speak_path
    speak_path.write_text(built["speak"] + "\n", encoding="utf-8")  # info: speak_path . write_text ( built [ "speak" ] + "\n" , encoding = "utf-8" )
    (folder / "news_update.json").write_text(json.dumps(built, indent=2) + "\n", encoding="utf-8")  # info: ( folder / "news_update.json" ) . write_text ( json . dumps ( built , indent = 2 ) + "\n" , encoding = "utf-8" )
    return speak_path  # info: return speak_path


# ====================================================
# SECTION: function _render_section
# What it does: Render one desk with one Kokoro voice through the existing lock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _render_section(persona: str, text: str, wav: Path, text_path: Path) -> dict:  # info: def _render_section
    text_path.write_text(text + "\n", encoding="utf-8")  # info: text_path . write_text ( text + "\n" , encoding = "utf-8" )
    script = PACIFIC / "Media" / "Voice" / "scripts" / "voice-render.sh"  # info: set script
    cmd = ["bash", str(script), "stitch", "--report", "news_update", "--kind", persona, "--text-file", str(text_path), "--out", str(wav)]  # info: set cmd
    try:  # info: try
        ran = subprocess.run(cmd, capture_output=True, text=True, timeout=240)  # info: set ran
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired ) as exc
        return {"ok": False, "detail": type(exc).__name__, "persona": persona}  # info: return { "ok" : False , "detail" : type ( exc ) . __name__ , "persona" : persona }
    if ran.returncode == 75:  # info: if ran . returncode == 75 :
        return {"ok": False, "detail": "lock_busy", "persona": persona}  # info: return { "ok" : False , "detail" : "lock_busy" , "persona" : persona }
    if ran.returncode != 0 or not wav.is_file():  # info: if ran . returncode != 0 or not wav . is_file ( ) :
        return {"ok": False, "detail": "speak_failed", "code": ran.returncode, "persona": persona}  # info: return { "ok" : False , "detail" : "speak_failed" , "code" : ran . returncode , "persona" : persona }
    return {"ok": True, "persona": persona, "wav": str(wav)}  # info: return { "ok" : True , "persona" : persona , "wav" : str ( wav ) }


# ====================================================
# SECTION: function _gap
# What it does: A short silence between two voices.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _gap(path: Path) -> bool:  # info: def _gap
    try:  # info: try
        ran = subprocess.run(  # info: set ran
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.45", "-c:a", "pcm_s16le", str(path)],  # info: [ "ffmpeg" , "-y" , "-f" , "lavfi" , "-i" , "anullsrc=r=24000:cl=mono" , "-t" , "0.45" , "-c:a" , "pcm_s16le" , str ( path ) ] ,
            capture_output=True,  # info: capture_output = True ,
            timeout=30,  # info: timeout = 30 ,
        )  # info: )
    except (OSError, subprocess.TimeoutExpired):  # info: except ( OSError , subprocess . TimeoutExpired )
        return False  # info: return False
    return ran.returncode == 0 and path.is_file()  # info: return ran . returncode == 0 and path . is_file ( )


# ====================================================
# SECTION: function _join
# What it does: Join the desk recordings into news_update_current.wav and retire the previous file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _join(parts: list[Path], built: dict) -> dict:  # info: def _join
    VOICE_DIR.mkdir(parents=True, exist_ok=True)  # info: VOICE_DIR . mkdir ( parents = True , exist_ok = True )
    dest = VOICE_DIR / "news_update_current.wav"  # info: set dest
    folder = Path(tempfile.mkdtemp(prefix="news-update-"))  # info: set folder
    try:  # info: try
        listing = folder / "join.txt"  # info: set listing
        listing.write_text("".join(f"file '{path}'\n" for path in parts), encoding="utf-8")  # info: listing . write_text ( "" . join ( f"file '{ path }'\n" for path in parts ) , encoding = "utf-8" )
        staged = folder / "joined.wav"  # info: set staged
        ran = subprocess.run(  # info: set ran
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(staged)],  # info: [ "ffmpeg" , "-y" , "-f" , "concat" , "-safe" , "0" , "-i" , str ( listing ) , "-ar" , "24000" , "-ac" , "1" , "-c:a" , "pcm_s16le" , str ( staged ) ] ,
            capture_output=True,  # info: capture_output = True ,
            timeout=120,  # info: timeout = 120 ,
        )  # info: )
        if ran.returncode != 0 or not staged.is_file():  # info: if ran . returncode != 0 or not staged . is_file ( ) :
            return {"ok": False, "detail": "join_failed"}  # info: return { "ok" : False , "detail" : "join_failed" }
        voice_dir = str(PACIFIC / "Media" / "Voice" / "scripts")  # info: set voice_dir
        if voice_dir not in sys.path:  # info: if voice_dir not in sys . path :
            sys.path.insert(0, voice_dir)  # info: sys . path . insert ( 0 , voice_dir )
        import speakers  # info: import speakers
        same_disk = dest.with_name(".news_update_current.new.wav")  # info: set same_disk
        shutil.copyfile(staged, same_disk)  # info: shutil . copyfile ( staged , same_disk )
        speakers.retire_current(dest)  # info: speakers . retire_current ( dest )
        os.replace(same_disk, dest)  # info: os . replace ( same_disk , dest )
    except (OSError, subprocess.TimeoutExpired) as exc:  # info: except ( OSError , subprocess . TimeoutExpired ) as exc
        return {"ok": False, "detail": type(exc).__name__}  # info: return { "ok" : False , "detail" : type ( exc ) . __name__ }
    REPORT_TEXT.mkdir(parents=True, exist_ok=True)  # info: REPORT_TEXT . mkdir ( parents = True , exist_ok = True )
    (REPORT_TEXT / "news_update_current.read.txt").write_text(built["speak"].strip() + "\n", encoding="utf-8")  # info: ( REPORT_TEXT / "news_update_current.read.txt" ) . write_text ( built [ "speak" ] . strip ( ) + "\n" , encoding = "utf-8" )
    (REPORT_TEXT / "news_update_current.speak.txt").write_text(built["speak"].strip() + "\n", encoding="utf-8")  # info: ( REPORT_TEXT / "news_update_current.speak.txt" ) . write_text ( built [ "speak" ] . strip ( ) + "\n" , encoding = "utf-8" )
    return {"ok": True, "wav": str(dest)}  # info: return { "ok" : True , "wav" : str ( dest ) }


# ====================================================
# SECTION: function render_update
# What it does: Speak each desk in its own voice, then replace news_update_current and push the reports file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def render_update(built: dict) -> dict:  # info: def render_update
    voice_dir = str(PACIFIC / "Media" / "Voice" / "scripts")  # info: set voice_dir
    if voice_dir not in sys.path:  # info: if voice_dir not in sys . path :
        sys.path.insert(0, voice_dir)  # info: sys . path . insert ( 0 , voice_dir )
    import status_cue  # info: import status_cue
    from hawaiian_lexicon import fold_place_spellings, pronounce_places  # info: from hawaiian_lexicon import fold_place_spellings , pronounce_places
    status_cue.play("news_update", "starting")  # info: status cue before the news render
    folder = Path(tempfile.mkdtemp(prefix="news-hour-"))  # info: set folder
    gap = folder / "gap.wav"  # info: set gap
    has_gap = _gap(gap)  # info: set has_gap
    parts = []  # info: set parts
    voices = []  # info: set voices
    for index, section in enumerate(built.get("sections") or []):  # info: for index , section in enumerate ( built . get ( "sections" ) or [ ] )
        wav = folder / f"part-{index}.wav"  # info: set wav
        spoken = pronounce_places(fold_place_spellings(section.get("text") or ""))  # info: set spoken
        rendered = _render_section(str(section.get("persona") or "ava"), spoken, wav, folder / f"part-{index}.txt")  # info: set rendered
        if not rendered.get("ok"):  # info: if not rendered . get ( "ok" ) :
            return rendered  # info: return rendered
        if parts and has_gap:  # info: if parts and has_gap :
            parts.append(gap)  # info: parts . append ( gap )
        parts.append(wav)  # info: parts . append ( wav )
        voices.append(section.get("persona"))  # info: voices . append ( section . get ( "persona" ) )
    if not parts:  # info: if not parts :
        return {"ok": False, "detail": "empty"}  # info: return { "ok" : False , "detail" : "empty" }
    joined = _join(parts, built)  # info: set joined
    if not joined.get("ok"):  # info: if not joined . get ( "ok" ) :
        return joined  # info: return joined
    if os.environ.get("RR_RADIO_PUSH", "1") == "0":  # info: if os . environ . get ( "RR_RADIO_PUSH" , "1" ) == "0" :
        return {"ok": True, "detail": "rendered", "wav": joined["wav"], "voices": voices}  # info: return { "ok" : True , "detail" : "rendered" , "wav" : joined [ "wav" ] , "voices" : voices }
    import radio_push  # info: import radio_push
    status_cue.play("news_update", "transit")  # info: transit cue as the send starts
    pushed = radio_push.push_report("news_update")  # info: set pushed
    if not isinstance(pushed, dict):  # info: if not isinstance ( pushed , dict ) :
        status_cue.play("news_update", "failed")  # info: failed cue when the send does not return
        return {"ok": False, "detail": "push_failed", "wav": joined["wav"]}  # info: return { "ok" : False , "detail" : "push_failed" , "wav" : joined [ "wav" ] }
    pushed["status_send"] = status_cue.after_push("news_update", pushed)  # info: sent cue after Mainland One has the file
    pushed["voices"] = voices  # info: pushed [ "voices" ] = voices
    pushed["wav"] = joined["wav"]  # info: pushed [ "wav" ] = joined [ "wav" ]
    return pushed  # info: return pushed


# ====================================================
# SECTION: function news_hour
# What it does: Poll the news desks, write this hour's script, and optionally speak and upload it.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def news_hour(registry: dict, conn, speak: bool = False, root: Path | None = None) -> dict:  # info: def news_hour
    from common import ROOT  # info: from common import ROOT
    from fetch import fetch_url  # info: from fetch import fetch_url
    base = root or ROOT  # info: set base
    polled = []  # info: set polled
    for feed in _roundup_feeds(registry):  # info: for feed in _roundup_feeds ( registry )
        try:  # info: try
            polled.append(poll_feed(registry, conn, feed, fetch_url, base))  # info: polled . append ( poll_feed ( registry , conn , feed , fetch_url , base ) )
        except Exception:  # info: except Exception
            polled.append({"feed": feed["id"], "ok": False})  # info: polled . append ( { "feed" : feed [ "id" ] , "ok" : False } )
    hours = float(_cfg(registry).get("backfill_hours") or 36)  # info: set hours
    stories = _load(conn, iso(utc_now() - timedelta(hours=hours)))  # info: set stories
    built = build_update(stories, registry, utc_now())  # info: set built
    path = _write_script(built, base)  # info: set path
    result = {  # info: set result
        "ok": True,  # info: "ok" : True ,
        "report": built["report"],  # info: "report" : built [ "report" ] ,
        "words": built["words"],  # info: "words" : built [ "words" ] ,
        "hour": built["hour"],  # info: "hour" : built [ "hour" ] ,
        "voices": [section["persona"] for section in built["sections"]],  # info: "voices" : [ section [ "persona" ] for section in built [ "sections" ] ] ,
        "script": str(path),  # info: "script" : str ( path ) ,
        "polled": len(polled),  # info: "polled" : len ( polled ) ,
        "stories": len(stories),  # info: "stories" : len ( stories ) ,
    }  # info: }
    if not speak:  # info: if not speak :
        result["detail"] = "script"  # info: result [ "detail" ] = "script"
        return result  # info: return result
    spoken = render_update(built)  # info: set spoken
    result["speak"] = spoken  # info: result [ "speak" ] = spoken
    result["detail"] = spoken.get("detail") or ("broadcast" if spoken.get("ok") else "speak_failed")  # info: result [ "detail" ] = spoken . get ( "detail" ) or ( "broadcast" if spoken . get ( "ok" ) else "speak_failed" )
    result["ok"] = bool(spoken.get("ok"))  # info: result [ "ok" ] = bool ( spoken . get ( "ok" ) )
    return result  # info: return result
