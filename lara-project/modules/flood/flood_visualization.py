import matplotlib.pyplot as plt
import numpy as np


def create_flood_maps(flood_data, output_folder):

    print("\nGenerating Flood Visualizations...\n")

    score = flood_data["score"]
    classes = flood_data["class"]

    valid_score = score[np.isfinite(score)]

    # Flood Risk Score
    plt.figure(figsize=(8, 6))
    plt.imshow(score, cmap="Blues")
    plt.colorbar(label="Flood Risk Score")
    plt.title("Flood Risk Score")
    plt.tight_layout()
    plt.savefig(output_folder / "Flood_Risk_Score.png", dpi=300)
    plt.close()

    # Flood Classes
    plt.figure(figsize=(8, 6))
    plt.imshow(classes, cmap="RdYlBu_r", vmin=1, vmax=5)

    cbar = plt.colorbar()
    cbar.set_ticks([1, 2, 3, 4, 5])
    cbar.set_ticklabels([
        "Very Low",
        "Low",
        "Moderate",
        "High",
        "Very High"
    ])

    plt.title("Flood Risk Classes")
    plt.tight_layout()
    plt.savefig(output_folder / "Flood_Risk_Classes.png", dpi=300)
    plt.close()

    # Histogram
    plt.figure(figsize=(8, 5))
    plt.hist(valid_score.flatten(), bins=20)
    plt.xlabel("Flood Risk Score")
    plt.ylabel("Frequency")
    plt.title("Flood Risk Distribution")
    plt.tight_layout()
    plt.savefig(output_folder / "Flood_Histogram.png", dpi=300)
    plt.close()

    # Pie Chart (ignore NoData = 0)
    valid_classes = classes[classes > 0]

    unique, counts = np.unique(valid_classes, return_counts=True)

    names = {
        1: "Very Low",
        2: "Low",
        3: "Moderate",
        4: "High",
        5: "Very High"
    }

    labels = [names[int(i)] for i in unique]

    plt.figure(figsize=(6, 6))
    plt.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90
    )
    plt.title("Flood Risk Distribution")
    plt.tight_layout()
    plt.savefig(output_folder / "Flood_PieChart.png", dpi=300)
    plt.close()

    print("Flood Risk Score Image Saved")
    print("Flood Class Image Saved")
    print("Flood Histogram Saved")
    print("Flood Pie Chart Saved")
    print("\nFlood Visualization Completed")
