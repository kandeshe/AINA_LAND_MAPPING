import json
import requests

from pathlib import Path


SOIL_LAYERS = {

    "phh2o": "pH",

    "soc": "OrganicCarbon",

    "nitrogen": "Nitrogen",

    "clay": "Clay",

    "sand": "Sand",

    "silt": "Silt",

    "bdod": "BulkDensity",

    "cec": "CEC"

}


DEPTH = "0-5cm"


def download_soil_data(config, output_folder):

    latitude = config.get("latitude", config.get("lat"))

    longitude = config.get("longitude", config.get("lon"))

    if latitude is None or longitude is None:
     raise KeyError(
        "Latitude/Longitude not found in config."
    )

    downloaded_files = {}

    print("\nDownloading SoilGrids Data...\n")

    for layer, folder in SOIL_LAYERS.items():

        save_folder = output_folder / folder

        save_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = save_folder / f"{folder}.tif"

        url = (
            "https://rest.isric.org/soilgrids/v2.0/properties/query"
            f"?lon={longitude}"
            f"&lat={latitude}"
            f"&property={layer}"
            f"&depth={DEPTH}"
            "&value=mean"
        )

        print(f"Downloading {folder}...")

        try:

            response = requests.get(
                url,
                timeout=60
            )

            response.raise_for_status()

            data = response.json()

            with open(
                save_folder / f"{folder}.json",
                "w"
            ) as f:

                json.dump(
                    data,
                    f,
                    indent=4
                )

            downloaded_files[layer] = {

                "json": save_folder / f"{folder}.json",

                "tif": filename

            }

            print("Done")

        except Exception as e:

            print(e)

            print(f"Failed : {folder}")

    print("\nDownload Complete")

    return downloaded_files
