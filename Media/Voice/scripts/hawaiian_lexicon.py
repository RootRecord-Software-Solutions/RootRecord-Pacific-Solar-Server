# G3 port 2026-09-29 (g3-voice-ailog): copied verbatim from G1 old skills/kokoro/scripts/hawaiian_lexicon.py (source kept in place).
"""Hawaiian / local place IPA for Kokoro via Misaki [Name](/ipa/) tags.

Source: operator IPA list. Glottal ʔ is stripped before speak — Misaki maps ʔ→t.
Dot syllable breaks and length marks stay; Kokoro vocab accepts them.
"""

from __future__ import annotations

import re

# Operator IPA (with ʔ). Do not feed ʔ to Kokoro — use kokoro_ipa().
PLACE_IPA: dict[str, str] = {
    # Islands
    "Hawaiʻi": "həˈwɐi.ʔi",
    "Hawaiian": "həˈwɐi.ən",
    "Oʻahu": "oˈʔɑ.hu",
    "Maui": "ˈmɐu.i",
    "Kauaʻi": "kɐuˈɑ.ʔi",
    "Molokaʻi": "moloˈkɑ.ʔi",
    "Lānaʻi": "lɑːˈnɑ.ʔi",
    "Niʻihau": "niːˈi.hɐu",
    "Kahoʻolawe": "kɑ.ho.ʔoˈlɑ.ve",
    # Volcanoes / mountains
    "Kīlauea": "kiː.lɐˈu.e.ɑ",
    "Mauna Loa": "ˈmɐu.nə ˈlo.ə",
    "Mauna Kea": "ˈmɐu.nə ˈke.ə",
    "Haleakalā": "hɑ.le.ɑ.kɑˈlɑː",
    "Hualālai": "hu.ɑˈlɑː.lɑi",
    "Halemaʻumaʻu": "hɑ.le.mɐˈu.mɐ.ʔu",
    # Hawaiʻi County
    "Hilo": "ˈhi.lo",
    "Pāhala": "pɑːˈhɑ.lə",
    "Pāhoa": "pɑːˈho.ə",
    "Kailua-Kona": "kɐiˈlu.ə ˈko.nə",
    "Kona": "ˈko.nə",
    "Waikoloa": "wɐi.koˈlo.ə",
    "Honokaʻa": "honoˈkɑ.ʔɑ",
    "Waimea": "wɐiˈme.ə",
    "Keaʻau": "ke.ɑˈʔɐu",
    "Hāwī": "ˈhɑː.vi",
    "Kapaʻau": "kɑˈpɑ.ʔɐu",
    "Kealakekua": "ke.ɑ.lɑ.keˈku.ə",
    "Hōnaunau-Nāpōʻopoʻo": "hoː.nɑuˈnɑu nɑːˈpoː.ʔo.poː.ʔo",
    "Hōnaunau": "hoː.nɑuˈnɑu",
    "Nāpōʻopoʻo": "nɑːˈpoː.ʔo.poː.ʔo",
    "Captain Cook": "ˈkæp.tən kʊk",
    "Mountain View": "ˈmaʊn.tən vjuː",
    "Hawaiian Paradise Park": "həˈwɐi.ən ˈpæɹ.ə.daɪs pɑɹk",
    "Hawaiian Ocean View": "həˈwɐi.ən ˈoʊ.ʃən vjuː",
    "Ainaloa": "ɑi.nɑˈlo.ə",
    "Kurtistown": "ˈkɝː.tɪs.taʊn",
    "Paukaa": "pɑuˈkɑ.ə",
    "Pepeekeo": "pe.pe.eˈke.o",
    "Laupāhoehoe": "lɑu.pɑː.hoeˈhoe",
    "Naalehu": "nɑːˈʔɑ.le.hu",
    "Nāʻālehu": "nɑːˈʔɑ.le.hu",
    "Volcano": "vɒlˈkeɪ.noʊ",
    "Puna": "ˈpu.nɑ",
    "Kaʻū": "kɑˈʔuː",
    "Kohala": "koˈhɑ.lə",
    "Hāmākua": "hɑːˈmɑː.ku.ə",
    # Oʻahu
    "Honolulu": "honoˈlu.lu",
    "Waikīkī": "wɐi.kiːˈkiː",
    "Kailua": "kɐiˈlu.ə",
    "Kāneʻohe": "kɑː.neˈʔo.he",
    "Pearl City": "pɝːl ˈsɪ.ti",
    "Waipahu": "wɐiˈpɑ.hu",
    "Kapolei": "kɑ.poˈlei",
    "ʻEwa Beach": "ˈʔe.vɑ biːtʃ",
    "ʻEwa Gentry": "ˈʔe.vɑ ˈdʒen.tɹi",
    "ʻEwa": "ˈʔe.vɑ",
    "Mililani": "mi.liˈlɑ.ni",
    "Makakilo": "mɑ.kɑˈki.lo",
    "Wahiawā": "wɑ.hi.ɑˈwɑː",
    "Waiʻanae": "wɐiˈɑ.nɑe",
    "Nānākuli": "nɑː.nɑːˈku.li",
    "Haleʻiwa": "hɑ.leˈi.vɑ",
    "Lāʻie": "lɑːˈʔi.e",
    "Hauʻula": "hɑuˈʔu.lə",
    "Kahuku": "kɑˈhu.ku",
    "Pūpūkea": "puː.puːˈke.ə",
    "Aiea": "ɑiˈe.ə",
    "Ahuimanu": "ɑ.hu.iˈmɑ.nu",
    "Heʻeia": "heˈʔei.ə",
    "Kahaluʻu": "kɑ.hɑˈlu.ʔu",
    # Maui County
    "Kahului": "kɑ.huˈlu.i",
    "Lāhainā": "lɑːˈhɐi.nɑː",
    "Kīhei": "kiːˈhei",
    "Wailuku": "wɐiˈlu.ku",
    "Makawao": "mɑ.kɑˈwɐu",
    "Hāna": "ˈhɑː.nɑ",
    "Pāʻia": "pɑːˈʔi.ɑ",
    "Pukalani": "pu.kɑˈlɑ.ni",
    "Haʻikū-Pauwela": "hɑˈi.kuː pɑuˈwe.lə",
    "Nāpili-Honokōwai": "nɑːˈpi.li honoˈkoː.wɐi",
    "Kula": "ˈku.lə",
    "Wailea": "wɐiˈle.ə",
    "Kaunakakai": "kɑu.nɑ.kɑˈkɑi",
    "Lānaʻi City": "lɑːˈnɑ.ʔi ˈsɪ.ti",
    "Kāʻanapali": "kɑː.ʔɑ.nɑˈpɑ.li",
    # Kauaʻi County
    "Līhuʻe": "liːˈhu.ʔe",
    "Kapaʻa": "kɑˈpɑ.ʔɑ",
    "Hanalei": "hɑ.nɑˈlei",
    "Poʻipū": "poˈʔi.puː",
    "Kōloa": "koːˈlo.ə",
    "Kalaheo": "kɑ.lɑˈhe.o",
    "Hanamāʻulu": "hɑ.nɑ.mɑːˈʔu.lu",
    "Hanapēpē": "hɑ.nɑˈpeː.peː",
    "Kekaha": "keˈkɑ.hə",
    "Princeville": "ˈpɹɪns.vɪl",
    "Anahola": "ɑ.nɑˈho.lə",
    "ʻEleʻele": "ʔe.leˈʔe.le",
    # Everyday
    "Aloha": "ɑˈlo.hɑ",
    "Mahalo": "mɑˈhɑ.lo",
    "Pele": "ˈpe.le",
}

