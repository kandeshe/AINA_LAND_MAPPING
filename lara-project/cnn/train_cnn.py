from pathlib import Path
import json
import csv

import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)


# ============================================================
# LARA CNN - LAND COVER CLASSIFICATION
# ============================================================

print()
print("=" * 70)
print("              LARA CNN TRAINING")
print("=" * 70)


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_DIR = BASE_DIR / "dataset"

MODEL_DIR = BASE_DIR.parent / "models"

OUTPUT_DIR = BASE_DIR / "results"


MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


MODEL_PATH = MODEL_DIR / "lara_landcover_cnn.keras"

CLASS_NAMES_PATH = MODEL_DIR / "lara_landcover_classes.json"

HISTORY_CSV = OUTPUT_DIR / "training_history.csv"

ACCURACY_GRAPH = OUTPUT_DIR / "training_accuracy.png"

LOSS_GRAPH = OUTPUT_DIR / "training_loss.png"

CONFUSION_MATRIX = OUTPUT_DIR / "confusion_matrix.png"

CLASSIFICATION_REPORT = OUTPUT_DIR / "classification_report.txt"


# ============================================================
# 2. SETTINGS
# ============================================================

IMAGE_SIZE = (
    64,
    64
)

CHANNELS = 3

BATCH_SIZE = 32

EPOCHS = 20

RANDOM_SEED = 42


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


# ============================================================
# 3. PRINT CONFIGURATION
# ============================================================

print()

print("Dataset:")
print(DATASET_DIR)

print()

print("Model output:")
print(MODEL_PATH)

print()

print("Image size:")
print(IMAGE_SIZE)

print()

print("Classes:")
for index, class_name in enumerate(
    EXPECTED_CLASSES
):
    print(
        f"{index}: {class_name}"
    )

print()

print("Epochs :", EPOCHS)

print("Batch size :", BATCH_SIZE)


# ============================================================
# 4. CHECK DATASET
# ============================================================

if not DATASET_DIR.exists():

    raise FileNotFoundError(
        f"Dataset not found:\n{DATASET_DIR}"
    )


for class_name in EXPECTED_CLASSES:

    class_folder = DATASET_DIR / class_name

    if not class_folder.exists():

        raise FileNotFoundError(
            f"Missing class folder:\n{class_folder}"
        )


print()
print("=" * 70)
print("DATASET FOUND")
print("=" * 70)


# ============================================================
# 5. LOAD DATASET
# ============================================================

print()
print("Loading images...")


image_paths = []

labels = []


for label, class_name in enumerate(
    EXPECTED_CLASSES
):

    class_folder = DATASET_DIR / class_name

    files = sorted(
        [
            file
            for file in class_folder.rglob("*")
            if file.is_file()
            and file.suffix.lower()
            in {
                ".jpg",
                ".jpeg",
                ".png"
            }
        ]
    )

    print(
        f"{class_name:<25} : {len(files)}"
    )

    for file in files:

        image_paths.append(
            str(file)
        )

        labels.append(label)


image_paths = np.array(
    image_paths
)

labels = np.array(
    labels
)


print()
print(
    "Total images:",
    len(image_paths)
)


# ============================================================
# 6. TRAIN / VALIDATION / TEST SPLIT
# ============================================================

print()
print("=" * 70)
print("CREATING DATA SPLITS")
print("=" * 70)


# First split:
# 80% training
# 20% temporary

train_paths, temp_paths, train_labels, temp_labels = (
    train_test_split(
        image_paths,
        labels,
        test_size=0.20,
        random_state=RANDOM_SEED,
        stratify=labels
    )
)


# Split temporary:
# 10% validation
# 10% test

validation_paths, test_paths, validation_labels, test_labels = (
    train_test_split(
        temp_paths,
        temp_labels,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temp_labels
    )
)


print()

print(
    "Training images   :",
    len(train_paths)
)

print(
    "Validation images :",
    len(validation_paths)
)

print(
    "Test images       :",
    len(test_paths)
)


# ============================================================
# 7. IMAGE LOADING FUNCTION
# ============================================================

def load_image(path, label):

    image = tf.io.read_file(path)

    image = tf.image.decode_jpeg(
        image,
        channels=CHANNELS
    )

    image = tf.image.resize(
        image,
        IMAGE_SIZE
    )

    image = tf.cast(
        image,
        tf.float32
    )

    image = image / 255.0

    return image, label


# ============================================================
# 8. DATA AUGMENTATION
# ============================================================

data_augmentation = keras.Sequential(
    [

        layers.RandomFlip(
            "horizontal"
        ),

        layers.RandomRotation(
            0.10
        ),

        layers.RandomZoom(
            0.10
        ),

        layers.RandomContrast(
            0.10
        )

    ],
    name="data_augmentation"
)


