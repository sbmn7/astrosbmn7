import swisseph as swe
from datetime import datetime, timedelta
import pytz
from varr import rasi_names, nakshatras
import os
from pathlib import Path
import sys
import re
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun
import astropy.units as u
import numpy as np
from BS_DATABASE import gregorian_to_bs
from varr import (fixed_karanas, KARANA_NAMES, nakshatras, 
                  NAKSHATRA_NAMES, RASI_NAMES, month_names, 
                  TITHI_NAMES, NADI_MAP,GANA_MAP,VEDIC_WEEKDAYS, 
                  YOGA_NAMES, YONI_MAP, NAAM_AKSHAR_MAP, PADA_SPAN, 
                  RASHI_LORDS, ARUDHA_NAMES, DIVISION_NAMES, YOGINI_NAMES, YOGINI_YEARS, NAKSHATRA_SPAN)
os.environ["FONTCONFIG_PATH"] = os.path.join(os.path.dirname(__file__), "etc", "fonts")
os.environ["PATH"] += os.pathsep + os.path.join(os.path.dirname(__file__), "bin")
os.environ["G_MESSAGES_DEBUG"] = ""  # Suppress GLib-GIO warnings

def set_ephemeris_path():
    try:
        if getattr(sys, 'frozen', False):
            # PyInstaller bundle: use _MEIPASS for extracted files
            base_path = Path(sys._MEIPASS)
        else:
            # Development: use script's directory
            base_path = Path(__file__).parent
        ephe_path = base_path / "ephe"
        if not ephe_path.exists():
            raise FileNotFoundError(f"Ephemeris folder not found at: {ephe_path}")
        se1_files = list(ephe_path.glob("*.se1"))
        if not se1_files:
            raise FileNotFoundError(f"No .se1 ephemeris files found in: {ephe_path}")
        swe.set_ephe_path(str(ephe_path))
        return str(ephe_path)
    except (FileNotFoundError, Exception):
        sys.exit(1)

# Define base directory and font path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSansDevanagariUI-Regular.ttf")

# Set ephemeris path and store it globally
EPHE_PATH = set_ephemeris_path()
planet_speeds = {}  # new global
PLANETS = {
    "सु": swe.SUN, "चं": swe.MOON, "मं": swe.MARS,
    "बु": swe.MERCURY, "गु": swe.JUPITER, "शु": swe.VENUS,
    "श": swe.SATURN, "रा": swe.MEAN_NODE, "के": swe.MEAN_NODE 
}
def is_polar_region(lat):
    return abs(lat) >= 66.5  # Arctic/Antarctic Circle
def get_lahiri(jd):
    """
    Improved Lahiri (Chitra Paksha) Ayanamsa Calculation
    
    Uses quadratic formula for better accuracy over long time periods:
    - Base at J2000: 23° 51' 23" (23.8563889°)
    - Linear rate: 50.2564 arcsec/year
    - Quadratic term: accounts for precession rate changes
    
    Args:
        jd (float): Julian Date
    
    Returns:
        float: Lahiri ayanamsa in degrees
    """
    JD_J2000 = 2451545.0
    BASE_J2000_DEG = 23.85638888888889
    
    # Julian centuries from J2000
    t = (jd - JD_J2000) / 36525.0
    
    # Quadratic formula: Ayanamsa = Base + (Rate × t) + (Quadratic × t²)
    LINEAR_RATE = 5025.64      # arcseconds per century
    QUADRATIC_TERM = 1.11161   # arcseconds per century²
    
    precession_arcsec = (LINEAR_RATE * t) + (QUADRATIC_TERM * t * t)
    precession_deg = precession_arcsec / 3600.0
    
    ayanamsa_deg = BASE_J2000_DEG + precession_deg
    ayanamsa_deg = ayanamsa_deg % 360.0
    
    return round(ayanamsa_deg, 6)
def get_true_lahiri(jd):
    """
    TRUE Lahiri (Chitra Paksha) Ayanamsa
    Ayanamsa = True tropical longitude of Chitra (Spica) − 180°
    Works with ALL pyswisseph versions
    """
    import traceback
    
    # Print call stack to see WHO is calling this function
    print(f"\n{'='*70}")
    print(f"🔍🔍🔍 get_true_lahiri() CALLED - JD={jd:.2f}")
    print(f"{'='*70}")
    print("CALL STACK:")
    stack = traceback.extract_stack()
    for i, frame in enumerate(stack[-6:-1]):  # Show last 5 frames before this one
        print(f"  {i+1}. {frame.filename}:{frame.lineno} in {frame.name}")
        print(f"     {frame.line}")
    print(f"{'='*70}\n")
    flags = swe.FLG_SWIEPH | swe.FLG_TRUEPOS

    result = swe.fixstar_ut("Spica", jd, flags)

    # result[0] is ALWAYS the position array
    lon = result[0][0]   # longitude only
    ayanamsa = (lon - 180.0) % 360.0
    
    return (lon - 180.0) % 360.0
# ============================================================================
# KP (Krishnamurti Paddhati) AYANAMSA FUNCTIONS
# ============================================================================

KP_PRECESSION_RATE = 50.2388475  # arcseconds per year
KP_OLD_ZERO_YEAR = 291
KP_NEW_ZERO_YEAR = 292

def get_kp_old(jd):
    """OLD KP Ayanamsa - uses 291 AD as zero year"""
    year, month, day, hour = swe.revjul(jd)
    day_of_year = (datetime(year, month, day) - datetime(year, 1, 1)).days + 1
    days_in_year = 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365
    decimal_year = year + (day_of_year + hour/24) / days_in_year
    years_from_zero = decimal_year - KP_OLD_ZERO_YEAR
    ayanamsa_arcseconds = years_from_zero * KP_PRECESSION_RATE
    return ayanamsa_arcseconds / 3600.0

