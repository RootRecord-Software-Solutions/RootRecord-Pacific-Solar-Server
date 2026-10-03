#!/usr/bin/env python3
"""rr_control_panel.py — Root Monitor (was "RootRecord Control Panel"): native GTK4 / libadwaita desk app (no browser, no Electron).

INFO — MUST HAVE (future agents), added 2026-09-29:
- READ-ONLY viewer ADDED ALONGSIDE poller-dashboard.py, poller-watch.py, the poller ENERGY status line and
  npu-status.sh. It replaces nothing and changes none of them.
- Reads existing JSON / log / report files, sysfs and /proc only (Lib/rr_sources.py). No network server, no
  busy loop: one GLib timeout every refresh_sec (default 5 s) refreshes the header + the VISIBLE page only.
- Camera viewer is OFF by default (settings.json camera_viewer_enabled). OFF = no timer, no directory scan,
  no image load, no stream. ON = latest on-disk still per enabled camera every camera_refresh_sec (10 s),
  ONLY while the Cameras page is visible; the timer is removed as soon as you leave the page or turn it off.
  A local still URL (cam_server :8791) is fetched only when a camera has no still on disk, and only while visible.
- Risky actions (poller restart, Telegram/voice sends, gated RR_* flags) are disabled unless
  risky_actions_enabled=true AND the action is signed_off AND it has an argv; each needs a confirm dialog.
  Agents must never click them. Enabling them is a sign-off item.
- Controls → "Restart everything" is the operator button (2026-10-01). Confirm, then
  Packaging/restart-everything.sh restarts the poller stack, BLE, the AWS fetch tunnel, and this window.
  Agents must never click it. Ollama and the desktop session are left running.
- --check builds every widget and loads each data source once, prints a report and exits; no window shown.
- --screenshot DIR opens the window, captures each page to PNG (renders the window itself), then quits.
  Before each PNG is saved, every string in the window is checked against the known secret values; a match
  skips that PNG (secret guard).
- Renamed "Root Monitor" 2026-09-29 (file paths + APP_ID unchanged so the existing launcher keeps working).
  New pages (rr_pages.py): Running, Network (+ Starlink), SSH, Not migrated, and the Settings hub
  (Lib/rr_registry.py + Lib/rr_config_io.py). Automations (rr_automations_page.py) toggles every poller
  job, schedules EcoFlow action scripts at a clock time, and arms a polling rest that
  stops the stack and starts it again later. Every page does nothing unless it is visible.
- 2026-09-29 16:10 HST: NO switches. Every on/off control is a labelled Gtk.ToggleButton ("Camera viewer: Off" /
  "On", green = on, red outline = off) from rr_ui.state_toggle. The camera viewer button sits at the top of the
  Cameras page AND first on Settings → Panel (both stay in sync). Before this the only camera control was an
  Adw.SwitchRow at the bottom of Settings → Panel (below the fold) and the Cameras page pointed at the wrong sub-page.
"""
from __future__ import annotations  # info: from __future__ import annotations

import argparse  # info: import argparse
import os  # info: import os
import resource  # info: import resource
import subprocess  # info: import subprocess
import sys  # info: import sys
import threading  # info: import threading
import time  # info: import time
import warnings  # info: import warnings
from datetime import datetime  # info: from datetime import datetime
from pathlib import Path  # info: from pathlib import Path

HERE = Path(__file__).resolve().parent  # info: set HERE
sys.path.insert(0, str(HERE / "Lib"))  # info: sys . path . insert ( 0 ,
import rr_settings  # noqa: E402
import rr_gates  # noqa: E402
import rr_sources as src  # noqa: E402

warnings.filterwarnings("ignore", category=DeprecationWarning)  # info: warnings . filterwarnings ( "ignore" , category =
# Lightweight default: the cairo renderer measured ~110 MB peak vs ~180 MB (default) / ~275 MB (gl) on this desk
# (2026-09-29). Override with GSK_RENDERER=... or settings.json "gsk_renderer".
os.environ.setdefault("GSK_RENDERER", str(rr_settings.load().get("gsk_renderer") or "cairo"))  # info: os . environ . setdefault ( "GSK_RENDERER" ,

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")  # info: gi . require_version ( "Gtk" , "4.0" )
gi.require_version("Gdk", "4.0")  # info: gi . require_version ( "Gdk" , "4.0" )
gi.require_version("GdkPixbuf", "2.0")  # info: gi . require_version ( "GdkPixbuf" , "2.0" )
try:  # info: try :
    gi.require_version("Adw", "1")  # info: gi . require_version ( "Adw" , "1" )
    from gi.repository import Adw  # noqa: E402
except (ValueError, ImportError):  # info: except ( ValueError , ImportError ) :
    Adw = None  # info: set Adw
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango  # noqa: E402

APP_ID = "cloud.rootrecord.ControlPanel"  # info: set APP_ID
APP_NAME = "Root Monitor"  # info: set APP_NAME
PAGES = [("energy", "Energy"), ("weather", "Weather"), ("system", "System"), ("npu", "NPU"), ("ai", "AI log"),  # info: set PAGES
         ("poller", "Poller / services"), ("automations", "Automations"), ("scheduler", "Scheduler"), ("telemetry", "Telemetry"), ("running", "Running"), ("network", "Network"), ("ssh", "SSH"), ("aws", "AWS Fallback"),  # info: call (
         ("radio", "ML1 playlist"), ("cameras", "Cameras"), ("controls", "Controls"), ("migration", "Not migrated"), ("settings", "Settings")]  # info: call (

# ====================================================
# SECTION: CSS
# What it does: Set CSS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
CSS = b"""
.rr-mono { font-family: monospace; font-size: 9.5pt; }
.rr-big { font-size: 15pt; font-weight: bold; }
.rr-pass { color: #859900; font-weight: bold; }
.rr-warn { color: #b58900; font-weight: bold; }
.rr-fail { color: #dc322f; font-weight: bold; }
.rr-header { padding: 6px 12px; }
.rr-card { padding: 10px 14px; border-radius: 10px; }
/* Charge (batteries): low percent is red, full is green. */
levelbar block.low { background-color: #dc322f; }
levelbar block.high { background-color: #b58900; }
levelbar block.full { background-color: #859900; }
/* Use (CPU, RAM): a quiet bar is green. Red starts at the high offset (80%). */
levelbar.rr-usage block.low { background-color: #859900; }
levelbar.rr-usage block.high { background-color: #b58900; }
levelbar.rr-usage block.full { background-color: #dc322f; }
button.rr-island:checked { background-color: #859900; color: #fdf6e3; }
button.rr-restart { min-width: 240px; min-height: 148px; font-size: 16pt; font-weight: bold; padding: 18px 22px; }
"""


# ====================================================
# SECTION: function now_hst
# What it does: now hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def now_hst() -> str:  # info: def now_hst
    return datetime.now(src.TZ).strftime("%A %d %b %Y  %H:%M:%S HST")  # info: return datetime . now ( src . TZ


from rr_ui import TOGGLE_CSS, badge_css, esc, lbl, section, spawn, state_toggle, widget_texts  # noqa: E402

CSS += TOGGLE_CSS.encode()  # info: set CSS
from rr_pages import ExtraPages  # noqa: E402
from rr_aws_page import AwsFallbackPage  # noqa: E402
from rr_automations_page import AutomationsPage  # noqa: E402
from rr_scheduler_page import SchedulerPage  # noqa: E402
from rr_telemetry_page import TelemetryPage  # noqa: E402
from rr_radio_page import RadioPage  # noqa: E402


# ====================================================
# SECTION: class BarRow
# What it does: BarRow.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class BarRow:  # info: class BarRow
    def __init__(self, parent: Gtk.Box, name: str, sub: str, scale: str = "charge"):  # info: def __init__
        row = Gtk.Box(spacing=10)  # info: set row
        row.append(lbl(f"<b>{esc(name)}</b>", markup=True))  # info: row . append ( lbl ( f" <b>
        row.append(lbl(sub, "dim-label"))  # info: row . append ( lbl ( sub ,
        self.bar = Gtk.LevelBar(min_value=0, max_value=100, hexpand=True, valign=Gtk.Align.CENTER)  # info: self . bar = Gtk . LevelBar (
        self.bar.set_size_request(220, 14)  # info: self . bar . set_size_request ( 220 ,
        for n in ("low", "high", "full"):  # info: for n in ( "low" , "high" ,
            self.bar.remove_offset_value(n)  # info: self . bar . remove_offset_value ( n )
        if scale == "usage":
            # Under 50% green, 50–80% amber, 80% and above red.
            self.bar.add_css_class("rr-usage")
            self.bar.add_offset_value("low", 50)
            self.bar.add_offset_value("high", 80)
            self.bar.add_offset_value("full", 100)
        else:
            self.bar.add_offset_value("low", 20)  # info: self . bar . add_offset_value ( "low" ,
            self.bar.add_offset_value("high", 50)  # info: self . bar . add_offset_value ( "high" ,
            self.bar.add_offset_value("full", 100)  # info: self . bar . add_offset_value ( "full" ,
        row.append(self.bar)  # info: row . append ( self . bar )
        self.val = lbl("n/a", "rr-big")  # info: self . val = lbl ( "n/a" ,
        self.val.set_width_chars(7)  # info: self . val . set_width_chars ( 7 )
        row.append(self.val)  # info: row . append ( self . val )
        self.detail = lbl("", "dim-label", wrap=True)  # info: self . detail = lbl ( "" ,
        parent.append(row)  # info: parent . append ( row )
        parent.append(self.detail)  # info: parent . append ( self . detail )

    def set(self, pct, detail: str, *, charge_warn: bool = True):
        """Update bar + value. For charge bars, ≤10% CRITICAL (red), ≤20% LOW (amber)."""
        for c in ("rr-fail", "rr-warn", "rr-pass"):
            self.val.remove_css_class(c)
        if not self.val.has_css_class("rr-big"):
            self.val.add_css_class("rr-big")
        if isinstance(pct, (int, float)):
            v = float(pct)
            self.bar.set_value(max(0.0, min(100.0, v)))
            if charge_warn and v <= 10:
                self.val.set_text(f"{v:.1f}% CRITICAL")
                self.val.add_css_class("rr-fail")
            elif charge_warn and v <= 20:
                self.val.set_text(f"{v:.1f}% LOW")
                self.val.add_css_class("rr-warn")
            else:
                self.val.set_text(f"{v:.1f}%")
                if charge_warn and v >= 80:
                    self.val.add_css_class("rr-pass")
        else:
            self.bar.set_value(0)
            self.val.set_text("n/a")
        self.detail.set_text(detail)


