from varr import planet_map_en_to_dev, PLANET_OWN_SIGNS, ODD_SIGNS, COMBUSTION_LIMITS, MOOLATRIKONA_SIGNS, EXALTATION_POINTS, DEBILITATION_POINTS, NAISARGIKA_BALA, DIG_BALA_HOUSE, BENEFICS, MALEFICS, ASPECTS, AVASTHA_MULTIPLIERS, PLANET_SIGN_RELATIONSHIPS, DAY_PLANETS,NIGHT_PLANETS, NEUTRAL_PLANETS, DIGNITY_WEIGHTS, RASI_SIGNS, BALADI_STATES_EVEN, BALADI_STATES_ODD
# --- Calculation Functions ---

def get_house_number(planet_deg, asc_deg):
    """Calculate house number for a planet relative to ascendant."""
    if not (0 <= planet_deg < 360 and 0 <= asc_deg < 360):
        return 1  # Default to 1st house for invalid inputs
    asc_sign = int(asc_deg / 30) % 12
    planet_sign = int(planet_deg / 30) % 12
    return (planet_sign - asc_sign + 12) % 12 + 1

def get_planet_state(planet, degree, positions, divisional_dignities):
    if degree is None or not positions:
        return None, "Normal", 1.0, "Normal"

    sign_index = int(degree / 30) % 12
    sign_name = RASI_SIGNS[sign_index]
    degree_in_sign = degree % 30

    primary_state = None
    multiplier = 1.0
    sign_dignity = "Normal"
    dignity_multiplier = 1.0

    # Combustion
    if planet not in ["सु", "रा", "के"]:
        sun_deg = positions.get("सु")
        if sun_deg is not None:
            diff_sun = min((degree - sun_deg) % 360, (sun_deg - degree) % 360)
            if diff_sun <= COMBUSTION_LIMITS.get(planet, 8):
                primary_state = "Combust"
                multiplier *= 0.25

    # Exaltation (within 3° orb)
    exaltation = EXALTATION_POINTS.get(planet)
    if exaltation is not None:
        diff_exalt = min((degree - exaltation) % 360, (exaltation - degree) % 360)
        if diff_exalt <= 3:
            primary_state = "Exalted"
            multiplier *= 1.5

    # Debilitation (within 3° orb)
    debilitation = DEBILITATION_POINTS.get(planet)
    if debilitation is not None:
        diff_debil = min((degree - debilitation) % 360, (debilitation - degree) % 360)
        if diff_debil <= 3:
            primary_state = "Debilitated"
            multiplier *= 0.5

    # Sign-Based Dignity
    moola_info = MOOLATRIKONA_SIGNS.get(planet)
    if moola_info and moola_info[0] == sign_name and moola_info[1] <= degree_in_sign <= moola_info[2]:
        sign_dignity = "Moolatrikona"
        dignity_multiplier = 1.4
    elif sign_name in PLANET_OWN_SIGNS.get(planet, []):
        sign_dignity = "Own Sign"
        dignity_multiplier = 1.3
    elif divisional_dignities.get(planet, {}).get("D1") == divisional_dignities.get(planet, {}).get("D9"):
        sign_dignity = "Vargottama"
        dignity_multiplier = 1.35
    else:
        sign_relations = PLANET_SIGN_RELATIONSHIPS.get(planet, {})
        if sign_name in sign_relations.get("Friendly", []):
            sign_dignity = "Friendly"
            dignity_multiplier = 1.2
        elif sign_name in sign_relations.get("Neutral", []):
            sign_dignity = "Neutral"
            dignity_multiplier = 1.0
        elif sign_name in sign_relations.get("Enemy", []):
            sign_dignity = "Enemy"
            dignity_multiplier = 0.8

    multiplier *= dignity_multiplier
    combined_state = f"{primary_state}, {sign_dignity}" if primary_state else sign_dignity
    return primary_state, sign_dignity, multiplier, combined_state

