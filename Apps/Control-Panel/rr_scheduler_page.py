# ==============================================================================
# FILE: Apps/Control-Panel/rr_scheduler_page.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Root Monitor Scheduler page. Edits schedule JSON only. Never starts a poller."""
from __future__ import annotations  # info: from __future__ import annotations

import sys  # info: import sys
from pathlib import Path  # info: from pathlib import Path

from gi.repository import Gdk, GObject, Gtk  # info: from gi . repository import Gdk , GObject , Gtk

from rr_ui import esc, lbl  # info: from rr_ui import esc , lbl

_LIB = Path(__file__).resolve().parent / "Lib"  # info: set _LIB
if str(_LIB) not in sys.path:  # info: if str ( _LIB ) not in sys . path :
    sys.path.insert(0, str(_LIB))  # info: sys . path . insert ( 0 , str ( _LIB ) )

import rr_schedule as sched  # noqa: E402


# ====================================================
# SECTION: class SchedulerPage
# What it does: Simple schedule editor — pick a function, see placements, add/remove. Save writes files only.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class SchedulerPage:  # info: class SchedulerPage
    def b_scheduler(self, box):  # info: def b_scheduler
        db = self.paths.db  # info: set db
        flag = sched.load_disconnect(db)  # info: set flag
        self.sched_db = db  # info: self . sched_db = db
        self.sched_server = "pacific"  # info: self . sched_server = "pacific"
        self.sched_category = {s: "all" for s in sched.SERVERS}  # info: list filter only
        self.sched_view = {s: "function" for s in sched.SERVERS}  # info: function | day
        self.sched_selected_fn = ""  # info: self . sched_selected_fn = ""
        self.sched_docs = {s: sched.load_schedule(db, s) for s in sched.SERVERS}  # info: self . sched_docs
        self.sched_cats = {s: sched.load_catalog(db, s) for s in sched.SERVERS}  # info: self . sched_cats
        self.sched_dirty = False  # info: self . sched_dirty = False

        box.append(lbl(  # info: box . append
            "<b>Scheduler</b> — pick a function on the left, place it on the right. "
            "Polling stays <span foreground='#dc322f'><b>OFF</b></span>. Save only writes JSON files.",  # info: banner
            markup=True, wrap=True,  # info: markup
        ))  # info: )
        self.sched_status = lbl(  # info: self . sched_status
            f"disconnected={flag.get('polling_disconnected')} · "
            f"Pacific placements={len((self.sched_docs['pacific'].get('entries') or []))}",  # info: status
            "dim-label", wrap=True,  # info: css
        )  # info: )
        box.append(self.sched_status)  # info: box . append ( self . sched_status )

        nb = Gtk.Notebook()  # info: set nb
        self.sched_notebook = nb  # info: self . sched_notebook = nb
        for server in sched.SERVERS:  # info: for server in sched . SERVERS :
            page = self._sched_server_page(server)  # info: set page
            nb.append_page(page, Gtk.Label(label=server.upper()))  # info: nb . append_page
        nb.connect("switch-page", self._sched_on_tab)  # info: nb . connect
        box.append(nb)  # info: box . append ( nb )

        row = Gtk.Box(spacing=8, margin_top=10)  # info: set row
        save = Gtk.Button(label="Save schedule (files only)")  # info: set save
        save.add_css_class("suggested-action")  # info: save . add_css_class
        save.connect("clicked", self._sched_save)  # info: save . connect
        row.append(save)  # info: row . append ( save )
        keep = Gtk.Button(label="Keep polling off")  # info: set keep
        keep.connect("clicked", lambda *_: self._sched_force_disconnect())  # info: keep . connect
        row.append(keep)  # info: row . append ( keep )
        box.append(row)  # info: box . append ( row )
        self.report["scheduler"] = {  # info: self . report [ "scheduler" ]
            "polling_disconnected": True,  # info: "polling_disconnected" : True ,
            "servers": list(sched.SERVERS),  # info: "servers"
            "pacific_entries": len(self.sched_docs["pacific"].get("entries") or []),  # info: count
        }  # info: }

    def r_scheduler(self):  # info: def r_scheduler
        return  # info: no live poll; page is edit-only

    def _sched_server_page(self, server: str) -> Gtk.Box:  # info: def _sched_server_page
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=8)  # info: set root
        if server != "pacific" and not (self.sched_cats[server].get("functions") or []):  # info: if stub
            root.append(lbl(  # info: root . append
                f"{server.upper()} catalog is still a stub. You can edit the schedule file; Save does not start remote pollers.",  # info: text
                "dim-label", wrap=True,  # info: css
            ))  # info: )

        view_row = Gtk.Box(spacing=6)  # info: only two views
        view_btns: dict[str, Gtk.ToggleButton] = {}  # info: set view_btns
        group = None  # info: set group
        for mode, label in (("function", "This function"), ("day", "Whole day")):  # info: for mode
            btn = Gtk.ToggleButton(label=label)  # info: set btn
            if group is None:  # info: if group is None :
                group = btn  # info: set group
            else:  # info: else
                btn.set_group(group)  # info: btn . set_group ( group )
            btn.set_active(mode == "function")  # info: btn . set_active
            btn.connect("toggled", lambda b, srv=server, m=mode: self._sched_on_view(srv, m, b))  # info: connect
            view_btns[mode] = btn  # info: view_btns [ mode ] = btn
            view_row.append(btn)  # info: view_row . append ( btn )
        root.append(view_row)  # info: root . append ( view_row )

        shell = Gtk.Box(spacing=12, vexpand=True)  # info: set shell

        # Left: filter + function list
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)  # info: set left
        left.set_size_request(250, -1)  # info: left . set_size_request
        left.append(lbl("<b>1. Pick a function</b>", markup=True))  # info: left . append
        left.append(lbl("Number = how many times it is already on the schedule.", "dim-label", wrap=True))  # info: hint

        filter_row = Gtk.Box(spacing=6)  # info: set filter_row
        filter_row.append(lbl("Show"))  # info: filter_row . append
        cat_labels = [label for _k, label, _m, _s in sched.CATEGORY_TABS]  # info: set cat_labels
        cat_keys = [key for key, _label, _m, _s in sched.CATEGORY_TABS]  # info: set cat_keys
        cat_model = Gtk.StringList.new(cat_labels)  # info: set cat_model
        cat_drop = Gtk.DropDown(model=cat_model)  # info: set cat_drop
        cat_drop.set_selected(0)  # info: All
        cat_drop.set_hexpand(True)  # info: cat_drop . set_hexpand ( True )
        filter_row.append(cat_drop)  # info: filter_row . append ( cat_drop )
        left.append(filter_row)  # info: left . append ( filter_row )

        search = Gtk.Entry(placeholder_text="Search…")  # info: set search
        left.append(search)  # info: left . append ( search )
        scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=360)  # info: set scroll
        flist = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)  # info: set flist
        scroll.set_child(flist)  # info: scroll . set_child ( flist )
        left.append(scroll)  # info: left . append ( scroll )
        shell.append(left)  # info: shell . append ( left )

        view_stack = Gtk.Stack(vexpand=True, hexpand=True, transition_type=Gtk.StackTransitionType.CROSSFADE)  # info: set view_stack

        # Right: this function — what it is, where it is, how to place it
        fn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, hexpand=True)  # info: set fn_box
        fn_box.append(lbl("<b>2. This function</b>", markup=True))  # info: fn_box . append
        fn_title = lbl("← select something on the left", markup=True, wrap=True)  # info: set fn_title
        fn_title.add_css_class("heading")  # info: fn_title . add_css_class ( "heading" )
        fn_box.append(fn_title)  # info: fn_box . append ( fn_title )
        fn_summary = lbl("", "dim-label", wrap=True, markup=True, select=True)  # info: set fn_summary
        fn_box.append(fn_summary)  # info: fn_box . append ( fn_summary )
        fn_cmd = lbl("", "rr-mono", wrap=True, markup=True, select=True)  # info: set fn_cmd
        fn_box.append(fn_cmd)  # info: fn_box . append ( fn_cmd )

        fn_box.append(lbl("<b>Already on the schedule</b>", markup=True))  # info: placements header
        fn_scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=140)  # info: set fn_scroll
        fn_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)  # info: set fn_list
        fn_scroll.set_child(fn_list)  # info: fn_scroll . set_child ( fn_list )
        fn_box.append(fn_scroll)  # info: fn_box . append ( fn_scroll )

        fn_actions = Gtk.Box(spacing=8)  # info: set fn_actions
        fn_del = Gtk.Button(label="Remove selected")  # info: set fn_del
        fn_del.connect("clicked", lambda *_: self._sched_delete(server))  # info: connect
        fn_actions.append(fn_del)  # info: fn_actions . append ( fn_del )
        fn_tog = Gtk.Button(label="Turn on / off")  # info: set fn_tog
        fn_tog.connect("clicked", lambda *_: self._sched_toggle(server))  # info: connect
        fn_actions.append(fn_tog)  # info: fn_actions . append ( fn_tog )
        fn_box.append(fn_actions)  # info: fn_box . append ( fn_actions )

        fn_box.append(lbl("<b>3. Add a placement</b>", markup=True))  # info: place header
        place_help = lbl(  # info: set place_help
            "Boot = when poller starts · Once = after boot · Every X = repeat · Minute = each hour at that :MM",  # info: text
            "dim-label", wrap=True,  # info: css
        )  # info: )
        fn_box.append(place_help)  # info: fn_box . append ( place_help )

        place_row = Gtk.Box(spacing=8)  # info: set place_row
        boot_btn = Gtk.Button(label="At boot")  # info: set boot_btn
        boot_btn.connect("clicked", lambda *_: self._sched_place_phase(server, "boot"))  # info: connect
        place_row.append(boot_btn)  # info: place_row . append ( boot_btn )
        once_btn = Gtk.Button(label="Once at start")  # info: set once_btn
        once_btn.connect("clicked", lambda *_: self._sched_place_phase(server, "once_at_start"))  # info: connect
        place_row.append(once_btn)  # info: place_row . append ( once_btn )
        every_adj = Gtk.Adjustment(value=20, lower=1, upper=86400, step_increment=1, page_increment=10, page_size=0)  # info: set every_adj
        every_spin = Gtk.SpinButton(adjustment=every_adj, climb_rate=1, digits=0, numeric=True)  # info: set every_spin
        every_spin.set_width_chars(5)  # info: every_spin . set_width_chars ( 5 )
        place_row.append(every_spin)  # info: place_row . append ( every_spin )
        place_row.append(lbl("sec"))  # info: place_row . append
        every_btn = Gtk.Button(label="Every X seconds")  # info: set every_btn
        every_btn.connect("clicked", lambda *_: self._sched_place_every(server, int(every_spin.get_value())))  # info: connect
        place_row.append(every_btn)  # info: place_row . append ( every_btn )
        fn_box.append(place_row)  # info: fn_box . append ( place_row )

        sec_row = Gtk.Box(spacing=6)  # info: set sec_row
        sec_row.append(lbl("Click a minute (every hour):"))  # info: sec_row . append
        sec_adj = Gtk.Adjustment(value=0, lower=0, upper=59, step_increment=1, page_increment=5, page_size=0)  # info: set sec_adj
        sec_spin = Gtk.SpinButton(adjustment=sec_adj, climb_rate=1, digits=0, numeric=True)  # info: set sec_spin
        sec_spin.set_width_chars(3)  # info: sec_spin . set_width_chars ( 3 )
        sec_row.append(lbl("at second"))  # info: sec_row . append
        sec_row.append(sec_spin)  # info: sec_row . append ( sec_spin )
        fn_box.append(sec_row)  # info: fn_box . append ( sec_row )

        grid = Gtk.FlowBox(max_children_per_line=10, selection_mode=Gtk.SelectionMode.NONE, homogeneous=True)  # info: set grid
        for minute in range(60):  # info: for minute in range ( 60 ) :
            btn = Gtk.Button(label=f":{minute:02d}")  # info: set btn
            btn.set_size_request(48, 32)  # info: btn . set_size_request
            self._sched_wire_minute(btn, server, minute, sec_spin)  # info: call _sched_wire_minute
            grid.append(btn)  # info: grid . append ( btn )
        fn_box.append(grid)  # info: fn_box . append ( grid )
        view_stack.add_named(fn_box, "function")  # info: view_stack . add_named

        # Whole day overview
        day_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, vexpand=True)  # info: set day_box
        day_box.append(lbl(  # info: day_box . append
            "<b>Whole day</b> — every placement on this server (read-only overview). "
            "Switch back to <b>This function</b> to edit.",  # info: text
            markup=True, wrap=True,  # info: markup
        ))  # info: )
        day_title = lbl("", markup=True)  # info: set day_title
        day_box.append(day_title)  # info: day_box . append ( day_title )
        day_scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=360)  # info: set day_scroll
        day_list = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)  # info: set day_list
        day_scroll.set_child(day_list)  # info: day_scroll . set_child ( day_list )
        day_box.append(day_scroll)  # info: day_box . append ( day_scroll )
        view_stack.add_named(day_box, "day")  # info: view_stack . add_named

        shell.append(view_stack)  # info: shell . append ( view_stack )
        root.append(shell)  # info: root . append ( shell )

        if not hasattr(self, "sched_ui"):  # info: if not hasattr
            self.sched_ui = {}  # info: self . sched_ui = { }
        self.sched_ui[server] = {  # info: self . sched_ui [ server ]
            "flist": flist,  # info: "flist"
            "search": search,  # info: "search"
            "cat_drop": cat_drop,  # info: "cat_drop"
            "cat_keys": cat_keys,  # info: "cat_keys"
            "sec_spin": sec_spin,  # info: "sec_spin"
            "every_spin": every_spin,  # info: "every_spin"
            "view_stack": view_stack,  # info: "view_stack"
            "view_btns": view_btns,  # info: "view_btns"
            "fn_title": fn_title,  # info: "fn_title"
            "fn_summary": fn_summary,  # info: "fn_summary"
            "fn_cmd": fn_cmd,  # info: "fn_cmd"
            "fn_list": fn_list,  # info: "fn_list"
            "day_list": day_list,  # info: "day_list"
            "day_title": day_title,  # info: "day_title"
        }  # info: }

        search.connect("changed", lambda *_: self._sched_fill_palette(server))  # info: search . connect
        cat_drop.connect(  # info: cat_drop . connect
            "notify::selected",  # info: "notify::selected" ,
            lambda *_: self._sched_on_filter(server),  # info: lambda
        )  # info: )
        flist.connect("row-selected", lambda _b, row: self._sched_pick_fn(server, row))  # info: flist . connect
        fn_list.connect("row-selected", lambda _b, row: self._sched_pick_entry(server, row))  # info: fn_list
        day_list.connect("row-selected", lambda _b, row: self._sched_pick_entry(server, row))  # info: day_list

        self._sched_fill_palette(server)  # info: call _sched_fill_palette
        self._sched_fill_function_page(server)  # info: call _sched_fill_function_page
        self._sched_fill_day(server)  # info: call _sched_fill_day
        return root  # info: return root

    def _sched_on_filter(self, server: str) -> None:  # info: def _sched_on_filter
        ui = self.sched_ui.get(server) or {}  # info: set ui
        drop = ui.get("cat_drop")  # info: set drop
        keys = ui.get("cat_keys") or ["all"]  # info: set keys
        idx = int(drop.get_selected()) if drop is not None else 0  # info: set idx
        try:  # info: try
            self.sched_category[server] = keys[idx]  # info: self . sched_category [ server ]
        except IndexError:  # info: except
            self.sched_category[server] = "all"  # info: self . sched_category [ server ] = "all"
        self._sched_fill_palette(server)  # info: call _sched_fill_palette

    def _sched_on_view(self, server: str, mode: str, btn: Gtk.ToggleButton) -> None:  # info: def _sched_on_view
        if not btn.get_active():  # info: if not btn . get_active ( ) :
            return  # info: return
        self.sched_view[server] = mode  # info: self . sched_view [ server ] = mode
        ui = self.sched_ui.get(server) or {}  # info: set ui
        stack = ui.get("view_stack")  # info: set stack
        if stack is not None:  # info: if stack is not None :
            stack.set_visible_child_name(mode)  # info: stack . set_visible_child_name ( mode )
        if mode == "function":  # info: if mode == "function" :
            self._sched_fill_function_page(server)  # info: call _sched_fill_function_page
        elif mode == "day":  # info: elif mode == "day" :
            self._sched_fill_day(server)  # info: call _sched_fill_day

    def _sched_on_tab(self, _nb, _page, num):  # info: def _sched_on_tab
        try:  # info: try
            self.sched_server = sched.SERVERS[int(num)]  # info: self . sched_server
        except (IndexError, TypeError, ValueError):  # info: except
            self.sched_server = "pacific"  # info: self . sched_server = "pacific"
        mode = self.sched_view.get(self.sched_server, "function")  # info: set mode
        if mode == "day":  # info: if mode == "day" :
            self._sched_fill_day(self.sched_server)  # info: call _sched_fill_day
        else:  # info: else
            self._sched_fill_function_page(self.sched_server)  # info: call _sched_fill_function_page

    def _sched_lookup_fn(self, server: str, function_id: str) -> dict:  # info: def _sched_lookup_fn
        fid = (function_id or "").strip()  # info: set fid
        if not fid:  # info: if not fid :
            return {}  # info: return { }
        for fn in self.sched_cats.get(server, {}).get("functions") or []:  # info: for fn
            if isinstance(fn, dict) and str(fn.get("id") or "") == fid:  # info: if match
                return fn  # info: return fn
        return {}  # info: return { }

    def _sched_category_meta(self, server: str) -> tuple[str, str, frozenset[str] | None]:  # info: def _sched_category_meta
        key = self.sched_category.get(server, "all")  # info: set key
        for cat_key, _label, mode, sections in sched.CATEGORY_TABS:  # info: for cat_key
            if cat_key == key:  # info: if cat_key == key :
                return key, mode, sections  # info: return
        return "all", "all", None  # info: return

    def _sched_fn_in_category(self, server: str, fn: dict) -> bool:  # info: def _sched_fn_in_category
        _key, mode, sections = self._sched_category_meta(server)  # info: _key , mode , sections
        if mode in ("all", "every_x"):  # info: show all functions for All / Recurring filter
            return True  # info: return True
        if sections is None:  # info: if sections is None :
            return True  # info: return True
        return str(fn.get("section") or "") in sections  # info: return

    def _sched_placement_count(self, server: str, function_id: str) -> int:  # info: def _sched_placement_count
        fid = (function_id or "").strip()  # info: set fid
        if not fid:  # info: if not fid :
            return 0  # info: return 0
        return sum(  # info: return sum
            1 for e in (self.sched_docs.get(server, {}).get("entries") or [])  # info: for e
            if isinstance(e, dict) and str(e.get("function_id") or "") == fid  # info: match
        )  # info: )

    def _sched_fill_palette(self, server: str) -> None:  # info: def _sched_fill_palette
        ui = self.sched_ui[server]  # info: set ui
        flist: Gtk.ListBox = ui["flist"]  # info: set flist
        while (child := flist.get_first_child()) is not None:  # info: while
            flist.remove(child)  # info: flist . remove ( child )
        q = (ui["search"].get_text() or "").strip().lower()  # info: set q
        for fn in self.sched_cats[server].get("functions") or []:  # info: for fn
            if not self._sched_fn_in_category(server, fn):  # info: if wrong filter
                continue  # info: continue
            fid = str(fn.get("id") or "")  # info: set fid
            desc = str(fn.get("description") or "")  # info: set desc
            name = str(fn.get("name") or "")  # info: set name
            if q and q not in fid.lower() and q not in desc.lower() and q not in name.lower():  # info: if miss
                continue  # info: continue
            count = self._sched_placement_count(server, fid)  # info: set count
            badge = f"  ·  {count}" if count else ""  # info: set badge
            row = Gtk.ListBoxRow()  # info: set row
            row.fn_id = fid  # info: row . fn_id = fid
            row.set_child(lbl(f"<tt>{esc(fid)}</tt>{esc(badge)}", markup=True))  # info: row . set_child
            drag = Gtk.DragSource()  # info: set drag
            drag.set_actions(Gdk.DragAction.COPY)  # info: drag . set_actions

            def _prepare(_src, _x, _y, function_id=fid):  # info: def _prepare
                return Gdk.ContentProvider.new_for_value(function_id)  # info: return

            drag.connect("prepare", _prepare)  # info: drag . connect
            row.add_controller(drag)  # info: row . add_controller ( drag )
            flist.append(row)  # info: flist . append ( row )

    def _sched_pick_fn(self, server: str, row) -> None:  # info: def _sched_pick_fn
        if row is None:  # info: if row is None :
            return  # info: return
        self.sched_selected_fn = getattr(row, "fn_id", "") or ""  # info: self . sched_selected_fn
        self.sched_server = server  # info: self . sched_server = server
        ui = self.sched_ui.get(server) or {}  # info: set ui
        btn = (ui.get("view_btns") or {}).get("function")  # info: set btn
        if btn is not None and not btn.get_active():  # info: if not already on function
            btn.set_active(True)  # info: btn . set_active ( True )
        self._sched_fill_function_page(server)  # info: call _sched_fill_function_page

    def _sched_pick_entry(self, server: str, row) -> None:  # info: def _sched_pick_entry
        if row is None:  # info: if row is None :
            return  # info: return
        eid = getattr(row, "entry_id", None)  # info: set eid
        for item in self.sched_docs[server].get("entries") or []:  # info: for item
            if item.get("id") == eid:  # info: if match
                self.sched_selected_fn = str(item.get("function_id") or "")  # info: selected fn
                self.sched_server = server  # info: self . sched_server = server
                return  # info: return

    def _sched_wire_minute(self, btn: Gtk.Button, server: str, minute: int, sec_spin: Gtk.SpinButton) -> None:  # info: def _sched_wire_minute
        btn.connect("clicked", lambda *_: self._sched_place(server, minute, int(sec_spin.get_value())))  # info: click
        drop = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.COPY)  # info: set drop

        def _on_drop(_target, value, _x, _y, srv=server, minute=minute, spin=sec_spin):  # info: def _on_drop
            fid = str(value) if value is not None else ""  # info: set fid
            if fid:  # info: if fid :
                self.sched_selected_fn = fid  # info: self . sched_selected_fn = fid
                self._sched_place(srv, minute, int(spin.get_value()))  # info: call _sched_place
            return True  # info: return True

        drop.connect("drop", _on_drop)  # info: drop . connect
        btn.add_controller(drop)  # info: btn . add_controller ( drop )

    def _sched_place(self, server: str, minute: int, second: int) -> None:  # info: def _sched_place
        fid = self.sched_selected_fn  # info: set fid
        if not fid:  # info: if not fid :
            self.sched_status.set_text("Pick a function on the left first.")  # info: status
            return  # info: return
        entry = sched.make_entry(fid, minute=minute, second=second, hour=None, enabled=False)  # info: set entry
        self.sched_docs[server].setdefault("entries", []).append(entry)  # info: append
        self.sched_dirty = True  # info: self . sched_dirty = True
        self._sched_refresh_views(server)  # info: call _sched_refresh_views
        self.sched_status.set_text(f"Added {sched.entry_label(entry)} (not saved yet)")  # info: status

    def _sched_place_phase(self, server: str, phase: str) -> None:  # info: def _sched_place_phase
        fid = self.sched_selected_fn  # info: set fid
        if not fid:  # info: if not fid :
            self.sched_status.set_text("Pick a function on the left first.")  # info: status
            return  # info: return
        entry = sched.make_entry(fid, phase=phase, enabled=False)  # info: set entry
        self.sched_docs[server].setdefault("entries", []).append(entry)  # info: append
        self.sched_dirty = True  # info: self . sched_dirty = True
        self._sched_refresh_views(server)  # info: call _sched_refresh_views
        self.sched_status.set_text(f"Added {sched.entry_label(entry)} (not saved yet)")  # info: status

    def _sched_place_every(self, server: str, every_seconds: int) -> None:  # info: def _sched_place_every
        fid = self.sched_selected_fn  # info: set fid
        if not fid:  # info: if not fid :
            self.sched_status.set_text("Pick a function on the left first.")  # info: status
            return  # info: return
        entry = sched.make_entry(fid, every_seconds=max(1, int(every_seconds)), minute=None, enabled=False)  # info: entry
        self.sched_docs[server].setdefault("entries", []).append(entry)  # info: append
        self.sched_dirty = True  # info: self . sched_dirty = True
        self._sched_refresh_views(server)  # info: call _sched_refresh_views
        self.sched_status.set_text(f"Added {sched.entry_label(entry)} (not saved yet)")  # info: status

    def _sched_refresh_views(self, server: str) -> None:  # info: def _sched_refresh_views
        self._sched_fill_palette(server)  # info: call _sched_fill_palette
        self._sched_fill_function_page(server)  # info: call _sched_fill_function_page
        self._sched_fill_day(server)  # info: call _sched_fill_day

    def _sched_fill_function_page(self, server: str) -> None:  # info: def _sched_fill_function_page
        ui = self.sched_ui.get(server) or {}  # info: set ui
        box = ui.get("fn_list")  # info: set box
        title = ui.get("fn_title")  # info: set title
        summary = ui.get("fn_summary")  # info: set summary
        cmd_w = ui.get("fn_cmd")  # info: set cmd_w
        if box is None:  # info: if box is None :
            return  # info: return
        while (child := box.get_first_child()) is not None:  # info: while
            box.remove(child)  # info: box . remove ( child )
        fid = (self.sched_selected_fn or "").strip()  # info: set fid
        if not fid:  # info: if not fid :
            if title is not None:  # info: if title is not None :
                title.set_markup("← select something on the left")  # info: title
            if summary is not None:  # info: if summary is not None :
                summary.set_markup("Then you’ll see where it already sits, and buttons to place it.")  # info: summary
            if cmd_w is not None:  # info: if cmd_w is not None :
                cmd_w.set_markup("")  # info: cmd_w . set_markup ( "" )
            empty = Gtk.ListBoxRow()  # info: set empty
            empty.set_child(lbl("(nothing selected)", "dim-label"))  # info: empty . set_child
            box.append(empty)  # info: box . append ( empty )
            return  # info: return

        fn = self._sched_lookup_fn(server, fid)  # info: set fn
        name = str(fn.get("name") or fid)  # info: set name
        section_name = str(fn.get("section") or "—")  # info: set section_name
        desc = str(fn.get("description") or "").strip() or "No description."  # info: set desc
        builtin = str(fn.get("builtin") or "").strip()  # info: set builtin
        command = str(fn.get("command") or "").strip()  # info: set command
        if title is not None:  # info: if title is not None :
            title.set_markup(f"<b>{esc(name)}</b>  <tt>{esc(fid)}</tt>")  # info: title

        placed = [  # info: set placed
            e for e in (self.sched_docs.get(server, {}).get("entries") or [])  # info: for e
            if isinstance(e, dict) and str(e.get("function_id") or "") == fid  # info: match
        ]  # info: ]

        def place_key(e: dict) -> tuple:  # info: def place_key
            phase = str(e.get("phase") or "")  # info: set phase
            phase_ord = {"boot": 0, "once_at_start": 1}.get(phase, 2)  # info: set phase_ord
            every = e.get("every_seconds")  # info: set every
            if every is not None:  # info: if every is not None :
                return (phase_ord, 0, float(every), 0, 0)  # info: return
            return (  # info: return
                phase_ord,  # info: phase_ord
                1,  # info: clock
                int(e.get("hour") if e.get("hour") is not None else -1),  # info: hour
                int(e.get("minute") if e.get("minute") is not None else -1),  # info: minute
                int(e.get("second") if e.get("second") is not None else 0),  # info: second
            )  # info: )

        placed.sort(key=place_key)  # info: placed . sort
        if summary is not None:  # info: if summary is not None :
            summary.set_markup(  # info: summary . set_markup
                f"{esc(desc)}\n"
                f"group <tt>{esc(section_name)}</tt> · "
                f"<b>{len(placed)}</b> placement(s) on {esc(server)}"  # info: text
            )  # info: )
        if cmd_w is not None:  # info: if cmd_w is not None :
            if builtin and not command:  # info: if builtin
                cmd_w.set_markup(f"Runs builtin <tt>{esc(builtin)}</tt>")  # info: cmd_w
            elif command:  # info: elif command
                cmd_w.set_markup(f"<tt>{esc(command)}</tt>")  # info: cmd_w
            else:  # info: else
                cmd_w.set_markup("<i>No command listed in catalog.</i>")  # info: cmd_w

        if not placed:  # info: if not placed :
            empty = Gtk.ListBoxRow()  # info: set empty
            empty.set_child(lbl("Not placed yet. Use the buttons below.", "dim-label", wrap=True))  # info: empty
            box.append(empty)  # info: box . append ( empty )
            return  # info: return
        for e in placed:  # info: for e in placed :
            row = Gtk.ListBoxRow()  # info: set row
            row.entry_id = e.get("id")  # info: row . entry_id
            if e.get("phase") == "boot":  # info: if boot
                kind = "At boot"  # info: set kind
            elif e.get("phase") == "once_at_start":  # info: elif once
                kind = "Once at start"  # info: set kind
            elif e.get("every_seconds") is not None:  # info: elif every
                kind = f"Every {e.get('every_seconds')}s"  # info: set kind
            else:  # info: else
                kind = "Clock minute"  # info: set kind
            en = "on" if e.get("enabled") else "off"  # info: set en
            row.set_child(  # info: row . set_child
                lbl(f"<b>{esc(kind)}</b>  {esc(sched.entry_label(e))}  [{en}]", "rr-mono", wrap=True, markup=True)  # info: lbl
            )  # info: )
            box.append(row)  # info: box . append ( row )

    def _sched_selected_entry(self, server: str) -> dict | None:  # info: def _sched_selected_entry
        ui = self.sched_ui[server]  # info: set ui
        for key in ("fn_list", "day_list"):  # info: function page or whole day
            box = ui.get(key)  # info: set box
            if box is None:  # info: if box is None :
                continue  # info: continue
            sel = box.get_selected_row()  # info: set sel
            if sel is not None and getattr(sel, "entry_id", None):  # info: if usable
                eid = sel.entry_id  # info: set eid
                for entry in self.sched_docs[server].get("entries") or []:  # info: for entry
                    if entry.get("id") == eid:  # info: if match
                        return entry  # info: return entry
        return None  # info: return None

    def _sched_delete(self, server: str) -> None:  # info: def _sched_delete
        entry = self._sched_selected_entry(server)  # info: set entry
        if not entry:  # info: if not entry :
            self.sched_status.set_text("Select a placement in the list first.")  # info: status
            return  # info: return
        eid = entry.get("id")  # info: set eid
        self.sched_docs[server]["entries"] = [e for e in (self.sched_docs[server].get("entries") or []) if e.get("id") != eid]  # info: filter
        self.sched_dirty = True  # info: self . sched_dirty = True
        self._sched_refresh_views(server)  # info: call _sched_refresh_views
        self.sched_status.set_text(f"Removed {eid} (not saved yet)")  # info: status

    def _sched_toggle(self, server: str) -> None:  # info: def _sched_toggle
        entry = self._sched_selected_entry(server)  # info: set entry
        if not entry:  # info: if not entry :
            self.sched_status.set_text("Select a placement in the list first.")  # info: status
            return  # info: return
        entry["enabled"] = not bool(entry.get("enabled"))  # info: entry [ "enabled" ]
        self.sched_dirty = True  # info: self . sched_dirty = True
        self._sched_refresh_views(server)  # info: call _sched_refresh_views
        self.sched_status.set_text(f"Now {'on' if entry.get('enabled') else 'off'}: {sched.entry_label(entry)}")  # info: status

    def _sched_fill_day(self, server: str) -> None:  # info: def _sched_fill_day
        ui = self.sched_ui.get(server) or {}  # info: set ui
        box = ui.get("day_list")  # info: set box
        title = ui.get("day_title")  # info: set title
        if box is None:  # info: if box is None :
            return  # info: return
        while (child := box.get_first_child()) is not None:  # info: while
            box.remove(child)  # info: box . remove ( child )
        entries = [e for e in (self.sched_docs.get(server, {}).get("entries") or []) if isinstance(e, dict)]  # info: set entries
        if title is not None:  # info: if title is not None :
            title.set_markup(f"<b>{len(entries)}</b> placements · 00:00–23:59 HST pattern")  # info: title

        def add_row(text: str, entry: dict | None = None, *, header: bool = False) -> None:  # info: def add_row
            row = Gtk.ListBoxRow()  # info: set row
            if entry is not None:  # info: if entry is not None :
                row.entry_id = entry.get("id")  # info: row . entry_id
            css = "dim-label" if header else "rr-mono"  # info: set css
            row.set_child(lbl(text, css, wrap=True, markup=header))  # info: row . set_child
            box.append(row)  # info: box . append ( row )

        add_row("<b>Boot / once (start of day)</b>", header=True)  # info: header
        bootish = [e for e in entries if e.get("phase") in ("boot", "once_at_start")]  # info: set bootish
        bootish.sort(key=lambda x: (x.get("phase") or "", x.get("function_id") or ""))  # info: sort
        for e in bootish:  # info: for e in bootish :
            add_row(sched.entry_label(e), e)  # info: add_row
        if not bootish:  # info: if not bootish :
            add_row("(none)")  # info: add_row

        add_row("<b>Every X seconds (all day)</b>", header=True)  # info: header
        recurring = [e for e in entries if e.get("every_seconds") is not None]  # info: set recurring
        recurring.sort(key=lambda x: (float(x.get("every_seconds") or 0), x.get("function_id") or ""))  # info: sort
        for e in recurring:  # info: for e in recurring :
            add_row(sched.entry_label(e), e)  # info: add_row
        if not recurring:  # info: if not recurring :
            add_row("(none)")  # info: add_row

        add_row("<b>Clock minutes (by hour)</b>", header=True)  # info: header
        clocked = [  # info: set clocked
            e for e in entries  # info: for e
            if e.get("phase") is None and e.get("every_seconds") is None and e.get("minute") is not None  # info: clock
        ]  # info: ]
        by_hour: dict[int, list] = {h: [] for h in range(24)}  # info: set by_hour
        every_hour: list = []  # info: set every_hour
        for e in clocked:  # info: for e in clocked :
            if e.get("hour") is None:  # info: if every hour
                every_hour.append(e)  # info: every_hour . append ( e )
            else:  # info: else
                try:  # info: try
                    by_hour[int(e.get("hour"))].append(e)  # info: by_hour
                except (TypeError, ValueError):  # info: except
                    every_hour.append(e)  # info: every_hour . append ( e )

        def slot_key(e: dict) -> tuple:  # info: def slot_key
            return (int(e.get("minute") or 0), int(e.get("second") or 0), e.get("function_id") or "")  # info: return

        every_hour.sort(key=slot_key)  # info: every_hour . sort
        if every_hour:  # info: if every_hour :
            add_row("<b>Every hour</b>", header=True)  # info: header
            for e in every_hour:  # info: for e in every_hour :
                add_row(sched.entry_label(e), e)  # info: add_row
        for hour in range(24):  # info: for hour in range ( 24 ) :
            items = sorted(by_hour[hour], key=slot_key)  # info: set items
            if not items:  # info: skip empty hours to keep the list short
                continue  # info: continue
            add_row(f"<b>{hour:02d}:00</b>", header=True)  # info: header
            for e in items:  # info: for e in items :
                add_row(sched.entry_label(e), e)  # info: add_row
        if not clocked:  # info: if not clocked :
            add_row("(none)")  # info: add_row
        if not entries:  # info: if not entries :
            add_row("(schedule is empty)")  # info: add_row

    def _sched_force_disconnect(self) -> None:  # info: def _sched_force_disconnect
        sched.save_disconnect(self.sched_db, disconnected=True, armed=False)  # info: call save_disconnect
        for server in sched.SERVERS:  # info: for server
            doc = self.sched_docs[server]  # info: set doc
            doc["armed"] = False  # info: doc [ "armed" ] = False
            doc["polling_disconnected"] = True  # info: doc [ "polling_disconnected" ] = True
            sched.save_schedule(self.sched_db, server, doc)  # info: call save_schedule
        self.sched_dirty = False  # info: self . sched_dirty = False
        self.sched_status.set_text("Polling stays OFF. Files updated. Nothing started.")  # info: status

    def _sched_save(self, *_args) -> None:  # info: def _sched_save
        for server in sched.SERVERS:  # info: for server
            sched.save_schedule(self.sched_db, server, self.sched_docs[server])  # info: call save_schedule
            self.sched_docs[server] = sched.load_schedule(self.sched_db, server)  # info: reload
        self.sched_dirty = False  # info: self . sched_dirty = False
        self.sched_status.set_text("Saved. Polling still OFF. No poller start, no SSH push.")  # info: status
