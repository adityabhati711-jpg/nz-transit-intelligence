from pathlib import Path

import joblib
import pandas as pd

from sqlalchemy import text

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
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

    return dataframe


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

    return ColumnTransformer(
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


def evaluate(
    name,
    model,
    X_train,
    X_test,
    y_train,
    y_test,
):

    print(f"\nTraining {name}...")

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    results = {
        "Model": name,

        "Accuracy": accuracy_score(
            y_test,
            predictions,
        ),

        "Precision": precision_score(
            y_test,
            predictions,
            zero_division=0,
        ),

        "Recall": recall_score(
            y_test,
            predictions,
            zero_division=0,
        ),

        "F1": f1_score(
            y_test,
            predictions,
            zero_division=0,
        ),

        "ROC_AUC": roc_auc_score(
            y_test,
            probabilities,
        ),

        "PR_AUC": average_precision_score(
            y_test,
            probabilities,
        ),
    }

    return model, results


def main():

    print("NZ TRANSIT MODEL COMPARISON")
    print("---------------------------")

    dataframe = load_data()

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

    X_train = X.iloc[
        train_index
    ]

    X_test = X.iloc[
        test_index
    ]

    y_train = y.iloc[
        train_index
    ]

    y_test = y.iloc[
        test_index
    ]

    print("\nGROUPED TRAIN / TEST SPLIT")
    print("--------------------------")

    print(
        f"Training records: {len(X_train):,}"
    )

    print(
        f"Testing records: {len(X_test):,}"
    )

    print(
        f"Training delayed: {int(y_train.sum()):,}"
    )

    print(
        f"Testing delayed: {int(y_test.sum()):,}"
    )

    logistic_model = Pipeline(
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

    random_forest_model = Pipeline(
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

    results = []

    trained_logistic, logistic_results = evaluate(
        "Logistic Regression",
        logistic_model,
        X_train,
        X_test,
        y_train,
        y_test,
    )

    results.append(
        logistic_results
    )

    trained_rf, rf_results = evaluate(
        "Random Forest",
        random_forest_model,
        X_train,
        X_test,
        y_train,
        y_test,
    )

    results.append(
        rf_results
    )

    results_df = pd.DataFrame(
        results
    )

    print("\nMODEL COMPARISON")
    print("----------------")

    print(
        results_df.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    best_index = (
        results_df["PR_AUC"]
        .idxmax()
    )

    best_name = results_df.loc[
        best_index,
        "Model",
    ]

    if best_name == "Random Forest":

        best_model = trained_rf

        model_path = (
            MODEL_DIR
            / "delay_random_forest.joblib"
        )

    else:

        best_model = trained_logistic

        model_path = (
            MODEL_DIR
            / "delay_logistic_grouped.joblib"
        )

    joblib.dump(
        best_model,
        model_path,
    )

    print("\nBEST MODEL BY PR AUC")
    print("--------------------")

    print(best_name)

    print("\nMODEL SAVED")
    print("-----------")

    print(model_path)


if __name__ == "__main__":
    main()