from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sqlalchemy import text

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit

from src.database import engine


BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "delay_random_forest.joblib"
)

THRESHOLD_PATH = (
    BASE_DIR
    / "models"
    / "delay_random_forest_threshold.json"
)


QUERY = """
SELECT
    trip_id,
    route_id,
    stop_id,
    stop_sequence,
    direction_id,
    local_hour,
    day_number,
    time_period,
    is_weekend,
    is_delayed

FROM analytics.ml_delay_features

WHERE trip_id IS NOT NULL
"""


FEATURES = [
    "route_id",
    "stop_id",
    "direction_id",
    "time_period",
    "is_weekend",
    "stop_sequence",
    "local_hour",
    "day_number",
]


def load_data():

    with engine.connect() as connection:

        dataframe = pd.read_sql(
            text(QUERY),
            connection,
        )

    return dataframe


def create_test_set(dataframe):

    X = dataframe[
        FEATURES
    ].copy()

    y = dataframe[
        "is_delayed"
    ].astype(int)

    groups = dataframe[
        "trip_id"
    ]

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=42,
    )

    train_index, test_index = next(
        splitter.split(
            X,
            y,
            groups=groups,
        )
    )

    X_test = X.iloc[
        test_index
    ]

    y_test = y.iloc[
        test_index
    ]

    return X_test, y_test


def tune_threshold(
    model,
    X_test,
    y_test,
):

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    results = []

    thresholds = np.arange(
        0.10,
        0.91,
        0.05,
    )

    for threshold in thresholds:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        results.append({
            "threshold":
                round(
                    float(threshold),
                    2,
                ),

            "accuracy":
                accuracy_score(
                    y_test,
                    predictions,
                ),

            "precision":
                precision_score(
                    y_test,
                    predictions,
                    zero_division=0,
                ),

            "recall":
                recall_score(
                    y_test,
                    predictions,
                    zero_division=0,
                ),

            "f1":
                f1_score(
                    y_test,
                    predictions,
                    zero_division=0,
                ),
        })

    results_df = pd.DataFrame(
        results
    )

    print("THRESHOLD COMPARISON")
    print("--------------------")

    print(
        results_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    best_index = (
        results_df["f1"]
        .idxmax()
    )

    best = results_df.loc[
        best_index
    ]

    best_threshold = float(
        best["threshold"]
    )

    final_predictions = (
        probabilities
        >= best_threshold
    ).astype(int)

    print("\nBEST THRESHOLD BY F1")
    print("--------------------")

    print(
        f"Threshold: {best_threshold:.2f}"
    )

    print(
        f"Accuracy:  {best['accuracy']:.4f}"
    )

    print(
        f"Precision: {best['precision']:.4f}"
    )

    print(
        f"Recall:    {best['recall']:.4f}"
    )

    print(
        f"F1 Score:  {best['f1']:.4f}"
    )

    print("\nCONFUSION MATRIX")
    print("----------------")

    print(
        confusion_matrix(
            y_test,
            final_predictions,
        )
    )

    threshold_data = {
        "threshold":
            best_threshold,

        "accuracy":
            float(best["accuracy"]),

        "precision":
            float(best["precision"]),

        "recall":
            float(best["recall"]),

        "f1":
            float(best["f1"]),
    }

    with open(
        THRESHOLD_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            threshold_data,
            file,
            indent=4,
        )


def show_feature_importance(model):

    print("\nTOP FEATURE IMPORTANCE")
    print("----------------------")

    preprocessor = model.named_steps[
        "preprocessor"
    ]

    classifier = model.named_steps[
        "model"
    ]

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    importances = (
        classifier
        .feature_importances_
    )

    importance_df = pd.DataFrame({
        "feature":
            feature_names,

        "importance":
            importances,
    })

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=False,
        )
        .head(20)
    )

    print(
        importance_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )


def main():

    print("RANDOM FOREST MODEL ANALYSIS")
    print("----------------------------")

    dataframe = load_data()

    X_test, y_test = (
        create_test_set(
            dataframe
        )
    )

    model = joblib.load(
        MODEL_PATH
    )

    print(
        f"Testing records: {len(X_test):,}"
    )

    print(
        f"Delayed testing records: {int(y_test.sum()):,}"
    )

    print()

    tune_threshold(
        model,
        X_test,
        y_test,
    )

    show_feature_importance(
        model
    )

    print(
        "\nMODEL ANALYSIS COMPLETED SUCCESSFULLY"
    )

    print(
        f"Threshold saved to: {THRESHOLD_PATH}"
    )


if __name__ == "__main__":
    main()