def calculate_planet_status(planet, degree):
    """Calculate Baladi Avastha state based on planet degree and Rasi sign."""
    if degree is None:
        return "Unknown"
    sign_index = int(degree / 30) % 12
    sign_name = RASI_SIGNS[sign_index]
    is_odd_sign = sign_name in ODD_SIGNS
    position_in_sign = degree % 30
    avastha_segment = int(position_in_sign / 6)
    avastha_segment = min(avastha_segment, 4)  # Ensure index is within bounds
    state = BALADI_STATES_ODD[avastha_segment] if is_odd_sign else BALADI_STATES_EVEN[avastha_segment]
    return state

def calculate_uchcha_bala(planet, degree):
    """Calculate Uchcha Bala based on distance from exaltation point."""
    exalt_deg = EXALTATION_POINTS.get(planet)
    if exalt_deg is None:
        return 0.0
        
    diff = abs(degree - exalt_deg) % 360
    if diff > 180:
        diff = 360 - diff
        
    # Uchcha Bala is maximum at exact exaltation (60) and decreases linearly
    # to 0 at debilitation point (180° away)
    uchcha_bala = 60 * (1 - diff/180)
    return round(max(0, min(60, uchcha_bala)), 2)

def calculate_cheshta_bala(planet, speed, degree, sun_degree):
    """Calculate Cheshta Bala based on planetary motion and position, per Vedic norms."""
    MAX_CHESTA = 60.0
    STATIONARY_THRESHOLDS = {
        "बु": 0.15,  # Mercury
        "शु": 0.25,  # Venus
        "मं": 0.08,  # Mars
        "गु": 0.04,  # Jupiter
        "श": 0.02   # Saturn
    }

    if degree is None or sun_degree is None:
        print(f"Warning: Missing degree data for {planet}, returning 0.0")
        return 0.0

    diff_sun = min((degree - sun_degree) % 360, (sun_degree - degree) % 360)
    cheshta_bala = 0.0

    if planet == "सु":
        cheshta_bala = 0.0
    elif planet == "चं":
        cheshta_bala = MAX_CHESTA * (1 - abs(diff_sun - 90) / 90)
    elif planet in ["रा", "के"]:
        cheshta_bala = 30.0  # BPHS assigns moderate Cheshta Bala for nodes
    else:
        is_retrograde = speed < 0 if speed is not None else False
        is_stationary = speed is not None and abs(speed) < STATIONARY_THRESHOLDS.get(planet, 0.1)
        if is_stationary:
            cheshta_bala = MAX_CHESTA
        elif is_retrograde:
            cheshta_bala = MAX_CHESTA * (0.8 + 0.2 * (diff_sun / 180))
        elif planet in ["बु", "शु"]:
            max_elongation = 46 if planet == "बु" else 48
            elongation_factor = min(diff_sun, max_elongation) / max_elongation
            cheshta_bala = MAX_CHESTA * elongation_factor
        else:
            cheshta_bala = MAX_CHESTA * 0.75 * (diff_sun / 180)

    return round(max(0, min(MAX_CHESTA, cheshta_bala)), 2)

def calculate_dig_bala(planet, house, positions=None):
    """Calculate Dig Bala based on house position, per Vedic norms."""
    MAX_DIG_BALA = 60.0
    DIG_BALA_HOUSE = {
        "सु": 10,  # Sun: 10th house
        "चं": 4,   # Moon: 4th house
        "मं": 10,  # Mars: 10th house
        "बु": 1,   # Mercury: 1st house
        "गु": 1,   # Jupiter: 1st house (corrected from 9th)
        "शु": 4,   # Venus: 4th house
        "श": 7     # Saturn: 7th house
    }

    if not isinstance(house, int) or house < 1 or house > 12:
        print(f"Warning: Invalid house {house} for {planet}, returning 0.0")
        return 0.0

    # Handle Rahu/Ketu
    if planet in ["रा", "के"]:
        if positions:  # Optional: Use sign lord’s Dig Bala
            degree = positions.get(planet, 0)
            sign = get_sign(degree)
            lord = get_sign_lord(sign) if sign else None
            if lord in DIG_BALA_HOUSE:
                return calculate_dig_bala(lord, house, positions) * 0.5
        return 0.0  # Standard: No Dig Bala for Rahu/Ketu

    ideal_house = DIG_BALA_HOUSE.get(planet)
    if ideal_house is None:
        print(f"Warning: No ideal house for {planet}, returning 0.0")
        return 0.0

    # Calculate house distance (shortest path)
    diff_houses = min(abs(house - ideal_house), 12 - abs(house - ideal_house))

    # Non-linear decay: Cosine-based for smoother drop-off
    import math
    dig_bala = MAX_DIG_BALA * (math.cos(math.pi * diff_houses / 6) + 1) / 2
    # Examples: 60 at diff=0, ~45 at ±1, ~15 at ±3, 0 at ±6

    dig_bala = round(max(0, min(MAX_DIG_BALA, dig_bala)), 2)
    return dig_bala

