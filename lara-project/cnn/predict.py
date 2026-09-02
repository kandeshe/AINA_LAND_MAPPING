from pathlib import Path
import json
import sys

import numpy as np
import tensorflow as tf
from PIL import Image


# ============================================================
# LARA CNN - SATELLITE SCENE LAND-COVER CLASSIFICATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR.parent
    / "models"
    / "lara_landcover_cnn.keras"
)

CLASS_NAMES_PATH = (
    BASE_DIR.parent
    / "models"
    / "lara_landcover_classes.json"
)

RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

RESULT_FILE = (
    RESULTS_DIR
    / "satellite_landcover_prediction.json"
)

TILE_SIZE = 64
TOP_K = 5


# ============================================================
# LOAD CLASS NAMES
# ============================================================

def load_class_names():

    if not CLASS_NAMES_PATH.exists():

        raise FileNotFoundError(
            f"CNN class names file not found:\n"
            f"{CLASS_NAMES_PATH}"
        )

    with open(
        CLASS_NAMES_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        class_names = json.load(file)

    # Support either a list or dictionary JSON format

    if isinstance(class_names, dict):

        class_names = [
            class_names[key]
            for key in sorted(
                class_names,
                key=lambda x: int(x)
                if str(x).isdigit()
                else str(x)
            )
        ]

    return class_names


# ============================================================
# LOAD MODEL
# ============================================================

def load_cnn_model():

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"CNN model not found:\n"
            f"{MODEL_PATH}"
        )

    print("Loading CNN model...")

    model = tf.keras.models.load_model(
        MODEL_PATH
    )

    print("CNN model loaded.")

    return model


# ============================================================
# RUN CNN SCENE PREDICTION
# ============================================================

