from datetime import datetime, timedelta, date
import pytz
import swisseph as swe
import traceback
import ephem
from Vishmottari_Dasha import generate_dasha_tree, jd_to_date_str
from strength import show_strength_tables
import os
from math import cos, sin, radians
from collections import defaultdict
import math
from BS_DATABASE import gregorian_to_bs, bs_to_gregorian
from datetime import date as greg_date
from panchangyoga import SPECIAL_YOGAS
import sys
from pathlib import Path
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_sun
import astropy.units as u
import numpy as np  # Make sure numpy is imported in your file

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
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error setting ephemeris path: {e}")
        sys.exit(1)

# Set ephemeris path and store it globally
EPHE_PATH = set_ephemeris_path()

# --- Font Configuration ---
DEV_FONT_FAMILY = "Mangal"  # Primary choice
FALLBACK_FONTS = ["Noto Sans Devanagari", "Mangal", "Nirmala UI", "Arial"]  # Fallback options
DEV_FONT_SIZE = 10
devanagari_font_tuple = (DEV_FONT_FAMILY, DEV_FONT_SIZE)

planet_map_en_to_dev = {
    'Jupiter': 'Ju',
    'Saturn': 'Sa',
    'Mercury': 'Me',
    'Ketu': 'Ke',
    'Venus': 'Ve',
    'Sun': 'Su',
    'Moon': 'Mo',
    'Mars': 'Ma',
    'Rahu': 'Ra',
    'गु': 'Ju',
    'श': 'Sa',
    'बु': 'Me',
    'के': 'Ke',
    'शु': 'Ve',
    'सू': 'Su',
    'चं': 'Mo',
    'मं': 'Ma',
    'रा': 'Ra',
    'Ju': 'Ju',
    'Sa': 'Sa',
    'Me': 'Me',
    'Ke': 'Ke',
    'Ve': 'Ve',
    'Su': 'Su',
    'Mo': 'Mo',
    'Ma': 'Ma',
    'Ra': 'Ra'
}

# Global variables for chart data
planet_speeds = {} 
positions = {}
rashi_numbers = []
retro_flags = {}
combust_flags = {}
chart_cache = {}
LAT = 26.7372
LON = 87.1640
TZ_NAME = "Asia/Kathmandu"
LOCAL_TZ = pytz.timezone(TZ_NAME)
RASI_TO_ZODIAC = {
    0: "मेष", 1: "बृष", 2: "मिथुन", 3: "कर्क",
    4: "सिंह", 5: "कन्या", 6: "तुला", 7: "बृश्चिक",
    8: "धनु", 9: "मकर", 10: "कुम्भ", 11: "मिन"
}

# Define Planets
PLANETS = {
    "सु": swe.SUN,
    "चं": swe.MOON,
    "मं": swe.MARS,
    "बु": swe.MERCURY,
    "गु": swe.JUPITER,
    "शु": swe.VENUS,
    "श": swe.SATURN,
    "रा": swe.TRUE_NODE,
    "के": swe.TRUE_NODE,  # calculated later
    "ल": swe.MEAN_APOG
}

# Define Panchang Names
RASI_NAMES = [
    "मेष", "बृष", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "बृश्चिक", "धनु", "मकर", "कुम्भ", "मिन"
]
nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyestha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
        "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

# Mapping English weekdays to Vedic weekdays for SPECIAL_YOGAS
ENGLISH_TO_VEDIC_WEEKDAY = {
    "Sunday": "आइतबार",
    "Monday": "सोमबार",
    "Tuesday": "मंगरबार",
    "Wednesday": "बुधबार",
    "Thursday": "बिहिबार",
    "Friday": "शुक्रबार",
    "Saturday": "शनिबार"
}

def get_lahiri(jd):
    """
    Authentic Lahiri (Chitra Paksha) Ayanamsa Calculation (Linear Approximation)
    - Verified against official Indian Ephemeris values near J2000.
    - Base value at J2000 epoch (2000-01-01 12:00 UTC): 23°51'23" = 23.8563888...°
    - Precession rate: 50.2564 arcsec/year (official linear rate).

    Note: Highly precise calculations may include quadratic or higher-order terms.
    This function uses the linear term as provided.

    Args:
        jd (float): The Julian Date for which to calculate the ayanamsa.

    Returns:
        float: The Lahiri ayanamsa in degrees (0 to < 360), rounded to 6 decimal places.
    """
    JD_J2000 = 2451545.0  # J2000 epoch (2000-01-01 12:00 UTC)

    # Base value at J2000 in degrees
    BASE_J2000_DEG = 23.85638888888889

    # Precession rate in arcsec/year
    RATE_ARCSEC_PER_YEAR = 50.2564

    # Conversion factor from arcseconds to degrees
    DEG_PER_ARCSEC = 1.0 / 3600.0

    # Julian centuries since J2000
    t_centuries = (jd - JD_J2000) / 36525.0

    # Calculate total precession since J2000 in degrees (linear term only)
    precession_deg = RATE_ARCSEC_PER_YEAR * (t_centuries * 100.0) * DEG_PER_ARCSEC

    # Total ayanamsa = Base value at J2000 + total precession since J2000
    ayanamsa_deg = BASE_J2000_DEG + precession_deg

    # Ensure the result is within 0 to < 360 degrees
    ayanamsa_deg_wrapped = ayanamsa_deg % 360.0

    # Handle potential negative results from modulo for negative input
    if ayanamsa_deg_wrapped < 0:
        ayanamsa_deg_wrapped += 360.0

    return round(ayanamsa_deg_wrapped, 6)

