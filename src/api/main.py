from pathlib import Path
import json

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.database import engine


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "final_delay_model.joblib"
)

METRICS_PATH = (
    BASE_DIR
    / "models"
    / "final_model_metrics.json"
)


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
        description=(
            "ISO day number: "
            "Monday=1, Sunday=7"
        ),
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

def calculate_time_period(
    local_hour: int,
) -> str:

    if 5 <= local_hour <= 9:
        return "Morning Peak"

    if 10 <= local_hour <= 15:
        return "Midday"

    if 16 <= local_hour <= 19:
        return "Evening Peak"

    return "Off Peak"


def calculate_weekend(
    day_number: int,
) -> bool:

    return day_number in (6, 7)


def get_risk_level(
    probability: float,
) -> str:

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
        "service":
            "NZ Transit Intelligence API",

        "status":
            "running",

        "version":
            "1.1.0",

        "docs":
            "/docs",
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status":
            "healthy",

        "model_loaded":
            True,

        "model_file":
            MODEL_PATH.name,
    }


# ============================================================
# MODEL INFO
# ============================================================

@app.get("/model-info")
def get_model_info():

    return {
        "model":
            model_info.get(
                "model",
                "Unknown",
            ),

        "threshold":
            PREDICTION_THRESHOLD,

        "accuracy":
            model_info.get(
                "accuracy"
            ),

        "precision":
            model_info.get(
                "precision"
            ),

        "recall":
            model_info.get(
                "recall"
            ),

        "f1":
            model_info.get(
                "f1"
            ),

        "roc_auc":
            model_info.get(
                "roc_auc"
            ),

        "pr_auc":
            model_info.get(
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
    request: DelayPredictionRequest,
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
            "/gtfs/routes",
            "/gtfs/routes/{route_id}/stops",
            "/docs",
        ]
    }


# ============================================================
# GTFS ROUTE LIST
# ============================================================

@app.get("/gtfs/routes")
def get_gtfs_routes():

    query = text(
        """
        SELECT
            route_id,
            route_short_name,
            route_long_name
        FROM gtfs_routes
        ORDER BY
            route_short_name,
            route_long_name
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(query)
            .mappings()
            .all()
        )

    return [
        {
            "route_id":
                row["route_id"],

            "route_short_name":
                row["route_short_name"],

            "route_long_name":
                row["route_long_name"],
        }
        for row in rows
    ]


# ============================================================
# STOPS FOR SELECTED ROUTE + DIRECTION
# ============================================================

@app.get(
    "/gtfs/routes/{route_id}/stops"
)
def get_route_stops(
    route_id: str,
    direction_id: int = 0,
):

    query = text(
        """
        SELECT DISTINCT
            st.stop_id,
            s.stop_name,
            st.stop_sequence

        FROM gtfs_trips t

        JOIN gtfs_stop_times st
            ON t.trip_id = st.trip_id

        JOIN gtfs_stops s
            ON st.stop_id = s.stop_id

        WHERE
            t.route_id = :route_id
            AND t.direction_id = :direction_id

        ORDER BY
            st.stop_sequence,
            s.stop_name
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "route_id":
                        route_id,

                    "direction_id":
                        direction_id,
                },
            )
            .mappings()
            .all()
        )

    return [
        {
            "stop_id":
                row["stop_id"],

            "stop_name":
                row["stop_name"],

            "stop_sequence":
                row["stop_sequence"],
        }
        for row in rows
    ]


# ============================================================
# NETWORK ANALYTICS KPIs
# ============================================================

@app.get("/analytics/network-kpis")
def get_network_kpis():

    query = text(
        """
        SELECT
            total_observations,
            unique_trips,
            routes_observed,
            stops_observed,
            average_delay_minutes,
            median_delay_minutes,
            maximum_delay_minutes,
            delayed_percentage,
            on_time_percentage
        FROM analytics.network_kpis
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(query)
            .mappings()
            .first()
        )

    if row is None:
        return {}

    return dict(row)


# ============================================================
# TIME PERIOD PERFORMANCE
# ============================================================

@app.get("/analytics/time-period-performance")
def get_time_period_performance():

    query = text(
        """
        SELECT
            time_period,
            observations,
            delay_observations,
            average_delay_minutes,
            delayed_percentage
        FROM analytics.time_period_performance
        ORDER BY time_period
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(query)
            .mappings()
            .all()
        )

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# TOP DELAYED ROUTES
# ============================================================

@app.get("/analytics/top-delayed-routes")
def get_top_delayed_routes(
    limit: int = 10,
    min_observations: int = 10,
):

    limit = max(
        1,
        min(limit, 50),
    )

    min_observations = max(
        1,
        min_observations,
    )

    query = text(
        """
        SELECT
            route_id,
            route_short_name,
            route_long_name,
            observations,
            delay_observations,
            average_delay_minutes,
            delayed_percentage,
            on_time_percentage
        FROM analytics.route_performance
        WHERE observations >= :min_observations
        ORDER BY
            delayed_percentage DESC,
            observations DESC
        LIMIT :limit
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "limit": limit,
                    "min_observations":
                        min_observations,
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# TOP PROBLEM STOPS + MAP DATA
# ============================================================

@app.get("/analytics/problem-stops")
def get_problem_stops(
    limit: int = 50,
    min_observations: int = 5,
):

    limit = max(
        1,
        min(limit, 200),
    )

    min_observations = max(
        1,
        min_observations,
    )

    query = text(
        """
        SELECT
            si.stop_id,
            si.stop_name,
            si.observations,
            si.delay_observations,
            si.average_delay_minutes,
            si.maximum_delay_minutes,
            si.delayed_percentage,
            gs.stop_lat,
            gs.stop_lon

        FROM analytics.stop_insights si

        JOIN gtfs_stops gs
            ON si.stop_id = gs.stop_id

        WHERE
            si.observations >= :min_observations
            AND gs.stop_lat IS NOT NULL
            AND gs.stop_lon IS NOT NULL

        ORDER BY
            si.delayed_percentage DESC,
            si.observations DESC

        LIMIT :limit
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "limit": limit,
                    "min_observations":
                        min_observations,
                },
            )
            .mappings()
            .all()
        )

    return [
        {
            "stop_id":
                row["stop_id"],

            "stop_name":
                row["stop_name"],

            "observations":
                row["observations"],

            "delay_observations":
                row["delay_observations"],

            "average_delay_minutes":
                row["average_delay_minutes"],

            "maximum_delay_minutes":
                row["maximum_delay_minutes"],

            "delayed_percentage":
                row["delayed_percentage"],

            "stop_lat":
                row["stop_lat"],

            "stop_lon":
                row["stop_lon"],
        }
        for row in rows
    ]