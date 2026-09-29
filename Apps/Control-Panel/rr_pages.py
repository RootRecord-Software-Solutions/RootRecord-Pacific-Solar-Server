"""rr_pages.py — Root Monitor pages added 2026-09-29: Running, Network (+ Starlink), SSH, Not migrated, and the
Settings hub (registry-driven sub-pages). Mixed into rr_control_panel.Panel.

INFO — MUST HAVE (future agents):
- Every page here does NOTHING unless visible: Running/Network refresh only from Panel.tick() when they are the
  visible page; the Starlink helper process exists only while the Network page is visible (killed on leave /
  window close); SSH checks run only on a button press; Not-migrated and Settings pages have no timer at all.
- Secrets: the Settings hub renders Setting.display only (masked "set (len N)" / "empty"). Replace uses a
  PasswordEntry; every save = masked diff + confirm dialog -> rr_config_io.commit (backup 0600 + atomic write).
  Nothing is restarted: the dialog states "takes effect after <service> restart".
- Secrets in git-tracked files are never written (registry refuses); they are listed as security items.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from gi.repository import Gio, GLib, Gtk

import rr_netstat as net
import rr_running as run
import rr_ssh
import rr_sources as src
import rr_ui
from rr_ui import Adw, RowList, action_row, badge_css, boxed_list, esc, lbl, light_row, redact, section, set_row_text, spawn

HERE = Path(__file__).resolve().parent
MIGRATION_FILE = HERE / "Lib/rr_migration.json"
REL_UNIT = r"^(rr-|ava-|network-globe|ollama|flm|cloudflared|rootrecord|council|cam|weather|conky|github|bluetooth|NetworkManager|ssh|cron)"


def _trim():
    """Return freed heap to the OS after releasing a sub-page (glibc malloc_trim; no-op elsewhere)."""
    import gc
    gc.collect()
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (OSError, AttributeError):
        pass


def _sub_stack(box: Gtk.Box, width=210):
    row = Gtk.Box(vexpand=True, spacing=0)
    st = Gtk.Stack(hexpand=True, vexpand=True, transition_type=Gtk.StackTransitionType.NONE)
    sb = Gtk.StackSidebar(stack=st)
    sb.set_size_request(width, -1)
    row.append(sb)
    row.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
    row.append(st)
    box.append(row)
    return st


class ExtraPages:
    # ================================================================ Running
    def b_running(self, box):
        self.run_sum = lbl("", "dim-label", wrap=True)
        box.append(self.run_sum)
        o, i = section("Poller (rr-rootserver-poller) and its child jobs")
        self.run_poller = RowList(i, self.goto_settings, "poller process not found")
        box.append(o)
        o, i = section("RootRecord processes (command lines masked)")
        self.run_procs = RowList(i, self.goto_settings)
        box.append(o)
        o, i = section("Listening ports (all local TCP listeners)")
        self.run_ports = lbl("", "rr-mono", wrap=True, select=True)
        i.append(self.run_ports)
        box.append(o)
        o, i = section("Tunnels")
        self.run_tun = RowList(i, self.goto_settings, "no tunnel processes")
        box.append(o)
        o, i = section("Ollama and FLM (NPU)")
        self.run_ai = RowList(i, self.goto_settings)
        box.append(o)
        o, i = section("systemd --user units (RootRecord-related; all loaded units below)")
        self.run_uu = RowList(i, self.goto_settings, "none")
        self.run_uu_rest = self._expander(i, "all user units")
        box.append(o)
        o, i = section("systemd system units (running; RootRecord-related first)")
        self.run_su = RowList(i, self.goto_settings, "none")
        self.run_su_rest = self._expander(i, "other running system units")
        box.append(o)
        o, i = section("Timers and cron")
        self.run_timers = lbl("", "rr-mono", wrap=True, select=True)
        i.append(self.run_timers)
        box.append(o)

    def _expander(self, parent, title):
        ex = Gtk.Expander(label=title)
        l = lbl("", "rr-mono", wrap=True, select=True)
        ex.set_child(l)
        parent.append(ex)
        return (ex, l)

    def r_running(self):
        t0 = time.process_time()
        sn = run.snapshot()
        pol = sn["poller"]
        items = []
        if pol:
            items.append({"key": pol["pid"], "title": pol["cmd"], "page": "services",
                          "sub": f"pid {pol['pid']} · up {run.fmt_dur(pol['age'])} · {pol['rss_mb']:.0f} MB · "
                                 f"ports {', '.join(pol['ports']) or '—'}"})
        for c in sn["children"]:
            items.append({"key": c["pid"], "title": ("  " * c["depth"]) + "└ " + c["cmd"], "page": c["settings"],
                          "sub": f"pid {c['pid']} (parent {c['ppid']}) · up {run.fmt_dur(c['age'])} · {c['rss_mb']:.0f} MB"
                                 + (f" · listening {', '.join(c['ports'])}" if c["ports"] else "")})
        self.run_poller.set(items)
        tree = {pol["pid"]} if pol else set()
        tree |= {c["pid"] for c in sn["children"]}
        others = [p for p in sn["procs"] if p["pid"] not in tree]
        self.run_procs.set([{"key": p["pid"], "title": p["cmd"], "page": p["settings"],
                             "sub": f"pid {p['pid']} · up {run.fmt_dur(p['age'])} · {p['rss_mb']:.0f} MB"
                                    + (f" · listening {', '.join(p['ports'])}" if p["ports"] else "")} for p in others])
        known = {8799: "poller HTTP", 8791: "cam_server", 11434: "Ollama", 52625: "FLM", 631: "cups", 53: "dns"}
        self.run_ports.set_text("  ".join(f":{p}{' ' + known[p] if p in known else ''}" for p in sn["listen_ports"]) or "—")
        tun = sn["tunnels"]
        self.run_tun.set([{"key": "summary", "title": tun[0]["summary"], "page": "network",
                           "sub": "rr-aws ProxyCommand and poller tunnel_start need cloudflared"}] +
                         [{"key": t["pid"], "title": t["cmd"], "sub": f"pid {t['pid']} · {t['kind']}", "page": "network"} for t in tun[1:]])
        ol = sn["ollama"]
        npu = src.npu(self.paths, self.argvs(), int(self.s.get("flm_port", 52625)))
        ai = [{"key": "ollama", "page": "ai", "title": f"Ollama {'up · v' + str(ol.get('version')) if ol['up'] else 'not reachable'} (127.0.0.1:11434)",
               "sub": ("loaded: " + ", ".join(f"{m['name']} {m['size_mb']} MB (VRAM {m['vram_mb']} MB)" for m in ol["loaded"])
                       if ol.get("loaded") else "no model loaded") if ol["up"] else ol.get("error", "")}]
        ai.append({"key": "flm", "page": "ai", "title": f"FLM (NPU): {npu.get('state', '?')}",
                   "sub": f"flm pids {npu.get('flm_pids') or 'none'} · :{self.s.get('flm_port', 52625)} "
                          f"{'open' if npu.get('port_open') else 'closed'} · accel {', '.join(npu.get('accel') or []) or 'none'} · "
                          f"inference lock {npu.get('lock')}"})
        self.run_ai.set(ai)
        import re
        uu = sn["user_units"]
        rel = [u for u in uu if re.search(REL_UNIT, u["unit"])]
        self.run_uu.set([{"key": u["unit"], "title": f"{u['unit']}  —  {u['active']}/{u['sub']}", "sub": u["desc"],
                          "page": run.settings_page(u["unit"] + " " + u["desc"])} for u in rel])
        ex, l = self.run_uu_rest
        ex.set_label(f"all user units ({len(uu)})")
        l.set_text(redact("\n".join(f"{u['unit']:<48} {u['active']}/{u['sub']}" for u in uu)))
        su = sn["system_units"]
        rel = [u for u in su if re.search(REL_UNIT, u["unit"])]
        self.run_su.set([{"key": u["unit"], "title": f"{u['unit']}  —  {u['active']}/{u['sub']}", "sub": u["desc"],
                          "page": run.settings_page(u["unit"] + " " + u["desc"])} for u in rel])
        ex, l = self.run_su_rest
        rest = [u for u in su if u not in rel]
        ex.set_label(f"other running system units ({len(rest)})")
        l.set_text(redact("\n".join(f"{u['unit']:<48} {u['sub']}" for u in rest)))
        cr = sn["cron"]
        self.run_timers.set_text(redact("user timers:\n  " + ("\n  ".join(sn["user_timers"]) or "none") +
                                 "\nsystem timers:\n  " + ("\n  ".join(sn["system_timers"]) or "none") +
                                 "\nuser crontab (masked):\n  " + ("\n  ".join(cr["user"]) or "none") +
                                 "\nsystem cron entries:\n  " + (", ".join(cr["system"]) or "none")))
        self.run_sum.set_text(f"{len(sn['procs'])} RootRecord-related processes of {sn['proc_total']} · poller "
                              f"{'pid ' + str(pol['pid']) if pol else 'NOT FOUND'} with {len(sn['children'])} child processes · "
                              f"{len(uu)} user units · {len(su)} running system units · read-only, refreshed every "
                              f"{self.s['refresh_sec']} s while this page is visible (units/timers/cron cached {run.SLOW_TTL} s) · "
                              f"sample {1000 * (time.process_time() - t0):.0f} ms CPU")
        self.report["running"] = {"procs": len(sn["procs"]), "poller": pol["pid"] if pol else None,
                                  "children": len(sn["children"]), "user_units": len(uu), "system_units": len(su),
                                  "ports": len(sn["listen_ports"]), "ollama_up": ol["up"]}

    # ================================================================ Network
    def b_network(self, box):
        self.net_rates = net.Rates()
        self.net_note = lbl("", "dim-label", wrap=True)
        box.append(self.net_note)
        o, i = section("Interfaces — live rate (between refreshes) and totals since boot (/proc/net/dev)")
        self.net_rows = RowList(i, None)
        box.append(o)
        o, i = section("Starlink dish (read-only gRPC get_status at 192.168.100.1:9200)")
        self.sl_lbl = lbl("", "rr-mono", wrap=True, select=True)
        self.sl_state = lbl("", "rr-big")
        i.append(self.sl_state)
        i.append(self.sl_lbl)
        self.sl_note = lbl("", "dim-label", wrap=True)
        i.append(self.sl_note)
        box.append(o)
        self.sl_proc = None
        self.sl_last = None
        if not net.starlink_available():
            self.sl_state.set_text("Starlink: placeholder")
            self.sl_note.set_text("Starlink helper venv missing (Apps/Control-Panel/Starlink/.venv). Placeholder only.")

    def r_network(self):
        rows = self.net_rates.sample()
        items = []
        for r in rows:
            items.append({"key": r["name"], "title": f"{r['name']}  ({r['kind']}, {r['state']}{', ' + r['speed'] if r['speed'] else ''})",
                          "sub": f"↓ {net.human_rate(r['rx_rate'])}   ↑ {net.human_rate(r['tx_rate'])}   ·   since boot "
                                 f"rx {net.human_bytes(r['rx'])} / tx {net.human_bytes(r['tx'])}   ·   packets {r['rx_pk']:,}/{r['tx_pk']:,}"
                                 f"   errors {r['rx_err'] + r['tx_err']} drops {r['rx_drop'] + r['tx_drop']}"})
        self.net_rows.set(items)
        up = run._uptime()
        self.net_note.set_text(f"Since boot = {run.fmt_dur(up)} ago · rates update every {self.s['refresh_sec']} s while this page is "
                               f"visible · Starlink polled every {self._sl_iv()} s only while visible (helper process stops when you leave)")
        self.report["network"] = {"ifaces": len(rows), "starlink": (self.sl_last or {}).get("state") if self.sl_last else
                                  ("helper ready" if net.starlink_available() else "placeholder")}

    def _sl_iv(self):
        return max(10, int(self.s.get("starlink_poll_sec", 10) or 10))

    def r_starlink(self):
        d = self.sl_last or {}
        if not d:
            return
        if not d.get("ok"):
            self.sl_state.set_text("Starlink: not reachable")
            self.sl_lbl.set_text(d.get("error", ""))
            return
        f = d.get("fraction_obstructed")
        obs = (f"{100 * f:.2f}% of sky" if f is not None else "n/a") + (" · OBSTRUCTED NOW" if d.get("currently_obstructed") else "")
        self.sl_state.set_text(f"Starlink: {d.get('state')}")
        self.sl_lbl.set_text(
            f"uptime        {run.fmt_dur(d.get('uptime_s'))}\n"
            f"latency       {d.get('pop_ping_latency_ms') or 0:.1f} ms (PoP ping) · drop {100 * (d.get('pop_ping_drop_rate') or 0):.1f}%\n"
            f"throughput    ↓ {net.human_rate((d.get('downlink_bps') or 0) / 8)}   ↑ {net.human_rate((d.get('uplink_bps') or 0) / 8)}\n"
            f"obstruction   {obs}")
        self.sl_note.set_text(f"alerts: {', '.join(d.get('alerts') or []) or 'none'} · sw {d.get('software_version')} · "
                              f"sampled {d.get('at')} (rpc {d.get('rpc_ms')} ms)")

    def sl_start(self):
        if self.sl_proc is not None or self.check or not net.starlink_available() or not self.s.get("starlink_enabled", True):
            return
        try:
            self.sl_proc = Gio.Subprocess.new([str(net.STARLINK_PY), str(net.STARLINK_SCRIPT), "--loop", str(self._sl_iv())],
                                              Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)
        except GLib.Error as e:
            self.sl_note.set_text(f"Starlink helper failed to start: {e.message}")
            return
        self.sl_cancel = Gio.Cancellable()
        self.sl_stream = Gio.DataInputStream.new(self.sl_proc.get_stdout_pipe())
        self.sl_proc.wait_async(None, lambda p, r: p.wait_finish(r))
        self.sl_note.set_text("Starlink: polling…")
        self._sl_read()

    def _sl_read(self):
        self.sl_stream.read_line_async(GLib.PRIORITY_DEFAULT, self.sl_cancel, self._sl_line)

    def _sl_line(self, stream, res):
        try:
            line, _n = stream.read_line_finish_utf8(res)
        except GLib.Error:
            return
        if line is None:
            return
        try:
            self.sl_last = json.loads(line)
            self.r_starlink()
        except ValueError:
            pass
        if self.sl_proc is not None:
            self._sl_read()

    def sl_stop(self):
        if getattr(self, "sl_proc", None) is not None:
            self.sl_cancel.cancel()
            self.sl_proc.force_exit()
            self.sl_proc = None

    def starlink_once(self):
        """--check only: one synchronous read-only poll through the helper."""
        if not net.starlink_available():
            return {"ok": False, "error": "helper missing"}
        try:
            out = subprocess.run([str(net.STARLINK_PY), str(net.STARLINK_SCRIPT), "--once"], capture_output=True, text=True, timeout=20).stdout
            self.sl_last = json.loads(out.strip().splitlines()[-1])
        except Exception as e:
            self.sl_last = {"ok": False, "error": f"{type(e).__name__}"}
        self.r_starlink()
        return self.sl_last

    # ================================================================ SSH
    def b_ssh(self, box):
        box.append(lbl("Hosts from ~/.ssh/config — host, user and alias only (key files are never opened). "
                       "'Status' runs `timeout 5 ssh -o BatchMode=yes -o ConnectTimeout=5 <alias> uptime` (read-only) once per press.",
                       "dim-label", wrap=True))
        o, i = section("SSH hosts")
        self.ssh_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.ssh_list.add_css_class("boxed-list")
        i.append(self.ssh_list)
        box.append(o)
        self.ssh_rows = {}
        hs = rr_ssh.hosts()
        mainland = (self.s.get("ssh_mainland_alias") or "").strip()
        for h in hs:
            role = rr_ssh.ROLES.get(h["alias"], "Mainland monitor/server" if h["alias"] == mainland else "")
            proxy = ("ProxyCommand set" + ("" if h["proxy_ok"] else " — its binary is MISSING on this desk")) if h["proxy"] else "direct"
            r = action_row(f"{h['alias']}{'  ·  ' + role if role else ''}",
                           f"{h['user'] or '(default user)'}@{h['hostname'] or h['alias']}:{h['port']} · {proxy} · "
                           f"identity {'configured' if h['identity'] else 'default'}", 3)
            self._ssh_buttons(r, h["alias"])
            self.ssh_list.append(r)
            self.ssh_rows[h["alias"]] = r
        if not mainland or mainland not in {h["alias"] for h in hs}:
            r = action_row("Mainland monitor / US-Mainland-Server  ·  placeholder",
                           "No Host alias for Mainland in ~/.ssh/config. Library: WO-ECO lists US-Mainland-Server as a stub continuity "
                           "node; the design doc template has an empty MAINLAND_SSH_HOST/USER/PORT. Add a Host block and set "
                           "settings.json ssh_mainland_alias to enable the buttons.", 4)
            self.ssh_list.append(r)
        self.report["ssh"] = {"hosts": [h["alias"] for h in hs], "mainland": mainland or "not configured"}

    def _ssh_buttons(self, row, alias):
        if Adw is None:
            return
        b1 = Gtk.Button(label="Open terminal", valign=Gtk.Align.CENTER)
        b1.connect("clicked", lambda *_: (spawn(rr_ssh.terminal_argv(alias)) if rr_ssh.terminal_argv(alias) else self.toast("no terminal found")))
        b2 = Gtk.Button(label="Status (uptime)", valign=Gtk.Align.CENTER)
        b2.connect("clicked", lambda *_: self.ssh_check(alias))
        row.add_suffix(b1)
        row.add_suffix(b2)

    def ssh_check(self, alias):
        r = self.ssh_rows.get(alias)
        base = r.get_subtitle().split("\n")[0]
        r.set_subtitle(base + "\nchecking… (≤ 5 s)")

        def done(out, rc):
            last = (out or "").strip().splitlines()[-1:] or ["(no output)"]
            verdict = "PASS" if rc == 0 else ("FAIL (timeout 5 s)" if rc == 124 else f"FAIL (rc {rc})")
            r.set_subtitle(base + f"\n{verdict}: {last[0][:160]}  · {time.strftime('%H:%M:%S')} HST")
        spawn(rr_ssh.check_argv(alias), done, capture=True)

    # ================================================================ Not migrated (placeholders)
    def b_migration(self, box):
        try:
            data = json.loads(MIGRATION_FILE.read_text())
        except (OSError, ValueError):
            data = {"items": [], "as_of": "?"}
        items = data.get("items", [])
        box.append(lbl(f"{len(items)} items not yet migrated from G2 / G1 (as of {data.get('as_of')}). Placeholders only — "
                       "no controls. Source: Library Work-Orders README, Residual-Path-Retirement-Table (all G2 KEPT), "
                       "G3-Runtime-Verification-Checklist. Data file: Lib/rr_migration.json.", "dim-label", wrap=True))
        st = _sub_stack(box, 260)
        self.mig_stack, self.mig_items, self.mig_built = st, {}, set()
        for it in items:
            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_start=16, margin_top=8, margin_end=8)
            sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
            sc.set_child(b)
            st.add_titled(sc, it["id"], f"{it['name']}  [{it['state']}]")
            self.mig_items[it["id"]] = (it, b)
        st.connect("notify::visible-child-name", lambda *_: self._mig_build(st.get_visible_child_name()))
        if self.check:
            for k in self.mig_items:
                self._mig_build(k)
                self.check_texts.append("\n".join(rr_ui.widget_texts(self.mig_items[k][1])))
        elif items:
            self._mig_build(items[0]["id"])
        self.report["migration"] = {"placeholders": len(items), "blocked": sum(1 for x in items if x["state"] == "BLOCKED"),
                                    "verify_pending": sum(1 for x in items if x["state"] == "VERIFY PENDING")}

    def _mig_build(self, key):
        """Placeholder sub-pages: built on visit, released when another one is shown."""
        if not key or key not in self.mig_items:
            return
        for other in list(self.mig_built):
            if other != key:
                self._clear(self.mig_items[other][1])
                self.mig_built.discard(other)
        if key in self.mig_built:
            return
        self.mig_built.add(key)
        it, b = self.mig_items[key]
        b.append(lbl(it["name"], "title-2", wrap=True))
        st = lbl(f"● {it['state']}", badge_css(it["state"]))
        b.append(st)
        b.append(lbl(f"Work order / tracker: {it['wo']}", wrap=True, select=True))
        b.append(lbl(it["note"], wrap=True, select=True))
        b.append(lbl("NOT MIGRATED — placeholder page. Root Monitor will get a real page when this item lands in G3.",
                     "rr-warn", wrap=True))
        lib = Path(self.s.get("pacific_root", "")).parent.parent
        for sp in it.get("sources", []):
            p = lib / sp
            btn = Gtk.Button(label=f"Open {Path(sp).name}", halign=Gtk.Align.START)
            btn.connect("clicked", lambda _b, p=p: self.open_path(p))
            btn.set_sensitive(p.exists())
            b.append(btn)
        if it.get("settings"):
            btn = Gtk.Button(label=f"Related settings → {it['settings']}", halign=Gtk.Align.START)
            btn.connect("clicked", lambda _b, pg=it["settings"]: self.goto_settings(pg))
            b.append(btn)

    # ================================================================ Settings hub
    @property
    def reg(self):
        if getattr(self, "_reg", None) is None:
            import rr_registry
            self._reg = rr_registry.Registry()
        return self._reg

    def b_settings(self, box):
        import rr_registry
        box.append(lbl("Every RootRecord setting in one place. Secrets are masked (set/empty + length only). Each save: masked diff "
                       "→ confirm → backup (0600 for secrets) under Database/GITHUB/control-panel-settings-backups → atomic write. "
                       "Nothing is restarted; each row says what restart it needs.", "dim-label", wrap=True))
        st = _sub_stack(box, 190)
        self.set_stack, self.set_boxes, self.set_built = st, {}, set()
        for pid, title in rr_registry.PAGES:
            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_start=10, margin_end=6, margin_top=6)
            sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
            sc.set_child(b)
            st.add_titled(sc, pid, title)
            self.set_boxes[pid] = b
        st.set_visible_child_name("panel")
        st.connect("notify::visible-child-name", lambda *_: self._set_build(st.get_visible_child_name()))
        self._set_build("panel")
        if self.check:
            # build every sub-page once; collect its strings for the leak test, then release it (peak = one page)
            for pid in self.set_boxes:
                self._set_build(pid)
                self.check_texts.append("\n".join(rr_ui.widget_texts(self.set_boxes[pid])))

    def _set_build(self, pid):
        """Registry sub-pages are built on visit and RELEASED when you switch to another sub-page
        (rebuild takes ~10–150 ms), so RSS stays at one sub-page. The Panel sub-page is kept."""
        if not pid:
            return
        for other in list(self.set_built):
            if other != pid and other != "panel":
                self._clear(self.set_boxes[other])
                self.set_built.discard(other)
        if pid in self.set_built:
            return
        self.set_built.add(pid)
        box = self.set_boxes[pid]
        if pid == "panel":
            self.b_panel_settings(box)
            return
        self.b_reg_page(pid, box)

    @staticmethod
    def _clear(box):
        while (c := box.get_first_child()) is not None:
            box.remove(c)
        _trim()

    def goto_settings(self, page):
        self.stack.set_visible_child_name("settings")
        self.ensure_built("settings")
        if page in getattr(self, "set_boxes", {}):
            self.set_stack.set_visible_child_name(page)

    GROUP_MAX, GROUP_HEAD = 20, 12   # big files render their first 12 rows; the rest are built on demand

    def ensure_redact(self):
        """Fill rr_ui.REDACT once (first visit of a page that shows config / process text)."""
        if not rr_ui.REDACT:
            rr_ui.REDACT[:] = self.reg.secret_values()

    def b_reg_page(self, pid, box):
        t0 = time.process_time()
        sets = self.reg.page_settings(pid)
        if pid == "environment":
            self.reg.all_settings()  # parse every file so the security list is complete
        groups: dict = {}
        for s in sets:
            gk = "env-vars" if s.file_id.startswith("env:") else s.file_id
            groups.setdefault(gk, []).append(s)
        n_edit = sum(1 for s in sets if s.editable)
        n_sec = sum(1 for s in sets if s.secret)
        box.append(lbl(f"{len(sets)} settings · {n_edit} editable · {n_sec} secret (masked) · {len(sets) - n_edit} read-only",
                       "heading"))
        if pid == "environment" and self.reg.security_items:
            box.append(lbl(f"SECURITY ITEMS — secret-looking keys in git-tracked files ({len(self.reg.security_items)})", "heading rr-warn"))
            box.append(lbl("Never written from here. File and key names only; values are never shown.", "dim-label"))
            g = boxed_list()
            for it in self.reg.security_items:
                g.append(light_row(f"{Path(it['file']).name} → {it['key']}", f"{it['file']} · {it['assessment']}")[0])
            box.append(g)
        for gk, ss in groups.items():
            first = ss[0]
            if gk == "env-vars":
                title = "Environment variables read by Pacific scripts" if pid != "flags" else "RR_* feature flags (poller environment)"
                desc = ("Flags are set in the poller drop-in rr-flags.conf (Environment=RR_X=0/1) — takes effect after "
                        "rr-rootserver-poller.service restart (never restarted here)." if pid == "flags" else
                        "Reference view: default in code + where it is set on this desk.")
            else:
                spec = self.reg.spec(gk)
                title = Path(first.path).name if spec is None else f"{spec.path.name}  ({spec.id})"
                desc = (f"{first.path}\nservice: {first.service} · {first.restart}"
                        + (f"\nREAD-ONLY: {spec.read_only}" if spec is not None and spec.read_only else ""))
            box.append(lbl(title, "heading", wrap=True))
            box.append(lbl(redact(desc), "dim-label", wrap=True))
            g = boxed_list()
            shown = ss if len(ss) <= self.GROUP_MAX else ss[:self.GROUP_HEAD]
            for s in shown:
                g.append(self._setting_row(s))
            if len(ss) > len(shown):
                more = Gtk.Button(label=f"Show the other {len(ss) - len(shown)} settings of this file", halign=Gtk.Align.START)
                more.add_css_class("flat")

                def expand(btn, g=g, rest=ss[len(shown):]):
                    g.remove(btn.get_parent())
                    for s in rest:
                        g.append(self._setting_row(s))
                more.connect("clicked", expand)
                g.append(more)
            box.append(g)
        self.report.setdefault("settings_pages", {})[pid] = {"settings": len(sets), "editable": n_edit, "secret": n_sec,
                                                             "build_ms": round(1000 * (time.process_time() - t0))}

    def _setting_row(self, s):
        sub = f"{s.display} · {s.kind}" + (f" · {s.restart}" if s.editable else f" · read-only: {s.ro_reason}")
        r, l = light_row(s.key, sub)
        if s.editable and s.secret:
            for text, mode in (("Replace…", "replace"), ("Clear", "clear")):
                b = Gtk.Button(label=text, valign=Gtk.Align.CENTER)
                b.add_css_class("flat")
                b.connect("clicked", lambda _b, m=mode: self.edit_setting(s, m, l))
                r.append(b)
        elif s.editable:
            b = Gtk.Button(label="Edit…", valign=Gtk.Align.CENTER)
            b.add_css_class("flat")
            b.connect("clicked", lambda _b: self.edit_setting(s, "edit", l))
            r.append(b)
        return r

    def edit_setting(self, s, mode, row):
        if mode == "clear":
            self._plan_confirm(s, "", row)
            return
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        if s.secret:
            e = Gtk.PasswordEntry(show_peek_icon=False, placeholder_text="new value (never shown, never logged)")
        else:
            e = Gtk.Entry(text=s.value_text())
        box.append(e)
        hint = {"port": "integer 1–65535", "bool01": "0 or 1", "bool": "true / false", "int": "integer", "float": "number",
                "url": "http(s)/rtsp/ws URL", "host": "hostname or IP"}.get(s.kind, "text")
        box.append(lbl(f"type: {hint} · {s.restart}", "dim-label", wrap=True))
        self.confirm(f"{'Replace secret' if s.secret else 'Edit'} {s.key}", f"{s.path}", "Next", lambda: self._plan_confirm(s, e.get_text(), row),
                     extra=box)

    def _plan_confirm(self, s, new, row):
        try:
            plan = self.reg.plan(s, new)
        except (ValueError, OSError) as ex:
            self.toast(f"Not saved: {ex}")
            return
        if plan.diff == "(no change)":
            self.toast("No change")
            return
        view = Gtk.TextView(editable=False, monospace=True)
        view.get_buffer().set_text(plan.diff[:6000])
        sc = Gtk.ScrolledWindow(min_content_height=220, min_content_width=520)
        sc.set_child(view)

        def ok():
            try:
                import rr_config_io
                res = rr_config_io.commit(plan)
                self.toast(f"Saved {plan.path.name} · backup {Path(res['backup']).name} · {plan.restart_note} (nothing restarted)")
                fresh = next((x for x in self.reg.page_settings(s.page) if x.file_id == s.file_id and x.key == s.key), None)
                if fresh is not None:
                    set_row_text(row, fresh.key, f"{fresh.display} · {fresh.kind} · saved — {plan.restart_note}")
            except Exception as ex:
                self.toast(f"Save failed: {ex}")
        self.confirm(f"Save {plan.path.name}?", f"Masked diff below. {plan.restart_note}. Nothing will be restarted.", "Save", ok, extra=sc)