def calculate_kala_bala(planet, is_day_chart, degree, sun_degree, jd):
    """Calculate Kala Bala with all components, per Vedic norms."""
    MAX_KALA = 60.0
    if planet in ["रा", "के"]:
        return 0.0
    if degree is None or sun_degree is None or jd is None:
        print(f"Warning: Missing data for {planet}, returning 0.0")
        return 0.0

    natonnata_bala = 60.0 if (is_day_chart and planet in DAY_PLANETS) or (not is_day_chart and planet in NIGHT_PLANETS) or planet == "बु" else 0.0
    diff_sun = min((degree - sun_degree) % 360, (sun_degree - degree) % 360)
    paksha_bala = (diff_sun / 180) * 60
    if planet == "चं":
        paksha_bala = min(paksha_bala * 2, 120) / 2
    elif planet in BENEFICS:
        paksha_bala *= 1.2
    elif planet in MALEFICS:
        paksha_bala *= 0.8

    day_fraction = jd % 1
    tribhaga_bala = 0.0
    if is_day_chart:
        if 0 <= day_fraction < 1/3 and planet == "बु":
            tribhaga_bala = 60.0
        elif 1/3 <= day_fraction < 2/3 and planet == "सु":
            tribhaga_bala = 60.0
        elif 2/3 <= day_fraction < 1 and planet == "गु":
            tribhaga_bala = 60.0
    else:
        if 0 <= day_fraction < 1/3 and planet == "चं":
            tribhaga_bala = 60.0
        elif 1/3 <= day_fraction < 2/3 and planet == "शु":
            tribhaga_bala = 60.0
        elif 2/3 <= day_fraction < 1 and planet == "श":
            tribhaga_bala = 60.0
    if planet == "मं" and 0.45 <= day_fraction <= 0.55:
        tribhaga_bala = 60.0

    # Varsha-Masa-Dina-Hora Bala (simplified)
    varsha_bala = 15.0 if planet == "गु" else 0.0  # Jupiter rules year
    masa_bala = 30.0 if planet == "चं" else 0.0   # Moon rules month
    dina_bala = 45.0 if planet == "सु" else 0.0   # Sun rules day
    hora_planets = ["सु", "चं", "मं", "बु", "गु", "शु", "श"]
    hora_index = int((jd % 1) * 24) % 7
    hora_bala = 60.0 if planet == hora_planets[hora_index] else 0.0

    # Yuddha Bala (placeholder, needs planet positions check)
    yuddha_bala = 0.0  # Implement if planets are within 1°

    ayan_bala = 30.0 if (planet in BENEFICS and (jd % 365.25) < 182.625) else 15.0
    kala_bala = (0.3 * natonnata_bala + 0.2 * paksha_bala + 0.15 * tribhaga_bala +
                 0.1 * varsha_bala + 0.1 * masa_bala + 0.1 * dina_bala + 0.05 * hora_bala + 0.05 * ayan_bala)
    return round(max(0, min(MAX_KALA, kala_bala)), 2)

