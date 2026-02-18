RASI_NAMES = [
        "मेष", "बृष", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "बृश्चिक", "धनु", "मकर", "कुम्भ", "मिन"
    ]
# Add these constants at the top with other planetary data
DIVISION_NAMES={
        1: "राशि कुण्डली - D1",   # D1
        2: "होरा कुण्डली - D2",   # D2
        3: "दृष्टांश कुण्डली - D3", # D3
        4: "चतुर्थांश कुण्डली - D4", # D4
        5: "पंचमांश कुण्डली - D5",  # D5
        6: "षष्ठांश कुण्डली - D6",  # D6
        7: "सप्तमांश कुण्डली - D7", # D7
        8: "अष्टमांश कुण्डली - D8", #D8
        9: "नवमांश कुण्डली - D9", # D9
        10: "दशमांश कुण्डली - D10",  # D10
        12: "द्वादशांश कुण्डली - D12",# D12
        16: "षोडशांश कुण्डली - D16",  # D16
        20: "विंशांश कुण्डली - D20",   # D20
        24: "सिद्धांश कुण्डली - D24",  # D24
        27: "भाम्शा कुण्डली - D27",   # D27
        30: "त्रिंशांश कुण्डली - D30", # D30
        40: "खवेदांश कुण्डली - D40",  # D40
        45: "अक्षणविंशांश कुण्डली - D45", # D45
        60: "षष्ट्यांश कुण्डली - D60", # D60
        81: "नवांशोत्तरषष्ट्यांश कुण्डली - D81", # D81
        108: "अष्टोत्तरसप्ततिअंश कुण्डली - D108",  # D108
        144: "चतुःचत्वारिंशांश कुण्डली - D144",     # D144
        150: "शतपञ्चांश कुण्डली - D150"             # D150
}
MOOLA_DASHA_YEARS = {
    "सु": 6, "चं": 10, "मं": 7, "बु": 17, "गु": 16,
    "शु": 20, "श": 19, "रा": 18, "के": 7
}
rasi_names = [
            "मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या",
            "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"
        ]
nakshatras = [
            "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
            "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वफाल्गुनी", "उत्तरफाल्गुनी",
            "हस्त", "चित्रा", "स्वाति", "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल",
            "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वभाद्रपदा",
            "उत्तरभाद्रपदा", "रेवती"
        ]
TITHI_NAMES = [
    "शुक्ल प्रतिपदा", "शुक्ल द्वितिया", "शुक्ल तृतिया", "शुक्ल चतुर्थी", "शुक्ल पञ्चमि",
    "शुक्ल षष्ठि", "शुक्ल सप्तमी", "शुक्ल अष्ठमी", "शुक्ल नवमी", "शुक्ल दशमी",
    "शुक्ल एकादशी", "शुक्ल द्वादशी", "शुक्ल त्रयोदशी", "शुक्ल चतुर्दशी", "पुर्णीमा",
    "कृष्ण प्रतिपदा", "कृष्ण द्वितिया", "कृष्ण तृतिया", "कृष्ण चतुर्थी", "कृष्ण पञ्चमि",
    "कृष्ण षष्ठि", "कृष्ण सप्तमी", "कृष्ण अष्ठमी", "कृष्ण नवमी", "कृष्ण दशमी",
    "कृष्ण एकादशी", "कृष्ण द्वादशी", "कृष्ण त्रयोदशी", "कृष्ण चतुर्दशी", "अमावस्या"
]

NAKSHATRA_NAMES = [
    "अश्विनी", "भरणी", "कृतिका", "रोहिनी", "मृगशिरा", "आद्र", "पुनर्वशु", "पुष्य", "अश्लेशा",
    "मघा", "पुर्व फाल्गुनी", "उत्तर फाल्गुनी", "हस्ता", "चित्रा", "स्वाति", "विशाखा", "अनुराधा",
    "ज्येष्ठा", "मुला", "पुर्व अषाढा", "उत्तर अषाढा", "श्रवण", "धनिष्ठा", "शतभिषा",
    "पुर्व भाद्रपदा", "उत्तर भाद्रपदा", "रेवती"
]
YOGA_NAMES = [
    "विषकुम्भ", "प्रिती", "आयुश्मान", "सौभाग्य", "सोभाना", "अतिगन्दा", "शुक्रमान", "धृती", "शुल",
    "गन्दा", "बृद्धी", "ध्रुव", "व्यघटा", "हर्षना", "बज्र", "सिद्दी", "व्यतिपात", "बरियाना",
    "परिघ", "शिव", "सिद्द", "सध्या", "शुभ", "शुक्ल", "ब्रह्मा", "इन्द्र", "बैधृती"
]

