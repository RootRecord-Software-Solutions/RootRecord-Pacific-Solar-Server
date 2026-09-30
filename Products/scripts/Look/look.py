"""Look at live stills with the small vision model. llama3.2 still talks.

Moondream (~1.7 GB) captions USGS cam stills and NHC outlook charts.
It does not speak to people. Captions become LOOK notes in live facts.
"""
from __future__ import annotations

import logging
import re
import time
import urllib.request
from pathlib import Path

from apps.core import config

log = logging.getLogger("ava.look")

CACHE = config.DATA_DIR / "look"
UA = "AvaIvy/2.0 (https://avaivy.cloud; look)"
CACHE_S = 180

_LOOK = re.compile(
    r"\b(look|looking|cam|camera|still|picture|photo|screenshot|satellite|outlook|"
    r"nhc map|hurricane map|storm map|cone chart|crater|lava lake|v1cam|v2cam|v3cam|"
    r"pack screen|lcd|what does (it|that|the (cam|pack|sky|storm)) look)\b",
    re.I,
)
_KILAUEA = re.compile(r"\b(kilauea|kīlauea|volcano|lava|cam|camera|crater|halema|v1|v2|v3)\b", re.I)
_NHC = re.compile(r"\b(nhc|hurricane|outlook|satellite|cone|storm map|epac|cpac)\b", re.I)
_PACK = re.compile(r"\b(pack screen|ecoflow screen|lcd|display on the pack)\b", re.I)
_PANELS = re.compile(
    r"\b(panels?|solar panel|rear shed|energy desk|site cam|shed cam)\b",
    re.I,
)

USGS = (
    ("V1 West Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V1cam/images/M.jpg"),
    ("V2 North Halemaʻumaʻu", "https://volcanoes.usgs.gov/observatories/hvo/cams/V2cam/images/M.jpg"),
    ("V3 lava lake", "https://volcanoes.usgs.gov/observatories/hvo/cams/V3cam/images/M.jpg"),
)
NHC_FALLBACK = (
    "https://www.nhc.noaa.gov/xgtwo/resize/xgtwo_pac_2d0_w1920.png",
    "https://www.nhc.noaa.gov/xgtwo/resize/xgtwo_cpac_2d0_w1920.png",
)


def wants_look(text: str) -> bool:
    return bool(_LOOK.search(text or ""))


def _fetch(url: str, dest: Path) -> Path | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and (time.time() - dest.stat().st_mtime) < CACHE_S:
        return dest
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read()
        if not raw or len(raw) < 800:
            return dest if dest.is_file() else None
        dest.write_bytes(raw)
        return dest
    except Exception as e:
        log.info("look fetch miss %s: %s", dest.name, e)
        return dest if dest.is_file() else None


def _usgs(asked: str) -> list[tuple[str, Path]]:
    want = USGS
    low = (asked or "").lower()
    if "v1" in low and "v2" not in low and "v3" not in low:
        want = USGS[:1]
    elif "v2" in low:
        want = USGS[1:2]
    elif "v3" in low or "lake" in low:
        want = USGS[2:3]
    else:
        want = USGS[:1]  # one still unless they name another
    out = []
    for title, url in want:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:24]
        path = _fetch(url, CACHE / f"usgs-{slug}.jpg")
        if path:
            out.append((title, path))
    return out


def _nhc() -> list[tuple[str, Path]]:
    from apps.core.services import nhc_media

    files = []
    try:
        current = nhc_media.current_files()
        for slug in ("epac_2day", "cpac_2day", "xgtwo_pac_2d0_w1920", "xgtwo_cpac_2d0_w1920"):
            p = current.get(slug)
            if p and Path(p).is_file():
                files.append((slug, Path(p)))
        if not files:
            for p in sorted(nhc_media.media_current().glob("*.png"))[:2]:
                files.append((p.stem, p))
    except Exception:
        files = []
    if files:
        return files[:2]
    out = []
    for i, url in enumerate(NHC_FALLBACK[:1]):
        path = _fetch(url, CACHE / f"nhc-{i}.png")
        if path:
            out.append(("NHC EPAC 2-day outlook", path))
    return out


def _pack_screens() -> list[tuple[str, Path]]:
    from apps.core.services.data_layout import ecoflow_dir

    roots = (
        config.PUBLIC_MEDIA / "images" / "ecoflow",
        ecoflow_dir() / "screens",
    )
    found: list[tuple[str, Path]] = []
    for root in roots:
        if not root.is_dir():
            continue
        for p in sorted(root.glob("*.png")) + sorted(root.glob("*.jpg")):
            found.append((p.stem, p))
            if len(found) >= 2:
                return found
    return found


def _panels() -> list[tuple[str, Path]]:
    root = Path.home() / ".ollama" / "skills" / "panels-cam" / "store" / "frames"
    if not root.is_dir():
        return []
    jpgs = sorted(root.glob("ch*.jpg"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jpgs:
        return []
    return [("Rear Shed panels", jpgs[0])]


def _pick(asked: str) -> list[tuple[str, Path]]:
    if _PANELS.search(asked or ""):
        shots = _panels()
        if shots:
            return shots
    if _PACK.search(asked or ""):
        shots = _pack_screens()
        return shots
    if _NHC.search(asked or "") and not _KILAUEA.search(asked or ""):
        return _nhc()
    if _KILAUEA.search(asked or "") or wants_look(asked):
        if _NHC.search(asked or ""):
            return _nhc()[:1] + _usgs(asked)[:1]
        if _PANELS.search(asked or ""):
            return _panels()[:1] + _usgs(asked)[:1]
        return _usgs(asked)
    return []


def notes_sync(asked: str) -> str:
    if not wants_look(asked):
        return ""
    picks = _pick(asked)
    if _PACK.search(asked or "") and not picks:
        return "LOOK: no pack screen photo on this disk."
    if not picks:
        return "LOOK: no still on hand for that."
    from apps.core.services import ollama as ollama_svc

    lines = []
    for title, path in picks[:2]:
        prompt = (
            f"This is a live still: {title}. "
            "Describe only what is visible in four short factual sentences. "
            "If a number or name is not on the still, omit it. "
            "If it is dark, cloudy, or a map, say that."
        )
        cap = ollama_svc.look_sync(prompt, [path], timeout=90)
        if cap:
            lines.append(f"LOOK ({title}): {cap.strip()[:700]}")
        else:
            lines.append(f"LOOK ({title}): still saved, looker quiet.")
    return "\n".join(lines)


async def notes(asked: str) -> str:
    import asyncio

    text = await asyncio.to_thread(notes_sync, asked or "")
    if text and "LOOK (" in text and "looker quiet" not in text:
        try:
            from apps.core.services import voice_events

            await voice_events.announce("phrase_looker", cooldown_s=120)
        except Exception as e:
            log.debug("looker voice skip: %s", e)
    return text
