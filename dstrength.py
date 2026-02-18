import tkinter as tk
from tkinter import ttk
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import tkinter.font as tkFont # Import the font module
# --- Font Configuration ---
# In strength.py:
planet_map_en_to_dev = {
    'Su': 'सु', 'Mo': 'चं', 'Ma': 'मं',
    'Me': 'बु', 'Ju': 'गु', 'Ve': 'शु',
    'Sa': 'श', 'Ra': 'रा', 'Ke': 'के'
}
DEV_FONT_FAMILY = "Mangal"  # Primary choice
FALLBACK_FONTS = ["Noto Sans Devanagari", "Mangal", "Nirmala UI", "Arial"]  # Fallback options
DEV_FONT_SIZE = 10
devanagari_font_tuple = (DEV_FONT_FAMILY, DEV_FONT_SIZE)

EXALTATION_POINTS = {
    "सु": 10, "चं": 33, "मं": 298,
    "बु": 165, "गु": 95, "शु": 357, "श": 200, "रा":45, "के":225
}

DEBILITATION_POINTS = {
    "सु": 190, "चं": 213, "मं": 118,
    "बु": 345, "गु": 275, "शु": 177, "श": 20, "रा":225, "के":45
}

NAISARGIKA_BALA = {
    "सु": 60, "चं": 51, "मं": 45,
    "बु": 36, "गु": 30, "शु": 42,
    "श": 18, "रा": 27, "के": 27
}

DIG_BALA_HOUSE = {
    "सु": 10,  # Sun is strongest in the 10th house
    "चं": 4,   # Moon is strongest in the 4th house
    "मं": 10,  # Mars is strongest in the 10th house
    "बु": 1,   # Mercury is strongest in the 1st house
    "गु": 1,   # Jupiter is strongest in the 1st house
    "शु": 4,   # Venus is strongest in the 4th house
    "श": 7,    # Saturn is strongest in the 7th house
    "रा": 7,
    "के": 7
}

BENEFICS = {"गु", "शु", "चं"}
MALEFICS = {"सु", "मं", "श", "के", "रा"}
ASPECTS = {
    "सु": [7], "चं": [7], "मं": [4,7,8], # Check if 'मं' is the correct Devanagari character
    "बु": [7], "गु": [5,7,9], "शु": [7],
    "श": [3,7,10], "रा": [3, 7, 11], "के": [3, 7, 11]
}

AVASTHA_MULTIPLIERS = {
    "Baladi": [1.0, 0.75, 0.5, 0.33, 0.25],
    "Jagradadi": [1.5, 1.0, 0.75]
}

DAY_PLANETS = {"सु", "मं", "गु"} # Check if 'मं' is the correct Devanagari character
NIGHT_PLANETS = {"चं", "शु", "श"}
NEUTRAL_PLANETS = {"बु"}

DIGNITY_WEIGHTS = {
    "Exalted": 5,
    "Own": 4,
    "Friendly": 3,
    "Neutral": 2,
    "Enemy": 1,
    "Debilitated": 0
}

# --- Start of Calculation Functions (mostly unchanged, keeping the ones from previous response) ---

def get_house_number(planet_deg, asc_deg):
    asc_sign = int(asc_deg / 30)
    planet_sign = int(planet_deg / 30)
    house = (planet_sign - asc_sign + 12) % 12 + 1
    return house