def get_kp_new(jd):
    """NEW KP Ayanamsa - uses 292 AD as zero year (more accurate)"""
    year, month, day, hour = swe.revjul(jd)
    day_of_year = (datetime(year, month, day) - datetime(year, 1, 1)).days + 1
    days_in_year = 366 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 365
    decimal_year = year + (day_of_year + hour/24) / days_in_year
    years_from_zero = decimal_year - KP_NEW_ZERO_YEAR
    ayanamsa_arcseconds = years_from_zero * KP_PRECESSION_RATE
    return ayanamsa_arcseconds / 3600.0
def get_ayanamsa(jd, ayanamsa_type):
    """
    Returns the ayanamsa value for a given Julian Date.
    Restricted to 'Lahiri' and 'True Lahiri' only.
    """

    if ayanamsa_type == "Lahiri":
        return get_lahiri(jd) 

    elif ayanamsa_type == "True Lahiri":
        return get_true_lahiri(jd) 
    elif ayanamsa_type == "KP Old":
        return get_kp_old(jd)
    elif ayanamsa_type == "KP New":
        return get_kp_new(jd)
    else:
        # Prevents the use of any other ayanamsa types
        raise ValueError(
            f"Ayanamsa '{ayanamsa_type}' is not supported. "
            "Only 'Lahiri' and 'True Lahiri' are allowed."
        )
def convert_to_dms(decimal, is_latitude=True):
    degrees = int(abs(decimal))
    minutes_decimal = abs(decimal - degrees) * 60
    minutes = int(minutes_decimal)
    seconds = int((minutes_decimal - minutes) * 60)
    
    if is_latitude:
        direction = "N" if decimal >= 0 else "S"
    else:
        direction = "E" if decimal >= 0 else "W"
        
    return degrees, minutes, seconds, direction
def get_divisional_position(degree, division):
    """
    Returns the sidereal longitude of a planet in the given divisional chart.
    The result is in degrees (0–360).
    """
    sign = int(degree / 30)
    deg_in_sign = degree % 30
    new_deg_in_sign = deg_in_sign  # Initialize to avoid UnboundLocalError

    if division == 1:
        return degree

    elif division == 2:  # Hora
        if sign % 2 == 0:  # Even Rasi
            return 120 if deg_in_sign < 15 else 90  # सिंह or कर्क
        else:  # Odd Rasi
            return 90 if deg_in_sign < 15 else 120  # कर्क or सिंह

    elif division == 3:  # Drekkana
        if deg_in_sign < 10:
            new_sign = sign
        elif deg_in_sign < 20:
            new_sign = (sign + 4) % 12
        else:
            new_sign = (sign + 8) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 4:  # Chaturthamsha
        part = int(deg_in_sign / 7.5)
        new_sign = (sign + part * 4) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 5:  # Panchamsha
        part = int(deg_in_sign / 6)
        if sign % 2 == 0:
            new_sign = (sign + part) % 12
        else:
            new_sign = (sign + (4 - part)) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 6:  # Shashtamsha
        part = int(deg_in_sign / 5)
        if sign % 2 == 0:
            new_sign = (sign + part) % 12
        else:
            new_sign = (sign + (5 - part)) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 7:  # Saptamsha
        part = int(deg_in_sign / (30 / 7))
        if sign % 2 == 0:
            new_sign = (sign - part + 7) % 12
        else:
            new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 8:  # Ashtamsha
        part = int(deg_in_sign / 3.75)
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign
    
    elif division == 9:  # D9 Navamsa using Maitreya logic
        return (degree * 9) % 360
    elif division == 10:  # Dasamsha
        part = int(deg_in_sign / 3)
        if sign % 2 == 0:
            new_sign = (sign + 9 + part) % 12
        else:
            new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 12:  # Dvadashamsha
        part = int(deg_in_sign / 2.5)
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 16:  # Shodashamsha
        part = int(deg_in_sign / 1.875)
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 20:  # Vimshamsha
        part = int(deg_in_sign / 1.5)
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 24:  # Siddhamsha
        part = int(deg_in_sign / 1.25)
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 27:  # Bhamsha
        part = int(deg_in_sign / 1.1111)
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 30:  # Trimshamsha (parashara unequal)
        if sign % 2 == 0:  # even signs
            if deg_in_sign < 5:
                new_sign = 11  # मिन
            elif deg_in_sign < 10:
                new_sign = 0   # मेष
            elif deg_in_sign < 18:
                new_sign = 1   # बृष
            elif deg_in_sign < 25:
                new_sign = 2   # मिथुन
            else:
                new_sign = 3   # कर्क
        else:  # odd signs
            if deg_in_sign < 5:
                new_sign = 5   # कन्या
            elif deg_in_sign < 12:
                new_sign = 6   # तुला
            elif deg_in_sign < 20:
                new_sign = 7   # बृश्चिक
            elif deg_in_sign < 25:
                new_sign = 8   # धनु
            else:
                new_sign = 9   # मकर
        return new_sign * 30 + deg_in_sign

    elif division == 40:  # Khavedamsha
        part = int(deg_in_sign / 0.75)
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 45:  # Akshavedamsha
        part = int(deg_in_sign / (30 / 45))
        new_sign = (sign + part) % 12
        return new_sign * 30 + deg_in_sign

    elif division == 60:  # Shashtiamsha
        slice_size = 30.0 / division
        part = int(deg_in_sign / slice_size)
        new_sign = (sign + part) % 12
        intra_slice_deg = deg_in_sign - part * slice_size
        new_deg_in_sign = intra_slice_deg * division
        return new_sign * 30 + new_deg_in_sign
    elif division == 81:  # D81
        slice_size = 30.0 / division
        part = int(deg_in_sign / slice_size)
        new_sign = (sign + part) % 12
        intra_slice_deg = deg_in_sign - part * slice_size
        new_deg_in_sign = intra_slice_deg * division
        return new_sign * 30 + new_deg_in_sign

    elif division == 108:  # D108
        slice_size = 30.0 / division
        part = int(deg_in_sign / slice_size)
        new_sign = (sign + part) % 12
        intra_slice_deg = deg_in_sign - part * slice_size
        new_deg_in_sign = intra_slice_deg * division
        return new_sign * 30 + new_deg_in_sign

    elif division == 144:  # D144
        slice_size = 30.0 / division
        part = int(deg_in_sign / slice_size)
        new_sign = (sign + part) % 12
        intra_slice_deg = deg_in_sign - part * slice_size
        new_deg_in_sign = intra_slice_deg * division
        return new_sign * 30 + new_deg_in_sign

    elif division == 150:  # D150
        slice_size = 30.0 / division
        part = int(deg_in_sign / slice_size)
        new_sign = (sign + part) % 12
        intra_slice_deg = deg_in_sign - part * slice_size
        new_deg_in_sign = intra_slice_deg * division
        return new_sign * 30 + new_deg_in_sign

    else:
        # Default fallback
        return (degree * division) % 360