# ====================================================
# SECTION: class Panel
# What it does: Panel.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class Panel(ExtraPages, AwsFallbackPage, AutomationsPage, SchedulerPage, TelemetryPage, RadioPage):  # info: class Panel
    def __init__(self, settings: dict, check: bool = False, camera_override: bool | None = None):  # info: def __init__
        self.s = settings  # info: self . s = settings
        self.check = check  # info: self . check = check
        self.camera_override = camera_override  # info: self . camera_override = camera_override
        self.paths = src.Paths(settings["database_root"], settings["pacific_root"])  # info: self . paths = src . Paths (
        self.pw = src.load_poller_watch(self.paths)  # info: self . pw = src . load_poller_watch (
        self.cams = src.discover_cameras(self.paths)  # info: self . cams = src . discover_cameras (
        for c in self.cams:  # info: for c in self . cams :
            self.s["cameras"].setdefault(c, {"enabled": True, "label": c.upper()})  # info: self . s [ "cameras" ] . setdefault
        self.timer_id = 0  # info: self . timer_id = 0
        self.cam_timer_id = 0  # info: self . cam_timer_id = 0
        self.cam_fetching: set[str] = set()  # info: self . cam_fetching : set [ str ]
        self.errors: list[str] = []  # info: self . errors : list [ str ]
        self.check_texts: list[str] = []   # --check: strings of sub-pages released after building
        self.win = None  # info: self . win = None
        self.report: dict = {}  # info: self . report : dict = { }
        self._argvs = None  # info: self . _argvs = None
        self.cam_toggles: list = []   # every "Camera viewer: On/Off" button (Cameras page + Settings → Panel)
        self.build()  # info: self . build ( )

    # ----------------------------------------------------------- settings helpers
    @property  # info: decorator property
    def camera_viewer_on(self) -> bool:  # info: def camera_viewer_on
        if self.camera_override is not None:  # info: if self . camera_override is not None :
            return self.camera_override  # info: return self . camera_override
        return bool(self.s.get("camera_viewer_enabled"))  # info: return bool ( self . s . get

    def argvs(self):  # info: def argvs
        if self._argvs is None:  # info: if self . _argvs is None :
            self._argvs = src.proc_argvs()  # info: self . _argvs = src . proc_argvs (
        return self._argvs  # info: return self . _argvs

    # ----------------------------------------------------------- build
    def build(self):  # info: def build
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)  # info: self . root = Gtk . Box (
        self.header = lbl("", "rr-header", markup=True)  # info: self . header = lbl ( "" ,
        self.header.set_ellipsize(Pango.EllipsizeMode.END)  # info: self . header . set_ellipsize ( Pango .
        self.root.append(self.header)  # info: self . root . append ( self .
        self.root.append(Gtk.Separator())  # info: self . root . append ( Gtk .
        body = Gtk.Box(vexpand=True)  # info: set body
        self.stack = Gtk.Stack(hexpand=True, vexpand=True, transition_type=Gtk.StackTransitionType.CROSSFADE)  # info: self . stack = Gtk . Stack (
        side = Gtk.StackSidebar(stack=self.stack)  # info: set side
        side.set_size_request(170, -1)  # info: side . set_size_request ( 170 , - 1
        body.append(side)  # info: body . append ( side )
        body.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))  # info: body . append ( Gtk . Separator (
        body.append(self.stack)  # info: body . append ( self . stack )
        self.root.append(body)  # info: self . root . append ( body )
        self.builders = {"energy": self.b_energy, "weather": self.b_weather, "system": self.b_system,  # info: self . builders = { "energy" : self
                         "npu": self.b_npu, "ai": self.b_ai, "poller": self.b_poller, "cameras": self.b_cameras,  # info: "npu" : self . b_npu , "ai" :
                         "controls": self.b_controls, "settings": self.b_settings, "running": self.b_running,  # info: "controls" : self . b_controls , "settings" :
                         "network": self.b_network, "ssh": self.b_ssh, "migration": self.b_migration,  # info: "network" : self . b_network , "ssh" :
                         "aws": self.b_aws, "automations": self.b_automations, "scheduler": self.b_scheduler, "telemetry": self.b_telemetry, "radio": self.b_radio}  # info: builders
        self.refreshers = {"energy": self.r_energy, "weather": self.r_weather, "system": self.r_system,  # info: self . refreshers = { "energy" : self
                           "npu": self.r_npu, "ai": self.r_ai, "poller": self.r_poller, "cameras": self.r_cameras,  # info: "npu" : self . r_npu , "ai" :
                           "controls": self.r_controls, "settings": lambda: None, "running": self.r_running,  # info: "controls" : self . r_controls , "settings" :
                           "network": self.r_network, "ssh": lambda: None, "migration": lambda: None,  # info: "network" : self . r_network , "ssh" :
                           "aws": lambda: None, "automations": self.r_automations, "scheduler": self.r_scheduler, "telemetry": self.r_telemetry, "radio": self.r_radio}  # info: refreshers
        self.page_boxes, self.built = {}, set()  # info: self . page_boxes , self . built =
        self.cam_tiles = {}  # info: self . cam_tiles = { }
        for name, title in PAGES:  # info: for name , title in PAGES :
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=14, margin_bottom=14,  # info: set box
                          margin_start=16, margin_end=16)  # info: set margin_start
            self.page_boxes[name] = box  # info: self . page_boxes [ name ] = box
            if self.check:  # info: if self . check :
                self.ensure_built(name)  # --check builds every widget up front
            sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)  # info: set sc
            sc.set_child(box)  # info: sc . set_child ( box )
            self.stack.add_titled(sc, name, title)  # info: self . stack . add_titled ( sc ,
        start = self.s.get("start_page", "energy")  # info: set start
        if start == "cameras" or start not in dict(PAGES):  # info: if start == "cameras" or start not in
            start = "energy"  # info: set start
        self.stack.set_visible_child_name(start)  # info: self . stack . set_visible_child_name ( start )
        self.ensure_built(start)  # info: self . ensure_built ( start )
        self.stack.connect("notify::visible-child-name", self.on_page)  # info: self . stack . connect ( "notify::visible-child-name" ,

    def ensure_built(self, name):  # info: def ensure_built
        """Pages are built on first visit in the window (keeps RSS down); --check builds all of them."""  # info: """Pages are built on first visit in the window (keeps RSS down); --check builds all of them."""
        if name not in self.built:  # info: if name not in self . built :
            self.built.add(name)  # info: self . built . add ( name )
            if name in ("running", "network", "ssh", "migration", "settings"):  # info: if name in ( "running" , "network" ,
                self.ensure_redact()  # info: self . ensure_redact ( )
            self.builders[name](self.page_boxes[name])  # info: self . builders [ name ] ( self

    # ----------------------------------------------------------- energy
    def b_energy(self, box):  # info: def b_energy
        o, i = section("Batteries (same three bars as poller-dashboard.py)")  # info: o , i = section ( "Batteries (same three bars as poller-dashboard.py)" )
        self.bar_b1 = BarRow(i, "B1", "river2pro")  # info: self . bar_b1 = BarRow ( i ,
        self.bar_b2 = BarRow(i, "B2", "delta2")  # info: self . bar_b2 = BarRow ( i ,
        self.bar_b3 = BarRow(i, "B3", "System (laptop)")  # info: self . bar_b3 = BarRow ( i ,
        self.energy_alert = lbl("", "rr-fail", wrap=True)
        self.energy_alert.set_visible(False)
        i.append(self.energy_alert)
        self.exp_lbl = lbl("", "dim-label", wrap=True)  # info: self . exp_lbl = lbl ( "" ,
        i.append(self.exp_lbl)  # info: i . append ( self . exp_lbl )
        self.energy_refresh_lbl = lbl("", "dim-label")
        i.append(self.energy_refresh_lbl)
        box.append(o)  # info: box . append ( o )
        o, i = section("Watts (Energy/watts/*-last.json)")  # info: o , i = section ( "Watts (Energy/watts/*-last.json)" )
        self.watts_grid = Gtk.Grid(column_spacing=18, row_spacing=4)  # info: self . watts_grid = Gtk . Grid (
        heads = ["device", "solar in", "AC out", "AC in", "USB-C out", "charge src", "source", "at"]  # info: set heads
        for c, h in enumerate(heads):  # info: for c , h in enumerate ( heads
            self.watts_grid.attach(lbl(f"<b>{h}</b>", markup=True), c, 0, 1, 1)  # info: self . watts_grid . attach ( lbl (
        self.watt_cells = {}  # info: self . watt_cells = { }
        for r, dev in enumerate(("river2pro", "delta2"), start=1):  # info: for r , dev in enumerate ( (
            self.watts_grid.attach(lbl(dev), 0, r, 1, 1)  # info: self . watts_grid . attach ( lbl (
            cells = []  # info: set cells
            for c in range(1, len(heads)):  # info: for c in range ( 1 , len
                w = lbl("—")  # info: set w
                self.watts_grid.attach(w, c, r, 1, 1)  # info: self . watts_grid . attach ( w ,
                cells.append(w)  # info: cells . append ( w )
            self.watt_cells[dev] = cells  # info: self . watt_cells [ dev ] = cells
        i.append(self.watts_grid)  # info: i . append ( self . watts_grid )
        box.append(o)  # info: box . append ( o )
        o, i = section("Poller status line (latest ENERGY heartbeat, automations_current.log)")  # info: o , i = section ( "Poller status line (latest ENERGY heartbeat, automations_current.log)" )
        self.status_line = lbl("", "rr-mono", wrap=True, select=True)  # info: self . status_line = lbl ( "" ,
        i.append(self.status_line)  # info: i . append ( self . status_line )
        self.summary_lbl = lbl("", "rr-mono dim-label", wrap=True, select=True)  # info: self . summary_lbl = lbl ( "" ,
        i.append(self.summary_lbl)  # info: i . append ( self . summary_lbl )
        self.sun_lbl = lbl("", wrap=True)  # info: self . sun_lbl = lbl ( "" ,
        i.append(self.sun_lbl)  # info: i . append ( self . sun_lbl )
        box.append(o)  # info: box . append ( o )

    def r_energy(self):  # info: def r_energy
        e = src.energy(self.paths)  # info: set e
        lg = self.logd()  # info: set lg
        stale = self.s["stale_after_sec"]  # info: set stale
        alerts = []
        for bar, dev, nice in ((self.bar_b1, "river2pro", "B1 River 2 Pro"),
                               (self.bar_b2, "delta2", "B2 Delta 2")):
            d = e[dev]
            st = " · STALE" if d["age"] is not None and d["age"] > stale else ""
            bar.set(d["soc"], f"{src.fmt_age(d['age'])}{st} · source {d['source'] or '—'} · {lg['summary'].get(dev, '')}")
            soc = d["soc"]
            if isinstance(soc, (int, float)):
                if soc <= 10:
                    alerts.append(f"{nice} CRITICAL at {soc:.1f}%")
                elif soc <= 20:
                    alerts.append(f"{nice} LOW at {soc:.1f}%")
            if d["age"] is not None and d["age"] > stale:
                alerts.append(f"{nice} sample STALE ({src.fmt_age(d['age'])})")
        lap = e["laptop"]
        if lap:
            self.bar_b3.set(lap[0], f"System (laptop) · {lap[1]} · {'AC' if lap[2] else 'on battery'} (sysfs)")
            if isinstance(lap[0], (int, float)) and lap[0] <= 20 and not lap[2]:
                alerts.append(f"B3 laptop LOW at {float(lap[0]):.1f}% (on battery)")
        else:
            self.bar_b3.set(None, "no laptop battery found in /sys/class/power_supply")
        if hasattr(self, "energy_alert"):
            self.energy_alert.set_text("  ·  ".join(alerts) if alerts else "")
            self.energy_alert.set_visible(bool(alerts))
            if alerts and any("CRITICAL" in a for a in alerts):
                self.energy_alert.remove_css_class("rr-warn")
                self.energy_alert.add_css_class("rr-fail")
            elif alerts:
                self.energy_alert.remove_css_class("rr-fail")
                self.energy_alert.add_css_class("rr-warn")
        if hasattr(self, "energy_refresh_lbl"):
            self.energy_refresh_lbl.set_text(f"Energy page refreshed {now_hst()} · interval {self.s['refresh_sec']}s")
        exp = lg.get("b3_expansion")
        self.exp_lbl.set_text(f"Delta2 expansion battery (status line B3): {exp}" if exp else
                              "Delta2 expansion battery: not in the current status line (status line B3 absent)")
        for dev, cells in self.watt_cells.items():  # info: for dev , cells in self . watt_cells
            d = e[dev]  # info: set d
            vals = [d["solar_in"], d["ac_out"], d["ac_in"], d["usbc_out"]]  # info: set vals
            txt = [f"{v:g} W" if isinstance(v, (int, float)) else "—" for v in vals]  # info: set txt
            txt += [str(d["charge_source"] or "—"), str(d["source"] or "—"), src.hst(d["watts_at"])]  # info: set txt
            for w, t in zip(cells, txt):  # info: for w , t in zip ( cells
                w.set_text(t)  # info: w . set_text ( t )
        self.status_line.set_text((lg["energy_line_at"] + "  " + lg["energy_line"]).strip() or "no ENERGY line in the log tail yet")  # info: self . status_line . set_text ( ( lg
        self.summary_lbl.set_text("\n".join(f"SUMMARY={k} {v}" for k, v in lg["summary"].items()))  # info: self . summary_lbl . set_text ( "\n" .
        self.sun_lbl.set_text(f"SUN  {self._solar or '—'}")  # info: self . sun_lbl . set_text ( f" SUN
        self.report["energy"] = {"B1": e["river2pro"]["soc"], "B2": e["delta2"]["soc"], "B3_laptop": lap,  # info: self . report [ "energy" ] = {
                                 "status_line": bool(lg["energy_line"]), "b3_expansion": exp}  # info: "status_line" : bool ( lg [ "energy_line" ]

    # ----------------------------------------------------------- weather
    def b_weather(self, box):  # info: def b_weather
        o, i = section("Sun (NOAA solar table, same as dashboard SUN row)")  # info: o , i = section ( "Sun (NOAA solar table, same as dashboard SUN row)" )
        self.w_sun = lbl("", "rr-big", wrap=True)  # info: self . w_sun = lbl ( "" ,
        i.append(self.w_sun)  # info: i . append ( self . w_sun )
        box.append(o)  # info: box . append ( o )
        o, i = section("Stations — hourly NWS wind report")  # info: o , i = section (
        row = Gtk.Box(spacing=6)
        self.w_island_btns = {}
        self._island_lock = False
        current = src.island_label(self.s.get("weather_zone") or "Big Island")
        for label, _tok in src.ISLANDS:
            b = Gtk.ToggleButton(label=label)
            b.add_css_class("rr-island")
            b.set_active(label == current)
            row.append(b)
            self.w_island_btns[label] = b
        i.append(row)
        for label, b in self.w_island_btns.items():
            b.connect("toggled", self.on_island, label)
        self.w_station_sum = lbl("", wrap=True)
        self.w_stations = lbl("", "rr-mono", select=True)
        i.append(self.w_station_sum)
        i.append(self.w_stations)
        box.append(o)
        o, i = section("Zone forecast")  # info: o , i = section ( "Zone forecast" )
        self.w_zone = lbl("", "heading")  # info: self . w_zone = lbl ( "" ,
        self.w_today = lbl("", wrap=True, select=True)  # info: self . w_today = lbl ( "" ,
        self.w_tonight = lbl("", wrap=True, select=True)  # info: self . w_tonight = lbl ( "" ,
        self.w_adv = lbl("", "rr-warn", wrap=True)  # info: self . w_adv = lbl ( "" ,
        self.w_meta = lbl("", "dim-label", wrap=True)  # info: self . w_meta = lbl ( "" ,
        for w in (self.w_zone, self.w_adv, self.w_today, self.w_tonight, self.w_meta):  # info: for w in ( self . w_zone ,
            i.append(w)  # info: i . append ( w )
        b = Gtk.Button(label="Open weather reports folder", halign=Gtk.Align.START)  # info: set b
        b.connect("clicked", lambda *_: self.open_path(self.paths.weather_l0.parent))  # info: b . connect ( "clicked" , lambda *
        i.append(b)  # info: i . append ( b )
        box.append(o)  # info: box . append ( o )

    @property  # info: decorator property
    def _solar(self):  # info: def _solar
        if getattr(self, "_solar_at", 0) < time.time() - 30:  # info: if getattr ( self , "_solar_at" , 0
            try:  # info: try :
                self._solar_v = self.pw.aeyes_solar_state() if self.pw else None  # info: self . _solar_v = self . pw .
            except Exception:  # info: except Exception :
                self._solar_v = None  # info: self . _solar_v = None
            self._solar_at = time.time()  # info: self . _solar_at = time . time (
        return self._solar_v  # info: return self . _solar_v

    def on_island(self, btn, label):  # info: def on_island
        if self._island_lock:  # info: if self . _island_lock :
            return  # info: return
        if not btn.get_active():  # info: if not btn . get_active ( ) :
            if not any(b.get_active() for b in self.w_island_btns.values()):  # info: if not any (
                self._island_lock = True  # info: self . _island_lock = True
                btn.set_active(True)  # info: btn . set_active ( True )
                self._island_lock = False  # info: self . _island_lock = False
            return  # info: return
        self._island_lock = True  # info: self . _island_lock = True
        for name, other in self.w_island_btns.items():  # info: for name , other in self . w_island_btns
            if name != label:  # info: if name != label :
                other.set_active(False)  # info: other . set_active ( False )
        self._island_lock = False  # info: self . _island_lock = False
        self.s["weather_zone"] = label  # info: self . s [ "weather_zone" ] = label
        try:  # info: try :
            rr_settings.save(self.s)  # info: rr_settings . save ( self . s )
            self.toast(f"Weather: {label}")  # info: self . toast ( f" Weather: { label
        except Exception as e:  # info: except Exception as e :
            self.toast(f"Save failed: {e}")  # info: self . toast ( f" Save failed: { e
        self.safe(self.r_weather)  # info: self . safe ( self . r_weather )

    def r_weather(self):  # info: def r_weather
        w = src.weather(self.paths, self.s.get("weather_zone") or "Big Island", None)  # info: set w
        self.w_sun.set_text(self._solar or "solar table not available")  # info: self . w_sun . set_text ( self .
        label = w.get("island") or src.island_label(self.s.get("weather_zone") or "Big Island")  # info: set label
        self._island_lock = True  # info: self . _island_lock = True
        for name, b in getattr(self, "w_island_btns", {}).items():  # info: for name , b in getattr (
            if b.get_active() != (name == label):  # info: if b . get_active ( ) !=
                b.set_active(name == label)  # info: b . set_active ( name == label )
        self._island_lock = False  # info: self . _island_lock = False
        st = w.get("stations") or {}  # info: set st
        spots = []  # info: set spots
        if label == "Big Island":  # info: if label == "Big Island" :
            spots = [s for s in (src.station_spot(st, "Hilo AP"), src.station_spot(st, "Kona Intl")) if s]  # info: set spots
        elif label == "Maui":  # info: elif label == "Maui" :
            spots = [s for s in (src.station_spot(st, "Kahului AP"),) if s]  # info: set spots
        elif label == "Oahu":  # info: elif label == "Oahu" :
            spots = [s for s in (src.station_spot(st, "Honolulu AP"),) if s]  # info: set spots
        elif label == "Kauai":  # info: elif label == "Kauai" :
            spots = [s for s in (src.station_spot(st, "Lihue"),) if s]  # info: set spots
        bits = [f"{st.get('reporting', 0)} reporting · {st.get('silent', 0)} silent"] + spots  # info: set bits
        if st.get("collected"):  # info: if st . get ( "collected" ) :
            bits.append(f"collected {st['collected']}")  # info: bits . append (
        self.w_station_sum.set_text(" · ".join(bits) if st.get("rows") else "Hourly station report is not on disk yet.")  # info: self . w_station_sum . set_text (
        self.w_stations.set_text(src.format_stations(st) if st.get("rows") else "")  # info: self . w_stations . set_text (
        self.w_zone.set_text(label)  # info: self . w_zone . set_text ( label )
        self.w_today.set_markup(f"<b>Today:</b> {esc(w['today'] or '—')}")  # info: self . w_today . set_markup ( f" <b>Today:</b>
        self.w_tonight.set_markup(f"<b>Tonight:</b> {esc(w['tonight'] or '—')}")  # info: self . w_tonight . set_markup ( f" <b>Tonight:</b>
        self.w_adv.set_text("\n".join(w["advisories"]))  # info: self . w_adv . set_text ( "\n" .
        if w.get("collected"):  # info: if w . get ( "collected" ) :
            meta = f"ZFP collected {w['collected']}"  # info: set meta
        else:  # info: else :
            meta = "Zone forecast file is not on disk yet (zfp_zone_forecast_current.md). The station list above is the live report."  # info: set meta
        if w.get("state_generated"):  # info: if w . get ( "state_generated" ) :
            meta += f" · State report generated {w['state_generated']}"  # info: set meta
        self.w_meta.set_text(meta)  # info: self . w_meta . set_text ( meta )
        self.report["weather"] = {"zone": label, "today": bool(w["today"]), "solar": bool(self._solar),  # info: self . report [ "weather" ] = {
                                 "stations": st.get("reporting", 0)}  # info: "stations" : st . get ( "reporting" , 0 ) }

    # ----------------------------------------------------------- system
    def b_system(self, box):  # info: def b_system
        o, i = section("Host (System/last/host_current.json)")  # info: o , i = section ( "Host (System/last/host_current.json)" )
        self.bar_cpu = BarRow(i, "CPU", "", scale="usage")  # info: self . bar_cpu = BarRow ( i ,
        self.bar_mem = BarRow(i, "RAM", "", scale="usage")  # info: self . bar_mem = BarRow ( i ,
        i.append(lbl("Green under 50% · amber from 50% · red at 80% and above.", "dim-label"))
        self.sys_extra = lbl("", wrap=True)  # info: self . sys_extra = lbl ( "" ,
        i.append(self.sys_extra)  # info: i . append ( self . sys_extra )
        box.append(o)  # info: box . append ( o )
        o, i = section("Poller SYSTEM line (automations_current.log)")  # info: o , i = section ( "Poller SYSTEM line (automations_current.log)" )
        self.sys_line = lbl("", "rr-mono", wrap=True, select=True)  # info: self . sys_line = lbl ( "" ,
        i.append(self.sys_line)  # info: i . append ( self . sys_line )
        box.append(o)  # info: box . append ( o )

    def r_system(self):  # info: def r_system
        s = src.system(self.paths)  # info: set s
        gb = lambda b: f"{b / 1e9:.1f} GB" if isinstance(b, (int, float)) else "—"  # noqa: E731
        self.bar_cpu.set(s["cpu"], f"5-min avg {s['five_cpu']:.1f}%" if isinstance(s["five_cpu"], (int, float)) else "")  # info: self . bar_cpu . set ( s [
        self.bar_mem.set(s["mem"], f"available {gb(s['mem_avail'])} of {gb(s['mem_total'])}"  # info: self . bar_mem . set ( s [
                         + (f" · 5-min avg {s['five_mem']:.1f}%" if isinstance(s['five_mem'], (int, float)) else ""))  # info: call +
        ld = " / ".join(f"{x:.2f}" if isinstance(x, (int, float)) else "—" for x in s["load"])  # info: set ld
        self.sys_extra.set_text(f"load 1/5/15: {ld} · host {s['host'] or '—'} · sampled {src.hst(s['at'])} ({src.fmt_age(s['age'])})")  # info: self . sys_extra . set_text ( f" load 1/5/15:
        self.sys_line.set_text(self.logd()["system_line"] or "—")  # info: self . sys_line . set_text ( self .
        self.report["system"] = {"cpu": s["cpu"], "mem": s["mem"]}  # info: self . report [ "system" ] = {

    # ----------------------------------------------------------- npu
    def b_npu(self, box):  # info: def b_npu
        o, i = section("NPU / FastFlowLM (passive: /dev/accel, /proc, lock holder file)")  # info: o , i = section ( "NPU / FastFlowLM (passive: /dev/accel, /proc, lock holder file)" )
        self.npu_lbl = lbl("", wrap=True, select=True)  # info: self . npu_lbl = lbl ( "" ,
        i.append(self.npu_lbl)  # info: i . append ( self . npu_lbl )
        box.append(o)  # info: box . append ( o )
        o, i = section("npu-status.sh (read-only script, run on request at nice 10)")  # info: o , i = section ( "npu-status.sh (read-only script, run on request at nice 10)" )
        self.npu_btn = Gtk.Button(label="Run npu-status.sh", halign=Gtk.Align.START)  # info: self . npu_btn = Gtk . Button (
        self.npu_btn.connect("clicked", self.run_npu_status)  # info: self . npu_btn . connect ( "clicked" ,
        i.append(self.npu_btn)  # info: i . append ( self . npu_btn )
        self.npu_out = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)  # info: self . npu_out = Gtk . TextView (
        self.npu_out.set_size_request(-1, 220)  # info: self . npu_out . set_size_request ( - 1
        i.append(self.npu_out)  # info: i . append ( self . npu_out )
        box.append(o)  # info: box . append ( o )

    def r_npu(self):  # info: def r_npu
        n = src.npu(self.paths, self.argvs(), int(self.s.get("flm_port", 52625)))  # info: set n
        self.npu_lbl.set_text(f"accel devices: {', '.join(n['accel']) or 'none'}\nFLM: {n['state']}\ninference lock: {n['lock']}")  # info: self . npu_lbl . set_text ( f" accel devices:
        self.report["npu"] = n  # info: self . report [ "npu" ] = n

    def run_npu_status(self, *_):  # info: def run_npu_status
        self.npu_btn.set_sensitive(False)  # info: self . npu_btn . set_sensitive ( False )
        self.npu_out.get_buffer().set_text("running npu-status.sh …")  # info: self . npu_out . get_buffer ( ) .

        def done(out, rc):  # info: def done
            self.npu_out.get_buffer().set_text(f"{out}\n[exit {rc} · {now_hst()}]")  # info: self . npu_out . get_buffer ( ) .
            self.npu_btn.set_sensitive(True)  # info: self . npu_btn . set_sensitive ( True )
        spawn(["nice", "-n", "10", "bash", str(self.paths.npu_status_sh)], done, capture=True)  # info: call spawn

    # ----------------------------------------------------------- ai
    def b_ai(self, box):  # info: def b_ai
        o, i = section("AI inference log (Logs/AI/Inference/inference_current.jsonl — lengths/timings only)")  # info: o , i = section ( "AI inference log (Logs/AI/Inference/inference_current.jsonl — lengths/timings only)" )
        self.ai_lbl = lbl("", wrap=True, select=True)  # info: self . ai_lbl = lbl ( "" ,
        i.append(self.ai_lbl)  # info: i . append ( self . ai_lbl )
        box.append(o)  # info: box . append ( o )
        o, i = section("AI processing report (head of ai-processing-report_current.md)")  # info: o , i = section ( "AI processing report (head of ai-processing-report_current.md)" )
        self.ai_rep = lbl("", "rr-mono", wrap=True, select=True)  # info: self . ai_rep = lbl ( "" ,
        i.append(self.ai_rep)  # info: i . append ( self . ai_rep )
        box.append(o)  # info: box . append ( o )

    def r_ai(self):  # info: def r_ai
        a = src.ai_summary(self.paths)  # info: set a
        if not a.get("present"):  # info: if not a . get ( "present" )
            self.ai_lbl.set_text("inference_current.jsonl not found")  # info: self . ai_lbl . set_text ( "inference_current.jsonl not found" )
            self.report["ai"] = {"present": False}  # info: self . report [ "ai" ] = {
            return  # info: return
        fmt = lambda d: ", ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda kv: -kv[1]))  # noqa: E731
        last = a["last"] or {}  # info: set last
        lat = f"avg {a['lat_avg']:.0f} ms · max {a['lat_max']} ms" if a["lat_avg"] is not None else "—"  # info: set lat
        self.ai_lbl.set_text(  # info: self . ai_lbl . set_text (
            f"requests in current log: {a['count']} (today {a['today']}) · fallbacks {a['fallbacks']} · non-zero exits {a['errors']}\n"  # info: f" requests in current log: { a [ 'count' ] }
            f"latency: {lat}\nroutes: {fmt(a['routes'])}\nmodels: {fmt(a['models'])}\ncallers: {fmt(a['callers'])}\n"  # info: f" latency: { lat } \nroutes: { fmt
            f"last: {last.get('ts', '—')} {last.get('route', '')} {last.get('model', '')} {last.get('latency_ms', '')} ms "  # info: f" last: { last . get ( 'ts'
            f"exit {last.get('exit_code', '')}\nrouting log rows: {a['routing_rows']}")  # info: f" exit { last . get ( 'exit_code'
        self.ai_rep.set_text(a.get("report_head") or "—")  # info: self . ai_rep . set_text ( a .
        self.report["ai"] = {"count": a["count"], "routes": a["routes"]}  # info: self . report [ "ai" ] = {

    # ----------------------------------------------------------- poller / services
    def b_poller(self, box):  # info: def b_poller
        o, i = section("Services (same PASS/WARN/FAIL rule as poller-dashboard.py)")  # info: o , i = section ( "Services (same PASS/WARN/FAIL rule as poller-dashboard.py)" )
        self.svc_grid = Gtk.Grid(column_spacing=16, row_spacing=4)  # info: self . svc_grid = Gtk . Grid (
        self.svc_cells = []  # info: self . svc_cells = [ ]
        for r, (label, *_x) in enumerate(src.SERVICES):  # info: for r , ( label , * _x
            self.svc_grid.attach(lbl(f"<b>{esc(label)}</b>", markup=True), 0, r, 1, 1)  # info: self . svc_grid . attach ( lbl (
            b, d = lbl("…"), lbl("", "dim-label")  # info: b , d = lbl ( "…" )
            self.svc_grid.attach(b, 1, r, 1, 1)  # info: self . svc_grid . attach ( b ,
            self.svc_grid.attach(d, 2, r, 1, 1)  # info: self . svc_grid . attach ( d ,
            self.svc_cells.append((b, d))  # info: self . svc_cells . append ( ( b
        i.append(self.svc_grid)  # info: i . append ( self . svc_grid )
        self.log_state = lbl("", "dim-label")  # info: self . log_state = lbl ( "" ,
        i.append(self.log_state)  # info: i . append ( self . log_state )
        row = Gtk.Box(spacing=8)  # info: set row
        b1 = Gtk.Button(label="Open poller dashboard (read-only terminal)")  # info: set b1
        b1.connect("clicked", self.open_dashboard)  # info: b1 . connect ( "clicked" , self .
        b2 = Gtk.Button(label="Open Logs folder")  # info: set b2
        b2.connect("clicked", lambda *_: self.open_path(self.paths.logs_dir))  # info: b2 . connect ( "clicked" , lambda *
        row.append(b1)  # info: row . append ( b1 )
        row.append(b2)  # info: row . append ( b2 )
        i.append(row)  # info: i . append ( row )
        box.append(o)  # info: box . append ( o )
        o, i = section("Recent poller log (formatted with poller-watch.py format_line)")  # info: o , i = section ( "Recent poller log (formatted with poller-watch.py format_line)" )
        self.log_view = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.NONE)  # info: self . log_view = Gtk . TextView (
        self.log_view.set_size_request(-1, 360)  # info: self . log_view . set_size_request ( - 1
        i.append(self.log_view)  # info: i . append ( self . log_view )
        box.append(o)  # info: box . append ( o )

    def r_poller(self):  # info: def r_poller
        rows = src.services(self.argvs())  # info: set rows
        for (b, d), (_label, state, detail) in zip(self.svc_cells, rows):  # info: for ( b , d ) , (
            b.set_text(f"● {state}")  # info: b . set_text ( f" ● { state
            for c in ("rr-pass", "rr-warn", "rr-fail"):  # info: for c in ( "rr-pass" , "rr-warn" ,
                b.remove_css_class(c)  # info: b . remove_css_class ( c )
            b.add_css_class(badge_css(state))  # info: b . add_css_class ( badge_css ( state )
            d.set_text(detail)  # info: d . set_text ( detail )
        lg = self.logd()  # info: set lg
        la = lg.get("log_age")  # info: set la
        self.log_state.set_text(f"log: {int(la)}s since last write" if la is not None else "log: missing")  # info: self . log_state . set_text ( f" log:
        self.log_view.get_buffer().set_text("\n".join(src.formatted_log(self.pw, lg["lines"], int(self.s["log_lines"]))))  # info: self . log_view . get_buffer ( ) .
        self.report["poller"] = {r[0]: r[1] for r in rows}  # info: self . report [ "poller" ] = {

    def open_dashboard(self, *_):  # info: def open_dashboard
        dash = str(self.paths.poller_dashboard)  # info: set dash
        if any(dash in " ".join(a) or a[1:2] and a[1].endswith("poller-dashboard.py") for _p, a in src.proc_argvs()):  # info: if any ( dash in " " . join
            self.toast("poller-dashboard.py is already open — leaving it")  # info: self . toast ( "poller-dashboard.py is already open — leaving it" )
            return  # info: return
        spawn(["ptyxis", "--new-window", "-T", "RootRecord poller — rootserver", "-x", f"/usr/bin/python3 '{dash}'"])  # info: call spawn

    # ----------------------------------------------------------- cameras
    def b_cameras(self, box):  # info: def b_cameras
        self.cam_box = box  # info: self . cam_box = box
        bar = Gtk.Box(spacing=10)  # info: set bar
        bar.append(self.cam_toggle_btn(big=True))  # info: bar . append ( self . cam_toggle_btn (
        bar.append(lbl("click to turn the camera viewer on / off (this session; Settings → Panel → Save settings keeps it)",  # info: bar . append ( lbl ( "click to turn the camera viewer on / off (this session; Settings → Panel → Save settings
                       "dim-label", wrap=True))  # info: "dim-label" , wrap = True ) )
        box.append(bar)  # info: box . append ( bar )
        self.cam_off = lbl("Camera viewer is OFF (default). Press the button above (also first on Settings → Panel).\n"  # info: self . cam_off = lbl ( "Camera viewer is OFF (default). Press the button above (also first on Settings → Panel
                           "While off the panel does no camera work: no timer, no image loading, no streams.",  # info: "While off the panel does no camera work: no timer, no image loading, no streams." ,
                           "dim-label", wrap=True)  # info: "dim-label" , wrap = True )
        box.append(self.cam_off)  # info: box . append ( self . cam_off )
        self.cam_flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, min_children_per_line=2, max_children_per_line=2,  # info: self . cam_flow = Gtk . FlowBox (
                                    column_spacing=10, row_spacing=10, homogeneous=True)  # info: set column_spacing
        self.cam_tiles = {}  # info: self . cam_tiles = { }
        for c in self.cams:  # info: for c in self . cams :
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)  # info: set v
            pic = Gtk.Picture(content_fit=Gtk.ContentFit.CONTAIN, can_shrink=True)  # info: set pic
            pic.set_size_request(360, 203)  # info: pic . set_size_request ( 360 , 203 )
            cap = lbl(c, "dim-label")  # info: set cap
            v.append(pic)  # info: v . append ( pic )
            v.append(cap)  # info: v . append ( cap )
            self.cam_flow.append(v)  # info: self . cam_flow . append ( v )
            self.cam_tiles[c] = (v, pic, cap)  # info: self . cam_tiles [ c ] = (
        box.append(self.cam_flow)  # info: box . append ( self . cam_flow )
        self.cam_note = lbl("", "dim-label", wrap=True)  # info: self . cam_note = lbl ( "" ,
        box.append(self.cam_note)  # info: box . append ( self . cam_note )
        self.cam_flow.set_visible(False)  # info: self . cam_flow . set_visible ( False )

    def r_cameras(self):  # info: def r_cameras
        """Called only when the Cameras page is visible (or once in --check with the viewer ON)."""  # info: """Called only when the Cameras page is visible (or once in --check with the viewer ON)."""
        on = self.camera_viewer_on  # info: set on
        for b in self.cam_toggles:  # info: for b in self . cam_toggles :
            if b.get_active() != on:  # info: if b . get_active ( ) != on
                b.rr_set(on)  # info: b . rr_set ( on )
        self.cam_off.set_visible(not on)  # info: self . cam_off . set_visible ( not on
        self.cam_flow.set_visible(on)  # info: self . cam_flow . set_visible ( on )
        if not on:  # info: if not on :
            self.cam_note.set_text("")  # info: self . cam_note . set_text ( "" )
            self.report["cameras"] = {"viewer": "off"}  # info: self . report [ "cameras" ] = {
            return  # info: return
        enabled = [c for c in self.cams if self.s["cameras"].get(c, {}).get("enabled", True)]  # info: set enabled
        for c, (v, _p, _cap) in self.cam_tiles.items():  # info: for c , ( v , _p ,
            v.get_parent().set_visible(c in enabled)  # info: v . get_parent ( ) . set_visible (
        stills = src.latest_stills(self.paths, enabled)  # info: set stills
        loaded, missing = [], []  # info: loaded , missing = [ ] , [
        for c in enabled:  # info: for c in enabled :
            _v, pic, cap = self.cam_tiles[c]  # info: _v , pic , cap = self .
            p = stills.get(c)  # info: set p
            label = self.s["cameras"].get(c, {}).get("label", c)  # info: set label
            if p is None:  # info: if p is None :
                missing.append(c)  # info: missing . append ( c )
                cap.set_text(f"{label} · no still on disk")  # info: cap . set_text ( f" { label }
                self.fetch_live(c)  # info: self . fetch_live ( c )
                continue  # info: continue
            try:  # info: try :
                src.STATS["camera_files_opened"] += 1  # info: src . STATS [ "camera_files_opened" ] += 1
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p), 640, 360, True)  # info: set pb
                pic.set_paintable(Gdk.Texture.new_for_pixbuf(pb))  # info: pic . set_paintable ( Gdk . Texture .
                cap.set_text(f"{label} · {src.still_time(p)} · {p.name}")  # info: cap . set_text ( f" { label }
                loaded.append(c)  # info: loaded . append ( c )
            except GLib.Error as e:  # info: except GLib . Error as e :
                cap.set_text(f"{label} · still unreadable ({e.message[:60]}) — expected while hardware work is ongoing")  # info: cap . set_text ( f" { label }
                missing.append(c)  # info: missing . append ( c )
        self.cam_note.set_text(f"Stills from {self.paths.camera_images} · refresh every {self.s['camera_refresh_sec']} s "  # info: self . cam_note . set_text ( f" Stills from
                               f"while this page is visible · missing/flapping stills are expected during camera work")  # info: f" while this page is visible · missing/flapping stills are expected during camera work " )
        self.report["cameras"] = {"viewer": "on", "enabled": enabled, "loaded": loaded, "missing": missing}  # info: self . report [ "cameras" ] = {

    def fetch_live(self, cam: str):  # info: def fetch_live
        """Fallback when a camera has no still on disk: one local still from cam_server (visible page only)."""  # info: """Fallback when a camera has no still on disk: one local still from cam_server (visible page only)."""
        if not self.s.get("camera_live_fallback") or cam in self.cam_fetching or self.check:  # info: if not self . s . get (
            return  # info: return
        still = "current.jpg" if cam == "ch1" else f"current_{cam}.jpg"  # info: set still
        url = self.s.get("camera_live_fallback_url", "").replace("{still}", still)  # info: set url
        if not url.startswith("http://127.0.0.1:"):  # info: if not url . startswith ( "http://127.0.0.1:" )
            return  # info: return
        self.cam_fetching.add(cam)  # info: self . cam_fetching . add ( cam )

        def work():  # info: def work
            import urllib.request  # info: import urllib . request
            data = None  # info: set data
            try:  # info: try :
                src.STATS["camera_http_fetches"] += 1  # info: src . STATS [ "camera_http_fetches" ] += 1
                with urllib.request.urlopen(url, timeout=8) as r:  # info: with urllib . request . urlopen ( url
                    data = r.read(4_000_000)  # info: set data
            except Exception:  # info: except Exception :
                data = None  # info: set data
            GLib.idle_add(self._live_done, cam, data)  # info: GLib . idle_add ( self . _live_done ,
        threading.Thread(target=work, daemon=True).start()  # info: threading . Thread ( target = work ,

    def _live_done(self, cam, data):  # info: def _live_done
        self.cam_fetching.discard(cam)  # info: self . cam_fetching . discard ( cam )
        if data and self.camera_viewer_on and self.stack.get_visible_child_name() == "cameras":  # info: if data and self . camera_viewer_on and self
            try:  # info: try :
                loader = GdkPixbuf.PixbufLoader()  # info: set loader
                loader.set_size(640, 360)  # info: loader . set_size ( 640 , 360 )
                loader.write(data)  # info: loader . write ( data )
                loader.close()  # info: loader . close ( )
                _v, pic, cap = self.cam_tiles[cam]  # info: _v , pic , cap = self .
                pic.set_paintable(Gdk.Texture.new_for_pixbuf(loader.get_pixbuf()))  # info: pic . set_paintable ( Gdk . Texture .
                cap.set_text(f"{cam} · local cam_server still (no still on disk)")  # info: cap . set_text ( f" { cam }
            except Exception:  # info: except Exception :
                pass  # info: pass
        return False  # info: return False

    def cam_timer_update(self):  # info: def cam_timer_update
        if "cameras" not in self.built:  # info: if "cameras" not in self . built :
            if self.stack.get_visible_child_name() != "cameras":  # info: if self . stack . get_visible_child_name ( )
                return  # info: return
            self.ensure_built("cameras")  # info: self . ensure_built ( "cameras" )
        want = (self.win is not None and self.camera_viewer_on and self.stack.get_visible_child_name() == "cameras")  # info: set want
        if want and not self.cam_timer_id:  # info: if want and not self . cam_timer_id :
            self.r_cameras()  # info: self . r_cameras ( )
            self.cam_timer_id = GLib.timeout_add_seconds(int(self.s["camera_refresh_sec"]), self._cam_tick)  # info: self . cam_timer_id = GLib . timeout_add_seconds (
        elif not want and self.cam_timer_id:  # info: elif not want and self . cam_timer_id :
            GLib.source_remove(self.cam_timer_id)  # info: GLib . source_remove ( self . cam_timer_id )
            self.cam_timer_id = 0  # info: self . cam_timer_id = 0
        if not want:  # info: if not want :
            for _c, (_v, pic, _cap) in self.cam_tiles.items():  # info: for _c , ( _v , pic ,
                pic.set_paintable(None)  # drop textures when not viewing
            if self.stack.get_visible_child_name() == "cameras":  # info: if self . stack . get_visible_child_name ( )
                self.r_cameras()  # info: self . r_cameras ( )

    def cam_toggle_btn(self, big=False):  # info: def cam_toggle_btn
        b = state_toggle("Camera viewer", self.camera_viewer_on, lambda _b, on: self.set_camera_viewer(on), big=big,  # info: set b
                         tooltip="Off = zero camera work (no timer, no images, no streams). Only changes what this panel shows.")  # info: set tooltip
        self.cam_toggles.append(b)  # info: self . cam_toggles . append ( b )
        return b  # info: return b

    def set_camera_viewer(self, on: bool):  # info: def set_camera_viewer
        self.s["camera_viewer_enabled"] = bool(on)  # info: self . s [ "camera_viewer_enabled" ] = bool
        self.camera_override = None  # info: self . camera_override = None
        for b in self.cam_toggles:  # info: for b in self . cam_toggles :
            if b.get_active() != bool(on):  # info: if b . get_active ( ) != bool
                b.rr_set(on)  # info: b . rr_set ( on )
        self.cam_timer_update()  # info: self . cam_timer_update ( )

    def _cam_tick(self):  # info: def _cam_tick
        self.safe(self.r_cameras)  # info: self . safe ( self . r_cameras )
        return True  # info: return True

    # ----------------------------------------------------------- controls
    def b_controls(self, box):  # info: def b_controls
        o, i = section("Safe, read-only actions")  # info: o , i = section ( "Safe, read-only actions" )
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)  # info: set row
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)  # info: set left
        for text, fn in (("Open Logs folder", lambda *_: self.open_path(self.paths.logs_dir)),  # info: for text , fn in ( ( "Open Logs folder"
                         ("Open Database folder", lambda *_: self.open_path(self.paths.db)),  # info: call (
                         ("Run npu-status.sh (NPU page)", lambda *_: (self.stack.set_visible_child_name("npu"), self.run_npu_status())),  # info: call (
                         ("Open poller dashboard (read-only terminal)", self.open_dashboard)):  # info: call (
            b = Gtk.Button(label=text, halign=Gtk.Align.START)  # info: set b
            b.connect("clicked", fn)  # info: b . connect ( "clicked" , fn )
            left.append(b)  # info: left . append ( b )
        row.append(left)  # info: row . append ( left )
        restart = Gtk.Button(label="Restart everything", halign=Gtk.Align.END, valign=Gtk.Align.CENTER)  # info: set restart
        restart.add_css_class("destructive-action")  # info: restart . add_css_class ( "destructive-action" )
        restart.add_css_class("rr-restart")  # info: restart . add_css_class ( "rr-restart" )
        restart.set_tooltip_text("Stops the poller stack, BLE, and the AWS fetch tunnel, starts them again, then restarts this window. Confirm first.")  # info: restart . set_tooltip_text
        restart.connect("clicked", self.confirm_restart_everything)  # info: restart . connect ( "clicked" , self .
        row.append(restart)  # info: row . append ( restart )
        i.append(row)  # info: i . append ( row )
        box.append(o)  # info: box . append ( o )
        o, i = section("Risky actions — NEED SIGN-OFF (disabled by default; confirm dialog; never run by agents)")  # info: o , i = section ( "Risky actions — NEED SIGN-OFF (disabled by default; confirm dialog; never run by agents)" )
        self.risky_note = lbl("", "rr-warn", wrap=True)  # info: self . risky_note = lbl ( "" ,
        i.append(self.risky_note)  # info: i . append ( self . risky_note )
        self.risky_btns = []  # info: self . risky_btns = [ ]
        for a in self.s.get("risky_actions", []):  # info: for a in self . s . get
            row = Gtk.Box(spacing=8)  # info: set row
            b = Gtk.Button(label=a.get("label", a.get("id")))  # info: set b
            b.add_css_class("destructive-action")  # info: b . add_css_class ( "destructive-action" )
            b.connect("clicked", self.confirm_risky, a)  # info: b . connect ( "clicked" , self .
            row.append(b)  # info: row . append ( b )
            row.append(lbl("needs sign-off", "dim-label"))  # info: row . append ( lbl ( "needs sign-off" ,
            i.append(row)  # info: i . append ( row )
            self.risky_btns.append((b, a))  # info: self . risky_btns . append ( ( b
        box.append(o)  # info: box . append ( o )
        o, i = section("Gated RR_* job flags (current jobs.py view). Turn each one on or off under Settings → Feature Flags. Saving writes rr-flags.conf and does not restart the poller.")  # info: o , i = section ( "Gated RR_* job flags (current jobs.py view). Turn each one on or off under Settings → Featu
        self.gated_lbl = lbl("", "rr-mono", wrap=True, select=True)  # info: self . gated_lbl = lbl ( "" ,
        i.append(self.gated_lbl)  # info: i . append ( self . gated_lbl )
        box.append(o)  # info: box . append ( o )

    def r_controls(self):  # info: def r_controls
        if "controls" not in self.built:  # info: if "controls" not in self . built :
            return  # info: return
        allow = bool(self.s.get("risky_actions_enabled"))  # info: set allow
        for b, a in self.risky_btns:  # info: for b , a in self . risky_btns
            b.set_sensitive(allow and bool(a.get("signed_off")) and bool(a.get("argv")))  # info: b . set_sensitive ( allow and bool (
        self.risky_note.set_text("risky_actions_enabled = false in settings.json → every risky button is disabled." if not allow else  # info: self . risky_note . set_text ( "risky_actions_enabled = false in settings.json → every risky button is disable
                                 "risky_actions_enabled = true: only actions marked signed_off with a command are clickable, each behind a confirm dialog.")  # info: "risky_actions_enabled = true: only actions marked signed_off with a command are clickable, each behind a conf
        g = src.gated_jobs(self.paths)  # info: set g
        self.gated_lbl.set_text("\n".join(f"{jid:<32} {flag:<22} default {'ON' if d == '1' else 'OFF'}" for jid, flag, d in g) or "—")  # info: self . gated_lbl . set_text ( "\n" .
        self.report["controls"] = {"risky_enabled": allow, "gated_flags": len(g),  # info: self . report [ "controls" ] = {
                                   "clickable_risky": sum(1 for b, _a in self.risky_btns if b.get_sensitive())}  # info: "clickable_risky" : sum ( 1 for b ,

    def confirm_risky(self, _btn, action):  # info: def confirm_risky
        if not (self.s.get("risky_actions_enabled") and action.get("signed_off") and action.get("argv")):  # info: if not ( self . s . get
            return  # info: return
        self.confirm(f"Run risky action?", f"{action.get('label')}\n\nCommand: {' '.join(action['argv'])}\n\n"  # info: self . confirm ( f" Run risky action? " ,
                     "This needs Alexander's sign-off. Continue only if it was approved.",  # info: "This needs Alexander's sign-off. Continue only if it was approved." ,
                     "Run", lambda: spawn(list(action["argv"])))  # info: "Run" , lambda : spawn ( list (

    def confirm_restart_everything(self, *_btn):  # info: def confirm_restart_everything
        """Confirm, then hand the restart to a detached script. Does nothing when there is no window."""  # info: """Confirm, then hand the restart to a detached script. Does nothing when there is no window."""
        if self.win is None:  # info: if self . win is None :
            return  # info: return
        script = HERE / "Packaging" / "restart-everything.sh"  # info: set script

        def go():  # info: def go
            subprocess.Popen(  # info: call subprocess . Popen
                ["/bin/bash", str(script)],  # info: [ "/bin/bash" , str ( script ) ] ,
                start_new_session=True,  # info: set start_new_session
                stdin=subprocess.DEVNULL,  # info: set stdin
                stdout=subprocess.DEVNULL,  # info: set stdout
                stderr=subprocess.DEVNULL,  # info: set stderr
                close_fds=True,  # info: set close_fds
            )  # info: )
            self.toast("Restarting the stack and this window…")  # info: self . toast

        self.confirm(  # info: call self . confirm
            "Restart everything?",  # info: "Restart everything?" ,
            "Stops the poller stack and starts it again: poller, tunnel, cameras, weather, relay, and the Hawaii globe. "  # info: "Stops the poller stack and starts it again: poller, tunnel, cameras, weather, relay, and the Hawaii globe. "
            "Restarts the EcoFlow BLE owner and the AWS fetch tunnel. Then closes Root Monitor and opens it again.\n\n"  # info: "Restarts the EcoFlow BLE owner and the AWS fetch tunnel. Then closes Root Monitor and opens it again.\n\n"
            "Ollama stays up. The laptop is not rebooted.",  # info: "Ollama stays up. The laptop is not rebooted." ,
            "Restart", go)  # info: "Restart" , go )

    # ----------------------------------------------------------- settings
    def b_panel_settings(self, box):  # info: def b_panel_settings
        """Settings → Panel sub-page (Root Monitor's own settings.json)."""  # info: """Settings → Panel sub-page (Root Monitor's own settings.json)."""
        s = self.s  # info: set s
        self.set_widgets = {}  # info: self . set_widgets = { }
        if Adw is None:  # info: if Adw is None :
            box.append(lbl("libadwaita not available — edit settings.json directly.", wrap=True))  # info: box . append ( lbl ( "libadwaita not available — edit settings.json directly." ,
            return  # info: return
        page = Adw.PreferencesPage()  # info: set page
        g = Adw.PreferencesGroup(title="Cameras",  # info: set g
                                 description="Buttons only change what THIS PANEL shows. Collectors, grab jobs and the poller are not touched. "  # info: set description
                                             "Changes apply now; press Save settings (bottom) to keep them after a restart.")  # info: "Changes apply now; press Save settings (bottom) to keep them after a restart." )
        row = Adw.ActionRow(title="Camera viewer page", subtitle="Off = zero camera work (no timer, no images, no streams)")  # info: set row
        b = self.cam_toggle_btn()  # info: set b
        row.add_suffix(b)  # info: row . add_suffix ( b )
        row.set_activatable_widget(b)  # info: row . set_activatable_widget ( b )
        g.add(row)  # info: g . add ( row )
        self._spin(g, "camera_refresh_sec", "Camera still refresh (s, only while visible)", 5, 120)  # info: self . _spin ( g , "camera_refresh_sec" ,
        self._switch(g, "camera_live_fallback", "Local still fallback", "Only when a camera has no still on disk, only while visible",  # info: self . _switch ( g , "camera_live_fallback" ,
                     "Still fallback")  # info: "Still fallback" )
        for c in self.cams:  # info: for c in self . cams :
            row = Adw.ActionRow(title=f"Show {c}", subtitle="discovered from Security/Cameras/grab_all.sh")  # info: set row
            b = state_toggle(f"Show {c}", bool(s["cameras"].get(c, {}).get("enabled", True)),  # info: set b
                             lambda _b, on, c=c: s["cameras"].setdefault(c, {}).update(enabled=on))  # info: lambda _b , on , c = c
            row.add_suffix(b)  # info: row . add_suffix ( b )
            row.set_activatable_widget(b)  # info: row . set_activatable_widget ( b )
            g.add(row)  # info: g . add ( row )
        page.add(g)  # info: page . add ( g )
        g = Adw.PreferencesGroup(title="General", description=f"All settings live in {rr_settings.SETTINGS_FILE}")  # info: set g
        self._spin(g, "refresh_sec", "Refresh interval (s)", 2, 60)  # info: self . _spin ( g , "refresh_sec" ,
        self._spin(g, "stale_after_sec", "Mark SOC stale after (s)", 60, 7200)  # info: self . _spin ( g , "stale_after_sec" ,
        self._spin(g, "log_lines", "Poller log lines shown", 10, 200)  # info: self . _spin ( g , "log_lines" ,
        self._entry(g, "weather_zone", "Weather island (Big Island, Maui, Oahu, Kauai)")  # info: self . _entry ( g , "weather_zone" ,
        self._entry(g, "start_page", "Start page (energy, weather, system, npu, ai, poller, automations, telemetry, running, network, ssh, aws, cameras, controls, migration, settings)")
        self._entry(g, "gsk_renderer", "GTK renderer (cairo = lightest; applies on next start)")  # info: self . _entry ( g , "gsk_renderer" ,
        self._switch(g, "starlink_enabled", "Starlink status on the Network page", "helper runs only while that page is visible",  # info: self . _switch ( g , "starlink_enabled" ,
                     "Starlink")  # info: "Starlink" )
        self._spin(g, "starlink_poll_sec", "Starlink poll interval (s, minimum 10)", 10, 300)  # info: self . _spin ( g , "starlink_poll_sec" ,
        self._entry(g, "ssh_mainland_alias", "Mainland SSH Host alias (empty = placeholder)")  # info: self . _entry ( g , "ssh_mainland_alias" ,
        self._entry(g, "aws_fallback_mode", "AWS Fallback mode (dry-run = confirm only; write = SSH flag after confirm)")
        self._entry(g, "aws_fallback_alias", "AWS Fallback SSH Host alias (default rr-aws-ip)")
        self._entry(g, "data_poll_toggle_mode", "Data-poll toggle mode (dry-run = confirm only; write = save intent after confirm)")
        self._entry(g, "data_poll_desired", "Data-poll desired (local = Pacific poll; ml2 = gate LOCAL_DATA_POLL_JOBS)")
        self._switch(g, "data_poll_apply_dropin", "Data-poll write also updates systemd drop-in",
                     "Off = intent/settings only (safe). On = write rr-data-poll.conf.",
                     "Apply drop-in")
        self._switch(g, "data_poll_restart_poller", "Data-poll write restarts poller when gate flips",
                     "Only when apply-dropin wrote a new RR_LOCAL_DATA_POLL that differs from live. Prefer off unless kill-switch must bind now.",
                     "Restart poller")
        self._switch(g, "data_poll_sync_ml2", "Data-poll write soft-syncs ML2 collectors/stream timers",
                     "Exclusive gate peer: Local → stop ml2-collectors+db-stream; ML2 → start them. Never deletes units.",
                     "Sync ML2")
        self._entry(g, "data_poll_ml2_alias", "Data-poll ML2 SSH Host alias (default ml2-ip)")
        page.add(g)  # info: page . add ( g )
        g = Adw.PreferencesGroup(title="Paths (read-only sources)")  # info: set g
        self._entry(g, "database_root", "Database root")  # info: self . _entry ( g , "database_root" ,
        self._entry(g, "pacific_root", "Pacific repo root")  # info: self . _entry ( g , "pacific_root" ,
        page.add(g)  # info: page . add ( g )
        g = Adw.PreferencesGroup(title="Safety — NEEDS SIGN-OFF",  # info: set g
                                 description="Risky actions stay disabled unless this is on AND the action is signed_off in settings.json.")  # info: set description
        row = Adw.ActionRow(title="Allow risky actions (needs sign-off)", subtitle="confirm dialog before it turns on")  # info: set row
        b = state_toggle("Risky actions", bool(s.get("risky_actions_enabled")), self._risky_toggled)  # info: set b
        row.add_suffix(b)  # info: row . add_suffix ( b )
        row.set_activatable_widget(b)  # info: row . set_activatable_widget ( b )
        self.risky_row = b  # info: self . risky_row = b
        g.add(row)  # info: g . add ( row )
        page.add(g)  # info: page . add ( g )
        g = Adw.PreferencesGroup(title="Execution gates", description="The broker reads this file on its own. Opening a gate needs confirm. Agents cannot toggle these.")  # info: set g
        gate_doc = rr_gates.load()  # info: set gate_doc
        for dotted, title in rr_gates.LABELS:  # info: for dotted , title in rr_gates . LABELS
            row = Adw.ActionRow(title=title, subtitle=dotted)  # info: set row
            def ch(_btn, active, key=dotted):  # info: def ch
                if active:  # info: if active
                    if self.win is None:  # info: if self . win is None
                        _btn.rr_set(False)  # info: _btn . rr_set ( False )
                        return  # info: return
                    def yes(k=key):  # info: def yes
                        rr_gates.set_gate(k, True, confirmed=True)  # info: call rr_gates . set_gate
                    def no(b=_btn):  # info: def no
                        b.rr_set(False)  # info: b . rr_set ( False )
                    self.confirm(f"Enable {key}?", "The execution broker enforces this gate. Confirm to open it.", "Enable", yes, no)  # info: call self . confirm
                else:  # info: else
                    rr_gates.set_gate(key, False, confirmed=False)  # info: call rr_gates . set_gate
            b = state_toggle(title, rr_gates.lookup(gate_doc, dotted), ch)  # info: set b
            row.add_suffix(b)  # info: row . add_suffix ( b )
            row.set_activatable_widget(b)  # info: row . set_activatable_widget ( b )
            g.add(row)  # info: g . add ( row )
        page.add(g)  # info: page . add ( g )
        self.url_group = Adw.PreferencesGroup(title="Known URLs", description="Name + URL only. No credentials or tokens are stored. Click to open with xdg-open.")  # info: self . url_group = Adw . PreferencesGroup (
        add = Gtk.Button(icon_name="list-add-symbolic", valign=Gtk.Align.CENTER, tooltip_text="Add URL")  # info: set add
        add.add_css_class("flat")  # info: add . add_css_class ( "flat" )
        add.connect("clicked", lambda *_: self.edit_url(None))  # info: add . connect ( "clicked" , lambda *
        self.url_group.set_header_suffix(add)  # info: self . url_group . set_header_suffix ( add )
        self.url_rows = []  # info: self . url_rows = [ ]
        self.fill_urls()  # info: self . fill_urls ( )
        page.add(self.url_group)  # info: page . add ( self . url_group )
        g = Adw.PreferencesGroup()  # info: set g
        save = Gtk.Button(label="Save settings", halign=Gtk.Align.START)  # info: set save
        save.add_css_class("suggested-action")  # info: save . add_css_class ( "suggested-action" )
        save.connect("clicked", self.save_settings)  # info: save . connect ( "clicked" , self .
        g.add(save)  # info: g . add ( save )
        page.add(g)  # info: page . add ( g )
        page.set_vexpand(True)  # info: page . set_vexpand ( True )
        box.append(page)  # info: box . append ( page )

    def _spin(self, g, key, title, lo, hi):  # info: def _spin
        row = Adw.SpinRow.new_with_range(lo, hi, 1)  # info: set row
        row.set_title(title)  # info: row . set_title ( title )
        row.set_value(float(self.s.get(key) or lo))  # info: row . set_value ( float ( self .
        row.connect("notify::value", lambda r, _p: self.s.__setitem__(key, int(r.get_value())))  # info: row . connect ( "notify::value" , lambda r
        g.add(row)  # info: g . add ( row )

    def _entry(self, g, key, title):  # info: def _entry
        row = Adw.EntryRow(title=title)  # info: set row
        row.set_text(str(self.s.get(key, "")))  # info: row . set_text ( str ( self .
        row.connect("changed", lambda r: self.s.__setitem__(key, r.get_text()))  # info: row . connect ( "changed" , lambda r
        g.add(row)  # info: g . add ( row )

    def _switch(self, g, key, title, sub="", name=None):  # info: def _switch
        """On/off setting row: labelled toggle button ("<name>: On/Off"), no Gtk.Switch."""  # info: """On/off setting row: labelled toggle button ("<name>: On/Off"), no Gtk.Switch."""
        row = Adw.ActionRow(title=title, subtitle=sub)  # info: set row

        def ch(_b, on):  # info: def ch
            self.s[key] = on  # info: self . s [ key ] = on
            if key == "camera_viewer_enabled":  # info: if key == "camera_viewer_enabled" :
                self.set_camera_viewer(on)  # info: self . set_camera_viewer ( on )
        b = state_toggle(name or title, bool(self.s.get(key)), ch)  # info: set b
        row.add_suffix(b)  # info: row . add_suffix ( b )
        row.set_activatable_widget(b)  # info: row . set_activatable_widget ( b )
        g.add(row)  # info: g . add ( row )

    def _risky_toggled(self, btn, active):  # info: def _risky_toggled
        if active and not self.s.get("risky_actions_enabled"):  # info: if active and not self . s .
            if self.win is None:  # info: if self . win is None :
                btn.rr_set(False)   # no window = no confirm dialog = stays off
                return  # info: return

            def yes():  # info: def yes
                self.s["risky_actions_enabled"] = True  # info: self . s [ "risky_actions_enabled" ] = True
                self.r_controls()  # info: self . r_controls ( )

            def no():  # info: def no
                btn.rr_set(False)  # info: btn . rr_set ( False )
            self.confirm("Allow risky actions?", "Poller restart, Telegram/voice sends and RR_* flags need Alexander's sign-off.",  # info: self . confirm ( "Allow risky actions?" , "Poller restart, Telegram/voice sends and RR_* flags need Alexander'
                         "Allow", yes, no)  # info: "Allow" , yes , no )
        elif not active:  # info: elif not active :
            self.s["risky_actions_enabled"] = False  # info: self . s [ "risky_actions_enabled" ] = False
            self.r_controls()  # info: self . r_controls ( )

    def fill_urls(self):  # info: def fill_urls
        for r in self.url_rows:  # info: for r in self . url_rows :
            self.url_group.remove(r)  # info: self . url_group . remove ( r )
        self.url_rows = []  # info: self . url_rows = [ ]
        for idx, u in enumerate(self.s.get("known_urls", [])):  # info: for idx , u in enumerate ( self
            row = Adw.ActionRow(title=GLib.markup_escape_text(u.get("name", "")), subtitle=GLib.markup_escape_text(u.get("url", "")),  # info: set row
                                activatable=True)  # info: set activatable
            row.connect("activated", lambda _r, url=u.get("url", ""): self.open_url(url))  # info: row . connect ( "activated" , lambda _r
            for icon, tip, fn in (("document-edit-symbolic", "Edit", lambda *_a, i=idx: self.edit_url(i)),  # info: for icon , tip , fn in (
                                  ("user-trash-symbolic", "Remove", lambda *_a, i=idx: self.remove_url(i))):  # info: call (
                b = Gtk.Button(icon_name=icon, valign=Gtk.Align.CENTER, tooltip_text=tip)  # info: set b
                b.add_css_class("flat")  # info: b . add_css_class ( "flat" )
                b.connect("clicked", fn)  # info: b . connect ( "clicked" , fn )
                row.add_suffix(b)  # info: row . add_suffix ( b )
            self.url_group.add(row)  # info: self . url_group . add ( row )
            self.url_rows.append(row)  # info: self . url_rows . append ( row )

    def edit_url(self, idx):  # info: def edit_url
        cur = self.s["known_urls"][idx] if idx is not None else {"name": "", "url": "http://"}  # info: set cur
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # info: set box
        en, eu = Gtk.Entry(text=cur["name"], placeholder_text="Name"), Gtk.Entry(text=cur["url"], placeholder_text="URL")  # info: en , eu = Gtk . Entry (
        box.append(en)  # info: box . append ( en )
        box.append(eu)  # info: box . append ( eu )

        def ok():  # info: def ok
            url = eu.get_text().strip()  # info: set url
            if not rr_settings.url_is_clean(url):  # info: if not rr_settings . url_is_clean ( url )
                self.toast("URL refused: must be http(s)/file and carry no credentials or tokens")  # info: self . toast ( "URL refused: must be http(s)/file and carry no credentials or tokens" )
                return  # info: return
            item = {"name": en.get_text().strip() or url, "url": url}  # info: set item
            if idx is None:  # info: if idx is None :
                self.s["known_urls"].append(item)  # info: self . s [ "known_urls" ] . append
            else:  # info: else :
                self.s["known_urls"][idx] = item  # info: self . s [ "known_urls" ] [ idx
            self.fill_urls()  # info: self . fill_urls ( )
        self.confirm("Known URL", "Name and URL (no credentials).", "OK", ok, extra=box)  # info: self . confirm ( "Known URL" , "Name and URL (no credentials)." ,

    def remove_url(self, idx):  # info: def remove_url
        u = self.s["known_urls"][idx]  # info: set u

        def yes():  # info: def yes
            del self.s["known_urls"][idx]  # info: del self . s [ "known_urls" ] [
            self.fill_urls()  # info: self . fill_urls ( )
        self.confirm("Remove URL?", f"{u['name']}\n{u['url']}", "Remove", yes)  # info: self . confirm ( "Remove URL?" , f" {

    def save_settings(self, *_):  # info: def save_settings
        try:  # info: try :
            rr_settings.save(self.s)  # info: rr_settings . save ( self . s )
            self.paths = src.Paths(self.s["database_root"], self.s["pacific_root"])  # info: self . paths = src . Paths (
            self.restart_timer()  # info: self . restart_timer ( )
            self.toast(f"Saved {rr_settings.SETTINGS_FILE.name}")  # info: self . toast ( f" Saved { rr_settings
        except Exception as e:  # info: except Exception as e :
            self.toast(f"Save failed: {e}")  # info: self . toast ( f" Save failed: { e

    # ----------------------------------------------------------- shared UI helpers
    def confirm(self, heading, body, ok_label, on_ok, on_cancel=None, extra=None):  # info: def confirm
        if self.win is None:  # info: if self . win is None :
            return  # info: return
        if Adw is not None:  # info: if Adw is not None :
            d = Adw.AlertDialog(heading=heading, body=body)  # info: set d
            d.add_response("cancel", "Cancel")  # info: d . add_response ( "cancel" , "Cancel" )
            d.add_response("ok", ok_label)  # info: d . add_response ( "ok" , ok_label )
            d.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE if ok_label in ("Run", "Allow", "Remove", "Turn off", "Delete", "Schedule", "Publish", "Restart") else Adw.ResponseAppearance.SUGGESTED)  # info: d . set_response_appearance ( "ok" , Adw .
            d.set_default_response("cancel")  # info: d . set_default_response ( "cancel" )
            d.set_close_response("cancel")  # info: d . set_close_response ( "cancel" )
            if extra is not None:  # info: if extra is not None :
                d.set_extra_child(extra)  # info: d . set_extra_child ( extra )
            d.connect("response", lambda _d, r: (on_ok() if r == "ok" else (on_cancel() if on_cancel else None)))  # info: d . connect ( "response" , lambda _d
            d.present(self.win)  # info: d . present ( self . win )
        else:  # info: else :
            d = Gtk.AlertDialog(message=heading, detail=body, buttons=["Cancel", ok_label], cancel_button=0, default_button=0)  # info: set d
            d.choose(self.win, None, lambda dd, res: (on_ok() if dd.choose_finish(res) == 1 else (on_cancel() if on_cancel else None)))  # info: d . choose ( self . win ,

    def toast(self, msg):  # info: def toast
        if getattr(self, "toasts", None) is not None and Adw is not None:  # info: if getattr ( self , "toasts" , None
            self.toasts.add_toast(Adw.Toast(title=msg))  # info: self . toasts . add_toast ( Adw .
        else:  # info: else :
            print(msg)  # info: call print

    def open_path(self, p: Path):  # info: def open_path
        spawn(["xdg-open", str(p)])  # info: call spawn

    def open_url(self, url: str):  # info: def open_url
        if rr_settings.url_is_clean(url):  # info: if rr_settings . url_is_clean ( url ) :
            spawn(["xdg-open", url])  # info: call spawn

    # ----------------------------------------------------------- refresh loop
    def logd(self):  # info: def logd
        if self._logd is None:  # info: if self . _logd is None :
            self._logd = src.log_digest(self.paths)  # info: self . _logd = src . log_digest (
        return self._logd  # info: return self . _logd

    _logd = None  # info: set _logd

    def header_refresh(self):  # info: def header_refresh
        e = src.energy(self.paths)  # info: set e
        st, n = src.poller_quick(self.argvs())  # info: st , n = src . poller_quick (
        col = {"PASS": "#859900", "WARN": "#b58900"}.get(st, "#dc322f")
        stale_after = int(self.s.get("stale_after_sec") or 900)

        def soc_hdr(label, d):
            soc = d.get("soc") if isinstance(d, dict) else d
            age = d.get("age") if isinstance(d, dict) else None
            if not isinstance(soc, (int, float)):
                return f"{label} n/a"
            flag = ""
            fg = None
            if soc <= 10:
                flag = " CRITICAL"
                fg = "#dc322f"
            elif soc <= 20:
                flag = " LOW"
                fg = "#b58900"
            if age is not None and age > stale_after:
                flag += " STALE"
                fg = fg or "#b58900"
            body = f"{label} {soc:.0f}%{flag}"
            if fg:
                return f"<span foreground='{fg}'><b>{esc(body)}</b></span>"
            return esc(body)

        lap = e["laptop"]  # info: set lap
        la = self.logd().get("log_age")  # info: set la
        b3 = f"B3 laptop {lap[0]:.0f}%" if lap and isinstance(lap[0], (int, float)) else "B3 laptop n/a"
        if lap and isinstance(lap[0], (int, float)) and lap[0] <= 20 and not lap[2]:
            b3 = f"<span foreground='#b58900'><b>{esc(f'B3 laptop {lap[0]:.0f}% LOW')}</b></span>"
        else:
            b3 = esc(b3)
        self.header.set_markup(
            f"<b>Root Monitor · Pacific Solar Server</b>   poller <span foreground='{col}'><b>● {st}</b></span> ({n} proc)"
            f"   {soc_hdr('B1', e['river2pro'])} · {soc_hdr('B2', e['delta2'])} · {b3}"
            f"   log {int(la) if la is not None else '—'}s   <span alpha='70%'>{esc(now_hst())}</span>")

    def refresh_visible(self):  # info: def refresh_visible
        name = self.stack.get_visible_child_name()  # info: set name
        self.ensure_built(name)  # info: self . ensure_built ( name )
        if name == "cameras":  # info: if name == "cameras" :
            return  # camera page has its own timer (only while visible + on)
        self.refreshers[name]()  # info: self . refreshers [ name ] ( )

    def safe(self, fn):  # info: def safe
        try:  # info: try :
            fn()  # info: call fn
        except Exception as e:  # info: except Exception as e :
            msg = f"{getattr(fn, '__name__', fn)}: {e}"  # info: set msg
            self.errors.append(msg)  # info: self . errors . append ( msg )
            print("panel error:", msg, file=sys.stderr)  # info: call print
            if os.environ.get("RR_PANEL_DEBUG"):  # info: if os . environ . get ( "RR_PANEL_DEBUG"
                import traceback  # info: import traceback
                traceback.print_exc()  # info: traceback . print_exc ( )

    def tick(self):  # info: def tick
        self._argvs = None  # info: self . _argvs = None
        self._logd = None  # info: self . _logd = None
        self.safe(self.header_refresh)  # info: self . safe ( self . header_refresh )
        self.safe(self.refresh_visible)  # info: self . safe ( self . refresh_visible )
        return True  # info: return True

    def restart_timer(self):  # info: def restart_timer
        if self.timer_id:  # info: if self . timer_id :
            GLib.source_remove(self.timer_id)  # info: GLib . source_remove ( self . timer_id )
        self.timer_id = GLib.timeout_add_seconds(int(self.s["refresh_sec"]), self.tick)  # info: self . timer_id = GLib . timeout_add_seconds (
        self.cam_timer_update()  # info: self . cam_timer_update ( )

    def on_page(self, *_):  # info: def on_page
        self._argvs = None  # info: self . _argvs = None
        self._logd = None  # info: self . _logd = None
        self.safe(self.awf_maybe_release)  # info: self . safe ( self . awf_maybe_release )
        self.safe(self.refresh_visible)  # info: self . safe ( self . refresh_visible )
        self.cam_timer_update()  # info: self . cam_timer_update ( )
        self.sl_update()  # info: self . sl_update ( )

    def sl_update(self):  # info: def sl_update
        """Starlink helper process lives only while the Network page is visible in the window."""  # info: """Starlink helper process lives only while the Network page is visible in the window."""
        if self.win is not None and self.stack.get_visible_child_name() == "network" and "network" in self.built:  # info: if self . win is not None and
            self.sl_start()  # info: self . sl_start ( )
        else:  # info: else :
            self.sl_stop()  # info: self . sl_stop ( )

    def attach(self, win):  # info: def attach
        self.win = win  # info: self . win = win
        self.tick()  # info: self . tick ( )
        self.restart_timer()  # info: self . restart_timer ( )

    def stop(self):  # info: def stop
        self.sl_stop()  # info: self . sl_stop ( )
        for attr in ("timer_id", "cam_timer_id"):  # info: for attr in ( "timer_id" , "cam_timer_id" )
            if getattr(self, attr):  # info: if getattr ( self , attr ) :
                GLib.source_remove(getattr(self, attr))  # info: GLib . source_remove ( getattr ( self ,
                setattr(self, attr, 0)  # info: call setattr


