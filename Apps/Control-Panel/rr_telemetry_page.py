# ==============================================================================
# FILE: Apps/Control-Panel/rr_telemetry_page.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Root Monitor Telemetry page. Mixed into Panel.

A service window is written to the public website file. The home page banner
and the live network panel read that file. This page does not restart the poller.
"""
from __future__ import annotations  # info: from __future__ import annotations

import importlib.util  # info: import importlib . util
from datetime import datetime, timedelta  # info: from datetime import datetime , timedelta
from pathlib import Path  # info: from pathlib import Path

from gi.repository import Gtk  # info: from gi . repository import Gtk

from rr_ui import esc, lbl, section  # info: from rr_ui import esc , lbl , section


# ====================================================
# SECTION: function _load_notice
# What it does: Load service_notice.py by path. Does not publish a window.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _load_notice(pacific: Path):  # info: def _load_notice
    path = Path(pacific) / "Automations" / "scripts" / "service_notice.py"  # info: set path
    spec = importlib.util.spec_from_file_location("service_notice", path)  # info: set spec
    if spec is None or spec.loader is None:  # info: if spec is None or spec . loader is None
        raise ImportError(str(path))  # info: raise ImportError
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    return mod  # info: return mod


# ====================================================
# SECTION: function _spin
# What it does: Integer spin button.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _spin(value: int, upper: int) -> Gtk.SpinButton:  # info: def _spin
    adj = Gtk.Adjustment(value=value, lower=0, upper=upper, step_increment=1, page_increment=1, page_size=0)  # info: set adj
    spin = Gtk.SpinButton(adjustment=adj, climb_rate=1, digits=0, numeric=True)  # info: set spin
    spin.set_width_chars(3)  # info: spin . set_width_chars ( 3 )
    return spin  # info: return spin


# ====================================================
# SECTION: class TelemetryPage
# What it does: Telemetry page mixin. Writes the public notice only after confirm.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class TelemetryPage:  # info: class TelemetryPage
    def _notice(self):  # info: def _notice
        if getattr(self, "_notice_mod", None) is None:  # info: if getattr ( self , "_notice_mod" , None ) is None
            self._notice_mod = _load_notice(self.paths.pacific)  # info: self . _notice_mod = _load_notice
        return self._notice_mod  # info: return self . _notice_mod

    def b_telemetry(self, box):  # info: def b_telemetry
        try:  # info: try
            self._notice()  # info: self . _notice ( )
        except Exception as exc:  # info: except Exception as exc
            self.errors.append(f"telemetry: {exc}")  # info: self . errors . append
            box.append(lbl(f"Telemetry page failed to load: {exc}", "rr-fail", wrap=True))  # info: box . append
            self.report["telemetry"] = {"error": str(exc)}  # info: self . report [ "telemetry" ] = { "error" : str ( exc ) }
            return  # info: return
        self.tel_note = lbl("", wrap=True)  # info: self . tel_note = lbl ( "" , wrap = True )
        box.append(self.tel_note)  # info: box . append ( self . tel_note )
        o, inner = section("Service windows")  # info: o , inner = section ( "Service windows" )
        inner.append(lbl(  # info: inner . append ( lbl
            "Set when this server is expected to go down and come back. The public home page shows a service banner. The live network panel keeps the last known counts and the expected return time.",  # info: "Set when this server is expected to go down and come back. The public home page shows a service banner. The live network panel keeps the last known counts and the expected return time." ,
            "dim-label", wrap=True))  # info: "dim-label" , wrap = True ) )
        new = Gtk.Button(label="New service window", halign=Gtk.Align.START)  # info: set new
        new.connect("clicked", lambda *_: self._open_window_form())  # info: new . connect
        inner.append(new)  # info: inner . append ( new )
        self.tel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)  # info: self . tel_box = Gtk . Box
        inner.append(self.tel_box)  # info: inner . append ( self . tel_box )
        box.append(o)  # info: box . append ( o )
        self._fill_windows()  # info: self . _fill_windows ( )

    def r_telemetry(self):  # info: def r_telemetry
        if "telemetry" not in self.built or not hasattr(self, "tel_note"):  # info: if "telemetry" not in self . built or not hasattr
            return  # info: return
        self._fill_windows()  # info: self . _fill_windows ( )

    def _fill_windows(self):  # info: def _fill_windows
        mod = self._notice()  # info: set mod
        doc = mod.load()  # info: set doc
        items = [it for it in doc.get("windows") or [] if isinstance(it, dict)]  # info: set items
        now = datetime.now(mod.HST)  # info: set now
        signature = tuple((it.get("id"), it.get("down_at"), it.get("up_at"), it.get("note"), (it.get("last_known") or {}).get("at"), mod.phase(it, now)) for it in items)  # info: set signature
        if signature == getattr(self, "_tel_sig", None) and self.tel_box.get_first_child() is not None:  # info: if signature == getattr ( self , "_tel_sig" , None ) and
            return  # info: return
        self._tel_sig = signature  # info: self . _tel_sig = signature
        self.tel_note.set_text("Saved to the public website file. The site publish picks it up on its own. Nothing here restarts the poller.")  # info: self . tel_note . set_text
        while (child := self.tel_box.get_first_child()) is not None:  # info: while ( child := self . tel_box . get_first_child ( ) ) is not None
            self.tel_box.remove(child)  # info: self . tel_box . remove ( child )
        if not items:  # info: if not items
            self.tel_box.append(lbl("No service windows.", "dim-label"))  # info: self . tel_box . append
        current = mod.current_window(doc, now)  # info: set current
        for item in items:  # info: for item in items
            kind = mod.phase(item, now)  # info: set kind
            known = item.get("last_known") if isinstance(item.get("last_known"), dict) else {}  # info: set known
            counts = f"Hawaiʻi {known.get('hawaii', '—')} · Mainland {known.get('mainland', '—')} · flows {known.get('flows', '—')} · endpoints {known.get('endpoints', '—')}"  # info: set counts
            line = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)  # info: set line
            text = lbl("", wrap=True)  # info: set text
            text.set_markup(  # info: text . set_markup
                f"<b>{esc(kind)}</b>  down {esc(item.get('down_at') or '—')} · back {esc(item.get('up_at') or '—')}\n"  # info: f" <b> { esc ( kind ) } </b>
                f"<span alpha='75%'>{esc(item.get('note') or 'No public note')}</span>\n"  # info: f" <span alpha='75%'> { esc ( item . get ( 'note' ) or 'No public note' ) } </span> \n"
                f"<span alpha='75%'>Last known {esc(known.get('at') or '—')} · {esc(counts)}</span>")  # info: f" <span alpha='75%'> Last known { esc ( known . get ( 'at' ) or '—' ) }
            buttons = Gtk.Box(spacing=8)  # info: set buttons
            refresh = Gtk.Button(label="Refresh last known")  # info: set refresh
            refresh.connect("clicked", lambda _b, iid=item["id"]: self._refresh_window(iid))  # info: refresh . connect
            delete = Gtk.Button(label="Delete")  # info: set delete
            delete.connect("clicked", lambda _b, iid=item["id"]: self._delete_window(iid))  # info: delete . connect
            buttons.append(refresh)  # info: buttons . append ( refresh )
            buttons.append(delete)  # info: buttons . append ( delete )
            line.append(text)  # info: line . append ( text )
            line.append(buttons)  # info: line . append ( buttons )
            self.tel_box.append(line)  # info: self . tel_box . append ( line )
        self.report["telemetry"] = {"windows": len(items), "showing": bool(current), "current": (current or {}).get("id")}  # info: self . report [ "telemetry" ] = {

    def _open_window_form(self):  # info: def _open_window_form
        if self.win is None:  # info: if self . win is None
            return  # info: return
        mod = self._notice()  # info: set mod
        now = datetime.now(mod.HST)  # info: set now
        form = Gtk.Window(title="New service window", modal=True, transient_for=self.win)  # info: set form
        form.set_default_size(480, 360)  # info: form . set_default_size ( 480 , 360 )
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)  # info: set root
        root.append(lbl("Times are HST. The return time is when the server is expected back online.", "dim-label", wrap=True))  # info: root . append
        down_date = Gtk.Entry(text=now.date().isoformat())  # info: set down_date
        up_date = Gtk.Entry(text=(now.date() + timedelta(days=1)).isoformat())  # info: set up_date
        down_h, down_m = _spin(22, 23), _spin(0, 59)  # info: down_h , down_m = _spin ( 22 , 23 ) , _spin ( 0 , 59 )
        up_h, up_m = _spin(6, 23), _spin(0, 59)  # info: up_h , up_m = _spin ( 6 , 23 ) , _spin ( 0 , 59 )
        note = Gtk.Entry(placeholder_text="Public note, optional")  # info: set note
        root.append(_row("Down date", down_date))  # info: root . append
        root.append(_clock("Down time", down_h, down_m))  # info: root . append
        root.append(_row("Back date", up_date))  # info: root . append
        root.append(_clock("Back time", up_h, up_m))  # info: root . append
        root.append(_row("Note", note))  # info: root . append
        buttons = Gtk.Box(spacing=8, halign=Gtk.Align.END)  # info: set buttons
        cancel = Gtk.Button(label="Cancel")  # info: set cancel
        cancel.connect("clicked", lambda *_: form.close())  # info: cancel . connect
        save = Gtk.Button(label="Publish")  # info: set save
        save.add_css_class("suggested-action")  # info: save . add_css_class ( "suggested-action" )
        save.connect("clicked", lambda *_: self._submit_window(form, mod, down_date, down_h, down_m, up_date, up_h, up_m, note))  # info: save . connect
        buttons.append(cancel)  # info: buttons . append ( cancel )
        buttons.append(save)  # info: buttons . append ( save )
        root.append(buttons)  # info: root . append ( buttons )
        form.set_child(root)  # info: form . set_child ( root )
        form.present()  # info: form . present ( )

    def _submit_window(self, form, mod, down_date, down_h, down_m, up_date, up_h, up_m, note):  # info: def _submit_window
        down = mod.parse_when(down_date.get_text(), int(down_h.get_value()), int(down_m.get_value()))  # info: set down
        up = mod.parse_when(up_date.get_text(), int(up_h.get_value()), int(up_m.get_value()))  # info: set up
        if down is None or up is None:  # info: if down is None or up is None
            self.toast("Use a YYYY-MM-DD date and a valid clock time.")  # info: self . toast
            return  # info: return
        err = mod.validate_window(down, up)  # info: set err
        text, note_err = mod.clean_note(note.get_text())  # info: text , note_err = mod . clean_note
        if err or note_err:  # info: if err or note_err
            self.toast(err or note_err)  # info: self . toast
            return  # info: return
        body = f"Down {down.strftime('%Y-%m-%d %H:%M')} HST\nBack {up.strftime('%Y-%m-%d %H:%M')} HST"  # info: set body
        if text:  # info: if text
            body += f"\n\n{text}"  # info: set body
        body += "\n\nThis publishes on the website. The home page banner and the live network panel use it."  # info: set body

        def yes():  # info: def yes
            try:  # info: try
                mod.add_window(down, up, text)  # info: mod . add_window
            except Exception as exc:  # info: except Exception as exc
                self.toast(str(exc))  # info: self . toast
                return  # info: return
            form.close()  # info: form . close ( )
            self._fill_windows()  # info: self . _fill_windows ( )
            self.toast("Service window published")  # info: self . toast

        self.confirm("Publish this service window?", body, "Publish", yes)  # info: self . confirm

    def _refresh_window(self, item_id):  # info: def _refresh_window
        if self.win is None:  # info: if self . win is None
            return  # info: return

        def yes():  # info: def yes
            try:  # info: try
                self._notice().refresh_last_known(item_id)  # info: self . _notice ( ) . refresh_last_known
            except Exception as exc:  # info: except Exception as exc
                self.toast(str(exc))  # info: self . toast
                return  # info: return
            self._fill_windows()  # info: self . _fill_windows ( )
            self.toast("Last known state updated")  # info: self . toast

        self.confirm("Refresh last known?", "Read the public network counts again and store them on this window.", "Refresh", yes)  # info: self . confirm

    def _delete_window(self, item_id):  # info: def _delete_window
        if self.win is None:  # info: if self . win is None
            return  # info: return

        def yes():  # info: def yes
            self._notice().delete_window(item_id)  # info: self . _notice ( ) . delete_window
            self._fill_windows()  # info: self . _fill_windows ( )
            self.toast("Service window removed")  # info: self . toast

        self.confirm("Remove this service window?", "The public banner and the planned-down line go away after the site publish.", "Delete", yes)  # info: self . confirm


# ====================================================
# SECTION: function _row
# What it does: A caption plus one widget.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _row(caption: str, widget) -> Gtk.Box:  # info: def _row
    row = Gtk.Box(spacing=8)  # info: set row
    row.append(lbl(caption))  # info: row . append ( lbl ( caption ) )
    row.append(widget)  # info: row . append ( widget )
    return row  # info: return row


# ====================================================
# SECTION: function _clock
# What it does: Hour and minute spins labeled HST.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _clock(caption: str, hour: Gtk.SpinButton, minute: Gtk.SpinButton) -> Gtk.Box:  # info: def _clock
    row = Gtk.Box(spacing=8)  # info: set row
    row.append(lbl(caption))  # info: row . append ( lbl ( caption ) )
    row.append(hour)  # info: row . append ( hour )
    row.append(lbl(":"))  # info: row . append ( lbl ( ":" ) )
    row.append(minute)  # info: row . append ( minute )
    row.append(lbl("HST", "dim-label"))  # info: row . append
    return row  # info: return row
