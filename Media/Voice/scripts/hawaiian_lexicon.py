# ==============================================================================
# FILE: Media/Voice/scripts/hawaiian_lexicon.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
# G3 port 2026-09-29 (g3-voice-ailog): copied verbatim from G1 old skills/kokoro/scripts/hawaiian_lexicon.py (source kept in place).
"""Hawaiian / local place IPA for Kokoro via Misaki [Name](/ipa/) tags.

Source: operator IPA list. Glottal ʔ is stripped before speak — Misaki maps ʔ→t.
Dot syllable breaks and length marks stay; Kokoro vocab accepts them.
"""

from __future__ import annotations  # info: from __future__ import annotations

import re  # info: import re

# Operator IPA (with ʔ). Do not feed ʔ to Kokoro — use kokoro_ipa().
# ====================================================
# SECTION: PLACE_IPA
# What it does: Set PLACE_IPA.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
PLACE_IPA: dict[str, str] = {  # info: set PLACE_IPA
    # Islands
    "Hawaiʻi": "həˈwɐi.ʔi",  # info: "Hawaiʻi" : "həˈwɐi.ʔi" ,
    "Hawaiian": "həˈwɐi.ən",  # info: "Hawaiian" : "həˈwɐi.ən" ,
    "Oʻahu": "oˈʔɑ.hu",  # info: "Oʻahu" : "oˈʔɑ.hu" ,
    "Maui": "ˈmɐu.i",  # info: "Maui" : "ˈmɐu.i" ,
    "Kauaʻi": "kɐuˈɑ.ʔi",  # info: "Kauaʻi" : "kɐuˈɑ.ʔi" ,
    "Molokaʻi": "moloˈkɑ.ʔi",  # info: "Molokaʻi" : "moloˈkɑ.ʔi" ,
    "Lānaʻi": "lɑːˈnɑ.ʔi",  # info: "Lānaʻi" : "lɑːˈnɑ.ʔi" ,
    "Niʻihau": "niːˈi.hɐu",  # info: "Niʻihau" : "niːˈi.hɐu" ,
    "Kahoʻolawe": "kɑ.ho.ʔoˈlɑ.ve",  # info: "Kahoʻolawe" : "kɑ.ho.ʔoˈlɑ.ve" ,
    # Volcanoes / mountains
    "Kīlauea": "kiː.lɐˈu.e.ɑ",  # info: "Kīlauea" : "kiː.lɐˈu.e.ɑ" ,
    "Mauna Loa": "ˈmɐu.nə ˈlo.ə",  # info: "Mauna Loa" : "ˈmɐu.nə ˈlo.ə" ,
    "Mauna Kea": "ˈmɐu.nə ˈke.ə",  # info: "Mauna Kea" : "ˈmɐu.nə ˈke.ə" ,
    "Haleakalā": "hɑ.le.ɑ.kɑˈlɑː",  # info: "Haleakalā" : "hɑ.le.ɑ.kɑˈlɑː" ,
    "Hualālai": "hu.ɑˈlɑː.lɑi",  # info: "Hualālai" : "hu.ɑˈlɑː.lɑi" ,
    "Halemaʻumaʻu": "hɑ.le.mɐˈu.mɐ.ʔu",  # info: "Halemaʻumaʻu" : "hɑ.le.mɐˈu.mɐ.ʔu" ,
    # Hawaiʻi County
    "Hilo": "ˈhi.lo",  # info: "Hilo" : "ˈhi.lo" ,
    "Pāhala": "pɑːˈhɑ.lə",  # info: "Pāhala" : "pɑːˈhɑ.lə" ,
    "Pāhoa": "pɑːˈho.ə",  # info: "Pāhoa" : "pɑːˈho.ə" ,
    "Kailua-Kona": "kɐiˈlu.ə ˈko.nə",  # info: "Kailua-Kona" : "kɐiˈlu.ə ˈko.nə" ,
    "Kona": "ˈko.nə",  # info: "Kona" : "ˈko.nə" ,
    "Waikoloa": "wɐi.koˈlo.ə",  # info: "Waikoloa" : "wɐi.koˈlo.ə" ,
    "Honokaʻa": "honoˈkɑ.ʔɑ",  # info: "Honokaʻa" : "honoˈkɑ.ʔɑ" ,
    "Waimea": "wɐiˈme.ə",  # info: "Waimea" : "wɐiˈme.ə" ,
    "Keaʻau": "ke.ɑˈʔɐu",  # info: "Keaʻau" : "ke.ɑˈʔɐu" ,
    "Hāwī": "ˈhɑː.vi",  # info: "Hāwī" : "ˈhɑː.vi" ,
    "Kapaʻau": "kɑˈpɑ.ʔɐu",  # info: "Kapaʻau" : "kɑˈpɑ.ʔɐu" ,
    "Kealakekua": "ke.ɑ.lɑ.keˈku.ə",  # info: "Kealakekua" : "ke.ɑ.lɑ.keˈku.ə" ,
    "Hōnaunau-Nāpōʻopoʻo": "hoː.nɑuˈnɑu nɑːˈpoː.ʔo.poː.ʔo",  # info: "Hōnaunau-Nāpōʻopoʻo" : "hoː.nɑuˈnɑu nɑːˈpoː.ʔo.poː.ʔo" ,
    "Hōnaunau": "hoː.nɑuˈnɑu",  # info: "Hōnaunau" : "hoː.nɑuˈnɑu" ,
    "Nāpōʻopoʻo": "nɑːˈpoː.ʔo.poː.ʔo",  # info: "Nāpōʻopoʻo" : "nɑːˈpoː.ʔo.poː.ʔo" ,
    "Captain Cook": "ˈkæp.tən kʊk",  # info: "Captain Cook" : "ˈkæp.tən kʊk" ,
    "Mountain View": "ˈmaʊn.tən vjuː",  # info: "Mountain View" : "ˈmaʊn.tən vjuː" ,
    "Hawaiian Paradise Park": "həˈwɐi.ən ˈpæɹ.ə.daɪs pɑɹk",  # info: "Hawaiian Paradise Park" : "həˈwɐi.ən ˈpæɹ.ə.daɪs pɑɹk" ,
    "Hawaiian Ocean View": "həˈwɐi.ən ˈoʊ.ʃən vjuː",  # info: "Hawaiian Ocean View" : "həˈwɐi.ən ˈoʊ.ʃən vjuː" ,
    "Ainaloa": "ɑi.nɑˈlo.ə",  # info: "Ainaloa" : "ɑi.nɑˈlo.ə" ,
    "Kurtistown": "ˈkɝː.tɪs.taʊn",  # info: "Kurtistown" : "ˈkɝː.tɪs.taʊn" ,
    "Paukaa": "pɑuˈkɑ.ə",  # info: "Paukaa" : "pɑuˈkɑ.ə" ,
    "Pepeekeo": "pe.pe.eˈke.o",  # info: "Pepeekeo" : "pe.pe.eˈke.o" ,
    "Laupāhoehoe": "lɑu.pɑː.hoeˈhoe",  # info: "Laupāhoehoe" : "lɑu.pɑː.hoeˈhoe" ,
    "Naalehu": "nɑːˈʔɑ.le.hu",  # info: "Naalehu" : "nɑːˈʔɑ.le.hu" ,
    "Nāʻālehu": "nɑːˈʔɑ.le.hu",  # info: "Nāʻālehu" : "nɑːˈʔɑ.le.hu" ,
    "Volcano": "vɒlˈkeɪ.noʊ",  # info: "Volcano" : "vɒlˈkeɪ.noʊ" ,
    "Puna": "ˈpu.nɑ",  # info: "Puna" : "ˈpu.nɑ" ,
    "Kaʻū": "kɑˈʔuː",  # info: "Kaʻū" : "kɑˈʔuː" ,
    "Kohala": "koˈhɑ.lə",  # info: "Kohala" : "koˈhɑ.lə" ,
    "Hāmākua": "hɑːˈmɑː.ku.ə",  # info: "Hāmākua" : "hɑːˈmɑː.ku.ə" ,
    # Oʻahu
    "Honolulu": "honoˈlu.lu",  # info: "Honolulu" : "honoˈlu.lu" ,
    "Waikīkī": "wɐi.kiːˈkiː",  # info: "Waikīkī" : "wɐi.kiːˈkiː" ,
    "Kailua": "kɐiˈlu.ə",  # info: "Kailua" : "kɐiˈlu.ə" ,
    "Kāneʻohe": "kɑː.neˈʔo.he",  # info: "Kāneʻohe" : "kɑː.neˈʔo.he" ,
    "Pearl City": "pɝːl ˈsɪ.ti",  # info: "Pearl City" : "pɝːl ˈsɪ.ti" ,
    "Waipahu": "wɐiˈpɑ.hu",  # info: "Waipahu" : "wɐiˈpɑ.hu" ,
    "Kapolei": "kɑ.poˈlei",  # info: "Kapolei" : "kɑ.poˈlei" ,
    "ʻEwa Beach": "ˈʔe.vɑ biːtʃ",  # info: "ʻEwa Beach" : "ˈʔe.vɑ biːtʃ" ,
    "ʻEwa Gentry": "ˈʔe.vɑ ˈdʒen.tɹi",  # info: "ʻEwa Gentry" : "ˈʔe.vɑ ˈdʒen.tɹi" ,
    "ʻEwa": "ˈʔe.vɑ",  # info: "ʻEwa" : "ˈʔe.vɑ" ,
    "Mililani": "mi.liˈlɑ.ni",  # info: "Mililani" : "mi.liˈlɑ.ni" ,
    "Makakilo": "mɑ.kɑˈki.lo",  # info: "Makakilo" : "mɑ.kɑˈki.lo" ,
    "Wahiawā": "wɑ.hi.ɑˈwɑː",  # info: "Wahiawā" : "wɑ.hi.ɑˈwɑː" ,
    "Waiʻanae": "wɐiˈɑ.nɑe",  # info: "Waiʻanae" : "wɐiˈɑ.nɑe" ,
    "Nānākuli": "nɑː.nɑːˈku.li",  # info: "Nānākuli" : "nɑː.nɑːˈku.li" ,
    "Haleʻiwa": "hɑ.leˈi.vɑ",  # info: "Haleʻiwa" : "hɑ.leˈi.vɑ" ,
    "Lāʻie": "lɑːˈʔi.e",  # info: "Lāʻie" : "lɑːˈʔi.e" ,
    "Hauʻula": "hɑuˈʔu.lə",  # info: "Hauʻula" : "hɑuˈʔu.lə" ,
    "Kahuku": "kɑˈhu.ku",  # info: "Kahuku" : "kɑˈhu.ku" ,
    "Pūpūkea": "puː.puːˈke.ə",  # info: "Pūpūkea" : "puː.puːˈke.ə" ,
    "Aiea": "ɑiˈe.ə",  # info: "Aiea" : "ɑiˈe.ə" ,
    "Ahuimanu": "ɑ.hu.iˈmɑ.nu",  # info: "Ahuimanu" : "ɑ.hu.iˈmɑ.nu" ,
    "Heʻeia": "heˈʔei.ə",  # info: "Heʻeia" : "heˈʔei.ə" ,
    "Kahaluʻu": "kɑ.hɑˈlu.ʔu",  # info: "Kahaluʻu" : "kɑ.hɑˈlu.ʔu" ,
    # Maui County
    "Kahului": "kɑ.huˈlu.i",  # info: "Kahului" : "kɑ.huˈlu.i" ,
    "Lāhainā": "lɑːˈhɐi.nɑː",  # info: "Lāhainā" : "lɑːˈhɐi.nɑː" ,
    "Kīhei": "kiːˈhei",  # info: "Kīhei" : "kiːˈhei" ,
    "Wailuku": "wɐiˈlu.ku",  # info: "Wailuku" : "wɐiˈlu.ku" ,
    "Makawao": "mɑ.kɑˈwɐu",  # info: "Makawao" : "mɑ.kɑˈwɐu" ,
    "Hāna": "ˈhɑː.nɑ",  # info: "Hāna" : "ˈhɑː.nɑ" ,
    "Pāʻia": "pɑːˈʔi.ɑ",  # info: "Pāʻia" : "pɑːˈʔi.ɑ" ,
    "Pukalani": "pu.kɑˈlɑ.ni",  # info: "Pukalani" : "pu.kɑˈlɑ.ni" ,
    "Haʻikū-Pauwela": "hɑˈi.kuː pɑuˈwe.lə",  # info: "Haʻikū-Pauwela" : "hɑˈi.kuː pɑuˈwe.lə" ,
    "Nāpili-Honokōwai": "nɑːˈpi.li honoˈkoː.wɐi",  # info: "Nāpili-Honokōwai" : "nɑːˈpi.li honoˈkoː.wɐi" ,
    "Kula": "ˈku.lə",  # info: "Kula" : "ˈku.lə" ,
    "Wailea": "wɐiˈle.ə",  # info: "Wailea" : "wɐiˈle.ə" ,
    "Kaunakakai": "kɑu.nɑ.kɑˈkɑi",  # info: "Kaunakakai" : "kɑu.nɑ.kɑˈkɑi" ,
    "Lānaʻi City": "lɑːˈnɑ.ʔi ˈsɪ.ti",  # info: "Lānaʻi City" : "lɑːˈnɑ.ʔi ˈsɪ.ti" ,
    "Kāʻanapali": "kɑː.ʔɑ.nɑˈpɑ.li",  # info: "Kāʻanapali" : "kɑː.ʔɑ.nɑˈpɑ.li" ,
    # Kauaʻi County
    "Līhuʻe": "liːˈhu.ʔe",  # info: "Līhuʻe" : "liːˈhu.ʔe" ,
    "Kapaʻa": "kɑˈpɑ.ʔɑ",  # info: "Kapaʻa" : "kɑˈpɑ.ʔɑ" ,
    "Hanalei": "hɑ.nɑˈlei",  # info: "Hanalei" : "hɑ.nɑˈlei" ,
    "Poʻipū": "poˈʔi.puː",  # info: "Poʻipū" : "poˈʔi.puː" ,
    "Kōloa": "koːˈlo.ə",  # info: "Kōloa" : "koːˈlo.ə" ,
    "Kalaheo": "kɑ.lɑˈhe.o",  # info: "Kalaheo" : "kɑ.lɑˈhe.o" ,
    "Hanamāʻulu": "hɑ.nɑ.mɑːˈʔu.lu",  # info: "Hanamāʻulu" : "hɑ.nɑ.mɑːˈʔu.lu" ,
    "Hanapēpē": "hɑ.nɑˈpeː.peː",  # info: "Hanapēpē" : "hɑ.nɑˈpeː.peː" ,
    "Kekaha": "keˈkɑ.hə",  # info: "Kekaha" : "keˈkɑ.hə" ,
    "Princeville": "ˈpɹɪns.vɪl",  # info: "Princeville" : "ˈpɹɪns.vɪl" ,
    "Anahola": "ɑ.nɑˈho.lə",  # info: "Anahola" : "ɑ.nɑˈho.lə" ,
    "ʻEleʻele": "ʔe.leˈʔe.le",  # info: "ʻEleʻele" : "ʔe.leˈʔe.le" ,
    # Everyday
    "Aloha": "ɑˈlo.hɑ",  # info: "Aloha" : "ɑˈlo.hɑ" ,
    "Mahalo": "mɑˈhɑ.lo",  # info: "Mahalo" : "mɑˈhɑ.lo" ,
    "Pele": "ˈpe.le",  # info: "Pele" : "ˈpe.le" ,
}  # info: }

