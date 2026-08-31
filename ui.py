import os

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing --ignore-gpu-blocklist"
os.environ["QT_OPENGL"] = "software"
import sys
from geopy.geocoders import Nominatim
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QGroupBox,
    QGridLayout,
    QTabWidget,
    QTextEdit,
    QMessageBox,
    QProgressBar
)
from PySide6.QtGui import QPixmap
import os
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl
from PySide6.QtCore import Qt
from main import run_analysis
from resources.bridge import MapBridge
from PySide6.QtWebChannel import QWebChannel
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
print(BASE_DIR)
from PySide6.QtWebEngineCore import QWebEnginePage
from server import start_server
from widgets.image_viewer import ImageViewer
from modules.ai_advisor import AIAdvisor
from modules.location import get_location_name
start_server()
class DebugPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"[JS] {message} ({sourceID}:{lineNumber})")


class MainWindow(QMainWindow):
    from geopy.geocoders import Nominatim

    def search_location(self):

       place = self.searchBox.text().strip()

       if not place:
            return

       try:
            geolocator = Nominatim(user_agent="LARA")

            location = geolocator.geocode(place)

            if location is None:
                QMessageBox.warning(self, "Search", "Location not found")
                return

            lat = location.latitude
            lon = location.longitude

            self.txtLatitude.setText(f"{lat:.6f}")
            self.txtLongitude.setText(f"{lon:.6f}")

            self.mapView.page().runJavaScript(
                f"moveToLocation({lat}, {lon});"
            )

       except Exception as e:
            QMessageBox.critical(self, "Search Error", str(e))
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LARA - Agricultural Intelligence & Analysis")
        self.resize(1600, 900)

        self.build_ui()
        self.ai = AIAdvisor()
        self.analysis_result = None
        #self.searchButton.clicked.connect(self.search_location)
        self.analyzeButton.clicked.connect(self.run_analysis_clicked)
        self.askButton.clicked.connect(
        self.ask_ai
)
        print("Search button clicked")
    def create_status_section(self):

     layout = QHBoxLayout()

     self.statusLabel = QLabel("Ready")

     self.progressBar = QProgressBar()
     self.progressBar.setValue(0)
     self.progressBar.setTextVisible(True)
     self.progressBar.setMaximumHeight(22)

     self.progressBar.setStyleSheet("""
        QProgressBar{
            border:1px solid gray;
            border-radius:5px;
            text-align:center;
        }

        QProgressBar::chunk{
            background-color:#2E7D32;
        }
    """)

     layout.addWidget(self.statusLabel, 1)
     layout.addWidget(self.progressBar, 2)

     self.mainLayout.addLayout(layout)

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        self.mainLayout = QVBoxLayout()
        central.setLayout(self.mainLayout)

        self.create_header()
        self.create_search_bar()

        # Horizontal line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        self.mainLayout.addWidget(line)

        self.create_middle_panel()
        self.create_tabs()
        self.create_status_section()


    
    def create_header(self):

        title = QLabel("LARA")

        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            QLabel{
                font-size:32px;
                font-weight:bold;
                color:#1B5E20;
                padding:15px;
            }
        """)

        self.mainLayout.addWidget(title)

    def create_middle_panel(self):

        layout = QHBoxLayout()

        # ---------------- MAP ----------------

        mapGroup = QGroupBox("Map")
        mapLayout = QVBoxLayout()

        self.mapView = QWebEngineView()

        page = DebugPage(self.mapView)
        self.mapView.setPage(page)

        self.channel = QWebChannel()
        self.bridge = MapBridge(self)

        self.channel.registerObject("bridge", self.bridge)
        self.mapView.page().setWebChannel(self.channel)

        self.mapView.setUrl(
            QUrl("http://127.0.0.1:8000/map/map.html")
        )

        mapLayout.addWidget(self.mapView)
        mapGroup.setLayout(mapLayout)

        mapGroup.setMinimumHeight(520)

        # ---------------- INFO ----------------

        infoGroup = QGroupBox("Selected Location")
        infoGroup.setMaximumWidth(320)

        grid = QGridLayout()

        grid.addWidget(QLabel("Latitude"),0,0)

        self.txtLatitude = QLineEdit()
        grid.addWidget(self.txtLatitude,0,1)

        grid.addWidget(QLabel("Longitude"),1,0)

        self.txtLongitude = QLineEdit()
        grid.addWidget(self.txtLongitude,1,1)

        grid.addWidget(QLabel("Area (Acres)"),2,0)

        self.txtArea = QLineEdit()
        self.txtArea.setText("5")
        grid.addWidget(self.txtArea,2,1)

        grid.addWidget(QLabel("Location"), 4, 0)
        self.lblSelectedLocation = QLabel("--")
        grid.addWidget(self.lblSelectedLocation, 4, 1)

        grid.addWidget(QLabel("District"), 5, 0)
        self.lblSelectedDistrict = QLabel("--")
        grid.addWidget(self.lblSelectedDistrict, 5, 1)

        grid.addWidget(QLabel("Region"), 6, 0)
        self.lblSelectedRegion = QLabel("--")
        grid.addWidget(self.lblSelectedRegion, 6, 1)

        grid.addWidget(QLabel("Country"), 7, 0)
        self.lblSelectedCountry = QLabel("--")
        grid.addWidget(self.lblSelectedCountry, 7, 1)
        grid.addWidget(QLabel("Elevation"),3,0)

        self.lblElevation = QLabel("--")
        grid.addWidget(self.lblElevation,3,1)

        self.analyzeButton = QPushButton("Analyze")
        self.analyzeButton.setMinimumHeight(45)

        grid.addWidget(self.analyzeButton,8,0,1,2)

        grid.setRowStretch(8,1)

        infoGroup.setLayout(grid)

        layout.addWidget(mapGroup,5)
        layout.addWidget(infoGroup,1)

        self.mainLayout.addLayout(layout)
    
    def create_search_bar(self):

        layout = QHBoxLayout()

        self.searchBox = QLineEdit()
        self.searchBox.setPlaceholderText(
            "Search Village / City / Latitude,Longitude"
        )

        self.searchButton = QPushButton("Search")
        self.searchButton.setFixedWidth(140)

        self.searchButton.clicked.connect(self.search_location)
        self.searchButton.setFixedWidth(140)

        layout.addWidget(self.searchBox)
        layout.addWidget(self.searchButton)

        self.mainLayout.addLayout(layout)

    def search_location(self):

        place = self.searchBox.text().strip()

        if not place:
         return

        try:
         geolocator = Nominatim(user_agent="LARA_gis")

         location = geolocator.geocode(place)

         if location is None:
            QMessageBox.warning(
                self,
                "Search",
                "Location not found."
            )
            return

         lat = location.latitude
         lng = location.longitude

         self.txtLatitude.setText(str(lat))
         self.txtLongitude.setText(str(lng))

         self.mapView.page().runJavaScript(
            f"moveToLocation({lat}, {lng});"
        )

        except Exception as e:
          QMessageBox.warning(
            self,
            "Search Error",
            str(e)
           )


    def display_results(self, result):

     self.lblLocation.setText(
      f"Location : {result['location']}, {result['district']}, {result['region']}, {result['country']}"
    )

     self.lblCoordinates.setText(
        f"Coordinates : {result['latitude']} , {result['longitude']}"
    )

     self.lblAreaInfo.setText(
        f"Area : {result['area']} Acres"
    )

     self.lblElevationInfo.setText(
        f"Elevation : {result['elevation']}"
    )

     self.lblNDVI.setText(
        f"Average NDVI : {result['mean_ndvi']:.3f}"
    )

     self.lblNDWI.setText(
        f"Average NDWI : {result['mean_ndwi']:.3f}"
    )

     land = result["land_cover"]

     self.lblLandCover.setText(
    f"""Land Cover

        Water      : {land['water']}%
        Bare Land  : {land['bare']}%
        Sparse Veg : {land['sparse']}%
        Moderate   : {land['moderate']}%
        Dense Veg  : {land['dense']}%
        """
        )

     self.lblSlope.setText(
    f"Water Coverage : {result['water_percent']}%"
)
    
    # ---------------- RGB ----------------

     if "rgb_image" in result:
      self.rgbTab.loadImage(result["rgb_image"])
     # ---------------- NDVI ----------------

     if "ndvi_image" in result:

        pix = QPixmap(result["ndvi_image"])

        self.ndviTab.setPixmap(
            pix.scaled(
                900,
                600,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

     # ---------------- NDWI ----------------

     if "ndwi_image" in result:

        pix = QPixmap(result["ndwi_image"])

        self.ndwiTab.setPixmap(
            pix.scaled(
                900,
                600,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

     # ---------------- SAVI ----------------

     if "savi_image" in result:

        pix = QPixmap(result["savi_image"])

        self.saviTab.setPixmap(
            pix.scaled(
                900,
                600,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

     # ---------------- Terrain ----------------

     terrain = result.get("terrain")

     if terrain:

      self.load_image(self.demImage, terrain["dem"])
      self.load_image(self.hillshadeImage, terrain["hillshade"])
      self.load_image(self.slopeImage, terrain["slope"])
      self.load_image(self.aspectImage, terrain["aspect"])
      self.load_image(self.contourImage, terrain["contours"])
      self.load_image(self.triImage, terrain["tri"])

      # ---------------- Classification ----------------

     if "classification_image" in result:

       pix = QPixmap(result["classification_image"])

       self.classificationTab.setPixmap(
        pix.scaled(
            900,
            600,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
    )

     # ---------------- Hydrology ----------------

     if "hydrology_image" in result:

        pix = QPixmap(result["hydrology_image"])

        self.hydroImage.setPixmap(
        pix.scaled(
            900,
            600,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
    )


# ---------------- Climate display ----------------

     climate_folder = BASE_DIR / "data" / "satellite" / "Climate"

     temperature = climate_folder / "Temperature.png"
     zones = climate_folder / "ClimateZones.png"
     print(temperature)
     print(temperature.exists())

     print(zones)
     print(zones.exists())
     stats = climate_folder / "Climate_Statistics.txt"
     with open(stats, "r", encoding="cp1252") as f:
      self.climateStats.setPlainText(f.read())

     temperature = os.path.join(
     climate_folder,
     "Temperature.png"
    )

     zones = os.path.join(
     climate_folder,
     "ClimateZones.png"
    )

     stats = os.path.join(
     climate_folder,
     "Climate_Statistics.txt"
    )

     if os.path.exists(temperature):
      self.load_image(
        self.temperatureImage,
        temperature
    )

     if os.path.exists(zones):
      self.load_image(
        self.climateZoneImage,
        zones
    )

     if os.path.exists(stats):
      with open(stats, "r", encoding="cp1252") as f:
    
        self.climateStats.setPlainText(f.read())

     print("Loading Climate Images...")

     print(temperature)
     print(os.path.exists(temperature))

     print(zones)
     print(os.path.exists(zones))

     print(stats)
     print(os.path.exists(stats))
# ---------------- Soil ----------------
    

     soil_folder = BASE_DIR / "data" / "satellite" / "Soil"

     ph = soil_folder / "Phh2o" / "phh2o.png"

     carbon = soil_folder / "Soc" / "soc.png"

     clay = soil_folder / "Clay" / "clay.png"

     report = soil_folder / "Soil_Report.txt"

     if ph.exists():
        self.load_image(
            self.soilPHImage,
            str(ph)
        )

     if carbon.exists():
        self.load_image(
            self.soilCarbonImage,
            str(carbon)
        )

     if clay.exists():
        self.load_image(
            self.soilClayImage,
            str(clay)
        )

     if report.exists():
        with open(report, "r", errors="replace") as f:
            self.soilStats.setPlainText(f.read())
        
      #-----------------rainfall--------------
     rain_folder = os.path.join(BASE_DIR, "data", "satellite", "Rainfall")

     self.load_image(
        self.lblRainMonthly,
        os.path.join(rain_folder, "Monthly_Rainfall.png")
    )

     self.load_image(
     self.lblRainTrend,
     os.path.join(rain_folder, "Rainfall_Trend.png")

    )
     report = os.path.join(
    rain_folder,
    "Rainfall_Report.txt"
    )

     if os.path.exists(report):
      with open(report, "r", encoding="utf-8", errors="ignore") as f:
       self.txtRainfall.setPlainText(f.read())

       # ---------------- Groundwater ----------------

     gw_folder = os.path.join(
        BASE_DIR,
        "data",
        "satellite",
        "Groundwater"
    )

     self.load_image(
        self.lblGroundwaterDepth,
        os.path.join(gw_folder, "Groundwater_Depth.png")
    )

     self.load_image(
        self.lblRecharge,
        os.path.join(gw_folder, "Recharge_Potential.png")
    )

     report = os.path.join(
        gw_folder,
        "Groundwater_Report.txt"
    )

     if os.path.exists(report):
        with open(report, "r", encoding="utf-8", errors="ignore") as f:
            self.txtGroundwater.setPlainText(f.read())
      # ---------------- Flood ----------------

     if "flood_image" in result:

      pix = QPixmap(result["flood_image"])

      self.floodImage.setPixmap(
        pix.scaled(
            900,
            600,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
    )

    def update_coordinates(self, lat, lon):
       self.txtLatitude.setText(f"{lat:.6f}")
       self.txtLongitude.setText(f"{lon:.6f}")
    
    def create_tabs(self):

     self.tabs = QTabWidget()

    # ---------- Overview ----------
     self.overviewTab = QWidget()

     overviewLayout = QVBoxLayout()

     self.lblLocation = QLabel("Location : -")
     self.lblCoordinates = QLabel("Coordinates : -")
     self.lblAreaInfo = QLabel("Area : -")
     self.lblElevationInfo = QLabel("Elevation : -")
     self.lblLandCover = QLabel("Land Cover : -")
     self.lblSoil = QLabel("Soil : -")
     self.lblNDVI = QLabel("Average NDVI : -")
     self.lblNDWI = QLabel("Average NDWI : -")
     self.lblSlope = QLabel("Slope : -")

     for lbl in [
    self.lblLocation,
    self.lblCoordinates,
    self.lblAreaInfo,
    self.lblElevationInfo,
    self.lblLandCover,
    self.lblSoil,
    self.lblNDVI,
    self.lblNDWI,
    self.lblSlope
]:
      lbl.setStyleSheet("font-size:15px;padding:4px;")
      overviewLayout.addWidget(lbl)

     overviewLayout.addStretch()

     self.overviewTab.setLayout(overviewLayout)

    # ---------- RGB ----------
    
     self.rgbTab = ImageViewer()

    # ---------- NDVI ----------
     self.ndviTab = QLabel()
     self.ndviTab.setAlignment(Qt.AlignCenter)
     self.ndviTab.setMinimumHeight(500)
     self.ndviTab.setText("NDVI Image will appear here")

    # ---------- NDWI ----------
     self.ndwiTab = QLabel()
     self.ndwiTab.setAlignment(Qt.AlignCenter)
     self.ndwiTab.setMinimumHeight(500)
     self.ndwiTab.setText("NDWI Image will appear here")

    # ---------- SAVI ----------
     self.saviTab = QLabel()
     self.saviTab.setAlignment(Qt.AlignCenter)
     self.saviTab.setMinimumHeight(500)
     self.saviTab.setText("SAVI Image will appear here")

    # ---------- Classification ----------
     self.classificationTab = QLabel()
     self.classificationTab.setAlignment(Qt.AlignCenter)
     self.classificationTab.setMinimumHeight(500)
     self.classificationTab.setText("Classification Image will appear here")

    # ---------- Terrain ----------
     self.terrainTab = QWidget()

     terrainLayout = QVBoxLayout()

     grid = QGridLayout()

     self.demImage = QLabel("DEM")
     self.hillshadeImage = QLabel("Hillshade")
     self.slopeImage = QLabel("Slope")
     self.aspectImage = QLabel("Aspect")
     self.contourImage = QLabel("Contours")
     self.triImage = QLabel("TRI")

     terrainImages = [
      self.demImage,
      self.hillshadeImage,
      self.slopeImage,
      self.aspectImage,
      self.contourImage,
      self.triImage,
     ]

     for img in terrainImages:
         img.setAlignment(Qt.AlignCenter)
         img.setMinimumSize(900, 650)
         img.setStyleSheet("""
             QLabel{
               border:1px solid lightgray;
               background:white;
             }
         """)

     grid.addWidget(self.demImage,0,0)
     grid.addWidget(self.hillshadeImage,0,1)

     grid.addWidget(self.slopeImage,1,0)
     grid.addWidget(self.aspectImage,1,1)

     grid.addWidget(self.contourImage,2,0)
     grid.addWidget(self.triImage,2,1)

     terrainLayout.addLayout(grid)

     self.terrainStats = QTextEdit()
     self.terrainStats.setReadOnly(True)
     terrainLayout.addWidget(self.terrainStats)

     self.terrainTab.setLayout(terrainLayout)

    # ---------- Hydrology ----------
     self.hydrologyTab = QWidget()

     hydroLayout = QVBoxLayout()

     self.hydroImage = QLabel("Hydrology Map")
     self.hydroImage.setAlignment(Qt.AlignCenter)
     self.hydroImage.setMinimumHeight(400)

     self.hydroInfo = QTextEdit()
     self.hydroInfo.setReadOnly(True)

     hydroLayout.addWidget(self.hydroImage)
     hydroLayout.addWidget(self.hydroInfo)

     self.hydrologyTab.setLayout(hydroLayout)

    # ---------- Climate ----------
     

     self.climateTab = QWidget()

     climateLayout = QVBoxLayout()

        # Top Row
     topLayout = QHBoxLayout()

     self.temperatureImage = QLabel("Temperature")
     self.temperatureImage.setAlignment(Qt.AlignCenter)
     self.temperatureImage.setMinimumSize(500, 350)

     self.climateZoneImage = QLabel("Climate Zones")
     self.climateZoneImage.setAlignment(Qt.AlignCenter)
     self.climateZoneImage.setMinimumSize(500, 350)

     for img in [self.temperatureImage, self.climateZoneImage]:
         img.setStyleSheet("""
             QLabel{
                  border:1px solid lightgray;
                  background:white;
                }
            """)

     topLayout.addWidget(self.temperatureImage)
     topLayout.addWidget(self.climateZoneImage)

     climateLayout.addLayout(topLayout)

        # Statistics
     self.climateStats = QTextEdit()
     self.climateStats.setReadOnly(True)

     climateLayout.addWidget(self.climateStats)

     self.climateTab.setLayout(climateLayout)
            

    # ---------- Soil ----------

     self.soilTab = QWidget()

     soilLayout = QVBoxLayout()

     topLayout = QHBoxLayout()

     self.soilPHImage = QLabel("Soil pH")
     self.soilCarbonImage = QLabel("Organic Carbon")
     self.soilClayImage = QLabel("Clay")

     for lbl in (
        self.soilPHImage,
        self.soilCarbonImage,
        self.soilClayImage
     ):
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setMinimumSize(330,280)
        lbl.setStyleSheet("""
            QLabel{
                border:1px solid lightgray;
                background:white;
            }
        """)

     topLayout.addWidget(self.soilPHImage)
     topLayout.addWidget(self.soilCarbonImage)
     topLayout.addWidget(self.soilClayImage)

     soilLayout.addLayout(topLayout)

     self.soilStats = QTextEdit()
     self.soilStats.setReadOnly(True)

     soilLayout.addWidget(self.soilStats)

     self.soilTab.setLayout(soilLayout)
     

    # ---------- Rainfall ----------
     

     self.rainfallTab = QWidget()

     rainLayout = QVBoxLayout()

     topLayout = QHBoxLayout()

     self.lblRainMonthly = QLabel("Monthly Rainfall")
     self.lblRainTrend = QLabel("Rainfall Trend")

     for lbl in (
            self.lblRainMonthly,
            self.lblRainTrend
        ):
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setMinimumSize(500,350)
            lbl.setStyleSheet("""
                QLabel{
                    border:1px solid lightgray;
                    background:white;
                }
            """)

     topLayout.addWidget(self.lblRainMonthly)
     topLayout.addWidget(self.lblRainTrend)

     rainLayout.addLayout(topLayout)

     self.txtRainfall = QTextEdit()
     self.txtRainfall.setReadOnly(True)

     rainLayout.addWidget(self.txtRainfall)

     self.rainfallTab.setLayout(rainLayout)
            

    # ---------- Groundwater ----------

     self.groundwaterTab = QWidget()

     gwLayout = QVBoxLayout()

     topLayout = QHBoxLayout()

     self.lblGroundwaterDepth = QLabel("Groundwater Depth")
     self.lblRecharge = QLabel("Recharge Potential")

     for lbl in (
        self.lblGroundwaterDepth,
        self.lblRecharge
     ):
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setMinimumSize(500,350)
        lbl.setStyleSheet("""
            QLabel{
                border:1px solid lightgray;
                background:white;
            }
        """)

     topLayout.addWidget(self.lblGroundwaterDepth)
     topLayout.addWidget(self.lblRecharge)

     gwLayout.addLayout(topLayout)

     self.txtGroundwater = QTextEdit()
     self.txtGroundwater.setReadOnly(True)

     gwLayout.addWidget(self.txtGroundwater)

     self.groundwaterTab.setLayout(gwLayout)
      

    # ---------- Flood ----------
     self.floodTab = QWidget()

     floodLayout = QVBoxLayout()

     self.floodImage = QLabel("Flood Risk Map")
     self.floodImage.setAlignment(Qt.AlignCenter)
     self.floodImage.setMinimumHeight(400)

     self.floodInfo = QTextEdit()
     

     floodLayout.addWidget(self.floodImage)
     floodLayout.addWidget(self.floodInfo)

     self.floodTab.setLayout(floodLayout)
     

    # ---------- AI ----------

     self.aiTab = QWidget()

     aiLayout = QVBoxLayout()

     self.aiConversation = QTextEdit()
     self.aiConversation.setReadOnly(True)

     self.aiQuestion = QLineEdit()
     self.aiQuestion.setPlaceholderText(
        "Ask about this land..."
    )

     self.askButton = QPushButton("Ask AI")

     aiLayout.addWidget(self.aiConversation)
     aiLayout.addWidget(self.aiQuestion)
     aiLayout.addWidget(self.askButton)

     self.aiTab.setLayout(aiLayout)
     

    # ---------- Report ----------
     self.reportTab = QWidget()

     reportLayout = QVBoxLayout()

     self.reportPreview = QTextEdit()
     

     self.exportButton = QPushButton("Export PDF Report")

     reportLayout.addWidget(self.reportPreview)
     reportLayout.addWidget(self.exportButton)

     self.reportTab.setLayout(reportLayout)
     

     self.tabs.addTab(self.overviewTab, "Overview")
     self.tabs.addTab(self.rgbTab, "RGB")
     self.tabs.addTab(self.ndviTab, "NDVI")
     self.tabs.addTab(self.ndwiTab, "NDWI")
     self.tabs.addTab(self.saviTab, "SAVI")
     self.tabs.addTab(self.classificationTab, "Classification")
     self.tabs.addTab(self.terrainTab, "Terrain")
     self.tabs.addTab(self.hydrologyTab, "Hydrology")
     self.tabs.addTab(self.climateTab, "Climate")
     self.tabs.addTab(self.soilTab, "Soil")
     self.tabs.addTab(self.rainfallTab, "Rainfall")
     self.tabs.addTab(self.groundwaterTab, "Groundwater")
     self.tabs.addTab(self.floodTab, "Flood")
     self.tabs.addTab(self.aiTab, "AI Advisor")
     self.tabs.addTab(self.reportTab, "Report")

     self.mainLayout.addWidget(self.tabs)

    def run_analysis_clicked(self):

        self.analyzeButton.setEnabled(False)
        self.analyzeButton.setText("Analyzing...")

        try:

            # -----------------------
            # Read user input
            # -----------------------

            lat = float(self.txtLatitude.text())
            lon = float(self.txtLongitude.text())
            area = float(self.txtArea.text())

            # -----------------------
            # Progress
            # -----------------------

            self.statusLabel.setText("Downloading Satellite Data...")
            self.progressBar.setValue(10)
            QApplication.processEvents()

            # -----------------------
            # Run Analysis
            # -----------------------

            result = run_analysis(
                LAT=lat,
                LON=lon,
                ANALYSIS_AREA_ACRES=area
            )
            location = get_location_name(lat, lon)
            result["location"] = location["place"]
            result["district"] = location["district"]
            result["region"] = location["region"]
            result["country"] = location["country"]
            result["display_name"] = location["display_name"]
            self.lblSelectedLocation.setText(location["place"])
            self.lblSelectedDistrict.setText(location["district"])
            self.lblSelectedRegion.setText(location["region"])
            self.lblSelectedCountry.setText(location["country"])
            print(location)
            self.analysis_result = result
            

            # -----------------------
            # Update Progress
            # -----------------------

            self.statusLabel.setText("Generating Maps...")
            self.progressBar.setValue(50)
            QApplication.processEvents()

            # -----------------------
            # Display Results
            # -----------------------

            self.display_results(result)

            self.statusLabel.setText("Preparing Dashboard...")
            self.progressBar.setValue(80)
            QApplication.processEvents()

            # (We'll load images here in the next step)

            self.progressBar.setValue(100)
            self.statusLabel.setText("Analysis Completed Successfully")

        except Exception as e:

            self.progressBar.setValue(0)
            self.statusLabel.setText("Analysis Failed")

            QMessageBox.critical(
                self,
                "LARA Error",
                str(e)
            )

        finally:

            self.analyzeButton.setEnabled(True)
            self.analyzeButton.setText("Analyze")

    def build_ai_context(self):

         """
        Build AI context from the completed analysis and
        the reports generated by each analysis module.
        """

         context = {
            # =====================================================
            # LOCATION
            # =====================================================

            "location": self.analysis_result.get("location"),
            "district": self.analysis_result.get("district"),
            "region": self.analysis_result.get("region"),
            "country": self.analysis_result.get("country"),

            # =====================================================
            # BASIC LAND INFORMATION
            # =====================================================

            "latitude": self.analysis_result.get("latitude"),
            "longitude": self.analysis_result.get("longitude"),
            "area": self.analysis_result.get("area"),
            "elevation": self.analysis_result.get("elevation"),

            # =====================================================
            # VEGETATION / WATER INDICES
            # =====================================================

            "mean_ndvi": self.analysis_result.get("mean_ndvi"),
            "mean_ndwi": self.analysis_result.get("mean_ndwi"),
            "mean_savi": self.analysis_result.get("mean_savi"),

            "water_percent": self.analysis_result.get(
                "water_percent"
            ),

            # =====================================================
            # LARA SATELLITE LAND-COVER CLASSIFICATION
            # =====================================================

            "land_cover": self.analysis_result.get(
                "land_cover",
                {}
            ),

            # =====================================================
            # CNN LAND-COVER CLASSIFICATION
            # =====================================================

            "cnn_landcover": self.analysis_result.get(
                "cnn_landcover",
                {}
            ),

            # =====================================================
            # OTHER ENVIRONMENTAL DATA
            # =====================================================

            "rainfall": None,

            "groundwater": None,

            "flood_risk": None,

            "soil": {},

            "land_suitability": None,

            "temperature": None,

            # =====================================================
            # OPTIONAL TERRAIN DATA
            # =====================================================

            "terrain": self.analysis_result.get(
                "terrain",
                {}
            ),
        }
         data_folder = BASE_DIR / "data" / "satellite"

        # =====================================================
        # RAINFALL
        # =====================================================

         rainfall_report = (
            data_folder /
            "Rainfall" /
            "Rainfall_Report.txt"
        )

         if rainfall_report.exists():

            try:

                text = rainfall_report.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                for line in text.splitlines():

                    line = line.strip()

                    if line.startswith("Annual Rainfall"):

                        value = line.split(":")[-1]
                        value = value.replace("mm", "").strip()

                        try:
                            context["rainfall"] = float(value)
                        except ValueError:
                            pass

            except Exception as e:

                print(
                    "Rainfall report error:",
                    e
                )

        # =====================================================
        # GROUNDWATER
        # =====================================================

         groundwater_report = (
            data_folder /
            "Groundwater" /
            "Groundwater_Report.txt"
        )

         if groundwater_report.exists():

            try:

                text = groundwater_report.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                groundwater = {}

                for line in text.splitlines():

                    line = line.strip()

                    if line.startswith("Average Depth"):

                        value = line.split(":")[-1]
                        value = value.replace("m", "").strip()

                        try:
                            groundwater["average_depth"] = float(value)
                        except ValueError:
                            pass

                    elif line.startswith("Recharge Potential"):

                        value = line.split(":")[-1]
                        value = value.replace("%", "").strip()

                        try:
                            groundwater["recharge_potential"] = float(value)
                        except ValueError:
                            pass

                context["groundwater"] = groundwater

            except Exception as e:

                print(
                    "Groundwater report error:",
                    e
                )

        # =====================================================
        # SOIL
        # =====================================================

         soil_report = (
            data_folder /
            "Soil" /
            "Soil_Report.txt"
        )

         if soil_report.exists():

            try:

                text = soil_report.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                soil = {}

                current_layer = None

                for line in text.splitlines():

                    line = line.strip()

                    if line in [
                        "Soil pH",
                        "Organic Carbon",
                        "Nitrogen",
                        "Clay",
                        "Sand",
                        "Silt",
                        "Bulk Density",
                        "Cation Exchange Capacity"
                    ]:

                        current_layer = line

                    elif line.startswith("Mean"):

                        value = line.split(":")[-1].strip()

                        try:

                            value = float(value)

                            if current_layer == "Soil pH":
                                soil["ph"] = value

                            elif current_layer == "Organic Carbon":
                                soil["organic_carbon"] = value

                            elif current_layer == "Nitrogen":
                                soil["nitrogen"] = value

                            elif current_layer == "Clay":
                                soil["clay"] = value

                            elif current_layer == "Sand":
                                soil["sand"] = value

                            elif current_layer == "Silt":
                                soil["silt"] = value

                            elif current_layer == "Bulk Density":
                                soil["bulk_density"] = value

                            elif current_layer == "Cation Exchange Capacity":
                                soil["cec"] = value

                        except ValueError:
                            pass

                context["soil"] = soil

            except Exception as e:

                print(
                    "Soil report error:",
                    e
                )

        # =====================================================
        # FLOOD
        # =====================================================

         flood_report = (
            data_folder /
            "Flood" /
            "Flood_Report.txt"
        )

         if flood_report.exists():

            try:

                text = flood_report.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                risk = "Low"

                for line in text.splitlines():

                    line = line.strip()

                    if line.startswith("High"):

                        try:

                            value = float(
                                line.split(":")[-1]
                                .replace("%", "")
                                .strip()
                            )

                            if value > 5:
                                risk = "High"

                        except ValueError:
                            pass

                    if line.startswith("Very High"):

                        try:

                            value = float(
                                line.split(":")[-1]
                                .replace("%", "")
                                .strip()
                            )

                            if value > 0:
                                risk = "Very High"

                        except ValueError:
                            pass

                    if line.startswith("Moderate"):

                        try:

                            value = float(
                                line.split(":")[-1]
                                .replace("%", "")
                                .strip()
                            )

                            if value > 5 and risk == "Low":
                                risk = "Moderate"

                        except ValueError:
                            pass

                context["flood_risk"] = risk

            except Exception as e:

                print(
                    "Flood report error:",
                    e
                )

        # =====================================================
        # CLIMATE
        # =====================================================

         climate_report = (
            data_folder /
            "Climate" /
            "Climate_Statistics.txt"
        )

         if climate_report.exists():

            try:

                text = climate_report.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                for line in text.splitlines():

                    line = line.strip()

                    if line.startswith(
                        "Average Temperature"
                    ):

                        value = line.split(":")[-1]

                        value = (
                            value
                            .replace("°C", "")
                            .strip()
                        )

                        try:
                            context["temperature"] = float(value)
                        except ValueError:
                            pass

            except Exception as e:

                print(
                    "Climate report error:",
                    e
                )

        # =====================================================
        # LAND SUITABILITY
        # =====================================================

         suitability_report = (
            data_folder /
            "LandSuitability" /
            "Land_Suitability_Report.txt"
        )

         if suitability_report.exists():

            try:

                text = suitability_report.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                for line in text.splitlines():

                    line = line.strip()

                    if line.startswith(
                        "Average Score"
                    ):

                        value = line.split(":")[-1].strip()

                        try:
                            context[
                                "land_suitability"
                            ] = float(value)
                        except ValueError:
                            pass

            except Exception as e:

                print(
                    "Land suitability report error:",
                    e
                )

         return context
    
    def ask_ai(self):

     if self.analysis_result is None:

        QMessageBox.information(
            self,
            "LARA",
            "Please run analysis first."
        )

        return

     question = self.aiQuestion.text().strip()

     if not question:
        return

     self.aiConversation.append(
        f"<b>You:</b> {question}<br>"
    )

     ai_context = self.build_ai_context()

     print("\n========== AI CONTEXT ==========")
     print(ai_context)
     print("================================")

     answer = self.ai.ask(
        ai_context,
        question
    )
     print("\n========== AI CONTEXT ==========")
     print(ai_context)
     print("================================")
     self.aiConversation.append(
        f"<b>LARA:</b><br>{answer}<br><hr>"
    )

     self.aiQuestion.clear()
        

    def load_image(self, label, image_path):

     if not image_path:
        label.setText("No Image")
        return

     pixmap = QPixmap(image_path)
     print("Loading:", image_path)
     print("Null:", pixmap.isNull())
     print("Label Size:", label.width(), label.height())
     if pixmap.isNull():
        label.setText(f"Image not found\n{image_path}")
        return

     
     label.setPixmap(
      pixmap.scaled(
        label.width() if label.width() > 10 else 500,
        label.height() if label.height() > 10 else 350,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )
)
    

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()

    window.show()

    sys.exit(app.exec())