# English syllable respells for Kokoro G2P. IPA tags sound brutal on Heart/Echo/Nova;
# spaced English words do not. Operator-confirmed: Kīlauea → "Kill ah way uh".
SPEAK_ENGLISH: dict[str, str] = {
    # "wye" not "why" — Kokoro stresses the English question word.
    "Hawaiʻi": "hah wye ee",
    "Hawaiian": "hah wye uhn",
    "Oʻahu": "oh ah hoo",
    "Maui": "mow ee",
    # "kah wah ee" — "cow ah ee" came out livestock + why + ee.
    "Kauaʻi": "kah wah ee",
    "Molokaʻi": "moh loh kah ee",
    "Lānaʻi": "lah nah ee",
    "Niʻihau": "nee ee how",
    "Kahoʻolawe": "kah hoh oh lah vay",
    "Kīlauea": "Kill ah way uh",
    "Mauna Loa": "mow nah low ah",
    "Mauna Kea": "mow nah kay ah",
    "Haleakalā": "hah leh ah kah lah",
    "Hualālai": "hoo ah lah lye",
    "Halemaʻumaʻu": "hah leh mow mow",
    "Hilo": "hee loh",
    "Pāhala": "pah hah lah",
    "Pāhoa": "pah hoh ah",
    "Kailua-Kona": "kye loo ah koh nah",
    "Kona": "koh nah",
    "Waikoloa": "wye koh low ah",
    "Honokaʻa": "hoh noh kah ah",
    "Waimea": "wye may ah",
    "Keaʻau": "kay ah ow",
    "Hāwī": "hah vee",
    "Kapaʻau": "kah pah ow",
    "Kealakekua": "kay ah lah keh koo ah",
    "Hōnaunau-Nāpōʻopoʻo": "hoh now now nah poh oh poh oh",
    "Hōnaunau": "hoh now now",
    "Nāpōʻopoʻo": "nah poh oh poh oh",
    "Captain Cook": "Captain Cook",
    "Mountain View": "Mountain View",
    "Hawaiian Paradise Park": "hah wye uhn Paradise Park",
    "Hawaiian Ocean View": "hah wye uhn Ocean View",
    "Ainaloa": "eye nah low ah",
    "Kurtistown": "Kurtistown",
    "Paukaa": "pow kah ah",
    "Pepeekeo": "peh peh eh kay oh",
    "Laupāhoehoe": "lau pah hoy hoy",
    "Naalehu": "nah ah leh hoo",
    "Nāʻālehu": "nah ah leh hoo",
    "Puna": "poo nah",
    "Kaʻū": "kah oo",
    "Kohala": "koh hah lah",
    "Hāmākua": "hah mah koo ah",
    "Honolulu": "hoh noh loo loo",
    "Waikīkī": "wye kee kee",
    "Kailua": "kye loo ah",
    "Kāneʻohe": "kah neh oh heh",
    "Pearl City": "Pearl City",
    "Waipahu": "wye pah hoo",
    "Kapolei": "kah poh lay",
    "ʻEwa Beach": "eh vah Beach",
    "ʻEwa Gentry": "eh vah Gentry",
    "ʻEwa": "eh vah",
    "Mililani": "mee lee lah nee",
    "Makakilo": "mah kah kee loh",
    "Wahiawā": "wah hee ah vah",
    "Waiʻanae": "wye ah nye",
    "Nānākuli": "nah nah koo lee",
    "Haleʻiwa": "hah leh ee vah",
    "Lāʻie": "lah ee eh",
    "Hauʻula": "how oo lah",
    "Kahuku": "kah hoo koo",
    "Pūpūkea": "poo poo kay ah",
    "Aiea": "eye ay ah",
    "Ahuimanu": "ah hoo ee mah noo",
    "Heʻeia": "heh ay ah",
    "Kahaluʻu": "kah hah loo oo",
    "Kahului": "kah hoo loo ee",
    "Lāhainā": "lah high nah",
    "Kīhei": "kee hay",
    "Wailuku": "wye loo koo",
    "Makawao": "mah kah wow",
    "Hāna": "hah nah",
    "Pāʻia": "pah ee ah",
    "Pukalani": "poo kah lah nee",
    "Haʻikū-Pauwela": "high koo pow well ah",
    "Nāpili-Honokōwai": "nah pee lee hoh noh koh wye",
    "Kula": "koo lah",
    "Wailea": "wye lay ah",
    "Kaunakakai": "cow nah kah kye",
    "Lānaʻi City": "lah nah ee City",
    "Kāʻanapali": "kah ah nah pah lee",
    "Līhuʻe": "lee hoo eh",
    "Kapaʻa": "kah pah ah",
    "Hanalei": "hah nah lay",
    "Poʻipū": "poy poo",
    "Kōloa": "koh low ah",
    "Kalaheo": "kah lah hay oh",
    "Hanamāʻulu": "hah nah mah oo loo",
    "Hanapēpē": "hah nah pay pay",
    "Kekaha": "keh kah hah",
    "Princeville": "Princeville",
    "Anahola": "ah nah hoh lah",
    "ʻEleʻele": "eh leh eh leh",
    "Aloha": "ah loh hah",
    "Mahalo": "mah hah loh",
    "Pele": "peh leh",
}

