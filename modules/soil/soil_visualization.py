import matplotlib.pyplot as plt
import numpy as np


def create_soil_maps(layers, output_folder):

    print("\nGenerating Soil Maps...\n")

    for layer_name, info in layers.items():

        data = info["data"]

        save_folder = output_folder / layer_name.capitalize()

        save_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        valid = data[np.isfinite(data)]

        if valid.size == 0:

            print(f"{layer_name} : No Data")

            continue

        plt.figure(figsize=(8, 6))

        plt.imshow(
            data,
            cmap="terrain"
        )

        plt.colorbar(
            label=layer_name
        )

        plt.title(
            f"{layer_name} Map"
        )

        plt.tight_layout()

        plt.savefig(
            save_folder / f"{layer_name}.png",
            dpi=300
        )

        plt.close()

        plt.figure(figsize=(7, 4))

        plt.hist(
            valid.flatten(),
            bins=20
        )

        plt.title(
            f"{layer_name} Histogram"
        )

        plt.xlabel(layer_name)

        plt.ylabel("Frequency")

        plt.tight_layout()

        plt.savefig(
            save_folder / f"{layer_name}_histogram.png",
            dpi=300
        )

        plt.close()

        print(
            f"{layer_name} Maps Saved"
        )

    print("\nSoil Visualization Completed")