# English syllable respells for Kokoro G2P. IPA tags sound brutal on Heart/Echo/Nova;
# spaced English words do not. Operator-confirmed: Kīlauea → "Kill ah way uh".
# ====================================================
# SECTION: SPEAK_ENGLISH
# What it does: Set SPEAK_ENGLISH.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SPEAK_ENGLISH: dict[str, str] = {  # info: set SPEAK_ENGLISH
    # One word. Spaced "hah wye ee" made Kokoro stress "wye" as its own word.
    "Hawaiʻi": "hahwye-ee",  # info: "Hawaiʻi" : "hahwye-ee" ,
    "Hawaiian": "hahwye-uhn",  # info: "Hawaiian" : "hahwye-uhn" ,
    "Oʻahu": "oh ah hoo",  # info: "Oʻahu" : "oh ah hoo" ,
    "Maui": "mow ee",  # info: "Maui" : "mow ee" ,
    # "kah wah ee" — "cow ah ee" came out livestock + why + ee.
    "Kauaʻi": "kah wah ee",  # info: "Kauaʻi" : "kah wah ee" ,
    "Molokaʻi": "moh loh kah ee",  # info: "Molokaʻi" : "moh loh kah ee" ,
    "Lānaʻi": "lah nah ee",  # info: "Lānaʻi" : "lah nah ee" ,
    "Niʻihau": "nee ee how",  # info: "Niʻihau" : "nee ee how" ,
    "Kahoʻolawe": "kah hoh oh lah vay",  # info: "Kahoʻolawe" : "kah hoh oh lah vay" ,
    "Kīlauea": "keelah-wayuh",  # info: "Kīlauea" : "keelah-wayuh" ,
    "Mauna Loa": "mownah-lowah",  # info: "Mauna Loa" : "mownah-lowah" ,
    "Mauna Kea": "mow nah kay ah",  # info: "Mauna Kea" : "mow nah kay ah" ,
    "Haleakalā": "hah leh ah kah lah",  # info: "Haleakalā" : "hah leh ah kah lah" ,
    "Hualālai": "hoo ah lah lye",  # info: "Hualālai" : "hoo ah lah lye" ,
    "Halemaʻumaʻu": "hah leh mow mow",  # info: "Halemaʻumaʻu" : "hah leh mow mow" ,
    "Hilo": "hee loh",  # info: "Hilo" : "hee loh" ,
    "Pāhala": "pah hah lah",  # info: "Pāhala" : "pah hah lah" ,
    "Pāhoa": "pah hoh ah",  # info: "Pāhoa" : "pah hoh ah" ,
    "Kailua-Kona": "kye loo ah koh nah",  # info: "Kailua-Kona" : "kye loo ah koh nah" ,
    "Kona": "koh nah",  # info: "Kona" : "koh nah" ,
    "Waikoloa": "wye koh low ah",  # info: "Waikoloa" : "wye koh low ah" ,
    "Honokaʻa": "hoh noh kah ah",  # info: "Honokaʻa" : "hoh noh kah ah" ,
    "Waimea": "wye may ah",  # info: "Waimea" : "wye may ah" ,
    "Keaʻau": "kay ah ow",  # info: "Keaʻau" : "kay ah ow" ,
    "Hāwī": "hah vee",  # info: "Hāwī" : "hah vee" ,
    "Kapaʻau": "kah pah ow",  # info: "Kapaʻau" : "kah pah ow" ,
    "Kealakekua": "kay ah lah keh koo ah",  # info: "Kealakekua" : "kay ah lah keh koo ah" ,
    "Hōnaunau-Nāpōʻopoʻo": "hoh now now nah poh oh poh oh",  # info: "Hōnaunau-Nāpōʻopoʻo" : "hoh now now nah poh oh poh oh" ,
    "Hōnaunau": "hoh now now",  # info: "Hōnaunau" : "hoh now now" ,
    "Nāpōʻopoʻo": "nah poh oh poh oh",  # info: "Nāpōʻopoʻo" : "nah poh oh poh oh" ,
    "Captain Cook": "Captain Cook",  # info: "Captain Cook" : "Captain Cook" ,
    "Mountain View": "Mountain View",  # info: "Mountain View" : "Mountain View" ,
    "Hawaiian Paradise Park": "hah wye uhn Paradise Park",  # info: "Hawaiian Paradise Park" : "hah wye uhn Paradise Park" ,
    "Hawaiian Ocean View": "hah wye uhn Ocean View",  # info: "Hawaiian Ocean View" : "hah wye uhn Ocean View" ,
    "Ainaloa": "eye nah low ah",  # info: "Ainaloa" : "eye nah low ah" ,
    "Kurtistown": "Kurtistown",  # info: "Kurtistown" : "Kurtistown" ,
    "Paukaa": "pow kah ah",  # info: "Paukaa" : "pow kah ah" ,
    "Pepeekeo": "peh peh eh kay oh",  # info: "Pepeekeo" : "peh peh eh kay oh" ,
    "Laupāhoehoe": "lau pah hoy hoy",  # info: "Laupāhoehoe" : "lau pah hoy hoy" ,
    "Naalehu": "nah ah leh hoo",  # info: "Naalehu" : "nah ah leh hoo" ,
    "Nāʻālehu": "nah ah leh hoo",  # info: "Nāʻālehu" : "nah ah leh hoo" ,
    "Puna": "poo nah",  # info: "Puna" : "poo nah" ,
    "Kaʻū": "kah oo",  # info: "Kaʻū" : "kah oo" ,
    "Kohala": "koh hah lah",  # info: "Kohala" : "koh hah lah" ,
    "Hāmākua": "hah mah koo ah",  # info: "Hāmākua" : "hah mah koo ah" ,
    "Honolulu": "hoh noh loo loo",  # info: "Honolulu" : "hoh noh loo loo" ,
    "Waikīkī": "wye kee kee",  # info: "Waikīkī" : "wye kee kee" ,
    "Kailua": "kye loo ah",  # info: "Kailua" : "kye loo ah" ,
    "Kāneʻohe": "kah neh oh heh",  # info: "Kāneʻohe" : "kah neh oh heh" ,
    "Pearl City": "Pearl City",  # info: "Pearl City" : "Pearl City" ,
    "Waipahu": "wye pah hoo",  # info: "Waipahu" : "wye pah hoo" ,
    "Kapolei": "kah poh lay",  # info: "Kapolei" : "kah poh lay" ,
    "ʻEwa Beach": "eh vah Beach",  # info: "ʻEwa Beach" : "eh vah Beach" ,
    "ʻEwa Gentry": "eh vah Gentry",  # info: "ʻEwa Gentry" : "eh vah Gentry" ,
    "ʻEwa": "eh vah",  # info: "ʻEwa" : "eh vah" ,
    "Mililani": "mee lee lah nee",  # info: "Mililani" : "mee lee lah nee" ,
    "Makakilo": "mah kah kee loh",  # info: "Makakilo" : "mah kah kee loh" ,
    "Wahiawā": "wah hee ah vah",  # info: "Wahiawā" : "wah hee ah vah" ,
    "Waiʻanae": "wye ah nye",  # info: "Waiʻanae" : "wye ah nye" ,
    "Nānākuli": "nah nah koo lee",  # info: "Nānākuli" : "nah nah koo lee" ,
    "Haleʻiwa": "hah leh ee vah",  # info: "Haleʻiwa" : "hah leh ee vah" ,
    "Lāʻie": "lah ee eh",  # info: "Lāʻie" : "lah ee eh" ,
    "Hauʻula": "how oo lah",  # info: "Hauʻula" : "how oo lah" ,
    "Kahuku": "kah hoo koo",  # info: "Kahuku" : "kah hoo koo" ,
    "Pūpūkea": "poo poo kay ah",  # info: "Pūpūkea" : "poo poo kay ah" ,
    "Aiea": "eye ay ah",  # info: "Aiea" : "eye ay ah" ,
    "Ahuimanu": "ah hoo ee mah noo",  # info: "Ahuimanu" : "ah hoo ee mah noo" ,
    "Heʻeia": "heh ay ah",  # info: "Heʻeia" : "heh ay ah" ,
    "Kahaluʻu": "kah hah loo oo",  # info: "Kahaluʻu" : "kah hah loo oo" ,
    "Kahului": "kah hoo loo ee",  # info: "Kahului" : "kah hoo loo ee" ,
    "Lāhainā": "lah high nah",  # info: "Lāhainā" : "lah high nah" ,
    "Kīhei": "kee hay",  # info: "Kīhei" : "kee hay" ,
    "Wailuku": "wye loo koo",  # info: "Wailuku" : "wye loo koo" ,
    "Makawao": "mah kah wow",  # info: "Makawao" : "mah kah wow" ,
    "Hāna": "hah nah",  # info: "Hāna" : "hah nah" ,
    "Pāʻia": "pah ee ah",  # info: "Pāʻia" : "pah ee ah" ,
    "Pukalani": "poo kah lah nee",  # info: "Pukalani" : "poo kah lah nee" ,
    "Haʻikū-Pauwela": "high koo pow well ah",  # info: "Haʻikū-Pauwela" : "high koo pow well ah" ,
    "Nāpili-Honokōwai": "nah pee lee hoh noh koh wye",  # info: "Nāpili-Honokōwai" : "nah pee lee hoh noh koh wye" ,
    "Kula": "koo lah",  # info: "Kula" : "koo lah" ,
    "Wailea": "wye lay ah",  # info: "Wailea" : "wye lay ah" ,
    "Kaunakakai": "cow nah kah kye",  # info: "Kaunakakai" : "cow nah kah kye" ,
    "Lānaʻi City": "lah nah ee City",  # info: "Lānaʻi City" : "lah nah ee City" ,
    "Kāʻanapali": "kah ah nah pah lee",  # info: "Kāʻanapali" : "kah ah nah pah lee" ,
    "Līhuʻe": "lee hoo eh",  # info: "Līhuʻe" : "lee hoo eh" ,
    "Kapaʻa": "kah pah ah",  # info: "Kapaʻa" : "kah pah ah" ,
    "Hanalei": "hah nah lay",  # info: "Hanalei" : "hah nah lay" ,
    "Poʻipū": "poy poo",  # info: "Poʻipū" : "poy poo" ,
    "Kōloa": "koh low ah",  # info: "Kōloa" : "koh low ah" ,
    "Kalaheo": "kah lah hay oh",  # info: "Kalaheo" : "kah lah hay oh" ,
    "Hanamāʻulu": "hah nah mah oo loo",  # info: "Hanamāʻulu" : "hah nah mah oo loo" ,
    "Hanapēpē": "hah nah pay pay",  # info: "Hanapēpē" : "hah nah pay pay" ,
    "Kekaha": "keh kah hah",  # info: "Kekaha" : "keh kah hah" ,
    "Princeville": "Princeville",  # info: "Princeville" : "Princeville" ,
    "Anahola": "ah nah hoh lah",  # info: "Anahola" : "ah nah hoh lah" ,
    "ʻEleʻele": "eh leh eh leh",  # info: "ʻEleʻele" : "eh leh eh leh" ,
    "Aloha": "ah loh hah",  # info: "Aloha" : "ah loh hah" ,
    "Mahalo": "mah hah loh",  # info: "Mahalo" : "mah hah loh" ,
    "Pele": "peh leh",  # info: "Pele" : "peh leh" ,
}  # info: }

