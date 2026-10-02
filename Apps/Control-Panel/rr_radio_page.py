# ==============================================================================
# FILE: Apps/Control-Panel/rr_radio_page.py
# What this file is: Root Monitor page. Read-only ML1 lineup. Does not restart the station.
# Kind: python
# ==============================================================================
"""ML1 playlist page. Reads report files over SSH. Never restarts the radio."""
from __future__ import annotations

import json
from datetime import datetime

from rr_radio_lineup import TZ, order_rows
from rr_ui import esc, lbl, section, spawn

REMOTE = r"""
import json, subprocess
from pathlib import Path
d = Path("/home/ubuntu/rootrecord-radio/audio/reports")
rows = []
for p in sorted(d.iterdir()):
    if not p.is_file() or "_current" not in p.name:
        continue
    dur = 0.0
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
            text=True, timeout=15)
        dur = float(out.strip() or 0)
    except Exception:
        dur = 0.0
    st = p.stat()
    rows.append({"file": p.name, "bytes": st.st_size, "mtime": st.st_mtime, "duration": round(dur, 1)})
print(json.dumps(rows))
"""


def _fmt_clock(seconds: float) -> str:
    whole = int(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


def _fmt_mtime(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, TZ).strftime("%H:%M:%S")


class RadioPage:
    def b_radio(self, box):
        box.append(section("ML1 playlist"))
        self.radio_note = lbl("Reading the live report files. This does not restart the station.", "dim-label", wrap=True)
        box.append(self.radio_note)
        self.radio_list = lbl("", wrap=True, select=True, markup=True)
        box.append(self.radio_list)
        self._radio_proc = None
        self._radio_at = 0.0
        self._radio_text = ""

    def r_radio(self):
        import time
        if self._radio_proc is not None:
            return
        if self._radio_text and time.time() - self._radio_at < 30:
            return
        self._radio_proc = spawn(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "ml1", "python3", "-c", REMOTE],
            on_done=self._radio_done,
            capture=True,
        )

    def _radio_done(self, out, rc):
        import time
        self._radio_proc = None
        self._radio_at = time.time()
        if rc != 0 or not out.strip().startswith("["):
            self.radio_note.set_text("Could not read ML1 report files. Station was not touched.")
            self.radio_list.set_markup(esc(out.strip()[-400:]))
            return
        try:
            rows = json.loads(out)
        except json.JSONDecodeError:
            self.radio_note.set_text("ML1 returned a bad list. Station was not touched.")
            return
        now = datetime.now(TZ)
        lineup, held = order_rows(rows, now)
        from rr_radio_lineup import next_boundary
        slot = next_boundary(now)
        self.radio_note.set_text(
            f"Next cycle {slot.strftime('%H:%M')} HST. Locals first, news only with time left. "
            "A file updated after the last boundary waits for this cycle. Station not restarted."
        )
        lines = []
        for i, item in enumerate(lineup, 1):
            mark = "  cut at the half hour" if item.get("cut") else ""
            lines.append(
                f"{i:2}. {item['title']}  {_fmt_clock(item['starts_sec'])}  "
                f"{_fmt_clock(item.get('duration') or 0)}  updated {_fmt_mtime(item.get('mtime') or 0)}"
                f"{mark}"
            )
        if held:
            lines.append("")
            lines.append("Not this cycle")
            for item in held:
                lines.append(f"    {item['title']}  updated {_fmt_mtime(item.get('mtime') or 0)}")
        self._radio_text = "\n".join(lines)
        self.radio_list.set_markup(f"<tt>{esc(self._radio_text)}</tt>")
