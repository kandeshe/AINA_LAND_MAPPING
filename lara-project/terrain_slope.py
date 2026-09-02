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

    # Pixel size in x and y directions
    xres = transform.a
    yres = abs(transform.e)

    # Calculate terrain gradients
    dz_dy, dz_dx = np.gradient(dem, yres, xres)

    # Slope in radians
    slope_rad = np.arctan(
        np.sqrt(dz_dx**2 + dz_dy**2)
    )

    # Convert to degrees
    slope_deg = np.degrees(slope_rad)

    # Save GeoTIFF
    slope_tif = Path(terrain_folder) / "Slope.tif"

    profile = {
        "driver": "GTiff",
        "height": slope_deg.shape[0],
        "width": slope_deg.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": src.crs,
        "transform": transform
    }

    with rasterio.open(slope_tif, "w", **profile) as dst:
        dst.write(slope_deg.astype(np.float32), 1)

    # Save PNG
    plt.figure(figsize=(8, 8))

    image = plt.imshow(
        slope_deg,
        cmap="YlOrRd"
    )

    plt.colorbar(
        image,
        label="Slope (degrees)"
    )

    plt.title("Slope Map")

    plt.axis("off")

    slope_png = Path(terrain_folder) / "Slope.png"

    plt.savefig(
        slope_png,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print("Slope Map Saved")

    # Summary statistics
    valid = slope_deg[np.isfinite(slope_deg)]

    print("\n========== SLOPE SUMMARY ==========")
    print(f"Minimum Slope : {valid.min():.2f}°")
    print(f"Maximum Slope : {valid.max():.2f}°")
    print(f"Average Slope : {valid.mean():.2f}°")
