# ==============================================================================
# FILE: Media/Voice/scripts/clip_catalog.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Phrase-clip catalog: fixed 1–4 sentence texts from the automated reports, one entry per assigned persona.

Approved by Alexander 2026-09-29 ~04:00 HST as the one exception to "no stitching": clips are
pre-rendered with the SAME Kokoro voices/speeds and reused sentence-by-sentence by
voice_generate.py stitch; anything variable (numbers, names, values) is rendered live.
The G1 prebuilt chime clips / clip-stitch TTS are NOT used — every clip here is rendered fresh.

Persona follows speakers.KIND_AGENT. Slugs: lower_snake_case, unique per persona.
Sources name the G1 template the text comes from (old skills/…), or "G3" for new G3 templates.
"""
from __future__ import annotations  # info: from __future__ import annotations

# ====================================================
# SECTION: _FIXED
# What it does: Set _FIXED.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
_FIXED = [  # info: set _FIXED
    # (persona, slug, text, kinds, source)
    ("Ava", "nws_report_intro", "NWS Hawaii Report.", ["nws", "weather"], "media/voice/plugins/nws_weather.py title line (time part live)"),  # info: call (
    ("Ava", "nws_by_county", "NWS Hawaii by county.", ["nws"], "weather/nws-hawaii/scripts/nws_hawaii.py"),  # info: call (
    ("Ava", "nws_no_active_alerts", "No active HI alerts from the API sample.", ["nws", "alerts"], "weather/nws-hawaii/scripts/nws_hawaii.py"),  # info: call (
    ("Ava", "official_no_hurricane_statement", "Honolulu National Weather Service has no local hurricane statement in effect.", ["official"], "weather/official-weather-media/scripts/official_weather_media.py"),  # info: call (
    ("Ava", "boot_all_systems_running", "All systems running.", ["boot"], "origin kokoro_tts _TOKEN_WORDS phrase_all_systems_running"),  # info: call (
    ("Ava", "boot_satellite_restored", "Satellite connection restored.", ["boot"], "origin kokoro_tts _TOKEN_WORDS satellite_connection"),  # info: call (
    ("Bruce", "solar_hourly_intro", "Hourly solar report.", ["solar", "hourly"], "origin kokoro_tts _TOKEN_WORDS phrase_hourly_solar"),  # info: call (
    ("Bruce", "solar_ecoflow_offline", "EcoFlow is offline.", ["solar"], "origin kokoro_tts _TOKEN_WORDS phrase_ecoflow_down"),  # info: call (
    ("Bruce", "remaining_intro", "Remaining tasks.", ["remaining"], "origin kokoro_tts _TOKEN_WORDS phrase_remaining_tasks"),  # info: call (
    ("Bruce", "system_intro", "System performance report.", ["system"], "G3 system_perf template"),  # info: call (
    ("Bruce", "system_outro", "End of system report.", ["system"], "G3 system_perf template"),  # info: call (
    ("Carly", "energy_ecoflow_offline", "EcoFlow is offline.", ["energy"], "origin kokoro_tts _TOKEN_WORDS phrase_ecoflow_down"),  # info: call (
    ("Carly", "quake_hi_intro", "Hawaii Earthquake Report.", ["earthquake"], "media/voice/plugins/earthquake_hawaii.py title line (time part live)"),  # info: call (
    ("Carly", "quake_hi_none", "No new Hawaii earthquakes since the last report.", ["earthquake"], "earthquakes/earthquake-hourly/scripts/earthquake_hourly.py"),  # info: call (
    ("Carly", "quake_global_none", "No new global earthquakes since the last report.", ["earthquake"], "earthquakes/earthquake-hourly/scripts/earthquake_hourly.py"),  # info: call (
    ("Carly", "kilauea_intro", "Kilauea Report.", ["kilauea"], "media/voice/plugins/kilauea_report.py title line (time part live)"),  # info: call (
    ("Carly", "kilauea_hvo_notice", "Here is the latest Hawaiian Volcano Observatory notice, unedited for honesty.", ["kilauea"], "media/voice/plugins/kilauea_report.py"),  # info: call (
    ("Carly", "hurricane_intro", "Hurricane global desk, Pacific Root Server.", ["hurricane"], "weather/hurricane-desk/scripts/hurricane_desk.py"),  # info: call (
    ("Carly", "hurricane_quiet", "Around the world right now, the tropical boards are quiet.", ["hurricane"], "weather/hurricane-desk/scripts/hurricane_desk.py"),  # info: call (
    ("Carly", "hurricane_outro", "Stay with NWS Honolulu for watches and warnings.", ["hurricane"], "weather/hurricane-desk/scripts/hurricane_desk.py"),  # info: call (
    # 2026-09-29 04:30 (g3-voice-reports2): fixed lines of the newly ported G3 report templates (voice_reports.py)
    ("Ava", "nws_forecast_today", "State forecast for today.", ["nws"], "G3 voice_reports nws_weather"),  # info: call (
    ("Ava", "nws_forecast_tonight", "State forecast for tonight.", ["nws"], "G3 voice_reports nws_weather"),  # info: call (
    ("Ava", "morning_intro", "Morning report.", ["morning"], "G3 voice_reports morning_report"),  # info: call (
    ("Ava", "midday_intro", "Midday report.", ["midday"], "G3 voice_reports midday_report"),  # info: call (
    ("Ava", "late_intro", "Late report.", ["late"], "G3 voice_reports late_report"),  # info: call (
    ("Ava", "rollup_outro", "End of report.", ["morning", "midday", "late"], "G3 voice_reports roll-ups"),  # info: call (
    ("Ava", "rollup_ecoflow_offline", "EcoFlow is offline.", ["morning", "midday", "late"], "G3 voice_reports roll-ups"),  # info: call (
    ("Carly", "energy_intro", "Energy desk report.", ["energy"], "G3 voice_reports energy_report"),  # info: call (
    ("Bruce", "remaining_none", "No open tasks on file.", ["remaining"], "G3 voice_reports remaining_tasks"),  # info: call (
]  # info: ]

# PROPOSED pronunciations (2026-09-29, g3-voice-reports2). No respelling found in G1/G2/Library; candidates are
# written from standard Hawaiian phonology (a=ah e=eh i=ee o=oh u=oo, au=ow, ʻokina = glottal stop / syllable
# break, kahakō = long vowel). Rendered for Alexander's listen list only: "proposed": True keeps them OUT of the
# stitcher and they are NOT in hawaiian_lexicon.SPEAK_ENGLISH until approved.
# ====================================================
# SECTION: PROPOSED_PRONUNCIATION
# What it does: Set PROPOSED_PRONUNCIATION.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
PROPOSED_PRONUNCIATION = [  # info: set PROPOSED_PRONUNCIATION
    ("Kalākaua", "kah lah kow ah", "ka-LĀ-kau-a; ā long, au as in 'cow'"),  # info: call (
    ("Liliʻuokalani", "lee lee oo oh kah lah nee", "li-li-ʻu-o-ka-LA-ni; glottal stop before u"),  # info: call (
    ("Nuʻuanu", "noo oo ah noo", "nu-ʻu-A-nu; glottal stop between the two u"),  # info: call (
    ("Māhele", "mah heh leh", "MĀ-he-le; ā long"),  # info: call (
    # B variant from an existing source: misaki us_gold.json (the Kokoro G2P's own lexicon, G1 venv) has
    # Liliuokalani = lIlˌiəwˌɑkəlˈɑni (English-style). Rendered unrespelled so Alexander can compare A vs B.
    ("Liliʻuokalani", "Liliuokalani", "B: misaki us_gold English IPA lIlˌiəwˌɑkəlˈɑni", "_b_misaki"),  # info: call (
    # B for Māhele: the G2P reads A's final "leh" as "lay" (lˈA). Inline phonemes (misaki [word](/ipa/) syntax),
    # from Wiktionary /maˈhe.le/ [məˈhɛ.lɛ] (G1 state/store/hawaiian-dictionary) with the kahakō long first vowel.
    ("Māhele", "[Māhele](/mˌɑhˈɛlɛ/)", "B: inline IPA mˌɑhˈɛlɛ", "_b_ipa"),  # info: call (
]  # info: ]


# ====================================================
# SECTION: function chime_text
# What it does: :00 and :30 chime sentence from hourly_chimes.py. Playback uses the prebuilt wav.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def chime_text(hour: int, minute: int) -> str:  # info: def chime_text
    """Chime sentence for :00 and :30. Playback copies the prebuilt wav."""  # info: """Chime sentence for :00 and :30. Playback copies the prebuilt wav."""
    from hourly_chimes import chime_sentence  # info: from hourly_chimes import chime_sentence
    return chime_sentence(int(hour), int(minute))  # info: return chime_sentence ( int ( hour ) , int ( minute ) )


# ====================================================
# SECTION: function catalog
# What it does: catalog.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def catalog() -> list[dict]:  # info: def catalog
    out = [{"persona": p, "slug": s, "text": t, "kinds": k, "source": src} for p, s, t, k, src in _FIXED]  # info: set out
    for name, resp, _note, *suffix in PROPOSED_PRONUNCIATION:  # info: for name , resp , _note , *
        slug = "proposed_" + name.lower().replace("ʻ", "").translate(str.maketrans("āēīōū", "aeiou")) + "".join(suffix)  # info: set slug
        out.append({"persona": "Ava", "slug": slug, "text": f"{name}.", "spoken": f"{resp}.", "kinds": [],  # info: out . append ( { "persona" : "Ava"
                    "source": "PROPOSED respelling (Hawaiian phonology)", "proposed": True})  # info: "source" : "PROPOSED respelling (Hawaiian phonology)" , "proposed" : True }
    return out  # info: return out


if __name__ == "__main__":  # info: if __name__ == "__main__" :
    import json  # info: import json
    c = catalog()  # info: set c
    print(json.dumps({"total": len(c), "by_persona": {p: sum(1 for x in c if x["persona"] == p) for p in ("Ava", "Bruce", "Carly")}}))  # info: call print