# ASCII / ascii-okina aliases → canonical PLACE_IPA key (longest match wins).
# ====================================================
# SECTION: SPELLING_ALIASES
# What it does: Set SPELLING_ALIASES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
SPELLING_ALIASES: dict[str, str] = {  # info: set SPELLING_ALIASES
    "Hawaii": "Hawaiʻi",  # info: "Hawaii" : "Hawaiʻi" ,
    "Hawai'i": "Hawaiʻi",  # info: "Hawai'i" : "Hawaiʻi" ,
    "Hawaiʻi": "Hawaiʻi",  # info: "Hawaiʻi" : "Hawaiʻi" ,
    "Oahu": "Oʻahu",  # info: "Oahu" : "Oʻahu" ,
    "O'ahu": "Oʻahu",  # info: "O'ahu" : "Oʻahu" ,
    "Oʻahu": "Oʻahu",  # info: "Oʻahu" : "Oʻahu" ,
    "Kauai": "Kauaʻi",  # info: "Kauai" : "Kauaʻi" ,
    "Kaua'i": "Kauaʻi",  # info: "Kaua'i" : "Kauaʻi" ,
    "Kauaʻi": "Kauaʻi",  # info: "Kauaʻi" : "Kauaʻi" ,
    "Molokai": "Molokaʻi",  # info: "Molokai" : "Molokaʻi" ,
    "Moloka'i": "Molokaʻi",  # info: "Moloka'i" : "Molokaʻi" ,
    "Molokaʻi": "Molokaʻi",  # info: "Molokaʻi" : "Molokaʻi" ,
    "Lanai": "Lānaʻi",  # info: "Lanai" : "Lānaʻi" ,
    "Lana'i": "Lānaʻi",  # info: "Lana'i" : "Lānaʻi" ,
    "Lānaʻi": "Lānaʻi",  # info: "Lānaʻi" : "Lānaʻi" ,
    "Niihau": "Niʻihau",  # info: "Niihau" : "Niʻihau" ,
    "Ni'ihau": "Niʻihau",  # info: "Ni'ihau" : "Niʻihau" ,
    "Niʻihau": "Niʻihau",  # info: "Niʻihau" : "Niʻihau" ,
    "Kahoolawe": "Kahoʻolawe",  # info: "Kahoolawe" : "Kahoʻolawe" ,
    "Kaho'olawe": "Kahoʻolawe",  # info: "Kaho'olawe" : "Kahoʻolawe" ,
    "Kahoʻolawe": "Kahoʻolawe",  # info: "Kahoʻolawe" : "Kahoʻolawe" ,
    "Kilauea": "Kīlauea",  # info: "Kilauea" : "Kīlauea" ,
    "Kīlauea": "Kīlauea",  # info: "Kīlauea" : "Kīlauea" ,
    "Haleakala": "Haleakalā",  # info: "Haleakala" : "Haleakalā" ,
    "Haleakalā": "Haleakalā",  # info: "Haleakalā" : "Haleakalā" ,
    "Hualalai": "Hualālai",  # info: "Hualalai" : "Hualālai" ,
    "Hualālai": "Hualālai",  # info: "Hualālai" : "Hualālai" ,
    "Halemaumau": "Halemaʻumaʻu",  # info: "Halemaumau" : "Halemaʻumaʻu" ,
    "Halema'uma'u": "Halemaʻumaʻu",  # info: "Halema'uma'u" : "Halemaʻumaʻu" ,
    "Halemaʻumaʻu": "Halemaʻumaʻu",  # info: "Halemaʻumaʻu" : "Halemaʻumaʻu" ,
    "Pahala": "Pāhala",  # info: "Pahala" : "Pāhala" ,
    "Pāhala": "Pāhala",  # info: "Pāhala" : "Pāhala" ,
    "Pahoa": "Pāhoa",  # info: "Pahoa" : "Pāhoa" ,
    "Pāhoa": "Pāhoa",  # info: "Pāhoa" : "Pāhoa" ,
    "Kailua Kona": "Kailua-Kona",  # info: "Kailua Kona" : "Kailua-Kona" ,
    "Kailua-Kona": "Kailua-Kona",  # info: "Kailua-Kona" : "Kailua-Kona" ,
    "Honokaa": "Honokaʻa",  # info: "Honokaa" : "Honokaʻa" ,
    "Honoka'a": "Honokaʻa",  # info: "Honoka'a" : "Honokaʻa" ,
    "Honokaʻa": "Honokaʻa",  # info: "Honokaʻa" : "Honokaʻa" ,
    "Keaau": "Keaʻau",  # info: "Keaau" : "Keaʻau" ,
    "Kea'au": "Keaʻau",  # info: "Kea'au" : "Keaʻau" ,
    "Keaʻau": "Keaʻau",  # info: "Keaʻau" : "Keaʻau" ,
    "Hawi": "Hāwī",  # info: "Hawi" : "Hāwī" ,
    "Hāwī": "Hāwī",  # info: "Hāwī" : "Hāwī" ,
    "Kapaau": "Kapaʻau",  # info: "Kapaau" : "Kapaʻau" ,
    "Kapa'au": "Kapaʻau",  # info: "Kapa'au" : "Kapaʻau" ,
    "Kapaʻau": "Kapaʻau",  # info: "Kapaʻau" : "Kapaʻau" ,
    "Honaunau-Napoopoo": "Hōnaunau-Nāpōʻopoʻo",  # info: "Honaunau-Napoopoo" : "Hōnaunau-Nāpōʻopoʻo" ,
    "Honaunau-Napo'opo'o": "Hōnaunau-Nāpōʻopoʻo",  # info: "Honaunau-Napo'opo'o" : "Hōnaunau-Nāpōʻopoʻo" ,
    "Hōnaunau-Nāpōʻopoʻo": "Hōnaunau-Nāpōʻopoʻo",  # info: "Hōnaunau-Nāpōʻopoʻo" : "Hōnaunau-Nāpōʻopoʻo" ,
    "Honaunau": "Hōnaunau",  # info: "Honaunau" : "Hōnaunau" ,
    "Hōnaunau": "Hōnaunau",  # info: "Hōnaunau" : "Hōnaunau" ,
    "Napoopoo": "Nāpōʻopoʻo",  # info: "Napoopoo" : "Nāpōʻopoʻo" ,
    "Napo'opo'o": "Nāpōʻopoʻo",  # info: "Napo'opo'o" : "Nāpōʻopoʻo" ,
    "Nāpōʻopoʻo": "Nāpōʻopoʻo",  # info: "Nāpōʻopoʻo" : "Nāpōʻopoʻo" ,
    "Naalehu": "Naalehu",  # info: "Naalehu" : "Naalehu" ,
    "Na'alehu": "Nāʻālehu",  # info: "Na'alehu" : "Nāʻālehu" ,
    "Nāʻālehu": "Nāʻālehu",  # info: "Nāʻālehu" : "Nāʻālehu" ,
    "Kau": "Kaʻū",  # info: "Kau" : "Kaʻū" ,
    "Ka'u": "Kaʻū",  # info: "Ka'u" : "Kaʻū" ,
    "Kaʻū": "Kaʻū",  # info: "Kaʻū" : "Kaʻū" ,
    "Hamakua": "Hāmākua",  # info: "Hamakua" : "Hāmākua" ,
    "Hāmākua": "Hāmākua",  # info: "Hāmākua" : "Hāmākua" ,
    "Waikiki": "Waikīkī",  # info: "Waikiki" : "Waikīkī" ,
    "Waikīkī": "Waikīkī",  # info: "Waikīkī" : "Waikīkī" ,
    "Kaneohe": "Kāneʻohe",  # info: "Kaneohe" : "Kāneʻohe" ,
    "Kane'ohe": "Kāneʻohe",  # info: "Kane'ohe" : "Kāneʻohe" ,
    "Kāneʻohe": "Kāneʻohe",  # info: "Kāneʻohe" : "Kāneʻohe" ,
    "Ewa Beach": "ʻEwa Beach",  # info: "Ewa Beach" : "ʻEwa Beach" ,
    "'Ewa Beach": "ʻEwa Beach",  # info: "'Ewa Beach" : "ʻEwa Beach" ,
    "ʻEwa Beach": "ʻEwa Beach",  # info: "ʻEwa Beach" : "ʻEwa Beach" ,
    "Ewa Gentry": "ʻEwa Gentry",  # info: "Ewa Gentry" : "ʻEwa Gentry" ,
    "'Ewa Gentry": "ʻEwa Gentry",  # info: "'Ewa Gentry" : "ʻEwa Gentry" ,
    "ʻEwa Gentry": "ʻEwa Gentry",  # info: "ʻEwa Gentry" : "ʻEwa Gentry" ,
    "Ewa": "ʻEwa",  # info: "Ewa" : "ʻEwa" ,
    "'Ewa": "ʻEwa",  # info: "'Ewa" : "ʻEwa" ,
    "ʻEwa": "ʻEwa",  # info: "ʻEwa" : "ʻEwa" ,
    "Wahiawa": "Wahiawā",  # info: "Wahiawa" : "Wahiawā" ,
    "Wahiawā": "Wahiawā",  # info: "Wahiawā" : "Wahiawā" ,
    "Waianae": "Waiʻanae",  # info: "Waianae" : "Waiʻanae" ,
    "Wai'anae": "Waiʻanae",  # info: "Wai'anae" : "Waiʻanae" ,
    "Waiʻanae": "Waiʻanae",  # info: "Waiʻanae" : "Waiʻanae" ,
    "Nanakuli": "Nānākuli",  # info: "Nanakuli" : "Nānākuli" ,
    "Nānākuli": "Nānākuli",  # info: "Nānākuli" : "Nānākuli" ,
    "Haleiwa": "Haleʻiwa",  # info: "Haleiwa" : "Haleʻiwa" ,
    "Hale'iwa": "Haleʻiwa",  # info: "Hale'iwa" : "Haleʻiwa" ,
    "Haleʻiwa": "Haleʻiwa",  # info: "Haleʻiwa" : "Haleʻiwa" ,
    "Laie": "Lāʻie",  # info: "Laie" : "Lāʻie" ,
    "La'ie": "Lāʻie",  # info: "La'ie" : "Lāʻie" ,
    "Lāʻie": "Lāʻie",  # info: "Lāʻie" : "Lāʻie" ,
    "Hauula": "Hauʻula",  # info: "Hauula" : "Hauʻula" ,
    "Hau'ula": "Hauʻula",  # info: "Hau'ula" : "Hauʻula" ,
    "Hauʻula": "Hauʻula",  # info: "Hauʻula" : "Hauʻula" ,
    "Pupukea": "Pūpūkea",  # info: "Pupukea" : "Pūpūkea" ,
    "Pūpūkea": "Pūpūkea",  # info: "Pūpūkea" : "Pūpūkea" ,
    "Heeia": "Heʻeia",  # info: "Heeia" : "Heʻeia" ,
    "He'eia": "Heʻeia",  # info: "He'eia" : "Heʻeia" ,
    "Heʻeia": "Heʻeia",  # info: "Heʻeia" : "Heʻeia" ,
    "Kahaluu": "Kahaluʻu",  # info: "Kahaluu" : "Kahaluʻu" ,
    "Kahalu'u": "Kahaluʻu",  # info: "Kahalu'u" : "Kahaluʻu" ,
    "Kahaluʻu": "Kahaluʻu",  # info: "Kahaluʻu" : "Kahaluʻu" ,
    "Lahaina": "Lāhainā",  # info: "Lahaina" : "Lāhainā" ,
    "Lāhainā": "Lāhainā",  # info: "Lāhainā" : "Lāhainā" ,
    "Kihei": "Kīhei",  # info: "Kihei" : "Kīhei" ,
    "Kīhei": "Kīhei",  # info: "Kīhei" : "Kīhei" ,
    "Hana": "Hāna",  # info: "Hana" : "Hāna" ,
    "Hāna": "Hāna",  # info: "Hāna" : "Hāna" ,
    "Paia": "Pāʻia",  # info: "Paia" : "Pāʻia" ,
    "Pa'ia": "Pāʻia",  # info: "Pa'ia" : "Pāʻia" ,
    "Pāʻia": "Pāʻia",  # info: "Pāʻia" : "Pāʻia" ,
    "Haiku-Pauwela": "Haʻikū-Pauwela",  # info: "Haiku-Pauwela" : "Haʻikū-Pauwela" ,
    "Ha'iku-Pauwela": "Haʻikū-Pauwela",  # info: "Ha'iku-Pauwela" : "Haʻikū-Pauwela" ,
    "Haʻikū-Pauwela": "Haʻikū-Pauwela",  # info: "Haʻikū-Pauwela" : "Haʻikū-Pauwela" ,
    "Napili-Honokowai": "Nāpili-Honokōwai",  # info: "Napili-Honokowai" : "Nāpili-Honokōwai" ,
    "Nāpili-Honokōwai": "Nāpili-Honokōwai",  # info: "Nāpili-Honokōwai" : "Nāpili-Honokōwai" ,
    "Lanai City": "Lānaʻi City",  # info: "Lanai City" : "Lānaʻi City" ,
    "Lānaʻi City": "Lānaʻi City",  # info: "Lānaʻi City" : "Lānaʻi City" ,
    "Kaanapali": "Kāʻanapali",  # info: "Kaanapali" : "Kāʻanapali" ,
    "Ka'anapali": "Kāʻanapali",  # info: "Ka'anapali" : "Kāʻanapali" ,
    "Kāʻanapali": "Kāʻanapali",  # info: "Kāʻanapali" : "Kāʻanapali" ,
    "Lihue": "Līhuʻe",  # info: "Lihue" : "Līhuʻe" ,
    "Lihu'e": "Līhuʻe",  # info: "Lihu'e" : "Līhuʻe" ,
    "Līhuʻe": "Līhuʻe",  # info: "Līhuʻe" : "Līhuʻe" ,
    "Kapaa": "Kapaʻa",  # info: "Kapaa" : "Kapaʻa" ,
    "Kapa'a": "Kapaʻa",  # info: "Kapa'a" : "Kapaʻa" ,
    "Kapaʻa": "Kapaʻa",  # info: "Kapaʻa" : "Kapaʻa" ,
    "Poipu": "Poʻipū",  # info: "Poipu" : "Poʻipū" ,
    "Po'ipu": "Poʻipū",  # info: "Po'ipu" : "Poʻipū" ,
    "Poʻipū": "Poʻipū",  # info: "Poʻipū" : "Poʻipū" ,
    "Koloa": "Kōloa",  # info: "Koloa" : "Kōloa" ,
    "Kōloa": "Kōloa",  # info: "Kōloa" : "Kōloa" ,
    "Hanamaulu": "Hanamāʻulu",  # info: "Hanamaulu" : "Hanamāʻulu" ,
    "Hanama'ulu": "Hanamāʻulu",  # info: "Hanama'ulu" : "Hanamāʻulu" ,
    "Hanamāʻulu": "Hanamāʻulu",  # info: "Hanamāʻulu" : "Hanamāʻulu" ,
    "Hanapepe": "Hanapēpē",  # info: "Hanapepe" : "Hanapēpē" ,
    "Hanapēpē": "Hanapēpē",  # info: "Hanapēpē" : "Hanapēpē" ,
    "Eleele": "ʻEleʻele",  # info: "Eleele" : "ʻEleʻele" ,
    "'Ele'ele": "ʻEleʻele",  # info: "'Ele'ele" : "ʻEleʻele" ,
    "ʻEleʻele": "ʻEleʻele",  # info: "ʻEleʻele" : "ʻEleʻele" ,
    "Laupahoehoe": "Laupāhoehoe",  # info: "Laupahoehoe" : "Laupāhoehoe" ,
    "Laupāhoehoe": "Laupāhoehoe",  # info: "Laupāhoehoe" : "Laupāhoehoe" ,
    "Maui": "Maui",  # info: "Maui" : "Maui" ,
    "Hilo": "Hilo",  # info: "Hilo" : "Hilo" ,
    "Honolulu": "Honolulu",  # info: "Honolulu" : "Honolulu" ,
    "Mauna Loa": "Mauna Loa",  # info: "Mauna Loa" : "Mauna Loa" ,
    "Mauna Kea": "Mauna Kea",  # info: "Mauna Kea" : "Mauna Kea" ,
    "Waimea": "Waimea",  # info: "Waimea" : "Waimea" ,
    "Waikoloa": "Waikoloa",  # info: "Waikoloa" : "Waikoloa" ,
    "Kealakekua": "Kealakekua",  # info: "Kealakekua" : "Kealakekua" ,
    "Captain Cook": "Captain Cook",  # info: "Captain Cook" : "Captain Cook" ,
    "Mountain View": "Mountain View",  # info: "Mountain View" : "Mountain View" ,
    "Hawaiian Paradise Park": "Hawaiian Paradise Park",  # info: "Hawaiian Paradise Park" : "Hawaiian Paradise Park" ,
    "Hawaiian Ocean View": "Hawaiian Ocean View",  # info: "Hawaiian Ocean View" : "Hawaiian Ocean View" ,
    "Ainaloa": "Ainaloa",  # info: "Ainaloa" : "Ainaloa" ,
    "Kurtistown": "Kurtistown",  # info: "Kurtistown" : "Kurtistown" ,
    "Paukaa": "Paukaa",  # info: "Paukaa" : "Paukaa" ,
    "Pepeekeo": "Pepeekeo",  # info: "Pepeekeo" : "Pepeekeo" ,
    "Puna": "Puna",  # info: "Puna" : "Puna" ,
    "Kona": "Kona",  # info: "Kona" : "Kona" ,
    "Kohala": "Kohala",  # info: "Kohala" : "Kohala" ,
    "Pearl City": "Pearl City",  # info: "Pearl City" : "Pearl City" ,
    "Waipahu": "Waipahu",  # info: "Waipahu" : "Waipahu" ,
    "Kapolei": "Kapolei",  # info: "Kapolei" : "Kapolei" ,
    "Mililani": "Mililani",  # info: "Mililani" : "Mililani" ,
    "Makakilo": "Makakilo",  # info: "Makakilo" : "Makakilo" ,
    "Kahuku": "Kahuku",  # info: "Kahuku" : "Kahuku" ,
    "Aiea": "Aiea",  # info: "Aiea" : "Aiea" ,
    "Ahuimanu": "Ahuimanu",  # info: "Ahuimanu" : "Ahuimanu" ,
    "Kahului": "Kahului",  # info: "Kahului" : "Kahului" ,
    "Wailuku": "Wailuku",  # info: "Wailuku" : "Wailuku" ,
    "Makawao": "Makawao",  # info: "Makawao" : "Makawao" ,
    "Pukalani": "Pukalani",  # info: "Pukalani" : "Pukalani" ,
    "Kula": "Kula",  # info: "Kula" : "Kula" ,
    "Wailea": "Wailea",  # info: "Wailea" : "Wailea" ,
    "Kaunakakai": "Kaunakakai",  # info: "Kaunakakai" : "Kaunakakai" ,
    "Kailua": "Kailua",  # info: "Kailua" : "Kailua" ,
    "Hanalei": "Hanalei",  # info: "Hanalei" : "Hanalei" ,
    "Kalaheo": "Kalaheo",  # info: "Kalaheo" : "Kalaheo" ,
    "Kekaha": "Kekaha",  # info: "Kekaha" : "Kekaha" ,
    "Princeville": "Princeville",  # info: "Princeville" : "Princeville" ,
    "Anahola": "Anahola",  # info: "Anahola" : "Anahola" ,
    "Hawaiian": "Hawaiian",  # info: "Hawaiian" : "Hawaiian" ,
    "Aloha": "Aloha",  # info: "Aloha" : "Aloha" ,
    "Mahalo": "Mahalo",  # info: "Mahalo" : "Mahalo" ,
    "Pele": "Pele",  # info: "Pele" : "Pele" ,
}  # info: }

