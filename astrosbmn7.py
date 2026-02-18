import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QPen, QFont, QColor,QFontMetrics
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QLineEdit, QComboBox, QPushButton, 
                             QScrollArea, QFrame, QSplitter, QTextEdit, QTableWidget, 
                             QTableWidgetItem, QCompleter, QTreeWidget, QTreeWidgetItem, 
                             QHeaderView, QMessageBox,QSizePolicy)
import os
import sys
from utils import (calculate_lmt_and_charts_logic, get_nakshatra_from_degree, 
                   get_rashi_from_degree, get_pada_from_degree, calculate_arudha_positions, 
                   get_divisional_data_package, calculate_yogini_dasha)
from varr import DIVISION_NAMES, MOOLA_DASHA_YEARS, RASI_SIGNS
import swisseph as swe
from datetime import datetime
import pytz
from NepalIndia import Nepal_district_data, India_district_data, World_city_data
from BS_DATABASE import gregorian_to_bs,bs_to_gregorian
from timezonefinder import TimezoneFinder
from strength import calculate_strengths, calculate_ashtakavarga, get_karaka_info, calculate_sthanabala, calculate_dig_bala, calculate_saptavargaja_bala, calculate_uchcha_bala, get_house_number
from Yogasf import get_detected_yogas_list
#from nchart import calculate_panchang_for_date
from Vishmottari_Dasha import generate_dasha_tree, jd_to_date_str
print("QT FILE STARTED")
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS  # when bundled
    except AttributeError:
        base_path = os.path.abspath(".")  # when running directly

    return os.path.join(base_path, relative_path)