def calculate_avastha_bala(planet, degree, moon_degree):
    """Calculate Avastha Bala with Baladi, Jagradadi, and Deeptaadi, per Vedic norms."""
    if degree is None or moon_degree is None:
        return 0.0

    # Baladi Avastha
    position_in_sign = degree % 30
    segment = min(int(position_in_sign / 6), 4)
    baladi_multiplier = AVASTHA_MULTIPLIERS["Baladi"][segment]

    # Jagradadi Avastha
    moon_dist = min((degree - moon_degree) % 360, (moon_degree - degree) % 360)
    jagradadi_multiplier = (
        1.5 if moon_dist <= 60 else
        1.0 if moon_dist <= 120 else
        0.75
    )

    # Deeptaadi Avastha (simplified)
    sign = get_sign(degree)
    dignity = "Neutral"  # Placeholder; use divisional_dignities if available
    deeptaadi_multiplier = {
        "Exalted": 2.0, "Moolatrikona": 1.5, "Own Sign": 1.3, "Friendly": 1.2,
        "Neutral": 1.0, "Enemy": 0.8, "Debilitated": 0.5, "Combust": 0.3
    }.get(dignity, 1.0)

    avastha_bala = (baladi_multiplier + jagradadi_multiplier + deeptaadi_multiplier) / 3 * 60
    return round(max(0, min(60, avastha_bala)), 2)

def calculate_drik_bala(planet, degree, positions):
    """Calculate Drik Bala based on aspects, per Vedic norms."""
    if degree is None or not positions:
        return 0.0
    score = 0
    planet_deg = degree % 360
    pos_norm = {p: d % 360 for p, d in positions.items() if d is not None}

    for other, deg in pos_norm.items():
        if other == planet or other == "Asc":
            continue
        diff = min((planet_deg - deg) % 360, (deg - planet_deg) % 360)
        aspects = ASPECTS.get(other, [])
        for aspect_num in aspects:
            aspect_angle = aspect_num * 30
            if abs(diff - aspect_angle) <= 3:  # Tight orb
                score += 15 if other in BENEFICS else -10 if other in MALEFICS else 0

    asc_deg = pos_norm.get("Asc", 0)
    moon_deg = pos_norm.get("चं", 0)
    if min((planet_deg - asc_deg) % 360, (asc_deg - planet_deg) % 360) <= 5:
        score += 20
    if min((planet_deg - moon_deg) % 360, (moon_deg - planet_deg) % 360) <= 5:
        score += 15

    drik_bala = max(-60, min(60, score))
    return round(drik_bala, 2)

def calculate_saptavargaja_bala(planet, divisional_dignities):
    """Calculate Saptavargaja Bala for seven Vargas, per Vedic norms."""
    VARGAS = ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]
    WEIGHTS = {
        "Exalted": 45, "Moolatrikona": 30, "Own Sign": 30, "Friendly": 22.5,
        "Neutral": 15, "Enemy": 7.5, "Debilitated": 3.75
    }

    dignities = divisional_dignities.get(planet, {})
    total_points = 0
    count = 0
    for varga in VARGAS:
        dignity = dignities.get(varga, "Neutral")
        total_points += WEIGHTS.get(dignity, 15)
        count += 1
    if count == 0:
        return 0.0
    saptavargaja_bala = (total_points / count) * (60 / 45)  # Normalize to 0–60
    return round(max(0, min(60, saptavargaja_bala)), 2)