# Kokoro US vocab (model config) — allow IPA marks used in PLACE_IPA after ʔ strip.
# ====================================================
# SECTION: US_VOCAB
# What it does: Set US_VOCAB.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
US_VOCAB = frozenset(  # info: set US_VOCAB
    " !\"(),.:;?AIOQSTWYabcdefhijklmnopqrstuvwxyz"  # info: " !\"(),.:;?AIOQSTWYabcdefhijklmnopqrstuvwxyz"
    "æçðøŋœɐɑɒɔɕɖəɚɛɜɟɡɣɤɥɨɪɯɰɲɳɴɸɹɻɽɾʁʂʃʈʊʋʌʎʒʔʝ"  # info: "æçðøŋœɐɑɒɔɕɖəɚɛɜɟɡɣɤɥɨɪɯɰɲɳɴɸɹɻɽɾʁʂʃʈʊʋʌʎʒʔʝ"
    "ʣʤʥʦʧʨʰʲˈˌː̃βθχᵊᵝᵻ—“”…→↓↗↘ʦ"  # info: "ʣʤʥʦʧʨʰʲˈˌː̃βθχᵊᵝᵻ—“”…→↓↗↘ʦ"
    "ɝɒʊæ"  # info: "ɝɒʊæ"
)  # info: )

