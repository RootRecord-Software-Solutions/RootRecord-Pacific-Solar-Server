# ==============================================================================
# FILE: Apps/Control-Panel/rr_ui.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""rr_ui.py — small shared GTK helpers for Root Monitor (moved out of rr_control_panel.py 2026-09-29).
Import only after gi.require_version(...) has run (rr_control_panel.py does that)."""
from __future__ import annotations  # info: from __future__ import annotations

from gi.repository import Gio, GLib, Gtk, Pango  # info: from gi . repository import Gio , GLib

try:  # info: try :
    from gi.repository import Adw  # info: from gi . repository import Adw
except ImportError:  # pragma: no cover
    Adw = None  # info: set Adw


REDACT: list[str] = []   # known secret values (filled lazily by the panel); never printed


# ====================================================
# SECTION: function redact
# What it does: Replace any known secret value inside a display string with <masked len N>.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def redact(s: str) -> str:  # info: def redact
    """Replace any known secret value inside a display string with <masked len N>."""  # info: """Replace any known secret value inside a display string with <masked len N>."""
    if s and REDACT:  # info: if s and REDACT :
        for v in REDACT:  # info: for v in REDACT :
            if v in s:  # info: if v in s :
                s = s.replace(v, f"<masked len {len(v)}>")  # info: set s
    return s  # info: return s


# ====================================================
# SECTION: function lbl
# What it does: lbl.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lbl(text="", css=None, xalign=0.0, wrap=False, select=False, markup=False) -> Gtk.Label:  # info: def lbl
    w = Gtk.Label(xalign=xalign)  # info: set w
    (w.set_markup if markup else w.set_text)(text)  # info: call (
    if wrap:  # info: if wrap :
        w.set_wrap(True)  # info: w . set_wrap ( True )
        w.set_wrap_mode(Pango.WrapMode.WORD_CHAR)  # info: w . set_wrap_mode ( Pango . WrapMode .
    if select:  # info: if select :
        w.set_selectable(True)  # info: w . set_selectable ( True )
    for c in (css or "").split():  # info: for c in ( css or "" )
        w.add_css_class(c)  # info: w . add_css_class ( c )
    return w  # info: return w


# ====================================================
# SECTION: function esc
# What it does: esc.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def esc(s) -> str:  # info: def esc
    return GLib.markup_escape_text(str(s))  # info: return GLib . markup_escape_text ( str ( s


# ====================================================
# SECTION: function badge_css
# What it does: badge css.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def badge_css(state: str) -> str:  # info: def badge_css
    return {"PASS": "rr-pass", "WARN": "rr-warn", "FAIL": "rr-fail", "BLOCKED": "rr-fail",  # info: return { "PASS" : "rr-pass" , "WARN" :
            "VERIFY PENDING": "rr-warn"}.get(state, "dim-label")  # info: "VERIFY PENDING" : "rr-warn" } . get ( state


# ====================================================
# SECTION: function section
# What it does: section.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def section(title: str) -> tuple[Gtk.Box, Gtk.Box]:  # info: def section
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # info: set outer
    outer.append(lbl(title, "heading"))  # info: outer . append ( lbl ( title ,
    inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)  # info: set inner
    inner.add_css_class("card")  # info: inner . add_css_class ( "card" )
    inner.add_css_class("rr-card")  # info: inner . add_css_class ( "rr-card" )
    outer.append(inner)  # info: outer . append ( inner )
    return outer, inner  # info: return outer , inner


# ====================================================
# SECTION: function spawn
# What it does: Start a child without blocking the UI; always reaped (wait/communicate async).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def spawn(argv: list[str], on_done=None, capture=False):  # info: def spawn
    """Start a child without blocking the UI; always reaped (wait/communicate async)."""  # info: """Start a child without blocking the UI; always reaped (wait/communicate async)."""
    flags = Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE if capture else Gio.SubprocessFlags.NONE  # info: set flags
    proc = Gio.Subprocess.new(argv, flags)  # info: set proc
    if capture:  # info: if capture :
        def fin(p, res):  # info: def fin
            try:  # info: try :
                ok, out, _e = p.communicate_utf8_finish(res)  # info: ok , out , _e = p .
            except GLib.Error as e:  # info: except GLib . Error as e :
                out = f"error: {e.message}"  # info: set out
            if on_done:  # info: if on_done :
                on_done(out or "", p.get_exit_status() if p.get_if_exited() else -1)  # info: call on_done
        proc.communicate_utf8_async(None, None, fin)  # info: proc . communicate_utf8_async ( None , None ,
    else:  # info: else :
        proc.wait_async(None, lambda p, r: p.wait_finish(r))  # info: proc . wait_async ( None , lambda p
    return proc  # info: return proc


# ====================================================
# SECTION: TOGGLE_CSS
# What it does: Set TOGGLE_CSS.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
TOGGLE_CSS = """
button.rr-toggle { min-width: 150px; min-height: 30px; padding: 2px 14px; font-weight: bold; border-radius: 8px;
                   border: 2px solid transparent; background-image: none; }