def get_planet_state(planet, degree):
    # Ensure degree is used if planet not in dict
    exaltation = EXALTATION_POINTS.get(planet)
    debilitation = DEBILITATION_POINTS.get(planet)

    if exaltation is None or debilitation is None:
        # Handle planets not in standard exalt/debil list (like nodes if included)
         return "Normal", 1.0 # Or handle differently as per logic

    diff_exalt = abs(degree - exaltation) % 360
    diff_debil = abs(degree - debilitation) % 360

    # Normalize differences to be within 0-180 for shortest distance
    if diff_exalt > 180:
        diff_exalt = 360 - diff_exalt
    if diff_debil > 180:
        diff_debil = 360 - diff_debil

    if diff_exalt <= 5: # Within 5 degrees of exaltation point
        return "Exalted", 1.5 # Example multiplier
    elif diff_debil <= 5: # Within 5 degrees of debilitation point
        return "Debilitated", 0.5 # Example multiplier

    # Check for Mooltrikona - needs proper rashi/degree logic relative to exaltation rashi
    # This simple check (comparing to exaltation point) is not a complete Mooltrikona rule
    # A proper check would involve checking if the planet is in its Mooltrikona rashi
    # For simplicity, keeping the original logic but noting its limitation
    # if (degree - exaltation) % 360 < 180: # Original logic, simplified
    #     # This condition alone doesn't define Mooltrikona correctly
    #     pass # Need proper Rashi logic here
    # else:
    #     pass # Need proper Rashi logic here

    # Defaulting to Normal if not Exalted or Debilitated based on degree proximity
    return "Normal", 1.0 # Example multiplier

def calculate_uchcha_bala(planet, degree):
    exalt_deg = EXALTATION_POINTS.get(planet)
    debil_deg = DEBILITATION_POINTS.get(planet)
    if exalt_deg is None or debil_deg is None:
        return 0.0 # Handle planets like nodes if they don't have exalt/debil points

    diff_exalt = abs(degree - exalt_deg) % 360
    diff_debil = abs(degree - debil_deg) % 360

    # Normalize differences to be within 0-180
    if diff_exalt > 180:
        diff_exalt = 360 - diff_exalt
    if diff_debil > 180:
        diff_debil = 360 - diff_debil

    # Uchcha Bala calculation (distance from debilitation point / 3 degrees)
    # Max bala is 60 when at exaltation (180 deg from debilitation)
    # Min bala is 0 when at debilitation (0 deg from debilitation)
    # Strength = (Distance from Debilitation Point) / 3 degrees
    # Distance from Debilitation is 180 - Distance from Exaltation
    distance_from_debil_point = 180 - diff_exalt # This is simpler
    uchcha_bala = (distance_from_debil_point / 3) # 180 / 3 = 60

    return round(max(0, min(60, uchcha_bala)), 2) # Ensure score is between 0 and 60


def calculate_cheshta_bala(planet, speed):
    # Assuming speed is in degrees per day or similar relative measure
    # Need proper definition of Cheshta Bala rules based on motion states (Retrograde, Direct, etc.)
    # This is a simplified example based on positive/negative speed
    if planet in ['रा', 'के']:  # Nodes have average retrograde motion, often treated differently
         return 30.0 # Example average Cheshta Bala for nodes
    if planet in ["सु", "चं"]: # Sun and Moon don't retrograde
         return 30.0 # Example average Cheshta Bala

    # For other planets (मं, बु, गु, शु, श)
    if speed < 0: # Retrograde
        return 60.0
    elif speed == 0: # Stationary (Sambudha) - usually gives full Cheshta
        return 60.0 # Corrected: Stationary usually gets full bala
    elif 0 < speed < 0.5: # Slow direct motion (Manda)
         return 45.0 # Example value for slow motion
    elif speed >= 0.5 and speed < 1.5: # Normal direct motion (Madhya)
         return 30.0 # Example value for normal motion
    elif speed >= 1.5: # Fast direct motion (Atichara)
         return 15.0 # Example value for fast motion
    else: # Default/Catch-all
         return 0.0


def calculate_dig_bala(planet, house):
    ideal_house = DIG_BALA_HOUSE.get(planet)
    if ideal_house is None:
        return 0.0 # Handle planets like nodes if they don't have standard dig bala houses

    diff_houses = abs(house - ideal_house)
    # Find the shortest distance on the 1-12 house circle
    if diff_houses > 6:
        diff_houses = 12 - diff_houses

    # Dig Bala is max (60) at ideal house, 0 at opposite house (6 houses away)
    # Dig Bala = (6 - distance from ideal house) * 10
    dig_bala = (6 - diff_houses) * 10

    return round(max(0, min(60, dig_bala)), 2) # Ensure score is between 0 and 60


