import json
import numpy as np
import rasterio

from rasterio.transform import from_origin


def extract_soil_layers(soil_files, output_folder):

    print("\nExtracting Soil Layers...\n")

    layers = {}

    pixel_size = 0.0001

    for layer_name, files in soil_files.items():

        try:

            with open(files["json"], "r") as f:

                data = json.load(f)

            value = np.nan

            properties = data.get("properties", {})

            layers_data = properties.get("layers", [])

            if len(layers_data) > 0:

                depths = layers_data[0].get("depths", [])

                if len(depths) > 0:

                    values = depths[0].get("values", {})

                    value = values.get("mean", np.nan)

            raster = np.full(
                (100, 100),
                value,
                dtype=np.float32
            )

            transform = from_origin(
                0,
                0,
                pixel_size,
                pixel_size
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

            with rasterio.open(
                files["tif"],
                "w",
                **profile
            ) as dst:

                dst.write(
                    raster,
                    1
                )

            layers[layer_name] = {

                "data": raster,

                "profile": profile,

                "value": value,

                "file": files["tif"]

            }

            print(
                f"{layer_name} : {value}"
            )

        except Exception as e:

            print(f"Failed : {layer_name}")

            print(e)

    print("\nExtraction Complete")

    return layers