def calculate_upagrahas(lmt_chart):
    """
    Calculate nine Upagrahas based on the chart data.
    Requires datetime, sunrise/sunset times, planet_positions (with Sun), lat, lon, tz_name.
    Returns dict with Upagraha details including 'का' (Kala).
    """
    def get_lagna_degree(dt_local):
        """
        Calculate ascendant (lagna) degree for a given local datetime.
        Requires lat, lon, and tz_name from lmt_chart.
        """
        local_tz = pytz.timezone(lmt_chart["tz_name"])
        local_dt = dt_local if dt_local.tzinfo else local_tz.localize(dt_local)
        utc_dt = local_dt.astimezone(pytz.utc)

        jd = swe.julday(
            utc_dt.year, utc_dt.month, utc_dt.day,
            utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0 + utc_dt.microsecond / 3600000000.0
        )

        ayanamsa = get_lahiri(jd)
        swe.set_sid_mode(swe.SIDM_LAHIRI, ayanamsa, 0)

        house_result = swe.houses_ex(jd, lmt_chart["lat"], lmt_chart["lon"], b'W', flags=swe.FLG_SIDEREAL)
        ascendant_degree_tropical = house_result[1][0]
        ascendant_degree_sidereal = (ascendant_degree_tropical - ayanamsa) % 360
        return ascendant_degree_sidereal

    birth_dt = lmt_chart["datetime"]
    date_only = birth_dt.date()

    sunrise_dt = lmt_chart.get("sunrise_dt")
    sunset_dt = lmt_chart.get("sunset_dt")

    if not isinstance(sunrise_dt, datetime) or not isinstance(sunset_dt, datetime):
        raise ValueError("sunrise_dt and sunset_dt must be provided as datetime objects in lmt_chart")

    local_tz = pytz.timezone(lmt_chart["tz_name"])
    is_day = (sunrise_dt <= birth_dt < sunset_dt)
    day_duration = (sunset_dt - sunrise_dt).total_seconds()
    night_duration = (sunrise_dt + timedelta(days=1) - sunset_dt).total_seconds()

    day_ghatika = {6: 26, 0: 22, 1: 18, 2: 14, 3: 10, 4: 6, 5: 2}
    night_ghatika = {6: 10, 0: 6, 1: 2, 2: 26, 3: 22, 4: 18, 5: 14}
    Kala_day = {6: 2, 0: 30, 1: 26, 2: 22, 3: 18, 4: 14, 5: 10}
    Kala_night = {6: 14, 0: 10, 1: 6, 2: 2, 3: 30, 4: 26, 5: 22}
    Yama_day = {6: 18, 0: 14, 1: 10, 2: 6, 3: 2, 4: 30, 5: 26}
    Yama_night = {6: 2, 0: 30, 1: 26, 2: 22, 3: 18, 4: 14, 5: 10}
    Mrtyu_day = {6: 10, 0: 6, 1: 2, 2: 30, 3: 26, 4: 22, 5: 18}
    Mrtyu_night = {6: 22, 0: 18, 1: 14, 2: 10, 3: 6, 4: 2, 5: 30}
    ardhaprahara_day = {0: 10, 1: 6, 2: 2, 3: 30, 4: 26, 5: 22, 6: 18}
    ardhaprahara_night = {0: 22, 1: 18, 2: 14, 3: 10, 4: 6, 5: 2, 6: 30}

    wd = birth_dt.weekday()
    gulika_dt = None
    if is_day:
        gh = day_ghatika.get(wd, None)
        if gh is not None:
            gulika_dt = sunrise_dt + timedelta(minutes=gh * 24)
    else:
        gh = night_ghatika.get(wd, None)
        if gh is not None:
            next_sunrise_dt = calculate_sunrise_sunset(date_only + timedelta(days=1), lmt_chart["lat"], lmt_chart["lon"], lmt_chart["tz_name"])[0]
            if next_sunrise_dt:
                gulika_dt = sunset_dt + timedelta(minutes=gh * 24)

    gulika_deg = get_lagna_degree(gulika_dt) if gulika_dt else 0.0

    kala_dt = None
    if is_day:
        val = Kala_day.get(wd, None)
        if val is not None and day_duration > 0:
            kala_dt = sunrise_dt + timedelta(seconds=day_duration * val / 32.0)
    else:
        val = Kala_night.get(wd, None)
        if val is not None and day_duration > 0:
            kala_dt = sunset_dt + timedelta(seconds=day_duration * val / 32.0)
    kala_deg = get_lagna_degree(kala_dt) if kala_dt else 0.0

    yama_dt = None
    if is_day:
        val = Yama_day.get(wd, None)
        if val is not None and day_duration > 0:
            yama_dt = sunrise_dt + timedelta(seconds=day_duration * val / 32.0)
    else:
        val = Yama_night.get(wd, None)
        if val is not None and day_duration > 0:
            yama_dt = sunset_dt + timedelta(seconds=day_duration * val / 32.0)
    yama_deg = get_lagna_degree(yama_dt) if yama_dt else 0.0

    mrtyu_dt = None
    if is_day:
        val = Mrtyu_day.get(wd, None)
        if val is not None and day_duration > 0:
            mrtyu_dt = sunrise_dt + timedelta(seconds=day_duration * val / 32.0)
    else:
        val = Mrtyu_night.get(wd, None)
        if val is not None and day_duration > 0:
            mrtyu_dt = sunset_dt + timedelta(seconds=day_duration * val / 32.0)
    mrtyu_deg = get_lagna_degree(mrtyu_dt) if mrtyu_dt else 0.0

    wd_ardha = (wd + 1) % 7
    ardhaprahara_dt = None
    if is_day:
        gh = ardhaprahara_day.get(wd_ardha, None)
        if gh is not None:
            ardhaprahara_dt = sunrise_dt + timedelta(minutes=gh * 24)
    else:
        gh = ardhaprahara_night.get(wd_ardha, None)
        if gh is not None:
            ardhaprahara_dt = sunset_dt + timedelta(minutes=gh * 24)
    ardhaprahara_deg = get_lagna_degree(ardhaprahara_dt) if ardhaprahara_dt else 0.0

    try:
        sun_keys_to_try = ["सु", "Sun", "SU", "su", "Surya", "सूर्य"]
        sun_deg = None
        for key in sun_keys_to_try:
            if key in lmt_chart["planet_positions"]:
                sun_deg = lmt_chart["planet_positions"][key]
                break
        if sun_deg is None:
            print("⚠️ Sun position not found in planet_positions. Kala and shadow Upagrahas may be inaccurate.")
            return {}
    except KeyError as e:
        print(f"Error getting Sun position for Upagrahas: {e}")
        sun_deg = 0.0
    except Exception as e:
        print(f"An unexpected error occurred getting Sun position: {e}")
        sun_deg = 0.0

    dhuma_deg = (sun_deg + 133 + 20/60.0) % 360
    vyatipata_deg = (360 - dhuma_deg) % 360
    parivesha_deg = (180 + vyatipata_deg) % 360
    indrachapa_deg = (360 - parivesha_deg) % 360
    upaketu_deg = (16 + 40/60.0 + indrachapa_deg) % 360

    upagrahas = {
        "गु": get_lagna_meta(gulika_deg),
        "य": get_lagna_meta(yama_deg),
        "का": get_lagna_meta(kala_deg),
        "मृ": get_lagna_meta(mrtyu_deg),
        "अ": get_lagna_meta(ardhaprahara_deg),
        "धु": get_lagna_meta(dhuma_deg),
        "व्या": get_lagna_meta(vyatipata_deg),
        "प": get_lagna_meta(parivesha_deg),
        "इ": get_lagna_meta(indrachapa_deg),
        "उ": get_lagna_meta(upaketu_deg)
    }
    return upagrahas

