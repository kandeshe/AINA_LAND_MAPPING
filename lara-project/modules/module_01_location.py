"""
=====================================================
LARA PROJECT
Module 01 - Location & AOI Generator
=====================================================
Author : LARA Project
Version : 1.0
"""

from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
import json


# =====================================================
# CONFIGURATION
# =====================================================

PROJECT_ROOT = Path(r"D:\LARA-project")

DATA_FOLDER = PROJECT_ROOT / "data"
LOCATION_FOLDER = DATA_FOLDER / "locations"
LOG_FOLDER = PROJECT_ROOT / "logs"

LOCATION_FOLDER.mkdir(parents=True, exist_ok=True)
LOG_FOLDER.mkdir(parents=True, exist_ok=True)


# =====================================================
# LOCATION OBJECT
# =====================================================

@dataclass
class FarmLocation:

    farm_name: str
    latitude: float
    longitude: float


# =====================================================
# MODULE
# =====================================================

class LocationModule:

    def __init__(self, location: FarmLocation):

        self.location = location

        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.project_name = (
            self.location.farm_name.replace(" ", "_")
            + "_"
            + self.timestamp
        )

        self.project_folder = LOCATION_FOLDER / self.project_name

        self.project_folder.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------

    def validate_location(self):

        if self.location.latitude < -90 or self.location.latitude > 90:
            raise Exception("Invalid Latitude")

        if self.location.longitude < -180 or self.location.longitude > 180:
            raise Exception("Invalid Longitude")

        print("Location validated successfully.")

    # ------------------------------------------

    def create_aoi(self, size=0.005):

        lat = self.location.latitude
        lon = self.location.longitude

        polygon = [

            [lon-size, lat-size],
            [lon+size, lat-size],
            [lon+size, lat+size],
            [lon-size, lat+size],
            [lon-size, lat-size]

        ]

        geojson = {

            "type": "Feature",

            "properties": {

                "Farm": self.location.farm_name,

                "Created": self.timestamp

            },

            "geometry": {

                "type": "Polygon",

                "coordinates": [polygon]

            }

        }

        return geojson

    # ------------------------------------------

    def save_geojson(self, geojson):

        filepath = self.project_folder / "farm_aoi.geojson"

        with open(filepath, "w") as f:
            json.dump(geojson, f, indent=4)

        print("AOI Saved.")

    # ------------------------------------------

    def save_metadata(self):

        metadata = {

            "Farm Name": self.location.farm_name,

            "Latitude": self.location.latitude,

            "Longitude": self.location.longitude,

            "Created": self.timestamp

        }

        filepath = self.project_folder / "metadata.json"

        with open(filepath, "w") as f:
            json.dump(metadata, f, indent=4)

        print("Metadata Saved.")

    # ------------------------------------------

    def create_log(self):

        log_file = LOG_FOLDER / "module01.log"

        with open(log_file, "a") as f:

            f.write(
                f"{self.timestamp} | {self.location.farm_name} | Location Module Completed\n"
            )

    # ------------------------------------------

    def run(self):

        print("=" * 50)

        print("LARA PROJECT")

        print("Module 01")

        print("=" * 50)

        self.validate_location()

        geojson = self.create_aoi()

        self.save_geojson(geojson)

        self.save_metadata()

        self.create_log()

        print()

        print("Module 01 Completed Successfully")

        print()

        print("Project Folder")

        print(self.project_folder)

        print()

        return {

            "project_folder": self.project_folder,

            "geojson": geojson,

            "latitude": self.location.latitude,

            "longitude": self.location.longitude

        }


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    demo_location = FarmLocation(

        farm_name="Demo Namibia Farm",

        latitude=-22.5597,

        longitude=17.0832

    )

    module = LocationModule(demo_location)

    result = module.run()

    print(json.dumps(result["geojson"], indent=4))
    
