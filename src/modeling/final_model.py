from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sqlalchemy import text

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.database import engine


BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = BASE_DIR / "models"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
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


CATEGORICAL_FEATURES = [
    "route_id",
    "stop_id",
    "direction_id",
    "time_period",
    "is_weekend",
]


NUMERIC_FEATURES = [
    "stop_sequence",
    "local_hour",
    "day_number",
]


FEATURES = (
    CATEGORICAL_FEATURES
    + NUMERIC_FEATURES
)


def load_data():

    with engine.connect() as connection:

        dataframe = pd.read_sql(
            text(QUERY),
            connection,
        )

    print(
        f"Records loaded: {len(dataframe):,}"
    )

    print(
        f"Unique trips: "
        f"{dataframe['trip_id'].nunique():,}"
    )

    return dataframe


def split_data(dataframe):

    X = dataframe[FEATURES].copy()

    y = (
        dataframe["is_delayed"]
        .astype(int)
    )

    groups = dataframe["trip_id"]

    # ---------------------------------------------------------
    # First split:
    # 80% train+validation
    # 20% final untouched test
    # ---------------------------------------------------------

    first_split = GroupShuffleSplit(
        n_splits=1,
        test_size=0.20,
        random_state=42,
    )

    train_val_index, test_index = next(
        first_split.split(
            X,
            y,
            groups=groups,
        )
    )

    X_train_val = X.iloc[
        train_val_index
    ]

    y_train_val = y.iloc[
        train_val_index
    ]

    groups_train_val = groups.iloc[
        train_val_index
    ]

    X_test = X.iloc[
        test_index
    ]

    y_test = y.iloc[
        test_index
    ]

    test_groups = groups.iloc[
        test_index
    ]

    # ---------------------------------------------------------
    # Second split:
    # 75% of remaining -> training
    # 25% of remaining -> validation
    #
    # Overall approximately:
    # 60% train
    # 20% validation
    # 20% test
    # ---------------------------------------------------------

    second_split = GroupShuffleSplit(
        n_splits=1,
        test_size=0.25,
        random_state=43,
    )

    train_index, val_index = next(
        second_split.split(
            X_train_val,
            y_train_val,
            groups=groups_train_val,
        )
    )

    X_train = X_train_val.iloc[
        train_index
    ]

    y_train = y_train_val.iloc[
        train_index
    ]

    X_val = X_train_val.iloc[
        val_index
    ]

    y_val = y_train_val.iloc[
        val_index
    ]

    train_groups = groups_train_val.iloc[
        train_index
    ]

    val_groups = groups_train_val.iloc[
        val_index
    ]

    # ---------------------------------------------------------
    # Leakage check
    # ---------------------------------------------------------

    train_trip_ids = set(
        train_groups
    )

    val_trip_ids = set(
        val_groups
    )

    test_trip_ids = set(
        test_groups
    )

    train_val_overlap = (
        train_trip_ids
        & val_trip_ids
    )

    train_test_overlap = (
        train_trip_ids
        & test_trip_ids
    )

    val_test_overlap = (
        val_trip_ids
        & test_trip_ids
    )

    if (
        train_val_overlap
        or train_test_overlap
        or val_test_overlap
    ):
        raise RuntimeError(
            "Trip leakage detected between splits."
        )

    print("\nFINAL GROUPED DATA SPLIT")
    print("------------------------")

    print(
        f"Training records:   "
        f"{len(X_train):,}"
    )

    print(
        f"Validation records: "
        f"{len(X_val):,}"
    )

    print(
        f"Final test records: "
        f"{len(X_test):,}"
    )

    print()

    print(
        f"Training delayed:   "
        f"{int(y_train.sum()):,}"
    )

    print(
        f"Validation delayed: "
        f"{int(y_val.sum()):,}"
    )

    print(
        f"Test delayed:       "
        f"{int(y_test.sum()):,}"
    )

    print()

    print(
        "Trip leakage between splits: 0"
    )

    return (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    )


def build_preprocessor():

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
            ),
        ]
    )

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
        ]
    )

    return preprocessor


