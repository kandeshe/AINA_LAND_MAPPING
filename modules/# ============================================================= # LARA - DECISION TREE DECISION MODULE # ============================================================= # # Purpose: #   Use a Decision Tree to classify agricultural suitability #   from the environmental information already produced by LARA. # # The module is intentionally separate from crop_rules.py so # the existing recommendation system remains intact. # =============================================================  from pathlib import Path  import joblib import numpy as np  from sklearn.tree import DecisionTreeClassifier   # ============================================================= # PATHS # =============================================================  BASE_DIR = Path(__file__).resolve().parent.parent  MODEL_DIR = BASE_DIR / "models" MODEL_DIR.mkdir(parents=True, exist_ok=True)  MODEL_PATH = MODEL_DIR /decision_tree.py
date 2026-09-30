# =============================================================
# LARA - DECISION TREE DECISION MODULE
# =============================================================
#
# Purpose:
#   Use a Decision Tree to classify agricultural suitability
#   from the environmental information already produced by LARA.
#
# The module is intentionally separate from crop_rules.py so
# the existing recommendation system remains intact.
# =============================================================

from pathlib import Path

import joblib
import numpy as np

from sklearn.tree import DecisionTreeClassifier


# =============================================================
# PATHS
# =============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "lara_decision_tree.joblib"


# =============================================================
# FEATURES USED BY THE DECISION TREE
# =============================================================

FEATURE_NAMES = [
    "rainfall",
    "temperature",
    "ph",
    "nitrogen",
    "organic_carbon",
    "clay",
    "sand",
    "silt",
    "ndvi",
]


# =============================================================
# DECISION TREE CLASSIFIER
# =============================================================

class LARADecisionTree:
    """
    Decision Tree classifier for agricultural land suitability.

    The model uses environmental variables already available
    inside the LARA analysis dictionary.
    """

    def __init__(self):
        self.model = DecisionTreeClassifier(
            criterion="gini",
            max_depth=5,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42
        )

        self.trained = False

        if MODEL_PATH.exists():
            try:
                self.model = joblib.load(MODEL_PATH)
                self.trained = True
                print("LARA Decision Tree model loaded.")
            except Exception as e:
                print(
                    "Decision Tree model could not be loaded:",
                    e
                )

    # =========================================================
    # FEATURE EXTRACTION
    # =========================================================

    def extract_features(self, analysis):
        """
        Extract Decision Tree input features from the existing
        LARA analysis dictionary.
        """

        if not isinstance(analysis, dict):
            analysis = {}

        soil = analysis.get("soil", {})

        if not isinstance(soil, dict):
            soil = {}

        values = [
            analysis.get("rainfall", 0),
            analysis.get("temperature", 25),
            soil.get("ph", 7),
            soil.get("nitrogen", 0),
            soil.get("organic_carbon", 0),
            soil.get("clay", 0),
            soil.get("sand", 0),
            soil.get("silt", 0),
            analysis.get("mean_ndvi", 0),
        ]

        cleaned = []

        for value in values:
            try:
                number = float(value)

                if not np.isfinite(number):
                    number = 0.0

            except (TypeError, ValueError):
                number = 0.0

            cleaned.append(number)

        return np.array(
            cleaned,
            dtype=float
        )

    # =========================================================
    # TRAIN
    # =========================================================

    def train(self, X, y):
        """
        Train the Decision Tree.

        X:
            2D feature matrix.

        y:
            Target labels.
        """

        X = np.asarray(
            X,
            dtype=float
        )

        y = np.asarray(y)

        if X.ndim != 2:
            raise ValueError(
                "Decision Tree training data X must be 2-dimensional."
            )

        if len(X) != len(y):
            raise ValueError(
                "X and y must contain the same number of samples."
            )

        if len(X) < 2:
            raise ValueError(
                "At least two training samples are required."
            )

        self.model.fit(X, y)

        self.trained = True

        joblib.dump(
            self.model,
            MODEL_PATH
        )

        print(
            "Decision Tree trained successfully."
        )

        print(
            f"Model saved to: {MODEL_PATH}"
        )

    # =========================================================
    # PREDICT
    # =========================================================

    def predict(self, analysis):
        """
        Predict the suitability class for the current LARA
        analysis.
        """

        if not self.trained:
            return {
                "available": False,
                "prediction": None,
                "confidence": None,
                "message": (
                    "Decision Tree model has not been trained yet."
                )
            }

        features = self.extract_features(
            analysis
        )

        X = features.reshape(
            1,
            -1
        )

        prediction = self.model.predict(
            X
        )[0]

        confidence = None

        if hasattr(
            self.model,
            "predict_proba"
        ):
            probabilities = (
                self.model.predict_proba(X)[0]
            )

            confidence = float(
                np.max(probabilities)
            ) * 100.0

        return {
            "available": True,
            "prediction": str(prediction),
            "confidence": confidence,
            "features": {
                name: float(value)
                for name, value in zip(
                    FEATURE_NAMES,
                    features
                )
            }
        }


# =============================================================
# SINGLE SHARED INSTANCE
# =============================================================

decision_tree = LARADecisionTree()
