from strength import calculate_strengths, get_house_number, get_planet_state, MALEFICS, EXALTATION_POINTS, BENEFICS, ASPECTS
import swisseph as swe
import traceback
from yogadef import YOGA_DEFINITIONS
# --- Helper Functions ---
def normalize_positions(positions):
    """Normalize all degrees in positions to 0-360."""
    return {p: deg % 360 if deg is not None else 0 for p, deg in positions.items()}

def get_exaltation_point(planet):
    return EXALTATION_POINTS.get(planet, None)

def check_conjunction(planet1, planet2, positions, orb=8):
    if planet1 not in positions or planet2 not in positions:
        return False
    diff = abs(positions[planet1] - positions[planet2]) % 360
    return min(diff, 360 - diff) <= orb

def count_planets_in_house(house, house_positions):
    if not 1 <= house <= 12:
        house = (house - 1) % 12 + 1
    return sum(1 for p, h in house_positions.items() if h == house)

def check_aspect(planet1, target, positions, orb=5):
    if planet1 not in positions:
        return False
    planet1_deg = positions[planet1]
    aspect_distances = ASPECTS.get(planet1, [])
    if not aspect_distances:
        return False

    if isinstance(target, str):
        if target not in positions:
            return False
        target_deg = positions[target]
        for distance in aspect_distances:
            aspect_deg = (planet1_deg + (distance - 1) * 30) % 360
            diff = abs(target_deg - aspect_deg)
            if min(diff, 360 - diff) <= orb:
                return True
    elif isinstance(target, int):
        if not 1 <= target <= 12:
            return False
        house_start_deg = (target - 1) * 30
        house_end_deg = target * 30
        for distance in aspect_distances:
            aspect_deg = (planet1_deg + (distance - 1) * 30) % 360
            if target == 12:
                if aspect_deg >= house_start_deg or aspect_deg < house_end_deg % 360:
                    return True
            else:
                if house_start_deg <= aspect_deg < house_end_deg:
                    return True
    return False

def count_unique_occupied_houses(house_positions, exclude_planets=None):
    exclude_planets = exclude_planets or []
    return len(set(h for p, h in house_positions.items() if p not in exclude_planets))

def check_adjacent_houses(house_positions, count):
    """Check if planets occupy 'count' consecutive houses."""
    houses = sorted(set(house_positions.values()))
    if not houses:
        return False
    for i in range(len(houses)):
        consecutive = [houses[i]]
        for j in range(1, count):
            next_house = (houses[i] + j - 1) % 12 + 1
            if next_house in houses:
                consecutive.append(next_house)
        if len(consecutive) >= count:
            return True
    return False

def get_sign(degree):
    return int(degree / 30) + 1 if degree is not None else 1

def get_sign_owner(planet, positions, house_lords):
    sign = get_sign(positions.get(planet, 0))
    return house_lords.get(sign)
def is_planet_in_own_sign(planet, positions, house_lords):
    sign = get_sign(positions.get(planet, 0))
    return house_lords.get(sign) == planet

def is_planet_exalted(planet, positions):
    exalt_point = get_exaltation_point(planet)
    if exalt_point is None:
        return False
    planet_deg = positions.get(planet, 0)
    return abs(planet_deg - exalt_point) <= 5  # 5 degree orb

def is_planet_in_kendra(planet, house_positions):
    return house_positions.get(planet, 0) in [1,4,7,10]

def is_planet_in_trikona(planet, house_positions):
    return house_positions.get(planet, 0) in [1,5,9]
def is_planet_strong(planet, positions, house_positions, divisional_dignities):
    """Check if a planet is strong based on state or house position."""
    if planet not in positions:
        return False
    # Capture all 4 return values from the new get_planet_state
    state, sign_dignity, is_vargottama, is_combust = get_planet_state(
        planet, positions[planet], positions, divisional_dignities
    )
    # A planet is strong if it's Exalted, in Own Sign, or in Kendra (1,4,7,10) and NOT combust
    return (sign_dignity in ["Exaltation", "Own Sign"] or 
            house_positions.get(planet, 0) in [1, 4, 7, 10]) and not is_combust

def is_aspected_by_benefic(target, positions, house_positions=None, orb=5):
    for benefic in BENEFICS:
        if benefic in positions and check_aspect(benefic, target, positions, orb):
            return True
    return False

