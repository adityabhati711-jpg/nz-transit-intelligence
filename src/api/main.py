from pathlib import Path
import json

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = BASE_DIR / "models" / "final_delay_model.joblib"

METRICS_PATH = BASE_DIR / "models" / "final_model_metrics.json"


# ============================================================
# LOAD MODEL
# ============================================================

if not MODEL_PATH.exists():
    raise RuntimeError(
        f"Model file not found: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# ============================================================
# LOAD MODEL METRICS
# ============================================================

if METRICS_PATH.exists():

    with open(
        METRICS_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        model_info = json.load(file)

else:

    model_info = {
        "model": "Unknown",
        "threshold": 0.50,
    }


PREDICTION_THRESHOLD = float(
    model_info.get(
        "threshold",
        0.50,
    )
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="NZ Transit Intelligence API",
    description=(
        "Machine-learning API for Auckland "
        "Transport delay prediction."
    ),
    version="1.1.0",
)


# ============================================================
# REQUEST MODEL
# ============================================================

class DelayPredictionRequest(BaseModel):

    route_id: str = Field(
        ...,
        min_length=1,
        description="GTFS route ID",
    )

    stop_id: str = Field(
        ...,
        min_length=1,
        description="GTFS stop ID",
    )

    stop_sequence: int = Field(
        ...,
        ge=0,
        description="Stop sequence within the trip",
    )

    direction_id: int | None = Field(
        default=None,
        description="GTFS direction ID",
    )

    local_hour: int = Field(
        ...,
        ge=0,
        le=23,
        description="Local Auckland hour",
    )

    day_number: int = Field(
        ...,
        ge=1,
        le=7,
        description="ISO day number: Monday=1, Sunday=7",
    )


# ============================================================
# RESPONSE MODEL
# ============================================================

class DelayPredictionResponse(BaseModel):

    delayed: bool

    delay_probability: float

    delay_probability_percent: float

    threshold: float

    risk_level: str

    time_period: str

    is_weekend: bool


# ============================================================
# HELPERS
# ============================================================

def calculate_time_period(local_hour: int) -> str:

    if 5 <= local_hour <= 9:
        return "Morning Peak"

    if 10 <= local_hour <= 15:
        return "Midday"

    if 16 <= local_hour <= 19:
        return "Evening Peak"

    return "Off Peak"


def calculate_weekend(day_number: int) -> bool:

    return day_number in (6, 7)


def get_risk_level(probability: float) -> str:

    if probability < 0.25:
        return "Low"

    if probability < 0.50:
        return "Moderate"

    if probability < 0.75:
        return "High"

    return "Very High"


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "service": "NZ Transit Intelligence API",
        "status": "running",
        "version": "1.1.0",
        "docs": "/docs",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model_loaded": True,
        "model_file": MODEL_PATH.name,
    }


# ============================================================
# MODEL INFO
# ============================================================

@app.get("/model-info")
def get_model_info():

    return {
        "model": model_info.get(
            "model",
            "Unknown",
        ),

        "threshold": PREDICTION_THRESHOLD,

        "accuracy": model_info.get(
            "accuracy"
        ),

        "precision": model_info.get(
            "precision"
        ),

        "recall": model_info.get(
            "recall"
        ),

        "f1": model_info.get(
            "f1"
        ),

        "roc_auc": model_info.get(
            "roc_auc"
        ),

        "pr_auc": model_info.get(
            "pr_auc"
        ),
    }


# ============================================================
# DELAY PREDICTION
# ============================================================

@app.post(
    "/predict-delay",
    response_model=DelayPredictionResponse,
)
def predict_delay(
    request: DelayPredictionRequest
):

    time_period = calculate_time_period(
        request.local_hour
    )

    is_weekend = calculate_weekend(
        request.day_number
    )

    input_data = pd.DataFrame(
        [
            {
                "route_id":
                    request.route_id,

                "stop_id":
                    request.stop_id,

                "stop_sequence":
                    request.stop_sequence,

                "direction_id":
                    request.direction_id,

                "local_hour":
                    request.local_hour,

                "day_number":
                    request.day_number,

                "time_period":
                    time_period,

                "is_weekend":
                    is_weekend,
            }
        ]
    )

    try:

        probability = float(
            model.predict_proba(
                input_data
            )[0][1]
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Prediction failed: "
                f"{str(error)}"
            ),
        )

    delayed = (
        probability
        >= PREDICTION_THRESHOLD
    )

    risk_level = get_risk_level(
        probability
    )

    return DelayPredictionResponse(

        delayed=delayed,

        delay_probability=round(
            probability,
            4,
        ),

        delay_probability_percent=round(
            probability * 100,
            2,
        ),

        threshold=round(
            PREDICTION_THRESHOLD,
            2,
        ),

        risk_level=risk_level,

        time_period=time_period,

        is_weekend=is_weekend,
    )


# ============================================================
# API ROUTES
# ============================================================

@app.get("/routes")
def api_routes():

    return {
        "available_endpoints": [
            "/",
            "/health",
            "/model-info",
            "/predict-delay",
            "/routes",
            "/docs",
        ]
    }