def calculate_ishta_kashta(shadbala, state_multiplier, primary_state, sign_dignity, planet, positions, planet_speeds):
    """
    Calculate Ishta and Kashta Phala based on Vedic astrology norms.
    
    Args:
        shadbala: Total Shadbala score in virupas (for reference, not primary input)
        state_multiplier: Combined multiplier from planetary state
        primary_state: Primary state of planet ("Exalted", "Debilitated", "Combust", etc.)
        sign_dignity: Sign-based dignity ("Own", "Friendly", etc.)
        planet: Planet code (सु, चं, etc.)
        positions: Dictionary of planet positions (degrees)
        planet_speeds: Dictionary of planet speeds (positive or negative for retrograde)
    
    Returns:
        tuple: (ishta_phala, kashta_phala) both in virupas (0-60)
    """
    MAX_PHALA = 60.0
    BENEFICS = ["चं", "बु", "गु", "शु"]
    MALEFICS = ["सु", "मं", "श", "रा", "के"]

    # Calculate Ocha Bala (positional strength) and Cheshta Bala (motional strength)
    ocha_bala = calculate_uchcha_bala(planet, positions.get(planet, 0))  # Placeholder function
    cheshta_bala = calculate_cheshta_bala(planet, planet_speeds.get(planet, 0), 
                                         positions.get(planet, 0), positions.get("सु", 0))

    # Base Ishta Phala: Product of Ocha and Cheshta Bala, normalized to 0-100
    base_ishta = (ocha_bala * cheshta_bala) / 100.0  # Adjust scaling based on typical values

    # Dignity and state multipliers
    dignity_multipliers = {
        "Moolatrikona": 1.4, "Own Sign": 1.3, "Vargottama": 1.35, "Friendly": 1.1,
        "Neutral": 0.95, "Enemy": 0.8, "Debilitated": 0.5
    }
    state_multipliers = {
        "Exalted": 1.5, "Moolatrikona": 1.4, "Own": 1.3, "Friend": 1.1,
        "Neutral": 1.0, "Enemy": 0.8, "Debilitated": 0.4, "Combust": 0.3
    }

    dignity_factor = dignity_multipliers.get(sign_dignity, 1.0)
    state_factor = state_multipliers.get(primary_state, 1.0)
    # Adjust for planet nature
    nature_factor = 1.25 if planet in BENEFICS else 0.85 if planet in MALEFICS else 1.0
    # Combustion check (within 6 degrees of Sun, graduated penalty)
    sun_deg = positions.get("सु", 0)
    planet_deg = positions.get(planet, 0)
    degree_diff = min((planet_deg - sun_deg) % 360, (sun_deg - planet_deg) % 360)
    combustion_factor = 1.0
    if degree_diff < 6 and planet not in ["सु", "रा", "के"]:
        combustion_factor = 0.3 if degree_diff < 3 else 0.6  # Stronger penalty closer to Sun

    # Retrograde bonus (except for Sun and Moon)
    retrograde_factor = 1.5 if planet_speeds.get(planet, 0) < 0 and planet not in ["सु", "चं"] else 1.0

    # Special cases
    if planet == "गु" and sign_dignity == "Exalted":  # Jupiter in Cancer
        base_ishta *= 1.1
    elif planet == "श" and sign_dignity == "Exalted":  # Saturn in Libra
        base_ishta *= 1.2
    elif planet == "चं" and sign_dignity == "Exalted":  # Moon in Taurus
        base_ishta *= 1.15
    elif planet == "बु" and primary_state == "Combust":  # Mercury less affected by combustion
        combustion_factor = max(combustion_factor, 0.7)

    # Calculate Ishta Phala
    ishta_phala = base_ishta * dignity_factor * state_factor * nature_factor * combustion_factor * retrograde_factor
    ishta_phala = min(max(ishta_phala, 0), MAX_PHALA)

    # Calculate Kashta Phala
    kashta_phala = MAX_PHALA - ishta_phala

    # Placeholder for malefic aspects (implement if aspect data is available)
    malefic_aspect_factor = 1.0  # Increase kashta_phala if planet is aspected by malefics
    kashta_phala *= malefic_aspect_factor
    kashta_phala = min(max(kashta_phala, 0), MAX_PHALA)

    # Ensure sum is 60
    total = ishta_phala + kashta_phala
    if total != MAX_PHALA:
        adjustment = MAX_PHALA - total
        ishta_phala += adjustment / 2
        kashta_phala += adjustment / 2

    return round(ishta_phala, 2), round(kashta_phala, 2)

