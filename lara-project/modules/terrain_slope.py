import numpy as np
import rasterio
import matplotlib.pyplot as plt

from pathlib import Path


def generate_slope(clipped_dem, terrain_folder):

    print("\nGenerating Slope Map...")

    with rasterio.open(clipped_dem) as src:

        dem = src.read(1).astype(np.float32)

        nodata = src.nodata

        if nodata is not None:
            dem[dem == nodata] = np.nan

        transform = src.transform
        profile = src.profile.copy()

    xres = transform.a
    yres = abs(transform.e)
    np.gradient(dem, yres, xres)
    dz_dy, dz_dx = np.gradient(dem, yres, xres)

    slope_rad = np.arctan(
        np.sqrt(dz_dx**2 + dz_dy**2)
    )

    slope_deg = np.degrees(slope_rad)

    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1
    )

    slope_tif = Path(terrain_folder) / "Slope.tif"

    with rasterio.open(slope_tif, "w", **profile) as dst:
        dst.write(slope_deg.astype(np.float32), 1)

    plt.figure(figsize=(8, 8))

    img = plt.imshow(
        slope_deg,
        cmap="YlOrRd"
    )

    plt.colorbar(img, label="Slope (degrees)")

    plt.title("Slope Map")

    plt.axis("off")

    slope_png = Path(terrain_folder) / "Slope.png"

    plt.savefig(
        slope_png,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    valid = slope_deg[np.isfinite(slope_deg)]

    print("Slope Map Saved")
    print(f"Minimum Slope : {valid.min():.2f}°")
    print(f"Maximum Slope : {valid.max():.2f}°")
    print(f"Average Slope : {valid.mean():.2f}°")
