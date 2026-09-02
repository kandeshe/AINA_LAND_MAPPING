from pathlib import Path

from .flood_analysis import analyze_flood_risk
from .flood_visualization import create_flood_maps
from .flood_statistics import generate_flood_statistics


def generate_flood(config):

    print("\n==========================")
    print("Flood Risk Module")
    print("==========================")

    output_folder = Path(config["output_folder"])

    flood_folder = output_folder / "Flood"

    flood_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    flood_data = analyze_flood_risk(
        config,
        flood_folder
    )

    create_flood_maps(
        flood_data,
        flood_folder
    )

    generate_flood_statistics(
        flood_data,
        flood_folder
    )

    print("\nFlood Module Completed Successfully.")
