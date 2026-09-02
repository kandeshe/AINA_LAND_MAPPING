import numpy as np
import rasterio
import matplotlib.pyplot as plt

from pathlib import Path
from rasterio.warp import reproject, Resampling

def read_raster(filename):

    with rasterio.open(filename) as src:

        data = src.read(1).astype(np.float32)

        profile = src.profile

        nodata = src.nodata

    if nodata is not None:

        data[data == nodata] = np.nan

    return data, profile


def normalize(arr):

    valid = np.isfinite(arr)

    out = np.zeros_like(arr, dtype=np.float32)

    minimum = np.nanmin(arr)

    maximum = np.nanmax(arr)

    if maximum == minimum:

        out[:] = 0

        out[~valid] = np.nan

        return out

    out[valid] = (
        arr[valid] - minimum
    ) / (
        maximum - minimum
    )

    out[~valid] = np.nan

    return out
def resample_to_match(source, src_profile, target_profile):

    destination = np.empty(
        (
            target_profile["height"],
            target_profile["width"]
        ),
        dtype=np.float32
    )

    reproject(
        source=source,
        destination=destination,
        src_transform=src_profile["transform"],
        src_crs=src_profile["crs"],
        dst_transform=target_profile["transform"],
        dst_crs=target_profile["crs"],
        resampling=Resampling.bilinear
    )

    return destination