def is_daytime(sun_long, asc_long, chart_type="North"):
    # Simplified daytime check: Sun in houses 7-12 (South of horizon)
    # This assumes a standard house division (like whole sign or Sripati)
    # A more precise check requires calculating sunrise/sunset based on time and location
    # For this function's purpose (Kala Bala based on day/night chart), the ascendant/descendant axis is the horizon.
    # If Sun is above horizon (Houses 1-6 relative to Asc) - Day Chart
    # If Sun is below horizon (Houses 7-12 relative to Asc) - Night Chart

    # Check if Sun is in houses 1-6 relative to Ascendant
    sun_house = get_house_number(sun_long, asc_long)
    # print(f"Sun in House {sun_house} relative to Asc ({asc_long:.2f} deg)") # Debugging line
    return 1 <= sun_house <= 6 # True if Day Chart (Sun in Houses 1-6)

def calculate_kala_bala(planet, is_day_chart):
    # Kala Bala rules based on Day/Night chart
    # Day Chart: Sun, Mars, Jupiter Stronger (30) | Moon, Venus, Saturn Weaker (15) | Mercury (15)
    # Night Chart: Sun, Mars, Jupiter Weaker (15) | Moon, Venus, Saturn Stronger (30) | Mercury (15)

    score = 15.0 # Default score

    if is_day_chart:
        if planet in DAY_PLANETS: # Sun, Mars, Jupiter
            score = 30.0
        elif planet in NIGHT_PLANETS: # Moon, Venus, Saturn
             score = 15.0 # Explicitly set weaker score
        # Mercury is 15, Rahu/Ketu often 15 or 0 depending on system
    else: # Night Chart
        if planet in NIGHT_PLANETS: # Moon, Venus, Saturn
            score = 30.0
        elif planet in DAY_PLANETS: # Sun, Mars, Jupiter
             score = 15.0 # Explicitly set weaker score
        # Mercury is 15, Rahu/Ketu often 15 or 0

    # Rahu and Ketu are often given 15 or treated like the planet they are with, or based on weekday lord
    # For simplicity, keeping 15 for Rahu/Ketu as in original NAISARGIKA_BALA
    if planet in ["रा", "के"]:
        score = 15.0 # Or adjust based on more complex rules if needed

    return round(max(0, min(60, score * 2)), 2) # Scale score (15/30) to Bala points (30/60)

def calculate_avastha_bala(planet, degree, moon_degree):
    # Baladi Avastha (position within sign)
    position_in_sign = degree % 30
    # Avasthas are typically 0-6, 6-12, 12-18, 18-24, 24-30 degrees
    avastha_segment = int(position_in_sign / 6) # 0 to 4
    baladi_multiplier = AVASTHA_MULTIPLIERS["Baladi"][avastha_segment]

    # Jagradadi Avastha (distance from Moon)
    moon_dist = abs(degree - moon_degree) % 360
    # Normalize distance to 0-180
    if moon_dist > 180:
        moon_dist = 360 - moon_dist

    if moon_dist <= 60: # 0-60 degrees
        jagradadi_multiplier = AVASTHA_MULTIPLIERS["Jagradadi"][0] # Jagrat (Awake)
    elif moon_dist <= 120: # 60-120 degrees (Corrected range from original 180)
        jagradadi_multiplier = AVASTHA_MULTIPLIERS["Jagradadi"][1] # Swapna (Dreaming)
    else: # 120-180 degrees (Corrected range)
        jagradadi_multiplier = AVASTHA_MULTIPLIERS["Jagradadi"][2] # Sushupti (Sleeping)

    # Avastha Bala is often calculated as sum of points, not multiplier average
    # Example calculation based on multipliers * 60 (max bala)
    baladi_points = baladi_multiplier * 60
    jagradadi_points = jagradadi_multiplier * 60

    # Simplified sum or average - depends on specific system
    # Using average as in original code structure, scaled by 60
    avastha_bala = (baladi_multiplier + jagradadi_multiplier) / 2 * 60 # This looks like average multiplier * 60
    # Or perhaps sum of points? (baladi_points + jagradadi_points) / 2 ?

    # Let's stick to the original structure's intent (average multiplier * 60)
    return round(max(0, min(60, avastha_bala)), 2)