def get_sidereal_positions(jd, ayanamsa_type):
    """
    Calculates sidereal positions for planets using only supported ayanamsas.
    """
    positions = {}
    retro_flags = {}
    combust_flags = {}

    # Always compute TROPICAL positions first
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED 
    # Select ayanamsa - strictly restricted to requested types
    if ayanamsa_type == "Lahiri":
        ayanamsa_deg = get_lahiri(jd) 

    elif ayanamsa_type == "True Lahiri":
        ayanamsa_deg = get_true_lahiri(jd) 
    elif ayanamsa_type == "KP Old":
        ayanamsa_deg = get_kp_old(jd)
    elif ayanamsa_type == "KP New":
        ayanamsa_deg = get_kp_new(jd)
    else:
        raise ValueError(
            f"Ayanamsa '{ayanamsa_type}' not supported. "
            "Use 'Lahiri' or 'True Lahiri'."
        ) 
    # Planet loop for calculations
    for name, pid in PLANETS.items():
        pos_array, used_flags = swe.calc_ut(jd, pid, flags) 
        tropical_lon = pos_array[0]
        # Calculate sidereal longitude by subtracting the chosen ayanamsa
        sidereal_lon = (tropical_lon - ayanamsa_deg) % 360 

        positions[name] = sidereal_lon
        retro_flags[name] = pos_array[3] < 0 

    # Handle nodes and combustion as per existing logic
    rahu_pos = positions["रा"]
    positions["के"] = (rahu_pos + 180) % 360 
    retro_flags["के"] = False 
    sun_pos = positions["सु"]
    for name in positions:
        if name in ["सु", "रा", "के"]:
            combust_flags[name] = False
            continue

        diff = abs(positions[name] - sun_pos) % 360
        combust_flags[name] = min(diff, 360 - diff) < 6 

    return positions, retro_flags, combust_flags, ayanamsa_deg