# Yoga Detection Functions
def detect_yogas(positions, house_lords, asc_degree, d9_positions, d9_asc_degree, jd, divisional_dignities, is_day_birth=True):
    """Detect yogas based on planetary positions and house lordships."""
    if not positions or not isinstance(positions, dict) or "Asc" not in positions:
        return {}
    
    # Normalize positions for calculation
    positions = normalize_positions(positions)
    d9_positions = normalize_positions(d9_positions) if d9_positions else {}
    
    # Calculate house numbers for D1 and D9
    house_positions = {p: get_house_number(deg, asc_degree) for p, deg in positions.items() if p != "Asc"}
    d9_house_positions = {p: get_house_number(deg, d9_asc_degree) for p, deg in d9_positions.items() if p != "Asc"} if d9_positions else {}

    detected_yogas = {}
    for yoga_name, yoga_def in YOGA_DEFINITIONS.items():
        conditions_met_count = 0
        met_conditions_list = []
        total_conditions = len(yoga_def.get("conditions", []))
        
        for condition in yoga_def["conditions"]:
            try:
                # FIX: Passing jd and divisional_dignities to check_condition
                # These are needed for functions inside like get_planet_state
                if check_condition(
                    condition, 
                    positions, 
                    house_positions, 
                    house_lords, 
                    d9_positions, 
                    d9_house_positions, 
                    is_day_birth, 
                    jd, 
                    divisional_dignities
                ):
                    conditions_met_count += 1
                    met_conditions_list.append(condition)
            except Exception as e:
                print(f"Error checking condition {condition} for {yoga_name}: {e}")
                continue
        
        # Only add to results if at least one condition is met
        if conditions_met_count > 0:
            detected_yogas[yoga_name] = {
                "description": yoga_def.get("description", "N/A"),
                "conditions_met": f"{conditions_met_count}/{total_conditions}",
                "met_conditions": met_conditions_list,
                # FIX: Passing all 9 required arguments to estimate_yoga_strength
                "strength": estimate_yoga_strength(
                    yoga_name, 
                    conditions_met_count, 
                    positions, 
                    house_positions, 
                    house_lords, 
                    d9_positions, 
                    d9_house_positions, 
                    jd, 
                    divisional_dignities
                )
            }
    
    return detected_yogas

