import swisseph as swe

# Define constants
dasha_planets = ["Ke", "Ve", "Su", "Mo", "Ma", "Ra", "Ju", "Sa", "Me"]
mahadasha_durations = {"Ke": 7, "Ve": 20, "Su": 6, "Mo": 10, "Ma": 7, "Ra": 18, "Ju": 16, "Sa": 19, "Me": 17}

def calculate_starting_dasha(moon_lon):
    """
    Calculate the starting planet and balance of the first Mahadasha based on Moon's longitude.
    
    Args:
        moon_lon (float): Moon's sidereal longitude in degrees (0-360).
    
    Returns:
        tuple: (starting_planet, balance_years, starting_planet_index)
    """
    nakshatra_span = 360 / 27  # Each Nakshatra spans 13.333... degrees
    nakshatra_index = int(moon_lon / nakshatra_span)
    starting_planet_index = nakshatra_index % 9
    starting_planet = dasha_planets[starting_planet_index]
    proportion_passed = (moon_lon % nakshatra_span) / nakshatra_span
    balance_years = (1 - proportion_passed) * mahadasha_durations[starting_planet]
    return starting_planet, balance_years, starting_planet_index

def generate_dasha_tree(jd_birth, moon_lon, max_levels=4, num_mahadashas=10):
    """
    Generate the Vishmottari Dasha tree up to the specified level.
    
    Args:
        jd_birth (float): Julian Day of birth.
        moon_lon (float): Moon's sidereal longitude in degrees.
        max_levels (int): Maximum depth of Dasha levels (1: Maha, 2: Antar, 3: Pratyantar, 4: Sookshma).
        num_mahadashas (int): Number of Mahadashas to generate.
    
    Returns:
        list: List of Mahadasha dictionaries with nested sub-periods.
    """
    starting_planet, balance_years, starting_index = calculate_starting_dasha(moon_lon)
    mahadashas = []
    current_jd = jd_birth

    # First Mahadasha (partial duration)
    first_duration_days = balance_years * 365.25
    first_end_jd = current_jd + first_duration_days
    first_mahadasha = {
        'planet': starting_planet,
        'start_jd': current_jd,
        'end_jd': first_end_jd,
        'duration_days': first_duration_days
    }
    mahadashas.append(first_mahadasha)
    current_jd = first_end_jd

    # Subsequent Mahadashas (full duration)
    for i in range(1, num_mahadashas):
        planet_index = (starting_index + i) % 9
        planet = dasha_planets[planet_index]
        duration_years = mahadasha_durations[planet]
        duration_days = duration_years * 365.25
        end_jd = current_jd + duration_days
        maha = {
            'planet': planet,
            'start_jd': current_jd,
            'end_jd': end_jd,
            'duration_days': duration_days
        }
        mahadashas.append(maha)
        current_jd = end_jd

    # Generate sub-periods for each Mahadasha
    for maha in mahadashas:
        maha['sub_dashas'] = generate_sub_dashas(maha['planet'], maha['start_jd'], maha['end_jd'], 1, max_levels)

    return mahadashas

def generate_sub_dashas(parent_planet, start_jd, end_jd, level, max_levels):
    """
    Recursively generate sub-periods (Antardasha, Pratyantar Dasha, etc.) for a given period.
    
    Args:
        parent_planet (str): Planet of the parent period.
        start_jd (float): Start Julian Day of the period.
        end_jd (float): End Julian Day of the period.
        level (int): Current level (1: Antar, 2: Pratyantar, 3: Sookshma).
        max_levels (int): Maximum depth to generate.
    
    Returns:
        list: List of sub-period dictionaries.
    """
    if level >= max_levels:
        return []
    
    total_duration_days = end_jd - start_jd
    parent_index = dasha_planets.index(parent_planet)
    sub_planets = dasha_planets[parent_index:] + dasha_planets[:parent_index]
    sub_dashas = []
    current_jd = start_jd

    for p in sub_planets:
        duration_days = (mahadasha_durations[p] / 120.0) * total_duration_days
        sub_end_jd = current_jd + duration_days
        sub_dasha = {
            'planet': p,
            'start_jd': current_jd,
            'end_jd': sub_end_jd,
            'duration_days': duration_days
        }
        if level < max_levels - 1:
            sub_dasha['sub_dashas'] = generate_sub_dashas(p, current_jd, sub_end_jd, level + 1, max_levels)
        sub_dashas.append(sub_dasha)
        current_jd = sub_end_jd

    return sub_dashas

def jd_to_date_str(jd):
    """
    Convert Julian Day to a human-readable date string.
    
    Args:
        jd (float): Julian Day.
    
    Returns:
        str: Formatted date string (e.g., "1991-01-18 18:05:33").
    """
    year, month, day, hour = swe.revjul(jd)
    hour_int = int(hour)
    minute = int((hour - hour_int) * 60)
    second = int(((hour - hour_int) * 60 - minute) * 60)
    return f"{year}-{month:02d}-{day:02d} {hour_int:02d}:{minute:02d}:{second:02d}"