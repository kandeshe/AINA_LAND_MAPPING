import matplotlib.pyplot as plt


def create_rainfall_maps(rainfall_data, output_folder):

    print("\nGenerating Rainfall Maps...\n")

    months = list(rainfall_data.keys())

    rainfall = list(rainfall_data.values())

    plt.figure(figsize=(12, 6))

    plt.bar(
        months,
        rainfall
    )

    plt.title(
        "Monthly Rainfall"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Rainfall (mm)"
    )

    plt.xticks(
        rotation=45
    )

    plt.tight_layout()

    plt.savefig(
        output_folder / "Monthly_Rainfall.png",
        dpi=300
    )

    plt.close()

    plt.figure(figsize=(12, 6))

    plt.plot(
        months,
        rainfall,
        marker="o",
        linewidth=2
    )

    plt.title(
        "Rainfall Trend"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Rainfall (mm)"
    )

    plt.grid(True)

    plt.xticks(
        rotation=45
    )

    plt.tight_layout()

    plt.savefig(
        output_folder / "Rainfall_Trend.png",
        dpi=300
    )

    plt.close()

    print("Monthly Rainfall Chart Saved")

    print("Rainfall Trend Saved")

    print("\nRainfall Visualization Completed")
