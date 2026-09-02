import numpy as np
import rasterio
from pathlib import Path
import matplotlib.pyplot as plt

# --------------------------------------------------------
# D8 Direction Codes
#
# 32 64 128
# 16  X   1
#  8  4   2
# --------------------------------------------------------

DIRECTIONS = [
    (-1, 1,   128),
    (0, 1,      1),
    (1, 1,      2),
    (1, 0,      4),
    (1, -1,     8),
    (0, -1,    16),
    (-1, -1,   32),
    (-1, 0,    64)
]


def generate_hydrology(config):

    print("\n==========================")
    print("Hydrology Module")
    print("==========================")

    terrain_folder = Path(config["output_folder"]) / "Terrain"

    hydrology_folder = Path(config["output_folder"]) / "Hydrology"

    hydrology_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    dem_file = terrain_folder / "DEM_UTM.tif"

    if not dem_file.exists():

        print("DEM not found.")

        return

    with rasterio.open(dem_file) as src:

        dem = src.read(1).astype(np.float32)

        profile = src.profile

        nodata = src.nodata

    if nodata is not None:

        dem[dem == nodata] = np.nan

    rows, cols = dem.shape

    flow_direction = np.zeros(
        (rows, cols),
        dtype=np.uint8
    )

    print("\nCalculating Flow Direction...")
        
    for r in range(1, rows - 1):

        for c in range(1, cols - 1):

            if np.isnan(dem[r, c]):
                continue

            center = dem[r, c]

            steepest = 0

            direction = 0

            for dr, dc, code in DIRECTIONS:

                nr = r + dr
                nc = c + dc

                if np.isnan(dem[nr, nc]):
                    continue

                diff = center - dem[nr, nc]

                if diff > steepest:

                    steepest = diff

                    direction = code

            flow_direction[r, c] = direction

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0
    )

    direction_file = hydrology_folder / "FlowDirection.tif"

    with rasterio.open(
        direction_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            flow_direction,
            1
        )

    print("Flow Direction Created")

    print("\nCalculating Flow Accumulation...")

    flow_accumulation = np.ones(
        (rows, cols),
        dtype=np.float32
    )

    changed = True

    while changed:

        changed = False

        for r in range(1, rows - 1):

            for c in range(1, cols - 1):

                direction = flow_direction[r, c]

                if direction == 0:
                    continue

                if direction == 1:
                    nr, nc = r, c + 1

                elif direction == 2:
                    nr, nc = r + 1, c + 1

                elif direction == 4:
                    nr, nc = r + 1, c

                elif direction == 8:
                    nr, nc = r + 1, c - 1

                elif direction == 16:
                    nr, nc = r, c - 1

                elif direction == 32:
                    nr, nc = r - 1, c - 1

                elif direction == 64:
                    nr, nc = r - 1, c

                elif direction == 128:
                    nr, nc = r - 1, c + 1

                else:
                    continue

                new_value = flow_accumulation[r, c] + 1

                if new_value > flow_accumulation[nr, nc]:

                    flow_accumulation[nr, nc] = new_value

                    changed = True

    profile.update(
        dtype=rasterio.float32,
        count=1,
        nodata=np.nan
    )

    accumulation_file = (
        hydrology_folder /
        "FlowAccumulation.tif"
    )

    with rasterio.open(
        accumulation_file,
        "w",
        **profile
    ) as dst:

        dst.write(
            flow_accumulation.astype(np.float32),
            1
        )

    print("Flow Accumulation Created")

    valid = flow_accumulation[
        np.isfinite(flow_accumulation)
    ]

    print("\n========== HYDROLOGY ==========")

    print("Minimum :", valid.min())

    print("Maximum :", valid.max())

    print("Average :", valid.mean())

    print("\nGenerating PNG Images...")

    # --------------------------------------------------
    # Flow Direction PNG
    # --------------------------------------------------

    plt.figure(figsize=(8, 8))

    plt.imshow(flow_direction, cmap="tab20")

    plt.colorbar(label="Direction Code")

    plt.title("Flow Direction")

    plt.tight_layout()

    plt.savefig(
        hydrology_folder / "FlowDirection.png",
        dpi=300
    )

    plt.close()

    # --------------------------------------------------
    # Flow Accumulation PNG
    # --------------------------------------------------

    display = np.where(
        flow_accumulation > 0,
        np.log1p(flow_accumulation),
        0
    )

    plt.figure(figsize=(8, 8))

    plt.imshow(display, cmap="Blues")

    plt.colorbar(label="Log Flow Accumulation")

    plt.title("Flow Accumulation")

    plt.tight_layout()

    plt.savefig(
        hydrology_folder / "FlowAccumulation.png",
        dpi=300
    )

    plt.close()

    print("PNG Images Created")

    # --------------------------------------------------
    # Simple Stream Extraction
    # --------------------------------------------------

    threshold = np.percentile(valid, 95)

    streams = np.where(
        flow_accumulation >= threshold,
        1,
        0
    ).astype(np.uint8)

    profile.update(
        dtype=rasterio.uint8,
        count=1,
        nodata=0
    )

    stream_file = hydrology_folder / "Streams.tif"

    with rasterio.open(
        stream_file,
        "w",
        **profile
    ) as dst:

        dst.write(streams, 1)

    plt.figure(figsize=(8, 8))

    plt.imshow(streams, cmap="gray")

    plt.title("Extracted Streams")

    plt.tight_layout()

    plt.savefig(
        hydrology_folder / "Streams.png",
        dpi=300
    )

    plt.close()

    # --------------------------------------------------
    # Statistics Report
    # --------------------------------------------------

    stats_file = hydrology_folder / "Hydrology_Statistics.txt"

    with open(stats_file, "w") as f:

        f.write("HYDROLOGY REPORT\n")
        f.write("============================\n\n")

        f.write(f"Minimum Flow Accumulation : {valid.min():.2f}\n")
        f.write(f"Maximum Flow Accumulation : {valid.max():.2f}\n")
        f.write(f"Average Flow Accumulation : {valid.mean():.2f}\n")
        f.write(f"Median Flow Accumulation  : {np.median(valid):.2f}\n")
        f.write(f"Standard Deviation        : {valid.std():.2f}\n")
        f.write(f"Stream Threshold          : {threshold:.2f}\n")

    print("Statistics Saved")

    print("\nHydrology Module Completed Successfully.")