# --- Panchang Name Lists ---
TITHI_NAMES = [
    "शुक्ल प्रतिपदा", "शुक्ल द्वितिया", "शुक्ल तृतिया", "शुक्ल चतुर्थी", "शुक्ल पञ्चमि",
    "शुक्ल षष्ठि", "शुक्ल सप्तमी", "शुक्ल अष्ठमी", "शुक्ल नवमी", "शुक्ल दशमी",
    "शुक्ल एकादशी", "शुक्ल द्वादशी", "शुक्ल त्रयोदशी", "शुक्ल चतुर्दशी", "पुर्णीमा",
    "कृष्ण प्रतिपदा", "कृष्ण द्वितिया", "कृष्ण तृतिया", "कृष्ण चतुर्थी", "कृष्ण पञ्चमि",
    "कृष्ण षष्ठि", "कृष्ण सप्तमी", "कृष्ण अष्ठमी", "कृष्ण नवमी", "कृष्ण दशमी",
    "कृष्ण एकादशी", "कृष्ण द्वादशी", "कृष्ण त्रयोदशी", "कृष्ण चतुर्दशी", "अमावस्या"
]

nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyestha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
        "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

YOGA_NAMES = [
    "विषकुम्भ", "प्रिती", "आयुश्मान", "सौभाग्य", "सोभाना", "अतिगन्दा", "शुक्रमान", "धृती", "शुल",
    "गन्दा", "बृद्धी", "ध्रुव", "व्यघटा", "हर्षना", "बज्र", "सिद्दी", "व्यतिपात", "बरियाना",
    "परिघ", "शिव", "सिद्द", "सध्या", "शुभ", "शुक्ल", "ब्रह्मा", "इन्द्र", "बैधृती"
]

KARANA_NAMES = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि", "शकुनि", "चतुष्पद", "नाग", "किंस्तुघ्न"]

weekdays = [
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday"
]

def _calculate_karana(tithi_deg):
    """
    Calculate Karana based on Tithi degrees.
    """
    tithi_deg = tithi_deg % 360
    karana_num = int(tithi_deg / 6)
    
    fixed_karanas = {
        0: "किंस्तुघ्न",
        1: "शकुनि",
        2: "चतुष्पद",
        3: "नाग"
    }
    
    if karana_num in fixed_karanas:
        return fixed_karanas[karana_num]
    else:
        return KARANA_NAMES[(karana_num - 1) % 7]