# =============================================================== modes
# ====================================================
# SECTION: function run_check
# What it does: run check.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_check(args, settings) -> int:  # info: def run_check
    t0 = time.process_time()  # info: set t0
    w0 = time.time()  # info: set w0
    if Adw is not None:  # info: if Adw is not None :
        Adw.init()  # info: Adw . init ( )
    p = Panel(settings, check=True, camera_override=(args.camera_viewer == "on") if args.camera_viewer else None)  # info: set p
    p.tick()  # info: p . tick ( )
    for name, _t in PAGES:  # info: for name , _t in PAGES :
        if name == "cameras":  # info: if name == "cameras" :
            if p.camera_viewer_on:  # info: if p . camera_viewer_on :
                p.safe(p.r_cameras)  # info: p . safe ( p . r_cameras )
            else:  # info: else :
                p.report["cameras"] = {"viewer": "off"}  # info: p . report [ "cameras" ] = {
        else:  # info: else :
            p.safe(p.refreshers[name])  # info: p . safe ( p . refreshers [
    if "network" in dict(PAGES) and not args.no_starlink:  # info: if "network" in dict ( PAGES ) and
        p.safe(p.r_network)  # second sample -> real rates
        sl = p.starlink_once()  # info: set sl
        p.report["starlink"] = {k: sl.get(k) for k in ("ok", "state", "uptime_s", "pop_ping_latency_ms", "fraction_obstructed",  # info: p . report [ "starlink" ] = {
                                                         "downlink_bps", "uplink_bps", "error") if k in sl}  # info: "downlink_bps" , "uplink_bps" , "error" ) if k
    ru_app = resource.getrusage(resource.RUSAGE_SELF)   # app work done; test-harness allocations follow
    # secret leak test: every string in the built widget tree vs. the known secret values (never printed)
    texts = "\n".join(widget_texts(p.root)) + "\n".join(p.check_texts)  # info: set texts
    # plus every string a Settings row would render (big files are collapsed in the UI, so test the data too)
    import rr_registry  # info: import rr_registry
    texts += "\n".join(f"{s.key} {s.display} {s.ro_reason} {s.restart}" for pid, _t in rr_registry.PAGES  # info: set texts
                       for s in p.reg.page_settings(pid))  # info: for s in p . reg . page_settings
    secrets = p.reg.secret_values()  # info: set secrets
    leaks = sum(1 for v in secrets if v and v in texts)  # info: set leaks
    ru = resource.getrusage(resource.RUSAGE_SELF)  # info: set ru
    ruc = resource.getrusage(resource.RUSAGE_CHILDREN)  # info: set ruc
    print(f"{APP_NAME} --check  {now_hst()}")  # info: call print
    print(f"toolkit: Gtk {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"  # info: call print
          + (f" · Adw {Adw.get_major_version()}.{Adw.get_minor_version()}" if Adw else " · Adw missing (plain GTK4)"))  # info: call +
    print(f"settings: {rr_settings.SETTINGS_FILE} (exists={rr_settings.SETTINGS_FILE.exists()})")  # info: call print
    print(f"pages built: {len(PAGES)} ({', '.join(n for n, _ in PAGES)})")  # info: call print
    print(f"cameras discovered: {p.cams} · viewer {'ON' if p.camera_viewer_on else 'OFF'}")  # info: call print
    for k, v in p.report.items():  # info: for k , v in p . report
        print(f"  {k:<9} {v}")  # info: call print
    print(f"camera stats: {src.STATS}")  # info: call print
    print(f"known URLs: {len(settings.get('known_urls', []))}")  # info: call print
    print(f"secret leak test: {len(secrets)} known secret values checked against {len(texts):,} chars of widget text -> "  # info: call print
          f"{leaks} leaks ({'PASS' if leaks == 0 else 'FAIL'})")  # info: f" { leaks } leaks ( { 'PASS' if
    print(f"security items (secret-looking keys in git-tracked files): {len(p.reg.security_items)}")  # info: call print
    if leaks:  # info: if leaks :
        p.errors.append(f"secret leak test: {leaks} values visible")  # info: p . errors . append ( f" secret leak test:
    print(f"errors: {len(p.errors)}")  # info: call print
    for e in p.errors:  # info: for e in p . errors :
        print("  ERR", e)  # info: call print
    print(f"peak RSS (app: build every page + load all data once): {ru_app.ru_maxrss / 1024:.1f} MB")  # info: call print
    print(f"peak RSS incl. leak-test harness: {ru.ru_maxrss / 1024:.1f} MB · CPU user {ru.ru_utime:.2f}s sys {ru.ru_stime:.2f}s "  # info: call print
          f"(process CPU {time.process_time() - t0:.2f}s, wall {time.time() - w0:.2f}s) · children peak RSS "  # info: f" (process CPU { time . process_time ( )
          f"{ruc.ru_maxrss / 1024:.1f} MB (largest child incl. pages inherited at fork: git / systemctl / Starlink helper)")  # info: f" { ruc . ru_maxrss / 1024 :
    print("RESULT:", "PASS" if not p.errors else "FAIL")  # info: call print
    return 0 if not p.errors else 1  # info: return 0 if not p . errors else


