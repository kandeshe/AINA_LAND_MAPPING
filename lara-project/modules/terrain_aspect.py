import numpy as np
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path


def generate_aspect(dem_file, terrain_folder):

    print("\nGenerating Aspect Map...")

    with rasterio.open(dem_file) as src:

        dem = src.read(1).astype(np.float32)

        nodata = src.nodata

        if nodata is not None:
            dem[dem == nodata] = np.nan

        transform = src.transform

        xres = transform.a
        yres = abs(transform.e)

    dz_dy, dz_dx = np.gradient(dem, yres, xres)

    aspect = np.degrees(np.arctan2(dz_dy, -dz_dx))

    aspect = 90.0 - aspect

    aspect[aspect < 0] += 360

    aspect[np.isnan(dem)] = np.nan

    aspect_tif = Path(terrain_folder) / "aspect.tif"

    with rasterio.open(dem_file) as src:

        profile = src.profile.copy()

        profile.update(
            dtype="float32",
            count=1
        )

        with rasterio.open(
            aspect_tif,
            "w",
            **profile
        ) as dst:

            dst.write(aspect.astype(np.float32), 1)

    plt.figure(figsize=(8, 8))

    plt.imshow(
        aspect,
        cmap="hsv",
        vmin=0,
        vmax=360
    )

    plt.colorbar(label="Aspect (Degrees)")

    plt.title("Terrain Aspect")

    plt.axis("off")

    aspect_png = Path(terrain_folder) / "aspect.png"

    plt.savefig(
        aspect_png,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    valid = aspect[np.isfinite(aspect)]

    print("Aspect Map Saved")

    print(f"Minimum Aspect : {np.min(valid):.2f}°")
    print(f"Maximum Aspect : {np.max(valid):.2f}°")
    print(f"Average Aspect : {np.mean(valid):.2f}°")

    with open(
        Path(terrain_folder) / "aspect_statistics.txt",
        "w"
    ) as f:

        f.write("========== ASPECT ==========\n\n")
        f.write(f"Minimum : {np.min(valid):.2f}\n")
        f.write(f"Maximum : {np.max(valid):.2f}\n")
        f.write(f"Average : {np.mean(valid):.2f}\n")
