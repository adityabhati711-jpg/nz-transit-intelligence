from pathlib import Path

import joblib
import pandas as pd

from sqlalchemy import text

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.database import engine


BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODEL_PATH = (
    MODEL_DIR
    / "delay_baseline_logistic.joblib"
)


QUERY = """
SELECT
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

    print("Loading ML feature data...")

    with engine.connect() as connection:

        dataframe = pd.read_sql(
            text(QUERY),
            connection,
        )

    print(
        f"Records loaded: {len(dataframe):,}"
    )

    return dataframe


def prepare_data(dataframe):

    X = dataframe[FEATURES].copy()

    y = (
        dataframe["is_delayed"]
        .astype(int)
    )

    print("\nTARGET DISTRIBUTION")
    print("-------------------")

    delayed = int(y.sum())

    not_delayed = int(
        len(y) - delayed
    )

    delayed_percentage = (
        delayed
        / len(y)
        * 100
    )

    print(
        f"Delayed: {delayed:,}"
    )

    print(
        f"Not delayed: {not_delayed:,}"
    )

    print(
        f"Delayed percentage: "
        f"{delayed_percentage:.2f}%"
    )

    return X, y


def build_pipeline():

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

    model = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
    )

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                model,
            ),
        ]
    )

    return pipeline


def evaluate_model(
    model,
    X_test,
    y_test,
):

    predictions = model.predict(
        X_test
    )

    probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )

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

    print("\nMODEL PERFORMANCE")
    print("-----------------")

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

    print("\nCLASSIFICATION REPORT")
    print("---------------------")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0,
        )
    )


def main():

    print("NZ TRANSIT DELAY BASELINE MODEL")
    print("-------------------------------")

    dataframe = load_data()

    X, y = prepare_data(
        dataframe
    )

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    )

    print("\nTRAIN / TEST SPLIT")
    print("------------------")

    print(
        f"Training records: "
        f"{len(X_train):,}"
    )

    print(
        f"Testing records: "
        f"{len(X_test):,}"
    )

    model = build_pipeline()

    print("\nTraining baseline model...")

    model.fit(
        X_train,
        y_train,
    )

    print(
        "MODEL TRAINING SUCCESSFUL"
    )

    evaluate_model(
        model,
        X_test,
        y_test,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print("\nMODEL SAVED")
    print("-----------")

    print(
        MODEL_PATH
    )


if __name__ == "__main__":
    main()