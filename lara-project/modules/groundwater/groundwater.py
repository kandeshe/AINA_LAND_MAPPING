from pathlib import Path

from .groundwater_download import download_groundwater_data
from .groundwater_visualization import create_groundwater_maps
from .groundwater_statistics import generate_groundwater_statistics


def generate_groundwater(config):

    print("\n==========================")
    print("Groundwater Module")
    print("==========================")

    output_folder = Path(config["output_folder"])

    groundwater_folder = output_folder / "Groundwater"

    groundwater_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    groundwater_data = download_groundwater_data(
        config,
        groundwater_folder
    )

    create_groundwater_maps(
        groundwater_data,
        groundwater_folder
    )

    generate_groundwater_statistics(
        groundwater_data,
        groundwater_folder
    )

    print("\nGroundwater Module Completed Successfully.")
