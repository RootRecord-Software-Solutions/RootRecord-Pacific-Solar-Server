# ==============================================================================
# FILE: Apps/Control-Panel/rr_automations_page.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Root Monitor Automations page. Mixed into Panel.

Toggles write automation-overrides.json. New power schedules write
power-automations.json. Neither button restarts the poller or runs a radio
command itself. The poller reads both files.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

from gi.repository import Gtk  # info: from gi . repository import Gtk

from rr_ui import lbl, section, state_toggle  # info: from rr_ui import lbl , section , state_toggle

JOB_WARN = {  # info: set JOB_WARN
    "self_terminal": "Next poller start skips its own process record.",  # info: "self_terminal"
    "cloudflare_tunnel": "Next poller start skips the Cloudflare tunnel.",  # info: "cloudflare_tunnel"
    "heartbeat": "The ENERGY status line stops after the poller reloads this flag.",  # info: "heartbeat"
    "ecoflow_read_cycle": "EcoFlow battery reads stop after the poller reloads this flag.",  # info: "ecoflow_read_cycle"
    "service_supervisor": "Service checks stop after the poller reloads this flag.",  # info: "service_supervisor"
}  # info: }


# ====================================================
# SECTION: function _load_module
# What it does: Load one Python file by path. Does not run its main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_module(name: str, path: Path):  # info: def _load_module
    spec = importlib.util.spec_from_file_location(name, path)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader is None
        raise ImportError(str(path))  # info: raise ImportError
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    return mod  # info: return mod


# ====================================================
# SECTION: function _dropdown
# What it does: A GTK drop-down whose selected index maps to ids. Does not write a file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _dropdown(labels: list[str]) -> Gtk.DropDown:  # info: def _dropdown
    return Gtk.DropDown.new_from_strings(labels)  # info: return Gtk . DropDown . new_from_strings ( labels )


# ====================================================
# SECTION: function _selected
# What it does: The selected index, or 0 when nothing is selected.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _selected(widget: Gtk.DropDown) -> int:  # info: def _selected
    idx = widget.get_selected()  # info: set idx
    if idx is None or int(idx) > 100000:  # info: if idx is None or int ( idx ) > 100000
        return 0  # info: return 0
    return int(idx)  # info: return int ( idx )


# ====================================================
# SECTION: function _spin
# What it does: Integer spin button. Does not write a file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _spin(value: int, upper: int) -> Gtk.SpinButton:  # info: def _spin
    adj = Gtk.Adjustment(value=value, lower=0, upper=upper, step_increment=1, page_increment=1, page_size=0)  # info: set adj
    spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0, numeric=True)  # info: set spin
    spin.set_width_chars(3)  # info: spin . set_width_chars ( 3 )
    return spin  # info: return spin


