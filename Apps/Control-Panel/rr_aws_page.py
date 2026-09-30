"""rr_aws_page.py — Root Monitor "AWS Fallback" page (added 2026-09-29 15:10 HST, Phase 1). Mixed into Panel.

INFO — MUST HAVE (future agents):
- Built on visit and RELEASED on leave (window); NO timer, NO background SSH. The only network action is the "Status" button
  (read-only) and — in "write" mode only — a confirmed toggle. Default mode is dry-run (settings.json
  "aws_fallback_mode"): the confirm dialog shows the exact change, then nothing is written.
- Switch state = desired default from the catalog until a Status read returns the real AWS flags.
- Locked rows (core/no-fit) have no switch. Rows marked needs_signoff/decision_pending are labelled.
"""
from __future__ import annotations

import time

from gi.repository import Gtk

import rr_aws_fallback as awf
from rr_ui import Adw, action_row, esc, lbl, section, spawn


class AwsFallbackPage:
    def b_aws(self, box):
        self.awf_cat = awf.load()
        self.awf_mode = self.s.get("aws_fallback_mode", "dry-run")
        if self.awf_mode not in awf.MODES:
            self.awf_mode = "dry-run"
        self.awf_alias = self.s.get("aws_fallback_alias", "rr-aws-ip") or "rr-aws-ip"
        self.awf_root = self.awf_cat.get("remote_root", "/home/ubuntu/rootrecord/fallback")
        self.awf_state = awf.defaults(self.awf_cat)
        self.awf_remote = None
        mode_txt = ("DRY-RUN — toggles show the change and write nothing" if self.awf_mode == "dry-run"
                    else "WRITE — toggles write the flag on AWS after confirm + backup")
        box.append(lbl(f"<b>AWS Fallback</b> · {esc(self.awf_alias)} · {esc(self.awf_root)} · mode "
                       f"<span foreground='{'#b58900' if self.awf_mode == 'dry-run' else '#dc322f'}'><b>{esc(mode_txt)}</b></span>",
                       markup=True, wrap=True))
        box.append(lbl("The desk is canonical. AWS is a small fallback that keeps basic operations alive when the desk is offline. "
                       "Each function has one flag file on AWS. 'Status' reads them once over SSH (read-only). "
                       "Plan: Library 08-ideas/2026-09-29-aws-fallback-rebuild.md.", "dim-label", wrap=True))
        bar = Gtk.Box(spacing=8)
        b = Gtk.Button(label="Status (read AWS flags, RAM, disk)")
        b.connect("clicked", lambda *_: self.awf_status())
        bar.append(b)
        self.awf_status_lbl = lbl("not read yet (no SSH until you press Status)", "dim-label", wrap=True)
        bar.append(self.awf_status_lbl)
        box.append(bar)
        self.awf_budget_lbl = lbl("", "rr-mono", wrap=True)
        o, i = section("Budget (estimates from the catalog; floors: RAM ≥ 512 MB free, disk ≥ 1.5 GB free)")
        i.append(self.awf_budget_lbl)
        box.append(o)
        self.awf_rows, self.awf_switches = {}, {}
        groups = []
        for f in self.awf_cat["functions"]:
            if f.get("group") not in groups:
                groups.append(f.get("group"))
        for g in groups:
            o, i = section(f"{g}")
            lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
            lb.add_css_class("boxed-list")
            i.append(lb)
            for f in (x for x in self.awf_cat["functions"] if x.get("group") == g):
                tags = []
                if f.get("locked"):
                    tags.append("locked")
                if f.get("fallback_only"):
                    tags.append("runs only while desk offline")
                if f.get("needs_signoff"):
                    tags.append("NEEDS SIGN-OFF")
                if f.get("decision_pending"):
                    tags.append("DECISION PENDING")
                sub = (f"RAM ~{f.get('ram_mb', 0)} MB {f.get('ram_kind', '')} · disk ≤{f.get('disk_mb', 0)} MB · net {f.get('net', '')} · "
                       f"fits: {f.get('fits', '?')} · default {'ON' if f.get('default_on') else 'OFF'}"
                       + (f" · {', '.join(tags)}" if tags else "") + f"\nAWS: not read · measured: {f.get('measured', '')}")
                r = action_row(f"{f['label']}  ({f['id']})", sub, 3)
                if Adw is not None and not f.get("locked"):
                    sw = Gtk.Switch(valign=Gtk.Align.CENTER, active=bool(f.get("default_on")))
                    sw.connect("state-set", self.awf_on_toggle, f)
                    r.add_suffix(sw)
                    self.awf_switches[f["id"]] = sw
                lb.append(r)
                self.awf_rows[f["id"]] = (r, sub)
            box.append(o)
        self.awf_budget_refresh()
        self.report["aws"] = {"mode": self.awf_mode, "alias": self.awf_alias, "functions": len(self.awf_cat["functions"]),
                              "default_on": sorted(k for k, v in self.awf_state.items() if v),
                              "budget_t3micro": self._awf_budget(908), "budget_2gb": self._awf_budget(2048)}

    def _awf_budget(self, total):
        b = awf.budget(self.awf_cat, self.awf_state, total)
        return {k: b[k] for k in ("functions_ram_mb", "functions_disk_mb", "ram_free_est_mb", "ram_ok")}

    def awf_budget_refresh(self):
        lines = []
        rem = self.awf_remote or {}
        totals = [("t3.micro now", 908), ("2 GB (planned)", 2048)]
        if rem.get("mem_total_mb"):
            totals.insert(0, ("AWS measured", rem["mem_total_mb"]))
        for name, tot in totals:
            b = awf.budget(self.awf_cat, self.awf_state, tot)
            lines.append(f"{name:<16} total {tot:>5} MB − OS ~{b['baseline_mb']} − enabled {b['functions_ram_mb']:>4} MB "
                         f"= ~{b['ram_free_est_mb']:>5} MB free  {'OK' if b['ram_ok'] else 'BELOW 512 MB FLOOR'}")
        b = awf.budget(self.awf_cat, self.awf_state, 908)
        lines.append(f"disk caps of enabled functions: {b['functions_disk_mb']} MB (+ OS ~3.3 GB) on 6.7 GB root")
        if rem:
            lines.append(f"AWS now: MemAvailable {rem.get('mem_avail_mb', '?')} MB · disk free {rem.get('disk_free_mb', '?')} MB · "
                         f"runtime {'deployed' if rem.get('deployed') else 'NOT deployed'} · mode {rem.get('mode', '-')}")
        self.awf_budget_lbl.set_text("\n".join(lines))

    def awf_status(self):
        self.awf_status_lbl.set_text("reading… (≤ 10 s)")

        def done(out, rc):
            if rc != 0:
                self.awf_status_lbl.set_text(f"FAIL rc {rc} · {time.strftime('%H:%M:%S')} HST")
                return
            st = awf.parse_status(out)
            self.awf_remote = st
            for fid, (r, sub) in self.awf_rows.items():
                if st.get("deployed"):
                    real = st["flags"].get(fid)
                    txt = "flag missing" if real is None else ("ON" if real else "OFF")
                    if real is not None:
                        self.awf_state[fid] = real
                        sw = self.awf_switches.get(fid)
                        if sw is not None:
                            sw.handler_block_by_func(self.awf_on_toggle)
                            sw.set_active(real)
                            sw.set_state(real)
                            sw.handler_unblock_by_func(self.awf_on_toggle)
                else:
                    txt = "runtime not deployed"
                if Adw is not None:
                    r.set_subtitle(sub.replace("AWS: not read", f"AWS: {txt}"))
            self.awf_status_lbl.set_text(f"read {time.strftime('%H:%M:%S')} HST · deployed={st.get('deployed', 0)}")
            self.awf_budget_refresh()
        spawn(awf.status_argv(self.awf_alias, self.awf_root), done, capture=True)

    def awf_on_toggle(self, sw, new_state, f):
        fid = f["id"]
        old = self.awf_state.get(fid, False)
        if new_state == old:
            return False
        trial = dict(self.awf_state)
        trial[fid] = new_state
        b = awf.budget(self.awf_cat, trial, (self.awf_remote or {}).get("mem_total_mb") or 908)
        body = (f"{'Enable' if new_state else 'Disable'} {f['label']} ({fid}) on AWS.\n\n"
                f"Change: {awf.preview(self.awf_alias, fid, new_state, self.awf_root)}\n"
                f"Budget after: ~{b['ram_free_est_mb']} MB RAM free ({'OK' if b['ram_ok'] else 'BELOW FLOOR'}).\n"
                + ("\nNEEDS SIGN-OFF.\n" if f.get("needs_signoff") else "")
                + ("\nDRY-RUN: nothing will be written." if self.awf_mode == "dry-run" else "\nThis writes the flag on AWS now."))

        def revert():
            sw.handler_block_by_func(self.awf_on_toggle)
            sw.set_active(old)
            sw.set_state(old)
            sw.handler_unblock_by_func(self.awf_on_toggle)

        def ok():
            if self.awf_mode != "write":
                revert()
                self.toast(f"dry-run: {fid} → {'ON' if new_state else 'OFF'} not written")
                return

            def done(out, rc):
                if rc == 0:
                    self.awf_state[fid] = new_state
                    sw.set_state(new_state)
                    self.toast(f"AWS {fid} → {'ON' if new_state else 'OFF'} (backup taken)")
                    self.awf_budget_refresh()
                else:
                    revert()
                    self.toast(f"AWS write failed rc {rc}: {(out or '').strip()[:80]}")
            spawn(awf.write_argv(self.awf_alias, fid, new_state, self.awf_root), done, capture=True)
        self.confirm("AWS Fallback — confirm", body, "Apply" if self.awf_mode == "write" else "Dry-run", ok, revert)
        return True  # keep the switch where it was until confirmed

    def awf_maybe_release(self):
        """Release the page's widgets when another page is shown (window only), so it costs RAM only while visible."""
        if self.check or self.win is None or "aws" not in self.built:
            return
        if self.stack.get_visible_child_name() == "aws":
            return
        box = self.page_boxes["aws"]
        while (c := box.get_first_child()) is not None:
            box.remove(c)
        self.built.discard("aws")
        self.awf_rows, self.awf_switches = {}, {}
        from rr_pages import _trim
        _trim()
