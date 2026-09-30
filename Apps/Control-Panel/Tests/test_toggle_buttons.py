# ==============================================================================
# FILE: Apps/Control-Panel/Tests/test_toggle_buttons.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
#!/usr/bin/env python3
"""test_toggle_buttons.py — Root Monitor on/off buttons (added 2026-09-29 16:15 HST).

Builds the Panel in --check mode (no window) and checks: no Gtk.Switch / Adw.SwitchRow anywhere; the
"Camera viewer: Off" button is on the Cameras page AND first on Settings → Panel, both in sync; every toggle
updates the in-memory settings only (settings.json untouched; Save writes a TEMP copy here); risky actions need
the confirm; AWS Fallback dry-run / cancel / failed write revert the button. SAFETY: rr_aws_page.spawn is replaced
by a stub for the whole run, so NO ssh command is ever started and nothing is written on AWS.
"""
from __future__ import annotations  # info: from __future__ import annotations

import hashlib  # info: import hashlib
import json  # info: import json
import os  # info: import os
import sys  # info: import sys
import tempfile  # info: import tempfile
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent.parent  # info: set HERE
sys.path.insert(0, str(HERE))  # info: sys . path . insert ( 0 ,
sys.argv = [str(HERE / "rr_control_panel.py")]  # info: sys . argv = [ str ( HERE
import rr_control_panel as m  # noqa: E402
import rr_aws_page  # noqa: E402
from gi.repository import Gtk  # noqa: E402

results: list[tuple[str, bool, str]] = []  # info: set results


# ====================================================
# SECTION: function rec
# What it does: rec.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def rec(name, ok, note=""):  # info: def rec
    results.append((name, bool(ok), note))  # info: results . append ( ( name , bool


