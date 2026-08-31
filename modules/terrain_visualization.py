import numpy as np
import rasterio
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.colors import LightSource

def generate_dem_image(clipped_dem, terrain_folder):

    print("\nGenerating DEM Image...")

    with rasterio.open(clipped_dem) as src:

        dem = src.read(1).astype(np.float32)

        nodata = src.nodata

        if nodata is not None:
            dem[dem == nodata] = np.nan

    plt.figure(figsize=(8, 8))

    image = plt.imshow(
        dem,
        cmap="terrain"
    )

    plt.colorbar(
        image,
        label="Elevation (m)"
    )

    plt.title("Digital Elevation Model")

    plt.axis("off")

    dem_png = Path(terrain_folder) / "DEM.png"

    plt.savefig(
        dem_png,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print("DEM Image Saved")

def generate_hillshade(clipped_dem, terrain_folder):

     print("\nGenerating Hillshade...")

     with rasterio.open(clipped_dem) as src:

        dem = src.read(1).astype(np.float32)

        nodata = src.nodata

        if nodata is not None:
            dem[dem == nodata] = np.nan

     ls = LightSource(
        azdeg=315,
        altdeg=45
    )
     hillshade = ls.hillshade(
        dem,
        vert_exag=1,
        dx=1,
        dy=1
    )

     plt.figure(figsize=(8, 8))

     plt.imshow(
        hillshade,
        cmap="gray"
    )

     plt.title("Hillshade")

     plt.axis("off")

     hillshade_png = Path(terrain_folder) / "Hillshade.png"

     plt.savefig(
        hillshade_png,
        dpi=300,
        bbox_inches="tight"
    )

     plt.close()

     print("Hillshade Saved")