def generate_land_suitability(config):

    print("\n==========================")
    print("Land Suitability Module")
    print("==========================")

    output = Path(config["output_folder"])
    print("Output Folder :", output)
    print("Terrain Folder:", output / "Terrain")
    print("Hydrology Folder:", output / "Hydrology")
    print("Satellite Folder:", output / "Satellite")
    print("Climate Folder:", output / "Climate")

    terrain = output / "Terrain"

    hydrology = output / "Hydrology"

    satellite = output

    climate = output / "Climate"

    suitability = output / "LandSuitability"

    suitability.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Loading datasets...")

    slope, slope_profile = read_raster(
    terrain / "Slope.tif"
    )

    profile = slope_profile

    tri, tri_profile = read_raster(
    terrain / "TRI.tif"
)

    flow, flow_profile = read_raster(
    hydrology / "FlowAccumulation.tif"
)

    ndvi, ndvi_profile = read_raster(
    satellite / "NDVI" / "NDVI.tif"
)

    ndwi, ndwi_profile = read_raster(
    satellite / "NDWI" / "NDWI.tif"
)

    temperature, temp_profile = read_raster(
    climate / "Temperature.tif"
)

    print("Datasets Loaded")
    print("Resampling NDVI...")
    ndvi = resample_to_match(
    ndvi,
    ndvi_profile,
    profile
)

    print("Resampling NDWI...")
    ndwi = resample_to_match(
    ndwi,
    ndwi_profile,
    profile
)

    print("Resampling Complete")
    print("Slope       :", slope.shape)
    print("TRI         :", tri.shape)
    print("Flow        :", flow.shape)
    print("NDVI        :", ndvi.shape)
    print("NDWI        :", ndwi.shape)
    print("Temperature :", temperature.shape)

    print("Normalizing Layers...")

    slope_n = 1 - normalize(slope)

    tri_n = 1 - normalize(tri)

    ndvi_n = normalize(ndvi)

    ndwi_n = normalize(ndwi)

    flow_n = normalize(
        np.log1p(flow)
    )

    temp_n = 1 - normalize(
        np.abs(
            temperature - 25
        )
    )

    print("Calculating Land Suitability Score...")

    suitability_score = (
        (slope_n * 0.25) +
        (ndvi_n * 0.20) +
        (ndwi_n * 0.15) +
        (flow_n * 0.15) +
        (temp_n * 0.15) +
        (tri_n * 0.10)
    )

    suitability_score *= 100.0

    suitability_score[
        ~np.isfinite(suitability_score)
    ] = np.nan

    print("Suitability Score Calculated")

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=np.nan
    )

    score_file = (
        suitability /
        "SuitabilityScore.tif"
    )

    with rasterio.open(
        score_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            suitability_score.astype(np.float32),
            1
        )

    print("Suitability Score Raster Saved")

    print("Creating Suitability Classes...")

    classes = np.zeros(
        suitability_score.shape,
        dtype=np.uint8
    )

    classes[
        (suitability_score >= 0) &
        (suitability_score < 20)
    ] = 1

    classes[
        (suitability_score >= 20) &
        (suitability_score < 40)
    ] = 2

    classes[
        (suitability_score >= 40) &
        (suitability_score < 60)
    ] = 3

    classes[
        (suitability_score >= 60) &
        (suitability_score < 80)
    ] = 4

    classes[
        suitability_score >= 80
    ] = 5

    classes[
        np.isnan(suitability_score)
    ] = 0

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0
    )

    class_file = (
        suitability /
        "SuitabilityClasses.tif"
    )

    with rasterio.open(
        class_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            classes,
            1
        )

    print("Suitability Classes Saved")
    print("Generating Suitability Maps...")

    valid_scores = suitability_score[
        np.isfinite(suitability_score)
    ]

    # ------------------------------------
    # Suitability Score Map
    # ------------------------------------

    plt.figure(figsize=(10, 8))

    plt.imshow(
        suitability_score,
        cmap="RdYlGn",
        vmin=0,
        vmax=100
    )

    plt.colorbar(
        label="Suitability Score"
    )

    plt.title("Land Suitability Score")

    plt.tight_layout()

    plt.savefig(
        suitability / "SuitabilityScore.png",
        dpi=300
    )

    plt.close()

    print("Suitability Score Image Saved")

    # ------------------------------------
    # Suitability Class Map
    # ------------------------------------

    plt.figure(figsize=(10, 8))

    plt.imshow(
        classes,
        cmap="RdYlGn",
        interpolation="nearest",
        vmin=1,
        vmax=5
    )

    cbar = plt.colorbar(
        ticks=[1, 2, 3, 4, 5]
    )

    cbar.set_ticklabels([
        "Very Poor",
        "Poor",
        "Moderate",
        "Good",
        "Excellent"
    ])

    plt.title("Land Suitability Classes")

    plt.tight_layout()

    plt.savefig(
        suitability / "SuitabilityClasses.png",
        dpi=300
    )

    plt.close()

    print("Suitability Class Image Saved")

    print("Generating Report...")

    pixel_width = abs(
        profile["transform"].a
    )

    pixel_height = abs(
        profile["transform"].e
    )

    pixel_area = pixel_width * pixel_height

    report = (
        suitability /
        "Suitability_Report.txt"
    )

    class_names = {
        1: "Very Poor",
        2: "Poor",
        3: "Moderate",
        4: "Good",
        5: "Excellent"
    }

    with open(report, "w") as f:

        f.write(
            "LAND SUITABILITY REPORT\n"
        )

        f.write(
            "==============================\n\n"
        )

        f.write(
            f"Minimum Score : {valid_scores.min():.2f}\n"
        )

        f.write(
            f"Maximum Score : {valid_scores.max():.2f}\n"
        )

        f.write(
            f"Average Score : {valid_scores.mean():.2f}\n"
        )

        f.write(
            f"Median Score  : {np.median(valid_scores):.2f}\n"
        )

        f.write(
            f"Standard Deviation : {valid_scores.std():.2f}\n\n"
        )

        f.write(
            "CLASS STATISTICS\n"
        )

        f.write(
            "-----------------------------\n"
        )

        for i in range(1, 6):

            pixels = np.sum(
                classes == i
            )

            area_sq_m = pixels * pixel_area

            area_ha = area_sq_m / 10000

            area_sqkm = area_sq_m / 1000000

            percentage = (
                pixels /
                np.sum(classes > 0)
            ) * 100

            f.write(
                f"{class_names[i]}\n"
            )

            f.write(
                f"Pixels      : {pixels}\n"
            )

            f.write(
                f"Area (Ha)   : {area_ha:.2f}\n"
            )

            f.write(
                f"Area (SqKm) : {area_sqkm:.4f}\n"
            )

            f.write(
                f"Coverage    : {percentage:.2f}%\n"
            )

            f.write(
                "-----------------------------\n"
            )

    print("Report Saved")

    print("\n========== LAND SUITABILITY ==========")

    print(
        f"Minimum Score : {valid_scores.min():.2f}"
    )

    print(
        f"Maximum Score : {valid_scores.max():.2f}"
    )

    print(
        f"Average Score : {valid_scores.mean():.2f}"
    )

    print(
        f"Median Score  : {np.median(valid_scores):.2f}"
    )

    print(
        "\nLand Suitability Module Completed Successfully."
    )