KARANA_NAMES = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि", "शकुनि", "चतुष्पद", "नाग", "किंस्तुघ्न"]

VEDIC_WEEKDAYS = [  # Starting from Sunday
    "आइतबार", "सोमबार", "मंगरबार", "बुधबार",
    "बिहिबार", "शुक्रबार", "शनिबार"
]
fixed_karanas = {
        0: "किंस्तुघ्न",  # Amavasya, 2nd half
        1: "शकुनि",     # Shukla Pratipada, 1st half
        2: "चतुष्पद",   # Shukla Pratipada, 2nd half
        3: "नाग"        # Shukla Dwitiya, 1st half
    }
month_names = [
            "बैशाख", "ज्येष्ठ", "अषाढ", "श्रावण",
            "भाद्र",   "अश्विन","कार्तिक","मंसिर",
            "पौष",     "माघ",   "फाल्गुण","चैत्र"
        ]
NADI_MAP = [
    "आदि", "मध्य", "अन्त्य",   # 0-2: Ashwini, Bharani, Krittika
    "आदि", "मध्य", "अन्त्य",   # 3-5: Rohini, Mrigashira, Ardra
    "आदि", "मध्य", "अन्त्य",   # 6-8: Punarvasu, Pushya, Ashlesha
    "आदि", "मध्य", "अन्त्य",   # 9-11: Magha, Purva Phalguni, Uttara Phalguni
    "आदि", "मध्य", "अन्त्य",   # 12-14: Hasta, Chitra, Swati
    "आदि", "मध्य", "अन्त्य",   # 15-17: Vishakha, Anuradha, Jyeshtha
    "आदि", "मध्य", "अन्त्य",   # 18-20: Mula, Purva Ashadha, Uttara Ashadha
    "आदि", "मध्य", "अन्त्य",   # 21-23: Shravana, Dhanishtha, Shatabhisha
    "आदि", "मध्य", "अन्त्य"    # 24-26: Purva Bhadrapada, Uttara Bhadrapada, Revati
]

GANA_MAP = [
    "देव",     # अश्विनी
    "मनुष्य",  # भरणी
    "राक्षस",  # कृत्तिका
    "मनुष्य",  # रोहिणी
    "देव",     # मृगशिरा
    "मनुष्य",  # आर्द्रा
    "देव",     # पुनर्वसु
    "देव",     # पुष्य
    "राक्षस",  # आश्लेषा
    "राक्षस",  # मघा
    "मनुष्य",  # पूर्व फाल्गुनी
    "मनुष्य",  # उत्तर फाल्गुनी
    "देव",     # हस्त
    "राक्षस",  # चित्रा
    "देव",     # स्वाती
    "राक्षस",  # विशाखा
    "देव",     # अनुराधा
    "राक्षस",  # ज्येष्ठा
    "राक्षस",  # मूल
    "मनुष्य",  # पूर्वाषाढा
    "मनुष्य",  # उत्तराषाढा
    "देव",     # श्रवण
    "राक्षस",  # धनिष्ठा
    "राक्षस",  # शतभिषा
    "मनुष्य",  # पूर्व भाद्रपद
    "मनुष्य",  # उत्तर भाद्रपद
    "देव"      # रेवती
]
YONI_MAP = [
    "अश्व",     # 0. अश्विनी - Horse (Male)
    "गज",       # 1. भरणी - Elephant (Male)
    "मेष",      # 2. कृत्तिका - Sheep (Female)
    "सर्प",     # 3. रोहिणी - Serpent/Snake (Male)
    "सर्प",     # 4. मृगशिरा - Serpent (Female) [FIXED]
    "श्वान",    # 5. आर्द्रा - Dog (Female) [FIXED]
    "मार्जार",  # 6. पुनर्वसु - Cat (Male) [FIXED]
    "मेष",      # 7. पुष्य - Sheep/Goat (Male) [FIXED]
    "मार्जार",  # 8. आश्लेषा - Cat (Male) [FIXED]
    "मूषक",     # 9. मघा - Rat (Male) [FIXED]
    "मूषक",     # 10. पूर्व फाल्गुनी - Rat (Female) [FIXED]
    "गौ",       # 11. उत्तर फाल्गुनी - Cow (Male) [FIXED]
    "महिष",     # 12. हस्त - Buffalo (Female) [FIXED]
    "व्याघ्र",  # 13. चित्रा - Tiger (Female) [FIXED]
    "महिष",     # 14. स्वाति - Buffalo (Male) [FIXED]
    "व्याघ्र",  # 15. विशाखा - Tiger (Male) [FIXED]
    "मृग",      # 16. अनुराधा - Deer (Female) [FIXED]
    "मृग",      # 17. ज्येष्ठा - Deer (Male) [FIXED]
    "श्वान",    # 18. मूल - Dog (Male)
    "वानर",     # 19. पूर्वाषाढा - Monkey (Male) [FIXED]
    "नकुल",     # 20. उत्तराषाढा - Mongoose (Female) [FIXED]
    "वानर",     # 21. श्रवण - Monkey (Female) [FIXED]
    "सिंह",     # 22. धनिष्ठा - Lion (Female) [FIXED]
    "अश्व",     # 23. शतभिषा - Horse (Male) [FIXED]
    "सिंह",     # 24. पूर्व भाद्रपदा - Lion (Female) [FIXED]
    "गौ",       # 25. उत्तर भाद्रपदा - Cow (Female) [FIXED]
    "गज"       # 26. रेवती - Elephant (Female) [FIXED]
]
PADA_SPAN = 360.0 / 27.0 / 4.0   # 3.333333...

