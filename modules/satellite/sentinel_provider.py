"""
=========================================================
LARA PROJECT

Sentinel Provider (Dummy Version)

Author : LARA Project
Version : 1.0

This version is API independent.

Later we will replace the dummy search
with Copernicus Data Space STAC API.
=========================================================
"""

from pathlib import Path
from datetime import datetime
import json
import shutil

from satellite_provider import SatelliteProvider


class SentinelProvider(SatelliteProvider):

    def __init__(self):

        super().__init__()

        self.provider_name = "Sentinel-2"

    # -------------------------------------------------

    def search_images(
        self,
        latitude,
        longitude,
        start_date,
        end_date,
    ):

        print("\nSearching Sentinel imagery...")

        # Dummy scene

        return [

            {
                "scene_id": "S2A_DUMMY_0001",
                "date": "2026-07-01",
                "cloud_cover": 4.8,
                "latitude": latitude,
                "longitude": longitude
            }

        ]

    # -------------------------------------------------

    def get_best_scene(
        self,
        scenes
    ):

        if len(scenes) == 0:
            return None

        scenes = sorted(
            scenes,
            key=lambda x: x["cloud_cover"]
        )

        return scenes[0]

    # -------------------------------------------------

    def download_image(
        self,
        scene,
        output_folder
    ):

        output_folder = Path(output_folder)

        output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = output_folder / "rgb.tif"

        # Dummy file

        with open(destination, "w") as f:
            f.write("Dummy Sentinel RGB Image")

        print("RGB downloaded.")

        return str(destination)

    # -------------------------------------------------

    def download_ndvi(
        self,
        scene,
        output_folder
    ):

        output_folder = Path(output_folder)

        destination = output_folder / "ndvi.tif"

        with open(destination, "w") as f:
            f.write("Dummy NDVI")

        print("NDVI downloaded.")

        return str(destination)

    # -------------------------------------------------

    def get_metadata(
        self,
        scene
    ):

        metadata = {

            "provider": self.provider_name,

            "scene_id": scene["scene_id"],

            "date": scene["date"],

            "cloud_cover": scene["cloud_cover"]

        }

        return metadata

    # -------------------------------------------------

    def save_metadata(
        self,
        metadata,
        output_folder
    ):

        output_folder = Path(output_folder)

        file = output_folder / "metadata.json"

        with open(file, "w") as f:

            json.dump(
                metadata,
                f,
                indent=4
            )

        return str(file)

    # -------------------------------------------------

    def preview(
        self,
        scene,
        output_folder
    ):

        output_folder = Path(output_folder)

        preview = output_folder / "preview.png"

        with open(preview, "w") as f:
            f.write("Dummy Preview")

        print("Preview created.")

        return str(preview)


# =====================================================

if __name__ == "__main__":

    provider = SentinelProvider()

    scenes = provider.search_images(

        latitude=-22.5597,

        longitude=17.0832,

        start_date="2025-01-01",

        end_date="2026-07-01"

    )

    best = provider.get_best_scene(scenes)

    output = r"D:\LARA-project\data\satellite\Demo"

    rgb = provider.download_image(best, output)

    ndvi = provider.download_ndvi(best, output)

    metadata = provider.get_metadata(best)

    provider.save_metadata(metadata, output)

    provider.preview(best, output)

    print("\nCompleted Successfully")

    print(metadata)