def get_lagna_meta(degree):
    """
    Generate metadata for a given degree: degree within Rasi, Rasi, Nakshatra, pada.
    """
    degree = degree % 360
    if degree < 0:
        degree += 360

    rasi_index = int(degree // 30)
    degree_in_rasi = degree % 30
    nakshatra_degree_span = 360 / 27
    nakshatra_index = int(degree // nakshatra_degree_span)
    nakshatra_index = min(nakshatra_index, len(nakshatras) - 1)
    nakshatra_pos_in_nakshatra = degree % nakshatra_degree_span
    pada = int(nakshatra_pos_in_nakshatra // (nakshatra_degree_span / 4)) + 1
    pada = max(1, min(4, pada))

    return {
        "degree_in_rasi": round(degree_in_rasi, 2),
        "rasi": RASI_NAMES[rasi_index % 12],
        "nakshatra": nakshatras[nakshatra_index],
        "pada": pada
    }

def calculate_sunrise_sunset(date_obj, lat, lon, local_tz_name):
    """
    Calculate local sunrise and sunset times for a given date and location.
    date_obj is a datetime.date object or string in YYYY/MM/DD format.
    """
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y/%m/%d").date()

    observer = ephem.Observer()
    observer.date = date_obj
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = 0

    local_tz = pytz.timezone(local_tz_name)

    try:
        sunrise_utc = observer.next_rising(ephem.Sun()).datetime()
        sunset_utc = observer.next_setting(ephem.Sun()).datetime()
        sunrise_local = pytz.utc.localize(sunrise_utc).astimezone(local_tz)
        sunset_local = pytz.utc.localize(sunset_utc).astimezone(local_tz)
        return sunrise_local, sunset_local
    except ephem.NeverUpError:
        return None, None
    except ephem.NeverDownError:
        return None, None
    except Exception as e:
        print(f"Error calculating sunrise/sunset: {e}")
        return None, None

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
        greg_date = julian_day_to_gregorian(jd)
        bs_date = gregorian_to_bs(greg_date)
        if not isinstance(bs_date, str):
            return None, None

        bs_year, bs_month, _ = map(int, bs_date.split('-'))
        month_names = [
            "बैशाख", "ज्येष्ठ", "अषाढ", "श्रावण",
            "भाद्र", "अश्विन", "कार्तिक", "मंसिर",
            "पौष", "माघ", "फाल्गुण", "चैत्र"
        ]
        lunar_month_name = month_names[bs_month - 1]
        lunar_year = bs_year
        return lunar_month_name, lunar_year
    except Exception:
        traceback.print_exc()
        return None, None
def get_solar_eclipses_for_year(year, tz_name="Asia/Kathmandu"):
    """
    Returns a list of solar eclipses in the given year, using swisseph or fallback data.
    
    Args:
        year (int): Year to scan for eclipses
        tz_name (str): Timezone name for output formatting
    
    Returns:
        List[str]: List of formatted strings ["YYYY-MM-DD HH:MM:SS, Type", ...]
    """
    result = []
    local_tz = pytz.timezone(tz_name)
    
    # Fallback eclipse data for 2025
    fallback_eclipses = [
        {"jd": 2460764.420833, "date": "2025-03-29", "time": "15:50:00", "type": "Partial"},
        {"jd": 2460940.813889, "date": "2025-09-21", "time": "13:17:00", "type": "Partial"}
    ]
    
    # Try swisseph calculation
    try:
        start_dt = datetime(year, 1, 1, 0, 0, 0, tzinfo=pytz.utc)
        end_dt = datetime(year, 12, 31, 23, 59, 59, tzinfo=pytz.utc)
        jd_start = swe.julday(start_dt.year, start_dt.month, start_dt.day, start_dt.hour)
        jd_end = swe.julday(end_dt.year, end_dt.month, end_dt.day, end_dt.hour + end_dt.minute / 60.0 + end_dt.second / 3600.0)
        
        current_jd = jd_start
        while current_jd <= jd_end:
            try:
                eclipse_result = swe.sol_eclipse_when_glob(current_jd)
                
                if isinstance(eclipse_result, tuple) and len(eclipse_result) >= 2:
                    retflag, eclipse_times = eclipse_result[0], eclipse_result[1]
                    if retflag >= 0 and eclipse_times[0] <= jd_end:
                        eclipse_jd = eclipse_times[0]
                        eclipse_dt_local = ut_julday_to_local_datetime(eclipse_jd)
                        if eclipse_dt_local and eclipse_dt_local.year == year:
                            eclipse_type = {
                                swe.ECL_PARTIAL: "Partial",
                                swe.ECL_ANNULAR: "Annular",
                                swe.ECL_TOTAL: "Total",
                                swe.ECL_ANNULAR_TOTAL: "Annular-Total"
                            }.get(retflag & (swe.ECL_PARTIAL | swe.ECL_ANNULAR | swe.ECL_TOTAL | swe.ECL_ANNULAR_TOTAL), "Unknown")
                            result.append(f"{eclipse_dt_local.strftime('%Y-%m-%d %H:%M:%S')}, {eclipse_type}")
                        current_jd = eclipse_jd + 0.5  # Increment by half a day to avoid duplicates
                    else:
                        break
                else:
                    print(f"Unexpected result format from swe.sol_eclipse_when_glob: {eclipse_result}")
                    break
            except Exception as e:
                print(f"Error in solar eclipse calculation for JD {current_jd}: {str(e)}")
                break
        
        # Validate swisseph results against fallback
        if not result or any("Unknown" in r for r in result):
            print("WARNING: swisseph results invalid or incomplete. Using fallback eclipse data.")
            result = [f"{e['date']} {e['time']}, {e['type']}" for e in fallback_eclipses if e['date'].startswith(str(year))]
    
    except Exception as e:
        print(f"Error in solar eclipse calculation: {str(e)}. Using fallback eclipse data.")
        result = [f"{e['date']} {e['time']}, {e['type']}" for e in fallback_eclipses if e['date'].startswith(str(year))]
    
    return result if result else ["No solar eclipse in current year"]
def validate_inputs(positions: dict) -> None:
    """Validate critical inputs for Panchang calculation."""
    if not positions or 'सु' not in positions or 'चं' not in positions:
        raise ValueError("Missing Sun/Moon positions in input data")

def calculate_core_panchang(sun_lon: float, moon_lon: float) -> dict:
    """Calculate core Panchang elements: Tithi, Nakshatra, Yoga, Karana."""
    results = {}
    try:
        tithi_deg = (moon_lon - sun_lon) % 360
        nakshatra_index = int((moon_lon * 60) / 800) % len(nakshatras)
        results.update({
            'tithi': TITHI_NAMES[min(int(tithi_deg / 12), len(TITHI_NAMES) - 1)],
            'nakshatra': nakshatras[nakshatra_index],
            'yoga': YOGA_NAMES[int((sun_lon + moon_lon) % 360 / (800 / 60)) % len(YOGA_NAMES)],
            'karana': _calculate_karana(tithi_deg)
        })
        return results
    except Exception as e:
        results.update({
            'tithi': f"Error: {str(e)}",
            'nakshatra': f"Error: {str(e)}",
            'yoga': f"Error: {str(e)}",
            'karana': f"Error: {str(e)}"
        })
        return results

def calculate_weekday(jd: float, local_tz_name: str) -> dict:
    """Calculate Vedic weekday from Julian Day."""
    results = {}
    try:
        local_tz = pytz.timezone(local_tz_name)
        year, month, day, hour = swe.revjul(jd)
        utc_dt = datetime(year, month, day, int(hour), int((hour % 1) * 60))
        local_dt = local_tz.localize(utc_dt) if utc_dt.tzinfo is None else utc_dt.astimezone(local_tz)

        weekday_en = weekdays[(local_dt.weekday() + 1) % 7]
        weekday_vedic = ENGLISH_TO_VEDIC_WEEKDAY.get(weekday_en, weekday_en)
        results['weekday'] = weekday_vedic
        return results
    except Exception as e:
        results['weekday'] = f"Weekday Error: {str(e)}"
        return results


def calculate_special_yoga(nakshatra: str, weekday_vedic: str) -> dict:
    """
    Calculate special yogas based on Nakshatra and Vedic weekday.
    Returns a dict with 'special_yoga': list or error message.
    """
    try:
        special_yogas = []
        for yoga_name, yoga_combinations in SPECIAL_YOGAS.items():
            for nak, eng_weekday in yoga_combinations:
                vedic_day = ENGLISH_TO_VEDIC_WEEKDAY.get(eng_weekday)
                if nak == nakshatra and vedic_day == weekday_vedic:
                    special_yogas.append(yoga_name)
        return {'special_yoga': special_yogas if special_yogas else ["None"]}
    except Exception as e:
        return {'special_yoga': f"Special Yoga Error: {str(e)}"}
def calculate_sunrise_sunset_for_panchang_XXX(date_obj, lat, lon, local_tz_name):
    """
    Calculate local sunrise and sunset times for a given date and location.
    date_obj is a datetime.date object or string in YYYY/MM/DD format.
    """
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y/%m/%d").date()

    observer = ephem.Observer()
    observer.date = date_obj
    observer.lat = str(lat)
    observer.lon = str(lon)
    observer.elevation = 0

    local_tz = pytz.timezone(local_tz_name)


    try:
        sunrise_utc = observer.next_rising(ephem.Sun()).datetime()
        sunset_utc = observer.next_setting(ephem.Sun()).datetime()

        sunrise_local = pytz.utc.localize(sunrise_utc).astimezone(local_tz)
        sunset_local = pytz.utc.localize(sunset_utc).astimezone(local_tz)
        sunset_local = pytz.utc.localize(sunset_utc).astimezone(local_tz)
        return sunrise_local, sunset_local

    except ephem.NeverUpError:
        return None, None
    except ephem.NeverDownError:
        return None, None
    except Exception as e:
        traceback.print_exc()
        return None, None
def calculate_sunrise_sunset_for_panchang(date_obj, lat, lon, local_tz_name):
    """
    Calculate local sunrise and sunset times for Panchang using astropy.
    Returns datetime objects.
    """
    try:
        from datetime import datetime  # Explicitly import datetime here
        observer_location = EarthLocation(lat=lat * u.deg, lon=lon * u.deg)
        local_tz = pytz.timezone(local_tz_name)

        # Create an Astropy Time object for the given date (at midnight UTC)
        utc_midnight = datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0)
        utc_midnight_time = Time(utc_midnight, format='datetime', scale='utc')

        # Calculate Sun's position at each hour of the day
        times = utc_midnight_time + np.linspace(0, 24, 1000) * u.hour  # More points for accuracy
        altaz = get_sun(times).transform_to(AltAz(obstime=times, location=observer_location))

        # Find sunrise (altitude goes from below 0 to above 0)
        sunrise_idx = np.where((altaz.alt.value[:-1] < 0) & (altaz.alt.value[1:] >= 0))[0]
        if sunrise_idx.size > 0:
            sunrise_time = times[sunrise_idx[0]]
            sunrise_dt_utc = sunrise_time.to_datetime(timezone=pytz.utc)
            sunrise_local = sunrise_dt_utc.astimezone(local_tz)
        else:
            sunrise_local = None

        # Find sunset (altitude goes from above 0 to below 0)
        sunset_idx = np.where((altaz.alt.value[:-1] >= 0) & (altaz.alt.value[1:] < 0))[0]
        if sunset_idx.size > 0:
            sunset_time = times[sunset_idx[-1]]  # Use the *last* crossing
            sunset_dt_utc = sunset_time.to_datetime(timezone=pytz.utc)
            sunset_local = sunset_dt_utc.astimezone(local_tz)
        else:
            sunset_local = None

        return sunrise_local, sunset_local

    except Exception as e:
        print(f"Error in sunrise/sunset calc for panchang (astropy): {e}")
        traceback.print_exc()
        return None

def calculate_lunar_month_year_data(jd: float) -> dict:
    """Calculate lunar month and year."""
    results = {}
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
        return results
    except Exception as e:
        traceback.print_exc()
        results.update({
            'lunar_month': f"Error: {str(e)}",
            'lunar_year': f"Error: {str(e)}"
        })
        return results

def calculate_lunar_eclipses(jd: float, local_tz_name: str) -> dict:
    """Detect lunar eclipses for the current year, filtering for future events."""
    results = {}
    try:
        year, _, _, _ = swe.revjul(jd)
        local_tz = pytz.timezone(local_tz_name)
        year_start_dt = local_tz.localize(datetime(year, 1, 1, 0, 0, 0))
        jd_start = swe.julday(year_start_dt.year, year_start_dt.month, year_start_dt.day,
                              year_start_dt.hour + year_start_dt.minute / 60.0)
        year_end_dt = local_tz.localize(datetime(year, 12, 31, 23, 59, 59))
        jd_end = swe.julday(year_end_dt.year, year_end_dt.month, year_end_dt.day,
                            year_end_dt.hour + year_end_dt.minute / 60.0 + year_end_dt.second / 3600.0)
        
        eclipse_dates = []
        current_jd = jd_start
        while current_jd <= jd_end:
            try:
                eclipse_result = swe.lun_eclipse_when(current_jd, swe.FLG_MOSEPH)
                if isinstance(eclipse_result, tuple) and len(eclipse_result) >= 2:
                    retflag, eclipse_time = eclipse_result[0], eclipse_result[1]
                    if retflag >= 0 and eclipse_time[0] <= jd_end:
                        eclipse_jd = eclipse_time[0]
                        eclipse_dt_local = ut_julday_to_local_datetime(eclipse_jd)
                        if eclipse_dt_local and eclipse_dt_local.year == year:
                            eclipse_dates.append(eclipse_dt_local.strftime("%Y-%m-%d %H:%M:%S"))
                        current_jd = eclipse_time[0] + 0.1  # Small increment to avoid re-detection
                    else:
                        break
                else:
                    break
            except Exception as e:
                current_jd += 1.0  # Skip to next day
        
        # Filter out past lunar eclipses
        now_local = datetime.now(local_tz)
        future_lunar_eclipses = []
        for eclipse_str in eclipse_dates:
            try:
                eclipse_dt = local_tz.localize(datetime.strptime(eclipse_str, "%Y-%m-%d %H:%M:%S"))
                if eclipse_dt >= now_local:
                    future_lunar_eclipses.append(eclipse_str)
            except ValueError as e:
                print(f"Could not parse lunar eclipse date string '{eclipse_str}': {e}")
        
        results['chandra_grahan'] = future_lunar_eclipses if future_lunar_eclipses else ["No future lunar eclipse in current year"]
        return results
    except pytz.exceptions.UnknownTimeZoneError:
        results['chandra_grahan'] = f"Error: Invalid timezone {local_tz_name}"
        return results
    except Exception as e:
        traceback.print_exc()
        results['chandra_grahan'] = f"Error: {str(e)}"
        return results

def calculate_solar_eclipses(jd: float, local_tz_name: str) -> dict:
    """Compute solar eclipses for the current year, filtering for future events."""
    results = {}
    try:
        year, _, _, _ = swe.revjul(jd)
        local_tz = pytz.timezone(local_tz_name)
        surya_grahan_dates = get_solar_eclipses_for_year(year, local_tz_name)
        
        # Filter out past solar eclipses
        now_local = datetime.now(local_tz)
        future_surya_grahan = []
        for eclipse_str in surya_grahan_dates:
            dt_part = eclipse_str.split(',')[0].strip()
            try:
                eclipse_dt = local_tz.localize(datetime.strptime(dt_part, "%Y-%m-%d %H:%M:%S"))
                if eclipse_dt >= now_local:
                    future_surya_grahan.append(eclipse_str)
            except ValueError as e:
                print(f"Could not parse solar eclipse date string '{dt_part}': {e}")
        
        results['surya_grahan'] = future_surya_grahan if future_surya_grahan else ["No future solar eclipse in current year"]
        return results
    except pytz.exceptions.UnknownTimeZoneError:
        results['surya_grahan'] = f"Error: Invalid timezone {local_tz_name}"
        return results
    except Exception as e:
        traceback.print_exc()
        results['surya_grahan'] = f"Error: {str(e)}"
        return results

def calculate_panchang(jd: float, lat: float, lon: float, local_tz_name: str, positions: dict) -> dict:
    """Calculate Vedic Panchang elements for a given Julian Day and location."""
    results = {}
    try:
        # Validate inputs
        validate_inputs(positions)

        # Calculate core Panchang elements
        sun_lon = positions['सु'] % 360
        moon_lon = positions['चं'] % 360
        results.update(calculate_core_panchang(sun_lon, moon_lon))

        # Calculate weekday
        results.update(calculate_weekday(jd, local_tz_name))

        # Calculate special yoga
        if 'nakshatra' in results and 'weekday' in results and not results['nakshatra'].startswith("Error") and not results['weekday'].startswith("Error"):
            results.update(calculate_special_yoga(results['nakshatra'], results['weekday']))

        # Calculate sunrise and sunset using the new function
        year, month, day, _ = swe.revjul(jd)
        date_obj = datetime(int(year), int(month), int(day)).date()
        sunrise_local, sunset_local = calculate_sunrise_sunset_for_panchang(date_obj, lat, lon, local_tz_name)
        if sunrise_local and sunset_local:
            results.update({
                'sunrise': sunrise_local.strftime("%H:%M:%S"),
                'sunset': sunset_local.strftime("%H:%M:%S")
            })
        else:
            results['sunrise'] = "Error"
            results['sunset'] = "Error"

        # Calculate lunar month and year
        results.update(calculate_lunar_month_year_data(jd))

        # Calculate lunar and solar eclipses
        results.update(calculate_lunar_eclipses(jd, local_tz_name))
        results.update(calculate_solar_eclipses(jd, local_tz_name))

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
                    'NAKSHATRA_NAMES': len(nakshatras),
                    'YOGA_NAMES': len(YOGA_NAMES),
                    'KARANA_NAMES': len(KARANA_NAMES),
                    'VEDIC_WEEKDAYS': len(weekdays)
                }
            }
        }