all_districts = ["Other"] + list(Nepal_district_data.keys()) + list(India_district_data.keys()) + list(World_city_data.keys())
all_districts.sort() # Sort the predefined districts alphabetically after "Other"
global positions, rashi_numbers, retro_flags, combust_flags
global d9_positions, d9_asc_degree # Add global variables for D9 data
global d60_positions, d60_asc_degree # Add global variables for D60 data (since it's calculated here)
# Set environment variables for WeasyPrint
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
# --- Font Configuration ---
DEV_FONT_FAMILY = "Mangal"  # Primary choice
FALLBACK_FONTS = ["Noto Sans Devanagari", "Mangal", "Nirmala UI", "Arial"]  # Fallback options
DEV_FONT_SIZE = 10
devanagari_font_tuple = (DEV_FONT_FAMILY, DEV_FONT_SIZE)
# Global variables for chart data
positions = {}
rashi_numbers = []
retro_flags = {}
combust_flags = {}
chart_cache = {}
class NorthChartWidget(QWidget):
    def __init__(self, chart_data, rashi_numbers, title):
        super().__init__()
        self.chart_data = chart_data
        self.rashi_numbers = rashi_numbers
        self.chart_title = title
        self.setMinimumSize(280, 280) # Slightly larger for clarity

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        t_height = 30
        chart_rect = QRect(0, t_height, w, h - t_height)
        cx, cy = chart_rect.center().x(), chart_rect.center().y()
        
        # Draw Title
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(QRect(0, 0, w, t_height), Qt.AlignmentFlag.AlignCenter, self.chart_title)

        # Define Corner and Mid Points
        p_top_l = chart_rect.topLeft()
        p_top_r = chart_rect.topRight()
        p_bot_l = chart_rect.bottomLeft()
        p_bot_r = chart_rect.bottomRight()
        p_top_m = QPoint(cx, chart_rect.top())
        p_bot_m = QPoint(cx, chart_rect.bottom())
        p_l_m = QPoint(chart_rect.left(), cy)
        p_r_m = QPoint(chart_rect.right(), cy)

        # Draw Frame
        pen = QPen(QColor("black"), 1.5)
        painter.setPen(pen)
        painter.drawRect(chart_rect)
        
        # Draw Diagonals and Diamonds
        pen.setColor(QColor("black"))
        painter.setPen(pen)
        painter.drawLine(p_top_l, p_bot_r)
        painter.drawLine(p_top_r, p_bot_l)
        painter.drawLine(p_top_m, p_l_m)
        painter.drawLine(p_l_m, p_bot_m)
        painter.drawLine(p_bot_m, p_r_m)
        painter.drawLine(p_r_m, p_top_m)

        # Define "Safe Rects" for each house to prevent border crossing
        # House indexing: 0 (1st House) at top center
        side = w // 4
        safe_rects = [
            QRect(cx - side//2, cy - side, side, side),              # H1 (Top Diamond)
            QRect(p_top_l.x() + 5, p_top_l.y() + 5, side, side//2), # H2
            QRect(p_top_l.x() + 5, p_top_l.y() + 40, side//2, side), # H3
            QRect(chart_rect.left() + 5, cy - side//2, side, side),  # H4 (Left Diamond)
            # ... and so on for all 12 houses
        ]
        
        # Refined Logic: Instead of fixed Rects, calculate dynamic center bounds
        self.draw_house_content(painter, cx, cy, chart_rect)

    def draw_house_content(self, painter, cx, cy, rect):
        w = rect.width()
        h = rect.height()
        unit_w = w / 4
        unit_h = h / 4

        # House Centers (HC) and their constrained bounding boxes (BB)
        # Format: (Center_X, Center_Y, Max_Width, Max_Height)
        house_geometry = [
            (cx, cy - unit_h, unit_w * 1.5, unit_h),       # H1
            (cx - unit_w, cy - unit_h * 1.5, unit_w, unit_h), # H2
            (cx - unit_w * 1.5, cy - unit_h, unit_h, unit_w), # H3
            (cx - unit_w, cy, unit_w, unit_h * 1.5),       # H4
            (cx - unit_w * 1.5, cy + unit_h, unit_h, unit_w), # H5
            (cx - unit_w, cy + unit_h * 1.5, unit_w, unit_h), # H6
            (cx, cy + unit_h, unit_w * 1.5, unit_h),       # H7
            (cx + unit_w, cy + unit_h * 1.5, unit_w, unit_h), # H8
            (cx + unit_w * 1.5, cy + unit_h, unit_h, unit_w), # H9
            (cx + unit_w, cy, unit_w, unit_h * 1.5),       # H10
            (cx + unit_w * 1.5, cy - unit_h, unit_h, unit_w), # H11
            (cx + unit_w, cy - unit_h * 1.5, unit_w, unit_h), # H12
        ]

        for i, (hx, hy, mw, mh) in enumerate(house_geometry):
            rashi = str(self.rashi_numbers[i])
            planets = ", ".join(self.chart_data.get(i, []))
            full_text = f"{rashi}\n{planets}" if planets else rashi
            
            # Create a bounding box centered on the house center
            text_rect = QRect(int(hx - mw/2), int(hy - mh/2), int(mw), int(mh))
            
            # Draw text with word wrap and internal alignment
            painter.setPen(QColor("black"))
            painter.setFont(QFont("Mangal", 9))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, full_text)
class AVChartWidget(QWidget):
    def __init__(self, title, data):
        super().__init__()
        self.title = title
        self.data = data # List of 12 values
        self.setFixedSize(150, 150)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        
        # Draw Border
        p.drawRect(5, 5, w-10, h-10)
        
        # Draw North Indian Diamond Lines
        p.drawLine(5, 5, w-5, h-5)
        p.drawLine(w-5, 5, 5, h-5)
        p.drawLine(w//2, 5, 5, h//2)
        p.drawLine(5, h//2, w//2, h-5)
        p.drawLine(w//2, h-5, w-5, h//2)
        p.drawLine(w-5, h//2, w//2, 5)
        
        # House Centers (Roughly)
        centers = [
            (w//2, h//4), (w//4, h//8), (w//8, h//4), (w//4, h//2),
            (w//8, 3*h//4), (w//4, 7*h//8), (w//2, 3*h//4), (3*w//4, 7*h//8),
            (7*w//8, 3*h//4), (3*w//4, h//2), (7*w//8, h//4), (3*w//4, h//8)
        ]
        
        # Draw Title and Values
        p.drawText(10, 15, self.title)
        for i, val in enumerate(self.data):
            if i < len(centers):
                p.drawText(centers[i][0]-5, centers[i][1]+5, str(val))
class AstrologyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vedic Astrology - PyQt6")
        self.resize(1200, 800)

        # Main Widget and Horizontal Splitter
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QHBoxLayout(main_widget)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter)

        # --- LEFT PANEL: Input Form ---
        self.init_left_panel()

        # --- RIGHT PANEL: Results (Scrollable) ---
        self.init_right_panel()

    def init_left_panel(self):
        left_container = QFrame()
        left_container.setFixedWidth(330)
        left_layout = QVBoxLayout(left_container)
        
        form_grid = QGridLayout()
        
        # Row 0: Name
        form_grid.addWidget(QLabel("Name:"), 0, 0)
        self.name_input = QLineEdit("User")
        form_grid.addWidget(self.name_input, 0, 1)
        
        # Row 1: Gregorian Date (AD)
        form_grid.addWidget(QLabel("Date (AD YYYY-MM-DD):"), 1, 0)
        self.date_input = QLineEdit(datetime.now().strftime("%Y-%m-%d"))
        self.date_input.textChanged.connect(self.on_greg_date_changed)
        form_grid.addWidget(self.date_input, 1, 1)
        
        # Row 2: BS Date (Bikram Sambat)
        form_grid.addWidget(QLabel("Date (BS YYYY-MM-DD):"), 2, 0)
        self.bs_date_input = QLineEdit()
        self.bs_date_input.textChanged.connect(self.on_bs_date_changed)
        self.bs_date_input.setPlaceholderText("Auto-converted")
        form_grid.addWidget(self.bs_date_input, 2, 1)
        
        # Initialize BS date from current Gregorian date
        self.sync_bs_from_greg()
        
        # Row 3: Time
        form_grid.addWidget(QLabel("Time (HH:MM:SS):"), 3, 0)
        self.time_input = QLineEdit("10:30:00")
        form_grid.addWidget(self.time_input, 3, 1)
        
        # Row 4: AM/PM
        form_grid.addWidget(QLabel("AM/PM:"), 4, 0)
        self.ampm_combo = QComboBox()
        self.ampm_combo.addItems(["AM", "PM"])
        form_grid.addWidget(self.ampm_combo, 4, 1)
        
        # Row 5: Location Autocomplete
        form_grid.addWidget(QLabel("Location:"), 5, 0)
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Type to search places...")
        self.setup_location_autocomplete()  # autocomplete from combined location_data
        self.location_input.editingFinished.connect(self.on_location_selected)
        form_grid.addWidget(self.location_input, 5, 1)
        
        # Row 6: Latitude
        form_grid.addWidget(QLabel("Latitude:"), 6, 0)
        self.lat_input = QLineEdit("27.7172")  # default Kathmandu
        form_grid.addWidget(self.lat_input, 6, 1)
        
        # Row 7: Longitude
        form_grid.addWidget(QLabel("Longitude:"), 7, 0)
        self.lon_input = QLineEdit("85.3240")  # default Kathmandu
        form_grid.addWidget(self.lon_input, 7, 1)
        
        # Row 8: Timezone
        form_grid.addWidget(QLabel("Timezone:"), 8, 0)
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(["Asia/Kathmandu", "Asia/Kolkata", "UTC"])
        self.tz_combo.setCurrentText("Asia/Kathmandu")  # Default display
        form_grid.addWidget(self.tz_combo, 8, 1)
        
        # Row 9: Ayanamsa
        form_grid.addWidget(QLabel("Ayanamsa:"), 9, 0)
        self.ayanamsa_combo = QComboBox()
        self.ayanamsa_combo.addItems(["Lahiri", "True Lahiri", "KP Old", "KP New"])
        form_grid.addWidget(self.ayanamsa_combo, 9, 1)
        
        left_layout.addLayout(form_grid)

        # Calculate button
        self.calc_btn = QPushButton("Calculate Charts")
        self.calc_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; height: 40px;")
        self.calc_btn.clicked.connect(self.run_calculation)
        left_layout.addWidget(self.calc_btn)
        
        left_layout.addStretch()
        self.splitter.addWidget(left_container)


    def init_right_panel(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        
        # === Tab Bar with Division Selector AFTER Gochar ===
        self.tab_bar = QFrame()
        self.tab_bar.setMaximumHeight(50)
        self.tab_bar.setStyleSheet("""
        QFrame {
            background-color: #2c3e50;
            border-radius: 5px;
        }
        QPushButton {
            background-color: #34495e;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 2px;
            border-radius: 3px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #3498db;
        }
        QPushButton:checked, QPushButton:pressed {
            background-color: #e74c3c;
        }
        QComboBox {
            background-color: #34495e;
            color: white;
            border: 1px solid #2c3e50;
            padding: 5px 10px;
            border-radius: 3px;
            min-width: 150px;
        }
        QComboBox:hover {
            background-color: #3498db;
        }
        QComboBox::drop-down {
            border: none;
            width: 20px;
        }
        QComboBox QAbstractItemView {
            background-color: #34495e;
            color: white;
            selection-background-color: #e74c3c;
        }
        """)
        
        tab_layout = QHBoxLayout(self.tab_bar)
        tab_layout.setSpacing(5)
        tab_layout.setContentsMargins(10, 5, 10, 5)
        
        self.tab_buttons = {}
        tab_items = [
            ("Charts", "charts"),
            ("Vimshottari", "vimshottari"),
            ("Moola", "moola"),
            ("Yogini", "yogini"),
            ("Strength", "strength"),
            ("Yogas", "yogas"),
            ("Gochar", "gochar")
        ]
        
        # Add tab buttons
        for label, key in tab_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.switch_tab(k))
            self.tab_buttons[key] = btn
            tab_layout.addWidget(btn)
        
        # === ADD DIVISION SELECTOR RIGHT AFTER GOCHAR BUTTON ===
        label = QLabel("Division Chart:")
        label.setStyleSheet("color: white;")  # Sets the text color to white
        tab_layout.addWidget(label)
        self.division_selector = QComboBox()
        self.division_selector.addItems(list(DIVISION_NAMES.values()))
        self.division_selector.currentIndexChanged.connect(self.on_division_selector_changed)
        tab_layout.addWidget(self.division_selector)
        # ========================================================
        
        tab_layout.addStretch()
        self.right_layout.addWidget(self.tab_bar)
        
        # === CREATE CONTENT STACK (THIS WAS MISSING!) ===
        self.content_stack = QFrame()
        self.content_layout = QVBoxLayout(self.content_stack)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Charts View (Default) ---
        self.charts_view = QWidget()
        charts_layout = QVBoxLayout(self.charts_view)
        self.charts_layout = QHBoxLayout()
        self.tables_layout = QHBoxLayout()
        charts_layout.addLayout(self.charts_layout)
        charts_layout.addLayout(self.tables_layout)
        self.content_layout.addWidget(self.charts_view)
        
        # --- Other Tabs ---
        self.vimshottari_view = self.create_dasha_view("Vimshottari Dasha", "vimshottari")
        self.moola_view = self.create_dasha_view("Moola Dasha", "moola")
        self.yogini_view = self.create_dasha_view("Yogini Dasha", "yogini")
        self.strength_view = self.create_strength_view()
        self.yogas_view = self.create_yogas_view()
        self.gochar_view = self.create_gochar_view()
        
        self.content_layout.addWidget(self.vimshottari_view)
        self.content_layout.addWidget(self.moola_view)
        self.content_layout.addWidget(self.yogini_view)
        self.content_layout.addWidget(self.strength_view)
        self.content_layout.addWidget(self.yogas_view)
        self.content_layout.addWidget(self.gochar_view)
        
        # Hide all except Charts initially
        self.vimshottari_view.hide()
        self.moola_view.hide()
        self.yogini_view.hide()
        self.strength_view.hide()
        self.yogas_view.hide()
        self.gochar_view.hide()
        self.tab_buttons["charts"].setChecked(True)
        
        self.right_layout.addWidget(self.content_stack)  # Now content_stack exists!
        # ==============================================
        
        self.scroll.setWidget(self.right_container)
        self.splitter.addWidget(self.scroll)
        self.splitter.setSizes([350, 850])
        self.splitter.setCollapsible(0, False)
    def switch_tab(self, tab_key):
        """Switch between different analysis tabs"""
        # Update button states
        for key, btn in self.tab_buttons.items():
            btn.setChecked(key == tab_key)
        
        # Hide all views
        self.charts_view.hide()
        self.vimshottari_view.hide()
        self.moola_view.hide()
        self.yogini_view.hide()
        self.strength_view.hide()
        self.yogas_view.hide()
        self.gochar_view.hide()
        
        # Show selected view
        if tab_key == "charts":
            self.charts_view.show()
        elif tab_key == "vimshottari":
            self.vimshottari_view.show()
            self.calculate_vimshottari()
        elif tab_key == "moola":
            self.moola_view.show()
            self.calculate_moola()
        elif tab_key == "yogini":
            self.yogini_view.show()
            self.calculate_yogini()
        elif tab_key == "strength":
            self.strength_view.show()
            self.calculate_strength_tab()
        elif tab_key == "yogas":
            self.yogas_view.show()
            self.calculate_yogas()
        elif tab_key == "gochar":
            self.gochar_view.show()
            self.calculate_gochar()
    def get_moola_starting_group(self):
        """Finds the strongest planet group (Kendra, Panaphara, or Apoklima)"""
        if not hasattr(self, 'current_astro_data'): 
            return []
        
        results = self.current_astro_data
        positions = results['positions']
        
        # 1. Get real strengths from your strength.py
        try:
            # We use the data already calculated during the 'Submit' phase
            table_data, _ = calculate_strengths(
                jd=results['jd'],
                positions=positions,
                planet_speeds=results.get('speeds', {}),
                divisional_dignities=results.get('div_dignities', {}),
                phala_weights={},
                include_nodes=True
            )
            # Create a lookup for Shadbala scores
            shadbala_lookup = {row[0]: float(row[2]) for row in table_data}
        except Exception as e:
            print(f"Shadbala calculation error: {e}")
            shadbala_lookup = {p: 0 for p in ["सु", "चं", "मं", "बु", "गु", "शु", "श", "रा", "के"]}

        # 2. Define Vedic House Groups
        asc_lon = positions.get('Asc', 0)
        asc_sign_idx = int(asc_lon // 30)
        
        groups = [
            [1, 4, 7, 10], # Kendra
            [2, 5, 8, 11], # Panaphara
            [3, 6, 9, 12]  # Apoklima
        ]
        
        target_grahas = ["सु", "चं", "मं", "बु", "गु", "शु", "श", "रा", "के"]

        for house_group in groups:
            found_planets = []
            for name in target_grahas:
                if name not in positions: continue
                p_lon = positions[name]
                p_sign_idx = int(p_lon // 30)
                
                # House calculation (Sign-to-Sign)
                house_num = (p_sign_idx - asc_sign_idx) % 12 + 1
                
                if house_num in house_group:
                    strength = shadbala_lookup.get(name, 0)
                    found_planets.append({'name': name, 'strength': strength})
            
            if found_planets:
                # Sort strongest to weakest based on Shadbala
                found_planets.sort(key=lambda x: x['strength'], reverse=True)
                return [p['name'] for p in found_planets]
                
        return target_grahas

    def create_dasha_view(self, title, dasha_type):
        """Create a hierarchical Tree view for Dasha displays"""
        view = QWidget()
        layout = QVBoxLayout(view)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; padding: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # CHANGED: Use QTreeWidget instead of QTableWidget
        tree = QTreeWidget()
        tree.setColumnCount(4)
        tree.setHeaderLabels(["Dasha Period (Planet)", "Start Date", "End Date", "Duration"])
        tree.setColumnWidth(0, 200) # Give the planet name room to indent
        tree.setObjectName(f"{dasha_type}_tree")
        
        layout.addWidget(tree)
        
        # Store reference
        setattr(self, f"{dasha_type}_table", tree) # Keeping the name '_table' if your other code depends on it, but it's now a Tree.
        return view
    def create_strength_view(self):
        view = QWidget()
        main_layout = QVBoxLayout(view)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for the entire content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1a1a1a;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a5a5a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #1a1a1a;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- Section 1: Shadbala Summary ---
        shadbala_frame = QFrame()
        shadbala_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                border: 2px solid #3d3d3d;
            }
        """)
        shadbala_layout = QVBoxLayout(shadbala_frame)
        shadbala_layout.setContentsMargins(15, 15, 15, 15)
        shadbala_layout.setSpacing(10)
        
        shadbala_title = QLabel("षडबल सारांश (Shadbala Summary)")
        shadbala_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 10px;
            background-color: #1a1a1a;
            border-radius: 6px;
        """)
        shadbala_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        shadbala_layout.addWidget(shadbala_title)
        
        self.strength_table = QTableWidget()
        self.strength_table.setColumnCount(8)
        self.strength_table.setHorizontalHeaderLabels([
            "Planet", "Sthana", "Dig", "Kala", "Chesta", "Naisargika", "Drik", "Total"
        ])
        self.strength_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 8px;
                gridline-color: #3d3d3d;
                border: none;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 10px;
                border-bottom: 1px solid #3d3d3d;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 12px;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
            }
        """)
        
        # FIX: Proper table sizing - no unnecessary scroll
        self.strength_table.verticalHeader().setVisible(False)
        self.strength_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.strength_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.strength_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.strength_table.setMinimumHeight(200)
        self.strength_table.setMaximumHeight(350)
        
        shadbala_layout.addWidget(self.strength_table)
        layout.addWidget(shadbala_frame)

        # --- Section 2: Sthanabala Breakdown ---
        sthana_frame = QFrame()
        sthana_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                border: 2px solid #3d3d3d;
            }
        """)
        sthana_layout = QVBoxLayout(sthana_frame)
        sthana_layout.setContentsMargins(15, 15, 15, 15)
        sthana_layout.setSpacing(10)
        
        sthana_title = QLabel("स्थानबल विवरण (Sthanabala Breakdown)")
        sthana_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 10px;
            background-color: #1a1a1a;
            border-radius: 6px;
        """)
        sthana_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sthana_layout.addWidget(sthana_title)
        
        self.sthana_table = QTableWidget()
        self.sthana_table.setColumnCount(7)
        self.sthana_table.setHorizontalHeaderLabels([
            "Planet", "Uchcha", "Saptavarga", "Oja-Yugma", "Dig", "Kendradi", "Total"
        ])
        self.sthana_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 8px;
                gridline-color: #3d3d3d;
                border: none;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 10px;
                border-bottom: 1px solid #3d3d3d;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 12px;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
            }
        """)
        
        # FIX: Proper table sizing
        self.sthana_table.verticalHeader().setVisible(False)
        self.sthana_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.sthana_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.sthana_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sthana_table.setMinimumHeight(200)
        self.sthana_table.setMaximumHeight(350)
        
        sthana_layout.addWidget(self.sthana_table)
        layout.addWidget(sthana_frame)

        # --- Section 3: Chara Karakas ---
        karaka_frame = QFrame()
        karaka_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                border: 2px solid #3d3d3d;
            }
        """)
        karaka_layout = QVBoxLayout(karaka_frame)
        karaka_layout.setContentsMargins(15, 15, 15, 15)
        karaka_layout.setSpacing(10)
        
        karaka_title = QLabel("चर कारक (Chara Karakas)")
        karaka_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 10px;
            background-color: #1a1a1a;
            border-radius: 6px;
        """)
        karaka_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        karaka_layout.addWidget(karaka_title)
        
        self.karaka_table = QTableWidget()
        self.karaka_table.setColumnCount(4)
        self.karaka_table.setHorizontalHeaderLabels(["Karaka", "Planet", "Degree", "Sign"])
        self.karaka_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 8px;
                gridline-color: #3d3d3d;
                border: none;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 10px;
                border-bottom: 1px solid #3d3d3d;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 12px;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
            }
        """)
        
        # FIX: Proper table sizing
        self.karaka_table.verticalHeader().setVisible(False)
        self.karaka_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.karaka_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.karaka_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.karaka_table.setMinimumHeight(220)
        self.karaka_table.setMaximumHeight(350)
        
        karaka_layout.addWidget(self.karaka_table)
        layout.addWidget(karaka_frame)
        
        # --- Section 4: Ashtakavarga ---
        av_frame = QFrame()
        av_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                border: 2px solid #3d3d3d;
            }
        """)
        av_layout = QVBoxLayout(av_frame)
        av_layout.setContentsMargins(15, 15, 15, 15)
        av_layout.setSpacing(10)
        
        av_title = QLabel("अष्टकवर्ग (Ashtakavarga)")
        av_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            padding: 10px;
            background-color: #1a1a1a;
            border-radius: 6px;
        """)
        av_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        av_layout.addWidget(av_title)
        
        # Container for Ashtakavarga grids
        self.av_container = QGridLayout()
        self.av_container.setSpacing(15)
        av_layout.addLayout(self.av_container)
        
        layout.addWidget(av_frame)
        
        # Add stretch at the end to push content to top
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        return view
    
    def create_yogas_view(self):
        view = QWidget()
        view.setStyleSheet("""
            QWidget {
                background-color: #0f0f1a;
                font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
            }
        """)
        
        main_layout = QVBoxLayout(view)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Custom Scroll Area with glassmorphism scrollbar
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #0f0f1a;
            }
            QScrollBar:vertical {
                background-color: rgba(30, 30, 50, 0.5);
                width: 8px;
                border-radius: 4px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #818cf8, stop:1 #a78bfa);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #0f0f1a;")
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(32)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Hero Section with cosmic gradient and glow effects
        hero_frame = QFrame()
        hero_frame.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:0.5, cy:0.3, radius:0.8,
                    stop:0 #1e1b4b, stop:0.4 #312e81, stop:1 #1e1b4b);
                border-radius: 20px;
                border: 1px solid rgba(99, 102, 241, 0.3);
            }
        """)
        hero_frame.setGraphicsEffect(self._create_glow_effect())
        
        hero_layout = QVBoxLayout(hero_frame)
        hero_layout.setContentsMargins(40, 35, 40, 35)
        hero_layout.setSpacing(12)
        
        # Title with gradient text effect using styled label
        title_container = QWidget()
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(12)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        om_symbol = QLabel("🕉")
        om_symbol.setStyleSheet("font-size: 32px; background: transparent;")
        title_layout.addWidget(om_symbol)
        
        title_text = QLabel("D1 & D9 Yoga Analysis")
        title_text.setStyleSheet("""
            font-size: 28px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: 2px;
            background: transparent;
        """)
        title_layout.addWidget(title_text)
        
        hero_layout.addWidget(title_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Discover the cosmic planetary combinations shaping your destiny")
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #a5b4fc;
            letter-spacing: 0.5px;
            background: transparent;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(subtitle)
        
        layout.addWidget(hero_frame)
        
        # Strength Indicators - Horizontal card layout with icons
        indicators_frame = QFrame()
        indicators_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 50, 0.6);
                border-radius: 16px;
                border: 1px solid rgba(99, 102, 241, 0.2);
            }
        """)
        
        indicators_layout = QHBoxLayout(indicators_frame)
        indicators_layout.setContentsMargins(24, 20, 24, 20)
        indicators_layout.setSpacing(16)
        indicators_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Strength indicator cards
        strengths = [
            ("Weak", "#ef4444", "⚡"),
            ("Moderate", "#f59e0b", "🔥"),
            ("Strong", "#10b981", "⭐"),
            ("Very Strong", "#3b82f6", "💎")
        ]
        
        for label, color, icon in strengths:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(255, 255, 255, 0.03);
                    border-radius: 12px;
                    border: 1px solid {color}40;
                    padding: 12px 20px;
                }}
                QFrame:hover {{
                    background-color: rgba(255, 255, 255, 0.06);
                    border: 1px solid {color}80;
                }}
            """)
            
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(8)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 16px; color: {color}; background: transparent;")
            card_layout.addWidget(icon_label)
            
            text_label = QLabel(label)
            text_label.setStyleSheet(f"""
                font-size: 13px;
                font-weight: 600;
                color: {color};
                background: transparent;
            """)
            card_layout.addWidget(text_label)
            
            indicators_layout.addWidget(card)
        
        layout.addWidget(indicators_frame)
        
        # Main Content Card - Yoga Table
        table_card = QFrame()
        table_card.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 35, 0.8);
                border-radius: 20px;
                border: 1px solid rgba(99, 102, 241, 0.2);
            }
        """)
        
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # Table Header
        table_header = QFrame()
        table_header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(99, 102, 241, 0.2), stop:1 rgba(99, 102, 241, 0.05));
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid rgba(99, 102, 241, 0.2);
            }
        """)
        
        header_layout = QHBoxLayout(table_header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(12)
        
        header_icon = QLabel("✨")
        header_icon.setStyleSheet("font-size: 20px; background: transparent;")
        header_layout.addWidget(header_icon)
        
        header_title = QLabel("Detected Yogas")
        header_title.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            background: transparent;
        """)
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        
        table_layout.addWidget(table_header)
        
        # Enhanced Table
        self.yoga_table = QTableWidget()
        self.yoga_table.setColumnCount(3)
        self.yoga_table.setHorizontalHeaderLabels(["Yoga Name", "Description & Conditions", "Strength"])
        
        self.yoga_table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                color: #e2e8f0;
                border: none;
                gridline-color: rgba(99, 102, 241, 0.1);
                outline: none;
            }
            QTableWidget::item {
                color: #e2e8f0;
                padding: 20px 24px;
                border-bottom: 1px solid rgba(99, 102, 241, 0.1);
                background-color: transparent;
            }
            QTableWidget::item:selected {
                background-color: rgba(99, 102, 241, 0.15);
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: rgba(99, 102, 241, 0.08);
            }
            QHeaderView::section {
                background-color: transparent;
                color: #818cf8;
                padding: 16px 24px;
                font-weight: 600;
                font-size: 13px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                border: none;
                border-bottom: 2px solid rgba(99, 102, 241, 0.3);
            }
            QHeaderView::section:hover {
                color: #a5b4fc;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(99, 102, 241, 0.4);
                border-radius: 3px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(99, 102, 241, 0.6);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Table Configuration
        self.yoga_table.verticalHeader().setVisible(False)
        self.yoga_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.yoga_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.yoga_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.yoga_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.yoga_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.yoga_table.setShowGrid(False)
        self.yoga_table.setWordWrap(True)
        self.yoga_table.setTextElideMode(Qt.TextElideMode.ElideNone)
        
        # Column sizing
        header = self.yoga_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.yoga_table.setColumnWidth(0, 220)
        self.yoga_table.setColumnWidth(2, 140)
        self.yoga_table.verticalHeader().setDefaultSectionSize(70)
        self.yoga_table.setMinimumHeight(450)
        
        table_layout.addWidget(self.yoga_table)
        
        # Table Footer with subtle gradient
        table_footer = QFrame()
        table_footer.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(99, 102, 241, 0.05), stop:1 rgba(99, 102, 241, 0.15));
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
                min-height: 8px;
                max-height: 8px;
            }
        """)
        table_layout.addWidget(table_footer)
        
        layout.addWidget(table_card)
        
        # Insight Footer - Glassmorphism style
        insight_frame = QFrame()
        insight_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 30, 50, 0.4);
                border-radius: 16px;
                border: 1px solid rgba(99, 102, 241, 0.15);
            }
        """)
        
        insight_layout = QHBoxLayout(insight_frame)
        insight_layout.setContentsMargins(24, 20, 24, 20)
        insight_layout.setSpacing(16)
        
        info_icon = QLabel("🔮")
        info_icon.setStyleSheet("font-size: 24px; background: transparent;")
        insight_layout.addWidget(info_icon)
        
        info_text = QLabel("Yoga strength is calculated based on planetary dignity, house positions, and aspects. "
                        "These cosmic combinations reveal karmic patterns and life potentials.")
        info_text.setStyleSheet("""
            font-size: 13px;
            color: #94a3b8;
            line-height: 1.5;
            background: transparent;
        """)
        info_text.setWordWrap(True)
        insight_layout.addWidget(info_text, stretch=1)
        
        layout.addWidget(insight_frame)
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        return view

    def _create_glow_effect(self):
        """Helper method to create subtle glow effect for hero section"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(60)
        glow.setColor(QColor(99, 102, 241, 80))
        glow.setOffset(0, 0)
        return glow
    #callculation area for tabs buttons
    
    def calculate_vimshottari(self):
        if not hasattr(self, 'current_astro_data'):
            return
        
        jd = self.current_astro_data['jd']
        positions = self.current_astro_data['positions']
        moon_lon = positions.get('Moon') or positions.get('चं')

        if moon_lon is None: return

        # 1. Get the nested data
        dasha_data = generate_dasha_tree(jd, moon_lon)

        # 2. Clear the tree
        tree = self.vimshottari_table # This is now a QTreeWidget
        tree.clear()

        # 3. Recursive function to fill the tree
        def add_dasha_items(parent_item, dasha_list):
            for dasha in dasha_list:
                # Format dates and duration
                start_str = jd_to_date_str(dasha['start_jd'])
                end_str = jd_to_date_str(dasha['end_jd'])
                duration = f"{dasha['duration_days'] / 365.25:.2f} yrs"
                
                # Create a tree row
                item = QTreeWidgetItem([str(dasha['planet']), start_str, end_str, duration])
                
                # Add to parent (either the tree itself or a Mahadasha item)
                if parent_item == tree:
                    tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                
                # If there are sub-dashas (Antar, Pratyantar...), call this function again
                if 'sub_dashas' in dasha and dasha['sub_dashas']:
                    add_dasha_items(item, dasha['sub_dashas'])

        # Start the recursive process
        add_dasha_items(tree, dasha_data)
    def calculate_moola(self):
        """Calculate Moola Dasha based on strict Vedic norms"""
        if not hasattr(self, 'current_astro_data'):
            print("Please calculate charts first.")
            return

        # 1. Get the strict sequence of planets
        ordered_planets = self.get_moola_starting_group()
        
        # 2. Add any missing planets to complete the list
        all_p = ["सु", "चं", "मं", "बु", "गु", "शु", "श", "रा", "के"]
        for p in all_p:
            if p not in ordered_planets:
                ordered_planets.append(p)

        # 3. Reference the Tree widget and clear it
        tree = self.moola_table 
        tree.clear()
        
        current_jd = self.current_astro_data['jd']

        # 4. Fill the Tree UI
        for p_name in ordered_planets:
            years = MOOLA_DASHA_YEARS.get(p_name, 7)
            duration_days = years * 365.25
            end_jd = current_jd + duration_days
            
            # Create a row in the tree
            item = QTreeWidgetItem([
                p_name, 
                jd_to_date_str(current_jd), 
                jd_to_date_str(end_jd), 
                f"{years} yrs"
            ])
            
            # If this was the first planet (strongest), make it bold/green
            if p_name == ordered_planets[0]:
                item.setBackground(0, QColor("#E8F5E9")) # Light green
            
            tree.addTopLevelItem(item)
            current_jd = end_jd
        
        tree.resizeColumnToContents(0)
    
    def calculate_yogini(self):
        if not hasattr(self, 'current_astro_data'):
            return

        jd = self.current_astro_data['jd']
        positions = self.current_astro_data['positions']
        moon_lon = positions.get('Moon') or positions.get('चं')

        if moon_lon is None:
            return

        dasha_list = calculate_yogini_dasha(jd, moon_lon)

        tree = self.yogini_table
        tree.clear()

        for dasha in dasha_list:
            start_str = jd_to_date_str(dasha['start_jd'])
            end_str = jd_to_date_str(dasha['end_jd'])
            duration = f"{dasha['duration_days']/365.25:.2f} yrs"

            item = QTreeWidgetItem([
                str(dasha['planet']),
                start_str,
                end_str,
                duration
            ])

            tree.addTopLevelItem(item)

    
    def calculate_strength_tab(self):
        if not hasattr(self, 'current_astro_data'): return
        results = self.current_astro_data
        positions = results['positions']
        div_dignities = results.get('div_dignities', {})

        # 1. Fill Sthanabala Breakdown Table
        try:
            planets = ["सु", "चं", "मं", "बु", "गु", "शु", "श", "रा", "के"]
            self.sthana_table.setRowCount(0)
            
            for i, p in enumerate(planets):
                if p not in positions: continue
                
                # We call your function here
                # Note: You'll need to make sure the helper functions 
                # (calculate_uchcha_bala, etc.) are also imported/available
                total_sthana = calculate_sthanabala(p, positions[p], div_dignities, positions)
                
                # To show individual components, you might need to modify 
                # calculate_sthanabala to return a dictionary, 
                # but for now, we will show the result.
                self.sthana_table.insertRow(i)
                self.sthana_table.setItem(i, 0, QTableWidgetItem(p))
                # (Assuming you want to see the total for now, or you can 
                #  extract parts if your function returns them)
                self.sthana_table.setItem(i, 6, QTableWidgetItem(str(total_sthana)))
            for i, p in enumerate(planets):
                if p not in positions: continue
                deg = positions[p]
                
                # We calculate components manually to fill columns
                uchcha = calculate_uchcha_bala(p, deg)
                # Use your existing logic for others
                sapta = calculate_saptavargaja_bala(p, div_dignities.get(p, {})) if p not in ["रा", "के"] else 15.0
                
                # Oja-Yugma Logic
                sign = int(deg // 30) + 1
                is_even = sign in [2, 4, 6, 8, 10, 12]
                oja = 15.0 if ((p in ["चं", "शु"] and is_even) or (p in ["सु", "मं", "बु", "गु", "श"] and not is_even)) else 0.0
                
                dig = calculate_dig_bala(p, get_house_number(deg, positions['Asc']), positions)
                
                # Kendradi
                h = (int(deg // 30) - int(positions['Asc'] // 30)) % 12 + 1
                kendradi = 60.0 if h in [1, 4, 7, 10] else (30.0 if h in [2, 5, 8, 11] else 15.0)
                
                total = uchcha + sapta + oja + dig + kendradi

                # Fill columns 0 to 6
                self.sthana_table.setItem(i, 0, QTableWidgetItem(p))
                self.sthana_table.setItem(i, 1, QTableWidgetItem(f"{uchcha:.2f}"))
                self.sthana_table.setItem(i, 2, QTableWidgetItem(f"{sapta:.2f}"))
                self.sthana_table.setItem(i, 3, QTableWidgetItem(f"{oja:.2f}"))
                self.sthana_table.setItem(i, 4, QTableWidgetItem(f"{dig:.2f}"))
                self.sthana_table.setItem(i, 5, QTableWidgetItem(f"{kendradi:.2f}"))
                self.sthana_table.setItem(i, 6, QTableWidgetItem(f"{total:.2f}"))    
        except Exception as e:
            print(f"Sthanabala Table Error: {e}")

        # ... (keep the existing Karaka and Shadbala code below this) ...
        try:
            from strength import calculate_strengths
            table_data, _ = calculate_strengths(results['jd'], positions, results.get('speeds',{}), {}, {}, True)
            self.strength_table.setRowCount(0)
            for r_idx, r_data in enumerate(table_data):
                self.strength_table.insertRow(r_idx)
                for c_idx, val in enumerate(r_data):
                    self.strength_table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))
        except Exception as e: print(f"Shadbala Error: {e}")

        # 2. Fill Chara Karakas
        # --- PART 3: Chara Karakas (Strictly using your function output) ---
        # --- PART 3: Chara Karakas (Brute Force Fix) ---
        try:
            # 1. Clear the table first
            self.karaka_table.setRowCount(0)
            
            # 2. Get the data
            karaka_list = get_karaka_info(positions, include_nodes=True, include_eighth_karaka=True)
            
            # DEBUG PRINT: Look at your terminal/console to see if this triggers
            print(f"DEBUG: Karaka list length is {len(karaka_list) if karaka_list else 0}")

            if not karaka_list or len(karaka_list) == 0:
                # If list is empty, let's try to manually call identify_karakas
                print("DEBUG: List empty, trying manual fallback...")
                manual_karakas = get_karaka_info(positions, include_nodes=True)
                karaka_list = []
                for k_name, p_code in manual_karakas.items():
                    karaka_list.append({"Karaka": k_name, "Planet": p_code, "Position": ""})

            # 3. Force Row Count
            self.karaka_table.setRowCount(len(karaka_list))
            
            for row, info in enumerate(karaka_list):
                # We use .get() with a default string to prevent crashes
                k_name = str(info.get("Karaka", "N/A"))
                p_name = str(info.get("Planet", "N/A"))
                p_pos  = str(info.get("Position", ""))

                # Set Table Items directly
                self.karaka_table.setItem(row, 0, QTableWidgetItem(k_name))
                self.karaka_table.setItem(row, 1, QTableWidgetItem(p_name))
                
                # Handling Position Split
                if "(" in p_pos:
                    # e.g., "Aquarius (2.60°)" -> ["Aquarius ", "2.60°)"]
                    parts = p_pos.split("(")
                    sign_val = parts[0].strip()
                    deg_val = parts[1].replace(")", "").strip()
                    self.karaka_table.setItem(row, 2, QTableWidgetItem(deg_val))
                    self.karaka_table.setItem(row, 3, QTableWidgetItem(sign_val))
                else:
                    # If position is empty, we calculate it from positions dict manually
                    p_code = info.get("Planet", "")
                    if p_code in positions:
                        deg = positions[p_code]
                        self.karaka_table.setItem(row, 2, QTableWidgetItem(f"{deg % 30:.2f}°"))
                        self.karaka_table.setItem(row, 3, QTableWidgetItem(RASI_SIGNS[int(deg//30)]))
                    else:
                        self.karaka_table.setItem(row, 3, QTableWidgetItem(p_pos))

            self.karaka_table.resizeColumnsToContents()
            print("DEBUG: Karaka table fill complete.")

        except Exception as e:
            print(f"CRITICAL ERROR in Karaka Table: {e}")

        # 3. Fill Ashtakavarga (Visualizing numbers)
        # Inside calculate_strength_tab, where you do Ashtakavarga:
        self.clear_layout(self.av_container)
        av_results = calculate_ashtakavarga(positions)
        
        row, col = 0, 0
        for p_name, scores in av_results.items():
            chart = AVChartWidget(p_name, scores)
            self.av_container.addWidget(chart, row, col)
            col += 1
            if col > 3: 
                col = 0; row += 1
    def create_gochar_view(self):
        """Create transit/Gochar view with charts, tables, and panchang"""
        view = QWidget()
        main_layout = QVBoxLayout(view)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Gochar (Transit) Analysis")
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 10px;
            background-color: #1a1a1a;
            border-radius: 8px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Top section: Moon Phase and Current Transit Info
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setSpacing(15)
        
        # Moon Phase Image (Left)
        self.gochar_moon_frame = QFrame()
        self.gochar_moon_frame.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 10px;
            border: 2px solid #3d3d3d;
        """)
        self.gochar_moon_frame.setFixedWidth(180)
        moon_layout = QVBoxLayout(self.gochar_moon_frame)
        moon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        moon_layout.setContentsMargins(15, 15, 15, 15)
        
        self.gochar_moon_label = QLabel()
        self.gochar_moon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gochar_moon_label.setFixedSize(120, 120)
        moon_layout.addWidget(self.gochar_moon_label)
        
        self.gochar_moon_phase_text = QLabel("Moon Phase: --")
        self.gochar_moon_phase_text.setStyleSheet("""
            color: #ffffff; 
            font-weight: bold;
            font-size: 12px;
            padding: 5px;
        """)
        self.gochar_moon_phase_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        moon_layout.addWidget(self.gochar_moon_phase_text)
        
        top_layout.addWidget(self.gochar_moon_frame)
        
        # Transit Summary Table (Right) - FIXED SCROLLING ISSUE
        self.gochar_summary_table = QTableWidget()
        self.gochar_summary_table.setColumnCount(6)
        self.gochar_summary_table.setHorizontalHeaderLabels([
            "Planet", 
            "Degree", 
            "Rashi", 
            "Retrograde", 
            "Combustion", 
            "Status"
        ])
        self.gochar_summary_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 8px;
                border: 2px solid #3d3d3d;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 10px;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                font-size: 13px;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
            }
        """)
        
        # FIX: Proper sizing to avoid unnecessary scroll
        self.gochar_summary_table.verticalHeader().setVisible(False)
        self.gochar_summary_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.gochar_summary_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        
        header = self.gochar_summary_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Planet
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Degree
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Rashi
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Retro
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Combust
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Status

        # FIX: Set proper height based on content
        self.gochar_summary_table.setMinimumHeight(250)
        self.gochar_summary_table.setMaximumHeight(350)
        
        self.gochar_summary_table.setWordWrap(True)
        top_layout.addWidget(self.gochar_summary_table, stretch=2)
        
        main_layout.addWidget(top_widget)
        
        # Middle section: D1 Transit Chart and D9 Transit Chart side by side
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.setSpacing(15)
        
        # D1 Transit Chart - FIXED STRETCHING
        d1_frame = QFrame()
        d1_frame.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 10px;
            border: 2px solid #3d3d3d;
        """)
        d1_layout = QVBoxLayout(d1_frame)
        d1_layout.setContentsMargins(15, 15, 15, 15)
        
        d1_title = QLabel("D1 Transit Chart")
        d1_title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 8px;
            background-color: #1a1a1a;
            border-radius: 5px;
        """)
        d1_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d1_layout.addWidget(d1_title)
        
        # FIX: Proper chart sizing with aspect ratio
        self.gochar_d1_chart = NorthChartWidget({}, [1,2,3,4,5,6,7,8,9,10,11,12], "D1 Gochar")
        self.gochar_d1_chart.setMinimumSize(350, 350)
        self.gochar_d1_chart.setMaximumSize(500, 500)
        # Keep aspect ratio
        self.gochar_d1_chart.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        d1_layout.addWidget(self.gochar_d1_chart, alignment=Qt.AlignmentFlag.AlignCenter)
        
        charts_layout.addWidget(d1_frame)
        
        # D9 Transit Chart - FIXED STRETCHING
        d9_frame = QFrame()
        d9_frame.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 10px;
            border: 2px solid #3d3d3d;
        """)
        d9_layout = QVBoxLayout(d9_frame)
        d9_layout.setContentsMargins(15, 15, 15, 15)
        
        d9_title = QLabel("D9 Transit Chart")
        d9_title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 8px;
            background-color: #1a1a1a;
            border-radius: 5px;
        """)
        d9_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d9_layout.addWidget(d9_title)
        
        # FIX: Proper chart sizing with aspect ratio
        self.gochar_d9_chart = NorthChartWidget({}, [1,2,3,4,5,6,7,8,9,10,11,12], "D9 Gochar")
        self.gochar_d9_chart.setMinimumSize(350, 350)
        self.gochar_d9_chart.setMaximumSize(500, 500)
        # Keep aspect ratio
        self.gochar_d9_chart.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        d9_layout.addWidget(self.gochar_d9_chart, alignment=Qt.AlignmentFlag.AlignCenter)
        
        charts_layout.addWidget(d9_frame)
        
        main_layout.addWidget(charts_widget)
        
        # Bottom section: Upagrahas and Rashi Changes (side by side)
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setSpacing(15)
        
        # Upagraha Table - FIXED SCROLLING
        upagraha_frame = QFrame()
        upagraha_frame.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 10px;
            border: 2px solid #3d3d3d;
        """)
        upagraha_layout = QVBoxLayout(upagraha_frame)
        upagraha_layout.setContentsMargins(15, 15, 15, 15)
        
        upagraha_title = QLabel("Upagrahas (Transit)")
        upagraha_title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 8px;
            background-color: #1a1a1a;
            border-radius: 5px;
        """)
        upagraha_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upagraha_layout.addWidget(upagraha_title)
        
        self.gochar_upagraha_table = QTableWidget()
        self.gochar_upagraha_table.setColumnCount(5)
        self.gochar_upagraha_table.setHorizontalHeaderLabels(["Upagraha", "Degree", "Rashi", "Nakshatra", "Pada"])
        self.gochar_upagraha_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 8px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 10px;
                font-weight: bold;
                border: 1px solid #3d3d3d;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
            }
        """)
        
        # FIX: Proper sizing
        self.gochar_upagraha_table.verticalHeader().setVisible(False)
        self.gochar_upagraha_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.gochar_upagraha_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.gochar_upagraha_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gochar_upagraha_table.setMinimumHeight(200)
        self.gochar_upagraha_table.setMaximumHeight(300)
        
        upagraha_layout.addWidget(self.gochar_upagraha_table)
        bottom_layout.addWidget(upagraha_frame)
        
        # Rashi Change Predictions Table - FIXED SCROLLING
        rashi_change_frame = QFrame()
        rashi_change_frame.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 10px;
            border: 2px solid #3d3d3d;
        """)
        rashi_change_layout = QVBoxLayout(rashi_change_frame)
        rashi_change_layout.setContentsMargins(15, 15, 15, 15)
        
        rashi_change_title = QLabel("Upcoming Rashi Changes (Next 365 Days)")
        rashi_change_title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 8px;
            background-color: #1a1a1a;
            border-radius: 5px;
        """)
        rashi_change_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rashi_change_layout.addWidget(rashi_change_title)
        
        self.gochar_rashi_change_table = QTableWidget()
        self.gochar_rashi_change_table.setColumnCount(3)
        self.gochar_rashi_change_table.setHorizontalHeaderLabels(["Planet", "Entering Rashi", "Date of Change"])
        self.gochar_rashi_change_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 8px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 10px;
                font-weight: bold;
                border: 1px solid #3d3d3d;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
            }
        """)
        
        # FIX: Proper sizing
        self.gochar_rashi_change_table.verticalHeader().setVisible(False)
        self.gochar_rashi_change_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.gochar_rashi_change_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.gochar_rashi_change_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gochar_rashi_change_table.setMinimumHeight(200)
        self.gochar_rashi_change_table.setMaximumHeight(300)
        
        rashi_change_layout.addWidget(self.gochar_rashi_change_table)
        bottom_layout.addWidget(rashi_change_frame)
        
        main_layout.addWidget(bottom_widget)
        
        # Panchang Details Section - FIXED SCROLLING
        panchang_frame = QFrame()
        panchang_frame.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 10px;
            border: 2px solid #3d3d3d;
        """)
        panchang_layout = QVBoxLayout(panchang_frame)
        panchang_layout.setContentsMargins(15, 15, 15, 15)
        
        panchang_title = QLabel("Panchang Details (Transit Time)")
        panchang_title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #ffffff;
            padding: 8px;
            background-color: #1a1a1a;
            border-radius: 5px;
        """)
        panchang_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panchang_layout.addWidget(panchang_title)
        
        self.gochar_panchang_table = QTableWidget()
        self.gochar_panchang_table.setColumnCount(2)
        self.gochar_panchang_table.setHorizontalHeaderLabels(["Element", "Value"])
        self.gochar_panchang_table.setStyleSheet("""
            QTableWidget {
                background-color: #2a2a2a;
                color: #ffffff;
                border-radius: 8px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #1a1a1a;
                color: #ffffff;
                padding: 10px;
                font-weight: bold;
                border: 1px solid #3d3d3d;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                border-radius: 6px;
            }
        """)
        
        # FIX: Proper sizing
        self.gochar_panchang_table.verticalHeader().setVisible(False)
        self.gochar_panchang_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.gochar_panchang_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.gochar_panchang_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.gochar_panchang_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.gochar_panchang_table.setColumnWidth(0, 200)
        self.gochar_panchang_table.setMinimumHeight(200)
        self.gochar_panchang_table.setMaximumHeight(300)
        
        panchang_layout.addWidget(self.gochar_panchang_table)
        main_layout.addWidget(panchang_frame)
        
        # Calculate button
        self.gochar_calc_btn = QPushButton("Calculate Current Transit")
        self.gochar_calc_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: #ffffff;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.gochar_calc_btn.setFixedHeight(45)
        self.gochar_calc_btn.clicked.connect(self.calculate_gochar)
        main_layout.addWidget(self.gochar_calc_btn)
        
        return view
    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
    def calculate_yogas(self):
        if not hasattr(self, 'current_astro_data'): return
        
        results = self.current_astro_data
        positions = results['positions']
        
        # Extract required data (ensure these keys exist in your current_astro_data)
        d9_data = results.get('d9_positions', {})
        house_lords = results.get('house_lords', {})
        div_dignities = results.get('div_dignities', {})
        
        # 1. Get the list from our cleaned function
        # Note: Make sure to import get_detected_yogas_list from yogasf
        yoga_list = get_detected_yogas_list(
            positions, 
            house_lords, 
            positions.get("Asc", 0),
            d9_data,
            d9_data.get("Asc", 0),
            results['jd'],
            div_dignities
        )

        # 2. Fill the Table
        self.yoga_table.setRowCount(0)
        if not yoga_list:
            self.yoga_table.setRowCount(1)
            self.yoga_table.setItem(0, 1, QTableWidgetItem("No significant yogas found"))
            return

        for row, yoga in enumerate(yoga_list):
            self.yoga_table.insertRow(row)
            
            # Yoga Name
            name_item = QTableWidgetItem(yoga['name'])
            name_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            
            # Combined Description and Conditions
            desc_text = f"{yoga['description']}\n\n{yoga['details']}"
            desc_item = QTableWidgetItem(desc_text)
            
            # Strength
            strength_item = QTableWidgetItem(yoga['strength'])
            
            self.yoga_table.setItem(row, 0, name_item)
            self.yoga_table.setItem(row, 1, desc_item)
            self.yoga_table.setItem(row, 2, strength_item)
            
            # Allow the row to wrap text
            self.yoga_table.resizeRowToContents(row)
    def _calculate_retrograde_end(self, jd_start, planet_pid, lat, lon, ayanamsa_type, days_limit=90):
        """Calculate when a planet becomes direct (speed changes from negative to positive)"""
        try:
            from astropy.time import Time
            from utils import get_ayanamsa
            
            flags = swe.FLG_SWIEPH | swe.FLG_SPEED
            
            # Check if currently retrograde
            initial_speed = swe.calc_ut(jd_start, planet_pid, flags)[0][3]
            if initial_speed >= 0:
                return None  # Already direct
            
            for day in range(1, days_limit + 1):
                jd_check = jd_start + day
                speed = swe.calc_ut(jd_check, planet_pid, flags)[0][3]
                
                if speed >= 0:  # Planet is now direct or stationary
                    # Binary search for exact moment
                    jd_low = jd_check - 1
                    jd_high = jd_check
                    for _ in range(25):  # High precision
                        jd_mid = (jd_low + jd_high) / 2
                        speed_mid = swe.calc_ut(jd_mid, planet_pid, flags)[0][3]
                        if speed_mid < 0:
                            jd_low = jd_mid
                        else:
                            jd_high = jd_mid
                        if jd_high - jd_low < 1e-7:
                            break
                    
                    t = Time(jd_high, format='jd', scale='utc')
                    return t.datetime.strftime("%d-%m-%Y")
            
            return f">{days_limit} days"  # Not found within limit
            
        except Exception as e:
            return None


    def _calculate_combustion_end(self, jd_start, planet_pid, sun_pid, lat, lon, ayanamsa_type, days_limit=90):
        """Calculate when a planet moves out of combustion orb from Sun"""
        try:
            from astropy.time import Time
            from utils import get_ayanamsa
            
            flags = swe.FLG_SWIEPH
            
            # Get ayanamsa for sidereal calculation
            ayan_deg = get_ayanamsa(jd_start, ayanamsa_type)
            
            # Check if currently combust using SIDEREAL positions
            sun_pos_tropical = swe.calc_ut(jd_start, sun_pid, flags)[0][0]
            planet_pos_tropical = swe.calc_ut(jd_start, planet_pid, flags)[0][0]
            
            # Convert to sidereal
            sun_pos_sidereal = (sun_pos_tropical - ayan_deg) % 360
            planet_pos_sidereal = (planet_pos_tropical - ayan_deg) % 360
            
            # Calculate angular distance (shortest path)
            diff = abs(planet_pos_sidereal - sun_pos_sidereal) % 360
            dist = min(diff, 360 - diff)
            
            # Combustion orbs: Venus/Shukra = 8-10°, Mercury/Budh = 8-12°, others = 6°
            planet_orbs = {
                swe.MERCURY: 10,  # Budh
                swe.VENUS: 8,     # Shukra (currently 8-10 degrees)
                swe.MARS: 6,
                swe.JUPITER: 6,
                swe.SATURN: 6,
                swe.MOON: 12      # Chandra
            }
            combust_orb = planet_orbs.get(planet_pid, 6)
            
            if dist >= combust_orb:
                return None  # Not combust
            
            # Search for when it clears the orb
            for day in range(1, days_limit + 1):
                jd_check = jd_start + day
                
                ayan_check = get_ayanamsa(jd_check, ayanamsa_type)
                sun_tropical = swe.calc_ut(jd_check, sun_pid, flags)[0][0]
                planet_tropical = swe.calc_ut(jd_check, planet_pid, flags)[0][0]
                
                sun_sidereal = (sun_tropical - ayan_check) % 360
                planet_sidereal = (planet_tropical - ayan_check) % 360
                
                diff = abs(planet_sidereal - sun_sidereal) % 360
                angular_dist = min(diff, 360 - diff)
                
                if angular_dist >= combust_orb:  # Out of combustion
                    # Binary search for exact moment
                    jd_low = jd_check - 1
                    jd_high = jd_check
                    for _ in range(25):
                        jd_mid = (jd_low + jd_high) / 2
                        ayan_mid = get_ayanamsa(jd_mid, ayanamsa_type)
                        sun_mid = swe.calc_ut(jd_mid, sun_pid, flags)[0][0]
                        planet_mid = swe.calc_ut(jd_mid, planet_pid, flags)[0][0]
                        
                        sun_mid_sid = (sun_mid - ayan_mid) % 360
                        planet_mid_sid = (planet_mid - ayan_mid) % 360
                        
                        diff_mid = abs(planet_mid_sid - sun_mid_sid) % 360
                        dist_mid = min(diff_mid, 360 - diff_mid)
                        
                        if dist_mid < combust_orb:
                            jd_low = jd_mid
                        else:
                            jd_high = jd_mid
                        if jd_high - jd_low < 1e-4:
                            break
                    
                    t = Time(jd_high, format='jd', scale='utc')
                    return t.datetime.strftime("%d-%m-%Y")
            
            return f">{days_limit} days"
            
        except Exception as e:
            print(f"Error calculating combustion end: {e}")
            return None
    def calculate_gochar(self):
        """Calculate transit positions and update all Gochar view elements"""
        if not hasattr(self, 'current_astro_data') or not hasattr(self, 'birth_input_data'):
            QMessageBox.warning(self, "Error", "Please calculate birth chart first!")
            return
        def is_combust_now(planet_pid):
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
        
        try:
            # Import functions
            from gochar import (
                get_divisional_data_package,
                check_planet_rasi_changes,
                get_moon_phase_pixmap,
                make_chart_data,
                calculate_upagrahas,
                calculate_panchang
            )
            from utils import get_sidereal_positions, PLANETS, get_ayanamsa
            
            # Get birth location from stored input data
            birth_input = self.birth_input_data
            lat = float(birth_input['lat'])
            lon = float(birth_input['lon'])
            tz_name = birth_input['tz_name']
            ayanamsa_type = birth_input.get('ayanamsa', 'Lahiri')
            
            # Get current time for transit calculation
            current_dt = datetime.now()
            local_tz = pytz.timezone(tz_name)
            local_dt = local_tz.localize(current_dt)
            utc_dt = local_dt.astimezone(pytz.utc)
            
            # Convert to Julian Day
            jd = swe.julday(
                utc_dt.year, utc_dt.month, utc_dt.day,
                utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
            )
            
            # 1. Calculate Gochar positions
            positions, retro_flags, combust_flags, ayan_deg = get_sidereal_positions(jd, ayanamsa_type)
            
            # Add Ascendant for chart calculation
            house_result = swe.houses_ex(jd, lat, lon, b'W', flags=swe.FLG_SWIEPH)
            asc_tropical = house_result[1][0]
            asc_sidereal = (asc_tropical - ayan_deg) % 360
            positions['Asc'] = asc_sidereal
            
            # Calculate Moon phase
            sun_lon = positions['सु']
            moon_lon = positions['चं']
            phase_angle = (moon_lon - sun_lon) % 360
            
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
            
            # 2. Update Moon Phase Image
            pixmap = get_moon_phase_pixmap(moon_phase, size=(100, 100))
            if pixmap and not pixmap.isNull():
                self.gochar_moon_label.setPixmap(pixmap)
            else:
                self.gochar_moon_label.setText("🌙")
            self.gochar_moon_phase_text.setText(f"Moon Phase: {moon_phase}")
            
            # 3. Build planet data with retrograde and combustion end dates
            planet_table_data = []
            rashi_names_list = ["मेष", "वृष", "मिथुन", "कर्क", "सिंह", "कन्या", 
                            "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"]
            
            planet_name_map = {
                'सु': 'Sun (सूर्य)', 'चं': 'Moon (चंद्र)', 'मं': 'Mars (मंगल)',
                'बु': 'Mercury (बुध)', 'गु': 'Jupiter (गुरु)', 'शु': 'Venus (शुक्र)',
                'श': 'Saturn (शनि)', 'रा': 'Rahu (राहु)', 'के': 'Ketu (केतु)'
            }
            
            # Planet ID mapping for swe calculations
            planet_id_map = {
                'सु': swe.SUN, 'चं': swe.MOON, 'मं': swe.MARS,
                'बु': swe.MERCURY, 'गु': swe.JUPITER, 'शु': swe.VENUS,
                'श': swe.SATURN, 'रा': swe.MEAN_NODE, 'के': swe.TRUE_NODE
            }
            
            for planet, degree in positions.items():
                if planet == 'Asc':
                    continue
                
                rashi_num = int(degree // 30) % 12
                is_retro = retro_flags.get(planet, False)
                if planet in ['रा', 'के']:
                    is_retro = False
                is_combust = is_combust_now(planet_id_map[planet])
                if planet == 'सु':
                    is_combust = False
                degree_in_rashi = degree % 30
                
                # Calculate retrograde end date if retrograde
                retro_end_date = None
                if is_retro and planet in planet_id_map:
                    retro_end_date = self._calculate_retrograde_end(jd, planet_id_map[planet], lat, lon, ayanamsa_type)
                
                # Calculate combustion end date if combust (skip Sun, Rahu, Ketu)
                combust_end_date = None
                if is_combust and planet in planet_id_map and planet not in ['सु', 'रा', 'के']:
                    combust_end_date = self._calculate_combustion_end(
                        jd, planet_id_map[planet], swe.SUN, lat, lon, ayanamsa_type
                    )
                
                planet_table_data.append({
                    'planet': planet,
                    'full_degree': degree,
                    'degree_in_rashi': degree_in_rashi,
                    'rashi_num': rashi_num,
                    'is_retro': is_retro,
                    'is_combust': is_combust,
                    'retro_end_date': retro_end_date,
                    'combust_end_date': combust_end_date
                })
            
            # 4. Update Transit Summary Table with 6 columns
            self.gochar_summary_table.setRowCount(len(planet_table_data))
            
            for idx, pdata in enumerate(planet_table_data):
                # Column 0: Planet name
                name_item = QTableWidgetItem(planet_name_map.get(pdata['planet'], pdata['planet']))
                name_item.setForeground(QColor("white"))
                self.gochar_summary_table.setItem(idx, 0, name_item)
                
                # Column 1: Degree in Rashi
                degree_text = f"{pdata['degree_in_rashi']:.2f}°"
                degree_item = QTableWidgetItem(degree_text)
                degree_item.setForeground(QColor("#87CEEB"))  # Light blue
                self.gochar_summary_table.setItem(idx, 1, degree_item)
                
                # Column 2: Rashi
                rashi_name = rashi_names_list[pdata['rashi_num']]
                rashi_item = QTableWidgetItem(f"{rashi_name} ({pdata['rashi_num'] + 1})")
                rashi_item.setForeground(QColor("white"))
                self.gochar_summary_table.setItem(idx, 2, rashi_item)
                
                # Column 3: Retrograde with end date
                if pdata['is_retro']:
                    if pdata['retro_end_date']:
                        retro_text = f"Yes ®\nDirect: {pdata['retro_end_date']}"
                    else:
                        retro_text = "Yes ®"
                    retro_color = "red"
                else:
                    retro_text = "Direct"
                    retro_color = "green"
                retro_item = QTableWidgetItem(retro_text)
                retro_item.setForeground(QColor(retro_color))
                self.gochar_summary_table.setItem(idx, 3, retro_item)
                
                # Column 4: Combustion with end date
                if pdata['is_combust']:
                    if pdata['combust_end_date']:
                        combust_text = f"Yes ©\nClear: {pdata['combust_end_date']}"
                    else:
                        combust_text = "Yes ©"
                    combust_color = "orange"
                else:
                    combust_text = "No"
                    combust_color = "white"
                combust_item = QTableWidgetItem(combust_text)
                combust_item.setForeground(QColor(combust_color))
                self.gochar_summary_table.setItem(idx, 4, combust_item)
                
                # Column 5: Overall Status
                status_parts = []
                if pdata['is_retro']:
                    status_parts.append("Retrograde")
                if pdata['is_combust']:
                    status_parts.append("Combust")
                if not status_parts:
                    status_parts.append("Normal")
                
                status_text = " + ".join(status_parts)
                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(QColor("white"))
                self.gochar_summary_table.setItem(idx, 5, status_item)
            self.gochar_summary_table.resizeRowsToContents()
            # 5. Calculate and Update D1 Transit Chart
            asc_sign = int(positions['Asc'] // 30)
            d1_chart_data = make_chart_data(positions, 1, asc_sign, retro_flags, combust_flags)
            d1_rashi_numbers = [(asc_sign + i) % 12 + 1 for i in range(12)]
            
            self.gochar_d1_chart.chart_data = d1_chart_data
            self.gochar_d1_chart.rashi_numbers = d1_rashi_numbers
            self.gochar_d1_chart.chart_title = "D1 Transit Chart"
            self.gochar_d1_chart.update()
            
            # 6. Calculate and Update D9 Transit Chart
            d9_chart_data, d9_rashi_numbers, d9_title = get_divisional_data_package(
                "D9", positions, retro_flags, combust_flags
            )
            
            self.gochar_d9_chart.chart_data = d9_chart_data
            self.gochar_d9_chart.rashi_numbers = d9_rashi_numbers
            self.gochar_d9_chart.chart_title = "D9 Transit Chart"
            self.gochar_d9_chart.update()
            
            # 7. Calculate Upagrahas
            panchang_result = calculate_panchang(jd, lat, lon, tz_name, positions)
            
            if panchang_result['status'] == 'success':
                panchang_data = panchang_result['data']
                
                transit_for_upagraha = {
                    "datetime": local_dt,
                    "sunrise": panchang_data.get('sunrise', '06:00:00'),
                    "sunset": panchang_data.get('sunset', '18:00:00'),
                    "planet_positions": positions,
                    "lat": lat,
                    "lon": lon,
                    "tz_name": tz_name
                }
                
                upagraha_results = calculate_upagrahas(transit_for_upagraha, ayanamsa_type)
                
                self.gochar_upagraha_table.setRowCount(len(upagraha_results))
                upagraha_name_map = {
                    'गु': 'Gulika', 'य': 'Yamaghantaka', 'का': 'Kala',
                    'मृ': 'Mrityu', 'अ': 'Ardhaprahara', 'धु': 'Dhuma',
                    'व्या': 'Vyatipata', 'प': 'Parivesha', 'इ': 'Indrachapa', 'उ': 'Upaketu'
                }
                
                for idx, (symbol, data) in enumerate(upagraha_results.items()):
                    name_item = QTableWidgetItem(f"{upagraha_name_map.get(symbol, symbol)} ({symbol})")
                    name_item.setForeground(QColor("white"))
                    self.gochar_upagraha_table.setItem(idx, 0, name_item)
                    
                    deg_item = QTableWidgetItem(f"{data['degree']:.2f}°")
                    deg_item.setForeground(QColor("white"))
                    self.gochar_upagraha_table.setItem(idx, 1, deg_item)
                    
                    rashi_item = QTableWidgetItem(data['rasi'])
                    rashi_item.setForeground(QColor("white"))
                    self.gochar_upagraha_table.setItem(idx, 2, rashi_item)
                    
                    nak_item = QTableWidgetItem(data['nakshatra'])
                    nak_item.setForeground(QColor("white"))
                    self.gochar_upagraha_table.setItem(idx, 3, nak_item)
                    
                    pada_item = QTableWidgetItem(str(data['pada']))
                    pada_item.setForeground(QColor("white"))
                    self.gochar_upagraha_table.setItem(idx, 4, pada_item)
            
            # 8. Calculate Rashi Changes
            rashi_changes = check_planet_rasi_changes(jd, lat, lon, days=365, ayanamsa_type=ayanamsa_type)
            
            self.gochar_rashi_change_table.setRowCount(len(rashi_changes))
            row = 0
            for planet, change_info in rashi_changes.items():
                planet_display = planet_name_map.get(planet, planet)
                planet_item = QTableWidgetItem(planet_display)
                planet_item.setForeground(QColor("white"))
                self.gochar_rashi_change_table.setItem(row, 0, planet_item)
                
                new_rashi_num = change_info['new_rasi'] - 1
                new_rashi_name = rashi_names_list[new_rashi_num]
                rashi_item = QTableWidgetItem(f"{new_rashi_name} ({change_info['new_rasi']})")
                rashi_item.setForeground(QColor("#4CAF50"))
                self.gochar_rashi_change_table.setItem(row, 1, rashi_item)
                
                date_item = QTableWidgetItem(change_info['change_date'])
                date_item.setForeground(QColor("white"))
                self.gochar_rashi_change_table.setItem(row, 2, date_item)
                
                row += 1
            
            # 9. Update Panchang Table
            if panchang_result['status'] == 'success':
                p_data = panchang_result['data']
                panchang_items = [
                    ("Tithi", p_data.get('tithi', '--')),
                    ("Nakshatra", p_data.get('nakshatra', '--')),
                    ("Yoga", p_data.get('yoga', '--')),
                    ("Karana", p_data.get('karana', '--')),
                    ("Weekday", p_data.get('weekday', '--')),
                    ("Sunrise", p_data.get('sunrise', '--')),
                    ("Sunset", p_data.get('sunset', '--')),
                    ("Nadi", p_data.get('nadi', '--')),
                    ("Gana", p_data.get('gana', '--')),
                    ("Yoni", p_data.get('yoni', '--')),
                    ("Varna", p_data.get('varna', '--')),
                    ("Lunar Month", f"{p_data.get('lunar_month', '--')} {p_data.get('lunar_year', '')}"),
                    ("Naam Akshar", p_data.get('naam_akshar', '--'))
                ]
                
                self.gochar_panchang_table.setRowCount(len(panchang_items))
                for idx, (element, value) in enumerate(panchang_items):
                    elem_item = QTableWidgetItem(element)
                    elem_item.setForeground(QColor("#FFD700"))
                    elem_item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                    self.gochar_panchang_table.setItem(idx, 0, elem_item)
                    
                    val_item = QTableWidgetItem(str(value))
                    val_item.setForeground(QColor("white"))
                    self.gochar_panchang_table.setItem(idx, 1, val_item)
            
            QMessageBox.information(self, "Success", "Transit/Gochar calculation completed!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to calculate Gochar: {str(e)}")
            import traceback
            traceback.print_exc()
    def run_calculation(self):
        time_parts = self.time_input.text().split(':')
        while len(time_parts) < 3:
            time_parts.append("00")
        input_data = {
            'name': self.name_input.text(),
            'lat': float(self.lat_input.text()),
            'lon': float(self.lon_input.text()),
            'date': self.date_input.text(),
            'hour': time_parts[0],
            'minute': time_parts[1],
            'second': time_parts[2],
            'ampm': self.ampm_combo.currentText(),
            'tz_name': self.tz_combo.currentText(),
            'ayanamsa': self.ayanamsa_combo.currentText()
        }

        try:
            results = calculate_lmt_and_charts_logic(input_data)
            
            # Store both results AND original input
            self.current_astro_data = results
            self.birth_input_data = input_data  # <-- ADD THIS LINE
            
            self.display_results(results)
        except Exception as e:
            print(f"Error in calculation: {e}")
            import traceback
            traceback.print_exc()

    def create_panchang_widget(self, data):
        """Create a widget to display Panchang details"""
        panchang_frame = QFrame()
        panchang_frame.setFrameShape(QFrame.Shape.Box)
        panchang_frame.setMaximumWidth(250)
        panchang_layout = QVBoxLayout(panchang_frame)
        
        title_label = QLabel("पञ्चाङ्ग विवरण")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panchang_layout.addWidget(title_label)
        
        panchang = data.get('panchang', {})
        panchang_data = panchang.get('data', {})
        
        elements = [
            ("तिथि:", panchang_data.get('tithi', 'N/A')),
            ("नक्षत्र:", panchang_data.get('nakshatra', 'N/A')),
            ("योग:", panchang_data.get('yoga', 'N/A')),
            ("करण:", panchang_data.get('karana', 'N/A')),
            ("वार:", panchang_data.get('weekday', 'N/A')),
            ("सूर्योदय:", panchang_data.get('sunrise', 'N/A')),
            ("सूर्यास्त:", panchang_data.get('sunset', 'N/A')),
            ("नाडी:", panchang_data.get('nadi', 'N/A')),
            ("गण:", panchang_data.get('gana', 'N/A')),
            ("योनी:", panchang_data.get('yoni', 'N/A')),
            ("वर्ण:", panchang_data.get('varna', 'N/A')),
            ("नामाक्षर:", panchang_data.get('naam_akshar','N/A'))
        ]
        
        for label_text, value in elements:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet("font-weight: bold;")
            value_label = QLabel(str(value))
            row_layout.addWidget(label)
            row_layout.addWidget(value_label)
            row_layout.addStretch()
            panchang_layout.addLayout(row_layout)
        
        panchang_layout.addStretch()
        return panchang_frame
    def create_arudha_widget(self, data):
        """Create a widget to display Arudha (Pada) details"""
        arudha_frame = QFrame()
        arudha_frame.setFrameShape(QFrame.Shape.Box)
        arudha_frame.setMaximumWidth(250)
        arudha_layout = QVBoxLayout(arudha_frame)
        
        title_label = QLabel("Arudha Details")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arudha_layout.addWidget(title_label)
        
        # Calculate Arudhas
        arudhas = calculate_arudha_positions(data['positions'], data['rashi_numbers'])
        
        # Create table for Arudhas
        arudha_table = QTableWidget()
        arudha_table.setColumnCount(5)
        arudha_table.setHorizontalHeaderLabels(["Arudha", "Degree", "Rashi", "Nakshatra", "Pada"])
        
        row = 0
        # Sort by A1, A2, A3... order
        sorted_keys = sorted(arudhas.keys(), key=lambda x: int(x.split()[0][1:].split('(')[0]))
        
        for key in sorted_keys:
            meta = arudhas[key]
            arudha_table.insertRow(row)
            
            # Format degree in DMS
            degree_in_rashi = meta.get('degree', 0)
            d = int(degree_in_rashi)
            m = int((degree_in_rashi - d) * 60)
            s = int(((degree_in_rashi - d) * 60 - m) * 60)
            deg_str = f"{d}° {m}' {s}\""
            
            arudha_table.setItem(row, 0, QTableWidgetItem(str(key)))
            arudha_table.setItem(row, 1, QTableWidgetItem(deg_str))
            arudha_table.setItem(row, 2, QTableWidgetItem(meta.get('rasi', 'N/A')))
            arudha_table.setItem(row, 3, QTableWidgetItem(meta.get('nakshatra', 'N/A')))
            arudha_table.setItem(row, 4, QTableWidgetItem(str(meta.get('pada', 'N/A'))))
            row += 1
        
        arudha_table.resizeColumnsToContents()
        arudha_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        arudha_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        arudha_table.setMaximumWidth(arudha_table.horizontalHeader().length() + 20)
        
        arudha_layout.addWidget(arudha_table)
        arudha_layout.addStretch()
        return arudha_frame
    def display_results(self, data):
        # Clear previous widgets - completely remove from layout and delete
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                
        while self.tables_layout.count():
            item = self.tables_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        # Inside AstrologyApp.initUI:
        self.current_pos = data['positions']
        self.current_retro = data['retro_flags']
        self.current_combust = data['combust_flags']
        self.tables_layout.setSpacing(40)
        pos = data['positions']
        retro = data['retro_flags']
        combust = data['combust_flags']
        
        # 2. D1 and D9 Charts (Fixed Widgets)
        d1_pkg = get_divisional_data_package("D1", pos, retro, combust)
        self.charts_layout.addWidget(NorthChartWidget(*d1_pkg))

        d9_pkg = get_divisional_data_package("D9", pos, retro, combust)
        self.charts_layout.addWidget(NorthChartWidget(*d9_pkg))

        # 3. Dynamic Chart (Defaults to D60)
        d60_pkg = get_divisional_data_package("D60", pos, retro, combust)
        self.dynamic_chart_widget = NorthChartWidget(*d60_pkg)
        self.charts_layout.addWidget(self.dynamic_chart_widget)
        self.division_selector.setCurrentText(DIVISION_NAMES[60])
        # 4. Handle Signal safely
        try: self.division_selector.currentIndexChanged.disconnect()
        except: pass
        self.division_selector.currentIndexChanged.connect(self.on_division_selector_changed)
        
        # Panchang Panel
        panchang_widget = self.create_panchang_widget(data)
        self.charts_layout.addWidget(panchang_widget)
        self.charts_layout.addStretch()
        
        # Planet Table - FIXED DEGREE DISPLAY
        planet_container = QWidget()
        planet_vbox = QVBoxLayout(planet_container)
        planet_vbox.setContentsMargins(0, 0, 0, 0)
        planet_vbox.setSpacing(2)
        
        planet_title = QLabel("Planets Details")
        planet_title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 2px;")
        planet_vbox.addWidget(planet_title)
        
        self.planet_table = QTableWidget()
        self.planet_table.setColumnCount(5)
        self.planet_table.setHorizontalHeaderLabels(["Planet", "Degree", "Rashi", "Nakshatra", "Pada"])
        
        row = 0
        if 'Asc' in pos:
            asc_deg = pos['Asc']
            self.planet_table.insertRow(row)
            self.planet_table.setItem(row, 0, QTableWidgetItem("Asc"))
            
            deg_in_sign = asc_deg % 30
            d = int(deg_in_sign)
            m = int((deg_in_sign - d) * 60)
            s = int(((deg_in_sign - d) * 60 - m) * 60)
            deg_str = f"{d}° {m}' {s}\""
            
            self.planet_table.setItem(row, 1, QTableWidgetItem(deg_str))
            self.planet_table.setItem(row, 2, QTableWidgetItem(get_rashi_from_degree(asc_deg)))
            self.planet_table.setItem(row, 3, QTableWidgetItem(get_nakshatra_from_degree(asc_deg)))
            self.planet_table.setItem(row, 4, QTableWidgetItem(str(get_pada_from_degree(asc_deg))))
            row += 1
        for p, deg in pos.items():
            if p == 'Asc':
                continue
                
            self.planet_table.insertRow(row)
            self.planet_table.setItem(row, 0, QTableWidgetItem(str(p)))
            
            # Show degree within sign (0-30) in DMS format
            deg_in_sign = deg % 30
            d = int(deg_in_sign)
            m = int((deg_in_sign - d) * 60)
            s = int(((deg_in_sign - d) * 60 - m) * 60)
            deg_str = f"{d}° {m}' {s}\""
            
            self.planet_table.setItem(row, 1, QTableWidgetItem(deg_str))
            self.planet_table.setItem(row, 2, QTableWidgetItem(get_rashi_from_degree(deg)))
            self.planet_table.setItem(row, 3, QTableWidgetItem(get_nakshatra_from_degree(deg)))
            self.planet_table.setItem(row, 4, QTableWidgetItem(str(get_pada_from_degree(deg))))
            row += 1
        self.planet_table.resizeColumnsToContents()
        self.planet_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.planet_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.planet_table.setMaximumWidth(self.planet_table.horizontalHeader().length() + 20)
        planet_vbox.addWidget(self.planet_table)
        self.tables_layout.addWidget(planet_container)
        
        # Upagraha Table - FIXED
        upagraha_container = QWidget()
        upagraha_vbox = QVBoxLayout(upagraha_container)
        upagraha_vbox.setContentsMargins(0, 0, 0, 0)
        upagraha_vbox.setSpacing(2)
        
        upagraha_title = QLabel("Upagraha Details")
        upagraha_title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 2px;")
        upagraha_vbox.addWidget(upagraha_title)
        
        self.up_table = QTableWidget()
        self.up_table.setColumnCount(5)
        self.up_table.setHorizontalHeaderLabels(["Upagraha", "Degree", "Rashi", "Nakshatra", "Pada"])
        
        row = 0
        for up, meta in data['upagrahas'].items():
            self.up_table.insertRow(row)
            
            # Use degree directly from meta (already 0-30)
            degree_in_rashi = meta.get('degree', 0)
            
            # Convert to DMS format
            d = int(degree_in_rashi)
            m = int((degree_in_rashi - d) * 60)
            s = int(((degree_in_rashi - d) * 60 - m) * 60)
            deg_str = f"{d}° {m}' {s}\""
            
            self.up_table.setItem(row, 0, QTableWidgetItem(str(up)))
            self.up_table.setItem(row, 1, QTableWidgetItem(deg_str))
            self.up_table.setItem(row, 2, QTableWidgetItem(meta.get('rasi', 'N/A')))
            self.up_table.setItem(row, 3, QTableWidgetItem(meta.get('nakshatra', 'N/A')))
            self.up_table.setItem(row, 4, QTableWidgetItem(str(meta.get('pada', 'N/A'))))
            row += 1
        self.up_table.resizeColumnsToContents()
        self.up_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.up_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.up_table.setMaximumWidth(self.up_table.horizontalHeader().length() + 20)
        upagraha_vbox.addWidget(self.up_table)
        self.tables_layout.addWidget(upagraha_container)
        # Arudha
        # Arudha Table
        arudha_container = QWidget()
        arudha_vbox = QVBoxLayout(arudha_container)
        arudha_vbox.setContentsMargins(0, 0, 0, 0)
        arudha_vbox.setSpacing(2)
        
        arudha_title = QLabel("Arudha Details")
        arudha_title.setStyleSheet("font-weight: bold; font-size: 12px; padding: 2px;")
        arudha_vbox.addWidget(arudha_title)
        
        self.arudha_table = QTableWidget()
        self.arudha_table.setColumnCount(5)
        self.arudha_table.setHorizontalHeaderLabels(["Arudha", "Degree", "Rashi", "Nakshatra", "Pada"])
        
        # Calculate Arudhas
        arudhas = calculate_arudha_positions(pos, data['rashi_numbers'])
        
        row = 0
        # Sort by A1, A2, A3... order
        sorted_keys = sorted(arudhas.keys(), key=lambda x: int(x.split()[0][1:].split('(')[0]))
        
        for key in sorted_keys:
            meta = arudhas[key]
            self.arudha_table.insertRow(row)
            
            # Format degree in DMS
            degree_in_rashi = meta.get('degree', 0)
            d = int(degree_in_rashi)
            m = int((degree_in_rashi - d) * 60)
            s = int(((degree_in_rashi - d) * 60 - m) * 60)
            deg_str = f"{d}° {m}' {s}\""
            
            self.arudha_table.setItem(row, 0, QTableWidgetItem(str(key)))
            self.arudha_table.setItem(row, 1, QTableWidgetItem(deg_str))
            self.arudha_table.setItem(row, 2, QTableWidgetItem(meta.get('rasi', 'N/A')))
            self.arudha_table.setItem(row, 3, QTableWidgetItem(meta.get('nakshatra', 'N/A')))
            self.arudha_table.setItem(row, 4, QTableWidgetItem(str(meta.get('pada', 'N/A'))))
            row += 1
        
        self.arudha_table.resizeColumnsToContents()
        self.arudha_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.arudha_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        self.arudha_table.setMaximumWidth(self.arudha_table.horizontalHeader().length() + 20)
        arudha_vbox.addWidget(self.arudha_table)
        self.tables_layout.addWidget(arudha_container)
        self.tables_layout.addStretch()
    def setup_location_autocomplete(self):
        """Setup autocomplete for location search using NepalIndia data"""
        # Combine all locations from Nepal and India
        all_locations = []
        self.location_data = {}  # Map: "Place, Country" -> (lat, lon)
        
        # Add Nepal districts
        for district, data in Nepal_district_data.items():
            display_name = f"{district}, Nepal"
            all_locations.append(display_name)
            self.location_data[display_name] = {"lat": data['lat'], "lon": data['lon']}

        # Add India districts  
        for district, data in India_district_data.items():
            display_name = f"{district}, India"
            all_locations.append(display_name)
            self.location_data[display_name] = {"lat": data['lat'], "lon": data['lon']}

        # Add world city data  
        for district, data in World_city_data.items():
            display_name = f"{district}, World"
            all_locations.append(display_name)
            self.location_data[display_name] = {"lat": data['lat'], "lon": data['lon']}

        # Sort alphabetically
        all_locations.sort()
        
        # Setup completer
        self.completer = QCompleter(all_locations, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.location_input.setCompleter(self.completer)
        
        # Store for reference
        self.all_locations = all_locations
    def on_location_selected(self):
        """Auto-fill lat/lon and timezone when location is selected from dropdown"""
        location_text = self.location_input.text().strip()
        
        # 1. Check if location exists in your database
        if location_text in self.location_data:
            lat, lon = self.location_data[location_text]["lat"], self.location_data[location_text]["lon"]
            self.lat_input.setText(str(lat))
            self.lon_input.setText(str(lon))
            
            # 2. Set timezone based on country first
            if "Nepal" in location_text:
                self.tz_combo.setCurrentText("Asia/Kathmandu")
            elif "India" in location_text:
                self.tz_combo.setCurrentText("Asia/Kolkata")
            else:
                # 3. For other countries, detect automatically
                tf = TimezoneFinder()
                tz_name = tf.timezone_at(lat=lat, lng=lon)
                if tz_name:
                    # If the timezone is not already in the combo, add it
                    if self.tz_combo.findText(tz_name) == -1:
                        self.tz_combo.addItem(tz_name)
                    self.tz_combo.setCurrentText(tz_name)
                else:
                    # fallback to UTC if detection fails
                    self.tz_combo.setCurrentText("UTC")

    
    def sync_bs_from_greg(self):
        """Convert Gregorian to BS and update BS field"""
        try:
            greg_date = self.date_input.text().strip()
            if greg_date:
                bs_date = gregorian_to_bs(greg_date)
                if bs_date and bs_date != self.bs_date_input.text():
                    self.bs_date_input.blockSignals(True)
                    self.bs_date_input.setText(bs_date)
                    self.bs_date_input.blockSignals(False)
        except Exception as e:
            print(f"Greg to BS conversion error: {e}")
    
    def sync_greg_from_bs(self):
        """Convert BS to Gregorian and update Gregorian field"""
        try:
            bs_date = self.bs_date_input.text().strip()
            if bs_date:
                greg_date = bs_to_gregorian(bs_date)
                if greg_date and greg_date != self.date_input.text():
                    self.date_input.blockSignals(True)
                    self.date_input.setText(greg_date)
                    self.date_input.blockSignals(False)
        except Exception as e:
            print(f"BS to Greg conversion error: {e}")
    
    def on_greg_date_changed(self, text):
        """Handle changes in Gregorian date field"""
        # Use timer to avoid rapid-fire conversions while typing
        if hasattr(self, 'greg_timer'):
            self.greg_timer.stop()
        else:
            self.greg_timer = QTimer(self)
            self.greg_timer.setSingleShot(True)
            self.greg_timer.timeout.connect(self.sync_bs_from_greg)
        self.greg_timer.start(500)  # 500ms delay
    
    def on_bs_date_changed(self, text):
        """Handle changes in BS date field"""
        if hasattr(self, 'bs_timer'):
            self.bs_timer.stop()
        else:
            self.bs_timer = QTimer(self)
            self.bs_timer.setSingleShot(True)
            self.bs_timer.timeout.connect(self.sync_greg_from_bs)
        self.bs_timer.start(500)  # 500ms delay
    def on_division_selector_changed(self, index):
        if index < 0 or not hasattr(self, 'current_pos'):
            return
        
        selected_text = self.division_selector.currentText()
        
        # Extract division number from text (e.g., "षष्ट्यांश कुण्डली - D60" → 60)
        import re
        match = re.search(r"D(\d+)", selected_text)
        if not match:
            return
        
        division_num = int(match.group(1))
        div_code = f"D{division_num}"
        
        # Recalculate divisional chart
        new_pkg = get_divisional_data_package(div_code, 
                                            self.current_pos, 
                                            self.current_retro, 
                                            self.current_combust)
        
        # Update the dynamic chart widget
        if hasattr(self, 'dynamic_chart_widget'):
            self.dynamic_chart_widget.chart_data = new_pkg[0]
            self.dynamic_chart_widget.rashi_numbers = new_pkg[1]
            self.dynamic_chart_widget.chart_title = selected_text
            self.dynamic_chart_widget.update()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AstrologyApp()
    window.show()
    sys.exit(app.exec())
