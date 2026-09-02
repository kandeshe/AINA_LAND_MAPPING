from pathlib import Path
from PIL import Image


# ============================================================
# LARA CNN DATASET CHECKER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR


EXPECTED_CLASSES = [
    "AnnualCrop",
    "Forest",
    "HerbaceousVegetation",
    "Highway",
    "Industrial",
    "Pasture",
    "PermanentCrop",
    "Residential",
    "River",
    "SeaLake"
]


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png"
}


def check_dataset():

    print()
    print("=" * 60)
    print("             LARA CNN DATASET CHECK")
    print("=" * 60)

    print()
    print("Dataset location:")
    print(DATASET_DIR)

    if not DATASET_DIR.exists():

        print()
        print("ERROR: Dataset folder does not exist.")
        return

    # --------------------------------------------------------
    # Find actual class folders
    # --------------------------------------------------------

    class_folders = sorted(
        [
            folder
            for folder in DATASET_DIR.iterdir()
            if folder.is_dir()
        ]
    )

    print()
    print("Detected folders:")
    
    for folder in class_folders:
        print(" -", folder.name)

    # --------------------------------------------------------
    # Check expected classes
    # --------------------------------------------------------

    detected_names = {
        folder.name
        for folder in class_folders
    }

    missing_classes = [
        name
        for name in EXPECTED_CLASSES
        if name not in detected_names
    ]

    extra_classes = [
        name
        for name in detected_names
        if name not in EXPECTED_CLASSES
    ]

    print()
    print("=" * 60)
    print("CLASS VALIDATION")
    print("=" * 60)

    if missing_classes:

        print()
        print("Missing classes:")

        for name in missing_classes:
            print(" -", name)

    else:

        print()
        print("All 10 expected classes are present.")

    if extra_classes:

        print()
        print("Additional folders detected:")

        for name in extra_classes:
            print(" -", name)

    # --------------------------------------------------------
    # Count images
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("IMAGE COUNT")
    print("=" * 60)

    total_images = 0

    class_counts = {}

    corrupted_images = []

    image_sizes = {}

    channel_counts = {}

    for class_name in EXPECTED_CLASSES:

        class_folder = DATASET_DIR / class_name

        if not class_folder.exists():

            class_counts[class_name] = 0

            continue

        images = [
            file
            for file in class_folder.rglob("*")
            if file.is_file()
            and file.suffix.lower() in IMAGE_EXTENSIONS
        ]

        class_counts[class_name] = len(images)

        total_images += len(images)

        print(
            f"{class_name:<25} : {len(images)}"
        )

        # ----------------------------------------------------
        # Inspect images
        # ----------------------------------------------------

        for image_file in images:

            try:

                with Image.open(image_file) as image:

                    image.verify()

                # Open again because verify() closes the image
                with Image.open(image_file) as image:

                    width, height = image.size

                    mode = image.mode

                    image_sizes[
                        (width, height)
                    ] = image_sizes.get(
                        (width, height),
                        0
                    ) + 1

                    if mode == "RGB":

                        channels = 3

                    elif mode == "RGBA":

                        channels = 4

                    elif mode == "L":

                        channels = 1

                    else:

                        channels = mode

                    channel_counts[
                        channels
                    ] = channel_counts.get(
                        channels,
                        0
                    ) + 1

            except Exception as error:

                corrupted_images.append(
                    (
                        str(image_file),
                        str(error)
                    )
                )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)

    print()
    print("Total images :", total_images)

    print()
    print("Image dimensions:")

    for size, count in sorted(
        image_sizes.items()
    ):

        print(
            f"  {size[0]} x {size[1]} : {count}"
        )

    print()
    print("Image channels:")

    for channels, count in sorted(
        channel_counts.items(),
        key=lambda item: str(item[0])
    ):

        print(
            f"  {channels} channels : {count}"
        )

    # --------------------------------------------------------
    # Corrupted image check
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CORRUPTED IMAGE CHECK")
    print("=" * 60)

    if corrupted_images:

        print()
        print(
            f"Corrupted images found: "
            f"{len(corrupted_images)}"
        )

        for file_path, error in corrupted_images[:20]:

            print()
            print(file_path)
            print("Error:", error)

    else:

        print()
        print("No corrupted images detected.")

    # --------------------------------------------------------
    # Dataset balance
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("CLASS BALANCE")
    print("=" * 60)

    counts = [
        count
        for count in class_counts.values()
        if count > 0
    ]

    if counts:

        minimum = min(counts)
        maximum = max(counts)

        print()
        print("Minimum class size :", minimum)
        print("Maximum class size :", maximum)

        if minimum == maximum:

            print(
                "Dataset classes are evenly balanced."
            )

        else:

            print(
                "Dataset classes have different image counts."
            )

    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("FINAL DATASET CHECK")
    print("=" * 60)

    if (
        not missing_classes
        and total_images > 0
        and not corrupted_images
    ):

        print()
        print("DATASET CHECK PASSED")

        print()
        print(
            "The dataset is ready for CNN preprocessing."
        )

    else:

        print()
        print("DATASET CHECK REQUIRES ATTENTION")

    print()
    print("=" * 60)
    print("LARA CNN DATASET CHECK COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":

    check_dataset()