def calculate_drik_bala(planet, degree, positions):
    # Drik Bala (Aspectual Strength)
    # Score based on aspects from Benefics and Malefics
    score = 0
    # Convert all positions to 0-360 range for calculations
    planet_deg_norm = degree % 360
    pos_norm = {p: d % 360 for p, d in positions.items()}

    for other, deg in pos_norm.items():
        if other == planet: # Don't aspect self
            continue

        aspect_diff = abs(planet_deg_norm - deg) % 360
        # Normalize difference to 0-180 for shortest arc
        if aspect_diff > 180:
            aspect_diff = 360 - aspect_diff

        # Check for specific aspects from the other planet
        aspects_from_other = ASPECTS.get(other, []) # Aspects *cast by* 'other' planet
        for aspect_house_num in aspects_from_other:
             # Aspect is present if angular distance is close to aspect_house_num * 30 degrees
             aspect_angle = aspect_house_num * 30
             # Check if the angle difference is within a tolerance (e.g., 5 degrees)
             if abs(aspect_diff - aspect_angle) <= 5: # Tolerance of 5 degrees
                 if other in BENEFICS:
                     # Benefic aspect adds strength (e.g., +15)
                     score += 15
                 elif other in MALEFICS:
                     # Malefic aspect reduces strength (e.g., -10)
                     score -= 10

    # Also consider special aspects like Ascendant and Moon conjunctions
    # (Original code had this, let's keep it)
    asc_deg_norm = pos_norm.get("Asc", 0)
    moon_deg_norm = pos_norm.get("चं", 0)

    # Conjunction with Ascendant (within 5 degrees)
    if abs(planet_deg_norm - asc_deg_norm) % 360 <= 5:
        score += 20 # Example points for Asc conjunction

    # Conjunction with Moon (within 5 degrees)
    if abs(planet_deg_norm - moon_deg_norm) % 360 <= 5:
        score += 15 # Example points for Moon conjunction

    # Drik Bala is typically scaled to 60, can be positive or negative before scaling
    # Let's cap the score and then scale to 0-60 range
    # Assuming max positive score could be around 60, max negative around -60
    # Scale range -60 to +60 to 0 to 60
    scaled_score = (score + 60) / 2 # This would map -60 to 0, +60 to 60

    return round(max(0, min(60, scaled_score)), 2) # Ensure result is between 0 and 60


def calculate_saptavargaja_bala(planet, divisional_dignities):
    # Saptavargaja Bala (Divisional Strength)
    dignities = divisional_dignities.get(planet, {})
    total_weight = 0
    count = 0
    for div, dignity in dignities.items():
        # Use weights for different dignities (Exalted, Own, Friendly, etc.)
        weight = DIGNITY_WEIGHTS.get(dignity, 2) # Default to Neutral weight
        total_weight += weight
        count += 1

    # Normalize the total weight and scale to a max bala (e.g., 60)
    # Max possible weight per division is 5 (Exalted). Total max weight = count * 5
    max_possible_total_weight = count * 5

    if max_possible_total_weight == 0:
        return 0.0

    saptavargaja_bala = (total_weight / max_possible_total_weight) * 60 # Scale to 60

    return round(max(0, min(60, saptavargaja_bala)), 2) if count else 0


def calculate_ishta_kashta(phala_weight):
    # Ishta Phala and Kashta Phala
    # Phala Weight is assumed to be a score out of 100 (0-100)
    phala_weight = max(0, min(100, phala_weight)) # Ensure it's within 0-100

    # Ishta Phala = Phala Weight % of 60 (max Shadbala)
    ishta = (phala_weight / 100) * 60

    # Kashta Phala = (100 - Phala Weight) % of 60
    kashta = ((100 - phala_weight) / 100) * 60

    return round(max(0, ishta), 2), round(max(0, kashta), 2) # Ensure scores are non-negative