# In Yogasf.py, find the check_condition definition and update it:
# REPLACE the old definition with this:
def check_condition(condition_name, positions, house_positions, house_lords, d9_positions, d9_house_positions, is_day_birth, jd, divisional_dignities):
    # Example logic for a condition that needs dignity check
    #primary_state = "Neutral"
    if condition_name == "9th_lord_in_exaltation":
        ninth_lord = house_lords.get(9)
        if ninth_lord in positions:
            # get_planet_state now correctly receives all 4 required positional arguments
            state, sign_dignity, _, _ = get_planet_state(ninth_lord, positions[ninth_lord], positions, divisional_dignities)
            return sign_dignity == "Exaltation"
    moon_house = house_positions.get("चं", 0)
    sun_house = house_positions.get("सु", 0)
    
    sign_lords_map = {
        1: "मं", 2: "शु", 3: "बु", 4: "चं", 5: "सु", 6: "बु",
        7: "शु", 8: "मं", 9: "गु", 10: "श", 11: "श", 12: "गु"
    }

    # Raj Yoga
    if condition_name == "kendra_lord_in_trikona":
        for house in [1, 4, 7, 10]:
            lord = house_lords.get(house)
            if lord and house_positions.get(lord, 0) in [1, 5, 9]:
                return True
    elif condition_name == "trikona_lord_in_kendra":
        for house in [1, 5, 9]:
            lord = house_lords.get(house)
            if lord and house_positions.get(lord, 0) in [1, 4, 7, 10]:
                return True
    elif condition_name == "kendra_lord_aspects_trikona_lord":
        for k_house in [1, 4, 7, 10]:
            for t_house in [1, 5, 9]:
                k_lord = house_lords.get(k_house)
                t_lord = house_lords.get(t_house)
                if k_lord in positions and t_lord in positions and check_aspect(k_lord, t_lord, positions):
                    return True
    elif condition_name == "trikona_lord_aspects_kendra_lord":
        for t_house in [1, 5, 9]:
            for k_house in [1, 4, 7, 10]:
                t_lord = house_lords.get(t_house)
                k_lord = house_lords.get(k_house)
                if t_lord in positions and k_lord in positions and check_aspect(t_lord, k_lord, positions):
                    return True

    # Other Yogas
    elif condition_name == "jupiter_moon_conjunction":
        return check_conjunction("गु", "चं", positions)
    elif condition_name == "planets_in_2nd_from_moon":
        return count_planets_in_house((moon_house % 12) + 1, house_positions) > 0
    elif condition_name == "planets_in_12th_from_moon":
        return count_planets_in_house((moon_house - 2 + 12) % 12 + 1, house_positions) > 0
    elif condition_name == "planets_in_2nd_and_12th_from_moon":
        return (count_planets_in_house((moon_house % 12) + 1, house_positions) > 0 and
                count_planets_in_house((moon_house - 2 + 12) % 12 + 1, house_positions) > 0)
    elif condition_name == "malefic_lords_of_6_8_12_in_6_8_12":
        for lord in [house_lords.get(h) for h in [6, 8, 12]]:
            if lord in positions and house_positions.get(lord, 0) in [6, 8, 12]:
                return True
        return False  # ← Now outside the loop!
    elif condition_name == "debilitated_planet_in_kendra_with_strong_owner":
        for planet, degree in positions.items():
            # Step 1: Check if planet is debilitated in kendra
            primary_state, sign_dignity, multiplier, combined_state = get_planet_state(
                planet, degree, positions, divisional_dignities
            )
            if primary_state == "Debilitated" and house_positions.get(planet, 0) in [1, 4, 7, 10]:
                debilitated_sign = get_sign(degree)
                debilitated_sign_lord = sign_lords_map.get(debilitated_sign)
            
                # Step 2: Check the Strength of the Lord
                if debilitated_sign_lord in positions:
                    l_state, l_dignity, _, l_combust = get_planet_state(
                        debilitated_sign_lord, positions[debilitated_sign_lord], 
                        positions, divisional_dignities
                    )
                    lord_is_well_placed = house_positions.get(debilitated_sign_lord, 0) in [1, 4, 7, 10, 5, 9]
                    if lord_is_well_placed and not l_combust:
                        return True
        return False
    elif condition_name == "mutual_exchange_between_planets":
        planets = [p for p in positions if p not in ["रा", "के", "Asc"]]
        for i, p1 in enumerate(planets):
            for p2 in planets[i+1:]:
                p1_sign = get_sign(positions[p1])
                p2_sign = get_sign(positions[p2])
                if sign_lords_map.get(p1_sign) == p2 and sign_lords_map.get(p2_sign) == p1:
                    return True
    elif condition_name == "moon_without_planetary_support":
        planets_to_check = [p for p in house_positions if p not in ["चं", "सु", "रा", "के"]]
        return not (any(house_positions.get(p) == (moon_house % 12) + 1 for p in planets_to_check) or
                    any(house_positions.get(p) == (moon_house - 2 + 12) % 12 + 1 for p in planets_to_check))
    elif condition_name == "strong_planets_in_angular_houses":
        for planet in ["मं", "बु", "गु", "शु", "श"]:
            if planet in positions and house_positions.get(planet, 0) in [1, 4, 7, 10]:
            # UPDATED: Use primary_state
                primary_state, sign_dignity, multiplier, combined_state = get_planet_state(
                    planet, positions[planet], positions, divisional_dignities
                )
                if primary_state in ["Exalted", "Own"]:
                    return True
    elif condition_name == "moon_mars_conjunction":
        return check_conjunction("चं", "मं", positions)
    elif condition_name == "mercury_sun_conjunction":
        return check_conjunction("बु", "सु", positions)
    elif condition_name == "benefic_in_10th":
        return any(house_positions.get(b, 0) == 10 for b in BENEFICS)
    elif condition_name == "moon_in_4th_with_benefics":
        return house_positions.get("चं", 0) == 4 and is_aspected_by_benefic("चं", positions)
    elif condition_name == "planets_in_2nd_from_sun":
        return count_planets_in_house((sun_house % 12) + 1, house_positions) > 0
    elif condition_name == "planets_in_12th_from_sun":
        return count_planets_in_house((sun_house - 2 + 12) % 12 + 1, house_positions) > 0
    elif condition_name == "planets_in_2nd_and_12th_from_sun":
        return (count_planets_in_house((sun_house % 12) + 1, house_positions) > 0 and
                count_planets_in_house((sun_house - 2 + 12) % 12 + 1, house_positions) > 0)
    elif condition_name == "planets_in_seven_houses":
        return count_unique_occupied_houses(house_positions, ["रा", "के"]) == 7
    elif condition_name == "planets_in_first_four_houses":
        planets = [p for p in house_positions if p not in ["रा", "के"]]
        return planets and all(house_positions.get(p) in [1, 2, 3, 4] for p in planets)
    elif condition_name == "planets_in_three_houses":
        return count_unique_occupied_houses(house_positions, ["रा", "के"]) == 3
    elif condition_name == "planets_in_two_houses":
        return count_unique_occupied_houses(house_positions, ["रा", "के"]) == 2
    elif condition_name == "planets_in_two_adjacent_houses":
        return check_adjacent_houses({p: h for p, h in house_positions.items() if p not in ["रा", "के"]}, 2)
    elif condition_name == "planets_in_four_consecutive_houses":
        return check_adjacent_houses({p: h for p, h in house_positions.items() if p not in ["रा", "के"]}, 4)
    elif condition_name == "planets_in_three_consecutive_houses":
        return check_adjacent_houses({p: h for p, h in house_positions.items() if p not in ["रा", "के"]}, 3)
    elif condition_name == "planets_in_five_consecutive_houses":
        return check_adjacent_houses({p: h for p, h in house_positions.items() if p not in ["रा", "के"]}, 5)
    elif condition_name == "planets_in_six_houses":
        return count_unique_occupied_houses(house_positions, ["रा", "के"]) == 6
    elif condition_name == "planets_distributed_in_multiple_houses":
        return count_unique_occupied_houses(house_positions, ["रा", "के"]) >= 4  # Refined to require 4+ houses
    elif condition_name == "planets_in_single_house_except_sun_moon":
        planets = {p: h for p, h in house_positions.items() if p not in ["सु", "चं", "रा", "के"]}
        return planets and len(set(planets.values())) == 1
    elif condition_name == "planets_in_four_houses":
        return count_unique_occupied_houses(house_positions, ["रा", "के"]) == 4
    elif condition_name == "planets_in_five_houses":
        return count_unique_occupied_houses(house_positions, ["रा", "के"]) == 5
    elif condition_name == "ascendant_lord_in_own_navamsa_with_benefics":
        asc_lord = house_lords.get(1)
        if asc_lord in positions and asc_lord in d9_positions:
            planet_rules_sign = {
                "मं": [1, 8], "शु": [2, 7], "बु": [3, 6], "चं": [4],
                "सु": [5], "गु": [9, 12], "श": [10, 11]
            }
            asc_lord_d9_sign = get_sign(d9_positions.get(asc_lord, 0))
            is_asc_lord_in_own_d9_sign = asc_lord in planet_rules_sign and asc_lord_d9_sign in planet_rules_sign[asc_lord]
            is_associated_with_benefics_in_d9 = (is_aspected_by_benefic(asc_lord, d9_positions) or
                                               any(check_conjunction(asc_lord, b, d9_positions) for b in BENEFICS if b in d9_positions))
            return is_asc_lord_in_own_d9_sign and is_associated_with_benefics_in_d9
    elif condition_name == "9th_lord_with_venus_in_kendra_from_ascendant":
        ninth_lord = house_lords.get(9)
        return (ninth_lord in positions and "शु" in positions and
                check_conjunction(ninth_lord, "शु", positions) and
                house_positions.get(ninth_lord, 0) in [1, 4, 7, 10])
    elif condition_name == "strong_7th_lord_in_kendra_with_jupiter":
        seventh_lord = house_lords.get(7)
        return (seventh_lord in positions and "गु" in positions and
                is_planet_strong(seventh_lord, positions, house_positions, divisional_dignities) and
                house_positions.get(seventh_lord, 0) in [1, 4, 7, 10] and
                (house_positions.get("गु", 0) == house_positions.get(seventh_lord, 0) or check_aspect("गु", seventh_lord, positions)))
    elif condition_name == "9th_lord_in_exaltation_with_ascendant_lord":
        ninth_lord = house_lords.get(9)
        asc_lord = house_lords.get(1)
        if ninth_lord in positions and asc_lord in positions:
            # UPDATED: Changed 'state' to 'primary_state'
            primary_state, sign_dignity, multiplier, combined_state = get_planet_state(
            ninth_lord, positions[ninth_lord], positions, divisional_dignities
            )
            return primary_state == "Exalted" and check_conjunction(ninth_lord, asc_lord, positions)
    elif condition_name == "4th_lord_in_kendra_with_strong_moon":
        fourth_lord = house_lords.get(4)
        return (fourth_lord in positions and "चं" in positions and
                house_positions.get(fourth_lord, 0) in [1, 4, 7, 10] and
                is_planet_strong("चं", positions, house_positions , divisional_dignities) and
                check_conjunction(fourth_lord, "चं", positions))
    elif condition_name == "benefics_in_5th_with_9th_lord_in_kendra":
        ninth_lord = house_lords.get(9)
        return (ninth_lord in positions and
                house_positions.get(ninth_lord, 0) in [1, 4, 7, 10] and
                any(house_positions.get(b, 0) == 5 for b in BENEFICS))
    elif condition_name == "4th_lord_in_kendra_with_venus_or_jupiter":
        fourth_lord = house_lords.get(4)
        return (fourth_lord in positions and
                house_positions.get(fourth_lord, 0) in [1, 4, 7, 10] and
                (house_positions.get("शु", 0) == house_positions.get(fourth_lord, 0) or
                 house_positions.get("गु", 0) == house_positions.get(fourth_lord, 0)))
    elif condition_name == "moon_in_4th_with_venus_and_jupiter":
        return (house_positions.get("चं", 0) == 4 and
                house_positions.get("शु", 0) == 4 and
                house_positions.get("गु", 0) == 4)
    elif condition_name == "10th_lord_with_9th_lord_in_kendra":
        tenth_lord = house_lords.get(10)
        ninth_lord = house_lords.get(9)
        return (tenth_lord in positions and ninth_lord in positions and
                check_conjunction(tenth_lord, ninth_lord, positions) and
                house_positions.get(tenth_lord, 0) in [1, 4, 7, 10])
    elif condition_name == "3rd_lord_in_6th_with_benefic_aspects":
        third_lord = house_lords.get(3)
        return (third_lord in positions and
                house_positions.get(third_lord, 0) == 6 and
                is_aspected_by_benefic(third_lord, positions))
    elif condition_name == "5th_lord_in_kendra_with_jupiter_in_5th":
        fifth_lord = house_lords.get(5)
        return (fifth_lord in positions and "गु" in positions and
                house_positions.get(fifth_lord, 0) in [1, 4, 7, 10] and
                house_positions.get("गु", 0) == 5)
    elif condition_name == "8th_lord_in_kendra_with_benefic_influence":
        eighth_lord = house_lords.get(8)
        return (eighth_lord in positions and
                house_positions.get(eighth_lord, 0) in [1, 4, 7, 10] and
                (is_aspected_by_benefic(eighth_lord, positions) or
                 any(check_conjunction(eighth_lord, b, positions) for b in BENEFICS)))
    elif condition_name == "jupiter_in_9th_with_venus_in_kendra":
        return (house_positions.get("गु", 0) == 9 and
                house_positions.get("शु", 0) in [1, 4, 7, 10])
    elif condition_name == "4th_lord_with_moon_in_kendra":
        fourth_lord = house_lords.get(4)
        return (fourth_lord in positions and "चं" in positions and
                check_conjunction(fourth_lord, "चं", positions) and
                house_positions.get(fourth_lord, 0) in [1, 4, 7, 10])
    elif condition_name == "9th_lord_with_sun_in_kendra":
        ninth_lord = house_lords.get(9)
        return (ninth_lord in positions and "सु" in positions and
                check_conjunction(ninth_lord, "सु", positions) and
                house_positions.get(ninth_lord, 0) in [1, 4, 7, 10])
    elif condition_name == "3rd_lord_with_mercury_in_kendra":
        third_lord = house_lords.get(3)
        return (third_lord in positions and "बु" in positions and
                check_conjunction(third_lord, "बु", positions) and
                house_positions.get(third_lord, 0) in [1, 4, 7, 10])
    elif condition_name == "10th_lord_in_exaltation_with_6th_lord":
        tenth_lord = house_lords.get(10)
        if tenth_lord in positions:
            primary_state, sign_dignity, multiplier, combined_state = get_planet_state(
                tenth_lord, positions[tenth_lord], positions, divisional_dignities
            )
            return primary_state == "Exalted" # Use primary_state here
    elif condition_name == "ascendant_lord_in_kendra_with_jupiter_aspect":
        asc_lord = house_lords.get(1)
        return (asc_lord in positions and "गु" in positions and
                house_positions.get(asc_lord, 0) in [1, 4, 7, 10] and
                check_aspect("गु", asc_lord, positions))
    elif condition_name == "jupiter_in_5th_or_9th_with_venus_mercury":
        if "गु" in positions and "शु" in positions and "बु" in positions:
            return (house_positions.get("गु", 0) in [5, 9] and
                    check_conjunction("शु", "गु", positions) and
                    check_conjunction("बु", "गु", positions))
    elif condition_name == "venus_in_5th_with_moon_and_jupiter":
        return (house_positions.get("शु", 0) == 5 and
                check_conjunction("चं", "शु", positions) and
                check_conjunction("गु", "शु", positions))
    elif condition_name == "ascendant_lord_in_exaltation_with_9th_lord":
        asc_lord = house_lords.get(1)
        ninth_lord = house_lords.get(9)
        if asc_lord in positions and ninth_lord in positions:
            # UPDATED: Capture 4 values
            primary_state, sign_dignity, multiplier, combined_state = get_planet_state(
                asc_lord, positions[asc_lord], positions, divisional_dignities
            )
            # UPDATED: Change 'state' to 'primary_state' in the return line
            return primary_state == "Exalted" and check_conjunction(asc_lord, ninth_lord, positions)
    elif condition_name == "sun_in_10th_with_benefic_aspects":
        return house_positions.get("सु", 0) == 10 and is_aspected_by_benefic("सु", positions)
    elif condition_name == "venus_in_kendra_with_moon_in_5th_or_9th":
        return (house_positions.get("शु", 0) in [1, 4, 7, 10] and
                house_positions.get("चं", 0) in [5, 9])
    elif condition_name == "ascendant_lord_venus_jupiter_in_kendra":
        asc_lord = house_lords.get(1)
        return (asc_lord in positions and "शु" in positions and "गु" in positions and
                house_positions.get(asc_lord, 0) in [1, 4, 7, 10] and
                house_positions.get("शु", 0) in [1, 4, 7, 10] and
                house_positions.get("गु", 0) in [1, 4, 7, 10])
    elif condition_name == "7th_lord_with_venus_in_kendra":
        seventh_lord = house_lords.get(7)
        return (seventh_lord in positions and "शु" in positions and
                check_conjunction(seventh_lord, "शु", positions) and
                house_positions.get(seventh_lord, 0) in [1, 4, 7, 10])
    elif condition_name == "jupiter_in_5th_with_strong_mercury":
        return (house_positions.get("गु", 0) == 5 and
                is_planet_strong("बु", positions, house_positions, divisional_dignities))
    elif condition_name == "jupiter_venus_mercury_in_kendra_or_trikona":
        return (house_positions.get("गु", 0) in [1, 4, 7, 10, 5, 9] and
                house_positions.get("शु", 0) in [1, 4, 7, 10, 5, 9] and
                house_positions.get("बु", 0) in [1, 4, 7, 10, 5, 9])
    elif condition_name == "10th_lord_in_1st_with_jupiter":
        tenth_lord = house_lords.get(10)
        return (tenth_lord in positions and "गु" in positions and
                house_positions.get(tenth_lord, 0) == 1 and
                house_positions.get("गु", 0) == 1)
    elif condition_name == "benefics_in_kendra_no_malefics_in_trikona":
        return (any(house_positions.get(b, 0) in [1, 4, 7, 10] for b in BENEFICS) and
                not any(house_positions.get(m, 0) in [5, 9] for m in MALEFICS))
    elif condition_name == "all_kendras_occupied_by_planets":
        planets = [p for p in house_positions if p not in ["रा", "के"]]
        return all(any(house_positions.get(p) == h for p in planets) for h in [1, 4, 7, 10])
    elif condition_name == "benefics_in_6th_7th_8th_from_moon":
        houses_from_moon = [(moon_house + i - 1 + 12) % 12 + 1 for i in [6, 7, 8]]
        return all(any(house_positions.get(b, 0) == h for b in BENEFICS) for h in houses_from_moon)
    elif condition_name == "lord_of_9th_in_kendra_with_venus":
        ninth_lord = house_lords.get(9)
        return (ninth_lord in positions and "शु" in positions and
                house_positions.get(ninth_lord, 0) in [1, 4, 7, 10] and
                check_conjunction(ninth_lord, "शु", positions))
    elif condition_name == "jupiter_mars_conjunction":
        return check_conjunction("गु", "मं", positions)
    elif condition_name == "day_birth_sun_moon_ascendant_in_odd_signs":
        if is_day_birth:
            return all(get_sign(positions.get(p, 0)) % 2 == 1 for p in ["सु", "चं", "Asc"])
        return False
    elif condition_name == "benefics_flanking_ascendant":
        asc_house = 1
        return (any(house_positions.get(b, 0) == (asc_house % 12) + 1 for b in BENEFICS) and
                any(house_positions.get(b, 0) == (asc_house - 2 + 12) % 12 + 1 for b in BENEFICS))
    elif condition_name == "malefics_flanking_ascendant":
        asc_house = 1
        return (any(house_positions.get(m, 0) == (asc_house % 12) + 1 for m in MALEFICS) and
                any(house_positions.get(m, 0) == (asc_house - 2 + 12) % 12 + 1 for m in MALEFICS))
    elif condition_name == "benefics_in_6th_7th_8th_from_moon_without_malefics":
        houses_from_moon = [(moon_house + i - 1 + 12) % 12 + 1 for i in [6, 7, 8]]
        return (all(any(house_positions.get(b, 0) == h for b in BENEFICS) for h in houses_from_moon) and
                not any(house_positions.get(m, 0) in houses_from_moon for m in MALEFICS))
    elif condition_name == "jupiter_mercury_venus_in_kendra_or_2nd":
        return (house_positions.get("गु", 0) in [1, 4, 7, 10, 2] and
                house_positions.get("बु", 0) in [1, 4, 7, 10, 2] and
                house_positions.get("शु", 0) in [1, 4, 7, 10, 2])
    elif condition_name == "benefics_in_3rd_6th_10th_11th_from_moon":
        houses_from_moon = [(moon_house + i - 1 + 12) % 12 + 1 for i in [3, 6, 10, 11]]
        return all(any(house_positions.get(b, 0) == h for b in BENEFICS) for h in houses_from_moon)
    elif condition_name == "lord_of_ascendant_with_moon_in_kendra":
        asc_lord = house_lords.get(1)
        return (asc_lord in positions and "चं" in positions and
                check_conjunction(asc_lord, "चं", positions) and
                house_positions.get(asc_lord, 0) in [1, 4, 7, 10])
    elif condition_name == "lords_of_5th_6th_in_kendra_with_strong_ascendant":
        fifth_lord = house_lords.get(5)
        sixth_lord = house_lords.get(6)
        asc_lord = house_lords.get(1)
        return (fifth_lord in positions and sixth_lord in positions and asc_lord in positions and
                check_conjunction(fifth_lord, sixth_lord, positions) and
                house_positions.get(fifth_lord, 0) in [1, 4, 7, 10] and
                is_planet_strong(asc_lord, positions, house_positions, divisional_dignities))
    elif condition_name == "mercury_in_kendra_in_own_or_exalted_sign":
        if "बु" in positions and house_positions.get("बु", 0) in [1, 4, 7, 10]:
            return get_sign(positions["बु"]) in [3, 6]  # Gemini, Virgo
    elif condition_name == "venus_in_kendra_in_own_or_exalted_sign":
        if "शु" in positions and house_positions.get("शु", 0) in [1, 4, 7, 10]:
            return get_sign(positions["शु"]) in [2, 7, 12]  # Taurus, Libra, Pisces
    elif condition_name == "mars_in_kendra_in_own_or_exalted_sign":
        if "मं" in positions and house_positions.get("मं", 0) in [1, 4, 7, 10]:
            return get_sign(positions["मं"]) in [1, 8, 10]  # Aries, Scorpio, Capricorn
    elif condition_name == "jupiter_in_kendra_in_own_or_exalted_sign":
        if "गु" in positions and house_positions.get("गु", 0) in [1, 4, 7, 10]:
            return get_sign(positions["गु"]) in [9, 12, 4]  # Sagittarius, Pisces, Cancer
    elif condition_name == "saturn_in_kendra_in_own_or_exalted_sign":
        if "श" in positions and house_positions.get("श", 0) in [1, 4, 7, 10]:
            return get_sign(positions["श"]) in [10, 11, 7]  # Capricorn, Aquarius, Libra
    elif condition_name == "sun_in_2nd_from_moon_with_jupiter":
        target_house = (moon_house % 12) + 1
        return (house_positions.get("सु", 0) == target_house and
                check_conjunction("गु", "सु", positions))
    elif condition_name == "jupiter_in_trikona_with_venus_in_kendra":
        return (house_positions.get("गु", 0) in [5, 9] and
                house_positions.get("शु", 0) in [1, 4, 7, 10])
    elif condition_name == "moon_in_6th_8th_12th_from_jupiter":
        jupiter_house = house_positions.get("गु", 0)
        houses_from_jupiter = [(jupiter_house + i - 1 + 12) % 12 + 1 for i in [6, 8, 12]]
        return moon_house in houses_from_jupiter
    elif condition_name == "12th_lord_in_12th_with_benefic_aspects":
        twelfth_lord = house_lords.get(12)
        return (twelfth_lord in positions and
                house_positions.get(twelfth_lord, 0) == 12 and
                is_aspected_by_benefic(twelfth_lord, positions))
    elif condition_name == "lords_of_2_11_in_kendra_or_trikona":
        second_lord = house_lords.get(2)
        eleventh_lord = house_lords.get(11)
        return ((second_lord in positions and house_positions.get(second_lord, 0) in [1, 4, 7, 10, 5, 9]) or
                (eleventh_lord in positions and house_positions.get(eleventh_lord, 0) in [1, 4, 7, 10, 5, 9]))
    elif condition_name == "malefic_lords_of_6_8_12_in_6_8_12":
        for lord in [house_lords.get(h) for h in [6, 8, 12]]:
            if lord in positions and house_positions.get(lord, 0) in [6, 8, 12]:
                return True
            return False
    elif condition_name == "10th_lord_in_exaltation_with_benefic_in_9th":
        tenth_lord = house_lords.get(10)
        if not tenth_lord: return False

        # Calculate the state of the 10th Lord specifically
        # This ensures 'primary_state' is defined right here
        try:
            p_state, _sign, _mult, _comb = get_planet_state(
                tenth_lord, 
                positions[tenth_lord], 
                positions, 
                divisional_dignities.get(tenth_lord, {})
            )
            primary_state = p_state # Now it is associated with a value!
        except:
            primary_state = "Neutral"

        # Check conditions
        is_exalted = (primary_state == "Exalted")
        benefics = ["गु", "शु", "बु", "चं"]
        
        # Check if any benefic is in House 9
        benefic_in_9 = False
        for p, degree in positions.items():
            if p in benefics:
                if get_house_number(degree, positions['Asc']) == 9:
                    benefic_in_9 = True
                    break
        
        return is_exalted and benefic_in_9
    return False