button.rr-toggle.rr-on { background-color: #2e7d32; color: #ffffff; border-color: #66bb6a; }
button.rr-toggle.rr-on:hover { background-color: #388e3c; }
button.rr-toggle.rr-off { background-color: alpha(#dc322f, 0.16); border-color: alpha(#dc322f, 0.70); }
button.rr-toggle.rr-off:hover { background-color: alpha(#dc322f, 0.28); }
button.rr-toggle.rr-big { min-width: 260px; min-height: 40px; font-size: 12pt; }
"""


# ====================================================
# SECTION: function state_toggle
# What it does: Labelled on/off button (replaces Gtk.Switch / Adw.SwitchRow, 2026-09-29): reads "<name>: On" (green) or "<name>: Off" (red outline). on_change(btn, active) runs after a user click.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def state_toggle(name: str, active: bool, on_change=None, on_text: str = "On", off_text: str = "Off",  # info: def state_toggle
                 tooltip: str | None = None, big: bool = False) -> Gtk.ToggleButton:  # info: set tooltip
    """Labelled on/off button (replaces Gtk.Switch / Adw.SwitchRow, 2026-09-29): reads "<name>: On" (green) or
    "<name>: Off" (red outline). on_change(btn, active) runs after a user click. btn.rr_set(active) changes the
    state WITHOUT calling on_change (reverts, status reads)."""
    b = Gtk.ToggleButton(valign=Gtk.Align.CENTER, halign=Gtk.Align.START)  # info: set b
    b.add_css_class("rr-toggle")  # info: b . add_css_class ( "rr-toggle" )
    if big:  # info: if big :
        b.add_css_class("rr-big")  # info: b . add_css_class ( "rr-big" )
    if tooltip:  # info: if tooltip :
        b.set_tooltip_text(tooltip)  # info: b . set_tooltip_text ( tooltip )

    def paint():  # info: def paint
        on = b.get_active()  # info: set on
        b.set_label(f"{name}: {on_text if on else off_text}")  # info: b . set_label ( f" { name }
        b.add_css_class("rr-on" if on else "rr-off")  # info: b . add_css_class ( "rr-on" if on else
        b.remove_css_class("rr-off" if on else "rr-on")  # info: b . remove_css_class ( "rr-off" if on else

    def toggled(_b):  # info: def toggled
        paint()  # info: call paint
        if on_change is not None:  # info: if on_change is not None :
            on_change(b, b.get_active())  # info: call on_change

    b.set_active(bool(active))  # info: b . set_active ( bool ( active )
    paint()  # info: call paint
    hid = b.connect("toggled", toggled)  # info: set hid

    def rr_set(value: bool):  # info: def rr_set
        b.handler_block(hid)  # info: b . handler_block ( hid )
        b.set_active(bool(value))  # info: b . set_active ( bool ( value )
        paint()  # info: call paint
        b.handler_unblock(hid)  # info: b . handler_unblock ( hid )
    b.rr_set = rr_set  # info: b . rr_set = rr_set
    return b  # info: return b


# ====================================================
# SECTION: function action_row
# What it does: Plain-text Adw.ActionRow (markup OFF, so file names / commands render literally).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def action_row(title: str, subtitle: str = "", lines: int = 2):  # info: def action_row
    """Plain-text Adw.ActionRow (markup OFF, so file names / commands render literally)."""  # info: """Plain-text Adw.ActionRow (markup OFF, so file names / commands render literally)."""
    if Adw is None:  # info: if Adw is None :
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)  # info: set b
        b.append(lbl(title))  # info: b . append ( lbl ( title )
        b.append(lbl(subtitle, "dim-label", wrap=True))  # info: b . append ( lbl ( subtitle ,
        return b  # info: return b
    r = Adw.ActionRow()  # info: set r
    r.set_use_markup(False)  # info: r . set_use_markup ( False )
    r.set_title(redact(title))  # info: r . set_title ( redact ( title )
    r.set_subtitle(redact(subtitle))  # info: r . set_subtitle ( redact ( subtitle )
    r.set_subtitle_lines(lines)  # info: r . set_subtitle_lines ( lines )
    r.set_title_lines(2)  # info: r . set_title_lines ( 2 )
    return r  # info: return r


# ====================================================
# SECTION: function light_row
# What it does: Cheap settings row: ONE label (title + small subtitle) in a box; suffix widgets appended by the caller. About half the widgets of an Adw.ActionRow — the Settings hub renders hundre
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def light_row(title: str, sub: str = "", tooltip: str | None = None):  # info: def light_row
    """Cheap settings row: ONE label (title + small subtitle) in a box; suffix widgets appended by the caller.
    About half the widgets of an Adw.ActionRow — the Settings hub renders hundreds of these."""
    row = Gtk.Box(spacing=8, margin_top=5, margin_bottom=5, margin_start=10, margin_end=6)  # info: set row
    l = Gtk.Label(xalign=0, hexpand=True, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR)  # info: set l
    set_row_text(l, title, sub)  # info: call set_row_text
    if tooltip:  # info: if tooltip :
        l.set_tooltip_text(redact(tooltip))  # info: l . set_tooltip_text ( redact ( tooltip )
    row.append(l)  # info: row . append ( l )
    return row, l  # info: return row , l


# ====================================================
# SECTION: function set_row_text
# What it does: set row text.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def set_row_text(l: Gtk.Label, title: str, sub: str):  # info: def set_row_text
    l.set_markup(f"{esc(redact(title))}\n<span size='small' alpha='75%'>{esc(redact(sub))}</span>")  # info: l . set_markup ( f" { esc (


# ====================================================
# SECTION: function boxed_list
# What it does: boxed list.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def boxed_list() -> Gtk.ListBox:  # info: def boxed_list
    lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)  # info: set lb
    lb.add_css_class("boxed-list")  # info: lb . add_css_class ( "boxed-list" )
    return lb  # info: return lb


# ====================================================
# SECTION: class RowList
# What it does: A boxed Gtk.ListBox of ActionRows keyed by id. Rows are rebuilt only when the key set changes; otherwise titles/subtitles are updated in place (no widget churn on the 5 s refresh).
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
class RowList:  # info: class RowList
    """A boxed Gtk.ListBox of ActionRows keyed by id. Rows are rebuilt only when the key set changes; otherwise
    titles/subtitles are updated in place (no widget churn on the 5 s refresh)."""

    def __init__(self, parent: Gtk.Box, link=None, empty="—", lines=2):  # info: def __init__
        self.lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)  # info: self . lb = Gtk . ListBox (
        self.lb.add_css_class("boxed-list")  # info: self . lb . add_css_class ( "boxed-list" )
        parent.append(self.lb)  # info: parent . append ( self . lb )
        self.link, self.empty, self.lines = link, empty, lines  # info: self . link , self . empty ,
        self.keys: list | None = None  # info: self . keys : list | None =
        self.rows: dict = {}  # info: self . rows : dict = { }

    def set(self, items: list[dict]):  # info: def set
        keys = [it["key"] for it in items] or ["__empty__"]  # info: set keys
        if keys != self.keys:  # info: if keys != self . keys :
            while (c := self.lb.get_first_child()) is not None:  # info: while ( c := self . lb .
                self.lb.remove(c)  # info: self . lb . remove ( c )
            self.rows = {}  # info: self . rows = { }
            if not items:  # info: if not items :
                self.lb.append(action_row(self.empty))  # info: self . lb . append ( action_row (
            for it in items:  # info: for it in items :
                r = action_row(it["title"], it.get("sub", ""), self.lines)  # info: set r
                if self.link and it.get("page") and Adw is not None:  # info: if self . link and it . get
                    b = Gtk.Button(label="Settings →", valign=Gtk.Align.CENTER, tooltip_text=f"Settings → {it['page']}")  # info: set b
                    b.add_css_class("flat")  # info: b . add_css_class ( "flat" )
                    b.connect("clicked", lambda _b, p=it["page"]: self.link(p))  # info: b . connect ( "clicked" , lambda _b
                    r.add_suffix(b)  # info: r . add_suffix ( b )
                self.lb.append(r)  # info: self . lb . append ( r )
                self.rows[it["key"]] = r  # info: self . rows [ it [ "key" ]
            self.keys = keys  # info: self . keys = keys
        elif Adw is not None:  # info: elif Adw is not None :
            for it in items:  # info: for it in items :
                r = self.rows[it["key"]]  # info: set r
                ti, su = redact(it["title"]), redact(it.get("sub", ""))  # info: ti , su = redact ( it [
                if r.get_title() != ti:  # info: if r . get_title ( ) != ti
                    r.set_title(ti)  # info: r . set_title ( ti )
                if r.get_subtitle() != su:  # info: if r . get_subtitle ( ) != su
                    r.set_subtitle(su)  # info: r . set_subtitle ( su )


# ====================================================
# SECTION: function widget_texts
# What it does: Every visible string in a widget tree (labels, entries, row titles/subtitles, tooltips, text views). Used by --check to prove no secret value is rendered.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def widget_texts(w) -> list[str]:  # info: def widget_texts
    """Every visible string in a widget tree (labels, entries, row titles/subtitles, tooltips, text views).
    Used by --check to prove no secret value is rendered."""
    out = []  # info: set out
    stack = [w]  # info: set stack
    while stack:  # info: while stack :
        x = stack.pop()  # info: set x
        for getter in ("get_label", "get_text", "get_title", "get_subtitle", "get_tooltip_text", "get_placeholder_text"):  # info: for getter in ( "get_label" , "get_text" ,
            fn = getattr(x, getter, None)  # info: set fn
            if fn is None:  # info: if fn is None :
                continue  # info: continue
            try:  # info: try :
                v = fn()  # info: set v
            except TypeError:  # info: except TypeError :
                continue  # info: continue
            if isinstance(v, str) and v:  # info: if isinstance ( v , str ) and
                out.append(v)  # info: out . append ( v )
        if isinstance(x, Gtk.TextView):  # info: if isinstance ( x , Gtk . TextView
            b = x.get_buffer()  # info: set b
            out.append(b.get_text(b.get_start_iter(), b.get_end_iter(), True))  # info: out . append ( b . get_text (
        c = x.get_first_child()  # info: set c
        while c is not None:  # info: while c is not None :
            stack.append(c)  # info: stack . append ( c )
            c = c.get_next_sibling()  # info: set c
        if isinstance(x, Gtk.Stack):  # lazily-hidden pages are still children; covered above
            pass  # info: pass
    return out  # info: return out