def calculate_sthanabala(planet, degree, divisional_dignities, positions):
    # Sthana Bala (Positional Strength) - Sum of multiple components

    # 1. Uchcha Bala (Exaltation Strength) - already calculated
    uchcha = calculate_uchcha_bala(planet, degree)

    # 2. Saptavargaja Bala (Divisional Strength) - already calculated
    saptavargaja = calculate_saptavargaja_bala(planet, divisional_dignities)

    # 3. Oochcha Sthana (Exalted or Mooltrikona in Rashi) - Binary (60 or 0)
    # This requires proper Rashi and Mooltrikona logic.
    # The previous get_planet_state was simplified. Need actual Rashi.
    # Assuming degree is longitude:
    # planet_rashi = int(degree / 30) + 1 # 1-12

    # For simplicity, using a placeholder - needs proper Rashi check
    # Oochcha sthana is 60 if in exaltation or mooltrikona rashi, 0 otherwise.
    oochcha_sthana = 0 # Placeholder - Implement proper Rashi check here

    # 4. Svasthana (Own Rashi) - Binary (60 or 0)
    # Needs proper Rashi logic.
    svasthana = 0 # Placeholder - Implement proper Rashi check here

    # 5. Dig Bala (Directional Strength) - already calculated
    house = get_house_number(degree, positions.get("Asc", 0))
    dig = calculate_dig_bala(planet, house)

    # 6. Kendradi Bala (Angular Strength) - Binary (60 or 0)
    # Strength based on house position (Kendras 1,4,7,10)
    kendradi = 60 if house in [1, 4, 7, 10] else 0 # Standard rule

    # Total Sthana Bala is the sum
    sthana_bala_total = uchcha + saptavargaja + oochcha_sthana + svasthana + dig + kendradi

    # Shadbala components are often scaled/normalized later, but Sthana Bala is typically the sum of these points.
    # Ensure it's not negative, though components should be non-negative except maybe Drik.
    return max(0, round(sthana_bala_total, 2))