def predict_scene(
    image_path,
    save_result=True
):

    image_path = Path(
        image_path
    ).resolve()

    print()
    print("=" * 70)
    print("       LARA CNN SATELLITE SCENE CLASSIFICATION")
    print("=" * 70)

    print()
    print("Satellite image:")
    print(image_path)

    # --------------------------------------------------------
    # CHECK IMAGE
    # --------------------------------------------------------

    if not image_path.exists():

        raise FileNotFoundError(
            f"Satellite image not found:\n"
            f"{image_path}"
        )

    # --------------------------------------------------------
    # LOAD CLASSES
    # --------------------------------------------------------

    class_names = load_class_names()

    # --------------------------------------------------------
    # LOAD MODEL
    # --------------------------------------------------------

    model = load_cnn_model()

    # --------------------------------------------------------
    # LOAD IMAGE
    # --------------------------------------------------------

    print()
    print("Loading satellite image...")

    image = Image.open(
        image_path
    ).convert("RGB")

    image_width, image_height = image.size

    print(
        f"Image size: "
        f"{image_width} x {image_height}"
    )

    if (
        image_width < TILE_SIZE
        or image_height < TILE_SIZE
    ):

        raise ValueError(
            "Satellite image is smaller "
            "than the CNN tile size."
        )

    # --------------------------------------------------------
    # CREATE TILES
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("CREATING SATELLITE TILES")
    print("=" * 70)

    tiles = []
    tile_locations = []

    for y in range(
        0,
        image_height - TILE_SIZE + 1,
        TILE_SIZE
    ):

        for x in range(
            0,
            image_width - TILE_SIZE + 1,
            TILE_SIZE
        ):

            tile = image.crop(
                (
                    x,
                    y,
                    x + TILE_SIZE,
                    y + TILE_SIZE
                )
            )

            tile_array = np.asarray(
                tile,
                dtype=np.float32
            )

            tile_array /= 255.0

            tiles.append(
                tile_array
            )

            tile_locations.append(
                {
                    "x": x,
                    "y": y
                }
            )

    tiles = np.asarray(
        tiles,
        dtype=np.float32
    )

    print()
    print(
        "Tile size:",
        f"{TILE_SIZE} x {TILE_SIZE}"
    )

    print(
        "Total tiles:",
        len(tiles)
    )

    # --------------------------------------------------------
    # CNN PREDICTION
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("RUNNING CNN ON SATELLITE TILES")
    print("=" * 70)

    predictions = model.predict(
        tiles,
        batch_size=32,
        verbose=1
    )

    # --------------------------------------------------------
    # PREDICTED CLASSES
    # --------------------------------------------------------

    predicted_indices = np.argmax(
        predictions,
        axis=1
    )

    predicted_classes = [
        class_names[int(index)]
        for index in predicted_indices
    ]

    confidence_values = np.max(
        predictions,
        axis=1
    )

    # --------------------------------------------------------
    # CLASS DISTRIBUTION
    # --------------------------------------------------------

    class_counts = {
        class_name: 0
        for class_name in class_names
    }

    class_confidences = {
        class_name: []
        for class_name in class_names
    }

    for index, class_name in enumerate(
        predicted_classes
    ):

        class_counts[class_name] += 1

        class_confidences[
            class_name
        ].append(
            float(
                confidence_values[index]
            )
        )

    total_tiles = len(
        predicted_classes
    )

    # --------------------------------------------------------
    # DISTRIBUTION
    # --------------------------------------------------------

    distribution = []

    for class_name in class_names:

        count = class_counts[
            class_name
        ]

        percentage = (
            count
            / total_tiles
        ) * 100.0

        confidence_list = (
            class_confidences[
                class_name
            ]
        )

        if confidence_list:

            average_confidence = (
                sum(confidence_list)
                / len(confidence_list)
            )

        else:

            average_confidence = 0.0

        distribution.append(
            {
                "class": class_name,
                "tiles": count,
                "percentage": percentage,
                "average_confidence":
                    average_confidence
            }
        )

    # --------------------------------------------------------
    # DOMINANT CLASS
    # --------------------------------------------------------

    dominant_class = max(
        class_counts,
        key=class_counts.get
    )

    dominant_count = (
        class_counts[
            dominant_class
        ]
    )

    dominant_percentage = (
        dominant_count
        / total_tiles
    ) * 100.0

    # --------------------------------------------------------
    # OVERALL CONFIDENCE
    # --------------------------------------------------------

    overall_confidence = float(
        np.mean(
            confidence_values
        )
    )

    # --------------------------------------------------------
    # SCENE CLASS SCORES
    # --------------------------------------------------------

    scene_class_scores = {}

    for class_index, class_name in enumerate(
        class_names
    ):

        scene_class_scores[
            class_name
        ] = float(
            np.mean(
                predictions[
                    :,
                    class_index
                ]
            )
        )

    sorted_scene_classes = sorted(
        scene_class_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    # --------------------------------------------------------
    # TILE RESULTS
    # --------------------------------------------------------

    tile_results = []

    for index, class_name in enumerate(
        predicted_classes
    ):

        tile_results.append(
            {
                "tile": index + 1,

                "x": tile_locations[
                    index
                ]["x"],

                "y": tile_locations[
                    index
                ]["y"],

                "prediction": class_name,

                "confidence": float(
                    confidence_values[
                        index
                    ]
                )
            }
        )

    # --------------------------------------------------------
    # RESULT OBJECT
    # --------------------------------------------------------

    result = {

        "model":
            "LARA Land Cover CNN",

        "source_image":
            str(image_path),

        "image_size": {

            "width":
                image_width,

            "height":
                image_height
        },

        "tile_size":
            TILE_SIZE,

        "total_tiles":
            total_tiles,

        "dominant_land_cover":
            dominant_class,

        "dominant_coverage_percent":
            dominant_percentage,

        "average_prediction_confidence":
            overall_confidence,

        "class_distribution":
            distribution,

        "scene_class_scores":
            [
                {
                    "class":
                        class_name,

                    "score":
                        score
                }

                for class_name, score
                in sorted_scene_classes
            ],

        "tile_predictions":
            tile_results
    }

    # --------------------------------------------------------
    # SAVE JSON
    # --------------------------------------------------------

    if save_result:

        with open(
            RESULT_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                result,
                file,
                indent=4
            )

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL CNN SCENE RESULT")
    print("=" * 70)

    print()

    print(
        "Dominant Land Cover :",
        dominant_class
    )

    print(
        "Scene Coverage      :",
        f"{dominant_percentage:.2f}%"
    )

    print(
        "Average Confidence  :",
        f"{overall_confidence * 100:.2f}%"
    )

    print()

    print("Top Scene Classes")
    print("-" * 50)

    for class_name, score in (
        sorted_scene_classes[:TOP_K]
    ):

        print(
            f"{class_name:<25}"
            f": {score * 100:6.2f}%"
        )

    if save_result:

        print()
        print(
            "Prediction saved:"
        )

        print(
            RESULT_FILE
        )

    print()
    print("=" * 70)
    print("SATELLITE CNN ANALYSIS COMPLETE")
    print("=" * 70)

    return result


# ============================================================
# COMMAND-LINE MODE
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) >= 2:

        input_image = sys.argv[1]

    else:

        input_image = (
            BASE_DIR.parent
            / "data"
            / "satellite"
            / "RGB"
            / "rgb_preview.jpg"
        )

    predict_scene(
        input_image
    )