def calculate_gochar(lat, lon, jd):
    positions = {}
    retro_flags = {}
    combust_flags = {}
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED

    house_result = swe.houses_ex(jd, lat, lon, b'W', swe.FLG_SWIEPH)
    ascendant_degree_tropical = house_result[1][0]
    ayanamsa = get_lahiri(jd)
    ascendant_degree_sidereal = (ascendant_degree_tropical - ayanamsa) % 360
    positions['Asc'] = ascendant_degree_sidereal

    for name, pid in PLANETS.items():
        if name == "के":
            rahu_pos = positions.get("रा")
            if rahu_pos is None:
                raise RuntimeError("❌ Rahu must be calculated before Ketu.")
            ketu_pos = (rahu_pos + 180) % 360
            positions["के"] = ketu_pos
            planet_speeds["के"] = -1.0
            retro_flags["के"] = False
            continue

        pos_array, used_flags = swe.calc_ut(jd, pid, flags)
        if not (used_flags & swe.FLG_SWIEPH):
            raise RuntimeError(f"❌ Swiss Ephemeris fallback for {name}!")

        pos = pos_array[0]
        speed = pos_array[3]
        sidereal_pos = (pos - ayanamsa) % 360

        positions[name] = sidereal_pos
        planet_speeds[name] = speed
        retro_flags[name] = speed < 0 if name != "रा" else False

    moon_pos = positions.get("चं", None)
    sun_pos = positions.get("सु", None)
    if moon_pos is None or sun_pos is None:
        moon_phase = "Unknown"
    else:
        sun_long = swe.calc_ut(jd, swe.SUN)[0][0]
        moon_long = swe.calc_ut(jd, swe.MOON)[0][0]
        phase_angle = (moon_long - sun_long) % 360
        if phase_angle < 10:
            moon_phase = "New Moon"
        elif 10 <= phase_angle < 75:
            moon_phase = "Waxing Crescent"
        elif 75 <= phase_angle < 105:
            moon_phase = "First Quarter"
        elif 105 <= phase_angle < 165:
            moon_phase = "Waxing Gibbous"
        elif 165 <= phase_angle < 195:
            moon_phase = "Full Moon"
        elif 195 <= phase_angle < 255:
            moon_phase = "Waning Gibbous"
        elif 255 <= phase_angle < 285:
            moon_phase = "Third Quarter"
        else:
            moon_phase = "Waning Crescent"

    return positions, retro_flags, combust_flags, moon_phase