# ASCII / ascii-okina aliases → canonical PLACE_IPA key (longest match wins).
SPELLING_ALIASES: dict[str, str] = {
    "Hawaii": "Hawaiʻi",
    "Hawai'i": "Hawaiʻi",
    "Hawaiʻi": "Hawaiʻi",
    "Oahu": "Oʻahu",
    "O'ahu": "Oʻahu",
    "Oʻahu": "Oʻahu",
    "Kauai": "Kauaʻi",
    "Kaua'i": "Kauaʻi",
    "Kauaʻi": "Kauaʻi",
    "Molokai": "Molokaʻi",
    "Moloka'i": "Molokaʻi",
    "Molokaʻi": "Molokaʻi",
    "Lanai": "Lānaʻi",
    "Lana'i": "Lānaʻi",
    "Lānaʻi": "Lānaʻi",
    "Niihau": "Niʻihau",
    "Ni'ihau": "Niʻihau",
    "Niʻihau": "Niʻihau",
    "Kahoolawe": "Kahoʻolawe",
    "Kaho'olawe": "Kahoʻolawe",
    "Kahoʻolawe": "Kahoʻolawe",
    "Kilauea": "Kīlauea",
    "Kīlauea": "Kīlauea",
    "Haleakala": "Haleakalā",
    "Haleakalā": "Haleakalā",
    "Hualalai": "Hualālai",
    "Hualālai": "Hualālai",
    "Halemaumau": "Halemaʻumaʻu",
    "Halema'uma'u": "Halemaʻumaʻu",
    "Halemaʻumaʻu": "Halemaʻumaʻu",
    "Pahala": "Pāhala",
    "Pāhala": "Pāhala",
    "Pahoa": "Pāhoa",
    "Pāhoa": "Pāhoa",
    "Kailua Kona": "Kailua-Kona",
    "Kailua-Kona": "Kailua-Kona",
    "Honokaa": "Honokaʻa",
    "Honoka'a": "Honokaʻa",
    "Honokaʻa": "Honokaʻa",
    "Keaau": "Keaʻau",
    "Kea'au": "Keaʻau",
    "Keaʻau": "Keaʻau",
    "Hawi": "Hāwī",
    "Hāwī": "Hāwī",
    "Kapaau": "Kapaʻau",
    "Kapa'au": "Kapaʻau",
    "Kapaʻau": "Kapaʻau",
    "Honaunau-Napoopoo": "Hōnaunau-Nāpōʻopoʻo",
    "Honaunau-Napo'opo'o": "Hōnaunau-Nāpōʻopoʻo",
    "Hōnaunau-Nāpōʻopoʻo": "Hōnaunau-Nāpōʻopoʻo",
    "Honaunau": "Hōnaunau",
    "Hōnaunau": "Hōnaunau",
    "Napoopoo": "Nāpōʻopoʻo",
    "Napo'opo'o": "Nāpōʻopoʻo",
    "Nāpōʻopoʻo": "Nāpōʻopoʻo",
    "Naalehu": "Naalehu",
    "Na'alehu": "Nāʻālehu",
    "Nāʻālehu": "Nāʻālehu",
    "Kau": "Kaʻū",
    "Ka'u": "Kaʻū",
    "Kaʻū": "Kaʻū",
    "Hamakua": "Hāmākua",
    "Hāmākua": "Hāmākua",
    "Waikiki": "Waikīkī",
    "Waikīkī": "Waikīkī",
    "Kaneohe": "Kāneʻohe",
    "Kane'ohe": "Kāneʻohe",
    "Kāneʻohe": "Kāneʻohe",
    "Ewa Beach": "ʻEwa Beach",
    "'Ewa Beach": "ʻEwa Beach",
    "ʻEwa Beach": "ʻEwa Beach",
    "Ewa Gentry": "ʻEwa Gentry",
    "'Ewa Gentry": "ʻEwa Gentry",
    "ʻEwa Gentry": "ʻEwa Gentry",
    "Ewa": "ʻEwa",
    "'Ewa": "ʻEwa",
    "ʻEwa": "ʻEwa",
    "Wahiawa": "Wahiawā",
    "Wahiawā": "Wahiawā",
    "Waianae": "Waiʻanae",
    "Wai'anae": "Waiʻanae",
    "Waiʻanae": "Waiʻanae",
    "Nanakuli": "Nānākuli",
    "Nānākuli": "Nānākuli",
    "Haleiwa": "Haleʻiwa",
    "Hale'iwa": "Haleʻiwa",
    "Haleʻiwa": "Haleʻiwa",
    "Laie": "Lāʻie",
    "La'ie": "Lāʻie",
    "Lāʻie": "Lāʻie",
    "Hauula": "Hauʻula",
    "Hau'ula": "Hauʻula",
    "Hauʻula": "Hauʻula",
    "Pupukea": "Pūpūkea",
    "Pūpūkea": "Pūpūkea",
    "Heeia": "Heʻeia",
    "He'eia": "Heʻeia",
    "Heʻeia": "Heʻeia",
    "Kahaluu": "Kahaluʻu",
    "Kahalu'u": "Kahaluʻu",
    "Kahaluʻu": "Kahaluʻu",
    "Lahaina": "Lāhainā",
    "Lāhainā": "Lāhainā",
    "Kihei": "Kīhei",
    "Kīhei": "Kīhei",
    "Hana": "Hāna",
    "Hāna": "Hāna",
    "Paia": "Pāʻia",
    "Pa'ia": "Pāʻia",
    "Pāʻia": "Pāʻia",
    "Haiku-Pauwela": "Haʻikū-Pauwela",
    "Ha'iku-Pauwela": "Haʻikū-Pauwela",
    "Haʻikū-Pauwela": "Haʻikū-Pauwela",
    "Napili-Honokowai": "Nāpili-Honokōwai",
    "Nāpili-Honokōwai": "Nāpili-Honokōwai",
    "Lanai City": "Lānaʻi City",
    "Lānaʻi City": "Lānaʻi City",
    "Kaanapali": "Kāʻanapali",
    "Ka'anapali": "Kāʻanapali",
    "Kāʻanapali": "Kāʻanapali",
    "Lihue": "Līhuʻe",
    "Lihu'e": "Līhuʻe",
    "Līhuʻe": "Līhuʻe",
    "Kapaa": "Kapaʻa",
    "Kapa'a": "Kapaʻa",
    "Kapaʻa": "Kapaʻa",
    "Poipu": "Poʻipū",
    "Po'ipu": "Poʻipū",
    "Poʻipū": "Poʻipū",
    "Koloa": "Kōloa",
    "Kōloa": "Kōloa",
    "Hanamaulu": "Hanamāʻulu",
    "Hanama'ulu": "Hanamāʻulu",
    "Hanamāʻulu": "Hanamāʻulu",
    "Hanapepe": "Hanapēpē",
    "Hanapēpē": "Hanapēpē",
    "Eleele": "ʻEleʻele",
    "'Ele'ele": "ʻEleʻele",
    "ʻEleʻele": "ʻEleʻele",
    "Laupahoehoe": "Laupāhoehoe",
    "Laupāhoehoe": "Laupāhoehoe",
    "Maui": "Maui",
    "Hilo": "Hilo",
    "Honolulu": "Honolulu",
    "Mauna Loa": "Mauna Loa",
    "Mauna Kea": "Mauna Kea",
    "Waimea": "Waimea",
    "Waikoloa": "Waikoloa",
    "Kealakekua": "Kealakekua",
    "Captain Cook": "Captain Cook",
    "Mountain View": "Mountain View",
    "Hawaiian Paradise Park": "Hawaiian Paradise Park",
    "Hawaiian Ocean View": "Hawaiian Ocean View",
    "Ainaloa": "Ainaloa",
    "Kurtistown": "Kurtistown",
    "Paukaa": "Paukaa",
    "Pepeekeo": "Pepeekeo",
    "Puna": "Puna",
    "Kona": "Kona",
    "Kohala": "Kohala",
    "Pearl City": "Pearl City",
    "Waipahu": "Waipahu",
    "Kapolei": "Kapolei",
    "Mililani": "Mililani",
    "Makakilo": "Makakilo",
    "Kahuku": "Kahuku",
    "Aiea": "Aiea",
    "Ahuimanu": "Ahuimanu",
    "Kahului": "Kahului",
    "Wailuku": "Wailuku",
    "Makawao": "Makawao",
    "Pukalani": "Pukalani",
    "Kula": "Kula",
    "Wailea": "Wailea",
    "Kaunakakai": "Kaunakakai",
    "Kailua": "Kailua",
    "Hanalei": "Hanalei",
    "Kalaheo": "Kalaheo",
    "Kekaha": "Kekaha",
    "Princeville": "Princeville",
    "Anahola": "Anahola",
    "Hawaiian": "Hawaiian",
    "Aloha": "Aloha",
    "Mahalo": "Mahalo",
    "Pele": "Pele",
}