def build_logistic():

    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "model",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def build_random_forest():

    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(),
            ),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    max_depth=18,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def validation_metrics(
    name,
    model,
    X_train,
    y_train,
    X_val,
    y_val,
):

    print(
        f"\nTraining {name}..."
    )

    model.fit(
        X_train,
        y_train,
    )

    probabilities = (
        model.predict_proba(
            X_val
        )[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    result = {
        "model": name,

        "accuracy": accuracy_score(
            y_val,
            predictions,
        ),

        "precision": precision_score(
            y_val,
            predictions,
            zero_division=0,
        ),

        "recall": recall_score(
            y_val,
            predictions,
            zero_division=0,
        ),

        "f1": f1_score(
            y_val,
            predictions,
            zero_division=0,
        ),

        "roc_auc": roc_auc_score(
            y_val,
            probabilities,
        ),

        "pr_auc": average_precision_score(
            y_val,
            probabilities,
        ),
    }

    return model, result


def choose_model(
    X_train,
    y_train,
    X_val,
    y_val,
):

    logistic = build_logistic()

    random_forest = (
        build_random_forest()
    )

    trained_logistic, logistic_result = (
        validation_metrics(
            "Logistic Regression",
            logistic,
            X_train,
            y_train,
            X_val,
            y_val,
        )
    )

    trained_rf, rf_result = (
        validation_metrics(
            "Random Forest",
            random_forest,
            X_train,
            y_train,
            X_val,
            y_val,
        )
    )

    results = pd.DataFrame(
        [
            logistic_result,
            rf_result,
        ]
    )

    print("\nVALIDATION MODEL COMPARISON")
    print("---------------------------")

    print(
        results.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    best_index = (
        results["pr_auc"]
        .idxmax()
    )

    best_name = results.loc[
        best_index,
        "model",
    ]

    if best_name == "Random Forest":

        best_model = trained_rf

    else:

        best_model = (
            trained_logistic
        )

    print("\nSELECTED MODEL")
    print("--------------")

    print(best_name)

    return (
        best_name,
        best_model,
    )


def choose_threshold(
    model,
    X_val,
    y_val,
):

    probabilities = (
        model.predict_proba(
            X_val
        )[:, 1]
    )

    thresholds = np.arange(
        0.10,
        0.91,
        0.05,
    )

    results = []

    for threshold in thresholds:

        predictions = (
            probabilities
            >= threshold
        ).astype(int)

        results.append({
            "threshold":
                float(
                    round(
                        threshold,
                        2,
                    )
                ),

            "precision":
                precision_score(
                    y_val,
                    predictions,
                    zero_division=0,
                ),

            "recall":
                recall_score(
                    y_val,
                    predictions,
                    zero_division=0,
                ),

            "f1":
                f1_score(
                    y_val,
                    predictions,
                    zero_division=0,
                ),
        })

    results_df = pd.DataFrame(
        results
    )

    best_index = (
        results_df["f1"]
        .idxmax()
    )

    best = results_df.loc[
        best_index
    ]

    threshold = float(
        best["threshold"]
    )

    print("\nVALIDATION THRESHOLD")
    print("--------------------")

    print(
        f"Selected threshold: "
        f"{threshold:.2f}"
    )

    print(
        f"Validation precision: "
        f"{best['precision']:.4f}"
    )

    print(
        f"Validation recall: "
        f"{best['recall']:.4f}"
    )

    print(
        f"Validation F1: "
        f"{best['f1']:.4f}"
    )

    return threshold


def final_test(
    model,
    threshold,
    X_test,
    y_test,
):

    probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

    predictions = (
        probabilities
        >= threshold
    ).astype(int)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    pr_auc = average_precision_score(
        y_test,
        probabilities,
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
    )

    print("\nFINAL UNTOUCHED TEST RESULTS")
    print("----------------------------")

    print(
        f"Accuracy:  {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall:    {recall:.4f}"
    )

    print(
        f"F1 Score:  {f1:.4f}"
    )

    print(
        f"ROC AUC:   {roc_auc:.4f}"
    )

    print(
        f"PR AUC:    {pr_auc:.4f}"
    )

    print("\nCONFUSION MATRIX")
    print("----------------")

    print(matrix)

    return {
        "threshold": threshold,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
    }


def main():

    print("NZ TRANSIT FINAL MODEL PIPELINE")
    print("-------------------------------")

    dataframe = load_data()

    (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    ) = split_data(
        dataframe
    )

    (
        best_name,
        best_model,
    ) = choose_model(
        X_train,
        y_train,
        X_val,
        y_val,
    )

    threshold = choose_threshold(
        best_model,
        X_val,
        y_val,
    )

    results = final_test(
        best_model,
        threshold,
        X_test,
        y_test,
    )

    model_path = (
        MODEL_DIR
        / "final_delay_model.joblib"
    )

    results_path = (
        MODEL_DIR
        / "final_model_metrics.json"
    )

    joblib.dump(
        best_model,
        model_path,
    )

    output = {
        "model": best_name,
        **{
            key: float(value)
            for key, value
            in results.items()
        },
    }

    with open(
        results_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
        )

    print("\nFINAL MODEL SAVED")
    print("-----------------")

    print(model_path)

    print(
        "\nFINAL METRICS SAVED"
    )

    print("-------------------")

    print(results_path)

    print(
        "\nDAY 4 FINAL MODEL PIPELINE "
        "COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":
    main()