FESTIVAL_CONFIG = {
    "Dashami": {
        "target_tithi": 10,
        "paksha": "शुक्ल",
        "nepali_month": "आश्विन"
    },
    "Bhaitika": {
        "target_tithi": 13,
        "paksha": "कृष्ण",
        "nepali_month": "कार्तिक"
    }
}

def ut_julday_to_local_datetime(jd_ut):
    """
    Convert UT Julian Day to local datetime using J2000 epoch.
    """
    try:
        JD_J2000 = 2451545.0  # Julian Day for 2000-01-01 12:00:00 UTC
        seconds_per_day = 86400
        days_since_J2000 = jd_ut - JD_J2000
        seconds_total = days_since_J2000 * seconds_per_day
        # Start from the J2000 epoch UTC datetime
        dt_utc = datetime(2000, 1, 1, 12, 0, 0, tzinfo=pytz.utc) + timedelta(seconds=seconds_total)
        
        # The rest of the conversion to local time remains the same
        local_tz = pytz.timezone("Asia/Kathmandu") # Assuming LOCAL_TZ is this
        dt_local = dt_utc.astimezone(local_tz)
        return dt_local
    except Exception as e:
        print(f"Time conversion error: {e}")
        return None

def get_sidereal_positions(jd, ayanamsa_type="Lahiri"):
    """
    Calculate sidereal planetary positions using PLANETS dict.
    Returns: positions_dict with Devanagari keys (e.g., 'सु', 'चं', ...)
    """
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED

    try:
        if ayanamsa_type == "Lahiri":
            ayanamsa = get_lahiri(jd)
        else:
            raise ValueError(f"Unsupported ayanamsa: {ayanamsa_type}")
    except Exception as e:
        print(f"Ayanamsa calculation failed: {str(e)}")
        return {}

    positions = {}
    retro_flags = {}

    for name, pid in PLANETS.items():
        try:
            if name == "के":
                continue
            pos_array, flags_used = swe.calc_ut(jd, pid, flags)
            tropical_lon = pos_array[0]
            speed = pos_array[3]
            sidereal_lon = (tropical_lon - ayanamsa) % 360
            positions[name] = sidereal_lon
            retro_flags[name] = speed < 0
        except Exception as e:
            print(f"⚠️ Planet {name} calculation failed: {str(e)}")
            continue

    if "रा" in positions:
        positions["के"] = (positions["रा"] + 180) % 360
        retro_flags["के"] = True
    else:
        print("❌ Rahu missing - cannot calculate Ketu")

    if "सु" not in positions:
        print("❌ Sun ('सु') missing in final positions!")

    return positions
