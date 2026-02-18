from utils import (swe, get_ayanamsa, planet_speeds, PLANETS, 
                   get_divisional_position, convert_to_dms,
                   get_lahiri, get_kp_old, get_true_lahiri, get_kp_new,
                   EPHE_PATH)
import re
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun
import astropy.units as u
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import sys
import os
from varr import (TITHI_NAMES, YOGA_NAMES, KARANA_NAMES,YONI_MAP, NADI_MAP, 
                  VEDIC_WEEKDAYS, NAAM_AKSHAR_MAP,NAKSHATRA_NAMES, GANA_MAP,
                  fixed_karanas,PADA_SPAN,month_names, RASI_NAMES,
                  rasi_names, nakshatras)
from BS_DATABASE import gregorian_to_bs

# Import PyQt6 modules
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

def check_planet_rasi_changes(jd_start, lat, lon, days=365, ayanamsa_type="Lahiri"):
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    result = {}
    rahu_change_date = None

    # 1. Find Rahu's change date
    name_rahu = "रा"
    pid_rahu = swe.MEAN_NODE
    jd = jd_start
    pos_rahu_start = swe.calc_ut(jd, pid_rahu, flags)[0][0]
    sidereal_pos_rahu_start = (pos_rahu_start - get_ayanamsa(jd, ayanamsa_type)) % 360
    last_rasi_rahu = int(sidereal_pos_rahu_start // 30)

    for delta in range(1, days + 1):
        jd_next = jd_start + delta
        pos_rahu_next = swe.calc_ut(jd_next, pid_rahu, flags)[0][0]
        sidereal_pos_rahu_next = (pos_rahu_next - get_ayanamsa(jd_next, ayanamsa_type)) % 360
        new_rasi_rahu = int(sidereal_pos_rahu_next // 30)

        if new_rasi_rahu != last_rasi_rahu:
            jd_low = jd_next - 1
            jd_high = jd_next
            for _ in range(30):
                jd_mid = (jd_low + jd_high) / 2
                pos_rahu_mid = swe.calc_ut(jd_mid, pid_rahu, flags)[0][0]
                sidereal_pos_rahu_mid = (pos_rahu_mid - get_ayanamsa(jd_mid, ayanamsa_type)) % 360
                mid_rasi_rahu = int(sidereal_pos_rahu_mid // 30)
                if mid_rasi_rahu == last_rasi_rahu:
                    jd_low = jd_mid
                else:
                    jd_high = jd_mid
                if jd_high - jd_low < 1e-9:
                    break
            rahu_change_jd = jd_high
            t_rahu = Time(rahu_change_jd, format='jd', scale='utc')
            rahu_change_date_str = t_rahu.datetime.strftime("%d-%m-%Y")
            rahu_new_rasi = new_rasi_rahu + 1

            result[name_rahu] = {
                "new_rasi": rahu_new_rasi,
                "change_date": rahu_change_date_str
            }
            rahu_change_date = rahu_change_jd
            break

    # 2. Calculate Ketu's change based on Rahu's change date
    name_ketu = "के"
    if rahu_change_date is not None:
        jd_ketu_change = rahu_change_date
        pos_rahu_at_change = swe.calc_ut(jd_ketu_change, swe.MEAN_NODE, flags)[0][0]
        pos_ketu_at_change = (pos_rahu_at_change + 180) % 360
        sidereal_pos_ketu_at_change = (pos_ketu_at_change - get_ayanamsa(jd_ketu_change, ayanamsa_type)) % 360
        ketu_new_rasi = int(sidereal_pos_ketu_at_change // 30) + 1

        t_ketu = Time(jd_ketu_change, format='jd', scale='utc')
        ketu_change_date_str = t_ketu.datetime.strftime("%d-%m-%Y")

        result[name_ketu] = {
            "new_rasi": ketu_new_rasi,
            "change_date": ketu_change_date_str
        }

    # 3. Calculate rasi changes for other planets
    for name, pid in PLANETS.items():
        if name not in ["रा", "के"]:
            jd = jd_start
            pos = swe.calc_ut(jd, pid, flags)[0][0]
            sidereal_pos = (pos - get_ayanamsa(jd, ayanamsa_type)) % 360
            last_rasi = int(sidereal_pos // 30)

            for delta in range(1, days + 1):
                jd_next = jd_start + delta
                pos = swe.calc_ut(jd_next, pid, flags)[0][0]
                sidereal_pos = (pos - get_ayanamsa(jd_next, ayanamsa_type)) % 360
                new_rasi = int(sidereal_pos // 30)

                if new_rasi != last_rasi:
                    jd_low = jd_next - 1
                    jd_high = jd_next
                    for _ in range(30):
                        jd_mid = (jd_low + jd_high) / 2
                        pos_mid = swe.calc_ut(jd_mid, pid, flags)[0][0]
                        sidereal_pos_mid = (pos_mid - get_ayanamsa(jd_mid, ayanamsa_type)) % 360
                        mid_rasi = int(sidereal_pos_mid // 30)
                        if mid_rasi == last_rasi:
                            jd_low = jd_mid
                        else:
                            jd_high = jd_mid
                        if jd_high - jd_low < 1e-9:
                            break
                    t = Time(jd_high, format='jd', scale='utc')
                    change_date = t.datetime.strftime("%d-%m-%Y")
                    result[name] = {
                        "new_rasi": new_rasi + 1,
                        "change_date": change_date
                    }
                    break
    return result

def calculate_gochar(lat, lon, jd):
    positions = {}
    retro_flags = {}
    combust_flags = {}
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED

    house_result = swe.houses_ex(jd, lat, lon, b'W', swe.FLG_SWIEPH)
    ascendant_degree_tropical = house_result[1][0]
    ayanamsa = get_ayanamsa(jd)
    positions['Asc'] = (ascendant_degree_tropical - ayanamsa) % 360

    for name, pid in PLANETS.items():
        if name == "के":
            rahu_pos = positions.get("रा")
            if rahu_pos is None: continue
            positions["के"] = (rahu_pos + 180) % 360
            planet_speeds["के"] = -1.0
            retro_flags["के"] = False
            continue

        pos_array, _ = swe.calc_ut(jd, pid, flags)
        pos, speed = pos_array[0], pos_array[3]
        positions[name] = (pos - ayanamsa) % 360
        planet_speeds[name] = speed
        retro_flags[name] = speed < 0 if name != "रा" else False

    sun_pos = positions.get("सु")
    moon_pos = positions.get("चं")
    
    if None not in (sun_pos, moon_pos):
        sun_long = swe.calc_ut(jd, swe.SUN)[0][0]
        moon_long = swe.calc_ut(jd, swe.MOON)[0][0]
        phase_angle = (moon_long - sun_long) % 360
        
        phases = [
            (10, "New Moon"), (75, "Waxing Crescent"), (105, "First Quarter"),
            (165, "Waxing Gibbous"), (195, "Full Moon"), (255, "Waning Gibbous"),
            (285, "Third Quarter")
        ]
        moon_phase = "Waning Crescent"
        for angle, name in phases:
            if phase_angle < angle:
                moon_phase = name
                break
    else:
        moon_phase = "Unknown"

    return positions, retro_flags, combust_flags, moon_phase

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def get_moon_phase_pixmap(moon_phase, size=(100, 100)):
    """
    Returns a QPixmap for the given moon phase using PyQt6.
    """
    paths = {
        "New Moon": "moon/new-moon.png",
        "Waxing Crescent": "moon/waxing-crescent.png",
        "First Quarter": "moon/first-quarter.png",
        "Waxing Gibbous": "moon/waxing-gibbous.png",
        "Full Moon": "moon/full.png",
        "Waning Gibbous": "moon/waning-gibbous.png",
        "Third Quarter": "moon/third-quarter.png",
        "Waning Crescent": "moon/waning-crescent.png"
    }
    
    image_name = paths.get(moon_phase, "moon/default.png")
    full_path = os.path.join(get_base_path(), image_name)
    
    if not os.path.exists(full_path):
        full_path = os.path.join(get_base_path(), "moon/default.png")

    pixmap = QPixmap(full_path)
    if not pixmap.isNull():
        # PyQt6 uses AspectRatioMode and TransformationMode enums
        return pixmap.scaled(
            size[0], 
            size[1], 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
    return None
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
def is_combust_now(planet_pid, ayanamsa_type,jd):
    flags = swe.FLG_SWIEPH
    ayan = get_ayanamsa(jd, ayanamsa_type)

    sun_lon = swe.calc_ut(jd, swe.SUN, flags)[0][0]
    planet_lon = swe.calc_ut(jd, planet_pid, flags)[0][0]

    sun_sid = (sun_lon - ayan) % 360
    planet_sid = (planet_lon - ayan) % 360

    diff = abs(planet_sid - sun_sid)
    dist = min(diff, 360 - diff)

    orb = {swe.MERCURY:10, swe.VENUS:8}.get(planet_pid, 6)
    return dist < orb