# Back-compat names used by older diagnose / tests.
PLACE_PHONEMES: dict[str, str] = {}  # info: set PLACE_PHONEMES
SPEAK_AS: dict[str, str] = {}  # info: set SPEAK_AS
HAWAIIAN_KEYS: frozenset[str] = frozenset()  # info: set HAWAIIAN_KEYS
KILAUEA = ""  # info: set KILAUEA


# ====================================================
# SECTION: function kokoro_ipa
# What it does: Strip glottal stops — Misaki replaces ʔ with t.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def kokoro_ipa(ipa: str) -> str:  # info: def kokoro_ipa
    """Strip glottal stops — Misaki replaces ʔ with t."""  # info: """Strip glottal stops — Misaki replaces ʔ with t."""
    out = (ipa or "").replace("ʔ", "")  # info: set out
    out = re.sub(r"\.\.+", ".", out)  # info: set out
    out = re.sub(r"\s{2,}", " ", out).strip()  # info: set out
    return out  # info: return out


# ====================================================
# SECTION: function ipa_tag
# What it does: ipa tag.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def ipa_tag(name: str, ipa: str) -> str:  # info: def ipa_tag
    return f"[{name}](/{kokoro_ipa(ipa)}/)"  # info: return f" [ { name } ](/ {


# ====================================================
# SECTION: function _rebuild_derived
# What it does:  rebuild derived.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _rebuild_derived() -> None:  # info: def _rebuild_derived
    global PLACE_PHONEMES, SPEAK_AS, HAWAIIAN_KEYS, KILAUEA  # info: global PLACE_PHONEMES , SPEAK_AS , HAWAIIAN_KEYS , KILAUEA
    # PLACE_PHONEMES kept for diagnose tools; voice path uses SPEAK_ENGLISH only.
    PLACE_PHONEMES = {  # info: set PLACE_PHONEMES
        alias: kokoro_ipa(PLACE_IPA[canon])  # info: set alias
        for alias, canon in SPELLING_ALIASES.items()  # info: for alias , canon in SPELLING_ALIASES . items
        if canon in PLACE_IPA  # info: if canon in PLACE_IPA
    }  # info: }
    for canon, ipa in PLACE_IPA.items():  # info: for canon , ipa in PLACE_IPA . items
        PLACE_PHONEMES[canon] = kokoro_ipa(ipa)  # info: PLACE_PHONEMES [ canon ] = kokoro_ipa ( ipa
        PLACE_PHONEMES[canon.lower()] = kokoro_ipa(ipa)  # info: PLACE_PHONEMES [ canon . lower ( ) ]
    SPEAK_AS = dict(SPEAK_ENGLISH)  # info: set SPEAK_AS
    HAWAIIAN_KEYS = frozenset(PLACE_IPA)  # info: set HAWAIIAN_KEYS
    KILAUEA = SPEAK_ENGLISH["Kīlauea"]  # info: set KILAUEA


