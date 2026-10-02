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
from __future__ import annotations  # info: from __future__ import annotations

import json  # info: import json
import subprocess  # info: import subprocess
import time  # info: import time
from pathlib import Path  # info: from pathlib import Path

from gi.repository import Gio, GLib, Gtk  # info: from gi . repository import Gio , GLib

import rr_netstat as net  # info: import rr_netstat as net
import rr_running as run  # info: import rr_running as run
import rr_ssh  # info: import rr_ssh
import rr_sources as src  # info: import rr_sources as src
import rr_ui  # info: import rr_ui
from rr_ui import Adw, RowList, action_row, badge_css, boxed_list, esc, lbl, light_row, redact, section, set_row_text, spawn  # info: from rr_ui import Adw , RowList , action_row

HERE = Path(__file__).resolve().parent  # info: set HERE
MIGRATION_FILE = HERE / "Lib/rr_migration.json"  # info: set MIGRATION_FILE
REL_UNIT = r"^(rr-|ava-|network-globe|ollama|flm|cloudflared|rootrecord|council|cam|weather|conky|github|bluetooth|NetworkManager|ssh|cron)"  # info: set REL_UNIT


# ====================================================
# SECTION: function _bool_on
# What it does: Effective on/off: the saved value, or the code default when the flag file has no line yet.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _bool_on(s) -> bool:  # info: def _bool_on
    """Effective on/off: the saved value, or the code default when the flag file has no line yet."""  # info: """Effective on/off: the saved value, or the code default when the flag file has no line yet."""
    raw = s._value  # info: set raw
    if raw is None or str(raw).strip() == "":  # info: if raw is None or str ( raw
        disp = s.display or ""  # info: set disp
        blob = disp.split(" ·", 1)[0][len("default "):] if disp.startswith("default ") else "0"  # info: set blob
        bits = [b.strip().strip('"').strip("'") for b in blob.split("|") if b.strip()]  # info: set bits
        raw = bits[0] if bits else "0"  # info: set raw
    return str(raw).strip().strip('"').strip("'").lower() in ("1", "true", "yes")  # info: return str ( raw ) . strip (


# ====================================================
# SECTION: function _trim
# What it does: Return freed heap to the OS after releasing a sub-page (glibc malloc_trim; no-op elsewhere).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _trim():  # info: def _trim
    """Return freed heap to the OS after releasing a sub-page (glibc malloc_trim; no-op elsewhere)."""  # info: """Return freed heap to the OS after releasing a sub-page (glibc malloc_trim; no-op elsewhere)."""
    import gc  # info: import gc
    gc.collect()  # info: gc . collect ( )
    try:  # info: try :
        import ctypes  # info: import ctypes
        ctypes.CDLL("libc.so.6").malloc_trim(0)  # info: ctypes . CDLL ( "libc.so.6" ) . malloc_trim
    except (OSError, AttributeError):  # info: except ( OSError , AttributeError ) :
        pass  # info: pass


# ====================================================
# SECTION: function _sub_stack
# What it does:  sub stack.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _sub_stack(box: Gtk.Box, width=210):  # info: def _sub_stack
    row = Gtk.Box(vexpand=True, spacing=0)  # info: set row
    st = Gtk.Stack(hexpand=True, vexpand=True, transition_type=Gtk.StackTransitionType.NONE)  # info: set st
    sb = Gtk.StackSidebar(stack=st)  # info: set sb
    sb.set_size_request(width, -1)  # info: sb . set_size_request ( width , - 1
    row.append(sb)  # info: row . append ( sb )
    row.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))  # info: row . append ( Gtk . Separator (
    row.append(st)  # info: row . append ( st )
    box.append(row)  # info: box . append ( row )
    return st  # info: return st