# Constants for Rahu-kalam, Yamagandam, and Gulika-kalam (based on sunrise→sunset)
DAY_SLICES = 8  # Divide daytime into 8 parts

# Correct slice indexes per weekday (Mon=0 ... Sun=6)
RK_INDEX = [1, 6, 4, 5, 3, 2, 7]  # Rahu Kalam
YG_INDEX = [4, 3, 2, 1, 0, 6, 5]  # Yamagandam
GK_INDEX = [5, 4, 3, 2, 1, 0, 6]  # Gulika Kalam

def get_period(start_dt, end_dt, slice_index):
    """Return (start, end) datetimes of the given slice index."""
    span = (end_dt - start_dt) / DAY_SLICES
    s = start_dt + span * slice_index
    e = s + span
    if e < s:
        e += timedelta(days=1)  # Handle cases where end time might be earlier
    return s, e

def rahu_kalam_yamaganda(dt_local, sunrise, sunset):
    """Calculate Rahu Kalam, Yamagandam, and Gulika Kalam for given day."""
    wd = dt_local.weekday()  # Monday = 0 … Sunday = 6
    rk_start, rk_end = get_period(sunrise, sunset, RK_INDEX[wd])
    yg_start, yg_end = get_period(sunrise, sunset, YG_INDEX[wd])
    gk_start, gk_end = get_period(sunrise, sunset, GK_INDEX[wd])
    return {
        "rahu_kalam": (rk_start, rk_end),
        "yamagandam": (yg_start, yg_end),
        "gulika_kalam": (gk_start, gk_end),
    }
