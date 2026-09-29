"""Phrase-clip catalog: fixed 1–4 sentence texts from the automated reports, one entry per assigned persona.

Approved by Alexander 2026-09-29 ~04:00 HST as the one exception to "no stitching": clips are
pre-rendered with the SAME Kokoro voices/speeds and reused sentence-by-sentence by
voice_generate.py stitch; anything variable (numbers, names, values) is rendered live.
The G1 prebuilt chime clips / clip-stitch TTS are NOT used — every clip here is rendered fresh.

Persona follows speakers.KIND_AGENT. Slugs: lower_snake_case, unique per persona.
Sources name the G1 template the text comes from (old skills/…), or "G3" for new G3 templates.
"""
from __future__ import annotations

from speakable import spoken_clock

_FIXED = [
    # (persona, slug, text, kinds, source)
    ("Ava", "nws_report_intro", "NWS Hawaii Report.", ["nws", "weather"], "media/voice/plugins/nws_weather.py title line (time part live)"),
    ("Ava", "nws_by_county", "NWS Hawaii by county.", ["nws"], "weather/nws-hawaii/scripts/nws_hawaii.py"),
    ("Ava", "nws_no_active_alerts", "No active HI alerts from the API sample.", ["nws", "alerts"], "weather/nws-hawaii/scripts/nws_hawaii.py"),
    ("Ava", "official_no_hurricane_statement", "Honolulu National Weather Service has no local hurricane statement in effect.", ["official"], "weather/official-weather-media/scripts/official_weather_media.py"),
    ("Ava", "boot_all_systems_running", "All systems running.", ["boot"], "origin kokoro_tts _TOKEN_WORDS phrase_all_systems_running"),
    ("Ava", "boot_satellite_restored", "Satellite connection restored.", ["boot"], "origin kokoro_tts _TOKEN_WORDS satellite_connection"),
    ("Bruce", "solar_hourly_intro", "Hourly solar report.", ["solar", "hourly"], "origin kokoro_tts _TOKEN_WORDS phrase_hourly_solar"),
    ("Bruce", "solar_ecoflow_offline", "EcoFlow is offline.", ["solar"], "origin kokoro_tts _TOKEN_WORDS phrase_ecoflow_down"),
    ("Bruce", "remaining_intro", "Remaining tasks.", ["remaining"], "origin kokoro_tts _TOKEN_WORDS phrase_remaining_tasks"),
    ("Bruce", "system_intro", "System performance report.", ["system"], "G3 system_perf template"),
    ("Bruce", "system_outro", "End of system report.", ["system"], "G3 system_perf template"),
    ("Carly", "energy_ecoflow_offline", "EcoFlow is offline.", ["energy"], "origin kokoro_tts _TOKEN_WORDS phrase_ecoflow_down"),
    ("Carly", "quake_hi_intro", "Hawaii Earthquake Report.", ["earthquake"], "media/voice/plugins/earthquake_hawaii.py title line (time part live)"),
    ("Carly", "quake_hi_none", "No new Hawaii earthquakes since the last report.", ["earthquake"], "earthquakes/earthquake-hourly/scripts/earthquake_hourly.py"),
    ("Carly", "quake_global_none", "No new global earthquakes since the last report.", ["earthquake"], "earthquakes/earthquake-hourly/scripts/earthquake_hourly.py"),
    ("Carly", "kilauea_intro", "Kilauea Report.", ["kilauea"], "media/voice/plugins/kilauea_report.py title line (time part live)"),
    ("Carly", "kilauea_hvo_notice", "Here is the latest Hawaiian Volcano Observatory notice, unedited for honesty.", ["kilauea"], "media/voice/plugins/kilauea_report.py"),
    ("Carly", "hurricane_intro", "Hurricane global desk, Pacific Root Server.", ["hurricane"], "weather/hurricane-desk/scripts/hurricane_desk.py"),
    ("Carly", "hurricane_quiet", "Around the world right now, the tropical boards are quiet.", ["hurricane"], "weather/hurricane-desk/scripts/hurricane_desk.py"),
    ("Carly", "hurricane_outro", "Stay with NWS Honolulu for watches and warnings.", ["hurricane"], "weather/hurricane-desk/scripts/hurricane_desk.py"),
    # 2026-09-29 04:30 (g3-voice-reports2): fixed lines of the newly ported G3 report templates (voice_reports.py)
    ("Ava", "nws_forecast_today", "State forecast for today.", ["nws"], "G3 voice_reports nws_weather"),
    ("Ava", "nws_forecast_tonight", "State forecast for tonight.", ["nws"], "G3 voice_reports nws_weather"),
    ("Ava", "morning_intro", "Morning report.", ["morning"], "G3 voice_reports morning_report"),
    ("Ava", "midday_intro", "Midday report.", ["midday"], "G3 voice_reports midday_report"),
    ("Ava", "late_intro", "Late report.", ["late"], "G3 voice_reports late_report"),
    ("Ava", "rollup_outro", "End of report.", ["morning", "midday", "late"], "G3 voice_reports roll-ups"),
    ("Ava", "rollup_ecoflow_offline", "EcoFlow is offline.", ["morning", "midday", "late"], "G3 voice_reports roll-ups"),
    ("Carly", "energy_intro", "Energy desk report.", ["energy"], "G3 voice_reports energy_report"),
    ("Bruce", "remaining_none", "No open tasks on file.", ["remaining"], "G3 voice_reports remaining_tasks"),
]