def calculate_sthanabala(planet, degree, divisional_dignities, positions):
    if degree is None or not isinstance(degree, (int, float)) or not 0 <= degree < 360:
        raise ValueError(f"Invalid degree {degree} for {planet}")
    if not positions or not isinstance(positions, dict) or "Asc" not in positions:
        raise ValueError(f"Invalid positions data for {planet}: {positions}")
    # Rest unchanged

    # Uchcha Bala
    uchcha = calculate_uchcha_bala(planet, degree) or 0.0

    # Saptavargaja Bala
    div_dignities = divisional_dignities.get(planet, {}) if divisional_dignities else {}
    saptavargaja = calculate_saptavargaja_bala(planet, div_dignities) or 0.0
    if planet in ["रा", "के"]:
        sign = get_sign(degree)
        lord = get_sign_lord(sign) if sign else None
        if lord and divisional_dignities.get(lord):
            saptavargaja = calculate_saptavargaja_bala(lord, divisional_dignities.get(lord, {})) * 0.5
        else:
            saptavargaja = 15.0

    # Oja-Yugma Bala
    oja_yugma = 0.0
    sign = get_sign(degree)
    if sign:
        is_even_sign = sign in ["Taurus", "Cancer", "Virgo", "Scorpio", "Capricorn", "Pisces"]
        if (planet in ["चं", "शु"] and is_even_sign) or (planet in ["सु", "मं", "बु", "गु", "श"] and not is_even_sign):
            oja_yugma = 15.0

    # Dig Bala
    asc_deg = positions.get("Asc", 0)
    house = get_house_number(degree, asc_deg)
    dig = calculate_dig_bala(planet, house, positions) or 0.0

    # Kendra/Trikona Bala
    if house in [1, 4, 7, 10]:
        kendradi = 60.0  # Kendra
    elif house in [5, 9]:
        kendradi = 45.0  # Trikona
    elif house in [2, 8, 11]:
        kendradi = 30.0  # Panapara
    else:
        kendradi = 15.0  # Apoklima

    # Sum components
    sthana_bala = uchcha + saptavargaja + oja_yugma + dig + kendradi
    return round(max(0, sthana_bala), 2)
