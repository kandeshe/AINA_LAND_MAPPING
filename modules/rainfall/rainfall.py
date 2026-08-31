from pathlib import Path

from .rainfall_download import download_rainfall_data
from .rainfall_visualization import create_rainfall_maps
from .rainfall_statistics import generate_rainfall_statistics


def generate_rainfall(config):

    print("\n==========================")
    print("Rainfall Module")
    print("==========================")

    output_folder = Path(config["output_folder"])

    rainfall_folder = output_folder / "Rainfall"

    rainfall_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    rainfall_data = download_rainfall_data(
        config,
        rainfall_folder
    )

    create_rainfall_maps(
        rainfall_data,
        rainfall_folder
    )

    generate_rainfall_statistics(
        rainfall_data,
        rainfall_folder
    )

    print("\nRainfall Module Completed Successfully.")