NAAM_AKSHAR_MAP = [
    ["चू", "चे", "चो", "ला"],   # 1. Ashwini
    ["ली", "लू", "ले", "लो"],   # 2. Bharani
    ["अ", "ई", "उ", "ए"],       # 3. Krittika
    ["ओ", "वा", "वी", "वू"],     # 4. Rohini
    ["वे", "वो", "का", "की"],   # 5. Mrigashira
    ["कू", "घ", "ङ", "छ"],      # 6. Ardra
    ["के", "को", "हा", "ही"],   # 7. Punarvasu
    ["हू", "हे", "हो", "डा"],   # 8. Pushya
    ["डी", "डू", "डे", "डो"],   # 9. Ashlesha
    ["मा", "मी", "मू", "मे"],   # 10. Magha
    ["मो", "टा", "टी", "टू"],   # 11. Purva Phalguni
    ["टे", "टो", "पा", "पी"],   # 12. Uttara Phalguni
    ["पू", "ष", "ण", "ठ"],      # 13. Hasta
    ["पे", "पो", "रा", "री"],   # 14. Chitra
    ["रू", "रे", "रो", "ता"],   # 15. Swati
    ["ती", "तू", "ते", "तो"],   # 16. Vishakha
    ["ना", "नी", "नू", "ने"],   # 17. Anuradha
    ["नो", "या", "यी", "यू"],   # 18. Jyeshtha
    ["ये", "यो", "भा", "भी"],   # 19. Mula
    ["भू", "ध", "फ", "ढ"],      # 20. Purva Ashadha (Bhu, Dha, Pha, Dha)
    ["भे", "भो", "जा", "जी"],   # 21. Uttara Ashadha
    ["खी", "खू", "खे", "खो"],   # 22. Shravana (Corrected: Khi, Khu, Khe, Kho)
    ["गा", "गी", "गू", "गे"],   # 23. Dhanishta (Corrected: Ga, Gi, Gu, Ge)
    ["गो", "सा", "सी", "सू"],   # 24. Shatabhisha (Corrected: Go, Sa, Si, Su)
    ["से", "सो", "दा", "दी"],   # 25. Purva Bhadrapada (Corrected: Se, So, Da, Di)
    ["दू", "थ", "झ", "ञ"],      # 26. Uttara Bhadrapada (Corrected: Du, Tha, Jha, Tra/Na)
    ["दे", "दो", "च", "ची"]     # 27. Revati (Corrected: De, Do, Cha, Chi)
]
ARUDHA_NAMES = {
        1: "A1 (AL)",
        2: "A2 (D-2)",
        3: "A3",
        4: "A4",
        5: "A5",
        6: "A6",
        7: "A7",
        8: "A8",
        9: "A9",
        10: "A10",
        11: "A11",
        12: "A12 (UL)"
    }