_rebuild_derived()  # info: call _rebuild_derived

# Longest alias first so "Hawaiian Paradise Park" wins over "Hawaiian".
_ALIAS_ORDER = sorted(SPELLING_ALIASES.keys(), key=len, reverse=True)  # info: set _ALIAS_ORDER
_ALIAS_RE = re.compile(  # info: set _ALIAS_RE
    r"(?<!\[)\b(" + "|".join(re.escape(a) for a in _ALIAS_ORDER) + r")\b",  # info: r"(?<!\[)\b(" + "|" . join ( re .
    flags=re.IGNORECASE,  # info: set flags
)  # info: )
_EXISTING_TAG_RE = re.compile(r"\[([^\]]+)\]\(/[^)]+/\)")  # info: set _EXISTING_TAG_RE


# ====================================================
# SECTION: function fold_place_spellings
# What it does: Normalize okina spellings to ASCII aliases for matching.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def fold_place_spellings(text: str) -> str:  # info: def fold_place_spellings
    """Normalize okina spellings to ASCII aliases for matching."""  # info: """Normalize okina spellings to ASCII aliases for matching."""
    out = text or ""  # info: set out
    folds = (  # info: set folds
        ("Hawaiʻi", "Hawaii"),  # info: call (
        ("Hawai'i", "Hawaii"),  # info: call (
        ("Kīlauea", "Kilauea"),  # info: call (
        ("Oʻahu", "Oahu"),  # info: call (
        ("O'ahu", "Oahu"),  # info: call (
        ("Kauaʻi", "Kauai"),  # info: call (
        ("Kaua'i", "Kauai"),  # info: call (
        ("Molokaʻi", "Molokai"),  # info: call (
        ("Moloka'i", "Molokai"),  # info: call (
        ("Lānaʻi", "Lanai"),  # info: call (
        ("Lana'i", "Lanai"),  # info: call (
        ("Niʻihau", "Niihau"),  # info: call (
        ("Ni'ihau", "Niihau"),  # info: call (
        ("Kahoʻolawe", "Kahoolawe"),  # info: call (
        ("Kaho'olawe", "Kahoolawe"),  # info: call (
        ("Halemaʻumaʻu", "Halemaumau"),  # info: call (
        ("Halema'uma'u", "Halemaumau"),  # info: call (
        ("Haleakalā", "Haleakala"),  # info: call (
        ("Hualālai", "Hualalai"),  # info: call (
        ("Pāhala", "Pahala"),  # info: call (
        ("Pāhoa", "Pahoa"),  # info: call (
        ("Honokaʻa", "Honokaa"),  # info: call (
        ("Honoka'a", "Honokaa"),  # info: call (
        ("Keaʻau", "Keaau"),  # info: call (
        ("Kapaʻau", "Kapaau"),  # info: call (
        ("Hāwī", "Hawi"),  # info: call (
        ("Hōnaunau", "Honaunau"),  # info: call (
        ("Nāpōʻopoʻo", "Napoopoo"),  # info: call (
        ("Napo'opo'o", "Napoopoo"),  # info: call (
        ("Nāʻālehu", "Naalehu"),  # info: call (
        ("Na'alehu", "Naalehu"),  # info: call (
        ("Kaʻū", "Kau"),  # info: call (
        ("Ka'u", "Kau"),  # info: call (
        ("Hāmākua", "Hamakua"),  # info: call (
        ("Waikīkī", "Waikiki"),  # info: call (
        ("Kāneʻohe", "Kaneohe"),  # info: call (
        ("Kane'ohe", "Kaneohe"),  # info: call (
        ("ʻEwa", "Ewa"),  # info: call (
        ("'Ewa", "Ewa"),  # info: call (
        ("Wahiawā", "Wahiawa"),  # info: call (
        ("Waiʻanae", "Waianae"),  # info: call (
        ("Wai'anae", "Waianae"),  # info: call (
        ("Nānākuli", "Nanakuli"),  # info: call (
        ("Haleʻiwa", "Haleiwa"),  # info: call (
        ("Lāʻie", "Laie"),  # info: call (
        ("Hauʻula", "Hauula"),  # info: call (
        ("Pūpūkea", "Pupukea"),  # info: call (
        ("Heʻeia", "Heeia"),  # info: call (
        ("Kahaluʻu", "Kahaluu"),  # info: call (
        ("Lāhainā", "Lahaina"),  # info: call (
        ("Kīhei", "Kihei"),  # info: call (
        ("Hāna", "Hana"),  # info: call (
        ("Pāʻia", "Paia"),  # info: call (
        ("Kāʻanapali", "Kaanapali"),  # info: call (
        ("Līhuʻe", "Lihue"),  # info: call (
        ("Lihu'e", "Lihue"),  # info: call (
        ("Kapaʻa", "Kapaa"),  # info: call (
        ("Poʻipū", "Poipu"),  # info: call (
        ("Kōloa", "Koloa"),  # info: call (
        ("Hanamāʻulu", "Hanamaulu"),  # info: call (
        ("Hanapēpē", "Hanapepe"),  # info: call (
        ("ʻEleʻele", "Eleele"),  # info: call (
        ("Laupāhoehoe", "Laupahoehoe"),  # info: call (
        ("Honaunau-Napoopoo", "Honaunau-Napoopoo"),  # info: call (
        ("Hōnaunau-Nāpōʻopoʻo", "Honaunau-Napoopoo"),  # info: call (
    )  # info: )
    for src, dest in folds:  # info: for src , dest in folds :
        out = out.replace(src, dest)  # info: set out
        out = out.replace(src.lower(), dest)  # info: set out
        out = out.replace(src.upper(), dest)  # info: set out
    return out  # info: return out