# PROPOSED pronunciations (2026-09-29, g3-voice-reports2). No respelling found in G1/G2/Library; candidates are
# written from standard Hawaiian phonology (a=ah e=eh i=ee o=oh u=oo, au=ow, ʻokina = glottal stop / syllable
# break, kahakō = long vowel). Rendered for Alexander's listen list only: "proposed": True keeps them OUT of the
# stitcher and they are NOT in hawaiian_lexicon.SPEAK_ENGLISH until approved.
PROPOSED_PRONUNCIATION = [
    ("Kalākaua", "kah lah kow ah", "ka-LĀ-kau-a; ā long, au as in 'cow'"),
    ("Liliʻuokalani", "lee lee oo oh kah lah nee", "li-li-ʻu-o-ka-LA-ni; glottal stop before u"),
    ("Nuʻuanu", "noo oo ah noo", "nu-ʻu-A-nu; glottal stop between the two u"),
    ("Māhele", "mah heh leh", "MĀ-he-le; ā long"),
]


def chime_text(hour: int, minute: int) -> str:
    """Exact G1 chime sentence (media/voice/local_tts.build_time_announcement)."""
    return f"It's {spoken_clock(hour, minute)}.".replace("..", ".")  # G1 gave "p.m.." — same speech, cleaner text


def catalog() -> list[dict]:
    out = [{"persona": p, "slug": s, "text": t, "kinds": k, "source": src} for p, s, t, k, src in _FIXED]
    for h in range(24):
        for m in (0, 30):
            out.append({"persona": "Ava", "slug": f"chime_{h:02d}{m:02d}", "text": chime_text(h, m),
                        "kinds": ["chime"], "source": "media/hourly-chime + local_tts.build_time_announcement (:00/:30)"})
    for name, resp, _note in PROPOSED_PRONUNCIATION:
        slug = "proposed_" + name.lower().replace("ʻ", "").translate(str.maketrans("āēīōū", "aeiou"))
        out.append({"persona": "Ava", "slug": slug, "text": f"{name}.", "spoken": f"{resp}.", "kinds": [],
                    "source": "PROPOSED respelling (Hawaiian phonology)", "proposed": True})
    return out


if __name__ == "__main__":
    import json
    c = catalog()
    print(json.dumps({"total": len(c), "by_persona": {p: sum(1 for x in c if x["persona"] == p) for p in ("Ava", "Bruce", "Carly")}}))