# Kokoro US vocab (model config) — allow IPA marks used in PLACE_IPA after ʔ strip.
US_VOCAB = frozenset(
    " !\"(),.:;?AIOQSTWYabcdefhijklmnopqrstuvwxyz"
    "æçðøŋœɐɑɒɔɕɖəɚɛɜɟɡɣɤɥɨɪɯɰɲɳɴɸɹɻɽɾʁʂʃʈʊʋʌʎʒʔʝ"
    "ʣʤʥʦʧʨʰʲˈˌː̃βθχᵊᵝᵻ—“”…→↓↗↘ʦ"
    "ɝɒʊæ"
)

# Back-compat names used by older diagnose / tests.
PLACE_PHONEMES: dict[str, str] = {}
SPEAK_AS: dict[str, str] = {}
HAWAIIAN_KEYS: frozenset[str] = frozenset()
KILAUEA = ""


def kokoro_ipa(ipa: str) -> str:
    """Strip glottal stops — Misaki replaces ʔ with t."""
    out = (ipa or "").replace("ʔ", "")
    out = re.sub(r"\.\.+", ".", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


def ipa_tag(name: str, ipa: str) -> str:
    return f"[{name}](/{kokoro_ipa(ipa)}/)"


def _rebuild_derived() -> None:
    global PLACE_PHONEMES, SPEAK_AS, HAWAIIAN_KEYS, KILAUEA
    # PLACE_PHONEMES kept for diagnose tools; voice path uses SPEAK_ENGLISH only.
    PLACE_PHONEMES = {
        alias: kokoro_ipa(PLACE_IPA[canon])
        for alias, canon in SPELLING_ALIASES.items()
        if canon in PLACE_IPA
    }
    for canon, ipa in PLACE_IPA.items():
        PLACE_PHONEMES[canon] = kokoro_ipa(ipa)
        PLACE_PHONEMES[canon.lower()] = kokoro_ipa(ipa)
    SPEAK_AS = dict(SPEAK_ENGLISH)
    HAWAIIAN_KEYS = frozenset(PLACE_IPA)
    KILAUEA = SPEAK_ENGLISH["Kīlauea"]


_rebuild_derived()

# Longest alias first so "Hawaiian Paradise Park" wins over "Hawaiian".
_ALIAS_ORDER = sorted(SPELLING_ALIASES.keys(), key=len, reverse=True)
_ALIAS_RE = re.compile(
    r"(?<!\[)\b(" + "|".join(re.escape(a) for a in _ALIAS_ORDER) + r")\b",
    flags=re.IGNORECASE,
)
_EXISTING_TAG_RE = re.compile(r"\[([^\]]+)\]\(/[^)]+/\)")


def fold_place_spellings(text: str) -> str:
    """Normalize okina spellings to ASCII aliases for matching."""
    out = text or ""
    folds = (
        ("Hawaiʻi", "Hawaii"),
        ("Hawai'i", "Hawaii"),
        ("Kīlauea", "Kilauea"),
        ("Oʻahu", "Oahu"),
        ("O'ahu", "Oahu"),
        ("Kauaʻi", "Kauai"),
        ("Kaua'i", "Kauai"),
        ("Molokaʻi", "Molokai"),
        ("Moloka'i", "Molokai"),
        ("Lānaʻi", "Lanai"),
        ("Lana'i", "Lanai"),
        ("Niʻihau", "Niihau"),
        ("Ni'ihau", "Niihau"),
        ("Kahoʻolawe", "Kahoolawe"),
        ("Kaho'olawe", "Kahoolawe"),
        ("Halemaʻumaʻu", "Halemaumau"),
        ("Halema'uma'u", "Halemaumau"),
        ("Haleakalā", "Haleakala"),
        ("Hualālai", "Hualalai"),
        ("Pāhala", "Pahala"),
        ("Pāhoa", "Pahoa"),
        ("Honokaʻa", "Honokaa"),
        ("Honoka'a", "Honokaa"),
        ("Keaʻau", "Keaau"),
        ("Kapaʻau", "Kapaau"),
        ("Hāwī", "Hawi"),
        ("Hōnaunau", "Honaunau"),
        ("Nāpōʻopoʻo", "Napoopoo"),
        ("Napo'opo'o", "Napoopoo"),
        ("Nāʻālehu", "Naalehu"),
        ("Na'alehu", "Naalehu"),
        ("Kaʻū", "Kau"),
        ("Ka'u", "Kau"),
        ("Hāmākua", "Hamakua"),
        ("Waikīkī", "Waikiki"),
        ("Kāneʻohe", "Kaneohe"),
        ("Kane'ohe", "Kaneohe"),
        ("ʻEwa", "Ewa"),
        ("'Ewa", "Ewa"),
        ("Wahiawā", "Wahiawa"),
        ("Waiʻanae", "Waianae"),
        ("Wai'anae", "Waianae"),
        ("Nānākuli", "Nanakuli"),
        ("Haleʻiwa", "Haleiwa"),
        ("Lāʻie", "Laie"),
        ("Hauʻula", "Hauula"),
        ("Pūpūkea", "Pupukea"),
        ("Heʻeia", "Heeia"),
        ("Kahaluʻu", "Kahaluu"),
        ("Lāhainā", "Lahaina"),
        ("Kīhei", "Kihei"),
        ("Hāna", "Hana"),
        ("Pāʻia", "Paia"),
        ("Kāʻanapali", "Kaanapali"),
        ("Līhuʻe", "Lihue"),
        ("Lihu'e", "Lihue"),
        ("Kapaʻa", "Kapaa"),
        ("Poʻipū", "Poipu"),
        ("Kōloa", "Koloa"),
        ("Hanamāʻulu", "Hanamaulu"),
        ("Hanapēpē", "Hanapepe"),
        ("ʻEleʻele", "Eleele"),
        ("Laupāhoehoe", "Laupahoehoe"),
        ("Honaunau-Napoopoo", "Honaunau-Napoopoo"),
        ("Hōnaunau-Nāpōʻopoʻo", "Honaunau-Napoopoo"),
    )
    for src, dest in folds:
        out = out.replace(src, dest)
        out = out.replace(src.lower(), dest)
        out = out.replace(src.upper(), dest)
    return out


def _english_for(canon: str) -> str:
    return SPEAK_ENGLISH.get(canon) or canon


def pronounce_places(text: str) -> str:
    """Replace place names with spaced English syllables Kokoro can say."""
    out = text or ""

    def _from_tag(m: re.Match) -> str:
        raw = m.group(1)
        for alias in _ALIAS_ORDER:
            if alias.lower() == raw.lower() or SPELLING_ALIASES.get(alias, "").lower() == raw.lower():
                canon = SPELLING_ALIASES[alias]
                return _english_for(canon)
        # Tag name may already be canonical orthography.
        if raw in SPEAK_ENGLISH:
            return SPEAK_ENGLISH[raw]
        return raw

    out = _EXISTING_TAG_RE.sub(_from_tag, out)

    def _wrap(m: re.Match) -> str:
        raw = m.group(1)
        canon = None
        for alias in _ALIAS_ORDER:
            if alias.lower() == raw.lower():
                canon = SPELLING_ALIASES[alias]
                break
        if not canon:
            return raw
        return _english_for(canon)

    out = _ALIAS_RE.sub(_wrap, out)
    return out


def lexicon_entries() -> dict[str, str]:
    """No place-name golds — English respells must hit normal G2P."""
    return {}


DIAGNOSE_NAMES = (
    "Hawaii",
    "Hawaiian",
    "Kilauea",
    "Hilo",
    "Honolulu",
    "Puna",
    "Kona",
    "Kau",
    "Mauna Loa",
    "Mauna Kea",
    "Oahu",
    "Maui",
    "Kauai",
    "Molokai",
    "Lanai",
    "Niihau",
    "Kahoolawe",
    "Lihue",
    "Pahoa",
    "Halemaumau",
    "Waikiki",
    "Lahaina",
    "Haleakala",
    "Kaneohe",
    "Waianae",
    "Ewa",
    "Kohala",
    "Aloha",
    "Mahalo",
    "Pele",
    "Mountain View",
    "Captain Cook",
    "Pahala",
    "Waimea",
    "Kihei",
)