def calculate_panchang_for_date(date_time_str, lat=LAT, lon=LON, tz_name=TZ_NAME):
    """
    Calculate panchang, upagrahas, ascendant, and related data for a specific date and time.

    Args:
        date_time_str (str): Date and time in format 'YYYY-MM-DD HH:MM:SS'
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        tz_name (str): Timezone name (e.g., 'Asia/Kathmandu')

    Returns:
        dict: Dictionary containing panchang data, upagrahas, ascendant, and metadata
    """
    try:
        # Parse input date and time
        local_tz = pytz.timezone(tz_name)
        dt_local = local_tz.localize(datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S"))
        dt_utc = dt_local.astimezone(pytz.utc)

        # Calculate Julian Day
        jd = swe.julday(
            dt_utc.year, dt_utc.month, dt_utc.day,
            dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
        )

        # Calculate ascendant
        house_result = swe.houses_ex(jd, lat, lon, b'W', flags=swe.FLG_SWIEPH)
        ascendant_degree_tropical = house_result[1][0]
        ayanamsa = get_lahiri(jd)
        ascendant_degree_sidereal = (ascendant_degree_tropical - ayanamsa) % 360
        ascendant_data = get_lagna_meta(ascendant_degree_sidereal)

        # Get sidereal positions
        positions = get_sidereal_positions(jd, "Lahiri")
        if not positions or 'सु' not in positions or 'चं' not in positions:
            raise ValueError("Failed to calculate planetary positions")

        # Calculate sunrise and sunset using the new function
        year_local, month_local, day_local = dt_local.year, dt_local.month, dt_local.day
        date_obj_local = date(year_local, month_local, day_local)
        sunrise_local, sunset_local = calculate_sunrise_sunset_for_panchang(date_obj_local, lat, lon, tz_name)
        if not sunrise_local or not sunset_local:
            raise ValueError("Failed to calculate sunrise/sunset")


        # **NEW LOGIC TO ENSURE SUNRISE BEFORE SUNSET**
        if sunset_local < sunrise_local:
            # If sunset appears to be on the previous day, add one day
            sunset_local += timedelta(days=1)

        # Calculate Rahu-kalam, Yamagandam, and Gulika-kalam
        kalam_periods = rahu_kalam_yamaganda(dt_local, sunrise_local, sunset_local)
        kalam_formatted = {
            "rahu_kalam": f"{kalam_periods['rahu_kalam'][0].strftime('%H:%M')} - {kalam_periods['rahu_kalam'][1].strftime('%H:%M')}",
            "yamagandam": f"{kalam_periods['yamagandam'][0].strftime('%H:%M')} - {kalam_periods['yamagandam'][1].strftime('%H:%M')}",
            "gulika_kalam": f"{kalam_periods['gulika_kalam'][0].strftime('%H:%M')} - {kalam_periods['gulika_kalam'][1].strftime('%H:%M')}"
        }

        # Calculate panchang
        panchang = calculate_panchang(jd, lat, lon, tz_name, positions)
        if panchang['status'] != 'success':
            raise ValueError(f"Panchang calculation failed: {panchang['message']}")

        # Add kalam periods to panchang data
        panchang['data'].update(kalam_formatted)

        # Calculate upagrahas
        lmt_chart = {
            'datetime': dt_local,
            'sunrise_dt': sunrise_local,
            'sunset_dt': sunset_local,
            'planet_positions': {'सूर्य': positions['सु'], 'चं': positions['चं']},
            'lat': lat,
            'lon': lon,
            'tz_name': tz_name
        }
        upagrahas = calculate_upagrahas(lmt_chart)
        if not upagrahas:
            raise ValueError("Failed to calculate upagrahas")

        # Compile results
        return {
            'status': 'success',
            'data': {
                'panchang': panchang['data'],
                'upagrahas': upagrahas,  # Include all upagrahas
                'ascendant': ascendant_data,
                'planetary_positions': {k: get_lagna_meta(v) for k, v in positions.items()}
            },
            'meta': {
                'input_datetime': dt_local.isoformat(),
                'julian_day': jd,
                'calculation_time': datetime.now().isoformat(),
                'ephemeris_path': EPHE_PATH
            }
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'status': 'error',
            'message': f"Calculation failed: {str(e)}",
            'traceback': traceback.format_exc()
        }
def generate_tithi_kala_report(start_month=9, end_month=11):
    current_year = datetime.now().year
    tz = pytz.timezone(TZ_NAME)
    start_date = tz.localize(datetime(current_year, start_month, 1))
    end_date = tz.localize(datetime(current_year, end_month, 30))
    
    report = []
    delta = timedelta(days=1)
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y/%m/%d")
        try:
            sunrise, sunset = calculate_sunrise_sunset(date_str, LAT, LON, TZ_NAME)
            jd_noon = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)
            positions = get_sidereal_positions(jd_noon, "Lahiri")
            panchang = calculate_panchang(jd_noon, LAT, LON, TZ_NAME, positions)
            tithi = panchang['data']['tithi']
            
            lmt_chart = {
                'datetime': sunrise,
                'sunrise': sunrise.strftime("%H:%M:%S"),
                'sunset': sunset.strftime("%H:%M:%S"),
                'planet_positions': {'सूर्य': positions['सु'], 'चं': positions['चं']},
                'lat': LAT,
                'lon': LON,
                'tz_name': TZ_NAME
            }
            kala = calculate_upagrahas(lmt_chart)['का']
            
            report.append({
                'date': current_date.strftime("%Y-%m-%d"),
                'tithi': tithi,
                'kala': kala
            })
        except Exception as e:
            print(f"Skipped {date_str}: {str(e)}")
            report.append({'date': current_date.strftime("%Y-%m-%d"), 'error': str(e)})
        current_date += delta
    
    return report

# Test Example
