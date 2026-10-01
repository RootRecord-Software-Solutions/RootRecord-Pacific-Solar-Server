# ==============================================================================
# FILE: Media/Voice/scripts/test_hawaiian_lexicon.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
# G3 port 2026-09-29 (g3-voice-ailog): copied verbatim from G1 old skills/kokoro/scripts/test_hawaiian_lexicon.py (source kept in place).
from hawaiian_lexicon import (  # info: from hawaiian_lexicon import (
    SPEAK_ENGLISH,  # info: SPEAK_ENGLISH ,
    fold_place_spellings,  # info: fold_place_spellings ,
    lexicon_entries,  # info: lexicon_entries ,
    pronounce_places,  # info: pronounce_places ,
)  # info: )
from speakable import speakable  # info: from speakable import speakable


# ====================================================
# SECTION: function test_kilauea_is_kill_ah_way_uh
# What it does: test kilauea is kill ah way uh.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_kilauea_is_kill_ah_way_uh():  # info: def test_kilauea_is_kill_ah_way_uh
    spoken = speakable("Kīlauea is not erupting.")  # info: set spoken
    assert "Kill ah way uh" in spoken  # info: assert "Kill ah way uh" in spoken
    assert "Kilauea" not in spoken  # info: assert "Kilauea" not in spoken
    assert "[Kīlauea]" not in spoken  # info: assert "[Kīlauea]" not in spoken


# ====================================================
# SECTION: function test_sentence_uses_english_syllables
# What it does: test sentence uses english syllables.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_sentence_uses_english_syllables():  # info: def test_sentence_uses_english_syllables
    spoken = speakable(  # info: set spoken
        "Kīlauea is not erupting in Hilo, Pāhoa, or Pāhala on Hawaiʻi."  # info: "Kīlauea is not erupting in Hilo, Pāhoa, or Pāhala on Hawaiʻi."
    )  # info: )
    assert "Kill ah way uh" in spoken  # info: assert "Kill ah way uh" in spoken
    assert "hee loh" in spoken  # info: assert "hee loh" in spoken
    assert "pah hoh ah" in spoken  # info: assert "pah hoh ah" in spoken
    assert "pah hah lah" in spoken  # info: assert "pah hah lah" in spoken
    assert "hahwye-ee" in spoken  # info: assert "hahwye-ee" in spoken


# ====================================================
# SECTION: function test_operator_ipa_tags_become_english
# What it does: test operator ipa tags become english.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_operator_ipa_tags_become_english():  # info: def test_operator_ipa_tags_become_english
    raw = (  # info: set raw
        "[Kīlauea](/kiː.lɐˈu.e.ɑ/) is not erupting in "  # info: "[Kīlauea](/kiː.lɐˈu.e.ɑ/) is not erupting in "
        "[Hilo](/ˈhi.lo/) on [Hawaiʻi](/həˈwɐi.ʔi/)."  # info: "[Hilo](/ˈhi.lo/) on [Hawaiʻi](/həˈwɐi.ʔi/)."
    )  # info: )
    spoken = speakable(raw)  # info: set spoken
    assert "Kill ah way uh" in spoken  # info: assert "Kill ah way uh" in spoken
    assert "hee loh" in spoken  # info: assert "hee loh" in spoken
    assert "hahwye-ee" in spoken  # info: assert "hahwye-ee" in spoken
    assert "](/" not in spoken  # info: assert "](/" not in spoken


# ====================================================
# SECTION: function test_kauai_is_kah_wah_ee
# What it does: test kauai is kah wah ee.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_kauai_is_kah_wah_ee():  # info: def test_kauai_is_kah_wah_ee
    spoken = speakable("Kauai County: Flood Watch.")  # info: set spoken
    assert "kah wah ee" in spoken  # info: assert "kah wah ee" in spoken
    assert "cow" not in spoken.lower()  # info: assert "cow" not in spoken . lower (


# ====================================================
# SECTION: function test_hst_keeps_standard_time
# What it does: test hst keeps standard time.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_hst_keeps_standard_time():  # info: def test_hst_keeps_standard_time
    spoken = speakable("as of 4:18 AM Hawaiian Standard Time")  # info: set spoken
    assert "Standard Time" in spoken  # info: assert "Standard Time" in spoken
    assert "hah wye uhn Standard" not in spoken  # info: assert "hah wye uhn Standard" not in spoken


