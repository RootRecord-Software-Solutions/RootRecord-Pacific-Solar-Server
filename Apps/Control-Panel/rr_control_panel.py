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
- --check builds every widget and loads each data source once, prints a report and exits; no window shown.
- --screenshot DIR opens the window, captures each page to PNG (renders the window itself), then quits.
  Before each PNG is saved, every string in the window is checked against the known secret values; a match
  skips that PNG (secret guard).
- Renamed "Root Monitor" 2026-09-29 (file paths + APP_ID unchanged so the existing launcher keeps working).
  New pages (rr_pages.py): Running, Network (+ Starlink), SSH, Not migrated, and the Settings hub
  (Lib/rr_registry.py + Lib/rr_config_io.py). Every page does nothing unless it is visible.
"""
from __future__ import annotations

import argparse
import os
import resource
import sys
import threading
import time
import warnings
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "Lib"))
import rr_settings  # noqa: E402
import rr_sources as src  # noqa: E402

warnings.filterwarnings("ignore", category=DeprecationWarning)
# Lightweight default: the cairo renderer measured ~110 MB peak vs ~180 MB (default) / ~275 MB (gl) on this desk
# (2026-09-29). Override with GSK_RENDERER=... or settings.json "gsk_renderer".
os.environ.setdefault("GSK_RENDERER", str(rr_settings.load().get("gsk_renderer") or "cairo"))

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
try:
    gi.require_version("Adw", "1")
    from gi.repository import Adw  # noqa: E402
except (ValueError, ImportError):
    Adw = None
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango  # noqa: E402

APP_ID = "cloud.rootrecord.ControlPanel"
APP_NAME = "Root Monitor"
PAGES = [("energy", "Energy"), ("weather", "Weather"), ("system", "System"), ("npu", "NPU"), ("ai", "AI log"),
         ("poller", "Poller / services"), ("running", "Running"), ("network", "Network"), ("ssh", "SSH"),
         ("cameras", "Cameras"), ("controls", "Controls"), ("migration", "Not migrated"), ("settings", "Settings")]

CSS = b"""
.rr-mono { font-family: monospace; font-size: 9.5pt; }
.rr-big { font-size: 15pt; font-weight: bold; }
.rr-pass { color: #859900; font-weight: bold; }
.rr-warn { color: #b58900; font-weight: bold; }
.rr-fail { color: #dc322f; font-weight: bold; }
.rr-header { padding: 6px 12px; }
.rr-card { padding: 10px 14px; border-radius: 10px; }
levelbar block.low { background-color: #dc322f; }
levelbar block.high { background-color: #b58900; }
levelbar block.full { background-color: #859900; }
"""


def now_hst() -> str:
    return datetime.now(src.TZ).strftime("%a %d %b %Y  %H:%M:%S HST")


from rr_ui import badge_css, esc, lbl, section, spawn, widget_texts  # noqa: E402
from rr_pages import ExtraPages  # noqa: E402


class BarRow:
    def __init__(self, parent: Gtk.Box, name: str, sub: str):
        row = Gtk.Box(spacing=10)
        row.append(lbl(f"<b>{esc(name)}</b>", markup=True))
        row.append(lbl(sub, "dim-label"))
        self.bar = Gtk.LevelBar(min_value=0, max_value=100, hexpand=True, valign=Gtk.Align.CENTER)
        self.bar.set_size_request(220, 14)
        for n in ("low", "high", "full"):
            self.bar.remove_offset_value(n)
        self.bar.add_offset_value("low", 20)
        self.bar.add_offset_value("high", 50)
        self.bar.add_offset_value("full", 100)
        row.append(self.bar)
        self.val = lbl("n/a", "rr-big")
        self.val.set_width_chars(7)
        row.append(self.val)
        self.detail = lbl("", "dim-label", wrap=True)
        parent.append(row)
        parent.append(self.detail)

    def set(self, pct, detail: str):
        if isinstance(pct, (int, float)):
            self.bar.set_value(max(0.0, min(100.0, float(pct))))
            self.val.set_text(f"{float(pct):.1f}%")
        else:
            self.bar.set_value(0)
            self.val.set_text("n/a")
        self.detail.set_text(detail)


class Panel(ExtraPages):
    def __init__(self, settings: dict, check: bool = False, camera_override: bool | None = None):
        self.s = settings
        self.check = check
        self.camera_override = camera_override
        self.paths = src.Paths(settings["database_root"], settings["pacific_root"])
        self.pw = src.load_poller_watch(self.paths)
        self.cams = src.discover_cameras(self.paths)
        for c in self.cams:
            self.s["cameras"].setdefault(c, {"enabled": True, "label": c.upper()})
        self.timer_id = 0
        self.cam_timer_id = 0
        self.cam_fetching: set[str] = set()
        self.errors: list[str] = []
        self.check_texts: list[str] = []   # --check: strings of sub-pages released after building
        self.win = None
        self.report: dict = {}
        self._argvs = None
        self.build()

    # ----------------------------------------------------------- settings helpers
    @property
    def camera_viewer_on(self) -> bool:
        if self.camera_override is not None:
            return self.camera_override
        return bool(self.s.get("camera_viewer_enabled"))

    def argvs(self):
        if self._argvs is None:
            self._argvs = src.proc_argvs()
        return self._argvs

    # ----------------------------------------------------------- build
    def build(self):
        self.root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.header = lbl("", "rr-header", markup=True)
        self.header.set_ellipsize(Pango.EllipsizeMode.END)
        self.root.append(self.header)
        self.root.append(Gtk.Separator())
        body = Gtk.Box(vexpand=True)
        self.stack = Gtk.Stack(hexpand=True, vexpand=True, transition_type=Gtk.StackTransitionType.CROSSFADE)
        side = Gtk.StackSidebar(stack=self.stack)
        side.set_size_request(170, -1)
        body.append(side)
        body.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        body.append(self.stack)
        self.root.append(body)
        self.builders = {"energy": self.b_energy, "weather": self.b_weather, "system": self.b_system,
                         "npu": self.b_npu, "ai": self.b_ai, "poller": self.b_poller, "cameras": self.b_cameras,
                         "controls": self.b_controls, "settings": self.b_settings, "running": self.b_running,
                         "network": self.b_network, "ssh": self.b_ssh, "migration": self.b_migration}
        self.refreshers = {"energy": self.r_energy, "weather": self.r_weather, "system": self.r_system,
                           "npu": self.r_npu, "ai": self.r_ai, "poller": self.r_poller, "cameras": self.r_cameras,
                           "controls": self.r_controls, "settings": lambda: None, "running": self.r_running,
                           "network": self.r_network, "ssh": lambda: None, "migration": lambda: None}
        self.page_boxes, self.built = {}, set()
        self.cam_tiles = {}
        for name, title in PAGES:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12, margin_top=14, margin_bottom=14,
                          margin_start=16, margin_end=16)
            self.page_boxes[name] = box
            if self.check:
                self.ensure_built(name)  # --check builds every widget up front
            sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
            sc.set_child(box)
            self.stack.add_titled(sc, name, title)
        start = self.s.get("start_page", "energy")
        if start == "cameras" or start not in dict(PAGES):
            start = "energy"
        self.stack.set_visible_child_name(start)
        self.ensure_built(start)
        self.stack.connect("notify::visible-child-name", self.on_page)

    def ensure_built(self, name):
        """Pages are built on first visit in the window (keeps RSS down); --check builds all of them."""
        if name not in self.built:
            self.built.add(name)
            if name in ("running", "network", "ssh", "migration", "settings"):
                self.ensure_redact()
            self.builders[name](self.page_boxes[name])

    # ----------------------------------------------------------- energy
    def b_energy(self, box):
        o, i = section("Batteries (same three bars as poller-dashboard.py)")
        self.bar_b1 = BarRow(i, "B1", "river2pro")
        self.bar_b2 = BarRow(i, "B2", "delta2")
        self.bar_b3 = BarRow(i, "B3", "System (laptop)")
        self.exp_lbl = lbl("", "dim-label", wrap=True)
        i.append(self.exp_lbl)
        box.append(o)
        o, i = section("Watts (Energy/watts/*-last.json)")
        self.watts_grid = Gtk.Grid(column_spacing=18, row_spacing=4)
        heads = ["device", "solar in", "AC out", "AC in", "USB-C out", "charge src", "source", "at"]
        for c, h in enumerate(heads):
            self.watts_grid.attach(lbl(f"<b>{h}</b>", markup=True), c, 0, 1, 1)
        self.watt_cells = {}
        for r, dev in enumerate(("river2pro", "delta2"), start=1):
            self.watts_grid.attach(lbl(dev), 0, r, 1, 1)
            cells = []
            for c in range(1, len(heads)):
                w = lbl("—")
                self.watts_grid.attach(w, c, r, 1, 1)
                cells.append(w)
            self.watt_cells[dev] = cells
        i.append(self.watts_grid)
        box.append(o)
        o, i = section("Poller status line (latest ENERGY heartbeat, automations_current.log)")
        self.status_line = lbl("", "rr-mono", wrap=True, select=True)
        i.append(self.status_line)
        self.summary_lbl = lbl("", "rr-mono dim-label", wrap=True, select=True)
        i.append(self.summary_lbl)
        self.sun_lbl = lbl("", wrap=True)
        i.append(self.sun_lbl)
        box.append(o)

    def r_energy(self):
        e = src.energy(self.paths)
        lg = self.logd()
        stale = self.s["stale_after_sec"]
        for bar, dev in ((self.bar_b1, "river2pro"), (self.bar_b2, "delta2")):
            d = e[dev]
            st = " · STALE" if d["age"] is not None and d["age"] > stale else ""
            bar.set(d["soc"], f"{src.fmt_age(d['age'])}{st} · source {d['source'] or '—'} · {lg['summary'].get(dev, '')}")
        lap = e["laptop"]
        if lap:
            self.bar_b3.set(lap[0], f"System (laptop) · {lap[1]} · {'AC' if lap[2] else 'on battery'} (sysfs)")
        else:
            self.bar_b3.set(None, "no laptop battery found in /sys/class/power_supply")
        exp = lg.get("b3_expansion")
        self.exp_lbl.set_text(f"Delta2 expansion battery (status line B3): {exp}" if exp else
                              "Delta2 expansion battery: not in the current status line (status line B3 absent)")
        for dev, cells in self.watt_cells.items():
            d = e[dev]
            vals = [d["solar_in"], d["ac_out"], d["ac_in"], d["usbc_out"]]
            txt = [f"{v:g} W" if isinstance(v, (int, float)) else "—" for v in vals]
            txt += [str(d["charge_source"] or "—"), str(d["source"] or "—"), src.hst(d["watts_at"])]
            for w, t in zip(cells, txt):
                w.set_text(t)
        self.status_line.set_text((lg["energy_line_at"] + "  " + lg["energy_line"]).strip() or "no ENERGY line in the log tail yet")
        self.summary_lbl.set_text("\n".join(f"SUMMARY={k} {v}" for k, v in lg["summary"].items()))
        self.sun_lbl.set_text(f"SUN  {self._solar or '—'}")
        self.report["energy"] = {"B1": e["river2pro"]["soc"], "B2": e["delta2"]["soc"], "B3_laptop": lap,
                                 "status_line": bool(lg["energy_line"]), "b3_expansion": exp}

    # ----------------------------------------------------------- weather
    def b_weather(self, box):
        o, i = section("Sun (NOAA solar table, same as dashboard SUN row)")
        self.w_sun = lbl("", "rr-big", wrap=True)
        i.append(self.w_sun)
        box.append(o)
        o, i = section("Zone forecast")
        self.w_zone = lbl("", "heading")
        self.w_today = lbl("", wrap=True, select=True)
        self.w_tonight = lbl("", wrap=True, select=True)
        self.w_adv = lbl("", "rr-warn", wrap=True)
        self.w_meta = lbl("", "dim-label", wrap=True)
        for w in (self.w_zone, self.w_adv, self.w_today, self.w_tonight, self.w_meta):
            i.append(w)
        b = Gtk.Button(label="Open weather reports folder", halign=Gtk.Align.START)
        b.connect("clicked", lambda *_: self.open_path(self.paths.weather_l0.parent))
        i.append(b)
        box.append(o)

    @property
    def _solar(self):
        if getattr(self, "_solar_at", 0) < time.time() - 30:
            try:
                self._solar_v = self.pw.aeyes_solar_state() if self.pw else None
            except Exception:
                self._solar_v = None
            self._solar_at = time.time()
        return self._solar_v

    def r_weather(self):
        w = src.weather(self.paths, self.s["weather_zone"], None)
        self.w_sun.set_text(self._solar or "solar table not available")
        self.w_zone.set_text(f"{w['zone']}")
        self.w_today.set_markup(f"<b>Today:</b> {esc(w['today'] or '—')}")
        self.w_tonight.set_markup(f"<b>Tonight:</b> {esc(w['tonight'] or '—')}")
        self.w_adv.set_text("\n".join(w["advisories"]))
        self.w_meta.set_text(f"ZFP collected {w['collected'] or '—'} · State report generated {w['state_generated'] or '—'}")
        self.report["weather"] = {"zone": w["zone"], "today": bool(w["today"]), "solar": bool(self._solar)}

    # ----------------------------------------------------------- system
    def b_system(self, box):
        o, i = section("Host (System/last/host-last.json)")
        self.bar_cpu = BarRow(i, "CPU", "")
        self.bar_mem = BarRow(i, "RAM", "")
        self.sys_extra = lbl("", wrap=True)
        i.append(self.sys_extra)
        box.append(o)
        o, i = section("Poller SYSTEM line (automations_current.log)")
        self.sys_line = lbl("", "rr-mono", wrap=True, select=True)
        i.append(self.sys_line)
        box.append(o)

    def r_system(self):
        s = src.system(self.paths)
        gb = lambda b: f"{b / 1e9:.1f} GB" if isinstance(b, (int, float)) else "—"  # noqa: E731
        self.bar_cpu.set(s["cpu"], f"5-min avg {s['five_cpu']:.1f}%" if isinstance(s["five_cpu"], (int, float)) else "")
        self.bar_mem.set(s["mem"], f"available {gb(s['mem_avail'])} of {gb(s['mem_total'])}"
                         + (f" · 5-min avg {s['five_mem']:.1f}%" if isinstance(s['five_mem'], (int, float)) else ""))
        ld = " / ".join(f"{x:.2f}" if isinstance(x, (int, float)) else "—" for x in s["load"])
        self.sys_extra.set_text(f"load 1/5/15: {ld} · host {s['host'] or '—'} · sampled {src.hst(s['at'])} ({src.fmt_age(s['age'])})")
        self.sys_line.set_text(self.logd()["system_line"] or "—")
        self.report["system"] = {"cpu": s["cpu"], "mem": s["mem"]}

    # ----------------------------------------------------------- npu
    def b_npu(self, box):
        o, i = section("NPU / FastFlowLM (passive: /dev/accel, /proc, lock holder file)")
        self.npu_lbl = lbl("", wrap=True, select=True)
        i.append(self.npu_lbl)
        box.append(o)
        o, i = section("npu-status.sh (read-only script, run on request at nice 10)")
        self.npu_btn = Gtk.Button(label="Run npu-status.sh", halign=Gtk.Align.START)
        self.npu_btn.connect("clicked", self.run_npu_status)
        i.append(self.npu_btn)
        self.npu_out = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        self.npu_out.set_size_request(-1, 220)
        i.append(self.npu_out)
        box.append(o)

    def r_npu(self):
        n = src.npu(self.paths, self.argvs(), int(self.s.get("flm_port", 52625)))
        self.npu_lbl.set_text(f"accel devices: {', '.join(n['accel']) or 'none'}\nFLM: {n['state']}\ninference lock: {n['lock']}")
        self.report["npu"] = n

    def run_npu_status(self, *_):
        self.npu_btn.set_sensitive(False)
        self.npu_out.get_buffer().set_text("running npu-status.sh …")

        def done(out, rc):
            self.npu_out.get_buffer().set_text(f"{out}\n[exit {rc} · {now_hst()}]")
            self.npu_btn.set_sensitive(True)
        spawn(["nice", "-n", "10", "bash", str(self.paths.npu_status_sh)], done, capture=True)

    # ----------------------------------------------------------- ai
    def b_ai(self, box):
        o, i = section("AI inference log (Logs/AI/Inference/inference_current.jsonl — lengths/timings only)")
        self.ai_lbl = lbl("", wrap=True, select=True)
        i.append(self.ai_lbl)
        box.append(o)
        o, i = section("AI processing report (head of ai-processing-report_current.md)")
        self.ai_rep = lbl("", "rr-mono", wrap=True, select=True)
        i.append(self.ai_rep)
        box.append(o)

    def r_ai(self):
        a = src.ai_summary(self.paths)
        if not a.get("present"):
            self.ai_lbl.set_text("inference_current.jsonl not found")
            self.report["ai"] = {"present": False}
            return
        fmt = lambda d: ", ".join(f"{k} {v}" for k, v in sorted(d.items(), key=lambda kv: -kv[1]))  # noqa: E731
        last = a["last"] or {}
        lat = f"avg {a['lat_avg']:.0f} ms · max {a['lat_max']} ms" if a["lat_avg"] is not None else "—"
        self.ai_lbl.set_text(
            f"requests in current log: {a['count']} (today {a['today']}) · fallbacks {a['fallbacks']} · non-zero exits {a['errors']}\n"
            f"latency: {lat}\nroutes: {fmt(a['routes'])}\nmodels: {fmt(a['models'])}\ncallers: {fmt(a['callers'])}\n"
            f"last: {last.get('ts', '—')} {last.get('route', '')} {last.get('model', '')} {last.get('latency_ms', '')} ms "
            f"exit {last.get('exit_code', '')}\nrouting log rows: {a['routing_rows']}")
        self.ai_rep.set_text(a.get("report_head") or "—")
        self.report["ai"] = {"count": a["count"], "routes": a["routes"]}

    # ----------------------------------------------------------- poller / services
    def b_poller(self, box):
        o, i = section("Services (same PASS/WARN/FAIL rule as poller-dashboard.py)")
        self.svc_grid = Gtk.Grid(column_spacing=16, row_spacing=4)
        self.svc_cells = []
        for r, (label, *_x) in enumerate(src.SERVICES):
            self.svc_grid.attach(lbl(f"<b>{esc(label)}</b>", markup=True), 0, r, 1, 1)
            b, d = lbl("…"), lbl("", "dim-label")
            self.svc_grid.attach(b, 1, r, 1, 1)
            self.svc_grid.attach(d, 2, r, 1, 1)
            self.svc_cells.append((b, d))
        i.append(self.svc_grid)
        self.log_state = lbl("", "dim-label")
        i.append(self.log_state)
        row = Gtk.Box(spacing=8)
        b1 = Gtk.Button(label="Open poller dashboard (read-only terminal)")
        b1.connect("clicked", self.open_dashboard)
        b2 = Gtk.Button(label="Open Logs folder")
        b2.connect("clicked", lambda *_: self.open_path(self.paths.logs_dir))
        row.append(b1)
        row.append(b2)
        i.append(row)
        box.append(o)
        o, i = section("Recent poller log (formatted with poller-watch.py format_line)")
        self.log_view = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.NONE)
        self.log_view.set_size_request(-1, 360)
        i.append(self.log_view)
        box.append(o)

    def r_poller(self):
        rows = src.services(self.argvs())
        for (b, d), (_label, state, detail) in zip(self.svc_cells, rows):
            b.set_text(f"● {state}")
            for c in ("rr-pass", "rr-warn", "rr-fail"):
                b.remove_css_class(c)
            b.add_css_class(badge_css(state))
            d.set_text(detail)
        lg = self.logd()
        la = lg.get("log_age")
        self.log_state.set_text(f"log: {int(la)}s since last write" if la is not None else "log: missing")
        self.log_view.get_buffer().set_text("\n".join(src.formatted_log(self.pw, lg["lines"], int(self.s["log_lines"]))))
        self.report["poller"] = {r[0]: r[1] for r in rows}

    def open_dashboard(self, *_):
        dash = str(self.paths.poller_dashboard)
        if any(dash in " ".join(a) or a[1:2] and a[1].endswith("poller-dashboard.py") for _p, a in src.proc_argvs()):
            self.toast("poller-dashboard.py is already open — leaving it")
            return
        spawn(["ptyxis", "--new-window", "-T", "RootRecord poller — rootserver", "-x", f"/usr/bin/python3 '{dash}'"])

    # ----------------------------------------------------------- cameras
    def b_cameras(self, box):
        self.cam_box = box
        self.cam_off = lbl("Camera viewer is OFF (default). Turn it on in Settings → Cameras.\n"
                           "While off the panel does no camera work: no timer, no image loading, no streams.",
                           "dim-label", wrap=True)
        box.append(self.cam_off)
        self.cam_flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, min_children_per_line=2, max_children_per_line=2,
                                    column_spacing=10, row_spacing=10, homogeneous=True)
        self.cam_tiles = {}
        for c in self.cams:
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            pic = Gtk.Picture(content_fit=Gtk.ContentFit.CONTAIN, can_shrink=True)
            pic.set_size_request(360, 203)
            cap = lbl(c, "dim-label")
            v.append(pic)
            v.append(cap)
            self.cam_flow.append(v)
            self.cam_tiles[c] = (v, pic, cap)
        box.append(self.cam_flow)
        self.cam_note = lbl("", "dim-label", wrap=True)
        box.append(self.cam_note)
        self.cam_flow.set_visible(False)

    def r_cameras(self):
        """Called only when the Cameras page is visible (or once in --check with the viewer ON)."""
        on = self.camera_viewer_on
        self.cam_off.set_visible(not on)
        self.cam_flow.set_visible(on)
        if not on:
            self.cam_note.set_text("")
            self.report["cameras"] = {"viewer": "off"}
            return
        enabled = [c for c in self.cams if self.s["cameras"].get(c, {}).get("enabled", True)]
        for c, (v, _p, _cap) in self.cam_tiles.items():
            v.get_parent().set_visible(c in enabled)
        stills = src.latest_stills(self.paths, enabled)
        loaded, missing = [], []
        for c in enabled:
            _v, pic, cap = self.cam_tiles[c]
            p = stills.get(c)
            label = self.s["cameras"].get(c, {}).get("label", c)
            if p is None:
                missing.append(c)
                cap.set_text(f"{label} · no still on disk")
                self.fetch_live(c)
                continue
            try:
                src.STATS["camera_files_opened"] += 1
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p), 640, 360, True)
                pic.set_paintable(Gdk.Texture.new_for_pixbuf(pb))
                cap.set_text(f"{label} · {src.still_time(p)} · {p.name}")
                loaded.append(c)
            except GLib.Error as e:
                cap.set_text(f"{label} · still unreadable ({e.message[:60]}) — expected while hardware work is ongoing")
                missing.append(c)
        self.cam_note.set_text(f"Stills from {self.paths.camera_images} · refresh every {self.s['camera_refresh_sec']} s "
                               f"while this page is visible · missing/flapping stills are expected during camera work")
        self.report["cameras"] = {"viewer": "on", "enabled": enabled, "loaded": loaded, "missing": missing}

    def fetch_live(self, cam: str):
        """Fallback when a camera has no still on disk: one local still from cam_server (visible page only)."""
        if not self.s.get("camera_live_fallback") or cam in self.cam_fetching or self.check:
            return
        still = "current.jpg" if cam == "ch1" else f"current_{cam}.jpg"
        url = self.s.get("camera_live_fallback_url", "").replace("{still}", still)
        if not url.startswith("http://127.0.0.1:"):
            return
        self.cam_fetching.add(cam)

        def work():
            import urllib.request
            data = None
            try:
                src.STATS["camera_http_fetches"] += 1
                with urllib.request.urlopen(url, timeout=8) as r:
                    data = r.read(4_000_000)
            except Exception:
                data = None
            GLib.idle_add(self._live_done, cam, data)
        threading.Thread(target=work, daemon=True).start()

    def _live_done(self, cam, data):
        self.cam_fetching.discard(cam)
        if data and self.camera_viewer_on and self.stack.get_visible_child_name() == "cameras":
            try:
                loader = GdkPixbuf.PixbufLoader()
                loader.set_size(640, 360)
                loader.write(data)
                loader.close()
                _v, pic, cap = self.cam_tiles[cam]
                pic.set_paintable(Gdk.Texture.new_for_pixbuf(loader.get_pixbuf()))
                cap.set_text(f"{cam} · local cam_server still (no still on disk)")
            except Exception:
                pass
        return False

    def cam_timer_update(self):
        if "cameras" not in self.built:
            if self.stack.get_visible_child_name() != "cameras":
                return
            self.ensure_built("cameras")
        want = (self.win is not None and self.camera_viewer_on and self.stack.get_visible_child_name() == "cameras")
        if want and not self.cam_timer_id:
            self.r_cameras()
            self.cam_timer_id = GLib.timeout_add_seconds(int(self.s["camera_refresh_sec"]), self._cam_tick)
        elif not want and self.cam_timer_id:
            GLib.source_remove(self.cam_timer_id)
            self.cam_timer_id = 0
        if not want:
            for _c, (_v, pic, _cap) in self.cam_tiles.items():
                pic.set_paintable(None)  # drop textures when not viewing
            if self.stack.get_visible_child_name() == "cameras":
                self.r_cameras()

    def _cam_tick(self):
        self.safe(self.r_cameras)
        return True

    # ----------------------------------------------------------- controls
    def b_controls(self, box):
        o, i = section("Safe, read-only actions")
        for text, fn in (("Open Logs folder", lambda *_: self.open_path(self.paths.logs_dir)),
                         ("Open Database folder", lambda *_: self.open_path(self.paths.db)),
                         ("Run npu-status.sh (NPU page)", lambda *_: (self.stack.set_visible_child_name("npu"), self.run_npu_status())),
                         ("Open poller dashboard (read-only terminal)", self.open_dashboard)):
            b = Gtk.Button(label=text, halign=Gtk.Align.START)
            b.connect("clicked", fn)
            i.append(b)
        box.append(o)
        o, i = section("Risky actions — NEED SIGN-OFF (disabled by default; confirm dialog; never run by agents)")
        self.risky_note = lbl("", "rr-warn", wrap=True)
        i.append(self.risky_note)
        self.risky_btns = []
        for a in self.s.get("risky_actions", []):
            row = Gtk.Box(spacing=8)
            b = Gtk.Button(label=a.get("label", a.get("id")))
            b.add_css_class("destructive-action")
            b.connect("clicked", self.confirm_risky, a)
            row.append(b)
            row.append(lbl("needs sign-off", "dim-label"))
            i.append(row)
            self.risky_btns.append((b, a))
        box.append(o)
        o, i = section("Gated RR_* job flags in jobs.py (read-only view; set in the poller environment at poller start)")
        self.gated_lbl = lbl("", "rr-mono", wrap=True, select=True)
        i.append(self.gated_lbl)
        box.append(o)

    def r_controls(self):
        if "controls" not in self.built:
            return
        allow = bool(self.s.get("risky_actions_enabled"))
        for b, a in self.risky_btns:
            b.set_sensitive(allow and bool(a.get("signed_off")) and bool(a.get("argv")))
        self.risky_note.set_text("risky_actions_enabled = false in settings.json → every risky button is disabled." if not allow else
                                 "risky_actions_enabled = true: only actions marked signed_off with a command are clickable, each behind a confirm dialog.")
        g = src.gated_jobs(self.paths)
        self.gated_lbl.set_text("\n".join(f"{jid:<32} {flag:<22} default {'ON' if d == '1' else 'OFF'}" for jid, flag, d in g) or "—")
        self.report["controls"] = {"risky_enabled": allow, "gated_flags": len(g),
                                   "clickable_risky": sum(1 for b, _a in self.risky_btns if b.get_sensitive())}

    def confirm_risky(self, _btn, action):
        if not (self.s.get("risky_actions_enabled") and action.get("signed_off") and action.get("argv")):
            return
        self.confirm(f"Run risky action?", f"{action.get('label')}\n\nCommand: {' '.join(action['argv'])}\n\n"
                     "This needs Alexander's sign-off. Continue only if it was approved.",
                     "Run", lambda: spawn(list(action["argv"])))

    # ----------------------------------------------------------- settings
    def b_panel_settings(self, box):
        """Settings → Panel sub-page (Root Monitor's own settings.json)."""
        s = self.s
        self.set_widgets = {}
        if Adw is None:
            box.append(lbl("libadwaita not available — edit settings.json directly.", wrap=True))
            return
        page = Adw.PreferencesPage()
        g = Adw.PreferencesGroup(title="General", description=f"All settings live in {rr_settings.SETTINGS_FILE}")
        self._spin(g, "refresh_sec", "Refresh interval (s)", 2, 60)
        self._spin(g, "stale_after_sec", "Mark SOC stale after (s)", 60, 7200)
        self._spin(g, "log_lines", "Poller log lines shown", 10, 200)
        self._entry(g, "weather_zone", "Weather zone (ZFP name)")
        self._entry(g, "start_page", "Start page (energy, weather, system, npu, ai, poller, running, network, ssh, controls, migration, settings)")
        self._entry(g, "gsk_renderer", "GTK renderer (cairo = lightest; applies on next start)")
        self._switch(g, "starlink_enabled", "Starlink status on the Network page", "helper runs only while that page is visible")
        self._spin(g, "starlink_poll_sec", "Starlink poll interval (s, minimum 10)", 10, 300)
        self._entry(g, "ssh_mainland_alias", "Mainland SSH Host alias (empty = placeholder)")
        page.add(g)
        g = Adw.PreferencesGroup(title="Paths (read-only sources)")
        self._entry(g, "database_root", "Database root")
        self._entry(g, "pacific_root", "Pacific repo root")
        page.add(g)
        g = Adw.PreferencesGroup(title="Cameras",
                                 description="Toggles only change what THIS PANEL shows. Collectors, grab jobs and the poller are not touched.")
        self._switch(g, "camera_viewer_enabled", "Camera viewer page", "Off = zero camera work (no timer, no images, no streams)")
        self._spin(g, "camera_refresh_sec", "Camera still refresh (s, only while visible)", 5, 120)
        self._switch(g, "camera_live_fallback", "Local still fallback", "Only when a camera has no still on disk, only while visible")
        for c in self.cams:
            row = Adw.SwitchRow(title=f"Show {c}", subtitle="discovered from Security/Cameras/grab_all.sh")
            row.set_active(bool(s["cameras"].get(c, {}).get("enabled", True)))
            row.connect("notify::active", lambda r, _p, c=c: s["cameras"].setdefault(c, {}).update(enabled=r.get_active()))
            g.add(row)
        page.add(g)
        g = Adw.PreferencesGroup(title="Safety — NEEDS SIGN-OFF",
                                 description="Risky actions stay disabled unless this is on AND the action is signed_off in settings.json.")
        row = Adw.SwitchRow(title="Allow risky actions (needs sign-off)")
        row.set_active(bool(s.get("risky_actions_enabled")))
        row.connect("notify::active", self._risky_toggled)
        self.risky_row = row
        g.add(row)
        page.add(g)
        self.url_group = Adw.PreferencesGroup(title="Known URLs", description="Name + URL only. No credentials or tokens are stored. Click to open with xdg-open.")
        add = Gtk.Button(icon_name="list-add-symbolic", valign=Gtk.Align.CENTER, tooltip_text="Add URL")
        add.add_css_class("flat")
        add.connect("clicked", lambda *_: self.edit_url(None))
        self.url_group.set_header_suffix(add)
        self.url_rows = []
        self.fill_urls()
        page.add(self.url_group)
        g = Adw.PreferencesGroup()
        save = Gtk.Button(label="Save settings", halign=Gtk.Align.START)
        save.add_css_class("suggested-action")
        save.connect("clicked", self.save_settings)
        g.add(save)
        page.add(g)
        page.set_vexpand(True)
        box.append(page)

    def _spin(self, g, key, title, lo, hi):
        row = Adw.SpinRow.new_with_range(lo, hi, 1)
        row.set_title(title)
        row.set_value(float(self.s.get(key) or lo))
        row.connect("notify::value", lambda r, _p: self.s.__setitem__(key, int(r.get_value())))
        g.add(row)

    def _entry(self, g, key, title):
        row = Adw.EntryRow(title=title)
        row.set_text(str(self.s.get(key, "")))
        row.connect("changed", lambda r: self.s.__setitem__(key, r.get_text()))
        g.add(row)

    def _switch(self, g, key, title, sub=""):
        row = Adw.SwitchRow(title=title, subtitle=sub)
        row.set_active(bool(self.s.get(key)))

        def ch(r, _p):
            self.s[key] = r.get_active()
            if key == "camera_viewer_enabled":
                self.camera_override = None
                self.cam_timer_update()
        row.connect("notify::active", ch)
        g.add(row)

    def _risky_toggled(self, row, _p):
        if row.get_active() and not self.s.get("risky_actions_enabled"):
            def yes():
                self.s["risky_actions_enabled"] = True
                self.r_controls()

            def no():
                row.set_active(False)
            self.confirm("Allow risky actions?", "Poller restart, Telegram/voice sends and RR_* flags need Alexander's sign-off.",
                         "Allow", yes, no)
        elif not row.get_active():
            self.s["risky_actions_enabled"] = False
            self.r_controls()

    def fill_urls(self):
        for r in self.url_rows:
            self.url_group.remove(r)
        self.url_rows = []
        for idx, u in enumerate(self.s.get("known_urls", [])):
            row = Adw.ActionRow(title=GLib.markup_escape_text(u.get("name", "")), subtitle=GLib.markup_escape_text(u.get("url", "")),
                                activatable=True)
            row.connect("activated", lambda _r, url=u.get("url", ""): self.open_url(url))
            for icon, tip, fn in (("document-edit-symbolic", "Edit", lambda *_a, i=idx: self.edit_url(i)),
                                  ("user-trash-symbolic", "Remove", lambda *_a, i=idx: self.remove_url(i))):
                b = Gtk.Button(icon_name=icon, valign=Gtk.Align.CENTER, tooltip_text=tip)
                b.add_css_class("flat")
                b.connect("clicked", fn)
                row.add_suffix(b)
            self.url_group.add(row)
            self.url_rows.append(row)

    def edit_url(self, idx):
        cur = self.s["known_urls"][idx] if idx is not None else {"name": "", "url": "http://"}
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        en, eu = Gtk.Entry(text=cur["name"], placeholder_text="Name"), Gtk.Entry(text=cur["url"], placeholder_text="URL")
        box.append(en)
        box.append(eu)

        def ok():
            url = eu.get_text().strip()
            if not rr_settings.url_is_clean(url):
                self.toast("URL refused: must be http(s)/file and carry no credentials or tokens")
                return
            item = {"name": en.get_text().strip() or url, "url": url}
            if idx is None:
                self.s["known_urls"].append(item)
            else:
                self.s["known_urls"][idx] = item
            self.fill_urls()
        self.confirm("Known URL", "Name and URL (no credentials).", "OK", ok, extra=box)

    def remove_url(self, idx):
        u = self.s["known_urls"][idx]

        def yes():
            del self.s["known_urls"][idx]
            self.fill_urls()
        self.confirm("Remove URL?", f"{u['name']}\n{u['url']}", "Remove", yes)

    def save_settings(self, *_):
        try:
            rr_settings.save(self.s)
            self.paths = src.Paths(self.s["database_root"], self.s["pacific_root"])
            self.restart_timer()
            self.toast(f"Saved {rr_settings.SETTINGS_FILE.name}")
        except Exception as e:
            self.toast(f"Save failed: {e}")

    # ----------------------------------------------------------- shared UI helpers
    def confirm(self, heading, body, ok_label, on_ok, on_cancel=None, extra=None):
        if self.win is None:
            return
        if Adw is not None:
            d = Adw.AlertDialog(heading=heading, body=body)
            d.add_response("cancel", "Cancel")
            d.add_response("ok", ok_label)
            d.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE if ok_label in ("Run", "Allow", "Remove") else Adw.ResponseAppearance.SUGGESTED)
            d.set_default_response("cancel")
            d.set_close_response("cancel")
            if extra is not None:
                d.set_extra_child(extra)
            d.connect("response", lambda _d, r: (on_ok() if r == "ok" else (on_cancel() if on_cancel else None)))
            d.present(self.win)
        else:
            d = Gtk.AlertDialog(message=heading, detail=body, buttons=["Cancel", ok_label], cancel_button=0, default_button=0)
            d.choose(self.win, None, lambda dd, res: (on_ok() if dd.choose_finish(res) == 1 else (on_cancel() if on_cancel else None)))

    def toast(self, msg):
        if getattr(self, "toasts", None) is not None and Adw is not None:
            self.toasts.add_toast(Adw.Toast(title=msg))
        else:
            print(msg)

    def open_path(self, p: Path):
        spawn(["xdg-open", str(p)])

    def open_url(self, url: str):
        if rr_settings.url_is_clean(url):
            spawn(["xdg-open", url])

    # ----------------------------------------------------------- refresh loop
    def logd(self):
        if self._logd is None:
            self._logd = src.log_digest(self.paths)
        return self._logd

    _logd = None

    def header_refresh(self):
        e = src.energy(self.paths)
        st, n = src.poller_quick(self.argvs())
        col = {"PASS": "#859900", "WARN": "#b58900"}.get(st, "#dc322f")
        f = lambda v: f"{v:.0f}%" if isinstance(v, (int, float)) else "n/a"  # noqa: E731
        lap = e["laptop"]
        la = self.logd().get("log_age")
        self.header.set_markup(
            f"<b>Root Monitor · Pacific Solar Server</b>   poller <span foreground='{col}'><b>● {st}</b></span> ({n} proc)"
            f"   B1 {f(e['river2pro']['soc'])} · B2 {f(e['delta2']['soc'])} · B3 laptop {f(lap[0]) if lap else 'n/a'}"
            f"   log {int(la) if la is not None else '—'}s   <span alpha='70%'>{esc(now_hst())}</span>")

    def refresh_visible(self):
        name = self.stack.get_visible_child_name()
        self.ensure_built(name)
        if name == "cameras":
            return  # camera page has its own timer (only while visible + on)
        self.refreshers[name]()

    def safe(self, fn):
        try:
            fn()
        except Exception as e:
            msg = f"{getattr(fn, '__name__', fn)}: {e}"
            self.errors.append(msg)
            print("panel error:", msg, file=sys.stderr)
            if os.environ.get("RR_PANEL_DEBUG"):
                import traceback
                traceback.print_exc()

    def tick(self):
        self._argvs = None
        self._logd = None
        self.safe(self.header_refresh)
        self.safe(self.refresh_visible)
        return True

    def restart_timer(self):
        if self.timer_id:
            GLib.source_remove(self.timer_id)
        self.timer_id = GLib.timeout_add_seconds(int(self.s["refresh_sec"]), self.tick)
        self.cam_timer_update()

    def on_page(self, *_):
        self._argvs = None
        self._logd = None
        self.safe(self.refresh_visible)
        self.cam_timer_update()
        self.sl_update()

    def sl_update(self):
        """Starlink helper process lives only while the Network page is visible in the window."""
        if self.win is not None and self.stack.get_visible_child_name() == "network" and "network" in self.built:
            self.sl_start()
        else:
            self.sl_stop()

    def attach(self, win):
        self.win = win
        self.tick()
        self.restart_timer()

    def stop(self):
        self.sl_stop()
        for attr in ("timer_id", "cam_timer_id"):
            if getattr(self, attr):
                GLib.source_remove(getattr(self, attr))
                setattr(self, attr, 0)


# =============================================================== modes
def run_check(args, settings) -> int:
    t0 = time.process_time()
    w0 = time.time()
    if Adw is not None:
        Adw.init()
    p = Panel(settings, check=True, camera_override=(args.camera_viewer == "on") if args.camera_viewer else None)
    p.tick()
    for name, _t in PAGES:
        if name == "cameras":
            if p.camera_viewer_on:
                p.safe(p.r_cameras)
            else:
                p.report["cameras"] = {"viewer": "off"}
        else:
            p.safe(p.refreshers[name])
    if "network" in dict(PAGES) and not args.no_starlink:
        p.safe(p.r_network)  # second sample -> real rates
        sl = p.starlink_once()
        p.report["starlink"] = {k: sl.get(k) for k in ("ok", "state", "uptime_s", "pop_ping_latency_ms", "fraction_obstructed",
                                                         "downlink_bps", "uplink_bps", "error") if k in sl}
    ru_app = resource.getrusage(resource.RUSAGE_SELF)   # app work done; test-harness allocations follow
    # secret leak test: every string in the built widget tree vs. the known secret values (never printed)
    texts = "\n".join(widget_texts(p.root)) + "\n".join(p.check_texts)
    # plus every string a Settings row would render (big files are collapsed in the UI, so test the data too)
    import rr_registry
    texts += "\n".join(f"{s.key} {s.display} {s.ro_reason} {s.restart}" for pid, _t in rr_registry.PAGES
                       for s in p.reg.page_settings(pid))
    secrets = p.reg.secret_values()
    leaks = sum(1 for v in secrets if v and v in texts)
    ru = resource.getrusage(resource.RUSAGE_SELF)
    ruc = resource.getrusage(resource.RUSAGE_CHILDREN)
    print(f"{APP_NAME} --check  {now_hst()}")
    print(f"toolkit: Gtk {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
          + (f" · Adw {Adw.get_major_version()}.{Adw.get_minor_version()}" if Adw else " · Adw missing (plain GTK4)"))
    print(f"settings: {rr_settings.SETTINGS_FILE} (exists={rr_settings.SETTINGS_FILE.exists()})")
    print(f"pages built: {len(PAGES)} ({', '.join(n for n, _ in PAGES)})")
    print(f"cameras discovered: {p.cams} · viewer {'ON' if p.camera_viewer_on else 'OFF'}")
    for k, v in p.report.items():
        print(f"  {k:<9} {v}")
    print(f"camera stats: {src.STATS}")
    print(f"known URLs: {len(settings.get('known_urls', []))}")
    print(f"secret leak test: {len(secrets)} known secret values checked against {len(texts):,} chars of widget text -> "
          f"{leaks} leaks ({'PASS' if leaks == 0 else 'FAIL'})")
    print(f"security items (secret-looking keys in git-tracked files): {len(p.reg.security_items)}")
    if leaks:
        p.errors.append(f"secret leak test: {leaks} values visible")
    print(f"errors: {len(p.errors)}")
    for e in p.errors:
        print("  ERR", e)
    print(f"peak RSS (app: build every page + load all data once): {ru_app.ru_maxrss / 1024:.1f} MB")
    print(f"peak RSS incl. leak-test harness: {ru.ru_maxrss / 1024:.1f} MB · CPU user {ru.ru_utime:.2f}s sys {ru.ru_stime:.2f}s "
          f"(process CPU {time.process_time() - t0:.2f}s, wall {time.time() - w0:.2f}s) · children peak RSS "
          f"{ruc.ru_maxrss / 1024:.1f} MB (git ls-files / systemctl / Starlink helper)")
    print("RESULT:", "PASS" if not p.errors else "FAIL")
    return 0 if not p.errors else 1


def build_window(app, panel: Panel):
    cls = Adw.ApplicationWindow if Adw else Gtk.ApplicationWindow
    win = cls(application=app, title=APP_NAME)
    win.set_default_size(1100, 760)
    tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    hb = Adw.HeaderBar() if Adw else Gtk.HeaderBar()
    tb.append(hb)
    if Adw:
        panel.toasts = Adw.ToastOverlay(child=panel.root, vexpand=True)
        tb.append(panel.toasts)
        win.set_content(tb)
    else:
        tb.append(panel.root)
        win.set_child(tb)
    win.connect("close-request", lambda *_: (panel.stop(), False)[1])
    return win


def capture(win, path: Path) -> bool:
    gi.require_version("Graphene", "1.0")
    from gi.repository import Graphene
    w, h = win.get_width(), win.get_height()
    paintable = Gtk.WidgetPaintable.new(win)
    snap = Gtk.Snapshot()
    paintable.snapshot(snap, w, h)
    node = snap.to_node()
    if node is None:
        return False
    tex = win.get_renderer().render_texture(node, Graphene.Rect().init(0, 0, w, h))
    return bool(tex.save_to_png(str(path)))


def run_gui(args, settings) -> int:
    AppCls = Adw.Application if Adw else Gtk.Application
    flags = Gio.ApplicationFlags.NON_UNIQUE if (args.screenshot or args.run_for) else Gio.ApplicationFlags.DEFAULT_FLAGS
    app = AppCls(application_id=APP_ID, flags=flags)
    state = {}

    def activate(a):
        if state.get("win"):
            state["win"].present()
            return
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        panel = Panel(settings, camera_override=None)
        win = build_window(a, panel)
        state.update(win=win, panel=panel)
        panel.attach(win)
        win.present()
        if args.screenshot:
            shoot(a, win, panel, Path(args.screenshot))
        elif args.run_for:
            def done():
                ru = resource.getrusage(resource.RUSAGE_SELF)
                print(f"window run {args.run_for}s · peak RSS {ru.ru_maxrss / 1024:.1f} MB · CPU user {ru.ru_utime:.2f}s "
                      f"sys {ru.ru_stime:.2f}s · camera stats {src.STATS} · errors {len(panel.errors)}")
                panel.stop()
                win.close()
                a.quit()
                return False
            GLib.timeout_add_seconds(int(args.run_for), done)

    app.connect("activate", activate)
    return app.run([sys.argv[0]])


def shoot(app, win, panel: Panel, out: Path):
    """Capture every page (and every Settings / Not-migrated sub-page) to PNG. Secret guard: before each PNG,
    all window strings are compared with the known secret values; any match skips that PNG."""
    import rr_registry
    out.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(src.TZ).strftime("%Y%m%d-%H%M%S")
    seq = [(n, None) for n, _ in PAGES if n not in ("cameras", "settings", "migration")]
    seq += [("cameras", False), ("cameras", True), ("migration", None), ("migration", "discord")]
    seq += [("settings", pid) for pid, _t in rr_registry.PAGES]
    secrets = [v for v in panel.reg.secret_values() if v]
    done = []

    def select(name, sub):
        if name == "cameras":
            panel.camera_override = sub
        panel.stack.set_visible_child_name(name)
        panel.on_page()
        if name == "settings" and sub:
            panel.set_stack.set_visible_child_name(sub)
        if name == "migration" and sub and sub in getattr(panel, "mig_items", {}):
            panel.mig_stack.set_visible_child_name(sub)

    def step(i=[0]):  # noqa: B006
        if i[0] > 0:
            name, sub = seq[i[0] - 1]
            tag = "" if sub is None else ("-viewer-on" if sub is True else "-viewer-off" if sub is False else f"-{sub}")
            fn = out / f"{ts}-{i[0]:02d}-{name}{tag}.png"
            texts = "\n".join(widget_texts(win))
            leak = sum(1 for v in secrets if v in texts)
            if leak:
                done.append((str(fn), False, f"SKIPPED by secret guard ({leak} matches)"))
            else:
                done.append((str(fn), capture(win, fn), "secret guard PASS (0 matches)"))
        if i[0] >= len(seq):
            for f, ok, note in done:
                print(("SAVED " if ok else "NOT SAVED ") + f + " · " + note)
            ru = resource.getrusage(resource.RUSAGE_SELF)
            print(f"window peak RSS: {ru.ru_maxrss / 1024:.1f} MB · CPU user {ru.ru_utime:.2f}s sys {ru.ru_stime:.2f}s")
            print(f"camera stats: {src.STATS} · starlink helper running at exit: {panel.sl_proc is not None}")
            panel.stop()
            win.close()
            app.quit()
            return False
        name, sub = seq[i[0]]
        select(name, sub)
        i[0] += 1
        slow = name == "cameras" or name == "network" or (name == "settings" and sub in ("environment", "flags"))
        GLib.timeout_add(3500 if slow else 1300, step)
        return False
    GLib.timeout_add(1500, step)


def main() -> int:
    ap = argparse.ArgumentParser(description="Root Monitor — RootRecord control panel (GTK4)")
    ap.add_argument("--check", action="store_true", help="build widgets + load data once, print report, exit (no window)")
    ap.add_argument("--camera-viewer", choices=("on", "off"), help="override camera_viewer_enabled for this run (not saved)")
    ap.add_argument("--screenshot", metavar="DIR", help="open the window, save a PNG of every page into DIR, quit")
    ap.add_argument("--no-starlink", action="store_true", help="--check: skip the one read-only Starlink poll")
    ap.add_argument("--run-for", type=int, metavar="SEC", help="open the window, quit after SEC seconds, print peak RSS (testing)")
    args = ap.parse_args()
    settings = rr_settings.load()
    if args.check:
        return run_check(args, settings)
    return run_gui(args, settings)


if __name__ == "__main__":
    sys.exit(main())
