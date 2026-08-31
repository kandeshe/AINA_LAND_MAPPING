import json
import numpy as np
import rasterio
import requests

from rasterio.transform import from_origin


def download_groundwater_data(config, output_folder):

    print("\nDownloading Groundwater Data...\n")

    latitude = config.get("latitude", config.get("lat"))
    longitude = config.get("longitude", config.get("lon"))

    url = (
        "https://api.open-meteo.com/v1/elevation"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
    )

    try:

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        data = response.json()

        with open(output_folder / "Groundwater.json", "w") as f:
            json.dump(data, f, indent=4)

        elevation = float(data["elevation"][0])

        # Initial groundwater depth estimation
        if elevation < 50:
            depth = 5.0
        elif elevation < 150:
            depth = 12.0
        elif elevation < 300:
            depth = 20.0
        elif elevation < 600:
            depth = 35.0
        else:
            depth = 60.0

        recharge = max(0.0, 100.0 - depth)

        raster = np.full((100, 100), depth, dtype=np.float32)

        transform = from_origin(
            longitude - 0.005,
            latitude + 0.005,
            0.0001,
            0.0001
        )

        profile = {
            "driver": "GTiff",
            "height": raster.shape[0],
            "width": raster.shape[1],
            "count": 1,
            "dtype": rasterio.float32,
            "crs": "EPSG:4326",
            "transform": transform,
            "nodata": np.nan
        }

        tif_file = output_folder / "Groundwater_Depth.tif"

        with rasterio.open(tif_file, "w", **profile) as dst:
            dst.write(raster, 1)

        print(f"Elevation          : {elevation:.2f} m")
        print(f"Estimated Depth    : {depth:.2f} m")
        print(f"Recharge Potential : {recharge:.2f}%")

        print("\nGroundwater Download Completed")

        return {
            "depth": depth,
            "recharge": recharge,
            "elevation": elevation,
            "data": raster,
            "profile": profile,
            "file": tif_file
        }

    except Exception as e:

        print("Groundwater download failed")
        print(e)

        return {}