def calculate_strengths(jd, positions, planet_speeds, divisional_dignities, phala_weights, include_nodes=False):
    # Conditionally define the planet list
    base_planets = ["सु", "चं", "मं", "बु", "गु", "शु", "श"]
    planets = base_planets + ["रा", "के"] if include_nodes else base_planets
    asc_deg = positions.get("Asc", 0)
    sun_deg = positions.get("सु", 0)
    moon_deg = positions.get("चं", 0)
    is_day = is_daytime(sun_deg, asc_deg) # Pass asc_deg to is_daytime

    table1_data = []
    bala_breakdown = {
        "Sthana": {}, "Cheshta": {}, "Dig": {}, "Kala": {}, "Avastha": {}, "Drik": {}
    }

    for planet in planets:
        degree = positions.get(planet, 0)
        speed = planet_speeds.get(planet, 0)
        # house = get_house_number(degree, asc_deg) # Already used in calculate_sthanabala/dig_bala

        # Need divisional dignities for Saptavargaja Bala
        planet_div_dignities = divisional_dignities.get(planet, {})

        sthanabala = calculate_sthanabala(planet, degree, {planet: planet_div_dignities}, positions) # Pass single planet's div dignities
        cheshtabala = calculate_cheshta_bala(planet, speed)
        digbala = calculate_dig_bala(planet, get_house_number(degree, asc_deg)) # Recalculate house here
        kalabala = calculate_kala_bala(planet, is_day)
        avasthabala = calculate_avastha_bala(planet, degree, moon_deg)
        drikbala = calculate_drik_bala(planet, degree, positions) # Pass all positions for aspects

        bala_breakdown["Sthana"][planet] = round(sthanabala, 2)
        bala_breakdown["Cheshta"][planet] = round(cheshtabala, 2)
        bala_breakdown["Dig"][planet] = round(digbala, 2)
        bala_breakdown["Kala"][planet] = round(kalabala, 2)
        bala_breakdown["Avastha"][planet] = round(avasthabala, 2)
        bala_breakdown["Drik"][planet] = round(drikbala, 2)

        # Total Shadbala is the sum of all 6 balas
        shadbala = sthanabala + cheshtabala + digbala + kalabala + avasthabala + drikbala

        # Ra/Ke often don't have all 6 balas calculated in standard Shadbala
        # If including nodes, decide how to handle their shadbala total
        # For simplicity, just sum the calculated balas for nodes too,
        # but be aware some systems might only calculate specific balas for them.
        if planet in ["रा", "के"]:
             # Optionally adjust shadbala calculation for nodes if needed
             pass # Currently sums whatever balas were calculated

        phala_weight = phala_weights.get(planet, 50) # Default to 50 if not provided
        ishta, kashta = calculate_ishta_kashta(phala_weight)

        # Final Score is Shadbala normalized against a benchmark (e.g., 360 or ideal minimum)
        # Normalizing against max possible (360) is common, then converted to %
        # Some systems normalize against ideal minimum required Shadbala (e.g., 360 for Sun)
        # Using 360 as the denominator for simplicity
        final_score_percent = (shadbala / 360) * 100 # Score as a percentage of max possible

        table1_data.append([
            planet,
            f"{shadbala:.2f}",
            f"{final_score_percent:.2f}%",
            f"{ishta:.1f}",
            f"{kashta:.1f}"
        ])

    table1_data.sort(key=lambda x: float(x[2].replace('%', '')), reverse=True)
    for i, row in enumerate(table1_data):
        row.insert(1, str(i + 1)) # Insert rank as the second element

    # --- Calculate Total Shadbala (Optional addition) ---
    # This calculates total % score, not total points. Maybe sum shadbala points instead?
    total_shadbala_sum_percent = sum(float(row[3].replace('%', '')) for row in table1_data if len(row) > 3) # Summing the % column
    # print(f"Total Shadbala score percentage: {total_shadbala_sum_percent:.2f}%") # Debugging line
        # New: Dictionary of final strength percentage per planet
    final_strength_percent = {
        row[0]: float(row[3].replace('%', ''))  # Use index 0 for the planet (Devanagari key) and index 3 for the percentage value
        for row in table1_data
    }

    print(f"DEBUG in strength.py: Keys of final_strength_percent before return (FIXED): {final_strength_percent.keys()}")
    print(f"DEBUG in strength.py: Contents of final_strength_percent before return (FIXED): {final_strength_percent}")

    return table1_data, bala_breakdown, final_strength_percent


# --- End of Calculation Functions ---