def make_chart_data(positions, division, ascendant_sign, retro_flags=None, combust_flags=None):
    chart = {i: [] for i in range(12)}
    
    if retro_flags is None: retro_flags = {}
    if combust_flags is None: combust_flags = {}

    # Define the planets that should never show the retrograde symbol
    nodes = ['रा', 'के', 'Ra', 'Ke'] 

    for planet, degree in positions.items():
        if planet == 'Asc':
            continue

        label = planet
        
        # Check if the planet is retrograde AND ensure it's not a node
        if retro_flags.get(planet, False) and planet not in nodes:
            label += '®'
            
        if combust_flags.get(planet, False):
            label += '©'

        # Calculate divisional position
        divisional_position = get_divisional_position(degree, division)
        planet_sign = int(divisional_position // 30)
        
        # Calculate house number using whole-sign system
        house_number = (planet_sign - ascendant_sign + 12) % 12
        chart[house_number].append(label)

    return chart
def calculate_upagrahas(lmt_chart, ayanamsa_type):

    def get_lagna_degree(dt):

        if "lat" not in lmt_chart or "lon" not in lmt_chart or "tz_name" not in lmt_chart:
            raise ValueError("Missing lat, lon, or tz_name in lmt_chart")

        local_tz = pytz.timezone(lmt_chart["tz_name"])
        local_dt = dt if dt.tzinfo else local_tz.localize(dt)
        utc_dt = local_dt.astimezone(pytz.utc)

        jd = swe.julday(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
        )

        if ayanamsa_type == "Lahiri":
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            house_result = swe.houses_ex(jd, lmt_chart["lat"], lmt_chart["lon"], b'W', flags=swe.FLG_SIDEREAL)
            ascendant_degree = house_result[1][0] % 360

        else:
            ayanamsa_deg = get_ayanamsa(jd, ayanamsa_type)
            house_result = swe.houses_ex(jd, lmt_chart["lat"], lmt_chart["lon"], b'W', flags=swe.FLG_SWIEPH)
            ascendant_tropical = house_result[1][0]
            ascendant_degree = (ascendant_tropical - ayanamsa_deg) % 360

        return ascendant_degree
    # Helper function to generate metadata
    def get_lagna_meta(degree):
        """
        Generate metadata for a given degree: degree, sign, nakshatra, pada.
        """
        rasi = int(degree // 30)
        
        nakshatra_index = int(degree // 13.3333)
        nakshatra_pos = degree % 13.3333
        pada = int(nakshatra_pos // 3.3333) + 1

        return {
            "degree": round(degree % 30, 2),
            "rasi": rasi_names[rasi],
            "nakshatra": nakshatras[nakshatra_index],
            "pada": pada
        }

    # Parse birth datetime and sunrise/sunset times
    birth_dt = lmt_chart["datetime"]
    date = birth_dt.date()
    local_tz = pytz.timezone(lmt_chart["tz_name"])

    # Parse "HH:MM:SS" format and localize to timezone
    try:
        sunrise_parts = list(map(int, lmt_chart["sunrise"].split(":")))
        sunset_parts = list(map(int, lmt_chart["sunset"].split(":")))
    except (ValueError, KeyError) as e:
        raise ValueError("Invalid sunrise or sunset format. Expected 'HH:MM:SS'.") from e

    sunrise_dt = datetime(date.year, date.month, date.day,
                          sunrise_parts[0], sunrise_parts[1], sunrise_parts[2])
    sunset_dt = datetime(date.year, date.month, date.day,
                         sunset_parts[0], sunset_parts[1], sunset_parts[2])

    # Localize sunrise and sunset to the same timezone as birth_dt
    sunrise_dt = local_tz.localize(sunrise_dt)
    sunset_dt = local_tz.localize(sunset_dt)

    # Determine if birth is during day (sunrise to sunset) or night
    is_day = (sunrise_dt <= birth_dt < sunset_dt)

    # Day duration in seconds
    day_duration = (sunset_dt - sunrise_dt).total_seconds()

    # Ghatika counts (24 min) for Gulika (Mandi) for day and night births
    day_ghatika = {6: 26, 0: 22, 1: 18, 2: 14, 3: 10, 4: 6,  5: 2}
    night_ghatika = {6: 10, 0: 6,  1: 2,  2: 26, 3: 22, 4: 18, 5: 14}
    # Upagraha rising values (out of 32) for Kala, Yamaghantaka, Mrityu
    Kala_day   = {6: 2,  0: 30, 1: 26, 2: 22, 3: 18, 4: 14, 5: 10}
    Kala_night = {6: 14, 0: 10, 1: 6,  2: 2,  3: 30, 4: 26, 5: 22}
    Yama_day   = {6: 18, 0: 14, 1: 10, 2: 6,  3: 2,  4: 30, 5: 26}
    Yama_night = {6: 2,  0: 30, 1: 26, 2: 22, 3: 18, 4: 14, 5: 10}
    Mrtyu_day  = {6: 10, 0: 6,  1: 2,  2: 30, 3: 26, 4: 22, 5: 18}
    Mrtyu_night= {6: 22, 0: 18, 1: 14, 2: 10, 3: 6,  4: 2,  5: 30}
    ardhaprahara_day = {0: 10, 1: 6, 2: 2, 3: 30, 4: 26, 5: 22, 6: 18} # Sunday=0..Saturday=6
    ardhaprahara_night = {0: 22, 1: 18, 2: 14, 3: 10, 4: 6, 5: 2, 6: 30}

    wd = birth_dt.weekday()  # Monday=0,... Sunday=6

    # --- Gulika (Mandi) using ghatika table ---
    if is_day:
        gh = day_ghatika.get(wd, 0)
        gulika_dt = sunrise_dt + timedelta(minutes=gh * 24)
    else:
        gh = night_ghatika.get(wd, 0)
        gulika_dt = sunset_dt + timedelta(minutes=gh * 24)
    gulika_deg = get_lagna_degree(gulika_dt)

    # --- Kala (Sun's portion) ---
    if is_day:
        val = Kala_day.get(wd, 0)
        kala_dt = sunrise_dt + timedelta(seconds=day_duration * val / 32.0)
    else:
        val = Kala_night.get(wd, 0)
        kala_dt = sunset_dt + timedelta(seconds=day_duration * val / 32.0)
    kala_deg = get_lagna_degree(kala_dt)

    # --- Yamaghantaka (Jupiter's portion) ---
    if is_day:
        val = Yama_day.get(wd, 0)
        yama_dt = sunrise_dt + timedelta(seconds=day_duration * val / 32.0)
    else:
        val = Yama_night.get(wd, 0)
        yama_dt = sunset_dt + timedelta(seconds=day_duration * val / 32.0)
    yama_deg = get_lagna_degree(yama_dt)

    # --- Mrityu (Mars's portion) ---
    if is_day:
        val = Mrtyu_day.get(wd, 0)
        mrtyu_dt = sunrise_dt + timedelta(seconds=day_duration * val / 32.0)
    else:
        val = Mrtyu_night.get(wd, 0)
        mrtyu_dt = sunset_dt + timedelta(seconds=day_duration * val / 32.0)
    mrtyu_deg = get_lagna_degree(mrtyu_dt)
    # ardhaprahara section
    if is_day:
        gh = ardhaprahara_day.get(wd, 0) # Check if wd matches your dict keys
        ardhaprahara_dt = sunrise_dt + timedelta(minutes=gh * 24)
    else:
        gh = ardhaprahara_night.get(wd, 0) # Check if wd matches your dict keys
        ardhaprahara_dt = sunset_dt + timedelta(minutes=gh * 24)
    ardhaprahara_deg = get_lagna_degree(ardhaprahara_dt)
    # --- Shadow (Aprakasha) upagrahas from Sun longitude ---
    try:
        sun_deg = lmt_chart["planet_positions"]["सूर्य"]
    except KeyError:
        # Map alternative Sun keys
        planet_key_map = {"Sun": "सूर्य", "SU": "सूर्य", "su": "सूर्य", "Surya": "सूर्य", "सु": "सूर्य"}
        for key in planet_key_map:
            if key in lmt_chart["planet_positions"]:
                sun_deg = lmt_chart["planet_positions"][key]
                break
        else:
            available_keys = list(lmt_chart["planet_positions"].keys())
            raise ValueError(
                f"Sun position ('सूर्य' or equivalent) not found in planet_positions. "
                f"Available keys: {available_keys}"
            )
    dhuma_deg = (sun_deg + 133 + 20/60.0) % 360
    vyatipata_deg = (360 - dhuma_deg) % 360
    parivesha_deg = (180 + vyatipata_deg) % 360
    indrachapa_deg = (360 - parivesha_deg) % 360
    upaketu_deg = (16 + 40/60.0 + indrachapa_deg) % 360

    # Build result dict with get_lagna_meta
    upagrahas = {
        "गु":  get_lagna_meta(gulika_deg),
        "य":   get_lagna_meta(yama_deg),
        "का": get_lagna_meta(kala_deg),
        "मृ":  get_lagna_meta(mrtyu_deg),
        "अ": get_lagna_meta(ardhaprahara_deg), # Added Ardhaprahara here
        "धु":  get_lagna_meta(dhuma_deg),
        "व्या": get_lagna_meta(vyatipata_deg),
        "प":   get_lagna_meta(parivesha_deg),
        "इ":   get_lagna_meta(indrachapa_deg),
        "उ":   get_lagna_meta(upaketu_deg)
    }
    return upagrahas
def calculate_lmt_and_charts_logic(input_data):
    """
    Logic separated from GUI. 
    input_data: dict containing 'name', 'gender', 'date', 'hour', 'minute', 
                'second', 'ampm', 'tz_name', 'lat', 'lon', 'ayanamsa'
    """
    # 1. Input Extraction (No .get() calls)
    name = input_data.get('name', '').strip()
    lat = float(input_data['lat'])
    lon = float(input_data['lon'])
    greg_date = input_data['date']
    hour = int(input_data['hour'])
    minute = int(input_data['minute'])
    second = int(input_data['second'])
    ampm = input_data['ampm']
    tz_name = input_data['tz_name']
    ayanamsa_type = input_data.get('ayanamsa', 'Lahiri')

    # 2. Datetime and Timezone Logic (Pure Python)
    if ampm == "PM" and hour != 12: hour += 12
    elif ampm == "AM" and hour == 12: hour = 0

    dt_str = f"{greg_date} {hour:02d}:{minute:02d}:{second:02d}"
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    
    local_tz = pytz.timezone(tz_name)
    try:
        local_dt = local_tz.localize(dt, is_dst=None)
    except pytz.exceptions.AmbiguousTimeError:
        local_dt = local_tz.localize(dt, is_dst=False)

    utc_dt = local_dt.astimezone(pytz.utc)

    # 3. LMT Calculations
    lmt = utc_dt + timedelta(seconds=lon * 240)
    lat_deg, lat_min, lat_sec, lat_dir = convert_to_dms(lat, True)
    lon_deg, lon_min, lon_sec, lon_dir = convert_to_dms(lon, False)

    # 4. Julian Day and Swisseph (Astro Logic)
    jd_value = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    )

    pos_data, retro, combust, ayan_deg = get_sidereal_positions(jd_value, ayanamsa_type)

    # Calculate Houses
    house_result = swe.houses_ex(jd_value, lat, lon, b'W', flags=swe.FLG_SWIEPH)
    asc_tropical = house_result[1][0]
    asc_sidereal = (asc_tropical - ayan_deg) % 360
    
    pos_data['Asc'] = asc_sidereal
    asc_sign_d1 = int(asc_sidereal // 30) % 12
    rashi_nums = [(asc_sign_d1 + i) % 12 + 1 for i in range(12)]

    # 5. Panchang and Upagrahas
    panchang = calculate_panchang(jd_value, lat, lon, tz_name, pos_data)
    
    # Prep for Upagrahas (Mapping keys)
    planet_pos_map = pos_data.copy()
    if "Sun" in planet_pos_map: planet_pos_map["सूर्य"] = planet_pos_map.pop("Sun")
    
    upagraha_data = calculate_upagrahas({
        "datetime": lmt,
        "sunrise": panchang['data']['sunrise'],
        "sunset": panchang['data']['sunset'],
        "planet_positions": planet_pos_map,
        "lat": lat,
        "lon": lon,
        "tz_name": tz_name
    }, ayanamsa_type)


    # 6. Return Data Structure (To be used by PyQt to update the UI)
    return {
        "jd": jd_value,
        "positions": pos_data,
        "rashi_numbers": rashi_nums,
        "retro_flags": retro,
        "combust_flags": combust,
        "panchang": panchang,
        "upagrahas": upagraha_data,
        "lmt_str": lmt.strftime('%Y-%m-%d %I:%M:%S %p'),
        "coords_str": f"{int(lat_deg)}°{int(lat_min)}'{int(lat_sec)}\"{lat_dir}, {int(lon_deg)}°{int(lon_min)}'{int(lon_sec)}\"{lon_dir}"
    }
def get_divisional_data_package(selected_division_str, positions, retro_flags, combust_flags):
    """
    Pure logic to calculate divisional chart data.
    Returns: (chart_data, rashi_numbers, title)
    """
    # 1. Extract Division Number using Regex
    match = re.search(r"D(\d+)", selected_division_str)
    if not match:
        return None
    
    division = int(match.group(1))

    # 2. Calculate Ascendant for this division
    # positions['Asc'] comes from your previous sidereal calculation
    asc_deg = get_divisional_position(positions['Asc'], division)
    asc_sign = int(asc_deg / 30)

    # 3. Generate chart content (which planet is in which house)
    chart_data = make_chart_data(positions, division, asc_sign, retro_flags, combust_flags)
    
    # 4. Generate the house numbers (Rashi numbers) for the 12 houses
    rashi_numbers_div = [(asc_sign + i) % 12 + 1 for i in range(12)]
    
    title = f"{selected_division_str} Chart"
    
    return chart_data, rashi_numbers_div, title
def get_nakshatra_from_degree(degree):
    """Get nakshatra name from degree (0-360)"""
    # Each nakshatra is 13°20' (800 minutes or 13.333... degrees)
    nak_index = int(degree / (360 / 27)) % 27
    return NAKSHATRA_NAMES[nak_index]

def get_pada_from_degree(degree):
    """Get pada (1-4) from degree (0-360)"""
    # Each nakshatra has 4 padas, each pada is 3°20' (200 minutes or 3.333... degrees)
    pada_index = int(degree / (360 / 108)) % 4
    return pada_index + 1  # Pada is 1-indexed

def get_rashi_from_degree(degree):
    """Get rashi name from degree (0-360)"""
    rashi_index = int(degree / 30) % 12
    return RASI_NAMES[rashi_index]

def _calculate_karana(tithi_deg):
    """
    Calculate Karana based on Tithi degrees.
    """
    # Normalize tithi_deg to 0-360
    tithi_deg = tithi_deg % 360
    # Each Karana spans 6 degrees
    karana_num = int(tithi_deg / 6)
    if karana_num in fixed_karanas:
        return fixed_karanas[karana_num]
    else:
        # Movable Karanas cycle through the first 7 names
        return KARANA_NAMES[(karana_num - 1) % 7]

def calculate_sunrise_sunset(date, lat, lon, local_tz_name):
    """
    Calculate local sunrise and sunset times using Astropy.

    Args:
        date (datetime.date or str): Date in 'YYYY/MM/DD' format or datetime.date
        lat (float): Latitude in degrees
        lon (float): Longitude in degrees
        local_tz_name (str): Timezone name (e.g., 'Asia/Kathmandu')

    Returns:
        (datetime, datetime): Tuple of (sunrise_local, sunset_local)
    """
    try:
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y/%m/%d").date()

        observer_location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
        local_tz = pytz.timezone(local_tz_name)

        # Midnight UTC start for the date
        utc_midnight = datetime(date.year, date.month, date.day, 0, 0, 0)
        utc_midnight_time = Time(utc_midnight, format='datetime', scale='utc')

        # Generate 1000 points from midnight to next midnight
        times = utc_midnight_time + np.linspace(0, 24, 1000) * u.hour
        altaz = get_sun(times).transform_to(AltAz(obstime=times, location=observer_location))

        # Sunrise: when sun altitude crosses from negative to positive
        sunrise_idx = np.where((altaz.alt[:-1] < 0) & (altaz.alt[1:] >= 0))[0]
        sunrise_local = None
        if sunrise_idx.size > 0:
            sunrise_time = times[sunrise_idx[0]]
            sunrise_local = sunrise_time.to_datetime(timezone=pytz.utc).astimezone(local_tz)

        # Sunset: when sun altitude crosses from positive to negative
        sunset_idx = np.where((altaz.alt[:-1] >= 0) & (altaz.alt[1:] < 0))[0]
        sunset_local = None
        if sunset_idx.size > 0:
            sunset_time = times[sunset_idx[-1]]
            sunset_local = sunset_time.to_datetime(timezone=pytz.utc).astimezone(local_tz)

        return sunrise_local, sunset_local

    except Exception as e:
        print(f"Astropy sunrise/sunset error: {e}")
        return None, None
import traceback

def julian_day_to_gregorian(jd):
    """
    Fliegel–Van Flandern algorithm to turn a Julian Day (float) into a 'YYYY-MM-DD' string.
    """
    J = int(jd + 0.5)
    f = J + 1401 + (((4 * J + 274277) // 146097) * 3) // 4 - 38
    e = 4 * f + 3
    g = (e % 1461) // 4
    h = 5 * g + 2
    day = (h % 153) // 5 + 1
    month = ((h // 153 + 2) % 12) + 1
    year = e // 1461 - 4716 + (12 + 2 - month) // 12
    return f"{year:04d}-{month:02d}-{day:02d}"

def calculate_lunar_month_year(jd):
    """
    Calculate the lunar month and year for the Bikram Sambat calendar,
    by converting JD → Gregorian → BS, then mapping month number → name.
    """
    try:
        # 1) JD → Gregorian date string
        greg_date = julian_day_to_gregorian(jd)

        # 2) Gregorian → BS using your existing function
        bs_date = gregorian_to_bs(greg_date)
        if not isinstance(bs_date, str):
            # something went wrong upstream
            return None, None

        # 3) Parse BS and map month number → Nepali month name
        bs_year, bs_month, _ = map(int, bs_date.split('-'))
        lunar_month_name = month_names[bs_month - 1]
        lunar_year = bs_year

        return lunar_month_name, lunar_year

    except Exception:
        traceback.print_exc()
        return None, None
# ───────────── NAKSHATRA ATTRIBUTES ─────────────
def calculate_panchang(jd, lat, lon, local_tz_name, positions):
    results = {}
    def get_varna_from_moon(moon_lon):
        rashi_index = int(moon_lon / 30) % 12  # Added %12 for safety

        if rashi_index in [3, 7, 11]:      # Cancer, Scorpio, Pisces
            return "ब्राह्मण"
        elif rashi_index in [0, 4, 8]:     # Aries, Leo, Sagittarius
            return "क्षत्रिय"
        elif rashi_index in [1, 5, 9]:     # Taurus, Virgo, Capricorn
            return "वैश्य"
        else:                              # Gemini, Libra, Aquarius
            return "शूद्र"

    try:
        # 1. VALIDATE CRITICAL INPUTS
        if not positions or 'सु' not in positions or 'चं' not in positions:
            raise ValueError("Missing Sun/Moon positions in input data")

        # 2. CALCULATE CORE PANCHANG ELEMENTS
        sun_lon = positions['सु'] % 360
        moon_lon = positions['चं'] % 360
        
        # ULTRA-SAFE nakshatra calculation
        # Each nakshatra is 13.333... degrees (360/27)
        nakshatra_span = 360.0 / 27.0  # = 13.333333...
        
        # Use min() to ensure we never get 27
        nak_index = min(int(moon_lon / nakshatra_span), 26)
        
        # Debug output
        print(f"DEBUG: moon_lon={moon_lon:.6f}, nak_index={nak_index}, max_index=26")
        
        # Verify all maps have 27 elements
        print(f"DEBUG: NADI_MAP len={len(NADI_MAP)}, GANA_MAP len={len(GANA_MAP)}, YONI_MAP len={len(YONI_MAP)}")
        # ---- PADA & NAAM AKSHAR CALCULATION ----

        nakshatra_start_deg = nak_index * nakshatra_span
        deg_in_nak = moon_lon - nakshatra_start_deg
        if deg_in_nak < 0:
            deg_in_nak += 360

        pada_index = int(deg_in_nak / PADA_SPAN)
        pada_index = min(pada_index, 3)   # safety

        pada_number = pada_index + 1
        naam_akshar = NAAM_AKSHAR_MAP[nak_index][pada_index]

        tithi_deg = (moon_lon - sun_lon) % 360
        
        results.update({
            'tithi': TITHI_NAMES[min(int(tithi_deg / 12), len(TITHI_NAMES) - 1)],
            'nakshatra': NAKSHATRA_NAMES[nak_index],  # Use same safe index
            'yoga': YOGA_NAMES[int((sun_lon + moon_lon) % 360 / (800 / 60)) % len(YOGA_NAMES)],
            'karana': _calculate_karana(tithi_deg),
            'nadi': NADI_MAP[nak_index],
            'gana': GANA_MAP[nak_index],
            'yoni': YONI_MAP[nak_index],
            'varna': get_varna_from_moon(moon_lon),
            'naam_akshar': naam_akshar
        })

        # 3. CALCULATE WEEKDAY
        try:
            year, month, day, hour = swe.revjul(jd)
            utc_dt = datetime(year, month, day, int(hour), int((hour % 1) * 60))
            local_tz = pytz.timezone(local_tz_name)
            local_dt = local_tz.localize(utc_dt) if utc_dt.tzinfo is None else utc_dt.astimezone(local_tz)
            results['weekday'] = VEDIC_WEEKDAYS[(local_dt.weekday() + 1) % 7]
        except Exception as e:
            results['weekday'] = f"Weekday Error: {str(e)}"

        # 4. SUNRISE/SUNSET CALCULATION
        try:
            year, month, day, hour = swe.revjul(jd)
            date = f"{year}/{month:02d}/{day:02d}"
            sunrise_local, sunset_local = calculate_sunrise_sunset(date, lat, lon, local_tz_name)

            results.update({
                'sunrise': sunrise_local.strftime("%H:%M:%S"),
                'sunset': sunset_local.strftime("%H:%M:%S")
            })
        except Exception as e:
            traceback.print_exc()
            results.update({
                'sunrise': f"Error: {str(e)}",
                'sunset': f"Error: {str(e)}"
            })

        # 5. LUNAR MONTH AND YEAR CALCULATION
        try:
            lunar_month_name, lunar_year = calculate_lunar_month_year(jd)
            if lunar_month_name is not None and lunar_year is not None:
                results.update({
                    'lunar_month': lunar_month_name,
                    'lunar_year': lunar_year
                })
            else:
                results.update({
                    'lunar_month': "Error calculating lunar month",
                    'lunar_year': "Error calculating lunar year"
                })
        except Exception as e:
            traceback.print_exc()
            results.update({
                'lunar_month': f"Error: {str(e)}",
                'lunar_year': f"Error: {str(e)}"
            })

        # 6. RETURN SUCCESSFUL RESULTS
        return {
            'status': 'success',
            'data': results,
            'meta': {
                'calculation_time': datetime.now().isoformat(),
                'ephemeris_path': EPHE_PATH
            }
        }

    except Exception as e:
        traceback.print_exc()
        return {
            'status': 'error',
            'message': f"Panchang calculation failed: {str(e)}",
            'traceback': traceback.format_exc(),
            'debug': {
                'input_jd': jd,
                'positions_keys': list(positions.keys()) if positions else None,
                'list_lengths': {
                    'TITHI_NAMES': len(TITHI_NAMES),
                    'NAKSHATRA_NAMES': len(NAKSHATRA_NAMES),
                    'YOGA_NAMES': len(YOGA_NAMES),
                    'KARANA_NAMES': len(KARANA_NAMES),
                    'VEDIC_WEEKDAYS': len(VEDIC_WEEKDAYS),
                    'NADI_MAP': len(NADI_MAP),
                    'GANA_MAP': len(GANA_MAP),
                    'YONI_MAP': len(YONI_MAP)
                }
            }
        }
def calculate_and_display_planetary_positions(positions, ayanamsa):
    # Define nakshatra and rasi names
    # Calculate nakshatra, pada, and rasi for each planet
    planetary_positions = []
    for planet, degree in positions.items():
        if planet == 'Asc':
            continue
        
        # Calculate nakshatra and pada
        nakshatra_index = int((degree * 27) / 360) % 27
        nakshatra_name = NAKSHATRA_NAMES[nakshatra_index]
        
        # Calculate the position within the nakshatra
        nakshatra_start_degree = (nakshatra_index * 360) / 27
        position_within_nakshatra = degree - nakshatra_start_degree
        
        # Calculate the pada (1 to 4)
        pada = int(position_within_nakshatra / (360 / 27 / 4)) + 1

        # Calculate rasi
        rasi_index = int(degree / 30) % 12
        rasi_name = RASI_NAMES[rasi_index]

        # Calculate degree within the house
        house_degree = degree % 30

        # Format the information
        planetary_positions.append(f"{planet}: {house_degree:.2f}° | Nakshatra: {nakshatra_name} {pada} | Rasi: {rasi_name}")

    # Join all planetary positions into a single string
    planetary_positions_str = "\n".join(planetary_positions)
    return planetary_positions_str
# ============================================================================
# ARUDHA (PADA) CALCULATION FUNCTIONS
# ============================================================================
def get_divisional_data_package(div_code, positions, retro, combust):
    """Helper to get chart data package for any division"""
    div_num = int(div_code[1:])  # Extract number from "D60" → 60
    
    # Calculate ascendant for this division
    div_asc_deg = get_divisional_position(positions['Asc'], div_num)
    div_asc_sign = int(div_asc_deg // 30)
    
    # Generate chart data
    chart_data = make_chart_data(positions, div_num, div_asc_sign, retro, combust)
    rashi_nums = [(div_asc_sign + i) % 12 + 1 for i in range(12)]
    title = DIVISION_NAMES.get(div_num, f"Division {div_code}")
    
    return (chart_data, rashi_nums, title)
def get_arudha_meta(degree, arudha_name):
    """
    Generate metadata for Arudha position similar to upagraha format.
    """
    rasi = int(degree // 30)    
    nakshatra_index = int(degree // 13.3333)
    nakshatra_pos = degree % 13.3333
    pada = int(nakshatra_pos // 3.3333) + 1   
    return {
        "name": arudha_name,
        "degree": round(degree % 30, 2),
        "full_degree": degree,
        "rasi": rasi_names[rasi],
        "nakshatra": nakshatras[nakshatra_index],
        "pada": pada
    }
def calculate_arudha_positions(positions, rashi_numbers):
    """
    Calculate all 12 Arudha Padas (A1-A12) based on planetary positions.
    
    Args:
        positions: Dictionary of planet longitudes
        rashi_numbers: List of 12 rashi numbers for houses 0-11
    
    Returns:
        Dictionary with A1-A12 as keys, each containing degree, rashi, nakshatra, pada
    """
    
    # Map house numbers (0-11) to their rashi signs (0-11)
    # rashi_numbers contains the sign number (1-12) for each house
    house_to_rashi = {i: (rashi_numbers[i] - 1) % 12 for i in range(12)}
    
    # Map rashi to its lord
    arudhas = {}
    
    for house_num in range(1, 13):  # Houses 1-12
        # Get the rashi of this house (0-11)
        house_rashi = house_to_rashi[house_num - 1]
        
        # Find the lord of this rashi
        lord_planet = RASHI_LORDS[house_rashi]
        
        # Get lord's position in degrees
        if lord_planet not in positions:
            continue
            
        lord_degree = positions[lord_planet]
        lord_rashi = int(lord_degree // 30)  # 0-11
        
        # Calculate distance from house rashi to lord's rashi
        distance = (lord_rashi - house_rashi) % 12
        
        # Apply Satya Jataka exception: if distance is 0 or 6, use 10th from lord
        if distance == 0 or distance == 6:
            arudha_rashi = (lord_rashi + 9) % 12  # 10th from lord (0-indexed: +9)
        else:
            arudha_rashi = (lord_rashi + distance) % 12
        
        # Calculate degree within the arudha rashi (use same offset as lord)
        degree_in_rashi = lord_degree % 30
        arudha_degree = arudha_rashi * 30 + degree_in_rashi
        
        # Get metadata
        arudha_meta = get_arudha_meta(arudha_degree, ARUDHA_NAMES[house_num])
        arudhas[ARUDHA_NAMES[house_num]] = arudha_meta
    
    return arudhas
# ---------------- YOGINI DASHA ---------------- #
def calculate_yogini_dasha(jd, moon_lon):
    """
    Calculate Yogini Dasha tree based on Moon longitude.
    Returns list of dicts similar to Vimshottari format.
    """

    dashas = []

    moon_lon = moon_lon % 360

    # 1. Nakshatra Index
    nak_index = min(int(moon_lon / NAKSHATRA_SPAN), 26)

    # 2. Degrees inside Nakshatra
    nak_start_deg = nak_index * NAKSHATRA_SPAN
    deg_in_nak = moon_lon - nak_start_deg
    if deg_in_nak < 0:
        deg_in_nak += 360

    # 3. Starting Yogini Index
    start_yogini_index = (nak_index + 3) % 8

    # 4. Balance of First Dasha
    remaining_deg = NAKSHATRA_SPAN - deg_in_nak
    balance_ratio = remaining_deg / NAKSHATRA_SPAN

    current_jd = jd

    # ---- FIRST DASHAS WITH BALANCE ---- #
    for i in range(8):
        yog_index = (start_yogini_index + i) % 8
        yog_name = YOGINI_NAMES[yog_index]
        yog_years = YOGINI_YEARS[yog_index]

        # First dasha uses balance ratio
        if i == 0:
            yog_years = yog_years * balance_ratio

        duration_days = yog_years * 365.25
        end_jd = current_jd + duration_days

        dashas.append({
            "planet": yog_name,
            "start_jd": current_jd,
            "end_jd": end_jd,
            "duration_days": duration_days
        })

        current_jd = end_jd

    return dashas