# ====================================================
# SECTION: function build_window
# What it does: build window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def build_window(app, panel: Panel):  # info: def build_window
    cls = Adw.ApplicationWindow if Adw else Gtk.ApplicationWindow  # info: set cls
    win = cls(application=app, title=APP_NAME)  # info: set win
    win.set_default_size(1100, 760)  # info: win . set_default_size ( 1100 , 760 )
    tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)  # info: set tb
    hb = Adw.HeaderBar() if Adw else Gtk.HeaderBar()  # info: set hb
    tb.append(hb)  # info: tb . append ( hb )
    if Adw:  # info: if Adw :
        panel.toasts = Adw.ToastOverlay(child=panel.root, vexpand=True)  # info: panel . toasts = Adw . ToastOverlay (
        tb.append(panel.toasts)  # info: tb . append ( panel . toasts )
        win.set_content(tb)  # info: win . set_content ( tb )
    else:  # info: else :
        tb.append(panel.root)  # info: tb . append ( panel . root )
        win.set_child(tb)  # info: win . set_child ( tb )
    win.connect("close-request", lambda *_: (panel.stop(), False)[1])  # info: win . connect ( "close-request" , lambda *
    return win  # info: return win


# ====================================================
# SECTION: function capture
# What it does: capture.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def capture(win, path: Path) -> bool:  # info: def capture
    gi.require_version("Graphene", "1.0")  # info: gi . require_version ( "Graphene" , "1.0" )
    from gi.repository import Graphene  # info: from gi . repository import Graphene
    w, h = win.get_width(), win.get_height()  # info: w , h = win . get_width (
    paintable = Gtk.WidgetPaintable.new(win)  # info: set paintable
    snap = Gtk.Snapshot()  # info: set snap
    paintable.snapshot(snap, w, h)  # info: paintable . snapshot ( snap , w ,
    node = snap.to_node()  # info: set node
    if node is None:  # info: if node is None :
        return False  # info: return False
    tex = win.get_renderer().render_texture(node, Graphene.Rect().init(0, 0, w, h))  # info: set tex
    return bool(tex.save_to_png(str(path)))  # info: return bool ( tex . save_to_png ( str


