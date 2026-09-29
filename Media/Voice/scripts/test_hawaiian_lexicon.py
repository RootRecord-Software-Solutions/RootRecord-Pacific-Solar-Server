# G3 port 2026-09-29 (g3-voice-ailog): copied verbatim from G1 old skills/kokoro/scripts/test_hawaiian_lexicon.py (source kept in place).
from hawaiian_lexicon import (
    SPEAK_ENGLISH,
    fold_place_spellings,
    lexicon_entries,
    pronounce_places,
)
from speakable import speakable


def test_kilauea_is_kill_ah_way_uh():
    spoken = speakable("Kīlauea is not erupting.")
    assert "Kill ah way uh" in spoken
    assert "Kilauea" not in spoken
    assert "[Kīlauea]" not in spoken


def test_sentence_uses_english_syllables():
    spoken = speakable(
        "Kīlauea is not erupting in Hilo, Pāhoa, or Pāhala on Hawaiʻi."
    )
    assert "Kill ah way uh" in spoken
    assert "hee loh" in spoken
    assert "pah hoh ah" in spoken
    assert "pah hah lah" in spoken
    assert "hah wye ee" in spoken


def test_operator_ipa_tags_become_english():
    raw = (
        "[Kīlauea](/kiː.lɐˈu.e.ɑ/) is not erupting in "
        "[Hilo](/ˈhi.lo/) on [Hawaiʻi](/həˈwɐi.ʔi/)."
    )
    spoken = speakable(raw)
    assert "Kill ah way uh" in spoken
    assert "hee loh" in spoken
    assert "hah wye ee" in spoken
    assert "](/" not in spoken


def test_kauai_is_kah_wah_ee():
    spoken = speakable("Kauai County: Flood Watch.")
    assert "kah wah ee" in spoken
    assert "cow" not in spoken.lower()


def test_hst_keeps_standard_time():
    spoken = speakable("as of 4:18 AM Hawaiian Standard Time")
    assert "Standard Time" in spoken
    assert "hah wye uhn Standard" not in spoken


def test_decimal_depth_is_not_a_clock():
    spoken = speakable(
        "Depth 0.04 kilometers. Sep 17, 4:18 AM Hawaiian Standard Time."
    )
    assert "0.04" in spoken or "zero" in spoken.lower()
    assert "twelve four a.m. kilometers" not in spoken
    assert "four eighteen a.m." in spoken


def test_no_place_lexicon_golds():
    assert lexicon_entries() == {}


def test_fold_okina():
    assert "Hawaii" in fold_place_spellings("Hawaiʻi")
    assert "Kilauea" in fold_place_spellings("Kīlauea")


def test_pronounce_wraps_plain_names():
    out = pronounce_places("Quake near Pahoa and Hilo.")
    assert "pah hoh ah" in out
    assert "hee loh" in out


def test_speak_english_has_kilauea():
    assert SPEAK_ENGLISH["Kīlauea"] == "Kill ah way uh"


def test_date_time_not_eaten_as_clock():
    spoken = speakable("2026-09-16 19:04 HST")
    assert "September 16" in spoken
    assert "seven four p.m." in spoken
    assert "2026-09-four" not in spoken
    assert "four nineteen" not in spoken


def test_morning_hint_forces_am():
    spoken = speakable("about 12 37 in the morning Hawaiian Standard Time")
    assert "twelve thirty seven a.m." in spoken
    assert "p.m. in the morning" not in spoken


def test_speakable_idempotent_on_hst():
    once = speakable("as of 4:18 AM Hawaiian Standard Time")
    twice = speakable(once)
    assert once == twice
    assert "Hawaii Standard Time" in once
    assert "hah wye ee" not in once.lower()