# ====================================================
# SECTION: class ExtraPages
# What it does: ExtraPages.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class ExtraPages:  # info: class ExtraPages
    # ================================================================ Running
    def b_running(self, box):  # info: def b_running
        self.run_sum = lbl("", "dim-label", wrap=True)  # info: self . run_sum = lbl ( "" ,
        box.append(self.run_sum)  # info: box . append ( self . run_sum )
        o, i = section("Poller (rr-rootserver-poller) and its child jobs")  # info: o , i = section ( "Poller (rr-rootserver-poller) and its child jobs" )
        self.run_poller = RowList(i, self.goto_settings, "poller process not found")  # info: self . run_poller = RowList ( i ,
        box.append(o)  # info: box . append ( o )
        o, i = section("RootRecord processes (command lines masked)")  # info: o , i = section ( "RootRecord processes (command lines masked)" )
        self.run_procs = RowList(i, self.goto_settings)  # info: self . run_procs = RowList ( i ,
        box.append(o)  # info: box . append ( o )
        o, i = section("Listening ports (all local TCP listeners)")  # info: o , i = section ( "Listening ports (all local TCP listeners)" )
        self.run_ports = lbl("", "rr-mono", wrap=True, select=True)  # info: self . run_ports = lbl ( "" ,
        i.append(self.run_ports)  # info: i . append ( self . run_ports )
        box.append(o)  # info: box . append ( o )
        o, i = section("Tunnels")  # info: o , i = section ( "Tunnels" )
        self.run_tun = RowList(i, self.goto_settings, "no tunnel processes")  # info: self . run_tun = RowList ( i ,
        box.append(o)  # info: box . append ( o )
        o, i = section("Ollama and FLM (NPU)")  # info: o , i = section ( "Ollama and FLM (NPU)" )
        self.run_ai = RowList(i, self.goto_settings)  # info: self . run_ai = RowList ( i ,
        box.append(o)  # info: box . append ( o )
        o, i = section("systemd --user units (RootRecord-related; all loaded units below)")  # info: o , i = section ( "systemd --user units (RootRecord-related; all loaded units below)" )
        self.run_uu = RowList(i, self.goto_settings, "none")  # info: self . run_uu = RowList ( i ,
        self.run_uu_rest = self._expander(i, "all user units")  # info: self . run_uu_rest = self . _expander (
        box.append(o)  # info: box . append ( o )
        o, i = section("systemd system units (running; RootRecord-related first)")  # info: o , i = section ( "systemd system units (running; RootRecord-related first)" )
        self.run_su = RowList(i, self.goto_settings, "none")  # info: self . run_su = RowList ( i ,
        self.run_su_rest = self._expander(i, "other running system units")  # info: self . run_su_rest = self . _expander (
        box.append(o)  # info: box . append ( o )
        o, i = section("Timers and cron")  # info: o , i = section ( "Timers and cron" )
        self.run_timers = lbl("", "rr-mono", wrap=True, select=True)  # info: self . run_timers = lbl ( "" ,
        i.append(self.run_timers)  # info: i . append ( self . run_timers )
        box.append(o)  # info: box . append ( o )

    def _expander(self, parent, title):  # info: def _expander
        ex = Gtk.Expander(label=title)  # info: set ex
        l = lbl("", "rr-mono", wrap=True, select=True)  # info: set l
        ex.set_child(l)  # info: ex . set_child ( l )
        parent.append(ex)  # info: parent . append ( ex )
        return (ex, l)  # info: return ( ex , l )

    def r_running(self):  # info: def r_running
        t0 = time.process_time()  # info: set t0
        sn = run.snapshot()  # info: set sn
        pol = sn["poller"]  # info: set pol
        items = []  # info: set items
        if pol:  # info: if pol :
            items.append({"key": pol["pid"], "title": pol["cmd"], "page": "services",  # info: items . append ( { "key" : pol
                          "sub": f"pid {pol['pid']} · up {run.fmt_dur(pol['age'])} · {pol['rss_mb']:.0f} MB · "  # info: "sub" : f" pid { pol [ 'pid'
                                 f"ports {', '.join(pol['ports']) or '—'}"})  # info: f" ports { ', ' . join ( pol
        for c in sn["children"]:  # info: for c in sn [ "children" ] :
            items.append({"key": c["pid"], "title": ("  " * c["depth"]) + "└ " + c["cmd"], "page": c["settings"],  # info: items . append ( { "key" : c
                          "sub": f"pid {c['pid']} (parent {c['ppid']}) · up {run.fmt_dur(c['age'])} · {c['rss_mb']:.0f} MB"  # info: "sub" : f" pid { c [ 'pid'
                                 + (f" · listening {', '.join(c['ports'])}" if c["ports"] else "")})  # info: call +
        self.run_poller.set(items)  # info: self . run_poller . set ( items )
        tree = {pol["pid"]} if pol else set()  # info: set tree
        tree |= {c["pid"] for c in sn["children"]}  # info: tree |= { c [ "pid" ] for
        others = [p for p in sn["procs"] if p["pid"] not in tree]  # info: set others
        self.run_procs.set([{"key": p["pid"], "title": p["cmd"], "page": p["settings"],  # info: self . run_procs . set ( [ {
                             "sub": f"pid {p['pid']} · up {run.fmt_dur(p['age'])} · {p['rss_mb']:.0f} MB"  # info: "sub" : f" pid { p [ 'pid'
                                    + (f" · listening {', '.join(p['ports'])}" if p["ports"] else "")} for p in others])  # info: call +
        known = {8799: "poller HTTP", 8791: "cam_server", 11434: "Ollama", 52625: "FLM", 631: "cups", 53: "dns"}  # info: set known
        self.run_ports.set_text("  ".join(f":{p}{' ' + known[p] if p in known else ''}" for p in sn["listen_ports"]) or "—")  # info: self . run_ports . set_text ( " " .
        tun = sn["tunnels"]  # info: set tun
        self.run_tun.set([{"key": "summary", "title": tun[0]["summary"], "page": "network",  # info: self . run_tun . set ( [ {
                           "sub": "poller tunnel_start runs cloudflared as a poller child · SSH page shows whether rr-aws's ProxyCommand binary exists"}] +  # info: "sub" : "poller tunnel_start runs cloudflared as a poller child · SSH page shows whether rr-aws's ProxyCommand
                         [{"key": t["pid"], "title": t["cmd"], "sub": f"pid {t['pid']} · {t['kind']}", "page": "network"} for t in tun[1:]])  # info: [ { "key" : t [ "pid" ]
        ol = sn["ollama"]  # info: set ol
        npu = src.npu(self.paths, self.argvs(), int(self.s.get("flm_port", 52625)))  # info: set npu
        ai = [{"key": "ollama", "page": "ai", "title": f"Ollama {'up · v' + str(ol.get('version')) if ol['up'] else 'not reachable'} (127.0.0.1:11434)",  # info: set ai
               "sub": ("loaded: " + ", ".join(f"{m['name']} {m['size_mb']} MB (VRAM {m['vram_mb']} MB)" for m in ol["loaded"])  # info: call "sub"
                       if ol.get("loaded") else "no model loaded") if ol["up"] else ol.get("error", "")}]  # info: if ol . get ( "loaded" ) else
        ai.append({"key": "flm", "page": "ai", "title": f"FLM (NPU): {npu.get('state', '?')}",  # info: ai . append ( { "key" : "flm"
                   "sub": f"flm pids {npu.get('flm_pids') or 'none'} · :{self.s.get('flm_port', 52625)} "  # info: "sub" : f" flm pids { npu . get
                          f"{'open' if npu.get('port_open') else 'closed'} · accel {', '.join(npu.get('accel') or []) or 'none'} · "  # info: f" { 'open' if npu . get (
                          f"inference lock {npu.get('lock')}"})  # info: f" inference lock { npu . get ( 'lock'
        self.run_ai.set(ai)  # info: self . run_ai . set ( ai )
        import re  # info: import re
        uu = sn["user_units"]  # info: set uu
        rel = [u for u in uu if re.search(REL_UNIT, u["unit"])]  # info: set rel
        self.run_uu.set([{"key": u["unit"], "title": f"{u['unit']}  —  {u['active']}/{u['sub']}", "sub": u["desc"],  # info: self . run_uu . set ( [ {
                          "page": run.settings_page(u["unit"] + " " + u["desc"])} for u in rel])  # info: "page" : run . settings_page ( u [
        ex, l = self.run_uu_rest  # info: ex , l = self . run_uu_rest
        ex.set_label(f"all user units ({len(uu)})")  # info: ex . set_label ( f" all user units ( { len
        l.set_text(redact("\n".join(f"{u['unit']:<48} {u['active']}/{u['sub']}" for u in uu)))  # info: l . set_text ( redact ( "\n" .
        su = sn["system_units"]  # info: set su
        rel = [u for u in su if re.search(REL_UNIT, u["unit"])]  # info: set rel
        self.run_su.set([{"key": u["unit"], "title": f"{u['unit']}  —  {u['active']}/{u['sub']}", "sub": u["desc"],  # info: self . run_su . set ( [ {
                          "page": run.settings_page(u["unit"] + " " + u["desc"])} for u in rel])  # info: "page" : run . settings_page ( u [
        ex, l = self.run_su_rest  # info: ex , l = self . run_su_rest
        rest = [u for u in su if u not in rel]  # info: set rest
        ex.set_label(f"other running system units ({len(rest)})")  # info: ex . set_label ( f" other running system units ( { len
        l.set_text(redact("\n".join(f"{u['unit']:<48} {u['sub']}" for u in rest)))  # info: l . set_text ( redact ( "\n" .
        cr = sn["cron"]  # info: set cr
        self.run_timers.set_text(redact("user timers:\n  " + ("\n  ".join(sn["user_timers"]) or "none") +  # info: self . run_timers . set_text ( redact (
                                 "\nsystem timers:\n  " + ("\n  ".join(sn["system_timers"]) or "none") +  # info: call "\nsystem timers:\n "
                                 "\nuser crontab (masked):\n  " + ("\n  ".join(cr["user"]) or "none") +  # info: call "\nuser crontab (masked):\n "
                                 "\nsystem cron entries:\n  " + (", ".join(cr["system"]) or "none")))  # info: call "\nsystem cron entries:\n "
        self.run_sum.set_text(f"{len(sn['procs'])} RootRecord-related processes of {sn['proc_total']} · poller "  # info: self . run_sum . set_text ( f" {
                              f"{'pid ' + str(pol['pid']) if pol else 'NOT FOUND'} with {len(sn['children'])} child processes · "  # info: f" { 'pid ' + str ( pol [
                              f"{len(uu)} user units · {len(su)} running system units · read-only, refreshed every "  # info: f" { len ( uu ) } user units ·
                              f"{self.s['refresh_sec']} s while this page is visible (units/timers/cron cached {run.SLOW_TTL} s) · "  # info: f" { self . s [ 'refresh_sec' ]
                              f"sample {1000 * (time.process_time() - t0):.0f} ms CPU")  # info: f" sample { 1000 * ( time .
        self.report["running"] = {"procs": len(sn["procs"]), "poller": pol["pid"] if pol else None,  # info: self . report [ "running" ] = {
                                  "children": len(sn["children"]), "user_units": len(uu), "system_units": len(su),  # info: "children" : len ( sn [ "children" ]
                                  "ports": len(sn["listen_ports"]), "ollama_up": ol["up"]}  # info: "ports" : len ( sn [ "listen_ports" ]

    # ================================================================ Network
    def b_network(self, box):  # info: def b_network
        self.net_rates = net.Rates()  # info: self . net_rates = net . Rates (
        self.net_note = lbl("", "dim-label", wrap=True)  # info: self . net_note = lbl ( "" ,
        box.append(self.net_note)  # info: box . append ( self . net_note )
        o, i = section("Interfaces — live rate (between refreshes) and totals since boot (/proc/net/dev)")  # info: o , i = section ( "Interfaces — live rate (between refreshes) and totals since boot (/proc/net/dev)" )
        self.net_rows = RowList(i, None)  # info: self . net_rows = RowList ( i ,
        box.append(o)  # info: box . append ( o )
        o, i = section("Starlink dish (read-only gRPC get_status at 192.168.100.1:9200)")  # info: o , i = section ( "Starlink dish (read-only gRPC get_status at 192.168.100.1:9200)" )
        self.sl_lbl = lbl("", "rr-mono", wrap=True, select=True)  # info: self . sl_lbl = lbl ( "" ,
        self.sl_state = lbl("", "rr-big")  # info: self . sl_state = lbl ( "" ,
        i.append(self.sl_state)  # info: i . append ( self . sl_state )
        i.append(self.sl_lbl)  # info: i . append ( self . sl_lbl )
        self.sl_note = lbl("", "dim-label", wrap=True)  # info: self . sl_note = lbl ( "" ,
        i.append(self.sl_note)  # info: i . append ( self . sl_note )
        box.append(o)  # info: box . append ( o )
        self.sl_proc = None  # info: self . sl_proc = None
        self.sl_last = None  # info: self . sl_last = None
        if not net.starlink_available():  # info: if not net . starlink_available ( ) :
            self.sl_state.set_text("Starlink: placeholder")  # info: self . sl_state . set_text ( "Starlink: placeholder" )
            self.sl_note.set_text("Starlink helper venv missing (Apps/Control-Panel/Starlink/.venv). Placeholder only.")  # info: self . sl_note . set_text ( "Starlink helper venv missing (Apps/Control-Panel/Starlink/.venv). Placeholder onl

    def r_network(self):  # info: def r_network
        rows = self.net_rates.sample()  # info: set rows
        items = []  # info: set items
        for r in rows:  # info: for r in rows :
            items.append({"key": r["name"], "title": f"{r['name']}  ({r['kind']}, {r['state']}{', ' + r['speed'] if r['speed'] else ''})",  # info: items . append ( { "key" : r
                          "sub": f"↓ {net.human_rate(r['rx_rate'])}   ↑ {net.human_rate(r['tx_rate'])}   ·   since boot "  # info: "sub" : f" ↓ { net . human_rate
                                 f"rx {net.human_bytes(r['rx'])} / tx {net.human_bytes(r['tx'])}   ·   packets {r['rx_pk']:,}/{r['tx_pk']:,}"  # info: f" rx { net . human_bytes ( r
                                 f"   errors {r['rx_err'] + r['tx_err']} drops {r['rx_drop'] + r['tx_drop']}"})  # info: f" errors { r [ 'rx_err' ] +
        self.net_rows.set(items)  # info: self . net_rows . set ( items )
        up = run._uptime()  # info: set up
        self.net_note.set_text(f"Since boot = {run.fmt_dur(up)} ago · rates update every {self.s['refresh_sec']} s while this page is "  # info: self . net_note . set_text ( f" Since boot =
                               f"visible · Starlink polled every {self._sl_iv()} s only while visible (helper process stops when you leave)")  # info: f" visible · Starlink polled every { self . _sl_iv ( )
        self.report["network"] = {"ifaces": len(rows), "starlink": (self.sl_last or {}).get("state") if self.sl_last else  # info: self . report [ "network" ] = {
                                  ("helper ready" if net.starlink_available() else "placeholder")}  # info: call (

    def _sl_iv(self):  # info: def _sl_iv
        return max(10, int(self.s.get("starlink_poll_sec", 10) or 10))  # info: return max ( 10 , int ( self

    def r_starlink(self):  # info: def r_starlink
        d = self.sl_last or {}  # info: set d
        if not d:  # info: if not d :
            return  # info: return
        if not d.get("ok"):  # info: if not d . get ( "ok" )
            self.sl_state.set_text("Starlink: not reachable")  # info: self . sl_state . set_text ( "Starlink: not reachable" )
            self.sl_lbl.set_text(d.get("error", ""))  # info: self . sl_lbl . set_text ( d .
            return  # info: return
        f = d.get("fraction_obstructed")  # info: set f
        obs = (f"{100 * f:.2f}% of sky" if f is not None else "n/a") + (" · OBSTRUCTED NOW" if d.get("currently_obstructed") else "")  # info: set obs
        self.sl_state.set_text(f"Starlink: {d.get('state')}")  # info: self . sl_state . set_text ( f" Starlink:
        self.sl_lbl.set_text(  # info: self . sl_lbl . set_text (
            f"uptime        {run.fmt_dur(d.get('uptime_s'))}\n"  # info: f" uptime { run . fmt_dur ( d
            f"latency       {d.get('pop_ping_latency_ms') or 0:.1f} ms (PoP ping) · drop {100 * (d.get('pop_ping_drop_rate') or 0):.1f}%\n"  # info: f" latency { d . get ( 'pop_ping_latency_ms'
            f"throughput    ↓ {net.human_rate((d.get('downlink_bps') or 0) / 8)}   ↑ {net.human_rate((d.get('uplink_bps') or 0) / 8)}\n"  # info: f" throughput ↓ { net . human_rate ( (
            f"obstruction   {obs}")  # info: f" obstruction { obs } " )
        self.sl_note.set_text(f"alerts: {', '.join(d.get('alerts') or []) or 'none'} · sw {d.get('software_version')} · "  # info: self . sl_note . set_text ( f" alerts:
                              f"sampled {d.get('at')} (rpc {d.get('rpc_ms')} ms)")  # info: f" sampled { d . get ( 'at'

    def sl_start(self):  # info: def sl_start
        if self.sl_proc is not None or self.check or not net.starlink_available() or not self.s.get("starlink_enabled", True):  # info: if self . sl_proc is not None or
            return  # info: return
        try:  # info: try :
            self.sl_proc = Gio.Subprocess.new([str(net.STARLINK_PY), str(net.STARLINK_SCRIPT), "--loop", str(self._sl_iv())],  # info: self . sl_proc = Gio . Subprocess .
                                              Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE)  # info: Gio . SubprocessFlags . STDOUT_PIPE | Gio .
        except GLib.Error as e:  # info: except GLib . Error as e :
            self.sl_note.set_text(f"Starlink helper failed to start: {e.message}")  # info: self . sl_note . set_text ( f" Starlink helper failed to start:
            return  # info: return
        self.sl_cancel = Gio.Cancellable()  # info: self . sl_cancel = Gio . Cancellable (
        self.sl_stream = Gio.DataInputStream.new(self.sl_proc.get_stdout_pipe())  # info: self . sl_stream = Gio . DataInputStream .
        self.sl_proc.wait_async(None, lambda p, r: p.wait_finish(r))  # info: self . sl_proc . wait_async ( None ,
        self.sl_note.set_text("Starlink: polling…")  # info: self . sl_note . set_text ( "Starlink: polling…" )
        self._sl_read()  # info: self . _sl_read ( )

    def _sl_read(self):  # info: def _sl_read
        self.sl_stream.read_line_async(GLib.PRIORITY_DEFAULT, self.sl_cancel, self._sl_line)  # info: self . sl_stream . read_line_async ( GLib .

    def _sl_line(self, stream, res):  # info: def _sl_line
        try:  # info: try :
            line, _n = stream.read_line_finish_utf8(res)  # info: line , _n = stream . read_line_finish_utf8 (
        except GLib.Error:  # info: except GLib . Error :
            return  # info: return
        if line is None:  # info: if line is None :
            return  # info: return
        try:  # info: try :
            self.sl_last = json.loads(line)  # info: self . sl_last = json . loads (
            self.r_starlink()  # info: self . r_starlink ( )
        except ValueError:  # info: except ValueError :
            pass  # info: pass
        if self.sl_proc is not None:  # info: if self . sl_proc is not None :
            self._sl_read()  # info: self . _sl_read ( )

    def sl_stop(self):  # info: def sl_stop
        if getattr(self, "sl_proc", None) is not None:  # info: if getattr ( self , "sl_proc" , None
            self.sl_cancel.cancel()  # info: self . sl_cancel . cancel ( )
            self.sl_proc.force_exit()  # info: self . sl_proc . force_exit ( )
            self.sl_proc = None  # info: self . sl_proc = None

    def starlink_once(self):  # info: def starlink_once
        """--check only: one synchronous read-only poll through the helper."""  # info: """--check only: one synchronous read-only poll through the helper."""
        if not net.starlink_available():  # info: if not net . starlink_available ( ) :
            return {"ok": False, "error": "helper missing"}  # info: return { "ok" : False , "error" :
        try:  # info: try :
            out = subprocess.run([str(net.STARLINK_PY), str(net.STARLINK_SCRIPT), "--once"], capture_output=True, text=True, timeout=20).stdout  # info: set out
            self.sl_last = json.loads(out.strip().splitlines()[-1])  # info: self . sl_last = json . loads (
        except Exception as e:  # info: except Exception as e :
            self.sl_last = {"ok": False, "error": f"{type(e).__name__}"}  # info: self . sl_last = { "ok" : False
        self.r_starlink()  # info: self . r_starlink ( )
        return self.sl_last  # info: return self . sl_last

    # ================================================================ SSH
    def b_ssh(self, box):  # info: def b_ssh
        box.append(lbl("Hosts from ~/.ssh/config — host, user and alias only (key files are never opened). "  # info: box . append ( lbl ( "Hosts from ~/.ssh/config — host, user and alias only (key files are never opened). "
                       "'Status' runs `timeout 5 ssh -o BatchMode=yes -o ConnectTimeout=5 <alias> uptime` (read-only) once per press.",  # info: "'Status' runs `timeout 5 ssh -o BatchMode=yes -o ConnectTimeout=5 <alias> uptime` (read-only) once per press.
                       "dim-label", wrap=True))  # info: "dim-label" , wrap = True ) )
        o, i = section("SSH hosts")  # info: o , i = section ( "SSH hosts" )
        self.ssh_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)  # info: self . ssh_list = Gtk . ListBox (
        self.ssh_list.add_css_class("boxed-list")  # info: self . ssh_list . add_css_class ( "boxed-list" )
        i.append(self.ssh_list)  # info: i . append ( self . ssh_list )
        box.append(o)  # info: box . append ( o )
        self.ssh_rows = {}  # info: self . ssh_rows = { }
        hs = rr_ssh.hosts()  # info: set hs
        mainland = (self.s.get("ssh_mainland_alias") or "").strip()  # info: set mainland
        for h in hs:  # info: for h in hs :
            role = rr_ssh.ROLES.get(h["alias"], "Mainland monitor/server" if h["alias"] == mainland else "")  # info: set role
            proxy = ("ProxyCommand set" + ("" if h["proxy_ok"] else " — its binary is MISSING on this desk")) if h["proxy"] else "direct"  # info: set proxy
            r = action_row(f"{h['alias']}{'  ·  ' + role if role else ''}",  # info: set r
                           f"{h['user'] or '(default user)'}@{h['hostname'] or h['alias']}:{h['port']} · {proxy} · "  # info: f" { h [ 'user' ] or '(default user)'
                           f"identity {'configured' if h['identity'] else 'default'}", 3)  # info: f" identity { 'configured' if h [ 'identity'
            self._ssh_buttons(r, h["alias"])  # info: self . _ssh_buttons ( r , h [
            self.ssh_list.append(r)  # info: self . ssh_list . append ( r )
            self.ssh_rows[h["alias"]] = r  # info: self . ssh_rows [ h [ "alias" ]
        if not mainland or mainland not in {h["alias"] for h in hs}:  # info: if not mainland or mainland not in {
            r = action_row("Mainland monitor / US-Mainland-One  ·  placeholder",  # info: set r
                           "No Host alias for Mainland in ~/.ssh/config. Library: WO-ECO lists US-Mainland-One as a stub continuity "  # info: "No Host alias for Mainland in ~/.ssh/config. Library: WO-ECO lists US-Mainland-One as a stub continuity "
                           "node; the design doc template has an empty MAINLAND_SSH_HOST/USER/PORT. Add a Host block and set "  # info: "node; the design doc template has an empty MAINLAND_SSH_HOST/USER/PORT. Add a Host block and set "
                           "settings.json ssh_mainland_alias to enable the buttons.", 4)  # info: "settings.json ssh_mainland_alias to enable the buttons." , 4 )
            self.ssh_list.append(r)  # info: self . ssh_list . append ( r )
        self.report["ssh"] = {"hosts": [h["alias"] for h in hs], "mainland": mainland or "not configured"}  # info: self . report [ "ssh" ] = {

    def _ssh_buttons(self, row, alias):  # info: def _ssh_buttons
        if Adw is None:  # info: if Adw is None :
            return  # info: return
        b1 = Gtk.Button(label="Open terminal", valign=Gtk.Align.CENTER)  # info: set b1
        b1.connect("clicked", lambda *_: (spawn(rr_ssh.terminal_argv(alias)) if rr_ssh.terminal_argv(alias) else self.toast("no terminal found")))  # info: b1 . connect ( "clicked" , lambda *
        b2 = Gtk.Button(label="Status (uptime)", valign=Gtk.Align.CENTER)  # info: set b2
        b2.connect("clicked", lambda *_: self.ssh_check(alias))  # info: b2 . connect ( "clicked" , lambda *
        row.add_suffix(b1)  # info: row . add_suffix ( b1 )
        row.add_suffix(b2)  # info: row . add_suffix ( b2 )

    def ssh_check(self, alias):  # info: def ssh_check
        r = self.ssh_rows.get(alias)  # info: set r
        base = r.get_subtitle().split("\n")[0]  # info: set base
        r.set_subtitle(base + "\nchecking… (≤ 5 s)")  # info: r . set_subtitle ( base + "\nchecking… (≤ 5 s)" )

        def done(out, rc):  # info: def done
            last = (out or "").strip().splitlines()[-1:] or ["(no output)"]  # info: set last
            verdict = "PASS" if rc == 0 else ("FAIL (timeout 5 s)" if rc == 124 else f"FAIL (rc {rc})")  # info: set verdict
            r.set_subtitle(base + f"\n{verdict}: {last[0][:160]}  · {time.strftime('%H:%M:%S')} HST")  # info: r . set_subtitle ( base + f" \n
        spawn(rr_ssh.check_argv(alias), done, capture=True)  # info: call spawn

    # ================================================================ Not migrated (placeholders)
    def b_migration(self, box):  # info: def b_migration
        try:  # info: try :
            data = json.loads(MIGRATION_FILE.read_text())  # info: set data
        except (OSError, ValueError):  # info: except ( OSError , ValueError ) :
            data = {"items": [], "as_of": "?"}  # info: set data
        items = data.get("items", [])  # info: set items
        box.append(lbl(f"{len(items)} items not yet migrated from G2 / G1 (as of {data.get('as_of')}). Placeholders only — "  # info: box . append ( lbl ( f" {
                       "no controls. Source: Library Work-Orders README, Residual-Path-Retirement-Table, "  # info: "no controls. Source: Library Work-Orders README, Residual-Path-Retirement-Table, "
                       "G3-Runtime-Verification-Checklist. Data file: Lib/rr_migration.json.", "dim-label", wrap=True))  # info: "G3-Runtime-Verification-Checklist. Data file: Lib/rr_migration.json." , "dim-label" , wrap = True )
        st = _sub_stack(box, 260)  # info: set st
        self.mig_stack, self.mig_items, self.mig_built = st, {}, set()  # info: self . mig_stack , self . mig_items ,
        for it in items:  # info: for it in items :
            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10, margin_start=16, margin_top=8, margin_end=8)  # info: set b
            sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)  # info: set sc
            sc.set_child(b)  # info: sc . set_child ( b )
            st.add_titled(sc, it["id"], f"{it['name']}  [{it['state']}]")  # info: st . add_titled ( sc , it [
            self.mig_items[it["id"]] = (it, b)  # info: self . mig_items [ it [ "id" ]
        st.connect("notify::visible-child-name", lambda *_: self._mig_build(st.get_visible_child_name()))  # info: st . connect ( "notify::visible-child-name" , lambda *
        if self.check:  # info: if self . check :
            for k in self.mig_items:  # info: for k in self . mig_items :
                self._mig_build(k)  # info: self . _mig_build ( k )
                self.check_texts.append("\n".join(rr_ui.widget_texts(self.mig_items[k][1])))  # info: self . check_texts . append ( "\n" .
        elif items:  # info: elif items :
            self._mig_build(items[0]["id"])  # info: self . _mig_build ( items [ 0 ]
        self.report["migration"] = {"placeholders": len(items), "blocked": sum(1 for x in items if x["state"] == "BLOCKED"),  # info: self . report [ "migration" ] = {
                                    "verify_pending": sum(1 for x in items if x["state"] == "VERIFY PENDING")}  # info: "verify_pending" : sum ( 1 for x in

    def _mig_build(self, key):  # info: def _mig_build
        """Placeholder sub-pages: built on visit, released when another one is shown."""  # info: """Placeholder sub-pages: built on visit, released when another one is shown."""
        if not key or key not in self.mig_items:  # info: if not key or key not in self
            return  # info: return
        for other in list(self.mig_built):  # info: for other in list ( self . mig_built
            if other != key:  # info: if other != key :
                self._clear(self.mig_items[other][1])  # info: self . _clear ( self . mig_items [
                self.mig_built.discard(other)  # info: self . mig_built . discard ( other )
        if key in self.mig_built:  # info: if key in self . mig_built :
            return  # info: return
        self.mig_built.add(key)  # info: self . mig_built . add ( key )
        it, b = self.mig_items[key]  # info: it , b = self . mig_items [
        b.append(lbl(it["name"], "title-2", wrap=True))  # info: b . append ( lbl ( it [
        st = lbl(f"● {it['state']}", badge_css(it["state"]))  # info: set st
        b.append(st)  # info: b . append ( st )
        b.append(lbl(f"Work order / tracker: {it['wo']}", wrap=True, select=True))  # info: b . append ( lbl ( f" Work order / tracker:
        b.append(lbl(it["note"], wrap=True, select=True))  # info: b . append ( lbl ( it [
        b.append(lbl("NOT MIGRATED — placeholder page. Root Monitor will get a real page when this item lands in G3.",  # info: b . append ( lbl ( "NOT MIGRATED — placeholder page. Root Monitor will get a real page when this item lands in
                     "rr-warn", wrap=True))  # info: "rr-warn" , wrap = True ) )
        lib = Path(self.s.get("pacific_root", "")).parent.parent  # info: set lib
        for sp in it.get("sources", []):  # info: for sp in it . get ( "sources"
            p = lib / sp  # info: set p
            btn = Gtk.Button(label=f"Open {Path(sp).name}", halign=Gtk.Align.START)  # info: set btn
            btn.connect("clicked", lambda _b, p=p: self.open_path(p))  # info: btn . connect ( "clicked" , lambda _b
            btn.set_sensitive(p.exists())  # info: btn . set_sensitive ( p . exists (
            b.append(btn)  # info: b . append ( btn )
        if it.get("settings"):  # info: if it . get ( "settings" ) :
            btn = Gtk.Button(label=f"Related settings → {it['settings']}", halign=Gtk.Align.START)  # info: set btn
            btn.connect("clicked", lambda _b, pg=it["settings"]: self.goto_settings(pg))  # info: btn . connect ( "clicked" , lambda _b
            b.append(btn)  # info: b . append ( btn )

    # ================================================================ Settings hub
    @property  # info: decorator property
    def reg(self):  # info: def reg
        if getattr(self, "_reg", None) is None:  # info: if getattr ( self , "_reg" , None
            import rr_registry  # info: import rr_registry
            self._reg = rr_registry.Registry()  # info: self . _reg = rr_registry . Registry (
        return self._reg  # info: return self . _reg

    def b_settings(self, box):  # info: def b_settings
        import rr_registry  # info: import rr_registry
        box.append(lbl("Every RootRecord setting in one place. Secrets are masked (set/empty + length only). Each save: masked diff "  # info: box . append ( lbl ( "Every RootRecord setting in one place. Secrets are masked (set/empty + length only). Eac
                       "→ confirm → backup (0600 for secrets) under Database/GITHUB/control-panel-settings-backups → atomic write. "  # info: "→ confirm → backup (0600 for secrets) under Database/GITHUB/control-panel-settings-backups → atomic write. "
                       "Nothing is restarted; each row says what restart it needs.", "dim-label", wrap=True))  # info: "Nothing is restarted; each row says what restart it needs." , "dim-label" , wrap = True )
        st = _sub_stack(box, 190)  # info: set st
        self.set_stack, self.set_boxes, self.set_built = st, {}, set()  # info: self . set_stack , self . set_boxes ,
        for pid, title in rr_registry.PAGES:  # info: for pid , title in rr_registry . PAGES
            b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_start=10, margin_end=6, margin_top=6)  # info: set b
            sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)  # info: set sc
            sc.set_child(b)  # info: sc . set_child ( b )
            st.add_titled(sc, pid, title)  # info: st . add_titled ( sc , pid ,
            self.set_boxes[pid] = b  # info: self . set_boxes [ pid ] = b
        st.set_visible_child_name("panel")  # info: st . set_visible_child_name ( "panel" )
        st.connect("notify::visible-child-name", lambda *_: self._set_build(st.get_visible_child_name()))  # info: st . connect ( "notify::visible-child-name" , lambda *
        self._set_build("panel")  # info: self . _set_build ( "panel" )
        if self.check:  # info: if self . check :
            # build every sub-page once; collect its strings for the leak test, then release it (peak = one page)
            for pid in self.set_boxes:  # info: for pid in self . set_boxes :
                self._set_build(pid)  # info: self . _set_build ( pid )
                self.check_texts.append("\n".join(rr_ui.widget_texts(self.set_boxes[pid])))  # info: self . check_texts . append ( "\n" .

    def _set_build(self, pid):  # info: def _set_build
        """Registry sub-pages are built on visit and RELEASED when you switch to another sub-page
        (rebuild takes ~10–150 ms), so RSS stays at one sub-page. The Panel sub-page is kept."""
        if not pid:  # info: if not pid :
            return  # info: return
        for other in list(self.set_built):  # info: for other in list ( self . set_built
            if other != pid and other != "panel":  # info: if other != pid and other != "panel"
                self._clear(self.set_boxes[other])  # info: self . _clear ( self . set_boxes [
                self.set_built.discard(other)  # info: self . set_built . discard ( other )
        if pid in self.set_built:  # info: if pid in self . set_built :
            return  # info: return
        self.set_built.add(pid)  # info: self . set_built . add ( pid )
        box = self.set_boxes[pid]  # info: set box
        if pid == "panel":  # info: if pid == "panel" :
            self.b_panel_settings(box)  # info: self . b_panel_settings ( box )
            return  # info: return
        self.b_reg_page(pid, box)  # info: self . b_reg_page ( pid , box )

    @staticmethod  # info: decorator staticmethod
    def _clear(box):  # info: def _clear
        while (c := box.get_first_child()) is not None:  # info: while ( c := box . get_first_child (
            box.remove(c)  # info: box . remove ( c )
        _trim()  # info: call _trim

    def goto_settings(self, page):  # info: def goto_settings
        self.stack.set_visible_child_name("settings")  # info: self . stack . set_visible_child_name ( "settings" )
        self.ensure_built("settings")  # info: self . ensure_built ( "settings" )
        if page in getattr(self, "set_boxes", {}):  # info: if page in getattr ( self , "set_boxes"
            self.set_stack.set_visible_child_name(page)  # info: self . set_stack . set_visible_child_name ( page )

    # Every setting of a file is built when that page is opened. Big files (weather resources, specialist routes)
    # are long scrolls, not a hidden tail.

    def ensure_redact(self):  # info: def ensure_redact
        """Fill rr_ui.REDACT once (first visit of a page that shows config / process text)."""  # info: """Fill rr_ui.REDACT once (first visit of a page that shows config / process text)."""
        if not rr_ui.REDACT:  # info: if not rr_ui . REDACT :
            rr_ui.REDACT[:] = self.reg.secret_values()  # info: rr_ui . REDACT [ : ] = self

    def b_reg_page(self, pid, box):  # info: def b_reg_page
        t0 = time.process_time()  # info: set t0
        sets = self.reg.page_settings(pid)  # info: set sets
        if pid == "environment":  # info: if pid == "environment" :
            self.reg.all_settings()  # parse every file so the security list is complete
        groups: dict = {}  # info: set groups
        for s in sets:  # info: for s in sets :
            gk = "env-vars" if s.file_id.startswith("env:") else s.file_id  # info: set gk
            groups.setdefault(gk, []).append(s)  # info: groups . setdefault ( gk , [ ]
        n_edit = sum(1 for s in sets if s.editable)  # info: set n_edit
        n_sec = sum(1 for s in sets if s.secret)  # info: set n_sec
        box.append(lbl(f"{len(sets)} settings · {n_edit} editable · {n_sec} secret (masked) · {len(sets) - n_edit} read-only",  # info: box . append ( lbl ( f" {
                       "heading"))  # info: "heading" ) )
        if pid == "environment" and self.reg.security_items:  # info: if pid == "environment" and self . reg
            box.append(lbl(f"SECURITY ITEMS — secret-looking keys in git-tracked files ({len(self.reg.security_items)})", "heading rr-warn"))  # info: box . append ( lbl ( f" SECURITY ITEMS — secret-looking keys in git-tracked files (
            box.append(lbl("Never written from here. File and key names only; values are never shown.", "dim-label"))  # info: box . append ( lbl ( "Never written from here. File and key names only; values are never shown." ,
            g = boxed_list()  # info: set g
            for it in self.reg.security_items:  # info: for it in self . reg . security_items
                g.append(light_row(f"{Path(it['file']).name} → {it['key']}", f"{it['file']} · {it['assessment']}")[0])  # info: g . append ( light_row ( f" {
            box.append(g)  # info: box . append ( g )
        for gk, ss in groups.items():  # info: for gk , ss in groups . items
            first = ss[0]  # info: set first
            if gk == "env-vars":  # info: if gk == "env-vars" :
                title = "Environment variables read by Pacific scripts" if pid != "flags" else "RR_* feature flags (poller environment)"  # info: set title
                desc = ("Each flag is a toggle. Saving writes rr-flags.conf (created on the first save). "  # info: set desc
                        "The poller is not restarted; the new value is used the next time that service starts."  # info: "The poller is not restarted; the new value is used the next time that service starts."
                        if pid == "flags" else  # info: if pid == "flags" else
                        "Reference view: default in code + where it is set on this desk.")  # info: "Reference view: default in code + where it is set on this desk." )
            else:  # info: else :
                spec = self.reg.spec(gk)  # info: set spec
                title = Path(first.path).name if spec is None else f"{spec.path.name}  ({spec.id})"  # info: set title
                desc = (f"{first.path}\nservice: {first.service} · {first.restart}"  # info: set desc
                        + (f"\nREAD-ONLY: {spec.read_only}" if spec is not None and spec.read_only else ""))  # info: call +
            box.append(lbl(title, "heading", wrap=True))  # info: box . append ( lbl ( title ,
            box.append(lbl(redact(desc), "dim-label", wrap=True))  # info: box . append ( lbl ( redact (
            g = boxed_list()  # info: set g
            for s in ss:  # info: for s in ss :
                g.append(self._setting_row(s))  # info: g . append ( self . _setting_row (
            box.append(g)  # info: box . append ( g )
        self.report.setdefault("settings_pages", {})[pid] = {"settings": len(sets), "editable": n_edit, "secret": n_sec,  # info: self . report . setdefault ( "settings_pages" ,
                                                             "build_ms": round(1000 * (time.process_time() - t0))}  # info: "build_ms" : round ( 1000 * ( time

    def _setting_row(self, s):  # info: def _setting_row
        sub = f"{s.display} · {s.kind}" + (f" · {s.restart}" if s.editable else f" · read-only: {s.ro_reason}")  # info: set sub
        r, l = light_row(s.key, sub)  # info: r , l = light_row ( s .
        if s.editable and s.kind == "bool01":  # info: if s . editable and s . kind
            on = _bool_on(s)  # info: set on
            r.append(rr_ui.state_toggle(  # info: r . append ( rr_ui . state_toggle (
                s.key, on,  # info: s . key , on ,
                on_change=lambda btn, active, s=s, row=l: self._toggle_bool(s, active, row, btn),  # info: set on_change
                tooltip="Writes 0 or 1 after you confirm. Nothing is restarted."))  # info: set tooltip
            return r  # info: return r
        if s.editable and s.secret:  # info: if s . editable and s . secret
            for text, mode in (("Replace…", "replace"), ("Clear", "clear")):  # info: for text , mode in ( ( "Replace…"
                b = Gtk.Button(label=text, valign=Gtk.Align.CENTER)  # info: set b
                b.add_css_class("flat")  # info: b . add_css_class ( "flat" )
                b.connect("clicked", lambda _b, m=mode: self.edit_setting(s, m, l))  # info: b . connect ( "clicked" , lambda _b
                r.append(b)  # info: r . append ( b )
        elif s.editable:  # info: elif s . editable :
            b = Gtk.Button(label="Edit…", valign=Gtk.Align.CENTER)  # info: set b
            b.add_css_class("flat")  # info: b . add_css_class ( "flat" )
            b.connect("clicked", lambda _b: self.edit_setting(s, "edit", l))  # info: b . connect ( "clicked" , lambda _b
            r.append(b)  # info: r . append ( b )
        return r  # info: return r

    def edit_setting(self, s, mode, row):  # info: def edit_setting
        if mode == "clear":  # info: if mode == "clear" :
            self._plan_confirm(s, "", row)  # info: self . _plan_confirm ( s , "" ,
            return  # info: return
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # info: set box
        if s.secret:  # info: if s . secret :
            e = Gtk.PasswordEntry(show_peek_icon=False, placeholder_text="new value (never shown, never logged)")  # info: set e
        else:  # info: else :
            e = Gtk.Entry(text=s.value_text())  # info: set e
        box.append(e)  # info: box . append ( e )
        hint = {"port": "integer 1–65535", "bool01": "0 or 1", "bool": "true / false", "int": "integer", "float": "number",  # info: set hint
                "url": "http(s)/rtsp/ws URL", "host": "hostname or IP"}.get(s.kind, "text")  # info: "url" : "http(s)/rtsp/ws URL" , "host" : "hostname or IP" }
        box.append(lbl(f"type: {hint} · {s.restart}", "dim-label", wrap=True))  # info: box . append ( lbl ( f" type:
        self.confirm(f"{'Replace secret' if s.secret else 'Edit'} {s.key}", f"{s.path}", "Next", lambda: self._plan_confirm(s, e.get_text(), row),  # info: self . confirm ( f" { 'Replace secret' if
                     extra=box)  # info: set extra

    def _toggle_bool(self, s, active, row, btn):  # info: def _toggle_bool
        def revert():  # info: def revert
            btn.rr_set(not active)  # info: btn . rr_set ( not active )
        self._plan_confirm(s, "1" if active else "0", row, on_cancel=revert, on_fail=revert)  # info: self . _plan_confirm ( s , "1" if

    def _plan_confirm(self, s, new, row, on_cancel=None, on_fail=None):  # info: def _plan_confirm
        try:  # info: try :
            plan = self.reg.plan(s, new)  # info: set plan
        except (ValueError, OSError) as ex:  # info: except ( ValueError , OSError ) as ex
            if on_fail:  # info: if on_fail :
                on_fail()  # info: call on_fail
            self.toast(f"Not saved: {ex}")  # info: self . toast ( f" Not saved: { ex
            return  # info: return
        if plan.diff == "(no change)":  # info: if plan . diff == "(no change)" :
            self.toast("No change")  # info: self . toast ( "No change" )
            return  # info: return
        view = Gtk.TextView(editable=False, monospace=True)  # info: set view
        view.get_buffer().set_text(plan.diff[:6000])  # info: view . get_buffer ( ) . set_text (
        sc = Gtk.ScrolledWindow(min_content_height=220, min_content_width=520)  # info: set sc
        sc.set_child(view)  # info: sc . set_child ( view )

        def ok():  # info: def ok
            try:  # info: try :
                import rr_config_io  # info: import rr_config_io
                res = rr_config_io.commit(plan)  # info: set res
                self.toast(f"Saved {plan.path.name} · backup {Path(res['backup']).name} · {plan.restart_note} (nothing restarted)")  # info: self . toast ( f" Saved { plan
                fresh = next((x for x in self.reg.page_settings(s.page) if x.file_id == s.file_id and x.key == s.key), None)  # info: set fresh
                if fresh is not None:  # info: if fresh is not None :
                    set_row_text(row, fresh.key, f"{fresh.display} · {fresh.kind} · saved — {plan.restart_note}")  # info: call set_row_text
            except Exception as ex:  # info: except Exception as ex :
                if on_fail:  # info: if on_fail :
                    on_fail()  # info: call on_fail
                self.toast(f"Save failed: {ex}")  # info: self . toast ( f" Save failed: { ex
        self.confirm(f"Save {plan.path.name}?", f"Masked diff below. {plan.restart_note}. Nothing will be restarted.", "Save", ok,  # info: self . confirm ( f" Save { plan
                     on_cancel=on_cancel, extra=sc)  # info: set on_cancel