# ====================================================
# SECTION: function run_gui
# What it does: run gui.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_gui(args, settings) -> int:  # info: def run_gui
    AppCls = Adw.Application if Adw else Gtk.Application  # info: set AppCls
    flags = Gio.ApplicationFlags.NON_UNIQUE if (args.screenshot or args.run_for) else Gio.ApplicationFlags.DEFAULT_FLAGS  # info: set flags
    app = AppCls(application_id=APP_ID, flags=flags)  # info: set app
    state = {}  # info: set state

    def activate(a):  # info: def activate
        if state.get("win"):  # info: if state . get ( "win" ) :
            state["win"].present()  # info: state [ "win" ] . present ( )
            return  # info: return
        prov = Gtk.CssProvider()  # info: set prov
        prov.load_from_data(CSS)  # info: prov . load_from_data ( CSS )
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)  # info: Gtk . StyleContext . add_provider_for_display ( Gdk .
        panel = Panel(settings, camera_override=None)  # info: set panel
        win = build_window(a, panel)  # info: set win
        state.update(win=win, panel=panel)  # info: state . update ( win = win ,
        panel.attach(win)  # info: panel . attach ( win )
        win.present()  # info: win . present ( )
        if args.screenshot:  # info: if args . screenshot :
            shoot(a, win, panel, Path(args.screenshot))  # info: call shoot
        elif args.run_for:  # info: elif args . run_for :
            def done():  # info: def done
                ru = resource.getrusage(resource.RUSAGE_SELF)  # info: set ru
                print(f"window run {args.run_for}s · peak RSS {ru.ru_maxrss / 1024:.1f} MB · CPU user {ru.ru_utime:.2f}s "  # info: call print
                      f"sys {ru.ru_stime:.2f}s · camera stats {src.STATS} · errors {len(panel.errors)}")  # info: f" sys { ru . ru_stime : .2f
                panel.stop()  # info: panel . stop ( )
                win.close()  # info: win . close ( )
                a.quit()  # info: a . quit ( )
                return False  # info: return False
            GLib.timeout_add_seconds(int(args.run_for), done)  # info: GLib . timeout_add_seconds ( int ( args .

    app.connect("activate", activate)  # info: app . connect ( "activate" , activate )
    return app.run([sys.argv[0]])  # info: return app . run ( [ sys .