def estimate_yoga_strength(yoga_name, conditions_met, positions, house_positions, 
                           house_lords, d9_positions, d9_house_positions, jd, 
                           divisional_dignities, debug=False):
    """
    Estimate yoga strength based on planetary Shadbala.
    """
    
    # Initialize diagnostics
    diag = {
        "yoga": yoga_name,
        "conditions_met": conditions_met,
        "planets_found": [],
        "strengths": {},
        "errors": [],
        "threshold": None
    }
    
    if conditions_met == 0:
        return "Weak" if not debug else diag
    
    # Get Shadbala - CRITICAL FIXES HERE
    try:
        # Default phala weights if not provided elsewhere
        default_phala = {
            "Exalted": 1.0, "Own Sign": 0.8, "Moolatrikona": 0.7,
            "Friendly": 0.6, "Neutral": 0.5, "Enemy": 0.3, "Debilitated": 0.2
        }
        
        # FIX 1: Pass actual jd and divisional_dignities!
        table_data, bala_breakdown = calculate_strengths(
            jd=jd,  # Was None, now actual jd
            positions=positions,
            planet_speeds={p: 0 for p in positions},
            divisional_dignities=divisional_dignities,  # Was {}, now actual!
            phala_weights=default_phala,  # Added missing parameter
            include_nodes=True
        )
        
        if not bala_breakdown:
            diag["errors"].append("Empty bala_breakdown")
            return "Weak" if not debug else diag
            
    except Exception as e:
        import traceback
        diag["errors"].append(f"calculate_strengths failed: {str(e)}")
        diag["traceback"] = traceback.format_exc()
        return "Weak" if not debug else diag

    # Identify involved planets - COMPREHENSIVE MAPPING
    planets = set()
    
    def get_lords(houses):
        return {house_lords.get(h) for h in houses if house_lords.get(h)}
    
    yoga_lower = yoga_name.lower()
    
    if "raj" in yoga_lower:
        planets = get_lords([1, 4, 7, 10, 5, 9])
    elif "gajakesari" in yoga_lower:
        planets = {"गु", "चं"}
    elif "pancha mahapurusha" in yoga_lower:
        planets = {"मं", "बु", "गु", "शु", "श"}
    elif "budha aditya" in yoga_lower:
        planets = {"बु", "सु"}
    elif "chandra mangala" in yoga_lower:
        planets = {"चं", "मं"}
    elif "lakshmi" in yoga_lower:
        planets = {"शु", "चं"}
    elif "dhana" in yoga_lower:
        planets = get_lords([2, 5, 9, 11]) | {"शु", "गु"}
    elif "viparita" in yoga_lower:
        planets = get_lords([6, 8, 12])
    elif "neech bhang" in yoga_lower:
        sign_lords = {1:"मं", 2:"शु", 3:"बु", 4:"चं", 5:"सु", 6:"बु", 
                      7:"शु", 8:"मं", 9:"गु", 10:"श", 11:"श", 12:"गु"}
        for p, deg in positions.items():
            if p in ["रा", "के", "Asc"]: continue
            try:
                _, dignity, _, _ = get_planet_state(p, deg, positions, divisional_dignities.get(p, {}))
                if dignity == "Debilitated":
                    planets.add(p)
                    sign = int(deg / 30) + 1
                    planets.add(sign_lords.get(sign))
            except: continue
    elif "parivartana" in yoga_lower:
        sign_lords = {1:"मं", 2:"शु", 3:"बु", 4:"चं", 5:"सु", 6:"बु", 
                      7:"शु", 8:"मं", 9:"गु", 10:"श", 11:"श", 12:"गु"}
        planet_list = [p for p in positions if p not in ["रा", "के", "Asc"]]
        for i, p1 in enumerate(planet_list):
            for p2 in planet_list[i+1:]:
                s1, s2 = int(positions[p1]/30)+1, int(positions[p2]/30)+1
                if sign_lords.get(s1) == p2 and sign_lords.get(s2) == p1:
                    planets.update([p1, p2])
    elif "saraswati" in yoga_lower:
        planets = {"गु", "बु", "शु"}
    elif "kalanidhi" in yoga_lower:
        planets = {"गु", "शु", house_lords.get(5)}
    elif "kalpadruma" in yoga_lower:
        planets = {house_lords.get(1), "चं"}
    elif "chamara" in yoga_lower:
        planets = get_lords([7, 9, 10])
    elif "chatra" in yoga_lower or "kuta" in yoga_lower:
        planets = get_lords([7, 9])
    elif "subha" in yoga_lower:
        planets = {"चं"} | set(BENEFICS)
    elif "asubha" in yoga_lower:
        planets = {"चं"} | set(MALEFICS)
    elif "amala" in yoga_lower or "kahala" in yoga_lower or "kemadruma" in yoga_lower:
        planets = {"चं"}
    elif "mahabhagya" in yoga_lower:
        planets = {"सु", "चं"}
    elif "ruchaka" in yoga_lower:
        planets = {"मं"}
    elif "bhadra" in yoga_lower:
        planets = {"बु"}
    elif "hamsa" in yoga_lower:
        planets = {"गु"}
    elif "malavya" in yoga_lower:
        planets = {"शु"}
    elif "shasha" in yoga_lower or "sasa" in yoga_lower:
        planets = {"श"}
    elif "vasumati" in yoga_lower:
        for p, h in house_positions.items():
            if h in [3, 6, 10, 11]:
                planets.add(p)
    elif "matsya" in yoga_lower:
        planets = get_lords([9]) | set(BENEFICS)
    elif "kurma" in yoga_lower:
        planets = get_lords([6, 7, 8]) | set(BENEFICS)
    elif "varaha" in yoga_lower:
        planets = get_lords([1, 2, 9])
    elif "yogada" in yoga_lower or "kevala" in yoga_lower:
        planets = get_lords([1, 9, 10])
    else:
        # Generic extraction from YOGA_DEFINITIONS
        try:
            conditions = YOGA_DEFINITIONS[yoga_name]["conditions"]
            for cond in conditions:
                for part in cond.split("_"):
                    if part.isdigit():
                        planets.add(house_lords.get(int(part)))
                pmap = {"jupiter":"गु", "venus":"शु", "mercury":"बु", 
                       "moon":"चं", "sun":"सु", "mars":"मं", "saturn":"श"}
                for eng, hin in pmap.items():
                    if cond.lower().startswith(eng):
                        planets.add(hin)
        except: pass

    # Clean up
    planets = {p for p in planets if p and p in positions and p not in ["रा", "के", "Asc"]}
    
    # Fallback
    if not planets:
        planets = set(positions.keys()) - {"Asc", "रा", "के"}
        diag["errors"].append("Using fallback: all planets")
    
    diag["planets_found"] = list(planets)

    # Calculate strengths from bala_breakdown
    # Structure: {"Sthana": {"सु": 165.5, ...}, "Cheshta": {...}, ...}
    planet_totals = {}
    grand_total = 0
    
    for planet in planets:
        if planet not in positions:
            continue
        total = 0
        # Sum all 6 Shadbala components
        for component in ["Sthana", "Cheshta", "Dig", "Kala", "Avastha", "Drik"]:
            if component in bala_breakdown and isinstance(bala_breakdown[component], dict):
                total += bala_breakdown[component].get(planet, 0)
        planet_totals[planet] = total
        grand_total += total
    
    diag["strengths"] = planet_totals
    diag["total"] = grand_total
    
    # Calculate average
    count = len(planet_totals)
    avg = grand_total / count if count > 0 else 0
    diag["average"] = avg
    
    # Apply calibrated thresholds (Virupas)
    if avg >= 360:  # 6+ Rupas
        result = "Very Strong"
        diag["threshold"] = ">= 360 Virupas"
    elif avg >= 300:  # 5+ Rupas
        result = "Strong"
        diag["threshold"] = ">= 300 Virupas"
    elif avg >= 240:  # 4+ Rupas
        result = "Medium"
        diag["threshold"] = ">= 240 Virupas"
    else:
        result = "Weak"
        diag["threshold"] = "< 240 Virupas"
    
    diag["result"] = result
    
    if debug:
        return diag
    return result