# ====================================================
# SECTION: function walk
# What it does: walk.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def walk(w):  # info: def walk
    st = [w]  # info: set st
    while st:  # info: while st :
        x = st.pop()  # info: set x
        yield x  # info: yield x
        c = x.get_first_child()  # info: set c
        while c is not None:  # info: while c is not None :
            st.append(c)  # info: st . append ( c )
            c = c.get_next_sibling()  # info: set c


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    sfile = m.rr_settings.SETTINGS_FILE  # info: set sfile
    h0 = hashlib.md5(sfile.read_bytes()).hexdigest()  # info: set h0
    spawned = []  # info: set spawned
    rr_aws_page.spawn = lambda argv, on_done=None, capture=False: spawned.append((argv, on_done))  # never runs ssh
    if m.Adw is not None:  # info: if m . Adw is not None :
        m.Adw.init()  # info: m . Adw . init ( )
    s = m.rr_settings.load()  # info: set s
    s["camera_viewer_enabled"] = False     # test from the default state regardless of the desk file
    s["risky_actions_enabled"] = False  # info: s [ "risky_actions_enabled" ] = False
    p = m.Panel(s, check=True)  # info: set p
    toasts, answers = [], []  # info: toasts , answers = [ ] , [
    p.toast = toasts.append  # info: p . toast = toasts . append

    def fake_confirm(heading, body, ok_label, on_ok, on_cancel=None, extra=None):  # info: def fake_confirm
        (on_ok if answers.pop(0) else (on_cancel or (lambda: None)))()  # info: call (
    p.confirm = fake_confirm  # info: p . confirm = fake_confirm

    # 1. no switches anywhere (every page is built in check mode; Settings → Panel stays built)
    kinds = [type(x).__name__ for pg in p.page_boxes.values() for x in walk(pg)]  # info: set kinds
    rec("no Gtk.Switch in any page", "Switch" not in kinds, f"{len(kinds)} widgets walked")  # info: call rec
    rec("no Adw.SwitchRow in any page", "SwitchRow" not in kinds)  # info: call rec
    toggles = [x for pg in p.page_boxes.values() for x in walk(pg) if isinstance(x, Gtk.ToggleButton)]  # info: set toggles
    rec("toggle buttons present", len(toggles) >= 10, f"{len(toggles)} ToggleButtons")  # info: call rec
    rec("every toggle is labelled with its state",  # info: call rec
        all(t.get_label().endswith((": On", ": Off")) and (t.has_css_class("rr-on") != t.has_css_class("rr-off")) for t in toggles))  # info: call all

    # 2. camera viewer button: Cameras page + Settings → Panel, default Off
    cam_page = [t for t in walk(p.page_boxes["cameras"]) if isinstance(t, Gtk.ToggleButton)]  # info: set cam_page
    panel_box = p.set_boxes["panel"]  # info: set panel_box
    set_btns = [t for t in walk(panel_box) if isinstance(t, Gtk.ToggleButton) and t.get_label().startswith("Camera viewer")]  # info: set set_btns
    rec("Cameras page has the camera viewer button", len(cam_page) == 1 and cam_page[0].get_label() == "Camera viewer: Off",  # info: call rec
        cam_page[0].get_label() if cam_page else "missing")  # info: cam_page [ 0 ] . get_label ( )
    rec("Cameras page button is the first widget row", p.page_boxes["cameras"].get_first_child().get_first_child() is cam_page[0])  # info: call rec
    rec("Cameras page button is big + off-styled", cam_page[0].has_css_class("rr-big") and cam_page[0].has_css_class("rr-off"))  # info: call rec
    rec("Settings → Panel has the camera viewer button", len(set_btns) == 1 and set_btns[0].get_label() == "Camera viewer: Off")  # info: call rec
    ordered = []  # info: set ordered

    def dfs(w):  # info: def dfs
        if isinstance(w, Gtk.ToggleButton):  # info: if isinstance ( w , Gtk . ToggleButton
            ordered.append(w)  # info: ordered . append ( w )
        c = w.get_first_child()  # info: set c
        while c is not None:  # info: while c is not None :
            dfs(c)  # info: call dfs
            c = c.get_next_sibling()  # info: set c
    dfs(panel_box)  # info: call dfs
    rec("camera viewer is the FIRST button on Settings → Panel", ordered and ordered[0] is set_btns[0], ordered[0].get_label())  # info: call rec

    # 3. click on the Cameras page -> on everywhere, in memory only
    cam_page[0].set_active(True)  # info: cam_page [ 0 ] . set_active ( True
    rec("click → setting on", p.s["camera_viewer_enabled"] is True and p.camera_viewer_on)  # info: call rec
    rec("click → both buttons read On + green", all(b.get_label() == "Camera viewer: On" and b.has_css_class("rr-on") for b in p.cam_toggles),  # info: call rec
        str([b.get_label() for b in p.cam_toggles]))  # info: call str
    set_btns[0].set_active(False)  # info: set_btns [ 0 ] . set_active ( False
    rec("Settings button → off everywhere", p.s["camera_viewer_enabled"] is False and all(b.get_label() == "Camera viewer: Off" for b in p.cam_toggles))  # info: call rec
    p.camera_override = True  # info: p . camera_override = True
    p.r_cameras()  # info: p . r_cameras ( )
    rec("--camera-viewer override repaints the buttons", all(b.get_active() for b in p.cam_toggles))  # info: call rec
    p.camera_override = None  # info: p . camera_override = None
    p.r_cameras()  # info: p . r_cameras ( )
    rec("override cleared → buttons Off again", not any(b.get_active() for b in p.cam_toggles))  # info: call rec

    # 4. other panel toggles
    by = {t.get_label().rsplit(":", 1)[0]: t for t in ordered}  # info: set by
    st0 = bool(p.s.get("starlink_enabled", True))  # info: set st0
    by["Starlink"].set_active(not st0)  # info: by [ "Starlink" ] . set_active ( not
    rec("Starlink button updates starlink_enabled", p.s["starlink_enabled"] is (not st0))  # info: call rec
    by["Starlink"].set_active(st0)  # info: by [ "Starlink" ] . set_active ( st0
    by["Show ch2"].set_active(False)  # info: by [ "Show ch2" ] . set_active ( False
    rec("Show ch2 button updates cameras.ch2.enabled", p.s["cameras"]["ch2"]["enabled"] is False)  # info: call rec
    by["Show ch2"].set_active(True)  # info: by [ "Show ch2" ] . set_active ( True
    fb = bool(p.s.get("camera_live_fallback"))  # info: set fb
    by["Still fallback"].set_active(not fb)  # info: by [ "Still fallback" ] . set_active ( not
    rec("Still fallback button updates camera_live_fallback", p.s["camera_live_fallback"] is (not fb))  # info: call rec
    by["Still fallback"].set_active(fb)  # info: by [ "Still fallback" ] . set_active ( fb

    # 5. risky actions: confirm required
    rb = by["Risky actions"]  # info: set rb
    rb.set_active(True)   # no window -> no dialog -> stays off
    rec("risky: no window → stays Off", not rb.get_active() and not p.s["risky_actions_enabled"])  # info: call rec
    p.win = object()  # info: p . win = object ( )
    answers.append(False)  # info: answers . append ( False )
    rb.set_active(True)  # info: rb . set_active ( True )
    rec("risky: cancel → button back Off, setting off", not rb.get_active() and not p.s["risky_actions_enabled"], rb.get_label())  # info: call rec
    answers.append(True)  # info: answers . append ( True )
    rb.set_active(True)  # info: rb . set_active ( True )
    rec("risky: confirm → On", rb.get_active() and p.s["risky_actions_enabled"] is True)  # info: call rec
    rb.set_active(False)  # info: rb . set_active ( False )
    rec("risky: off needs no dialog", not p.s["risky_actions_enabled"] and not answers)  # info: call rec
    p.win = None  # info: p . win = None

    # 6. AWS Fallback buttons (spawn is stubbed; nothing leaves the desk)
    p.win = object()  # info: p . win = object ( )
    sw = p.awf_switches  # info: set sw
    fid = next(k for k, b in sw.items() if b.get_active())  # info: set fid
    b = sw[fid]  # info: set b
    rec("AWS rows use labelled buttons", all(isinstance(x, Gtk.ToggleButton) and x.get_label().startswith("AWS: ") for x in sw.values()),  # info: call rec
        f"{len(sw)} buttons")  # info: f" { len ( sw ) } buttons
    p.awf_mode = "dry-run"  # info: p . awf_mode = "dry-run"
    answers.append(True)  # info: answers . append ( True )
    b.set_active(False)  # info: b . set_active ( False )
    rec("AWS dry-run confirm → reverts, nothing spawned", b.get_active() and p.awf_state[fid] is True and not spawned  # info: call rec
        and b.get_label() == "AWS: On", toasts[-1] if toasts else "")  # info: and b . get_label ( ) == "AWS: On"
    answers.append(False)  # info: answers . append ( False )
    b.set_active(False)  # info: b . set_active ( False )
    rec("AWS cancel → reverts", b.get_active() and p.awf_state[fid] is True and not spawned)  # info: call rec
    p.awf_mode = "write"  # info: p . awf_mode = "write"
    answers.append(True)  # info: answers . append ( True )
    b.set_active(False)  # info: b . set_active ( False )
    argv, done = spawned[-1]  # info: argv , done = spawned [ - 1
    rec("AWS write mode builds ONE ssh write (stubbed, not run)", len(spawned) == 1 and argv[2] == "ssh" and f"F={fid}" in argv[-1])  # info: call rec
    done("error", 3)  # info: call done
    rec("AWS failed write → reverts to On", b.get_active() and p.awf_state[fid] is True)  # info: call rec
    answers.append(True)  # info: answers . append ( True )
    b.set_active(False)  # info: b . set_active ( False )
    spawned[-1][1]("ok", 0)  # info: spawned [ - 1 ] [ 1 ]
    rec("AWS successful write → stays Off, state updated", not b.get_active() and p.awf_state[fid] is False and b.get_label() == "AWS: Off")  # info: call rec
    n = len(spawned)  # info: set n
    p.awf_status()  # info: p . awf_status ( )
    spawned[-1][1](f"deployed=1\nflag.{fid}=1\nmem_total_mb=908\n", 0)  # info: spawned [ - 1 ] [ 1 ]
    rec("AWS status read repaints the button without a dialog", b.get_active() and not answers and len(spawned) == n + 1)  # info: call rec
    p.win = None  # info: p . win = None

    # 7. Save writes the toggles (temp copy only); desk settings.json untouched
    with tempfile.TemporaryDirectory(prefix="rm-toggle-test-") as td:  # info: with tempfile . TemporaryDirectory ( prefix = "rm-toggle-test-"
        tmp = Path(td) / "settings.json"  # info: set tmp
        real_save = m.rr_settings.save  # info: set real_save
        m.rr_settings.save = lambda st: real_save(st, tmp)  # info: m . rr_settings . save = lambda st
        try:  # info: try :
            cam_page[0].set_active(True)  # info: cam_page [ 0 ] . set_active ( True
            p.save_settings()  # info: p . save_settings ( )
            saved = json.loads(tmp.read_text())  # info: set saved
            rec("Save settings keeps camera_viewer_enabled=true (temp copy)", saved.get("camera_viewer_enabled") is True)  # info: call rec
            cam_page[0].set_active(False)  # info: cam_page [ 0 ] . set_active ( False
        finally:  # info: finally :
            m.rr_settings.save = real_save  # info: m . rr_settings . save = real_save
    rec("desk settings.json not modified by the test", hashlib.md5(sfile.read_bytes()).hexdigest() == h0)  # info: call rec
    p.stop()  # info: p . stop ( )

    for name, ok, note in results:  # info: for name , ok , note in results
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""))  # info: call print
    npass = sum(1 for _n, ok, _x in results if ok)  # info: set npass
    print(f"toggle-button tests: {npass}/{len(results)} PASS")  # info: call print
    return 0 if npass == len(results) else 1  # info: return 0 if npass == len ( results


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    os.environ.setdefault("GSK_RENDERER", "cairo")  # info: os . environ . setdefault ( "GSK_RENDERER" ,
    sys.exit(main())  # info: sys . exit ( main ( ) )