# ====================================================
# SECTION: function shoot
# What it does: Capture every page (and every Settings / Not-migrated sub-page) to PNG. Secret guard: before each PNG, all window strings are compared with the known secret values; any match skips
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def shoot(app, win, panel: Panel, out: Path):  # info: def shoot
    """Capture every page (and every Settings / Not-migrated sub-page) to PNG. Secret guard: before each PNG,
    all window strings are compared with the known secret values; any match skips that PNG."""
    import rr_registry  # info: import rr_registry
    out.mkdir(parents=True, exist_ok=True)  # info: out . mkdir ( parents = True ,
    ts = datetime.now(src.TZ).strftime("%Y%m%d-%H%M%S")  # info: set ts
    seq = [(n, None) for n, _ in PAGES if n not in ("cameras", "settings", "migration")]  # info: set seq
    seq += [("cameras", False), ("cameras", True), ("migration", None), ("migration", "discord")]  # info: set seq
    seq += [("settings", pid) for pid, _t in rr_registry.PAGES]  # info: set seq
    secrets = [v for v in panel.reg.secret_values() if v]  # info: set secrets
    done = []  # info: set done

    def select(name, sub):  # info: def select
        if name == "cameras":  # info: if name == "cameras" :
            panel.camera_override = sub  # info: panel . camera_override = sub
        panel.stack.set_visible_child_name(name)  # info: panel . stack . set_visible_child_name ( name )
        panel.on_page()  # info: panel . on_page ( )
        if name == "settings" and sub:  # info: if name == "settings" and sub :
            panel.set_stack.set_visible_child_name(sub)  # info: panel . set_stack . set_visible_child_name ( sub )
        if name == "migration" and sub and sub in getattr(panel, "mig_items", {}):  # info: if name == "migration" and sub and sub
            panel.mig_stack.set_visible_child_name(sub)  # info: panel . mig_stack . set_visible_child_name ( sub )

    def step(i=[0]):  # noqa: B006
        if i[0] > 0:  # info: if i [ 0 ] > 0 :
            name, sub = seq[i[0] - 1]  # info: name , sub = seq [ i [
            tag = "" if sub is None else ("-viewer-on" if sub is True else "-viewer-off" if sub is False else f"-{sub}")  # info: set tag
            fn = out / f"{ts}-{i[0]:02d}-{name}{tag}.png"  # info: set fn
            texts = "\n".join(widget_texts(win))  # info: set texts
            leak = sum(1 for v in secrets if v in texts)  # info: set leak
            if leak:  # info: if leak :
                done.append((str(fn), False, f"SKIPPED by secret guard ({leak} matches)"))  # info: done . append ( ( str ( fn
            else:  # info: else :
                done.append((str(fn), capture(win, fn), "secret guard PASS (0 matches)"))  # info: done . append ( ( str ( fn
        if i[0] >= len(seq):  # info: if i [ 0 ] >= len (
            for f, ok, note in done:  # info: for f , ok , note in done
                print(("SAVED " if ok else "NOT SAVED ") + f + " · " + note)  # info: call print
            ru = resource.getrusage(resource.RUSAGE_SELF)  # info: set ru
            print(f"window peak RSS: {ru.ru_maxrss / 1024:.1f} MB · CPU user {ru.ru_utime:.2f}s sys {ru.ru_stime:.2f}s")  # info: call print
            print(f"camera stats: {src.STATS} · starlink helper running at exit: {panel.sl_proc is not None}")  # info: call print
            panel.stop()  # info: panel . stop ( )
            win.close()  # info: win . close ( )
            app.quit()  # info: app . quit ( )
            return False  # info: return False
        name, sub = seq[i[0]]  # info: name , sub = seq [ i [
        select(name, sub)  # info: call select
        i[0] += 1  # info: i [ 0 ] += 1
        slow = name == "cameras" or name == "network" or (name == "settings" and sub in ("environment", "flags"))  # info: set slow
        GLib.timeout_add(3500 if slow else 1300, step)  # info: GLib . timeout_add ( 3500 if slow else
        return False  # info: return False
    GLib.timeout_add(1500, step)  # info: GLib . timeout_add ( 1500 , step )


# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main() -> int:  # info: def main
    ap = argparse.ArgumentParser(description="Root Monitor — RootRecord control panel (GTK4)")  # info: set ap
    ap.add_argument("--check", action="store_true", help="build widgets + load data once, print report, exit (no window)")  # info: ap . add_argument ( "--check" , action =
    ap.add_argument("--camera-viewer", choices=("on", "off"), help="override camera_viewer_enabled for this run (not saved)")  # info: ap . add_argument ( "--camera-viewer" , choices =
    ap.add_argument("--screenshot", metavar="DIR", help="open the window, save a PNG of every page into DIR, quit")  # info: ap . add_argument ( "--screenshot" , metavar =
    ap.add_argument("--no-starlink", action="store_true", help="--check: skip the one read-only Starlink poll")  # info: ap . add_argument ( "--no-starlink" , action =
    ap.add_argument("--run-for", type=int, metavar="SEC", help="open the window, quit after SEC seconds, print peak RSS (testing)")  # info: ap . add_argument ( "--run-for" , type =
    args = ap.parse_args()  # info: set args
    settings = rr_settings.load()  # info: set settings
    if args.check:  # info: if args . check :
        return run_check(args, settings)  # info: return run_check ( args , settings )
    return run_gui(args, settings)  # info: return run_gui ( args , settings )


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    sys.exit(main())  # info: sys . exit ( main ( ) )