# GUI Functions
def get_detected_yogas_list(positions, house_lords, asc_degree, d9_positions, d9_asc_degree, jd, divisional_dignities, is_day_birth=True):
    """
    Logic-only function: Detects yogas and returns a list of dictionaries.
    Removes all Tkinter dependencies.
    """
    try:
        # 1. Call your existing detection logic
        detected_yogas = detect_yogas(
            positions, house_lords, asc_degree, 
            d9_positions, d9_asc_degree, jd, 
            divisional_dignities, is_day_birth
        )
        
        yoga_results = []
        
        # 2. Sort by strength and format data
        sorted_yogas = sorted(detected_yogas.items(), key=lambda x: x[1]["strength"], reverse=True)
        
        for yoga_name, yoga_details in sorted_yogas:
            conditions = "\n".join([f"• {cond.replace('_', ' ').title()}" for cond in yoga_details.get('met_conditions', [])])
            
            yoga_results.append({
                "name": yoga_name,
                "description": yoga_details.get('description', 'N/A'),
                "met": yoga_details.get('conditions_met', 'N/A'),
                "details": conditions,
                "strength": str(yoga_details.get('strength', 'N/A'))
            })
            
        return yoga_results

    except Exception as e:
        print(f"Error in yoga detection: {e}")
        return []