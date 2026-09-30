from pathlib import Path
import numpy as np

from .soil_download import download_soil_data
from .soil_extract import extract_soil_layers
from .soil_visualization import create_soil_maps
from .soil_statistics import (
    generate_soil_statistics,
    SOIL_CONVERSIONS
)


def generate_soil(config):

    print("\n==========================")
    print("Soil Module")
    print("==========================")

    output = Path(
        config["output_folder"]
    )

    soil_folder = output / "Soil"

    soil_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # ==========================================================
    # DOWNLOAD
    # ==========================================================

    soil_files = download_soil_data(
        config,
        soil_folder
    )

    # ==========================================================
    # EXTRACT
    # ==========================================================

    layers = extract_soil_layers(
        soil_files,
        soil_folder
    )

    # ==========================================================
    # VISUALIZATION
    # ==========================================================

    create_soil_maps(
        layers,
        soil_folder
    )

    # ==========================================================
    # STATISTICS
    # ==========================================================

    generate_soil_statistics(
        layers,
        soil_folder
    )

    # ==========================================================
    # CENTRAL SOIL RESULT
    # ==========================================================

    soil_result = {

        "ph": None,

        "organic_carbon": None,

        "nitrogen": None,

        "clay": None,

        "sand": None,

        "silt": None,

        "bulk_density": None,

        "cec": None

    }

    field_mapping = {

        "phh2o": "ph",

        "soc": "organic_carbon",

        "nitrogen": "nitrogen",

        "clay": "clay",

        "sand": "sand",

        "silt": "silt",

        "bdod": "bulk_density",

        "cec": "cec"

    }

    for layer_name, result_key in field_mapping.items():

        if layer_name not in layers:
            continue

        raw_value = layers[layer_name].get(
            "value"
        )

        if raw_value is None:
            continue

        try:

            raw_value = float(
                raw_value
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        if not np.isfinite(raw_value):
            continue

        conversion = SOIL_CONVERSIONS.get(
            layer_name,
            1.0
        )

        soil_result[result_key] = (
            raw_value * conversion
        )

    # ==========================================================
    # PRINT CENTRAL RESULT
    # ==========================================================

    print(
        "\n========== CENTRAL SOIL RESULT =========="
    )

    for key, value in soil_result.items():

        print(
            f"{key} : {value}"
        )

    print(
        "\nSoil Module Completed Successfully."
    )

    return soil_result