# ====================================================
# SECTION: function _english_for
# What it does:  english for.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def _english_for(canon: str) -> str:  # info: def _english_for
    return SPEAK_ENGLISH.get(canon) or canon  # info: return SPEAK_ENGLISH . get ( canon ) or


# ====================================================
# SECTION: function pronounce_places
# What it does: Replace place names with spaced English syllables Kokoro can say.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def pronounce_places(text: str) -> str:  # info: def pronounce_places
    """Replace place names with spaced English syllables Kokoro can say."""  # info: """Replace place names with spaced English syllables Kokoro can say."""
    out = text or ""  # info: set out

    def _from_tag(m: re.Match) -> str:  # info: def _from_tag
        raw = m.group(1)  # info: set raw
        for alias in _ALIAS_ORDER:  # info: for alias in _ALIAS_ORDER :
            if alias.lower() == raw.lower() or SPELLING_ALIASES.get(alias, "").lower() == raw.lower():  # info: if alias . lower ( ) == raw
                canon = SPELLING_ALIASES[alias]  # info: set canon
                return _english_for(canon)  # info: return _english_for ( canon )
        # Tag name may already be canonical orthography.
        if raw in SPEAK_ENGLISH:  # info: if raw in SPEAK_ENGLISH :
            return SPEAK_ENGLISH[raw]  # info: return SPEAK_ENGLISH [ raw ]
        return raw  # info: return raw

    out = _EXISTING_TAG_RE.sub(_from_tag, out)  # info: set out

    def _wrap(m: re.Match) -> str:  # info: def _wrap
        raw = m.group(1)  # info: set raw
        canon = None  # info: set canon
        for alias in _ALIAS_ORDER:  # info: for alias in _ALIAS_ORDER :
            if alias.lower() == raw.lower():  # info: if alias . lower ( ) == raw
                canon = SPELLING_ALIASES[alias]  # info: set canon
                break  # info: break
        if not canon:  # info: if not canon :
            return raw  # info: return raw
        return _english_for(canon)  # info: return _english_for ( canon )

    out = _ALIAS_RE.sub(_wrap, out)  # info: set out
    return out  # info: return out


