from pathlib import Path

from .soil_download import download_soil_data
from .soil_extract import extract_soil_layers
from .soil_visualization import create_soil_maps
from .soil_statistics import generate_soil_statistics


def generate_soil(config):

    print("\n==========================")
    print("Soil Module")
    print("==========================")

    output = Path(config["output_folder"])

    soil_folder = output / "Soil"

    soil_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    soil_files = download_soil_data(
        config,
        soil_folder
    )

    layers = extract_soil_layers(
        soil_files,
        soil_folder
    )

    create_soil_maps(
        layers,
        soil_folder
    )

    generate_soil_statistics(
        layers,
        soil_folder
    )

    print("\nSoil Module Completed Successfully.")
