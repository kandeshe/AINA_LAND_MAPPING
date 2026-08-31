import matplotlib.pyplot as plt
import numpy as np


def create_groundwater_maps(groundwater, output_folder):

    print("\nGenerating Groundwater Maps...\n")

    if not groundwater:

        print("No groundwater data available.")

        return

    data = groundwater["data"]

    valid = data[np.isfinite(data)]

    plt.figure(figsize=(8, 6))

    plt.imshow(
        data,
        cmap="Blues_r"
    )

    plt.colorbar(
        label="Groundwater Depth (m)"
    )

    plt.title(
        "Estimated Groundwater Depth"
    )

    plt.tight_layout()

    plt.savefig(
        output_folder / "Groundwater_Depth.png",
        dpi=300
    )

    plt.close()

    plt.figure(figsize=(7, 5))

    plt.hist(
        valid.flatten(),
        bins=20
    )

    plt.xlabel(
        "Depth (m)"
    )

    plt.ylabel(
        "Frequency"
    )

    plt.title(
        "Groundwater Depth Distribution"
    )

    plt.tight_layout()

    plt.savefig(
        output_folder / "Groundwater_Histogram.png",
        dpi=300
    )

    plt.close()

    recharge = groundwater["recharge"]

    plt.figure(figsize=(5, 5))

    plt.pie(
        [recharge, 100 - recharge],
        labels=[
            "Recharge Potential",
            "Remaining"
        ],
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title(
        "Groundwater Recharge Potential"
    )

    plt.tight_layout()

    plt.savefig(
        output_folder / "Recharge_Potential.png",
        dpi=300
    )

    plt.close()

    print("Groundwater Depth Map Saved")

    print("Groundwater Histogram Saved")

    print("Recharge Potential Chart Saved")

    print("\nGroundwater Visualization Completed")
