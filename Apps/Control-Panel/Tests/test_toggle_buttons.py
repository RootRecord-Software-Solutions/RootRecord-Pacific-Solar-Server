#!/usr/bin/env python3
"""test_toggle_buttons.py — Root Monitor on/off buttons (added 2026-09-29 16:15 HST).

Builds the Panel in --check mode (no window) and checks: no Gtk.Switch / Adw.SwitchRow anywhere; the
"Camera viewer: Off" button is on the Cameras page AND first on Settings → Panel, both in sync; every toggle
updates the in-memory settings only (settings.json untouched; Save writes a TEMP copy here); risky actions need
the confirm; AWS Fallback dry-run / cancel / failed write revert the button. SAFETY: rr_aws_page.spawn is replaced
by a stub for the whole run, so NO ssh command is ever started and nothing is written on AWS.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.argv = [str(HERE / "rr_control_panel.py")]
import rr_control_panel as m  # noqa: E402
import rr_aws_page  # noqa: E402
from gi.repository import Gtk  # noqa: E402

results: list[tuple[str, bool, str]] = []


def rec(name, ok, note=""):
    results.append((name, bool(ok), note))


def walk(w):
    st = [w]
    while st:
        x = st.pop()
        yield x
        c = x.get_first_child()
        while c is not None:
            st.append(c)
            c = c.get_next_sibling()


def main() -> int:
    sfile = m.rr_settings.SETTINGS_FILE
    h0 = hashlib.md5(sfile.read_bytes()).hexdigest()
    spawned = []
    rr_aws_page.spawn = lambda argv, on_done=None, capture=False: spawned.append((argv, on_done))  # never runs ssh
    if m.Adw is not None:
        m.Adw.init()
    s = m.rr_settings.load()
    s["camera_viewer_enabled"] = False     # test from the default state regardless of the desk file
    s["risky_actions_enabled"] = False
    p = m.Panel(s, check=True)
    toasts, answers = [], []
    p.toast = toasts.append

    def fake_confirm(heading, body, ok_label, on_ok, on_cancel=None, extra=None):
        (on_ok if answers.pop(0) else (on_cancel or (lambda: None)))()
    p.confirm = fake_confirm

    # 1. no switches anywhere (every page is built in check mode; Settings → Panel stays built)
    kinds = [type(x).__name__ for pg in p.page_boxes.values() for x in walk(pg)]
    rec("no Gtk.Switch in any page", "Switch" not in kinds, f"{len(kinds)} widgets walked")
    rec("no Adw.SwitchRow in any page", "SwitchRow" not in kinds)
    toggles = [x for pg in p.page_boxes.values() for x in walk(pg) if isinstance(x, Gtk.ToggleButton)]
    rec("toggle buttons present", len(toggles) >= 10, f"{len(toggles)} ToggleButtons")
    rec("every toggle is labelled with its state",
        all(t.get_label().endswith((": On", ": Off")) and (t.has_css_class("rr-on") != t.has_css_class("rr-off")) for t in toggles))

    # 2. camera viewer button: Cameras page + Settings → Panel, default Off
    cam_page = [t for t in walk(p.page_boxes["cameras"]) if isinstance(t, Gtk.ToggleButton)]
    panel_box = p.set_boxes["panel"]
    set_btns = [t for t in walk(panel_box) if isinstance(t, Gtk.ToggleButton) and t.get_label().startswith("Camera viewer")]
    rec("Cameras page has the camera viewer button", len(cam_page) == 1 and cam_page[0].get_label() == "Camera viewer: Off",
        cam_page[0].get_label() if cam_page else "missing")
    rec("Cameras page button is the first widget row", p.page_boxes["cameras"].get_first_child().get_first_child() is cam_page[0])
    rec("Cameras page button is big + off-styled", cam_page[0].has_css_class("rr-big") and cam_page[0].has_css_class("rr-off"))
    rec("Settings → Panel has the camera viewer button", len(set_btns) == 1 and set_btns[0].get_label() == "Camera viewer: Off")
    ordered = []

    def dfs(w):
        if isinstance(w, Gtk.ToggleButton):
            ordered.append(w)
        c = w.get_first_child()
        while c is not None:
            dfs(c)
            c = c.get_next_sibling()
    dfs(panel_box)
    rec("camera viewer is the FIRST button on Settings → Panel", ordered and ordered[0] is set_btns[0], ordered[0].get_label())

    # 3. click on the Cameras page -> on everywhere, in memory only
    cam_page[0].set_active(True)
    rec("click → setting on", p.s["camera_viewer_enabled"] is True and p.camera_viewer_on)
    rec("click → both buttons read On + green", all(b.get_label() == "Camera viewer: On" and b.has_css_class("rr-on") for b in p.cam_toggles),
        str([b.get_label() for b in p.cam_toggles]))
    set_btns[0].set_active(False)
    rec("Settings button → off everywhere", p.s["camera_viewer_enabled"] is False and all(b.get_label() == "Camera viewer: Off" for b in p.cam_toggles))
    p.camera_override = True
    p.r_cameras()
    rec("--camera-viewer override repaints the buttons", all(b.get_active() for b in p.cam_toggles))
    p.camera_override = None
    p.r_cameras()
    rec("override cleared → buttons Off again", not any(b.get_active() for b in p.cam_toggles))

    # 4. other panel toggles
    by = {t.get_label().rsplit(":", 1)[0]: t for t in ordered}
    st0 = bool(p.s.get("starlink_enabled", True))
    by["Starlink"].set_active(not st0)
    rec("Starlink button updates starlink_enabled", p.s["starlink_enabled"] is (not st0))
    by["Starlink"].set_active(st0)
    by["Show ch2"].set_active(False)
    rec("Show ch2 button updates cameras.ch2.enabled", p.s["cameras"]["ch2"]["enabled"] is False)
    by["Show ch2"].set_active(True)
    fb = bool(p.s.get("camera_live_fallback"))
    by["Still fallback"].set_active(not fb)
    rec("Still fallback button updates camera_live_fallback", p.s["camera_live_fallback"] is (not fb))
    by["Still fallback"].set_active(fb)

    # 5. risky actions: confirm required
    rb = by["Risky actions"]
    rb.set_active(True)   # no window -> no dialog -> stays off
    rec("risky: no window → stays Off", not rb.get_active() and not p.s["risky_actions_enabled"])
    p.win = object()
    answers.append(False)
    rb.set_active(True)
    rec("risky: cancel → button back Off, setting off", not rb.get_active() and not p.s["risky_actions_enabled"], rb.get_label())
    answers.append(True)
    rb.set_active(True)
    rec("risky: confirm → On", rb.get_active() and p.s["risky_actions_enabled"] is True)
    rb.set_active(False)
    rec("risky: off needs no dialog", not p.s["risky_actions_enabled"] and not answers)
    p.win = None

    # 6. AWS Fallback buttons (spawn is stubbed; nothing leaves the desk)
    p.win = object()
    sw = p.awf_switches
    fid = next(k for k, b in sw.items() if b.get_active())
    b = sw[fid]
    rec("AWS rows use labelled buttons", all(isinstance(x, Gtk.ToggleButton) and x.get_label().startswith("AWS: ") for x in sw.values()),
        f"{len(sw)} buttons")
    p.awf_mode = "dry-run"
    answers.append(True)
    b.set_active(False)
    rec("AWS dry-run confirm → reverts, nothing spawned", b.get_active() and p.awf_state[fid] is True and not spawned
        and b.get_label() == "AWS: On", toasts[-1] if toasts else "")
    answers.append(False)
    b.set_active(False)
    rec("AWS cancel → reverts", b.get_active() and p.awf_state[fid] is True and not spawned)
    p.awf_mode = "write"
    answers.append(True)
    b.set_active(False)
    argv, done = spawned[-1]
    rec("AWS write mode builds ONE ssh write (stubbed, not run)", len(spawned) == 1 and argv[2] == "ssh" and f"F={fid}" in argv[-1])
    done("error", 3)
    rec("AWS failed write → reverts to On", b.get_active() and p.awf_state[fid] is True)
    answers.append(True)
    b.set_active(False)
    spawned[-1][1]("ok", 0)
    rec("AWS successful write → stays Off, state updated", not b.get_active() and p.awf_state[fid] is False and b.get_label() == "AWS: Off")
    n = len(spawned)
    p.awf_status()
    spawned[-1][1](f"deployed=1\nflag.{fid}=1\nmem_total_mb=908\n", 0)
    rec("AWS status read repaints the button without a dialog", b.get_active() and not answers and len(spawned) == n + 1)
    p.win = None

    # 7. Save writes the toggles (temp copy only); desk settings.json untouched
    with tempfile.TemporaryDirectory(prefix="rm-toggle-test-") as td:
        tmp = Path(td) / "settings.json"
        real_save = m.rr_settings.save
        m.rr_settings.save = lambda st: real_save(st, tmp)
        try:
            cam_page[0].set_active(True)
            p.save_settings()
            saved = json.loads(tmp.read_text())
            rec("Save settings keeps camera_viewer_enabled=true (temp copy)", saved.get("camera_viewer_enabled") is True)
            cam_page[0].set_active(False)
        finally:
            m.rr_settings.save = real_save
    rec("desk settings.json not modified by the test", hashlib.md5(sfile.read_bytes()).hexdigest() == h0)
    p.stop()

    for name, ok, note in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({note})" if note else ""))
    npass = sum(1 for _n, ok, _x in results if ok)
    print(f"toggle-button tests: {npass}/{len(results)} PASS")
    return 0 if npass == len(results) else 1


if __name__ == "__main__":
    os.environ.setdefault("GSK_RENDERER", "cairo")
    sys.exit(main())