RASHI_LORDS = {
        0: "मं",   # Mars rules Aries (0)
        1: "शु",   # Venus rules Taurus (1)
        2: "बु",   # Mercury rules Gemini (2)
        3: "चं",   # Moon rules Cancer (3)
        4: "सु",   # Sun rules Leo (4)
        5: "बु",   # Mercury rules Virgo (5)
        6: "शु",   # Venus rules Libra (6)
        7: "मं",   # Mars rules Scorpio (7)
        8: "गु",   # Jupiter rules Sagittarius (8)
        9: "श",    # Saturn rules Capricorn (9)
        10: "श",   # Saturn rules Aquarius (10)
        11: "गु"   # Jupiter rules Pisces (11)
    }
# --- Font Configuration ---
planet_map_en_to_dev = {
    'Su': 'सु', 'Mo': 'चं', 'Ma': 'मं',
    'Me': 'बु', 'Ju': 'गु', 'Ve': 'शु',
    'Sa': 'श', 'Ra': 'रा', 'Ke': 'के'
}
DEV_FONT_FAMILY = "Mangal"
FALLBACK_FONTS = ["Noto Sans Devanagari", "Mangal", "Nirmala UI", "Arial"]
DEV_FONT_SIZE = 10
devanagari_font_tuple = (DEV_FONT_FAMILY, DEV_FONT_SIZE)
# --- Constants (Aligned with generate_moola_dasha_tree) ---
PLANET_OWN_SIGNS = {
    "सु": ["Leo"], "चं": ["Cancer"], "मं": ["Aries", "Scorpio"],
    "बु": ["Gemini", "Virgo"], "गु": ["Sagittarius", "Pisces"],
    "शु": ["Taurus", "Libra"], "श": ["Capricorn", "Aquarius"],
    "रा": [], "के": []  # Rahu/Ketu don't own signs
}
PLANET_FRIENDS = {
    "सु": ["चं", "मं", "गु"], 
    "चं": ["सु", "बु"], 
    "मं": ["सु", "चं", "गु"],  # Moon is friend to Mars
    "बु": ["सु", "शु"], 
    "गु": ["सु", "चं", "मं"], 
    "शु": ["बु", "श"],  # Venus-Saturn friendship
    "श": ["शु", "रा", "के"],  # Saturn friends
    "रा": ["श", "के"], 
    "के": ["श", "रा"]
}

COMBUSTION_LIMITS = {
    "सु": 0, "चं": 11, "मं": 17, "बु": 14, "गु": 11, "शु": 10, "श": 8, "रा": 8, "के": 8
}
MOOLATRIKONA_SIGNS = {
    "सु": ("Leo", 0, 20),         # Sun: Leo 0–20°
    "चं": ("Taurus", 3, 30),      # Moon: Taurus 3–30°
    "मं": ("Aries", 0, 12),       # Mars: Aries 0–12°
    "बु": ("Virgo", 15, 20),       # Mercury: Virgo 15–20°
    "गु": ("Sagittarius", 0, 10),  # Jupiter: Sagittarius 0–10°
    "शु": ("Libra", 0, 15),        # Venus: Libra 0–15°
    "श": ("Aquarius", 0, 20),      # Saturn: Aquarius 0–20°
    "रा": None, "के": None
}
EXALTATION_POINTS = {
    "सु": 10, "चं": 33, "मं": 298,
    "बु": 165, "गु": 95, "शु": 357,
    "श": 200, "रा": 45, "के": 225
}

DEBILITATION_POINTS = {
    "सु": 190, "चं": 213, "मं": 118,
    "बु": 345, "गु": 275, "शु": 177,
    "श": 20, "रा": 225, "के": 45
}

NAISARGIKA_BALA = {
    "सु": 60, "चं": 51, "मं": 45,
    "बु": 36, "गु": 30, "शु": 42,
    "श": 18, "रा": 27, "के": 27
}

DIG_BALA_HOUSE = {
    "सु": 10,  # 10th house (Midheaven)
    "चं": 4,   # 4th house (Nadir)
    "मं": 1,   # 1st house (East)
    "बु": 1,   # 1st house (East)
    "गु": 9,   # 9th house (North-East)
    "शु": 4,   # 4th house (Nadir)
    "श": 7,    # 7th house (West)
    "रा": 7,   # 7th house (West)
    "के": 7    # 7th house (West)
}