def show_strength_tables(parent, jd, positions, planet_speeds, divisional_dignities, phala_weights):
    """
    Displays the planetary strength tables and bar graphs.
    This function now uses the devanagari_font_tuple defined at the top.
    """
    # Call calculate_strengths without nodes for Strength button
    table1_data, bala_breakdown = calculate_strengths(jd, positions, planet_speeds, divisional_dignities, phala_weights, include_nodes=False)

    outer_frame = tk.Frame(parent)
    outer_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(outer_frame)
    scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    table1_frame = tk.Frame(scrollable_frame)
    table1_frame.pack(fill=tk.X, pady=(0, 20))

    # --- Apply font to the main title label ---
    tk.Label(table1_frame, text="Planetary Strengths (Shadbala)", font=devanagari_font_tuple + ('bold',)).pack(anchor='w') # Use the font tuple and add bold

    # --- Apply font to the Treeview ---
    # You need to use ttk.Style to change the font of a Treeview
    style = ttk.Style()

    # Define a style based on the Treeview widget
    # Configure the font for the treeview rows ('Treeview')
    style.configure("Strength.Treeview", font=devanagari_font_tuple, rowheight=25)
    style.configure("Strength.Treeview.Heading", font=devanagari_font_tuple + ('bold',))

    table1 = ttk.Treeview(table1_frame,
        columns=("Rank", "Planet", "Total", "Final%", "Istha", "Kashta"),
        show="headings", height=min(len(table1_data), 10),
        style="Strength.Treeview"  # ← Apply your new style
    )
    for col in table1["columns"]:
        table1.heading(col, text=col)
        # Adjust column widths as needed to fit content
        if col == "Planet":
             table1.column(col, width=70, anchor='center') # Give planet column more width
        elif col == "Rank":
             table1.column(col, width=50, anchor='center')
        else:
            table1.column(col, width=80, anchor='center') # Adjust other widths

    for row in table1_data:
        table1.insert("", "end", values=row)

    table1.pack(fill=tk.X, expand=True) # Allow treeview to expand horizontally

    # --- Apply font to Matplotlib plots ---
    # Matplotlib needs its own font configuration
    # This affects plot titles, axis labels, tick labels, etc.
    devanagari_fonts = [DEV_FONT_FAMILY] + FALLBACK_FONTS
    
    # Find the first available font that supports Devanagari
    available_font = [DEV_FONT_FAMILY] + FALLBACK_FONTS
    for font in devanagari_fonts:
        try:
            # Test if the font is available
            test_fig, test_ax = plt.subplots()
            test_ax.text(0.5, 0.5, "सु", fontfamily=font)
            plt.close(test_fig)
            available_font = font
            break
        except:
            continue
    
    if available_font is None:
        available_font = "Mangal"  # Ultimate fallback
    # Find a font that Matplotlib can use that supports Devanagari
    # Try setting the font family first using rcParams:
    plt.rcParams['font.family'] = available_font # Add a fallback generic family
    plt.rcParams['axes.titlesize'] = 10 # Adjust font sizes if needed
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10


    # You can also try adding font properties directly to text elements if rcParams doesn't fully work:
    # from matplotlib.font_manager import FontProperties
    # try:
    #     dev_font_prop = FontProperties(family=DEV_FONT_FAMILY, size=10)
    # except:
    #     dev_font_prop = FontProperties(family='sans-serif', size=10) # Fallback

    for segment, data in bala_breakdown.items():
        fig, ax = plt.subplots(figsize=(9, 3.7))
        planets = list(data.keys())
        values = list(data.values())

        ax.bar(planets, values, color='teal')

        # Apply font to Matplotlib elements using fontfamily parameter or fontproperties object
        # Using fontfamily parameter directly is often simpler if the font is found
        ax.set_title(f"{segment} Bala (All Planets)", fontfamily=available_font)
        ax.set_ylabel("Points", fontfamily=available_font)
        ax.set_xlabel("Planets", fontfamily=available_font)

        # Apply font to x-axis tick labels (planet names)
        # Explicitly setting font family for each tick label is often necessary
        for tick_label in ax.get_xticklabels():
             tick_label.set_fontfamily(available_font)
             # Or using fontproperties if created: tick_label.set_fontproperties(dev_font_prop)


        ax.set_ylim(0, max(values) * 1.1 if values else 200) # Auto adjust y-limit

        canvas_chart = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas_chart.draw()
        canvas_chart.get_tk_widget().pack(fill=tk.X, expand=True, pady=8) # Allow chart to expand

        # Close the figure to free memory
        plt.close(fig)

    # --- Check for potential non-Devanagari characters used for Devanagari planets ---
    # Ensure your planet keys/names in dictionaries (like ASPECTS, DAY_PLANETS)
    # are the correct Devanagari glyphs ("सु", "चं", "मं", etc.)
    # The issue 'مं' was noted before. Ensure it's corrected to 'मं'.

    return outer_frame

# Rest of the file is unchanged calculations (get_house_number, get_planet_state, etc.)
# ... (Keep the rest of the functions like calculate_uchcha_bala, calculate_cheshta_bala,
# calculate_dig_bala, is_daytime, calculate_kala_bala, calculate_avastha_bala,
# calculate_drik_bala, calculate_saptavargaja_bala, calculate_ishta_kashta,
# calculate_sthanabala, calculate_strengths - they are correctly included above)