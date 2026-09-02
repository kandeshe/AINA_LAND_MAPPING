import numpy as np
import rasterio
import matplotlib.pyplot as plt
from pathlib import Path


def generate_contours(dem_file, terrain_folder):

    print("\nGenerating Contour Map...")

    with rasterio.open(dem_file) as src:

        # Read DEM with NoData automatically masked
        dem = src.read(1, masked=True).astype(np.float32)

        transform = src.transform

    rows, cols = dem.shape

    x = np.arange(cols) * transform.a + transform.c
    y = np.arange(rows) * transform.e + transform.f

    X, Y = np.meshgrid(x, y)

    # Extract only valid values
    valid = dem.compressed()

    if valid.size == 0:
        print("No valid DEM values.")
        return

    print("Minimum DEM :", valid.min())
    print("Maximum DEM :", valid.max())

    minimum = np.floor(valid.min())
    maximum = np.ceil(valid.max())

    elevation_range = maximum - minimum

    if elevation_range < 20:
        interval = 1
    elif elevation_range < 100:
        interval = 5
    elif elevation_range < 500:
        interval = 10
    else:
        interval = 20

    levels = np.arange(minimum, maximum + interval, interval)

    plt.figure(figsize=(8, 8))

    contour = plt.contour(
        X,
        Y,
        dem.filled(np.nan),
        levels=levels,
        colors="black",
        linewidths=0.6
    )

    plt.clabel(
        contour,
        inline=True,
        fontsize=8,
        fmt="%d m"
    )

    plt.imshow(
        dem.filled(np.nan),
        extent=[X.min(), X.max(), Y.min(), Y.max()],
        origin="upper",
        cmap="terrain"
    )

    plt.colorbar(label="Elevation (m)")

    plt.title("Contour Map")

    plt.axis("equal")

    contour_png = Path(terrain_folder) / "contours.png"

    plt.savefig(
        contour_png,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    with open(Path(terrain_folder) / "contours_statistics.txt", "w") as f:

        f.write("========== CONTOURS ==========\n\n")
        f.write(f"Minimum Elevation : {minimum:.2f} m\n")
        f.write(f"Maximum Elevation : {maximum:.2f} m\n")
        f.write(f"Contour Interval : {interval} m\n")
        f.write(f"Number of Contours : {len(levels)}\n")

    print("Contour Map Saved")
    print("Minimum Elevation :", minimum)
    print("Maximum Elevation :", maximum)
    print("Contour Interval :", interval, "m")
    print("Number of Contours :", len(levels))
