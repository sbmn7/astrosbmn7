import swisseph as swe
from datetime import datetime, timedelta

# Updated SPECIAL_YOGAS with corrected and expanded entries
SPECIAL_YOGAS = {
    "अमृत सिद्दि योग": [
        ("Pushya", "Monday"),
        ("Ashwini", "Monday"),
        ("Hasta", "Monday"),
        ("Rohini", "Wednesday"),
        ("Revati", "Friday")
    ],
    "सर्वथा सिद्दि योग": [
        ("Ashwini", "Sunday"),
        ("Mrigashira", "Wednesday"),
        ("Punarvasu", "Thursday"),
        ("Pushya", "Thursday"),
        ("Hasta", "Monday"),
        ("Anuradha", "Tuesday"),
        ("Shravana", "Monday"),
        ("Dhanishta", "Friday"),
        ("Shatabhisha", "Saturday"),
        ("Revati", "Friday"),
        ("Rohini", "Friday"),
        ("Uttara Phalguni", "Friday"),
        ("Uttara Ashadha", "Friday"),
        ("Uttara Bhadrapada", "Friday")
    ],
    "रवि योग": [
        ("Krittika", "Sunday"),
        ("Uttara Phalguni", "Sunday"),
        ("Vishakha", "Sunday")
    ],
    "सिद्दि योग": [
        ("Mrigashira", "Monday"),
        ("Anuradha", "Wednesday"),
        ("Revati", "Friday")
    ],
    "मरण सिद्दि योग": [
        ("Ardra", "Tuesday"),
        ("Jyestha", "Saturday"),
        ("Bharani", "Sunday")
    ],
    "धन योग": [
        ("Punarvasu", "Thursday"),
        ("Purva Phalguni", "Friday")
    ],
    "महाधन योग": [
        ("Hasta", "Wednesday"),
        ("Pushya", "Thursday")
    ],
    "महाराज योग": [  # Renamed to avoid conflict with chart-based Raja Yoga
        ("Swati", "Sunday"),
        ("Shravana", "Monday")
    ],
    "छत्र योग": [
        ("Revati", "Thursday"),
        ("Rohini", "Friday")
    ],
    "शुभ योग": [
        ("Uttara Bhadrapada", "Thursday"),
        ("Hasta", "Friday")
    ],
    "सौभाग्य योग": [
        ("Chitra", "Wednesday"),
        ("Shatabhisha", "Thursday")
    ],
    "ब्रह्मा योग": [
        ("Purva Bhadrapada", "Monday"),
        ("Swati", "Friday")
    ],
    "इन्द्र योग": [
        ("Vishakha", "Tuesday"),
        ("Punarvasu", "Wednesday")
    ],
    "शुकर्म योग": [
        ("Chitra", "Monday"),
        ("Dhanishta", "Friday")
    ],
    "गुरु पुष्य योग": [  # Added standard yoga
        ("Pushya", "Thursday")
    ],
    "त्रिपुस्कर योग": [  # Added standard yoga, simplified (Tithi check needed for full accuracy)
        ("Punarvasu", "Sunday"),
        ("Vishakha", "Tuesday"),
        ("Uttara Bhadrapada", "Saturday")
    ]
}

def get_nakshatra(jd):
    """Calculate the Moon's Nakshatra for a given Julian Day."""
    nakshatras = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
        "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyestha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
        "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    try:
        moon_pos, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)
        nak_index = int((moon_pos[0] % 360) / 13.33333333333)  # Each Nakshatra is 13°20'
        return nakshatras[nak_index]
    except Exception:
        return None

def get_weekday(jd):
    """Calculate the weekday for a given Julian Day."""
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    try:
        dt = swe.julday_to_datetime(jd)
        return weekdays[dt.weekday()]
    except Exception:
        return None

def detect_panchang_yogas(jd):
    """Detect Panchang yogas based on Moon's Nakshatra and weekday."""
    nakshatra = get_nakshatra(jd)
    weekday = get_weekday(jd)
    if not nakshatra or not weekday:
        return []
    
    detected_yogas = []
    for yoga_name, conditions in SPECIAL_YOGAS.items():
        if (nakshatra, weekday) in conditions:
            detected_yogas.append(yoga_name)
    
    return detected_yogas

def show_panchang_yogas(parent, jd):
    """Display detected Panchang yogas in a Tkinter GUI."""
    try:
        import tkinter as tk
        from tkinter import ttk
        yogas = detect_panchang_yogas(jd)
        
        frame = tk.Frame(parent)
        tk.Label(frame, text="Panchang Yogas", font=("Mangal", 10, "bold")).pack(pady=5)
        
        if not yogas:
            tk.Label(frame, text="No Panchang yogas detected.", font=("Mangal", 10)).pack()
        else:
            for yoga in yogas:
                tk.Label(frame, text=yoga, font=("Mangal", 10)).pack(anchor="w")
        
        frame.pack(fill=tk.BOTH, expand=True)
        return frame
    except Exception as e:
        tk.Label(parent, text=f"Error displaying Panchang yogas: {e}", font=("Mangal", 10)).pack()
        return None