"""rr_aws_page.py — Root Monitor "AWS Fallback" page (added 2026-09-29 15:10 HST, Phase 1). Mixed into Panel.

INFO — MUST HAVE (future agents):
- Built on visit and RELEASED on leave (window); NO timer, NO background SSH. The only network action is the "Status" button
  (read-only) and — in "write" mode only — a confirmed toggle. Default mode is dry-run (settings.json
  "aws_fallback_mode"): the confirm dialog shows the exact change, then nothing is written.
- Button state = desired default from the catalog until a Status read returns the real AWS flags. Each row has a labelled
  toggle button ("AWS: On" / "AWS: Off", rr_ui.state_toggle; was a Gtk.Switch until 2026-09-29 16:10 HST).
- Locked rows (core/no-fit) have no button. Rows marked needs_signoff/decision_pending are labelled.
"""
from __future__ import annotations  # info: from __future__ import annotations

import time  # info: import time

from gi.repository import Gtk  # info: from gi . repository import Gtk

import rr_aws_fallback as awf  # info: import rr_aws_fallback as awf
from rr_ui import Adw, action_row, esc, lbl, section, spawn, state_toggle  # info: from rr_ui import Adw , action_row , esc


# ====================================================
# SECTION: class AwsFallbackPage
# What it does: AwsFallbackPage.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class AwsFallbackPage:  # info: class AwsFallbackPage
    def b_aws(self, box):  # info: def b_aws
        self.awf_cat = awf.load()  # info: self . awf_cat = awf . load (
        self.awf_mode = self.s.get("aws_fallback_mode", "dry-run")  # info: self . awf_mode = self . s .
        if self.awf_mode not in awf.MODES:  # info: if self . awf_mode not in awf .
            self.awf_mode = "dry-run"  # info: self . awf_mode = "dry-run"
        self.awf_alias = self.s.get("aws_fallback_alias", "rr-aws-ip") or "rr-aws-ip"  # info: self . awf_alias = self . s .
        self.awf_root = self.awf_cat.get("remote_root", "/home/ubuntu/rootrecord/fallback")  # info: self . awf_root = self . awf_cat .
        self.awf_state = awf.defaults(self.awf_cat)  # info: self . awf_state = awf . defaults (
        self.awf_remote = None  # info: self . awf_remote = None
        mode_txt = ("DRY-RUN — toggles show the change and write nothing" if self.awf_mode == "dry-run"  # info: set mode_txt
                    else "WRITE — toggles write the flag on AWS after confirm + backup")  # info: else "WRITE — toggles write the flag on AWS after confirm + backup" )
        box.append(lbl(f"<b>AWS Fallback</b> · {esc(self.awf_alias)} · {esc(self.awf_root)} · mode "  # info: box . append ( lbl ( f" <b>AWS Fallback</b> ·
                       f"<span foreground='{'#b58900' if self.awf_mode == 'dry-run' else '#dc322f'}'><b>{esc(mode_txt)}</b></span>",
                       markup=True, wrap=True))  # info: set markup
        box.append(lbl("The desk is canonical. AWS is a small fallback that keeps basic operations alive when the desk is offline. "  # info: box . append ( lbl ( "The desk is canonical. AWS is a small fallback that keeps basic operations alive when th
                       "Each function has one flag file on AWS. 'Status' reads them once over SSH (read-only). "  # info: "Each function has one flag file on AWS. 'Status' reads them once over SSH (read-only). "
                       "Plan: Library 08-ideas/2026-09-29-aws-fallback-rebuild.md.", "dim-label", wrap=True))  # info: "Plan: Library 08-ideas/2026-09-29-aws-fallback-rebuild.md." , "dim-label" , wrap = True )
        bar = Gtk.Box(spacing=8)  # info: set bar
        b = Gtk.Button(label="Status (read AWS flags, RAM, disk)")  # info: set b
        b.connect("clicked", lambda *_: self.awf_status())  # info: b . connect ( "clicked" , lambda *
        bar.append(b)  # info: bar . append ( b )
        self.awf_status_lbl = lbl("not read yet (no SSH until you press Status)", "dim-label", wrap=True)  # info: self . awf_status_lbl = lbl ( "not read yet (no SSH until you press Status)" ,
        bar.append(self.awf_status_lbl)  # info: bar . append ( self . awf_status_lbl )
        box.append(bar)  # info: box . append ( bar )
        self.awf_budget_lbl = lbl("", "rr-mono", wrap=True)  # info: self . awf_budget_lbl = lbl ( "" ,
        bud = self.awf_cat.get("budget", {})  # info: set bud
        o, i = section(f"Budget (catalog estimates; floors: RAM ≥ {bud.get('ram_floor_mb', 512)} MB free, "  # info: o , i = section ( f" Budget (catalog estimates; floors: RAM ≥
                       f"disk ≥ {bud.get('disk_floor_mb', 1536) / 1024:.1f} GB free) · profile {self.awf_cat.get('profile', '-')}")  # info: f" disk ≥ { bud . get ( 'disk_floor_mb'
        i.append(self.awf_budget_lbl)  # info: i . append ( self . awf_budget_lbl )
        box.append(o)  # info: box . append ( o )
        self.awf_rows, self.awf_switches = {}, {}  # info: self . awf_rows , self . awf_switches =
        groups = []  # info: set groups
        for f in self.awf_cat["functions"]:  # info: for f in self . awf_cat [ "functions"
            if f.get("group") not in groups:  # info: if f . get ( "group" ) not
                groups.append(f.get("group"))  # info: groups . append ( f . get (
        for g in groups:  # info: for g in groups :
            o, i = section(f"{g}")  # info: o , i = section ( f" {
            lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)  # info: set lb
            lb.add_css_class("boxed-list")  # info: lb . add_css_class ( "boxed-list" )
            i.append(lb)  # info: i . append ( lb )
            for f in (x for x in self.awf_cat["functions"] if x.get("group") == g):  # info: for f in ( x for x in
                tags = []  # info: set tags
                if f.get("locked"):  # info: if f . get ( "locked" ) :
                    tags.append("locked")  # info: tags . append ( "locked" )
                if f.get("fallback_only"):  # info: if f . get ( "fallback_only" ) :
                    tags.append("runs only while desk offline")  # info: tags . append ( "runs only while desk offline" )
                if f.get("needs_signoff"):  # info: if f . get ( "needs_signoff" ) :
                    tags.append("NEEDS SIGN-OFF")  # info: tags . append ( "NEEDS SIGN-OFF" )
                if f.get("decision_pending"):  # info: if f . get ( "decision_pending" ) :
                    tags.append("DECISION PENDING")  # info: tags . append ( "DECISION PENDING" )
                sub = (f"RAM ~{f.get('ram_mb', 0)} MB {f.get('ram_kind', '')} · disk ≤{f.get('disk_mb', 0)} MB · net {f.get('net', '')} · "  # info: set sub
                       f"fits: {f.get('fits', '?')} · default {'ON' if f.get('default_on') else 'OFF'}"  # info: f" fits: { f . get ( 'fits'
                       + (f" · {', '.join(tags)}" if tags else "") + f"\nAWS: not read · measured: {f.get('measured', '')}")  # info: call +
                r = action_row(f"{f['label']}  ({f['id']})", sub, 3)  # info: set r
                if Adw is not None and not f.get("locked"):  # info: if Adw is not None and not f
                    sw = state_toggle("AWS", bool(f.get("default_on")), lambda b, on, f=f: self.awf_on_toggle(b, on, f))  # info: set sw
                    r.add_suffix(sw)  # info: r . add_suffix ( sw )
                    self.awf_switches[f["id"]] = sw  # info: self . awf_switches [ f [ "id" ]
                lb.append(r)  # info: lb . append ( r )
                self.awf_rows[f["id"]] = (r, sub)  # info: self . awf_rows [ f [ "id" ]
            box.append(o)  # info: box . append ( o )
        self.awf_budget_refresh()  # info: self . awf_budget_refresh ( )
        self.report["aws"] = {"mode": self.awf_mode, "alias": self.awf_alias, "functions": len(self.awf_cat["functions"]),  # info: self . report [ "aws" ] = {
                              "default_on": sorted(k for k, v in self.awf_state.items() if v),  # info: "default_on" : sorted ( k for k ,
                              "budget_t3micro": self._awf_budget(908), "budget_2gb": self._awf_budget(2048)}  # info: "budget_t3micro" : self . _awf_budget ( 908 )

    def _awf_budget(self, total):  # info: def _awf_budget
        b = awf.budget(self.awf_cat, self.awf_state, total)  # info: set b
        return {k: b[k] for k in ("functions_ram_mb", "functions_disk_mb", "ram_free_est_mb", "ram_ok")}  # info: return { k : b [ k ]

    def awf_budget_refresh(self):  # info: def awf_budget_refresh
        lines = []  # info: set lines
        rem = self.awf_remote or {}  # info: set rem
        inst = self.awf_cat.get("budget", {}).get("instance_now", {})  # info: set inst
        totals = [(f"{inst.get('type', 't3.micro')} est.", int(inst.get("ram_mb", 908)))]  # info: set totals
        if rem.get("mem_total_mb"):  # info: if rem . get ( "mem_total_mb" ) :
            totals.insert(0, ("AWS measured", rem["mem_total_mb"]))  # info: totals . insert ( 0 , ( "AWS measured"
        for name, tot in totals:  # info: for name , tot in totals :
            b = awf.budget(self.awf_cat, self.awf_state, tot)  # info: set b
            lines.append(f"{name:<16} total {tot:>5} MB − OS ~{b['baseline_mb']} − enabled {b['functions_ram_mb']:>4} MB "  # info: lines . append ( f" { name :
                         f"= ~{b['ram_free_est_mb']:>5} MB free  {'OK' if b['ram_ok'] else 'BELOW ' + str(b['ram_floor_mb']) + ' MB FLOOR'}")  # info: f" = ~ { b [ 'ram_free_est_mb' ] :
        b = awf.budget(self.awf_cat, self.awf_state, 908)  # info: set b
        lines.append(f"disk caps of enabled functions: {b['functions_disk_mb']} MB (+ OS ~3.3 GB) on 6.7 GB root")  # info: lines . append ( f" disk caps of enabled functions: { b
        if rem:  # info: if rem :
            lines.append(f"AWS now: MemAvailable {rem.get('mem_avail_mb', '?')} MB · disk free {rem.get('disk_free_mb', '?')} MB · "  # info: lines . append ( f" AWS now: MemAvailable { rem
                         f"runtime {'deployed' if rem.get('deployed') else 'NOT deployed'} · release {rem.get('release', '-')} · mode {rem.get('mode', '-')}")  # info: f" runtime { 'deployed' if rem . get
        self.awf_budget_lbl.set_text("\n".join(lines))  # info: self . awf_budget_lbl . set_text ( "\n" .

    def awf_status(self):  # info: def awf_status
        self.awf_status_lbl.set_text("reading… (≤ 10 s)")  # info: self . awf_status_lbl . set_text ( "reading… (≤ 10 s)" )

        def done(out, rc):  # info: def done
            if rc != 0:  # info: if rc != 0 :
                self.awf_status_lbl.set_text(f"FAIL rc {rc} · {time.strftime('%H:%M:%S')} HST")  # info: self . awf_status_lbl . set_text ( f" FAIL rc
                return  # info: return
            st = awf.parse_status(out)  # info: set st
            self.awf_remote = st  # info: self . awf_remote = st
            for fid, (r, sub) in self.awf_rows.items():  # info: for fid , ( r , sub )
                if st.get("deployed"):  # info: if st . get ( "deployed" ) :
                    real = st["flags"].get(fid)  # info: set real
                    txt = "flag missing" if real is None else ("ON" if real else "OFF")  # info: set txt
                    if real is not None:  # info: if real is not None :
                        self.awf_state[fid] = real  # info: self . awf_state [ fid ] = real
                        sw = self.awf_switches.get(fid)  # info: set sw
                        if sw is not None:  # info: if sw is not None :
                            sw.rr_set(real)  # info: sw . rr_set ( real )
                else:  # info: else :
                    txt = "runtime not deployed"  # info: set txt
                if Adw is not None:  # info: if Adw is not None :
                    r.set_subtitle(sub.replace("AWS: not read", f"AWS: {txt}"))  # info: r . set_subtitle ( sub . replace (
            self.awf_status_lbl.set_text(f"read {time.strftime('%H:%M:%S')} HST · deployed={st.get('deployed', 0)}")  # info: self . awf_status_lbl . set_text ( f" read
            self.awf_budget_refresh()  # info: self . awf_budget_refresh ( )
        spawn(awf.status_argv(self.awf_alias, self.awf_root), done, capture=True)  # info: call spawn

    def awf_on_toggle(self, sw, new_state, f):  # info: def awf_on_toggle
        fid = f["id"]  # info: set fid
        old = self.awf_state.get(fid, False)  # info: set old
        if new_state == old:  # info: if new_state == old :
            return False  # info: return False
        trial = dict(self.awf_state)  # info: set trial
        trial[fid] = new_state  # info: trial [ fid ] = new_state
        b = awf.budget(self.awf_cat, trial, (self.awf_remote or {}).get("mem_total_mb") or 908)  # info: set b
        body = (f"{'Enable' if new_state else 'Disable'} {f['label']} ({fid}) on AWS.\n\n"  # info: set body
                f"Change: {awf.preview(self.awf_alias, fid, new_state, self.awf_root)}\n"  # info: f" Change: { awf . preview ( self
                f"Budget after: ~{b['ram_free_est_mb']} MB RAM free ({'OK' if b['ram_ok'] else 'BELOW FLOOR'}).\n"  # info: f" Budget after: ~ { b [ 'ram_free_est_mb' ] }
                + ("\nNEEDS SIGN-OFF.\n" if f.get("needs_signoff") else "")  # info: call +
                + ("\nDRY-RUN: nothing will be written." if self.awf_mode == "dry-run" else "\nThis writes the flag on AWS now."))  # info: call +

        def revert():  # info: def revert
            sw.rr_set(old)  # info: sw . rr_set ( old )

        def ok():  # info: def ok
            if self.awf_mode != "write":  # info: if self . awf_mode != "write" :
                revert()  # info: call revert
                self.toast(f"dry-run: {fid} → {'ON' if new_state else 'OFF'} not written")  # info: self . toast ( f" dry-run: { fid
                return  # info: return

            def done(out, rc):  # info: def done
                if rc == 0:  # info: if rc == 0 :
                    self.awf_state[fid] = new_state  # info: self . awf_state [ fid ] = new_state
                    sw.rr_set(new_state)  # info: sw . rr_set ( new_state )
                    self.toast(f"AWS {fid} → {'ON' if new_state else 'OFF'} (backup taken)")  # info: self . toast ( f" AWS { fid
                    self.awf_budget_refresh()  # info: self . awf_budget_refresh ( )
                else:  # info: else :
                    revert()  # info: call revert
                    self.toast(f"AWS write failed rc {rc}: {(out or '').strip()[:80]}")  # info: self . toast ( f" AWS write failed rc { rc
            spawn(awf.write_argv(self.awf_alias, fid, new_state, self.awf_root), done, capture=True)  # info: call spawn
        self.confirm("AWS Fallback — confirm", body, "Apply" if self.awf_mode == "write" else "Dry-run", ok, revert)  # info: self . confirm ( "AWS Fallback — confirm" , body ,
        return True  # dry-run / cancel / failed write -> revert() puts the button back

    def awf_maybe_release(self):  # info: def awf_maybe_release
        """Release the page's widgets when another page is shown (window only), so it costs RAM only while visible."""  # info: """Release the page's widgets when another page is shown (window only), so it costs RAM only while visible."""
        if self.check or self.win is None or "aws" not in self.built:  # info: if self . check or self . win
            return  # info: return
        if self.stack.get_visible_child_name() == "aws":  # info: if self . stack . get_visible_child_name ( )
            return  # info: return
        box = self.page_boxes["aws"]  # info: set box
        while (c := box.get_first_child()) is not None:  # info: while ( c := box . get_first_child (
            box.remove(c)  # info: box . remove ( c )
        self.built.discard("aws")  # info: self . built . discard ( "aws" )
        self.awf_rows, self.awf_switches = {}, {}  # info: self . awf_rows , self . awf_switches =
        from rr_pages import _trim  # info: from rr_pages import _trim
        _trim()  # info: call _trim