# ====================================================
# SECTION: function lexicon_entries
# What it does: No place-name golds — English respells must hit normal G2P.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def lexicon_entries() -> dict[str, str]:  # info: def lexicon_entries
    """No place-name golds — English respells must hit normal G2P."""  # info: """No place-name golds — English respells must hit normal G2P."""
    return {}  # info: return { }


# ====================================================
# SECTION: DIAGNOSE_NAMES
# What it does: Set DIAGNOSE_NAMES.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
DIAGNOSE_NAMES = (  # info: set DIAGNOSE_NAMES
    "Hawaii",  # info: "Hawaii" ,
    "Hawaiian",  # info: "Hawaiian" ,
    "Kilauea",  # info: "Kilauea" ,
    "Hilo",  # info: "Hilo" ,
    "Honolulu",  # info: "Honolulu" ,
    "Puna",  # info: "Puna" ,
    "Kona",  # info: "Kona" ,
    "Kau",  # info: "Kau" ,
    "Mauna Loa",  # info: "Mauna Loa" ,
    "Mauna Kea",  # info: "Mauna Kea" ,
    "Oahu",  # info: "Oahu" ,
    "Maui",  # info: "Maui" ,
    "Kauai",  # info: "Kauai" ,
    "Molokai",  # info: "Molokai" ,
    "Lanai",  # info: "Lanai" ,
    "Niihau",  # info: "Niihau" ,
    "Kahoolawe",  # info: "Kahoolawe" ,
    "Lihue",  # info: "Lihue" ,
    "Pahoa",  # info: "Pahoa" ,
    "Halemaumau",  # info: "Halemaumau" ,
    "Waikiki",  # info: "Waikiki" ,
    "Lahaina",  # info: "Lahaina" ,
    "Haleakala",  # info: "Haleakala" ,
    "Kaneohe",  # info: "Kaneohe" ,
    "Waianae",  # info: "Waianae" ,
    "Ewa",  # info: "Ewa" ,
    "Kohala",  # info: "Kohala" ,
    "Aloha",  # info: "Aloha" ,
    "Mahalo",  # info: "Mahalo" ,
    "Pele",  # info: "Pele" ,
    "Mountain View",  # info: "Mountain View" ,
    "Captain Cook",  # info: "Captain Cook" ,
    "Pahala",  # info: "Pahala" ,
    "Waimea",  # info: "Waimea" ,
    "Kihei",  # info: "Kihei" ,
)  # info: )
