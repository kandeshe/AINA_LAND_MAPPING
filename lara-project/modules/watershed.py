import numpy as np
import rasterio
import matplotlib.pyplot as plt

from pathlib import Path
from scipy import ndimage

def generate_watersheds(config):

    print("\n==========================")
    print("Watershed Module")
    print("==========================")

    output_folder = Path(config["output_folder"])

    hydrology_folder = output_folder / "Hydrology"

    watershed_folder = output_folder / "Watershed"

    watershed_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    accumulation_file = hydrology_folder / "FlowAccumulation.tif"

    if not accumulation_file.exists():

        print("Flow Accumulation not found.")

        return

    with rasterio.open(accumulation_file) as src:

        accumulation = src.read(1)

        profile = src.profile

    print("Reading Flow Accumulation...")

    threshold = np.percentile(
        accumulation[np.isfinite(accumulation)],
        95
    )

    streams = accumulation >= threshold

    print("Extracting Stream Network...")
    print("Labelling Watersheds...")

    structure = np.array(
        [
            [1, 1, 1],
            [1, 1, 1],
            [1, 1, 1]
        ],
        dtype=np.uint8
    )

    labels, number_of_watersheds = ndimage.label(
        streams,
        structure=structure
    )

    print(f"Watersheds Found : {number_of_watersheds}")

    watershed = labels.astype(np.int32)

    profile.update(
        dtype=rasterio.int32,
        count=1,
        nodata=0
    )

    watershed_file = watershed_folder / "Watersheds.tif"

    with rasterio.open(
        watershed_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            watershed,
            1
        )

    print("Watershed Raster Saved")

    plt.figure(figsize=(10,10))

    plt.imshow(
        watershed,
        cmap="tab20"
    )

    plt.colorbar(
        label="Watershed ID"
    )

    plt.title("Watersheds")

    plt.tight_layout()

    plt.savefig(
        watershed_folder / "Watersheds.png",
        dpi=300
    )

    plt.close()

    print("Watershed Image Saved")

    print("\nCalculating Watershed Statistics...")

    valid_ids = np.unique(watershed)

    valid_ids = valid_ids[valid_ids > 0]

    pixel_width = abs(profile["transform"].a)
    pixel_height = abs(profile["transform"].e)

    pixel_area = pixel_width * pixel_height

    stats_file = watershed_folder / "Watershed_Statistics.txt"

    with open(stats_file, "w") as f:

        f.write("WATERSHED ANALYSIS REPORT\n")
        f.write("=============================\n\n")

        f.write(f"Total Watersheds : {len(valid_ids)}\n\n")

        total_area = 0

        for wid in valid_ids:

            count = np.sum(watershed == wid)

            area_sq_m = count * pixel_area

            area_hectares = area_sq_m / 10000

            area_sqkm = area_sq_m / 1000000

            total_area += area_sqkm

            f.write(f"Watershed ID : {wid}\n")
            f.write(f"Pixels       : {count}\n")
            f.write(f"Area (sq.m)  : {area_sq_m:.2f}\n")
            f.write(f"Area (Ha)    : {area_hectares:.2f}\n")
            f.write(f"Area (sq.km) : {area_sqkm:.4f}\n")
            f.write("----------------------------------\n")

        f.write("\nSUMMARY\n")
        f.write("=============================\n")
        f.write(f"Total Watersheds : {len(valid_ids)}\n")
        f.write(f"Combined Area    : {total_area:.4f} sq.km\n")

    print("Statistics Saved")

    print("\n========== WATERSHED SUMMARY ==========")
    print(f"Watersheds Detected : {len(valid_ids)}")
    print(f"Combined Area       : {total_area:.4f} sq.km")

    print("\nWatershed Module Completed Successfully.")
