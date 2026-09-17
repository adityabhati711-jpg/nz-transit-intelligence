from sqlalchemy import text

from src.database import engine


SQL_STATEMENTS = [

    # =========================================================
    # MACHINE-LEARNING READY FEATURE VIEW
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.ml_delay_features AS

    SELECT
        record_key,

        trip_id,
        route_id,
        route_short_name,

        stop_id,
        stop_name,

        stop_sequence,

        direction_id,

        local_date,
        local_hour,
        day_number,
        day_name,
        time_period,

        CASE
            WHEN day_number IN (6, 7)
            THEN TRUE
            ELSE FALSE
        END AS is_weekend,

        vehicle_id,

        delay_seconds,
        delay_minutes,

        delay_category,

        is_delayed

    FROM analytics.time_delay_features

    WHERE
        route_id IS NOT NULL
        AND stop_id IS NOT NULL
        AND delay_seconds IS NOT NULL
    """,

    # =========================================================
    # NETWORK KPI VIEW
    # =========================================================

    """
    CREATE OR REPLACE VIEW analytics.network_kpis AS

    SELECT

        COUNT(*) AS total_observations,

        COUNT(DISTINCT trip_id)
            AS unique_trips,

        COUNT(DISTINCT route_id)
            AS routes_observed,

        COUNT(DISTINCT stop_id)
            AS stops_observed,

        ROUND(
            AVG(delay_minutes)::numeric,
            2
        ) AS average_delay_minutes,

        ROUND(
            PERCENTILE_CONT(0.5)
            WITHIN GROUP (
                ORDER BY delay_minutes
            )::numeric,
            2
        ) AS median_delay_minutes,

        ROUND(
            MAX(delay_minutes)::numeric,
            2
        ) AS maximum_delay_minutes,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE is_delayed = TRUE
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS delayed_percentage,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE delay_seconds
                    BETWEEN -60 AND 300
                )
                / NULLIF(
                    COUNT(delay_seconds),
                    0
                )
            )::numeric,
            2
        ) AS on_time_percentage

    FROM analytics.trip_delay_features

    WHERE delay_seconds IS NOT NULL
    """
]


def build_feature_mart():

    print("BUILDING ANALYTICS FEATURE MART")
    print("-------------------------------")

    with engine.begin() as connection:

        for statement in SQL_STATEMENTS:
            connection.execute(
                text(statement)
            )

    print(
        "FEATURE MART CREATED SUCCESSFULLY"
    )


def validate():

    print("\nFEATURE MART VALIDATION")
    print("-----------------------")

    with engine.connect() as connection:

        feature_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.ml_delay_features
            """)
        ).scalar()

        delayed = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.ml_delay_features
                WHERE is_delayed = TRUE
            """)
        ).scalar()

        not_delayed = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM analytics.ml_delay_features
                WHERE is_delayed = FALSE
            """)
        ).scalar()

        kpi = connection.execute(
            text("""
                SELECT *
                FROM analytics.network_kpis
            """)
        ).mappings().one()

        print(
            f"ML-ready records: {feature_count:,}"
        )

        print(
            f"Delayed records: {delayed:,}"
        )

        print(
            f"Not delayed records: {not_delayed:,}"
        )

        print("\nNETWORK KPIs")
        print("------------")

        print(
            f"Observations: {kpi['total_observations']:,}"
        )

        print(
            f"Unique trips: {kpi['unique_trips']:,}"
        )

        print(
            f"Routes observed: {kpi['routes_observed']:,}"
        )

        print(
            f"Stops observed: {kpi['stops_observed']:,}"
        )

        print(
            f"Average delay: "
            f"{kpi['average_delay_minutes']} min"
        )

        print(
            f"Median delay: "
            f"{kpi['median_delay_minutes']} min"
        )

        print(
            f"Delayed: "
            f"{kpi['delayed_percentage']}%"
        )

        print(
            f"On time: "
            f"{kpi['on_time_percentage']}%"
        )


def main():

    build_feature_mart()
    validate()


if __name__ == "__main__":
    main()