# ============================================================
# 9. CREATE TF DATASETS
# ============================================================

def create_dataset(
    paths,
    labels,
    training=False
):

    dataset = tf.data.Dataset.from_tensor_slices(
        (
            paths,
            labels
        )
    )

    if training:

        dataset = dataset.shuffle(
            buffer_size=len(paths),
            seed=RANDOM_SEED
        )

    dataset = dataset.map(
        load_image,
        num_parallel_calls=tf.data.AUTOTUNE
    )

    if training:

        dataset = dataset.map(
            lambda image, label:
            (
                data_augmentation(image),
                label
            ),
            num_parallel_calls=tf.data.AUTOTUNE
        )

    dataset = dataset.batch(
        BATCH_SIZE
    )

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset


train_dataset = create_dataset(
    train_paths,
    train_labels,
    training=True
)


validation_dataset = create_dataset(
    validation_paths,
    validation_labels,
    training=False
)


test_dataset = create_dataset(
    test_paths,
    test_labels,
    training=False
)


# ============================================================
# 10. CNN MODEL
# ============================================================

print()
print("=" * 70)
print("BUILDING CNN")
print("=" * 70)


model = keras.Sequential(
    [

        layers.Input(
            shape=(
                IMAGE_SIZE[0],
                IMAGE_SIZE[1],
                CHANNELS
            )
        ),

        # ----------------------------------------------------
        # Convolution Block 1
        # ----------------------------------------------------

        layers.Conv2D(
            32,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.BatchNormalization(),

        layers.MaxPooling2D(
            (2, 2)
        ),

        # ----------------------------------------------------
        # Convolution Block 2
        # ----------------------------------------------------

        layers.Conv2D(
            64,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.BatchNormalization(),

        layers.MaxPooling2D(
            (2, 2)
        ),

        # ----------------------------------------------------
        # Convolution Block 3
        # ----------------------------------------------------

        layers.Conv2D(
            128,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.BatchNormalization(),

        layers.MaxPooling2D(
            (2, 2)
        ),

        # ----------------------------------------------------
        # Convolution Block 4
        # ----------------------------------------------------

        layers.Conv2D(
            256,
            (3, 3),
            activation="relu",
            padding="same"
        ),

        layers.BatchNormalization(),

        layers.MaxPooling2D(
            (2, 2)
        ),

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        layers.GlobalAveragePooling2D(),

        layers.Dense(
            128,
            activation="relu"
        ),

        layers.Dropout(
            0.40
        ),

        layers.Dense(
            len(EXPECTED_CLASSES),
            activation="softmax"
        )

    ],
    name="LARA_LandCover_CNN"
)


model.summary()


# ============================================================
# 11. COMPILE
# ============================================================

model.compile(

    optimizer=keras.optimizers.Adam(
        learning_rate=0.001
    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ]
)


# ============================================================
# 12. CALLBACKS
# ============================================================

callbacks = [

    keras.callbacks.EarlyStopping(

        monitor="val_loss",

        patience=5,

        restore_best_weights=True
    ),

    keras.callbacks.ReduceLROnPlateau(

        monitor="val_loss",

        factor=0.5,

        patience=2,

        min_lr=0.00001
    ),

    keras.callbacks.ModelCheckpoint(

        filepath=str(MODEL_PATH),

        monitor="val_accuracy",

        save_best_only=True,

        mode="max"
    )

]


# ============================================================
# 13. TRAIN CNN
# ============================================================

print()
print("=" * 70)
print("STARTING CNN TRAINING")
print("=" * 70)

print()

history = model.fit(

    train_dataset,

    validation_data=validation_dataset,

    epochs=EPOCHS,

    callbacks=callbacks

)


# ============================================================
# 14. SAVE FINAL MODEL
# ============================================================

print()
print("=" * 70)
print("SAVING MODEL")
print("=" * 70)


model.save(
    MODEL_PATH
)


print()
print(
    "Model saved:",
    MODEL_PATH
)


# ============================================================
# 15. SAVE CLASS NAMES
# ============================================================

with open(
    CLASS_NAMES_PATH,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        EXPECTED_CLASSES,
        file,
        indent=4
    )


print(
    "Class names saved:",
    CLASS_NAMES_PATH
)


# ============================================================
# 16. SAVE TRAINING HISTORY CSV
# ============================================================

history_data = history.history

history_length = len(
    history_data["loss"]
)


with open(
    HISTORY_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow(
        [
            "Epoch",
            "Training Loss",
            "Validation Loss",
            "Training Accuracy",
            "Validation Accuracy"
        ]
    )

    for epoch in range(
        history_length
    ):

        writer.writerow(
            [
                epoch + 1,

                history_data["loss"][epoch],

                history_data["val_loss"][epoch],

                history_data["accuracy"][epoch],

                history_data["val_accuracy"][epoch]
            ]
        )


print(
    "Training history saved:",
    HISTORY_CSV
)


# ============================================================
# 17. TRAINING ACCURACY GRAPH
# ============================================================

epochs_range = range(
    1,
    history_length + 1
)


plt.figure(
    figsize=(10, 6)
)

plt.plot(
    epochs_range,
    history_data["accuracy"],
    marker="o",
    label="Training Accuracy"
)

plt.plot(
    epochs_range,
    history_data["val_accuracy"],
    marker="o",
    label="Validation Accuracy"
)

plt.title(
    "LARA CNN Training and Validation Accuracy"
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Accuracy"
)

plt.grid(
    True
)

plt.legend()

plt.tight_layout()

plt.savefig(
    ACCURACY_GRAPH,
    dpi=300
)

plt.close()


print(
    "Accuracy graph saved:",
    ACCURACY_GRAPH
)


# ============================================================
# 18. TRAINING LOSS GRAPH
# ============================================================

plt.figure(
    figsize=(10, 6)
)

plt.plot(
    epochs_range,
    history_data["loss"],
    marker="o",
    label="Training Loss"
)

plt.plot(
    epochs_range,
    history_data["val_loss"],
    marker="o",
    label="Validation Loss"
)

plt.title(
    "LARA CNN Training and Validation Loss"
)

plt.xlabel(
    "Epoch"
)

plt.ylabel(
    "Loss"
)

plt.grid(
    True
)

plt.legend()

plt.tight_layout()

plt.savefig(
    LOSS_GRAPH,
    dpi=300
)

plt.close()


print(
    "Loss graph saved:",
    LOSS_GRAPH
)


# ============================================================
# 19. TEST EVALUATION
# ============================================================

print()
print("=" * 70)
print("EVALUATING CNN ON TEST DATA")
print("=" * 70)


test_loss, test_accuracy = model.evaluate(
    test_dataset,
    verbose=1
)


print()
print(
    f"Test Loss     : {test_loss:.4f}"
)

print(
    f"Test Accuracy : {test_accuracy:.4f}"
)

print(
    f"Test Accuracy : {test_accuracy * 100:.2f}%"
)


# ============================================================
# 20. PREDICTIONS
# ============================================================

print()
print("Generating test predictions...")


predictions = model.predict(
    test_dataset,
    verbose=1
)


predicted_labels = np.argmax(
    predictions,
    axis=1
)


# ============================================================
# 21. CLASSIFICATION REPORT
# ============================================================

report = classification_report(

    test_labels,

    predicted_labels,

    target_names=EXPECTED_CLASSES,

    digits=4
)


print()
print("=" * 70)
print("CLASSIFICATION REPORT")
print("=" * 70)

print()
print(report)


with open(
    CLASSIFICATION_REPORT,
    "w",
    encoding="utf-8"
) as file:

    file.write(
        "LARA CNN LAND COVER CLASSIFICATION REPORT\n"
    )

    file.write(
        "=" * 60
    )

    file.write("\n\n")

    file.write(
        f"Test Accuracy: "
        f"{test_accuracy * 100:.2f}%\n\n"
    )

    file.write(
        report
    )


print(
    "Classification report saved:",
    CLASSIFICATION_REPORT
)


# ============================================================
# 22. CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(

    test_labels,

    predicted_labels
)


display = ConfusionMatrixDisplay(

    confusion_matrix=cm,

    display_labels=EXPECTED_CLASSES
)


fig, ax = plt.subplots(
    figsize=(12, 10)
)


display.plot(
    ax=ax,
    xticks_rotation=45,
    cmap="Blues"
)


plt.title(
    "LARA CNN Land Cover Confusion Matrix"
)

plt.tight_layout()

plt.savefig(
    CONFUSION_MATRIX,
    dpi=300
)

plt.close()


print(
    "Confusion matrix saved:",
    CONFUSION_MATRIX
)


# ============================================================
# 23. FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("              LARA CNN TRAINING COMPLETE")
print("=" * 70)

print()

print(
    "Model:",
    MODEL_PATH
)

print(
    "Classes:",
    CLASS_NAMES_PATH
)

print(
    "History:",
    HISTORY_CSV
)

print(
    "Accuracy graph:",
    ACCURACY_GRAPH
)

print(
    "Loss graph:",
    LOSS_GRAPH
)

print(
    "Confusion matrix:",
    CONFUSION_MATRIX
)

print(
    "Classification report:",
    CLASSIFICATION_REPORT
)

print()

print(
    f"Final Test Accuracy: "
    f"{test_accuracy * 100:.2f}%"
)

print()

print("=" * 70)