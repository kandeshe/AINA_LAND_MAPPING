import numpy as np
import rasterio
from pathlib import Path
import matplotlib.pyplot as plt


def generate_tri(dem_file, terrain_folder):

    print("\nGenerating Terrain Ruggedness Index (TRI)...")

    with rasterio.open(dem_file) as src:

        dem = src.read(1).astype(np.float32)

        nodata = src.nodata

        if nodata is not None:
            dem[dem == nodata] = np.nan

        profile = src.profile

    rows, cols = dem.shape

    tri = np.full((rows, cols), np.nan, dtype=np.float32)

    for r in range(1, rows - 1):

        for c in range(1, cols - 1):

            window = dem[r-1:r+2, c-1:c+2]

            if np.isnan(window).any():
                continue

            center = window[1, 1]

            diff = np.abs(window - center)

            tri[r, c] = np.mean(diff)

    output_tif = Path(terrain_folder) / "TRI.tif"

    profile.update(
        dtype=rasterio.float32,
        count=1
    )

    with rasterio.open(
        output_tif,
        "w",
        **profile
    ) as dst:

        dst.write(tri, 1)

    plt.figure(figsize=(8,8))

    plt.imshow(tri, cmap="viridis")

    plt.colorbar(label="TRI")

    plt.title("Terrain Ruggedness Index")

    plt.axis("off")

    plt.savefig(
        Path(terrain_folder) / "TRI.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    valid = tri[np.isfinite(tri)]

    with open(
        Path(terrain_folder) / "TRI_statistics.txt",
        "w"
    ) as f:

        f.write("========== TRI ==========\n\n")
        f.write(f"Minimum TRI : {valid.min():.2f}\n")
        f.write(f"Maximum TRI : {valid.max():.2f}\n")
        f.write(f"Average TRI : {valid.mean():.2f}\n")

    print("TRI Generated")
    print("Minimum TRI :", valid.min())
    print("Maximum TRI :", valid.max())
    print("Average TRI :", valid.mean())