BENEFICS = {"गु", "शु", "चं"}
MALEFICS = {"सु", "मं", "श", "के", "रा"}
ASPECTS = {
    "सु": [7], "चं": [7], "मं": [4, 7, 8],
    "बु": [7], "गु": [5, 7, 9], "शु": [7],
    "श": [3, 7, 10], "रा": [3, 7, 11], "के": [3, 7, 11]
}

AVASTHA_MULTIPLIERS = {
    "Baladi": [1.0, 0.75, 0.5, 0.33, 0.25],
    "Jagradadi": [1.5, 1.0, 0.75]
}
# Sign-based relationships (Friendly, Neutral, Enemy) based on sign rulership
PLANET_SIGN_RELATIONSHIPS = {
    "सु": {"Friendly": ["Leo", "Cancer", "Aries", "Scorpio", "Sagittarius", "Pisces"],
           "Neutral": ["Taurus", "Libra", "Capricorn", "Aquarius"],
           "Enemy": ["Gemini", "Virgo"]},
    "चं": {"Friendly": ["Cancer", "Leo", "Gemini", "Virgo"],
           "Neutral": ["Aries", "Scorpio", "Sagittarius", "Pisces", "Taurus", "Libra", "Capricorn", "Aquarius"],
           "Enemy": []},
    "मं": {"Friendly": ["Aries", "Scorpio", "Leo", "Sagittarius", "Pisces"],
           "Neutral": ["Gemini", "Virgo", "Cancer"],
           "Enemy": ["Taurus", "Libra", "Capricorn", "Aquarius"]},
    "बु": {"Friendly": ["Gemini", "Virgo", "Taurus", "Libra"],
           "Neutral": ["Aries", "Scorpio", "Sagittarius", "Pisces", "Aquarius"],
           "Enemy": ["Leo", "Cancer", "Capricorn"]},
    "गु": {"Friendly": ["Sagittarius", "Pisces", "Leo", "Cancer", "Aries", "Scorpio"],
           "Neutral": ["Taurus", "Libra"],
           "Enemy": ["Gemini", "Virgo", "Capricorn", "Aquarius"]},
    "शु": {"Friendly": ["Taurus", "Libra", "Gemini", "Virgo", "Capricorn", "Aquarius"],
           "Neutral": ["Sagittarius", "Pisces"],
           "Enemy": ["Leo", "Cancer", "Aries", "Scorpio"]},
    "श": {"Friendly": ["Capricorn", "Aquarius", "Taurus", "Libra"],
           "Neutral": ["Gemini", "Virgo"],
           "Enemy": ["Leo", "Cancer", "Aries", "Scorpio", "Sagittarius", "Pisces"]},
    "रा": {"Friendly": ["Taurus", "Libra", "Capricorn", "Aquarius"],
           "Neutral": ["Gemini", "Virgo", "Sagittarius", "Pisces"],
           "Enemy": ["Leo", "Cancer", "Aries", "Scorpio"]},
    "के": {"Friendly": ["Taurus", "Libra", "Capricorn", "Aquarius"],
           "Neutral": ["Gemini", "Virgo", "Sagittarius", "Pisces"],
           "Enemy": ["Leo", "Cancer", "Aries", "Scorpio"]}
}
DAY_PLANETS = {"सु", "मं", "गु"}
NIGHT_PLANETS = {"चं", "शु", "श"}
NEUTRAL_PLANETS = {"बु"}

DIGNITY_WEIGHTS = {
    "Exalted": 6,       # Highest weight
    "Moolatrikona": 5,  # Slightly less than exaltation
    "Own Sign": 4,
    "Friendly": 3,
    "Neutral": 2,
    "Enemy": 1,
    "Debilitated": 0,
    "Vargottama": 4.5   # Between own sign and moolatrikona
}

# --- New Constants for Planet Status ---
RASI_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
ODD_SIGNS = {"Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"}
BALADI_STATES_ODD = ["Child", "Youth", "Adult", "Old", "Dead"]
BALADI_STATES_EVEN = ["Dead", "Old", "Adult", "Youth", "Child"]
YOGINI_NAMES = [
    "मंगला", "पिंगला", "धन्या", "भ्रमरी",
    "भद्रिका", "उल्का", "सिद्धा", "संकटा"
]

YOGINI_YEARS = [1, 2, 3, 4, 5, 6, 7, 8]
NAKSHATRA_SPAN = 360.0 / 27.0