# ====================================================
# SECTION: function test_decimal_depth_is_not_a_clock
# What it does: test decimal depth is not a clock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_decimal_depth_is_not_a_clock():  # info: def test_decimal_depth_is_not_a_clock
    spoken = speakable(  # info: set spoken
        "Depth 0.04 kilometers. Sep 17, 4:18 AM Hawaiian Standard Time."  # info: "Depth 0.04 kilometers. Sep 17, 4:18 AM Hawaiian Standard Time."
    )  # info: )
    assert "0.04" in spoken or "zero" in spoken.lower()  # info: assert "0.04" in spoken or "zero" in spoken
    assert "twelve four a.m. kilometers" not in spoken  # info: assert "twelve four a.m. kilometers" not in spoken
    assert "four eighteen a.m." in spoken  # info: assert "four eighteen a.m." in spoken


# ====================================================
# SECTION: function test_no_place_lexicon_golds
# What it does: test no place lexicon golds.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_no_place_lexicon_golds():  # info: def test_no_place_lexicon_golds
    assert lexicon_entries() == {}  # info: assert lexicon_entries ( ) == { }


# ====================================================
# SECTION: function test_fold_okina
# What it does: test fold okina.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_fold_okina():  # info: def test_fold_okina
    assert "Hawaii" in fold_place_spellings("Hawaiʻi")  # info: assert "Hawaii" in fold_place_spellings ( "Hawaiʻi" )
    assert "Kilauea" in fold_place_spellings("Kīlauea")  # info: assert "Kilauea" in fold_place_spellings ( "Kīlauea" )


# ====================================================
# SECTION: function test_pronounce_wraps_plain_names
# What it does: test pronounce wraps plain names.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_pronounce_wraps_plain_names():  # info: def test_pronounce_wraps_plain_names
    out = pronounce_places("Quake near Pahoa and Hilo.")  # info: set out
    assert "pah hoh ah" in out  # info: assert "pah hoh ah" in out
    assert "hee loh" in out  # info: assert "hee loh" in out


# ====================================================
# SECTION: function test_speak_english_has_kilauea
# What it does: test speak english has kilauea.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_speak_english_has_kilauea():  # info: def test_speak_english_has_kilauea
    assert SPEAK_ENGLISH["Kīlauea"] == "Kill ah way uh"  # info: assert SPEAK_ENGLISH [ "Kīlauea" ] == "Kill ah way uh"


# ====================================================
# SECTION: function test_date_time_not_eaten_as_clock
# What it does: test date time not eaten as clock.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_date_time_not_eaten_as_clock():  # info: def test_date_time_not_eaten_as_clock
    spoken = speakable("2026-09-16 19:04 HST")  # info: set spoken
    assert "September 16" in spoken  # info: assert "September 16" in spoken
    assert "seven four p.m." in spoken  # info: assert "seven four p.m." in spoken
    assert "2026-09-four" not in spoken  # info: assert "2026-09-four" not in spoken
    assert "four nineteen" not in spoken  # info: assert "four nineteen" not in spoken


# ====================================================
# SECTION: function test_morning_hint_forces_am
# What it does: test morning hint forces am.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_morning_hint_forces_am():  # info: def test_morning_hint_forces_am
    spoken = speakable("about 12 37 in the morning Hawaiian Standard Time")  # info: set spoken
    assert "twelve thirty seven a.m." in spoken  # info: assert "twelve thirty seven a.m." in spoken
    assert "p.m. in the morning" not in spoken  # info: assert "p.m. in the morning" not in spoken


# ====================================================
# SECTION: function test_speakable_idempotent_on_hst
# What it does: test speakable idempotent on hst.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def test_speakable_idempotent_on_hst():  # info: def test_speakable_idempotent_on_hst
    once = speakable("as of 4:18 AM Hawaiian Standard Time")  # info: set once
    twice = speakable(once)  # info: set twice
    assert once == twice  # info: assert once == twice
    assert "Hawaii Standard Time" in once  # info: assert "Hawaii Standard Time" in once
    assert "hah wye ee" not in once.lower() and "hahwye-ee" not in once.lower()  # info: assert the time phrase stays Hawaii Standard Time