# ====================================================
# SECTION: class AutomationsPage
# What it does: Automations page mixin. Builds on first visit. Writes only after confirm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class AutomationsPage:  # info: class AutomationsPage
    def _automation_libs(self):  # info: def _automation_libs
        if getattr(self, "_actl", None) is not None and getattr(self, "_jobmod", None) is not None:  # info: if getattr ( self , "_actl" , None ) is not None and
            return self._actl, self._jobmod  # info: return self . _actl , self . _jobmod
        scripts = Path(self.paths.pacific) / "Automations" / "scripts"  # info: set scripts
        self._actl = _load_module("automation_control", scripts / "automation_control.py")  # info: self . _actl = _load_module
        self._jobmod = _load_module("rr_poller_jobs", scripts / "jobs.py")  # info: self . _jobmod = _load_module
        return self._actl, self._jobmod  # info: return self . _actl , self . _jobmod

    def b_automations(self, box):  # info: def b_automations
        try:  # info: try
            actl, jobmod = self._automation_libs()  # info: actl , jobmod = self . _automation_libs ( )
            rows = actl.job_rows(jobmod)  # info: set rows
        except Exception as exc:  # info: except Exception as exc
            self.errors.append(f"automations: {exc}")  # info: self . errors . append
            box.append(lbl(f"Automations page failed to load: {exc}", "rr-fail", wrap=True))  # info: box . append
            self.report["automations"] = {"error": str(exc)}  # info: self . report [ "automations" ] = { "error" : str ( exc ) }
            return  # info: return
        self.auto_rows = {r["id"]: r for r in rows}  # info: self . auto_rows = { r [ "id" ] : r for r in rows }
        self.auto_job_btns = {}  # info: self . auto_job_btns = { }
        self.auto_job_widgets = {}  # info: self . auto_job_widgets = { }
        self.auto_expanders = {}  # info: self . auto_expanders = { }
        self.auto_power_widgets = {}  # info: self . auto_power_widgets = { }
        self.auto_note = lbl("", wrap=True)  # info: self . auto_note = lbl ( "" , wrap = True )
        box.append(self.auto_note)  # info: box . append ( self . auto_note )
        self._build_power(box, actl)  # info: self . _build_power ( box , actl )
        search = Gtk.SearchEntry(placeholder_text="Filter jobs by name")  # info: set search
        search.connect("search-changed", self._filter_jobs)  # info: search . connect ( "search-changed" , self . _filter_jobs )
        box.append(search)  # info: box . append ( search )
        self._build_jobs(box, rows)  # info: self . _build_jobs ( box , rows )
        self.report["automations"] = {"jobs": len(rows), "power": len(actl.load_power().get("items") or [])}  # info: self . report [ "automations" ] = {
        self._refresh_automations_view()  # info: self . _refresh_automations_view ( )

    def _build_power(self, box, actl):  # info: def _build_power
        o, inner = section("Power schedules")  # info: o , inner = section ( "Power schedules" )
        inner.append(lbl(  # info: inner . append ( lbl
            "Run an EcoFlow function at a clock time. Example: Delta 2 AC off at 22:00 and AC on at 06:00. Times are HST.",  # info: "Run an EcoFlow function at a clock time. Example: Delta 2 AC off at 22:00 and AC on at 06:00. Times are HST." ,
            "dim-label", wrap=True))  # info: "dim-label" , wrap = True ) )
        doc = actl.load_power()  # info: set doc
        self.auto_master = state_toggle("Power schedules", bool(doc.get("master_enabled", True)), self._master_toggled, big=True)  # info: self . auto_master = state_toggle
        inner.append(self.auto_master)  # info: inner . append ( self . auto_master )
        new = Gtk.Button(label="New power schedule", halign=Gtk.Align.START)  # info: set new
        new.connect("clicked", lambda *_: self._open_power_form())  # info: new . connect ( "clicked" , lambda * _ : self . _open_power_form ( ) )
        inner.append(new)  # info: inner . append ( new )
        self.auto_power_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # info: self . auto_power_box = Gtk . Box
        inner.append(self.auto_power_box)  # info: inner . append ( self . auto_power_box )
        box.append(o)  # info: box . append ( o )
        self._rebuild_power_rows()  # info: self . _rebuild_power_rows ( )

    def _build_jobs(self, box, rows):  # info: def _build_jobs
        grouped: dict[str, list] = {}  # info: set grouped
        order = []  # info: set order
        for row in rows:  # info: for row in rows
            if row["section"] not in grouped:  # info: if row [ "section" ] not in grouped
                order.append(row["section"])  # info: order . append ( row [ "section" ] )
                grouped[row["section"]] = []  # info: grouped [ row [ "section" ] ] = [ ]
            grouped[row["section"]].append(row)  # info: grouped [ row [ "section" ] ] . append ( row )
        for section_id in order:  # info: for section_id in order
            items = grouped[section_id]  # info: set items
            exp = Gtk.Expander(label=items[0]["section_title"])  # info: set exp
            inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)  # info: set inner
            for job in items:  # info: for job in items
                line = Gtk.Box(spacing=8)  # info: set line
                text = lbl("", wrap=True)  # info: set text
                text.set_hexpand(True)  # info: text . set_hexpand ( True )
                btn = state_toggle("Job", job["enabled"], lambda b, on, jid=job["id"]: self._job_toggled(b, on, jid))  # info: set btn
                line.append(text)  # info: line . append ( text )
                line.append(btn)  # info: line . append ( btn )
                inner.append(line)  # info: inner . append ( line )
                self.auto_job_btns[job["id"]] = btn  # info: self . auto_job_btns [ job [ "id" ] ] = btn
                self.auto_job_widgets[job["id"]] = {"line": line, "text": text}  # info: self . auto_job_widgets [ job [ "id" ] ] = { "line" : line , "text" : text }
            exp.set_child(inner)  # info: exp . set_child ( inner )
            self.auto_expanders[section_id] = exp  # info: self . auto_expanders [ section_id ] = exp
            box.append(exp)  # info: box . append ( exp )

    def r_automations(self):  # info: def r_automations
        if "automations" not in self.built or not hasattr(self, "auto_note"):  # info: if "automations" not in self . built or not hasattr
            return  # info: return
        self._refresh_automations_view()  # info: self . _refresh_automations_view ( )

    def _refresh_automations_view(self):  # info: def _refresh_automations_view
        actl = self._actl  # info: set actl
        state = actl.poller_control_state()  # info: set state
        if state == "live":  # info: if state == "live"
            note = "The running poller reads these toggles each cycle and runs a due power schedule in that minute."  # info: set note
        elif state == "restart":  # info: elif state == "restart"
            note = "Saved here. This poller process started before that reader. Restart the poller when you want toggles and schedules to take effect."  # info: set note
        else:  # info: else
            note = "Saved here. The poller is not running, so nothing fires until it starts."  # info: set note
        self.auto_note.set_text(note)  # info: self . auto_note . set_text ( note )
        doc = actl.load_power()  # info: set doc
        if not getattr(self.auto_master, "_rr_pending", False) and self.auto_master.get_active() != bool(doc.get("master_enabled", True)):  # info: if not getattr ( self . auto_master , "_rr_pending" , False ) and
            self.auto_master.rr_set(bool(doc.get("master_enabled", True)))  # info: self . auto_master . rr_set
        self._sync_power_rows(doc)  # info: self . _sync_power_rows ( doc )
        overrides = actl.load_overrides()  # info: set overrides
        counts: dict[str, list] = {}  # info: set counts
        for jid, meta in self.auto_rows.items():  # info: for jid , meta in self . auto_rows . items ( )
            job = {"id": jid, "enabled": meta["code_on"]}  # info: set job
            eff = actl.job_enabled(job, overrides)  # info: set eff
            btn = self.auto_job_btns[jid]  # info: set btn
            if not getattr(btn, "_rr_pending", False) and btn.get_active() != eff:  # info: if not getattr ( btn , "_rr_pending" , False ) and
                btn.rr_set(eff)  # info: btn . rr_set ( eff )
            flag = "override" if isinstance(overrides.get("jobs"), dict) and jid in overrides["jobs"] else "code default"  # info: set flag
            code = "On" if meta["code_on"] else "Off"  # info: set code
            self.auto_job_widgets[jid]["text"].set_markup(  # info: self . auto_job_widgets [ jid ] [ "text" ] . set_markup
                f"<b>{_esc(jid)}</b>  <span alpha='70%'>{_esc(meta['schedule'])} · {flag} {code}</span>\n"  # info: f" <b> { _esc ( jid ) } </b>
                f"<span alpha='75%'>{_esc(meta['description'])}</span>")  # info: f" <span alpha='75%'> { _esc ( meta [ 'description' ] ) } </span> " )
            counts.setdefault(meta["section"], [meta["section_title"], 0, 0])  # info: counts . setdefault
            counts[meta["section"]][1 if eff else 2] += 1  # info: counts [ meta [ "section" ] ] [ 1 if eff else 2 ] += 1
        for section_id, exp in self.auto_expanders.items():  # info: for section_id , exp in self . auto_expanders . items ( )
            title, on_n, off_n = counts.get(section_id, ("", 0, 0))  # info: title , on_n , off_n = counts . get
            exp.set_label(f"{title} · {on_n} on · {off_n} off")  # info: exp . set_label
        self.report["automations"] = {  # info: self . report [ "automations" ] = {
            "jobs": len(self.auto_rows),  # info: "jobs"
            "power": len(doc.get("items") or []),  # info: "power"
            "master": bool(doc.get("master_enabled", True)),  # info: "master"
            "poller": state,  # info: "poller"
        }  # info: }

    def _filter_jobs(self, entry):  # info: def _filter_jobs
        query = entry.get_text().strip().lower()  # info: set query
        hit = {sid: False for sid in self.auto_expanders}  # info: set hit
        for jid, widgets in self.auto_job_widgets.items():  # info: for jid , widgets in self . auto_job_widgets . items ( )
            meta = self.auto_rows[jid]  # info: set meta
            show = not query or query in jid.lower() or query in meta["description"].lower() or query in meta["section_title"].lower()  # info: set show
            widgets["line"].set_visible(show)  # info: widgets [ "line" ] . set_visible ( show )
            if show and query:  # info: if show and query
                hit[meta["section"]] = True  # info: hit [ meta [ "section" ] ] = True
        if query:  # info: if query
            for sid, exp in self.auto_expanders.items():  # info: for sid , exp in self . auto_expanders . items ( )
                exp.set_expanded(hit[sid])  # info: exp . set_expanded ( hit [ sid ] )

    def _sync_power_rows(self, doc):  # info: def _sync_power_rows
        ids = [it.get("id") for it in doc.get("items") or [] if isinstance(it, dict)]  # info: set ids
        if ids != list(self.auto_power_widgets):  # info: if ids != list ( self . auto_power_widgets )
            self._rebuild_power_rows()  # info: self . _rebuild_power_rows ( )
            return  # info: return
        now = datetime.now(self._actl.HST)  # info: set now
        by_id = {it.get("id"): it for it in doc.get("items") or [] if isinstance(it, dict)}  # info: set by_id
        for item_id, widgets in self.auto_power_widgets.items():  # info: for item_id , widgets in self . auto_power_widgets . items ( )
            item = by_id.get(item_id)  # info: set item
            if not item:  # info: if not item
                continue  # info: continue
            widgets["text"].set_markup(f"<b>{_esc(item.get('name') or item_id)}</b>\n<span alpha='75%'>{_esc(self._actl.describe_item(item, now))}</span>")  # info: widgets [ "text" ] . set_markup
            btn = widgets["btn"]  # info: set btn
            if not getattr(btn, "_rr_pending", False) and btn.get_active() != bool(item.get("enabled")):  # info: if not getattr ( btn , "_rr_pending" , False ) and
                btn.rr_set(bool(item.get("enabled")))  # info: btn . rr_set

    def _rebuild_power_rows(self):  # info: def _rebuild_power_rows
        while (child := self.auto_power_box.get_first_child()) is not None:  # info: while ( child := self . auto_power_box . get_first_child ( ) ) is not None
            self.auto_power_box.remove(child)  # info: self . auto_power_box . remove ( child )
        self.auto_power_widgets = {}  # info: self . auto_power_widgets = { }
        doc = self._actl.load_power()  # info: set doc
        items = [it for it in doc.get("items") or [] if isinstance(it, dict)]  # info: set items
        if not items:  # info: if not items
            self.auto_power_box.append(lbl("No power schedules yet.", "dim-label"))  # info: self . auto_power_box . append
            return  # info: return
        now = datetime.now(self._actl.HST)  # info: set now
        for item in items:  # info: for item in items
            line = Gtk.Box(spacing=8)  # info: set line
            text = lbl("", wrap=True)  # info: set text
            text.set_hexpand(True)  # info: text . set_hexpand ( True )
            text.set_markup(f"<b>{_esc(item.get('name') or item.get('id'))}</b>\n<span alpha='75%'>{_esc(self._actl.describe_item(item, now))}</span>")  # info: text . set_markup
            btn = state_toggle("Schedule", bool(item.get("enabled")), lambda b, on, iid=item["id"]: self._item_toggled(b, on, iid))  # info: set btn
            delete = Gtk.Button(label="Delete", valign=Gtk.Align.CENTER)  # info: set delete
            delete.connect("clicked", lambda _b, iid=item["id"]: self._delete_item(iid))  # info: delete . connect
            line.append(text)  # info: line . append ( text )
            line.append(btn)  # info: line . append ( btn )
            line.append(delete)  # info: line . append ( delete )
            self.auto_power_box.append(line)  # info: self . auto_power_box . append ( line )
            self.auto_power_widgets[item["id"]] = {"text": text, "btn": btn}  # info: self . auto_power_widgets [ item [ "id" ] ] = { "text" : text , "btn" : btn }

    def _guard_window(self, btn, active: bool) -> bool:  # info: def _guard_window
        if self.win is None:  # info: if self . win is None
            btn.rr_set(not active)  # info: btn . rr_set ( not active )
            return False  # info: return False
        return True  # info: return True

    def _job_toggled(self, btn, active, jid):  # info: def _job_toggled
        if not self._guard_window(btn, active):  # info: if not self . _guard_window ( btn , active )
            return  # info: return
        meta = self.auto_rows[jid]  # info: set meta
        btn._rr_pending = True  # info: btn . _rr_pending = True
        extra = JOB_WARN.get(jid, "")  # info: set extra
        body = f"{jid}\n{meta['description']}\n{meta['schedule']}"  # info: set body
        if extra:  # info: if extra
            body += f"\n\n{extra}"  # info: set body
        body += "\n\nThis writes the override file. It does not restart the poller."  # info: set body

        def yes():  # info: def yes
            btn._rr_pending = False  # info: btn . _rr_pending = False
            try:  # info: try
                self._actl.set_job_override(jid, active, meta["code_on"])  # info: self . _actl . set_job_override
            except Exception as exc:  # info: except Exception as exc
                btn.rr_set(not active)  # info: btn . rr_set ( not active )
                self.toast(f"Save failed: {exc}")  # info: self . toast
                return  # info: return
            self.toast(f"{jid} {'on' if active else 'off'}")  # info: self . toast
            self._refresh_automations_view()  # info: self . _refresh_automations_view ( )

        def no():  # info: def no
            btn._rr_pending = False  # info: btn . _rr_pending = False
            btn.rr_set(not active)  # info: btn . rr_set ( not active )

        self.confirm(f"Turn {jid} {'on' if active else 'off'}?", body, "Turn on" if active else "Turn off", yes, no)  # info: self . confirm

    def _master_toggled(self, btn, active):  # info: def _master_toggled
        if not self._guard_window(btn, active):  # info: if not self . _guard_window ( btn , active )
            return  # info: return
        btn._rr_pending = True  # info: btn . _rr_pending = True

        def yes():  # info: def yes
            btn._rr_pending = False  # info: btn . _rr_pending = False
            self._actl.set_master(active)  # info: self . _actl . set_master ( active )
            self.toast("Power schedules on" if active else "Power schedules paused")  # info: self . toast

        def no():  # info: def no
            btn._rr_pending = False  # info: btn . _rr_pending = False
            btn.rr_set(not active)  # info: btn . rr_set ( not active )

        self.confirm(  # info: self . confirm
            "Power schedules",  # info: "Power schedules" ,
            "Armed rows run when their clock time arrives. Pausing stops every power schedule until you turn this back on.",  # info: "Armed rows run when their clock time arrives. Pausing stops every power schedule until you turn this back on." ,
            "Turn on" if active else "Turn off", yes, no)  # info: "Turn on" if active else "Turn off" , yes , no )

    def _item_toggled(self, btn, active, item_id):  # info: def _item_toggled
        if not self._guard_window(btn, active):  # info: if not self . _guard_window ( btn , active )
            return  # info: return
        btn._rr_pending = True  # info: btn . _rr_pending = True

        def yes():  # info: def yes
            btn._rr_pending = False  # info: btn . _rr_pending = False
            self._actl.set_item_enabled(item_id, active)  # info: self . _actl . set_item_enabled
            self._refresh_automations_view()  # info: self . _refresh_automations_view ( )

        def no():  # info: def no
            btn._rr_pending = False  # info: btn . _rr_pending = False
            btn.rr_set(not active)  # info: btn . rr_set ( not active )

        self.confirm("Power schedule", item_id, "Turn on" if active else "Turn off", yes, no)  # info: self . confirm

    def _delete_item(self, item_id):  # info: def _delete_item
        if self.win is None:  # info: if self . win is None
            return  # info: return
        doc = self._actl.load_power()  # info: set doc
        item = next((it for it in doc.get("items") or [] if isinstance(it, dict) and it.get("id") == item_id), None)  # info: set item
        name = item.get("name") if item else item_id  # info: set name

        def yes():  # info: def yes
            self._actl.delete_item(item_id)  # info: self . _actl . delete_item ( item_id )
            self._rebuild_power_rows()  # info: self . _rebuild_power_rows ( )
            self.toast("Power schedule deleted")  # info: self . toast ( "Power schedule deleted" )

        self.confirm("Delete power schedule?", str(name), "Delete", yes)  # info: self . confirm

    def _open_power_form(self):  # info: def _open_power_form
        if self.win is None:  # info: if self . win is None
            return  # info: return
        actl = self._actl  # info: set actl
        form = Gtk.Window(title="New power schedule", modal=True, transient_for=self.win)  # info: set form
        form.set_default_size(520, 460)  # info: form . set_default_size ( 520 , 460 )
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)  # info: set root
        name = Gtk.Entry(placeholder_text="Name, optional")  # info: set name
        root.append(name)  # info: root . append ( name )
        devices = [label for _key, label in actl.DEVICES]  # info: set devices
        device_ids = [key for key, _label in actl.DEVICES]  # info: set device_ids
        device = _dropdown(devices)  # info: set device
        root.append(_labeled("Device", device))  # info: root . append ( _labeled ( "Device" , device ) )
        first_ids = [row[1] for row in actl.functions_for(device_ids[0])]  # info: set first_ids
        function = _dropdown([row[2] for row in actl.functions_for(device_ids[0])])  # info: set function
        root.append(_labeled("Function", function))  # info: root . append ( _labeled ( "Function" , function ) )
        hour, minute = _spin(22, 23), _spin(0, 59)  # info: hour , minute = _spin ( 22 , 23 ) , _spin ( 0 , 59 )
        root.append(_clock_row("At", hour, minute))  # info: root . append ( _clock_row ( "At" , hour , minute ) )
        repeat = _dropdown(["Every day", "Once"])  # info: set repeat
        root.append(_labeled("Repeat", repeat))  # info: root . append ( _labeled ( "Repeat" , repeat ) )
        tomorrow = (datetime.now(actl.HST) + timedelta(days=1)).date().isoformat()  # info: set tomorrow
        date = Gtk.Entry(text=tomorrow, placeholder_text="YYYY-MM-DD")  # info: set date
        date_row = _labeled("Date", date)  # info: set date_row
        date_row.set_visible(False)  # info: date_row . set_visible ( False )
        root.append(date_row)  # info: root . append ( date_row )
        second_on = Gtk.CheckButton(label="Also schedule a second step (for example turn it back on)")  # info: set second_on
        second_on.set_active(True)  # info: second_on . set_active ( True )
        root.append(second_on)  # info: root . append ( second_on )
        second_ids = list(first_ids)  # info: set second_ids
        second_fn = _dropdown([row[2] for row in actl.functions_for(device_ids[0])])  # info: set second_fn
        second_hour, second_minute = _spin(6, 23), _spin(0, 59)  # info: second_hour , second_minute = _spin ( 6 , 23 ) , _spin ( 0 , 59 )
        second_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)  # info: set second_box
        second_box.append(_labeled("Second function", second_fn))  # info: second_box . append
        second_box.append(_clock_row("At", second_hour, second_minute))  # info: second_box . append
        root.append(second_box)  # info: root . append ( second_box )
        hold = {"fn": first_ids, "second": second_ids, "touched": False, "block": False}  # info: set hold

        def refill(*_a):  # info: def refill
            hold["block"] = True  # info: hold [ "block" ] = True
            hold["touched"] = False  # info: hold [ "touched" ] = False
            dev = device_ids[_selected(device)]  # info: set dev
            rows = actl.functions_for(dev)  # info: set rows
            hold["fn"] = [row[1] for row in rows]  # info: hold [ "fn" ] = [ row [ 1 ] for row in rows ]
            hold["second"] = list(hold["fn"])  # info: hold [ "second" ] = list ( hold [ "fn" ] )
            function.set_model(Gtk.StringList.new([row[2] for row in rows]))  # info: function . set_model
            second_fn.set_model(Gtk.StringList.new([row[2] for row in rows]))  # info: second_fn . set_model
            function.set_selected(0)  # info: function . set_selected ( 0 )
            hold["block"] = False  # info: hold [ "block" ] = False
            _pick_opposite()  # info: call _pick_opposite

        def _pick_opposite():  # info: def _pick_opposite
            if hold["touched"] or not hold["fn"]:  # info: if hold [ "touched" ] or not hold [ "fn" ]
                return  # info: return
            dev = device_ids[_selected(device)]  # info: set dev
            current = hold["fn"][_selected(function)]  # info: set current
            other = actl.opposite_function(dev, current)  # info: set other
            if other not in hold["second"]:  # info: if other not in hold [ "second" ]
                return  # info: return
            hold["block"] = True  # info: hold [ "block" ] = True
            second_fn.set_selected(hold["second"].index(other))  # info: second_fn . set_selected
            hold["block"] = False  # info: hold [ "block" ] = False

        def on_repeat(*_a):  # info: def on_repeat
            date_row.set_visible(_selected(repeat) == 1)  # info: date_row . set_visible

        def on_second_fn(*_a):  # info: def on_second_fn
            if not hold["block"]:  # info: if not hold [ "block" ]
                hold["touched"] = True  # info: hold [ "touched" ] = True

        device.connect("notify::selected", refill)  # info: device . connect ( "notify::selected" , refill )
        function.connect("notify::selected", lambda *_a: _pick_opposite())  # info: function . connect
        second_fn.connect("notify::selected", on_second_fn)  # info: second_fn . connect ( "notify::selected" , on_second_fn )
        repeat.connect("notify::selected", on_repeat)  # info: repeat . connect ( "notify::selected" , on_repeat )
        second_on.connect("toggled", lambda b: second_box.set_visible(b.get_active()))  # info: second_on . connect
        _pick_opposite()  # info: call _pick_opposite
        hold["touched"] = False  # info: hold [ "touched" ] = False
        buttons = Gtk.Box(spacing=8, halign=Gtk.Align.END)  # info: set buttons
        cancel = Gtk.Button(label="Cancel")  # info: set cancel
        cancel.connect("clicked", lambda *_: form.close())  # info: cancel . connect ( "clicked" , lambda * _ : form . close ( ) )
        save = Gtk.Button(label="Schedule")  # info: set save
        save.add_css_class("suggested-action")  # info: save . add_css_class ( "suggested-action" )
        save.connect("clicked", lambda *_: self._submit_power(form, name, device_ids, device, hold, function, hour, minute, repeat, date, second_on, second_fn, second_hour, second_minute))  # info: save . connect
        buttons.append(cancel)  # info: buttons . append ( cancel )
        buttons.append(save)  # info: buttons . append ( save )
        root.append(buttons)  # info: root . append ( buttons )
        form.set_child(root)  # info: form . set_child ( root )
        form.present()  # info: form . present ( )

    def _submit_power(self, form, name, device_ids, device, hold, function, hour, minute, repeat, date, second_on, second_fn, second_hour, second_minute):  # info: def _submit_power
        actl = self._actl  # info: set actl
        dev = device_ids[_selected(device)]  # info: set dev
        kind = "once" if _selected(repeat) == 1 else "daily"  # info: set kind
        specs = [{  # info: set specs
            "name": name.get_text(),  # info: "name"
            "device": dev,  # info: "device"
            "function": hold["fn"][_selected(function)],  # info: "function"
            "hour": int(hour.get_value()),  # info: "hour"
            "minute": int(minute.get_value()),  # info: "minute"
            "repeat": kind,  # info: "repeat"
            "date": date.get_text().strip(),  # info: "date"
        }]  # info: } ]
        if second_on.get_active():  # info: if second_on . get_active ( )
            base = name.get_text().strip()  # info: set base
            second_date = date.get_text().strip()  # info: set second_date
            if kind == "once" and (int(second_hour.get_value()), int(second_minute.get_value())) <= (int(hour.get_value()), int(minute.get_value())):  # info: if kind == "once" and
                try:  # info: try
                    second_date = (datetime.strptime(second_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()  # info: set second_date
                except ValueError:  # info: except ValueError
                    second_date = date.get_text().strip()  # info: set second_date
            specs.append({  # info: specs . append
                "name": (base + " (return)")[:80] if base else "",  # info: "name"
                "device": dev,  # info: "device"
                "function": hold["second"][_selected(second_fn)],  # info: "function"
                "hour": int(second_hour.get_value()),  # info: "hour"
                "minute": int(second_minute.get_value()),  # info: "minute"
                "repeat": kind,  # info: "repeat"
                "date": second_date,  # info: "date"
            })  # info: } )
        for spec in specs:  # info: for spec in specs
            err = actl.validate_spec(spec)  # info: set err
            if err:  # info: if err
                self.toast(err)  # info: self . toast ( err )
                return  # info: return
        lines = []  # info: set lines
        for spec in specs:  # info: for spec in specs
            lines.append(  # info: lines . append
                f"{actl.device_label(spec['device'])} {actl.function_label(spec['device'], spec['function'])} "  # info: f" { actl . device_label ( spec [ 'device' ] ) }
                f"at {spec['hour']:02d}:{spec['minute']:02d} HST ({'every day' if kind == 'daily' else spec['date']})")  # info: f" at { spec [ 'hour' ] : 02d } :
        body = "The poller will run these. They switch the EcoFlow over BLE.\n\n" + "\n".join(lines)  # info: set body

        def yes():  # info: def yes
            try:  # info: try
                actl.add_items(specs)  # info: actl . add_items ( specs )
            except Exception as exc:  # info: except Exception as exc
                self.toast(str(exc))  # info: self . toast ( str ( exc ) )
                return  # info: return
            form.close()  # info: form . close ( )
            self._rebuild_power_rows()  # info: self . _rebuild_power_rows ( )
            self.toast("Power schedule saved")  # info: self . toast ( "Power schedule saved" )

        self.confirm("Schedule these power actions?", body, "Schedule", yes)  # info: self . confirm


# ====================================================
# SECTION: function _esc
# What it does: Escape text for a GTK markup label.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _esc(value) -> str:  # info: def _esc
    from rr_ui import esc  # info: from rr_ui import esc
    return esc(value)  # info: return esc ( value )


# ====================================================
# SECTION: function _labeled
# What it does: A caption plus a widget. Does not write a file.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _labeled(caption: str, widget) -> Gtk.Box:  # info: def _labeled
    row = Gtk.Box(spacing=8)  # info: set row
    row.append(lbl(caption))  # info: row . append ( lbl ( caption ) )
    row.append(widget)  # info: row . append ( widget )
    return row  # info: return row


# ====================================================
# SECTION: function _clock_row
# What it does: Hour and minute spins with an HST caption.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clock_row(caption: str, hour: Gtk.SpinButton, minute: Gtk.SpinButton) -> Gtk.Box:  # info: def _clock_row
    row = Gtk.Box(spacing=8)  # info: set row
    row.append(lbl(caption))  # info: row . append ( lbl ( caption ) )
    row.append(hour)  # info: row . append ( hour )
    row.append(lbl(":"))  # info: row . append ( lbl ( ":" ) )
    row.append(minute)  # info: row . append ( minute )
    row.append(lbl("HST", "dim-label"))  # info: row . append ( lbl ( "HST" , "dim-label" ) )
    return row  # info: return row
