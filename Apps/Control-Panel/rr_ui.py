"""rr_ui.py — small shared GTK helpers for Root Monitor (moved out of rr_control_panel.py 2026-09-29).
Import only after gi.require_version(...) has run (rr_control_panel.py does that)."""
from __future__ import annotations

from gi.repository import Gio, GLib, Gtk, Pango

try:
    from gi.repository import Adw
except ImportError:  # pragma: no cover
    Adw = None


REDACT: list[str] = []   # known secret values (filled lazily by the panel); never printed


def redact(s: str) -> str:
    """Replace any known secret value inside a display string with <masked len N>."""
    if s and REDACT:
        for v in REDACT:
            if v in s:
                s = s.replace(v, f"<masked len {len(v)}>")
    return s


def lbl(text="", css=None, xalign=0.0, wrap=False, select=False, markup=False) -> Gtk.Label:
    w = Gtk.Label(xalign=xalign)
    (w.set_markup if markup else w.set_text)(text)
    if wrap:
        w.set_wrap(True)
        w.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    if select:
        w.set_selectable(True)
    for c in (css or "").split():
        w.add_css_class(c)
    return w


def esc(s) -> str:
    return GLib.markup_escape_text(str(s))


def badge_css(state: str) -> str:
    return {"PASS": "rr-pass", "WARN": "rr-warn", "FAIL": "rr-fail", "BLOCKED": "rr-fail",
            "VERIFY PENDING": "rr-warn"}.get(state, "dim-label")


def section(title: str) -> tuple[Gtk.Box, Gtk.Box]:
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    outer.append(lbl(title, "heading"))
    inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
    inner.add_css_class("card")
    inner.add_css_class("rr-card")
    outer.append(inner)
    return outer, inner


def spawn(argv: list[str], on_done=None, capture=False):
    """Start a child without blocking the UI; always reaped (wait/communicate async)."""
    flags = Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_MERGE if capture else Gio.SubprocessFlags.NONE
    proc = Gio.Subprocess.new(argv, flags)
    if capture:
        def fin(p, res):
            try:
                ok, out, _e = p.communicate_utf8_finish(res)
            except GLib.Error as e:
                out = f"error: {e.message}"
            if on_done:
                on_done(out or "", p.get_exit_status() if p.get_if_exited() else -1)
        proc.communicate_utf8_async(None, None, fin)
    else:
        proc.wait_async(None, lambda p, r: p.wait_finish(r))
    return proc


def action_row(title: str, subtitle: str = "", lines: int = 2):
    """Plain-text Adw.ActionRow (markup OFF, so file names / commands render literally)."""
    if Adw is None:
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        b.append(lbl(title))
        b.append(lbl(subtitle, "dim-label", wrap=True))
        return b
    r = Adw.ActionRow()
    r.set_use_markup(False)
    r.set_title(redact(title))
    r.set_subtitle(redact(subtitle))
    r.set_subtitle_lines(lines)
    r.set_title_lines(2)
    return r


def light_row(title: str, sub: str = "", tooltip: str | None = None):
    """Cheap settings row: ONE label (title + small subtitle) in a box; suffix widgets appended by the caller.
    About half the widgets of an Adw.ActionRow — the Settings hub renders hundreds of these."""
    row = Gtk.Box(spacing=8, margin_top=5, margin_bottom=5, margin_start=10, margin_end=6)
    l = Gtk.Label(xalign=0, hexpand=True, wrap=True, wrap_mode=Pango.WrapMode.WORD_CHAR)
    set_row_text(l, title, sub)
    if tooltip:
        l.set_tooltip_text(redact(tooltip))
    row.append(l)
    return row, l


def set_row_text(l: Gtk.Label, title: str, sub: str):
    l.set_markup(f"{esc(redact(title))}\n<span size='small' alpha='75%'>{esc(redact(sub))}</span>")


def boxed_list() -> Gtk.ListBox:
    lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
    lb.add_css_class("boxed-list")
    return lb


class RowList:
    """A boxed Gtk.ListBox of ActionRows keyed by id. Rows are rebuilt only when the key set changes; otherwise
    titles/subtitles are updated in place (no widget churn on the 5 s refresh)."""

    def __init__(self, parent: Gtk.Box, link=None, empty="—", lines=2):
        self.lb = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.lb.add_css_class("boxed-list")
        parent.append(self.lb)
        self.link, self.empty, self.lines = link, empty, lines
        self.keys: list | None = None
        self.rows: dict = {}

    def set(self, items: list[dict]):
        keys = [it["key"] for it in items] or ["__empty__"]
        if keys != self.keys:
            while (c := self.lb.get_first_child()) is not None:
                self.lb.remove(c)
            self.rows = {}
            if not items:
                self.lb.append(action_row(self.empty))
            for it in items:
                r = action_row(it["title"], it.get("sub", ""), self.lines)
                if self.link and it.get("page") and Adw is not None:
                    b = Gtk.Button(label="Settings →", valign=Gtk.Align.CENTER, tooltip_text=f"Settings → {it['page']}")
                    b.add_css_class("flat")
                    b.connect("clicked", lambda _b, p=it["page"]: self.link(p))
                    r.add_suffix(b)
                self.lb.append(r)
                self.rows[it["key"]] = r
            self.keys = keys
        elif Adw is not None:
            for it in items:
                r = self.rows[it["key"]]
                ti, su = redact(it["title"]), redact(it.get("sub", ""))
                if r.get_title() != ti:
                    r.set_title(ti)
                if r.get_subtitle() != su:
                    r.set_subtitle(su)


def widget_texts(w) -> list[str]:
    """Every visible string in a widget tree (labels, entries, row titles/subtitles, tooltips, text views).
    Used by --check to prove no secret value is rendered."""
    out = []
    stack = [w]
    while stack:
        x = stack.pop()
        for getter in ("get_label", "get_text", "get_title", "get_subtitle", "get_tooltip_text", "get_placeholder_text"):
            fn = getattr(x, getter, None)
            if fn is None:
                continue
            try:
                v = fn()
            except TypeError:
                continue
            if isinstance(v, str) and v:
                out.append(v)
        if isinstance(x, Gtk.TextView):
            b = x.get_buffer()
            out.append(b.get_text(b.get_start_iter(), b.get_end_iter(), True))
        c = x.get_first_child()
        while c is not None:
            stack.append(c)
            c = c.get_next_sibling()
        if isinstance(x, Gtk.Stack):  # lazily-hidden pages are still children; covered above
            pass
    return out
