from pathlib import Path
import rasterio
import matplotlib.pyplot as plt
import numpy as np
import numpy as np
from rasterio.warp import reproject, Resampling


def resample_to_match(src_dataset, destination_profile):

    source = src_dataset.read(1).astype(np.float32)

    destination = np.empty(
        (
            destination_profile["height"],
            destination_profile["width"]
        ),
        dtype=np.float32
    )

    reproject(
        source=source,
        destination=destination,
        src_transform=src_dataset.transform,
        src_crs=src_dataset.crs,
        dst_transform=destination_profile["transform"],
        dst_crs=destination_profile["crs"],
        resampling=Resampling.bilinear
    )

    return destination

def normalize(array):

    minimum = np.nanmin(array)
    maximum = np.nanmax(array)

    if maximum == minimum:
        return np.zeros_like(array)

    return (array - minimum) / (maximum - minimum)


def analyze_flood_risk(config, output_folder):

    print("\nLoading datasets...")

    base = Path(config["output_folder"])

    terrain = base / "Terrain"
    hydrology = base / "Hydrology"
    rainfall = base / "Rainfall"

    with rasterio.open(terrain / "Slope.tif") as src:
        slope = src.read(1).astype(np.float32)
        profile = src.profile

    with rasterio.open(hydrology / "FlowAccumulation.tif") as src:
        flow = resample_to_match(src, profile)

    rainfall_csv = rainfall / "RainfallStatistics.csv"

    annual_rainfall = 0

    if rainfall_csv.exists():

        import csv

        with open(rainfall_csv) as f:

            reader = csv.reader(f)

            next(reader)

            for row in reader:

                try:
                    annual_rainfall += float(row[1])
                except:
                    pass

    rainfall_layer = np.full(
        slope.shape,
        annual_rainfall,
        dtype=np.float32
    )

    print("Calculating Flood Risk...")

    slope_score = 1 - normalize(slope)

    flow_score = normalize(flow)

    rainfall_score = normalize(rainfall_layer)

    flood_score = (
        0.40 * flow_score +
        0.35 * rainfall_score +
        0.25 * slope_score
    ) * 100

    flood_class = np.zeros_like(
        flood_score,
        dtype=np.uint8
    )

    flood_class[flood_score < 20] = 1
    flood_class[(flood_score >= 20) & (flood_score < 40)] = 2
    flood_class[(flood_score >= 40) & (flood_score < 60)] = 3
    flood_class[(flood_score >= 60) & (flood_score < 80)] = 4
    flood_class[flood_score >= 80] = 5

    profile.update(
        dtype=rasterio.float32,
        count=1
    )

    with rasterio.open(
        output_folder / "FloodRisk.tif",
        "w",
        **profile
    ) as dst:

        dst.write(
            flood_score.astype(np.float32),
            1
        )

    profile.update(
    dtype=rasterio.uint8,
    nodata=0
)

    with rasterio.open(
    output_folder / "FloodClasses.tif",
    "w",
    **profile
) as dst:

     dst.write(
        flood_class.astype(rasterio.uint8),
        1
    )

    plt.figure(figsize=(8,6))

    plt.imshow(
        flood_score,
        cmap="Blues"
    )

    plt.colorbar(label="Flood Risk")

    plt.title("Flood Risk")

    plt.tight_layout()

    plt.savefig(
        output_folder / "FloodRisk.png",
        dpi=300
    )

    plt.close()

    print("Flood Risk Raster Saved")

    print("Flood Classes Saved")

    print("Flood Map Saved")

    return {

        "score": flood_score,

        "class": flood_class,

        "annual_rainfall": annual_rainfall

    }