def get_sign(degree):
    """Convert degree (0-360) to zodiac sign name."""
    if degree is None or not isinstance(degree, (int, float)) or not 0 <= degree < 360:
        print(f"Warning: Invalid degree {degree}, returning None")
        return None
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[int(degree // 30) % 12]

def get_sign_lord(sign):
    """Return the ruling planet of a zodiac sign (Devanagari code)."""
    if not sign or not isinstance(sign, str):
        print(f"Warning: Invalid sign {sign}, returning None")
        return None
    sign_lords = {
        "aries": "मं", "taurus": "शु", "gemini": "बु", "cancer": "चं", "leo": "सु",
        "virgo": "बु", "libra": "शु", "scorpio": "मं", "sagittarius": "गु",
        "capricorn": "श", "aquarius": "श", "pisces": "गु"
    }
    return sign_lords.get(sign.lower())
def identify_karakas(positions, include_nodes=True, include_eighth_karaka=True, debug=False):
    """
    Jagannatha Hora–style Chara Karakas:
      - Uses full zodiac degrees (0–360°)
      - Includes Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn + Rahu (if include_nodes)
      - Never includes Ketu
      - Sorts descending, then remaps indices:
           0 → Dara, 1 → Amatya, 2 → Atma, 3 → Putra,
           4 → Gnati, 5 → Matri, 6 → Bhratri, 7 → Pitri
    """
    # 1) Build list of planets to use
    base = ["सु","चं","मं","बु","गु","शु","श"]
    if include_nodes:
        base.append("रा")

    # 2) Filter & validate degrees
    degs = {p: d for p, d in positions.items() if p in base and
            isinstance(d, (int,float)) and 0 <= d < 360}

    # 3) Sort descending by degree
    sorted_planets = [p for p,_ in sorted(degs.items(), key=lambda x: x[1], reverse=True)]


    # 4) Remap sorted indices → Karaka names
    idx_to_karaka = {
        0: "दारकारक",
        1: "अमात्यकारक",
        2: "आत्माकारक",
        3: "पुत्रकारक",
        4: "ज्ञातिकारक",
        5: "मातृकारक",
        6: "भ्रात्रीकारक",
        7: "पितृकारक"
    }

    karakas = {}
    for idx, planet in enumerate(sorted_planets):
        if idx in idx_to_karaka and (include_eighth_karaka or idx < 7):
            karakas[idx_to_karaka[idx]] = planet


    return karakas


def get_karaka_info(positions, include_nodes=True, include_eighth_karaka=False, debug=False):
    """
    Get detailed karaka information including degrees, signs, and positions.
    Returns a list of dictionaries with karaka → planet mapping and position.
    """
    karakas = identify_karakas(positions, include_nodes=True, include_eighth_karaka=True)
    if not karakas:
        return []

    karaka_info = []
    for karaka_name, planet in karakas.items():
        degree = positions.get(planet, 0)
        sign_index = int(degree / 30) % 12
        sign_name = RASI_SIGNS[sign_index]
        
        karaka_info.append({
            "Karaka": karaka_name,
            "Planet": planet,
            "PlanetName": planet_map_en_to_dev.get(planet, planet),
            "Degree": round(degree, 2),
            "Sign": sign_name,
            "SignIndex": sign_index,
            "Position": f"{sign_name} ({degree % 30:.2f}°)"
        })

    return karaka_info
def calculate_ashtakavarga(positions):
    """ 
    Generate sample Ashtakavarga data (replace with your actual calculations)
    Returns: Dictionary with BAV/SAV data for each planet
    """
    # Sample data - replace with your actual BAV/SAV calculations
    return {
        "Asc": [4,3,5,2,6,4,3,5,4,3,5,2],
        "Sun": [5,2,4,3,5,3,4,2,5,3,4,2],
        "Moon": [4,3,6,2,5,4,3,6,4,3,5,2],
        "Mars": [3,4,5,2,4,3,5,2,4,3,5,2],
        "Mercury": [5,3,4,2,5,3,4,2,5,3,4,2],
        "Jupiter": [6,2,3,4,5,2,3,4,5,2,3,4],
        "Venus": [4,3,5,2,4,3,5,2,4,3,5,2],
        "Saturn": [3,5,2,4,3,5,2,4,3,5,2,4],
        "Total": [28,24,30,22,32,26,25,29,27,23,31,21]
    }
def draw_ashtakavarga_chart(canvas, av_data, title, cell_size=15):
    canvas.delete("all")
    canvas.update()
    width = max(canvas.winfo_width(), 160)
    height = max(canvas.winfo_height(), 160)

    # Layout constants
    title_height = 12   # Height reserved for title above chart
    pad = 10            # Padding inside chart box
    chart_top = title_height + pad
    chart_bottom = height - pad
    chart_left = pad
    chart_right = width - pad
    cx = width // 2
    cy = (chart_top + chart_bottom) // 2

    # Draw title OUTSIDE chart area
    canvas.create_text(cx, 4, text=title, font=("Arial", 9, "bold"), anchor="n")

    # Chart structure
    canvas.create_rectangle(chart_left, chart_top, chart_right, chart_bottom, outline="black", width=1)

    # Midpoints of edges
    top = (cx, chart_top)
    bottom = (cx, chart_bottom)
    left = (chart_left, cy)
    right = (chart_right, cy)

    # Diamond + diagonals
    canvas.create_line(*top, *left, fill="black", width=1)
    canvas.create_line(*left, *bottom, fill="black", width=1)
    canvas.create_line(*bottom, *right, fill="black", width=1)
    canvas.create_line(*right, *top, fill="black", width=1)
    canvas.create_line(chart_left, chart_top, chart_right, chart_bottom, fill="black", width=1)
    canvas.create_line(chart_right, chart_top, chart_left, chart_bottom, fill="black", width=1)

    # House positions
    offset_diag_x = 26
    offset_diag_y = 8
    offset_card_x = 28
    offset_card_y = 20

    house_positions = [
        (cx, chart_top + offset_card_y),                          # 1
        (cx - offset_diag_x, chart_top + offset_diag_y),         # 2
        (chart_left + offset_diag_y, cy - offset_diag_x),        # 3
        (chart_left + offset_card_x, cy),                        # 4
        (chart_left + offset_diag_y, cy + offset_diag_x),        # 5
        (cx - offset_diag_x, chart_bottom - offset_diag_y),      # 6
        (cx, chart_bottom - offset_card_y),                      # 7
        (cx + offset_diag_x, chart_bottom - offset_diag_y),      # 8
        (chart_right - offset_diag_y, cy + offset_diag_x),       # 9
        (chart_right - offset_card_x, cy),                       # 10
        (chart_right - offset_diag_y, cy - offset_diag_x),       # 11
        (cx + offset_diag_x, chart_top + offset_diag_y),         # 12
    ]

    horizontal_indices = [1, 5, 7, 11]

    for i, (x, y) in enumerate(house_positions):
        value = av_data[i] if i < len(av_data) else "-"
        label = str(value)
        canvas.create_text(x, y, text=label,
                           font=("Mangal", 7),
                           fill="black",
                           anchor="center",
                           justify="center")
def is_daytime(sun_long, asc_long, chart_type="North"):
    """Determine if chart is daytime based on Sun's house."""
    if sun_long is None or asc_long is None:
        print("Warning: Missing Sun or Ascendant longitude, defaulting to daytime")
        return True
    sun_house = get_house_number(sun_long, asc_long)
    is_day = 1 <= sun_house <= 6
    return is_day
def calculate_strengths(jd, positions, planet_speeds, divisional_dignities, phala_weights, include_nodes=False):
    """Calculate Shadbala and related strengths for planets, including planet status and combined state."""
    if not positions or not isinstance(positions, dict):
        raise ValueError("Positions must be a non-empty dictionary")
    
    base_planets = ["सु", "चं", "मं", "बु", "गु", "शु", "श"]
    planets = base_planets + ["रा", "के"] if include_nodes else base_planets
    asc_deg = positions.get("Asc", 0)
    sun_deg = positions.get("सु", 0)
    moon_deg = positions.get("चं", 0)
    is_day = is_daytime(sun_deg, asc_deg)

    table1_data = []
    bala_breakdown = {
        "Sthana": {}, "Cheshta": {}, "Dig": {}, "Kala": {}, "Avastha": {}, "Drik": {}
    }

    for planet in planets:
        if planet not in positions:
            print(f"Warning: Skipping planet {planet} due to missing position data")
            continue
        degree = positions[planet]
        speed = planet_speeds.get(planet, 0)
        planet_div_dignities = divisional_dignities.get(planet, {})

        try:
            # Calculate components using revised functions
            sthanabala = calculate_sthanabala(planet, degree, {planet: planet_div_dignities}, positions)
            cheshtabala = calculate_cheshta_bala(planet, speed, degree, sun_deg)
            digbala = calculate_dig_bala(planet, get_house_number(degree, asc_deg), positions)
            kalabala = calculate_kala_bala(planet, is_day, degree, sun_deg, jd)
            avasthabala = calculate_avastha_bala(planet, degree, moon_deg)
            drikbala = calculate_drik_bala(planet, degree, positions)
            planet_status = calculate_planet_status(planet, degree)
            primary_state, sign_dignity, state_multiplier, combined_state = get_planet_state(
                planet, degree, positions, planet_div_dignities
            )

            # Total Shadbala
            shadbala = sthanabala + cheshtabala + digbala + kalabala + avasthabala + drikbala
            ishta, kashta = calculate_ishta_kashta(
                shadbala, state_multiplier, primary_state, sign_dignity, planet, positions, planet_speeds
            )
            final_score_percent = (shadbala / 360) * 100

            # Store in breakdown
            bala_breakdown["Sthana"][planet] = sthanabala
            bala_breakdown["Cheshta"][planet] = cheshtabala
            bala_breakdown["Dig"][planet] = digbala
            bala_breakdown["Kala"][planet] = kalabala
            bala_breakdown["Avastha"][planet] = avasthabala
            bala_breakdown["Drik"][planet] = drikbala

            # Append to table
            table1_data.append([
                planet,
                "",  # Rank placeholder
                f"{shadbala:.2f}",
                f"{final_score_percent:.2f}%",
                f"{ishta:.1f}",
                f"{kashta:.1f}",
                planet_status,
                combined_state
            ])
        except Exception as e:
            print(f"Error calculating strengths for planet {planet}: {str(e)}")
            continue

    # Sort by final score and assign ranks
    table1_data.sort(key=lambda x: float(x[3].replace('%', '')), reverse=True)
    for i, row in enumerate(table1_data):
        row[1] = str(i + 1)

    return table1_data, bala_breakdown